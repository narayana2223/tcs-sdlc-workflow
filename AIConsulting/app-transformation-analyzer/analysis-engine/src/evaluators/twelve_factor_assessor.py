"""
Main orchestrator for 12-factor assessment that coordinates evaluation, gap analysis,
and recommendation generation to produce comprehensive assessment results.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.assessment import (
    TwelveFactorAssessment, FactorEvaluation, Gap, Recommendation,
    FactorScore, TWELVE_FACTOR_DEFINITIONS
)
from ..analyzers.repository_analyzer import RepositoryAnalysisResult
from .factor_evaluator import TwelveFactorEvaluator
from .gap_analyzer import GapAnalyzer
from .recommendation_engine import RecommendationEngine
from ..utils.logging_config import log_performance, set_analysis_context

logger = logging.getLogger(__name__)


class TwelveFactorAssessorError(Exception):
    """Custom exception for 12-factor assessment errors."""
    pass


class TwelveFactorAssessor:
    """Main orchestrator for complete 12-factor assessment."""
    
    def __init__(self):
        """Initialize the assessor with all required components."""
        self.factor_evaluator = TwelveFactorEvaluator()
        self.gap_analyzer = GapAnalyzer()
        self.recommendation_engine = RecommendationEngine()
    
    @log_performance
    def assess_repository(
        self, 
        analysis_result: RepositoryAnalysisResult,
        assessment_id: Optional[str] = None
    ) -> TwelveFactorAssessment:
        """
        Perform complete 12-factor assessment of a repository.
        
        Args:
            analysis_result: Complete repository analysis results
            assessment_id: Optional assessment identifier
            
        Returns:
            Complete 12-factor assessment
        """
        try:
            if not assessment_id:
                assessment_id = f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Set analysis context for logging
            set_analysis_context(
                assessment_id=assessment_id,
                repo_url=analysis_result.repository_info.get('remote_url', 'unknown')
            )
            
            logger.info(f"Starting 12-factor assessment - ID: {assessment_id}")
            
            # Step 1: Evaluate all factors
            logger.info("Evaluating 12-factor compliance")
            factor_evaluations = self.factor_evaluator.evaluate_all_factors(analysis_result)
            
            # Step 2: Calculate overall scores
            overall_score, weighted_score = self.factor_evaluator.calculate_overall_score(factor_evaluations)
            grade = self.factor_evaluator.assign_grade(weighted_score)
            
            # Step 3: Analyze gaps
            logger.info("Analyzing implementation gaps")
            gaps = self.gap_analyzer.analyze_gaps(factor_evaluations, analysis_result)
            
            # Step 4: Generate recommendations
            logger.info("Generating recommendations")
            recommendations = self.recommendation_engine.generate_recommendations(
                gaps, factor_evaluations, analysis_result
            )
            
            # Step 5: Calculate confidence and coverage
            confidence = self._calculate_confidence(factor_evaluations)
            coverage = self._calculate_coverage(factor_evaluations)
            
            # Create assessment result
            assessment = TwelveFactorAssessment(
                repository_url=analysis_result.repository_info.get('remote_url', 'unknown'),
                assessment_id=assessment_id,
                timestamp=datetime.now().isoformat(),
                factor_evaluations=factor_evaluations,
                overall_score=overall_score,
                weighted_score=weighted_score,
                grade=grade,
                gaps=gaps,
                recommendations=recommendations,
                confidence=confidence,
                coverage=coverage
            )
            
            logger.info(f"Assessment completed - Grade: {grade}, Score: {weighted_score:.1f}/5.0")
            logger.info(f"Found {len(gaps)} gaps and generated {len(recommendations)} recommendations")
            
            return assessment
            
        except Exception as e:
            logger.error(f"12-factor assessment failed: {e}")
            raise TwelveFactorAssessorError(f"Assessment failed: {e}")
    
    def _calculate_confidence(self, evaluations: Dict[str, FactorEvaluation]) -> float:
        """Calculate overall confidence in the assessment."""
        if not evaluations:
            return 0.0
        
        confidences = [eval.confidence for eval in evaluations.values()]
        return sum(confidences) / len(confidences)
    
    def _calculate_coverage(self, evaluations: Dict[str, FactorEvaluation]) -> float:
        """Calculate coverage percentage (factors that could be evaluated)."""
        if not evaluations:
            return 0.0
        
        evaluable_factors = sum(1 for eval in evaluations.values() 
                              if eval.score != FactorScore.UNKNOWN)
        total_factors = len(TWELVE_FACTOR_DEFINITIONS)
        
        return (evaluable_factors / total_factors) * 100
    
    def generate_assessment_summary(self, assessment: TwelveFactorAssessment) -> Dict[str, Any]:
        """Generate a comprehensive summary of the assessment."""
        
        # Factor performance breakdown
        excellent_factors = [name for name, eval in assessment.factor_evaluations.items() 
                           if eval.score == FactorScore.EXCELLENT]
        good_factors = [name for name, eval in assessment.factor_evaluations.items() 
                       if eval.score == FactorScore.GOOD]
        fair_factors = [name for name, eval in assessment.factor_evaluations.items() 
                       if eval.score == FactorScore.FAIR]
        poor_factors = [name for name, eval in assessment.factor_evaluations.items() 
                       if eval.score in [FactorScore.POOR, FactorScore.MISSING]]
        
        # Gap analysis summary
        gap_summary = self.gap_analyzer.get_gap_summary(assessment.gaps)
        
        # Recommendation roadmap
        roadmap = self.recommendation_engine.create_implementation_roadmap(assessment.recommendations)
        
        # Critical insights
        insights = self._generate_insights(assessment)
        
        return {
            'overview': {
                'grade': assessment.grade,
                'overall_score': assessment.overall_score,
                'weighted_score': assessment.weighted_score,
                'confidence': assessment.confidence,
                'coverage': assessment.coverage
            },
            'factor_breakdown': {
                'excellent': {
                    'count': len(excellent_factors),
                    'factors': excellent_factors
                },
                'good': {
                    'count': len(good_factors),
                    'factors': good_factors
                },
                'fair': {
                    'count': len(fair_factors),
                    'factors': fair_factors
                },
                'poor': {
                    'count': len(poor_factors),
                    'factors': poor_factors
                }
            },
            'gaps': gap_summary,
            'recommendations': {
                'total': len(assessment.recommendations),
                'critical': len([r for r in assessment.recommendations 
                               if r.priority.value == 'critical']),
                'high': len([r for r in assessment.recommendations 
                           if r.priority.value == 'high']),
                'roadmap': roadmap
            },
            'insights': insights,
            'next_steps': self._generate_next_steps(assessment)
        }
    
    def _generate_insights(self, assessment: TwelveFactorAssessment) -> List[str]:
        """Generate key insights from the assessment."""
        insights = []
        
        # Grade-based insights
        if assessment.grade == 'F':
            insights.append("Repository shows minimal 12-factor compliance - comprehensive overhaul needed")
        elif assessment.grade == 'D':
            insights.append("Poor 12-factor compliance with critical gaps in core principles")
        elif assessment.grade == 'C':
            insights.append("Fair compliance with significant room for improvement")
        elif assessment.grade == 'B':
            insights.append("Good foundation with several areas for optimization")
        else:
            insights.append("Excellent 12-factor compliance with minor refinements needed")
        
        # Coverage insights
        if assessment.coverage < 50:
            insights.append("Limited code patterns available for assessment - results may be incomplete")
        elif assessment.coverage < 80:
            insights.append("Moderate code coverage for assessment - some factors could not be fully evaluated")
        
        # Technology-specific insights
        poor_factors = [eval for eval in assessment.factor_evaluations.values() 
                       if eval.score in [FactorScore.POOR, FactorScore.MISSING]]
        
        if len(poor_factors) > 0:
            common_patterns = {}
            for eval in poor_factors:
                factor_type = eval.factor_name.split('_')[0]  # First word as category
                common_patterns[factor_type] = common_patterns.get(factor_type, 0) + 1
            
            most_common = max(common_patterns.items(), key=lambda x: x[1])
            if most_common[1] > 1:
                insights.append(f"Multiple issues in {most_common[0]}-related factors suggest systemic gaps")
        
        # Gap severity insights
        critical_gaps = [gap for gap in assessment.gaps if gap.severity.value == 'critical']
        if len(critical_gaps) > 3:
            insights.append("Multiple critical gaps require immediate architectural attention")
        elif len(critical_gaps) > 0:
            insights.append("Some critical issues need prompt resolution to ensure system reliability")
        
        return insights
    
    def _generate_next_steps(self, assessment: TwelveFactorAssessment) -> List[str]:
        """Generate recommended next steps based on assessment results."""
        next_steps = []
        
        # Priority-based next steps
        critical_recs = [r for r in assessment.recommendations if r.priority.value == 'critical']
        high_recs = [r for r in assessment.recommendations if r.priority.value == 'high']
        
        if critical_recs:
            next_steps.append(f"Address {len(critical_recs)} critical recommendations immediately")
            
            # Add specific first step for most critical issue
            first_critical = critical_recs[0]
            if first_critical.implementation_steps:
                next_steps.append(f"Start with: {first_critical.implementation_steps[0]}")
        
        if high_recs:
            next_steps.append(f"Plan implementation of {len(high_recs)} high-priority improvements")
        
        # Assessment-specific steps
        if assessment.coverage < 70:
            next_steps.append("Conduct manual review of factors with limited automated assessment")
        
        if assessment.confidence < 0.7:
            next_steps.append("Validate assessment results through code review and team discussion")
        
        # Long-term planning
        if len(assessment.recommendations) > 10:
            next_steps.append("Create phased implementation plan spanning 3-6 months")
        
        next_steps.append("Establish monitoring for 12-factor compliance in future development")
        next_steps.append("Schedule follow-up assessment after implementing key recommendations")
        
        return next_steps
    
    def compare_assessments(
        self, 
        current: TwelveFactorAssessment, 
        previous: TwelveFactorAssessment
    ) -> Dict[str, Any]:
        """Compare two assessments to show progress over time."""
        
        # Score comparison
        score_delta = current.weighted_score - previous.weighted_score
        grade_improvement = current.grade != previous.grade
        
        # Factor-level changes
        factor_changes = {}
        for factor_name in current.factor_evaluations:
            if factor_name in previous.factor_evaluations:
                current_score = current.factor_evaluations[factor_name].score.value
                previous_score = previous.factor_evaluations[factor_name].score.value
                
                if current_score != previous_score:
                    factor_changes[factor_name] = {
                        'previous': previous_score,
                        'current': current_score,
                        'change': current_score - previous_score
                    }
        
        # Recommendation changes
        current_rec_count = len(current.recommendations)
        previous_rec_count = len(previous.recommendations)
        
        return {
            'overall_progress': {
                'score_change': score_delta,
                'grade_changed': grade_improvement,
                'previous_grade': previous.grade,
                'current_grade': current.grade
            },
            'factor_changes': factor_changes,
            'recommendations': {
                'previous_count': previous_rec_count,
                'current_count': current_rec_count,
                'change': current_rec_count - previous_rec_count
            },
            'assessment_dates': {
                'previous': previous.timestamp,
                'current': current.timestamp
            },
            'summary': self._generate_progress_summary(score_delta, grade_improvement, factor_changes)
        }
    
    def _generate_progress_summary(
        self, 
        score_delta: float, 
        grade_changed: bool, 
        factor_changes: Dict
    ) -> str:
        """Generate a human-readable summary of progress."""
        
        if abs(score_delta) < 0.1 and not factor_changes:
            return "No significant changes detected since last assessment"
        
        if score_delta > 0.5:
            summary = "Significant improvement in 12-factor compliance"
        elif score_delta > 0.1:
            summary = "Moderate improvement detected"
        elif score_delta < -0.1:
            summary = "Some regression in compliance scores"
        else:
            summary = "Minimal overall score change"
        
        if grade_changed:
            summary += " with grade improvement"
        
        if factor_changes:
            improved_factors = [name for name, change in factor_changes.items() 
                              if change['change'] > 0]
            if improved_factors:
                summary += f". {len(improved_factors)} factors showed improvement"
        
        return summary


# Convenience function for standalone assessment
def assess_repository_twelve_factor(
    analysis_result: RepositoryAnalysisResult,
    assessment_id: Optional[str] = None
) -> TwelveFactorAssessment:
    """
    Convenience function to perform a complete 12-factor assessment.
    
    Args:
        analysis_result: Repository analysis results
        assessment_id: Optional assessment identifier
        
    Returns:
        Complete 12-factor assessment
    """
    assessor = TwelveFactorAssessor()
    return assessor.assess_repository(analysis_result, assessment_id)