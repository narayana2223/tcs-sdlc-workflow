"""
Real-time Stream Processing Engine
Kafka Streams implementation for flight disruption management
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from confluent_kafka import Consumer, Producer, KafkaException
from confluent_kafka.admin import AdminClient

from ..kafka.kafka_config import KafkaConfig, TopicType
from ..kafka.producers import ProducerFactory


class ProcessingState(str, Enum):
    """Stream processing states"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class EventType(str, Enum):
    """Event processing types"""
    FLIGHT_UPDATE = "flight_update"
    WEATHER_UPDATE = "weather_update"
    DISRUPTION_DETECTED = "disruption_detected"
    PASSENGER_IMPACT = "passenger_impact"
    ML_PREDICTION = "ml_prediction"
    SYSTEM_ALERT = "system_alert"


@dataclass
class StreamEvent:
    """Standardized stream event"""
    event_id: str
    event_type: EventType
    timestamp: float
    source_topic: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    processed_timestamp: Optional[float] = None
    
    @property
    def age_seconds(self) -> float:
        """Get event age in seconds"""
        return time.time() - self.timestamp
    
    def add_processing_metadata(self, processor_name: str, processing_time_ms: float):
        """Add processing metadata"""
        if 'processing_chain' not in self.metadata:
            self.metadata['processing_chain'] = []
        
        self.metadata['processing_chain'].append({
            'processor': processor_name,
            'timestamp': time.time(),
            'processing_time_ms': processing_time_ms
        })


@dataclass
class ProcessingMetrics:
    """Stream processing metrics"""
    events_processed: int = 0
    events_failed: int = 0
    processing_time_ms_avg: float = 0.0
    processing_time_ms_max: float = 0.0
    last_processed_time: Optional[float] = None
    throughput_events_per_second: float = 0.0
    backlog_size: int = 0
    
    def update(self, processing_time_ms: float, success: bool = True):
        """Update metrics"""
        if success:
            self.events_processed += 1
        else:
            self.events_failed += 1
        
        # Update processing time metrics
        if self.processing_time_ms_avg == 0:
            self.processing_time_ms_avg = processing_time_ms
        else:
            alpha = 0.1  # Exponential moving average
            self.processing_time_ms_avg = (
                alpha * processing_time_ms + 
                (1 - alpha) * self.processing_time_ms_avg
            )
        
        self.processing_time_ms_max = max(self.processing_time_ms_max, processing_time_ms)
        self.last_processed_time = time.time()


