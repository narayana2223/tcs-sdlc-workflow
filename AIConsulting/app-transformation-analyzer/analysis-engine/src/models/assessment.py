"""
Data models for 12-factor assessment results and evaluation structures.
Defines the structure for scoring, recommendations, and gaps in AI agent development practices.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime


class FactorScore(Enum):
    """Scoring levels for 12-factor evaluation."""
    EXCELLENT = 5  # Fully implemented with best practices
    GOOD = 4       # Well implemented with minor improvements needed
    FAIR = 3       # Partially implemented, significant room for improvement
    POOR = 2       # Minimal implementation, major gaps
    MISSING = 1    # Not implemented or very poor implementation
    UNKNOWN = 0    # Cannot be determined from available information


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"    # Must fix - blocks effective AI agent development
    HIGH = "high"           # Should fix - significantly impacts effectiveness
    MEDIUM = "medium"       # Good to fix - moderate impact
    LOW = "low"            # Nice to fix - minor improvements


class ImplementationComplexity(Enum):
    """Complexity levels for implementing recommendations."""
    LOW = "low"           # Quick fix, minimal code changes
    MEDIUM = "medium"     # Moderate effort, some refactoring needed
    HIGH = "high"         # Significant effort, major changes required
    VERY_HIGH = "very_high"  # Complete redesign or major architectural changes


@dataclass
class FactorEvidence:
    """Evidence found for or against a factor implementation."""
    type: str  # 'positive', 'negative', 'neutral'
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class FactorEvaluation:
    """Evaluation result for a single 12-factor principle."""
    factor_name: str
    factor_description: str
    score: FactorScore
    score_reasoning: str
    evidence: List[FactorEvidence] = field(default_factory=list)
    confidence: float = 1.0
    weight: float = 1.0  # Importance weighting for overall score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'factor_name': self.factor_name,
            'factor_description': self.factor_description,
            'score': self.score.value,
            'score_name': self.score.name,
            'score_reasoning': self.score_reasoning,
            'evidence': [
                {
                    'type': e.type,
                    'description': e.description,
                    'file_path': e.file_path,
                    'line_number': e.line_number,
                    'code_snippet': e.code_snippet,
                    'confidence': e.confidence
                } for e in self.evidence
            ],
            'confidence': self.confidence,
            'weight': self.weight
        }


@dataclass
class Gap:
    """Represents a gap in 12-factor implementation."""
    factor_name: str
    gap_type: str  # 'missing', 'partial', 'poor_quality', 'anti_pattern'
    description: str
    impact: str
    current_state: str
    desired_state: str
    severity: RecommendationPriority
    affected_components: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'factor_name': self.factor_name,
            'gap_type': self.gap_type,
            'description': self.description,
            'impact': self.impact,
            'current_state': self.current_state,
            'desired_state': self.desired_state,
            'severity': self.severity.value,
            'affected_components': self.affected_components
        }


@dataclass
class Recommendation:
    """Specific recommendation for improving 12-factor compliance."""
    id: str
    factor_name: str
    title: str
    description: str
    rationale: str
    implementation_steps: List[str]
    priority: RecommendationPriority
    complexity: ImplementationComplexity
    estimated_effort: str  # e.g., "2-4 hours", "1-2 weeks"
    benefits: List[str]
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    code_examples: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'factor_name': self.factor_name,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'implementation_steps': self.implementation_steps,
            'priority': self.priority.value,
            'complexity': self.complexity.value,
            'estimated_effort': self.estimated_effort,
            'benefits': self.benefits,
            'risks': self.risks,
            'prerequisites': self.prerequisites,
            'resources': self.resources,
            'code_examples': self.code_examples
        }


@dataclass
class TwelveFactorAssessment:
    """Complete 12-factor assessment results."""
    repository_url: str
    assessment_id: str
    timestamp: str
    
    # Factor evaluations
    factor_evaluations: Dict[str, FactorEvaluation]
    
    # Overall scoring
    overall_score: float
    weighted_score: float
    grade: str  # A, B, C, D, F
    
    # Analysis results
    gaps: List[Gap]
    recommendations: List[Recommendation]
    
    # Metadata
    confidence: float
    coverage: float  # Percentage of factors that could be evaluated
    
    # Summary statistics
    score_distribution: Dict[str, int] = field(default_factory=dict)
    priority_distribution: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize computed fields."""
        if not self.score_distribution:
            self.score_distribution = self._calculate_score_distribution()
        if not self.priority_distribution:
            self.priority_distribution = self._calculate_priority_distribution()
    
    def _calculate_score_distribution(self) -> Dict[str, int]:
        """Calculate distribution of scores across factors."""
        distribution = {score.name: 0 for score in FactorScore}
        for evaluation in self.factor_evaluations.values():
            distribution[evaluation.score.name] += 1
        return distribution
    
    def _calculate_priority_distribution(self) -> Dict[str, int]:
        """Calculate distribution of recommendation priorities."""
        distribution = {priority.value: 0 for priority in RecommendationPriority}
        for recommendation in self.recommendations:
            distribution[recommendation.priority.value] += 1
        return distribution
    
    def get_factors_by_score(self, score: FactorScore) -> List[FactorEvaluation]:
        """Get all factors with a specific score."""
        return [eval for eval in self.factor_evaluations.values() 
                if eval.score == score]
    
    def get_critical_gaps(self) -> List[Gap]:
        """Get all critical gaps that need immediate attention."""
        return [gap for gap in self.gaps 
                if gap.severity == RecommendationPriority.CRITICAL]
    
    def get_recommendations_by_priority(self, priority: RecommendationPriority) -> List[Recommendation]:
        """Get recommendations by priority level."""
        return [rec for rec in self.recommendations 
                if rec.priority == priority]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'repository_url': self.repository_url,
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp,
            'factor_evaluations': {
                name: eval.to_dict() 
                for name, eval in self.factor_evaluations.items()
            },
            'overall_score': self.overall_score,
            'weighted_score': self.weighted_score,
            'grade': self.grade,
            'gaps': [gap.to_dict() for gap in self.gaps],
            'recommendations': [rec.to_dict() for rec in self.recommendations],
            'confidence': self.confidence,
            'coverage': self.coverage,
            'score_distribution': self.score_distribution,
            'priority_distribution': self.priority_distribution,
            'summary': {
                'total_factors': len(self.factor_evaluations),
                'total_gaps': len(self.gaps),
                'total_recommendations': len(self.recommendations),
                'critical_issues': len(self.get_critical_gaps()),
                'excellent_factors': len(self.get_factors_by_score(FactorScore.EXCELLENT)),
                'poor_factors': len(self.get_factors_by_score(FactorScore.POOR)) + 
                               len(self.get_factors_by_score(FactorScore.MISSING))
            }
        }


