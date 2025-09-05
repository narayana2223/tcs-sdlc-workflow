from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import structlog
from datetime import datetime, timedelta
from uuid import uuid4
import redis.asyncio as redis
import httpx
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from config import settings
from database import Database
from advanced_agent_system import AdvancedAgentSystem
from decision_engine import DecisionEngine
from reasoning_engine import ReasoningEngine
from multi_agent_coordinator import MultiAgentCoordinator

# Prometheus metrics
AGENT_DECISIONS = Counter('agent_decisions_total', 'Total agent decisions made', ['agent_type', 'decision_type'])
REASONING_TIME = Histogram('agent_reasoning_seconds', 'Time spent on reasoning', ['agent_type'])
ACTIVE_AGENTS = Gauge('active_agents', 'Currently active agents')
AGENT_CONFLICTS = Counter('agent_conflicts_total', 'Agent conflicts resolved', ['conflict_type'])

logger = structlog.get_logger()

# Pydantic models
class AgentType(str, Enum):
    DISRUPTION_PREDICTOR = "disruption_predictor"
    PASSENGER_MANAGER = "passenger_manager"
    COST_OPTIMIZER = "cost_optimizer"
    COMPLIANCE_CHECKER = "compliance_checker"
    COMMUNICATION_MANAGER = "communication_manager"
    RESOURCE_ALLOCATOR = "resource_allocator"
    EXECUTIVE_ADVISOR = "executive_advisor"

class DecisionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ReasoningRequest(BaseModel):
    scenario_id: str
    scenario_type: str
    context_data: Dict[str, Any]
    involved_agents: List[AgentType]
    priority: DecisionPriority = DecisionPriority.NORMAL
    time_constraint: Optional[int] = None  # seconds
    constraints: Optional[Dict[str, Any]] = None

class AgentDecision(BaseModel):
    decision_id: str
    agent_type: AgentType
    decision_type: str
    reasoning_chain: List[Dict[str, Any]]
    confidence_score: float
    execution_plan: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]
    estimated_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    alternatives_considered: List[Dict[str, Any]]
    created_at: datetime

class MultiAgentResponse(BaseModel):
    session_id: str
    coordinated_decision: Dict[str, Any]
    individual_decisions: List[AgentDecision]
    consensus_score: float
    conflict_resolution: Optional[Dict[str, Any]]
    execution_timeline: List[Dict[str, Any]]
    total_reasoning_time: float
    resource_allocation: Dict[str, Any]

