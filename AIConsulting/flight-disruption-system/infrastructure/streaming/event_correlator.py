"""
Event Correlation and Pattern Detection Engine
Advanced event correlation system for detecting patterns and relationships
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import math

from .stream_processor import StreamEvent, EventType, BaseStreamProcessor


class CorrelationType(str, Enum):
    """Types of event correlations"""
    CAUSAL = "causal"  # A causes B
    TEMPORAL = "temporal"  # A and B occur together in time
    SPATIAL = "spatial"  # A and B occur in same location
    PATTERN = "pattern"  # A follows a known pattern
    ANOMALY = "anomaly"  # A is anomalous behavior


class PatternType(str, Enum):
    """Types of patterns to detect"""
    CASCADING_DELAYS = "cascading_delays"
    WEATHER_IMPACT = "weather_impact"
    AIRPORT_CONGESTION = "airport_congestion"
    AIRLINE_DISRUPTION = "airline_disruption"
    CREW_SHORTAGE = "crew_shortage"
    AIRCRAFT_ROTATION = "aircraft_rotation"
    SEASONAL_PATTERN = "seasonal_pattern"
    NETWORK_EFFECT = "network_effect"


@dataclass
class CorrelationRule:
    """Rule for event correlation"""
    rule_id: str
    name: str
    correlation_type: CorrelationType
    source_event_types: List[EventType]
    target_event_types: List[EventType]
    time_window_seconds: int
    spatial_radius_km: float
    confidence_threshold: float
    pattern_matcher: Optional[str] = None
    enabled: bool = True


@dataclass
class EventCorrelation:
    """Detected correlation between events"""
    correlation_id: str
    correlation_type: CorrelationType
    pattern_type: Optional[PatternType]
    source_events: List[str]  # Event IDs
    target_events: List[str]  # Event IDs
    confidence_score: float
    detected_timestamp: float
    rule_id: str
    metadata: Dict[str, Any]
    
    @property
    def event_count(self) -> int:
        """Total number of events in correlation"""
        return len(self.source_events) + len(self.target_events)


@dataclass
class DetectedPattern:
    """Detected event pattern"""
    pattern_id: str
    pattern_type: PatternType
    events: List[str]  # Event IDs
    locations: List[str]
    start_time: float
    end_time: Optional[float]
    confidence_score: float
    impact_severity: str
    predicted_evolution: Optional[Dict[str, Any]]
    mitigation_suggestions: List[str]


class EventWindow:
    """Sliding window for event correlation"""
    
    def __init__(self, window_size_seconds: int = 3600):
        self.window_size = window_size_seconds
        self.events: deque = deque()
        self.events_by_type: Dict[EventType, List[StreamEvent]] = defaultdict(list)
        self.events_by_location: Dict[str, List[StreamEvent]] = defaultdict(list)
    
    def add_event(self, event: StreamEvent):
        """Add event to window"""
        self.events.append(event)
        self.events_by_type[event.event_type].append(event)
        
        # Extract location from event data
        locations = self._extract_locations(event)
        for location in locations:
            self.events_by_location[location].append(event)
        
        # Clean old events
        self._clean_old_events()
    
    def get_events_in_timerange(
        self,
        start_time: float,
        end_time: float,
        event_types: Optional[List[EventType]] = None
    ) -> List[StreamEvent]:
        """Get events within time range"""
        filtered_events = []
        
        for event in self.events:
            if start_time <= event.timestamp <= end_time:
                if not event_types or event.event_type in event_types:
                    filtered_events.append(event)
        
        return filtered_events
    
    def get_events_near_location(
        self,
        location: str,
        radius_km: float = 100
    ) -> List[StreamEvent]:
        """Get events near a location"""
        nearby_events = []
        
        # Direct location match
        if location in self.events_by_location:
            nearby_events.extend(self.events_by_location[location])
        
        # For more sophisticated location matching, we would use geospatial queries
        # For now, we'll do simple string matching for airport codes
        for loc, events in self.events_by_location.items():
            if self._calculate_location_distance(location, loc) <= radius_km:
                nearby_events.extend(events)
        
        return nearby_events
    
    def _extract_locations(self, event: StreamEvent) -> List[str]:
        """Extract location information from event"""
        locations = []
        data = event.data
        
        # Common location fields
        location_fields = [
            'location', 'airport', 'departure_airport', 'arrival_airport',
            'affected_airports', 'airports'
        ]
        
        for field in location_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    locations.append(value)
                elif isinstance(value, list):
                    locations.extend(value)
        
        return list(set(locations))  # Remove duplicates
    
    def _calculate_location_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance between locations (simplified)"""
        # This is a simplified implementation
        # In production, you would use actual geospatial calculations
        if loc1 == loc2:
            return 0.0
        
        # Assume different airports are 100km apart on average
        # Same country airports are closer
        if len(loc1) >= 1 and len(loc2) >= 1:
            if loc1[0] == loc2[0]:  # Same country (first letter of IATA)
                return 50.0
            else:
                return 200.0
        
        return 100.0
    
    def _clean_old_events(self):
        """Remove events outside the window"""
        cutoff_time = time.time() - self.window_size
        
        # Clean main events deque
        while self.events and self.events[0].timestamp < cutoff_time:
            old_event = self.events.popleft()
            
            # Clean from type index
            if old_event.event_type in self.events_by_type:
                try:
                    self.events_by_type[old_event.event_type].remove(old_event)
                except ValueError:
                    pass
            
            # Clean from location index
            locations = self._extract_locations(old_event)
            for location in locations:
                if location in self.events_by_location:
                    try:
                        self.events_by_location[location].remove(old_event)
                    except ValueError:
                        pass
    
    def get_event_count(self) -> int:
        """Get current number of events in window"""
        return len(self.events)
    
    def get_events_by_type(self, event_type: EventType) -> List[StreamEvent]:
        """Get all events of specific type"""
        return list(self.events_by_type.get(event_type, []))


