"""
Recommendation engine for generating specific, actionable advice based on 12-factor assessment gaps.
Creates prioritized recommendations with implementation steps and resource guidance.
"""

import uuid
import logging
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..models.assessment import (
    Recommendation, Gap, FactorEvaluation, FactorScore, 
    RecommendationPriority, ImplementationComplexity,
    TWELVE_FACTOR_DEFINITIONS
)
from ..analyzers.repository_analyzer import RepositoryAnalysisResult

logger = logging.getLogger(__name__)


class RecommendationEngineError(Exception):
    """Custom exception for recommendation engine errors."""
    pass


class RecommendationTemplate:
    """Template for generating specific recommendations."""
    
    def __init__(
        self,
        template_id: str,
        factor_name: str,
        gap_types: List[str],
        title: str,
        description: str,
        rationale: str,
        implementation_steps: List[str],
        priority: RecommendationPriority,
        complexity: ImplementationComplexity,
        estimated_effort: str,
        benefits: List[str],
        risks: List[str] = None,
        prerequisites: List[str] = None,
        resources: List[str] = None,
        code_examples: List[Dict[str, str]] = None,
        tech_specific: Dict[str, any] = None
    ):
        self.template_id = template_id
        self.factor_name = factor_name
        self.gap_types = gap_types
        self.title = title
        self.description = description
        self.rationale = rationale
        self.implementation_steps = implementation_steps
        self.priority = priority
        self.complexity = complexity
        self.estimated_effort = estimated_effort
        self.benefits = benefits
        self.risks = risks or []
        self.prerequisites = prerequisites or []
        self.resources = resources or []
        self.code_examples = code_examples or []
        self.tech_specific = tech_specific or {}
    
    def matches_gap(self, gap: Gap) -> bool:
        """Check if this template matches a given gap."""
        return (gap.factor_name == self.factor_name and 
                gap.gap_type in self.gap_types)
    
    def generate_recommendation(
        self, 
        gap: Gap, 
        analysis_result: RepositoryAnalysisResult
    ) -> Recommendation:
        """Generate a specific recommendation from this template."""
        # Customize based on technology stack
        customized_steps = self._customize_implementation_steps(
            analysis_result.technology_stack
        )
        
        customized_examples = self._customize_code_examples(
            analysis_result.technology_stack
        )
        
        customized_resources = self._customize_resources(
            analysis_result.technology_stack
        )
        
        return Recommendation(
            id=str(uuid.uuid4()),
            factor_name=self.factor_name,
            title=self.title,
            description=self.description,
            rationale=self.rationale,
            implementation_steps=customized_steps,
            priority=self.priority,
            complexity=self.complexity,
            estimated_effort=self.estimated_effort,
            benefits=self.benefits,
            risks=self.risks,
            prerequisites=self.prerequisites,
            resources=customized_resources,
            code_examples=customized_examples
        )
    
    def _customize_implementation_steps(self, tech_stack) -> List[str]:
        """Customize implementation steps based on technology stack."""
        steps = self.implementation_steps.copy()
        
        if self.tech_specific:
            primary_lang = tech_stack.primary_language.lower()
            if primary_lang in self.tech_specific:
                lang_specific = self.tech_specific[primary_lang]
                if 'additional_steps' in lang_specific:
                    steps.extend(lang_specific['additional_steps'])
                if 'replace_steps' in lang_specific:
                    for old_step, new_step in lang_specific['replace_steps'].items():
                        steps = [step.replace(old_step, new_step) for step in steps]
        
        return steps
    
    def _customize_code_examples(self, tech_stack) -> List[Dict[str, str]]:
        """Customize code examples based on technology stack."""
        examples = self.code_examples.copy()
        
        if self.tech_specific:
            primary_lang = tech_stack.primary_language.lower()
            if primary_lang in self.tech_specific:
                lang_specific = self.tech_specific[primary_lang]
                if 'code_examples' in lang_specific:
                    examples.extend(lang_specific['code_examples'])
        
        return examples
    
    def _customize_resources(self, tech_stack) -> List[str]:
        """Customize resources based on technology stack."""
        resources = self.resources.copy()
        
        if self.tech_specific:
            primary_lang = tech_stack.primary_language.lower()
            if primary_lang in self.tech_specific:
                lang_specific = self.tech_specific[primary_lang]
                if 'resources' in lang_specific:
                    resources.extend(lang_specific['resources'])
        
        return resources


