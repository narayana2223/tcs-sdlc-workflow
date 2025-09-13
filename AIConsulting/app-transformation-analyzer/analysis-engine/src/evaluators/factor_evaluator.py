"""
12-Factor evaluation logic for AI agent development practices.
Evaluates repositories against each of the 12-factor principles and provides scoring.
"""

import re
import os
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
import json

from ..models.assessment import (
    FactorEvaluation, FactorEvidence, FactorScore, TwelveFactorDefinition,
    TWELVE_FACTOR_DEFINITIONS
)
from ..analyzers.repository_analyzer import RepositoryAnalysisResult

logger = logging.getLogger(__name__)


class FactorEvaluatorError(Exception):
    """Custom exception for factor evaluation errors."""
    pass


class BaseFactorEvaluator:
    """Base class for individual factor evaluators."""
    
    def __init__(self, factor_definition: TwelveFactorDefinition):
        """Initialize with factor definition."""
        self.definition = factor_definition
        self.evidence: List[FactorEvidence] = []
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        """
        Evaluate the factor against the repository analysis.
        
        Args:
            analysis_result: Complete repository analysis results
            
        Returns:
            FactorEvaluation with score and evidence
        """
        raise NotImplementedError("Subclasses must implement evaluate method")
    
    def _add_evidence(
        self, 
        evidence_type: str, 
        description: str, 
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        confidence: float = 1.0
    ) -> None:
        """Add evidence for the evaluation."""
        self.evidence.append(FactorEvidence(
            type=evidence_type,
            description=description,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            confidence=confidence
        ))
    
    def _search_code_patterns(
        self, 
        analysis_result: RepositoryAnalysisResult,
        patterns: List[str],
        evidence_type: str = 'positive'
    ) -> int:
        """Search for code patterns and add evidence."""
        matches = 0
        file_analyses = analysis_result.code_analysis.get('file_analyses', {})
        
        for file_path, file_analysis in file_analyses.items():
            try:
                # Get file content for pattern matching
                if hasattr(analysis_result, '_file_contents'):
                    content = analysis_result._file_contents.get(file_path, '')
                else:
                    # Try to read file content if path is available
                    content = ''
                
                for pattern in patterns:
                    regex_matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in regex_matches:
                        matches += 1
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Extract surrounding context
                        lines = content.split('\n')
                        start_line = max(0, line_num - 2)
                        end_line = min(len(lines), line_num + 2)
                        context = '\n'.join(lines[start_line:end_line])
                        
                        self._add_evidence(
                            evidence_type,
                            f"Found pattern '{pattern}' indicating {self.definition.name}",
                            file_path,
                            line_num,
                            context,
                            0.8
                        )
                        
                        # Limit evidence collection to avoid overflow
                        if matches >= 10:
                            break
                    
                    if matches >= 10:
                        break
                        
            except Exception as e:
                logger.warning(f"Error searching patterns in {file_path}: {e}")
                continue
        
        return matches
    
    def _search_dependencies(
        self, 
        analysis_result: RepositoryAnalysisResult,
        dependency_patterns: List[str],
        evidence_type: str = 'positive'
    ) -> int:
        """Search for specific dependencies indicating factor implementation."""
        matches = 0
        dependencies = analysis_result.dependency_analysis.get('dependencies', [])
        
        for dep in dependencies:
            dep_name = dep.name.lower()
            for pattern in dependency_patterns:
                if pattern.lower() in dep_name:
                    matches += 1
                    self._add_evidence(
                        evidence_type,
                        f"Found dependency '{dep.name}' indicating {self.definition.name}",
                        dep.source_file,
                        dep.line_number,
                        confidence=0.9
                    )
                    break
        
        return matches
    
    def _search_file_patterns(
        self, 
        analysis_result: RepositoryAnalysisResult,
        file_patterns: List[str],
        evidence_type: str = 'positive'
    ) -> int:
        """Search for file patterns indicating factor implementation."""
        matches = 0
        file_analyses = analysis_result.code_analysis.get('file_analyses', {})
        
        for file_path in file_analyses.keys():
            filename = os.path.basename(file_path).lower()
            for pattern in file_patterns:
                if pattern.lower() in filename or re.match(pattern, filename, re.IGNORECASE):
                    matches += 1
                    self._add_evidence(
                        evidence_type,
                        f"Found file '{filename}' indicating {self.definition.name}",
                        file_path,
                        confidence=0.7
                    )
                    break
        
        return matches


