"""
Enhanced Decision Models for Agentic Intelligence Transparency

This module provides comprehensive data models for capturing, tracking, and displaying
agent decision-making processes with full transparency and reasoning chains.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid


class DecisionType(Enum):
    """Types of decisions agents can make"""
    PREDICTION = "prediction"
    PASSENGER_REBOOKING = "passenger_rebooking"
    RESOURCE_ALLOCATION = "resource_allocation"
    COST_OPTIMIZATION = "cost_optimization"
    COMMUNICATION = "communication"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EMERGENCY_RESPONSE = "emergency_response"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


class ReasoningStep(Enum):
    """Steps in agent reasoning process"""
    DATA_GATHERING = "data_gathering"
    ANALYSIS = "analysis"
    OPTION_GENERATION = "option_generation"
    EVALUATION = "evaluation"
    DECISION = "decision"
    VALIDATION = "validation"
    EXECUTION = "execution"


class DataSourceType(Enum):
    """Types of data sources agents use"""
    WEATHER_API = "weather_api"
    FLIGHT_DATA = "flight_data"
    PASSENGER_PROFILE = "passenger_profile"
    AIRPORT_OPERATIONS = "airport_operations"
    PSS_SYSTEM = "pss_system"
    HOTEL_API = "hotel_api"
    TRANSPORT_API = "transport_api"
    HISTORICAL_DATA = "historical_data"
    ML_MODEL = "ml_model"
    REGULATORY_DATABASE = "regulatory_database"
    COST_DATABASE = "cost_database"
    REAL_TIME_EVENTS = "real_time_events"


class ConfidenceLevel(Enum):
    """Agent confidence levels"""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 21-40%
    MEDIUM = "medium"          # 41-60%
    HIGH = "high"              # 61-80%
    VERY_HIGH = "very_high"    # 81-100%


@dataclass
class DataPoint:
    """Individual data point used in decision"""
    source: DataSourceType
    key: str
    value: Any
    timestamp: datetime
    confidence: float
    relevance_score: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """Complete reasoning chain for a decision"""
    step: ReasoningStep
    description: str
    data_points_used: List[DataPoint]
    logic: str
    confidence_impact: float
    alternatives_considered: List[str]
    time_taken_seconds: float
    outcome: str


@dataclass
class DecisionAlternative:
    """Alternative option considered during decision"""
    alternative_id: str
    description: str
    pros: List[str]
    cons: List[str]
    estimated_cost: Optional[float]
    estimated_time: Optional[float]
    passenger_satisfaction_impact: Optional[float]
    why_not_chosen: str


@dataclass
class DecisionImpact:
    """Impact assessment of a decision"""
    passengers_affected: int
    cost_impact: float
    time_impact: float
    satisfaction_impact: float
    regulatory_compliance: bool
    cascading_effects: List[str]
    risk_assessment: Dict[str, float]


class AgentDecision(BaseModel):
    """Complete agent decision with full transparency"""
    
    # Core Decision Info
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_type: str
    decision_type: DecisionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Decision Content
    decision_summary: str
    detailed_decision: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    
    # Reasoning Process
    reasoning_chain: List[ReasoningChain]
    data_sources_used: List[DataPoint]
    alternatives_considered: List[DecisionAlternative]
    
    # Context
    triggering_event: str
    context: Dict[str, Any]
    constraints: List[str]
    assumptions: List[str]
    
    # Impact & Results
    expected_impact: DecisionImpact
    actual_impact: Optional[DecisionImpact] = None
    
    # Agent Collaboration
    collaborating_agents: List[str] = Field(default_factory=list)
    conflicts_resolved: List[str] = Field(default_factory=list)
    consensus_required: bool = False
    consensus_achieved: bool = False
    
    # Execution
    execution_status: str = "pending"  # pending, executing, completed, failed
    execution_start_time: Optional[datetime] = None
    execution_end_time: Optional[datetime] = None
    execution_notes: str = ""
    
    # Learning & Feedback
    feedback_score: Optional[float] = None
    lessons_learned: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    def to_display_format(self) -> Dict[str, Any]:
        """Convert to format suitable for UI display"""
        return {
            "id": self.decision_id,
            "agent": f"{self.agent_type.title()} Agent",
            "type": self.decision_type.value.replace('_', ' ').title(),
            "summary": self.decision_summary,
            "confidence": {
                "score": self.confidence_score,
                "level": self.confidence_level.value,
                "bar": "█" * int(self.confidence_score * 10),
                "percentage": f"{self.confidence_score:.1%}"
            },
            "reasoning_steps": [
                {
                    "step": step.step.value.replace('_', ' ').title(),
                    "description": step.description,
                    "logic": step.logic,
                    "data_points": len(step.data_points_used),
                    "confidence_impact": step.confidence_impact
                }
                for step in self.reasoning_chain
            ],
            "data_sources": [
                {
                    "source": dp.source.value.replace('_', ' ').title(),
                    "description": dp.description,
                    "value": str(dp.value)[:50] + "..." if len(str(dp.value)) > 50 else str(dp.value),
                    "confidence": dp.confidence,
                    "relevance": dp.relevance_score
                }
                for dp in self.data_sources_used
            ],
            "alternatives": [
                {
                    "description": alt.description,
                    "pros": alt.pros,
                    "cons": alt.cons,
                    "why_not_chosen": alt.why_not_chosen
                }
                for alt in self.alternatives_considered
            ],
            "impact": {
                "passengers": self.expected_impact.passengers_affected,
                "cost": f"£{self.expected_impact.cost_impact:,.2f}",
                "time": f"{self.expected_impact.time_impact:.1f} min",
                "satisfaction": f"{self.expected_impact.satisfaction_impact:.1f}/5",
                "cascading_effects": self.expected_impact.cascading_effects
            },
            "timestamp": self.timestamp.isoformat(),
            "execution_status": self.execution_status
        }


@dataclass
class DecisionStream:
    """Stream of decisions from multiple agents"""
    stream_id: str
    scenario_id: Optional[str]
    start_time: datetime
    decisions: List[AgentDecision] = field(default_factory=list)
    active_agents: List[str] = field(default_factory=list)
    total_passengers_affected: int = 0
    total_cost_impact: float = 0.0
    average_confidence: float = 0.0
    
    def add_decision(self, decision: AgentDecision):
        """Add new decision to stream"""
        self.decisions.append(decision)
        if decision.agent_id not in self.active_agents:
            self.active_agents.append(decision.agent_id)
        
        # Update aggregated metrics
        self.total_passengers_affected += decision.expected_impact.passengers_affected
        self.total_cost_impact += decision.expected_impact.cost_impact
        
        # Recalculate average confidence
        if self.decisions:
            self.average_confidence = sum(d.confidence_score for d in self.decisions) / len(self.decisions)
    
    def get_recent_decisions(self, limit: int = 10) -> List[AgentDecision]:
        """Get most recent decisions"""
        return sorted(self.decisions, key=lambda d: d.timestamp, reverse=True)[:limit]
    
    def get_decisions_by_agent(self, agent_type: str) -> List[AgentDecision]:
        """Get decisions by specific agent type"""
        return [d for d in self.decisions if d.agent_type == agent_type]


class AgentCollaboration(BaseModel):
    """Represents collaboration between multiple agents"""
    
    collaboration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participating_agents: List[str]
    collaboration_type: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    # Collaboration Process
    initial_conflict: str
    negotiation_steps: List[str] = Field(default_factory=list)
    compromise_reached: Optional[str] = None
    final_consensus: Optional[str] = None
    
    # Decisions Involved
    individual_decisions: List[str] = Field(default_factory=list)  # Decision IDs
    collaborative_decision: Optional[str] = None  # Final decision ID
    
    # Outcomes
    success: bool = False
    efficiency_gain: Optional[float] = None
    cost_optimization: Optional[float] = None
    passenger_satisfaction_impact: Optional[float] = None
    
    def to_display_format(self) -> Dict[str, Any]:
        """Convert to format suitable for UI display"""
        duration = (
            (self.end_time - self.start_time).total_seconds() 
            if self.end_time else 
            (datetime.utcnow() - self.start_time).total_seconds()
        )
        
        return {
            "id": self.collaboration_id,
            "agents": [agent.replace('_', ' ').title() for agent in self.participating_agents],
            "type": self.collaboration_type.replace('_', ' ').title(),
            "conflict": self.initial_conflict,
            "status": "Completed" if self.end_time else "In Progress",
            "duration": f"{duration:.1f}s",
            "negotiation_steps": self.negotiation_steps,
            "consensus": self.final_consensus or "Negotiating...",
            "success": self.success,
            "outcomes": {
                "efficiency_gain": f"{self.efficiency_gain:.1%}" if self.efficiency_gain else "TBD",
                "cost_optimization": f"£{self.cost_optimization:,.2f}" if self.cost_optimization else "TBD",
                "satisfaction_impact": f"+{self.passenger_satisfaction_impact:.1f}" if self.passenger_satisfaction_impact else "TBD"
            }
        }


# Utility functions for decision analysis
def calculate_confidence_level(score: float) -> ConfidenceLevel:
    """Calculate confidence level from numerical score"""
    if score <= 0.2:
        return ConfidenceLevel.VERY_LOW
    elif score <= 0.4:
        return ConfidenceLevel.LOW
    elif score <= 0.6:
        return ConfidenceLevel.MEDIUM
    elif score <= 0.8:
        return ConfidenceLevel.HIGH
    else:
        return ConfidenceLevel.VERY_HIGH


def analyze_decision_quality(decision: AgentDecision) -> Dict[str, Any]:
    """Analyze the quality of a decision"""
    analysis = {
        "reasoning_depth": len(decision.reasoning_chain),
        "data_diversity": len(set(dp.source for dp in decision.data_sources_used)),
        "alternatives_considered": len(decision.alternatives_considered),
        "confidence_alignment": _check_confidence_alignment(decision),
        "risk_assessment": _assess_decision_risk(decision),
        "completeness_score": _calculate_completeness(decision)
    }
    
    return analysis


def _check_confidence_alignment(decision: AgentDecision) -> str:
    """Check if confidence aligns with reasoning depth"""
    reasoning_depth = len(decision.reasoning_chain)
    data_points = len(decision.data_sources_used)
    alternatives = len(decision.alternatives_considered)
    
    expected_confidence = min(1.0, (reasoning_depth * 0.15 + data_points * 0.05 + alternatives * 0.1))
    
    if abs(decision.confidence_score - expected_confidence) < 0.2:
        return "Well-aligned"
    elif decision.confidence_score > expected_confidence:
        return "Overconfident"
    else:
        return "Underconfident"


def _assess_decision_risk(decision: AgentDecision) -> str:
    """Assess the risk level of a decision"""
    risk_factors = 0
    
    if decision.confidence_score < 0.6:
        risk_factors += 1
    if decision.expected_impact.passengers_affected > 100:
        risk_factors += 1
    if abs(decision.expected_impact.cost_impact) > 50000:
        risk_factors += 1
    if len(decision.assumptions) > 3:
        risk_factors += 1
    
    if risk_factors == 0:
        return "Low Risk"
    elif risk_factors <= 2:
        return "Medium Risk"
    else:
        return "High Risk"


def _calculate_completeness(decision: AgentDecision) -> float:
    """Calculate how complete a decision is"""
    completeness_factors = [
        1.0 if decision.reasoning_chain else 0.0,
        1.0 if decision.data_sources_used else 0.0,
        1.0 if decision.alternatives_considered else 0.0,
        1.0 if decision.expected_impact else 0.0,
        1.0 if decision.constraints else 0.0,
        1.0 if decision.assumptions else 0.0
    ]
    
    return sum(completeness_factors) / len(completeness_factors)