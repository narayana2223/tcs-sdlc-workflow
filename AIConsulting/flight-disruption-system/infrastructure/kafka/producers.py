"""
Kafka Producers for Flight Disruption Management System
High-performance, reliable message producers with schema validation
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from confluent_kafka import Producer, KafkaException
from confluent_kafka.schema_registry.avro import AvroSerializer
import avro.io
import avro.schema

from .kafka_config import KafkaConfig, TopicType, MessagePriority, SchemaManager


@dataclass
class MessageMetadata:
    """Metadata for Kafka messages"""
    message_id: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    timestamp: float = None
    priority: MessagePriority = MessagePriority.NORMAL
    source: str = "flight-disruption-system"
    version: str = "1.0"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class DeliveryReport:
    """Callback handler for message delivery reports"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, err, msg):
        """Handle delivery report"""
        if err is not None:
            self.logger.error(f'Message delivery failed: {err}')
            if self.callback:
                self.callback(err, msg, success=False)
        else:
            self.logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')
            if self.callback:
                self.callback(err, msg, success=True)


class BaseKafkaProducer(ABC):
    """Base class for all Kafka producers"""
    
    def __init__(self, kafka_config: KafkaConfig, schema_manager: Optional[SchemaManager] = None):
        self.kafka_config = kafka_config
        self.schema_manager = schema_manager
        self.producer = Producer(kafka_config.producer_config)
        self.logger = logging.getLogger(__name__)
        
        # Message tracking
        self.message_count = 0
        self.error_count = 0
        self.last_error_time = None
        
        # Delivery report handler
        self.delivery_report = DeliveryReport(self._on_delivery)
    
    def _on_delivery(self, err, msg, success: bool):
        """Handle message delivery result"""
        if success:
            self.message_count += 1
        else:
            self.error_count += 1
            self.last_error_time = time.time()
    
    @abstractmethod
    def _serialize_message(self, message: Dict[str, Any], topic: str) -> bytes:
        """Serialize message for the specific topic"""
        pass
    
    def _create_headers(self, metadata: MessageMetadata) -> Dict[str, bytes]:
        """Create message headers"""
        return {
            'message_id': metadata.message_id.encode('utf-8'),
            'correlation_id': (metadata.correlation_id or '').encode('utf-8'),
            'causation_id': (metadata.causation_id or '').encode('utf-8'),
            'timestamp': str(metadata.timestamp).encode('utf-8'),
            'priority': metadata.priority.value.encode('utf-8'),
            'source': metadata.source.encode('utf-8'),
            'version': metadata.version.encode('utf-8')
        }
    
    def send_message(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None,
        metadata: Optional[MessageMetadata] = None,
        callback: Optional[Callable] = None
    ) -> bool:
        """Send a message to Kafka"""
        try:
            # Create metadata if not provided
            if metadata is None:
                metadata = MessageMetadata(message_id=str(uuid.uuid4()))
            
            # Serialize message
            serialized_message = self._serialize_message(message, topic)
            
            # Create headers
            headers = self._create_headers(metadata)
            
            # Send message
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=serialized_message,
                partition=partition,
                headers=headers,
                callback=self.delivery_report if callback is None else callback
            )
            
            # Trigger delivery reports
            self.producer.poll(0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {topic}: {e}")
            return False
    
    def send_batch(
        self,
        messages: List[Dict[str, Any]],
        topic: str,
        key_extractor: Optional[Callable[[Dict[str, Any]], str]] = None
    ) -> Dict[str, int]:
        """Send a batch of messages"""
        results = {'success': 0, 'failed': 0}
        
        for message in messages:
            key = key_extractor(message) if key_extractor else None
            metadata = MessageMetadata(message_id=str(uuid.uuid4()))
            
            if self.send_message(topic, message, key=key, metadata=metadata):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush(30)  # 30 second timeout
        
        return results
    
    def flush(self, timeout: float = 10.0):
        """Flush all pending messages"""
        self.producer.flush(timeout)
    
    def close(self):
        """Close the producer"""
        self.producer.flush()
        self.producer = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics"""
        return {
            'messages_sent': self.message_count,
            'errors': self.error_count,
            'last_error_time': self.last_error_time,
            'producer_stats': json.loads(self.producer.stats()) if self.producer else {}
        }


class AvroKafkaProducer(BaseKafkaProducer):
    """Kafka producer with Avro serialization"""
    
    def __init__(self, kafka_config: KafkaConfig, schema_manager: SchemaManager):
        super().__init__(kafka_config, schema_manager)
        self.serializers = {}
        
        # Create serializers for each schema
        if schema_manager:
            self.serializers = {
                'flight_event': schema_manager.get_serializer('flight_event'),
                'disruption_event': schema_manager.get_serializer('disruption_event'),
                'passenger_event': schema_manager.get_serializer('passenger_event'),
                'external_data': schema_manager.get_serializer('external_data'),
                'ml_features': schema_manager.get_serializer('ml_features')
            }
    
    def _serialize_message(self, message: Dict[str, Any], topic: str) -> bytes:
        """Serialize message using Avro"""
        # Map topic to schema
        schema_mapping = {
            TopicType.FLIGHT_EVENTS: 'flight_event',
            TopicType.DISRUPTION_EVENTS: 'disruption_event',
            TopicType.PASSENGER_EVENTS: 'passenger_event',
            TopicType.EXTERNAL_DATA: 'external_data',
            TopicType.ML_FEATURES: 'ml_features'
        }
        
        schema_name = schema_mapping.get(topic)
        if schema_name and schema_name in self.serializers:
            serializer = self.serializers[schema_name]
            if serializer:
                return serializer(message, None)  # SerializationContext not needed here
        
        # Fallback to JSON serialization
        return json.dumps(message).encode('utf-8')


class JSONKafkaProducer(BaseKafkaProducer):
    """Kafka producer with JSON serialization"""
    
    def _serialize_message(self, message: Dict[str, Any], topic: str) -> bytes:
        """Serialize message using JSON"""
        return json.dumps(message, default=self._json_serializer).encode('utf-8')
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class FlightEventProducer:
    """Specialized producer for flight events"""
    
    def __init__(self, producer: BaseKafkaProducer):
        self.producer = producer
        self.topic = TopicType.FLIGHT_EVENTS
        self.logger = logging.getLogger(__name__)
    
    def send_flight_scheduled(
        self,
        flight_id: str,
        flight_number: str,
        airline_code: str,
        departure_airport: str,
        arrival_airport: str,
        scheduled_departure: datetime,
        scheduled_arrival: datetime,
        **kwargs
    ) -> bool:
        """Send flight scheduled event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'flight_id': flight_id,
            'flight_number': flight_number,
            'airline_code': airline_code,
            'departure_airport': departure_airport,
            'arrival_airport': arrival_airport,
            'event_type': 'SCHEDULED',
            'scheduled_departure': int(scheduled_departure.timestamp() * 1000),
            'scheduled_arrival': int(scheduled_arrival.timestamp() * 1000),
            'actual_departure': None,
            'actual_arrival': None,
            'delay_minutes': None,
            'gate': kwargs.get('gate'),
            'status': 'scheduled',
            'metadata': kwargs.get('metadata', {}),
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'flight-ops')
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=flight_id,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=MessagePriority.NORMAL
            )
        )
    
    def send_flight_delayed(
        self,
        flight_id: str,
        delay_minutes: int,
        reason: str,
        new_departure_time: datetime,
        new_arrival_time: datetime,
        **kwargs
    ) -> bool:
        """Send flight delayed event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'flight_id': flight_id,
            'flight_number': kwargs.get('flight_number', ''),
            'airline_code': kwargs.get('airline_code', ''),
            'departure_airport': kwargs.get('departure_airport', ''),
            'arrival_airport': kwargs.get('arrival_airport', ''),
            'event_type': 'DELAYED',
            'scheduled_departure': kwargs.get('scheduled_departure'),
            'scheduled_arrival': kwargs.get('scheduled_arrival'),
            'actual_departure': int(new_departure_time.timestamp() * 1000),
            'actual_arrival': int(new_arrival_time.timestamp() * 1000),
            'delay_minutes': delay_minutes,
            'gate': kwargs.get('gate'),
            'status': 'delayed',
            'metadata': {
                'delay_reason': reason,
                **kwargs.get('metadata', {})
            },
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'flight-ops')
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=flight_id,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=MessagePriority.HIGH
            )
        )
    
    def send_flight_cancelled(
        self,
        flight_id: str,
        reason: str,
        **kwargs
    ) -> bool:
        """Send flight cancelled event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'flight_id': flight_id,
            'flight_number': kwargs.get('flight_number', ''),
            'airline_code': kwargs.get('airline_code', ''),
            'departure_airport': kwargs.get('departure_airport', ''),
            'arrival_airport': kwargs.get('arrival_airport', ''),
            'event_type': 'CANCELLED',
            'scheduled_departure': kwargs.get('scheduled_departure'),
            'scheduled_arrival': kwargs.get('scheduled_arrival'),
            'actual_departure': None,
            'actual_arrival': None,
            'delay_minutes': None,
            'gate': kwargs.get('gate'),
            'status': 'cancelled',
            'metadata': {
                'cancellation_reason': reason,
                **kwargs.get('metadata', {})
            },
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'flight-ops')
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=flight_id,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=MessagePriority.CRITICAL
            )
        )


