import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import json
from kafka_producer import FlightKafkaProducer
from kafka_consumer import FlightKafkaConsumer, ConsumerManager
from config import KafkaConfig

logger = structlog.get_logger()

class StreamProcessor:
    """Real-time stream processing for flight disruption events"""
    
    def __init__(self, kafka_config: KafkaConfig):
        self.config = kafka_config
        self.producer = FlightKafkaProducer(kafka_config)
        self.consumer_manager = ConsumerManager(kafka_config)
        self.event_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.correlation_cache: Dict[str, Dict[str, Any]] = {}
        self.pattern_detectors: List[PatternDetector] = []
        self.running = False
        
    async def start(self):
        """Start the stream processor"""
        try:
            await self.producer.start()
            
            # Create consumers for stream processing
            await self.consumer_manager.create_consumer(
                consumer_name="stream_processor",
                consumer_group="stream-processing-group",
                topics=['flight.events', 'disruption.events', 'passenger.events']
            )
            
            # Register service handlers
            self.consumer_manager.register_service_handler(
                'stream_processing', 
                self._process_stream_event
            )
            
            # Initialize pattern detectors
            self._initialize_pattern_detectors()
            
            # Start consumers
            consumer_tasks = await self.consumer_manager.start_all_consumers()
            
            # Start background processing tasks
            processing_tasks = [
                asyncio.create_task(self._correlation_processor()),
                asyncio.create_task(self._pattern_detection_processor()),
                asyncio.create_task(self._window_cleanup_processor())
            ]
            
            self.running = True
            logger.info("Stream processor started successfully")
            
            # Return all tasks for monitoring
            return consumer_tasks + processing_tasks
            
        except Exception as e:
            logger.error("Failed to start stream processor", error=str(e))
            raise
    
    async def stop(self):
        """Stop the stream processor"""
        self.running = False
        await self.consumer_manager.stop_all_consumers()
        await self.producer.stop()
        logger.info("Stream processor stopped")
    
    async def _process_stream_event(self, event_data: Dict[str, Any], message):
        """Process individual stream event"""
        try:
            event_type = event_data.get('event_type')
            entity_id = event_data.get('entity_id')
            correlation_id = event_data.get('correlation_id')
            timestamp = datetime.fromisoformat(event_data.get('timestamp'))
            
            # Add to time window
            self.event_windows[message.topic].append({
                'event_data': event_data,
                'message': message,
                'processed_at': datetime.utcnow()
            })
            
            # Process correlation if available
            if correlation_id:
                await self._process_correlation(correlation_id, event_data)
            
            # Run real-time pattern detection
            await self._detect_patterns(event_data, message.topic)
            
            # Generate derived events if needed
            await self._generate_derived_events(event_data, message.topic)
            
            logger.debug(
                "Stream event processed",
                topic=message.topic,
                event_type=event_type,
                entity_id=entity_id
            )
            
        except Exception as e:
            logger.error("Error processing stream event", error=str(e))
    
    async def _process_correlation(self, correlation_id: str, event_data: Dict[str, Any]):
        """Process event correlation"""
        if correlation_id not in self.correlation_cache:
            self.correlation_cache[correlation_id] = {
                'events': [],
                'created_at': datetime.utcnow()
            }
        
        self.correlation_cache[correlation_id]['events'].append(event_data)
        
        # Check for complete correlation patterns
        correlated_events = self.correlation_cache[correlation_id]['events']
        await self._analyze_correlation_pattern(correlation_id, correlated_events)
    
    async def _analyze_correlation_pattern(self, correlation_id: str, events: List[Dict[str, Any]]):
        """Analyze correlated events for patterns"""
        try:
            # Example: Disruption -> Passenger Impact -> Notification chain
            event_types = [e.get('event_type') for e in events]
            
            if self._is_complete_disruption_chain(event_types):
                # Generate processing time metrics
                start_time = min(datetime.fromisoformat(e['timestamp']) for e in events)
                end_time = max(datetime.fromisoformat(e['timestamp']) for e in events)
                processing_time = (end_time - start_time).total_seconds()
                
                # Send metrics event
                await self.producer.send_metrics_event(
                    event_type='processing_time',
                    service_name='disruption_chain',
                    data={
                        'correlation_id': correlation_id,
                        'processing_time_seconds': processing_time,
                        'event_count': len(events),
                        'event_types': event_types
                    }
                )
                
                logger.info(
                    "Complete disruption chain processed",
                    correlation_id=correlation_id,
                    processing_time=processing_time
                )
        
        except Exception as e:
            logger.error("Error analyzing correlation pattern", error=str(e))
    
    def _is_complete_disruption_chain(self, event_types: List[str]) -> bool:
        """Check if events form a complete disruption processing chain"""
        required_events = ['disruption_detected', 'passenger_affected', 'notification_sent']
        return all(event_type in event_types for event_type in required_events)
    
    async def _detect_patterns(self, event_data: Dict[str, Any], topic: str):
        """Run pattern detection on current event"""
        for detector in self.pattern_detectors:
            try:
                if detector.can_process(topic, event_data):
                    pattern = await detector.detect(event_data, self.event_windows[topic])
                    if pattern:
                        await self._handle_detected_pattern(pattern)
            except Exception as e:
                logger.error(
                    "Pattern detector error",
                    detector=detector.__class__.__name__,
                    error=str(e)
                )
    
    async def _handle_detected_pattern(self, pattern: Dict[str, Any]):
        """Handle detected pattern"""
        pattern_type = pattern.get('type')
        confidence = pattern.get('confidence', 0.0)
        
        if confidence > 0.8:  # High confidence threshold
            # Send pattern event
            await self.producer.send_external_data_event(
                event_type='pattern_detected',
                source='stream_processor',
                data=pattern
            )
            
            logger.info(
                "High confidence pattern detected",
                pattern_type=pattern_type,
                confidence=confidence
            )
    
    async def _generate_derived_events(self, event_data: Dict[str, Any], topic: str):
        """Generate derived events based on processing logic"""
        try:
            event_type = event_data.get('event_type')
            
            # Example: Generate cascade events for disruptions
            if event_type == 'disruption_detected' and topic == 'disruption.events':
                disruption_data = event_data.get('data', {})
                
                # Check if this disruption might cause cascading effects
                if self._may_cause_cascade(disruption_data):
                    await self.producer.send_agent_decision_event(
                        event_type='cascade_risk_detected',
                        agent_id='cascade_detector',
                        data={
                            'source_disruption_id': event_data.get('entity_id'),
                            'risk_level': self._calculate_cascade_risk(disruption_data),
                            'affected_routes': disruption_data.get('affected_routes', [])
                        },
                        correlation_id=event_data.get('correlation_id')
                    )
        
        except Exception as e:
            logger.error("Error generating derived events", error=str(e))
    
    def _may_cause_cascade(self, disruption_data: Dict[str, Any]) -> bool:
        """Check if disruption may cause cascading effects"""
        # Simple heuristics - in production would use ML models
        delay_minutes = disruption_data.get('delay_minutes', 0)
        airport = disruption_data.get('departure_airport', '')
        aircraft_type = disruption_data.get('aircraft_type', '')
        
        # Major airports with high delay risk
        major_airports = ['LHR', 'CDG', 'FRA', 'AMS', 'MAD']
        
        return (
            delay_minutes > 120 or  # Long delays
            airport in major_airports or  # Major hub airports
            'A380' in aircraft_type  # Large aircraft
        )
    
    def _calculate_cascade_risk(self, disruption_data: Dict[str, Any]) -> float:
        """Calculate cascade risk score"""
        risk_score = 0.0
        
        # Delay factor
        delay_minutes = disruption_data.get('delay_minutes', 0)
        risk_score += min(delay_minutes / 60.0, 5.0) * 0.3
        
        # Airport factor
        major_airports = ['LHR', 'CDG', 'FRA', 'AMS', 'MAD']
        if disruption_data.get('departure_airport') in major_airports:
            risk_score += 0.4
        
        # Time of day factor
        hour = datetime.utcnow().hour
        if 6 <= hour <= 10 or 17 <= hour <= 21:  # Peak hours
            risk_score += 0.3
        
        return min(risk_score, 1.0)
    
    async def _correlation_processor(self):
        """Background processor for correlation cleanup"""
        while self.running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                # Clean up old correlations
                expired_correlations = [
                    corr_id for corr_id, data in self.correlation_cache.items()
                    if data['created_at'] < cutoff_time
                ]
                
                for corr_id in expired_correlations:
                    del self.correlation_cache[corr_id]
                
                if expired_correlations:
                    logger.debug(f"Cleaned up {len(expired_correlations)} expired correlations")
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error("Error in correlation processor", error=str(e))
                await asyncio.sleep(60)
    
    async def _pattern_detection_processor(self):
        """Background processor for batch pattern detection"""
        while self.running:
            try:
                # Run batch pattern detection every minute
                for topic, events in self.event_windows.items():
                    if len(events) > 10:  # Minimum events for batch processing
                        await self._run_batch_pattern_detection(topic, list(events))
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error("Error in pattern detection processor", error=str(e))
                await asyncio.sleep(60)
    
    async def _run_batch_pattern_detection(self, topic: str, events: List[Dict[str, Any]]):
        """Run batch pattern detection on event window"""
        try:
            # Example: Detect spike in disruption events
            if topic == 'disruption.events':
                recent_events = [
                    e for e in events 
                    if (datetime.utcnow() - e['processed_at']).seconds < 600  # Last 10 minutes
                ]
                
                if len(recent_events) > 5:  # Spike threshold
                    await self.producer.send_external_data_event(
                        event_type='disruption_spike_detected',
                        source='stream_processor',
                        data={
                            'topic': topic,
                            'event_count': len(recent_events),
                            'time_window_minutes': 10,
                            'spike_threshold': 5
                        }
                    )
                    
                    logger.warning(
                        "Disruption spike detected",
                        event_count=len(recent_events)
                    )
        
        except Exception as e:
            logger.error("Error in batch pattern detection", error=str(e))
    
    async def _window_cleanup_processor(self):
        """Background processor for cleaning up event windows"""
        while self.running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=2)
                
                for topic, window in self.event_windows.items():
                    # Remove old events
                    while window and window[0]['processed_at'] < cutoff_time:
                        window.popleft()
                
                await asyncio.sleep(600)  # Run every 10 minutes
                
            except Exception as e:
                logger.error("Error in window cleanup processor", error=str(e))
                await asyncio.sleep(60)
    
    def _initialize_pattern_detectors(self):
        """Initialize pattern detectors"""
        self.pattern_detectors = [
            AirportCongestionDetector(),
            WeatherImpactDetector(),
            CascadeEffectDetector(),
            FrequencyAnomalyDetector()
        ]
        
        logger.info(f"Initialized {len(self.pattern_detectors)} pattern detectors")
    
    async def get_processor_metrics(self) -> Dict[str, Any]:
        """Get stream processor metrics"""
        return {
            'status': 'running' if self.running else 'stopped',
            'event_windows': {
                topic: len(events) for topic, events in self.event_windows.items()
            },
            'correlation_cache_size': len(self.correlation_cache),
            'pattern_detectors_count': len(self.pattern_detectors),
            'producer_metrics': await self.producer.get_producer_metrics()
        }

