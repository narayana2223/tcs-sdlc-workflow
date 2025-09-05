"""
Regression Models for Delay and Cost Prediction

This module implements various regression models for predicting continuous values
such as delay duration, cost impact, passenger impact, and recovery time.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from .base_models import (
    RegressionModel, PredictionResult, ModelMetrics,
    DisruptionType, SeverityLevel
)


class DelayPredictionModel(RegressionModel):
    """Regression model for predicting flight delay duration in minutes"""
    
    def __init__(self, 
                 model_name: str = "delay_prediction",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # XGBoost parameters optimized for delay prediction
        self.xgb_params = {
            'objective': 'reg:squarederror',
            'max_depth': 8,
            'learning_rate': 0.1,
            'n_estimators': 150,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42
        }
        self.xgb_params.update(kwargs.get('xgb_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for delay prediction"""
        
        data = data.copy()
        
        # Time-based features
        if 'scheduled_departure' in data.columns:
            data['scheduled_departure'] = pd.to_datetime(data['scheduled_departure'])
            data['departure_hour'] = data['scheduled_departure'].dt.hour
            data['departure_day_of_week'] = data['scheduled_departure'].dt.dayofweek
            data['departure_month'] = data['scheduled_departure'].dt.month
            
            # Peak travel periods
            data['is_peak_departure'] = ((data['departure_hour'].between(6, 10)) | 
                                       (data['departure_hour'].between(17, 21))).astype(int)
            data['is_weekend'] = (data['departure_day_of_week'] >= 5).astype(int)
            data['is_holiday_season'] = data['departure_month'].isin([12, 1, 7, 8]).astype(int)
        
        # Route and operational features
        if 'route_distance_km' in data.columns:
            data['is_long_haul'] = (data['route_distance_km'] > 3000).astype(int)
            data['is_short_haul'] = (data['route_distance_km'] < 1000).astype(int)
            data['flight_duration_estimated'] = data['route_distance_km'] / 800  # Rough speed estimate
        
        if 'aircraft_type' in data.columns:
            # Encode aircraft types
            data = self.encode_categorical_features(data, ['aircraft_type'], is_training=True)
        
        if 'airline' in data.columns:
            data = self.encode_categorical_features(data, ['airline'], is_training=True)
        
        if 'origin_airport' in data.columns and 'destination_airport' in data.columns:
            data = self.encode_categorical_features(data, ['origin_airport', 'destination_airport'], is_training=True)
        
        # Weather features
        weather_cols = ['temperature', 'wind_speed', 'precipitation', 'visibility', 'weather_severity']
        for col in weather_cols:
            if col in data.columns:
                # Create severity thresholds
                if col == 'wind_speed':
                    data[f'{col}_high'] = (data[col] > 25).astype(int)  # High wind
                elif col == 'precipitation':
                    data[f'{col}_heavy'] = (data[col] > 5).astype(int)  # Heavy rain/snow
                elif col == 'visibility':
                    data[f'{col}_low'] = (data[col] < 1000).astype(int)  # Low visibility
                elif col == 'weather_severity':
                    data[f'{col}_severe'] = (data[col] > 0.7).astype(int)
        
        # Airport congestion and capacity
        if 'airport_congestion_score' in data.columns:
            data['high_congestion'] = (data['airport_congestion_score'] > 0.8).astype(int)
            data['medium_congestion'] = (data['airport_congestion_score'].between(0.5, 0.8)).astype(int)
        
        if 'runway_capacity_utilization' in data.columns:
            data['runway_saturated'] = (data['runway_capacity_utilization'] > 0.9).astype(int)
        
        # Historical delay patterns
        if 'avg_delay_last_7days' in data.columns:
            data['recent_delay_pattern'] = pd.cut(data['avg_delay_last_7days'], 
                                                bins=[0, 15, 45, 120, float('inf')], 
                                                labels=[0, 1, 2, 3]).astype(int)
        
        # Aircraft and maintenance features
        if 'days_since_maintenance' in data.columns:
            data['maintenance_due_soon'] = (data['days_since_maintenance'] > 25).astype(int)
            data['recent_maintenance'] = (data['days_since_maintenance'] < 5).astype(int)
        
        if 'aircraft_age_years' in data.columns:
            data['older_aircraft'] = (data['aircraft_age_years'] > 15).astype(int)
        
        # Crew and operational factors
        if 'crew_delay_risk' in data.columns:
            data['high_crew_risk'] = (data['crew_delay_risk'] > 0.7).astype(int)
        
        if 'turnaround_time_minutes' in data.columns:
            data['tight_turnaround'] = (data['turnaround_time_minutes'] < 45).astype(int)
        
        # Network effects
        if 'connecting_flights' in data.columns:
            data['has_connections'] = (data['connecting_flights'] > 0).astype(int)
            data['many_connections'] = (data['connecting_flights'] > 10).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'delay_minutes',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train delay prediction model"""
        
        self.logger.info(f"Training {self.model_name}")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['scheduled_departure', 'actual_departure', target_column, 
                       'flight_id', 'aircraft_id', 'registration']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols and not col.endswith('_departure')]
        
        # Handle target variable - ensure non-negative delays
        y = prepared_data[target_column].clip(lower=0)
        
        # Features
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=True)
        
        # Split data chronologically (important for time series)
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        self.logger.info(f"Average delay in training: {y_train.mean():.1f} minutes")
        
        # Train XGBoost regressor
        self.model = xgb.XGBRegressor(**self.xgb_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred = np.clip(y_pred, 0, None)  # Ensure non-negative predictions
        
        # Calculate regression metrics
        metrics_dict = self.calculate_regression_metrics(y_val, y_pred)
        
        # Custom delay-specific metrics
        within_15min_accuracy = np.mean(np.abs(y_val - y_pred) <= 15)
        within_30min_accuracy = np.mean(np.abs(y_val - y_pred) <= 30)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            prediction_accuracy_1hour=within_15min_accuracy * 100,
            prediction_accuracy_4hour=within_30min_accuracy * 100
        )
        
        self.logger.info(f"Training completed. MAE: {metrics_dict['mae']:.2f}, "
                        f"RMSE: {metrics_dict['rmse']:.2f}, R²: {metrics_dict['r2_score']:.3f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict flight delays"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        
        predictions = self.model.predict(X)
        predictions = np.clip(predictions, 0, None)  # Ensure non-negative
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            pred_value = float(predictions[idx])
            
            # Determine disruption type based on features
            disruption_type = self._determine_delay_cause(row, pred_value)
            
            # Calculate confidence based on feature importance and prediction magnitude
            confidence = self._calculate_delay_confidence(row, pred_value)
            
            # Determine severity
            severity = self.determine_severity(pred_value, disruption_type)
            
            # Estimate cost impact
            cost_impact = self._estimate_delay_cost(pred_value, row)
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=pred_value,
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                forecast_horizon_minutes=240,  # 4-hour forecast
                affected_flights=[row.get('flight_id', 'unknown')],
                estimated_impact_cost=cost_impact
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'delay_minutes') -> ModelMetrics:
        """Evaluate delay prediction model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        y_true = prepared_data[target_column].clip(lower=0)
        y_pred = np.clip(self.model.predict(X), 0, None)
        
        # Calculate metrics
        metrics_dict = self.calculate_regression_metrics(y_true, y_pred)
        
        # Custom metrics
        within_15min = np.mean(np.abs(y_true - y_pred) <= 15)
        within_30min = np.mean(np.abs(y_true - y_pred) <= 30)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            prediction_accuracy_1hour=within_15min * 100,
            prediction_accuracy_4hour=within_30min * 100
        )
    
    def _determine_delay_cause(self, row: pd.Series, predicted_delay: float) -> DisruptionType:
        """Determine most likely cause of predicted delay"""
        
        # Weather-related
        if any(row.get(f'{col}_severe', 0) or row.get(f'{col}_high', 0) or row.get(f'{col}_heavy', 0) or row.get(f'{col}_low', 0) 
               for col in ['weather_severity', 'wind_speed', 'precipitation', 'visibility']):
            return DisruptionType.WEATHER
        
        # Airport congestion
        if row.get('high_congestion', 0) or row.get('runway_saturated', 0):
            return DisruptionType.AIRPORT_CONGESTION
        
        # Maintenance issues
        if row.get('maintenance_due_soon', 0) or row.get('older_aircraft', 0):
            return DisruptionType.TECHNICAL
        
        # Crew issues
        if row.get('high_crew_risk', 0):
            return DisruptionType.CREW
        
        # Peak hour operations (likely ATC)
        if row.get('is_peak_departure', 0):
            return DisruptionType.ATC
        
        # Default to airline operational
        return DisruptionType.AIRLINE_OPERATIONAL
    
    def _calculate_delay_confidence(self, row: pd.Series, predicted_delay: float) -> float:
        """Calculate confidence for delay prediction"""
        
        base_confidence = 0.82  # Historical model accuracy
        
        # Adjust confidence based on feature quality
        confidence_adjustments = 0
        
        # High confidence factors
        if row.get('weather_severity_severe', 0):
            confidence_adjustments += 0.1  # Weather data is usually reliable
        
        if row.get('high_congestion', 0):
            confidence_adjustments += 0.08  # Airport data is reliable
        
        # Uncertainty factors
        if predicted_delay > 300:  # Very long delays are harder to predict
            confidence_adjustments -= 0.1
        
        if row.get('tight_turnaround', 0):  # Complex operational factors
            confidence_adjustments -= 0.05
        
        final_confidence = np.clip(base_confidence + confidence_adjustments, 0.3, 0.95)
        return float(final_confidence)
    
    def _estimate_delay_cost(self, predicted_delay: float, row: pd.Series) -> float:
        """Estimate cost impact of predicted delay"""
        
        # Base cost per minute of delay
        cost_per_minute = 12.0  # GBP
        
        # Adjust based on aircraft size and route
        if row.get('is_long_haul', 0):
            cost_per_minute *= 1.8
        elif row.get('is_short_haul', 0):
            cost_per_minute *= 0.7
        
        # Peak hour multiplier
        if row.get('is_peak_departure', 0):
            cost_per_minute *= 1.3
        
        # Connection impact
        if row.get('many_connections', 0):
            cost_per_minute *= 1.5
        elif row.get('has_connections', 0):
            cost_per_minute *= 1.2
        
        return float(predicted_delay * cost_per_minute)


