import asyncio
import json
import structlog
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from config import KafkaConfig

logger = structlog.get_logger()

class FlightKafkaConsumer:
    """Production-ready Kafka consumer for flight disruption events"""
    
    def __init__(self, config: KafkaConfig, consumer_group: str):
        self.config = config
        self.consumer_group = consumer_group
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        self.topics = [
            'flight.events',
            'disruption.events', 
            'passenger.events',
            'rebooking.events',
            'notification.events',
            'compliance.events',
            'cost.events',
            'external.data',
            'agent.decisions',
            'system.metrics'
        ]
    
    async def start(self, topics: Optional[List[str]] = None):
        """Initialize and start Kafka consumer"""
        try:
            topics_to_consume = topics or self.topics
            
            self.consumer = AIOKafkaConsumer(
                *topics_to_consume,
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=self._deserialize_message,
                key_deserializer=lambda x: x.decode() if x else None,
                enable_auto_commit=False,  # Manual commit for better reliability
                auto_offset_reset='earliest',
                max_poll_records=self.config.max_poll_records,
                max_poll_interval_ms=300000,  # 5 minutes
                session_timeout_ms=30000,    # 30 seconds
                heartbeat_interval_ms=3000,  # 3 seconds
                consumer_timeout_ms=1000     # 1 second
            )
            
            await self.consumer.start()
            self.running = True
            logger.info(
                "Kafka consumer started successfully",
                group_id=self.consumer_group,
                topics=topics_to_consume
            )
            
        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise
    
    async def stop(self):
        """Stop Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event types"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def consume_messages(self):
        """Main consumer loop"""
        if not self.consumer or not self.running:
            raise RuntimeError("Consumer not started")
        
        logger.info("Starting message consumption")
        
        try:
            while self.running:
                try:
                    # Poll for messages
                    msg_batch = await self.consumer.getmany(
                        timeout_ms=1000,
                        max_records=self.config.max_poll_records
                    )
                    
                    if not msg_batch:
                        continue
                    
                    # Process messages by topic partition
                    for topic_partition, messages in msg_batch.items():
                        await self._process_messages(topic_partition, messages)
                    
                    # Commit offsets after successful processing
                    await self.consumer.commit()
                    
                except KafkaError as e:
                    logger.error("Kafka error during consumption", error=str(e))
                    await asyncio.sleep(5)  # Backoff on error
                    
                except Exception as e:
                    logger.error("Unexpected error during consumption", error=str(e))
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error("Fatal error in consumer loop", error=str(e))
            raise
    
    async def _process_messages(self, topic_partition, messages):
        """Process batch of messages from a topic partition"""
        try:
            for message in messages:
                await self._process_single_message(message)
                
        except Exception as e:
            logger.error(
                "Error processing message batch",
                topic=topic_partition.topic,
                partition=topic_partition.partition,
                error=str(e)
            )
            # Don't re-raise to avoid losing the entire batch
    
    async def _process_single_message(self, message):
        """Process a single message"""
        try:
            # Extract message data
            event_data = message.value
            topic = message.topic
            partition = message.partition
            offset = message.offset
            key = message.key
            
            logger.debug(
                "Processing message",
                topic=topic,
                partition=partition,
                offset=offset,
                key=key,
                event_type=event_data.get('event_type')
            )
            
            # Validate message structure
            if not self._validate_message(event_data):
                logger.warning("Invalid message structure", event_data=event_data)
                return
            
            # Route to appropriate handler
            event_type = event_data.get('event_type')
            if event_type in self.handlers:
                await self.handlers[event_type](event_data, message)
            else:
                # Default handler
                await self._default_handler(event_data, message)
                
        except Exception as e:
            logger.error(
                "Error processing single message",
                message_key=message.key,
                error=str(e)
            )
    
    async def _default_handler(self, event_data: Dict[str, Any], message):
        """Default handler for unregistered event types"""
        logger.info(
            "Unhandled event received",
            event_type=event_data.get('event_type'),
            entity_id=event_data.get('entity_id'),
            topic=message.topic
        )
    
    def _deserialize_message(self, value: bytes) -> Dict[str, Any]:
        """Deserialize message from JSON bytes"""
        try:
            return json.loads(value.decode())
        except Exception as e:
            logger.error("Failed to deserialize message", error=str(e))
            return {}
    
    def _validate_message(self, event_data: Dict[str, Any]) -> bool:
        """Validate message structure"""
        required_fields = ['event_id', 'event_type', 'entity_id', 'timestamp', 'data']
        
        for field in required_fields:
            if field not in event_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    async def get_consumer_metrics(self) -> Dict[str, Any]:
        """Get consumer metrics"""
        if not self.consumer:
            return {"status": "not_initialized"}
        
        try:
            metrics = {
                "status": "running" if self.running else "stopped",
                "group_id": self.consumer_group,
                "subscribed_topics": list(self.consumer.subscription()),
                "registered_handlers": list(self.handlers.keys())
            }
            
            # Get partition assignments
            assignments = self.consumer.assignment()
            if assignments:
                metrics["assigned_partitions"] = [
                    {"topic": tp.topic, "partition": tp.partition}
                    for tp in assignments
                ]
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get consumer metrics", error=str(e))
            return {"status": "error", "error": str(e)}

class EventRouter:
    """Routes events to appropriate service handlers"""
    
    def __init__(self):
        self.service_handlers: Dict[str, Callable] = {}
    
    def register_service_handler(self, service_name: str, handler: Callable):
        """Register handler for a specific service"""
        self.service_handlers[service_name] = handler
        logger.info(f"Registered service handler: {service_name}")
    
    async def route_flight_event(self, event_data: Dict[str, Any], message):
        """Route flight events"""
        await self._route_to_service('flight_service', event_data, message)
    
    async def route_disruption_event(self, event_data: Dict[str, Any], message):
        """Route disruption events"""
        await self._route_to_service('disruption_service', event_data, message)
        
        # Also route to dependent services
        await self._route_to_service('passenger_service', event_data, message)
        await self._route_to_service('notification_service', event_data, message)
    
    async def route_passenger_event(self, event_data: Dict[str, Any], message):
        """Route passenger events"""
        await self._route_to_service('passenger_service', event_data, message)
    
    async def route_rebooking_event(self, event_data: Dict[str, Any], message):
        """Route rebooking events"""
        await self._route_to_service('rebooking_service', event_data, message)
        await self._route_to_service('notification_service', event_data, message)
    
    async def route_notification_event(self, event_data: Dict[str, Any], message):
        """Route notification events"""
        await self._route_to_service('notification_service', event_data, message)
    
    async def route_compliance_event(self, event_data: Dict[str, Any], message):
        """Route compliance events"""
        await self._route_to_service('compliance_service', event_data, message)
    
    async def route_cost_event(self, event_data: Dict[str, Any], message):
        """Route cost optimization events"""
        await self._route_to_service('cost_service', event_data, message)
    
    async def route_external_data_event(self, event_data: Dict[str, Any], message):
        """Route external data events"""
        source = event_data.get('entity_id', '')
        
        if 'weather' in source.lower():
            await self._route_to_service('weather_service', event_data, message)
        elif 'pss' in source.lower():
            await self._route_to_service('pss_service', event_data, message)
        else:
            await self._route_to_service('external_data_service', event_data, message)
    
    async def route_agent_decision_event(self, event_data: Dict[str, Any], message):
        """Route AI agent decision events"""
        await self._route_to_service('agent_service', event_data, message)
    
    async def route_metrics_event(self, event_data: Dict[str, Any], message):
        """Route system metrics events"""
        await self._route_to_service('metrics_service', event_data, message)
    
    async def _route_to_service(self, service_name: str, event_data: Dict[str, Any], message):
        """Route event to specific service handler"""
        try:
            if service_name in self.service_handlers:
                await self.service_handlers[service_name](event_data, message)
            else:
                logger.debug(f"No handler registered for service: {service_name}")
                
        except Exception as e:
            logger.error(
                "Error routing to service",
                service=service_name,
                event_type=event_data.get('event_type'),
                error=str(e)
            )

class ConsumerManager:
    """Manages multiple Kafka consumers for different services"""
    
    def __init__(self, config: KafkaConfig):
        self.config = config
        self.consumers: Dict[str, FlightKafkaConsumer] = {}
        self.router = EventRouter()
    
    async def create_consumer(
        self,
        consumer_name: str,
        consumer_group: str,
        topics: List[str]
    ) -> FlightKafkaConsumer:
        """Create and configure a new consumer"""
        
        consumer = FlightKafkaConsumer(self.config, consumer_group)
        
        # Register event handlers
        consumer.register_handler('flight_created', self.router.route_flight_event)
        consumer.register_handler('flight_updated', self.router.route_flight_event)
        consumer.register_handler('flight_cancelled', self.router.route_flight_event)
        
        consumer.register_handler('disruption_detected', self.router.route_disruption_event)
        consumer.register_handler('disruption_resolved', self.router.route_disruption_event)
        
        consumer.register_handler('passenger_affected', self.router.route_passenger_event)
        consumer.register_handler('passenger_notified', self.router.route_passenger_event)
        
        consumer.register_handler('rebooking_initiated', self.router.route_rebooking_event)
        consumer.register_handler('rebooking_completed', self.router.route_rebooking_event)
        
        consumer.register_handler('notification_sent', self.router.route_notification_event)
        consumer.register_handler('notification_delivered', self.router.route_notification_event)
        
        consumer.register_handler('compliance_check', self.router.route_compliance_event)
        consumer.register_handler('compensation_calculated', self.router.route_compliance_event)
        
        consumer.register_handler('cost_optimized', self.router.route_cost_event)
        consumer.register_handler('vendor_booked', self.router.route_cost_event)
        
        consumer.register_handler('weather_data', self.router.route_external_data_event)
        consumer.register_handler('pss_data', self.router.route_external_data_event)
        
        consumer.register_handler('agent_decision', self.router.route_agent_decision_event)
        consumer.register_handler('agent_action', self.router.route_agent_decision_event)
        
        consumer.register_handler('system_metric', self.router.route_metrics_event)
        
        await consumer.start(topics)
        self.consumers[consumer_name] = consumer
        
        logger.info(
            "Consumer created and started",
            name=consumer_name,
            group=consumer_group,
            topics=topics
        )
        
        return consumer
    
    async def start_all_consumers(self):
        """Start consumption for all registered consumers"""
        tasks = []
        for name, consumer in self.consumers.items():
            task = asyncio.create_task(
                consumer.consume_messages(),
                name=f"consumer-{name}"
            )
            tasks.append(task)
        
        logger.info(f"Started {len(tasks)} consumer tasks")
        return tasks
    
    async def stop_all_consumers(self):
        """Stop all consumers"""
        for name, consumer in self.consumers.items():
            await consumer.stop()
            logger.info(f"Stopped consumer: {name}")
        
        self.consumers.clear()
    
    def register_service_handler(self, service_name: str, handler: Callable):
        """Register service handler with the router"""
        self.router.register_service_handler(service_name, handler)