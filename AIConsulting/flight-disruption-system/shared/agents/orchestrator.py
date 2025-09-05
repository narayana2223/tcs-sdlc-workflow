"""
Multi-Agent Orchestration System using LangGraph

This module provides the core orchestration logic for coordinating multiple AI agents
in the flight disruption management system. It uses LangGraph for workflow management
and ensures proper agent communication, state management, and decision coordination.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, TypedDict, Annotated
from enum import Enum
import uuid
import structlog

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .base_agent import BaseAgent, AgentType, AgentStatus, SharedMemory, PerformanceMonitor

logger = structlog.get_logger()


class TaskType(Enum):
    """Types of tasks that can be orchestrated"""
    DISRUPTION_RESPONSE = "disruption_response"
    PASSENGER_REBOOKING = "passenger_rebooking"
    COST_OPTIMIZATION = "cost_optimization"
    COMMUNICATION_CAMPAIGN = "communication_campaign"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    EMERGENCY_RESPONSE = "emergency_response"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class WorkflowState(TypedDict):
    """State structure for LangGraph workflows"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    context: Dict[str, Any]
    agents_involved: List[str]
    current_step: str
    step_results: Dict[str, Any]
    decisions: List[Dict[str, Any]]
    messages: List[BaseMessage]
    start_time: datetime
    deadline: Optional[datetime]
    status: str
    error_message: Optional[str]


