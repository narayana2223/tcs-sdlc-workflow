# Flight Disruption System - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
```bash
# Install Python dependencies
pip install confluent-kafka pydantic sqlalchemy aiohttp backoff avro-python3

# Start Kafka (Docker)
docker run -d --name zookeeper -p 2181:2181 confluentinc/cp-zookeeper:latest
docker run -d --name kafka -p 9092:9092 --link zookeeper confluentinc/cp-kafka:latest
```

### Environment Variables
```bash
# Kafka Configuration
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export SCHEMA_REGISTRY_URL=http://localhost:8081

# API Configuration (Mock Mode)
export FLIGHT_DATA_API_MOCK_MODE=true
export WEATHER_API_MOCK_MODE=true
export AIRLINE_SYSTEM_API_MOCK_MODE=true

# Demo Configuration
export DEMO_SCENARIO=weather_disruption
export DEMO_DURATION_HOURS=4
export DEMO_SPEED_MULTIPLIER=10.0
```

## 🎮 Running the System

### 1. Basic System Startup
```python
import asyncio
from infrastructure.main import start_system

async def main():
    system = await start_system()
    # System is now running
    await system.get_system_status()  # Check status

asyncio.run(main())
```

### 2. Run Demo Scenarios
```python
import asyncio
from infrastructure.main import flight_disruption_system
from infrastructure.demo.mock_data_generator import ScenarioType

async def run_demo():
    async with flight_disruption_system() as system:
        # Run weather disruption scenario
        await system.run_demo_scenario(
            ScenarioType.WEATHER_DISRUPTION,
            duration_hours=4,
            speed_multiplier=10.0  # 10x speed
        )

asyncio.run(run_demo())
```

### 3. Command Line Usage
```bash
# Start system with demo
python -m infrastructure.main

# With specific scenario
DEMO_SCENARIO=network_wide_chaos python -m infrastructure.main
```

## 📊 Available Demo Scenarios

| Scenario | Code | Description |
|----------|------|-------------|
| Normal Operations | `normal_operations` | Typical day, minimal disruptions |
| Weather Disruption | `weather_disruption` | Severe weather at major hub |
| Technical Delays | `technical_delays` | Airline technical issues |
| Airport Congestion | `airport_congestion` | ATC congestion |
| Cascading Delays | `cascading_delays` | Network-wide delay cascade |
| Airline Disruption | `airline_disruption` | Fleet-wide operational issues |
| Network Chaos | `network_wide_chaos` | Multiple simultaneous disruptions |

## 🔍 Monitoring System Health

```python
# Check system health
status = await system.get_system_status()
print(f"System Status: {status['health']['overall_status']}")

# Monitor specific components
stream_metrics = status['components']['stream_processors']
error_stats = status['components']['error_handler']

# Check Kafka topics
from infrastructure.kafka.kafka_config import setup_kafka_infrastructure
kafka_setup = setup_kafka_infrastructure()
topics = kafka_setup['topic_manager'].list_topics()
```

## 🎯 Key Components Usage

### Kafka Producers
```python
from infrastructure.kafka.producers import ProducerFactory
from infrastructure.kafka.kafka_config import get_kafka_config_from_env

config = get_kafka_config_from_env()
factory = ProducerFactory(config)

# Send flight event
flight_producer = factory.create_flight_producer()
flight_producer.send_flight_delayed(
    flight_id="FL123",
    delay_minutes=45,
    reason="Weather",
    new_departure_time=datetime.now() + timedelta(minutes=45),
    new_arrival_time=datetime.now() + timedelta(hours=2, minutes=45)
)
```

### Stream Processing
```python
from infrastructure.streaming.stream_processor import create_default_stream_processors

# Create and start stream processors
stream_manager = await create_default_stream_processors(config)
await stream_manager.start_all()

# Get processing metrics
metrics = stream_manager.get_all_metrics()
```

### External API Clients
```python
from infrastructure.external_apis.weather_client import WeatherClient
from infrastructure.external_apis.base_client import create_api_config_from_env

# Create weather client
weather_config = create_api_config_from_env('WEATHER')
weather_config.mock_mode = True

async with WeatherClient(weather_config) as client:
    weather_data = await client.get_current_weather('LHR')
    print(f"Weather at LHR: {weather_data.condition}")
```

## 🛠️ Configuration Options

