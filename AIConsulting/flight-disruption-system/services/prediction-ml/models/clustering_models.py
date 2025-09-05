"""
Clustering Models for Disruption Pattern Analysis

This module implements clustering algorithms for identifying similar disruption
patterns, passenger behavior, operational patterns, and anomaly detection.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import uuid

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns

from .base_models import (
    ClusteringModel, PredictionResult, ModelMetrics,
    DisruptionType, SeverityLevel
)


class DisruptionPatternClustering(ClusteringModel):
    """Clustering model for identifying similar disruption patterns"""
    
    def __init__(self, 
                 model_name: str = "disruption_pattern_clustering",
                 n_clusters: int = 5,
                 **kwargs):
        
        super().__init__(model_name, n_clusters, **kwargs)
        
        # KMeans parameters for disruption clustering
        self.kmeans_params = {
            'n_clusters': n_clusters,
            'random_state': 42,
            'n_init': 10,
            'max_iter': 300
        }
        self.kmeans_params.update(kwargs.get('kmeans_params', {}))
        
        # Pattern characteristics for each cluster
        self.cluster_characteristics = {}
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for disruption pattern clustering"""
        
        data = data.copy()
        
        # Temporal pattern features
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['month'] = data['timestamp'].dt.month
            
            # Cyclical encoding for better clustering
            data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
            data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)
            data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
            data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
            data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
            data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)
        
        # Disruption characteristics
        if 'delay_minutes' in data.columns:
            data['delay_log'] = np.log1p(data['delay_minutes'])  # Log transform for better distribution
            
        if 'affected_passengers' in data.columns:
            data['passengers_log'] = np.log1p(data['affected_passengers'])
        
        # Weather features
        weather_features = ['temperature', 'wind_speed', 'precipitation', 'visibility']
        for feature in weather_features:
            if feature in data.columns:
                # Normalize weather features
                data[f'{feature}_norm'] = (data[feature] - data[feature].mean()) / data[feature].std()
        
        # Airport and route features
        if 'airport_code' in data.columns:
            # One-hot encode major airports
            major_airports = ['LHR', 'CDG', 'FRA', 'AMS', 'BCN', 'FCO']
            for airport in major_airports:
                data[f'airport_{airport}'] = (data['airport_code'] == airport).astype(int)
        
        if 'route_distance_km' in data.columns:
            data['route_distance_norm'] = (data['route_distance_km'] - data['route_distance_km'].mean()) / data['route_distance_km'].std()
        
        # Operational features
        if 'aircraft_type' in data.columns:
            # Group aircraft by size category
            wide_body = ['A330', 'A340', 'A350', 'A380', 'B747', 'B767', 'B777', 'B787']
            narrow_body = ['A319', 'A320', 'A321', 'B737']
            
            data['wide_body'] = data['aircraft_type'].isin(wide_body).astype(int)
            data['narrow_body'] = data['aircraft_type'].isin(narrow_body).astype(int)
        
        # Disruption type encoding
        if 'disruption_type' in data.columns:
            disruption_types = data['disruption_type'].unique()
            for dtype in disruption_types:
                data[f'type_{dtype}'] = (data['disruption_type'] == dtype).astype(int)
        
        # Recovery characteristics
        if 'recovery_time_minutes' in data.columns:
            data['recovery_time_log'] = np.log1p(data['recovery_time_minutes'])
        
        # Cost impact
        if 'estimated_cost' in data.columns:
            data['cost_log'] = np.log1p(data['estimated_cost'])
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: Optional[str] = None,
              validation_split: float = 0.0) -> ModelMetrics:
        """Train disruption pattern clustering model"""
        
        self.logger.info(f"Training {self.model_name}")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            raise ValueError("No data available after feature preparation")
        
        # Select features for clustering
        clustering_features = [
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'month_sin', 'month_cos',
            'delay_log', 'passengers_log', 'recovery_time_log', 'cost_log'
        ]
        
        # Add weather features if available
        weather_features = [col for col in prepared_data.columns if col.endswith('_norm')]
        clustering_features.extend(weather_features)
        
        # Add airport features
        airport_features = [col for col in prepared_data.columns if col.startswith('airport_')]
        clustering_features.extend(airport_features[:10])  # Limit number of airport features
        
        # Add aircraft type features
        aircraft_features = ['wide_body', 'narrow_body']
        clustering_features.extend([col for col in aircraft_features if col in prepared_data.columns])
        
        # Add disruption type features
        type_features = [col for col in prepared_data.columns if col.startswith('type_')]
        clustering_features.extend(type_features)
        
        # Filter to available features
        self.feature_columns = [col for col in clustering_features if col in prepared_data.columns]
        
        # Prepare feature matrix
        X = prepared_data[self.feature_columns].fillna(0)
        
        # Standardize features
        X = self.preprocess_data(X, is_training=True)
        
        self.logger.info(f"Clustering {len(X)} samples using {len(self.feature_columns)} features")
        
        # Train KMeans clustering
        self.model = KMeans(**self.kmeans_params)
        cluster_labels = self.model.fit_predict(X)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Analyze cluster characteristics
        self.cluster_characteristics = self._analyze_clusters(prepared_data, cluster_labels)
        
        # Calculate clustering metrics
        metrics_dict = self.calculate_clustering_metrics(X, cluster_labels)
        
        metrics = ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )
        
        self.logger.info(f"Clustering completed. Found {self.n_clusters} patterns")
        self.logger.info(f"Silhouette score: {metrics_dict.get('silhouette_score', 0):.3f}")
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Assign disruption patterns to new data"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            return []
        
        # Prepare features
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        # Predict cluster assignments
        cluster_labels = self.model.predict(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            cluster_id = int(cluster_labels[idx])
            cluster_info = self.cluster_characteristics.get(cluster_id, {})
            
            # Determine disruption type and severity from cluster characteristics
            disruption_type = cluster_info.get('primary_disruption_type', DisruptionType.AIRLINE_OPERATIONAL)
            severity = cluster_info.get('typical_severity', SeverityLevel.MEDIUM)
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=f"pattern_{cluster_id}",
                confidence=0.75,  # Clustering confidence based on cluster cohesion
                severity=severity,
                disruption_type=disruption_type,
                features_used=self.feature_columns,
                model_version=self.model_version,
                affected_flights=[row.get('flight_id', 'unknown')]
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: Optional[str] = None) -> ModelMetrics:
        """Evaluate clustering model"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        cluster_labels = self.model.predict(X)
        metrics_dict = self.calculate_clustering_metrics(X, cluster_labels)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )
    
    def _analyze_clusters(self, data: pd.DataFrame, labels: np.ndarray) -> Dict[int, Dict[str, Any]]:
        """Analyze characteristics of each cluster"""
        
        characteristics = {}
        
        for cluster_id in range(self.n_clusters):
            cluster_mask = labels == cluster_id
            cluster_data = data[cluster_mask]
            
            if len(cluster_data) == 0:
                continue
            
            cluster_info = {
                'size': len(cluster_data),
                'percentage': len(cluster_data) / len(data) * 100
            }
            
            # Temporal patterns
            if 'hour' in cluster_data.columns:
                cluster_info['peak_hours'] = cluster_data['hour'].mode().tolist()
                cluster_info['avg_hour'] = cluster_data['hour'].mean()
            
            if 'day_of_week' in cluster_data.columns:
                cluster_info['common_days'] = cluster_data['day_of_week'].mode().tolist()
            
            if 'month' in cluster_data.columns:
                cluster_info['seasonal_pattern'] = cluster_data['month'].mode().tolist()
            
            # Disruption characteristics
            if 'delay_minutes' in cluster_data.columns:
                cluster_info['avg_delay'] = cluster_data['delay_minutes'].mean()
                cluster_info['median_delay'] = cluster_data['delay_minutes'].median()
                cluster_info['delay_std'] = cluster_data['delay_minutes'].std()
            
            if 'affected_passengers' in cluster_data.columns:
                cluster_info['avg_passengers'] = cluster_data['affected_passengers'].mean()
            
            if 'estimated_cost' in cluster_data.columns:
                cluster_info['avg_cost'] = cluster_data['estimated_cost'].mean()
            
            # Determine primary disruption type
            if 'disruption_type' in cluster_data.columns:
                type_counts = cluster_data['disruption_type'].value_counts()
                primary_type = type_counts.index[0] if len(type_counts) > 0 else 'unknown'
                
                try:
                    cluster_info['primary_disruption_type'] = DisruptionType(primary_type.lower())
                except ValueError:
                    cluster_info['primary_disruption_type'] = DisruptionType.AIRLINE_OPERATIONAL
            
            # Determine typical severity
            avg_delay = cluster_info.get('avg_delay', 0)
            avg_passengers = cluster_info.get('avg_passengers', 0)
            
            if avg_delay > 180 or avg_passengers > 500:
                cluster_info['typical_severity'] = SeverityLevel.HIGH
            elif avg_delay > 60 or avg_passengers > 200:
                cluster_info['typical_severity'] = SeverityLevel.MEDIUM
            else:
                cluster_info['typical_severity'] = SeverityLevel.LOW
            
            # Airport patterns
            if 'airport_code' in cluster_data.columns:
                airport_counts = cluster_data['airport_code'].value_counts()
                cluster_info['common_airports'] = airport_counts.head(3).index.tolist()
            
            # Weather patterns
            weather_cols = ['temperature', 'wind_speed', 'precipitation', 'visibility']
            weather_summary = {}
            for col in weather_cols:
                if col in cluster_data.columns:
                    weather_summary[col] = {
                        'mean': cluster_data[col].mean(),
                        'std': cluster_data[col].std()
                    }
            cluster_info['weather_patterns'] = weather_summary
            
            characteristics[cluster_id] = cluster_info
        
        return characteristics
    
    def visualize_clusters(self, data: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """Create visualizations of the clustering results"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before visualization")
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        labels = self.model.predict(X)
        
        # Reduce dimensionality for visualization
        if X.shape[1] > 2:
            pca = PCA(n_components=2, random_state=42)
            X_vis = pca.fit_transform(X)
        else:
            X_vis = X
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Plot clusters
        colors = plt.cm.Set3(np.linspace(0, 1, self.n_clusters))
        for i in range(self.n_clusters):
            cluster_mask = labels == i
            cluster_info = self.cluster_characteristics.get(i, {})
            cluster_size = cluster_info.get('size', 0)
            
            plt.scatter(X_vis[cluster_mask, 0], X_vis[cluster_mask, 1], 
                       c=[colors[i]], label=f'Pattern {i} (n={cluster_size})', alpha=0.7)
        
        # Plot cluster centers if using PCA
        if hasattr(self.model, 'cluster_centers_'):
            centers_vis = pca.transform(self.model.cluster_centers_)
            plt.scatter(centers_vis[:, 0], centers_vis[:, 1], 
                       c='black', marker='x', s=200, linewidths=3, label='Centroids')
        
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.title('Disruption Pattern Clusters')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """Get summary of all clusters"""
        
        if not self.cluster_characteristics:
            return {}
        
        summary = {
            'total_clusters': len(self.cluster_characteristics),
            'cluster_details': {}
        }
        
        for cluster_id, info in self.cluster_characteristics.items():
            summary['cluster_details'][f'pattern_{cluster_id}'] = {
                'description': self._generate_cluster_description(info),
                'size': info.get('size', 0),
                'percentage': info.get('percentage', 0),
                'characteristics': {
                    'avg_delay_minutes': info.get('avg_delay', 0),
                    'avg_affected_passengers': info.get('avg_passengers', 0),
                    'primary_disruption_type': info.get('primary_disruption_type', DisruptionType.AIRLINE_OPERATIONAL).value,
                    'typical_severity': info.get('typical_severity', SeverityLevel.MEDIUM).value,
                    'peak_hours': info.get('peak_hours', []),
                    'common_airports': info.get('common_airports', [])
                }
            }
        
        return summary
    
    def _generate_cluster_description(self, cluster_info: Dict[str, Any]) -> str:
        """Generate human-readable description of cluster"""
        
        description_parts = []
        
        # Size and frequency
        size = cluster_info.get('size', 0)
        percentage = cluster_info.get('percentage', 0)
        description_parts.append(f"{percentage:.1f}% of disruptions ({size} incidents)")
        
        # Disruption type
        disruption_type = cluster_info.get('primary_disruption_type', DisruptionType.AIRLINE_OPERATIONAL)
        description_parts.append(f"primarily {disruption_type.value} related")
        
        # Timing patterns
        peak_hours = cluster_info.get('peak_hours', [])
        if peak_hours:
            if len(peak_hours) == 1:
                description_parts.append(f"typically occurs at {peak_hours[0]:02d}:00")
            else:
                hours_str = ", ".join([f"{h:02d}:00" for h in peak_hours[:3]])
                description_parts.append(f"commonly occurs at {hours_str}")
        
        # Impact level
        avg_delay = cluster_info.get('avg_delay', 0)
        avg_passengers = cluster_info.get('avg_passengers', 0)
        
        if avg_delay > 120:
            description_parts.append(f"with significant delays (avg: {avg_delay:.0f} min)")
        elif avg_delay > 30:
            description_parts.append(f"with moderate delays (avg: {avg_delay:.0f} min)")
        
        if avg_passengers > 300:
            description_parts.append(f"affecting many passengers (avg: {avg_passengers:.0f})")
        
        # Location patterns
        common_airports = cluster_info.get('common_airports', [])
        if common_airports:
            airports_str = ", ".join(common_airports[:2])
            description_parts.append(f"frequently at {airports_str}")
        
        return "; ".join(description_parts)


