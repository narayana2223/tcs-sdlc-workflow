"""
Time Series Forecasting Models for Flight Disruption Prediction

This module implements various time series forecasting models for predicting
flight disruptions, delays, and operational patterns with 2-4 hour advance notice.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import uuid

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb

from .base_models import (
    TimeSeriesModel, PredictionResult, ModelMetrics, 
    DisruptionType, SeverityLevel
)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class XGBoostTimeSeriesModel(TimeSeriesModel):
    """XGBoost-based time series forecasting model"""
    
    def __init__(self, 
                 model_name: str = "xgboost_timeseries",
                 forecast_horizon_minutes: int = 240,
                 **kwargs):
        
        super().__init__(model_name, forecast_horizon_minutes, **kwargs)
        
        # XGBoost parameters
        self.xgb_params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        self.xgb_params.update(kwargs.get('xgb_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for XGBoost time series model"""
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'delay_minutes']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Required columns missing: {required_cols}")
        
        data = data.copy()
        data = data.sort_values('timestamp')
        
        # Create time-based features
        data = self.create_time_features(data, 'timestamp')
        
        # Create lag features
        data = self.create_lag_features(data, 'delay_minutes', lags=[1, 2, 3, 6, 12, 24])
        
        # Weather features (if available)
        if 'weather_score' in data.columns:
            data = self.create_lag_features(data, 'weather_score', lags=[1, 2, 3, 6])
        
        # Airport congestion features (if available)
        if 'airport_congestion' in data.columns:
            data = self.create_lag_features(data, 'airport_congestion', lags=[1, 2, 4, 8])
        
        # Flight density features
        if 'flights_per_hour' in data.columns:
            data = self.create_lag_features(data, 'flights_per_hour', lags=[1, 2, 4])
        
        # Aircraft type features (if available)
        if 'aircraft_type' in data.columns:
            data = self.encode_categorical_features(data, ['aircraft_type'], is_training=True)
        
        # Route features (if available)
        if 'route' in data.columns:
            data = self.encode_categorical_features(data, ['route'], is_training=True)
        
        # Remove rows with NaN values (due to lag features)
        data = data.dropna()
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'delay_minutes',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train XGBoost time series model"""
        
        self.logger.info(f"Training {self.model_name} model")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns (exclude timestamp, target, and non-feature columns)
        exclude_cols = ['timestamp', target_column, 'flight_id', 'aircraft_id']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols and not col.startswith('timestamp')]
        
        # Split features and target
        X = prepared_data[self.feature_columns]
        y = prepared_data[target_column]
        
        # Train-validation split
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        
        # Create and train XGBoost model
        self.model = xgb.XGBRegressor(**self.xgb_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate on validation set
        y_pred = self.model.predict(X_val)
        
        # Calculate metrics
        mae = mean_absolute_error(y_val, y_pred)
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        
        # Calculate custom metrics
        accuracy_1h = self._calculate_forecast_accuracy(y_val, y_pred, threshold_minutes=60)
        accuracy_4h = self._calculate_forecast_accuracy(y_val, y_pred, threshold_minutes=240)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse,
            prediction_accuracy_1hour=accuracy_1h,
            prediction_accuracy_4hour=accuracy_4h
        )
        
        self.logger.info(f"Model training completed. MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Make delay predictions"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        predictions = self.model.predict(X)
        
        # Get prediction confidence (using feature importance and historical accuracy)
        feature_importance = self.get_feature_importance()
        base_confidence = 0.85  # Historical model accuracy
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            pred_value = max(0, predictions[idx])  # Ensure non-negative delays
            
            # Determine disruption type based on features and prediction
            disruption_type = self._determine_disruption_type(row, pred_value)
            
            # Calculate confidence
            confidence = self.calculate_prediction_confidence(
                pred_value, 
                historical_accuracy=base_confidence
            )
            
            # Determine severity
            severity = self.determine_severity(
                pred_value, 
                disruption_type,
                affected_passengers=row.get('affected_passengers')
            )
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=float(pred_value),
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                forecast_horizon_minutes=self.forecast_horizon_minutes,
                affected_flights=[row.get('flight_id', 'unknown')],
                estimated_impact_cost=self._estimate_cost_impact(pred_value, severity)
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'delay_minutes') -> ModelMetrics:
        """Evaluate model performance"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        y_true = prepared_data[target_column]
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        
        # Custom metrics
        accuracy_1h = self._calculate_forecast_accuracy(y_true, y_pred, threshold_minutes=60)
        accuracy_4h = self._calculate_forecast_accuracy(y_true, y_pred, threshold_minutes=240)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse,
            prediction_accuracy_1hour=accuracy_1h,
            prediction_accuracy_4hour=accuracy_4h
        )
    
    def _calculate_forecast_accuracy(self, 
                                   y_true: np.ndarray, 
                                   y_pred: np.ndarray, 
                                   threshold_minutes: float = 60) -> float:
        """Calculate forecast accuracy within a threshold"""
        
        accuracy = np.mean(np.abs(y_true - y_pred) <= threshold_minutes)
        return float(accuracy)
    
    def _determine_disruption_type(self, row: pd.Series, predicted_delay: float) -> DisruptionType:
        """Determine likely disruption type based on features"""
        
        # Check weather features
        if 'weather_score' in row and row['weather_score'] > 0.7:
            return DisruptionType.WEATHER
        
        # Check airport congestion
        if 'airport_congestion' in row and row['airport_congestion'] > 0.8:
            return DisruptionType.AIRPORT_CONGESTION
        
        # Check time patterns for ATC delays
        if 'is_peak_hour' in row and row['is_peak_hour'] == 1:
            return DisruptionType.ATC
        
        # Default based on delay magnitude
        if predicted_delay > 120:
            return DisruptionType.TECHNICAL
        else:
            return DisruptionType.AIRLINE_OPERATIONAL
    
    def _estimate_cost_impact(self, predicted_delay: float, severity: SeverityLevel) -> float:
        """Estimate cost impact of predicted delay"""
        
        # Base cost per minute of delay
        cost_per_minute = 15.0  # GBP
        
        # Severity multipliers
        severity_multipliers = {
            SeverityLevel.LOW: 1.0,
            SeverityLevel.MEDIUM: 1.5,
            SeverityLevel.HIGH: 2.5,
            SeverityLevel.CRITICAL: 4.0,
            SeverityLevel.EMERGENCY: 6.0
        }
        
        multiplier = severity_multipliers.get(severity, 1.0)
        estimated_cost = predicted_delay * cost_per_minute * multiplier
        
        return float(estimated_cost)