### Kafka Topics
```python
# Topic configurations are in kafka_config.py
from infrastructure.kafka.kafka_config import TopicType

# Available topics:
# - TopicType.FLIGHT_EVENTS
# - TopicType.DISRUPTION_EVENTS
# - TopicType.PASSENGER_EVENTS
# - TopicType.EXTERNAL_DATA
# - TopicType.NOTIFICATIONS
# - TopicType.ML_FEATURES
# - TopicType.SYSTEM_METRICS
# - TopicType.DEAD_LETTER
```

### Stream Processing
```python
# Configure stream processors
processor_config = {
    'batch_size': 100,
    'max_processing_time_ms': 5000,
    'buffer_timeout_seconds': 1.0,
    'enable_exactly_once': True
}
```

### Error Handling
```python
from infrastructure.reliability.error_handler import create_default_retry_config

# Configure retry behavior
retry_config = create_default_retry_config(max_attempts=3)

# Network-specific retry config
network_retry = create_network_retry_config()
```

## 📈 Performance Tuning

### High Throughput Setup
```python
# Increase Kafka producer settings
producer_config = {
    'batch.size': 32768,           # 32KB batches
    'linger.ms': 5,                # Wait 5ms for batching
    'compression.type': 'lz4',     # Fast compression
    'acks': 'all',                 # Durability
    'retries': 3                   # Reliability
}

# Increase consumer settings
consumer_config = {
    'fetch.min.bytes': 50000,      # 50KB minimum fetch
    'fetch.max.wait.ms': 100,      # Max 100ms wait
    'max.poll.records': 1000       # Process 1000 records per poll
}
```

### Memory Optimization
```python
# Configure event window sizes
event_window_config = {
    'window_size_seconds': 3600,   # 1 hour window
    'cleanup_interval': 300,       # Clean every 5 minutes
    'max_events_in_memory': 10000  # Memory limit
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Kafka Connection Failed**
   ```bash
   # Check Kafka is running
   docker ps | grep kafka
   
   # Test connection
   kafka-topics --list --bootstrap-server localhost:9092
   ```

2. **Schema Registry Issues**
   ```bash
   # Start schema registry
   docker run -d -p 8081:8081 --link kafka confluentinc/cp-schema-registry:latest
   ```

3. **High Memory Usage**
   ```python
   # Reduce event window size
   event_window = EventWindow(window_size_seconds=1800)  # 30 minutes
   
   # Enable cleanup
   processor.clear_expired_cache()
   ```

4. **Processing Delays**
   ```python
   # Check processor metrics
   metrics = processor.get_metrics()
   print(f"Backlog: {metrics['backlog_size']}")
   print(f"Processing time: {metrics['processing_time_ms_avg']}")
   
   # Increase batch size
   processor.batch_size = 200
   ```

## 🔧 Development Tips

### Adding New Event Types
```python
# 1. Define in kafka_config.py
class NewEventType(str, Enum):
    MY_EVENT = "my_event"

# 2. Create producer method
class MyEventProducer:
    def send_my_event(self, data):
        return self.producer.send_message(
            topic=TopicType.MY_EVENTS,
            message=data
        )

# 3. Add stream processor
class MyEventProcessor(BaseStreamProcessor):
    async def process_events(self, events):
        # Process events
        return processed_events
```

### Custom Pattern Detection
```python
# Add to PatternMatcher in event_correlator.py
def _detect_my_pattern(self, window):
    # Custom pattern detection logic
    events = window.get_events_by_type(EventType.MY_EVENT)
    
    if self._matches_my_criteria(events):
        return [DetectedPattern(
            pattern_id=f"my_pattern_{int(time.time())}",
            pattern_type=PatternType.MY_PATTERN,
            events=[e.event_id for e in events],
            confidence_score=0.8
        )]
    
    return []
```

### Adding External APIs
```python
# Extend base_client.py
class MyAPIClient(CachedAPIClient):
    async def get_my_data(self, params):
        response = await self._make_cached_request(
            'GET', '/my-endpoint', params=params
        )
        return self._parse_my_response(response.data)
```

## 📞 Support Commands

```bash
# System status
curl http://localhost:8000/health

# Kafka topic status
kafka-topics --describe --bootstrap-server localhost:9092

# View recent logs
tail -f /tmp/flight-disruption-system.log

# Monitor resource usage
htop
```

## 🎯 Production Checklist

- [ ] Configure production Kafka cluster
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure real API endpoints
- [ ] Set up SSL/TLS encryption  
- [ ] Configure backup and recovery
- [ ] Set up alerting (PagerDuty/Slack)
- [ ] Load test with production volumes
- [ ] Security audit and penetration testing
- [ ] Disaster recovery testing

---

**Need Help?** Check the logs, review error metrics, or consult the full documentation in `INFRASTRUCTURE_SUMMARY.md`