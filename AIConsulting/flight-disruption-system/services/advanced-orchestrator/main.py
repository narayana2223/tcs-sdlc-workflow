"""
Advanced Agent Orchestrator Service - Phase 2.2
Production-ready FastAPI service for multi-agent coordination and orchestration

This service provides:
- RESTful API for multi-agent coordination requests
- Real-time conflict resolution and consensus building
- Advanced orchestration with dependency management
- Performance monitoring and analytics
- WebSocket support for real-time updates
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import asyncio
import uuid

# Import the multi-agent coordinator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from agents.multi_agent_coordinator import MultiAgentCoordinator, CoordinationPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Agent Orchestrator",
    description="Multi-agent coordination and orchestration service for flight disruptions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the multi-agent coordinator
coordinator = MultiAgentCoordinator()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models for API requests/responses
class DisruptionRequest(BaseModel):
    disruption_id: str = Field(..., description="Unique identifier for the disruption")
    type: str = Field(..., description="Type of disruption (weather, technical, atc, etc.)")
    severity: str = Field(..., description="Severity level (low, moderate, high, severe)")
    affected_flights: List[Dict[str, Any]] = Field(..., description="List of affected flights")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class CoordinationResponse(BaseModel):
    coordination_id: str = Field(..., description="Unique coordination session ID")
    request_id: str = Field(..., description="Original request ID")
    status: str = Field(..., description="Coordination status")
    task_plan: Dict[str, Any] = Field(..., description="Generated task plan")
    orchestration_results: Dict[str, Any] = Field(..., description="Agent orchestration results")
    consensus_decision: Dict[str, Any] = Field(..., description="Final consensus decision")
    confidence_score: float = Field(..., description="Overall confidence in coordination")
    estimated_completion: str = Field(..., description="Estimated completion time")

class AgentStatusResponse(BaseModel):
    coordinator_status: Dict[str, Any]
    individual_agent_status: Dict[str, Dict[str, Any]]
    active_coordinations: int
    performance_metrics: Dict[str, Any]

class CoordinationHistoryItem(BaseModel):
    coordination_id: str
    timestamp: datetime
    disruption_type: str
    agents_involved: List[str]
    success: bool
    confidence_score: float
    execution_time: str

# In-memory storage for coordination sessions and history
coordination_sessions: Dict[str, Dict[str, Any]] = {}
coordination_history: List[CoordinationHistoryItem] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "advanced-agent-orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "coordinator_status": "active",
        "agents_available": len(coordinator.agents)
    }

@app.get("/status", response_model=AgentStatusResponse)
async def get_system_status():
    """Get comprehensive system status including all agents"""
    try:
        coordinator_status = await coordinator.get_agent_status()
        
        # Get individual agent statuses
        individual_statuses = {}
        for agent_name, agent in coordinator.agents.items():
            individual_statuses[agent_name] = await agent.get_agent_status()
        
        performance_metrics = {
            "active_coordinations": len(coordination_sessions),
            "total_coordinations_completed": len(coordination_history),
            "average_coordination_success_rate": calculate_success_rate(),
            "system_uptime": "operational",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return AgentStatusResponse(
            coordinator_status=coordinator_status,
            individual_agent_status=individual_statuses,
            active_coordinations=len(coordination_sessions),
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.post("/coordinate", response_model=CoordinationResponse)
async def coordinate_disruption_response(
    request: DisruptionRequest,
    background_tasks: BackgroundTasks
):
    """Coordinate multi-agent response to flight disruption"""
    try:
        coordination_id = str(uuid.uuid4())
        
        logger.info(f"Starting coordination {coordination_id} for disruption {request.disruption_id}")
        
        # Prepare disruption data for coordinator
        disruption_data = {
            "disruption_id": request.disruption_id,
            "type": request.type,
            "severity": request.severity,
            "affected_flights": request.affected_flights,
            "additional_context": request.additional_context or {}
        }
        
        # Execute coordination
        coordination_result = await coordinator.handle_disruption_request(disruption_data)
        
        # Store coordination session
        coordination_sessions[coordination_id] = {
            "coordination_id": coordination_id,
            "request": request.dict(),
            "result": coordination_result,
            "status": "completed" if coordination_result.get("overall_confidence", 0) > 0.5 else "partial",
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow()
        }
        
        # Add to history
        history_item = CoordinationHistoryItem(
            coordination_id=coordination_id,
            timestamp=datetime.utcnow(),
            disruption_type=request.type,
            agents_involved=list(coordinator.agents.keys()),
            success=coordination_result.get("overall_confidence", 0) > 0.5,
            confidence_score=coordination_result.get("overall_confidence", 0),
            execution_time=f"{len(coordination_result.get('orchestration_results', {}))} phases"
        )
        coordination_history.append(history_item)
        
        # Broadcast update to WebSocket connections
        background_tasks.add_task(
            broadcast_coordination_update,
            coordination_id,
            "completed",
            coordination_result
        )
        
        # Build response
        response = CoordinationResponse(
            coordination_id=coordination_id,
            request_id=request.disruption_id,
            status=coordination_sessions[coordination_id]["status"],
            task_plan=coordination_result.get("task_plan", {}),
            orchestration_results=coordination_result.get("orchestration_results", {}),
            consensus_decision=coordination_result.get("consensus_decision", {}),
            confidence_score=coordination_result.get("overall_confidence", 0.0),
            estimated_completion=extract_estimated_completion(coordination_result)
        )
        
        logger.info(f"Coordination {coordination_id} completed with confidence {response.confidence_score}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error coordinating disruption response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Coordination failed: {str(e)}")

@app.get("/coordination/{coordination_id}")
async def get_coordination_details(coordination_id: str):
    """Get details of a specific coordination session"""
    if coordination_id not in coordination_sessions:
        raise HTTPException(status_code=404, detail="Coordination session not found")
    
    session = coordination_sessions[coordination_id]
    
    return {
        "coordination_id": coordination_id,
        "status": session["status"],
        "created_at": session["created_at"].isoformat(),
        "completed_at": session.get("completed_at", datetime.utcnow()).isoformat(),
        "request_details": session["request"],
        "coordination_results": session["result"],
        "performance_metrics": extract_performance_metrics(session["result"])
    }

@app.get("/coordination-history")
async def get_coordination_history(limit: int = 50):
    """Get coordination history"""
    recent_history = sorted(
        coordination_history, 
        key=lambda x: x.timestamp, 
        reverse=True
    )[:limit]
    
    return {
        "total_coordinations": len(coordination_history),
        "recent_coordinations": [item.dict() for item in recent_history],
        "success_rate": calculate_success_rate(),
        "average_confidence": calculate_average_confidence()
    }

@app.post("/test-coordination")
async def test_coordination():
    """Test coordination with sample disruption data"""
    sample_disruption = DisruptionRequest(
        disruption_id="TEST_" + str(uuid.uuid4())[:8],
        type="weather",
        severity="moderate",
        affected_flights=[
            {
                "flight_id": "BA123",
                "departure_time": (datetime.utcnow() + datetime.timedelta(hours=2)).isoformat() + "Z",
                "departure_airport": "LHR",
                "arrival_airport": "CDG",
                "aircraft_type": "A320",
                "passenger_count": 150
            },
            {
                "flight_id": "BA456",
                "departure_time": (datetime.utcnow() + datetime.timedelta(hours=3)).isoformat() + "Z",
                "departure_airport": "LHR",
                "arrival_airport": "AMS",
                "aircraft_type": "A330",
                "passenger_count": 280
            }
        ],
        additional_context={
            "weather_conditions": "thunderstorms",
            "expected_duration": "2-4 hours",
            "airports_affected": ["LHR"]
        }
    )
    
    return await coordinate_disruption_response(sample_disruption, BackgroundTasks())

@app.websocket("/ws/coordination-updates")
async def coordination_updates_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time coordination updates"""
    await manager.connect(websocket)
    
    # Send initial status
    try:
        initial_status = {
            "type": "connection_established",
            "message": "Connected to coordination updates",
            "active_coordinations": len(coordination_sessions),
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_text(json.dumps(initial_status))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back or handle commands if needed
                await websocket.send_text(f"Received: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        manager.disconnect(websocket)

@app.get("/agents/{agent_name}/status")
async def get_individual_agent_status(agent_name: str):
    """Get status of a specific agent"""
    if agent_name not in coordinator.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    agent = coordinator.agents[agent_name]
    status = await agent.get_agent_status()
    
    return {
        "agent_name": agent_name,
        "status": status,
        "coordinator_view": coordinator.agent_status.get(agent_name, "unknown").value if agent_name in coordinator.agent_status else "unknown",
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/agents/test/{agent_name}")
async def test_individual_agent(agent_name: str):
    """Test an individual agent with sample data"""
    if agent_name not in coordinator.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    # Sample test data
    test_disruption = {
        "type": "weather",
        "severity": "moderate",
        "affected_flights": [
            {
                "flight_id": f"TEST_{agent_name.upper()}",
                "departure_time": (datetime.utcnow() + datetime.timedelta(hours=2)).isoformat() + "Z",
                "departure_airport": "LHR",
                "arrival_airport": "CDG",
                "aircraft_type": "A320",
                "passenger_count": 150
            }
        ]
    }
    
    agent = coordinator.agents[agent_name]
    result = await agent.handle_disruption_request(test_disruption)
    
    return {
        "agent_name": agent_name,
        "test_result": result,
        "test_timestamp": datetime.utcnow().isoformat(),
        "success": "error" not in result
    }

# Utility functions
def calculate_success_rate() -> float:
    """Calculate overall coordination success rate"""
    if not coordination_history:
        return 0.0
    
    successful = sum(1 for item in coordination_history if item.success)
    return round(successful / len(coordination_history) * 100, 1)

def calculate_average_confidence() -> float:
    """Calculate average confidence score"""
    if not coordination_history:
        return 0.0
    
    total_confidence = sum(item.confidence_score for item in coordination_history)
    return round(total_confidence / len(coordination_history), 2)

def extract_estimated_completion(coordination_result: Dict[str, Any]) -> str:
    """Extract estimated completion time from coordination result"""
    consensus_decision = coordination_result.get("consensus_decision", {})
    integrated_decision = consensus_decision.get("integrated_decision", {})
    timeline = integrated_decision.get("timeline", {})
    
    return timeline.get("estimated_completion", "2-4 hours")

def extract_performance_metrics(coordination_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract performance metrics from coordination result"""
    metrics = coordination_result.get("coordination_metrics", {})
    
    return {
        "coordination_success_rate": metrics.get("coordination_success_rate", 0),
        "total_agents_coordinated": metrics.get("total_agents_coordinated", 0),
        "successful_executions": metrics.get("successful_agent_executions", 0),
        "conflicts_resolved": coordination_result.get("conflict_resolution", {}).get("conflicts_resolved", 0),
        "confidence_score": coordination_result.get("overall_confidence", 0.0)
    }

async def broadcast_coordination_update(
    coordination_id: str, 
    status: str, 
    coordination_result: Dict[str, Any]
):
    """Broadcast coordination update to WebSocket connections"""
    try:
        update = {
            "type": "coordination_update",
            "coordination_id": coordination_id,
            "status": status,
            "confidence_score": coordination_result.get("overall_confidence", 0.0),
            "agents_involved": len(coordination_result.get("orchestration_results", {})),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast(json.dumps(update))
    except Exception as e:
        logger.error(f"Error broadcasting update: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")