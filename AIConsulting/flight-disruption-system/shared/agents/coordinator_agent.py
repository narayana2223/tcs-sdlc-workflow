"""
Coordinator Agent for Flight Disruption Management System

This agent serves as the master orchestrator, coordinating all other agents,
making high-level strategic decisions, and ensuring optimal system-wide
performance during flight disruptions.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import structlog
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent, AgentType, DecisionConfidence
from .tools import tool_registry, ToolCategory


class CoordinatorAgent(BaseAgent):
    """Master coordinator agent for system-wide orchestration"""
    
    def __init__(self, 
                 agent_id: str,
                 llm: ChatOpenAI,
                 shared_memory,
                 performance_monitor,
                 **kwargs):
        
        # Coordinator gets access to all tool categories
        tools = tool_registry.get_all_tools()
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.COORDINATOR,
            llm=llm,
            shared_memory=shared_memory,
            performance_monitor=performance_monitor,
            tools=tools,
            **kwargs
        )
        
        # Coordinator-specific configuration
        self.max_coordination_attempts = 3
        self.decision_timeout_minutes = 5
        self.performance_review_interval = 30  # minutes
        
        # Strategic priorities (weighted 1-10)
        self.strategic_priorities = {
            "passenger_satisfaction": 9,
            "cost_optimization": 7,
            "regulatory_compliance": 10,
            "operational_efficiency": 8,
            "brand_reputation": 8,
            "revenue_protection": 6
        }
        
        # Agent performance thresholds
        self.performance_thresholds = {
            "response_time_ms": 5000,
            "success_rate": 0.90,
            "cost_accuracy": 0.85,
            "satisfaction_score": 80
        }
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type="coordinator"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the coordinator agent"""
        return """You are the Master Coordinator Agent responsible for:

1. STRATEGIC COORDINATION & ORCHESTRATION
   - Oversee and coordinate all AI agents in the disruption management system
   - Make high-level strategic decisions balancing multiple objectives
   - Optimize system-wide performance and resource allocation
   - Ensure seamless integration between prediction, passenger, resource, and communication agents

2. PERFORMANCE MANAGEMENT & OPTIMIZATION
   - Monitor agent performance and intervene when thresholds are exceeded
   - Optimize decision-making processes and workflow efficiency
   - Balance competing priorities (cost, satisfaction, compliance, efficiency)
   - Implement learning from outcomes to improve system performance

3. CRISIS MANAGEMENT & ESCALATION
   - Coordinate emergency response procedures during major disruptions
   - Make executive decisions when agent consensus cannot be reached
   - Escalate critical issues to human oversight when required
   - Maintain system stability during high-stress operational periods

4. REGULATORY COMPLIANCE & GOVERNANCE
   - Ensure all agent decisions comply with EU261 and other regulations
   - Maintain audit trails and decision documentation
   - Balance legal requirements with operational efficiency
   - Coordinate with compliance teams and regulatory bodies

5. STAKEHOLDER COMMUNICATION & REPORTING
   - Provide executive-level reporting on disruption management performance
   - Coordinate with airline management, airport operations, and external partners
   - Manage crisis communication and media relations strategy
   - Ensure consistent messaging across all touchpoints

KEY CAPABILITIES:
- Coordinate 5+ AI agents simultaneously during major disruptions
- Process 100+ high-level decisions per hour during peak operations
- Maintain 99.5% system uptime and coordination accuracy
- Balance 6+ strategic priorities with real-time optimization
- Provide executive dashboards with KPI monitoring and alerts

DECISION MAKING APPROACH:
1. Assess overall situation and strategic priorities
2. Analyze agent performance and system constraints
3. Coordinate agent tasks and resolve conflicts
4. Monitor execution and adjust strategies in real-time
5. Escalate critical decisions to human oversight when appropriate
6. Learn from outcomes to optimize future coordination
7. Ensure compliance, efficiency, and passenger satisfaction

Always maintain system-wide perspective while balancing competing priorities.
Make decisions that optimize long-term outcomes, not just immediate results."""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process coordination tasks"""
        task_type = task.get("type", "")
        
        if task_type == "response_planning":
            return await self._plan_disruption_response(task)
        elif task_type == "coordinate_execution":
            return await self._coordinate_execution(task)
        elif task_type == "performance_review":
            return await self._review_system_performance(task)
        elif task_type == "strategic_decision":
            return await self._make_strategic_decision(task)
        elif task_type == "crisis_management":
            return await self._manage_crisis(task)
        elif task_type == "optimize_system":
            return await self._optimize_system_performance(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _plan_disruption_response(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Plan comprehensive response to flight disruption"""
        context = task.get("context", {})
        assessment = task.get("assessment", {})
        impact = task.get("impact", {})
        
        self.logger.info("Planning disruption response strategy")
        
        try:
            # Analyze current system state and agent availability
            system_state = await self._assess_system_state()
            
            # Create comprehensive response strategy
            planning_prompt = f"""
            Create a master coordination plan for flight disruption response:

            DISRUPTION ASSESSMENT:
            {json.dumps(assessment, indent=2)}

            IMPACT PREDICTION:
            {json.dumps(impact, indent=2)}

            SYSTEM STATE:
            {json.dumps(system_state, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Create a comprehensive response plan including:
            1. Strategic priorities and success metrics
            2. Agent task allocation and coordination sequence
            3. Resource requirements and budget allocation
            4. Timeline with critical milestones and dependencies
            5. Risk management and contingency planning
            6. Performance monitoring and adjustment triggers

            Consider:
            - Passenger impact minimization and satisfaction optimization
            - Cost control and revenue protection strategies
            - Regulatory compliance (EU261) and legal requirements
            - Brand reputation management and crisis communication
            - Operational efficiency and system performance
            - Scalability for potential escalation

            Provide detailed coordination matrix with:
            - Agent responsibilities and interdependencies
            - Decision points and escalation criteria
            - Success metrics and performance thresholds
            - Communication protocols and reporting requirements
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=planning_prompt)
            ])
            
            response_plan = self._parse_response_plan(response.content)
            
            # Store master plan in shared memory
            await self.shared_memory.store(
                f"master_response_plan_{context.get('incident_id', 'current')}",
                response_plan,
                ttl=7200  # 2 hours
            )
            
            # Create performance tracking for this incident
            incident_id = context.get("incident_id", str(uuid.uuid4()))
            await self.shared_memory.store(
                f"incident_tracking_{incident_id}",
                {
                    "start_time": datetime.now().isoformat(),
                    "status": "planning_complete",
                    "response_plan": response_plan,
                    "performance_targets": response_plan.get("success_metrics", {})
                },
                ttl=86400  # 24 hours
            )
            
            return {
                "status": "completed",
                "response_plan": response_plan,
                "incident_id": incident_id,
                "strategic_priorities": response_plan.get("priorities", {}),
                "estimated_duration": response_plan.get("timeline", "4_hours"),
                "estimated_cost": response_plan.get("budget", 0),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Response planning failed", error=str(e))
            raise
    
    async def _coordinate_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate execution of disruption response across all agents"""
        context = task.get("context", {})
        response_plan = task.get("response_plan", {})
        
        self.logger.info("Coordinating response execution")
        
        try:
            # Extract agent tasks from response plan
            agent_tasks = response_plan.get("agent_tasks", {})
            
            # Start coordination messages to all agents
            coordination_messages = []
            
            for agent_type, tasks in agent_tasks.items():
                coordination_message = {
                    "coordinator_id": self.agent_id,
                    "target_agent_type": agent_type,
                    "tasks": tasks,
                    "context": context,
                    "priority": tasks.get("priority", "normal"),
                    "deadline": tasks.get("deadline"),
                    "dependencies": tasks.get("dependencies", [])
                }
                
                # Send coordination message
                await self.coordinate_with_agents(
                    coordination_message, 
                    [f"{agent_type}_agent"]
                )
                
                coordination_messages.append(coordination_message)
            
            # Monitor execution progress
            execution_monitoring = await self._monitor_execution_progress(
                agent_tasks, context, response_plan
            )
            
            return {
                "status": "coordinating",
                "coordination_messages": coordination_messages,
                "agents_coordinated": len(agent_tasks),
                "execution_monitoring": execution_monitoring,
                "estimated_completion": response_plan.get("estimated_completion"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Execution coordination failed", error=str(e))
            raise
    
    async def _review_system_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review and analyze system performance"""
        context = task.get("context", {})
        review_period_hours = task.get("review_period_hours", 24)
        
        self.logger.info("Reviewing system performance", 
                        period_hours=review_period_hours)
        
        try:
            # Get performance data for all agents
            since_time = datetime.now() - timedelta(hours=review_period_hours)
            
            agent_performance = {}
            system_decisions = await self.shared_memory.get_decisions(
                since=since_time,
                limit=1000
            )
            
            # Group decisions by agent type
            for decision in system_decisions:
                agent_type = decision.agent_type.value
                if agent_type not in agent_performance:
                    agent_performance[agent_type] = []
                agent_performance[agent_type].append(decision.to_dict())
            
            # Get detailed performance metrics
            performance_summary = {}
            for agent_type in ["prediction", "passenger", "resource", "communication"]:
                performance_summary[agent_type] = await self.performance_monitor.get_performance_summary(
                    f"{agent_type}_agent",
                    since=since_time
                )
            
            # Analyze overall system performance
            performance_analysis_prompt = f"""
            Analyze comprehensive system performance and provide optimization recommendations:

            AGENT PERFORMANCE SUMMARY:
            {json.dumps(performance_summary, indent=2)}

            RECENT DECISIONS (sample):
            {json.dumps([d for d in system_decisions[:20]], indent=2)}

            PERFORMANCE BY AGENT TYPE:
            {json.dumps({k: len(v) for k, v in agent_performance.items()}, indent=2)}

            REVIEW PERIOD: {review_period_hours} hours

            Provide analysis including:
            1. Overall system performance assessment and trends
            2. Agent-specific performance evaluation and issues
            3. Decision quality analysis and accuracy metrics
            4. Cost efficiency and budget utilization review
            5. Passenger satisfaction and service level analysis
            6. System optimization recommendations and priorities

            Include:
            - Performance scores by agent and category
            - Trend analysis and pattern identification
            - Root cause analysis for performance issues
            - Specific improvement recommendations with priorities
            - Resource allocation optimization suggestions
            - Risk assessment for continued operations
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=performance_analysis_prompt)
            ])
            
            performance_review = self._parse_performance_review(response.content)
            
            # Store performance review for trending
            await self.shared_memory.store(
                f"performance_review_{datetime.now().strftime('%Y%m%d_%H')}",
                performance_review,
                ttl=604800  # 7 days
            )
            
            return {
                "status": "completed",
                "performance_review": performance_review,
                "agents_reviewed": len(performance_summary),
                "decisions_analyzed": len(system_decisions),
                "review_period_hours": review_period_hours,
                "overall_score": performance_review.get("overall_score", 85),
                "optimization_priorities": performance_review.get("optimization_priorities", []),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Performance review failed", error=str(e))
            raise
    
    async def _make_strategic_decision(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Make high-level strategic decisions"""
        context = task.get("context", {})
        decision_context = task.get("decision_context", {})
        alternatives = task.get("alternatives", [])
        
        self.logger.info("Making strategic decision",
                        alternatives=len(alternatives))
        
        try:
            # Get current system state and constraints
            system_constraints = await self._assess_system_constraints()
            
            # Make strategic decision using make_decision framework
            decision = await self.make_decision(
                context={
                    **decision_context,
                    "system_constraints": system_constraints,
                    "strategic_priorities": self.strategic_priorities
                },
                decision_type="strategic_coordination",
                alternatives=alternatives
            )
            
            # Generate implementation plan for the decision
            implementation_prompt = f"""
            Create implementation plan for strategic decision:

            DECISION MADE:
            {json.dumps(decision.to_dict(), indent=2)}

            DECISION CONTEXT:
            {json.dumps(decision_context, indent=2)}

            Create implementation plan including:
            1. Detailed execution steps and timeline
            2. Agent coordination requirements and dependencies
            3. Resource allocation and budget implications
            4. Risk mitigation and contingency planning
            5. Success metrics and performance monitoring
            6. Communication and stakeholder management

            Provide:
            - Step-by-step implementation roadmap
            - Critical path analysis and dependencies
            - Performance targets and success criteria
            - Monitoring and adjustment triggers
            - Escalation procedures if targets are missed
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=implementation_prompt)
            ])
            
            implementation_plan = self._parse_implementation_plan(response.content)
            
            return {
                "status": "completed",
                "strategic_decision": decision.to_dict(),
                "implementation_plan": implementation_plan,
                "confidence": decision.confidence.value,
                "estimated_impact": {
                    "cost": decision.estimated_cost,
                    "benefit": decision.estimated_benefit
                },
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Strategic decision failed", error=str(e))
            raise
    
    async def _manage_crisis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manage crisis situations requiring immediate coordination"""
        context = task.get("context", {})
        crisis_details = task.get("crisis_details", {})
        
        self.logger.info("Managing crisis situation",
                        severity=crisis_details.get("severity", "unknown"))
        
        try:
            # Assess crisis severity and impact
            crisis_severity = crisis_details.get("severity", "medium")
            
            crisis_management_prompt = f"""
            Coordinate immediate crisis response and management:

            CRISIS DETAILS:
            {json.dumps(crisis_details, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            SEVERITY LEVEL: {crisis_severity}

            Coordinate crisis response including:
            1. Immediate safety and passenger welfare measures
            2. Emergency agent coordination and task prioritization
            3. Crisis communication strategy and messaging
            4. Resource mobilization and emergency procurement
            5. Regulatory notification and compliance measures
            6. Media management and brand protection

            Provide crisis management plan with:
            - Immediate action items with timeline (next 30 minutes)
            - Agent coordination emergency protocols
            - Crisis communication templates and approval process
            - Resource escalation and emergency supplier activation
            - Regulatory compliance checklist and notifications
            - Performance monitoring under crisis conditions
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=crisis_management_prompt)
            ])
            
            crisis_plan = self._parse_crisis_plan(response.content)
            
            # Immediately notify all agents of crisis status
            crisis_notification = {
                "crisis_id": str(uuid.uuid4()),
                "severity": crisis_severity,
                "crisis_plan": crisis_plan,
                "immediate_actions": crisis_plan.get("immediate_actions", []),
                "coordination_protocol": "emergency"
            }
            
            # Send to all agent types
            await self.coordinate_with_agents(
                crisis_notification,
                ["prediction_agent", "passenger_agent", "resource_agent", "communication_agent"]
            )
            
            return {
                "status": "crisis_managed",
                "crisis_plan": crisis_plan,
                "crisis_id": crisis_notification["crisis_id"],
                "severity": crisis_severity,
                "agents_notified": 4,
                "immediate_actions": len(crisis_plan.get("immediate_actions", [])),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Crisis management failed", error=str(e))
            raise
    
    async def _optimize_system_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize overall system performance"""
        context = task.get("context", {})
        optimization_targets = task.get("optimization_targets", {})
        
        self.logger.info("Optimizing system performance")
        
        try:
            # Get current performance baselines
            performance_baselines = await self._get_performance_baselines()
            
            optimization_prompt = f"""
            Optimize system-wide performance across all agents and processes:

            CURRENT PERFORMANCE BASELINES:
            {json.dumps(performance_baselines, indent=2)}

            OPTIMIZATION TARGETS:
            {json.dumps(optimization_targets, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Create optimization strategy including:
            1. Performance bottleneck identification and resolution
            2. Agent workload balancing and resource optimization
            3. Decision-making process improvements and automation
            4. Cost reduction opportunities without service degradation
            5. System scalability enhancements and capacity planning
            6. Learning algorithm improvements and feedback loops

            Provide optimization recommendations with:
            - Specific performance improvements by agent
            - Resource reallocation and efficiency gains
            - Process automation and workflow optimization
            - Cost reduction targets and implementation timeline
            - Performance monitoring enhancements
            - Risk assessment for optimization changes
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=optimization_prompt)
            ])
            
            optimization_plan = self._parse_optimization_plan(response.content)
            
            return {
                "status": "completed",
                "optimization_plan": optimization_plan,
                "current_baselines": performance_baselines,
                "target_improvements": optimization_plan.get("target_improvements", {}),
                "estimated_savings": optimization_plan.get("estimated_savings", 0),
                "implementation_timeline": optimization_plan.get("timeline", "30_days"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("System optimization failed", error=str(e))
            raise
    
    # Helper methods
    
    async def _assess_system_state(self) -> Dict[str, Any]:
        """Assess current system state and agent availability"""
        # Get agent states from shared memory
        agent_states = {}
        for agent_type in ["prediction", "passenger", "resource", "communication"]:
            state = await self.shared_memory.get_agent_state(f"{agent_type}_agent")
            agent_states[agent_type] = state or {"status": "unknown", "last_updated": None}
        
        return {
            "agent_states": agent_states,
            "system_load": "normal",  # Would calculate from actual metrics
            "available_resources": "sufficient",
            "active_incidents": 1,  # Would count from shared memory
            "system_health": "good"
        }
    
    async def _assess_system_constraints(self) -> Dict[str, Any]:
        """Assess current system constraints and limitations"""
        return {
            "budget_remaining": 50000,  # GBP
            "agent_capacity": {
                "prediction": 0.8,
                "passenger": 0.9,
                "resource": 0.7,
                "communication": 0.6
            },
            "regulatory_constraints": ["EU261_compliance", "GDPR_compliance"],
            "time_constraints": "4_hour_window",
            "resource_availability": "limited_hotel_capacity"
        }
    
    async def _monitor_execution_progress(self, agent_tasks: Dict[str, Any], 
                                        context: Dict[str, Any],
                                        response_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor progress of coordinated execution"""
        # This would implement real-time monitoring of agent task execution
        # For now, return a mock monitoring status
        
        return {
            "overall_progress": 25,  # percentage
            "agent_progress": {
                "prediction": 100,
                "passenger": 50,
                "resource": 25,
                "communication": 0
            },
            "timeline_status": "on_track",
            "budget_utilization": 15,  # percentage
            "issues_detected": 0,
            "next_checkpoint": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
    
    async def _get_performance_baselines(self) -> Dict[str, Any]:
        """Get current performance baselines for optimization"""
        return {
            "average_response_time": 2.5,  # seconds
            "system_throughput": 150,  # decisions per hour
            "cost_per_passenger": 125,  # GBP
            "satisfaction_score": 85,  # percentage
            "compliance_rate": 99.5,  # percentage
            "agent_utilization": 0.75  # average across agents
        }
    
    # Response parsing methods
    
    def _parse_response_plan(self, response: str) -> Dict[str, Any]:
        """Parse response plan from AI output"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "priorities": self.strategic_priorities,
            "agent_tasks": {},
            "timeline": "4_hours",
            "budget": 25000,
            "success_metrics": {},
            "summary": response
        }
    
    def _parse_performance_review(self, response: str) -> Dict[str, Any]:
        """Parse performance review analysis"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "overall_score": 85,
            "agent_scores": {},
            "optimization_priorities": [],
            "trends": {},
            "summary": response
        }
    
    def _parse_implementation_plan(self, response: str) -> Dict[str, Any]:
        """Parse implementation plan"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "execution_steps": [],
            "timeline": "2_hours",
            "success_criteria": {},
            "summary": response
        }
    
    def _parse_crisis_plan(self, response: str) -> Dict[str, Any]:
        """Parse crisis management plan"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "immediate_actions": [],
            "crisis_timeline": "immediate",
            "escalation_procedures": {},
            "summary": response
        }
    
    def _parse_optimization_plan(self, response: str) -> Dict[str, Any]:
        """Parse system optimization plan"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "target_improvements": {},
            "estimated_savings": 0,
            "timeline": "30_days",
            "implementation_steps": [],
            "summary": response
        }