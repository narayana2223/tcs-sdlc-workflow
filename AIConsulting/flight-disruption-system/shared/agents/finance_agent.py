"""
Finance Agent - Autonomous Financial Optimization and Revenue Protection

This agent handles cost optimization, revenue protection, and financial decision-making
with sophisticated reasoning and collaboration capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import structlog

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .base_agent import BaseAgent, AgentType, AgentStatus, Decision, DecisionConfidence
from .agentic_intelligence import AgenticIntelligenceEngine, ReasoningType, ConflictType
from .tools import AirlineOperationTool, ToolCategory

logger = structlog.get_logger()


class FinancialMetric:
    """Financial calculation utilities"""
    
    @staticmethod
    def calculate_disruption_cost(
        passengers: int,
        avg_compensation: float,
        hotel_cost: float,
        transport_cost: float,
        opportunity_cost: float = 0
    ) -> Decimal:
        """Calculate total disruption cost"""
        total_cost = (
            passengers * avg_compensation +
            hotel_cost + 
            transport_cost +
            opportunity_cost
        )
        return Decimal(str(total_cost))
    
    @staticmethod
    def calculate_roi(benefit: float, cost: float) -> float:
        """Calculate return on investment"""
        if cost == 0:
            return float('inf') if benefit > 0 else 0
        return (benefit - cost) / cost * 100


class FinanceOptimizationTool(AirlineOperationTool):
    """Tool for financial optimization calculations"""
    
    name = "finance_optimization"
    description = "Optimize costs and calculate financial impact of decisions"
    category = ToolCategory.COST_MANAGEMENT
    
    async def _arun(self, optimization_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run financial optimization"""
        
        passengers = optimization_context.get("passengers", 0)
        disruption_type = optimization_context.get("disruption_type", "delay")
        duration_hours = optimization_context.get("duration_hours", 2)
        
        # Calculate compensation based on EU261
        base_compensation = self._calculate_eu261_compensation(disruption_type, duration_hours)
        total_compensation = passengers * base_compensation
        
        # Calculate accommodation costs
        hotel_cost = self._calculate_accommodation_cost(passengers, duration_hours)
        
        # Calculate transport costs
        transport_cost = self._calculate_transport_cost(passengers)
        
        # Calculate opportunity cost (lost revenue)
        opportunity_cost = self._calculate_opportunity_cost(passengers, disruption_type)
        
        total_cost = total_compensation + hotel_cost + transport_cost + opportunity_cost
        
        # Generate cost optimization recommendations
        optimizations = self._generate_optimizations(passengers, duration_hours, total_cost)
        
        return {
            "total_cost": float(total_cost),
            "breakdown": {
                "compensation": float(total_compensation),
                "accommodation": float(hotel_cost),
                "transport": float(transport_cost),
                "opportunity_cost": float(opportunity_cost)
            },
            "optimizations": optimizations,
            "cost_per_passenger": float(total_cost / max(passengers, 1)),
            "roi_analysis": self._calculate_prevention_roi(total_cost)
        }
    
    def _calculate_eu261_compensation(self, disruption_type: str, duration_hours: float) -> float:
        """Calculate EU261 compensation amounts"""
        if disruption_type == "cancellation":
            return 250.0  # Short haul cancellation
        elif duration_hours >= 3:
            return 250.0  # Significant delay
        elif duration_hours >= 2:
            return 125.0  # Moderate delay
        else:
            return 0.0  # No compensation required
    
    def _calculate_accommodation_cost(self, passengers: int, duration_hours: float) -> float:
        """Calculate hotel accommodation costs"""
        if duration_hours < 8:  # Day disruption
            return passengers * 25.0  # Meal vouchers
        else:  # Overnight accommodation
            return passengers * 95.0  # Hotel + meals
    
    def _calculate_transport_cost(self, passengers: int) -> float:
        """Calculate transport costs"""
        return passengers * 15.0  # Average transport voucher
    
    def _calculate_opportunity_cost(self, passengers: int, disruption_type: str) -> float:
        """Calculate lost revenue opportunity cost"""
        avg_ticket_value = 180.0
        if disruption_type == "cancellation":
            return passengers * avg_ticket_value * 0.15  # 15% revenue loss
        else:
            return passengers * avg_ticket_value * 0.05  # 5% revenue impact
    
    def _generate_optimizations(self, passengers: int, duration: float, total_cost: float) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        optimizations = []
        
        # Hotel optimization
        optimizations.append({
            "category": "accommodation",
            "description": "Negotiate bulk hotel rates",
            "potential_savings": total_cost * 0.12,
            "implementation": "Use preferred vendor agreements"
        })
        
        # Transport optimization
        optimizations.append({
            "category": "transport", 
            "description": "Optimize transport coordination",
            "potential_savings": total_cost * 0.08,
            "implementation": "Shared transport and routing optimization"
        })
        
        # Communication optimization
        optimizations.append({
            "category": "communication",
            "description": "Proactive passenger communication",
            "potential_savings": total_cost * 0.15,
            "implementation": "Reduce compensation claims through better service"
        })
        
        return optimizations
    
    def _calculate_prevention_roi(self, disruption_cost: float) -> Dict[str, float]:
        """Calculate ROI of disruption prevention measures"""
        return {
            "predictive_maintenance_roi": 340.0,  # % ROI
            "weather_monitoring_roi": 280.0,
            "crew_optimization_roi": 220.0,
            "cost_avoidance_value": disruption_cost * 0.85
        }