class PatternDetector:
    """Base class for pattern detectors"""
    
    def can_process(self, topic: str, event_data: Dict[str, Any]) -> bool:
        """Check if this detector can process the event"""
        return True
    
    async def detect(self, event_data: Dict[str, Any], event_window: deque) -> Optional[Dict[str, Any]]:
        """Detect patterns in the event stream"""
        raise NotImplementedError

class AirportCongestionDetector(PatternDetector):
    """Detects airport congestion patterns"""
    
    def can_process(self, topic: str, event_data: Dict[str, Any]) -> bool:
        return topic == 'flight.events' and event_data.get('event_type') in ['flight_delayed', 'flight_cancelled']
    
    async def detect(self, event_data: Dict[str, Any], event_window: deque) -> Optional[Dict[str, Any]]:
        try:
            current_airport = event_data.get('data', {}).get('departure_airport')
            if not current_airport:
                return None
            
            # Count recent events at same airport
            recent_count = sum(
                1 for event in event_window
                if (datetime.utcnow() - event['processed_at']).seconds < 1800  # Last 30 minutes
                and event['event_data'].get('data', {}).get('departure_airport') == current_airport
            )
            
            if recent_count > 3:  # Congestion threshold
                return {
                    'type': 'airport_congestion',
                    'confidence': min(recent_count / 10.0, 1.0),
                    'airport': current_airport,
                    'affected_flights': recent_count,
                    'time_window_minutes': 30
                }
        
        except Exception as e:
            logger.error("Airport congestion detection error", error=str(e))
        
        return None

