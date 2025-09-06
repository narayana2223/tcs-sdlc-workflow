"""
Enhanced Decision Logger for Agentic Intelligence Transparency

This module captures, tracks, and streams agent decisions with complete reasoning chains,
data source attribution, and real-time collaboration monitoring for executive oversight.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from contextlib import asynccontextmanager
import structlog
from collections import defaultdict, deque

from ..models.decision_models import (
    AgentDecision, DecisionStream, AgentCollaboration,
    DataPoint, ReasoningChain, DecisionAlternative,
    DecisionImpact, DecisionType, ReasoningStep,
    DataSourceType, calculate_confidence_level
)

logger = structlog.get_logger()


class DecisionLogger:
    """
    Comprehensive decision logging system that captures agent reasoning
    processes with full transparency and real-time streaming capabilities
    """
    
    def __init__(self, max_decisions_in_memory: int = 1000):
        self.max_decisions_in_memory = max_decisions_in_memory
        
        # In-memory storage for fast access
        self.decision_streams: Dict[str, DecisionStream] = {}
        self.active_decisions: Dict[str, AgentDecision] = {}
        self.collaborations: Dict[str, AgentCollaboration] = {}
        
        # Real-time subscribers for streaming
        self.decision_subscribers: List[Callable] = []
        self.collaboration_subscribers: List[Callable] = []
        
        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_decisions": 0,
            "average_confidence": 0.0,
            "success_rate": 0.0,
            "average_execution_time": 0.0,
            "cost_savings": 0.0,
            "passenger_satisfaction": 0.0
        })
        
        # Decision quality metrics
        self.quality_metrics = {
            "reasoning_depth_avg": 0.0,
            "data_diversity_avg": 0.0,
            "alternatives_avg": 0.0,
            "confidence_alignment_rate": 0.0
        }
        
        logger.info("DecisionLogger initialized", max_memory=max_decisions_in_memory)
    
    async def start_decision(self, 
                           agent_id: str, 
                           agent_type: str,
                           decision_type: DecisionType,
                           triggering_event: str,
                           context: Dict[str, Any] = None) -> str:
        """Start tracking a new decision process"""
        
        decision = AgentDecision(
            agent_id=agent_id,
            agent_type=agent_type,
            decision_type=decision_type,
            triggering_event=triggering_event,
            decision_summary="Decision in progress...",
            detailed_decision="Analyzing situation and gathering data...",
            confidence_score=0.0,
            confidence_level=calculate_confidence_level(0.0),
            reasoning_chain=[],
            data_sources_used=[],
            alternatives_considered=[],
            context=context or {},
            constraints=[],
            assumptions=[],
            expected_impact=DecisionImpact(
                passengers_affected=0,
                cost_impact=0.0,
                time_impact=0.0,
                satisfaction_impact=0.0,
                regulatory_compliance=True,
                cascading_effects=[],
                risk_assessment={}
            )
        )
        
        self.active_decisions[decision.decision_id] = decision
        
        await self._notify_decision_subscribers("decision_started", decision)
        
        logger.info("Decision tracking started", 
                   decision_id=decision.decision_id,
                   agent_id=agent_id,
                   decision_type=decision_type.value)
        
        return decision.decision_id
    
    async def add_reasoning_step(self,
                               decision_id: str,
                               step: ReasoningStep,
                               description: str,
                               logic: str,
                               data_points: List[DataPoint] = None,
                               alternatives: List[str] = None,
                               confidence_impact: float = 0.0) -> None:
        """Add a reasoning step to an active decision"""
        
        if decision_id not in self.active_decisions:
            logger.error("Decision not found", decision_id=decision_id)
            return
        
        decision = self.active_decisions[decision_id]
        
        reasoning_step = ReasoningChain(
            step=step,
            description=description,
            data_points_used=data_points or [],
            logic=logic,
            confidence_impact=confidence_impact,
            alternatives_considered=alternatives or [],
            time_taken_seconds=0.0,  # Will be calculated
            outcome=""  # Will be filled when step completes
        )
        
        # Calculate time since last step or decision start
        if decision.reasoning_chain:
            last_timestamp = decision.reasoning_chain[-1].timestamp if hasattr(decision.reasoning_chain[-1], 'timestamp') else decision.timestamp
        else:
            last_timestamp = decision.timestamp
        
        current_time = datetime.utcnow()
        reasoning_step.time_taken_seconds = (current_time - last_timestamp).total_seconds()
        
        decision.reasoning_chain.append(reasoning_step)
        
        # Add data points to decision's data sources
        if data_points:
            decision.data_sources_used.extend(data_points)
        
        # Update confidence based on reasoning depth and data quality
        decision.confidence_score = self._calculate_dynamic_confidence(decision)
        decision.confidence_level = calculate_confidence_level(decision.confidence_score)
        
        await self._notify_decision_subscribers("reasoning_step_added", decision)
        
        logger.info("Reasoning step added",
                   decision_id=decision_id,
                   step=step.value,
                   confidence=decision.confidence_score)
    
    async def add_data_point(self,
                           decision_id: str,
                           source: DataSourceType,
                           key: str,
                           value: Any,
                           description: str,
                           confidence: float = 1.0,
                           relevance_score: float = 1.0,
                           metadata: Dict[str, Any] = None) -> None:
        """Add a data point used in decision making"""
        
        if decision_id not in self.active_decisions:
            return
        
        data_point = DataPoint(
            source=source,
            key=key,
            value=value,
            timestamp=datetime.utcnow(),
            confidence=confidence,
            relevance_score=relevance_score,
            description=description,
            metadata=metadata or {}
        )
        
        decision = self.active_decisions[decision_id]
        decision.data_sources_used.append(data_point)
        
        # Update confidence based on data quality
        decision.confidence_score = self._calculate_dynamic_confidence(decision)
        decision.confidence_level = calculate_confidence_level(decision.confidence_score)
        
        await self._notify_decision_subscribers("data_point_added", decision)
        
        logger.info("Data point added",
                   decision_id=decision_id,
                   source=source.value,
                   key=key,
                   confidence=confidence)
    
    async def add_alternative(self,
                            decision_id: str,
                            alternative: DecisionAlternative) -> None:
        """Add an alternative considered during decision making"""
        
        if decision_id not in self.active_decisions:
            return
        
        decision = self.active_decisions[decision_id]
        decision.alternatives_considered.append(alternative)
        
        # Update confidence - more alternatives usually increase confidence
        decision.confidence_score = self._calculate_dynamic_confidence(decision)
        decision.confidence_level = calculate_confidence_level(decision.confidence_score)
        
        await self._notify_decision_subscribers("alternative_added", decision)
        
        logger.info("Alternative added",
                   decision_id=decision_id,
                   alternative_id=alternative.alternative_id)
    
    async def complete_decision(self,
                              decision_id: str,
                              final_decision: str,
                              detailed_explanation: str,
                              expected_impact: DecisionImpact,
                              constraints: List[str] = None,
                              assumptions: List[str] = None) -> AgentDecision:
        """Complete and finalize a decision"""
        
        if decision_id not in self.active_decisions:
            logger.error("Decision not found for completion", decision_id=decision_id)
            return None
        
        decision = self.active_decisions[decision_id]
        
        # Finalize decision details
        decision.decision_summary = final_decision
        decision.detailed_decision = detailed_explanation
        decision.expected_impact = expected_impact
        decision.constraints = constraints or []
        decision.assumptions = assumptions or []
        decision.execution_status = "pending"
        
        # Final confidence calculation
        decision.confidence_score = self._calculate_dynamic_confidence(decision)
        decision.confidence_level = calculate_confidence_level(decision.confidence_score)
        
        # Move from active to completed
        completed_decision = self.active_decisions.pop(decision_id)
        
        # Add to appropriate decision stream
        stream_id = f"{decision.agent_type}_{datetime.utcnow().strftime('%Y%m%d')}"
        if stream_id not in self.decision_streams:
            self.decision_streams[stream_id] = DecisionStream(
                stream_id=stream_id,
                start_time=datetime.utcnow(),
                scenario_id=decision.context.get("scenario_id")
            )
        
        self.decision_streams[stream_id].add_decision(completed_decision)
        
        # Update agent performance metrics
        await self._update_agent_performance(completed_decision)
        
        await self._notify_decision_subscribers("decision_completed", completed_decision)
        
        logger.info("Decision completed",
                   decision_id=decision_id,
                   agent_id=decision.agent_id,
                   confidence=decision.confidence_score,
                   passengers_affected=expected_impact.passengers_affected)
        
        return completed_decision
    
    async def start_collaboration(self,
                                agent_ids: List[str],
                                collaboration_type: str,
                                initial_conflict: str) -> str:
        """Start tracking agent collaboration"""
        
        collaboration = AgentCollaboration(
            participating_agents=agent_ids,
            collaboration_type=collaboration_type,
            initial_conflict=initial_conflict
        )
        
        self.collaborations[collaboration.collaboration_id] = collaboration
        
        await self._notify_collaboration_subscribers("collaboration_started", collaboration)
        
        logger.info("Collaboration started",
                   collaboration_id=collaboration.collaboration_id,
                   agents=agent_ids,
                   conflict=initial_conflict)
        
        return collaboration.collaboration_id
    
    async def add_negotiation_step(self,
                                 collaboration_id: str,
                                 step_description: str) -> None:
        """Add a negotiation step to collaboration"""
        
        if collaboration_id not in self.collaborations:
            return
        
        collaboration = self.collaborations[collaboration_id]
        collaboration.negotiation_steps.append(step_description)
        
        await self._notify_collaboration_subscribers("negotiation_step", collaboration)
        
        logger.info("Negotiation step added",
                   collaboration_id=collaboration_id,
                   step=step_description)
    
    async def complete_collaboration(self,
                                   collaboration_id: str,
                                   final_consensus: str,
                                   success: bool,
                                   collaborative_decision_id: str = None) -> None:
        """Complete a collaboration"""
        
        if collaboration_id not in self.collaborations:
            return
        
        collaboration = self.collaborations[collaboration_id]
        collaboration.end_time = datetime.utcnow()
        collaboration.final_consensus = final_consensus
        collaboration.success = success
        collaboration.collaborative_decision = collaborative_decision_id
        
        await self._notify_collaboration_subscribers("collaboration_completed", collaboration)
        
        logger.info("Collaboration completed",
                   collaboration_id=collaboration_id,
                   success=success,
                   consensus=final_consensus)
    
    def subscribe_to_decisions(self, callback: Callable) -> None:
        """Subscribe to real-time decision updates"""
        self.decision_subscribers.append(callback)
        logger.info("Decision subscriber added", callback=callback.__name__)
    
    def subscribe_to_collaborations(self, callback: Callable) -> None:
        """Subscribe to real-time collaboration updates"""
        self.collaboration_subscribers.append(callback)
        logger.info("Collaboration subscriber added", callback=callback.__name__)
    
    def get_recent_decisions(self, limit: int = 20) -> List[AgentDecision]:
        """Get recent decisions across all streams"""
        all_decisions = []
        for stream in self.decision_streams.values():
            all_decisions.extend(stream.decisions)
        
        return sorted(all_decisions, key=lambda d: d.timestamp, reverse=True)[:limit]
    
    def get_agent_performance(self, agent_id: str = None) -> Dict[str, Any]:
        """Get performance metrics for specific agent or all agents"""
        if agent_id:
            return self.agent_performance.get(agent_id, {})
        return dict(self.agent_performance)
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get overall system decision analytics"""
        total_decisions = sum(len(stream.decisions) for stream in self.decision_streams.values())
        
        if total_decisions == 0:
            return {"total_decisions": 0}
        
        all_decisions = self.get_recent_decisions(1000)  # Last 1000 decisions
        
        return {
            "total_decisions": total_decisions,
            "average_confidence": sum(d.confidence_score for d in all_decisions) / len(all_decisions),
            "decision_types": self._get_decision_type_distribution(all_decisions),
            "agent_activity": self._get_agent_activity_stats(all_decisions),
            "quality_metrics": self.quality_metrics,
            "recent_activity": len([d for d in all_decisions if d.timestamp > datetime.utcnow() - timedelta(hours=1)])
        }
    
    async def _notify_decision_subscribers(self, event_type: str, decision: AgentDecision) -> None:
        """Notify all decision subscribers"""
        for callback in self.decision_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, decision.to_display_format())
                else:
                    callback(event_type, decision.to_display_format())
            except Exception as e:
                logger.error("Error notifying decision subscriber", 
                           callback=callback.__name__, error=str(e))
    
    async def _notify_collaboration_subscribers(self, event_type: str, collaboration: AgentCollaboration) -> None:
        """Notify all collaboration subscribers"""
        for callback in self.collaboration_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, collaboration.to_display_format())
                else:
                    callback(event_type, collaboration.to_display_format())
            except Exception as e:
                logger.error("Error notifying collaboration subscriber",
                           callback=callback.__name__, error=str(e))
    
    def _calculate_dynamic_confidence(self, decision: AgentDecision) -> float:
        """Calculate confidence based on reasoning depth and data quality"""
        base_confidence = 0.3
        
        # Reasoning depth contribution (max 0.3)
        reasoning_bonus = min(0.3, len(decision.reasoning_chain) * 0.05)
        
        # Data source diversity contribution (max 0.2)
        data_sources = set(dp.source for dp in decision.data_sources_used)
        data_bonus = min(0.2, len(data_sources) * 0.04)
        
        # Data quality contribution (max 0.15)
        if decision.data_sources_used:
            avg_data_confidence = sum(dp.confidence for dp in decision.data_sources_used) / len(decision.data_sources_used)
            data_quality_bonus = avg_data_confidence * 0.15
        else:
            data_quality_bonus = 0.0
        
        # Alternatives consideration contribution (max 0.05)
        alternatives_bonus = min(0.05, len(decision.alternatives_considered) * 0.02)
        
        total_confidence = base_confidence + reasoning_bonus + data_bonus + data_quality_bonus + alternatives_bonus
        
        return min(1.0, total_confidence)
    
    async def _update_agent_performance(self, decision: AgentDecision) -> None:
        """Update performance metrics for an agent"""
        agent_stats = self.agent_performance[decision.agent_id]
        
        # Update counters
        agent_stats["total_decisions"] += 1
        
        # Update averages (simple moving average)
        n = agent_stats["total_decisions"]
        agent_stats["average_confidence"] = (
            (agent_stats["average_confidence"] * (n - 1) + decision.confidence_score) / n
        )
        
        # Update execution time when available
        if decision.execution_start_time and decision.execution_end_time:
            execution_time = (decision.execution_end_time - decision.execution_start_time).total_seconds()
            agent_stats["average_execution_time"] = (
                (agent_stats["average_execution_time"] * (n - 1) + execution_time) / n
            )
        
        # Update cost impact
        agent_stats["cost_savings"] += decision.expected_impact.cost_impact
        
        logger.debug("Agent performance updated",
                    agent_id=decision.agent_id,
                    total_decisions=n,
                    avg_confidence=agent_stats["average_confidence"])
    
    def _get_decision_type_distribution(self, decisions: List[AgentDecision]) -> Dict[str, int]:
        """Get distribution of decision types"""
        distribution = defaultdict(int)
        for decision in decisions:
            distribution[decision.decision_type.value] += 1
        return dict(distribution)
    
    def _get_agent_activity_stats(self, decisions: List[AgentDecision]) -> Dict[str, int]:
        """Get activity statistics by agent"""
        activity = defaultdict(int)
        for decision in decisions:
            activity[decision.agent_type] += 1
        return dict(activity)


# Global decision logger instance
decision_logger = DecisionLogger()

# Convenience functions for easy access
async def log_decision_start(agent_id: str, agent_type: str, decision_type: DecisionType, 
                           triggering_event: str, context: Dict[str, Any] = None) -> str:
    """Start logging a decision"""
    return await decision_logger.start_decision(agent_id, agent_type, decision_type, 
                                               triggering_event, context)

async def log_reasoning_step(decision_id: str, step: ReasoningStep, description: str, 
                           logic: str, **kwargs) -> None:
    """Log a reasoning step"""
    await decision_logger.add_reasoning_step(decision_id, step, description, logic, **kwargs)

async def log_data_point(decision_id: str, source: DataSourceType, key: str, 
                        value: Any, description: str, **kwargs) -> None:
    """Log a data point"""
    await decision_logger.add_data_point(decision_id, source, key, value, description, **kwargs)