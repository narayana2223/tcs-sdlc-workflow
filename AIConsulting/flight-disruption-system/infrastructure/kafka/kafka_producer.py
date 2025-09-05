import asyncio
import json
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from config import KafkaConfig

logger = structlog.get_logger()

class FlightKafkaProducer:
    """Production-ready Kafka producer for flight disruption events"""
    
    def __init__(self, config: KafkaConfig):
        self.config = config
        self.producer: Optional[AIOKafkaProducer] = None
        self.topics = {
            'flight': 'flight.events',
            'disruption': 'disruption.events', 
            'passenger': 'passenger.events',
            'rebooking': 'rebooking.events',
            'notification': 'notification.events',
            'compliance': 'compliance.events',
            'cost': 'cost.events',
            'external': 'external.data',
            'agent': 'agent.decisions',
            'metrics': 'system.metrics'
        }
    
    async def start(self):
        """Initialize and start Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=self._serialize_message,
                key_serializer=lambda x: x.encode() if x else None,
                compression_type='snappy',
                max_batch_size=self.config.batch_size,
                linger_ms=self.config.linger_ms,
                acks='all',
                enable_idempotence=True,
                max_in_flight_requests_per_connection=5,
                retries=3,
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
                metadata_max_age_ms=300000
            )
            
            await self.producer.start()
            logger.info("Kafka producer started successfully")
            
        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            raise
    
    async def stop(self):
        """Stop Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def send_flight_event(
        self,
        event_type: str,
        flight_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send flight-related event"""
        await self._send_event(
            topic='flight',
            event_type=event_type,
            entity_id=flight_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_disruption_event(
        self,
        event_type: str,
        disruption_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send disruption-related event"""
        await self._send_event(
            topic='disruption',
            event_type=event_type,
            entity_id=disruption_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_passenger_event(
        self,
        event_type: str,
        passenger_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send passenger-related event"""
        await self._send_event(
            topic='passenger',
            event_type=event_type,
            entity_id=passenger_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_rebooking_event(
        self,
        event_type: str,
        rebooking_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send rebooking-related event"""
        await self._send_event(
            topic='rebooking',
            event_type=event_type,
            entity_id=rebooking_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_notification_event(
        self,
        event_type: str,
        notification_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send notification-related event"""
        await self._send_event(
            topic='notification',
            event_type=event_type,
            entity_id=notification_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_compliance_event(
        self,
        event_type: str,
        compliance_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send compliance-related event"""
        await self._send_event(
            topic='compliance',
            event_type=event_type,
            entity_id=compliance_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_cost_event(
        self,
        event_type: str,
        optimization_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send cost optimization event"""
        await self._send_event(
            topic='cost',
            event_type=event_type,
            entity_id=optimization_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_external_data_event(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send external data event (weather, PSS, etc.)"""
        await self._send_event(
            topic='external',
            event_type=event_type,
            entity_id=source,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_agent_decision_event(
        self,
        event_type: str,
        agent_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send AI agent decision event"""
        await self._send_event(
            topic='agent',
            event_type=event_type,
            entity_id=agent_id,
            data=data,
            correlation_id=correlation_id
        )
    
    async def send_metrics_event(
        self,
        metric_type: str,
        service_name: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send system metrics event"""
        await self._send_event(
            topic='metrics',
            event_type=metric_type,
            entity_id=service_name,
            data=data,
            correlation_id=correlation_id
        )
    
    async def _send_event(
        self,
        topic: str,
        event_type: str,
        entity_id: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Send event to Kafka topic"""
        try:
            # Create event structure
            event = {
                'event_id': f"{entity_id}_{event_type}_{datetime.utcnow().isoformat()}",
                'event_type': event_type,
                'entity_id': entity_id,
                'correlation_id': correlation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data,
                'schema_version': '1.0',
                'source_service': 'flight-disruption-system'
            }
            
            # Get topic name
            topic_name = self.topics.get(topic)
            if not topic_name:
                raise ValueError(f"Unknown topic: {topic}")
            
            # Send to Kafka
            await self.producer.send_and_wait(
                topic_name,
                value=event,
                key=entity_id,
                partition=self._get_partition(entity_id, topic_name)
            )
            
            logger.debug(
                "Event sent to Kafka",
                topic=topic_name,
                event_type=event_type,
                entity_id=entity_id,
                correlation_id=correlation_id
            )
            
        except KafkaError as e:
            logger.error(
                "Failed to send event to Kafka",
                topic=topic,
                event_type=event_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error sending event",
                topic=topic,
                event_type=event_type,
                entity_id=entity_id,
                error=str(e)
            )
            raise
    
    def _serialize_message(self, value: Dict[str, Any]) -> bytes:
        """Serialize message to JSON bytes"""
        try:
            return json.dumps(value, default=self._json_serializer).encode()
        except Exception as e:
            logger.error("Failed to serialize message", error=str(e))
            raise
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _get_partition(self, key: str, topic: str) -> Optional[int]:
        """Get partition for message based on key"""
        # Simple hash-based partitioning
        # In production, you might want more sophisticated partitioning logic
        return hash(key) % self.config.default_partitions
    
    async def send_batch_events(self, events: list):
        """Send multiple events in batch"""
        try:
            tasks = []
            for event in events:
                task = self._send_event(**event)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            logger.info(f"Batch of {len(events)} events sent successfully")
            
        except Exception as e:
            logger.error("Failed to send batch events", error=str(e))
            raise
    
    async def get_producer_metrics(self) -> Dict[str, Any]:
        """Get producer metrics"""
        if not self.producer:
            return {"status": "not_initialized"}
        
        try:
            # Get basic producer metrics
            metrics = {
                "status": "running",
                "bootstrap_servers": self.config.bootstrap_servers,
                "topics": list(self.topics.values()),
                "compression_type": "snappy",
                "batch_size": self.config.batch_size,
                "linger_ms": self.config.linger_ms
            }
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get producer metrics", error=str(e))
            return {"status": "error", "error": str(e)}