class DisruptionEventProducer:
    """Specialized producer for disruption events"""
    
    def __init__(self, producer: BaseKafkaProducer):
        self.producer = producer
        self.topic = TopicType.DISRUPTION_EVENTS
        self.logger = logging.getLogger(__name__)
    
    def send_disruption_started(
        self,
        disruption_id: str,
        disruption_type: str,
        severity: str,
        cause: str,
        affected_airports: List[str],
        affected_flights: List[str],
        start_time: datetime,
        description: str,
        **kwargs
    ) -> bool:
        """Send disruption started event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'disruption_id': disruption_id,
            'disruption_type': disruption_type.upper(),
            'severity': severity.upper(),
            'cause': cause,
            'affected_airports': affected_airports,
            'affected_flights': affected_flights,
            'start_time': int(start_time.timestamp() * 1000),
            'estimated_end_time': kwargs.get('estimated_end_time'),
            'description': description,
            'impact_radius_km': kwargs.get('impact_radius_km'),
            'metadata': kwargs.get('metadata', {}),
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'disruption-monitor')
        }
        
        priority = MessagePriority.CRITICAL if severity.upper() == 'CRITICAL' else MessagePriority.HIGH
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=disruption_id,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=priority
            )
        )


class PassengerEventProducer:
    """Specialized producer for passenger events"""
    
    def __init__(self, producer: BaseKafkaProducer):
        self.producer = producer
        self.topic = TopicType.PASSENGER_EVENTS
        self.logger = logging.getLogger(__name__)
    
    def send_passenger_rebooked(
        self,
        passenger_id: str,
        booking_id: str,
        old_flight_id: str,
        new_flight_id: str,
        **kwargs
    ) -> bool:
        """Send passenger rebooked event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'passenger_id': passenger_id,
            'booking_id': booking_id,
            'flight_id': new_flight_id,
            'event_type': 'REBOOKED',
            'loyalty_tier': kwargs.get('loyalty_tier'),
            'special_needs': kwargs.get('special_needs', []),
            'contact_preferences': kwargs.get('contact_preferences', []),
            'previous_flight_id': old_flight_id,
            'compensation_amount': kwargs.get('compensation_amount'),
            'metadata': {
                'rebooking_reason': kwargs.get('reason', 'disruption'),
                **kwargs.get('metadata', {})
            },
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'rebooking-service')
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=passenger_id,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=MessagePriority.HIGH
            )
        )


