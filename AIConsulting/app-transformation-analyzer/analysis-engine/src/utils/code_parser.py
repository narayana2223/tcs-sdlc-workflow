"""
Code parsing utilities for AST analysis and code structure extraction.
Supports multiple programming languages and extracts component relationships.
"""

import ast
import os
import re
import json
import logging
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class CodeElement:
    """Represents a code element (class, function, variable, etc.)."""
    name: str
    type: str  # 'class', 'function', 'variable', 'import', 'module'
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    parent: Optional[str] = None
    parameters: List[str] = None
    return_type: Optional[str] = None
    decorators: List[str] = None
    docstring: Optional[str] = None
    complexity: int = 0
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.decorators is None:
            self.decorators = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    language: str
    lines_of_code: int
    complexity_score: int
    elements: List[CodeElement]
    imports: List[str]
    exports: List[str]
    dependencies: List[str]
    
    def __post_init__(self):
        if self.elements is None:
            self.elements = []
        if self.imports is None:
            self.imports = []
        if self.exports is None:
            self.exports = []
        if self.dependencies is None:
            self.dependencies = []


class CodeParserError(Exception):
    """Custom exception for code parsing errors."""
    pass


class PythonASTAnalyzer:
    """Python-specific AST analyzer."""
    
    def analyze_file(self, file_path: str, content: str) -> FileAnalysis:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content, filename=file_path)
            analyzer = PythonASTVisitor(file_path)
            analyzer.visit(tree)
            
            return FileAnalysis(
                file_path=file_path,
                language='python',
                lines_of_code=len([line for line in content.split('\n') if line.strip()]),
                complexity_score=analyzer.complexity_score,
                elements=analyzer.elements,
                imports=analyzer.imports,
                exports=analyzer.exports,
                dependencies=analyzer.dependencies
            )
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python file {file_path}: {e}")
            return self._create_empty_analysis(file_path, content, 'python')
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            raise CodeParserError(f"Failed to analyze Python file: {e}")


class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for Python code analysis."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.elements: List[CodeElement] = []
        self.imports: List[str] = []
        self.exports: List[str] = []
        self.dependencies: List[str] = []
        self.complexity_score = 0
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
    
    def visit_Import(self, node: ast.Import):
        """Handle import statements."""
        for alias in node.names:
            import_name = alias.name
            self.imports.append(import_name)
            self.dependencies.append(import_name)
            
            self.elements.append(CodeElement(
                name=import_name,
                type='import',
                file_path=self.file_path,
                line_number=node.lineno
            ))
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from...import statements."""
        module = node.module or ''
        for alias in node.names:
            import_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(import_name)
            self.dependencies.append(module if module else alias.name)
            
            self.elements.append(CodeElement(
                name=import_name,
                type='import',
                file_path=self.file_path,
                line_number=node.lineno
            ))
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions."""
        class_name = node.name
        parent_class = self.current_class
        self.current_class = class_name
        
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        element = CodeElement(
            name=class_name,
            type='class',
            file_path=self.file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else None,
            parent=parent_class,
            decorators=decorators,
            docstring=docstring,
            dependencies=base_classes
        )
        
        self.elements.append(element)
        self.exports.append(class_name)
        
        # Visit child nodes
        self.generic_visit(node)
        self.current_class = parent_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions."""
        func_name = node.name
        parent = self.current_class or self.current_function
        
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        self.complexity_score += complexity
        
        element = CodeElement(
            name=func_name,
            type='function',
            file_path=self.file_path,
            line_number=node.lineno,
            end_line_number=node.end_lineno if hasattr(node, 'end_lineno') else None,
            parent=parent,
            parameters=parameters,
            decorators=decorators,
            docstring=docstring,
            complexity=complexity
        )
        
        self.elements.append(element)
        
        if not self.current_class:  # Only export top-level functions
            self.exports.append(func_name)
        
        # Visit child nodes
        old_function = self.current_function
        self.current_function = func_name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)  # Same logic as regular functions
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity


class JavaScriptAnalyzer:
    """JavaScript/TypeScript code analyzer using regex patterns."""
    
    def analyze_file(self, file_path: str, content: str) -> FileAnalysis:
        """Analyze JavaScript/TypeScript file."""
        try:
            elements = []
            imports = []
            exports = []
            dependencies = []
            
            lines = content.split('\n')
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
            
            # Extract imports
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern in import_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        imports.append(match)
                        dependencies.append(match)
                        elements.append(CodeElement(
                            name=match,
                            type='import',
                            file_path=file_path,
                            line_number=i
                        ))
            
            # Extract functions
            function_patterns = [
                r'function\s+(\w+)\s*\(',
                r'(\w+)\s*:\s*function\s*\(',
                r'(\w+)\s*=\s*function\s*\(',
                r'(\w+)\s*=\s*\([^)]*\)\s*=>'
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern in function_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        elements.append(CodeElement(
                            name=match,
                            type='function',
                            file_path=file_path,
                            line_number=i
                        ))
                        exports.append(match)
            
            # Extract classes
            class_pattern = r'class\s+(\w+)'
            for i, line in enumerate(lines, 1):
                matches = re.findall(class_pattern, line)
                for match in matches:
                    elements.append(CodeElement(
                        name=match,
                        type='class',
                        file_path=file_path,
                        line_number=i
                    ))
                    exports.append(match)
            
            return FileAnalysis(
                file_path=file_path,
                language='javascript',
                lines_of_code=lines_of_code,
                complexity_score=len(elements),  # Simplified complexity
                elements=elements,
                imports=imports,
                exports=exports,
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"Error analyzing JavaScript file {file_path}: {e}")
            raise CodeParserError(f"Failed to analyze JavaScript file: {e}")


class GenericCodeAnalyzer:
    """Generic code analyzer for unsupported languages."""
    
    def analyze_file(self, file_path: str, content: str, language: str) -> FileAnalysis:
        """Basic analysis for unsupported languages."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])
        
        return FileAnalysis(
            file_path=file_path,
            language=language,
            lines_of_code=lines_of_code,
            complexity_score=0,
            elements=[],
            imports=[],
            exports=[],
            dependencies=[]
        )