class PatternMatcher:
    """Pattern matching engine for detecting known patterns"""
    
    def __init__(self):
        self.pattern_detectors = {
            PatternType.CASCADING_DELAYS: self._detect_cascading_delays,
            PatternType.WEATHER_IMPACT: self._detect_weather_impact,
            PatternType.AIRPORT_CONGESTION: self._detect_airport_congestion,
            PatternType.AIRLINE_DISRUPTION: self._detect_airline_disruption,
            PatternType.NETWORK_EFFECT: self._detect_network_effect
        }
        
        self.logger = logging.getLogger(__name__)
    
    def detect_patterns(self, event_window: EventWindow) -> List[DetectedPattern]:
        """Detect all patterns in the event window"""
        patterns = []
        
        for pattern_type, detector in self.pattern_detectors.items():
            try:
                detected = detector(event_window)
                patterns.extend(detected)
            except Exception as e:
                self.logger.error(f"Error detecting {pattern_type}: {e}")
        
        return patterns
    
    def _detect_cascading_delays(self, window: EventWindow) -> List[DetectedPattern]:
        """Detect cascading delay patterns"""
        patterns = []
        
        # Get flight delay events
        delay_events = []
        for event in window.get_events_by_type(EventType.FLIGHT_UPDATE):
            if (event.data.get('delay_minutes', 0) > 15 or 
                event.data.get('event_type') == 'DELAYED'):
                delay_events.append(event)
        
        if len(delay_events) < 3:
            return patterns
        
        # Group delays by airport and time
        airport_delays = defaultdict(list)
        for event in delay_events:
            airports = []
            if event.data.get('departure_airport'):
                airports.append(event.data['departure_airport'])
            if event.data.get('arrival_airport'):
                airports.append(event.data['arrival_airport'])
            
            for airport in airports:
                airport_delays[airport].append(event)
        
        # Look for cascading patterns
        for airport, events in airport_delays.items():
            if len(events) >= 3:
                # Sort by time
                events.sort(key=lambda e: e.timestamp)
                
                # Check if delays are increasing over time
                delays = [e.data.get('delay_minutes', 0) for e in events]
                if self._is_increasing_pattern(delays):
                    confidence = min(1.0, len(events) / 10.0 + 0.3)
                    
                    patterns.append(DetectedPattern(
                        pattern_id=f"cascade_{airport}_{int(events[0].timestamp)}",
                        pattern_type=PatternType.CASCADING_DELAYS,
                        events=[e.event_id for e in events],
                        locations=[airport],
                        start_time=events[0].timestamp,
                        end_time=events[-1].timestamp,
                        confidence_score=confidence,
                        impact_severity=self._assess_delay_severity(delays),
                        predicted_evolution={
                            'expected_additional_delays': len(events) * 2,
                            'peak_delay_estimate': max(delays) * 1.5,
                            'resolution_time_hours': 3 + len(events) * 0.5
                        },
                        mitigation_suggestions=[
                            f"Implement ground delay program at {airport}",
                            "Consider flight diversions to alternate airports",
                            "Increase ground handling capacity",
                            "Coordinate with air traffic control"
                        ]
                    ))
        
        return patterns
    
    def _detect_weather_impact(self, window: EventWindow) -> List[DetectedPattern]:
        """Detect weather impact patterns"""
        patterns = []
        
        # Get weather and flight events
        weather_events = window.get_events_by_type(EventType.WEATHER_UPDATE)
        flight_events = window.get_events_by_type(EventType.FLIGHT_UPDATE)
        
        if not weather_events or not flight_events:
            return patterns
        
        # Group by location
        for weather_event in weather_events:
            location = weather_event.data.get('location')
            if not location:
                continue
            
            # Find affected flights
            affected_flights = []
            weather_time = weather_event.timestamp
            
            for flight_event in flight_events:
                # Check if flight is at the same location within time window
                flight_airports = [
                    flight_event.data.get('departure_airport'),
                    flight_event.data.get('arrival_airport')
                ]
                
                if (location in flight_airports and
                    abs(flight_event.timestamp - weather_time) < 3600 and  # 1 hour
                    (flight_event.data.get('delay_minutes', 0) > 0 or
                     flight_event.data.get('event_type') == 'CANCELLED')):
                    affected_flights.append(flight_event)
            
            if len(affected_flights) >= 2:
                weather_severity = weather_event.data.get('severity', 'moderate')
                impact_score = weather_event.data.get('flight_impact_score', 0.5)
                
                patterns.append(DetectedPattern(
                    pattern_id=f"weather_{location}_{int(weather_time)}",
                    pattern_type=PatternType.WEATHER_IMPACT,
                    events=[weather_event.event_id] + [f.event_id for f in affected_flights],
                    locations=[location],
                    start_time=weather_event.timestamp,
                    end_time=max(f.timestamp for f in affected_flights),
                    confidence_score=min(1.0, impact_score + len(affected_flights) * 0.1),
                    impact_severity=weather_severity,
                    predicted_evolution={
                        'weather_duration_hours': self._estimate_weather_duration(weather_event.data),
                        'additional_affected_flights': len(affected_flights) * 2,
                        'recovery_time_hours': 2 if weather_severity == 'light' else 6
                    },
                    mitigation_suggestions=[
                        f"Monitor weather conditions at {location}",
                        "Consider preemptive cancellations",
                        "Prepare alternate airport options",
                        "Increase passenger rebooking capacity"
                    ]
                ))
        
        return patterns
    
    def _detect_airport_congestion(self, window: EventWindow) -> List[DetectedPattern]:
        """Detect airport congestion patterns"""
        patterns = []
        
        # Get flight events
        flight_events = window.get_events_by_type(EventType.FLIGHT_UPDATE)
        
        # Group by airport
        airport_activity = defaultdict(list)
        for event in flight_events:
            airports = []
            if event.data.get('departure_airport'):
                airports.append(('departure', event.data['departure_airport']))
            if event.data.get('arrival_airport'):
                airports.append(('arrival', event.data['arrival_airport']))
            
            for direction, airport in airports:
                airport_activity[airport].append((direction, event))
        
        # Analyze congestion patterns
        for airport, activities in airport_activity.items():
            if len(activities) < 5:
                continue
            
            # Count delays and cancellations
            delays = []
            cancellations = 0
            
            for direction, event in activities:
                if event.data.get('delay_minutes', 0) > 0:
                    delays.append(event.data['delay_minutes'])
                if event.data.get('event_type') == 'CANCELLED':
                    cancellations += 1
            
            # Check for congestion indicators
            avg_delay = statistics.mean(delays) if delays else 0
            delay_rate = len(delays) / len(activities)
            
            if avg_delay > 30 or delay_rate > 0.4 or cancellations > 2:
                congestion_score = min(1.0, 
                    (avg_delay / 60.0) * 0.4 + 
                    delay_rate * 0.4 + 
                    (cancellations / len(activities)) * 0.2
                )
                
                patterns.append(DetectedPattern(
                    pattern_id=f"congestion_{airport}_{int(time.time())}",
                    pattern_type=PatternType.AIRPORT_CONGESTION,
                    events=[event.event_id for _, event in activities],
                    locations=[airport],
                    start_time=min(event.timestamp for _, event in activities),
                    end_time=max(event.timestamp for _, event in activities),
                    confidence_score=congestion_score,
                    impact_severity=self._assess_congestion_severity(avg_delay, delay_rate),
                    predicted_evolution={
                        'peak_congestion_hours': 2,
                        'queue_buildup_flights': len(activities),
                        'recovery_time_hours': 4
                    },
                    mitigation_suggestions=[
                        f"Implement ground delay program at {airport}",
                        "Increase ground handling resources",
                        "Consider runway/gate capacity optimization",
                        "Coordinate slot management"
                    ]
                ))
        
        return patterns
    
    def _detect_airline_disruption(self, window: EventWindow) -> List[DetectedPattern]:
        """Detect airline-wide disruption patterns"""
        patterns = []
        
        flight_events = window.get_events_by_type(EventType.FLIGHT_UPDATE)
        
        # Group by airline
        airline_events = defaultdict(list)
        for event in flight_events:
            airline = event.data.get('airline_code')
            if airline:
                airline_events[airline].append(event)
        
        # Analyze each airline
        for airline, events in airline_events.items():
            if len(events) < 3:
                continue
            
            # Calculate disruption metrics
            total_flights = len(events)
            delayed_flights = sum(1 for e in events if e.data.get('delay_minutes', 0) > 15)
            cancelled_flights = sum(1 for e in events if e.data.get('event_type') == 'CANCELLED')
            
            disruption_rate = (delayed_flights + cancelled_flights * 2) / total_flights
            
            if disruption_rate > 0.3:  # 30% disruption rate
                patterns.append(DetectedPattern(
                    pattern_id=f"airline_disruption_{airline}_{int(time.time())}",
                    pattern_type=PatternType.AIRLINE_DISRUPTION,
                    events=[e.event_id for e in events],
                    locations=list(set([
                        loc for e in events 
                        for loc in [e.data.get('departure_airport'), e.data.get('arrival_airport')]
                        if loc
                    ])),
                    start_time=min(e.timestamp for e in events),
                    end_time=max(e.timestamp for e in events),
                    confidence_score=min(1.0, disruption_rate),
                    impact_severity=self._assess_airline_disruption_severity(disruption_rate),
                    predicted_evolution={
                        'affected_flights_next_6h': int(total_flights * 1.5),
                        'recovery_time_hours': 8 + cancelled_flights,
                        'passenger_impact_estimate': total_flights * 150
                    },
                    mitigation_suggestions=[
                        f"Coordinate with {airline} operations center",
                        "Prepare additional rebooking capacity",
                        "Consider interline agreements activation",
                        "Monitor crew and aircraft positioning"
                    ]
                ))
        
        return patterns
    
    def _detect_network_effect(self, window: EventWindow) -> List[DetectedPattern]:
        """Detect network-wide disruption effects"""
        patterns = []
        
        # Get all events that could indicate network effects
        all_events = []
        for event_type in [EventType.FLIGHT_UPDATE, EventType.DISRUPTION_DETECTED]:
            all_events.extend(window.get_events_by_type(event_type))
        
        if len(all_events) < 10:
            return patterns
        
        # Analyze geographical spread
        locations = set()
        airlines = set()
        for event in all_events:
            # Extract locations
            for field in ['departure_airport', 'arrival_airport', 'location', 'affected_airports']:
                if field in event.data:
                    value = event.data[field]
                    if isinstance(value, str):
                        locations.add(value)
                    elif isinstance(value, list):
                        locations.update(value)
            
            # Extract airlines
            if 'airline_code' in event.data:
                airlines.add(event.data['airline_code'])
        
        # Check for network effect indicators
        if len(locations) >= 5 and len(airlines) >= 3:
            disruption_density = len(all_events) / max(len(locations), 1)
            
            if disruption_density > 2:  # Average 2+ events per location
                patterns.append(DetectedPattern(
                    pattern_id=f"network_effect_{int(time.time())}",
                    pattern_type=PatternType.NETWORK_EFFECT,
                    events=[e.event_id for e in all_events],
                    locations=list(locations),
                    start_time=min(e.timestamp for e in all_events),
                    end_time=max(e.timestamp for e in all_events),
                    confidence_score=min(1.0, disruption_density / 5.0),
                    impact_severity="high" if len(locations) > 10 else "medium",
                    predicted_evolution={
                        'cascade_probability': 0.7 if len(locations) > 8 else 0.4,
                        'peak_impact_hours': 4,
                        'full_recovery_hours': 24
                    },
                    mitigation_suggestions=[
                        "Activate network operations center",
                        "Coordinate with multiple airlines",
                        "Consider system-wide ground delay",
                        "Prepare for passenger rebooking surge"
                    ]
                ))
        
        return patterns
    
    # Helper methods
    def _is_increasing_pattern(self, values: List[float]) -> bool:
        """Check if values show an increasing pattern"""
        if len(values) < 3:
            return False
        
        increases = 0
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increases += 1
        
        return increases >= len(values) * 0.6  # 60% increases
    
    def _assess_delay_severity(self, delays: List[int]) -> str:
        """Assess severity of delay pattern"""
        if not delays:
            return "low"
        
        avg_delay = statistics.mean(delays)
        max_delay = max(delays)
        
        if avg_delay > 60 or max_delay > 120:
            return "high"
        elif avg_delay > 30 or max_delay > 60:
            return "medium"
        else:
            return "low"
    
    def _estimate_weather_duration(self, weather_data: Dict[str, Any]) -> float:
        """Estimate weather event duration"""
        condition = weather_data.get('condition', '').lower()
        severity = weather_data.get('severity', '').lower()
        
        base_duration = {
            'thunderstorm': 2,
            'fog': 4,
            'snow': 6,
            'rain': 3,
            'wind': 4
        }
        
        duration = 2  # Default
        for key, value in base_duration.items():
            if key in condition:
                duration = value
                break
        
        # Adjust for severity
        if severity == 'severe':
            duration *= 1.5
        elif severity == 'extreme':
            duration *= 2
        
        return duration
    
    def _assess_congestion_severity(self, avg_delay: float, delay_rate: float) -> str:
        """Assess airport congestion severity"""
        if avg_delay > 60 or delay_rate > 0.6:
            return "high"
        elif avg_delay > 30 or delay_rate > 0.4:
            return "medium"
        else:
            return "low"
    
    def _assess_airline_disruption_severity(self, disruption_rate: float) -> str:
        """Assess airline disruption severity"""
        if disruption_rate > 0.6:
            return "high"
        elif disruption_rate > 0.4:
            return "medium"
        else:
            return "low"


