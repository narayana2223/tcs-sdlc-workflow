import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
import redis
import json

from .real_time_monitor import FlightEvent, DisruptionAlert, AlertSeverity


class PatternType(Enum):
    WEATHER_PATTERN = "weather_pattern"
    MAINTENANCE_PATTERN = "maintenance_pattern"
    CREW_PATTERN = "crew_pattern"
    AIRPORT_CONGESTION = "airport_congestion"
    CASCADE_EFFECT = "cascade_effect"
    SEASONAL_TREND = "seasonal_trend"
    ANOMALY_CLUSTER = "anomaly_cluster"


@dataclass
class DisruptionPattern:
    pattern_id: str
    pattern_type: PatternType
    airports_affected: List[str]
    airlines_affected: List[str]
    start_time: datetime
    duration_hours: float
    confidence_score: float
    severity_score: float
    affected_flights: List[str]
    root_cause: str
    propagation_risk: float
    financial_impact: float
    passenger_impact: int
    pattern_features: Dict[str, float]
    similar_historical_patterns: List[str]


@dataclass
class EarlyWarning:
    warning_id: str
    pattern_type: PatternType
    predicted_start: datetime
    predicted_duration: float
    confidence: float
    severity: AlertSeverity
    affected_airports: List[str]
    affected_flights_estimate: int
    recommended_actions: List[str]
    created_at: datetime
    alert_threshold_reached: bool


