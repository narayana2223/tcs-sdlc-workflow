"""
Kafka Configuration and Topic Management
Comprehensive Kafka setup for flight disruption management system
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType, NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError
import avro.schema
import avro.io
from confluent_kafka import Producer, Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic as ConfluentNewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer


class TopicType(str, Enum):
    """Kafka topic types for different data streams"""
    FLIGHT_EVENTS = "flight.events"
    DISRUPTION_EVENTS = "disruption.events"
    PASSENGER_EVENTS = "passenger.events"
    BOOKING_EVENTS = "booking.events"
    EXTERNAL_DATA = "external.data"
    NOTIFICATIONS = "notifications"
    ML_FEATURES = "ml.features"
    SYSTEM_METRICS = "system.metrics"
    DEAD_LETTER = "dead.letter"


class MessagePriority(str, Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class TopicConfig:
    """Configuration for Kafka topics"""
    name: str
    partitions: int
    replication_factor: int
    retention_ms: int
    cleanup_policy: str = "delete"
    compression_type: str = "lz4"
    max_message_bytes: int = 1048576  # 1MB
    segment_ms: int = 604800000  # 1 week
    min_in_sync_replicas: int = 1
    
    @property
    def config_dict(self) -> Dict[str, str]:
        """Get topic configuration as dictionary"""
        return {
            'cleanup.policy': self.cleanup_policy,
            'compression.type': self.compression_type,
            'retention.ms': str(self.retention_ms),
            'max.message.bytes': str(self.max_message_bytes),
            'segment.ms': str(self.segment_ms),
            'min.insync.replicas': str(self.min_in_sync_replicas)
        }


@dataclass
class KafkaConfig:
    """Kafka cluster configuration"""
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    schema_registry_url: Optional[str] = None
    client_id: str = "flight-disruption-system"
    
    @property
    def producer_config(self) -> Dict[str, Any]:
        """Get producer configuration"""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'security.protocol': self.security_protocol,
            'client.id': self.client_id,
            'acks': 'all',
            'retries': 3,
            'retry.backoff.ms': 1000,
            'max.in.flight.requests.per.connection': 5,
            'enable.idempotence': True,
            'compression.type': 'lz4',
            'batch.size': 16384,
            'linger.ms': 10,
            'buffer.memory': 33554432
        }
        
        if self.sasl_mechanism:
            config.update({
                'sasl.mechanism': self.sasl_mechanism,
                'sasl.username': self.sasl_username,
                'sasl.password': self.sasl_password
            })
            
        return config
    
    @property
    def consumer_config(self) -> Dict[str, Any]:
        """Get consumer configuration"""
        config = {
            'bootstrap.servers': self.bootstrap_servers,
            'security.protocol': self.security_protocol,
            'client.id': self.client_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,
            'max.poll.interval.ms': 300000,
            'session.timeout.ms': 30000,
            'heartbeat.interval.ms': 3000,
            'fetch.min.bytes': 1,
            'fetch.max.wait.ms': 500
        }
        
        if self.sasl_mechanism:
            config.update({
                'sasl.mechanism': self.sasl_mechanism,
                'sasl.username': self.sasl_username,
                'sasl.password': self.sasl_password
            })
            
        return config


class TopicManager:
    """Kafka topic management and administration"""
    
    def __init__(self, kafka_config: KafkaConfig):
        self.kafka_config = kafka_config
        self.admin_client = AdminClient({
            'bootstrap.servers': kafka_config.bootstrap_servers,
            'security.protocol': kafka_config.security_protocol
        })
        self.logger = logging.getLogger(__name__)
        
        # Define topic configurations
        self.topic_configs = self._get_default_topic_configs()
    
    def _get_default_topic_configs(self) -> Dict[str, TopicConfig]:
        """Get default topic configurations for all topics"""
        return {
            TopicType.FLIGHT_EVENTS: TopicConfig(
                name="flight.events",
                partitions=6,
                replication_factor=2,
                retention_ms=86400000 * 7,  # 7 days
                cleanup_policy="delete",
                max_message_bytes=2097152  # 2MB
            ),
            TopicType.DISRUPTION_EVENTS: TopicConfig(
                name="disruption.events",
                partitions=3,
                replication_factor=3,
                retention_ms=86400000 * 30,  # 30 days
                cleanup_policy="delete"
            ),
            TopicType.PASSENGER_EVENTS: TopicConfig(
                name="passenger.events",
                partitions=4,
                replication_factor=2,
                retention_ms=86400000 * 14,  # 14 days
                cleanup_policy="delete"
            ),
            TopicType.BOOKING_EVENTS: TopicConfig(
                name="booking.events",
                partitions=4,
                replication_factor=2,
                retention_ms=86400000 * 90,  # 90 days
                cleanup_policy="delete"
            ),
            TopicType.EXTERNAL_DATA: TopicConfig(
                name="external.data",
                partitions=8,
                replication_factor=2,
                retention_ms=86400000 * 3,  # 3 days
                cleanup_policy="delete",
                max_message_bytes=5242880  # 5MB for weather data
            ),
            TopicType.NOTIFICATIONS: TopicConfig(
                name="notifications",
                partitions=2,
                replication_factor=2,
                retention_ms=86400000 * 7,  # 7 days
                cleanup_policy="delete"
            ),
            TopicType.ML_FEATURES: TopicConfig(
                name="ml.features",
                partitions=4,
                replication_factor=2,
                retention_ms=86400000 * 7,  # 7 days
                cleanup_policy="delete",
                compression_type="gzip"  # Better compression for ML data
            ),
            TopicType.SYSTEM_METRICS: TopicConfig(
                name="system.metrics",
                partitions=2,
                replication_factor=2,
                retention_ms=86400000 * 30,  # 30 days
                cleanup_policy="delete"
            ),
            TopicType.DEAD_LETTER: TopicConfig(
                name="dead.letter.queue",
                partitions=2,
                replication_factor=3,
                retention_ms=86400000 * 90,  # 90 days
                cleanup_policy="delete"
            )
        }
    
    def create_all_topics(self) -> Dict[str, bool]:
        """Create all required topics"""
        results = {}
        
        for topic_type, config in self.topic_configs.items():
            try:
                result = self.create_topic(config)
                results[topic_type] = result
            except Exception as e:
                self.logger.error(f"Failed to create topic {config.name}: {e}")
                results[topic_type] = False
        
        return results
    
    def create_topic(self, topic_config: TopicConfig) -> bool:
        """Create a single topic with configuration"""
        try:
            topic = ConfluentNewTopic(
                topic=topic_config.name,
                num_partitions=topic_config.partitions,
                replication_factor=topic_config.replication_factor,
                config=topic_config.config_dict
            )
            
            future = self.admin_client.create_topics([topic])
            
            # Wait for topic creation
            for topic_name, future_result in future.items():
                try:
                    future_result.result(timeout=30)
                    self.logger.info(f"Topic {topic_name} created successfully")
                    return True
                except Exception as e:
                    if "already exists" in str(e).lower():
                        self.logger.info(f"Topic {topic_name} already exists")
                        return True
                    else:
                        self.logger.error(f"Failed to create topic {topic_name}: {e}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error creating topic {topic_config.name}: {e}")
            return False
    
    def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic"""
        try:
            future = self.admin_client.delete_topics([topic_name])
            
            for topic, future_result in future.items():
                try:
                    future_result.result(timeout=30)
                    self.logger.info(f"Topic {topic} deleted successfully")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to delete topic {topic}: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error deleting topic {topic_name}: {e}")
            return False
    
    def list_topics(self) -> List[str]:
        """List all topics in the cluster"""
        try:
            metadata = self.admin_client.list_topics(timeout=10)
            return list(metadata.topics.keys())
        except Exception as e:
            self.logger.error(f"Error listing topics: {e}")
            return []
    
    def get_topic_config(self, topic_name: str) -> Optional[Dict[str, str]]:
        """Get configuration for a specific topic"""
        try:
            resource = ConfigResource(ConfigResourceType.TOPIC, topic_name)
            configs = self.admin_client.describe_configs([resource])
            
            for resource, future in configs.items():
                config_dict = future.result(timeout=10)
                return {entry.name: entry.value for entry in config_dict.values()}
                
        except Exception as e:
            self.logger.error(f"Error getting config for topic {topic_name}: {e}")
            return None