class EventCorrelationEngine(BaseStreamProcessor):
    """Main event correlation engine"""
    
    def __init__(self, kafka_config):
        super().__init__(
            processor_name="event-correlation-engine",
            kafka_config=kafka_config,
            input_topics=[
                "flight.events",
                "disruption.events",
                "external.data",
                "passenger.events"
            ],
            output_topics=["system.metrics", "notifications"]
        )
        
        # Correlation components
        self.event_window = EventWindow(window_size_seconds=7200)  # 2 hours
        self.pattern_matcher = PatternMatcher()
        self.correlation_rules = self._load_correlation_rules()
        
        # Correlation tracking
        self.active_correlations: Dict[str, EventCorrelation] = {}
        self.detected_patterns: Dict[str, DetectedPattern] = {}
        
        # Performance metrics
        self.correlation_metrics = {
            'total_correlations_detected': 0,
            'patterns_detected_by_type': defaultdict(int),
            'correlation_processing_time_avg': 0.0,
            'false_positive_rate': 0.0
        }
    
    async def process_events(self, events: List[StreamEvent]) -> List[StreamEvent]:
        """Process events for correlation and pattern detection"""
        output_events = []
        
        for event in events:
            # Add event to window
            self.event_window.add_event(event)
            
            # Detect correlations
            correlations = await self._detect_correlations(event)
            for correlation in correlations:
                correlation_event = await self._create_correlation_event(correlation)
                if correlation_event:
                    output_events.append(correlation_event)
        
        # Detect patterns periodically
        if len(events) > 0:  # Only if we processed events
            patterns = self.pattern_matcher.detect_patterns(self.event_window)
            for pattern in patterns:
                # Check if pattern is new
                if pattern.pattern_id not in self.detected_patterns:
                    self.detected_patterns[pattern.pattern_id] = pattern
                    pattern_event = await self._create_pattern_event(pattern)
                    if pattern_event:
                        output_events.append(pattern_event)
        
        return output_events
    
    async def _detect_correlations(self, event: StreamEvent) -> List[EventCorrelation]:
        """Detect correlations for a new event"""
        correlations = []
        
        for rule in self.correlation_rules:
            if not rule.enabled:
                continue
            
            if event.event_type not in rule.source_event_types:
                continue
            
            correlation = await self._apply_correlation_rule(event, rule)
            if correlation:
                correlations.append(correlation)
        
        return correlations
    
    async def _apply_correlation_rule(
        self,
        event: StreamEvent,
        rule: CorrelationRule
    ) -> Optional[EventCorrelation]:
        """Apply correlation rule to detect correlations"""
        
        # Get events within time window
        start_time = event.timestamp - rule.time_window_seconds
        end_time = event.timestamp + rule.time_window_seconds
        
        candidate_events = self.event_window.get_events_in_timerange(
            start_time, end_time, rule.target_event_types
        )
        
        if not candidate_events:
            return None
        
        # Apply spatial filtering if needed
        if rule.spatial_radius_km > 0:
            event_locations = self._extract_event_locations(event)
            if event_locations:
                nearby_events = []
                for candidate in candidate_events:
                    candidate_locations = self._extract_event_locations(candidate)
                    if self._check_spatial_proximity(
                        event_locations, candidate_locations, rule.spatial_radius_km
                    ):
                        nearby_events.append(candidate)
                candidate_events = nearby_events
        
        if not candidate_events:
            return None
        
        # Calculate correlation confidence
        confidence = self._calculate_correlation_confidence(
            event, candidate_events, rule
        )
        
        if confidence >= rule.confidence_threshold:
            correlation_id = f"{rule.rule_id}_{event.event_id}_{int(time.time())}"
            
            return EventCorrelation(
                correlation_id=correlation_id,
                correlation_type=rule.correlation_type,
                pattern_type=self._infer_pattern_type(rule),
                source_events=[event.event_id],
                target_events=[e.event_id for e in candidate_events],
                confidence_score=confidence,
                detected_timestamp=time.time(),
                rule_id=rule.rule_id,
                metadata={
                    'rule_name': rule.name,
                    'time_window_used': rule.time_window_seconds,
                    'spatial_radius_used': rule.spatial_radius_km,
                    'candidate_events_count': len(candidate_events)
                }
            )
        
        return None
    
    def _extract_event_locations(self, event: StreamEvent) -> List[str]:
        """Extract location information from event"""
        locations = []
        data = event.data
        
        location_fields = [
            'location', 'airport', 'departure_airport', 'arrival_airport',
            'affected_airports'
        ]
        
        for field in location_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    locations.append(value)
                elif isinstance(value, list):
                    locations.extend(value)
        
        return locations
    
    def _check_spatial_proximity(
        self,
        locations1: List[str],
        locations2: List[str],
        radius_km: float
    ) -> bool:
        """Check if two sets of locations are within proximity"""
        for loc1 in locations1:
            for loc2 in locations2:
                distance = self._calculate_location_distance(loc1, loc2)
                if distance <= radius_km:
                    return True
        return False
    
    def _calculate_location_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance between locations"""
        # Simplified distance calculation
        if loc1 == loc2:
            return 0.0
        
        # Assume airports in same country are closer
        if len(loc1) >= 1 and len(loc2) >= 1:
            if loc1[0] == loc2[0]:
                return 50.0
            else:
                return 200.0
        
        return 100.0
    
    def _calculate_correlation_confidence(
        self,
        source_event: StreamEvent,
        target_events: List[StreamEvent],
        rule: CorrelationRule
    ) -> float:
        """Calculate confidence score for correlation"""
        base_confidence = 0.5
        
        # Temporal proximity boost
        avg_time_diff = statistics.mean([
            abs(source_event.timestamp - target.timestamp)
            for target in target_events
        ])
        
        temporal_boost = max(0, 1 - (avg_time_diff / rule.time_window_seconds))
        base_confidence += temporal_boost * 0.3
        
        # Event count boost
        count_boost = min(0.2, len(target_events) * 0.05)
        base_confidence += count_boost
        
        # Pattern-specific boosts
        if rule.correlation_type == CorrelationType.CAUSAL:
            # Check for logical causality
            if self._check_causal_logic(source_event, target_events):
                base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def _check_causal_logic(
        self,
        source_event: StreamEvent,
        target_events: List[StreamEvent]
    ) -> bool:
        """Check for logical causality between events"""
        # Simplified causal logic checking
        source_type = source_event.event_type
        
        for target in target_events:
            target_type = target.event_type
            
            # Weather -> Flight delays
            if (source_type == EventType.WEATHER_UPDATE and
                target_type == EventType.FLIGHT_UPDATE and
                target.data.get('delay_minutes', 0) > 0):
                return True
            
            # Disruption -> Flight impacts
            if (source_type == EventType.DISRUPTION_DETECTED and
                target_type == EventType.FLIGHT_UPDATE):
                return True
        
        return False
    
    def _infer_pattern_type(self, rule: CorrelationRule) -> Optional[PatternType]:
        """Infer pattern type from correlation rule"""
        if 'weather' in rule.name.lower():
            return PatternType.WEATHER_IMPACT
        elif 'cascading' in rule.name.lower() or 'delay' in rule.name.lower():
            return PatternType.CASCADING_DELAYS
        elif 'congestion' in rule.name.lower():
            return PatternType.AIRPORT_CONGESTION
        elif 'airline' in rule.name.lower():
            return PatternType.AIRLINE_DISRUPTION
        
        return None
    
    async def _create_correlation_event(self, correlation: EventCorrelation) -> Optional[StreamEvent]:
        """Create event for detected correlation"""
        try:
            correlation_data = {
                'correlation_id': correlation.correlation_id,
                'correlation_type': correlation.correlation_type.value,
                'pattern_type': correlation.pattern_type.value if correlation.pattern_type else None,
                'event_count': correlation.event_count,
                'confidence_score': correlation.confidence_score,
                'source_events': correlation.source_events,
                'target_events': correlation.target_events,
                'detected_timestamp': correlation.detected_timestamp,
                'rule_id': correlation.rule_id,
                'metadata': correlation.metadata
            }
            
            return StreamEvent(
                event_id=correlation.correlation_id,
                event_type=EventType.SYSTEM_ALERT,
                timestamp=time.time(),
                source_topic=self.output_topics[0],
                data=correlation_data,
                metadata={
                    'processor': self.processor_name,
                    'alert_type': 'event_correlation',
                    'priority': 'medium' if correlation.confidence_score > 0.7 else 'low'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create correlation event: {e}")
            return None
    
    async def _create_pattern_event(self, pattern: DetectedPattern) -> Optional[StreamEvent]:
        """Create event for detected pattern"""
        try:
            pattern_data = {
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type.value,
                'event_count': len(pattern.events),
                'locations': pattern.locations,
                'confidence_score': pattern.confidence_score,
                'impact_severity': pattern.impact_severity,
                'start_time': pattern.start_time,
                'end_time': pattern.end_time,
                'predicted_evolution': pattern.predicted_evolution,
                'mitigation_suggestions': pattern.mitigation_suggestions,
                'affected_events': pattern.events
            }
            
            # Determine priority based on severity and confidence
            priority = "critical"
            if pattern.impact_severity == "low" or pattern.confidence_score < 0.6:
                priority = "medium"
            elif pattern.confidence_score < 0.8:
                priority = "high"
            
            return StreamEvent(
                event_id=pattern.pattern_id,
                event_type=EventType.SYSTEM_ALERT,
                timestamp=time.time(),
                source_topic=self.output_topics[1],
                data=pattern_data,
                metadata={
                    'processor': self.processor_name,
                    'alert_type': 'pattern_detection',
                    'priority': priority,
                    'requires_action': pattern.impact_severity in ['medium', 'high']
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create pattern event: {e}")
            return None
    
    def _load_correlation_rules(self) -> List[CorrelationRule]:
        """Load predefined correlation rules"""
        return [
            # Weather -> Flight Impact
            CorrelationRule(
                rule_id="weather_flight_impact",
                name="Weather to Flight Impact Correlation",
                correlation_type=CorrelationType.CAUSAL,
                source_event_types=[EventType.WEATHER_UPDATE],
                target_event_types=[EventType.FLIGHT_UPDATE],
                time_window_seconds=3600,  # 1 hour
                spatial_radius_km=50,
                confidence_threshold=0.6
            ),
            
            # Disruption -> Multiple Flight Impacts
            CorrelationRule(
                rule_id="disruption_cascade",
                name="Disruption Cascade Correlation",
                correlation_type=CorrelationType.CAUSAL,
                source_event_types=[EventType.DISRUPTION_DETECTED],
                target_event_types=[EventType.FLIGHT_UPDATE, EventType.PASSENGER_IMPACT],
                time_window_seconds=7200,  # 2 hours
                spatial_radius_km=100,
                confidence_threshold=0.5
            ),
            
            # Temporal clustering of delays
            CorrelationRule(
                rule_id="delay_clustering",
                name="Temporal Delay Clustering",
                correlation_type=CorrelationType.TEMPORAL,
                source_event_types=[EventType.FLIGHT_UPDATE],
                target_event_types=[EventType.FLIGHT_UPDATE],
                time_window_seconds=1800,  # 30 minutes
                spatial_radius_km=0,  # No spatial constraint
                confidence_threshold=0.7
            ),
            
            # Airport congestion pattern
            CorrelationRule(
                rule_id="airport_congestion",
                name="Airport Congestion Pattern",
                correlation_type=CorrelationType.SPATIAL,
                source_event_types=[EventType.FLIGHT_UPDATE],
                target_event_types=[EventType.FLIGHT_UPDATE],
                time_window_seconds=3600,  # 1 hour
                spatial_radius_km=5,  # Same airport
                confidence_threshold=0.6
            )
        ]
    
    def get_correlation_metrics(self) -> Dict[str, Any]:
        """Get correlation engine metrics"""
        return {
            **self.correlation_metrics,
            'active_correlations_count': len(self.active_correlations),
            'detected_patterns_count': len(self.detected_patterns),
            'event_window_size': self.event_window.get_event_count(),
            'correlation_rules_count': len(self.correlation_rules),
            'correlation_rules_enabled': sum(1 for r in self.correlation_rules if r.enabled)
        }