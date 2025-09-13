"""
Dependency analyzer for mapping project dependencies, package management,
and vulnerability detection across different programming languages.
"""

import os
import json
import re
import logging
import requests
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import yaml
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a project dependency."""
    name: str
    version: str
    type: str  # 'direct', 'transitive', 'dev', 'peer'
    language: str
    source_file: str
    line_number: Optional[int] = None
    latest_version: Optional[str] = None
    is_outdated: bool = False
    vulnerabilities: List[Dict] = None
    license: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.vulnerabilities is None:
            self.vulnerabilities = []


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability in a dependency."""
    cve_id: str
    severity: str
    title: str
    description: str
    affected_versions: List[str]
    patched_versions: List[str]
    published_date: str
    references: List[str]
    
    def __post_init__(self):
        if self.affected_versions is None:
            self.affected_versions = []
        if self.patched_versions is None:
            self.patched_versions = []
        if self.references is None:
            self.references = []


@dataclass
class LicenseInfo:
    """License information for a dependency."""
    name: str
    spdx_id: str
    is_osi_approved: bool
    risk_level: str  # 'low', 'medium', 'high'
    compatibility: List[str]
    restrictions: List[str]
    
    def __post_init__(self):
        if self.compatibility is None:
            self.compatibility = []
        if self.restrictions is None:
            self.restrictions = []


class DependencyAnalyzerError(Exception):
    """Custom exception for dependency analysis errors."""
    pass