class SchemaManager:
    """Avro schema management for Kafka topics"""
    
    def __init__(self, schema_registry_url: str):
        self.schema_registry_url = schema_registry_url
        self.client = SchemaRegistryClient({'url': schema_registry_url}) if schema_registry_url else None
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, str]:
        """Load Avro schemas for different event types"""
        return {
            'flight_event': '''{
                "type": "record",
                "name": "FlightEvent",
                "namespace": "com.flightdisruption.events",
                "fields": [
                    {"name": "event_id", "type": "string"},
                    {"name": "flight_id", "type": "string"},
                    {"name": "flight_number", "type": "string"},
                    {"name": "airline_code", "type": "string"},
                    {"name": "departure_airport", "type": "string"},
                    {"name": "arrival_airport", "type": "string"},
                    {"name": "event_type", "type": {"type": "enum", "name": "FlightEventType", 
                        "symbols": ["SCHEDULED", "UPDATED", "DELAYED", "CANCELLED", "DEPARTED", "ARRIVED"]}},
                    {"name": "scheduled_departure", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "scheduled_arrival", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "actual_departure", "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}], "default": null},
                    {"name": "actual_arrival", "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}], "default": null},
                    {"name": "delay_minutes", "type": ["null", "int"], "default": null},
                    {"name": "gate", "type": ["null", "string"], "default": null},
                    {"name": "status", "type": "string"},
                    {"name": "metadata", "type": {"type": "map", "values": "string"}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "source", "type": "string"}
                ]
            }''',
            
            'disruption_event': '''{
                "type": "record",
                "name": "DisruptionEvent",
                "namespace": "com.flightdisruption.events",
                "fields": [
                    {"name": "event_id", "type": "string"},
                    {"name": "disruption_id", "type": "string"},
                    {"name": "disruption_type", "type": {"type": "enum", "name": "DisruptionType",
                        "symbols": ["WEATHER", "TECHNICAL", "OPERATIONAL", "SECURITY", "AIR_TRAFFIC", "CREW", "OTHER"]}},
                    {"name": "severity", "type": {"type": "enum", "name": "Severity",
                        "symbols": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}},
                    {"name": "cause", "type": "string"},
                    {"name": "affected_airports", "type": {"type": "array", "items": "string"}},
                    {"name": "affected_flights", "type": {"type": "array", "items": "string"}},
                    {"name": "start_time", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "estimated_end_time", "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}], "default": null},
                    {"name": "description", "type": "string"},
                    {"name": "impact_radius_km", "type": ["null", "double"], "default": null},
                    {"name": "metadata", "type": {"type": "map", "values": "string"}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "source", "type": "string"}
                ]
            }''',
            
            'passenger_event': '''{
                "type": "record",
                "name": "PassengerEvent",
                "namespace": "com.flightdisruption.events",
                "fields": [
                    {"name": "event_id", "type": "string"},
                    {"name": "passenger_id", "type": "string"},
                    {"name": "booking_id", "type": "string"},
                    {"name": "flight_id", "type": "string"},
                    {"name": "event_type", "type": {"type": "enum", "name": "PassengerEventType",
                        "symbols": ["BOOKED", "CHECKED_IN", "REBOOKED", "CANCELLED", "NO_SHOW", "COMPENSATED"]}},
                    {"name": "loyalty_tier", "type": ["null", "string"], "default": null},
                    {"name": "special_needs", "type": {"type": "array", "items": "string"}},
                    {"name": "contact_preferences", "type": {"type": "array", "items": "string"}},
                    {"name": "previous_flight_id", "type": ["null", "string"], "default": null},
                    {"name": "compensation_amount", "type": ["null", "double"], "default": null},
                    {"name": "metadata", "type": {"type": "map", "values": "string"}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "source", "type": "string"}
                ]
            }''',
            
            'external_data': '''{
                "type": "record",
                "name": "ExternalData",
                "namespace": "com.flightdisruption.events",
                "fields": [
                    {"name": "event_id", "type": "string"},
                    {"name": "data_source", "type": {"type": "enum", "name": "DataSource",
                        "symbols": ["WEATHER_API", "AIRPORT_API", "AIRLINE_API", "HOTEL_API", "TRANSPORT_API", "NOTIFICATION_API"]}},
                    {"name": "data_type", "type": "string"},
                    {"name": "location", "type": ["null", "string"], "default": null},
                    {"name": "payload", "type": {"type": "map", "values": ["string", "double", "long", "boolean"]}},
                    {"name": "quality_score", "type": ["null", "double"], "default": null},
                    {"name": "expiry_time", "type": ["null", {"type": "long", "logicalType": "timestamp-millis"}], "default": null},
                    {"name": "metadata", "type": {"type": "map", "values": "string"}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "source", "type": "string"}
                ]
            }''',
            
            'ml_features': '''{
                "type": "record",
                "name": "MLFeatures",
                "namespace": "com.flightdisruption.events",
                "fields": [
                    {"name": "feature_id", "type": "string"},
                    {"name": "entity_id", "type": "string"},
                    {"name": "entity_type", "type": {"type": "enum", "name": "EntityType",
                        "symbols": ["FLIGHT", "AIRPORT", "AIRLINE", "ROUTE", "PASSENGER"]}},
                    {"name": "feature_vector", "type": {"type": "array", "items": "double"}},
                    {"name": "feature_names", "type": {"type": "array", "items": "string"}},
                    {"name": "model_version", "type": "string"},
                    {"name": "prediction_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "confidence_score", "type": ["null", "double"], "default": null},
                    {"name": "metadata", "type": {"type": "map", "values": "string"}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}}
                ]
            }'''
        }
    
    def register_schemas(self) -> Dict[str, int]:
        """Register all schemas with the schema registry"""
        if not self.client:
            return {}
        
        schema_ids = {}
        for schema_name, schema_str in self.schemas.items():
            try:
                schema = avro.schema.parse(schema_str)
                subject = f"{schema_name}-value"
                schema_id = self.client.register(subject, schema)
                schema_ids[schema_name] = schema_id
            except Exception as e:
                logging.error(f"Failed to register schema {schema_name}: {e}")
        
        return schema_ids
    
    def get_serializer(self, schema_name: str) -> Optional[AvroSerializer]:
        """Get Avro serializer for a schema"""
        if not self.client or schema_name not in self.schemas:
            return None
        
        try:
            schema_str = self.schemas[schema_name]
            return AvroSerializer(self.client, schema_str)
        except Exception as e:
            logging.error(f"Failed to create serializer for {schema_name}: {e}")
            return None
    
    def get_deserializer(self, schema_name: str) -> Optional[AvroDeserializer]:
        """Get Avro deserializer for a schema"""
        if not self.client or schema_name not in self.schemas:
            return None
        
        try:
            schema_str = self.schemas[schema_name]
            return AvroDeserializer(self.client, schema_str)
        except Exception as e:
            logging.error(f"Failed to create deserializer for {schema_name}: {e}")
            return None


