"""
AI Agent Decision Tracking and Learning System
Advanced system for tracking AI agent decisions, outcomes, and continuous learning
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from uuid import UUID, uuid4
import json
import statistics
from dataclasses import dataclass, asdict

from ..models.comprehensive_models import (
    Flight, PassengerProfile, Booking, Disruption,
    AgentDecision, DecisionType
)


class LearningSignal(str, Enum):
    """Types of learning signals"""
    PASSENGER_FEEDBACK = "passenger_feedback"
    OPERATIONAL_OUTCOME = "operational_outcome"
    COST_EFFICIENCY = "cost_efficiency"
    TIME_EFFICIENCY = "time_efficiency"
    COMPLIANCE_SUCCESS = "compliance_success"
    SYSTEM_PERFORMANCE = "system_performance"


class DecisionOutcome(str, Enum):
    """Decision outcome categories"""
    EXCELLENT = "excellent"      # 90-100% success
    GOOD = "good"               # 75-89% success
    ADEQUATE = "adequate"       # 60-74% success
    POOR = "poor"              # 40-59% success
    FAILED = "failed"          # < 40% success


@dataclass
class LearningData:
    """Structured learning data from decision outcomes"""
    signal_type: LearningSignal
    signal_value: float
    context_factors: Dict[str, Any]
    timestamp: datetime
    confidence: float
    source: str


@dataclass
class DecisionPattern:
    """Pattern identified from decision history"""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    typical_outcome: DecisionOutcome
    success_rate: float
    average_cost: Decimal
    average_satisfaction: float
    occurrence_count: int
    last_seen: datetime


class AgentDecisionTracker:
    """
    Comprehensive AI agent decision tracking and learning system
    """
    
    def __init__(self):
        """Initialize the decision tracker"""
        self.decisions: List[AgentDecision] = []
        self.learning_data: List[LearningData] = []
        self.decision_patterns: List[DecisionPattern] = []
        self.model_performance_metrics: Dict[str, Dict[str, float]] = {}
        
        # Learning configuration
        self.learning_config = {
            'min_decisions_for_pattern': 10,
            'confidence_threshold': 0.7,
            'feedback_decay_days': 30,
            'pattern_update_frequency': 24,  # hours
            'last_pattern_analysis': None
        }
    
    def track_decision(
        self,
        decision: AgentDecision,
        context: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Track a new AI agent decision
        
        Args:
            decision: The agent decision to track
            context: Additional context for decision tracking
            
        Returns:
            Decision ID for future reference
        """
        context = context or {}
        
        # Enhance decision with tracking metadata
        decision.context_factors.update({
            'tracking_started': datetime.now().isoformat(),
            'system_load': context.get('system_load', 'normal'),
            'concurrent_decisions': len([d for d in self.decisions 
                                       if not d.actual_outcome and 
                                       (datetime.now() - d.decision_timestamp).seconds < 3600])
        })
        
        # Store decision
        self.decisions.append(decision)
        
        # Log decision for monitoring
        self._log_decision_start(decision, context)
        
        return decision.id
    
    def update_decision_outcome(
        self,
        decision_id: UUID,
        actual_outcome: Dict[str, Any],
        learning_signals: Optional[List[LearningData]] = None
    ) -> bool:
        """
        Update decision with actual outcome and learning data
        
        Args:
            decision_id: ID of the decision to update
            actual_outcome: Actual outcome of the decision
            learning_signals: Learning signals from the outcome
            
        Returns:
            True if update successful
        """
        # Find decision
        decision = self._find_decision_by_id(decision_id)
        if not decision:
            return False
        
        # Update decision outcome
        decision.actual_outcome = actual_outcome
        
        # Calculate performance metrics
        self._calculate_decision_metrics(decision)
        
        # Process learning signals
        if learning_signals:
            self.learning_data.extend(learning_signals)
            self._process_learning_signals(decision, learning_signals)
        
        # Update model performance tracking
        self._update_model_performance(decision)
        
        # Check if patterns need updating
        self._check_pattern_update_needed()
        
        # Log outcome
        self._log_decision_outcome(decision)
        
        return True
    
    def collect_passenger_feedback(
        self,
        decision_id: UUID,
        passenger_id: UUID,
        feedback_score: float,
        feedback_comments: Optional[str] = None,
        specific_aspects: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Collect passenger feedback for a decision
        
        Args:
            decision_id: Decision ID
            passenger_id: Passenger providing feedback
            feedback_score: Overall satisfaction score (1-5)
            feedback_comments: Optional text feedback
            specific_aspects: Scores for specific aspects
            
        Returns:
            True if feedback recorded
        """
        decision = self._find_decision_by_id(decision_id)
        if not decision:
            return False
        
        # Update decision with feedback
        decision.passenger_feedback = feedback_score
        
        # Create learning signal
        learning_signal = LearningData(
            signal_type=LearningSignal.PASSENGER_FEEDBACK,
            signal_value=feedback_score,
            context_factors={
                'passenger_id': str(passenger_id),
                'comments': feedback_comments,
                'specific_aspects': specific_aspects or {},
                'decision_type': decision.decision_type.value,
                'time_since_decision': (datetime.now() - decision.decision_timestamp).total_seconds() / 3600
            },
            timestamp=datetime.now(),
            confidence=0.9,  # High confidence in direct feedback
            source='passenger_direct'
        )
        
        self.learning_data.append(learning_signal)
        
        # Process feedback for immediate learning
        self._process_passenger_feedback(decision, learning_signal)
        
        return True
    
    def analyze_decision_patterns(
        self,
        lookback_days: int = 30,
        min_occurrences: int = 5
    ) -> List[DecisionPattern]:
        """
        Analyze decision history to identify patterns
        
        Args:
            lookback_days: Days of history to analyze
            min_occurrences: Minimum occurrences to consider a pattern
            
        Returns:
            List of identified patterns
        """
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_decisions = [d for d in self.decisions 
                          if d.decision_timestamp >= cutoff_date and d.actual_outcome]
        
        if len(recent_decisions) < min_occurrences:
            return []
        
        # Group decisions by type and key characteristics
        grouped_decisions = self._group_decisions_for_pattern_analysis(recent_decisions)
        
        patterns = []
        for group_key, decisions_group in grouped_decisions.items():
            if len(decisions_group) >= min_occurrences:
                pattern = self._analyze_decision_group(group_key, decisions_group)
                if pattern:
                    patterns.append(pattern)
        
        # Update stored patterns
        self._update_stored_patterns(patterns)
        
        return patterns
    
    def get_decision_recommendations(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
        passenger_profile: Optional[PassengerProfile] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations for a new decision based on historical patterns
        
        Args:
            decision_type: Type of decision being made
            context: Current decision context
            passenger_profile: Optional passenger profile
            
        Returns:
            Recommendations dictionary
        """
        recommendations = {
            'confidence_factors': [],
            'risk_factors': [],
            'suggested_approaches': [],
            'expected_outcomes': {},
            'similar_cases': []
        }
        
        # Find similar historical decisions
        similar_decisions = self._find_similar_decisions(
            decision_type, context, passenger_profile
        )
        
        if similar_decisions:
            # Analyze outcomes of similar decisions
            outcomes = self._analyze_similar_decision_outcomes(similar_decisions)
            recommendations.update(outcomes)
            
            # Extract success patterns
            success_patterns = self._extract_success_patterns(similar_decisions)
            recommendations['suggested_approaches'] = success_patterns
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(similar_decisions)
            recommendations['risk_factors'] = risk_factors
        
        # Add pattern-based recommendations
        relevant_patterns = self._find_relevant_patterns(decision_type, context)
        if relevant_patterns:
            pattern_recommendations = self._generate_pattern_recommendations(relevant_patterns)
            recommendations.update(pattern_recommendations)
        
        return recommendations
    
    def calculate_agent_performance_metrics(
        self,
        agent_version: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for a specific agent version
        
        Args:
            agent_version: Agent version to analyze
            time_period_days: Time period for analysis
            
        Returns:
            Performance metrics dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        agent_decisions = [
            d for d in self.decisions 
            if d.agent_version == agent_version 
            and d.decision_timestamp >= cutoff_date
            and d.actual_outcome
        ]
        
        if not agent_decisions:
            return {'error': 'No decisions found for agent version'}
        
        metrics = {
            'total_decisions': len(agent_decisions),
            'decision_types': {},
            'overall_performance': {},
            'trend_analysis': {},
            'learning_progress': {}
        }
        
        # Decision type breakdown
        for decision in agent_decisions:
            decision_type = decision.decision_type.value
            if decision_type not in metrics['decision_types']:
                metrics['decision_types'][decision_type] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'avg_quality': 0.0,
                    'success_rate': 0.0
                }
            
            type_metrics = metrics['decision_types'][decision_type]
            type_metrics['count'] += 1
            type_metrics['avg_confidence'] += decision.confidence_score
            
            if decision.passenger_feedback:
                type_metrics['avg_quality'] += decision.passenger_feedback / 5.0
        
        # Calculate averages
        for decision_type in metrics['decision_types']:
            type_metrics = metrics['decision_types'][decision_type]
            if type_metrics['count'] > 0:
                type_metrics['avg_confidence'] /= type_metrics['count']
                type_metrics['avg_quality'] /= type_metrics['count']
                
                # Calculate success rate
                successful_decisions = [
                    d for d in agent_decisions 
                    if d.decision_type.value == decision_type
                    and d.decision_quality_score >= 0.7
                ]
                type_metrics['success_rate'] = len(successful_decisions) / type_metrics['count']
        
        # Overall performance
        quality_scores = [d.decision_quality_score for d in agent_decisions 
                         if d.decision_quality_score is not None]
        if quality_scores:
            metrics['overall_performance'] = {
                'avg_quality_score': statistics.mean(quality_scores),
                'quality_std_dev': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                'quality_trend': self._calculate_quality_trend(agent_decisions),
                'success_rate': len([s for s in quality_scores if s >= 0.7]) / len(quality_scores)
            }
        
        # Learning progress analysis
        metrics['learning_progress'] = self._analyze_learning_progress(agent_decisions)
        
        return metrics
    
    def generate_learning_insights(
        self,
        focus_area: Optional[DecisionType] = None,
        min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate insights for improving agent decision-making
        
        Args:
            focus_area: Optional specific decision type to focus on
            min_confidence: Minimum confidence threshold for insights
            
        Returns:
            Learning insights dictionary
        """
        insights = {
            'key_findings': [],
            'improvement_opportunities': [],
            'successful_patterns': [],
            'failure_patterns': [],
            'recommendations': []
        }
        
        # Filter decisions for analysis
        decisions_to_analyze = [
            d for d in self.decisions 
            if d.actual_outcome 
            and (not focus_area or d.decision_type == focus_area)
        ]
        
        if not decisions_to_analyze:
            return insights
        
        # Identify successful patterns
        successful_decisions = [
            d for d in decisions_to_analyze 
            if d.decision_quality_score and d.decision_quality_score >= 0.8
        ]
        insights['successful_patterns'] = self._extract_success_patterns(successful_decisions)
        
        # Identify failure patterns
        failed_decisions = [
            d for d in decisions_to_analyze 
            if d.decision_quality_score and d.decision_quality_score < 0.5
        ]
        insights['failure_patterns'] = self._extract_failure_patterns(failed_decisions)
        
        # Generate improvement opportunities
        insights['improvement_opportunities'] = self._identify_improvement_opportunities(
            decisions_to_analyze
        )
        
        # Key findings
        insights['key_findings'] = self._generate_key_findings(decisions_to_analyze)
        
        # Recommendations
        insights['recommendations'] = self._generate_improvement_recommendations(
            insights['improvement_opportunities'],
            insights['failure_patterns']
        )
        
        return insights
    
    # Helper methods
    def _find_decision_by_id(self, decision_id: UUID) -> Optional[AgentDecision]:
        """Find decision by ID"""
        for decision in self.decisions:
            if decision.id == decision_id:
                return decision
        return None
    
    def _calculate_decision_metrics(self, decision: AgentDecision):
        """Calculate performance metrics for a decision"""
        if not decision.actual_outcome:
            return
        
        # Calculate effectiveness metrics
        effectiveness_metrics = {}
        
        # Time efficiency
        if 'completion_time' in decision.actual_outcome:
            expected_time = decision.expected_impact.get('estimated_time', 3600)  # 1 hour default
            actual_time = decision.actual_outcome['completion_time']
            effectiveness_metrics['time_efficiency'] = min(1.0, expected_time / actual_time)
        
        # Cost effectiveness
        if 'total_cost' in decision.actual_outcome:
            expected_cost = decision.expected_impact.get('estimated_cost', 100.0)
            actual_cost = decision.actual_outcome['total_cost']
            effectiveness_metrics['cost_effectiveness'] = min(2.0, expected_cost / actual_cost)
        
        # Update decision metrics
        decision.success_metrics.update(effectiveness_metrics)
    
    def _process_learning_signals(
        self, 
        decision: AgentDecision, 
        signals: List[LearningData]
    ):
        """Process learning signals from decision outcome"""
        for signal in signals:
            # Update decision-specific learning
            if signal.signal_type == LearningSignal.PASSENGER_FEEDBACK:
                decision.passenger_feedback = signal.signal_value
            elif signal.signal_type == LearningSignal.OPERATIONAL_OUTCOME:
                decision.operational_effectiveness = signal.signal_value
            elif signal.signal_type == LearningSignal.COST_EFFICIENCY:
                decision.cost_effectiveness = signal.signal_value
            
            # Add to decision learning points
            learning_point = f"{signal.signal_type.value}: {signal.signal_value:.2f}"
            if learning_point not in decision.learning_points:
                decision.learning_points.append(learning_point)
    
    def _process_passenger_feedback(
        self, 
        decision: AgentDecision, 
        feedback_signal: LearningData
    ):
        """Process passenger feedback for immediate learning"""
        feedback_score = feedback_signal.signal_value
        
        # Analyze feedback context
        context_factors = feedback_signal.context_factors
        
        # Extract actionable insights
        if feedback_score < 3.0:  # Poor feedback
            insight = f"Low satisfaction ({feedback_score:.1f}) for {decision.decision_type.value}"
            if 'comments' in context_factors and context_factors['comments']:
                insight += f": {context_factors['comments'][:100]}"
            
            decision.learning_points.append(insight)
        elif feedback_score >= 4.0:  # Good feedback
            success_factor = f"High satisfaction ({feedback_score:.1f}) achieved"
            decision.learning_points.append(success_factor)
    
    def _update_model_performance(self, decision: AgentDecision):
        """Update model performance tracking"""
        model_key = f"{decision.agent_version}_{decision.model_version}"
        
        if model_key not in self.model_performance_metrics:
            self.model_performance_metrics[model_key] = {
                'decisions_count': 0,
                'avg_confidence': 0.0,
                'avg_quality': 0.0,
                'success_rate': 0.0,
                'last_updated': datetime.now()
            }
        
        metrics = self.model_performance_metrics[model_key]
        metrics['decisions_count'] += 1
        
        # Update running averages
        n = metrics['decisions_count']
        prev_avg_conf = metrics['avg_confidence']
        prev_avg_qual = metrics['avg_quality']
        
        metrics['avg_confidence'] = ((n - 1) * prev_avg_conf + decision.confidence_score) / n
        
        if decision.decision_quality_score:
            metrics['avg_quality'] = ((n - 1) * prev_avg_qual + decision.decision_quality_score) / n
        
        # Update success rate
        successful_decisions = [
            d for d in self.decisions 
            if f"{d.agent_version}_{d.model_version}" == model_key
            and d.decision_quality_score and d.decision_quality_score >= 0.7
        ]
        metrics['success_rate'] = len(successful_decisions) / metrics['decisions_count']
        metrics['last_updated'] = datetime.now()
    
    def _group_decisions_for_pattern_analysis(
        self, 
        decisions: List[AgentDecision]
    ) -> Dict[str, List[AgentDecision]]:
        """Group decisions for pattern analysis"""
        groups = {}
        
        for decision in decisions:
            # Create grouping key based on decision type and key context
            key_factors = [
                decision.decision_type.value,
                str(len(decision.alternatives_considered)),
                'high_confidence' if decision.confidence_score > 0.8 else 'low_confidence'
            ]
            
            # Add context-specific factors
            if 'passenger_loyalty_tier' in decision.context_factors:
                key_factors.append(decision.context_factors['passenger_loyalty_tier'])
            
            group_key = '|'.join(key_factors)
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(decision)
        
        return groups
    
    def _analyze_decision_group(
        self, 
        group_key: str, 
        decisions: List[AgentDecision]
    ) -> Optional[DecisionPattern]:
        """Analyze a group of similar decisions to identify patterns"""
        if len(decisions) < self.learning_config['min_decisions_for_pattern']:
            return None
        
        # Calculate group statistics
        quality_scores = [d.decision_quality_score for d in decisions 
                         if d.decision_quality_score is not None]
        
        if not quality_scores:
            return None
        
        avg_quality = statistics.mean(quality_scores)
        success_rate = len([s for s in quality_scores if s >= 0.7]) / len(quality_scores)
        
        # Determine typical outcome
        if avg_quality >= 0.9:
            typical_outcome = DecisionOutcome.EXCELLENT
        elif avg_quality >= 0.75:
            typical_outcome = DecisionOutcome.GOOD
        elif avg_quality >= 0.6:
            typical_outcome = DecisionOutcome.ADEQUATE
        elif avg_quality >= 0.4:
            typical_outcome = DecisionOutcome.POOR
        else:
            typical_outcome = DecisionOutcome.FAILED
        
        # Extract common conditions
        conditions = self._extract_common_conditions(decisions)
        
        # Calculate average cost
        costs = []
        for decision in decisions:
            if decision.actual_outcome and 'total_cost' in decision.actual_outcome:
                costs.append(Decimal(str(decision.actual_outcome['total_cost'])))
        
        avg_cost = statistics.mean(costs) if costs else Decimal('0')
        
        pattern = DecisionPattern(
            pattern_id=f"pattern_{hash(group_key)}",
            pattern_type=group_key.split('|')[0],  # Decision type
            conditions=conditions,
            typical_outcome=typical_outcome,
            success_rate=success_rate,
            average_cost=avg_cost,
            average_satisfaction=avg_quality,
            occurrence_count=len(decisions),
            last_seen=max(d.decision_timestamp for d in decisions)
        )
        
        return pattern
    
    def _extract_common_conditions(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """Extract common conditions from a group of decisions"""
        conditions = {}
        
        # Find common context factors
        all_factors = {}
        for decision in decisions:
            for key, value in decision.context_factors.items():
                if key not in all_factors:
                    all_factors[key] = []
                all_factors[key].append(value)
        
        # Identify factors with consistent values
        for key, values in all_factors.items():
            unique_values = list(set(str(v) for v in values))
            if len(unique_values) == 1:  # All same value
                conditions[key] = unique_values[0]
            elif len(unique_values) <= 3 and len(values) >= 5:  # Limited variation
                # Calculate mode
                value_counts = {}
                for v in values:
                    str_v = str(v)
                    value_counts[str_v] = value_counts.get(str_v, 0) + 1
                
                mode_value = max(value_counts, key=value_counts.get)
                if value_counts[mode_value] / len(values) >= 0.6:  # 60% or more
                    conditions[key] = mode_value
        
        return conditions
    
    def _find_similar_decisions(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
        passenger_profile: Optional[PassengerProfile]
    ) -> List[AgentDecision]:
        """Find historically similar decisions"""
        similar_decisions = []
        
        for decision in self.decisions:
            if (decision.decision_type == decision_type and 
                decision.actual_outcome and
                self._calculate_context_similarity(decision.context_factors, context) > 0.6):
                
                similar_decisions.append(decision)
        
        # Sort by similarity and recency
        similar_decisions.sort(
            key=lambda d: (
                self._calculate_context_similarity(d.context_factors, context),
                (datetime.now() - d.decision_timestamp).days
            ),
            reverse=True
        )
        
        return similar_decisions[:20]  # Return top 20 most similar
    
    def _calculate_context_similarity(
        self, 
        context1: Dict[str, Any], 
        context2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matching_values = 0
        for key in common_keys:
            if str(context1[key]) == str(context2[key]):
                matching_values += 1
        
        return matching_values / len(common_keys)
    
    def _extract_success_patterns(
        self, 
        successful_decisions: List[AgentDecision]
    ) -> List[str]:
        """Extract patterns from successful decisions"""
        patterns = []
        
        if not successful_decisions:
            return patterns
        
        # Analyze common characteristics
        high_confidence_decisions = [
            d for d in successful_decisions if d.confidence_score > 0.8
        ]
        
        if len(high_confidence_decisions) / len(successful_decisions) > 0.7:
            patterns.append("High confidence (>0.8) correlates with success")
        
        # Analyze decision speed
        quick_decisions = [
            d for d in successful_decisions 
            if len(d.reasoning_steps) <= 3
        ]
        
        if len(quick_decisions) / len(successful_decisions) > 0.6:
            patterns.append("Simpler reasoning paths often yield better outcomes")
        
        return patterns
    
    def _extract_failure_patterns(
        self, 
        failed_decisions: List[AgentDecision]
    ) -> List[str]:
        """Extract patterns from failed decisions"""
        patterns = []
        
        if not failed_decisions:
            return patterns
        
        # Analyze common failure characteristics
        low_confidence_decisions = [
            d for d in failed_decisions if d.confidence_score < 0.5
        ]
        
        if len(low_confidence_decisions) / len(failed_decisions) > 0.5:
            patterns.append("Low confidence (<0.5) often indicates poor outcomes")
        
        # Analyze over-complex reasoning
        complex_decisions = [
            d for d in failed_decisions 
            if len(d.reasoning_steps) > 10
        ]
        
        if len(complex_decisions) / len(failed_decisions) > 0.4:
            patterns.append("Over-complex reasoning may lead to poor decisions")
        
        return patterns
    
    def _check_pattern_update_needed(self):
        """Check if patterns need to be updated"""
        last_update = self.learning_config.get('last_pattern_analysis')
        update_frequency = self.learning_config['pattern_update_frequency']
        
        if (not last_update or 
            (datetime.now() - last_update).total_seconds() / 3600 > update_frequency):
            
            self.analyze_decision_patterns()
            self.learning_config['last_pattern_analysis'] = datetime.now()
    
    def _log_decision_start(self, decision: AgentDecision, context: Dict[str, Any]):
        """Log decision start for monitoring"""
        # This would integrate with logging system
        pass
    
    def _log_decision_outcome(self, decision: AgentDecision):
        """Log decision outcome for monitoring"""
        # This would integrate with logging system
        pass
    
    def _calculate_quality_trend(self, decisions: List[AgentDecision]) -> str:
        """Calculate quality trend over time"""
        if len(decisions) < 5:
            return "insufficient_data"
        
        # Sort by timestamp
        decisions.sort(key=lambda d: d.decision_timestamp)
        
        # Calculate trend in quality scores
        quality_scores = [d.decision_quality_score for d in decisions[-10:] 
                         if d.decision_quality_score is not None]
        
        if len(quality_scores) < 3:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = quality_scores[:len(quality_scores)//2]
        second_half = quality_scores[len(quality_scores)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg + 0.1:
            return "improving"
        elif second_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _analyze_learning_progress(self, decisions: List[AgentDecision]) -> Dict[str, Any]:
        """Analyze learning progress over time"""
        return {
            'learning_points_generated': sum(len(d.learning_points) for d in decisions),
            'avg_learning_points_per_decision': statistics.mean([len(d.learning_points) for d in decisions]),
            'most_common_learning_themes': self._extract_learning_themes(decisions)
        }
    
    def _extract_learning_themes(self, decisions: List[AgentDecision]) -> List[str]:
        """Extract common themes from learning points"""
        all_points = []
        for decision in decisions:
            all_points.extend(decision.learning_points)
        
        # Simple theme extraction (would be enhanced with NLP)
        themes = {}
        for point in all_points:
            words = point.lower().split()
            for word in words:
                if len(word) > 4:  # Filter short words
                    themes[word] = themes.get(word, 0) + 1
        
        # Return top themes
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:5]]
    
    def _update_stored_patterns(self, new_patterns: List[DecisionPattern]):
        """Update stored patterns with new analysis"""
        # Update existing patterns or add new ones
        pattern_dict = {p.pattern_id: p for p in new_patterns}
        
        for i, existing_pattern in enumerate(self.decision_patterns):
            if existing_pattern.pattern_id in pattern_dict:
                # Update existing pattern
                self.decision_patterns[i] = pattern_dict[existing_pattern.pattern_id]
                del pattern_dict[existing_pattern.pattern_id]
        
        # Add new patterns
        self.decision_patterns.extend(pattern_dict.values())
    
    def _find_relevant_patterns(
        self, 
        decision_type: DecisionType, 
        context: Dict[str, Any]
    ) -> List[DecisionPattern]:
        """Find patterns relevant to current decision context"""
        relevant_patterns = []
        
        for pattern in self.decision_patterns:
            if pattern.pattern_type == decision_type.value:
                # Check if context matches pattern conditions
                context_match = 0
                total_conditions = len(pattern.conditions)
                
                if total_conditions == 0:
                    continue
                
                for condition_key, condition_value in pattern.conditions.items():
                    if condition_key in context and str(context[condition_key]) == str(condition_value):
                        context_match += 1
                
                match_ratio = context_match / total_conditions
                if match_ratio >= 0.5:  # At least 50% match
                    relevant_patterns.append(pattern)
        
        return relevant_patterns
    
    def _generate_pattern_recommendations(
        self, 
        patterns: List[DecisionPattern]
    ) -> Dict[str, Any]:
        """Generate recommendations based on patterns"""
        recommendations = {
            'confidence_boost': [],
            'risk_warnings': [],
            'best_practices': []
        }
        
        for pattern in patterns:
            if pattern.success_rate > 0.8:
                recommendations['confidence_boost'].append(
                    f"Similar decisions have {pattern.success_rate:.1%} success rate"
                )
                recommendations['best_practices'].append(
                    f"Pattern shows {pattern.typical_outcome.value} outcomes"
                )
            elif pattern.success_rate < 0.5:
                recommendations['risk_warnings'].append(
                    f"Similar decisions have only {pattern.success_rate:.1%} success rate"
                )
        
        return recommendations
    
    def _analyze_similar_decision_outcomes(
        self, 
        similar_decisions: List[AgentDecision]
    ) -> Dict[str, Any]:
        """Analyze outcomes of similar decisions"""
        outcomes = {
            'expected_success_rate': 0.0,
            'expected_satisfaction': 0.0,
            'expected_cost_range': (0, 0),
            'common_challenges': []
        }
        
        if not similar_decisions:
            return outcomes
        
        quality_scores = [d.decision_quality_score for d in similar_decisions 
                         if d.decision_quality_score is not None]
        
        if quality_scores:
            outcomes['expected_success_rate'] = len([s for s in quality_scores if s >= 0.7]) / len(quality_scores)
            outcomes['expected_satisfaction'] = statistics.mean(quality_scores)
        
        # Extract cost information
        costs = []
        for decision in similar_decisions:
            if decision.actual_outcome and 'total_cost' in decision.actual_outcome:
                costs.append(decision.actual_outcome['total_cost'])
        
        if costs:
            outcomes['expected_cost_range'] = (min(costs), max(costs))
        
        return outcomes
    
    def _identify_improvement_opportunities(
        self, 
        decisions: List[AgentDecision]
    ) -> List[str]:
        """Identify opportunities for improvement"""
        opportunities = []
        
        # Analyze confidence vs outcome correlation
        high_conf_low_outcome = [
            d for d in decisions 
            if d.confidence_score > 0.8 and d.decision_quality_score and d.decision_quality_score < 0.6
        ]
        
        if len(high_conf_low_outcome) > len(decisions) * 0.1:  # More than 10%
            opportunities.append("Overconfidence: high confidence doesn't guarantee good outcomes")
        
        # Analyze reasoning complexity
        complex_poor_outcomes = [
            d for d in decisions 
            if len(d.reasoning_steps) > 8 and d.decision_quality_score and d.decision_quality_score < 0.6
        ]
        
        if len(complex_poor_outcomes) > len(decisions) * 0.15:
            opportunities.append("Simplify reasoning: complex reasoning paths may be counterproductive")
        
        return opportunities
    
    def _generate_key_findings(self, decisions: List[AgentDecision]) -> List[str]:
        """Generate key findings from decision analysis"""
        findings = []
        
        if len(decisions) < 10:
            return ["Insufficient data for meaningful analysis"]
        
        # Overall performance finding
        quality_scores = [d.decision_quality_score for d in decisions 
                         if d.decision_quality_score is not None]
        
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            findings.append(f"Average decision quality: {avg_quality:.2f}")
            
            if avg_quality > 0.8:
                findings.append("Overall performance is excellent")
            elif avg_quality > 0.6:
                findings.append("Overall performance is good with room for improvement")
            else:
                findings.append("Performance needs significant improvement")
        
        return findings
    
    def _generate_improvement_recommendations(
        self, 
        opportunities: List[str], 
        failure_patterns: List[str]
    ) -> List[str]:
        """Generate specific recommendations for improvement"""
        recommendations = []
        
        if "overconfidence" in str(opportunities).lower():
            recommendations.append("Implement confidence calibration techniques")
            recommendations.append("Add uncertainty quantification to decision process")
        
        if "complex reasoning" in str(opportunities).lower():
            recommendations.append("Implement reasoning path optimization")
            recommendations.append("Add decision complexity metrics and limits")
        
        if failure_patterns:
            recommendations.append("Review and address identified failure patterns")
            recommendations.append("Implement pattern-based early warning system")
        
        return recommendations