class NaturalLanguageToToolCallsEvaluator(BaseFactorEvaluator):
    """Evaluator for Natural Language to Tool Calls factor."""
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        self.evidence = []
        score = FactorScore.UNKNOWN
        
        # Positive indicators
        positive_patterns = [
            r'function_call|tool_call|function_calling',
            r'@tool|@function|@api_call',
            r'schema.*validation|pydantic|marshmallow',
            r'structured.*output|json.*schema',
            r'openai.*functions|anthropic.*tools'
        ]
        
        positive_deps = [
            'pydantic', 'marshmallow', 'jsonschema', 'openai', 'anthropic',
            'langchain', 'llama-index'
        ]
        
        positive_files = [
            r'.*tool.*\.py', r'.*function.*\.py', r'.*schema.*\.py',
            r'tools\.json', r'functions\.json'
        ]
        
        # Negative indicators
        negative_patterns = [
            r'raw.*text.*output|plain.*text.*response',
            r'string.*parsing|text.*parsing.*command',
            r'print\(.*\)|console\.log\(.*\)'  # Raw output without structure
        ]
        
        # Search for indicators
        positive_code = self._search_code_patterns(analysis_result, positive_patterns, 'positive')
        positive_deps_found = self._search_dependencies(analysis_result, positive_deps, 'positive')
        positive_files_found = self._search_file_patterns(analysis_result, positive_files, 'positive')
        negative_code = self._search_code_patterns(analysis_result, negative_patterns, 'negative')
        
        # Calculate score
        positive_score = positive_code + positive_deps_found + positive_files_found
        negative_score = negative_code
        
        if positive_score >= 5 and negative_score <= 2:
            score = FactorScore.EXCELLENT
            reasoning = f"Strong evidence of structured tool calling ({positive_score} indicators)"
        elif positive_score >= 3 and negative_score <= 5:
            score = FactorScore.GOOD
            reasoning = f"Good tool calling implementation ({positive_score} indicators, {negative_score} concerns)"
        elif positive_score >= 1:
            score = FactorScore.FAIR
            reasoning = f"Some tool calling patterns found ({positive_score} indicators, {negative_score} concerns)"
        elif negative_score > 5:
            score = FactorScore.POOR
            reasoning = f"Mostly raw text outputs found ({negative_score} anti-patterns)"
        else:
            score = FactorScore.MISSING
            reasoning = "No evidence of structured tool calling found"
        
        return FactorEvaluation(
            factor_name=self.definition.name,
            factor_description=self.definition.description,
            score=score,
            score_reasoning=reasoning,
            evidence=self.evidence.copy(),
            confidence=min(1.0, (positive_score + negative_score) / 10.0),
            weight=self.definition.weight
        )


