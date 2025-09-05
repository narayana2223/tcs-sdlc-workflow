import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import redis
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from ..models.base_models import PredictionResult, ModelMetrics
from ..models.time_series_models import XGBoostTimeSeriesModel, LSTMForecastingModel, WeatherImpactModel
from ..models.classification_models import DisruptionTypeClassifier, SeverityClassifier, CancellationProbabilityClassifier
from ..models.regression_models import DelayPredictionModel, CostImpactModel, RecoveryTimeModel
from ..models.clustering_models import DisruptionPatternClustering, AnomalyDetectionClustering


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DisruptionType(Enum):
    WEATHER = "weather"
    MECHANICAL = "mechanical"
    CREW = "crew"
    AIRPORT = "airport"
    AIR_TRAFFIC = "air_traffic"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class FlightEvent:
    flight_id: str
    airline_code: str
    aircraft_id: str
    origin: str
    destination: str
    scheduled_departure: datetime
    actual_departure: Optional[datetime]
    scheduled_arrival: datetime
    actual_arrival: Optional[datetime]
    status: str
    delay_minutes: int
    cancellation_code: Optional[str]
    weather_data: Dict[str, Any]
    maintenance_alerts: List[str]
    crew_data: Dict[str, Any]
    passenger_count: int
    connecting_flights: List[str]
    timestamp: datetime


@dataclass
class DisruptionAlert:
    alert_id: str
    flight_id: str
    alert_type: DisruptionType
    severity: AlertSeverity
    predicted_delay: int
    confidence_score: float
    impact_score: float
    affected_passengers: int
    financial_impact: float
    recommended_actions: List[str]
    created_at: datetime
    expires_at: datetime
    data_sources: List[str]


@dataclass
class MonitoringMetrics:
    total_flights_monitored: int
    alerts_generated: int
    predictions_made: int
    accuracy_rate: float
    false_positive_rate: float
    processing_latency_ms: float
    model_drift_score: float
    data_quality_score: float


class RealTimeMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )
        
        self.kafka_consumer = KafkaConsumer(
            'flight-events',
            'weather-updates',
            'maintenance-alerts',
            'crew-status',
            bootstrap_servers=config.get('kafka_servers', ['localhost:9092']),
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='disruption-monitor'
        )
        
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=config.get('kafka_servers', ['localhost:9092']),
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.thread_pool = ThreadPoolExecutor(max_workers=config.get('max_workers', 10))
        
        self.models = self._initialize_models()
        self.metrics = MonitoringMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.flight_cache = {}
        self.alert_history = {}
        
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize all ML models for real-time prediction."""
        return {
            'time_series': {
                'xgboost': XGBoostTimeSeriesModel(),
                'lstm': LSTMForecastingModel(),
                'weather_impact': WeatherImpactModel()
            },
            'classification': {
                'disruption_type': DisruptionTypeClassifier(),
                'severity': SeverityClassifier(),
                'cancellation_prob': CancellationProbabilityClassifier()
            },
            'regression': {
                'delay_prediction': DelayPredictionModel(),
                'cost_impact': CostImpactModel(),
                'recovery_time': RecoveryTimeModel()
            },
            'clustering': {
                'pattern_analysis': DisruptionPatternClustering(),
                'anomaly_detection': AnomalyDetectionClustering()
            }
        }
        
    async def start_monitoring(self):
        """Start the real-time monitoring system."""
        self.is_running = True
        self.logger.info("Starting real-time flight disruption monitoring...")
        
        tasks = [
            asyncio.create_task(self._consume_events()),
            asyncio.create_task(self._periodic_health_check()),
            asyncio.create_task(self._update_metrics()),
            asyncio.create_task(self._cleanup_expired_alerts())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in monitoring system: {e}")
            await self.stop_monitoring()
            
    async def stop_monitoring(self):
        """Stop the monitoring system gracefully."""
        self.is_running = False
        self.kafka_consumer.close()
        self.kafka_producer.close()
        self.thread_pool.shutdown(wait=True)
        self.logger.info("Monitoring system stopped")
        
    async def _consume_events(self):
        """Main event consumption loop."""
        while self.is_running:
            try:
                message_pack = self.kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        await self._process_event(message.topic, message.value)
                        
            except KafkaError as e:
                self.logger.error(f"Kafka error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1)
                
    async def _process_event(self, topic: str, data: Dict[str, Any]):
        """Process individual events and generate predictions."""
        start_time = time.time()
        
        try:
            if topic == 'flight-events':
                event = self._parse_flight_event(data)
                await self._analyze_flight_event(event)
            elif topic == 'weather-updates':
                await self._analyze_weather_update(data)
            elif topic == 'maintenance-alerts':
                await self._analyze_maintenance_alert(data)
            elif topic == 'crew-status':
                await self._analyze_crew_status(data)
                
        except Exception as e:
            self.logger.error(f"Error processing {topic} event: {e}")
        finally:
            processing_time = (time.time() - start_time) * 1000
            self._update_processing_metrics(processing_time)
            
    def _parse_flight_event(self, data: Dict[str, Any]) -> FlightEvent:
        """Parse raw flight event data into structured format."""
        return FlightEvent(
            flight_id=data['flight_id'],
            airline_code=data['airline_code'],
            aircraft_id=data['aircraft_id'],
            origin=data['origin'],
            destination=data['destination'],
            scheduled_departure=datetime.fromisoformat(data['scheduled_departure']),
            actual_departure=datetime.fromisoformat(data['actual_departure']) if data.get('actual_departure') else None,
            scheduled_arrival=datetime.fromisoformat(data['scheduled_arrival']),
            actual_arrival=datetime.fromisoformat(data['actual_arrival']) if data.get('actual_arrival') else None,
            status=data['status'],
            delay_minutes=data.get('delay_minutes', 0),
            cancellation_code=data.get('cancellation_code'),
            weather_data=data.get('weather_data', {}),
            maintenance_alerts=data.get('maintenance_alerts', []),
            crew_data=data.get('crew_data', {}),
            passenger_count=data.get('passenger_count', 0),
            connecting_flights=data.get('connecting_flights', []),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
        
    async def _analyze_flight_event(self, event: FlightEvent):
        """Analyze flight event and generate predictions."""
        self.flight_cache[event.flight_id] = event
        self.metrics.total_flights_monitored += 1
        
        features = self._extract_features(event)
        predictions = await self._generate_predictions(features, event)
        
        if self._should_generate_alert(predictions, event):
            alert = self._create_alert(predictions, event)
            await self._publish_alert(alert)
            
    def _extract_features(self, event: FlightEvent) -> Dict[str, Any]:
        """Extract features for ML model prediction."""
        now = datetime.now()
        
        features = {
            'flight_features': {
                'delay_minutes': event.delay_minutes,
                'passenger_count': event.passenger_count,
                'aircraft_age': self._get_aircraft_age(event.aircraft_id),
                'route_complexity': self._calculate_route_complexity(event.origin, event.destination),
                'time_to_departure': (event.scheduled_departure - now).total_seconds() / 3600,
                'day_of_week': event.scheduled_departure.weekday(),
                'hour_of_day': event.scheduled_departure.hour,
                'connecting_flights_count': len(event.connecting_flights)
            },
            'weather_features': {
                'origin_weather_score': self._calculate_weather_score(event.weather_data.get('origin', {})),
                'destination_weather_score': self._calculate_weather_score(event.weather_data.get('destination', {})),
                'route_weather_score': self._calculate_route_weather_score(event.origin, event.destination)
            },
            'operational_features': {
                'maintenance_alert_count': len(event.maintenance_alerts),
                'maintenance_severity': self._calculate_maintenance_severity(event.maintenance_alerts),
                'crew_availability': event.crew_data.get('availability_score', 1.0),
                'crew_fatigue_score': event.crew_data.get('fatigue_score', 0.0),
                'airport_congestion_origin': self._get_airport_congestion(event.origin),
                'airport_congestion_destination': self._get_airport_congestion(event.destination)
            },
            'historical_features': {
                'route_delay_history': self._get_route_delay_history(event.origin, event.destination),
                'aircraft_reliability': self._get_aircraft_reliability(event.aircraft_id),
                'seasonal_patterns': self._get_seasonal_patterns(event.scheduled_departure),
                'disruption_cascade_risk': self._calculate_cascade_risk(event)
            }
        }
        
        return features
        
    async def _generate_predictions(self, features: Dict[str, Any], event: FlightEvent) -> Dict[str, Any]:
        """Generate predictions using all available models."""
        predictions = {}
        
        feature_array = self._features_to_array(features)
        
        try:
            delay_pred = self.models['regression']['delay_prediction'].predict(feature_array)
            predictions['delay_prediction'] = {
                'minutes': float(delay_pred.prediction_value),
                'confidence': float(delay_pred.confidence_score)
            }
            
            disruption_type = self.models['classification']['disruption_type'].predict(feature_array)
            predictions['disruption_type'] = {
                'type': disruption_type.prediction_value,
                'confidence': float(disruption_type.confidence_score)
            }
            
            severity = self.models['classification']['severity'].predict(feature_array)
            predictions['severity'] = {
                'level': severity.prediction_value,
                'confidence': float(severity.confidence_score)
            }
            
            cancellation_prob = self.models['classification']['cancellation_prob'].predict(feature_array)
            predictions['cancellation_probability'] = {
                'probability': float(cancellation_prob.prediction_value),
                'confidence': float(cancellation_prob.confidence_score)
            }
            
            cost_impact = self.models['regression']['cost_impact'].predict(feature_array)
            predictions['cost_impact'] = {
                'amount': float(cost_impact.prediction_value),
                'confidence': float(cost_impact.confidence_score)
            }
            
            recovery_time = self.models['regression']['recovery_time'].predict(feature_array)
            predictions['recovery_time'] = {
                'minutes': float(recovery_time.prediction_value),
                'confidence': float(recovery_time.confidence_score)
            }
            
            anomaly_score = self.models['clustering']['anomaly_detection'].predict(feature_array)
            predictions['anomaly_score'] = float(anomaly_score.prediction_value)
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}")
            
        self.metrics.predictions_made += 1
        return predictions
        
    def _should_generate_alert(self, predictions: Dict[str, Any], event: FlightEvent) -> bool:
        """Determine if an alert should be generated based on predictions."""
        if not predictions:
            return False
            
        delay_threshold = 30
        severity_threshold = 0.6
        cancellation_threshold = 0.3
        anomaly_threshold = 0.8
        
        conditions = [
            predictions.get('delay_prediction', {}).get('minutes', 0) > delay_threshold,
            predictions.get('severity', {}).get('confidence', 0) > severity_threshold,
            predictions.get('cancellation_probability', {}).get('probability', 0) > cancellation_threshold,
            predictions.get('anomaly_score', 0) > anomaly_threshold
        ]
        
        return any(conditions)
        
    def _create_alert(self, predictions: Dict[str, Any], event: FlightEvent) -> DisruptionAlert:
        """Create a disruption alert from predictions."""
        severity_mapping = {
            'low': AlertSeverity.LOW,
            'medium': AlertSeverity.MEDIUM,
            'high': AlertSeverity.HIGH,
            'critical': AlertSeverity.CRITICAL
        }
        
        disruption_mapping = {
            'weather': DisruptionType.WEATHER,
            'mechanical': DisruptionType.MECHANICAL,
            'crew': DisruptionType.CREW,
            'airport': DisruptionType.AIRPORT,
            'air_traffic': DisruptionType.AIR_TRAFFIC,
            'security': DisruptionType.SECURITY,
            'other': DisruptionType.OTHER
        }
        
        alert_severity = severity_mapping.get(
            predictions.get('severity', {}).get('level', 'low'), 
            AlertSeverity.LOW
        )
        
        disruption_type = disruption_mapping.get(
            predictions.get('disruption_type', {}).get('type', 'other'),
            DisruptionType.OTHER
        )
        
        recommended_actions = self._generate_recommendations(predictions, event)
        
        alert = DisruptionAlert(
            alert_id=f"alert_{event.flight_id}_{int(time.time())}",
            flight_id=event.flight_id,
            alert_type=disruption_type,
            severity=alert_severity,
            predicted_delay=int(predictions.get('delay_prediction', {}).get('minutes', 0)),
            confidence_score=predictions.get('severity', {}).get('confidence', 0.0),
            impact_score=self._calculate_impact_score(predictions, event),
            affected_passengers=event.passenger_count + len(event.connecting_flights) * 150,
            financial_impact=predictions.get('cost_impact', {}).get('amount', 0.0),
            recommended_actions=recommended_actions,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4),
            data_sources=['flight_data', 'weather_data', 'maintenance_data', 'crew_data']
        )
        
        return alert
        
    def _generate_recommendations(self, predictions: Dict[str, Any], event: FlightEvent) -> List[str]:
        """Generate actionable recommendations based on predictions."""
        recommendations = []
        
        delay_minutes = predictions.get('delay_prediction', {}).get('minutes', 0)
        disruption_type = predictions.get('disruption_type', {}).get('type', 'other')
        cancellation_prob = predictions.get('cancellation_probability', {}).get('probability', 0)
        
        if delay_minutes > 60:
            recommendations.append("Consider rebooking passengers on alternative flights")
            recommendations.append("Activate passenger care protocols")
            
        if cancellation_prob > 0.5:
            recommendations.append("Prepare cancellation procedures and passenger notifications")
            recommendations.append("Secure accommodation for stranded passengers")
            
        if disruption_type == 'weather':
            recommendations.append("Monitor weather conditions and consider route changes")
            recommendations.append("Coordinate with airport operations for ground delays")
            
        elif disruption_type == 'mechanical':
            recommendations.append("Dispatch maintenance team immediately")
            recommendations.append("Prepare backup aircraft if available")
            
        elif disruption_type == 'crew':
            recommendations.append("Contact crew scheduling for replacement crew")
            recommendations.append("Check duty time regulations and rest requirements")
            
        if event.passenger_count > 200:
            recommendations.append("Activate crisis communication protocols")
            recommendations.append("Deploy additional customer service staff")
            
        return recommendations
        
    def _calculate_impact_score(self, predictions: Dict[str, Any], event: FlightEvent) -> float:
        """Calculate overall impact score for the disruption."""
        delay_score = min(predictions.get('delay_prediction', {}).get('minutes', 0) / 180, 1.0)
        passenger_score = min(event.passenger_count / 400, 1.0)
        cost_score = min(predictions.get('cost_impact', {}).get('amount', 0) / 100000, 1.0)
        cascade_score = min(len(event.connecting_flights) / 10, 1.0)
        
        return (delay_score * 0.3 + passenger_score * 0.25 + cost_score * 0.25 + cascade_score * 0.2)
        
    async def _publish_alert(self, alert: DisruptionAlert):
        """Publish alert to Kafka topic for agent consumption."""
        try:
            alert_data = asdict(alert)
            alert_data['created_at'] = alert.created_at.isoformat()
            alert_data['expires_at'] = alert.expires_at.isoformat()
            alert_data['severity'] = alert.severity.value
            alert_data['alert_type'] = alert.alert_type.value
            
            self.kafka_producer.send('disruption-alerts', alert_data)
            self.kafka_producer.flush()
            
            self.alert_history[alert.alert_id] = alert
            self.metrics.alerts_generated += 1
            
            self.logger.info(f"Generated alert {alert.alert_id} for flight {alert.flight_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing alert: {e}")
            
    async def _analyze_weather_update(self, data: Dict[str, Any]):
        """Process weather updates and trigger predictions for affected flights."""
        airport_code = data.get('airport_code')
        weather_conditions = data.get('conditions', {})
        
        affected_flights = self._get_flights_by_airport(airport_code)
        
        for flight_id in affected_flights:
            if flight_id in self.flight_cache:
                event = self.flight_cache[flight_id]
                event.weather_data[airport_code] = weather_conditions
                await self._analyze_flight_event(event)
                
    async def _analyze_maintenance_alert(self, data: Dict[str, Any]):
        """Process maintenance alerts and update affected flights."""
        aircraft_id = data.get('aircraft_id')
        alert_type = data.get('alert_type')
        severity = data.get('severity', 'low')
        
        affected_flights = self._get_flights_by_aircraft(aircraft_id)
        
        for flight_id in affected_flights:
            if flight_id in self.flight_cache:
                event = self.flight_cache[flight_id]
                event.maintenance_alerts.append(f"{alert_type}:{severity}")
                await self._analyze_flight_event(event)
                
    async def _analyze_crew_status(self, data: Dict[str, Any]):
        """Process crew status updates and update affected flights."""
        crew_id = data.get('crew_id')
        status = data.get('status')
        fatigue_score = data.get('fatigue_score', 0.0)
        
        affected_flights = self._get_flights_by_crew(crew_id)
        
        for flight_id in affected_flights:
            if flight_id in self.flight_cache:
                event = self.flight_cache[flight_id]
                event.crew_data[crew_id] = {
                    'status': status,
                    'fatigue_score': fatigue_score,
                    'availability_score': 1.0 if status == 'available' else 0.0
                }
                await self._analyze_flight_event(event)
                
    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to numpy array for ML models."""
        feature_list = []
        
        for category in features.values():
            for value in category.values():
                if isinstance(value, (int, float)):
                    feature_list.append(value)
                elif isinstance(value, str):
                    feature_list.append(hash(value) % 1000)
                else:
                    feature_list.append(0)
                    
        return np.array(feature_list).reshape(1, -1)
        
    def _get_aircraft_age(self, aircraft_id: str) -> float:
        """Get aircraft age from cache or database."""
        aircraft_data = self.redis_client.hget('aircraft_data', aircraft_id)
        if aircraft_data:
            data = json.loads(aircraft_data)
            return data.get('age_years', 10)
        return 10
        
    def _calculate_route_complexity(self, origin: str, destination: str) -> float:
        """Calculate route complexity score."""
        route_key = f"{origin}_{destination}"
        route_data = self.redis_client.hget('route_complexity', route_key)
        if route_data:
            return float(json.loads(route_data).get('complexity_score', 0.5))
        return 0.5
        
    def _calculate_weather_score(self, weather_data: Dict[str, Any]) -> float:
        """Calculate weather impact score."""
        if not weather_data:
            return 0.0
            
        visibility = weather_data.get('visibility_miles', 10)
        wind_speed = weather_data.get('wind_speed_mph', 0)
        precipitation = weather_data.get('precipitation_intensity', 0)
        
        score = 0.0
        if visibility < 3:
            score += 0.4
        if wind_speed > 25:
            score += 0.3
        if precipitation > 0.5:
            score += 0.3
            
        return min(score, 1.0)
        
    def _calculate_route_weather_score(self, origin: str, destination: str) -> float:
        """Calculate weather score along the route."""
        return 0.0
        
    def _calculate_maintenance_severity(self, alerts: List[str]) -> float:
        """Calculate overall maintenance severity."""
        if not alerts:
            return 0.0
            
        severity_scores = {'low': 0.2, 'medium': 0.5, 'high': 0.8, 'critical': 1.0}
        max_severity = 0.0
        
        for alert in alerts:
            if ':' in alert:
                severity = alert.split(':')[1]
                max_severity = max(max_severity, severity_scores.get(severity, 0.0))
                
        return max_severity
        
    def _get_airport_congestion(self, airport_code: str) -> float:
        """Get current airport congestion score."""
        congestion_data = self.redis_client.hget('airport_congestion', airport_code)
        if congestion_data:
            return float(json.loads(congestion_data).get('congestion_score', 0.0))
        return 0.0
        
    def _get_route_delay_history(self, origin: str, destination: str) -> float:
        """Get historical delay patterns for the route."""
        route_key = f"{origin}_{destination}"
        history_data = self.redis_client.hget('route_history', route_key)
        if history_data:
            return float(json.loads(history_data).get('avg_delay_minutes', 0))
        return 0.0
        
    def _get_aircraft_reliability(self, aircraft_id: str) -> float:
        """Get aircraft reliability score."""
        reliability_data = self.redis_client.hget('aircraft_reliability', aircraft_id)
        if reliability_data:
            return float(json.loads(reliability_data).get('reliability_score', 0.9))
        return 0.9
        
    def _get_seasonal_patterns(self, departure_time: datetime) -> float:
        """Get seasonal disruption patterns."""
        month = departure_time.month
        seasonal_scores = {1: 0.8, 2: 0.7, 3: 0.5, 4: 0.3, 5: 0.2, 6: 0.4, 
                          7: 0.6, 8: 0.5, 9: 0.3, 10: 0.4, 11: 0.6, 12: 0.8}
        return seasonal_scores.get(month, 0.5)
        
    def _calculate_cascade_risk(self, event: FlightEvent) -> float:
        """Calculate risk of cascade disruptions."""
        connecting_count = len(event.connecting_flights)
        passenger_ratio = event.passenger_count / 400
        hub_airports = ['ATL', 'ORD', 'DFW', 'DEN', 'LAX', 'PHX', 'LAS', 'DTW', 'MSP', 'SEA']
        
        hub_factor = 1.5 if event.origin in hub_airports or event.destination in hub_airports else 1.0
        return min((connecting_count * 0.1 + passenger_ratio * 0.5) * hub_factor, 1.0)
        
    def _get_flights_by_airport(self, airport_code: str) -> List[str]:
        """Get flights affected by airport conditions."""
        flight_ids = []
        for flight_id, event in self.flight_cache.items():
            if event.origin == airport_code or event.destination == airport_code:
                flight_ids.append(flight_id)
        return flight_ids
        
    def _get_flights_by_aircraft(self, aircraft_id: str) -> List[str]:
        """Get flights using specific aircraft."""
        flight_ids = []
        for flight_id, event in self.flight_cache.items():
            if event.aircraft_id == aircraft_id:
                flight_ids.append(flight_id)
        return flight_ids
        
    def _get_flights_by_crew(self, crew_id: str) -> List[str]:
        """Get flights assigned to specific crew member."""
        return []
        
    def _update_processing_metrics(self, processing_time_ms: float):
        """Update processing time metrics."""
        current_latency = self.metrics.processing_latency_ms
        self.metrics.processing_latency_ms = (current_latency * 0.9) + (processing_time_ms * 0.1)
        
    async def _periodic_health_check(self):
        """Perform periodic health checks and model validation."""
        while self.is_running:
            try:
                await asyncio.sleep(300)
                await self._validate_model_performance()
                await self._check_data_quality()
                await self._update_model_drift()
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                
    async def _update_metrics(self):
        """Update monitoring metrics periodically."""
        while self.is_running:
            try:
                await asyncio.sleep(60)
                metrics_data = asdict(self.metrics)
                metrics_data['timestamp'] = datetime.now().isoformat()
                
                self.kafka_producer.send('monitoring-metrics', metrics_data)
                self.kafka_producer.flush()
                
            except Exception as e:
                self.logger.error(f"Metrics update error: {e}")
                
    async def _cleanup_expired_alerts(self):
        """Clean up expired alerts from memory."""
        while self.is_running:
            try:
                await asyncio.sleep(600)
                now = datetime.now()
                expired_alerts = [
                    alert_id for alert_id, alert in self.alert_history.items()
                    if alert.expires_at < now
                ]
                
                for alert_id in expired_alerts:
                    del self.alert_history[alert_id]
                    
                self.logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")
                
            except Exception as e:
                self.logger.error(f"Alert cleanup error: {e}")
                
    async def _validate_model_performance(self):
        """Validate model performance against actual outcomes."""
        pass
        
    async def _check_data_quality(self):
        """Check data quality metrics."""
        pass
        
    async def _update_model_drift(self):
        """Monitor and update model drift metrics."""
        pass
        
    def get_metrics(self) -> MonitoringMetrics:
        """Get current monitoring metrics."""
        return self.metrics
        
    def get_active_alerts(self) -> List[DisruptionAlert]:
        """Get all active alerts."""
        now = datetime.now()
        return [alert for alert in self.alert_history.values() if alert.expires_at > now]