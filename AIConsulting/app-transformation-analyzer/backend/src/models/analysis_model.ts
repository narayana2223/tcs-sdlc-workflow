/**
 * Data models for repository analysis
 * Defines interfaces and types for analysis requests, responses, and status tracking
 */

export enum AnalysisStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum AnalysisType {
  FULL = 'full',
  QUICK = 'quick',
  SECURITY = 'security',
  PERFORMANCE = 'performance'
}

export interface AnalysisRequest {
  repositoryUrl: string;
  branchName?: string;
  analysisType: AnalysisType;
  options?: AnalysisOptions;
}

export interface AnalysisOptions {
  includeTests?: boolean;
  includeDependencies?: boolean;
  performanceMetrics?: boolean;
  securityScan?: boolean;
  codeQuality?: boolean;
  depth?: number; // For shallow cloning
  timeout?: number; // Analysis timeout in minutes
}

export interface AnalysisJob {
  id: string;
  userId: string;
  repositoryUrl: string;
  branchName?: string;
  analysisType: AnalysisType;
  options: AnalysisOptions;
  status: AnalysisStatus;
  progress: number; // 0-100
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  results?: AnalysisResult;
  metadata: {
    requestId: string;
    userAgent?: string;
    ipAddress?: string;
  };
}

export interface AnalysisResult {
  repository_info: RepositoryInfo;
  technology_stack: TechnologyStack;
  component_map: ComponentMap;
  code_analysis: CodeAnalysis;
  dependency_analysis: DependencyAnalysis;
  quality_metrics: QualityMetrics;
  recommendations: Recommendation[];
  analysis_timestamp: string;
}

export interface RepositoryInfo {
  remote_url: string;
  active_branch: string;
  total_files: number;
  total_commits: number;
  total_size_bytes: number;
  last_commit?: {
    sha: string;
    message: string;
    author: string;
    date: string;
  };
  contributors?: { [author: string]: number };
  languages?: { [language: string]: number };
}

export interface TechnologyStack {
  primary_language: string;
  languages: { [language: string]: number };
  frameworks: string[];
  databases: string[];
  web_servers: string[];
  build_tools: string[];
  testing_frameworks: string[];
  deployment_tools: string[];
  package_managers: string[];
  confidence_score: number;
}

export interface ComponentMap {
  components: { [componentId: string]: Component };
  relationships: ComponentRelationship[];
  clusters: string[][];
  complexity_metrics: {
    graph_density: number;
    average_in_degree_centrality: number;
    average_out_degree_centrality: number;
    total_components: number;
    total_relationships: number;
    cyclomatic_complexity: number;
  };
}

export interface Component {
  type: 'file' | 'class' | 'function' | 'module';
  name: string;
  path?: string;
  language?: string;
  lines_of_code?: number;
  complexity?: number;
  elements?: number;
  parent?: string;
}

export interface ComponentRelationship {
  source_component: string;
  target_component: string;
  relationship_type: 'imports' | 'extends' | 'calls' | 'references' | 'depends_on';
  strength: number;
  file_path: string;
  line_number?: number;
}

export interface CodeAnalysis {
  file_analyses: { [filePath: string]: FileAnalysis };
  project_metrics: ProjectMetrics;
  quality_metrics: CodeQualityMetrics;
  analysis_summary: {
    total_files: number;
    total_elements: number;
    languages_detected: { [language: string]: number };
    avg_complexity: number;
  };
}

export interface FileAnalysis {
  file_path: string;
  language: string;
  lines_of_code: number;
  complexity_score: number;
  elements: CodeElement[];
  imports: string[];
  exports: string[];
  dependencies: string[];
}

export interface CodeElement {
  name: string;
  type: 'class' | 'function' | 'variable' | 'import' | 'module';
  file_path: string;
  line_number: number;
  end_line_number?: number;
  parent?: string;
  parameters?: string[];
  return_type?: string;
  decorators?: string[];
  docstring?: string;
  complexity: number;
  dependencies?: string[];
}

export interface ProjectMetrics {
  total_files: number;
  total_lines_of_code: number;
  average_lines_per_file: number;
  total_complexity: number;
  average_complexity_per_file: number;
  language_distribution: { [language: string]: number };
  element_type_distribution: { [type: string]: number };
  unique_dependencies: number;
  dependency_list: string[];
}

export interface CodeQualityMetrics {
  maintainability_index: number;
  average_complexity: number;
  average_file_size: number;
  total_complexity: number;
  complexity_density: number;
}

export interface DependencyAnalysis {
  package_managers: { [manager: string]: string[] };
  total_dependencies: number;
  dependencies: Dependency[];
  vulnerabilities: { [packageName: string]: SecurityVulnerability[] };
  licenses: { [packageName: string]: LicenseInfo };
  metrics: DependencyMetrics;
}

export interface Dependency {
  name: string;
  version: string;
  type: 'direct' | 'transitive' | 'dev' | 'peer';
  language: string;
  source_file: string;
  line_number?: number;
  latest_version?: string;
  is_outdated: boolean;
  vulnerabilities: SecurityVulnerability[];
  license?: string;
  description?: string;
}

export interface SecurityVulnerability {
  cve_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_versions: string[];
  patched_versions: string[];
  published_date: string;
  references: string[];
}

export interface LicenseInfo {
  name: string;
  spdx_id: string;
  is_osi_approved: boolean;
  risk_level: 'low' | 'medium' | 'high';
  compatibility: string[];
  restrictions: string[];
}