class OwnYourPromptsEvaluator(BaseFactorEvaluator):
    """Evaluator for Own Your Prompts factor."""
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        self.evidence = []
        score = FactorScore.UNKNOWN
        
        # Positive indicators
        positive_patterns = [
            r'prompt.*template|template.*prompt',
            r'jinja2|handlebars|mustache',
            r'prompt.*version|version.*prompt',
            r'prompt.*test|test.*prompt'
        ]
        
        positive_deps = [
            'jinja2', 'handlebars', 'mustache', 'promptflow', 'langchain'
        ]
        
        positive_files = [
            r'.*prompt.*\.txt', r'.*prompt.*\.json', r'.*template.*\.txt',
            r'prompts/', r'templates/'
        ]
        
        # Negative indicators  
        negative_patterns = [
            r'f".*{.*}.*"',  # F-strings for prompts
            r'hardcoded.*prompt|static.*prompt',
            r'prompt.*=.*"[^"]{50,}"'  # Long hardcoded prompts
        ]
        
        # Search for indicators
        positive_code = self._search_code_patterns(analysis_result, positive_patterns, 'positive')
        positive_deps_found = self._search_dependencies(analysis_result, positive_deps, 'positive')
        positive_files_found = self._search_file_patterns(analysis_result, positive_files, 'positive')
        negative_code = self._search_code_patterns(analysis_result, negative_patterns, 'negative')
        
        # Check for prompt directories
        file_analyses = analysis_result.code_analysis.get('file_analyses', {})
        prompt_dirs = sum(1 for path in file_analyses.keys() 
                         if 'prompt' in path.lower() or 'template' in path.lower())
        
        # Calculate score
        positive_score = positive_code + positive_deps_found + positive_files_found + prompt_dirs
        negative_score = negative_code
        
        if positive_score >= 5 and negative_score <= 2:
            score = FactorScore.EXCELLENT
            reasoning = f"Excellent prompt management ({positive_score} indicators)"
        elif positive_score >= 3:
            score = FactorScore.GOOD
            reasoning = f"Good prompt templating found ({positive_score} indicators)"
        elif positive_score >= 1:
            score = FactorScore.FAIR
            reasoning = f"Some prompt management ({positive_score} indicators, {negative_score} hardcoded)"
        elif negative_score > 3:
            score = FactorScore.POOR
            reasoning = f"Mostly hardcoded prompts ({negative_score} instances)"
        else:
            score = FactorScore.MISSING
            reasoning = "No prompt management system found"
        
        return FactorEvaluation(
            factor_name=self.definition.name,
            factor_description=self.definition.description,
            score=score,
            score_reasoning=reasoning,
            evidence=self.evidence.copy(),
            confidence=min(1.0, (positive_score + negative_score) / 8.0),
            weight=self.definition.weight
        )


class OwnYourContextWindowEvaluator(BaseFactorEvaluator):
    """Evaluator for Own Your Context Window factor."""
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        self.evidence = []
        score = FactorScore.UNKNOWN
        
        # Positive indicators
        positive_patterns = [
            r'context.*window|window.*context|context.*limit',
            r'token.*count|count.*token|max_tokens',
            r'context.*compression|compress.*context',
            r'relevance.*score|ranking.*context',
            r'context.*overflow|truncate.*context'
        ]
        
        positive_deps = [
            'tiktoken', 'transformers', 'sentence-transformers', 'langchain'
        ]
        
        positive_files = [
            r'.*context.*\.py', r'.*token.*\.py', r'.*compression.*\.py'
        ]
        
        # Search for indicators
        positive_code = self._search_code_patterns(analysis_result, positive_patterns, 'positive')
        positive_deps_found = self._search_dependencies(analysis_result, positive_deps, 'positive')
        positive_files_found = self._search_file_patterns(analysis_result, positive_files, 'positive')
        
        # Calculate score
        positive_score = positive_code + positive_deps_found + positive_files_found
        
        if positive_score >= 4:
            score = FactorScore.EXCELLENT
            reasoning = f"Strong context window management ({positive_score} indicators)"
        elif positive_score >= 2:
            score = FactorScore.GOOD
            reasoning = f"Good context management ({positive_score} indicators)"
        elif positive_score >= 1:
            score = FactorScore.FAIR
            reasoning = f"Basic context awareness ({positive_score} indicators)"
        else:
            score = FactorScore.MISSING
            reasoning = "No context window management found"
        
        return FactorEvaluation(
            factor_name=self.definition.name,
            factor_description=self.definition.description,
            score=score,
            score_reasoning=reasoning,
            evidence=self.evidence.copy(),
            confidence=min(1.0, positive_score / 5.0),
            weight=self.definition.weight
        )


