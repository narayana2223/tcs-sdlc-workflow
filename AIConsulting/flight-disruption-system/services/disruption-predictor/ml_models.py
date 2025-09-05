import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import structlog
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import json

logger = structlog.get_logger()

class BasePredictor:
    """Base class for ML prediction models"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = []
        self.is_trained = False
    
    def preprocess_features(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Preprocess raw data into features"""
        raise NotImplementedError
    
    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the model"""
        raise NotImplementedError
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions"""
        raise NotImplementedError

class WeatherPredictor(BasePredictor):
    """ML model for weather-related disruption prediction"""
    
    def __init__(self):
        super().__init__()
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
    
    def preprocess_features(self, data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
        """Preprocess weather and flight data into features"""
        features = []
        targets = []
        
        for record in data:
            try:
                # Extract weather features
                weather_data = record.get('weather_data', {})
                if isinstance(weather_data, str):
                    weather_data = json.loads(weather_data) if weather_data else {}
                
                # Flight features
                departure_hour = self._extract_hour(record.get('scheduled_departure'))
                month = self._extract_month(record.get('scheduled_departure'))
                
                # Weather features with safe extraction
                visibility = self._parse_visibility(weather_data.get('visibility', '10000m'))
                wind_speed = self._parse_wind_speed(weather_data.get('wind_speed', '5kt'))
                temperature = self._parse_temperature(weather_data.get('temperature', '15C'))
                
                precipitation_type = weather_data.get('precipitation', 'none')
                has_precipitation = 1 if precipitation_type != 'none' else 0
                
                # Route features
                departure_airport = record.get('departure_airport', 'UNK')
                arrival_airport = record.get('arrival_airport', 'UNK')
                route_type = self._classify_route_type(departure_airport, arrival_airport)
                
                feature_row = {
                    'departure_hour': departure_hour,
                    'month': month,
                    'visibility_km': visibility,
                    'wind_speed_kt': wind_speed,
                    'temperature_c': temperature,
                    'has_precipitation': has_precipitation,
                    'route_type': route_type,
                    'is_weekend': self._is_weekend(record.get('scheduled_departure')),
                    'is_winter': 1 if month in [11, 12, 1, 2] else 0,
                }
                
                features.append(feature_row)
                
                # Target: weather-related disruption
                disruption_type = record.get('disruption_type', 'none')
                is_weather_disruption = 1 if disruption_type == 'weather' else 0
                targets.append(is_weather_disruption)
                
            except Exception as e:
                logger.warning("Failed to process record", error=str(e))
                continue
        
        if not features:
            raise ValueError("No valid features extracted from training data")
        
        df_features = pd.DataFrame(features)
        self.feature_names = df_features.columns.tolist()
        
        return df_features, pd.Series(targets)
    
    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the weather prediction model"""
        try:
            logger.info("Training weather prediction model", data_size=len(training_data))
            
            # Preprocess data
            X, y = self.preprocess_features(training_data)
            
            if len(X) < 10:
                raise ValueError("Insufficient training data")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_predictions = self.model.predict(X_train_scaled)
            test_predictions = self.model.predict(X_test_scaled)
            
            # Calculate metrics
            train_accuracy = accuracy_score(y_train, train_predictions)
            test_accuracy = accuracy_score(y_test, test_predictions)
            precision = precision_score(y_test, test_predictions, zero_division=0)
            recall = recall_score(y_test, test_predictions, zero_division=0)
            f1 = f1_score(y_test, test_predictions, zero_division=0)
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
            
            self.is_trained = True
            
            model_info = {
                'model_name': 'WeatherDisruptionPredictor',
                'model_version': '2.1.0',
                'model_type': 'weather',
                'accuracy_score': test_accuracy,
                'precision_score': precision,
                'recall_score': recall,
                'f1_score': f1,
                'train_accuracy': train_accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_names': self.feature_names,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'config': {
                    'algorithm': 'random_forest',
                    'n_estimators': self.model.n_estimators,
                    'max_depth': self.model.max_depth,
                    'features': self.feature_names
                },
                'is_active': True
            }
            
            logger.info(
                "Weather model training completed",
                accuracy=test_accuracy,
                f1=f1,
                training_samples=len(X_train)
            )
            
            return model_info
            
        except Exception as e:
            logger.error("Weather model training failed", error=str(e))
            raise
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict weather-related disruption"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        try:
            # Convert features to model format
            feature_row = {
                'departure_hour': self._extract_hour(features.get('scheduled_departure')),
                'month': self._extract_month(features.get('scheduled_departure')),
                'visibility_km': self._parse_visibility(
                    features.get('weather_data', {}).get('visibility', '10000m')
                ),
                'wind_speed_kt': self._parse_wind_speed(
                    features.get('weather_data', {}).get('wind_speed', '5kt')
                ),
                'temperature_c': self._parse_temperature(
                    features.get('weather_data', {}).get('temperature', '15C')
                ),
                'has_precipitation': 1 if features.get('weather_data', {}).get(
                    'precipitation', 'none'
                ) != 'none' else 0,
                'route_type': self._classify_route_type(
                    features.get('departure_airport', 'UNK'),
                    features.get('arrival_airport', 'UNK')
                ),
                'is_weekend': self._is_weekend(features.get('scheduled_departure')),
                'is_winter': 1 if self._extract_month(
                    features.get('scheduled_departure')
                ) in [11, 12, 1, 2] else 0,
            }
            
            # Create DataFrame with correct feature order
            df = pd.DataFrame([feature_row])[self.feature_names]
            
            # Scale features
            X_scaled = self.scaler.transform(df)
            
            # Predict
            probability = self.model.predict_proba(X_scaled)[0]
            prediction = self.model.predict(X_scaled)[0]
            
            return {
                'weather_disruption_risk': float(probability[1] if len(probability) > 1 else 0.5),
                'predicted_weather_disruption': bool(prediction),
                'confidence': float(max(probability)),
                'features_used': self.feature_names
            }
            
        except Exception as e:
            logger.error("Weather prediction failed", error=str(e))
            return {'weather_disruption_risk': 0.3, 'predicted_weather_disruption': False}
    
    # Helper methods
    def _extract_hour(self, timestamp) -> int:
        """Extract hour from timestamp"""
        try:
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
            elif hasattr(timestamp, 'hour'):
                return timestamp.hour
            return 12  # Default
        except:
            return 12
    
    def _extract_month(self, timestamp) -> int:
        """Extract month from timestamp"""
        try:
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).month
            elif hasattr(timestamp, 'month'):
                return timestamp.month
            return 6  # Default
        except:
            return 6
    
    def _parse_visibility(self, visibility_str: str) -> float:
        """Parse visibility string to kilometers"""
        try:
            if 'km' in visibility_str:
                return float(visibility_str.replace('km', ''))
            elif 'm' in visibility_str:
                return float(visibility_str.replace('m', '')) / 1000.0
            return 10.0  # Default good visibility
        except:
            return 10.0
    
    def _parse_wind_speed(self, wind_str: str) -> float:
        """Parse wind speed string to knots"""
        try:
            if 'kt' in wind_str:
                return float(wind_str.replace('kt', ''))
            elif 'mph' in wind_str:
                return float(wind_str.replace('mph', '')) * 0.868976
            return 5.0  # Default light wind
        except:
            return 5.0
    
    def _parse_temperature(self, temp_str: str) -> float:
        """Parse temperature string to Celsius"""
        try:
            if 'C' in temp_str:
                return float(temp_str.replace('C', ''))
            elif 'F' in temp_str:
                return (float(temp_str.replace('F', '')) - 32) * 5/9
            return 15.0  # Default temperature
        except:
            return 15.0
    
    def _classify_route_type(self, departure: str, arrival: str) -> int:
        """Classify route type (0=domestic, 1=short-haul, 2=long-haul)"""
        # Simple classification based on airport codes
        uk_airports = {'LHR', 'LGW', 'STN', 'MAN', 'EDI', 'BHX', 'GLA'}
        european_airports = {'CDG', 'AMS', 'FRA', 'MAD', 'FCO', 'BCN'}
        
        if departure in uk_airports and arrival in uk_airports:
            return 0  # Domestic
        elif departure in uk_airports and arrival in european_airports:
            return 1  # Short-haul
        elif departure in european_airports and arrival in uk_airports:
            return 1  # Short-haul
        else:
            return 2  # Long-haul
    
    def _is_weekend(self, timestamp) -> int:
        """Check if timestamp is weekend"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            return 1 if dt.weekday() >= 5 else 0
        except:
            return 0

class TechnicalPredictor(BasePredictor):
    """ML model for technical disruption prediction"""
    
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            random_state=42
        )
        self.scaler = StandardScaler()
    
    def preprocess_features(self, data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
        """Preprocess data for technical disruption prediction"""
        features = []
        targets = []
        
        for record in data:
            try:
                # Aircraft features
                aircraft_type = record.get('aircraft_type', 'Unknown')
                aircraft_age = self._estimate_aircraft_age(aircraft_type)
                
                # Flight features
                flight_duration = self._estimate_flight_duration(
                    record.get('scheduled_departure'),
                    record.get('scheduled_arrival')
                )
                
                feature_row = {
                    'aircraft_age_years': aircraft_age,
                    'flight_duration_hours': flight_duration,
                    'is_boeing': 1 if 'boeing' in aircraft_type.lower() or '737' in aircraft_type or '777' in aircraft_type else 0,
                    'is_airbus': 1 if 'airbus' in aircraft_type.lower() or 'a320' in aircraft_type.lower() or 'a350' in aircraft_type.lower() else 0,
                    'departure_hour': self._extract_hour(record.get('scheduled_departure')),
                    'is_long_haul': 1 if flight_duration > 6 else 0,
                }
                
                features.append(feature_row)
                
                # Target: technical disruption severity
                disruption_type = record.get('disruption_type', 'none')
                delay_minutes = record.get('delay_minutes', 0) if disruption_type == 'technical' else 0
                targets.append(delay_minutes)
                
            except Exception as e:
                logger.warning("Failed to process technical record", error=str(e))
                continue
        
        if not features:
            raise ValueError("No valid features extracted")
        
        df_features = pd.DataFrame(features)
        self.feature_names = df_features.columns.tolist()
        
        return df_features, pd.Series(targets)
    
    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train technical disruption model"""
        try:
            logger.info("Training technical prediction model", data_size=len(training_data))
            
            # Preprocess data
            X, y = self.preprocess_features(training_data)
            
            if len(X) < 10:
                raise ValueError("Insufficient training data")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Predictions for classification metrics
            train_pred = self.model.predict(X_train_scaled)
            test_pred = self.model.predict(X_test_scaled)
            
            # Convert to binary classification for metrics (>30 min delay = disruption)
            y_train_binary = (y_train > 30).astype(int)
            y_test_binary = (y_test > 30).astype(int)
            train_pred_binary = (train_pred > 30).astype(int)
            test_pred_binary = (test_pred > 30).astype(int)
            
            precision = precision_score(y_test_binary, test_pred_binary, zero_division=0)
            recall = recall_score(y_test_binary, test_pred_binary, zero_division=0)
            f1 = f1_score(y_test_binary, test_pred_binary, zero_division=0)
            
            self.is_trained = True
            
            model_info = {
                'model_name': 'TechnicalFailurePredictor',
                'model_version': '1.8.2',
                'model_type': 'technical',
                'accuracy_score': test_score,
                'precision_score': precision,
                'recall_score': recall,
                'f1_score': f1,
                'train_score': train_score,
                'feature_names': self.feature_names,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'config': {
                    'algorithm': 'gradient_boosting',
                    'n_estimators': self.model.n_estimators,
                    'learning_rate': self.model.learning_rate,
                    'features': self.feature_names
                },
                'is_active': True
            }
            
            logger.info(
                "Technical model training completed",
                r2_score=test_score,
                f1=f1,
                training_samples=len(X_train)
            )
            
            return model_info
            
        except Exception as e:
            logger.error("Technical model training failed", error=str(e))
            raise
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict technical disruption"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        try:
            aircraft_type = features.get('aircraft_type', 'Unknown')
            
            feature_row = {
                'aircraft_age_years': self._estimate_aircraft_age(aircraft_type),
                'flight_duration_hours': self._estimate_flight_duration(
                    features.get('scheduled_departure'),
                    features.get('scheduled_arrival')
                ),
                'is_boeing': 1 if 'boeing' in aircraft_type.lower() or '737' in aircraft_type or '777' in aircraft_type else 0,
                'is_airbus': 1 if 'airbus' in aircraft_type.lower() or 'a320' in aircraft_type.lower() or 'a350' in aircraft_type.lower() else 0,
                'departure_hour': self._extract_hour(features.get('scheduled_departure')),
                'is_long_haul': 1 if self._estimate_flight_duration(
                    features.get('scheduled_departure'),
                    features.get('scheduled_arrival')
                ) > 6 else 0,
            }
            
            # Create DataFrame with correct feature order
            df = pd.DataFrame([feature_row])[self.feature_names]
            
            # Scale features
            X_scaled = self.scaler.transform(df)
            
            # Predict delay minutes
            predicted_delay = self.model.predict(X_scaled)[0]
            
            return {
                'technical_delay_minutes': max(0, float(predicted_delay)),
                'technical_disruption_risk': min(1.0, float(predicted_delay) / 120.0),  # Scale to 0-1
                'predicted_technical_disruption': predicted_delay > 30,
                'features_used': self.feature_names
            }
            
        except Exception as e:
            logger.error("Technical prediction failed", error=str(e))
            return {'technical_disruption_risk': 0.2, 'predicted_technical_disruption': False}
    
    # Helper methods
    def _extract_hour(self, timestamp) -> int:
        """Extract hour from timestamp"""
        try:
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
            elif hasattr(timestamp, 'hour'):
                return timestamp.hour
            return 12  # Default
        except:
            return 12
    
    def _estimate_aircraft_age(self, aircraft_type: str) -> float:
        """Estimate aircraft age based on type (mock implementation)"""
        # Simple age estimation based on aircraft type
        age_map = {
            'boeing 737-800': 15,
            'boeing 777-200': 18,
            'boeing 787-9': 8,
            'airbus a320-200': 12,
            'airbus a350-1000': 5,
            'airbus a380-800': 15
        }
        
        for aircraft, age in age_map.items():
            if aircraft.lower() in aircraft_type.lower():
                return float(age)
        
        return 10.0  # Default age
    
    def _estimate_flight_duration(self, departure_time, arrival_time) -> float:
        """Estimate flight duration in hours"""
        try:
            if isinstance(departure_time, str):
                dep = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            else:
                dep = departure_time
                
            if isinstance(arrival_time, str):
                arr = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            else:
                arr = arrival_time
            
            duration = arr - dep
            return duration.total_seconds() / 3600.0
        except:
            return 2.0  # Default 2 hours

class DisruptionPredictor:
    """Combined disruption prediction model"""
    
    def __init__(self):
        self.weather_predictor = WeatherPredictor()
        self.technical_predictor = TechnicalPredictor()
        self.is_trained = False
    
    async def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Train all sub-models"""
        try:
            logger.info("Training combined disruption predictor")
            
            # Train weather model
            weather_info = await self.weather_predictor.train(training_data)
            
            # Train technical model
            technical_info = await self.technical_predictor.train(training_data)
            
            self.is_trained = True
            
            return {
                'models': [weather_info, technical_info],
                'combined_predictor': {
                    'name': 'CombinedDisruptionPredictor',
                    'version': '1.0.0',
                    'sub_models': ['weather', 'technical'],
                    'is_trained': True
                }
            }
            
        except Exception as e:
            logger.error("Combined model training failed", error=str(e))
            raise
    
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make combined prediction"""
        if not self.is_trained:
            raise ValueError("Models not trained")
        
        try:
            # Get predictions from sub-models
            weather_pred = await self.weather_predictor.predict(features)
            technical_pred = await self.technical_predictor.predict(features)
            
            # Combine predictions
            weather_risk = weather_pred.get('weather_disruption_risk', 0.0)
            technical_risk = technical_pred.get('technical_disruption_risk', 0.0)
            
            # Overall risk (max of individual risks with some combination)
            combined_risk = max(weather_risk, technical_risk) + 0.1 * min(weather_risk, technical_risk)
            combined_risk = min(1.0, combined_risk)
            
            # Determine primary disruption type
            if weather_risk > technical_risk and weather_risk > 0.3:
                primary_type = 'weather'
                predicted_delay = int(weather_risk * 120)  # Scale to minutes
            elif technical_risk > 0.3:
                primary_type = 'technical'
                predicted_delay = int(technical_pred.get('technical_delay_minutes', 0))
            else:
                primary_type = 'none'
                predicted_delay = 0
            
            return {
                'combined_risk_score': combined_risk,
                'weather_risk': weather_risk,
                'technical_risk': technical_risk,
                'primary_disruption_type': primary_type,
                'predicted_delay_minutes': predicted_delay,
                'weather_prediction': weather_pred,
                'technical_prediction': technical_pred
            }
            
        except Exception as e:
            logger.error("Combined prediction failed", error=str(e))
            return {
                'combined_risk_score': 0.3,
                'primary_disruption_type': 'none',
                'predicted_delay_minutes': 0
            }