class BaseStreamProcessor(ABC):
    """Base class for stream processors"""
    
    def __init__(
        self,
        processor_name: str,
        kafka_config: KafkaConfig,
        input_topics: List[str],
        output_topics: List[str] = None
    ):
        self.processor_name = processor_name
        self.kafka_config = kafka_config
        self.input_topics = input_topics
        self.output_topics = output_topics or []
        
        self.logger = logging.getLogger(f"{__name__}.{processor_name}")
        self.state = ProcessingState.STOPPED
        self.metrics = ProcessingMetrics()
        
        # Kafka components
        self.consumer: Optional[Consumer] = None
        self.producer: Optional[Producer] = None
        
        # Processing configuration
        self.batch_size = 100
        self.max_processing_time_ms = 5000
        self.enable_exactly_once = True
        
        # Event buffer for batching
        self.event_buffer: deque = deque()
        self.buffer_timeout_seconds = 1.0
        self.last_buffer_flush = time.time()
        
        # Error handling
        self.max_retries = 3
        self.dead_letter_topic = TopicType.DEAD_LETTER
    
    async def start(self):
        """Start the stream processor"""
        try:
            self.logger.info(f"Starting stream processor: {self.processor_name}")
            
            # Initialize Kafka consumer
            consumer_config = {
                **self.kafka_config.consumer_config,
                'group.id': f"{self.processor_name}-consumer-group",
                'auto.offset.reset': 'latest',
                'enable.auto.commit': False,  # Manual commit for exactly-once
                'max.poll.interval.ms': 300000,  # 5 minutes
            }
            
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe(self.input_topics)
            
            # Initialize Kafka producer
            if self.output_topics:
                producer_config = {
                    **self.kafka_config.producer_config,
                    'transactional.id': f"{self.processor_name}-producer"
                }
                self.producer = Producer(producer_config)
                
                if self.enable_exactly_once:
                    self.producer.init_transactions()
            
            self.state = ProcessingState.RUNNING
            self.logger.info(f"Stream processor {self.processor_name} started successfully")
            
            # Start processing loop
            await self._processing_loop()
            
        except Exception as e:
            self.logger.error(f"Failed to start processor {self.processor_name}: {e}")
            self.state = ProcessingState.ERROR
            raise
    
    async def stop(self):
        """Stop the stream processor"""
        self.logger.info(f"Stopping stream processor: {self.processor_name}")
        self.state = ProcessingState.STOPPED
        
        # Flush any remaining events
        if self.event_buffer:
            await self._flush_buffer()
        
        # Close Kafka components
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.flush()
            self.producer = None
    
    async def pause(self):
        """Pause the stream processor"""
        self.state = ProcessingState.PAUSED
        self.logger.info(f"Stream processor {self.processor_name} paused")
    
    async def resume(self):
        """Resume the stream processor"""
        self.state = ProcessingState.RUNNING
        self.logger.info(f"Stream processor {self.processor_name} resumed")
    
    async def _processing_loop(self):
        """Main processing loop"""
        while self.state in [ProcessingState.RUNNING, ProcessingState.PAUSED]:
            try:
                if self.state == ProcessingState.PAUSED:
                    await asyncio.sleep(1)
                    continue
                
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    # Check if we should flush buffered events
                    if self._should_flush_buffer():
                        await self._flush_buffer()
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        continue
                    else:
                        self.logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                # Process message
                await self._process_message(msg)
                
                # Update metrics
                self.metrics.backlog_size = len(self.event_buffer)
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.state = ProcessingState.ERROR
                break
    
    async def _process_message(self, msg):
        """Process a single Kafka message"""
        start_time = time.time()
        
        try:
            # Parse message
            event = self._parse_message(msg)
            if not event:
                return
            
            # Add to buffer
            self.event_buffer.append(event)
            
            # Process if buffer is full or timeout reached
            if len(self.event_buffer) >= self.batch_size or self._should_flush_buffer():
                await self._flush_buffer()
            
            # Commit offset
            self.consumer.commit(message=msg, asynchronous=False)
            
        except Exception as e:
            self.logger.error(f"Failed to process message: {e}")
            await self._handle_processing_error(msg, e)
        finally:
            processing_time = (time.time() - start_time) * 1000
            self.metrics.update(processing_time, success=True)
    
    def _parse_message(self, msg) -> Optional[StreamEvent]:
        """Parse Kafka message into StreamEvent"""
        try:
            # Parse headers
            headers = {}
            if msg.headers():
                headers = {k: v.decode('utf-8') if isinstance(v, bytes) else v 
                          for k, v in msg.headers()}
            
            # Parse message data
            message_data = json.loads(msg.value().decode('utf-8'))
            
            # Create StreamEvent
            event = StreamEvent(
                event_id=headers.get('message_id', str(time.time())),
                event_type=self._determine_event_type(msg.topic(), message_data),
                timestamp=float(headers.get('timestamp', time.time())),
                source_topic=msg.topic(),
                data=message_data,
                metadata={
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                    'headers': headers
                }
            )
            
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to parse message: {e}")
            return None
    
    def _determine_event_type(self, topic: str, data: Dict[str, Any]) -> EventType:
        """Determine event type from topic and data"""
        if topic == TopicType.FLIGHT_EVENTS:
            return EventType.FLIGHT_UPDATE
        elif topic == TopicType.EXTERNAL_DATA and data.get('data_source') == 'WEATHER_API':
            return EventType.WEATHER_UPDATE
        elif topic == TopicType.DISRUPTION_EVENTS:
            return EventType.DISRUPTION_DETECTED
        elif topic == TopicType.PASSENGER_EVENTS:
            return EventType.PASSENGER_IMPACT
        elif topic == TopicType.ML_FEATURES:
            return EventType.ML_PREDICTION
        else:
            return EventType.SYSTEM_ALERT
    
    async def _flush_buffer(self):
        """Flush event buffer and process events"""
        if not self.event_buffer:
            return
        
        events_to_process = list(self.event_buffer)
        self.event_buffer.clear()
        self.last_buffer_flush = time.time()
        
        try:
            # Begin transaction if exactly-once processing is enabled
            if self.producer and self.enable_exactly_once:
                self.producer.begin_transaction()
            
            # Process events
            output_events = await self.process_events(events_to_process)
            
            # Send output events
            if output_events and self.producer:
                for output_event in output_events:
                    await self._send_output_event(output_event)
            
            # Commit transaction
            if self.producer and self.enable_exactly_once:
                self.producer.commit_transaction()
            
        except Exception as e:
            self.logger.error(f"Failed to flush buffer: {e}")
            if self.producer and self.enable_exactly_once:
                self.producer.abort_transaction()
            raise
    
    def _should_flush_buffer(self) -> bool:
        """Check if buffer should be flushed"""
        return (
            len(self.event_buffer) >= self.batch_size or
            (self.event_buffer and 
             time.time() - self.last_buffer_flush >= self.buffer_timeout_seconds)
        )
    
    async def _send_output_event(self, event: StreamEvent):
        """Send processed event to output topic"""
        if not self.producer:
            return
        
        # Determine output topic
        output_topic = self._determine_output_topic(event)
        if not output_topic:
            return
        
        # Serialize event
        message_data = json.dumps(event.data)
        headers = {
            'message_id': event.event_id,
            'event_type': event.event_type.value,
            'timestamp': str(event.timestamp),
            'processor': self.processor_name
        }
        
        # Send message
        self.producer.produce(
            topic=output_topic,
            key=event.event_id,
            value=message_data.encode('utf-8'),
            headers=headers
        )
        
        self.producer.poll(0)  # Trigger delivery reports
    
    def _determine_output_topic(self, event: StreamEvent) -> Optional[str]:
        """Determine output topic for event"""
        if not self.output_topics:
            return None
        
        # Default to first output topic
        return self.output_topics[0]
    
    async def _handle_processing_error(self, msg, error: Exception):
        """Handle processing errors"""
        self.logger.error(f"Processing error: {error}")
        
        # Send to dead letter queue
        if self.producer:
            error_data = {
                'original_topic': msg.topic(),
                'original_partition': msg.partition(),
                'original_offset': msg.offset(),
                'error_message': str(error),
                'error_timestamp': time.time(),
                'processor': self.processor_name
            }
            
            self.producer.produce(
                topic=self.dead_letter_topic,
                key=f"error_{msg.topic()}_{msg.offset()}",
                value=json.dumps(error_data).encode('utf-8')
            )
    
    @abstractmethod
    async def process_events(self, events: List[StreamEvent]) -> List[StreamEvent]:
        """Process a batch of events - to be implemented by subclasses"""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics"""
        return {
            'processor_name': self.processor_name,
            'state': self.state.value,
            'metrics': asdict(self.metrics),
            'input_topics': self.input_topics,
            'output_topics': self.output_topics,
            'buffer_size': len(self.event_buffer)
        }


class FlightDataProcessor(BaseStreamProcessor):
    """Processor for flight data events"""
    
    def __init__(self, kafka_config: KafkaConfig):
        super().__init__(
            processor_name="flight-data-processor",
            kafka_config=kafka_config,
            input_topics=[TopicType.FLIGHT_EVENTS],
            output_topics=[TopicType.ML_FEATURES, TopicType.SYSTEM_METRICS]
        )
        
        # Flight state tracking
        self.flight_states: Dict[str, Dict[str, Any]] = {}
        self.delay_patterns: Dict[str, List[float]] = defaultdict(list)
    
    async def process_events(self, events: List[StreamEvent]) -> List[StreamEvent]:
        """Process flight events"""
        output_events = []
        
        for event in events:
            try:
                if event.event_type == EventType.FLIGHT_UPDATE:
                    processed_events = await self._process_flight_update(event)
                    output_events.extend(processed_events)
                    
            except Exception as e:
                self.logger.error(f"Failed to process flight event {event.event_id}: {e}")
        
        return output_events
    
    async def _process_flight_update(self, event: StreamEvent) -> List[StreamEvent]:
        """Process single flight update"""
        output_events = []
        flight_data = event.data
        flight_id = flight_data.get('flight_id')
        
        if not flight_id:
            return output_events
        
        # Track flight state changes
        previous_state = self.flight_states.get(flight_id, {})
        self.flight_states[flight_id] = flight_data
        
        # Detect significant changes
        if self._is_significant_delay(flight_data, previous_state):
            output_events.append(await self._create_delay_alert(event, flight_data, previous_state))
        
        if self._is_cancellation(flight_data, previous_state):
            output_events.append(await self._create_cancellation_alert(event, flight_data))
        
        # Generate ML features
        ml_features = await self._extract_ml_features(flight_data, previous_state)
        if ml_features:
            output_events.append(ml_features)
        
        return output_events
    
    def _is_significant_delay(self, current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
        """Check if delay is significant"""
        current_delay = current.get('delay_minutes', 0)
        previous_delay = previous.get('delay_minutes', 0)
        
        return current_delay > previous_delay + 15  # 15+ minute increase
    
    def _is_cancellation(self, current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
        """Check if flight was cancelled"""
        return (
            current.get('event_type') == 'CANCELLED' and
            previous.get('event_type') != 'CANCELLED'
        )
    
    async def _create_delay_alert(
        self,
        original_event: StreamEvent,
        flight_data: Dict[str, Any],
        previous_state: Dict[str, Any]
    ) -> StreamEvent:
        """Create delay alert event"""
        alert_data = {
            'alert_type': 'significant_delay',
            'flight_id': flight_data.get('flight_id'),
            'flight_number': flight_data.get('flight_number'),
            'previous_delay_minutes': previous_state.get('delay_minutes', 0),
            'current_delay_minutes': flight_data.get('delay_minutes', 0),
            'delay_increase': flight_data.get('delay_minutes', 0) - previous_state.get('delay_minutes', 0),
            'departure_airport': flight_data.get('departure_airport'),
            'arrival_airport': flight_data.get('arrival_airport'),
            'scheduled_departure': flight_data.get('scheduled_departure'),
            'affected_passengers_estimate': flight_data.get('seats_sold', 0)
        }
        
        return StreamEvent(
            event_id=f"delay_alert_{flight_data.get('flight_id')}_{int(time.time())}",
            event_type=EventType.SYSTEM_ALERT,
            timestamp=time.time(),
            source_topic=self.output_topics[1],
            data=alert_data,
            metadata={
                'original_event_id': original_event.event_id,
                'processor': self.processor_name,
                'alert_severity': 'high' if alert_data['delay_increase'] > 60 else 'medium'
            }
        )
    
    async def _create_cancellation_alert(
        self,
        original_event: StreamEvent,
        flight_data: Dict[str, Any]
    ) -> StreamEvent:
        """Create cancellation alert event"""
        alert_data = {
            'alert_type': 'flight_cancellation',
            'flight_id': flight_data.get('flight_id'),
            'flight_number': flight_data.get('flight_number'),
            'cancellation_reason': flight_data.get('metadata', {}).get('cancellation_reason'),
            'departure_airport': flight_data.get('departure_airport'),
            'arrival_airport': flight_data.get('arrival_airport'),
            'scheduled_departure': flight_data.get('scheduled_departure'),
            'affected_passengers_estimate': flight_data.get('seats_sold', 0),
            'advance_notice_hours': self._calculate_advance_notice(flight_data)
        }
        
        return StreamEvent(
            event_id=f"cancel_alert_{flight_data.get('flight_id')}_{int(time.time())}",
            event_type=EventType.SYSTEM_ALERT,
            timestamp=time.time(),
            source_topic=self.output_topics[1],
            data=alert_data,
            metadata={
                'original_event_id': original_event.event_id,
                'processor': self.processor_name,
                'alert_severity': 'critical'
            }
        )
    
    def _calculate_advance_notice(self, flight_data: Dict[str, Any]) -> float:
        """Calculate advance notice for cancellation"""
        scheduled_departure = flight_data.get('scheduled_departure')
        if not scheduled_departure:
            return 0.0
        
        try:
            departure_time = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
            advance_notice = departure_time - datetime.now()
            return advance_notice.total_seconds() / 3600  # Convert to hours
        except:
            return 0.0
    
    async def _extract_ml_features(
        self,
        flight_data: Dict[str, Any],
        previous_state: Dict[str, Any]
    ) -> Optional[StreamEvent]:
        """Extract ML features from flight data"""
        try:
            features = {
                'flight_id': flight_data.get('flight_id'),
                'airline_code': flight_data.get('airline_code'),
                'departure_airport': flight_data.get('departure_airport'),
                'arrival_airport': flight_data.get('arrival_airport'),
                'scheduled_hour': self._extract_hour_from_datetime(flight_data.get('scheduled_departure')),
                'day_of_week': self._extract_day_of_week(flight_data.get('scheduled_departure')),
                'delay_minutes': flight_data.get('delay_minutes', 0),
                'is_international': self._is_international_flight(flight_data),
                'aircraft_type_category': self._categorize_aircraft(flight_data.get('aircraft_type')),
                'load_factor': flight_data.get('load_factor', 0.0),
                'previous_delay_minutes': previous_state.get('delay_minutes', 0),
                'delay_trend': flight_data.get('delay_minutes', 0) - previous_state.get('delay_minutes', 0),
            }
            
            feature_vector = [
                features['scheduled_hour'],
                features['day_of_week'],
                features['delay_minutes'],
                1.0 if features['is_international'] else 0.0,
                features['aircraft_type_category'],
                features['load_factor'],
                features['previous_delay_minutes'],
                features['delay_trend']
            ]
            
            ml_data = {
                'entity_id': flight_data.get('flight_id'),
                'entity_type': 'FLIGHT',
                'feature_vector': feature_vector,
                'feature_names': list(features.keys()),
                'model_version': '1.0',
                'prediction_timestamp': int(time.time() * 1000),
                'metadata': features
            }
            
            return StreamEvent(
                event_id=f"ml_features_{flight_data.get('flight_id')}_{int(time.time())}",
                event_type=EventType.ML_PREDICTION,
                timestamp=time.time(),
                source_topic=self.output_topics[0],
                data=ml_data,
                metadata={
                    'processor': self.processor_name,
                    'feature_extraction_time': time.time()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract ML features: {e}")
            return None
    
    def _extract_hour_from_datetime(self, datetime_str: Optional[str]) -> int:
        """Extract hour from datetime string"""
        if not datetime_str:
            return 12  # Default noon
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.hour
        except:
            return 12
    
    def _extract_day_of_week(self, datetime_str: Optional[str]) -> int:
        """Extract day of week from datetime string"""
        if not datetime_str:
            return 1  # Default Monday
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.weekday()  # 0=Monday, 6=Sunday
        except:
            return 1
    
    def _is_international_flight(self, flight_data: Dict[str, Any]) -> bool:
        """Check if flight is international"""
        dep_airport = flight_data.get('departure_airport', '')
        arr_airport = flight_data.get('arrival_airport', '')
        
        # Simple heuristic: different country codes (first letter of IATA codes)
        if len(dep_airport) >= 1 and len(arr_airport) >= 1:
            return dep_airport[0] != arr_airport[0]
        return False
    
    def _categorize_aircraft(self, aircraft_type: Optional[str]) -> float:
        """Categorize aircraft type into numeric category"""
        if not aircraft_type:
            return 2.0  # Default medium
        
        aircraft_type = aircraft_type.upper()
        
        # Large aircraft
        if any(large in aircraft_type for large in ['747', '777', '787', '380', '350']):
            return 3.0
        # Small aircraft
        elif any(small in aircraft_type for small in ['737', '320', '319', '321', 'E190', 'CRJ']):
            return 1.0
        # Medium aircraft
        else:
            return 2.0


class WeatherCorrelationProcessor(BaseStreamProcessor):
    """Processor for correlating weather data with flight impacts"""
    
    def __init__(self, kafka_config: KafkaConfig):
        super().__init__(
            processor_name="weather-correlation-processor",
            kafka_config=kafka_config,
            input_topics=[TopicType.EXTERNAL_DATA, TopicType.FLIGHT_EVENTS],
            output_topics=[TopicType.DISRUPTION_EVENTS, TopicType.ML_FEATURES]
        )
        
        # Weather and flight data correlation
        self.weather_data: Dict[str, Dict[str, Any]] = {}  # location -> weather data
        self.flight_impacts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # airport -> impacts
        self.correlation_window_hours = 2
    
    async def process_events(self, events: List[StreamEvent]) -> List[StreamEvent]:
        """Process weather and flight correlation events"""
        output_events = []
        
        # Separate weather and flight events
        weather_events = [e for e in events if e.event_type == EventType.WEATHER_UPDATE]
        flight_events = [e for e in events if e.event_type == EventType.FLIGHT_UPDATE]
        
        # Process weather updates
        for weather_event in weather_events:
            await self._process_weather_update(weather_event)
        
        # Process flight events and check for weather correlation
        for flight_event in flight_events:
            correlation_events = await self._check_weather_correlation(flight_event)
            output_events.extend(correlation_events)
        
        # Check for weather-based disruption patterns
        disruption_events = await self._detect_weather_disruptions()
        output_events.extend(disruption_events)
        
        return output_events
    
    async def _process_weather_update(self, event: StreamEvent):
        """Process weather update event"""
        weather_data = event.data
        location = weather_data.get('location')
        
        if location:
            self.weather_data[location] = {
                'data': weather_data,
                'timestamp': event.timestamp,
                'impact_score': weather_data.get('flight_impact_score', 0.0)
            }
            
            # Clean old weather data
            self._cleanup_old_weather_data()
    
    async def _check_weather_correlation(self, flight_event: StreamEvent) -> List[StreamEvent]:
        """Check if flight event correlates with weather"""
        output_events = []
        flight_data = flight_event.data
        
        # Get airports for this flight
        airports = []
        if flight_data.get('departure_airport'):
            airports.append(flight_data['departure_airport'])
        if flight_data.get('arrival_airport'):
            airports.append(flight_data['arrival_airport'])
        
        # Check weather impact for each airport
        for airport in airports:
            weather_info = self.weather_data.get(airport)
            if weather_info and self._is_weather_related_impact(flight_data, weather_info):
                correlation_event = await self._create_weather_correlation_event(
                    flight_event, weather_info, airport
                )
                if correlation_event:
                    output_events.append(correlation_event)
        
        return output_events
    
    def _is_weather_related_impact(
        self,
        flight_data: Dict[str, Any],
        weather_info: Dict[str, Any]
    ) -> bool:
        """Check if flight impact is weather-related"""
        # Check if flight has delay/cancellation
        has_impact = (
            flight_data.get('delay_minutes', 0) > 15 or
            flight_data.get('event_type') == 'CANCELLED' or
            flight_data.get('status') == 'delayed'
        )
        
        # Check if weather has significant impact score
        weather_impact = weather_info.get('impact_score', 0.0) > 0.3
        
        # Check temporal correlation (within correlation window)
        time_diff = abs(flight_data.get('timestamp', 0) - weather_info.get('timestamp', 0))
        within_time_window = time_diff < (self.correlation_window_hours * 3600)
        
        return has_impact and weather_impact and within_time_window
    
    async def _create_weather_correlation_event(
        self,
        flight_event: StreamEvent,
        weather_info: Dict[str, Any],
        airport: str
    ) -> Optional[StreamEvent]:
        """Create weather correlation event"""
        try:
            correlation_data = {
                'correlation_type': 'weather_flight_impact',
                'flight_id': flight_event.data.get('flight_id'),
                'flight_number': flight_event.data.get('flight_number'),
                'airport': airport,
                'weather_conditions': {
                    'condition': weather_info['data'].get('condition'),
                    'severity': weather_info['data'].get('severity'),
                    'impact_score': weather_info.get('impact_score'),
                    'visibility_km': weather_info['data'].get('visibility_km'),
                    'wind_speed_kmh': weather_info['data'].get('wind_speed_kmh'),
                    'precipitation_mm': weather_info['data'].get('precipitation_mm')
                },
                'flight_impact': {
                    'delay_minutes': flight_event.data.get('delay_minutes', 0),
                    'status': flight_event.data.get('status'),
                    'event_type': flight_event.data.get('event_type')
                },
                'correlation_confidence': self._calculate_correlation_confidence(
                    flight_event.data, weather_info
                ),
                'correlation_timestamp': time.time()
            }
            
            return StreamEvent(
                event_id=f"weather_corr_{flight_event.data.get('flight_id')}_{int(time.time())}",
                event_type=EventType.SYSTEM_ALERT,
                timestamp=time.time(),
                source_topic=self.output_topics[0],
                data=correlation_data,
                metadata={
                    'processor': self.processor_name,
                    'original_flight_event_id': flight_event.event_id,
                    'correlation_type': 'weather_impact'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create weather correlation event: {e}")
            return None
    
    def _calculate_correlation_confidence(
        self,
        flight_data: Dict[str, Any],
        weather_info: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for weather-flight correlation"""
        confidence = 0.0
        
        # Base confidence from weather impact score
        confidence += weather_info.get('impact_score', 0.0) * 0.4
        
        # Confidence from flight delay severity
        delay_minutes = flight_data.get('delay_minutes', 0)
        if delay_minutes > 60:
            confidence += 0.3
        elif delay_minutes > 30:
            confidence += 0.2
        elif delay_minutes > 15:
            confidence += 0.1
        
        # Confidence from cancellation
        if flight_data.get('event_type') == 'CANCELLED':
            confidence += 0.3
        
        return min(1.0, confidence)
    
    async def _detect_weather_disruptions(self) -> List[StreamEvent]:
        """Detect airport-wide weather disruptions"""
        output_events = []
        
        for airport, weather_info in self.weather_data.items():
            if self._is_significant_weather_disruption(weather_info):
                disruption_event = await self._create_weather_disruption_event(airport, weather_info)
                if disruption_event:
                    output_events.append(disruption_event)
        
        return output_events
    
    def _is_significant_weather_disruption(self, weather_info: Dict[str, Any]) -> bool:
        """Check if weather constitutes a significant disruption"""
        impact_score = weather_info.get('impact_score', 0.0)
        weather_data = weather_info.get('data', {})
        
        return (
            impact_score > 0.6 or
            weather_data.get('severity') in ['severe', 'extreme'] or
            weather_data.get('visibility_km', 10) < 1 or
            weather_data.get('wind_speed_kmh', 0) > 50
        )
    
    async def _create_weather_disruption_event(
        self,
        airport: str,
        weather_info: Dict[str, Any]
    ) -> Optional[StreamEvent]:
        """Create weather disruption event"""
        try:
            weather_data = weather_info['data']
            
            disruption_data = {
                'disruption_id': f"weather_disruption_{airport}_{int(time.time())}",
                'disruption_type': 'WEATHER',
                'severity': self._map_weather_to_disruption_severity(weather_data),
                'cause': weather_data.get('condition', 'unknown'),
                'affected_airports': [airport],
                'affected_flights': [],  # Will be populated by downstream processors
                'start_time': int(weather_info.get('timestamp', time.time()) * 1000),
                'estimated_end_time': None,  # Will be estimated by forecasting
                'description': f"Weather disruption at {airport}: {weather_data.get('condition')}",
                'impact_radius_km': self._estimate_impact_radius(weather_data),
                'metadata': {
                    'weather_conditions': weather_data,
                    'impact_score': weather_info.get('impact_score'),
                    'auto_detected': True
                },
                'timestamp': int(time.time() * 1000),
                'source': 'weather-correlation-processor'
            }
            
            return StreamEvent(
                event_id=disruption_data['disruption_id'],
                event_type=EventType.DISRUPTION_DETECTED,
                timestamp=time.time(),
                source_topic=self.output_topics[0],
                data=disruption_data,
                metadata={
                    'processor': self.processor_name,
                    'disruption_category': 'weather',
                    'auto_generated': True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create weather disruption event: {e}")
            return None
    
    def _map_weather_to_disruption_severity(self, weather_data: Dict[str, Any]) -> str:
        """Map weather severity to disruption severity"""
        weather_severity = weather_data.get('severity', 'light').upper()
        
        mapping = {
            'LIGHT': 'LOW',
            'MODERATE': 'MEDIUM',
            'HEAVY': 'HIGH',
            'SEVERE': 'HIGH',
            'EXTREME': 'CRITICAL'
        }
        
        return mapping.get(weather_severity, 'MEDIUM')
    
    def _estimate_impact_radius(self, weather_data: Dict[str, Any]) -> float:
        """Estimate impact radius of weather event"""
        condition = weather_data.get('condition', '')
        severity = weather_data.get('severity', 'light')
        
        base_radius = 25.0  # km
        
        if 'thunderstorm' in condition or 'hurricane' in condition:
            base_radius = 100.0
        elif 'tornado' in condition:
            base_radius = 50.0
        elif 'fog' in condition:
            base_radius = 15.0
        
        # Scale by severity
        severity_multipliers = {
            'light': 0.5,
            'moderate': 1.0,
            'heavy': 1.5,
            'severe': 2.0,
            'extreme': 3.0
        }
        
        multiplier = severity_multipliers.get(severity.lower(), 1.0)
        return base_radius * multiplier
    
    def _cleanup_old_weather_data(self):
        """Clean up old weather data"""
        cutoff_time = time.time() - (self.correlation_window_hours * 3600)
        
        airports_to_remove = []
        for airport, weather_info in self.weather_data.items():
            if weather_info.get('timestamp', 0) < cutoff_time:
                airports_to_remove.append(airport)
        
        for airport in airports_to_remove:
            del self.weather_data[airport]


class StreamProcessorManager:
    """Manager for multiple stream processors"""
    
    def __init__(self, kafka_config: KafkaConfig):
        self.kafka_config = kafka_config
        self.processors: Dict[str, BaseStreamProcessor] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_processor(self, processor: BaseStreamProcessor):
        """Register a stream processor"""
        self.processors[processor.processor_name] = processor
        self.logger.info(f"Registered processor: {processor.processor_name}")
    
    async def start_all(self):
        """Start all registered processors"""
        self.logger.info("Starting all stream processors")
        
        tasks = []
        for processor in self.processors.values():
            task = asyncio.create_task(processor.start())
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error starting processors: {e}")
            await self.stop_all()
            raise
    
    async def stop_all(self):
        """Stop all processors"""
        self.logger.info("Stopping all stream processors")
        
        tasks = []
        for processor in self.processors.values():
            task = asyncio.create_task(processor.stop())
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all processors"""
        return {
            name: processor.get_metrics()
            for name, processor in self.processors.items()
        }
    
    def get_processor(self, name: str) -> Optional[BaseStreamProcessor]:
        """Get processor by name"""
        return self.processors.get(name)


async def create_default_stream_processors(kafka_config: KafkaConfig) -> StreamProcessorManager:
    """Create default set of stream processors"""
    manager = StreamProcessorManager(kafka_config)
    
    # Register default processors
    manager.register_processor(FlightDataProcessor(kafka_config))
    manager.register_processor(WeatherCorrelationProcessor(kafka_config))
    
    return manager