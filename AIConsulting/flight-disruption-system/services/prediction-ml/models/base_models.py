"""
Base ML Models for Flight Disruption Prediction

This module provides the foundation classes and interfaces for all machine learning
models used in disruption prediction, including time series forecasting, classification,
regression, and clustering models.
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import joblib

import sklearn
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, classification_report, silhouette_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import xgboost as xgb

logger = logging.getLogger(__name__)


class DisruptionType(Enum):
    """Types of flight disruptions"""
    WEATHER = "weather"
    TECHNICAL = "technical"
    CREW = "crew"
    AIRPORT_CONGESTION = "airport_congestion"
    ATC = "air_traffic_control"
    SECURITY = "security"
    AIRLINE_OPERATIONAL = "airline_operational"
    EXTERNAL = "external"


class SeverityLevel(Enum):
    """Severity levels for disruptions"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class PredictionResult:
    """Results from ML prediction models"""
    prediction_id: str
    model_name: str
    prediction_timestamp: datetime
    prediction_value: Union[float, str, int]
    confidence: float
    severity: SeverityLevel
    disruption_type: DisruptionType
    features_used: List[str]
    model_version: str
    
    # Additional metadata
    forecast_horizon_minutes: Optional[int] = None
    affected_flights: Optional[List[str]] = None
    affected_passengers: Optional[int] = None
    estimated_impact_cost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "prediction_id": self.prediction_id,
            "model_name": self.model_name,
            "prediction_timestamp": self.prediction_timestamp.isoformat(),
            "prediction_value": self.prediction_value,
            "confidence": self.confidence,
            "severity": self.severity.value,
            "disruption_type": self.disruption_type.value,
            "features_used": self.features_used,
            "model_version": self.model_version,
            "forecast_horizon_minutes": self.forecast_horizon_minutes,
            "affected_flights": self.affected_flights,
            "affected_passengers": self.affected_passengers,
            "estimated_impact_cost": self.estimated_impact_cost
        }


