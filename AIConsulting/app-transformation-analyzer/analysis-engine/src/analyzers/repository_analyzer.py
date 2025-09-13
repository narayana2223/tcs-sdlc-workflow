"""
Core repository analysis system that orchestrates Git operations, code analysis,
component mapping, and technology detection to provide comprehensive insights.
"""

import os
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import networkx as nx
from collections import defaultdict, Counter

from ..utils.git_helper import GitHelper, GitRepositoryError, get_repository_statistics
from ..utils.code_parser import CodeParser, FileAnalysis, calculate_project_metrics
from ..utils.dependency_analyzer import DependencyAnalyzer, DependencyAnalyzerError

logger = logging.getLogger(__name__)


@dataclass
class ComponentRelationship:
    """Represents a relationship between code components."""
    source_component: str
    target_component: str
    relationship_type: str  # 'imports', 'extends', 'calls', 'references'
    strength: float  # 0.0 to 1.0
    file_path: str
    line_number: Optional[int] = None


@dataclass
class TechnologyStack:
    """Represents detected technology stack information."""
    primary_language: str
    languages: Dict[str, float]  # language -> percentage
    frameworks: List[str]
    databases: List[str]
    web_servers: List[str]
    build_tools: List[str]
    testing_frameworks: List[str]
    deployment_tools: List[str]
    package_managers: List[str]
    confidence_score: float


@dataclass
class ComponentMap:
    """Map of all components and their relationships."""
    components: Dict[str, Any]
    relationships: List[ComponentRelationship]
    clusters: List[List[str]]
    dependency_graph: nx.DiGraph
    complexity_metrics: Dict[str, float]


@dataclass
class RepositoryAnalysisResult:
    """Complete repository analysis result."""
    repository_info: Dict[str, Any]
    technology_stack: TechnologyStack
    component_map: ComponentMap
    code_analysis: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    analysis_timestamp: str