class CodeParser:
    """Main code parser that supports multiple languages."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby'
    }
    
    def __init__(self):
        self.analyzers = {
            'python': PythonASTAnalyzer(),
            'javascript': JavaScriptAnalyzer(),
            'typescript': JavaScriptAnalyzer()  # Use JS analyzer for TypeScript
        }
        self.generic_analyzer = GenericCodeAnalyzer()
    
    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        _, ext = os.path.splitext(file_path)
        return self.LANGUAGE_EXTENSIONS.get(ext.lower(), 'unknown')
    
    def analyze_file(self, file_path: str, content: Optional[str] = None) -> FileAnalysis:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file
            content: File content (will be read if not provided)
            
        Returns:
            FileAnalysis: Analysis results
        """
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                raise CodeParserError(f"Failed to read file: {e}")
        
        language = self.detect_language(file_path)
        
        if language in self.analyzers:
            return self.analyzers[language].analyze_file(file_path, content)
        else:
            return self.generic_analyzer.analyze_file(file_path, content, language)
    
    def analyze_directory(
        self, 
        directory_path: str, 
        extensions: Optional[List[str]] = None
    ) -> Dict[str, FileAnalysis]:
        """
        Analyze all files in a directory.
        
        Args:
            directory_path: Path to directory
            extensions: File extensions to include (None for all supported)
            
        Returns:
            Dict mapping file paths to analysis results
        """
        results = {}
        
        if extensions is None:
            extensions = list(self.LANGUAGE_EXTENSIONS.keys())
        
        for root, dirs, files in os.walk(directory_path):
            # Skip hidden directories and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', 'env', 'build', 'dist'
            ]]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        analysis = self.analyze_file(file_path)
                        results[file_path] = analysis
                    except Exception as e:
                        logger.warning(f"Failed to analyze {file_path}: {e}")
                        continue
        
        return results
    
    def build_dependency_graph(
        self, 
        analyses: Dict[str, FileAnalysis]
    ) -> nx.DiGraph:
        """
        Build a dependency graph from file analyses.
        
        Args:
            analyses: Dictionary of file analyses
            
        Returns:
            NetworkX directed graph of dependencies
        """
        graph = nx.DiGraph()
        
        # Add nodes for all files
        for file_path, analysis in analyses.items():
            graph.add_node(file_path, **asdict(analysis))
        
        # Add edges for dependencies
        for file_path, analysis in analyses.items():
            for dependency in analysis.dependencies:
                # Try to resolve dependency to actual file
                target_file = self._resolve_dependency(dependency, analyses)
                if target_file and target_file in graph:
                    graph.add_edge(file_path, target_file)
        
        return graph
    
    def _resolve_dependency(
        self, 
        dependency: str, 
        analyses: Dict[str, FileAnalysis]
    ) -> Optional[str]:
        """Attempt to resolve a dependency string to an actual file path."""
        # Simple heuristic: look for files that export the dependency
        for file_path, analysis in analyses.items():
            if dependency in analysis.exports:
                return file_path
            
            # Check if dependency matches module/file name
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            if dependency.endswith(file_name) or file_name == dependency:
                return file_path
        
        return None
    
    def _create_empty_analysis(
        self, 
        file_path: str, 
        content: str, 
        language: str
    ) -> FileAnalysis:
        """Create an empty analysis for files that couldn't be parsed."""
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        return FileAnalysis(
            file_path=file_path,
            language=language,
            lines_of_code=lines_of_code,
            complexity_score=0,
            elements=[],
            imports=[],
            exports=[],
            dependencies=[]
        )


def calculate_project_metrics(analyses: Dict[str, FileAnalysis]) -> Dict[str, Any]:
    """
    Calculate overall project metrics from file analyses.
    
    Args:
        analyses: Dictionary of file analyses
        
    Returns:
        Dictionary of project-level metrics
    """
    if not analyses:
        return {}
    
    total_files = len(analyses)
    total_loc = sum(analysis.lines_of_code for analysis in analyses.values())
    total_complexity = sum(analysis.complexity_score for analysis in analyses.values())
    
    # Language distribution
    languages = defaultdict(int)
    for analysis in analyses.values():
        languages[analysis.language] += 1
    
    # Element type distribution
    element_types = defaultdict(int)
    for analysis in analyses.values():
        for element in analysis.elements:
            element_types[element.type] += 1
    
    # Dependency statistics
    unique_dependencies = set()
    for analysis in analyses.values():
        unique_dependencies.update(analysis.dependencies)
    
    return {
        'total_files': total_files,
        'total_lines_of_code': total_loc,
        'average_lines_per_file': total_loc / total_files if total_files > 0 else 0,
        'total_complexity': total_complexity,
        'average_complexity_per_file': total_complexity / total_files if total_files > 0 else 0,
        'language_distribution': dict(languages),
        'element_type_distribution': dict(element_types),
        'unique_dependencies': len(unique_dependencies),
        'dependency_list': list(unique_dependencies)
    }