@dataclass
class ModelMetrics:
    """Performance metrics for ML models"""
    model_name: str
    model_version: str
    evaluation_timestamp: datetime
    
    # Common metrics
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Regression metrics
    mae: Optional[float] = None  # Mean Absolute Error
    mse: Optional[float] = None  # Mean Squared Error
    rmse: Optional[float] = None  # Root Mean Squared Error
    r2_score: Optional[float] = None
    
    # Clustering metrics
    silhouette_score: Optional[float] = None
    inertia: Optional[float] = None
    
    # Custom metrics
    prediction_accuracy_1hour: Optional[float] = None
    prediction_accuracy_4hour: Optional[float] = None
    cost_impact_accuracy: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BaseMLModel(ABC):
    """Abstract base class for all ML models in the system"""
    
    def __init__(self, 
                 model_name: str,
                 model_version: str = "1.0.0",
                 model_path: Optional[str] = None):
        
        self.model_name = model_name
        self.model_version = model_version
        self.model_path = model_path or f"models/{model_name}_v{model_version}.pkl"
        
        self.model: Optional[BaseEstimator] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        
        self.is_trained = False
        self.last_updated = None
        self.feature_columns = []
        self.target_column = None
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup model-specific logging"""
        self.logger = logging.getLogger(f"{__name__}.{self.model_name}")
    
    @abstractmethod
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for training or prediction"""
        pass
    
    @abstractmethod
    def train(self, 
              data: pd.DataFrame, 
              target_column: str,
              validation_split: float = 0.2) -> ModelMetrics:
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Make predictions"""
        pass
    
    @abstractmethod
    def evaluate(self, data: pd.DataFrame, target_column: str) -> ModelMetrics:
        """Evaluate model performance"""
        pass
    
    def save_model(self, path: Optional[str] = None) -> str:
        """Save the trained model"""
        save_path = path or self.model_path
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'last_updated': datetime.now(),
            'is_trained': self.is_trained
        }
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.logger.info(f"Model saved to {save_path}")
        return save_path
    
    def load_model(self, path: Optional[str] = None) -> bool:
        """Load a trained model"""
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            self.logger.warning(f"Model file not found: {load_path}")
            return False
        
        try:
            with open(load_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data.get('scaler')
            self.label_encoder = model_data.get('label_encoder')
            self.feature_columns = model_data['feature_columns']
            self.target_column = model_data.get('target_column')
            self.last_updated = model_data.get('last_updated')
            self.is_trained = model_data.get('is_trained', False)
            
            self.logger.info(f"Model loaded from {load_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance if available"""
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importance_dict = {}
        if hasattr(self.model, 'feature_importances_') and len(self.feature_columns) == len(self.model.feature_importances_):
            importance_dict = dict(zip(self.feature_columns, self.model.feature_importances_))
        
        # Sort by importance
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate input data"""
        errors = []
        
        # Check if data is empty
        if data.empty:
            errors.append("Input data is empty")
        
        # Check for required columns
        missing_cols = set(self.feature_columns) - set(data.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check for null values in critical columns
        critical_nulls = data[self.feature_columns].isnull().sum()
        if critical_nulls.any():
            null_cols = critical_nulls[critical_nulls > 0].index.tolist()
            errors.append(f"Null values in critical columns: {null_cols}")
        
        return len(errors) == 0, errors
    
    def preprocess_data(self, data: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        """Standard data preprocessing"""
        processed_data = data.copy()
        
        # Handle missing values
        processed_data = processed_data.fillna(processed_data.median(numeric_only=True))
        processed_data = processed_data.fillna(processed_data.mode().iloc[0] if not processed_data.mode().empty else 0)
        
        # Feature scaling
        if self.scaler is None and is_training:
            self.scaler = StandardScaler()
            numeric_cols = processed_data.select_dtypes(include=[np.number]).columns
            processed_data[numeric_cols] = self.scaler.fit_transform(processed_data[numeric_cols])
        elif self.scaler is not None:
            numeric_cols = processed_data.select_dtypes(include=[np.number]).columns
            processed_data[numeric_cols] = self.scaler.transform(processed_data[numeric_cols])
        
        return processed_data
    
    def calculate_prediction_confidence(self, 
                                      prediction: Union[np.ndarray, float],
                                      prediction_proba: Optional[np.ndarray] = None,
                                      historical_accuracy: float = 0.85) -> float:
        """Calculate prediction confidence score"""
        
        base_confidence = historical_accuracy
        
        # Adjust based on prediction probability if available
        if prediction_proba is not None:
            if len(prediction_proba.shape) > 1:
                # Multi-class case - use max probability
                max_proba = np.max(prediction_proba, axis=1).mean()
            else:
                # Binary case
                max_proba = np.max(prediction_proba)
            
            # Combine base confidence with prediction probability
            confidence = (base_confidence * 0.3) + (max_proba * 0.7)
        else:
            confidence = base_confidence
        
        # Ensure confidence is between 0 and 1
        return np.clip(confidence, 0.0, 1.0)
    
    def determine_severity(self, 
                          prediction_value: Union[float, int],
                          disruption_type: DisruptionType,
                          affected_passengers: Optional[int] = None) -> SeverityLevel:
        """Determine severity level based on prediction and context"""
        
        # Base severity mapping for different disruption types
        severity_thresholds = {
            DisruptionType.WEATHER: {
                SeverityLevel.LOW: 30,      # minutes delay
                SeverityLevel.MEDIUM: 90,
                SeverityLevel.HIGH: 180,
                SeverityLevel.CRITICAL: 360,
            },
            DisruptionType.TECHNICAL: {
                SeverityLevel.LOW: 45,
                SeverityLevel.MEDIUM: 120,
                SeverityLevel.HIGH: 240,
                SeverityLevel.CRITICAL: 480,
            },
            DisruptionType.CREW: {
                SeverityLevel.LOW: 60,
                SeverityLevel.MEDIUM: 180,
                SeverityLevel.HIGH: 360,
                SeverityLevel.CRITICAL: 720,
            },
            DisruptionType.AIRPORT_CONGESTION: {
                SeverityLevel.LOW: 30,
                SeverityLevel.MEDIUM: 120,
                SeverityLevel.HIGH: 300,
                SeverityLevel.CRITICAL: 600,
            }
        }
        
        # Get thresholds for disruption type
        thresholds = severity_thresholds.get(disruption_type, severity_thresholds[DisruptionType.TECHNICAL])
        
        # Determine base severity
        severity = SeverityLevel.LOW
        for level, threshold in thresholds.items():
            if prediction_value >= threshold:
                severity = level
            else:
                break
        
        # Adjust based on affected passengers
        if affected_passengers:
            if affected_passengers > 1000 and severity.value < SeverityLevel.CRITICAL.value:
                severity = SeverityLevel(severity.value + 1)
            elif affected_passengers > 500 and severity.value < SeverityLevel.HIGH.value:
                severity = SeverityLevel(severity.value + 1)
        
        return severity


class TimeSeriesModel(BaseMLModel):
    """Base class for time series forecasting models"""
    
    def __init__(self, 
                 model_name: str,
                 forecast_horizon_minutes: int = 240,  # 4 hours
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        self.forecast_horizon_minutes = forecast_horizon_minutes
    
    def create_time_features(self, data: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
        """Create time-based features from timestamps"""
        data = data.copy()
        
        # Ensure timestamp column is datetime
        data[timestamp_col] = pd.to_datetime(data[timestamp_col])
        
        # Extract time features
        data['hour'] = data[timestamp_col].dt.hour
        data['day_of_week'] = data[timestamp_col].dt.dayofweek
        data['day_of_month'] = data[timestamp_col].dt.day
        data['month'] = data[timestamp_col].dt.month
        data['quarter'] = data[timestamp_col].dt.quarter
        data['is_weekend'] = (data[timestamp_col].dt.dayofweek >= 5).astype(int)
        
        # Peak hours (typically 6-9 AM and 4-8 PM)
        data['is_peak_hour'] = ((data['hour'].between(6, 9)) | 
                               (data['hour'].between(16, 20))).astype(int)
        
        # Season (Northern Hemisphere)
        data['season'] = ((data[timestamp_col].dt.month % 12 + 3) // 3).map({
            1: 'spring', 2: 'summer', 3: 'fall', 4: 'winter'
        })
        
        # Holiday indicators (simplified)
        data['is_holiday_season'] = data[timestamp_col].dt.month.isin([12, 1, 7, 8]).astype(int)
        
        return data
    
    def create_lag_features(self, 
                           data: pd.DataFrame, 
                           value_col: str,
                           lags: List[int] = [1, 2, 3, 6, 12, 24]) -> pd.DataFrame:
        """Create lagged features for time series"""
        data = data.copy()
        
        for lag in lags:
            data[f'{value_col}_lag_{lag}'] = data[value_col].shift(lag)
        
        # Rolling statistics
        for window in [3, 6, 12, 24]:
            data[f'{value_col}_rolling_mean_{window}'] = data[value_col].rolling(window=window).mean()
            data[f'{value_col}_rolling_std_{window}'] = data[value_col].rolling(window=window).std()
            data[f'{value_col}_rolling_min_{window}'] = data[value_col].rolling(window=window).min()
            data[f'{value_col}_rolling_max_{window}'] = data[value_col].rolling(window=window).max()
        
        return data


class ClassificationModel(BaseMLModel):
    """Base class for classification models"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.classes_ = None
    
    def encode_categorical_features(self, 
                                   data: pd.DataFrame, 
                                   categorical_cols: List[str],
                                   is_training: bool = False) -> pd.DataFrame:
        """Encode categorical features"""
        data = data.copy()
        
        for col in categorical_cols:
            if col not in data.columns:
                continue
            
            if is_training:
                if self.label_encoder is None:
                    self.label_encoder = {}
                
                if col not in self.label_encoder:
                    self.label_encoder[col] = LabelEncoder()
                    data[f'{col}_encoded'] = self.label_encoder[col].fit_transform(data[col].astype(str))
                else:
                    data[f'{col}_encoded'] = self.label_encoder[col].transform(data[col].astype(str))
            else:
                if self.label_encoder and col in self.label_encoder:
                    # Handle unknown categories
                    known_categories = self.label_encoder[col].classes_
                    data[col] = data[col].astype(str)
                    data[col] = data[col].apply(lambda x: x if x in known_categories else known_categories[0])
                    data[f'{col}_encoded'] = self.label_encoder[col].transform(data[col])
                else:
                    # If no encoder available, use simple mapping
                    unique_vals = data[col].unique()
                    mapping = {val: idx for idx, val in enumerate(unique_vals)}
                    data[f'{col}_encoded'] = data[col].map(mapping)
        
        return data


