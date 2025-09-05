# AI Agent Framework for Flight Disruption Management

A sophisticated multi-agent system using LangChain and LangGraph for autonomous flight disruption management with advanced decision-making capabilities.

## 🚀 Overview

This AI agent framework provides autonomous management of flight disruptions through coordinated multi-agent workflows. The system handles prediction, passenger management, resource optimization, communication, and strategic coordination with full audit trails and explainable AI decisions.

### Key Features

- **🤖 Multi-Agent Orchestration** - 5 specialized agents with LangGraph workflows
- **🧠 Autonomous Decision Making** - No human oversight required for routine operations
- **📊 Real-time Learning** - Continuous improvement from operational outcomes
- **💰 Cost-Benefit Analysis** - Every decision includes financial impact assessment
- **📋 Regulatory Compliance** - Built-in EU261 and GDPR compliance
- **🔍 Explainable AI** - Complete decision reasoning and audit trails

## 🏗️ Architecture

### Agent Types

1. **PredictionAgent** - AI-powered disruption forecasting (2-4 hour advance notice)
2. **PassengerAgent** - Intelligent rebooking and EU261 compliance
3. **ResourceAgent** - Cost optimization for hotels, transport, and services
4. **CommunicationAgent** - Multi-channel passenger communications
5. **CoordinatorAgent** - Master orchestration and strategic decisions

### Core Components

- **BaseAgent** - Foundation class with shared memory and decision tracking
- **AgentOrchestrator** - LangGraph-based workflow management
- **SharedMemory** - Cross-agent state and context management
- **PerformanceMonitor** - Real-time performance tracking and optimization
- **Custom Tools** - 15+ airline-specific operation tools

## 🚀 Quick Start

### Installation

```bash
# Install required dependencies
pip install langchain langchain-openai langgraph structlog pydantic

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export WEATHER_API_KEY="your-weather-api-key"  # Optional
```

### Basic Usage

```python
import asyncio
from shared.agents.agent_factory import AgentManager, AgentConfiguration
from shared.agents.orchestrator import TaskPriority

async def handle_disruption():
    # Configure agent system
    config = AgentConfiguration(
        openai_api_key="your-openai-api-key",
        model_name="gpt-4",
        temperature=0.1
    )
    
    # Create and initialize agent manager
    manager = AgentManager(config)
    await manager.initialize_system()
    
    # Define disruption scenario
    disruption_context = {
        "incident_id": "DISRUPTION_001",
        "type": "weather_delay", 
        "airport_code": "LHR",
        "affected_flights": [
            {"flight_number": "BA123", "passengers": 180},
            {"flight_number": "BA456", "passengers": 200}
        ],
        "severity": "medium",
        "expected_delay_hours": 4
    }
    
    # Let AI agents handle the disruption autonomously
    result = await manager.handle_disruption(
        disruption_context=disruption_context,
        priority=TaskPriority.HIGH
    )
    
    print(f"✅ Disruption handled by {len(result['agents_involved'])} agents")
    print(f"Execution time: {result['execution_time']:.2f} seconds")
    
    manager.shutdown()

# Run the example
asyncio.run(handle_disruption())
```

## 🔧 Available Workflows

### 1. Disruption Response Workflow
Comprehensive handling of flight disruptions with multi-agent coordination.

```python
result = await manager.handle_disruption(
    disruption_context={
        "type": "weather_delay",
        "airport_code": "LHR", 
        "affected_passengers": 380,
        "severity": "high"
    },
    priority=TaskPriority.CRITICAL
)
```

### 2. Passenger Rebooking Workflow  
Intelligent passenger rebooking with preference optimization.

```python
result = await manager.process_passenger_rebooking(
    passenger_context={
        "affected_passengers": [
            {"passenger_id": "PAX001", "tier_status": "Gold"},
            {"passenger_id": "PAX002", "tier_status": "Regular"}
        ],
        "rebooking_options": {"same_day_alternatives": 3}
    },
    priority=TaskPriority.HIGH
)
```

### 3. Cost Optimization Workflow
AI-driven cost optimization across all resources.

