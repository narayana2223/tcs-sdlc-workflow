"""
Gap analyzer for identifying areas where 12-factor principles are not properly implemented.
Analyzes factor evaluations to identify specific gaps and prioritize improvements.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter

from ..models.assessment import (
    FactorEvaluation, Gap, FactorScore, RecommendationPriority,
    TWELVE_FACTOR_DEFINITIONS
)
from ..analyzers.repository_analyzer import RepositoryAnalysisResult

logger = logging.getLogger(__name__)


class GapAnalyzerError(Exception):
    """Custom exception for gap analysis errors."""
    pass


class GapPattern:
    """Represents a specific gap pattern with detection logic."""
    
    def __init__(
        self,
        name: str,
        factor_name: str,
        gap_type: str,
        description: str,
        impact: str,
        current_state: str,
        desired_state: str,
        severity: RecommendationPriority,
        detection_criteria: Dict[str, any]
    ):
        self.name = name
        self.factor_name = factor_name
        self.gap_type = gap_type
        self.description = description
        self.impact = impact
        self.current_state = current_state
        self.desired_state = desired_state
        self.severity = severity
        self.detection_criteria = detection_criteria
    
    def matches(
        self, 
        evaluation: FactorEvaluation, 
        analysis_result: RepositoryAnalysisResult
    ) -> bool:
        """Check if this gap pattern matches the given evaluation."""
        criteria = self.detection_criteria
        
        # Check score criteria
        if 'max_score' in criteria:
            if evaluation.score.value > criteria['max_score']:
                return False
        
        if 'min_score' in criteria:
            if evaluation.score.value < criteria['min_score']:
                return False
        
        # Check evidence criteria
        if 'required_negative_evidence' in criteria:
            negative_evidence = [e for e in evaluation.evidence if e.type == 'negative']
            if len(negative_evidence) < criteria['required_negative_evidence']:
                return False
        
        if 'max_positive_evidence' in criteria:
            positive_evidence = [e for e in evaluation.evidence if e.type == 'positive']
            if len(positive_evidence) > criteria['max_positive_evidence']:
                return False
        
        # Check confidence criteria
        if 'min_confidence' in criteria:
            if evaluation.confidence < criteria['min_confidence']:
                return False
        
        # Check technology stack criteria
        if 'required_technologies' in criteria:
            tech_stack = analysis_result.technology_stack
            for tech in criteria['required_technologies']:
                if tech not in tech_stack.languages and tech not in tech_stack.frameworks:
                    return False
        
        if 'excluded_technologies' in criteria:
            tech_stack = analysis_result.technology_stack
            for tech in criteria['excluded_technologies']:
                if tech in tech_stack.languages or tech in tech_stack.frameworks:
                    return False
        
        return True
    
    def create_gap(self, affected_components: List[str] = None) -> Gap:
        """Create a Gap instance from this pattern."""
        return Gap(
            factor_name=self.factor_name,
            gap_type=self.gap_type,
            description=self.description,
            impact=self.impact,
            current_state=self.current_state,
            desired_state=self.desired_state,
            severity=self.severity,
            affected_components=affected_components or []
        )


class GapAnalyzer:
    """Analyzes factor evaluations to identify specific implementation gaps."""
    
    def __init__(self):
        """Initialize the gap analyzer with predefined gap patterns."""
        self.gap_patterns = self._initialize_gap_patterns()
    
    def _initialize_gap_patterns(self) -> List[GapPattern]:
        """Initialize predefined gap patterns for common issues."""
        patterns = []
        
        # Natural Language to Tool Calls gaps
        patterns.extend([
            GapPattern(
                name="missing_structured_outputs",
                factor_name="natural_language_to_tool_calls",
                gap_type="missing",
                description="No structured function calling or tool interfaces found",
                impact="Agents cannot reliably execute actions or chain operations",
                current_state="Raw text generation without structured outputs",
                desired_state="Structured function/tool calling with schema validation",
                severity=RecommendationPriority.CRITICAL,
                detection_criteria={
                    'max_score': 2,
                    'max_positive_evidence': 1,
                    'min_confidence': 0.5
                }
            ),
            GapPattern(
                name="poor_output_validation",
                factor_name="natural_language_to_tool_calls",
                gap_type="poor_quality",
                description="Tool calls exist but lack proper validation or error handling",
                impact="Unreliable tool execution and poor error recovery",
                current_state="Basic tool calling without validation",
                desired_state="Robust tool calling with schema validation and error handling",
                severity=RecommendationPriority.HIGH,
                detection_criteria={
                    'max_score': 3,
                    'required_negative_evidence': 1,
                    'min_confidence': 0.6
                }
            )
        ])
        
        # Own Your Prompts gaps
        patterns.extend([
            GapPattern(
                name="hardcoded_prompts",
                factor_name="own_your_prompts",
                gap_type="anti_pattern",
                description="Prompts are hardcoded in source code rather than managed as assets",
                impact="Difficult to version, test, and optimize prompts",
                current_state="Prompts embedded directly in code",
                desired_state="Prompts managed as versioned, testable templates",
                severity=RecommendationPriority.HIGH,
                detection_criteria={
                    'max_score': 2,
                    'required_negative_evidence': 2,
                    'min_confidence': 0.7
                }
            ),
            GapPattern(
                name="no_prompt_versioning",
                factor_name="own_your_prompts",
                gap_type="missing",
                description="No prompt versioning or template management system",
                impact="Cannot track prompt performance or roll back changes",
                current_state="Ad-hoc prompt management",
                desired_state="Versioned prompt templates with performance tracking",
                severity=RecommendationPriority.MEDIUM,
                detection_criteria={
                    'max_score': 3,
                    'max_positive_evidence': 1,
                    'min_confidence': 0.5
                }
            )
        ])
        
        # Own Your Context Window gaps
        patterns.extend([
            GapPattern(
                name="no_context_management",
                factor_name="own_your_context_window",
                gap_type="missing",
                description="No context window size monitoring or management",
                impact="Risk of context overflow and degraded performance",
                current_state="Naive context usage without monitoring",
                desired_state="Active context window management with compression",
                severity=RecommendationPriority.HIGH,
                detection_criteria={
                    'max_score': 2,
                    'max_positive_evidence': 0,
                    'min_confidence': 0.6
                }
            ),
            GapPattern(
                name="poor_context_relevance",
                factor_name="own_your_context_window",
                gap_type="poor_quality",
                description="Context stuffing without relevance filtering",
                impact="Wasted context space on irrelevant information",
                current_state="All available context included without filtering",
                desired_state="Relevance-based context selection and compression",
                severity=RecommendationPriority.MEDIUM,
                detection_criteria={
                    'max_score': 3,
                    'min_confidence': 0.5
                }
            )
        ])
        
        # Tools are Structured Outputs gaps
        patterns.extend([
            GapPattern(
                name="unstructured_tool_outputs",
                factor_name="tools_are_structured_outputs",
                gap_type="anti_pattern",
                description="Tools return unstructured text instead of structured data",
                impact="Difficult to parse and chain tool operations reliably",
                current_state="Tools return plain text or unvalidated outputs",
                desired_state="All tools return structured, validated data",
                severity=RecommendationPriority.CRITICAL,
                detection_criteria={
                    'max_score': 2,
                    'required_negative_evidence': 2,
                    'min_confidence': 0.7
                }
            ),
            GapPattern(
                name="missing_output_schemas",
                factor_name="tools_are_structured_outputs",
                gap_type="missing",
                description="No schema definition or validation for tool outputs",
                impact="Runtime errors and unreliable tool chaining",
                current_state="Tool outputs without schema validation",
                desired_state="Schema-validated tool outputs with type safety",
                severity=RecommendationPriority.HIGH,
                detection_criteria={
                    'max_score': 3,
                    'max_positive_evidence': 1,
                    'excluded_technologies': ['typescript']  # TS has built-in typing
                }
            )
        ])
        
        # Unify Execution State gaps
        patterns.extend([
            GapPattern(
                name="scattered_state_management",
                factor_name="unify_execution_state",
                gap_type="anti_pattern",
                description="State scattered across multiple systems without coordination",
                impact="Inconsistent agent behavior and difficult debugging",
                current_state="Multiple uncoordinated state stores",
                desired_state="Unified state management with consistency guarantees",
                severity=RecommendationPriority.HIGH,
                detection_criteria={
                    'max_score': 2,
                    'min_confidence': 0.6
                }
            ),
            GapPattern(
                name="no_state_persistence",
                factor_name="unify_execution_state",
                gap_type="missing",
                description="No state persistence for long-running operations",
                impact="Loss of progress on system restart or failure",
                current_state="In-memory only state management",
                desired_state="Persistent state with recovery capabilities",
                severity=RecommendationPriority.MEDIUM,
                detection_criteria={
                    'max_score': 3,
                    'max_positive_evidence': 1
                }
            )
        ])
        
        return patterns
    
    def analyze_gaps(
        self, 
        evaluations: Dict[str, FactorEvaluation],
        analysis_result: RepositoryAnalysisResult
    ) -> List[Gap]:
        """
        Analyze factor evaluations to identify specific gaps.
        
        Args:
            evaluations: Dictionary of factor evaluations
            analysis_result: Original repository analysis results
            
        Returns:
            List of identified gaps
        """
        try:
            logger.info("Starting gap analysis")
            
            gaps = []
            
            # Check each gap pattern against evaluations
            for pattern in self.gap_patterns:
                if pattern.factor_name in evaluations:
                    evaluation = evaluations[pattern.factor_name]
                    
                    if pattern.matches(evaluation, analysis_result):
                        # Identify affected components
                        affected_components = self._identify_affected_components(
                            pattern, evaluation, analysis_result
                        )
                        
                        gap = pattern.create_gap(affected_components)
                        gaps.append(gap)
                        
                        logger.debug(f"Identified gap: {pattern.name} in {pattern.factor_name}")
            
            # Add custom gaps based on specific evaluation results
            custom_gaps = self._identify_custom_gaps(evaluations, analysis_result)
            gaps.extend(custom_gaps)
            
            # Prioritize and deduplicate gaps
            gaps = self._prioritize_gaps(gaps)
            
            logger.info(f"Identified {len(gaps)} gaps across all factors")
            return gaps
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}")
            raise GapAnalyzerError(f"Failed to analyze gaps: {e}")
    
    def _identify_affected_components(
        self,
        pattern: GapPattern,
        evaluation: FactorEvaluation,
        analysis_result: RepositoryAnalysisResult
    ) -> List[str]:
        """Identify components affected by a specific gap."""
        affected = []
        
        # Extract components from evidence
        for evidence in evaluation.evidence:
            if evidence.file_path and evidence.type == 'negative':
                affected.append(evidence.file_path)
        
        # Add components based on technology stack
        tech_stack = analysis_result.technology_stack
        if pattern.factor_name == 'natural_language_to_tool_calls':
            # Add main application files for language-specific patterns
            if tech_stack.primary_language == 'python':
                affected.extend(['*.py files'])
            elif tech_stack.primary_language == 'javascript':
                affected.extend(['*.js files'])
        
        return list(set(affected))  # Remove duplicates
    
    def _identify_custom_gaps(
        self,
        evaluations: Dict[str, FactorEvaluation],
        analysis_result: RepositoryAnalysisResult
    ) -> List[Gap]:
        """Identify custom gaps based on specific evaluation patterns."""
        custom_gaps = []
        
        # Check for overall poor performance across factors
        poor_scores = [eval for eval in evaluations.values() 
                      if eval.score in [FactorScore.POOR, FactorScore.MISSING]]
        
        if len(poor_scores) >= len(evaluations) * 0.5:  # More than 50% poor scores
            custom_gaps.append(Gap(
                factor_name="overall",
                gap_type="systemic",
                description="Systemic issues across multiple 12-factor principles",
                impact="Poor overall AI agent architecture and practices",
                current_state="Multiple factors poorly implemented",
                desired_state="Comprehensive 12-factor compliance",
                severity=RecommendationPriority.CRITICAL,
                affected_components=["entire_codebase"]
            ))
        
        # Check for missing AI/ML dependencies
        dependencies = analysis_result.dependency_analysis.get('dependencies', [])
        ai_deps = ['openai', 'anthropic', 'langchain', 'transformers', 'torch', 'tensorflow']
        found_ai_deps = [dep.name for dep in dependencies 
                        if any(ai_dep in dep.name.lower() for ai_dep in ai_deps)]
        
        if not found_ai_deps and any(score.score != FactorScore.UNKNOWN 
                                    for score in evaluations.values()):
            custom_gaps.append(Gap(
                factor_name="natural_language_to_tool_calls",
                gap_type="missing",
                description="No AI/ML libraries found despite agent-related code patterns",
                impact="May be implementing custom AI logic without established libraries",
                current_state="Custom or no AI library usage",
                desired_state="Use of established AI/ML libraries and frameworks",
                severity=RecommendationPriority.MEDIUM,
                affected_components=["dependency_management"]
            ))
        
        return custom_gaps
    
    def _prioritize_gaps(self, gaps: List[Gap]) -> List[Gap]:
        """Prioritize and deduplicate gaps."""
        # Remove duplicates by gap type and factor
        unique_gaps = {}
        for gap in gaps:
            key = (gap.factor_name, gap.gap_type, gap.description[:50])  # Use first 50 chars as partial key
            if key not in unique_gaps or gap.severity.value > unique_gaps[key].severity.value:
                unique_gaps[key] = gap
        
        # Sort by severity (critical first) and then by factor name
        severity_order = {
            RecommendationPriority.CRITICAL: 4,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        
        sorted_gaps = sorted(
            unique_gaps.values(),
            key=lambda g: (severity_order[g.severity], g.factor_name)
        )
        
        return sorted_gaps
    
    def analyze_gap_trends(self, gaps: List[Gap]) -> Dict[str, any]:
        """Analyze trends and patterns in the identified gaps."""
        if not gaps:
            return {}
        
        # Gap type distribution
        gap_types = Counter(gap.gap_type for gap in gaps)
        
        # Severity distribution
        severities = Counter(gap.severity.value for gap in gaps)
        
        # Factor distribution
        factors = Counter(gap.factor_name for gap in gaps)
        
        # Most affected components
        all_components = []
        for gap in gaps:
            all_components.extend(gap.affected_components)
        component_counts = Counter(all_components)
        
        return {
            'total_gaps': len(gaps),
            'gap_type_distribution': dict(gap_types),
            'severity_distribution': dict(severities),
            'factor_distribution': dict(factors),
            'most_affected_components': dict(component_counts.most_common(10)),
            'critical_gaps_count': len([g for g in gaps if g.severity == RecommendationPriority.CRITICAL]),
            'systemic_issues': len([g for g in gaps if g.gap_type == 'systemic']),
            'recommendations': {
                'immediate_action_needed': len([g for g in gaps if g.severity == RecommendationPriority.CRITICAL]) > 0,
                'focus_areas': list(factors.most_common(3)),
                'complexity_assessment': 'high' if len(gaps) > 10 else 'medium' if len(gaps) > 5 else 'low'
            }
        }
    
    def get_gap_summary(self, gaps: List[Gap]) -> Dict[str, any]:
        """Generate a summary of gaps for reporting."""
        if not gaps:
            return {
                'summary': "No significant gaps identified",
                'health_score': 100,
                'status': 'excellent'
            }
        
        critical_count = len([g for g in gaps if g.severity == RecommendationPriority.CRITICAL])
        high_count = len([g for g in gaps if g.severity == RecommendationPriority.HIGH])
        medium_count = len([g for g in gaps if g.severity == RecommendationPriority.MEDIUM])
        low_count = len([g for g in gaps if g.severity == RecommendationPriority.LOW])
        
        # Calculate health score (0-100)
        health_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 8 + low_count * 3))
        
        # Determine status
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 70:
            status = 'good'
        elif health_score >= 50:
            status = 'fair'
        elif health_score >= 30:
            status = 'poor'
        else:
            status = 'critical'
        
        # Generate summary text
        if critical_count > 0:
            summary = f"{critical_count} critical issues require immediate attention"
        elif high_count > 0:
            summary = f"{high_count} high-priority improvements recommended"
        elif medium_count > 0:
            summary = f"{medium_count} medium-priority enhancements suggested"
        else:
            summary = f"{low_count} minor improvements identified"
        
        return {
            'summary': summary,
            'health_score': health_score,
            'status': status,
            'breakdown': {
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            }
        }