class ScenarioExecution(BaseModel):
    execution_id: str
    scenario_type: str
    status: str
    current_step: int
    total_steps: int
    agent_activities: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    started_at: datetime
    estimated_completion: datetime

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
agent_system: Optional[AdvancedAgentSystem] = None
decision_engine: Optional[DecisionEngine] = None
reasoning_engine: Optional[ReasoningEngine] = None
multi_agent_coordinator: Optional[MultiAgentCoordinator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, http_client, kafka_producer, kafka_consumer
    global agent_system, decision_engine, reasoning_engine, multi_agent_coordinator
    
    try:
        # Initialize database
        db = Database()
        await db.connect()
        logger.info("Database connected successfully")
        
        # Initialize Redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("Redis connected successfully")
        
        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("HTTP client initialized")
        
        # Initialize Kafka producer
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda x: json.dumps(x, default=str).encode()
        )
        await kafka_producer.start()
        logger.info("Kafka producer started")
        
        # Initialize advanced AI systems
        reasoning_engine = ReasoningEngine(
            openai_api_key=settings.openai_api_key,
            redis_client=redis_client
        )
        await reasoning_engine.initialize()
        
        decision_engine = DecisionEngine(
            db=db,
            reasoning_engine=reasoning_engine,
            kafka_producer=kafka_producer
        )
        
        multi_agent_coordinator = MultiAgentCoordinator(
            decision_engine=decision_engine,
            redis_client=redis_client
        )
        
        agent_system = AdvancedAgentSystem(
            db=db,
            redis_client=redis_client,
            http_client=http_client,
            kafka_producer=kafka_producer,
            reasoning_engine=reasoning_engine,
            decision_engine=decision_engine,
            coordinator=multi_agent_coordinator
        )
        
        await agent_system.initialize()
        
        logger.info("Agent orchestrator service started successfully")
        
    except Exception as e:
        logger.error("Failed to start agent orchestrator service", error=str(e))
        raise
    
    yield
    
    # Shutdown
    try:
        if kafka_producer:
            await kafka_producer.stop()
        if db:
            await db.disconnect()
        if redis_client:
            await redis_client.aclose()
        if http_client:
            await http_client.aclose()
        if agent_system:
            await agent_system.shutdown()
        logger.info("Agent orchestrator service shutdown completed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# FastAPI app
app = FastAPI(
    title="Advanced Agent Orchestrator Service",
    description="AI agent coordination and decision-making service for flight disruptions",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        await db.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check agent system
        agent_status = await agent_system.get_system_health()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "agent_system": agent_status,
                "active_agents": await agent_system.get_active_agent_count()
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/api/v1/reasoning/request", response_model=MultiAgentResponse)
async def request_multi_agent_reasoning(
    request: ReasoningRequest,
    background_tasks: BackgroundTasks
) -> MultiAgentResponse:
    """Request multi-agent reasoning for complex scenarios"""
    
    start_time = datetime.utcnow()
    session_id = str(uuid4())
    
    try:
        logger.info(
            "Processing multi-agent reasoning request",
            session_id=session_id,
            scenario_type=request.scenario_type,
            agents=request.involved_agents,
            priority=request.priority
        )
        
        # Coordinate multi-agent decision making
        result = await multi_agent_coordinator.coordinate_decision(
            session_id=session_id,
            scenario_type=request.scenario_type,
            context_data=request.context_data,
            involved_agents=request.involved_agents,
            priority=request.priority,
            time_constraint=request.time_constraint,
            constraints=request.constraints
        )
        
        # Update metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        REASONING_TIME.labels(agent_type="multi_agent").observe(processing_time)
        AGENT_DECISIONS.labels(
            agent_type="coordinator",
            decision_type=request.scenario_type
        ).inc()
        
        # Publish decision event
        await kafka_producer.send(
            'agent.decisions',
            value={
                'session_id': session_id,
                'decision_type': 'multi_agent_coordination',
                'agents_involved': [agent.value for agent in request.involved_agents],
                'consensus_score': result['consensus_score'],
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(
            "Multi-agent reasoning completed",
            session_id=session_id,
            consensus_score=result['consensus_score'],
            processing_time=processing_time
        )
        
        return MultiAgentResponse(
            session_id=session_id,
            coordinated_decision=result['coordinated_decision'],
            individual_decisions=[
                AgentDecision(**decision) for decision in result['individual_decisions']
            ],
            consensus_score=result['consensus_score'],
            conflict_resolution=result.get('conflict_resolution'),
            execution_timeline=result['execution_timeline'],
            total_reasoning_time=processing_time,
            resource_allocation=result['resource_allocation']
        )
        
    except Exception as e:
        logger.error(
            "Failed to process multi-agent reasoning",
            session_id=session_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/scenarios/execute")
async def execute_disruption_scenario(
    scenario_type: str,
    scenario_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> ScenarioExecution:
    """Execute a disruption scenario with autonomous agents"""
    
    execution_id = str(uuid4())
    
    try:
        logger.info(
            "Starting scenario execution",
            execution_id=execution_id,
            scenario_type=scenario_type
        )
        
        # Start scenario execution
        execution = await agent_system.execute_scenario(
            execution_id=execution_id,
            scenario_type=scenario_type,
            scenario_data=scenario_data
        )
        
        # Track execution in background
        background_tasks.add_task(
            agent_system.monitor_scenario_execution,
            execution_id
        )
        
        return ScenarioExecution(
            execution_id=execution_id,
            scenario_type=scenario_type,
            status=execution['status'],
            current_step=execution['current_step'],
            total_steps=execution['total_steps'],
            agent_activities=execution['agent_activities'],
            performance_metrics=execution['performance_metrics'],
            started_at=execution['started_at'],
            estimated_completion=execution['estimated_completion']
        )
        
    except Exception as e:
        logger.error("Failed to execute scenario", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/scenarios/{execution_id}/status")
async def get_scenario_status(execution_id: str) -> ScenarioExecution:
    """Get scenario execution status"""
    
    try:
        execution = await agent_system.get_scenario_status(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Scenario execution not found")
        
        return ScenarioExecution(**execution)
        
    except Exception as e:
        logger.error("Failed to get scenario status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    
    try:
        status = await agent_system.get_all_agents_status()
        return status
        
    except Exception as e:
        logger.error("Failed to get agents status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{agent_type}/decision")
async def request_agent_decision(
    agent_type: AgentType,
    scenario_data: Dict[str, Any],
    priority: DecisionPriority = DecisionPriority.NORMAL
) -> AgentDecision:
    """Request decision from specific agent"""
    
    try:
        decision = await agent_system.get_agent_decision(
            agent_type=agent_type,
            scenario_data=scenario_data,
            priority=priority
        )
        
        AGENT_DECISIONS.labels(
            agent_type=agent_type.value,
            decision_type=scenario_data.get('type', 'unknown')
        ).inc()
        
        return AgentDecision(**decision)
        
    except Exception as e:
        logger.error("Failed to get agent decision", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reasoning/explain/{decision_id}")
async def explain_decision_reasoning(decision_id: str):
    """Get detailed explanation of a decision's reasoning"""
    
    try:
        explanation = await reasoning_engine.explain_decision(decision_id)
        if not explanation:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        return explanation
        
    except Exception as e:
        logger.error("Failed to explain decision", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/conflicts/resolve")
async def resolve_agent_conflicts(
    conflicts: List[Dict[str, Any]]
):
    """Resolve conflicts between agent decisions"""
    
    try:
        resolution = await multi_agent_coordinator.resolve_conflicts(conflicts)
        
        AGENT_CONFLICTS.labels(
            conflict_type=resolution.get('conflict_type', 'unknown')
        ).inc()
        
        return resolution
        
    except Exception as e:
        logger.error("Failed to resolve conflicts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/performance")
async def get_agent_performance_analytics():
    """Get agent performance analytics"""
    
    try:
        analytics = await agent_system.get_performance_analytics()
        return analytics
        
    except Exception as e:
        logger.error("Failed to get performance analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/learning/insights")
async def get_learning_insights():
    """Get AI learning insights and improvements"""
    
    try:
        insights = await agent_system.get_learning_insights()
        return insights
        
    except Exception as e:
        logger.error("Failed to get learning insights", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/training/feedback")
async def submit_training_feedback(
    decision_id: str,
    feedback_data: Dict[str, Any]
):
    """Submit feedback for agent training"""
    
    try:
        result = await agent_system.submit_training_feedback(
            decision_id=decision_id,
            feedback_data=feedback_data
        )
        
        return {"message": "Feedback submitted successfully", "result": result}
        
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/simulation/run")
async def run_disruption_simulation(
    simulation_config: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Run comprehensive disruption simulation"""
    
    try:
        simulation_id = str(uuid4())
        
        result = await agent_system.run_simulation(
            simulation_id=simulation_id,
            config=simulation_config
        )
        
        # Monitor simulation in background
        background_tasks.add_task(
            agent_system.monitor_simulation,
            simulation_id
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to run simulation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006, workers=1)