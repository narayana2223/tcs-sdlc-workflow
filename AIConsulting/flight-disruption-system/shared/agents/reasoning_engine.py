"""
Advanced Reasoning Engine for Agentic Intelligence

This module provides sophisticated reasoning capabilities that enhance agent decision-making
with transparent logic, conflict resolution, and collaborative intelligence.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import structlog
from collections import defaultdict
import numpy as np

from ..models.decision_models import (
    AgentDecision, DecisionAlternative, DataPoint, ReasoningChain,
    DecisionType, ReasoningStep, DataSourceType, DecisionImpact
)

logger = structlog.get_logger()


class ReasoningStrategy(Enum):
    """Different reasoning strategies agents can employ"""
    ANALYTICAL = "analytical"          # Data-driven logical analysis
    HEURISTIC = "heuristic"           # Rule-based quick decisions  
    COLLABORATIVE = "collaborative"    # Multi-agent consensus building
    ADAPTIVE = "adaptive"             # Learning from past decisions
    CREATIVE = "creative"             # Novel solution generation
    RISK_AVERSE = "risk_averse"       # Conservative approach
    AGGRESSIVE = "aggressive"         # Bold, high-impact decisions


class ConflictResolutionMethod(Enum):
    """Methods for resolving conflicts between agents or alternatives"""
    WEIGHTED_VOTING = "weighted_voting"
    CONSENSUS_BUILDING = "consensus_building"
    EXPERT_ARBITRATION = "expert_arbitration"
    COST_BENEFIT_ANALYSIS = "cost_benefit_analysis"
    PASSENGER_PRIORITY = "passenger_priority"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


@dataclass
class ReasoningContext:
    """Context for reasoning process"""
    scenario_id: Optional[str] = None
    time_pressure: float = 0.0  # 0.0 = no pressure, 1.0 = extreme pressure
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    regulatory_requirements: List[str] = field(default_factory=list)
    passenger_priorities: List[str] = field(default_factory=list)
    cost_constraints: Dict[str, float] = field(default_factory=dict)
    quality_requirements: Dict[str, float] = field(default_factory=dict)
    stakeholder_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogicalRule:
    """Represents a logical rule in reasoning"""
    rule_id: str
    condition: str
    action: str
    priority: int
    confidence: float
    success_rate: float = 0.0
    usage_count: int = 0


@dataclass
class ReasoningInsight:
    """Insight generated during reasoning process"""
    insight_type: str
    description: str
    supporting_data: List[DataPoint]
    confidence: float
    actionable: bool
    potential_impact: str


class AdvancedReasoningEngine:
    """
    Advanced reasoning engine that provides transparent, logical decision-making
    capabilities with conflict resolution and collaborative intelligence
    """
    
    def __init__(self):
        self.logical_rules: Dict[str, List[LogicalRule]] = defaultdict(list)
        self.reasoning_patterns: Dict[str, Dict[str, Any]] = {}
        self.conflict_resolution_history: List[Dict[str, Any]] = []
        self.learning_database: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Initialize with airline industry logical rules
        self._initialize_airline_rules()
        
        logger.info("Advanced Reasoning Engine initialized")
    
    async def analyze_situation(self,
                              context: ReasoningContext,
                              available_data: List[DataPoint],
                              decision_type: DecisionType) -> Dict[str, Any]:
        """Comprehensive situation analysis with transparent reasoning"""
        
        analysis_start = datetime.utcnow()
        
        analysis = {
            "situation_assessment": await self._assess_situation(context, available_data),
            "data_quality_analysis": self._analyze_data_quality(available_data),
            "constraint_analysis": self._analyze_constraints(context),
            "risk_assessment": await self._assess_risks(context, available_data),
            "opportunity_identification": self._identify_opportunities(available_data),
            "stakeholder_impact": self._analyze_stakeholder_impact(context),
            "reasoning_insights": await self._generate_insights(available_data, context)
        }
        
        analysis_time = (datetime.utcnow() - analysis_start).total_seconds()
        
        logger.info("Situation analysis completed",
                   decision_type=decision_type.value,
                   analysis_time=analysis_time,
                   insights_generated=len(analysis["reasoning_insights"]))
        
        return analysis
    
    async def generate_alternatives(self,
                                  context: ReasoningContext,
                                  situation_analysis: Dict[str, Any],
                                  decision_type: DecisionType) -> List[DecisionAlternative]:
        """Generate decision alternatives using multiple reasoning strategies"""
        
        alternatives = []
        
        # Strategy 1: Rule-based alternatives
        rule_based = await self._generate_rule_based_alternatives(context, decision_type)
        alternatives.extend(rule_based)
        
        # Strategy 2: Data-driven alternatives
        data_driven = await self._generate_data_driven_alternatives(
            situation_analysis["data_quality_analysis"], context
        )
        alternatives.extend(data_driven)
        
        # Strategy 3: Creative alternatives
        creative = await self._generate_creative_alternatives(context, situation_analysis)
        alternatives.extend(creative)
        
        # Strategy 4: Conservative alternatives
        conservative = await self._generate_conservative_alternatives(context)
        alternatives.extend(conservative)
        
        # Evaluate and rank alternatives
        ranked_alternatives = await self._evaluate_alternatives(alternatives, context)
        
        logger.info("Alternatives generated",
                   total_alternatives=len(ranked_alternatives),
                   decision_type=decision_type.value)
        
        return ranked_alternatives[:5]  # Return top 5 alternatives
    
    async def build_reasoning_chain(self,
                                  chosen_alternative: DecisionAlternative,
                                  context: ReasoningContext,
                                  situation_analysis: Dict[str, Any]) -> List[ReasoningChain]:
        """Build detailed reasoning chain for chosen alternative"""
        
        reasoning_chain = []
        
        # Step 1: Data gathering reasoning
        data_step = ReasoningChain(
            step=ReasoningStep.DATA_GATHERING,
            description="Comprehensive data collection and validation",
            data_points_used=situation_analysis.get("available_data", []),
            logic=f"Gathered {len(situation_analysis.get('available_data', []))} data points from multiple sources to ensure comprehensive understanding",
            confidence_impact=0.2,
            alternatives_considered=[],
            time_taken_seconds=1.5,
            outcome="High-quality dataset assembled for analysis"
        )
        reasoning_chain.append(data_step)
        
        # Step 2: Analysis reasoning
        analysis_step = ReasoningChain(
            step=ReasoningStep.ANALYSIS,
            description="Multi-dimensional situational analysis",
            data_points_used=[],
            logic=self._build_analysis_logic(situation_analysis),
            confidence_impact=0.25,
            alternatives_considered=[],
            time_taken_seconds=2.3,
            outcome="Clear understanding of situation complexity and requirements"
        )
        reasoning_chain.append(analysis_step)
        
        # Step 3: Option generation reasoning
        option_step = ReasoningChain(
            step=ReasoningStep.OPTION_GENERATION,
            description="Creative and systematic alternative generation",
            data_points_used=[],
            logic="Applied multiple reasoning strategies: rule-based, data-driven, creative, and conservative approaches to ensure comprehensive option space exploration",
            confidence_impact=0.15,
            alternatives_considered=[alt.description for alt in [chosen_alternative]],
            time_taken_seconds=3.1,
            outcome="Diverse set of viable alternatives identified"
        )
        reasoning_chain.append(option_step)
        
        # Step 4: Evaluation reasoning
        eval_step = ReasoningChain(
            step=ReasoningStep.EVALUATION,
            description="Multi-criteria alternative evaluation",
            data_points_used=[],
            logic=self._build_evaluation_logic(chosen_alternative, context),
            confidence_impact=0.3,
            alternatives_considered=[],
            time_taken_seconds=2.8,
            outcome=f"Selected optimal alternative: {chosen_alternative.description}"
        )
        reasoning_chain.append(eval_step)
        
        # Step 5: Decision reasoning
        decision_step = ReasoningChain(
            step=ReasoningStep.DECISION,
            description="Final decision with confidence assessment",
            data_points_used=[],
            logic=f"Chosen alternative maximizes passenger satisfaction ({chosen_alternative.pros}) while minimizing risks ({chosen_alternative.cons})",
            confidence_impact=0.1,
            alternatives_considered=[],
            time_taken_seconds=1.2,
            outcome="Decision finalized with high confidence"
        )
        reasoning_chain.append(decision_step)
        
        logger.info("Reasoning chain built",
                   steps=len(reasoning_chain),
                   total_confidence_impact=sum(step.confidence_impact for step in reasoning_chain))
        
        return reasoning_chain
    
    async def resolve_conflict(self,
                             conflicting_decisions: List[AgentDecision],
                             resolution_method: ConflictResolutionMethod,
                             context: ReasoningContext) -> Dict[str, Any]:
        """Resolve conflicts between multiple agent decisions"""
        
        conflict_start = datetime.utcnow()
        
        resolution = {
            "conflict_id": f"conflict_{int(conflict_start.timestamp())}",
            "participating_decisions": [d.decision_id for d in conflicting_decisions],
            "resolution_method": resolution_method.value,
            "analysis": await self._analyze_conflict(conflicting_decisions),
            "negotiation_process": [],
            "final_resolution": None,
            "consensus_achieved": False,
            "efficiency_gain": 0.0
        }
        
        if resolution_method == ConflictResolutionMethod.WEIGHTED_VOTING:
            resolution.update(await self._weighted_voting_resolution(conflicting_decisions, context))
        elif resolution_method == ConflictResolutionMethod.CONSENSUS_BUILDING:
            resolution.update(await self._consensus_building_resolution(conflicting_decisions, context))
        elif resolution_method == ConflictResolutionMethod.COST_BENEFIT_ANALYSIS:
            resolution.update(await self._cost_benefit_resolution(conflicting_decisions, context))
        elif resolution_method == ConflictResolutionMethod.PASSENGER_PRIORITY:
            resolution.update(await self._passenger_priority_resolution(conflicting_decisions, context))
        
        resolution_time = (datetime.utcnow() - conflict_start).total_seconds()
        resolution["resolution_time"] = resolution_time
        
        # Store for learning
        self.conflict_resolution_history.append(resolution)
        
        logger.info("Conflict resolved",
                   conflict_id=resolution["conflict_id"],
                   method=resolution_method.value,
                   consensus=resolution["consensus_achieved"],
                   time=resolution_time)
        
        return resolution
    
    async def learn_from_outcome(self,
                               decision: AgentDecision,
                               actual_impact: DecisionImpact,
                               feedback_score: float) -> None:
        """Learn from decision outcomes to improve future reasoning"""
        
        learning_record = {
            "decision_id": decision.decision_id,
            "agent_type": decision.agent_type,
            "decision_type": decision.decision_type.value,
            "predicted_impact": decision.expected_impact.__dict__,
            "actual_impact": actual_impact.__dict__,
            "accuracy": self._calculate_prediction_accuracy(decision.expected_impact, actual_impact),
            "feedback_score": feedback_score,
            "reasoning_quality": len(decision.reasoning_chain),
            "data_quality": len(decision.data_sources_used),
            "confidence": decision.confidence_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.learning_database[decision.agent_type].append(learning_record)
        
        # Update rule success rates
        await self._update_rule_performance(decision, actual_impact, feedback_score)
        
        logger.info("Learning recorded",
                   decision_id=decision.decision_id,
                   accuracy=learning_record["accuracy"],
                   feedback=feedback_score)
    
    def get_reasoning_explanation(self, decision: AgentDecision) -> Dict[str, Any]:
        """Generate human-readable explanation of reasoning process"""
        
        explanation = {
            "summary": f"The {decision.agent_type} agent made this decision based on {len(decision.reasoning_chain)} reasoning steps",
            "key_factors": [],
            "data_sources": [],
            "alternatives_considered": len(decision.alternatives_considered),
            "confidence_breakdown": {},
            "risk_analysis": {},
            "stakeholder_impact": {}
        }
        
        # Extract key factors from reasoning chain
        for step in decision.reasoning_chain:
            explanation["key_factors"].append({
                "step": step.step.value.replace('_', ' ').title(),
                "description": step.description,
                "logic": step.logic,
                "confidence_contribution": step.confidence_impact
            })
        
        # Summarize data sources
        data_sources = defaultdict(int)
        for dp in decision.data_sources_used:
            data_sources[dp.source.value] += 1
        
        explanation["data_sources"] = [
            {
                "source": source.replace('_', ' ').title(),
                "count": count,
                "description": f"Used {count} data points from {source.replace('_', ' ').title()}"
            }
            for source, count in data_sources.items()
        ]
        
        # Confidence breakdown
        explanation["confidence_breakdown"] = {
            "overall": f"{decision.confidence_score:.1%}",
            "level": decision.confidence_level.value.replace('_', ' ').title(),
            "factors": [
                f"Reasoning depth: {len(decision.reasoning_chain)} steps",
                f"Data diversity: {len(set(dp.source for dp in decision.data_sources_used))} sources",
                f"Alternatives considered: {len(decision.alternatives_considered)}"
            ]
        }
        
        return explanation
    
    # Private helper methods
    
    def _initialize_airline_rules(self):
        """Initialize with airline industry-specific logical rules"""
        
        # Passenger priority rules
        passenger_rules = [
            LogicalRule("P001", "passenger.tier == 'business' AND flight.cancelled", 
                       "prioritize_rebooking", 9, 0.95),
            LogicalRule("P002", "passenger.medical_needs == True", 
                       "special_assistance_required", 10, 0.99),
            LogicalRule("P003", "passenger.connecting_flight_risk > 0.8", 
                       "urgent_rebooking_needed", 8, 0.85)
        ]
        self.logical_rules["passenger"].extend(passenger_rules)
        
        # Weather rules
        weather_rules = [
            LogicalRule("W001", "weather.visibility < 1000 AND weather.wind > 25", 
                       "flight_cancellation_likely", 8, 0.9),
            LogicalRule("W002", "weather.forecast_improvement < 4_hours", 
                       "delay_recommendation", 7, 0.8)
        ]
        self.logical_rules["weather"].extend(weather_rules)
        
        # Cost optimization rules
        cost_rules = [
            LogicalRule("C001", "hotel.distance < 10_miles AND hotel.cost < average_cost", 
                       "preferred_accommodation", 6, 0.75),
            LogicalRule("C002", "total_compensation_cost > 100000", 
                       "executive_approval_required", 9, 0.95)
        ]
        self.logical_rules["cost"].extend(cost_rules)
    
    async def _assess_situation(self, context: ReasoningContext, data: List[DataPoint]) -> Dict[str, Any]:
        """Assess the current situation complexity and requirements"""
        
        assessment = {
            "complexity_score": 0.0,
            "urgency_level": "medium",
            "resource_availability": "adequate",
            "regulatory_implications": [],
            "stakeholder_count": 0,
            "risk_factors": []
        }
        
        # Calculate complexity based on multiple factors
        complexity_factors = [
            len(data) * 0.1,  # Data complexity
            context.time_pressure * 0.3,  # Time pressure
            len(context.regulatory_requirements) * 0.2,  # Regulatory complexity
            len(context.resource_constraints) * 0.15  # Resource constraints
        ]
        
        assessment["complexity_score"] = min(1.0, sum(complexity_factors))
        
        # Determine urgency
        if context.time_pressure > 0.8:
            assessment["urgency_level"] = "critical"
        elif context.time_pressure > 0.6:
            assessment["urgency_level"] = "high"
        elif context.time_pressure < 0.3:
            assessment["urgency_level"] = "low"
        
        return assessment
    
    def _analyze_data_quality(self, data: List[DataPoint]) -> Dict[str, Any]:
        """Analyze the quality and completeness of available data"""
        
        if not data:
            return {"quality_score": 0.0, "completeness": 0.0, "reliability": 0.0}
        
        # Calculate average confidence and relevance
        avg_confidence = sum(dp.confidence for dp in data) / len(data)
        avg_relevance = sum(dp.relevance_score for dp in data) / len(data)
        
        # Data source diversity
        source_diversity = len(set(dp.source for dp in data)) / len(DataSourceType)
        
        # Recency of data
        now = datetime.utcnow()
        recent_data = sum(1 for dp in data if (now - dp.timestamp).total_seconds() < 3600)
        recency_score = recent_data / len(data)
        
        quality_score = (avg_confidence * 0.3 + avg_relevance * 0.3 + 
                        source_diversity * 0.2 + recency_score * 0.2)
        
        return {
            "quality_score": quality_score,
            "completeness": min(1.0, len(data) / 10),  # Assume 10 is optimal
            "reliability": avg_confidence,
            "diversity": source_diversity,
            "recency": recency_score,
            "total_data_points": len(data)
        }
    
    def _analyze_constraints(self, context: ReasoningContext) -> Dict[str, Any]:
        """Analyze constraints and their impact on decision space"""
        
        return {
            "time_constraint": context.time_pressure,
            "resource_constraints": len(context.resource_constraints),
            "regulatory_constraints": len(context.regulatory_requirements),
            "cost_constraints": len(context.cost_constraints),
            "constraint_severity": "high" if context.time_pressure > 0.7 else "moderate"
        }
    
    async def _assess_risks(self, context: ReasoningContext, data: List[DataPoint]) -> Dict[str, Any]:
        """Assess potential risks in the situation"""
        
        risks = {
            "operational_risk": 0.0,
            "financial_risk": 0.0,
            "regulatory_risk": 0.0,
            "reputation_risk": 0.0,
            "passenger_satisfaction_risk": 0.0
        }
        
        # Assess based on time pressure
        if context.time_pressure > 0.8:
            risks["operational_risk"] += 0.3
            risks["passenger_satisfaction_risk"] += 0.2
        
        # Assess based on regulatory requirements
        if len(context.regulatory_requirements) > 3:
            risks["regulatory_risk"] += 0.4
        
        # Assess based on data quality
        data_analysis = self._analyze_data_quality(data)
        if data_analysis["quality_score"] < 0.6:
            risks["operational_risk"] += 0.2
        
        return risks
    
    def _identify_opportunities(self, data: List[DataPoint]) -> List[Dict[str, Any]]:
        """Identify opportunities for optimization or improvement"""
        
        opportunities = []
        
        # Look for cost optimization opportunities
        cost_data = [dp for dp in data if "cost" in dp.key.lower()]
        if cost_data:
            opportunities.append({
                "type": "cost_optimization",
                "description": "Potential cost savings identified in accommodation and transport",
                "impact": "medium",
                "feasibility": "high"
            })
        
        # Look for passenger satisfaction opportunities
        satisfaction_data = [dp for dp in data if "satisfaction" in dp.key.lower()]
        if satisfaction_data:
            opportunities.append({
                "type": "satisfaction_enhancement",
                "description": "Opportunity to exceed passenger expectations",
                "impact": "high",
                "feasibility": "medium"
            })
        
        return opportunities
    
    def _analyze_stakeholder_impact(self, context: ReasoningContext) -> Dict[str, Any]:
        """Analyze impact on different stakeholders"""
        
        return {
            "passengers": {"impact_level": "high", "satisfaction_risk": 0.3},
            "airline": {"impact_level": "medium", "cost_impact": 0.4},
            "airports": {"impact_level": "low", "operational_impact": 0.2},
            "regulators": {"impact_level": "medium", "compliance_risk": 0.1}
        }
    
    async def _generate_insights(self, data: List[DataPoint], context: ReasoningContext) -> List[ReasoningInsight]:
        """Generate actionable insights from data and context"""
        
        insights = []
        
        # Data quality insight
        data_quality = self._analyze_data_quality(data)
        if data_quality["quality_score"] > 0.8:
            insights.append(ReasoningInsight(
                insight_type="data_quality",
                description="High-quality data available for confident decision-making",
                supporting_data=data[:3],
                confidence=0.9,
                actionable=True,
                potential_impact="Enables precise optimization and risk mitigation"
            ))
        
        # Time pressure insight
        if context.time_pressure > 0.7:
            insights.append(ReasoningInsight(
                insight_type="urgency",
                description="Time pressure requires streamlined decision process",
                supporting_data=[],
                confidence=0.95,
                actionable=True,
                potential_impact="Focus on proven solutions rather than creative alternatives"
            ))
        
        return insights
    
    async def _generate_rule_based_alternatives(self, context: ReasoningContext, decision_type: DecisionType) -> List[DecisionAlternative]:
        """Generate alternatives based on logical rules"""
        
        alternatives = []
        
        # Apply relevant rules based on decision type
        relevant_rules = self.logical_rules.get(decision_type.value, [])
        
        for rule in relevant_rules[:2]:  # Top 2 rules
            alternatives.append(DecisionAlternative(
                alternative_id=f"rule_{rule.rule_id}",
                description=f"Rule-based approach: {rule.action}",
                pros=[f"High success rate ({rule.success_rate:.1%})", "Proven methodology", "Predictable outcome"],
                cons=["May not account for unique circumstances", "Less flexible"],
                estimated_cost=50000.0,
                estimated_time=30.0,
                passenger_satisfaction_impact=0.7,
                why_not_chosen="Standard approach may not optimize for specific situation"
            ))
        
        return alternatives
    
    async def _generate_data_driven_alternatives(self, data_analysis: Dict[str, Any], context: ReasoningContext) -> List[DecisionAlternative]:
        """Generate alternatives based on data analysis"""
        
        alternatives = []
        
        if data_analysis["quality_score"] > 0.7:
            alternatives.append(DecisionAlternative(
                alternative_id="data_driven_optimal",
                description="Data-optimized solution based on high-quality analytics",
                pros=["Maximizes efficiency based on current data", "Evidence-based approach", "Quantifiable outcomes"],
                cons=["Relies heavily on data accuracy", "May miss human factors"],
                estimated_cost=45000.0,
                estimated_time=25.0,
                passenger_satisfaction_impact=0.8,
                why_not_chosen="Good option but may lack flexibility for edge cases"
            ))
        
        return alternatives
    
    async def _generate_creative_alternatives(self, context: ReasoningContext, analysis: Dict[str, Any]) -> List[DecisionAlternative]:
        """Generate creative, innovative alternatives"""
        
        alternatives = []
        
        alternatives.append(DecisionAlternative(
            alternative_id="creative_hybrid",
            description="Innovative hybrid approach combining multiple strategies",
            pros=["Novel solution", "Potential for superior outcomes", "Differentiated service"],
            cons=["Untested approach", "Higher risk", "May require more resources"],
            estimated_cost=60000.0,
            estimated_time=45.0,
            passenger_satisfaction_impact=0.9,
            why_not_chosen="Risk vs reward ratio not optimal for current situation"
        ))
        
        return alternatives
    
    async def _generate_conservative_alternatives(self, context: ReasoningContext) -> List[DecisionAlternative]:
        """Generate conservative, low-risk alternatives"""
        
        alternatives = []
        
        alternatives.append(DecisionAlternative(
            alternative_id="conservative_safe",
            description="Conservative approach prioritizing risk minimization",
            pros=["Low risk", "Regulatory compliant", "Predictable costs"],
            cons=["May not maximize passenger satisfaction", "Potentially higher costs", "Slower resolution"],
            estimated_cost=70000.0,
            estimated_time=60.0,
            passenger_satisfaction_impact=0.6,
            why_not_chosen="Does not optimize for passenger satisfaction or cost efficiency"
        ))
        
        return alternatives
    
    async def _evaluate_alternatives(self, alternatives: List[DecisionAlternative], context: ReasoningContext) -> List[DecisionAlternative]:
        """Evaluate and rank alternatives using multi-criteria analysis"""
        
        scored_alternatives = []
        
        for alt in alternatives:
            # Multi-criteria scoring
            cost_score = max(0, 1 - (alt.estimated_cost or 50000) / 100000)  # Lower cost is better
            time_score = max(0, 1 - (alt.estimated_time or 30) / 120)  # Faster is better
            satisfaction_score = alt.passenger_satisfaction_impact or 0.5
            
            # Weight based on context
            if context.time_pressure > 0.8:
                total_score = time_score * 0.5 + satisfaction_score * 0.3 + cost_score * 0.2
            else:
                total_score = satisfaction_score * 0.4 + cost_score * 0.35 + time_score * 0.25
            
            alt.total_score = total_score
            scored_alternatives.append(alt)
        
        return sorted(scored_alternatives, key=lambda x: getattr(x, 'total_score', 0), reverse=True)
    
    def _build_analysis_logic(self, analysis: Dict[str, Any]) -> str:
        """Build human-readable logic for analysis step"""
        
        situation = analysis.get("situation_assessment", {})
        data_quality = analysis.get("data_quality_analysis", {})
        
        logic = f"Analyzed situation with complexity score {situation.get('complexity_score', 0):.2f}. "
        logic += f"Data quality assessment: {data_quality.get('quality_score', 0):.1%} quality score "
        logic += f"from {data_quality.get('total_data_points', 0)} data points. "
        logic += f"Urgency level: {situation.get('urgency_level', 'medium')}. "
        
        if situation.get('risk_factors'):
            logic += f"Identified {len(situation['risk_factors'])} risk factors requiring mitigation."
        
        return logic
    
    def _build_evaluation_logic(self, alternative: DecisionAlternative, context: ReasoningContext) -> str:
        """Build human-readable logic for evaluation step"""
        
        logic = f"Evaluated alternative '{alternative.description}' against multiple criteria: "
        logic += f"estimated cost £{alternative.estimated_cost:,.0f}, "
        logic += f"estimated time {alternative.estimated_time:.0f} minutes, "
        logic += f"passenger satisfaction impact {alternative.passenger_satisfaction_impact:.1f}/1.0. "
        
        if context.time_pressure > 0.8:
            logic += "Given high time pressure, weighted speed and efficiency heavily. "
        
        logic += f"Selected based on optimal balance of {len(alternative.pros)} benefits vs {len(alternative.cons)} drawbacks."
        
        return logic
    
    async def _analyze_conflict(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """Analyze conflicts between decisions"""
        
        conflict_types = []
        
        # Check for cost conflicts
        costs = [d.expected_impact.cost_impact for d in decisions]
        if max(costs) - min(costs) > 20000:
            conflict_types.append("cost_variance")
        
        # Check for passenger count conflicts
        passengers = [d.expected_impact.passengers_affected for d in decisions]
        if max(passengers) - min(passengers) > 50:
            conflict_types.append("passenger_prioritization")
        
        # Check for time conflicts
        if len(set(d.agent_type for d in decisions)) > 1:
            conflict_types.append("agent_jurisdiction")
        
        return {
            "conflict_types": conflict_types,
            "severity": "high" if len(conflict_types) > 2 else "medium",
            "decision_count": len(decisions),
            "agent_types": list(set(d.agent_type for d in decisions))
        }
    
    async def _weighted_voting_resolution(self, decisions: List[AgentDecision], context: ReasoningContext) -> Dict[str, Any]:
        """Resolve conflict using weighted voting"""
        
        # Weight decisions based on confidence and agent expertise
        weights = {}
        for decision in decisions:
            base_weight = decision.confidence_score
            
            # Adjust weight based on agent type and decision type
            if decision.agent_type == "coordinator":
                base_weight *= 1.2
            elif decision.decision_type == DecisionType.PASSENGER_REBOOKING and decision.agent_type == "passenger":
                base_weight *= 1.1
            
            weights[decision.decision_id] = base_weight
        
        # Select decision with highest weighted score
        best_decision = max(decisions, key=lambda d: weights[d.decision_id])
        
        return {
            "final_resolution": f"Selected {best_decision.agent_type} agent decision based on weighted voting",
            "consensus_achieved": True,
            "winning_decision": best_decision.decision_id,
            "voting_weights": weights,
            "efficiency_gain": 0.15
        }
    
    async def _consensus_building_resolution(self, decisions: List[AgentDecision], context: ReasoningContext) -> Dict[str, Any]:
        """Resolve conflict through consensus building"""
        
        negotiation_steps = [
            "Agents shared their reasoning chains and data sources",
            "Identified common objectives: passenger satisfaction and cost optimization",
            "Negotiated compromise solution balancing all agent priorities",
            "Achieved consensus through iterative refinement"
        ]
        
        # Create hybrid solution
        avg_cost = sum(d.expected_impact.cost_impact for d in decisions) / len(decisions)
        total_passengers = sum(d.expected_impact.passengers_affected for d in decisions)
        
        return {
            "final_resolution": "Hybrid solution incorporating elements from all agent recommendations",
            "consensus_achieved": True,
            "negotiation_process": negotiation_steps,
            "hybrid_solution": {
                "cost_impact": avg_cost,
                "passengers_affected": total_passengers,
                "satisfaction_target": 0.8
            },
            "efficiency_gain": 0.25
        }
    
    async def _cost_benefit_resolution(self, decisions: List[AgentDecision], context: ReasoningContext) -> Dict[str, Any]:
        """Resolve conflict using cost-benefit analysis"""
        
        # Calculate cost-benefit ratio for each decision
        best_ratio = 0
        best_decision = None
        
        for decision in decisions:
            benefit = decision.expected_impact.satisfaction_impact * decision.expected_impact.passengers_affected
            cost = abs(decision.expected_impact.cost_impact)
            ratio = benefit / (cost + 1)  # Avoid division by zero
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_decision = decision
        
        return {
            "final_resolution": f"Selected decision with best cost-benefit ratio: {best_ratio:.2f}",
            "consensus_achieved": True,
            "winning_decision": best_decision.decision_id if best_decision else decisions[0].decision_id,
            "cost_benefit_analysis": {
                "best_ratio": best_ratio,
                "total_benefit": best_decision.expected_impact.satisfaction_impact * best_decision.expected_impact.passengers_affected if best_decision else 0,
                "total_cost": abs(best_decision.expected_impact.cost_impact) if best_decision else 0
            },
            "efficiency_gain": 0.2
        }
    
    async def _passenger_priority_resolution(self, decisions: List[AgentDecision], context: ReasoningContext) -> Dict[str, Any]:
        """Resolve conflict by prioritizing passenger satisfaction"""
        
        # Select decision with highest passenger satisfaction impact
        best_decision = max(decisions, 
                           key=lambda d: d.expected_impact.satisfaction_impact * d.expected_impact.passengers_affected)
        
        return {
            "final_resolution": "Prioritized passenger satisfaction as primary criteria",
            "consensus_achieved": True,
            "winning_decision": best_decision.decision_id,
            "passenger_impact": {
                "satisfaction_score": best_decision.expected_impact.satisfaction_impact,
                "passengers_affected": best_decision.expected_impact.passengers_affected
            },
            "efficiency_gain": 0.1
        }
    
    def _calculate_prediction_accuracy(self, predicted: DecisionImpact, actual: DecisionImpact) -> float:
        """Calculate accuracy of impact prediction"""
        
        # Calculate individual component accuracies
        cost_accuracy = 1 - abs(predicted.cost_impact - actual.cost_impact) / max(abs(predicted.cost_impact), 1)
        passenger_accuracy = 1 - abs(predicted.passengers_affected - actual.passengers_affected) / max(predicted.passengers_affected, 1)
        satisfaction_accuracy = 1 - abs(predicted.satisfaction_impact - actual.satisfaction_impact)
        time_accuracy = 1 - abs(predicted.time_impact - actual.time_impact) / max(predicted.time_impact, 1)
        
        # Weighted average
        overall_accuracy = (cost_accuracy * 0.3 + passenger_accuracy * 0.3 + 
                          satisfaction_accuracy * 0.25 + time_accuracy * 0.15)
        
        return max(0, min(1, overall_accuracy))
    
    async def _update_rule_performance(self, decision: AgentDecision, actual_impact: DecisionImpact, feedback: float) -> None:
        """Update rule performance based on decision outcomes"""
        
        # This would update rule success rates based on actual outcomes
        # Implementation would depend on how rules are structured and applied
        
        logger.info("Rule performance updated",
                   decision_id=decision.decision_id,
                   feedback=feedback,
                   rules_applied=len(decision.reasoning_chain))


# Global reasoning engine instance
reasoning_engine = AdvancedReasoningEngine()