class ToolsAreStructuredOutputsEvaluator(BaseFactorEvaluator):
    """Evaluator for Tools are Structured Outputs factor."""
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        self.evidence = []
        score = FactorScore.UNKNOWN
        
        # Positive indicators
        positive_patterns = [
            r'return.*json|json.*return|json\.dumps',
            r'pydantic.*BaseModel|dataclass',
            r'schema.*validation|validate.*schema',
            r'typing\.|Type\[|Optional\[|List\[|Dict\['
        ]
        
        positive_deps = [
            'pydantic', 'dataclasses', 'marshmallow', 'jsonschema', 'typing-extensions'
        ]
        
        # Negative indicators
        negative_patterns = [
            r'return.*str|print\(|console\.log',
            r'plain.*text.*output|raw.*string'
        ]
        
        # Search for indicators
        positive_code = self._search_code_patterns(analysis_result, positive_patterns, 'positive')
        positive_deps_found = self._search_dependencies(analysis_result, positive_deps, 'positive')
        negative_code = self._search_code_patterns(analysis_result, negative_patterns, 'negative')
        
        # Check technology stack for type safety
        tech_stack = analysis_result.technology_stack
        has_typing = 'typescript' in tech_stack.languages or tech_stack.primary_language == 'typescript'
        if has_typing:
            self._add_evidence('positive', 'TypeScript usage indicates structured outputs', confidence=0.8)
            positive_code += 2
        
        # Calculate score
        positive_score = positive_code + positive_deps_found
        negative_score = negative_code
        
        if positive_score >= 5 and negative_score <= 2:
            score = FactorScore.EXCELLENT
            reasoning = f"Excellent structured output usage ({positive_score} indicators)"
        elif positive_score >= 3:
            score = FactorScore.GOOD
            reasoning = f"Good structured outputs ({positive_score} indicators)"
        elif positive_score >= 1:
            score = FactorScore.FAIR
            reasoning = f"Some structured outputs ({positive_score} indicators, {negative_score} unstructured)"
        elif negative_score > 3:
            score = FactorScore.POOR
            reasoning = f"Mostly unstructured outputs ({negative_score} instances)"
        else:
            score = FactorScore.MISSING
            reasoning = "No structured output patterns found"
        
        return FactorEvaluation(
            factor_name=self.definition.name,
            factor_description=self.definition.description,
            score=score,
            score_reasoning=reasoning,
            evidence=self.evidence.copy(),
            confidence=min(1.0, (positive_score + negative_score) / 8.0),
            weight=self.definition.weight
        )


class UnifyExecutionStateEvaluator(BaseFactorEvaluator):
    """Evaluator for Unify Execution State factor."""
    
    def evaluate(self, analysis_result: RepositoryAnalysisResult) -> FactorEvaluation:
        self.evidence = []
        score = FactorScore.UNKNOWN
        
        # Positive indicators
        positive_patterns = [
            r'state.*manager|manager.*state',
            r'redux|vuex|mobx|context.*api',
            r'database.*transaction|atomic.*operation',
            r'state.*persistence|persist.*state',
            r'session.*management|session.*store'
        ]
        
        positive_deps = [
            'redux', 'vuex', 'mobx', 'sqlalchemy', 'django', 'flask-session'
        ]
        
        positive_files = [
            r'.*state.*\.py', r'.*store.*\.py', r'.*session.*\.py'
        ]
        
        # Search for indicators
        positive_code = self._search_code_patterns(analysis_result, positive_patterns, 'positive')
        positive_deps_found = self._search_dependencies(analysis_result, positive_deps, 'positive')
        positive_files_found = self._search_file_patterns(analysis_result, positive_files, 'positive')
        
        # Calculate score
        positive_score = positive_code + positive_deps_found + positive_files_found
        
        if positive_score >= 4:
            score = FactorScore.EXCELLENT
            reasoning = f"Strong state management ({positive_score} indicators)"
        elif positive_score >= 2:
            score = FactorScore.GOOD
            reasoning = f"Good state unification ({positive_score} indicators)"
        elif positive_score >= 1:
            score = FactorScore.FAIR
            reasoning = f"Basic state management ({positive_score} indicators)"
        else:
            score = FactorScore.MISSING
            reasoning = "No unified state management found"
        
        return FactorEvaluation(
            factor_name=self.definition.name,
            factor_description=self.definition.description,
            score=score,
            score_reasoning=reasoning,
            evidence=self.evidence.copy(),
            confidence=min(1.0, positive_score / 5.0),
            weight=self.definition.weight
        )


