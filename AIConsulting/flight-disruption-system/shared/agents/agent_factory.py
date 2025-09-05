"""
Agent Factory for Flight Disruption Management System

This module provides a factory for creating and managing AI agents,
including initialization, configuration, and lifecycle management.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import structlog

from langchain_openai import ChatOpenAI

from .base_agent import BaseAgent, AgentType, SharedMemory, PerformanceMonitor
from .prediction_agent import PredictionAgent
from .passenger_agent import PassengerAgent
from .resource_agent import ResourceAgent
from .communication_agent import CommunicationAgent
from .coordinator_agent import CoordinatorAgent
from .orchestrator import AgentOrchestrator, TaskType, TaskPriority

logger = structlog.get_logger()


class AgentConfiguration:
    """Configuration class for agent initialization"""
    
    def __init__(self,
                 openai_api_key: str,
                 model_name: str = "gpt-4",
                 temperature: float = 0.1,
                 max_tokens: int = 2000,
                 request_timeout: int = 30):
        
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_timeout = request_timeout
    
    def create_llm(self) -> ChatOpenAI:
        """Create configured LLM instance"""
        return ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            request_timeout=self.request_timeout
        )


class AgentFactory:
    """Factory for creating and managing AI agents"""
    
    def __init__(self, configuration: AgentConfiguration):
        self.configuration = configuration
        self.shared_memory = SharedMemory()
        self.performance_monitor = PerformanceMonitor()
        
        # Registry of agent classes
        self.agent_classes: Dict[AgentType, Type[BaseAgent]] = {
            AgentType.PREDICTION: PredictionAgent,
            AgentType.PASSENGER: PassengerAgent,
            AgentType.RESOURCE: ResourceAgent,
            AgentType.COMMUNICATION: CommunicationAgent,
            AgentType.COORDINATOR: CoordinatorAgent
        }
        
        # Active agent instances
        self.agents: Dict[str, BaseAgent] = {}
        
        # Orchestrator instance
        self.orchestrator: Optional[AgentOrchestrator] = None
        
        self.logger = structlog.get_logger().bind(component="agent_factory")
    
    def create_agent(self, 
                    agent_type: AgentType, 
                    agent_id: Optional[str] = None,
                    **kwargs) -> BaseAgent:
        """Create a new agent instance"""
        
        if agent_id is None:
            agent_id = f"{agent_type.value}_{str(uuid.uuid4())[:8]}"
        
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID {agent_id} already exists")
        
        agent_class = self.agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create LLM instance
        llm = self.configuration.create_llm()
        
        # Create agent instance
        agent = agent_class(
            agent_id=agent_id,
            llm=llm,
            shared_memory=self.shared_memory,
            performance_monitor=self.performance_monitor,
            **kwargs
        )
        
        # Register agent
        self.agents[agent_id] = agent
        
        self.logger.info("Agent created successfully",
                        agent_type=agent_type.value,
                        agent_id=agent_id)
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() 
                if agent.agent_type == agent_type]
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from factory"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info("Agent removed", agent_id=agent_id)
            return True
        return False
    
    def create_standard_agent_set(self) -> Dict[AgentType, BaseAgent]:
        """Create standard set of agents for flight disruption management"""
        
        standard_agents = {}
        
        # Create one agent of each type
        for agent_type in AgentType:
            agent = self.create_agent(agent_type)
            standard_agents[agent_type] = agent
        
        self.logger.info("Standard agent set created",
                        agent_count=len(standard_agents))
        
        return standard_agents
    
    def create_orchestrator(self) -> AgentOrchestrator:
        """Create orchestrator with registered agents"""
        
        if self.orchestrator is None:
            self.orchestrator = AgentOrchestrator(
                llm=self.configuration.create_llm(),
                shared_memory=self.shared_memory,
                performance_monitor=self.performance_monitor
            )
            
            # Register all existing agents with orchestrator
            for agent in self.agents.values():
                self.orchestrator.register_agent(agent)
        
        return self.orchestrator
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agent_status = {}
        for agent_id, agent in self.agents.items():
            agent_status[agent_id] = {
                "type": agent.agent_type.value,
                "status": agent.status.value,
                "created_at": getattr(agent, 'created_at', None)
            }
        
        return {
            "total_agents": len(self.agents),
            "agents_by_type": {
                agent_type.value: len(self.get_agents_by_type(agent_type))
                for agent_type in AgentType
            },
            "agent_status": agent_status,
            "orchestrator_active": self.orchestrator is not None,
            "shared_memory_items": len(self.shared_memory._memory),
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents"""
        health_status = {
            "overall_health": "healthy",
            "agent_health": {},
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check each agent
        for agent_id, agent in self.agents.items():
            try:
                # Basic connectivity test - get agent state
                agent_state = await self.shared_memory.get_agent_state(agent_id)
                
                # Get recent performance
                performance = await self.performance_monitor.get_performance_summary(
                    agent_id,
                    since=datetime.now() - timedelta(hours=1)
                )
                
                agent_healthy = True
                issues = []
                
                # Check performance thresholds
                if performance:
                    if performance.get("success_rate", 1.0) < 0.8:
                        agent_healthy = False
                        issues.append("Low success rate")
                    
                    if performance.get("avg_duration_ms", 0) > 10000:
                        agent_healthy = False
                        issues.append("High response time")
                
                health_status["agent_health"][agent_id] = {
                    "healthy": agent_healthy,
                    "status": agent.status.value,
                    "performance": performance,
                    "issues": issues
                }
                
                if not agent_healthy:
                    health_status["issues"].extend([f"{agent_id}: {issue}" for issue in issues])
                
            except Exception as e:
                health_status["agent_health"][agent_id] = {
                    "healthy": False,
                    "error": str(e),
                    "issues": ["Health check failed"]
                }
                health_status["issues"].append(f"{agent_id}: Health check failed - {str(e)}")
        
        # Overall health assessment
        unhealthy_agents = [
            agent_id for agent_id, health in health_status["agent_health"].items()
            if not health.get("healthy", False)
        ]
        
        if len(unhealthy_agents) > len(self.agents) * 0.5:
            health_status["overall_health"] = "critical"
        elif len(unhealthy_agents) > 0:
            health_status["overall_health"] = "degraded"
        
        return health_status


class AgentManager:
    """High-level manager for the entire agent system"""
    
    def __init__(self, configuration: AgentConfiguration):
        self.factory = AgentFactory(configuration)
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.logger = structlog.get_logger().bind(component="agent_manager")
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the complete agent system"""
        
        self.logger.info("Initializing agent system")
        
        try:
            # Create standard agent set
            self.agents = self.factory.create_standard_agent_set()
            
            # Create and configure orchestrator
            self.orchestrator = self.factory.create_orchestrator()
            
            # Initialize shared memory with system metadata
            await self.factory.shared_memory.store(
                "system_metadata",
                {
                    "initialized_at": datetime.now().isoformat(),
                    "agent_count": len(self.agents),
                    "version": "1.0.0",
                    "status": "operational"
                }
            )
            
            # Perform initial health check
            health_check = await self.factory.health_check()
            
            self.logger.info("Agent system initialized successfully",
                           agent_count=len(self.agents),
                           health_status=health_check["overall_health"])
            
            return {
                "status": "initialized",
                "agents_created": len(self.agents),
                "orchestrator_ready": self.orchestrator is not None,
                "health_check": health_check,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("System initialization failed", error=str(e))
            raise
    
    async def handle_disruption(self, 
                              disruption_context: Dict[str, Any],
                              priority: TaskPriority = TaskPriority.NORMAL) -> Dict[str, Any]:
        """Handle flight disruption using the agent system"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        self.logger.info("Handling flight disruption",
                        disruption_type=disruption_context.get("type", "unknown"),
                        priority=priority.value)
        
        try:
            # Execute disruption response workflow
            result = await self.orchestrator.execute_task(
                task_type=TaskType.DISRUPTION_RESPONSE,
                context=disruption_context,
                priority=priority
            )
            
            self.logger.info("Disruption handled successfully",
                           task_id=result.get("task_id"),
                           execution_time=result.get("execution_time"),
                           agents_involved=len(result.get("agents_involved", [])))
            
            return result
            
        except Exception as e:
            self.logger.error("Disruption handling failed", error=str(e))
            raise
    
    async def process_passenger_rebooking(self,
                                        passenger_context: Dict[str, Any],
                                        priority: TaskPriority = TaskPriority.HIGH) -> Dict[str, Any]:
        """Process passenger rebooking workflow"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        return await self.orchestrator.execute_task(
            task_type=TaskType.PASSENGER_REBOOKING,
            context=passenger_context,
            priority=priority
        )
    
    async def optimize_costs(self,
                           cost_context: Dict[str, Any],
                           priority: TaskPriority = TaskPriority.NORMAL) -> Dict[str, Any]:
        """Execute cost optimization workflow"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        return await self.orchestrator.execute_task(
            task_type=TaskType.COST_OPTIMIZATION,
            context=cost_context,
            priority=priority
        )
    
    async def send_communications(self,
                                communication_context: Dict[str, Any],
                                priority: TaskPriority = TaskPriority.HIGH) -> Dict[str, Any]:
        """Execute communication campaign workflow"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        return await self.orchestrator.execute_task(
            task_type=TaskType.COMMUNICATION_CAMPAIGN,
            context=communication_context,
            priority=priority
        )
    
    async def get_predictions(self,
                            prediction_context: Dict[str, Any],
                            priority: TaskPriority = TaskPriority.NORMAL) -> Dict[str, Any]:
        """Execute predictive analysis workflow"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        return await self.orchestrator.execute_task(
            task_type=TaskType.PREDICTIVE_ANALYSIS,
            context=prediction_context,
            priority=priority
        )
    
    async def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        
        if not self.orchestrator:
            raise RuntimeError("Agent system not initialized")
        
        # Get factory status
        factory_status = self.factory.get_system_status()
        
        # Get orchestrator performance
        orchestrator_performance = await self.orchestrator.get_agent_performance_summary()
        
        # Get health check
        health_check = await self.factory.health_check()
        
        return {
            "system_status": factory_status,
            "agent_performance": orchestrator_performance,
            "health_check": health_check,
            "timestamp": datetime.now().isoformat()
        }
    
    def shutdown(self):
        """Shutdown the agent system"""
        self.logger.info("Shutting down agent system")
        
        # Clear agents
        self.agents.clear()
        self.orchestrator = None
        
        # Clear factory
        self.factory.agents.clear()
        self.factory.orchestrator = None
        
        self.logger.info("Agent system shutdown complete")