class RepositoryConnector:
    """Handles Git repository operations and data extraction."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the repository connector."""
        self.git_helper = GitHelper(temp_dir)
        self.current_repo_path: Optional[str] = None
        self.current_repo_url: Optional[str] = None
    
    def connect_repository(
        self, 
        repo_url: str, 
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Connect to and clone a Git repository.
        
        Args:
            repo_url: Repository URL (GitHub, GitLab, etc.)
            branch: Specific branch to analyze
            depth: Shallow clone depth for faster cloning
            
        Returns:
            Repository information dictionary
            
        Raises:
            GitRepositoryError: If connection fails
        """
        try:
            logger.info(f"Connecting to repository: {repo_url}")
            
            # Clone repository
            self.current_repo_path = self.git_helper.clone_repository(
                repo_url, branch, depth
            )
            self.current_repo_url = repo_url
            
            # Get repository information
            repo_info = self.git_helper.get_repository_info(self.current_repo_path)
            repo_stats = get_repository_statistics(self.current_repo_path)
            
            # Combine information
            combined_info = {**repo_info, **repo_stats}
            
            logger.info(f"Successfully connected to repository with {combined_info.get('total_files', 0)} files")
            return combined_info
            
        except Exception as e:
            logger.error(f"Failed to connect to repository {repo_url}: {e}")
            raise GitRepositoryError(f"Repository connection failed: {e}")
    
    def get_file_tree(self, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get the file tree for the current repository.
        
        Args:
            extensions: File extensions to filter by
            
        Returns:
            List of file information dictionaries
        """
        if not self.current_repo_path:
            raise GitRepositoryError("No repository connected")
        
        return self.git_helper.get_file_list(self.current_repo_path, extensions)
    
    def get_file_content(self, file_path: str) -> str:
        """Get content of a specific file."""
        if not self.current_repo_path:
            raise GitRepositoryError("No repository connected")
        
        return self.git_helper.get_file_content(self.current_repo_path, file_path)
    
    def disconnect(self) -> None:
        """Disconnect and clean up the repository."""
        if self.current_repo_url:
            self.git_helper.cleanup_repository(self.current_repo_url)
            self.current_repo_path = None
            self.current_repo_url = None


class CodeAnalyzer:
    """Performs static code analysis and extracts structural information."""
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.parser = CodeParser()
    
    def analyze_codebase(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze entire codebase for structure and quality.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Code analysis results
        """
        try:
            logger.info("Starting codebase analysis")
            
            # Analyze all files
            file_analyses = self.parser.analyze_directory(repo_path)
            
            if not file_analyses:
                logger.warning("No analyzable files found in repository")
                return self._empty_code_analysis()
            
            # Build dependency graph
            dependency_graph = self.parser.build_dependency_graph(file_analyses)
            
            # Calculate project metrics
            project_metrics = calculate_project_metrics(file_analyses)
            
            # Extract code elements
            all_elements = []
            for analysis in file_analyses.values():
                all_elements.extend(analysis.elements)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(file_analyses)
            
            logger.info(f"Analyzed {len(file_analyses)} files with {len(all_elements)} code elements")
            
            return {
                'file_analyses': file_analyses,
                'dependency_graph': dependency_graph,
                'project_metrics': project_metrics,
                'quality_metrics': quality_metrics,
                'code_elements': all_elements,
                'analysis_summary': {
                    'total_files': len(file_analyses),
                    'total_elements': len(all_elements),
                    'languages_detected': project_metrics.get('language_distribution', {}),
                    'avg_complexity': project_metrics.get('average_complexity_per_file', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            raise Exception(f"Code analysis failed: {e}")
    
    def _calculate_quality_metrics(self, file_analyses: Dict[str, FileAnalysis]) -> Dict[str, float]:
        """Calculate code quality metrics."""
        if not file_analyses:
            return {}
        
        total_complexity = sum(analysis.complexity_score for analysis in file_analyses.values())
        total_files = len(file_analyses)
        total_loc = sum(analysis.lines_of_code for analysis in file_analyses.values())
        
        # Calculate various quality metrics
        avg_complexity = total_complexity / total_files if total_files > 0 else 0
        avg_file_size = total_loc / total_files if total_files > 0 else 0
        
        # Maintainability index (simplified)
        maintainability_index = max(0, 171 - 5.2 * avg_complexity - 0.23 * avg_file_size)
        
        return {
            'maintainability_index': maintainability_index,
            'average_complexity': avg_complexity,
            'average_file_size': avg_file_size,
            'total_complexity': total_complexity,
            'complexity_density': total_complexity / total_loc if total_loc > 0 else 0
        }
    
    def _empty_code_analysis(self) -> Dict[str, Any]:
        """Return empty code analysis structure."""
        return {
            'file_analyses': {},
            'dependency_graph': nx.DiGraph(),
            'project_metrics': {},
            'quality_metrics': {},
            'code_elements': [],
            'analysis_summary': {
                'total_files': 0,
                'total_elements': 0,
                'languages_detected': {},
                'avg_complexity': 0
            }
        }


class ComponentMapper:
    """Maps component relationships and creates architectural views."""
    
    def __init__(self):
        """Initialize the component mapper."""
        pass
    
    def create_component_map(
        self, 
        code_analysis: Dict[str, Any],
        dependency_analysis: Dict[str, Any]
    ) -> ComponentMap:
        """
        Create a comprehensive component map.
        
        Args:
            code_analysis: Results from code analysis
            dependency_analysis: Results from dependency analysis
            
        Returns:
            ComponentMap with relationships and structure
        """
        try:
            logger.info("Creating component map")
            
            # Extract components from code analysis
            components = self._extract_components(code_analysis)
            
            # Extract relationships
            relationships = self._extract_relationships(code_analysis)
            
            # Build dependency graph
            dependency_graph = self._build_component_graph(components, relationships)
            
            # Identify clusters/modules
            clusters = self._identify_clusters(dependency_graph)
            
            # Calculate complexity metrics
            complexity_metrics = self._calculate_complexity_metrics(
                components, relationships, dependency_graph
            )
            
            logger.info(f"Created component map with {len(components)} components and {len(relationships)} relationships")
            
            return ComponentMap(
                components=components,
                relationships=relationships,
                clusters=clusters,
                dependency_graph=dependency_graph,
                complexity_metrics=complexity_metrics
            )
            
        except Exception as e:
            logger.error(f"Component mapping failed: {e}")
            raise Exception(f"Component mapping failed: {e}")
    
    def _extract_components(self, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract components from code analysis."""
        components = {}
        
        file_analyses = code_analysis.get('file_analyses', {})
        
        for file_path, analysis in file_analyses.items():
            # File-level component
            file_component = {
                'type': 'file',
                'name': os.path.basename(file_path),
                'path': file_path,
                'language': analysis.language,
                'lines_of_code': analysis.lines_of_code,
                'complexity': analysis.complexity_score,
                'elements': len(analysis.elements)
            }
            components[file_path] = file_component
            
            # Element-level components
            for element in analysis.elements:
                element_key = f"{file_path}::{element.name}"
                components[element_key] = {
                    'type': element.type,
                    'name': element.name,
                    'file': file_path,
                    'line_number': element.line_number,
                    'complexity': element.complexity,
                    'parent': element.parent
                }
        
        return components
    
    def _extract_relationships(self, code_analysis: Dict[str, Any]) -> List[ComponentRelationship]:
        """Extract relationships between components."""
        relationships = []
        
        file_analyses = code_analysis.get('file_analyses', {})
        
        for file_path, analysis in file_analyses.items():
            # Import relationships
            for import_name in analysis.imports:
                relationships.append(ComponentRelationship(
                    source_component=file_path,
                    target_component=import_name,
                    relationship_type='imports',
                    strength=1.0,
                    file_path=file_path
                ))
            
            # Dependency relationships
            for dependency in analysis.dependencies:
                relationships.append(ComponentRelationship(
                    source_component=file_path,
                    target_component=dependency,
                    relationship_type='depends_on',
                    strength=0.8,
                    file_path=file_path
                ))
        
        return relationships
    
    def _build_component_graph(
        self, 
        components: Dict[str, Any], 
        relationships: List[ComponentRelationship]
    ) -> nx.DiGraph:
        """Build a NetworkX graph of components."""
        graph = nx.DiGraph()
        
        # Add nodes
        for comp_id, comp_data in components.items():
            graph.add_node(comp_id, **comp_data)
        
        # Add edges
        for rel in relationships:
            if rel.source_component in graph and rel.target_component in graph:
                graph.add_edge(
                    rel.source_component,
                    rel.target_component,
                    relationship_type=rel.relationship_type,
                    strength=rel.strength
                )
        
        return graph
    
    def _identify_clusters(self, graph: nx.DiGraph) -> List[List[str]]:
        """Identify clusters/modules in the component graph."""
        if not graph.nodes():
            return []
        
        try:
            # Convert to undirected for clustering
            undirected = graph.to_undirected()
            
            # Simple clustering based on connected components
            clusters = list(nx.connected_components(undirected))
            return [list(cluster) for cluster in clusters]
            
        except Exception as e:
            logger.warning(f"Clustering failed: {e}")
            return []
    
    def _calculate_complexity_metrics(
        self, 
        components: Dict[str, Any],
        relationships: List[ComponentRelationship],
        graph: nx.DiGraph
    ) -> Dict[str, float]:
        """Calculate complexity metrics for the component map."""
        if not graph.nodes():
            return {}
        
        try:
            # Graph-level metrics
            density = nx.density(graph)
            
            # Centrality metrics
            in_degree_centrality = nx.in_degree_centrality(graph)
            out_degree_centrality = nx.out_degree_centrality(graph)
            
            # Average centrality
            avg_in_centrality = sum(in_degree_centrality.values()) / len(in_degree_centrality)
            avg_out_centrality = sum(out_degree_centrality.values()) / len(out_degree_centrality)
            
            return {
                'graph_density': density,
                'average_in_degree_centrality': avg_in_centrality,
                'average_out_degree_centrality': avg_out_centrality,
                'total_components': len(components),
                'total_relationships': len(relationships),
                'cyclomatic_complexity': self._calculate_cyclomatic_complexity(graph)
            }
            
        except Exception as e:
            logger.warning(f"Complexity metrics calculation failed: {e}")
            return {}
    
    def _calculate_cyclomatic_complexity(self, graph: nx.DiGraph) -> float:
        """Calculate cyclomatic complexity of the graph."""
        try:
            # V - E + 2P (vertices - edges + 2*connected_components)
            V = graph.number_of_nodes()
            E = graph.number_of_edges()
            P = nx.number_weakly_connected_components(graph)
            
            return max(1, E - V + 2 * P)
            
        except Exception:
            return 1.0


class TechnologyDetector:
    """Detects technology stack and frameworks used in the repository."""
    
    FRAMEWORK_INDICATORS = {
        'react': ['react', 'jsx', 'tsx', 'package.json'],
        'angular': ['@angular', 'angular.json', 'ng-'],
        'vue': ['vue', '.vue', 'vue.config.js'],
        'django': ['django', 'manage.py', 'settings.py'],
        'flask': ['flask', 'app.py', 'wsgi.py'],
        'spring': ['springframework', 'pom.xml', '@SpringBootApplication'],
        'express': ['express', 'app.js', 'server.js'],
        'rails': ['rails', 'Gemfile', 'config/routes.rb'],
        'laravel': ['laravel', 'artisan', 'composer.json']
    }
    
    DATABASE_INDICATORS = {
        'mysql': ['mysql', 'mysqldump', 'my.cnf'],
        'postgresql': ['postgresql', 'postgres', 'pg_'],
        'mongodb': ['mongodb', 'mongo', 'mongoose'],
        'redis': ['redis', 'redis.conf'],
        'sqlite': ['sqlite', '.db', '.sqlite']
    }
    
    BUILD_TOOL_INDICATORS = {
        'webpack': ['webpack.config.js', 'webpack'],
        'maven': ['pom.xml', 'mvn'],
        'gradle': ['build.gradle', 'gradlew'],
        'npm': ['package.json', 'npm'],
        'yarn': ['yarn.lock', 'yarn'],
        'make': ['Makefile', 'make'],
        'cmake': ['CMakeLists.txt', 'cmake']
    }
    
    def detect_technology_stack(
        self, 
        repo_path: str,
        code_analysis: Dict[str, Any],
        dependency_analysis: Dict[str, Any]
    ) -> TechnologyStack:
        """
        Detect the technology stack used in the repository.
        
        Args:
            repo_path: Path to the repository
            code_analysis: Code analysis results
            dependency_analysis: Dependency analysis results
            
        Returns:
            TechnologyStack information
        """
        try:
            logger.info("Detecting technology stack")
            
            # Language detection from code analysis
            languages = self._detect_languages(code_analysis)
            primary_language = max(languages.items(), key=lambda x: x[1])[0] if languages else 'unknown'
            
            # Framework detection
            frameworks = self._detect_frameworks(repo_path, code_analysis, dependency_analysis)
            
            # Database detection
            databases = self._detect_databases(repo_path, dependency_analysis)
            
            # Build tools detection
            build_tools = self._detect_build_tools(repo_path, dependency_analysis)
            
            # Package managers from dependency analysis
            package_managers = list(dependency_analysis.get('package_managers', {}).keys())
            
            # Testing frameworks (basic detection)
            testing_frameworks = self._detect_testing_frameworks(dependency_analysis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                languages, frameworks, databases, build_tools
            )
            
            logger.info(f"Detected primary language: {primary_language}, frameworks: {frameworks}")
            
            return TechnologyStack(
                primary_language=primary_language,
                languages=languages,
                frameworks=frameworks,
                databases=databases,
                web_servers=[],  # Would need more sophisticated detection
                build_tools=build_tools,
                testing_frameworks=testing_frameworks,
                deployment_tools=[],  # Would need more sophisticated detection
                package_managers=package_managers,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Technology detection failed: {e}")
            raise Exception(f"Technology detection failed: {e}")
    
    def _detect_languages(self, code_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Detect programming languages and their usage percentages."""
        project_metrics = code_analysis.get('project_metrics', {})
        return project_metrics.get('language_distribution', {})
    
    def _detect_frameworks(
        self, 
        repo_path: str, 
        code_analysis: Dict[str, Any], 
        dependency_analysis: Dict[str, Any]
    ) -> List[str]:
        """Detect frameworks used in the project."""
        detected_frameworks = []
        
        # Check file contents and dependencies
        all_content = self._get_all_text_content(repo_path, code_analysis)
        dependencies = dependency_analysis.get('dependencies', [])
        dependency_names = [dep.name.lower() for dep in dependencies]
        
        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            score = 0
            for indicator in indicators:
                # Check in dependencies
                if any(indicator.lower() in dep_name for dep_name in dependency_names):
                    score += 2
                
                # Check in file content
                if indicator.lower() in all_content.lower():
                    score += 1
            
            if score >= 2:  # Threshold for detection
                detected_frameworks.append(framework)
        
        return detected_frameworks
    
    def _detect_databases(self, repo_path: str, dependency_analysis: Dict[str, Any]) -> List[str]:
        """Detect databases used in the project."""
        detected_databases = []
        
        dependencies = dependency_analysis.get('dependencies', [])
        dependency_names = [dep.name.lower() for dep in dependencies]
        
        for database, indicators in self.DATABASE_INDICATORS.items():
            for indicator in indicators:
                if any(indicator.lower() in dep_name for dep_name in dependency_names):
                    detected_databases.append(database)
                    break
        
        return detected_databases
    
    def _detect_build_tools(self, repo_path: str, dependency_analysis: Dict[str, Any]) -> List[str]:
        """Detect build tools used in the project."""
        detected_tools = []
        
        # Check for config files
        for tool, indicators in self.BUILD_TOOL_INDICATORS.items():
            for indicator in indicators:
                if self._file_exists_in_repo(repo_path, indicator):
                    detected_tools.append(tool)
                    break
        
        return detected_tools
    
    def _detect_testing_frameworks(self, dependency_analysis: Dict[str, Any]) -> List[str]:
        """Detect testing frameworks from dependencies."""
        testing_frameworks = []
        
        dependencies = dependency_analysis.get('dependencies', [])
        test_indicators = ['test', 'jest', 'mocha', 'pytest', 'junit', 'rspec', 'phpunit']
        
        for dep in dependencies:
            dep_name = dep.name.lower()
            for indicator in test_indicators:
                if indicator in dep_name and dep.type in ['dev', 'test']:
                    testing_frameworks.append(indicator)
                    break
        
        return list(set(testing_frameworks))
    
    def _get_all_text_content(self, repo_path: str, code_analysis: Dict[str, Any]) -> str:
        """Get concatenated text content for pattern matching."""
        content_parts = []
        
        file_analyses = code_analysis.get('file_analyses', {})
        for file_path in list(file_analyses.keys())[:50]:  # Limit for performance
            try:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_parts.append(f.read()[:10000])  # Limit per file
            except Exception:
                continue
        
        return ' '.join(content_parts)
    
    def _file_exists_in_repo(self, repo_path: str, filename: str) -> bool:
        """Check if a file exists anywhere in the repository."""
        for root, dirs, files in os.walk(repo_path):
            if filename in files:
                return True
        return False
    
    def _calculate_confidence_score(
        self, 
        languages: Dict[str, float],
        frameworks: List[str],
        databases: List[str],
        build_tools: List[str]
    ) -> float:
        """Calculate confidence score for technology detection."""
        score = 0.0
        
        # Language confidence
        if languages:
            score += 0.3
        
        # Framework confidence
        if frameworks:
            score += 0.3
        
        # Database confidence
        if databases:
            score += 0.2
        
        # Build tools confidence
        if build_tools:
            score += 0.2
        
        return min(1.0, score)


class RepositoryAnalyzer:
    """Main orchestrator for complete repository analysis."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the repository analyzer."""
        self.connector = RepositoryConnector(temp_dir)
        self.code_analyzer = CodeAnalyzer()
        self.component_mapper = ComponentMapper()
        self.technology_detector = TechnologyDetector()
        self.dependency_analyzer = DependencyAnalyzer()
    
    def analyze_repository(
        self, 
        repo_url: str,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> RepositoryAnalysisResult:
        """
        Perform complete repository analysis.
        
        Args:
            repo_url: Repository URL to analyze
            branch: Specific branch to analyze
            depth: Clone depth for faster analysis
            
        Returns:
            Complete analysis results
        """
        try:
            logger.info(f"Starting repository analysis for {repo_url}")
            start_time = datetime.now()
            
            # Step 1: Connect to repository
            repo_info = self.connector.connect_repository(repo_url, branch, depth)
            
            # Step 2: Analyze code structure
            code_analysis = self.code_analyzer.analyze_codebase(self.connector.current_repo_path)
            
            # Step 3: Analyze dependencies
            dependency_analysis = self.dependency_analyzer.analyze_repository(
                self.connector.current_repo_path
            )
            
            # Step 4: Detect technology stack
            technology_stack = self.technology_detector.detect_technology_stack(
                self.connector.current_repo_path, code_analysis, dependency_analysis
            )
            
            # Step 5: Create component map
            component_map = self.component_mapper.create_component_map(
                code_analysis, dependency_analysis
            )
            
            # Step 6: Calculate quality metrics
            quality_metrics = self._calculate_overall_quality_metrics(
                code_analysis, dependency_analysis, component_map
            )
            
            # Step 7: Generate recommendations
            recommendations = self._generate_recommendations(
                technology_stack, component_map, quality_metrics, dependency_analysis
            )
            
            analysis_time = datetime.now() - start_time
            logger.info(f"Repository analysis completed in {analysis_time.total_seconds():.2f} seconds")
            
            return RepositoryAnalysisResult(
                repository_info=repo_info,
                technology_stack=technology_stack,
                component_map=component_map,
                code_analysis=code_analysis,
                dependency_analysis=dependency_analysis,
                quality_metrics=quality_metrics,
                recommendations=recommendations,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            raise Exception(f"Repository analysis failed: {e}")
            
        finally:
            # Cleanup
            self.connector.disconnect()
    
    def _calculate_overall_quality_metrics(
        self,
        code_analysis: Dict[str, Any],
        dependency_analysis: Dict[str, Any],
        component_map: ComponentMap
    ) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        code_quality = code_analysis.get('quality_metrics', {})
        dependency_metrics = dependency_analysis.get('metrics', {})
        component_complexity = component_map.complexity_metrics
        
        # Overall maintainability score
        maintainability = code_quality.get('maintainability_index', 50)
        
        # Security score based on vulnerabilities
        total_deps = dependency_metrics.get('total_dependencies', 1)
        vulnerabilities = len(dependency_analysis.get('vulnerabilities', {}))
        security_score = max(0, 100 - (vulnerabilities / total_deps * 100))
        
        # Complexity score
        avg_complexity = code_quality.get('average_complexity', 5)
        complexity_score = max(0, 100 - (avg_complexity - 1) * 10)
        
        # Overall score
        overall_score = (maintainability + security_score + complexity_score) / 3
        
        return {
            'overall_score': overall_score,
            'maintainability_score': maintainability,
            'security_score': security_score,
            'complexity_score': complexity_score,
            'code_quality': code_quality,
            'dependency_health': dependency_metrics,
            'architectural_complexity': component_complexity
        }
    
    def _generate_recommendations(
        self,
        technology_stack: TechnologyStack,
        component_map: ComponentMap,
        quality_metrics: Dict[str, Any],
        dependency_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate transformation and improvement recommendations."""
        recommendations = []
        
        # Security recommendations
        vulnerabilities = dependency_analysis.get('vulnerabilities', {})
        if vulnerabilities:
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'title': 'Address Security Vulnerabilities',
                'description': f'Found {len(vulnerabilities)} dependencies with security vulnerabilities',
                'action': 'Update vulnerable dependencies to patched versions'
            })
        
        # Complexity recommendations
        avg_complexity = quality_metrics.get('code_quality', {}).get('average_complexity', 0)
        if avg_complexity > 10:
            recommendations.append({
                'category': 'maintainability',
                'priority': 'medium',
                'title': 'Reduce Code Complexity',
                'description': f'Average complexity is {avg_complexity:.1f}, consider refactoring',
                'action': 'Break down complex functions and classes'
            })
        
        # Dependency recommendations
        outdated_percentage = dependency_analysis.get('metrics', {}).get('outdated_percentage', 0)
        if outdated_percentage > 25:
            recommendations.append({
                'category': 'maintenance',
                'priority': 'medium',
                'title': 'Update Dependencies',
                'description': f'{outdated_percentage:.1f}% of dependencies are outdated',
                'action': 'Regularly update dependencies to latest stable versions'
            })
        
        # Architecture recommendations
        graph_density = component_map.complexity_metrics.get('graph_density', 0)
        if graph_density > 0.5:
            recommendations.append({
                'category': 'architecture',
                'priority': 'low',
                'title': 'Reduce Component Coupling',
                'description': 'High coupling detected between components',
                'action': 'Consider applying dependency injection and modularization patterns'
            })
        
        return recommendations