class PatternDetector:
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 1)
        )
        
        self.flight_history = deque(maxlen=10000)
        self.active_patterns = {}
        self.pattern_history = {}
        self.early_warnings = {}
        
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        self.pattern_thresholds = {
            PatternType.WEATHER_PATTERN: {'min_flights': 5, 'min_airports': 2, 'severity': 0.6},
            PatternType.MAINTENANCE_PATTERN: {'min_flights': 3, 'min_aircraft': 2, 'severity': 0.7},
            PatternType.CREW_PATTERN: {'min_flights': 4, 'min_bases': 2, 'severity': 0.5},
            PatternType.AIRPORT_CONGESTION: {'min_flights': 10, 'min_delay': 30, 'severity': 0.6},
            PatternType.CASCADE_EFFECT: {'min_connections': 20, 'cascade_depth': 3, 'severity': 0.8},
            PatternType.SEASONAL_TREND: {'min_duration': 24, 'trend_strength': 0.7, 'severity': 0.4},
            PatternType.ANOMALY_CLUSTER: {'min_anomalies': 5, 'cluster_density': 0.3, 'severity': 0.8}
        }
        
    async def analyze_patterns(self, recent_events: List[FlightEvent]) -> List[DisruptionPattern]:
        """Main pattern analysis function."""
        self.flight_history.extend(recent_events)
        
        patterns = []
        
        patterns.extend(await self._detect_weather_patterns())
        patterns.extend(await self._detect_maintenance_patterns())
        patterns.extend(await self._detect_crew_patterns())
        patterns.extend(await self._detect_airport_congestion())
        patterns.extend(await self._detect_cascade_effects())
        patterns.extend(await self._detect_seasonal_trends())
        patterns.extend(await self._detect_anomaly_clusters())
        
        self._update_active_patterns(patterns)
        return patterns
        
    async def _detect_weather_patterns(self) -> List[DisruptionPattern]:
        """Detect weather-related disruption patterns."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 6]
        
        weather_groups = defaultdict(list)
        for event in recent_events:
            if event.weather_data and self._has_weather_impact(event):
                for airport in [event.origin, event.destination]:
                    weather_groups[airport].append(event)
                    
        for airport, events in weather_groups.items():
            if len(events) >= self.pattern_thresholds[PatternType.WEATHER_PATTERN]['min_flights']:
                pattern = await self._create_weather_pattern(airport, events)
                if pattern:
                    patterns.append(pattern)
                    
        return patterns
        
    async def _detect_maintenance_patterns(self) -> List[DisruptionPattern]:
        """Detect maintenance-related disruption patterns."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 12]
        
        aircraft_groups = defaultdict(list)
        for event in recent_events:
            if event.maintenance_alerts:
                aircraft_groups[event.aircraft_id].append(event)
                
        maintenance_types = defaultdict(list)
        for aircraft_id, events in aircraft_groups.items():
            for event in events:
                for alert in event.maintenance_alerts:
                    maintenance_type = alert.split(':')[0] if ':' in alert else alert
                    maintenance_types[maintenance_type].extend(events)
                    
        for maintenance_type, events in maintenance_types.items():
            unique_aircraft = len(set(e.aircraft_id for e in events))
            if (len(events) >= self.pattern_thresholds[PatternType.MAINTENANCE_PATTERN]['min_flights'] and
                unique_aircraft >= self.pattern_thresholds[PatternType.MAINTENANCE_PATTERN]['min_aircraft']):
                
                pattern = await self._create_maintenance_pattern(maintenance_type, events)
                if pattern:
                    patterns.append(pattern)
                    
        return patterns
        
    async def _detect_crew_patterns(self) -> List[DisruptionPattern]:
        """Detect crew-related disruption patterns."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 8]
        
        crew_issues = defaultdict(list)
        for event in recent_events:
            if event.crew_data and self._has_crew_issues(event):
                base_airport = self._get_crew_base(event)
                crew_issues[base_airport].append(event)
                
        for base, events in crew_issues.items():
            if len(events) >= self.pattern_thresholds[PatternType.CREW_PATTERN]['min_flights']:
                pattern = await self._create_crew_pattern(base, events)
                if pattern:
                    patterns.append(pattern)
                    
        return patterns
        
    async def _detect_airport_congestion(self) -> List[DisruptionPattern]:
        """Detect airport congestion patterns."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 4]
        
        airport_delays = defaultdict(list)
        for event in recent_events:
            if event.delay_minutes >= 30:
                airport_delays[event.origin].append(event)
                airport_delays[event.destination].append(event)
                
        for airport, events in airport_delays.items():
            if len(events) >= self.pattern_thresholds[PatternType.AIRPORT_CONGESTION]['min_flights']:
                avg_delay = sum(e.delay_minutes for e in events) / len(events)
                if avg_delay >= self.pattern_thresholds[PatternType.AIRPORT_CONGESTION]['min_delay']:
                    pattern = await self._create_congestion_pattern(airport, events)
                    if pattern:
                        patterns.append(pattern)
                        
        return patterns
        
    async def _detect_cascade_effects(self) -> List[DisruptionPattern]:
        """Detect cascade disruption effects."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 6]
        
        connection_graph = self._build_connection_graph(recent_events)
        cascade_clusters = self._find_cascade_clusters(connection_graph)
        
        for cluster in cascade_clusters:
            if (len(cluster) >= self.pattern_thresholds[PatternType.CASCADE_EFFECT]['min_connections']):
                pattern = await self._create_cascade_pattern(cluster)
                if pattern:
                    patterns.append(pattern)
                    
        return patterns
        
    async def _detect_seasonal_trends(self) -> List[DisruptionPattern]:
        """Detect seasonal disruption trends."""
        patterns = []
        
        historical_data = self._get_historical_seasonal_data()
        current_period_data = self._get_current_period_data()
        
        trend_strength = self._calculate_trend_strength(historical_data, current_period_data)
        
        if (trend_strength >= self.pattern_thresholds[PatternType.SEASONAL_TREND]['trend_strength']):
            pattern = await self._create_seasonal_pattern(historical_data, current_period_data)
            if pattern:
                patterns.append(pattern)
                
        return patterns
        
    async def _detect_anomaly_clusters(self) -> List[DisruptionPattern]:
        """Detect clusters of anomalous events."""
        patterns = []
        
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).hours < 4]
        
        if len(recent_events) < 10:
            return patterns
            
        feature_matrix = self._extract_anomaly_features(recent_events)
        
        try:
            scaled_features = self.scaler.fit_transform(feature_matrix)
            anomaly_scores = self.anomaly_detector.fit_predict(scaled_features)
            
            anomaly_events = [event for i, event in enumerate(recent_events) if anomaly_scores[i] == -1]
            
            if len(anomaly_events) >= self.pattern_thresholds[PatternType.ANOMALY_CLUSTER]['min_anomalies']:
                clusters = self._cluster_anomalous_events(anomaly_events)
                
                for cluster in clusters:
                    pattern = await self._create_anomaly_pattern(cluster)
                    if pattern:
                        patterns.append(pattern)
                        
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            
        return patterns
        
    async def generate_early_warnings(self, patterns: List[DisruptionPattern]) -> List[EarlyWarning]:
        """Generate early warnings based on detected patterns."""
        warnings = []
        
        for pattern in patterns:
            if self._should_generate_warning(pattern):
                warning = await self._create_early_warning(pattern)
                warnings.append(warning)
                
        self._update_early_warnings(warnings)
        return warnings
        
    def _has_weather_impact(self, event: FlightEvent) -> bool:
        """Check if event has weather impact."""
        if not event.weather_data:
            return False
            
        for location_data in event.weather_data.values():
            visibility = location_data.get('visibility_miles', 10)
            wind_speed = location_data.get('wind_speed_mph', 0)
            precipitation = location_data.get('precipitation_intensity', 0)
            
            if visibility < 5 or wind_speed > 20 or precipitation > 0.3:
                return True
                
        return False
        
    def _has_crew_issues(self, event: FlightEvent) -> bool:
        """Check if event has crew-related issues."""
        for crew_id, crew_info in event.crew_data.items():
            availability = crew_info.get('availability_score', 1.0)
            fatigue = crew_info.get('fatigue_score', 0.0)
            
            if availability < 0.8 or fatigue > 0.6:
                return True
                
        return False
        
    def _get_crew_base(self, event: FlightEvent) -> str:
        """Get crew base airport for the event."""
        return event.origin
        
    def _build_connection_graph(self, events: List[FlightEvent]) -> Dict[str, Set[str]]:
        """Build flight connection graph."""
        graph = defaultdict(set)
        
        for event in events:
            for connecting_flight in event.connecting_flights:
                graph[event.flight_id].add(connecting_flight)
                graph[connecting_flight].add(event.flight_id)
                
        return graph
        
    def _find_cascade_clusters(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find connected components representing cascade effects."""
        visited = set()
        clusters = []
        
        def dfs(node, current_cluster):
            if node in visited:
                return
            visited.add(node)
            current_cluster.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, current_cluster)
                
        for flight_id in graph:
            if flight_id not in visited:
                cluster = []
                dfs(flight_id, cluster)
                if len(cluster) > 1:
                    clusters.append(cluster)
                    
        return clusters
        
    def _get_historical_seasonal_data(self) -> Dict[str, float]:
        """Get historical seasonal patterns."""
        current_month = datetime.now().month
        seasonal_key = f"seasonal_patterns:{current_month}"
        
        data = self.redis_client.hgetall(seasonal_key)
        return {k.decode(): float(v) for k, v in data.items()} if data else {}
        
    def _get_current_period_data(self) -> Dict[str, float]:
        """Get current period disruption data."""
        recent_events = [e for e in self.flight_history if (datetime.now() - e.timestamp).days < 7]
        
        return {
            'avg_delay': sum(e.delay_minutes for e in recent_events) / len(recent_events) if recent_events else 0,
            'cancellation_rate': sum(1 for e in recent_events if e.status == 'cancelled') / len(recent_events) if recent_events else 0,
            'disruption_rate': sum(1 for e in recent_events if e.delay_minutes > 30) / len(recent_events) if recent_events else 0
        }
        
    def _calculate_trend_strength(self, historical: Dict[str, float], current: Dict[str, float]) -> float:
        """Calculate strength of seasonal trend."""
        if not historical or not current:
            return 0.0
            
        differences = []
        for metric in ['avg_delay', 'cancellation_rate', 'disruption_rate']:
            hist_val = historical.get(metric, 0)
            curr_val = current.get(metric, 0)
            
            if hist_val > 0:
                diff = abs(curr_val - hist_val) / hist_val
                differences.append(diff)
                
        return sum(differences) / len(differences) if differences else 0.0
        
    def _extract_anomaly_features(self, events: List[FlightEvent]) -> np.ndarray:
        """Extract features for anomaly detection."""
        features = []
        
        for event in events:
            feature_vector = [
                event.delay_minutes,
                event.passenger_count,
                len(event.maintenance_alerts),
                len(event.connecting_flights),
                1 if event.status == 'cancelled' else 0,
                self._calculate_weather_severity(event.weather_data),
                self._calculate_crew_severity(event.crew_data),
                event.scheduled_departure.hour,
                event.scheduled_departure.weekday(),
                hash(event.origin) % 100,
                hash(event.destination) % 100
            ]
            features.append(feature_vector)
            
        return np.array(features)
        
    def _calculate_weather_severity(self, weather_data: Dict[str, Any]) -> float:
        """Calculate weather severity score."""
        if not weather_data:
            return 0.0
            
        max_severity = 0.0
        for location_data in weather_data.values():
            visibility = location_data.get('visibility_miles', 10)
            wind_speed = location_data.get('wind_speed_mph', 0)
            precipitation = location_data.get('precipitation_intensity', 0)
            
            severity = 0.0
            if visibility < 1:
                severity += 0.5
            elif visibility < 3:
                severity += 0.3
                
            if wind_speed > 40:
                severity += 0.4
            elif wind_speed > 25:
                severity += 0.2
                
            if precipitation > 0.8:
                severity += 0.4
            elif precipitation > 0.5:
                severity += 0.2
                
            max_severity = max(max_severity, min(severity, 1.0))
            
        return max_severity
        
    def _calculate_crew_severity(self, crew_data: Dict[str, Any]) -> float:
        """Calculate crew-related severity score."""
        if not crew_data:
            return 0.0
            
        total_severity = 0.0
        crew_count = 0
        
        for crew_info in crew_data.values():
            availability = crew_info.get('availability_score', 1.0)
            fatigue = crew_info.get('fatigue_score', 0.0)
            
            severity = (1 - availability) * 0.6 + fatigue * 0.4
            total_severity += severity
            crew_count += 1
            
        return total_severity / crew_count if crew_count > 0 else 0.0
        
    def _cluster_anomalous_events(self, anomaly_events: List[FlightEvent]) -> List[List[FlightEvent]]:
        """Cluster anomalous events by similarity."""
        if len(anomaly_events) < 2:
            return [anomaly_events] if anomaly_events else []
            
        feature_matrix = self._extract_anomaly_features(anomaly_events)
        
        try:
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            cluster_labels = dbscan.fit_predict(feature_matrix)
            
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append(anomaly_events[i])
                
            return list(clusters.values())
            
        except Exception as e:
            self.logger.error(f"Error clustering anomalous events: {e}")
            return [anomaly_events]
            
    async def _create_weather_pattern(self, airport: str, events: List[FlightEvent]) -> Optional[DisruptionPattern]:
        """Create a weather disruption pattern."""
        try:
            pattern_id = f"weather_{airport}_{int(datetime.now().timestamp())}"
            
            airports_affected = list(set([airport] + [e.origin for e in events] + [e.destination for e in events]))
            airlines_affected = list(set(e.airline_code for e in events))
            
            start_time = min(e.timestamp for e in events)
            duration = (max(e.timestamp for e in events) - start_time).total_seconds() / 3600
            
            avg_delay = sum(e.delay_minutes for e in events) / len(events)
            severity_score = min(avg_delay / 120, 1.0)
            
            weather_conditions = {}
            for event in events:
                for location, data in event.weather_data.items():
                    if location not in weather_conditions:
                        weather_conditions[location] = data
                        
            root_cause = self._determine_weather_cause(weather_conditions)
            
            return DisruptionPattern(
                pattern_id=pattern_id,
                pattern_type=PatternType.WEATHER_PATTERN,
                airports_affected=airports_affected,
                airlines_affected=airlines_affected,
                start_time=start_time,
                duration_hours=duration,
                confidence_score=0.85,
                severity_score=severity_score,
                affected_flights=[e.flight_id for e in events],
                root_cause=root_cause,
                propagation_risk=self._calculate_weather_propagation_risk(events),
                financial_impact=self._estimate_financial_impact(events),
                passenger_impact=sum(e.passenger_count for e in events),
                pattern_features=self._extract_weather_features(weather_conditions),
                similar_historical_patterns=self._find_similar_patterns(PatternType.WEATHER_PATTERN, weather_conditions)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating weather pattern: {e}")
            return None
            
    def _determine_weather_cause(self, weather_conditions: Dict[str, Any]) -> str:
        """Determine primary weather cause."""
        causes = []
        
        for location, data in weather_conditions.items():
            if data.get('visibility_miles', 10) < 3:
                causes.append("low_visibility")
            if data.get('wind_speed_mph', 0) > 25:
                causes.append("high_winds")
            if data.get('precipitation_intensity', 0) > 0.5:
                causes.append("heavy_precipitation")
            if data.get('temperature_f', 50) < 32:
                causes.append("freezing_conditions")
                
        return ", ".join(set(causes)) if causes else "adverse_weather"
        
    def _calculate_weather_propagation_risk(self, events: List[FlightEvent]) -> float:
        """Calculate risk of weather pattern propagation."""
        unique_airports = set()
        for event in events:
            unique_airports.add(event.origin)
            unique_airports.add(event.destination)
            
        hub_airports = ['ATL', 'ORD', 'DFW', 'DEN', 'LAX', 'PHX', 'LAS', 'DTW', 'MSP', 'SEA']
        hub_count = len([airport for airport in unique_airports if airport in hub_airports])
        
        return min(hub_count * 0.3 + len(unique_airports) * 0.1, 1.0)
        
    def _estimate_financial_impact(self, events: List[FlightEvent]) -> float:
        """Estimate financial impact of disruption pattern."""
        total_impact = 0.0
        
        for event in events:
            delay_cost = event.delay_minutes * 50
            passenger_comp = event.passenger_count * (100 if event.delay_minutes > 180 else 0)
            operational_cost = 5000 if event.status == 'cancelled' else event.delay_minutes * 25
            
            total_impact += delay_cost + passenger_comp + operational_cost
            
        return total_impact
        
    def _extract_weather_features(self, weather_conditions: Dict[str, Any]) -> Dict[str, float]:
        """Extract weather pattern features."""
        features = {}
        
        for location, data in weather_conditions.items():
            features[f"{location}_visibility"] = data.get('visibility_miles', 10)
            features[f"{location}_wind_speed"] = data.get('wind_speed_mph', 0)
            features[f"{location}_precipitation"] = data.get('precipitation_intensity', 0)
            features[f"{location}_temperature"] = data.get('temperature_f', 50)
            
        return features
        
    def _find_similar_patterns(self, pattern_type: PatternType, conditions: Dict[str, Any]) -> List[str]:
        """Find similar historical patterns."""
        return []
        
    async def _create_maintenance_pattern(self, maintenance_type: str, events: List[FlightEvent]) -> Optional[DisruptionPattern]:
        """Create a maintenance disruption pattern."""
        # Similar structure to weather pattern but focused on maintenance
        return None
        
    async def _create_crew_pattern(self, base: str, events: List[FlightEvent]) -> Optional[DisruptionPattern]:
        """Create a crew-related disruption pattern."""
        # Similar structure focusing on crew issues
        return None
        
    async def _create_congestion_pattern(self, airport: str, events: List[FlightEvent]) -> Optional[DisruptionPattern]:
        """Create airport congestion pattern."""
        # Similar structure focusing on airport congestion
        return None
        
    async def _create_cascade_pattern(self, cluster: List[str]) -> Optional[DisruptionPattern]:
        """Create cascade effect pattern."""
        # Similar structure focusing on cascade effects
        return None
        
    async def _create_seasonal_pattern(self, historical: Dict[str, float], current: Dict[str, float]) -> Optional[DisruptionPattern]:
        """Create seasonal trend pattern."""
        # Similar structure focusing on seasonal trends
        return None
        
    async def _create_anomaly_pattern(self, cluster: List[FlightEvent]) -> Optional[DisruptionPattern]:
        """Create anomaly cluster pattern."""
        # Similar structure focusing on anomalous events
        return None
        
    def _should_generate_warning(self, pattern: DisruptionPattern) -> bool:
        """Determine if early warning should be generated."""
        return (pattern.severity_score > 0.6 and 
                pattern.confidence_score > 0.7 and
                pattern.propagation_risk > 0.5)
                
    async def _create_early_warning(self, pattern: DisruptionPattern) -> EarlyWarning:
        """Create early warning from pattern."""
        warning_id = f"warning_{pattern.pattern_id}"
        
        predicted_start = datetime.now() + timedelta(minutes=30)
        predicted_duration = pattern.duration_hours * 1.2
        
        severity_mapping = {
            (0, 0.3): AlertSeverity.LOW,
            (0.3, 0.6): AlertSeverity.MEDIUM,
            (0.6, 0.8): AlertSeverity.HIGH,
            (0.8, 1.0): AlertSeverity.CRITICAL
        }
        
        severity = AlertSeverity.LOW
        for (min_score, max_score), alert_severity in severity_mapping.items():
            if min_score <= pattern.severity_score < max_score:
                severity = alert_severity
                break
                
        recommendations = self._generate_pattern_recommendations(pattern)
        
        return EarlyWarning(
            warning_id=warning_id,
            pattern_type=pattern.pattern_type,
            predicted_start=predicted_start,
            predicted_duration=predicted_duration,
            confidence=pattern.confidence_score,
            severity=severity,
            affected_airports=pattern.airports_affected,
            affected_flights_estimate=len(pattern.affected_flights),
            recommended_actions=recommendations,
            created_at=datetime.now(),
            alert_threshold_reached=pattern.severity_score > 0.7
        )
        
    def _generate_pattern_recommendations(self, pattern: DisruptionPattern) -> List[str]:
        """Generate recommendations based on pattern type."""
        recommendations = []
        
        if pattern.pattern_type == PatternType.WEATHER_PATTERN:
            recommendations.extend([
                "Monitor weather conditions closely",
                "Consider proactive flight cancellations",
                "Prepare ground delay programs",
                "Coordinate with airport operations"
            ])
            
        elif pattern.pattern_type == PatternType.MAINTENANCE_PATTERN:
            recommendations.extend([
                "Increase maintenance inspections",
                "Prepare backup aircraft",
                "Review maintenance schedules",
                "Coordinate with maintenance bases"
            ])
            
        elif pattern.pattern_type == PatternType.CREW_PATTERN:
            recommendations.extend([
                "Contact crew scheduling",
                "Prepare backup crew",
                "Review duty time limits",
                "Consider crew repositioning"
            ])
            
        return recommendations
        
    def _update_active_patterns(self, patterns: List[DisruptionPattern]):
        """Update active patterns in memory and cache."""
        for pattern in patterns:
            self.active_patterns[pattern.pattern_id] = pattern
            
        now = datetime.now()
        expired_patterns = [
            pid for pid, pattern in self.active_patterns.items()
            if (now - pattern.start_time).total_seconds() > pattern.duration_hours * 3600 * 2
        ]
        
        for pid in expired_patterns:
            self.pattern_history[pid] = self.active_patterns.pop(pid)
            
    def _update_early_warnings(self, warnings: List[EarlyWarning]):
        """Update early warnings."""
        for warning in warnings:
            self.early_warnings[warning.warning_id] = warning
            
    def get_active_patterns(self) -> List[DisruptionPattern]:
        """Get currently active patterns."""
        return list(self.active_patterns.values())
        
    def get_active_warnings(self) -> List[EarlyWarning]:
        """Get active early warnings."""
        return list(self.early_warnings.values())