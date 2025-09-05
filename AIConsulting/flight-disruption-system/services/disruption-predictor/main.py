"""
Flight Disruption Predictor Service

Advanced ML-powered service for predicting flight disruptions using
weather data, historical patterns, aircraft maintenance, and operational factors.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import os
import numpy as np
import structlog

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
import httpx
import redis
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer
from uuid import UUID
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

# Import local components
from config import settings
from database import Database
from agents import PredictionAgent
from ml_models import WeatherPredictor, TechnicalPredictor, DisruptionPredictor

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Pydantic models
class FlightPredictionRequest(BaseModel):
    flight_id: str
    departure_time: datetime
    arrival_time: datetime
    departure_airport: str
    arrival_airport: str
    aircraft_type: str
    weather_data: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    flight_id: str
    predicted_disruption_type: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    predicted_delay_minutes: int
    prediction_horizon_hours: int
    reasoning: str
    risk_factors: List[str]
    recommended_actions: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BatchPredictionRequest(BaseModel):
    flight_ids: List[str]
    prediction_horizon_hours: int = 4

# Prometheus metrics
PREDICTION_COUNTER = Counter('predictions_total', 'Total number of predictions made', ['type'])
PREDICTION_DURATION = Histogram('prediction_duration_seconds', 'Time spent making predictions')
CONFIDENCE_GAUGE = Gauge('prediction_confidence_current', 'Current prediction confidence scores')
HIGH_RISK_FLIGHTS = Gauge('high_risk_flights_current', 'Number of flights currently at high risk')

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None
prediction_agent: Optional[PredictionAgent] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, kafka_producer, prediction_agent, http_client
    
    # Initialize database
    db = Database(settings.database_url)
    await db.connect()
    
    # Initialize Redis
    redis_client = redis.from_url(settings.redis_url)
    
    # Initialize Kafka producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        value_serializer=lambda x: json.dumps(x, default=str).encode()
    )
    await kafka_producer.start()
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize AI prediction agent
    prediction_agent = PredictionAgent(
        openai_api_key=settings.openai_api_key,
        weather_api_key=settings.weather_api_key
    )
    
    # Start background prediction tasks
    asyncio.create_task(continuous_prediction_task())
    
    logger.info("Disruption Prediction Service started")
    
    yield
    
    # Shutdown
    if kafka_producer:
        await kafka_producer.stop()
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()
    if db:
        await db.disconnect()

app = FastAPI(
    title="Flight Disruption Prediction Service",
    description="AI-powered flight disruption prediction with 2-4 hour advance notice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "disruption-predictor",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/predictions/single", response_model=PredictionResponse)
async def predict_single_flight(request: FlightPredictionRequest) -> PredictionResponse:
    """Predict disruption for a single flight"""
    start_time = time.time()
    try:
        # Get flight data from database
        flight_data = await db.get_flight_data(request.flight_id)
        if not flight_data:
            raise HTTPException(status_code=404, detail="Flight not found")
        
        # Get weather data if not provided
        weather_data = request.weather_data
        if not weather_data:
            weather_data = await get_weather_data(
                request.departure_airport,
                request.departure_time
            )
        
        # Get historical data
        historical_data = await db.get_historical_disruptions(
            request.departure_airport,
            request.arrival_airport,
            request.aircraft_type
        )
        
        # Make prediction using AI agent
        prediction = await prediction_agent.predict_disruption({
            "flight_data": flight_data,
            "weather_data": weather_data,
            "historical_data": historical_data,
            "aircraft_type": request.aircraft_type,
            "route": f"{request.departure_airport}-{request.arrival_airport}"
        })
        
        # Store prediction in database
        await db.store_prediction(request.flight_id, prediction)
        
        # Cache result
        cache_key = f"prediction:{request.flight_id}"
        await redis_client.setex(
            cache_key, 
            3600,  # 1 hour cache
            json.dumps(prediction, default=str)
        )
        
        # Publish to Kafka if high risk
        if prediction["confidence_score"] > 0.7:
            await kafka_producer.send(
                "disruption-predictions",
                {
                    "flight_id": str(request.flight_id),
                    "prediction": prediction,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Update metrics
        PREDICTION_COUNTER.labels(type=prediction.get('predicted_disruption_type', 'none')).inc()
        PREDICTION_DURATION.observe(time.time() - start_time)
        CONFIDENCE_GAUGE.set(prediction.get('confidence_score', 0.5))
        
        return PredictionResponse(**prediction)
        
    except Exception as e:
        logger.error("Prediction failed", flight_id=str(request.flight_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/predictions/batch")
async def predict_batch_flights(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Predict disruptions for multiple flights"""
    try:
        # Add batch prediction to background tasks
        background_tasks.add_task(
            process_batch_predictions,
            request.flight_ids,
            request.prediction_horizon_hours
        )
        
        return {
            "message": f"Batch prediction started for {len(request.flight_ids)} flights",
            "flight_count": len(request.flight_ids),
            "prediction_horizon_hours": request.prediction_horizon_hours,
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
    except Exception as e:
        logger.error("Batch prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/api/v1/predictions/{flight_id}")
async def get_flight_prediction(flight_id: str) -> Optional[PredictionResponse]:
    """Get existing prediction for a flight"""
    try:
        # Check cache first
        cache_key = f"prediction:{flight_id}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            prediction = json.loads(cached)
            return PredictionResponse(**prediction)
        
        # Check database
        prediction = await db.get_latest_prediction(flight_id)
        if prediction:
            # Cache result
            await redis_client.setex(
                cache_key,
                3600,
                json.dumps(prediction, default=str)
            )
            return PredictionResponse(**prediction)
        
        return None
        
    except Exception as e:
        logger.error("Failed to get prediction", flight_id=str(flight_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get prediction: {str(e)}")

@app.get("/api/v1/predictions/high-risk")
async def get_high_risk_flights(
    hours_ahead: int = 4,
    confidence_threshold: float = 0.7
) -> List[PredictionResponse]:
    """Get flights with high disruption risk"""
    try:
        predictions = await db.get_high_risk_predictions(
            hours_ahead=hours_ahead,
            confidence_threshold=confidence_threshold
        )
        
        return [PredictionResponse(**pred) for pred in predictions]
        
    except Exception as e:
        logger.error("Failed to get high risk flights", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get high risk flights: {str(e)}")

@app.post("/api/v1/models/retrain")
async def retrain_models(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Retrain ML models with latest data"""
    try:
        background_tasks.add_task(retrain_prediction_models)
        
        return {
            "message": "Model retraining started",
            "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to start model retraining", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start retraining: {str(e)}")

@app.get("/api/v1/models/performance")
async def get_model_performance() -> Dict[str, Any]:
    """Get performance metrics for prediction models"""
    try:
        performance = await db.get_model_performance_metrics()
        return performance
        
    except Exception as e:
        logger.error("Failed to get model performance", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

# Background tasks
async def continuous_prediction_task():
    """Continuously predict disruptions for upcoming flights"""
    while True:
        try:
            # Get flights in next 4 hours
            upcoming_flights = await db.get_upcoming_flights(hours=4)
            
            for flight in upcoming_flights:
                # Check if we already have a recent prediction
                cache_key = f"prediction:{flight['id']}"
                cached = await redis_client.get(cache_key)
                
                if not cached:
                    # Make prediction
                    try:
                        request = FlightPredictionRequest(
                            flight_id=flight['id'],
                            departure_time=flight['scheduled_departure'],
                            arrival_time=flight['scheduled_arrival'],
                            departure_airport=flight['departure_airport'],
                            arrival_airport=flight['arrival_airport'],
                            aircraft_type=flight['aircraft_type']
                        )
                        
                        await predict_single_flight(request)
                        
                    except Exception as e:
                        logger.error(
                            "Failed to predict flight in background",
                            flight_id=str(flight['id']),
                            error=str(e)
                        )
            
            # Wait 10 minutes before next batch
            await asyncio.sleep(600)
            
        except Exception as e:
            logger.error("Continuous prediction task failed", error=str(e))
            await asyncio.sleep(60)  # Wait 1 minute before retry

async def process_batch_predictions(flight_ids: List[str], prediction_horizon_hours: int):
    """Process batch predictions in background"""
    try:
        for flight_id in flight_ids:
            # Get flight data
            flight_data = await db.get_flight_data(flight_id)
            if flight_data:
                request = FlightPredictionRequest(
                    flight_id=flight_id,
                    departure_time=flight_data['scheduled_departure'],
                    arrival_time=flight_data['scheduled_arrival'],
                    departure_airport=flight_data['departure_airport'],
                    arrival_airport=flight_data['arrival_airport'],
                    aircraft_type=flight_data['aircraft_type']
                )
                
                try:
                    await predict_single_flight(request)
                except Exception as e:
                    logger.error(
                        "Batch prediction failed for flight",
                        flight_id=str(flight_id),
                        error=str(e)
                    )
        
        logger.info("Batch prediction completed", flight_count=len(flight_ids))
        
    except Exception as e:
        logger.error("Batch prediction processing failed", error=str(e))

async def retrain_prediction_models():
    """Retrain ML models with latest data"""
    try:
        # Get training data
        training_data = await db.get_training_data()
        
        # Initialize model trainers
        weather_predictor = WeatherPredictor()
        technical_predictor = TechnicalPredictor()
        
        # Train models
        weather_model = await weather_predictor.train(training_data)
        technical_model = await technical_predictor.train(training_data)
        
        # Store new models
        await db.store_trained_model(weather_model)
        await db.store_trained_model(technical_model)
        
        # Update prediction agent with new models
        await prediction_agent.update_models({
            "weather": weather_model,
            "technical": technical_model
        })
        
        logger.info("Model retraining completed successfully")
        
    except Exception as e:
        logger.error("Model retraining failed", error=str(e))

async def get_weather_data(airport_code: str, departure_time: datetime) -> Dict[str, Any]:
    """Get weather data for prediction"""
    try:
        # Use weather API to get forecast
        if settings.weather_api_key and http_client:
            # Example weather API call (implement with actual weather service)
            response = await http_client.get(
                f"https://api.weather.com/forecast/{airport_code}",
                params={"datetime": departure_time.isoformat()},
                headers={"Authorization": f"Bearer {settings.weather_api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
        
        # Return default/mock weather data if API unavailable
        return {
            "visibility": "10000m",
            "wind_speed": "10kt",
            "precipitation": "none",
            "temperature": "15C",
            "pressure": "1013hPa"
        }
        
    except Exception as e:
        logger.error("Failed to get weather data", airport=airport_code, error=str(e))
        return {}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)