class ExternalDataProducer:
    """Producer for external data integration events"""
    
    def __init__(self, producer: BaseKafkaProducer):
        self.producer = producer
        self.topic = TopicType.EXTERNAL_DATA
        self.logger = logging.getLogger(__name__)
    
    def send_weather_data(
        self,
        location: str,
        weather_data: Dict[str, Any],
        quality_score: Optional[float] = None,
        **kwargs
    ) -> bool:
        """Send weather data event"""
        message = {
            'event_id': str(uuid.uuid4()),
            'data_source': 'WEATHER_API',
            'data_type': 'weather_update',
            'location': location,
            'payload': weather_data,
            'quality_score': quality_score,
            'expiry_time': kwargs.get('expiry_time'),
            'metadata': kwargs.get('metadata', {}),
            'timestamp': int(time.time() * 1000),
            'source': kwargs.get('source', 'weather-service')
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=location,
            metadata=MessageMetadata(
                message_id=message['event_id'],
                priority=MessagePriority.NORMAL
            )
        )


class MLFeaturesProducer:
    """Producer for ML feature events"""
    
    def __init__(self, producer: BaseKafkaProducer):
        self.producer = producer
        self.topic = TopicType.ML_FEATURES
        self.logger = logging.getLogger(__name__)
    
    def send_prediction_features(
        self,
        entity_id: str,
        entity_type: str,
        feature_vector: List[float],
        feature_names: List[str],
        model_version: str,
        prediction_timestamp: datetime,
        confidence_score: Optional[float] = None,
        **kwargs
    ) -> bool:
        """Send ML prediction features"""
        message = {
            'feature_id': str(uuid.uuid4()),
            'entity_id': entity_id,
            'entity_type': entity_type.upper(),
            'feature_vector': feature_vector,
            'feature_names': feature_names,
            'model_version': model_version,
            'prediction_timestamp': int(prediction_timestamp.timestamp() * 1000),
            'confidence_score': confidence_score,
            'metadata': kwargs.get('metadata', {}),
            'timestamp': int(time.time() * 1000)
        }
        
        return self.producer.send_message(
            topic=self.topic,
            message=message,
            key=entity_id,
            metadata=MessageMetadata(
                message_id=message['feature_id'],
                priority=MessagePriority.NORMAL
            )
        )


