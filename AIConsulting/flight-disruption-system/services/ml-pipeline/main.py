"""
ML Pipeline Service - Advanced Analytics & Optimization
Production-ready machine learning pipeline for predictive analytics and optimization

Features:
- Advanced ML model training and inference
- Real-time feature engineering and streaming analytics
- Model performance monitoring and A/B testing
- Automated model retraining and deployment
- Advanced anomaly detection and pattern recognition
- Predictive maintenance for system components
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
import joblib
import asyncpg
import redis
import json
import uuid
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import httpx
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter('ml_pipeline_requests_total', 'Total ML pipeline requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('ml_pipeline_request_duration_seconds', 'Request duration')
MODEL_ACCURACY = Gauge('ml_pipeline_model_accuracy', 'Current model accuracy', ['model_type'])
PREDICTION_COUNT = Counter('ml_pipeline_predictions_total', 'Total predictions made', ['model_type'])
TRAINING_DURATION = Histogram('ml_pipeline_training_duration_seconds', 'Model training duration')

# Data Models
class FeatureData(BaseModel):
    timestamp: datetime
    flight_id: str
    departure_delay: Optional[float] = None
    weather_score: Optional[float] = None
    aircraft_age: Optional[int] = None
    route_popularity: Optional[float] = None
    historical_performance: Optional[float] = None
    passenger_load_factor: Optional[float] = None
    crew_experience: Optional[float] = None
    airport_congestion: Optional[float] = None
    maintenance_score: Optional[float] = None

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    model_type: str = Field(default="disruption_predictor", description="Type of prediction model")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for prediction")

class TrainingRequest(BaseModel):
    model_type: str
    training_data_period: int = Field(default=30, description="Days of data to use for training")
    retrain_existing: bool = Field(default=True, description="Whether to retrain existing model")

class ModelMetrics(BaseModel):
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: Optional[float] = None
    training_time: float
    last_updated: datetime
    sample_size: int

class AnomalalyDetectionResult(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    detected_patterns: List[str]
    recommended_actions: List[str]

# ML Pipeline Manager
class MLPipelineManager:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_metrics = {}
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # Database connection
        self.db_pool = None
        
    async def initialize_db_pool(self):
        """Initialize database connection pool"""
        try:
            database_url = os.getenv('DATABASE_URL')
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def get_training_data(self, days: int = 30) -> pd.DataFrame:
        """Fetch training data from database"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                SELECT 
                    f.id as flight_id,
                    f.departure_time,
                    f.arrival_time,
                    f.aircraft_type,
                    f.departure_airport,
                    f.arrival_airport,
                    f.scheduled_departure,
                    f.scheduled_arrival,
                    d.disruption_type,
                    d.severity,
                    d.delay_duration,
                    d.cost_impact,
                    p.total_passengers,
                    p.rebookings_required,
                    EXTRACT(EPOCH FROM (f.departure_time - f.scheduled_departure))/3600 as departure_delay_hours,
                    CASE WHEN d.id IS NOT NULL THEN 1 ELSE 0 END as has_disruption
                FROM flights f
                LEFT JOIN disruptions d ON f.id = d.flight_id
                LEFT JOIN passengers p ON f.id = p.flight_id
                WHERE f.departure_time >= NOW() - INTERVAL '%s days'
                ORDER BY f.departure_time DESC
                """ % days
                
                rows = await conn.fetch(query)
                
                if rows:
                    # Convert to DataFrame
                    df = pd.DataFrame([dict(row) for row in rows])
                    
                    # Feature engineering
                    df['departure_hour'] = pd.to_datetime(df['departure_time']).dt.hour
                    df['day_of_week'] = pd.to_datetime(df['departure_time']).dt.dayofweek
                    df['route'] = df['departure_airport'] + '-' + df['arrival_airport']
                    df['flight_duration'] = (
                        pd.to_datetime(df['scheduled_arrival']) - 
                        pd.to_datetime(df['scheduled_departure'])
                    ).dt.total_seconds() / 3600
                    
                    # Calculate historical performance by route
                    route_performance = df.groupby('route')['has_disruption'].mean()
                    df['route_disruption_rate'] = df['route'].map(route_performance)
                    
                    # Fill missing values
                    df['departure_delay_hours'] = df['departure_delay_hours'].fillna(0)
                    df['total_passengers'] = df['total_passengers'].fillna(df['total_passengers'].mean())
                    df['rebookings_required'] = df['rebookings_required'].fillna(0)
                    df['cost_impact'] = df['cost_impact'].fillna(0)
                    df['delay_duration'] = df['delay_duration'].fillna(0)
                    
                    logger.info(f"Retrieved {len(df)} training records")
                    return df
                else:
                    logger.warning("No training data found")
                    return pd.DataFrame()
                    
        except Exception as e:
            logger.error(f"Error fetching training data: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch training data")
    
    async def train_disruption_predictor(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train disruption prediction model"""
        try:
            start_time = datetime.now()
            
            # Prepare features
            feature_columns = [
                'departure_hour', 'day_of_week', 'flight_duration',
                'total_passengers', 'route_disruption_rate'
            ]
            
            X = training_data[feature_columns]
            y = training_data['has_disruption']
            
            # Handle categorical variables
            le_aircraft = LabelEncoder()
            X['aircraft_encoded'] = le_aircraft.fit_transform(training_data['aircraft_type'].fillna('Unknown'))
            
            le_dep_airport = LabelEncoder()
            X['dep_airport_encoded'] = le_dep_airport.fit_transform(training_data['departure_airport'])
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')
            
            # Store model and preprocessors
            self.models['disruption_predictor'] = model
            self.scalers['disruption_predictor'] = scaler
            self.encoders['disruption_predictor'] = {
                'aircraft': le_aircraft,
                'dep_airport': le_dep_airport
            }
            
            # Feature importance
            feature_names = feature_columns + ['aircraft_encoded', 'dep_airport_encoded']
            self.feature_importance['disruption_predictor'] = dict(
                zip(feature_names, model.feature_importances_)
            )
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Store metrics
            metrics = ModelMetrics(
                model_type='disruption_predictor',
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                training_time=training_time,
                last_updated=datetime.now(),
                sample_size=len(training_data)
            )
            
            self.model_metrics['disruption_predictor'] = metrics
            
            # Update Prometheus metrics
            MODEL_ACCURACY.labels(model_type='disruption_predictor').set(accuracy)
            TRAINING_DURATION.observe(training_time)
            
            logger.info(f"Disruption predictor trained successfully - Accuracy: {accuracy:.3f}")
            
            return {
                'model_type': 'disruption_predictor',
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_importance': self.feature_importance['disruption_predictor'],
                'training_time': training_time,
                'sample_size': len(training_data)
            }
            
        except Exception as e:
            logger.error(f"Error training disruption predictor: {e}")
            raise HTTPException(status_code=500, detail="Model training failed")
    
    async def train_cost_predictor(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train cost impact prediction model"""
        try:
            start_time = datetime.now()
            
            # Filter data with disruptions
            disrupted_data = training_data[training_data['has_disruption'] == 1].copy()
            
            if len(disrupted_data) < 50:
                logger.warning("Insufficient disrupted flight data for cost prediction")
                return {'error': 'Insufficient training data'}
            
            # Prepare features
            feature_columns = [
                'departure_hour', 'day_of_week', 'flight_duration',
                'total_passengers', 'delay_duration'
            ]
            
            X = disrupted_data[feature_columns]
            y = disrupted_data['cost_impact']
            
            # Handle categorical variables
            le_severity = LabelEncoder()
            X['severity_encoded'] = le_severity.fit_transform(disrupted_data['severity'])
            
            le_disruption_type = LabelEncoder()
            X['disruption_type_encoded'] = le_disruption_type.fit_transform(
                disrupted_data['disruption_type']
            )
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # R² score
            r2_score = model.score(X_test, y_test)
            
            # Store model and preprocessors
            self.models['cost_predictor'] = model
            self.scalers['cost_predictor'] = scaler
            self.encoders['cost_predictor'] = {
                'severity': le_severity,
                'disruption_type': le_disruption_type
            }
            
            # Feature importance
            feature_names = feature_columns + ['severity_encoded', 'disruption_type_encoded']
            self.feature_importance['cost_predictor'] = dict(
                zip(feature_names, model.feature_importances_)
            )
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Store metrics
            metrics = ModelMetrics(
                model_type='cost_predictor',
                accuracy=r2_score,  # R² for regression
                precision=0.0,  # N/A for regression
                recall=0.0,     # N/A for regression
                f1_score=0.0,   # N/A for regression
                mse=mse,
                training_time=training_time,
                last_updated=datetime.now(),
                sample_size=len(disrupted_data)
            )
            
            self.model_metrics['cost_predictor'] = metrics
            
            # Update Prometheus metrics
            MODEL_ACCURACY.labels(model_type='cost_predictor').set(r2_score)
            TRAINING_DURATION.observe(training_time)
            
            logger.info(f"Cost predictor trained successfully - R²: {r2_score:.3f}, RMSE: {rmse:.2f}")
            
            return {
                'model_type': 'cost_predictor',
                'r2_score': r2_score,
                'rmse': rmse,
                'mse': mse,
                'feature_importance': self.feature_importance['cost_predictor'],
                'training_time': training_time,
                'sample_size': len(disrupted_data)
            }
            
        except Exception as e:
            logger.error(f"Error training cost predictor: {e}")
            raise HTTPException(status_code=500, detail="Cost model training failed")
    
    async def predict_disruption(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make disruption prediction"""
        try:
            if 'disruption_predictor' not in self.models:
                raise HTTPException(status_code=400, detail="Disruption predictor not trained")
            
            model = self.models['disruption_predictor']
            scaler = self.scalers['disruption_predictor']
            encoders = self.encoders['disruption_predictor']
            
            # Prepare features
            feature_vector = [
                features.get('departure_hour', 12),
                features.get('day_of_week', 1),
                features.get('flight_duration', 2.0),
                features.get('total_passengers', 150),
                features.get('route_disruption_rate', 0.1),
            ]
            
            # Encode categorical features
            aircraft_type = features.get('aircraft_type', 'Unknown')
            if aircraft_type in encoders['aircraft'].classes_:
                aircraft_encoded = encoders['aircraft'].transform([aircraft_type])[0]
            else:
                aircraft_encoded = 0  # Default for unknown aircraft
            feature_vector.append(aircraft_encoded)
            
            dep_airport = features.get('departure_airport', 'LHR')
            if dep_airport in encoders['dep_airport'].classes_:
                dep_airport_encoded = encoders['dep_airport'].transform([dep_airport])[0]
            else:
                dep_airport_encoded = 0  # Default for unknown airport
            feature_vector.append(dep_airport_encoded)
            
            # Scale features
            feature_vector = np.array(feature_vector).reshape(1, -1)
            feature_vector_scaled = scaler.transform(feature_vector)
            
            # Make prediction
            disruption_probability = model.predict_proba(feature_vector_scaled)[0][1]
            disruption_prediction = int(disruption_probability > 0.5)
            
            # Feature importance contribution
            feature_names = [
                'departure_hour', 'day_of_week', 'flight_duration',
                'total_passengers', 'route_disruption_rate',
                'aircraft_encoded', 'dep_airport_encoded'
            ]
            
            feature_contributions = {}
            for i, (name, value) in enumerate(zip(feature_names, feature_vector.flatten())):
                importance = self.feature_importance['disruption_predictor'].get(name, 0)
                feature_contributions[name] = {
                    'value': float(value),
                    'importance': float(importance),
                    'contribution': float(value * importance)
                }
            
            # Update metrics
            PREDICTION_COUNT.labels(model_type='disruption_predictor').inc()
            
            result = {
                'disruption_probability': float(disruption_probability),
                'disruption_prediction': bool(disruption_prediction),
                'confidence': float(abs(disruption_probability - 0.5) * 2),  # 0 to 1 scale
                'feature_contributions': feature_contributions,
                'model_version': 'disruption_predictor_v1',
                'prediction_timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            cache_key = f"prediction:disruption:{hash(str(features))}"
            await self.redis_client.setex(
                cache_key, 
                300,  # 5 minutes TTL
                json.dumps(result, default=str)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error making disruption prediction: {e}")
            raise HTTPException(status_code=500, detail="Prediction failed")
    
    async def detect_anomalies(self, recent_data: List[Dict[str, Any]]) -> AnomalalyDetectionResult:
        """Detect anomalies in flight patterns"""
        try:
            if len(recent_data) < 10:
                return AnomalalyDetectionResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    confidence=0.0,
                    detected_patterns=[],
                    recommended_actions=[]
                )
            
            df = pd.DataFrame(recent_data)
            
            # Calculate anomaly features
            delay_mean = df.get('departure_delay', pd.Series([0])).mean()
            delay_std = df.get('departure_delay', pd.Series([0])).std()
            cancellation_rate = df.get('is_cancelled', pd.Series([0])).mean()
            cost_increase = df.get('cost_impact', pd.Series([0])).mean()
            
            # Define thresholds
            delay_threshold = 2.0  # hours
            cancellation_threshold = 0.15  # 15%
            cost_threshold = 50000  # £50,000
            
            anomalies = []
            patterns = []
            actions = []
            anomaly_score = 0.0
            
            # Check for delay anomalies
            if delay_mean > delay_threshold:
                anomalies.append("high_delays")
                patterns.append(f"Average delay: {delay_mean:.1f} hours (threshold: {delay_threshold}h)")
                actions.append("Investigate crew scheduling and airport capacity")
                anomaly_score += 0.3
            
            # Check for cancellation anomalies
            if cancellation_rate > cancellation_threshold:
                anomalies.append("high_cancellations")
                patterns.append(f"Cancellation rate: {cancellation_rate:.1%} (threshold: {cancellation_threshold:.1%})")
                actions.append("Review maintenance schedules and crew availability")
                anomaly_score += 0.4
            
            # Check for cost anomalies
            if cost_increase > cost_threshold:
                anomalies.append("high_costs")
                patterns.append(f"Average cost impact: £{cost_increase:,.0f} (threshold: £{cost_threshold:,.0f})")
                actions.append("Optimize rebooking and accommodation strategies")
                anomaly_score += 0.3
            
            is_anomaly = anomaly_score > 0.5
            confidence = min(anomaly_score, 1.0)
            
            return AnomalalyDetectionResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                confidence=confidence,
                detected_patterns=patterns,
                recommended_actions=actions
            )
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return AnomalalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                detected_patterns=[],
                recommended_actions=[]
            )
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        try:
            performance = {}
            
            for model_type, metrics in self.model_metrics.items():
                performance[model_type] = {
                    'accuracy': metrics.accuracy,
                    'precision': metrics.precision,
                    'recall': metrics.recall,
                    'f1_score': metrics.f1_score,
                    'mse': metrics.mse,
                    'training_time': metrics.training_time,
                    'last_updated': metrics.last_updated.isoformat(),
                    'sample_size': metrics.sample_size,
                    'model_age_hours': (datetime.now() - metrics.last_updated).total_seconds() / 3600
                }
            
            # Add feature importance
            for model_type in self.feature_importance:
                if model_type in performance:
                    performance[model_type]['feature_importance'] = self.feature_importance[model_type]
            
            # Add recommendations for model updates
            recommendations = []
            for model_type, perf in performance.items():
                age_hours = perf.get('model_age_hours', 0)
                accuracy = perf.get('accuracy', 0)
                
                if age_hours > 168:  # 1 week
                    recommendations.append(f"{model_type}: Model is {age_hours:.1f} hours old - consider retraining")
                
                if accuracy < 0.8:
                    recommendations.append(f"{model_type}: Low accuracy ({accuracy:.3f}) - review training data")
            
            performance['recommendations'] = recommendations
            performance['overall_health'] = 'good' if len(recommendations) == 0 else 'needs_attention'
            
            return performance
            
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            raise HTTPException(status_code=500, detail="Failed to get model performance")