class RecommendationEngine:
    """Main recommendation engine for generating actionable advice."""
    
    def __init__(self):
        """Initialize the recommendation engine with templates."""
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> List[RecommendationTemplate]:
        """Initialize recommendation templates for common gaps."""
        templates = []
        
        # Natural Language to Tool Calls recommendations
        templates.extend([
            RecommendationTemplate(
                template_id="implement_structured_function_calling",
                factor_name="natural_language_to_tool_calls",
                gap_types=["missing", "poor_quality"],
                title="Implement Structured Function Calling",
                description="Add structured function/tool calling interfaces with schema validation",
                rationale="Structured outputs enable reliable agent operations and tool chaining",
                implementation_steps=[
                    "Define function schemas using JSON Schema or Pydantic models",
                    "Implement function calling interface with input validation",
                    "Add error handling for malformed function calls",
                    "Create tool registry for available functions",
                    "Implement function call execution with output validation"
                ],
                priority=RecommendationPriority.CRITICAL,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_effort="1-2 weeks",
                benefits=[
                    "Reliable agent-to-tool communication",
                    "Better error handling and debugging",
                    "Composable tool operations",
                    "Improved testing capabilities"
                ],
                risks=[
                    "Initial implementation complexity",
                    "Need to refactor existing code"
                ],
                prerequisites=[
                    "Define tool/function requirements",
                    "Choose schema validation library"
                ],
                resources=[
                    "OpenAI Function Calling documentation",
                    "Pydantic documentation for Python",
                    "JSON Schema specification"
                ],
                code_examples=[
                    {
                        "language": "python",
                        "title": "Pydantic Function Schema",
                        "code": """from pydantic import BaseModel
from typing import List

class SearchParams(BaseModel):
    query: str
    max_results: int = 10

class SearchResult(BaseModel):
    title: str
    content: str
    score: float

def search_function(params: SearchParams) -> List[SearchResult]:
    # Implementation here
    return []"""
                    }
                ],
                tech_specific={
                    'python': {
                        'additional_steps': [
                            "Install pydantic: pip install pydantic",
                            "Use FastAPI for automatic OpenAPI schema generation"
                        ],
                        'resources': [
                            "Pydantic documentation: https://docs.pydantic.dev/",
                            "FastAPI function calling examples"
                        ]
                    },
                    'javascript': {
                        'additional_steps': [
                            "Install zod: npm install zod",
                            "Use TypeScript for compile-time type checking"
                        ],
                        'resources': [
                            "Zod documentation for schema validation",
                            "TypeScript documentation"
                        ],
                        'code_examples': [
                            {
                                "language": "typescript",
                                "title": "Zod Function Schema",
                                "code": """import { z } from 'zod';

const SearchParamsSchema = z.object({
  query: z.string(),
  maxResults: z.number().default(10)
});

type SearchParams = z.infer<typeof SearchParamsSchema>;

function searchFunction(params: SearchParams) {
  const validated = SearchParamsSchema.parse(params);
  // Implementation here
  return [];
}"""
                            }
                        ]
                    }
                }
            ),
            
            RecommendationTemplate(
                template_id="add_output_validation",
                factor_name="natural_language_to_tool_calls",
                gap_types=["poor_quality"],
                title="Add Output Validation and Error Handling",
                description="Implement comprehensive validation for tool outputs and robust error handling",
                rationale="Validation ensures reliable tool chaining and better error recovery",
                implementation_steps=[
                    "Define output schemas for all tools",
                    "Implement runtime validation of tool outputs",
                    "Add structured error types and handling",
                    "Create fallback mechanisms for validation failures",
                    "Add logging and monitoring for validation errors"
                ],
                priority=RecommendationPriority.HIGH,
                complexity=ImplementationComplexity.LOW,
                estimated_effort="3-5 days",
                benefits=[
                    "Improved reliability",
                    "Better error debugging",
                    "Consistent output formats"
                ],
                resources=[
                    "Schema validation best practices",
                    "Error handling patterns documentation"
                ]
            )
        ])
        
        # Own Your Prompts recommendations
        templates.extend([
            RecommendationTemplate(
                template_id="implement_prompt_templates",
                factor_name="own_your_prompts",
                gap_types=["anti_pattern", "missing"],
                title="Implement Prompt Template Management",
                description="Replace hardcoded prompts with a versioned template system",
                rationale="Template-based prompts enable A/B testing, versioning, and optimization",
                implementation_steps=[
                    "Extract hardcoded prompts from source code",
                    "Create prompt template files (Jinja2, Handlebars, etc.)",
                    "Implement template rendering system",
                    "Add prompt versioning and metadata",
                    "Create testing framework for prompts",
                    "Implement prompt performance monitoring"
                ],
                priority=RecommendationPriority.HIGH,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_effort="1-2 weeks",
                benefits=[
                    "Easy prompt modification without code changes",
                    "A/B testing capabilities",
                    "Version control for prompts",
                    "Better collaboration with non-technical team members"
                ],
                prerequisites=[
                    "Identify all hardcoded prompts",
                    "Choose templating engine"
                ],
                resources=[
                    "Jinja2 documentation",
                    "Prompt engineering best practices",
                    "LangChain prompt templates"
                ],
                tech_specific={
                    'python': {
                        'code_examples': [
                            {
                                "language": "python",
                                "title": "Jinja2 Prompt Template",
                                "code": """from jinja2 import Environment, FileSystemLoader

class PromptManager:
    def __init__(self, template_dir="prompts"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def render_prompt(self, template_name, **kwargs):
        template = self.env.get_template(template_name)
        return template.render(**kwargs)

# Usage
prompt_manager = PromptManager()
prompt = prompt_manager.render_prompt(
    "search_query.txt", 
    query="python functions",
    max_results=10
)"""
                            }
                        ]
                    }
                }
            )
        ])
        
        # Own Your Context Window recommendations
        templates.extend([
            RecommendationTemplate(
                template_id="implement_context_management",
                factor_name="own_your_context_window",
                gap_types=["missing", "poor_quality"],
                title="Implement Context Window Management",
                description="Add context size monitoring, compression, and relevance filtering",
                rationale="Active context management prevents overflow and optimizes token usage",
                implementation_steps=[
                    "Implement token counting for context size monitoring",
                    "Add context size limits and warnings",
                    "Implement relevance scoring for context selection",
                    "Add context compression/summarization",
                    "Create context overflow handling",
                    "Implement context window analytics"
                ],
                priority=RecommendationPriority.HIGH,
                complexity=ImplementationComplexity.HIGH,
                estimated_effort="2-3 weeks",
                benefits=[
                    "Prevents context overflow errors",
                    "Optimized token usage and costs",
                    "Better performance with relevant context",
                    "Scalable to larger documents"
                ],
                prerequisites=[
                    "Choose tokenization library",
                    "Define relevance scoring criteria"
                ],
                resources=[
                    "tiktoken for OpenAI token counting",
                    "transformers library for tokenization",
                    "Context compression techniques"
                ],
                tech_specific={
                    'python': {
                        'resources': [
                            "tiktoken: https://github.com/openai/tiktoken",
                            "LangChain text splitters"
                        ],
                        'code_examples': [
                            {
                                "language": "python",
                                "title": "Context Window Manager",
                                "code": """import tiktoken
from typing import List, Tuple

class ContextManager:
    def __init__(self, model="gpt-3.5-turbo", max_tokens=4000):
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_tokens = max_tokens
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def compress_context(self, contexts: List[str]) -> str:
        # Sort by relevance (simplified)
        total_tokens = 0
        selected = []
        
        for context in contexts:
            tokens = self.count_tokens(context)
            if total_tokens + tokens <= self.max_tokens:
                selected.append(context)
                total_tokens += tokens
            else:
                break
        
        return "\\n".join(selected)"""
                            }
                        ]
                    }
                }
            )
        ])
        
        # Tools are Structured Outputs recommendations
        templates.extend([
            RecommendationTemplate(
                template_id="implement_structured_tool_outputs",
                factor_name="tools_are_structured_outputs",
                gap_types=["anti_pattern", "missing"],
                title="Convert Tools to Structured Outputs",
                description="Refactor tools to return structured data instead of plain text",
                rationale="Structured outputs enable reliable parsing and tool composition",
                implementation_steps=[
                    "Audit existing tools for output formats",
                    "Define output schemas for each tool",
                    "Refactor tools to return structured data",
                    "Add output validation and type checking",
                    "Update tool consumers to handle structured outputs",
                    "Add error handling for schema violations"
                ],
                priority=RecommendationPriority.CRITICAL,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_effort="1-2 weeks",
                benefits=[
                    "Reliable tool output parsing",
                    "Better tool composition",
                    "Reduced runtime errors",
                    "Improved debugging"
                ],
                resources=[
                    "JSON Schema documentation",
                    "API design best practices"
                ]
            )
        ])
        
        # Unify Execution State recommendations
        templates.extend([
            RecommendationTemplate(
                template_id="implement_unified_state_management",
                factor_name="unify_execution_state",
                gap_types=["anti_pattern", "missing"],
                title="Implement Unified State Management",
                description="Create a centralized state management system with consistency guarantees",
                rationale="Unified state prevents inconsistencies and enables reliable agent behavior",
                implementation_steps=[
                    "Design centralized state schema",
                    "Implement state management layer",
                    "Add state persistence and recovery",
                    "Implement atomic state operations",
                    "Add state validation and consistency checks",
                    "Create state monitoring and debugging tools"
                ],
                priority=RecommendationPriority.HIGH,
                complexity=ImplementationComplexity.HIGH,
                estimated_effort="2-4 weeks",
                benefits=[
                    "Consistent agent behavior",
                    "Better debugging and monitoring",
                    "Reliable state recovery",
                    "Scalable state management"
                ],
                prerequisites=[
                    "Define state schema and requirements",
                    "Choose persistence layer"
                ],
                resources=[
                    "State management patterns",
                    "Database design principles",
                    "Redux/MobX documentation for patterns"
                ]
            )
        ])
        
        return templates
    
    def generate_recommendations(
        self,
        gaps: List[Gap],
        evaluations: Dict[str, FactorEvaluation],
        analysis_result: RepositoryAnalysisResult
    ) -> List[Recommendation]:
        """
        Generate specific recommendations based on identified gaps.
        
        Args:
            gaps: List of identified gaps
            evaluations: Factor evaluations
            analysis_result: Original repository analysis results
            
        Returns:
            List of prioritized recommendations
        """
        try:
            logger.info(f"Generating recommendations for {len(gaps)} gaps")
            
            recommendations = []
            
            # Generate recommendations from templates
            for gap in gaps:
                matching_templates = [t for t in self.templates if t.matches_gap(gap)]
                
                for template in matching_templates:
                    recommendation = template.generate_recommendation(gap, analysis_result)
                    recommendations.append(recommendation)
            
            # Generate custom recommendations for specific patterns
            custom_recommendations = self._generate_custom_recommendations(
                gaps, evaluations, analysis_result
            )
            recommendations.extend(custom_recommendations)
            
            # Prioritize and deduplicate recommendations
            recommendations = self._prioritize_recommendations(recommendations)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            raise RecommendationEngineError(f"Failed to generate recommendations: {e}")
    
    def _generate_custom_recommendations(
        self,
        gaps: List[Gap],
        evaluations: Dict[str, FactorEvaluation],
        analysis_result: RepositoryAnalysisResult
    ) -> List[Recommendation]:
        """Generate custom recommendations for specific scenarios."""
        custom_recommendations = []
        
        # Check for overall architecture recommendations
        poor_factors = [name for name, eval in evaluations.items() 
                       if eval.score in [FactorScore.POOR, FactorScore.MISSING]]
        
        if len(poor_factors) >= len(evaluations) * 0.6:  # 60% or more poor factors
            custom_recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                factor_name="overall",
                title="Comprehensive 12-Factor Architecture Review",
                description="Conduct a comprehensive review and redesign of agent architecture",
                rationale="Multiple factors poorly implemented suggest need for architectural overhaul",
                implementation_steps=[
                    "Conduct architecture review with stakeholders",
                    "Create 12-factor compliance roadmap",
                    "Prioritize critical factors for immediate attention",
                    "Plan phased implementation approach",
                    "Establish monitoring and compliance tracking"
                ],
                priority=RecommendationPriority.CRITICAL,
                complexity=ImplementationComplexity.VERY_HIGH,
                estimated_effort="2-3 months",
                benefits=[
                    "Improved overall system architecture",
                    "Better maintainability and scalability",
                    "Reduced technical debt",
                    "Enhanced team productivity"
                ],
                risks=[
                    "Significant development effort required",
                    "Potential temporary disruption to development"
                ]
            ))
        
        # Technology-specific recommendations
        tech_stack = analysis_result.technology_stack
        
        if tech_stack.primary_language == 'python' and 'langchain' not in [dep.name.lower() for dep in analysis_result.dependency_analysis.get('dependencies', [])]:
            custom_recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                factor_name="natural_language_to_tool_calls",
                title="Consider LangChain Integration",
                description="Evaluate LangChain for standardized agent patterns and tool calling",
                rationale="LangChain provides pre-built patterns for many 12-factor principles",
                implementation_steps=[
                    "Evaluate LangChain compatibility with current architecture",
                    "Create proof of concept with LangChain tools",
                    "Plan migration strategy if beneficial",
                    "Implement LangChain-based tool calling"
                ],
                priority=RecommendationPriority.MEDIUM,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_effort="1-2 weeks",
                benefits=[
                    "Pre-built 12-factor patterns",
                    "Large ecosystem of tools",
                    "Community support and documentation"
                ],
                resources=[
                    "LangChain documentation",
                    "LangChain tool calling examples"
                ]
            ))
        
        return custom_recommendations
    
    def _prioritize_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Prioritize and deduplicate recommendations."""
        # Remove duplicates by title and factor
        unique_recommendations = {}
        for rec in recommendations:
            key = (rec.factor_name, rec.title)
            if key not in unique_recommendations:
                unique_recommendations[key] = rec
            else:
                # Keep the higher priority recommendation
                existing = unique_recommendations[key]
                priority_order = {
                    RecommendationPriority.CRITICAL: 4,
                    RecommendationPriority.HIGH: 3,
                    RecommendationPriority.MEDIUM: 2,
                    RecommendationPriority.LOW: 1
                }
                if priority_order[rec.priority] > priority_order[existing.priority]:
                    unique_recommendations[key] = rec
        
        # Sort by priority and complexity
        priority_order = {
            RecommendationPriority.CRITICAL: 4,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        
        complexity_order = {
            ImplementationComplexity.LOW: 1,
            ImplementationComplexity.MEDIUM: 2,
            ImplementationComplexity.HIGH: 3,
            ImplementationComplexity.VERY_HIGH: 4
        }
        
        sorted_recommendations = sorted(
            unique_recommendations.values(),
            key=lambda r: (priority_order[r.priority], complexity_order[r.complexity]),
            reverse=True
        )
        
        return sorted_recommendations
    
    def create_implementation_roadmap(
        self, 
        recommendations: List[Recommendation]
    ) -> Dict[str, any]:
        """Create a phased implementation roadmap from recommendations."""
        if not recommendations:
            return {}
        
        # Phase 1: Critical items with low-medium complexity
        phase1 = [r for r in recommendations 
                 if r.priority == RecommendationPriority.CRITICAL and 
                 r.complexity in [ImplementationComplexity.LOW, ImplementationComplexity.MEDIUM]]
        
        # Phase 2: High priority items and remaining critical items
        phase2 = [r for r in recommendations 
                 if (r.priority == RecommendationPriority.HIGH) or
                 (r.priority == RecommendationPriority.CRITICAL and r not in phase1)]
        
        # Phase 3: Medium priority items
        phase3 = [r for r in recommendations 
                 if r.priority == RecommendationPriority.MEDIUM]
        
        # Phase 4: Low priority items
        phase4 = [r for r in recommendations 
                 if r.priority == RecommendationPriority.LOW]
        
        return {
            'total_recommendations': len(recommendations),
            'phases': {
                'phase_1_immediate': {
                    'description': 'Critical fixes with immediate impact',
                    'timeline': '2-4 weeks',
                    'recommendations': [r.id for r in phase1],
                    'count': len(phase1)
                },
                'phase_2_short_term': {
                    'description': 'High priority improvements',
                    'timeline': '1-2 months',
                    'recommendations': [r.id for r in phase2],
                    'count': len(phase2)
                },
                'phase_3_medium_term': {
                    'description': 'Medium priority enhancements',
                    'timeline': '2-4 months',
                    'recommendations': [r.id for r in phase3],
                    'count': len(phase3)
                },
                'phase_4_long_term': {
                    'description': 'Nice-to-have improvements',
                    'timeline': '4+ months',
                    'recommendations': [r.id for r in phase4],
                    'count': len(phase4)
                }
            },
            'estimated_total_effort': self._calculate_total_effort(recommendations),
            'quick_wins': len([r for r in recommendations 
                             if r.complexity == ImplementationComplexity.LOW and 
                             r.priority in [RecommendationPriority.HIGH, RecommendationPriority.CRITICAL]])
        }
    
    def _calculate_total_effort(self, recommendations: List[Recommendation]) -> str:
        """Calculate estimated total effort for all recommendations."""
        # This is a simplified calculation
        effort_mapping = {
            ImplementationComplexity.LOW: 1,
            ImplementationComplexity.MEDIUM: 3,
            ImplementationComplexity.HIGH: 8,
            ImplementationComplexity.VERY_HIGH: 20
        }
        
        total_weeks = sum(effort_mapping[rec.complexity] for rec in recommendations)
        
        if total_weeks <= 4:
            return "1 month"
        elif total_weeks <= 12:
            return f"{total_weeks // 4} months"
        else:
            return f"{total_weeks // 4}+ months"