class CostImpactModel(RegressionModel):
    """Regression model for predicting financial impact of disruptions"""
    
    def __init__(self, 
                 model_name: str = "cost_impact_prediction",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # Gradient Boosting for cost prediction
        self.gbr_params = {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }
        self.gbr_params.update(kwargs.get('gbr_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for cost impact prediction"""
        
        data = data.copy()
        
        # Passenger impact features
        if 'affected_passengers' in data.columns:
            data['passenger_cost_base'] = data['affected_passengers'] * 150  # Base cost per passenger
            data['large_passenger_impact'] = (data['affected_passengers'] > 200).astype(int)
        
        # Delay duration impact
        if 'delay_minutes' in data.columns:
            data['delay_cost_base'] = data['delay_minutes'] * 15  # Base cost per minute
            data['extreme_delay'] = (data['delay_minutes'] > 240).astype(int)
        
        # Disruption type impacts (different cost structures)
        if 'disruption_type' in data.columns:
            high_cost_disruptions = ['weather', 'technical', 'crew']
            data['high_cost_disruption'] = data['disruption_type'].isin(high_cost_disruptions).astype(int)
        
        # Compensation requirements
        if 'compensation_required' in data.columns:
            data['compensation_flag'] = data['compensation_required'].astype(int)
        
        # Hotel and transport needs
        if 'requires_accommodation' in data.columns:
            data['accommodation_flag'] = data['requires_accommodation'].astype(int)
        
        if 'requires_transport' in data.columns:
            data['transport_flag'] = data['requires_transport'].astype(int)
        
        # Route and aircraft cost factors
        if 'route_distance_km' in data.columns:
            data['long_haul_route'] = (data['route_distance_km'] > 3000).astype(int)
        
        if 'aircraft_type' in data.columns:
            # Encode aircraft types - larger aircraft = higher costs
            data = self.encode_categorical_features(data, ['aircraft_type'], is_training=True)
        
        # Time-sensitive factors
        if 'is_peak_hour' in data.columns:
            data['peak_hour_multiplier'] = data['is_peak_hour'] * 1.5
        
        if 'is_weekend' in data.columns:
            data['weekend_multiplier'] = data['is_weekend'] * 1.2
        
        # Network cascade effects
        if 'affected_downstream_flights' in data.columns:
            data['cascade_cost'] = data['affected_downstream_flights'] * 500  # Estimate per affected flight
            data['major_cascade'] = (data['affected_downstream_flights'] > 5).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'total_cost_gbp',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train cost impact model"""
        
        self.logger.info(f"Training {self.model_name}")
        
        # Prepare features
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['timestamp', target_column, 'flight_id', 'incident_id']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols]
        
        # Target - ensure positive costs
        y = prepared_data[target_column].clip(lower=0)
        
        # Features
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=True)
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples")
        self.logger.info(f"Average cost in training: £{y_train.mean():.0f}")
        
        # Train Gradient Boosting Regressor
        self.model = GradientBoostingRegressor(**self.gbr_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred = np.clip(y_pred, 0, None)  # Ensure non-negative costs
        
        # Calculate metrics
        metrics_dict = self.calculate_regression_metrics(y_val, y_pred)
        
        # Cost-specific metrics
        within_20pct_accuracy = np.mean(np.abs(y_val - y_pred) / (y_val + 1) <= 0.2)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            cost_impact_accuracy=within_20pct_accuracy * 100
        )
        
        self.logger.info(f"Cost training completed. MAE: £{metrics_dict['mae']:.0f}, "
                        f"RMSE: £{metrics_dict['rmse']:.0f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict cost impact of disruptions"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            self.logger.warning("No data available for prediction")
            return []
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        
        predictions = self.model.predict(X)
        predictions = np.clip(predictions, 0, None)  # Ensure non-negative costs
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            pred_value = float(predictions[idx])
            
            # Determine disruption type and severity based on cost
            disruption_type = self._determine_disruption_from_cost(row)
            severity = self._determine_severity_from_cost(pred_value)
            
            # High confidence for cost predictions with good features
            confidence = 0.87 if row.get('passenger_cost_base', 0) > 0 else 0.75
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=pred_value,
                confidence=confidence,
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                estimated_impact_cost=pred_value,
                affected_passengers=int(row.get('affected_passengers', 0))
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'total_cost_gbp') -> ModelMetrics:
        """Evaluate cost impact model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available for evaluation")
        
        # Make predictions
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        y_true = prepared_data[target_column].clip(lower=0)
        y_pred = np.clip(self.model.predict(X), 0, None)
        
        # Calculate metrics
        metrics_dict = self.calculate_regression_metrics(y_true, y_pred)
        
        # Cost accuracy within 20%
        within_20pct = np.mean(np.abs(y_true - y_pred) / (y_true + 1) <= 0.2)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            cost_impact_accuracy=within_20pct * 100
        )
    
    def _determine_disruption_from_cost(self, row: pd.Series) -> DisruptionType:
        """Determine disruption type from cost features"""
        
        if row.get('high_cost_disruption', 0):
            # Look at specific indicators
            if row.get('accommodation_flag', 0):
                return DisruptionType.WEATHER  # Often requires overnight stays
            elif row.get('major_cascade', 0):
                return DisruptionType.TECHNICAL  # Technical issues cause cascades
            else:
                return DisruptionType.CREW  # Crew issues are expensive
        else:
            return DisruptionType.AIRLINE_OPERATIONAL
    
    def _determine_severity_from_cost(self, predicted_cost: float) -> SeverityLevel:
        """Determine severity level from predicted cost"""
        
        if predicted_cost > 100000:  # £100k+
            return SeverityLevel.CRITICAL
        elif predicted_cost > 50000:  # £50k+
            return SeverityLevel.HIGH
        elif predicted_cost > 20000:  # £20k+
            return SeverityLevel.MEDIUM
        elif predicted_cost > 5000:   # £5k+
            return SeverityLevel.LOW
        else:
            return SeverityLevel.LOW


class RecoveryTimeModel(RegressionModel):
    """Model for predicting time to recover from disruptions"""
    
    def __init__(self, 
                 model_name: str = "recovery_time_prediction",
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # Random Forest for recovery time prediction
        self.rf_params = {
            'n_estimators': 150,
            'max_depth': 12,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42
        }
        self.rf_params.update(kwargs.get('rf_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for recovery time prediction"""
        
        data = data.copy()
        
        # Disruption characteristics
        if 'disruption_severity' in data.columns:
            data['high_severity'] = (data['disruption_severity'] >= 4).astype(int)
            data['medium_severity'] = (data['disruption_severity'] == 3).astype(int)
        
        if 'disruption_type' in data.columns:
            # Different disruption types have different recovery patterns
            weather_types = ['weather', 'storm', 'fog']
            technical_types = ['technical', 'maintenance', 'aircraft']
            data['weather_disruption'] = data['disruption_type'].isin(weather_types).astype(int)
            data['technical_disruption'] = data['disruption_type'].isin(technical_types).astype(int)
        
        # Available resources for recovery
        if 'spare_aircraft_available' in data.columns:
            data['has_spare_aircraft'] = (data['spare_aircraft_available'] > 0).astype(int)
        
        if 'crew_availability' in data.columns:
            data['sufficient_crew'] = (data['crew_availability'] > 0.8).astype(int)
        
        if 'alternative_routes' in data.columns:
            data['has_alternatives'] = (data['alternative_routes'] > 0).astype(int)
            data['many_alternatives'] = (data['alternative_routes'] > 3).astype(int)
        
        # Operational complexity
        if 'affected_flights' in data.columns:
            data['complex_recovery'] = (data['affected_flights'] > 10).astype(int)
            data['simple_recovery'] = (data['affected_flights'] <= 3).astype(int)
        
        if 'network_impact_score' in data.columns:
            data['network_wide_impact'] = (data['network_impact_score'] > 0.7).astype(int)
        
        # Time factors
        if 'disruption_start_hour' in data.columns:
            # Night disruptions are often slower to recover from
            data['nighttime_disruption'] = ((data['disruption_start_hour'] < 6) | 
                                           (data['disruption_start_hour'] > 22)).astype(int)
            data['peak_hour_disruption'] = ((data['disruption_start_hour'].between(6, 10)) | 
                                           (data['disruption_start_hour'].between(17, 21))).astype(int)
        
        # Airport factors
        if 'airport_size' in data.columns:
            data = self.encode_categorical_features(data, ['airport_size'], is_training=True)
        
        if 'hub_airport' in data.columns:
            data['is_hub'] = data['hub_airport'].astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: str = 'recovery_time_minutes',
              validation_split: float = 0.2) -> ModelMetrics:
        """Train recovery time model"""
        
        self.logger.info(f"Training {self.model_name}")
        
        prepared_data = self.prepare_features(data)
        self.target_column = target_column
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Define feature columns
        exclude_cols = ['timestamp', target_column, 'disruption_id', 'resolution_timestamp']
        self.feature_columns = [col for col in prepared_data.columns 
                               if col not in exclude_cols]
        
        # Target - ensure positive recovery times
        y = prepared_data[target_column].clip(lower=0)
        
        # Features
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=True)
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training on {len(X_train)} samples")
        self.logger.info(f"Average recovery time: {y_train.mean():.0f} minutes")
        
        # Train Random Forest
        self.model = RandomForestRegressor(**self.rf_params)
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        y_pred = np.clip(y_pred, 0, None)
        
        metrics_dict = self.calculate_regression_metrics(y_val, y_pred)
        
        # Recovery-specific metrics
        within_30min_accuracy = np.mean(np.abs(y_val - y_pred) <= 30)
        within_60min_accuracy = np.mean(np.abs(y_val - y_pred) <= 60)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            prediction_accuracy_1hour=within_30min_accuracy * 100,
            prediction_accuracy_4hour=within_60min_accuracy * 100
        )
        
        self.logger.info(f"Recovery training completed. MAE: {metrics_dict['mae']:.1f} min, "
                        f"RMSE: {metrics_dict['rmse']:.1f} min")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict recovery times for disruptions"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            return []
        
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        
        predictions = self.model.predict(X)
        predictions = np.clip(predictions, 0, None)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            pred_value = float(predictions[idx])
            
            # Determine disruption characteristics
            if row.get('weather_disruption', 0):
                disruption_type = DisruptionType.WEATHER
            elif row.get('technical_disruption', 0):
                disruption_type = DisruptionType.TECHNICAL
            else:
                disruption_type = DisruptionType.AIRLINE_OPERATIONAL
            
            # Determine severity based on recovery time
            if pred_value > 480:  # 8+ hours
                severity = SeverityLevel.CRITICAL
            elif pred_value > 240:  # 4+ hours
                severity = SeverityLevel.HIGH
            elif pred_value > 120:  # 2+ hours
                severity = SeverityLevel.MEDIUM
            else:
                severity = SeverityLevel.LOW
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=pred_value,
                confidence=0.79,  # Base confidence for recovery predictions
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: str = 'recovery_time_minutes') -> ModelMetrics:
        """Evaluate recovery time model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        
        X = prepared_data[self.feature_columns]
        X = self.preprocess_data(X, is_training=False)
        y_true = prepared_data[target_column].clip(lower=0)
        y_pred = np.clip(self.model.predict(X), 0, None)
        
        metrics_dict = self.calculate_regression_metrics(y_true, y_pred)
        
        within_30min = np.mean(np.abs(y_true - y_pred) <= 30)
        within_60min = np.mean(np.abs(y_true - y_pred) <= 60)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict,
            prediction_accuracy_1hour=within_30min * 100,
            prediction_accuracy_4hour=within_60min * 100
        )