```python  
result = await manager.optimize_costs(
    cost_context={
        "disruption_costs": {
            "hotel_accommodation": 15000,
            "compensation": 25000
        },
        "optimization_targets": {"cost_reduction_percentage": 15}
    }
)
```

### 4. Communication Campaign Workflow
Multi-channel passenger communication with personalization.

```python
result = await manager.send_communications(
    communication_context={
        "affected_passengers": 500,
        "message_content": "Flight delay notification", 
        "urgency": "high"
    }
)
```

### 5. Predictive Analysis Workflow
Proactive disruption prediction and impact analysis.

```python
result = await manager.get_predictions(
    prediction_context={
        "forecast_window_hours": 4,
        "airports": ["LHR", "CDG", "FRA"],
        "weather_data": {"lhr": {"severity": "high"}}
    }
)
```

## 🛠️ Agent Configuration

### Agent System Configuration

```python
config = AgentConfiguration(
    openai_api_key="your-api-key",
    model_name="gpt-4",           # or gpt-3.5-turbo
    temperature=0.1,              # Low for consistency
    max_tokens=2000,              # Response length
    request_timeout=30            # API timeout
)
```

### Individual Agent Customization

```python
# Create custom agent with specific tools
prediction_agent = factory.create_agent(
    agent_type=AgentType.PREDICTION,
    agent_id="custom_predictor_01",
    max_memory_window=50,         # Conversation history
    prediction_window_hours=6,    # Custom forecast window
    confidence_threshold=0.8      # Higher confidence requirement
)
```

## 🔍 Decision Tracking & Audit Trails

Every agent decision is automatically tracked with complete audit trails:

```python
# Get decision history
decisions = await shared_memory.get_decisions(
    agent_type=AgentType.PASSENGER,
    since=datetime.now() - timedelta(hours=24),
    limit=100
)

# Analyze decision
for decision in decisions:
    print(f"Decision: {decision.decision_type}")
    print(f"Confidence: {decision.confidence.value}")  
    print(f"Reasoning: {decision.reasoning}")
    print(f"Cost Impact: £{decision.estimated_cost}")
    print(f"Tools Used: {decision.tools_used}")
```

### Learning from Outcomes

```python
# Provide feedback on decision outcomes
await agent.learn_from_outcome(
    decision_id="decision-123",
    outcome="successful_rebooking", 
    actual_cost=150.0,
    actual_benefit=400.0,
    feedback_score=0.9  # 0-1 scale
)
```

## 📊 Performance Monitoring

### Real-time Metrics

```python
# Get system performance
performance = await manager.get_system_performance()

print(f"System Health: {performance['health_check']['overall_health']}")
print(f"Total Agents: {performance['system_status']['total_agents']}")

# Agent-specific metrics
for agent_type, metrics in performance['agent_performance'].items():
    success_rate = metrics['success_rate'] * 100
    avg_response = metrics['avg_duration_ms'] / 1000
    print(f"{agent_type}: {success_rate:.1f}% success, {avg_response:.2f}s response")
```

### Health Checks

```python
# Automated health monitoring
health_check = await factory.health_check()

if health_check['overall_health'] != 'healthy':
    print("🚨 System Issues Detected:")
    for issue in health_check['issues']:
        print(f"  - {issue}")
```

## 🛡️ Error Handling & Reliability

### Circuit Breaker Pattern
Built-in circuit breakers protect against cascading failures:

```python
# Automatic circuit breaker activation
# - 5+ failures in 60 seconds -> circuit opens
# - Exponential backoff recovery
# - Automatic health check recovery
```

### Graceful Degradation
System continues operating even with agent failures:

```python
# If passenger agent fails:
# -> Coordinator takes over passenger tasks
# -> Reduced functionality but core operations continue
# -> Automatic recovery attempts every 5 minutes
```

## 🔧 Custom Tools Development

### Creating Custom Tools