class LSTMForecastingModel(TimeSeriesModel):
    """LSTM-based time series forecasting model for flight disruptions"""
    
    def __init__(self, 
                 model_name: str = "lstm_forecasting",
                 forecast_horizon_minutes: int = 240,
                 sequence_length: int = 24,  # Look back 24 hours
                 **kwargs):
        
        super().__init__(model_name, forecast_horizon_minutes, **kwargs)
        
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM models")
        
        self.sequence_length = sequence_length
        
        # LSTM parameters
        self.lstm_params = {
            'units': 50,
            'dropout': 0.2,
            'recurrent_dropout': 0.2,
            'learning_rate': 0.001,
            'epochs': 100,
            'batch_size': 32
        }
        self.lstm_params.update(kwargs.get('lstm_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for LSTM model"""
        
        data = data.copy()
        data = data.sort_values('timestamp')
        
        # Create time-based features
        data = self.create_time_features(data, 'timestamp')
        
        # Normalize continuous features
        continuous_features = ['delay_minutes', 'weather_score', 'airport_congestion', 'flights_per_hour']
        for feature in continuous_features:
            if feature in data.columns:
                data[f'{feature}_normalized'] = (data[feature] - data[feature].mean()) / data[feature].std()
        
        return data
    
    def create_sequences(self, data: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        
        # Select features for sequence creation
        feature_cols = [col for col in data.columns 
                       if col.endswith('_normalized') or col in ['hour', 'day_of_week', 'is_peak_hour']]
        
        sequences = []
        targets = []
        
        for i in range(len(data) - self.sequence_length):
            # Input sequence
            seq = data[feature_cols].iloc[i:i+self.sequence_length].values
            sequences.append(seq)
            
            # Target (next value)
            target = data[target_column].iloc[i+self.sequence_length]
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'delay_minutes',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train LSTM model"""
        
        self.logger.info(f"Training {self.model_name} model")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        # Create sequences
        X, y = self.create_sequences(prepared_data, target_column)
        
        if len(X) == 0:
            raise ValueError("No sequences available for training")
        
        # Train-validation split
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Build LSTM model
        self.model = Sequential([
            LSTM(self.lstm_params['units'], 
                 return_sequences=True,
                 input_shape=(X.shape[1], X.shape[2]),
                 dropout=self.lstm_params['dropout'],
                 recurrent_dropout=self.lstm_params['recurrent_dropout']),
            LSTM(self.lstm_params['units'] // 2,
                 dropout=self.lstm_params['dropout'],
                 recurrent_dropout=self.lstm_params['recurrent_dropout']),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        # Compile model
        optimizer = Adam(learning_rate=self.lstm_params['learning_rate'])
        self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=self.lstm_params['epochs'],
            batch_size=self.lstm_params['batch_size'],
            validation_data=(X_val, y_val),
            verbose=0
        )
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val, verbose=0)
        mae = mean_absolute_error(y_val, y_pred)
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        
        # Calculate custom metrics
        accuracy_1h = self._calculate_forecast_accuracy(y_val, y_pred.flatten(), threshold_minutes=60)
        accuracy_4h = self._calculate_forecast_accuracy(y_val, y_pred.flatten(), threshold_minutes=240)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse,
            prediction_accuracy_1hour=accuracy_1h,
            prediction_accuracy_4hour=accuracy_4h
        )
        
        self.logger.info(f"LSTM training completed. MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Make predictions using LSTM model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if len(prepared_data) < self.sequence_length:
            self.logger.warning("Insufficient data for LSTM prediction")
            return []
        
        # Create sequences for prediction
        X, _ = self.create_sequences(prepared_data, self.target_column or 'delay_minutes')
        
        if len(X) == 0:
            return []
        
        # Make predictions
        predictions = self.model.predict(X, verbose=0)
        
        results = []
        for idx, pred in enumerate(predictions):
            pred_value = max(0, float(pred[0]))  # Ensure non-negative
            
            # Determine disruption type and severity
            row_idx = idx + self.sequence_length
            if row_idx < len(prepared_data):
                row = prepared_data.iloc[row_idx]
                disruption_type = self._determine_disruption_type(row, pred_value)
                severity = self.determine_severity(pred_value, disruption_type)
                
                result = PredictionResult(
                    prediction_id=str(uuid.uuid4()),
                    model_name=self.model_name,
                    prediction_timestamp=datetime.now(),
                    prediction_value=pred_value,
                    confidence=0.80,  # Base LSTM confidence
                    severity=severity,
                    disruption_type=disruption_type,
                    features_used=[f"lstm_sequence_{self.sequence_length}"],
                    model_version=self.model_version,
                    forecast_horizon_minutes=self.forecast_horizon_minutes
                )
                
                results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'delay_minutes') -> ModelMetrics:
        """Evaluate LSTM model performance"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        X, y_true = self.create_sequences(prepared_data, target_column)
        
        if len(X) == 0:
            raise ValueError("No sequences available for evaluation")
        
        # Make predictions
        y_pred = self.model.predict(X, verbose=0).flatten()
        
        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        
        accuracy_1h = self._calculate_forecast_accuracy(y_true, y_pred, threshold_minutes=60)
        accuracy_4h = self._calculate_forecast_accuracy(y_true, y_pred, threshold_minutes=240)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse,
            prediction_accuracy_1hour=accuracy_1h,
            prediction_accuracy_4hour=accuracy_4h
        )
    
    def _calculate_forecast_accuracy(self, 
                                   y_true: np.ndarray, 
                                   y_pred: np.ndarray, 
                                   threshold_minutes: float = 60) -> float:
        """Calculate forecast accuracy within threshold"""
        accuracy = np.mean(np.abs(y_true - y_pred) <= threshold_minutes)
        return float(accuracy)
    
    def _determine_disruption_type(self, row: pd.Series, predicted_delay: float) -> DisruptionType:
        """Determine disruption type from LSTM features"""
        
        # Simple heuristic based on available features
        if 'weather_score_normalized' in row and row['weather_score_normalized'] > 1.0:
            return DisruptionType.WEATHER
        elif 'is_peak_hour' in row and row['is_peak_hour'] == 1:
            return DisruptionType.ATC
        elif predicted_delay > 180:
            return DisruptionType.TECHNICAL
        else:
            return DisruptionType.AIRLINE_OPERATIONAL


class WeatherImpactModel(TimeSeriesModel):
    """Specialized model for weather impact on flight operations"""
    
    def __init__(self, 
                 model_name: str = "weather_impact",
                 forecast_horizon_minutes: int = 240,
                 **kwargs):
        
        super().__init__(model_name, forecast_horizon_minutes, **kwargs)
        
        # Weather-specific parameters
        self.weather_features = [
            'temperature', 'humidity', 'pressure', 
            'wind_speed', 'wind_direction', 'visibility',
            'precipitation', 'cloud_cover', 'weather_severity_score'
        ]
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare weather-specific features"""
        
        data = data.copy()
        data = data.sort_values('timestamp')
        
        # Create time features
        data = self.create_time_features(data, 'timestamp')
        
        # Weather interaction features
        if 'wind_speed' in data.columns and 'precipitation' in data.columns:
            data['adverse_weather_score'] = (
                (data['wind_speed'] > 30).astype(int) +
                (data['precipitation'] > 5).astype(int) +
                (data['visibility'] < 1000).astype(int)
            )
        
        # Seasonal weather patterns
        if 'month' in data.columns:
            data['is_winter'] = data['month'].isin([12, 1, 2]).astype(int)
            data['is_storm_season'] = data['month'].isin([6, 7, 8, 9]).astype(int)
        
        # Airport-specific weather features
        if 'airport_code' in data.columns:
            # Create dummy variables for major airports
            major_airports = ['LHR', 'CDG', 'FRA', 'AMS', 'BCN']
            for airport in major_airports:
                data[f'is_{airport}'] = (data['airport_code'] == airport).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'weather_delay_minutes',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train weather impact model"""
        
        self.logger.info("Training weather impact model")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        # Select weather-related features
        available_weather_features = [f for f in self.weather_features if f in prepared_data.columns]
        time_features = ['hour', 'day_of_week', 'month', 'is_peak_hour', 'is_weekend']
        airport_features = [col for col in prepared_data.columns if col.startswith('is_') and len(col) == 6]
        
        self.feature_columns = available_weather_features + time_features + airport_features + ['adverse_weather_score']
        self.feature_columns = [col for col in self.feature_columns if col in prepared_data.columns]
        
        # Remove rows with missing weather data
        prepared_data = prepared_data.dropna(subset=self.feature_columns)
        
        if prepared_data.empty:
            raise ValueError("No data available after removing missing weather data")
        
        # Split data
        X = prepared_data[self.feature_columns]
        y = prepared_data[target_column]
        
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Use Random Forest for weather impact (handles non-linear relationships well)
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse
        )
        
        self.logger.info(f"Weather model training completed. MAE: {mae:.2f} minutes")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict weather-related delays"""
        
        if not self.is_trained:
            raise ValueError("Weather model must be trained first")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        predictions = self.model.predict(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            pred_value = max(0, predictions[idx])
            
            # Weather delays are always weather disruption type
            disruption_type = DisruptionType.WEATHER
            severity = self.determine_severity(pred_value, disruption_type)
            
            # Higher confidence for weather predictions due to specialized model
            confidence = 0.88
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=float(pred_value),
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                forecast_horizon_minutes=self.forecast_horizon_minutes,
                affected_flights=[row.get('flight_id', 'unknown')]
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'weather_delay_minutes') -> ModelMetrics:
        """Evaluate weather model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns]
        y_true = prepared_data[target_column]
        y_pred = self.model.predict(X)
        
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            mae=mae,
            mse=mse,
            rmse=rmse
        )