class AgentOrchestrator:
    """Orchestrates multiple AI agents using LangGraph workflows"""
    
    def __init__(self,
                 llm: ChatOpenAI,
                 shared_memory: SharedMemory,
                 performance_monitor: PerformanceMonitor):
        
        self.llm = llm
        self.shared_memory = shared_memory
        self.performance_monitor = performance_monitor
        self.agents: Dict[AgentType, BaseAgent] = {}
        
        # Create memory saver for workflow state persistence
        self.memory = MemorySaver()
        
        # Create workflow graphs for different task types
        self.workflows = {}
        self._initialize_workflows()
        
        self.logger = structlog.get_logger().bind(component="orchestrator")
        
        # Active tasks tracking
        self.active_tasks: Dict[str, WorkflowState] = {}
        
        # Task queue for prioritization
        self.task_queue: List[Tuple[TaskPriority, str, WorkflowState]] = []
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator"""
        self.agents[agent.agent_type] = agent
        self.logger.info("Agent registered", 
                        agent_type=agent.agent_type.value,
                        agent_id=agent.agent_id)
    
    def _initialize_workflows(self) -> None:
        """Initialize LangGraph workflows for different task types"""
        
        # Disruption Response Workflow
        self.workflows[TaskType.DISRUPTION_RESPONSE] = self._create_disruption_response_workflow()
        
        # Passenger Rebooking Workflow
        self.workflows[TaskType.PASSENGER_REBOOKING] = self._create_passenger_rebooking_workflow()
        
        # Cost Optimization Workflow
        self.workflows[TaskType.COST_OPTIMIZATION] = self._create_cost_optimization_workflow()
        
        # Communication Campaign Workflow
        self.workflows[TaskType.COMMUNICATION_CAMPAIGN] = self._create_communication_workflow()
        
        # Predictive Analysis Workflow
        self.workflows[TaskType.PREDICTIVE_ANALYSIS] = self._create_predictive_analysis_workflow()
    
    def _create_disruption_response_workflow(self) -> StateGraph:
        """Create workflow for handling flight disruptions"""
        workflow = StateGraph(WorkflowState)
        
        # Define workflow steps
        workflow.add_node("assess_situation", self._assess_disruption_situation)
        workflow.add_node("predict_impact", self._predict_disruption_impact)
        workflow.add_node("plan_response", self._plan_disruption_response)
        workflow.add_node("coordinate_resources", self._coordinate_disruption_resources)
        workflow.add_node("execute_response", self._execute_disruption_response)
        workflow.add_node("monitor_progress", self._monitor_disruption_progress)
        
        # Define workflow edges
        workflow.add_edge(START, "assess_situation")
        workflow.add_edge("assess_situation", "predict_impact")
        workflow.add_edge("predict_impact", "plan_response")
        workflow.add_edge("plan_response", "coordinate_resources")
        workflow.add_edge("coordinate_resources", "execute_response")
        workflow.add_edge("execute_response", "monitor_progress")
        workflow.add_edge("monitor_progress", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _create_passenger_rebooking_workflow(self) -> StateGraph:
        """Create workflow for passenger rebooking"""
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("analyze_passengers", self._analyze_affected_passengers)
        workflow.add_node("find_alternatives", self._find_rebooking_alternatives)
        workflow.add_node("optimize_assignments", self._optimize_passenger_assignments)
        workflow.add_node("process_rebookings", self._process_passenger_rebookings)
        workflow.add_node("send_notifications", self._send_passenger_notifications)
        
        workflow.add_edge(START, "analyze_passengers")
        workflow.add_edge("analyze_passengers", "find_alternatives")
        workflow.add_edge("find_alternatives", "optimize_assignments")
        workflow.add_edge("optimize_assignments", "process_rebookings")
        workflow.add_edge("process_rebookings", "send_notifications")
        workflow.add_edge("send_notifications", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _create_cost_optimization_workflow(self) -> StateGraph:
        """Create workflow for cost optimization"""
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("assess_costs", self._assess_current_costs)
        workflow.add_node("find_savings", self._find_cost_savings)
        workflow.add_node("optimize_resources", self._optimize_resource_allocation)
        workflow.add_node("validate_compliance", self._validate_cost_compliance)
        workflow.add_node("implement_changes", self._implement_cost_changes)
        
        workflow.add_edge(START, "assess_costs")
        workflow.add_edge("assess_costs", "find_savings")
        workflow.add_edge("find_savings", "optimize_resources")
        workflow.add_edge("optimize_resources", "validate_compliance")
        workflow.add_edge("validate_compliance", "implement_changes")
        workflow.add_edge("implement_changes", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _create_communication_workflow(self) -> StateGraph:
        """Create workflow for communication campaigns"""
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("segment_passengers", self._segment_passengers)
        workflow.add_node("personalize_messages", self._personalize_messages)
        workflow.add_node("select_channels", self._select_communication_channels)
        workflow.add_node("send_communications", self._send_bulk_communications)
        workflow.add_node("track_responses", self._track_communication_responses)
        
        workflow.add_edge(START, "segment_passengers")
        workflow.add_edge("segment_passengers", "personalize_messages")
        workflow.add_edge("personalize_messages", "select_channels")
        workflow.add_edge("select_channels", "send_communications")
        workflow.add_edge("send_communications", "track_responses")
        workflow.add_edge("track_responses", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _create_predictive_analysis_workflow(self) -> StateGraph:
        """Create workflow for predictive analysis"""
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("collect_data", self._collect_prediction_data)
        workflow.add_node("analyze_patterns", self._analyze_prediction_patterns)
        workflow.add_node("generate_forecasts", self._generate_disruption_forecasts)
        workflow.add_node("validate_predictions", self._validate_predictions)
        workflow.add_node("distribute_insights", self._distribute_prediction_insights)
        
        workflow.add_edge(START, "collect_data")
        workflow.add_edge("collect_data", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "generate_forecasts")
        workflow.add_edge("generate_forecasts", "validate_predictions")
        workflow.add_edge("validate_predictions", "distribute_insights")
        workflow.add_edge("distribute_insights", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def execute_task(self,
                          task_type: TaskType,
                          context: Dict[str, Any],
                          priority: TaskPriority = TaskPriority.NORMAL,
                          deadline: Optional[datetime] = None) -> Dict[str, Any]:
        """Execute a coordinated task using the appropriate workflow"""
        
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Create initial state
        initial_state: WorkflowState = {
            "task_id": task_id,
            "task_type": task_type,
            "priority": priority,
            "context": context,
            "agents_involved": [],
            "current_step": "start",
            "step_results": {},
            "decisions": [],
            "messages": [SystemMessage(content=f"Starting {task_type.value} workflow")],
            "start_time": start_time,
            "deadline": deadline,
            "status": "running",
            "error_message": None
        }
        
        # Add to active tasks
        self.active_tasks[task_id] = initial_state
        
        try:
            # Get appropriate workflow
            workflow = self.workflows.get(task_type)
            if not workflow:
                raise ValueError(f"No workflow defined for task type: {task_type}")
            
            # Execute workflow
            config = {"configurable": {"thread_id": task_id}}
            
            self.logger.info("Starting workflow execution",
                           task_id=task_id,
                           task_type=task_type.value,
                           priority=priority.value)
            
            # Run the workflow
            result = await workflow.ainvoke(initial_state, config=config)
            
            # Update task status
            result["status"] = "completed"
            result["end_time"] = datetime.now()
            result["execution_time"] = (result["end_time"] - start_time).total_seconds()
            
            # Store final results
            self.active_tasks[task_id] = result
            
            # Record performance metrics
            await self.performance_monitor.record_execution(
                "orchestrator",
                f"workflow_{task_type.value}",
                result["execution_time"] * 1000,  # Convert to ms
                True,
                {"task_id": task_id, "agents_involved": result["agents_involved"]}
            )
            
            self.logger.info("Workflow completed successfully",
                           task_id=task_id,
                           execution_time=result["execution_time"],
                           agents_involved=result["agents_involved"])
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update task with error
            if task_id in self.active_tasks:
                self.active_tasks[task_id].update({
                    "status": "failed",
                    "error_message": error_msg,
                    "end_time": end_time,
                    "execution_time": execution_time
                })
            
            # Record failure metrics
            await self.performance_monitor.record_execution(
                "orchestrator",
                f"workflow_{task_type.value}",
                execution_time * 1000,
                False,
                {"task_id": task_id, "error": error_msg}
            )
            
            self.logger.error("Workflow execution failed",
                            task_id=task_id,
                            task_type=task_type.value,
                            error=error_msg)
            
            raise
    
    # Workflow step implementations
    
    async def _assess_disruption_situation(self, state: WorkflowState) -> WorkflowState:
        """Assess the current disruption situation"""
        if AgentType.PREDICTION not in self.agents:
            raise ValueError("Prediction agent not available")
        
        prediction_agent = self.agents[AgentType.PREDICTION]
        
        # Call prediction agent to assess situation
        assessment_task = {
            "type": "situation_assessment",
            "context": state["context"],
            "urgency": state["priority"].value
        }
        
        result = await prediction_agent.process_task(assessment_task)
        
        state["step_results"]["situation_assessment"] = result
        state["agents_involved"].append(prediction_agent.agent_id)
        state["current_step"] = "assess_situation"
        
        return state
    
    async def _predict_disruption_impact(self, state: WorkflowState) -> WorkflowState:
        """Predict the impact of the disruption"""
        prediction_agent = self.agents[AgentType.PREDICTION]
        
        impact_task = {
            "type": "impact_prediction",
            "context": state["context"],
            "assessment": state["step_results"]["situation_assessment"]
        }
        
        result = await prediction_agent.process_task(impact_task)
        
        state["step_results"]["impact_prediction"] = result
        state["current_step"] = "predict_impact"
        
        return state
    
    async def _plan_disruption_response(self, state: WorkflowState) -> WorkflowState:
        """Plan the response to the disruption"""
        coordinator_agent = self.agents.get(AgentType.COORDINATOR)
        if not coordinator_agent:
            # Use prediction agent as fallback coordinator
            coordinator_agent = self.agents[AgentType.PREDICTION]
        
        planning_task = {
            "type": "response_planning",
            "context": state["context"],
            "assessment": state["step_results"]["situation_assessment"],
            "impact": state["step_results"]["impact_prediction"]
        }
        
        result = await coordinator_agent.process_task(planning_task)
        
        state["step_results"]["response_plan"] = result
        state["current_step"] = "plan_response"
        
        if coordinator_agent.agent_id not in state["agents_involved"]:
            state["agents_involved"].append(coordinator_agent.agent_id)
        
        return state
    
    async def _coordinate_disruption_resources(self, state: WorkflowState) -> WorkflowState:
        """Coordinate resources for disruption response"""
        resource_agent = self.agents.get(AgentType.RESOURCE)
        
        if resource_agent:
            coordination_task = {
                "type": "resource_coordination",
                "context": state["context"],
                "response_plan": state["step_results"]["response_plan"]
            }
            
            result = await resource_agent.process_task(coordination_task)
            state["step_results"]["resource_coordination"] = result
            
            if resource_agent.agent_id not in state["agents_involved"]:
                state["agents_involved"].append(resource_agent.agent_id)
        else:
            state["step_results"]["resource_coordination"] = {"status": "skipped", "reason": "No resource agent available"}
        
        state["current_step"] = "coordinate_resources"
        return state
    
    async def _execute_disruption_response(self, state: WorkflowState) -> WorkflowState:
        """Execute the disruption response plan"""
        # Coordinate execution across multiple agents
        execution_tasks = []
        
        # Passenger management
        if AgentType.PASSENGER in self.agents:
            passenger_agent = self.agents[AgentType.PASSENGER]
            passenger_task = {
                "type": "execute_passenger_response",
                "context": state["context"],
                "plan": state["step_results"]["response_plan"]
            }
            execution_tasks.append(("passenger", passenger_agent, passenger_task))
        
        # Resource management
        if AgentType.RESOURCE in self.agents:
            resource_agent = self.agents[AgentType.RESOURCE]
            resource_task = {
                "type": "execute_resource_response",
                "context": state["context"],
                "plan": state["step_results"]["response_plan"]
            }
            execution_tasks.append(("resource", resource_agent, resource_task))
        
        # Communication
        if AgentType.COMMUNICATION in self.agents:
            comm_agent = self.agents[AgentType.COMMUNICATION]
            comm_task = {
                "type": "execute_communication_response",
                "context": state["context"],
                "plan": state["step_results"]["response_plan"]
            }
            execution_tasks.append(("communication", comm_agent, comm_task))
        
        # Execute tasks in parallel
        execution_results = {}
        for task_name, agent, task in execution_tasks:
            try:
                result = await agent.process_task(task)
                execution_results[task_name] = result
                
                if agent.agent_id not in state["agents_involved"]:
                    state["agents_involved"].append(agent.agent_id)
                    
            except Exception as e:
                execution_results[task_name] = {"status": "failed", "error": str(e)}
        
        state["step_results"]["execution"] = execution_results
        state["current_step"] = "execute_response"
        
        return state
    
    async def _monitor_disruption_progress(self, state: WorkflowState) -> WorkflowState:
        """Monitor the progress of disruption response"""
        # Collect status from all involved agents
        monitoring_results = {}
        
        for agent_id in state["agents_involved"]:
            agent_state = await self.shared_memory.get_agent_state(agent_id)
            if agent_state:
                monitoring_results[agent_id] = agent_state
        
        # Assess overall progress
        progress_assessment = {
            "overall_status": "in_progress",
            "completion_percentage": 0.0,
            "agent_statuses": monitoring_results,
            "next_actions": []
        }
        
        # Simple progress calculation
        completed_agents = len([s for s in monitoring_results.values() 
                              if s.get("status") in ["completed", "idle"]])
        total_agents = len(monitoring_results)
        
        if total_agents > 0:
            progress_assessment["completion_percentage"] = (completed_agents / total_agents) * 100
        
        if progress_assessment["completion_percentage"] >= 100:
            progress_assessment["overall_status"] = "completed"
        
        state["step_results"]["monitoring"] = progress_assessment
        state["current_step"] = "monitor_progress"
        
        return state
    
    # Additional workflow step implementations for other task types
    
    async def _analyze_affected_passengers(self, state: WorkflowState) -> WorkflowState:
        """Analyze passengers affected by disruption"""
        passenger_agent = self.agents.get(AgentType.PASSENGER)
        if not passenger_agent:
            raise ValueError("Passenger agent not available")
        
        analysis_task = {
            "type": "passenger_analysis",
            "context": state["context"]
        }
        
        result = await passenger_agent.process_task(analysis_task)
        state["step_results"]["passenger_analysis"] = result
        state["agents_involved"].append(passenger_agent.agent_id)
        
        return state
    
    async def _find_rebooking_alternatives(self, state: WorkflowState) -> WorkflowState:
        """Find rebooking alternatives for passengers"""
        passenger_agent = self.agents[AgentType.PASSENGER]
        
        alternatives_task = {
            "type": "find_alternatives",
            "context": state["context"],
            "passenger_analysis": state["step_results"]["passenger_analysis"]
        }
        
        result = await passenger_agent.process_task(alternatives_task)
        state["step_results"]["alternatives"] = result
        
        return state
    
    async def _optimize_passenger_assignments(self, state: WorkflowState) -> WorkflowState:
        """Optimize passenger seat assignments"""
        # This could involve both passenger and resource agents
        optimization_results = {}
        
        if AgentType.PASSENGER in self.agents:
            passenger_agent = self.agents[AgentType.PASSENGER]
            passenger_task = {
                "type": "optimize_assignments",
                "context": state["context"],
                "alternatives": state["step_results"]["alternatives"]
            }
            optimization_results["passenger_optimization"] = await passenger_agent.process_task(passenger_task)
        
        if AgentType.RESOURCE in self.agents:
            resource_agent = self.agents[AgentType.RESOURCE]
            resource_task = {
                "type": "optimize_resources",
                "context": state["context"],
                "alternatives": state["step_results"]["alternatives"]
            }
            optimization_results["resource_optimization"] = await resource_agent.process_task(resource_task)
            
            if resource_agent.agent_id not in state["agents_involved"]:
                state["agents_involved"].append(resource_agent.agent_id)
        
        state["step_results"]["optimization"] = optimization_results
        return state
    
    async def _process_passenger_rebookings(self, state: WorkflowState) -> WorkflowState:
        """Process passenger rebookings"""
        passenger_agent = self.agents[AgentType.PASSENGER]
        
        rebooking_task = {
            "type": "process_rebookings",
            "context": state["context"],
            "optimization": state["step_results"]["optimization"]
        }
        
        result = await passenger_agent.process_task(rebooking_task)
        state["step_results"]["rebooking_results"] = result
        
        return state
    
    async def _send_passenger_notifications(self, state: WorkflowState) -> WorkflowState:
        """Send notifications to passengers"""
        comm_agent = self.agents.get(AgentType.COMMUNICATION)
        if not comm_agent:
            state["step_results"]["notifications"] = {"status": "skipped", "reason": "No communication agent available"}
            return state
        
        notification_task = {
            "type": "send_notifications",
            "context": state["context"],
            "rebooking_results": state["step_results"]["rebooking_results"]
        }
        
        result = await comm_agent.process_task(notification_task)
        state["step_results"]["notifications"] = result
        
        if comm_agent.agent_id not in state["agents_involved"]:
            state["agents_involved"].append(comm_agent.agent_id)
        
        return state
    
    # Placeholder implementations for other workflow steps
    async def _assess_current_costs(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["cost_assessment"] = {"status": "completed"}
        return state
    
    async def _find_cost_savings(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["cost_savings"] = {"status": "completed"}
        return state
    
    async def _optimize_resource_allocation(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["resource_allocation"] = {"status": "completed"}
        return state
    
    async def _validate_cost_compliance(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["compliance_validation"] = {"status": "completed"}
        return state
    
    async def _implement_cost_changes(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["cost_implementation"] = {"status": "completed"}
        return state
    
    async def _segment_passengers(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["passenger_segmentation"] = {"status": "completed"}
        return state
    
    async def _personalize_messages(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["message_personalization"] = {"status": "completed"}
        return state
    
    async def _select_communication_channels(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["channel_selection"] = {"status": "completed"}
        return state
    
    async def _send_bulk_communications(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["bulk_communications"] = {"status": "completed"}
        return state
    
    async def _track_communication_responses(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["response_tracking"] = {"status": "completed"}
        return state
    
    async def _collect_prediction_data(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["data_collection"] = {"status": "completed"}
        return state
    
    async def _analyze_prediction_patterns(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["pattern_analysis"] = {"status": "completed"}
        return state
    
    async def _generate_disruption_forecasts(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["forecasts"] = {"status": "completed"}
        return state
    
    async def _validate_predictions(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["prediction_validation"] = {"status": "completed"}
        return state
    
    async def _distribute_prediction_insights(self, state: WorkflowState) -> WorkflowState:
        state["step_results"]["insight_distribution"] = {"status": "completed"}
        return state
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a running or completed task"""
        return self.active_tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task["status"] == "running":
                task["status"] = "cancelled"
                task["end_time"] = datetime.now()
                self.logger.info("Task cancelled", task_id=task_id)
                return True
        return False
    
    async def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all agents"""
        summary = {}
        for agent_type, agent in self.agents.items():
            summary[agent_type.value] = await self.performance_monitor.get_performance_summary(
                agent.agent_id,
                since=datetime.now() - timedelta(hours=24)
            )
        return summary