```python
from shared.agents.tools import AirlineOperationTool, ToolCategory

class CustomFlightTool(AirlineOperationTool):
    name = "custom_flight_checker" 
    description = "Check custom flight data"
    category = ToolCategory.FLIGHT_OPERATIONS
    
    async def _arun(self, flight_number: str):
        # Your custom logic here
        return {"status": "checked", "flight": flight_number}

# Register custom tool
from shared.agents.tools import tool_registry
tool_registry.register_tool(CustomFlightTool())
```

### Available Tool Categories

- **FLIGHT_OPERATIONS** - Flight status, alternatives, disruption analysis
- **PASSENGER_SERVICES** - Passenger data, rebooking, compensation
- **COST_MANAGEMENT** - Cost calculation, hotel booking, optimization
- **COMMUNICATION** - Notifications, messaging, response tracking  
- **DATA_ANALYSIS** - Pattern analysis, prediction, reporting
- **COMPLIANCE** - EU261 checking, regulatory validation

## 📈 Advanced Features

### Multi-Agent Coordination

```python
# Agents automatically coordinate through shared memory
await prediction_agent.coordinate_with_agents(
    message={
        "type": "disruption_forecast",
        "severity": "high", 
        "affected_flights": ["BA123", "BA456"]
    },
    target_agents=["passenger_agent", "resource_agent"]
)
```

### Dynamic Decision Making

```python
# Agents make context-aware decisions
decision = await passenger_agent.make_decision(
    context={
        "passenger_tier": "gold",
        "connection_risk": "high",
        "available_alternatives": 3
    },
    decision_type="rebooking_priority",
    alternatives=[
        {"option": "same_day", "cost": 50, "satisfaction": 0.9},
        {"option": "next_day", "cost": 200, "satisfaction": 0.6}
    ]
)
```

### Cost-Benefit Optimization

```python
# Every decision includes financial analysis
print(f"Estimated Cost: £{decision.estimated_cost}")
print(f"Estimated Benefit: £{decision.estimated_benefit}") 
print(f"ROI: {(decision.estimated_benefit - decision.estimated_cost) / decision.estimated_cost * 100:.1f}%")
```

## 🔒 Security & Compliance

### Data Privacy (GDPR)
- Passenger data encrypted in memory
- Automatic data retention policies  
- Right to be forgotten implementation
- Audit trails for data access

### EU261 Compliance
- Automatic compensation calculation
- Regulatory requirement validation
- Compliance reporting and documentation
- Legal decision justification

### API Security
- JWT token authentication
- Rate limiting and abuse protection
- TLS encryption for all communications
- Secret management integration

## 🚀 Production Deployment

### Docker Integration

```yaml
# docker-compose.yml
services:
  flight-ai-agents:
    build: 
      context: ./shared/agents
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    volumes:
      - ./shared/agents:/app/agents
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flight-ai-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flight-ai-agents
  template:
    spec:
      containers:
      - name: agents
        image: flight-disruption/ai-agents:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-secrets
              key: openai-api-key
```

### Monitoring & Alerting

```python
# Prometheus metrics integration
from prometheus_client import Counter, Histogram, Gauge

agent_decisions_total = Counter(
    'agent_decisions_total', 
    'Total agent decisions', 
    ['agent_type', 'decision_type']
)

decision_duration = Histogram(
    'agent_decision_duration_seconds',
    'Time spent on decisions',
    ['agent_type']
)
```

## 📚 Examples & Tutorials

Complete examples are available in the `examples/` directory:

- **`basic_usage.py`** - Getting started with core workflows
- **`advanced_coordination.py`** - Multi-agent coordination patterns
- **`custom_tools.py`** - Creating and integrating custom tools
- **`performance_optimization.py`** - System tuning and optimization
- **`production_deployment.py`** - Production-ready configurations

### Running Examples

```bash
cd shared/agents/examples
python basic_usage.py
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-agent`)
3. **Add comprehensive tests**
4. **Update documentation** 
5. **Submit pull request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black shared/agents/
isort shared/agents/

# Type checking 
mypy shared/agents/
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: [Flight Disruption System Docs](../../../docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/flight-disruption-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/flight-disruption-system/discussions)
- **Email**: support@your-airline.com

---

**Built with ❤️ for autonomous flight disruption management**