@dataclass
class TwelveFactorDefinition:
    """Definition of a 12-factor principle."""
    name: str
    title: str
    description: str
    rationale: str
    indicators: Dict[str, List[str]]  # 'positive', 'negative' indicators
    weight: float = 1.0
    evaluation_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'indicators': self.indicators,
            'weight': self.weight,
            'evaluation_criteria': self.evaluation_criteria
        }


# Pre-defined 12-factor definitions for AI agent development
TWELVE_FACTOR_DEFINITIONS = {
    'natural_language_to_tool_calls': TwelveFactorDefinition(
        name='natural_language_to_tool_calls',
        title='Natural Language to Tool Calls',
        description='Agents should convert natural language requests into structured tool calls rather than generating raw text',
        rationale='Tool calls provide structured, verifiable outputs that can be chained and composed reliably',
        indicators={
            'positive': [
                'Function/tool calling interfaces',
                'Structured output parsing',
                'API integration patterns',
                'Schema validation'
            ],
            'negative': [
                'Raw text generation without structure',
                'String parsing for commands',
                'Unvalidated outputs'
            ]
        },
        weight=1.2,
        evaluation_criteria=[
            'Presence of structured function/tool interfaces',
            'Input validation and schema enforcement',
            'Separation of natural language understanding from tool execution',
            'Error handling for malformed requests'
        ]
    ),
    
    'own_your_prompts': TwelveFactorDefinition(
        name='own_your_prompts',
        title='Own Your Prompts',
        description='Prompts should be version-controlled, templated, and managed as first-class assets',
        rationale='Treating prompts as code enables proper versioning, testing, and optimization',
        indicators={
            'positive': [
                'Template engines for prompts',
                'Version controlled prompt files',
                'Prompt testing frameworks',
                'Prompt optimization tools'
            ],
            'negative': [
                'Hardcoded prompts in source code',
                'Ad-hoc prompt construction',
                'No prompt versioning or testing'
            ]
        },
        weight=1.1,
        evaluation_criteria=[
            'Prompts stored as separate, version-controlled assets',
            'Template system for prompt composition',
            'Testing infrastructure for prompt validation',
            'Prompt performance monitoring'
        ]
    ),
    
    'own_your_context_window': TwelveFactorDefinition(
        name='own_your_context_window',
        title='Own Your Context Window',
        description='Actively manage context window usage with strategies for relevance, compression, and overflow handling',
        rationale='Context window is a limited resource that must be managed strategically for optimal performance',
        indicators={
            'positive': [
                'Context compression algorithms',
                'Relevance scoring systems',
                'Context window monitoring',
                'Dynamic context management'
            ],
            'negative': [
                'Naive context stuffing',
                'No context size monitoring',
                'Poor context relevance filtering'
            ]
        },
        weight=1.0,
        evaluation_criteria=[
            'Context size monitoring and limits',
            'Relevance-based context selection',
            'Context compression or summarization',
            'Graceful handling of context overflow'
        ]
    ),
    
    'tools_are_structured_outputs': TwelveFactorDefinition(
        name='tools_are_structured_outputs',
        title='Tools are Structured Outputs',
        description='Tool outputs should be structured data (JSON, schemas) rather than unstructured text',
        rationale='Structured outputs enable reliable parsing, validation, and chaining of tool operations',
        indicators={
            'positive': [
                'JSON/XML output formats',
                'Schema-based validation',
                'Type-safe tool interfaces',
                'Output parsing libraries'
            ],
            'negative': [
                'Plain text tool outputs',
                'No output validation',
                'String-based parsing'
            ]
        },
        weight=1.1,
        evaluation_criteria=[
            'Tools return structured data formats',
            'Output schema definition and validation',
            'Type safety in tool interfaces',
            'Error handling for malformed outputs'
        ]
    ),
    
    'unify_execution_state': TwelveFactorDefinition(
        name='unify_execution_state',
        title='Unify Execution State',
        description='Maintain consistent execution state across agent operations and tool calls',
        rationale='Unified state management prevents inconsistencies and enables reliable agent behavior',
        indicators={
            'positive': [
                'State management patterns',
                'Consistent data storage',
                'State synchronization',
                'Transaction patterns'
            ],
            'negative': [
                'Scattered state management',
                'Inconsistent data access',
                'No state validation'
            ]
        },
        weight=1.0,
        evaluation_criteria=[
            'Centralized state management system',
            'State consistency validation',
            'Atomic operations for state changes',
            'State recovery mechanisms'
        ]
    ),
    
    'launch_pause_resume': TwelveFactorDefinition(
        name='launch_pause_resume',
        title='Launch/Pause/Resume',
        description='Agents should support lifecycle management with ability to pause and resume operations',
        rationale='Long-running agents need proper lifecycle management for reliability and resource efficiency',
        indicators={
            'positive': [
                'Process lifecycle management',
                'State persistence',
                'Graceful shutdown patterns',
                'Resume capabilities'
            ],
            'negative': [
                'No lifecycle management',
                'Stateless-only execution',
                'Poor shutdown handling'
            ]
        },
        weight=0.9,
        evaluation_criteria=[
            'Process lifecycle control interfaces',
            'State persistence for resumption',
            'Graceful shutdown procedures',
            'Resource cleanup on pause/stop'
        ]
    ),
    
    'contact_humans': TwelveFactorDefinition(
        name='contact_humans',
        title='Contact Humans',
        description='Agents should have clear mechanisms to escalate to human operators when needed',
        rationale='Human oversight is essential for handling edge cases and maintaining trust',
        indicators={
            'positive': [
                'Human escalation interfaces',
                'Approval workflows',
                'Human-in-the-loop patterns',
                'Notification systems'
            ],
            'negative': [
                'No human escalation',
                'Fully autonomous operation',
                'No approval mechanisms'
            ]
        },
        weight=1.1,
        evaluation_criteria=[
            'Clear escalation triggers and mechanisms',
            'Human approval workflows',
            'Communication interfaces for human operators',
            'Audit trails for human interactions'
        ]
    ),
    
    'own_your_control_flow': TwelveFactorDefinition(
        name='own_your_control_flow',
        title='Own Your Control Flow',
        description='Explicitly manage agent control flow rather than relying on implicit LLM reasoning chains',
        rationale='Explicit control flow enables debugging, testing, and predictable agent behavior',
        indicators={
            'positive': [
                'State machines',
                'Workflow engines',
                'Decision trees',
                'Control flow visualization'
            ],
            'negative': [
                'Implicit LLM-driven flow',
                'No flow visualization',
                'Unpredictable execution paths'
            ]
        },
        weight=1.2,
        evaluation_criteria=[
            'Explicit control flow definition',
            'Flow visualization and debugging tools',
            'Deterministic execution paths',
            'Flow testing capabilities'
        ]
    ),
    
    'compact_errors': TwelveFactorDefinition(
        name='compact_errors',
        title='Compact Errors',
        description='Error messages should be concise, structured, and actionable rather than verbose logs',
        rationale='Compact errors preserve context window space while providing actionable information',
        indicators={
            'positive': [
                'Structured error formats',
                'Error categorization',
                'Actionable error messages',
                'Error compression'
            ],
            'negative': [
                'Verbose error logs',
                'Unstructured error messages',
                'No error categorization'
            ]
        },
        weight=0.8,
        evaluation_criteria=[
            'Structured error message formats',
            'Error categorization and codes',
            'Actionable error descriptions',
            'Error message length optimization'
        ]
    ),
    
    'small_focused_agents': TwelveFactorDefinition(
        name='small_focused_agents',
        title='Small, Focused Agents',
        description='Agents should have narrow, well-defined responsibilities rather than being monolithic',
        rationale='Focused agents are easier to test, maintain, and compose into larger systems',
        indicators={
            'positive': [
                'Single responsibility principle',
                'Microservices architecture',
                'Agent composition patterns',
                'Clear boundaries'
            ],
            'negative': [
                'Monolithic agents',
                'Multiple responsibilities',
                'Unclear boundaries'
            ]
        },
        weight=1.0,
        evaluation_criteria=[
            'Clear agent responsibility boundaries',
            'Minimal interface complexity',
            'Agent composition capabilities',
            'Independent deployability'
        ]
    ),
    
    'trigger_from_anywhere': TwelveFactorDefinition(
        name='trigger_from_anywhere',
        title='Trigger from Anywhere',
        description='Agents should be triggerable through multiple interfaces (API, CLI, webhooks, events)',
        rationale='Multiple trigger mechanisms enable flexible integration and deployment scenarios',
        indicators={
            'positive': [
                'Multiple interface support',
                'Event-driven architecture',
                'API endpoints',
                'CLI interfaces'
            ],
            'negative': [
                'Single trigger mechanism',
                'Tightly coupled interfaces',
                'No programmatic access'
            ]
        },
        weight=0.9,
        evaluation_criteria=[
            'Multiple trigger interface support',
            'Consistent behavior across interfaces',
            'Interface documentation',
            'Authentication and authorization'
        ]
    ),
    
    'make_agent_stateless_reducer': TwelveFactorDefinition(
        name='make_agent_stateless_reducer',
        title='Make Agent a Stateless Reducer',
        description='Agents should be implemented as pure functions that reduce state and inputs to outputs',
        rationale='Stateless design enables better testing, scaling, and reasoning about agent behavior',
        indicators={
            'positive': [
                'Pure function patterns',
                'Immutable state handling',
                'Functional programming',
                'Reducer patterns'
            ],
            'negative': [
                'Mutable global state',
                'Side effects in core logic',
                'Stateful agent design'
            ]
        },
        weight=1.0,
        evaluation_criteria=[
            'Stateless function design',
            'Immutable data structures',
            'Pure function implementations',
            'Predictable input/output mappings'
        ]
    )
}