class ProducerFactory:
    """Factory for creating specialized producers"""
    
    def __init__(self, kafka_config: KafkaConfig, schema_manager: Optional[SchemaManager] = None):
        self.kafka_config = kafka_config
        self.schema_manager = schema_manager
        
        # Create base producer
        if schema_manager:
            self.base_producer = AvroKafkaProducer(kafka_config, schema_manager)
        else:
            self.base_producer = JSONKafkaProducer(kafka_config)
    
    def create_flight_producer(self) -> FlightEventProducer:
        """Create flight event producer"""
        return FlightEventProducer(self.base_producer)
    
    def create_disruption_producer(self) -> DisruptionEventProducer:
        """Create disruption event producer"""
        return DisruptionEventProducer(self.base_producer)
    
    def create_passenger_producer(self) -> PassengerEventProducer:
        """Create passenger event producer"""
        return PassengerEventProducer(self.base_producer)
    
    def create_external_data_producer(self) -> ExternalDataProducer:
        """Create external data producer"""
        return ExternalDataProducer(self.base_producer)
    
    def create_ml_features_producer(self) -> MLFeaturesProducer:
        """Create ML features producer"""
        return MLFeaturesProducer(self.base_producer)
    
    def get_base_producer(self) -> BaseKafkaProducer:
        """Get base producer for custom usage"""
        return self.base_producer
    
    def close_all(self):
        """Close all producers"""
        self.base_producer.close()