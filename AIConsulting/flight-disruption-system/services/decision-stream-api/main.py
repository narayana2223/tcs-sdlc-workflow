"""
Real-Time Decision Stream API

This service provides real-time streaming of agent decisions with WebSocket broadcasting
for transparent agentic intelligence demonstration across all interfaces.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog
from contextlib import asynccontextmanager

# Import our decision logging components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.agents.decision_logger import decision_logger
from shared.agents.reasoning_engine import reasoning_engine
from shared.models.decision_models import (
    AgentDecision, DecisionStream, AgentCollaboration,
    DecisionType, ReasoningStep, DataSourceType
)

# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "decisions": [],
            "collaborations": [],
            "analytics": [],
            "all": []
        }
        self.client_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, stream_type: str, client_id: str = None):
        await websocket.accept()
        
        if stream_type not in self.active_connections:
            stream_type = "all"
        
        self.active_connections[stream_type].append(websocket)
        self.active_connections["all"].append(websocket)
        
        self.client_info[websocket] = {
            "client_id": client_id or f"client_{id(websocket)}",
            "stream_type": stream_type,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info("WebSocket client connected",
                   client_id=self.client_info[websocket]["client_id"],
                   stream_type=stream_type,
                   total_connections=len(self.active_connections["all"]))
    
    def disconnect(self, websocket: WebSocket):
        client_info = self.client_info.get(websocket, {})
        client_id = client_info.get("client_id", "unknown")
        stream_type = client_info.get("stream_type", "all")
        
        # Remove from specific stream
        if websocket in self.active_connections.get(stream_type, []):
            self.active_connections[stream_type].remove(websocket)
        
        # Remove from all connections
        if websocket in self.active_connections["all"]:
            self.active_connections["all"].remove(websocket)
        
        # Clean up client info
        if websocket in self.client_info:
            del self.client_info[websocket]
        
        logger.info("WebSocket client disconnected",
                   client_id=client_id,
                   stream_type=stream_type,
                   total_connections=len(self.active_connections["all"]))
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast_to_stream(self, message: dict, stream_type: str = "all"):
        """Broadcast message to all clients subscribed to stream type"""
        connections = self.active_connections.get(stream_type, [])
        
        if not connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e))
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
        
        logger.debug("Message broadcast",
                    stream_type=stream_type,
                    recipients=len(connections) - len(disconnected),
                    disconnected=len(disconnected))
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections["all"]),
            "by_stream_type": {
                stream: len(connections) 
                for stream, connections in self.active_connections.items()
            },
            "client_details": [
                {
                    "client_id": info["client_id"],
                    "stream_type": info["stream_type"],
                    "connected_duration": (datetime.utcnow() - info["connected_at"]).total_seconds(),
                    "last_ping": info["last_ping"].isoformat()
                }
                for info in self.client_info.values()
            ]
        }


# Global connection manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    logger.info("Starting Decision Stream API service")
    
    # Subscribe to decision logger events
    decision_logger.subscribe_to_decisions(on_decision_event)
    decision_logger.subscribe_to_collaborations(on_collaboration_event)
    
    # Start background tasks
    background_tasks = [
        asyncio.create_task(heartbeat_task()),
        asyncio.create_task(analytics_task()),
        asyncio.create_task(demo_scenario_task())
    ]
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down Decision Stream API service")
        
        # Cancel background tasks
        for task in background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*background_tasks, return_exceptions=True)


# FastAPI app with lifespan
app = FastAPI(
    title="Decision Stream API",
    description="Real-time agent decision streaming service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3010"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class DecisionStreamRequest(BaseModel):
    agent_id: str
    agent_type: str
    decision_type: str
    triggering_event: str
    context: Optional[Dict[str, Any]] = None


class ScenarioTriggerRequest(BaseModel):
    scenario_type: str
    complexity: str = "medium"  # low, medium, high
    passenger_count: int = 50
    parameters: Optional[Dict[str, Any]] = None


# Event handlers
async def on_decision_event(event_type: str, decision_data: Dict[str, Any]):
    """Handle decision events from decision logger"""
    
    message = {
        "type": "decision_event",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": decision_data
    }
    
    await manager.broadcast_to_stream(message, "decisions")
    await manager.broadcast_to_stream(message, "all")


async def on_collaboration_event(event_type: str, collaboration_data: Dict[str, Any]):
    """Handle collaboration events from decision logger"""
    
    message = {
        "type": "collaboration_event",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": collaboration_data
    }
    
    await manager.broadcast_to_stream(message, "collaborations")
    await manager.broadcast_to_stream(message, "all")


# Background tasks
async def heartbeat_task():
    """Send periodic heartbeat to maintain connections"""
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat(),
            "server_status": "healthy",
            "active_connections": len(manager.active_connections["all"])
        }
        
        await manager.broadcast_to_stream(heartbeat_message, "all")


async def analytics_task():
    """Send periodic analytics updates"""
    while True:
        await asyncio.sleep(60)  # Every minute
        
        # Get system analytics
        analytics = decision_logger.get_system_analytics()
        
        analytics_message = {
            "type": "system_analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "data": analytics
        }
        
        await manager.broadcast_to_stream(analytics_message, "analytics")
        await manager.broadcast_to_stream(analytics_message, "all")


async def demo_scenario_task():
    """Generate demo scenarios for demonstration purposes"""
    while True:
        await asyncio.sleep(120)  # Every 2 minutes
        
        # Generate demo decision for demonstration
        if len(manager.active_connections["all"]) > 0:
            await generate_demo_decision()


# API endpoints
@app.get("/")
async def root():
    return {
        "service": "Decision Stream API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "websocket": "/ws/{stream_type}",
            "health": "/health",
            "analytics": "/analytics",
            "connections": "/connections",
            "trigger_scenario": "/trigger-scenario"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "decision-stream-api",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections["all"]),
        "decision_logger_status": "operational"
    }


@app.get("/analytics")
async def get_analytics():
    """Get current system analytics"""
    try:
        analytics = decision_logger.get_system_analytics()
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Error retrieving analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Error retrieving analytics")


@app.get("/connections")
async def get_connections():
    """Get connection statistics"""
    return await manager.get_connection_stats()


@app.get("/decisions/recent")
async def get_recent_decisions(limit: int = 20):
    """Get recent decisions"""
    try:
        decisions = decision_logger.get_recent_decisions(limit)
        return {
            "status": "success",
            "count": len(decisions),
            "decisions": [decision.to_display_format() for decision in decisions]
        }
    except Exception as e:
        logger.error("Error retrieving recent decisions", error=str(e))
        raise HTTPException(status_code=500, detail="Error retrieving decisions")


@app.post("/trigger-scenario")
async def trigger_scenario(request: ScenarioTriggerRequest):
    """Trigger a demo scenario for demonstration purposes"""
    try:
        await generate_scenario(
            request.scenario_type,
            request.complexity,
            request.passenger_count,
            request.parameters or {}
        )
        
        return {
            "status": "success",
            "message": f"Triggered {request.scenario_type} scenario",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Error triggering scenario", error=str(e))
        raise HTTPException(status_code=500, detail="Error triggering scenario")


# WebSocket endpoints
@app.websocket("/ws/{stream_type}")
async def websocket_endpoint(websocket: WebSocket, stream_type: str, client_id: Optional[str] = None):
    """WebSocket endpoint for real-time decision streaming"""
    
    await manager.connect(websocket, stream_type, client_id)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "stream_type": stream_type,
            "client_id": manager.client_info[websocket]["client_id"],
            "timestamp": datetime.utcnow().isoformat(),
            "available_streams": list(manager.active_connections.keys())
        }
        await manager.send_personal_message(welcome_message, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message from client
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                data = json.loads(message)
                
                # Handle client messages
                if data.get("type") == "ping":
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_personal_message(pong_message, websocket)
                    manager.client_info[websocket]["last_ping"] = datetime.utcnow()
                
                elif data.get("type") == "subscribe":
                    # Handle subscription changes
                    new_stream = data.get("stream_type", "all")
                    # Implementation for changing subscriptions
                    
                elif data.get("type") == "request_analytics":
                    # Send current analytics to specific client
                    analytics = decision_logger.get_system_analytics()
                    analytics_message = {
                        "type": "analytics_response",
                        "data": analytics,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.send_personal_message(analytics_message, websocket)
                    
            except asyncio.TimeoutError:
                # Send keep-alive ping
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(ping_message, websocket)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        manager.disconnect(websocket)


# Demo scenario generation
async def generate_demo_decision():
    """Generate a demo decision for demonstration purposes"""
    
    # Start a demo decision
    decision_id = await decision_logger.start_decision(
        agent_id="demo_prediction_agent",
        agent_type="prediction",
        decision_type=DecisionType.PREDICTION,
        triggering_event="Weather conditions detected at LHR - potential delays",
        context={
            "airport": "LHR",
            "scenario": "demo",
            "weather_condition": "fog",
            "affected_flights": 23
        }
    )
    
    # Simulate reasoning steps
    await asyncio.sleep(1)
    await decision_logger.add_reasoning_step(
        decision_id=decision_id,
        step=ReasoningStep.DATA_GATHERING,
        description="Collecting weather data and flight information",
        logic="Accessing Met Office API and flight tracking systems to assess situation",
        confidence_impact=0.2
    )
    
    await asyncio.sleep(0.5)
    await decision_logger.add_data_point(
        decision_id=decision_id,
        source=DataSourceType.WEATHER_API,
        key="visibility",
        value="800m",
        description="Current visibility at LHR runway 09L",
        confidence=0.95,
        relevance_score=0.9
    )
    
    await asyncio.sleep(0.5)
    await decision_logger.add_reasoning_step(
        decision_id=decision_id,
        step=ReasoningStep.ANALYSIS,
        description="Analyzing impact on flight operations",
        logic="Visibility below 1000m threshold requires enhanced approach procedures",
        confidence_impact=0.25
    )
    
    await asyncio.sleep(1)
    from shared.models.decision_models import DecisionAlternative, DecisionImpact
    
    alternative = DecisionAlternative(
        alternative_id="delay_flights",
        description="Implement 30-minute delays for affected flights",
        pros=["Safety maintained", "Orderly processing", "Minimal passenger disruption"],
        cons=["Schedule impact", "Connecting flight risks"],
        estimated_cost=45000.0,
        estimated_time=180.0,
        passenger_satisfaction_impact=0.7,
        why_not_chosen="Selected as optimal balance of safety and efficiency"
    )
    
    await decision_logger.add_alternative(decision_id, alternative)
    
    # Complete decision
    impact = DecisionImpact(
        passengers_affected=180,
        cost_impact=45000.0,
        time_impact=30.0,
        satisfaction_impact=0.7,
        regulatory_compliance=True,
        cascading_effects=["Connected flight delays", "Ground handling adjustments"],
        risk_assessment={"operational": 0.2, "financial": 0.1, "reputational": 0.15}
    )
    
    await decision_logger.complete_decision(
        decision_id=decision_id,
        final_decision="Implement controlled 30-minute delays for 23 affected flights",
        detailed_explanation="Based on current weather conditions and safety requirements, implementing strategic delays to maintain safety while minimizing passenger impact",
        expected_impact=impact,
        constraints=["CAA safety regulations", "Airport slot availability"],
        assumptions=["Weather will improve within 2 hours", "No further deterioration expected"]
    )


async def generate_scenario(scenario_type: str, complexity: str, passenger_count: int, parameters: Dict[str, Any]):
    """Generate complex scenarios with multiple agents and decisions"""
    
    scenario_generators = {
        "weather_disruption": generate_weather_scenario,
        "aircraft_maintenance": generate_maintenance_scenario,
        "crew_shortage": generate_crew_scenario,
        "cascade_delay": generate_cascade_scenario
    }
    
    generator = scenario_generators.get(scenario_type, generate_demo_decision)
    await generator(complexity, passenger_count, parameters)


async def generate_weather_scenario(complexity: str, passenger_count: int, parameters: Dict[str, Any]):
    """Generate weather disruption scenario with multiple agent decisions"""
    
    # Multiple agents making decisions
    agents = [
        ("prediction_agent_1", "prediction"),
        ("passenger_agent_1", "passenger"),
        ("resource_agent_1", "resource"),
        ("communication_agent_1", "communication")
    ]
    
    decision_ids = []
    
    for agent_id, agent_type in agents:
        decision_id = await decision_logger.start_decision(
            agent_id=agent_id,
            agent_type=agent_type,
            decision_type=DecisionType.PREDICTION if agent_type == "prediction" else DecisionType.PASSENGER_REBOOKING,
            triggering_event="Major weather system approaching - multiple airports affected",
            context={
                "scenario": "weather_disruption",
                "complexity": complexity,
                "affected_airports": ["LHR", "LGW", "STN"],
                "passenger_count": passenger_count
            }
        )
        decision_ids.append(decision_id)
        
        # Simulate different reasoning for each agent
        await simulate_agent_reasoning(decision_id, agent_type, complexity)
    
    # Simulate collaboration between agents
    collab_id = await decision_logger.start_collaboration(
        agent_ids=[f"{agent[0]}" for agent in agents],
        collaboration_type="weather_response_coordination",
        initial_conflict="Conflicting priorities between cost optimization and passenger satisfaction"
    )
    
    await asyncio.sleep(2)
    await decision_logger.add_negotiation_step(
        collab_id,
        "Agents sharing weather data and passenger impact assessments"
    )
    
    await asyncio.sleep(1)
    await decision_logger.add_negotiation_step(
        collab_id,
        "Consensus building on priority passenger rebooking strategy"
    )
    
    await decision_logger.complete_collaboration(
        collab_id,
        "Agreed on balanced approach prioritizing safety while minimizing costs",
        True
    )


async def simulate_agent_reasoning(decision_id: str, agent_type: str, complexity: str):
    """Simulate agent reasoning process based on agent type"""
    
    if agent_type == "prediction":
        await decision_logger.add_data_point(
            decision_id, DataSourceType.WEATHER_API, "wind_speed", "32 knots",
            "Wind speed exceeding operational limits", 0.92, 0.95
        )
        await decision_logger.add_data_point(
            decision_id, DataSourceType.FLIGHT_DATA, "affected_flights", "47 flights",
            "Flights requiring attention", 0.98, 0.9
        )
    
    elif agent_type == "passenger":
        await decision_logger.add_data_point(
            decision_id, DataSourceType.PASSENGER_PROFILE, "priority_passengers", "23 business class",
            "High-value passengers requiring priority rebooking", 0.95, 0.8
        )
    
    # Add reasoning steps based on complexity
    steps_count = {"low": 2, "medium": 4, "high": 6}[complexity]
    
    for i in range(steps_count):
        await asyncio.sleep(0.3)
        await decision_logger.add_reasoning_step(
            decision_id,
            [ReasoningStep.DATA_GATHERING, ReasoningStep.ANALYSIS, ReasoningStep.EVALUATION][i % 3],
            f"Step {i+1}: Processing {agent_type} specific requirements",
            f"Applying {agent_type} logic to current situation",
            confidence_impact=0.1 + (i * 0.05)
        )


async def generate_maintenance_scenario(complexity: str, passenger_count: int, parameters: Dict[str, Any]):
    """Generate aircraft maintenance scenario"""
    # Implementation for maintenance scenarios
    await generate_demo_decision()  # Placeholder


async def generate_crew_scenario(complexity: str, passenger_count: int, parameters: Dict[str, Any]):
    """Generate crew shortage scenario"""
    # Implementation for crew scenarios
    await generate_demo_decision()  # Placeholder


async def generate_cascade_scenario(complexity: str, passenger_count: int, parameters: Dict[str, Any]):
    """Generate cascade delay scenario affecting multiple flights"""
    # Implementation for cascade scenarios
    await generate_demo_decision()  # Placeholder


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        log_level="info",
        reload=True
    )