class RegressionModel(BaseMLModel):
    """Base class for regression models"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
    
    def calculate_regression_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mae': mae,
            'mse': mse, 
            'rmse': rmse,
            'r2_score': r2
        }


class ClusteringModel(BaseMLModel):
    """Base class for clustering models"""
    
    def __init__(self, model_name: str, n_clusters: int = 5, **kwargs):
        super().__init__(model_name, **kwargs)
        self.n_clusters = n_clusters
    
    def calculate_clustering_metrics(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """Calculate clustering metrics"""
        metrics = {}
        
        if len(np.unique(labels)) > 1:
            metrics['silhouette_score'] = silhouette_score(X, labels)
        
        if hasattr(self.model, 'inertia_'):
            metrics['inertia'] = self.model.inertia_
        
        return metrics


class ModelFactory:
    """Factory for creating different types of ML models"""
    
    @staticmethod
    def create_xgboost_regressor(model_name: str, **xgb_params) -> 'XGBoostRegressionModel':
        """Create XGBoost regression model"""
        from .regression_models import XGBoostRegressionModel
        return XGBoostRegressionModel(model_name, **xgb_params)
    
    @staticmethod
    def create_xgboost_classifier(model_name: str, **xgb_params) -> 'XGBoostClassificationModel':
        """Create XGBoost classification model"""
        from .classification_models import XGBoostClassificationModel
        return XGBoostClassificationModel(model_name, **xgb_params)
    
    @staticmethod
    def create_lstm_forecaster(model_name: str, **lstm_params) -> 'LSTMForecastingModel':
        """Create LSTM time series model"""
        from .time_series_models import LSTMForecastingModel
        return LSTMForecastingModel(model_name, **lstm_params)
    
    @staticmethod
    def create_kmeans_clustering(model_name: str, **kmeans_params) -> 'KMeansClusteringModel':
        """Create K-means clustering model"""
        from .clustering_models import KMeansClusteringModel
        return KMeansClusteringModel(model_name, **kmeans_params)


# Model performance tracking
class ModelPerformanceTracker:
    """Tracks model performance over time"""
    
    def __init__(self):
        self.performance_history: Dict[str, List[ModelMetrics]] = {}
    
    def add_metrics(self, metrics: ModelMetrics):
        """Add performance metrics"""
        model_key = f"{metrics.model_name}_v{metrics.model_version}"
        
        if model_key not in self.performance_history:
            self.performance_history[model_key] = []
        
        self.performance_history[model_key].append(metrics)
    
    def get_latest_metrics(self, model_name: str, model_version: str) -> Optional[ModelMetrics]:
        """Get latest metrics for a model"""
        model_key = f"{model_name}_v{model_version}"
        
        if model_key in self.performance_history and self.performance_history[model_key]:
            return self.performance_history[model_key][-1]
        
        return None
    
    def is_performance_degrading(self, 
                                model_name: str, 
                                model_version: str,
                                metric_name: str = "accuracy",
                                threshold: float = 0.05) -> bool:
        """Check if model performance is degrading"""
        model_key = f"{model_name}_v{model_version}"
        
        if model_key not in self.performance_history or len(self.performance_history[model_key]) < 2:
            return False
        
        recent_metrics = self.performance_history[model_key][-5:]  # Last 5 evaluations
        
        if len(recent_metrics) < 2:
            return False
        
        # Check if there's a downward trend
        metric_values = [getattr(m, metric_name, 0) for m in recent_metrics if hasattr(m, metric_name)]
        
        if len(metric_values) < 2:
            return False
        
        # Simple trend check - compare first half with second half
        mid_point = len(metric_values) // 2
        first_half_avg = np.mean(metric_values[:mid_point]) if mid_point > 0 else metric_values[0]
        second_half_avg = np.mean(metric_values[mid_point:])
        
        degradation = (first_half_avg - second_half_avg) / first_half_avg
        
        return degradation > threshold


# Global performance tracker instance
performance_tracker = ModelPerformanceTracker()