def get_kafka_config_from_env() -> KafkaConfig:
    """Load Kafka configuration from environment variables"""
    return KafkaConfig(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        security_protocol=os.getenv('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT'),
        sasl_mechanism=os.getenv('KAFKA_SASL_MECHANISM'),
        sasl_username=os.getenv('KAFKA_SASL_USERNAME'),
        sasl_password=os.getenv('KAFKA_SASL_PASSWORD'),
        ssl_cafile=os.getenv('KAFKA_SSL_CAFILE'),
        ssl_certfile=os.getenv('KAFKA_SSL_CERTFILE'),
        ssl_keyfile=os.getenv('KAFKA_SSL_KEYFILE'),
        schema_registry_url=os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
        client_id=os.getenv('KAFKA_CLIENT_ID', 'flight-disruption-system')
    )


def setup_kafka_infrastructure():
    """Setup complete Kafka infrastructure"""
    config = get_kafka_config_from_env()
    
    # Create topic manager and setup topics
    topic_manager = TopicManager(config)
    topic_results = topic_manager.create_all_topics()
    
    # Setup schema registry if available
    schema_manager = None
    if config.schema_registry_url:
        schema_manager = SchemaManager(config.schema_registry_url)
        schema_ids = schema_manager.register_schemas()
        logging.info(f"Registered schemas: {schema_ids}")
    
    logging.info(f"Topic creation results: {topic_results}")
    
    return {
        'config': config,
        'topic_manager': topic_manager,
        'schema_manager': schema_manager,
        'topics_created': all(topic_results.values())
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = setup_kafka_infrastructure()
    print(f"Kafka infrastructure setup completed: {result['topics_created']}")