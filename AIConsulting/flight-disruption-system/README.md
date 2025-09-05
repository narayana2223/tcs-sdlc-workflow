# Flight Disruption Management System

A production-ready microservices system for UK airlines to handle flight disruptions autonomously.

## System Overview

This system manages 10,000+ passengers during major disruptions with AI-powered prediction, autonomous decision-making, and EU261 compliance.

### Core Services

1. **Disruption Predictor** - AI/ML service for 2-4 hour advance predictions
2. **Passenger Management** - Handles rebooking and passenger data
3. **Cost Optimizer** - Optimizes hotels, transport, and compensation costs
4. **Compliance Service** - Ensures EU261 regulatory compliance
5. **Notification Service** - Real-time passenger communication

### Architecture

- **Microservices**: FastAPI-based services
- **Event Streaming**: Apache Kafka for real-time events
- **AI/ML**: LangChain/LangGraph for autonomous agents
- **Containerization**: Docker with Kubernetes support
- **Monitoring**: Prometheus, Grafana, ELK Stack

## Quick Start

```bash
# Start all services
docker-compose up -d

# View services
docker-compose ps

# View logs
docker-compose logs -f [service-name]
```

## Project Structure

```
flight-disruption-system/
├── services/                    # Core microservices
│   ├── disruption-predictor/   # AI prediction service
│   ├── passenger-management/   # Passenger rebooking service
│   ├── cost-optimizer/        # Cost optimization service
│   ├── compliance/             # EU261 compliance service
│   └── notification/           # Communication service
├── shared/                     # Shared components
│   ├── database/              # Database schemas and migrations
│   ├── kafka/                 # Kafka configuration
│   └── monitoring/            # Monitoring stack
├── gateway/                   # API Gateway
├── infrastructure/            # Infrastructure as Code
│   ├── docker/               # Docker configurations
│   └── k8s/                  # Kubernetes manifests
└── docs/                     # Documentation
```

## Environment Setup

1. Copy environment files:
   ```bash
   cp .env.example .env
   ```

2. Configure your settings in `.env`

3. Start the system:
   ```bash
   docker-compose up -d
   ```

## Monitoring

- **Health Checks**: `/health` endpoint on all services
- **Metrics**: Prometheus metrics at `/metrics`
- **Dashboards**: Grafana at `http://localhost:3000`
- **Logs**: ELK Stack at `http://localhost:5601`

## API Documentation

- **API Gateway**: `http://localhost:8000/docs`
- **Individual Services**: `http://localhost:[port]/docs`

## Contributing

1. Follow the microservices architecture patterns
2. Ensure all services have health checks
3. Add comprehensive logging
4. Write unit and integration tests