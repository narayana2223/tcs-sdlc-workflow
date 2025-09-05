# Getting Started - Flight Disruption Management System

This guide will help you set up and run the complete Flight Disruption Management System.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose V2
- Git (for version control)
- Minimum 8GB RAM and 4 CPU cores recommended
- Internet connection for pulling Docker images and API access

## Quick Start (5 minutes)

1. **Clone and Navigate**
   ```bash
   cd flight-disruption-system
   ```

2. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys (OpenAI, Weather, etc.)
   ```

3. **Start the System**
   ```bash
   # Make scripts executable (Unix/Mac)
   chmod +x scripts/*.sh

   # Start all services
   docker-compose up -d

   # Wait for services to be healthy (2-3 minutes)
   ./scripts/health-check.sh
   ```

4. **Access the System**
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana Dashboard: http://localhost:3000 (admin/admin_password)
   - Prometheus: http://localhost:9090

## System Architecture

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Load Balancer     │    │   API Gateway    │    │  Executive Dashboard│
│   (Production)      │    │   Port: 8000     │    │   Port: 3001        │
└─────────────────────┘    └──────────────────┘    └─────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
         ┌──────────▼─────────┐    ┌▼──────────────▼──────────┐    ┌──────────────▼─────────┐
         │ Disruption         │    │ Passenger Management     │    │ Cost Optimization      │
         │ Predictor          │    │ & Rebooking             │    │ Service                │
         │ Port: 8001         │    │ Port: 8002              │    │ Port: 8003             │
         └────────────────────┘    └─────────────────────────┘    └────────────────────────┘
                    │                           │                           │
         ┌──────────▼─────────┐    ┌──────────▼─────────┐    ┌──────────────▼─────────┐
         │ EU261 Compliance   │    │ Notification       │    │ Monitoring Stack       │
         │ Service            │    │ Service            │    │ (Prometheus/Grafana)   │
         │ Port: 8004         │    │ Port: 8005         │    │ Port: 3000/9090        │
         └────────────────────┘    └────────────────────┘    └────────────────────────┘
                    │                           │                           │
                    └───────────────┬───────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │     Infrastructure            │
                    │ PostgreSQL │ Redis │ Kafka    │
                    │ Port: 5432 │ 6379  │ 9092     │
                    └───────────────────────────────┘
```

## Core Services Overview

### 1. API Gateway (Port 8000)
- **Purpose**: Central entry point, authentication, rate limiting, routing
- **Key Features**: JWT authentication, request/response logging, metrics collection
- **Health Check**: `curl http://localhost:8000/health`

### 2. Disruption Predictor (Port 8001)
- **Purpose**: AI-powered prediction of flight disruptions 2-4 hours in advance
- **Key Features**: Weather analysis, ML models, LangGraph agents, real-time predictions
- **Key Endpoints**: `/api/v1/predictions/single`, `/api/v1/predictions/batch`

### 3. Passenger Management (Port 8002)
- **Purpose**: Handles passenger data, rebooking, and PSS integration
- **Key Features**: Intelligent rebooking engine, PSS sync, passenger notifications
- **Key Endpoints**: `/api/v1/passengers`, `/api/v1/bookings`, `/api/v1/rebookings`

### 4. Cost Optimizer (Port 8003)
- **Purpose**: Optimizes costs for hotels, transport, and compensation
- **Key Features**: AI-driven cost optimization, vendor integration, budget management
- **Key Endpoints**: `/api/v1/cost-optimization`, `/api/v1/hotels`, `/api/v1/transport`

### 5. Compliance Service (Port 8004)
- **Purpose**: Ensures EU261 regulatory compliance
- **Key Features**: Automatic compensation calculation, claim processing, regulatory reporting
- **Key Endpoints**: `/api/v1/compliance`, `/api/v1/compensation`

### 6. Notification Service (Port 8005)
- **Purpose**: Multi-channel passenger communication
- **Key Features**: SMS, email, push notifications, WhatsApp integration
- **Key Endpoints**: `/api/v1/notifications`, `/api/v1/notifications/bulk`

## Configuration

### Environment Variables (.env file)

```bash
# Database
POSTGRES_PASSWORD=secure_password_here
DATABASE_URL=postgresql://flight_user:secure_password_here@postgres:5432/flight_disruption

# AI/ML APIs (Required for predictions)
OPENAI_API_KEY=your_openai_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# External Service APIs (Optional but recommended)
AMADEUS_API_KEY=your_amadeus_api_key
SABRE_API_KEY=your_sabre_api_key
HOTEL_BOOKING_API_KEY=your_hotel_api_key
SMS_PROVIDER_API_KEY=your_sms_api_key
EMAIL_PROVIDER_API_KEY=your_email_api_key

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

### Essential API Keys

1. **OpenAI API Key** (Required)
   - Sign up at https://platform.openai.com/
   - Used for AI-powered disruption analysis and decision making

2. **Weather API Key** (Recommended)
   - Weather service for prediction accuracy
   - Try OpenWeatherMap or similar service

3. **Airline PSS APIs** (Production)
   - Amadeus, Sabre, or Travelport for real airline integration

## Testing the System

### 1. Basic Health Check
```bash
# Check all services
./scripts/health-check.sh

# Individual service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### 2. Create Test Data
```bash
# Create a test passenger
curl -X POST http://localhost:8000/api/v1/passengers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "pnr": "TEST123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+447700123456"
  }'
```

### 3. Test Prediction
```bash
# Get prediction for a flight
curl -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "flight_id": "UUID_HERE",
    "departure_time": "2024-01-15T08:00:00Z",
    "arrival_time": "2024-01-15T10:30:00Z",
    "departure_airport": "LHR",
    "arrival_airport": "CDG",
    "aircraft_type": "Airbus A320"
  }'
```

## Monitoring and Observability

### Grafana Dashboards
- **URL**: http://localhost:3000
- **Login**: admin / admin_password
- **Key Dashboards**:
  - System Overview: Service health, request rates, response times
  - Business Metrics: Disruption rates, rebooking success, compensation costs
  - Infrastructure: Database, Redis, Kafka metrics

### Prometheus Metrics
- **URL**: http://localhost:9090
- **Key Metrics**:
  - `gateway_requests_total`: API request counts
  - `disruption_predictions_total`: Prediction counts by type
  - `rebookings_total`: Rebooking success/failure rates
  - `notifications_sent_total`: Notification delivery rates

### Logs
```bash
# Collect all service logs
./scripts/collect-logs.sh

# View live logs for specific service
docker-compose logs -f passenger-management
```

## Scaling and Production

### Horizontal Scaling
```bash
# Scale passenger management service
docker-compose up -d --scale passenger-management=3

# Scale disruption predictor
docker-compose up -d --scale disruption-predictor=2
```

### Database Performance
- **Connection Pooling**: Configured for 20 max connections per service
- **Indexing**: Optimized indexes for frequent queries
- **Monitoring**: Built-in connection and query monitoring

### Caching Strategy
- **Redis**: Used for prediction caching, rate limiting, session storage
- **TTL**: 1 hour for predictions, 30 minutes for rebooking options

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check Docker resources
   docker system df
   docker system prune -f
   
   # Restart services
   docker-compose down
   docker-compose up -d
   ```

2. **Database connection issues**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready
   
   # View database logs
   docker-compose logs postgres
   ```

3. **High CPU/Memory usage**
   ```bash
   # Check resource usage
   docker stats
   
   # Scale down resource-intensive services
   docker-compose up -d --scale disruption-predictor=1
   ```

4. **AI predictions not working**
   - Verify OpenAI API key in `.env`
   - Check API quota and billing
   - View prediction service logs: `docker-compose logs disruption-predictor`

### Performance Optimization

1. **Database**
   - Increase `max_connections` for high load
   - Add read replicas for reporting queries
   - Use connection pooling (pgbouncer)

2. **Caching**
   - Increase Redis memory limit
   - Implement application-level caching
   - Use CDN for static content

3. **AI/ML Services**
   - Cache prediction results
   - Use model quantization
   - Implement prediction batching

## Support and Development

### Development Setup
```bash
# Install development dependencies
pip install -r shared/requirements.txt
pip install pytest black isort mypy

# Run tests (when implemented)
pytest tests/

# Code formatting
black services/
isort services/
```

### Adding New Services
1. Create service directory in `services/`
2. Add Dockerfile and requirements.txt
3. Update docker-compose.yml
4. Add service routes in API Gateway
5. Update monitoring configuration

### API Documentation
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Getting Help
1. Check service logs: `docker-compose logs [service-name]`
2. Verify configuration in `.env` file
3. Run health checks: `./scripts/health-check.sh`
4. Check monitoring dashboards for system metrics

## Next Steps

1. **Customize Configuration**: Update `.env` with your actual API keys and settings
2. **Load Test Data**: Import your flight and passenger data
3. **Configure Integrations**: Set up airline PSS, notification providers
4. **Set Up Monitoring**: Configure alerts and notification channels
5. **Scale for Production**: Set up load balancers, multiple instances
6. **Security Hardening**: Implement proper SSL, network policies, secrets management

---

**System Status**: All core services implemented and functional
**Last Updated**: January 2024
**Version**: 1.0.0