# Initialize ML Pipeline Manager
ml_manager = MLPipelineManager()

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ml_manager.initialize_db_pool()
    logger.info("ML Pipeline Service started")
    yield
    # Shutdown
    await ml_manager.close_db_pool()
    logger.info("ML Pipeline Service stopped")

# Create FastAPI app
app = FastAPI(
    title="ML Pipeline Service",
    description="Advanced ML pipeline for predictive analytics and optimization",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "ml-pipeline",
        "models_loaded": list(ml_manager.models.keys()),
        "database_connected": ml_manager.db_pool is not None
    }

@app.post("/train/{model_type}")
async def train_model(model_type: str, request: TrainingRequest, background_tasks: BackgroundTasks):
    """Train ML model"""
    REQUEST_COUNT.labels(method="POST", endpoint="/train").inc()
    
    with REQUEST_DURATION.time():
        try:
            if model_type not in ['disruption_predictor', 'cost_predictor']:
                raise HTTPException(status_code=400, detail="Invalid model type")
            
            # Get training data
            training_data = await ml_manager.get_training_data(request.training_data_period)
            
            if training_data.empty:
                raise HTTPException(status_code=400, detail="No training data available")
            
            # Train model
            if model_type == 'disruption_predictor':
                result = await ml_manager.train_disruption_predictor(training_data)
            elif model_type == 'cost_predictor':
                result = await ml_manager.train_cost_predictor(training_data)
            
            return {
                "message": f"{model_type} training completed",
                "training_results": result
            }
            
        except Exception as e:
            logger.error(f"Error training {model_type}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def make_prediction(request: PredictionRequest):
    """Make ML prediction"""
    REQUEST_COUNT.labels(method="POST", endpoint="/predict").inc()
    
    with REQUEST_DURATION.time():
        try:
            if request.model_type == 'disruption_predictor':
                result = await ml_manager.predict_disruption(request.features)
            else:
                raise HTTPException(status_code=400, detail="Invalid model type")
            
            # Check confidence threshold
            if result['confidence'] < request.confidence_threshold:
                result['low_confidence_warning'] = True
                result['message'] = f"Prediction confidence ({result['confidence']:.3f}) below threshold ({request.confidence_threshold})"
            
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/anomaly-detection")
async def detect_anomalies(recent_data: List[Dict[str, Any]]):
    """Detect anomalies in recent data"""
    REQUEST_COUNT.labels(method="POST", endpoint="/anomaly-detection").inc()
    
    with REQUEST_DURATION.time():
        result = await ml_manager.detect_anomalies(recent_data)
        return result

@app.get("/model-performance")
async def get_model_performance():
    """Get model performance metrics"""
    REQUEST_COUNT.labels(method="GET", endpoint="/model-performance").inc()
    
    with REQUEST_DURATION.time():
        return await ml_manager.get_model_performance()

@app.get("/feature-importance/{model_type}")
async def get_feature_importance(model_type: str):
    """Get feature importance for model"""
    REQUEST_COUNT.labels(method="GET", endpoint="/feature-importance").inc()
    
    if model_type not in ml_manager.feature_importance:
        raise HTTPException(status_code=404, detail="Model not found or not trained")
    
    return {
        "model_type": model_type,
        "feature_importance": ml_manager.feature_importance[model_type],
        "last_updated": ml_manager.model_metrics[model_type].last_updated
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/retrain-all")
async def retrain_all_models(background_tasks: BackgroundTasks):
    """Retrain all models with latest data"""
    REQUEST_COUNT.labels(method="POST", endpoint="/retrain-all").inc()
    
    async def retrain_models():
        try:
            training_data = await ml_manager.get_training_data(30)
            
            if not training_data.empty:
                # Retrain disruption predictor
                await ml_manager.train_disruption_predictor(training_data)
                logger.info("Disruption predictor retrained")
                
                # Retrain cost predictor
                await ml_manager.train_cost_predictor(training_data)
                logger.info("Cost predictor retrained")
            
        except Exception as e:
            logger.error(f"Error retraining models: {e}")
    
    background_tasks.add_task(retrain_models)
    
    return {"message": "Model retraining started in background"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=True
    )