class TwelveFactorEvaluator:
    """Main orchestrator for 12-factor evaluation."""
    
    def __init__(self):
        """Initialize the evaluator with all factor evaluators."""
        self.evaluators = {
            'natural_language_to_tool_calls': NaturalLanguageToToolCallsEvaluator(
                TWELVE_FACTOR_DEFINITIONS['natural_language_to_tool_calls']
            ),
            'own_your_prompts': OwnYourPromptsEvaluator(
                TWELVE_FACTOR_DEFINITIONS['own_your_prompts']
            ),
            'own_your_context_window': OwnYourContextWindowEvaluator(
                TWELVE_FACTOR_DEFINITIONS['own_your_context_window']
            ),
            'tools_are_structured_outputs': ToolsAreStructuredOutputsEvaluator(
                TWELVE_FACTOR_DEFINITIONS['tools_are_structured_outputs']
            ),
            'unify_execution_state': UnifyExecutionStateEvaluator(
                TWELVE_FACTOR_DEFINITIONS['unify_execution_state']
            )
            # Additional evaluators would be added here following the same pattern
        }
    
    def evaluate_all_factors(
        self, 
        analysis_result: RepositoryAnalysisResult
    ) -> Dict[str, FactorEvaluation]:
        """
        Evaluate all 12 factors against the repository analysis.
        
        Args:
            analysis_result: Complete repository analysis results
            
        Returns:
            Dictionary mapping factor names to evaluations
        """
        try:
            logger.info("Starting 12-factor evaluation")
            
            evaluations = {}
            
            for factor_name, evaluator in self.evaluators.items():
                try:
                    logger.debug(f"Evaluating factor: {factor_name}")
                    evaluation = evaluator.evaluate(analysis_result)
                    evaluations[factor_name] = evaluation
                    
                    logger.debug(f"Factor {factor_name} scored {evaluation.score.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate factor {factor_name}: {e}")
                    # Create a default evaluation for failed factors
                    evaluations[factor_name] = FactorEvaluation(
                        factor_name=factor_name,
                        factor_description=TWELVE_FACTOR_DEFINITIONS[factor_name].description,
                        score=FactorScore.UNKNOWN,
                        score_reasoning=f"Evaluation failed: {str(e)}",
                        evidence=[],
                        confidence=0.0,
                        weight=TWELVE_FACTOR_DEFINITIONS[factor_name].weight
                    )
            
            # Add placeholder evaluations for factors not yet implemented
            for factor_name in TWELVE_FACTOR_DEFINITIONS:
                if factor_name not in evaluations:
                    evaluations[factor_name] = FactorEvaluation(
                        factor_name=factor_name,
                        factor_description=TWELVE_FACTOR_DEFINITIONS[factor_name].description,
                        score=FactorScore.UNKNOWN,
                        score_reasoning="Evaluation not yet implemented",
                        evidence=[],
                        confidence=0.0,
                        weight=TWELVE_FACTOR_DEFINITIONS[factor_name].weight
                    )
            
            logger.info(f"Completed 12-factor evaluation: {len(evaluations)} factors assessed")
            return evaluations
            
        except Exception as e:
            logger.error(f"12-factor evaluation failed: {e}")
            raise FactorEvaluatorError(f"Failed to evaluate factors: {e}")
    
    def calculate_overall_score(self, evaluations: Dict[str, FactorEvaluation]) -> Tuple[float, float]:
        """
        Calculate overall scores from factor evaluations.
        
        Args:
            evaluations: Dictionary of factor evaluations
            
        Returns:
            Tuple of (simple_average_score, weighted_score)
        """
        if not evaluations:
            return 0.0, 0.0
        
        # Simple average
        valid_scores = [eval.score.value for eval in evaluations.values() 
                       if eval.score != FactorScore.UNKNOWN]
        simple_avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
        
        # Weighted average
        total_weighted = 0.0
        total_weight = 0.0
        
        for evaluation in evaluations.values():
            if evaluation.score != FactorScore.UNKNOWN:
                total_weighted += evaluation.score.value * evaluation.weight * evaluation.confidence
                total_weight += evaluation.weight * evaluation.confidence
        
        weighted_avg = total_weighted / total_weight if total_weight > 0 else 0.0
        
        return simple_avg, weighted_avg
    
    def assign_grade(self, weighted_score: float) -> str:
        """Assign letter grade based on weighted score."""
        if weighted_score >= 4.5:
            return 'A'
        elif weighted_score >= 3.5:
            return 'B'
        elif weighted_score >= 2.5:
            return 'C'
        elif weighted_score >= 1.5:
            return 'D'
        else:
            return 'F'