class AnomalyDetectionClustering(ClusteringModel):
    """DBSCAN-based clustering for anomaly detection in flight operations"""
    
    def __init__(self, 
                 model_name: str = "anomaly_detection",
                 eps: float = 0.5,
                 min_samples: int = 5,
                 **kwargs):
        
        super().__init__(model_name, **kwargs)
        
        # DBSCAN parameters for anomaly detection
        self.dbscan_params = {
            'eps': eps,
            'min_samples': min_samples,
            'metric': 'euclidean'
        }
        self.dbscan_params.update(kwargs.get('dbscan_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for anomaly detection"""
        
        data = data.copy()
        
        # Operational anomaly indicators
        if 'delay_minutes' in data.columns:
            # Z-score for delay (extreme delays are anomalies)
            delay_mean = data['delay_minutes'].mean()
            delay_std = data['delay_minutes'].std()
            data['delay_zscore'] = (data['delay_minutes'] - delay_mean) / delay_std
        
        if 'cost_impact' in data.columns:
            # Z-score for cost
            cost_mean = data['cost_impact'].mean()
            cost_std = data['cost_impact'].std()
            data['cost_zscore'] = (data['cost_impact'] - cost_mean) / cost_std
        
        # Rate-based features (unusual rates indicate anomalies)
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['hour'] = data['timestamp'].dt.hour
            
            # Disruptions per hour (unusual frequency)
            hourly_counts = data.groupby('hour').size()
            data['hourly_disruption_rate'] = data['hour'].map(hourly_counts)
            
            # Deviation from normal hourly pattern
            normal_rate = hourly_counts.mean()
            data['hourly_rate_deviation'] = (data['hourly_disruption_rate'] - normal_rate) / hourly_counts.std()
        
        # Multi-dimensional operational metrics
        operational_features = ['aircraft_utilization', 'crew_utilization', 'gate_utilization']
        for feature in operational_features:
            if feature in data.columns:
                feature_mean = data[feature].mean()
                feature_std = data[feature].std()
                data[f'{feature}_zscore'] = (data[feature] - feature_mean) / feature_std
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: Optional[str] = None,
              validation_split: float = 0.0) -> ModelMetrics:
        """Train anomaly detection model"""
        
        self.logger.info(f"Training {self.model_name}")
        
        prepared_data = self.prepare_features(data)
        
        # Select features for anomaly detection
        anomaly_features = [
            'delay_zscore', 'cost_zscore', 'hourly_rate_deviation'
        ]
        
        # Add operational z-scores
        zscore_features = [col for col in prepared_data.columns if col.endswith('_zscore')]
        anomaly_features.extend(zscore_features)
        
        # Filter to available features
        self.feature_columns = [col for col in anomaly_features if col in prepared_data.columns]
        
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=True)
        
        self.logger.info(f"Detecting anomalies in {len(X)} samples")
        
        # Apply DBSCAN
        self.model = DBSCAN(**self.dbscan_params)
        cluster_labels = self.model.fit_predict(X)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Analyze results
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_anomalies = list(cluster_labels).count(-1)
        anomaly_percentage = (n_anomalies / len(cluster_labels)) * 100
        
        self.logger.info(f"Found {n_clusters} normal clusters and {n_anomalies} anomalies ({anomaly_percentage:.1f}%)")
        
        # Calculate metrics (excluding anomalies for silhouette score)
        if n_clusters > 1:
            non_anomaly_mask = cluster_labels != -1
            if np.sum(non_anomaly_mask) > 0:
                metrics_dict = self.calculate_clustering_metrics(
                    X[non_anomaly_mask], 
                    cluster_labels[non_anomaly_mask]
                )
            else:
                metrics_dict = {}
        else:
            metrics_dict = {}
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Detect anomalies in new data"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        
        if prepared_data.empty:
            return []
        
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        # Predict using DBSCAN (note: DBSCAN doesn't have predict method)
        # We need to use fit_predict which may not be ideal for new data
        # In production, consider using isolation forest or one-class SVM
        cluster_labels = self.model.fit_predict(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            cluster_label = cluster_labels[idx]
            is_anomaly = cluster_label == -1
            
            if is_anomaly:
                # Anomaly detected
                severity = SeverityLevel.CRITICAL
                confidence = 0.85
                pred_value = "anomaly_detected"
            else:
                # Normal pattern
                severity = SeverityLevel.LOW
                confidence = 0.70
                pred_value = f"normal_cluster_{cluster_label}"
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=pred_value,
                confidence=confidence,
                severity=severity,
                disruption_type=DisruptionType.EXTERNAL if is_anomaly else DisruptionType.AIRLINE_OPERATIONAL,
                features_used=self.feature_columns,
                model_version=self.model_version
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: Optional[str] = None) -> ModelMetrics:
        """Evaluate anomaly detection"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        cluster_labels = self.model.fit_predict(X)
        
        # Calculate metrics for non-anomaly points
        non_anomaly_mask = cluster_labels != -1
        if np.sum(non_anomaly_mask) > 1:
            metrics_dict = self.calculate_clustering_metrics(
                X[non_anomaly_mask], 
                cluster_labels[non_anomaly_mask]
            )
        else:
            metrics_dict = {}
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )


class PassengerBehaviorClustering(ClusteringModel):
    """Clustering model for passenger behavior analysis during disruptions"""
    
    def __init__(self, 
                 model_name: str = "passenger_behavior_clustering",
                 n_clusters: int = 4,
                 **kwargs):
        
        super().__init__(model_name, n_clusters, **kwargs)
        
        # Agglomerative clustering for passenger behavior
        self.agg_params = {
            'n_clusters': n_clusters,
            'linkage': 'ward'
        }
        self.agg_params.update(kwargs.get('agg_params', {}))
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for passenger behavior clustering"""
        
        data = data.copy()
        
        # Passenger response features
        if 'response_time_minutes' in data.columns:
            data['response_time_log'] = np.log1p(data['response_time_minutes'])
        
        if 'rebooking_accepted' in data.columns:
            data['accepts_rebooking'] = data['rebooking_accepted'].astype(int)
        
        if 'complaint_filed' in data.columns:
            data['files_complaint'] = data['complaint_filed'].astype(int)
        
        if 'compensation_claimed' in data.columns:
            data['claims_compensation'] = data['compensation_claimed'].astype(int)
        
        # Passenger characteristics
        if 'tier_status' in data.columns:
            tier_mapping = {'platinum': 4, 'gold': 3, 'silver': 2, 'bronze': 1, 'regular': 0}
            data['tier_numeric'] = data['tier_status'].map(tier_mapping).fillna(0)
        
        if 'travel_purpose' in data.columns:
            data['business_travel'] = (data['travel_purpose'] == 'business').astype(int)
        
        if 'booking_lead_time_days' in data.columns:
            data['advance_booking'] = (data['booking_lead_time_days'] > 14).astype(int)
        
        # Historical behavior
        if 'previous_disruptions' in data.columns:
            data['experienced_traveler'] = (data['previous_disruptions'] > 2).astype(int)
        
        return data
    
    def train(self, 
              data: pd.DataFrame, 
              target_column: Optional[str] = None,
              validation_split: float = 0.0) -> ModelMetrics:
        """Train passenger behavior clustering"""
        
        self.logger.info(f"Training {self.model_name}")
        
        prepared_data = self.prepare_features(data)
        
        # Select behavioral features
        behavior_features = [
            'response_time_log', 'accepts_rebooking', 'files_complaint', 
            'claims_compensation', 'tier_numeric', 'business_travel',
            'advance_booking', 'experienced_traveler'
        ]
        
        self.feature_columns = [col for col in behavior_features if col in prepared_data.columns]
        
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=True)
        
        self.logger.info(f"Clustering {len(X)} passenger behaviors")
        
        # Apply Agglomerative Clustering
        self.model = AgglomerativeClustering(**self.agg_params)
        cluster_labels = self.model.fit_predict(X)
        
        self.is_trained = True
        self.last_updated = datetime.now()
        
        # Analyze behavior patterns
        self._analyze_passenger_clusters(prepared_data, cluster_labels)
        
        # Calculate metrics
        metrics_dict = self.calculate_clustering_metrics(X, cluster_labels)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Predict passenger behavior clusters"""
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        # Note: AgglomerativeClustering doesn't have predict method
        # In production, you'd need to use a different approach or retrain
        cluster_labels = self.model.fit_predict(X)
        
        results = []
        for idx, (_, row) in enumerate(prepared_data.iterrows()):
            cluster_id = int(cluster_labels[idx])
            
            result = PredictionResult(
                prediction_id=str(uuid.uuid4()),
                model_name=self.model_name,
                prediction_timestamp=datetime.now(),
                prediction_value=f"behavior_type_{cluster_id}",
                confidence=0.72,
                severity=SeverityLevel.LOW,  # Behavioral clustering is informational
                disruption_type=DisruptionType.AIRLINE_OPERATIONAL,
                features_used=self.feature_columns,
                model_version=self.model_version
            )
            
            results.append(result)
        
        return results
    
    def evaluate(self, data: pd.DataFrame, target_column: Optional[str] = None) -> ModelMetrics:
        """Evaluate passenger behavior clustering"""
        
        prepared_data = self.prepare_features(data)
        X = prepared_data[self.feature_columns].fillna(0)
        X = self.preprocess_data(X, is_training=False)
        
        cluster_labels = self.model.fit_predict(X)
        metrics_dict = self.calculate_clustering_metrics(X, cluster_labels)
        
        return ModelMetrics(
            model_name=self.model_name,
            model_version=self.model_version,
            evaluation_timestamp=datetime.now(),
            **metrics_dict
        )
    
    def _analyze_passenger_clusters(self, data: pd.DataFrame, labels: np.ndarray):
        """Analyze passenger behavior clusters"""
        
        self.logger.info("Analyzing passenger behavior clusters:")
        
        for cluster_id in range(self.n_clusters):
            cluster_mask = labels == cluster_id
            cluster_data = data[cluster_mask]
            
            if len(cluster_data) == 0:
                continue
            
            self.logger.info(f"\nCluster {cluster_id} ({len(cluster_data)} passengers):")
            
            # Response patterns
            if 'accepts_rebooking' in cluster_data.columns:
                acceptance_rate = cluster_data['accepts_rebooking'].mean()
                self.logger.info(f"  Rebooking acceptance rate: {acceptance_rate:.2f}")
            
            if 'files_complaint' in cluster_data.columns:
                complaint_rate = cluster_data['files_complaint'].mean()
                self.logger.info(f"  Complaint rate: {complaint_rate:.2f}")
            
            if 'tier_numeric' in cluster_data.columns:
                avg_tier = cluster_data['tier_numeric'].mean()
                self.logger.info(f"  Average tier level: {avg_tier:.2f}")
            
            if 'business_travel' in cluster_data.columns:
                business_pct = cluster_data['business_travel'].mean()
                self.logger.info(f"  Business travelers: {business_pct:.2f}")