export interface DependencyMetrics {
  total_dependencies: number;
  direct_dependencies: number;
  dev_dependencies: number;
  transitive_dependencies: number;
  outdated_dependencies: number;
  outdated_percentage: number;
  language_distribution: { [language: string]: number };
  type_distribution: { [type: string]: number };
}

export interface QualityMetrics {
  overall_score: number;
  maintainability_score: number;
  security_score: number;
  complexity_score: number;
  code_quality: CodeQualityMetrics;
  dependency_health: DependencyMetrics;
  architectural_complexity: {
    graph_density: number;
    average_in_degree_centrality: number;
    average_out_degree_centrality: number;
    total_components: number;
    total_relationships: number;
    cyclomatic_complexity: number;
  };
}

export interface Recommendation {
  id: string;
  category: 'architecture' | 'performance' | 'security' | 'maintainability';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  action: string;
  impact?: string;
  effort?: 'low' | 'medium' | 'high';
  implementation?: string[];
}

// Request validation schemas
export interface AnalysisRequestValidation {
  repositoryUrl: {
    isRequired: boolean;
    pattern: RegExp;
    maxLength: number;
  };
  branchName: {
    isRequired: boolean;
    maxLength: number;
    pattern: RegExp;
  };
  analysisType: {
    isRequired: boolean;
    allowedValues: AnalysisType[];
  };
  options: {
    depth: {
      min: number;
      max: number;
    };
    timeout: {
      min: number;
      max: number;
    };
  };
}

// API Response interfaces
export interface AnalysisResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AnalysisStatus;
    message: string;
    estimatedCompletionTime?: string;
  };
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  requestId: string;
}

export interface AnalysisStatusResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AnalysisStatus;
    progress: number;
    message?: string;
    createdAt: string;
    startedAt?: string;
    completedAt?: string;
    estimatedCompletionTime?: string;
    error?: string;
  };
  error?: {
    code: string;
    message: string;
  };
  timestamp: string;
  requestId: string;
}

export interface AnalysisResultsResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AnalysisStatus;
    results: AnalysisResult;
    metadata: {
      analysisTime: number; // seconds
      linesAnalyzed: number;
      filesAnalyzed: number;
      cacheHit?: boolean;
    };
  };
  error?: {
    code: string;
    message: string;
  };
  timestamp: string;
  requestId: string;
}

// Error types
export class AnalysisError extends Error {
  public statusCode: number;
  public code: string;

  constructor(message: string, statusCode: number = 500, code: string = 'ANALYSIS_ERROR') {
    super(message);
    this.name = 'AnalysisError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export class ValidationError extends AnalysisError {
  constructor(message: string, field?: string) {
    super(message, 400, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class RepositoryNotFoundError extends AnalysisError {
  constructor(repositoryUrl: string) {
    super(`Repository not found or inaccessible: ${repositoryUrl}`, 404, 'REPOSITORY_NOT_FOUND');
    this.name = 'RepositoryNotFoundError';
  }
}

export class AnalysisTimeoutError extends AnalysisError {
  constructor(timeoutMinutes: number) {
    super(`Analysis timed out after ${timeoutMinutes} minutes`, 408, 'ANALYSIS_TIMEOUT');
    this.name = 'AnalysisTimeoutError';
  }
}

export class EngineUnavailableError extends AnalysisError {
  constructor() {
    super('Analysis engine is currently unavailable', 503, 'ENGINE_UNAVAILABLE');
    this.name = 'EngineUnavailableError';
  }
}

export class AnalysisNotFoundError extends AnalysisError {
  constructor(analysisId: string) {
    super(`Analysis not found: ${analysisId}`, 404, 'ANALYSIS_NOT_FOUND');
    this.name = 'AnalysisNotFoundError';
  }
}

// Utility functions
export const getDefaultAnalysisOptions = (): AnalysisOptions => ({
  includeTests: true,
  includeDependencies: true,
  performanceMetrics: false,
  securityScan: true,
  codeQuality: true,
  depth: undefined, // Full clone by default
  timeout: 30, // 30 minutes default
});

export const isValidRepositoryUrl = (url: string): boolean => {
  const patterns = [
    /^https:\/\/github\.com\/[\w\-_.]+\/[\w\-_.]+(?:\.git)?$/,
    /^https:\/\/gitlab\.com\/[\w\-_.]+\/[\w\-_.]+(?:\.git)?$/,
    /^https:\/\/bitbucket\.org\/[\w\-_.]+\/[\w\-_.]+(?:\.git)?$/,
    /^git@github\.com:[\w\-_.]+\/[\w\-_.]+\.git$/,
    /^git@gitlab\.com:[\w\-_.]+\/[\w\-_.]+\.git$/,
  ];
  
  return patterns.some(pattern => pattern.test(url));
};

export const sanitizeRepositoryUrl = (url: string): string => {
  // Remove trailing slashes and normalize
  return url.trim().replace(/\/$/, '');
};

export const estimateAnalysisTime = (
  analysisType: AnalysisType,
  options: AnalysisOptions
): number => {
  // Base time estimates in minutes
  const baseTimes = {
    [AnalysisType.QUICK]: 2,
    [AnalysisType.FULL]: 10,
    [AnalysisType.SECURITY]: 8,
    [AnalysisType.PERFORMANCE]: 12,
  };

  let estimatedTime = baseTimes[analysisType];

  // Adjust based on options
  if (options.includeDependencies) estimatedTime += 2;
  if (options.securityScan) estimatedTime += 3;
  if (options.performanceMetrics) estimatedTime += 4;

  // Shallow clone reduces time
  if (options.depth && options.depth <= 10) estimatedTime *= 0.5;

  return Math.ceil(estimatedTime);
};