class WeatherImpactDetector(PatternDetector):
    """Detects weather-related disruption patterns"""
    
    def can_process(self, topic: str, event_data: Dict[str, Any]) -> bool:
        return topic == 'disruption.events' and 'weather' in str(event_data.get('data', {})).lower()
    
    async def detect(self, event_data: Dict[str, Any], event_window: deque) -> Optional[Dict[str, Any]]:
        try:
            # Count weather-related disruptions in recent window
            weather_events = [
                event for event in event_window
                if (datetime.utcnow() - event['processed_at']).seconds < 3600  # Last hour
                and 'weather' in str(event['event_data'].get('data', {})).lower()
            ]
            
            if len(weather_events) > 2:
                return {
                    'type': 'weather_impact_pattern',
                    'confidence': min(len(weather_events) / 5.0, 1.0),
                    'affected_flights': len(weather_events),
                    'time_window_minutes': 60
                }
        
        except Exception as e:
            logger.error("Weather impact detection error", error=str(e))
        
        return None

class CascadeEffectDetector(PatternDetector):
    """Detects cascade effects in disruptions"""
    
    async def detect(self, event_data: Dict[str, Any], event_window: deque) -> Optional[Dict[str, Any]]:
        # Complex cascade detection logic would go here
        return None

class FrequencyAnomalyDetector(PatternDetector):
    """Detects anomalies in event frequencies"""
    
    async def detect(self, event_data: Dict[str, Any], event_window: deque) -> Optional[Dict[str, Any]]:
        # Frequency anomaly detection logic would go here
        return None