class PackageManagerDetector:
    """Detects package managers and their configuration files."""
    
    PACKAGE_FILES = {
        'npm': ['package.json', 'package-lock.json', 'yarn.lock'],
        'pip': ['requirements.txt', 'Pipfile', 'Pipfile.lock', 'setup.py', 'pyproject.toml'],
        'maven': ['pom.xml'],
        'gradle': ['build.gradle', 'build.gradle.kts'],
        'composer': ['composer.json', 'composer.lock'],
        'go': ['go.mod', 'go.sum'],
        'cargo': ['Cargo.toml', 'Cargo.lock'],
        'gem': ['Gemfile', 'Gemfile.lock'],
        'nuget': ['packages.config', '*.csproj', '*.fsproj', '*.vbproj']
    }
    
    def detect_package_managers(self, repo_path: str) -> Dict[str, List[str]]:
        """
        Detect package managers used in the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dict mapping package manager names to their config files found
        """
        found_managers = defaultdict(list)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', 'env', 'build', 'dist', 'target'
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                for manager, config_files in self.PACKAGE_FILES.items():
                    for config_pattern in config_files:
                        if self._matches_pattern(file, config_pattern):
                            found_managers[manager].append(relative_path)
                            break
        
        return dict(found_managers)
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches the pattern."""
        if '*' in pattern:
            return filename.endswith(pattern.replace('*', ''))
        return filename == pattern


class NPMAnalyzer:
    """Analyzer for NPM/Yarn dependencies."""
    
    def analyze_package_json(self, file_path: str, content: str) -> List[Dependency]:
        """Analyze package.json file."""
        dependencies = []
        
        try:
            data = json.loads(content)
            
            # Regular dependencies
            for name, version in data.get('dependencies', {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    type='direct',
                    language='javascript',
                    source_file=file_path
                ))
            
            # Dev dependencies
            for name, version in data.get('devDependencies', {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    type='dev',
                    language='javascript',
                    source_file=file_path
                ))
            
            # Peer dependencies
            for name, version in data.get('peerDependencies', {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    type='peer',
                    language='javascript',
                    source_file=file_path
                ))
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {file_path}: {e}")
        
        return dependencies


class PipAnalyzer:
    """Analyzer for Python pip dependencies."""
    
    def analyze_requirements_txt(self, file_path: str, content: str) -> List[Dependency]:
        """Analyze requirements.txt file."""
        dependencies = []
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse requirement line
            match = re.match(r'^([a-zA-Z0-9\-_.]+)([>=<!~\s]*)(.*)$', line)
            if match:
                name = match.group(1)
                operator = match.group(2).strip() if match.group(2) else ''
                version = match.group(3).strip() if match.group(3) else ''
                
                dependencies.append(Dependency(
                    name=name,
                    version=f"{operator}{version}" if operator else version,
                    type='direct',
                    language='python',
                    source_file=file_path,
                    line_number=line_num
                ))
        
        return dependencies
    
    def analyze_pipfile(self, file_path: str, content: str) -> List[Dependency]:
        """Analyze Pipfile."""
        dependencies = []
        
        try:
            data = yaml.safe_load(content)
            
            # Regular packages
            for name, version_spec in data.get('packages', {}).items():
                if isinstance(version_spec, str):
                    version = version_spec
                elif isinstance(version_spec, dict):
                    version = version_spec.get('version', '*')
                else:
                    version = '*'
                
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    type='direct',
                    language='python',
                    source_file=file_path
                ))
            
            # Dev packages
            for name, version_spec in data.get('dev-packages', {}).items():
                if isinstance(version_spec, str):
                    version = version_spec
                elif isinstance(version_spec, dict):
                    version = version_spec.get('version', '*')
                else:
                    version = '*'
                
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    type='dev',
                    language='python',
                    source_file=file_path
                ))
            
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML in {file_path}: {e}")
        
        return dependencies


class MavenAnalyzer:
    """Analyzer for Maven dependencies."""
    
    def analyze_pom_xml(self, file_path: str, content: str) -> List[Dependency]:
        """Analyze pom.xml file."""
        dependencies = []
        
        try:
            root = ET.fromstring(content)
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            # Find dependencies section
            deps_elements = root.findall('.//maven:dependency', namespace)
            if not deps_elements:
                # Try without namespace
                deps_elements = root.findall('.//dependency')
            
            for dep in deps_elements:
                group_id = self._get_element_text(dep, 'groupId', namespace)
                artifact_id = self._get_element_text(dep, 'artifactId', namespace)
                version = self._get_element_text(dep, 'version', namespace)
                scope = self._get_element_text(dep, 'scope', namespace) or 'compile'
                
                if group_id and artifact_id:
                    name = f"{group_id}:{artifact_id}"
                    dep_type = 'dev' if scope in ['test', 'provided'] else 'direct'
                    
                    dependencies.append(Dependency(
                        name=name,
                        version=version or 'unknown',
                        type=dep_type,
                        language='java',
                        source_file=file_path
                    ))
            
        except ET.ParseError as e:
            logger.warning(f"Invalid XML in {file_path}: {e}")
        
        return dependencies
    
    def _get_element_text(self, parent, tag, namespace):
        """Get text content of XML element."""
        element = parent.find(f'maven:{tag}', namespace)
        if element is None:
            element = parent.find(tag)
        return element.text if element is not None else None


class VulnerabilityScanner:
    """Scanner for security vulnerabilities in dependencies."""
    
    def __init__(self):
        self.vulnerability_cache = {}
        self.cache_ttl = timedelta(hours=24)
        
    def scan_npm_vulnerabilities(self, dependencies: List[Dependency]) -> Dict[str, List[SecurityVulnerability]]:
        """Scan NPM dependencies for vulnerabilities."""
        vulnerabilities = {}
        
        for dep in dependencies:
            if dep.language == 'javascript':
                vulns = self._check_npm_advisory(dep.name, dep.version)
                if vulns:
                    vulnerabilities[dep.name] = vulns
        
        return vulnerabilities
    
    def scan_python_vulnerabilities(self, dependencies: List[Dependency]) -> Dict[str, List[SecurityVulnerability]]:
        """Scan Python dependencies for vulnerabilities."""
        vulnerabilities = {}
        
        for dep in dependencies:
            if dep.language == 'python':
                vulns = self._check_pyup_safety(dep.name, dep.version)
                if vulns:
                    vulnerabilities[dep.name] = vulns
        
        return vulnerabilities
    
    def _check_npm_advisory(self, package_name: str, version: str) -> List[SecurityVulnerability]:
        """Check NPM advisory database."""
        # Placeholder implementation - would integrate with npm audit API
        cache_key = f"npm:{package_name}:{version}"
        
        if cache_key in self.vulnerability_cache:
            cached_data, cached_time = self.vulnerability_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
        
        try:
            # This would be a real API call in production
            # For now, return empty list
            vulns = []
            self.vulnerability_cache[cache_key] = (vulns, datetime.now())
            return vulns
            
        except Exception as e:
            logger.warning(f"Failed to check vulnerabilities for {package_name}: {e}")
            return []
    
    def _check_pyup_safety(self, package_name: str, version: str) -> List[SecurityVulnerability]:
        """Check Python safety database."""
        # Placeholder implementation - would integrate with safety API
        cache_key = f"python:{package_name}:{version}"
        
        if cache_key in self.vulnerability_cache:
            cached_data, cached_time = self.vulnerability_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
        
        try:
            # This would be a real API call in production
            vulns = []
            self.vulnerability_cache[cache_key] = (vulns, datetime.now())
            return vulns
            
        except Exception as e:
            logger.warning(f"Failed to check vulnerabilities for {package_name}: {e}")
            return []


class LicenseAnalyzer:
    """Analyzer for dependency licenses."""
    
    LICENSE_RISK_LEVELS = {
        'MIT': 'low',
        'Apache-2.0': 'low',
        'BSD-3-Clause': 'low',
        'BSD-2-Clause': 'low',
        'ISC': 'low',
        'GPL-3.0': 'high',
        'GPL-2.0': 'high',
        'LGPL-3.0': 'medium',
        'LGPL-2.1': 'medium',
        'AGPL-3.0': 'high',
        'Unlicense': 'low',
        'CC0-1.0': 'low'
    }
    
    def analyze_licenses(self, dependencies: List[Dependency]) -> Dict[str, LicenseInfo]:
        """Analyze licenses for dependencies."""
        license_info = {}
        
        for dep in dependencies:
            license_name = self._get_package_license(dep)
            if license_name:
                license_info[dep.name] = LicenseInfo(
                    name=license_name,
                    spdx_id=license_name,
                    is_osi_approved=self._is_osi_approved(license_name),
                    risk_level=self.LICENSE_RISK_LEVELS.get(license_name, 'medium'),
                    compatibility=[],
                    restrictions=self._get_license_restrictions(license_name)
                )
        
        return license_info
    
    def _get_package_license(self, dependency: Dependency) -> Optional[str]:
        """Get license for a package (placeholder implementation)."""
        # This would integrate with package registry APIs
        return None
    
    def _is_osi_approved(self, license_name: str) -> bool:
        """Check if license is OSI approved."""
        osi_licenses = {
            'MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause',
            'ISC', 'GPL-3.0', 'GPL-2.0', 'LGPL-3.0', 'LGPL-2.1'
        }
        return license_name in osi_licenses
    
    def _get_license_restrictions(self, license_name: str) -> List[str]:
        """Get restrictions for a license."""
        restrictions_map = {
            'GPL-3.0': ['copyleft', 'patent_protection'],
            'GPL-2.0': ['copyleft'],
            'LGPL-3.0': ['weak_copyleft', 'patent_protection'],
            'LGPL-2.1': ['weak_copyleft'],
            'AGPL-3.0': ['strong_copyleft', 'network_copyleft']
        }
        return restrictions_map.get(license_name, [])


class DependencyAnalyzer:
    """Main dependency analyzer that coordinates all analysis."""
    
    def __init__(self):
        self.detector = PackageManagerDetector()
        self.analyzers = {
            'npm': NPMAnalyzer(),
            'pip': PipAnalyzer(),
            'maven': MavenAnalyzer()
        }
        self.vulnerability_scanner = VulnerabilityScanner()
        self.license_analyzer = LicenseAnalyzer()
    
    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze all dependencies in a repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Comprehensive dependency analysis results
        """
        try:
            # Detect package managers
            package_managers = self.detector.detect_package_managers(repo_path)
            
            if not package_managers:
                logger.info(f"No package managers detected in {repo_path}")
                return self._empty_analysis()
            
            logger.info(f"Detected package managers: {list(package_managers.keys())}")
            
            # Analyze dependencies for each package manager
            all_dependencies = []
            analysis_results = {}
            
            for manager, config_files in package_managers.items():
                if manager in self.analyzers:
                    deps = self._analyze_package_manager(
                        repo_path, manager, config_files
                    )
                    all_dependencies.extend(deps)
                    analysis_results[manager] = {
                        'config_files': config_files,
                        'dependencies': deps
                    }
            
            # Scan for vulnerabilities
            vulnerabilities = self._scan_all_vulnerabilities(all_dependencies)
            
            # Analyze licenses
            license_info = self.license_analyzer.analyze_licenses(all_dependencies)
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(all_dependencies)
            
            # Calculate metrics
            metrics = self._calculate_dependency_metrics(all_dependencies)
            
            return {
                'package_managers': package_managers,
                'total_dependencies': len(all_dependencies),
                'dependencies': all_dependencies,
                'vulnerabilities': vulnerabilities,
                'licenses': license_info,
                'dependency_graph': dependency_graph,
                'metrics': metrics,
                'analysis_results': analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            raise DependencyAnalyzerError(f"Failed to analyze dependencies: {e}")
    
    def _analyze_package_manager(
        self, 
        repo_path: str, 
        manager: str, 
        config_files: List[str]
    ) -> List[Dependency]:
        """Analyze dependencies for a specific package manager."""
        dependencies = []
        analyzer = self.analyzers[manager]
        
        for config_file in config_files:
            file_path = os.path.join(repo_path, config_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if manager == 'npm' and config_file.endswith('package.json'):
                    deps = analyzer.analyze_package_json(config_file, content)
                elif manager == 'pip':
                    if config_file.endswith('requirements.txt'):
                        deps = analyzer.analyze_requirements_txt(config_file, content)
                    elif config_file.endswith('Pipfile'):
                        deps = analyzer.analyze_pipfile(config_file, content)
                    else:
                        continue
                elif manager == 'maven' and config_file.endswith('pom.xml'):
                    deps = analyzer.analyze_pom_xml(config_file, content)
                else:
                    continue
                
                dependencies.extend(deps)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {config_file}: {e}")
                continue
        
        return dependencies
    
    def _scan_all_vulnerabilities(self, dependencies: List[Dependency]) -> Dict[str, List[SecurityVulnerability]]:
        """Scan all dependencies for vulnerabilities."""
        all_vulnerabilities = {}
        
        # Group by language
        js_deps = [d for d in dependencies if d.language == 'javascript']
        python_deps = [d for d in dependencies if d.language == 'python']
        
        # Scan each language
        if js_deps:
            js_vulns = self.vulnerability_scanner.scan_npm_vulnerabilities(js_deps)
            all_vulnerabilities.update(js_vulns)
        
        if python_deps:
            py_vulns = self.vulnerability_scanner.scan_python_vulnerabilities(python_deps)
            all_vulnerabilities.update(py_vulns)
        
        return all_vulnerabilities
    
    def _build_dependency_graph(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Build a dependency graph."""
        graph = nx.DiGraph()
        
        # Add nodes for each dependency
        for dep in dependencies:
            graph.add_node(dep.name, **asdict(dep))
        
        # Basic graph metrics
        return {
            'node_count': graph.number_of_nodes(),
            'edge_count': graph.number_of_edges(),
            'is_connected': nx.is_connected(graph.to_undirected()) if graph.nodes() else False,
            'density': nx.density(graph)
        }
    
    def _calculate_dependency_metrics(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Calculate dependency metrics."""
        if not dependencies:
            return {}
        
        # Count by type
        type_counts = defaultdict(int)
        language_counts = defaultdict(int)
        
        for dep in dependencies:
            type_counts[dep.type] += 1
            language_counts[dep.language] += 1
        
        # Calculate outdated percentage
        outdated_count = sum(1 for dep in dependencies if dep.is_outdated)
        
        return {
            'total_dependencies': len(dependencies),
            'direct_dependencies': type_counts.get('direct', 0),
            'dev_dependencies': type_counts.get('dev', 0),
            'transitive_dependencies': type_counts.get('transitive', 0),
            'outdated_dependencies': outdated_count,
            'outdated_percentage': (outdated_count / len(dependencies)) * 100,
            'language_distribution': dict(language_counts),
            'type_distribution': dict(type_counts)
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'package_managers': {},
            'total_dependencies': 0,
            'dependencies': [],
            'vulnerabilities': {},
            'licenses': {},
            'dependency_graph': {'node_count': 0, 'edge_count': 0},
            'metrics': {},
            'analysis_results': {}
        }