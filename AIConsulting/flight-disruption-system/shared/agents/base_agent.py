"""
Base Agent Framework for Flight Disruption Management System

This module provides the foundation for all AI agents in the system,
including shared memory management, decision tracking, and performance monitoring.
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict
import structlog
from pydantic import BaseModel, Field

from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

logger = structlog.get_logger()


class AgentType(Enum):
    """Agent types in the system"""
    PREDICTION = "prediction"
    PASSENGER = "passenger" 
    RESOURCE = "resource"
    COMMUNICATION = "communication"
    COORDINATOR = "coordinator"


class DecisionConfidence(Enum):
    """Decision confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentDecision:
    """Represents a decision made by an agent"""
    decision_id: str
    agent_id: str
    agent_type: AgentType
    timestamp: datetime
    decision_type: str
    context: Dict[str, Any]
    reasoning: str
    confidence: DecisionConfidence
    estimated_cost: float
    estimated_benefit: float
    alternatives_considered: List[Dict[str, Any]]
    tools_used: List[str]
    execution_time_ms: float
    outcome: Optional[str] = None
    actual_cost: Optional[float] = None
    actual_benefit: Optional[float] = None
    feedback_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDecision":
        """Create decision from dictionary"""
        data['agent_type'] = AgentType(data['agent_type'])
        data['confidence'] = DecisionConfidence(data['confidence'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class SharedMemory:
    """Shared memory system for all agents"""
    
    def __init__(self):
        self._memory: Dict[str, Any] = {}
        self._decisions: List[AgentDecision] = []
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        self._context_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store data in shared memory with optional TTL"""
        async with self._lock:
            self._memory[key] = {
                'value': value,
                'timestamp': datetime.now(),
                'ttl': ttl
            }
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from shared memory"""
        async with self._lock:
            if key not in self._memory:
                return None
            
            item = self._memory[key]
            if item['ttl'] and (datetime.now() - item['timestamp']).seconds > item['ttl']:
                del self._memory[key]
                return None
            
            return item['value']
    
    async def store_decision(self, decision: AgentDecision) -> None:
        """Store agent decision"""
        async with self._lock:
            self._decisions.append(decision)
            # Keep only last 1000 decisions to prevent memory bloat
            if len(self._decisions) > 1000:
                self._decisions = self._decisions[-1000:]
    
    async def get_decisions(self, 
                          agent_type: Optional[AgentType] = None,
                          since: Optional[datetime] = None,
                          limit: int = 100) -> List[AgentDecision]:
        """Get agent decisions with filtering"""
        async with self._lock:
            decisions = self._decisions
            
            if agent_type:
                decisions = [d for d in decisions if d.agent_type == agent_type]
            
            if since:
                decisions = [d for d in decisions if d.timestamp >= since]
            
            return decisions[-limit:]
    
    async def update_agent_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """Update agent state"""
        async with self._lock:
            self._agent_states[agent_id] = {
                **state,
                'last_updated': datetime.now()
            }
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state"""
        async with self._lock:
            return self._agent_states.get(agent_id)
    
    async def add_context(self, context: Dict[str, Any]) -> None:
        """Add context to history"""
        async with self._lock:
            self._context_history.append({
                **context,
                'timestamp': datetime.now()
            })
            # Keep only last 500 context items
            if len(self._context_history) > 500:
                self._context_history = self._context_history[-500:]
    
    async def get_context_history(self, 
                                since: Optional[datetime] = None,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """Get context history"""
        async with self._lock:
            history = self._context_history
            
            if since:
                history = [h for h in history if h['timestamp'] >= since]
            
            return history[-limit:]


class PerformanceMonitor:
    """Performance monitoring for agents"""
    
    def __init__(self):
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
    
    async def record_execution(self, 
                             agent_id: str,
                             action: str,
                             duration_ms: float,
                             success: bool,
                             metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record agent execution metrics"""
        async with self._lock:
            if agent_id not in self._metrics:
                self._metrics[agent_id] = []
            
            self._metrics[agent_id].append({
                'action': action,
                'duration_ms': duration_ms,
                'success': success,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            })
            
            # Keep only last 1000 metrics per agent
            if len(self._metrics[agent_id]) > 1000:
                self._metrics[agent_id] = self._metrics[agent_id][-1000:]
    
    async def get_performance_summary(self, 
                                    agent_id: str,
                                    since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get performance summary for agent"""
        async with self._lock:
            if agent_id not in self._metrics:
                return {}
            
            metrics = self._metrics[agent_id]
            if since:
                metrics = [m for m in metrics if m['timestamp'] >= since]
            
            if not metrics:
                return {}
            
            total_executions = len(metrics)
            successful_executions = len([m for m in metrics if m['success']])
            avg_duration = sum(m['duration_ms'] for m in metrics) / total_executions
            
            return {
                'total_executions': total_executions,
                'success_rate': successful_executions / total_executions,
                'avg_duration_ms': avg_duration,
                'min_duration_ms': min(m['duration_ms'] for m in metrics),
                'max_duration_ms': max(m['duration_ms'] for m in metrics),
                'recent_errors': [m for m in metrics[-10:] if not m['success']]
            }


class BaseAgent(ABC):
    """Base class for all AI agents in the system"""
    
    def __init__(self,
                 agent_id: str,
                 agent_type: AgentType,
                 llm: ChatOpenAI,
                 shared_memory: SharedMemory,
                 performance_monitor: PerformanceMonitor,
                 tools: Optional[List[BaseTool]] = None,
                 max_memory_window: int = 20):
        
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm = llm
        self.shared_memory = shared_memory
        self.performance_monitor = performance_monitor
        self.tools = tools or []
        self.status = AgentStatus.IDLE
        
        # Initialize agent memory
        self.memory = ConversationBufferWindowMemory(
            k=max_memory_window,
            return_messages=True
        )
        
        # Tool executor
        self.tool_executor = ToolExecutor(self.tools)
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type=agent_type.value
        )
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task - must be implemented by each agent"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    async def make_decision(self,
                          context: Dict[str, Any],
                          decision_type: str,
                          alternatives: List[Dict[str, Any]]) -> AgentDecision:
        """Make a decision with full audit trail"""
        start_time = datetime.now()
        decision_id = str(uuid.uuid4())
        
        try:
            self.status = AgentStatus.PROCESSING
            await self.shared_memory.update_agent_state(self.agent_id, {
                'status': self.status.value,
                'current_task': decision_type
            })
            
            # Create enhanced prompt with context and alternatives
            prompt = self._create_decision_prompt(context, decision_type, alternatives)
            
            # Get AI reasoning
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ])
            
            # Parse response to extract decision details
            decision_details = self._parse_decision_response(response.content)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create decision record
            decision = AgentDecision(
                decision_id=decision_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                timestamp=start_time,
                decision_type=decision_type,
                context=context,
                reasoning=decision_details['reasoning'],
                confidence=DecisionConfidence(decision_details['confidence']),
                estimated_cost=decision_details['estimated_cost'],
                estimated_benefit=decision_details['estimated_benefit'],
                alternatives_considered=alternatives,
                tools_used=decision_details.get('tools_used', []),
                execution_time_ms=execution_time
            )
            
            # Store decision in shared memory
            await self.shared_memory.store_decision(decision)
            
            # Record performance metrics
            await self.performance_monitor.record_execution(
                self.agent_id,
                f"decision_{decision_type}",
                execution_time,
                True,
                {'decision_id': decision_id, 'confidence': decision_details['confidence']}
            )
            
            self.status = AgentStatus.IDLE
            await self.shared_memory.update_agent_state(self.agent_id, {
                'status': self.status.value,
                'last_decision': decision_id
            })
            
            self.logger.info("Decision made successfully", 
                           decision_id=decision_id,
                           decision_type=decision_type,
                           confidence=decision_details['confidence'])
            
            return decision
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            await self.performance_monitor.record_execution(
                self.agent_id,
                f"decision_{decision_type}",
                execution_time,
                False,
                {'error': str(e)}
            )
            
            self.logger.error("Decision making failed",
                            decision_type=decision_type,
                            error=str(e))
            raise
    
    def _create_decision_prompt(self,
                              context: Dict[str, Any],
                              decision_type: str,
                              alternatives: List[Dict[str, Any]]) -> str:
        """Create structured prompt for decision making"""
        return f"""
You need to make a {decision_type} decision based on the following context:

CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE ALTERNATIVES:
{json.dumps(alternatives, indent=2)}

Please analyze the situation and provide your decision in the following JSON format:
{{
    "selected_alternative": "index or description of chosen alternative",
    "reasoning": "detailed explanation of your decision process",
    "confidence": "low|medium|high|critical",
    "estimated_cost": 0.0,
    "estimated_benefit": 0.0,
    "tools_used": ["list of tools you would use"],
    "risk_assessment": "assessment of potential risks",
    "success_probability": 0.0
}}

Consider:
1. Cost-benefit analysis
2. Risk factors
3. Time sensitivity
4. Regulatory compliance
5. Customer satisfaction impact
6. Operational efficiency
7. Available resources
"""
    
    def _parse_decision_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to extract decision details"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                decision_data = {
                    'reasoning': response,
                    'confidence': 'medium',
                    'estimated_cost': 0.0,
                    'estimated_benefit': 0.0,
                    'tools_used': []
                }
            
            # Validate and set defaults
            decision_data.setdefault('reasoning', 'No reasoning provided')
            decision_data.setdefault('confidence', 'medium')
            decision_data.setdefault('estimated_cost', 0.0)
            decision_data.setdefault('estimated_benefit', 0.0)
            decision_data.setdefault('tools_used', [])
            
            return decision_data
            
        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.warning("Failed to parse decision response", error=str(e))
            return {
                'reasoning': response,
                'confidence': 'low',
                'estimated_cost': 0.0,
                'estimated_benefit': 0.0,
                'tools_used': []
            }
    
    async def learn_from_outcome(self, decision_id: str, outcome: str, 
                               actual_cost: float, actual_benefit: float,
                               feedback_score: float) -> None:
        """Learn from decision outcomes to improve future decisions"""
        decisions = await self.shared_memory.get_decisions()
        for decision in decisions:
            if decision.decision_id == decision_id:
                decision.outcome = outcome
                decision.actual_cost = actual_cost
                decision.actual_benefit = actual_benefit
                decision.feedback_score = feedback_score
                
                # Store learning data for future model improvements
                await self.shared_memory.store(
                    f"learning_{decision_id}",
                    {
                        'decision': decision.to_dict(),
                        'performance_delta': {
                            'cost_accuracy': abs(decision.estimated_cost - actual_cost),
                            'benefit_accuracy': abs(decision.estimated_benefit - actual_benefit),
                            'confidence_validation': feedback_score
                        }
                    },
                    ttl=86400 * 30  # Store for 30 days
                )
                
                self.logger.info("Learning recorded",
                               decision_id=decision_id,
                               feedback_score=feedback_score)
                break
    
    async def get_relevant_context(self, task_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get relevant context from shared memory for decision making"""
        # Get recent decisions of similar type
        recent_decisions = await self.shared_memory.get_decisions(
            agent_type=self.agent_type,
            since=datetime.now() - timedelta(hours=24),
            limit=limit
        )
        
        # Get recent context history
        context_history = await self.shared_memory.get_context_history(
            since=datetime.now() - timedelta(hours=6),
            limit=limit
        )
        
        # Get performance metrics
        performance = await self.performance_monitor.get_performance_summary(
            self.agent_id,
            since=datetime.now() - timedelta(hours=24)
        )
        
        return {
            'recent_decisions': [d.to_dict() for d in recent_decisions],
            'context_history': context_history,
            'performance_metrics': performance
        }
    
    async def coordinate_with_agents(self, message: Dict[str, Any], 
                                   target_agents: List[str]) -> List[Dict[str, Any]]:
        """Send coordination messages to other agents"""
        responses = []
        coordination_id = str(uuid.uuid4())
        
        # Store coordination request in shared memory
        await self.shared_memory.store(
            f"coordination_{coordination_id}",
            {
                'from_agent': self.agent_id,
                'message': message,
                'target_agents': target_agents,
                'timestamp': datetime.now()
            },
            ttl=3600  # 1 hour TTL
        )
        
        # In a real implementation, this would trigger the target agents
        # For now, we'll simulate by storing coordination markers
        for target_agent in target_agents:
            await self.shared_memory.store(
                f"coordination_request_{target_agent}_{coordination_id}",
                {
                    'from_agent': self.agent_id,
                    'coordination_id': coordination_id,
                    'message': message,
                    'status': 'pending'
                },
                ttl=3600
            )
        
        self.logger.info("Coordination request sent",
                        coordination_id=coordination_id,
                        target_agents=target_agents)
        
        return responses
    
    def __str__(self) -> str:
        return f"{self.agent_type.value.title()}Agent({self.agent_id})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} type={self.agent_type.value} status={self.status.value}>"