# Model ensemble for combining multiple forecasting approaches
class TimeSeriesEnsemble:
    """Ensemble of time series models for robust predictions"""
    
    def __init__(self, models: List[TimeSeriesModel], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)
        
        if len(self.weights) != len(self.models):
            raise ValueError("Number of weights must match number of models")
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Make ensemble predictions"""
        
        all_predictions = []
        for model in self.models:
            if model.is_trained:
                predictions = model.predict(data)
                all_predictions.append(predictions)
        
        if not all_predictions:
            return []
        
        # Combine predictions using weighted average
        ensemble_results = []
        min_length = min(len(preds) for preds in all_predictions)
        
        for i in range(min_length):
            # Get predictions from all models for this data point
            model_predictions = [preds[i].prediction_value for preds in all_predictions]
            model_confidences = [preds[i].confidence for preds in all_predictions]
            
            # Weighted average
            weighted_prediction = sum(pred * weight for pred, weight in zip(model_predictions, self.weights))
            weighted_confidence = sum(conf * weight for conf, weight in zip(model_confidences, self.weights))
            
            # Use the first model's metadata as base
            base_result = all_predictions[0][i]
            
            ensemble_result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name="time_series_ensemble",
                prediction_timestamp=datetime.now(),
                prediction_value=weighted_prediction,
                confidence=weighted_confidence,
                severity=base_result.severity,
                disruption_type=base_result.disruption_type,
                features_used=["ensemble_of_models"],
                model_version="1.0.0",
                forecast_horizon_minutes=base_result.forecast_horizon_minutes,
                affected_flights=base_result.affected_flights
            )
            
            ensemble_results.append(ensemble_result)
        
        return ensemble_results