class FinanceAgent(BaseAgent):
    """
    Autonomous Finance Agent
    
    Handles cost optimization, revenue protection, and financial decision-making
    with sophisticated reasoning and real-time learning capabilities.
    """
    
    def __init__(
        self,
        agent_id: str,
        shared_memory,
        intelligence_engine: AgenticIntelligenceEngine,
        openai_api_key: str,
        cost_optimization_threshold: float = 1000.0,
        model: str = "gpt-4"
    ):
        super().__init__(agent_id, AgentType.RESOURCE, shared_memory)
        
        self.intelligence_engine = intelligence_engine
        self.cost_optimization_threshold = cost_optimization_threshold
        
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Performance tracking
        self.cost_savings_achieved = 0.0
        self.decisions_made = 0
        self.accuracy_score = 0.8
        
        # Initialize tools
        self.tools = [FinanceOptimizationTool()]
        
        logger.info(f"FinanceAgent {agent_id} initialized")
    
    async def analyze_financial_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze financial impact of disruption with autonomous reasoning
        """
        self.status = AgentStatus.PROCESSING
        
        try:
            # Process reasoning through intelligence engine
            reasoning = await self.intelligence_engine.process_agent_reasoning(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                context=context,
                reasoning_type=ReasoningType.ANALYTICAL
            )
            
            # Perform financial analysis
            analysis_result = await self._perform_financial_analysis(context, reasoning)
            
            # Make autonomous financial decision
            decision = await self._make_financial_decision(analysis_result, reasoning)
            
            self.decisions_made += 1
            self.status = AgentStatus.IDLE
            
            return {
                "analysis": analysis_result,
                "decision": decision,
                "reasoning": reasoning,
                "confidence": reasoning.confidence,
                "execution_time": (datetime.utcnow() - reasoning.timestamp).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error in financial impact analysis: {e}")
            self.status = AgentStatus.ERROR
            raise
    
    async def optimize_costs(
        self,
        cost_context: Dict[str, Any],
        collaboration_required: bool = True
    ) -> Dict[str, Any]:
        """
        Autonomous cost optimization with agent collaboration
        """
        self.status = AgentStatus.PROCESSING
        
        try:
            # Generate optimization reasoning
            reasoning = await self.intelligence_engine.process_agent_reasoning(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                context=cost_context,
                reasoning_type=ReasoningType.STRATEGIC
            )
            
            # Run optimization analysis
            optimization_tool = FinanceOptimizationTool()
            optimization_result = await optimization_tool._arun(cost_context)
            
            # Potential savings calculation
            potential_savings = sum(opt["potential_savings"] for opt in optimization_result["optimizations"])
            
            # Collaborate with other agents if beneficial
            if collaboration_required and potential_savings > self.cost_optimization_threshold:
                collaboration = await self._initiate_cost_collaboration(cost_context, optimization_result)
                optimization_result["collaboration"] = collaboration
            
            # Make final optimization decision
            decision = Decision(
                decision_id=f"finance_{uuid.uuid4().hex[:8]}",
                decision_type="cost_optimization",
                context=cost_context,
                options=optimization_result["optimizations"],
                chosen_option=optimization_result["optimizations"][0] if optimization_result["optimizations"] else None,
                reasoning=reasoning.reasoning_chain,
                confidence=DecisionConfidence.HIGH,
                estimated_cost=optimization_result["total_cost"],
                estimated_benefit=potential_savings,
                tools_used=["finance_optimization"]
            )
            
            await self.shared_memory.add_decision(decision)
            
            # Track performance
            self.cost_savings_achieved += potential_savings
            self.status = AgentStatus.IDLE
            
            return {
                "optimization": optimization_result,
                "potential_savings": potential_savings,
                "decision": decision,
                "reasoning": reasoning,
                "roi": FinancialMetric.calculate_roi(potential_savings, optimization_result["total_cost"])
            }
            
        except Exception as e:
            logger.error(f"Error in cost optimization: {e}")
            self.status = AgentStatus.ERROR
            raise
    
    async def handle_cost_conflict(
        self,
        conflicting_agents: List[str],
        conflict_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle cost-related conflicts with other agents
        """
        try:
            # Initiate autonomous conflict resolution
            resolution = await self.intelligence_engine.resolve_agent_conflict(
                conflicting_agents=[self.agent_id] + conflicting_agents,
                conflict_context=conflict_context,
                conflict_type=ConflictType.COST_OPTIMIZATION
            )
            
            # Analyze financial implications of resolution
            financial_impact = await self._analyze_resolution_cost(resolution, conflict_context)
            
            return {
                "resolution": resolution,
                "financial_impact": financial_impact,
                "savings_achieved": financial_impact.get("net_savings", 0),
                "consensus_reached": resolution.consensus_status.value == "achieved"
            }
            
        except Exception as e:
            logger.error(f"Error handling cost conflict: {e}")
            raise
    
    async def learn_from_financial_outcome(
        self,
        decision_context: Dict[str, Any],
        predicted_cost: float,
        actual_cost: float,
        predicted_savings: float,
        actual_savings: float
    ) -> Dict[str, Any]:
        """
        Learn from financial decision outcomes to improve accuracy
        """
        try:
            # Calculate accuracy scores
            cost_accuracy = 1 - abs(predicted_cost - actual_cost) / max(predicted_cost, actual_cost)
            savings_accuracy = 1 - abs(predicted_savings - actual_savings) / max(predicted_savings, actual_savings) if predicted_savings > 0 else 0
            
            # Overall feedback score
            feedback_score = (cost_accuracy + savings_accuracy) / 2
            
            # Process learning through intelligence engine
            learning_event = await self.intelligence_engine.learn_from_outcome(
                agent_id=self.agent_id,
                decision_context=decision_context,
                predicted_outcome={
                    "cost": predicted_cost,
                    "savings": predicted_savings
                },
                actual_outcome={
                    "cost": actual_cost,
                    "savings": actual_savings
                },
                feedback_score=feedback_score
            )
            
            # Update internal accuracy tracking
            alpha = 0.1  # Learning rate
            self.accuracy_score = (1 - alpha) * self.accuracy_score + alpha * feedback_score
            
            return {
                "learning_event": learning_event,
                "cost_accuracy": cost_accuracy,
                "savings_accuracy": savings_accuracy,
                "updated_accuracy": self.accuracy_score,
                "performance_improvement": feedback_score > 0.7
            }
            
        except Exception as e:
            logger.error(f"Error in learning from financial outcome: {e}")
            raise
    
    async def _perform_financial_analysis(self, context: Dict[str, Any], reasoning) -> Dict[str, Any]:
        """Perform detailed financial impact analysis"""
        
        # Use optimization tool for baseline calculation
        optimization_tool = FinanceOptimizationTool()
        baseline_analysis = await optimization_tool._arun(context)
        
        # Enhanced analysis with market conditions
        market_factors = await self._analyze_market_conditions(context)
        
        # Risk assessment
        risk_analysis = await self._assess_financial_risks(context, baseline_analysis)
        
        return {
            "baseline": baseline_analysis,
            "market_factors": market_factors,
            "risk_analysis": risk_analysis,
            "confidence": reasoning.confidence,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_market_conditions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market conditions affecting costs"""
        
        # Simplified market analysis (in production, would use real market data)
        return {
            "hotel_market": {
                "availability": "medium",
                "pricing_trend": "stable",
                "bulk_discount_available": True
            },
            "transport_market": {
                "capacity": "high",
                "demand": "medium",
                "cost_efficiency": 0.85
            },
            "currency_impact": {
                "exchange_rate_risk": "low",
                "hedging_recommended": False
            }
        }
    
    async def _assess_financial_risks(self, context: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Assess financial risks and scenarios"""
        
        total_cost = baseline["total_cost"]
        
        return {
            "cost_variance": {
                "best_case": total_cost * 0.85,  # 15% better
                "worst_case": total_cost * 1.25,  # 25% worse
                "most_likely": total_cost
            },
            "risk_factors": [
                "Hotel availability constraints",
                "Peak season pricing",
                "Currency fluctuation",
                "Vendor capacity limitations"
            ],
            "mitigation_strategies": [
                "Maintain vendor relationships",
                "Use dynamic pricing models",
                "Implement cost caps",
                "Monitor market trends"
            ],
            "confidence_interval": 0.85
        }
    
    async def _make_financial_decision(self, analysis: Dict[str, Any], reasoning) -> Decision:
        """Make autonomous financial decision based on analysis"""
        
        import uuid
        
        baseline = analysis["baseline"]
        optimizations = baseline["optimizations"]
        
        # Select best optimization option
        best_option = max(optimizations, key=lambda x: x["potential_savings"]) if optimizations else None
        
        decision = Decision(
            decision_id=f"finance_{uuid.uuid4().hex[:8]}",
            decision_type="financial_optimization",
            context=analysis,
            options=optimizations,
            chosen_option=best_option,
            reasoning=reasoning.reasoning_chain,
            confidence=DecisionConfidence.HIGH if reasoning.confidence > 0.8 else DecisionConfidence.MEDIUM,
            estimated_cost=baseline["total_cost"],
            estimated_benefit=best_option["potential_savings"] if best_option else 0,
            tools_used=["finance_optimization"]
        )
        
        return decision
    
    async def _initiate_cost_collaboration(self, context: Dict[str, Any], optimization: Dict[str, Any]):
        """Initiate collaboration with other agents for cost optimization"""
        
        # Identify relevant agents for collaboration
        target_agents = []
        
        # Resource agent for accommodation optimization
        if any(opt["category"] == "accommodation" for opt in optimization["optimizations"]):
            target_agents.append("resource_agent_01")
        
        # Communication agent for passenger management
        if optimization["total_cost"] > 5000:  # High impact disruption
            target_agents.append("communication_agent_01")
        
        # Passenger agent for service optimization
        target_agents.append("passenger_agent_01")
        
        if target_agents:
            collaboration = await self.intelligence_engine.initiate_agent_collaboration(
                initiating_agent=self.agent_id,
                target_agents=target_agents,
                collaboration_context={
                    "type": "cost_optimization",
                    "total_cost": optimization["total_cost"],
                    "optimization_opportunities": optimization["optimizations"],
                    "priority": "high" if optimization["total_cost"] > 10000 else "medium"
                },
                collaboration_type="cost_optimization"
            )
            
            return collaboration
        
        return None
    
    async def _analyze_resolution_cost(self, resolution, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial impact of conflict resolution"""
        
        # Simplified cost analysis of resolution
        base_cost = context.get("estimated_cost", 0)
        
        # Calculate resolution impact
        if resolution.consensus_status.value == "achieved":
            # Successful resolution typically reduces costs through efficiency
            net_savings = base_cost * 0.08  # 8% savings through cooperation
            implementation_cost = base_cost * 0.02  # 2% coordination overhead
        else:
            # Failed resolution increases costs
            net_savings = -base_cost * 0.05  # 5% additional cost
            implementation_cost = base_cost * 0.03  # 3% higher overhead
        
        return {
            "base_cost": base_cost,
            "resolution_impact": net_savings,
            "implementation_cost": implementation_cost,
            "net_savings": net_savings - implementation_cost,
            "roi": FinancialMetric.calculate_roi(net_savings, implementation_cost)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current agent performance metrics"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "decisions_made": self.decisions_made,
            "cost_savings_achieved": self.cost_savings_achieved,
            "accuracy_score": self.accuracy_score,
            "avg_cost_per_decision": self.cost_savings_achieved / max(self.decisions_made, 1),
            "tools_available": len(self.tools)
        }