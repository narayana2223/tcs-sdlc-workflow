"""
Classification Models for Disruption Type and Severity Prediction

This module implements various classification models for predicting disruption types,
severity levels, and other categorical outcomes in flight operations.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid
from collections import Counter

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.model_selection import cross_val_score
import xgboost as xgb

from .base_models import (
    ClassificationModel, PredictionResult, ModelMetrics,
    DisruptionType, SeverityLevel
)


class DisruptionTypeClassifier(ClassificationModel):
    """Classifier for predicting types of flight disruptions"""
    
    def __init__(self, 
                 model_name: str = "disruption_type_classifier",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # XGBoost parameters optimized for classification
        self.xgb_params = {
            'objective': 'multi:softprob',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        self.xgb_params.update(kwargs.get('xgb_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for disruption type classification"""
        
        data = data.copy()
        
        # Weather-related features
        if 'weather_score' in data.columns:
            data['high_weather_risk'] = (data['weather_score'] > 0.7).astype(int)
            data['moderate_weather_risk'] = (data['weather_score'].between(0.3, 0.7)).astype(int)
        
        # Temporal features
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['month'] = data['timestamp'].dt.month
            
            # Peak operation hours
            data['is_peak_hour'] = ((data['hour'].between(6, 10)) | 
                                  (data['hour'].between(17, 21))).astype(int)
            data['is_overnight'] = ((data['hour'] < 6) | 
                                  (data['hour'] > 22)).astype(int)
        
        # Airport congestion indicators
        if 'airport_congestion' in data.columns:
            data['high_congestion'] = (data['airport_congestion'] > 0.8).astype(int)
            data['medium_congestion'] = (data['airport_congestion'].between(0.5, 0.8)).astype(int)
        
        # Aircraft and route features
        if 'aircraft_type' in data.columns:
            data = self.encode_categorical_features(data, ['aircraft_type'], is_training=True)
        
        if 'route' in data.columns:
            data = self.encode_categorical_features(data, ['route'], is_training=True)
            
        if 'airline' in data.columns:
            data = self.encode_categorical_features(data, ['airline'], is_training=True)
        
        # Flight operational features
        if 'flight_duration_minutes' in data.columns:
            data['is_long_haul'] = (data['flight_duration_minutes'] > 360).astype(int)
            data['is_short_haul'] = (data['flight_duration_minutes'] < 120).astype(int)
        
        # Maintenance indicators
        if 'days_since_maintenance' in data.columns:
            data['maintenance_due'] = (data['days_since_maintenance'] > 30).astype(int)
            data['recent_maintenance'] = (data['days_since_maintenance'] < 7).astype(int)
        
        # Crew-related features
        if 'crew_hours_today' in data.columns:
            data['crew_fatigue_risk'] = (data['crew_hours_today'] > 8).astype(int)
        
        # Historical disruption patterns
        if 'disruptions_last_week' in data.columns:
            data['high_recent_disruptions'] = (data['disruptions_last_week'] > 5).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'disruption_type',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train disruption type classifier"""
        
        self.logger.info(f"Training {self.model_name}")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['timestamp', target_column, 'flight_id', 'aircraft_id']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols]
        
        # Prepare target - map disruption types to integers
        if target_column in prepared_data.columns:
            # Convert string labels to DisruptionType enum values
            disruption_mapping = {dt.value: dt.name for dt in DisruptionType}
            prepared_data[f'{target_column}_mapped'] = prepared_data[target_column].map(
                {v: k for k, v in disruption_mapping.items()}
            )
            
            # Handle any unmapped values
            prepared_data[f'{target_column}_mapped'] = prepared_data[f'{target_column}_mapped'].fillna('EXTERNAL')
            
            # Create label encoder for target
            if self.label_encoder is None:
                self.label_encoder = {}
            
            from sklearn.preprocessing import LabelEncoder
            self.label_encoder[target_column] = LabelEncoder()
            y = self.label_encoder[target_column].fit_transform(prepared_data[f'{target_column}_mapped'])
        else:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Features
        X = prepared_data[self.feature_columns]
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        self.logger.info(f"Class distribution: {Counter(y_train)}")
        
        # Create and train XGBoost classifier
        self.model = xgb.XGBClassifier(**self.xgb_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        self.classes_ = self.label_encoder[target_column].classes_
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)
        
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average='weighted')
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )
        
        self.logger.info(f"Training completed. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict disruption types"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = X.fillna(X.median())
        
        predictions = self.model.predict(X)
        prediction_probabilities = self.model.predict_proba(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            # Get predicted class
            pred_class_idx = predictions[idx]
            pred_class_name = self.classes_[pred_class_idx]
            
            # Map back to DisruptionType
            try:
                disruption_type = DisruptionType(pred_class_name.lower())
            except ValueError:
                disruption_type = DisruptionType.EXTERNAL
            
            # Get prediction confidence
            confidence = self.calculate_prediction_confidence(
                predictions[idx],
                prediction_probabilities[idx:idx+1],
                historical_accuracy=0.85
            )
            
            # Determine severity based on features and disruption type
            severity = self._determine_severity_from_features(row, disruption_type)
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=pred_class_name,
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                affected_flights=[row.get('flight_id', 'unknown')]
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'disruption_type') -> ModelMetrics:
        """Evaluate disruption type classifier"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Prepare target
        disruption_mapping = {dt.value: dt.name for dt in DisruptionType}
        prepared_data[f'{target_column}_mapped'] = prepared_data[target_column].map(
            {v: k for k, v in disruption_mapping.items()}
        ).fillna('EXTERNAL')
        
        y_true = self.label_encoder[target_column].transform(prepared_data[f'{target_column}_mapped'])
        
        # Make predictions
        X = prepared_data[self.feature_columns].fillna(prepared_data[self.feature_columns].median())
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average='weighted')
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )
    
    def _determine_severity_from_features(self, row: pd.Series, disruption_type: DisruptionType) -> SeverityLevel:
        """Determine severity based on row features and disruption type"""
        
        severity_score = 0
        
        # Weather-based severity
        if disruption_type == DisruptionType.WEATHER:
            if row.get('high_weather_risk', 0):
                severity_score += 3
            elif row.get('moderate_weather_risk', 0):
                severity_score += 2
        
        # Congestion-based severity
        if disruption_type == DisruptionType.AIRPORT_CONGESTION:
            if row.get('high_congestion', 0):
                severity_score += 3
            elif row.get('medium_congestion', 0):
                severity_score += 2
        
        # Peak hour increases severity
        if row.get('is_peak_hour', 0):
            severity_score += 1
        
        # Long haul flights more severe impact
        if row.get('is_long_haul', 0):
            severity_score += 1
        
        # Recent disruptions increase severity
        if row.get('high_recent_disruptions', 0):
            severity_score += 1
        
        # Map score to severity level
        if severity_score >= 5:
            return SeverityLevel.CRITICAL
        elif severity_score >= 3:
            return SeverityLevel.HIGH
        elif severity_score >= 2:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW


class SeverityClassifier(ClassificationModel):
    """Classifier for predicting disruption severity levels"""
    
    def __init__(self, 
                 model_name: str = "severity_classifier",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # Random Forest parameters for severity classification
        self.rf_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'class_weight': 'balanced'  # Handle class imbalance
        }
        self.rf_params.update(kwargs.get('rf_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for severity classification"""
        
        data = data.copy()
        
        # Impact-related features
        if 'affected_passengers' in data.columns:
            data['passenger_impact_high'] = (data['affected_passengers'] > 500).astype(int)
            data['passenger_impact_medium'] = (data['affected_passengers'].between(100, 500)).astype(int)
        
        if 'delay_minutes' in data.columns:
            data['delay_severe'] = (data['delay_minutes'] > 180).astype(int)
            data['delay_moderate'] = (data['delay_minutes'].between(60, 180)).astype(int)
        
        # Disruption type impact
        if 'disruption_type' in data.columns:
            high_severity_types = ['weather', 'technical', 'crew']
            data['high_severity_disruption'] = data['disruption_type'].isin(high_severity_types).astype(int)
        
        # Cascading effect indicators
        if 'affected_routes' in data.columns:
            data['multiple_routes_affected'] = (data['affected_routes'] > 1).astype(int)
        
        if 'network_impact' in data.columns:
            data['network_wide_impact'] = (data['network_impact'] > 0.5).astype(int)
        
        # Temporal criticality
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['hour'] = data['timestamp'].dt.hour
            
            # Critical travel times
            data['critical_travel_time'] = ((data['hour'].between(6, 9)) | 
                                          (data['hour'].between(17, 20))).astype(int)
        
        # Recovery difficulty
        if 'available_alternatives' in data.columns:
            data['limited_alternatives'] = (data['available_alternatives'] < 3).astype(int)
        
        # Cost impact
        if 'estimated_cost' in data.columns:
            data['high_cost_impact'] = (data['estimated_cost'] > 10000).astype(int)
            data['medium_cost_impact'] = (data['estimated_cost'].between(5000, 10000)).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'severity_level',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train severity classifier"""
        
        self.logger.info(f"Training {self.model_name}")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['timestamp', target_column, 'flight_id', 'aircraft_id']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols]
        
        # Prepare target
        if target_column in prepared_data.columns:
            # Map severity levels to numeric values
            severity_mapping = {
                'low': 1, 'medium': 2, 'high': 3, 'critical': 4, 'emergency': 5
            }
            
            # Handle both string and numeric targets
            if prepared_data[target_column].dtype == 'object':
                y = prepared_data[target_column].map(severity_mapping)
            else:
                y = prepared_data[target_column]
            
            # Fill any unmapped values with medium severity
            y = y.fillna(2)
        else:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Features
        X = prepared_data[self.feature_columns]
        X = X.fillna(X.median())
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples")
        self.logger.info(f"Severity distribution: {Counter(y_train)}")
        
        # Create and train Random Forest classifier
        self.model = RandomForestClassifier(**self.rf_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        self.classes_ = sorted(y.unique())
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average='weighted')
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )
        
        self.logger.info(f"Severity training completed. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict severity levels"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = X.fillna(X.median())
        
        predictions = self.model.predict(X)
        prediction_probabilities = self.model.predict_proba(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            # Map prediction to SeverityLevel
            pred_value = int(predictions[idx])
            try:
                severity = SeverityLevel(pred_value)
            except ValueError:
                severity = SeverityLevel.MEDIUM
            
            # Get prediction confidence
            confidence = self.calculate_prediction_confidence(
                predictions[idx],
                prediction_probabilities[idx:idx+1],
                historical_accuracy=0.78
            )
            
            # Determine disruption type from features if available
            disruption_type = DisruptionType.AIRLINE_OPERATIONAL
            if row.get('high_weather_risk', 0):
                disruption_type = DisruptionType.WEATHER
            elif row.get('high_congestion', 0):
                disruption_type = DisruptionType.AIRPORT_CONGESTION
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=severity.name.lower(),
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                affected_flights=[row.get('flight_id', 'unknown')]
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'severity_level') -> ModelMetrics:
        """Evaluate severity classifier"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Prepare target
        severity_mapping = {
            'low': 1, 'medium': 2, 'high': 3, 'critical': 4, 'emergency': 5
        }
        
        if prepared_data[target_column].dtype == 'object':
            y_true = prepared_data[target_column].map(severity_mapping).fillna(2)
        else:
            y_true = prepared_data[target_column]
        
        # Make predictions
        X = prepared_data[self.feature_columns].fillna(prepared_data[self.feature_columns].median())
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average='weighted')
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )


class CancellationProbabilityClassifier(ClassificationModel):
    """Binary classifier for predicting flight cancellation probability"""
    
    def __init__(self, 
                 model_name: str = "cancellation_probability",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # Logistic Regression for probability output
        self.lr_params = {
            'random_state': 42,
            'max_iter': 1000,
            'class_weight': 'balanced'
        }
        self.lr_params.update(kwargs.get('lr_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for cancellation prediction"""
        
        data = data.copy()
        
        # Delay-related features
        if 'delay_minutes' in data.columns:
            data['extreme_delay'] = (data['delay_minutes'] > 360).astype(int)  # 6+ hours
            data['severe_delay'] = (data['delay_minutes'] > 240).astype(int)   # 4+ hours
        
        # Weather severity
        if 'weather_score' in data.columns:
            data['extreme_weather'] = (data['weather_score'] > 0.9).astype(int)
            data['severe_weather'] = (data['weather_score'] > 0.7).astype(int)
        
        # Technical issues
        if 'technical_issues' in data.columns:
            data['critical_technical'] = (data['technical_issues'] > 2).astype(int)
        
        # Crew availability
        if 'crew_available' in data.columns:
            data['crew_shortage'] = (data['crew_available'] == 0).astype(int)
        
        # Airport closure/restrictions
        if 'airport_status' in data.columns:
            data['airport_closed'] = (data['airport_status'] == 'closed').astype(int)
            data['airport_restricted'] = (data['airport_status'] == 'restricted').astype(int)
        
        # Aircraft availability
        if 'aircraft_available' in data.columns:
            data['no_aircraft'] = (data['aircraft_available'] == 0).astype(int)
        
        # Regulatory/safety issues
        if 'safety_issues' in data.columns:
            data['safety_concerns'] = (data['safety_issues'] > 0).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'is_cancelled',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train cancellation probability classifier"""
        
        self.logger.info(f"Training {self.model_name}")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['timestamp', target_column, 'flight_id', 'aircraft_id']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols]
        
        # Target (binary: cancelled or not)
        if target_column in prepared_data.columns:
            y = prepared_data[target_column].astype(int)
        else:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Features
        X = prepared_data[self.feature_columns]
        X = X.fillna(0)  # For binary features, fill with 0
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples")
        self.logger.info(f"Cancellation rate: {y_train.mean():.3f}")
        
        # Train Logistic Regression
        self.model = LogisticRegression(**self.lr_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)
        
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )
        
        self.logger.info(f"Cancellation training completed. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict cancellation probabilities"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = X.fillna(0)
        
        predictions = self.model.predict(X)
        prediction_probabilities = self.model.predict_proba(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            # Get cancellation probability (probability of class 1)
            cancellation_prob = prediction_probabilities[idx, 1] if prediction_probabilities.shape[1] > 1 else prediction_probabilities[idx, 0]
            
            # Determine severity based on cancellation probability
            if cancellation_prob > 0.8:
                severity = SeverityLevel.CRITICAL
            elif cancellation_prob > 0.6:
                severity = SeverityLevel.HIGH
            elif cancellation_prob > 0.3:
                severity = SeverityLevel.MEDIUM
            else:
                severity = SeverityLevel.LOW
            
            # Determine likely disruption type
            disruption_type = DisruptionType.AIRLINE_OPERATIONAL
            if row.get('extreme_weather', 0):
                disruption_type = DisruptionType.WEATHER
            elif row.get('critical_technical', 0):
                disruption_type = DisruptionType.TECHNICAL
            elif row.get('crew_shortage', 0):
                disruption_type = DisruptionType.CREW
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=float(cancellation_prob),
                confidence=float(max(cancellation_prob, 1 - cancellation_prob)),
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                affected_flights=[row.get('flight_id', 'unknown')]
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'is_cancelled') -> ModelMetrics:
        """Evaluate cancellation classifier"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Make predictions
        X = prepared_data[self.feature_columns].fillna(0)
        y_true = prepared_data[target_column].astype(int)
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            accuracy=accuracy,
            f1_score=f1
        )