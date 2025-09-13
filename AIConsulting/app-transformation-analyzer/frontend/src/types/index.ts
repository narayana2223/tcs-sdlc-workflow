/**
 * TypeScript type definitions for the Application Transformation Analyzer frontend
 * Matches backend API interfaces for seamless integration
 */

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  requestId: string;
}

// User Types (simplified - no auth required)
export interface User {
  id: string;
  username: string;
  name: string;
  email: string;
  role: string;
  createdAt: string;
}

// Analysis Types
export interface AnalysisRequest {
  repositoryUrl: string;
  branchName?: string;
  analysisType: 'full' | 'quick' | 'dependencies' | 'security' | 'quality';
  options?: {
    depth?: number;
    includeTests?: boolean;
    timeout?: number;
  };
}

export interface AnalysisJob {
  id: string;
  repositoryUrl: string;
  branchName?: string;
  analysisType: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  estimatedCompletionTime?: string;
  error?: string;
  message?: string;
  hasResults: boolean;
}

export interface AnalysisResults {
  jobId: string;
  status: string;
  results: {
    code_analysis: {
      project_metrics: {
        total_files: number;
        total_lines_of_code: number;
        languages: { [key: string]: number };
      };
      file_analysis: {
        [filename: string]: {
          lines_of_code: number;
          complexity: number;
          maintainability_index: number;
          test_coverage?: number;
        };
      };
      dependency_analysis: {
        direct_dependencies: { [key: string]: string };
        transitive_dependencies: { [key: string]: string };
        outdated_dependencies: { [key: string]: { current: string; latest: string } };
        security_vulnerabilities: Array<{
          package: string;
          severity: 'low' | 'medium' | 'high' | 'critical';
          description: string;
        }>;
      };
      architecture_analysis: {
        components: Array<{
          name: string;
          type: string;
          dependencies: string[];
          complexity: number;
        }>;
        layers: string[];
        patterns: string[];
      };
    };
    technology_stack: {
      primary_language: string;
      frameworks: string[];
      databases: string[];
      build_tools: string[];
      deployment_tools: string[];
      testing_frameworks: string[];
    };
  };
  metadata?: {
    analysisTime: number;
    linesAnalyzed: number;
    filesAnalyzed: number;
    cacheHit: boolean;
  };
}

// Assessment Types
export interface AssessmentRequest {
  analysisJobId: string;
  options?: {
    factors?: string[];
    weights?: { [key: string]: number };
    timeout?: number;
  };
}

export interface AssessmentJob {
  id: string;
  analysisJobId: string;
  repositoryUrl: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  grade?: string;
  overall_score?: number;
  hasResults: boolean;
}

export interface Evidence {
  type: 'positive' | 'negative' | 'neutral';
  description: string;
  file_path?: string;
  line_number?: number;
  code_snippet?: string;
  confidence: number;
}

export interface FactorEvaluation {
  factor_name: string;
  factor_description: string;
  score: number;
  score_name: string;
  score_reasoning: string;
  confidence: number;
  weight: number;
  evidence: Evidence[];
}

export interface Gap {
  factor_name: string;
  gap_type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  effort_estimate: number;
}

export interface Recommendation {
  id: string;
  factor_name: string;
  title: string;
  description: string;
  rationale: string;
  implementation_steps: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  complexity: 'low' | 'medium' | 'high' | 'very_high';
  estimated_effort: string;
  benefits: string[];
  risks: string[];
  prerequisites: string[];
  resources: string[];
  code_examples: Array<{
    language: string;
    title: string;
    code: string;
  }>;
}

export interface TwelveFactorAssessment {
  assessment_id: string;
  repository_url: string;
  timestamp: string;
  grade: string;
  overall_score: number;
  weighted_score: number;
  confidence: number;
  coverage: number;
  factor_evaluations: { [key: string]: FactorEvaluation };
  recommendations: Recommendation[];
  gaps: Gap[];
  score_distribution?: { [key: string]: number };
  summary: {
    total_factors: number;
    excellent_factors: number;
    critical_issues: number;
    total_gaps: number;
    total_recommendations: number;
  };
}

export interface AssessmentResults {
  assessmentId: string;
  status: string;
  results: TwelveFactorAssessment;
  metadata?: {
    assessmentTime: number;
    factorsEvaluated: number;
    overallScore: number;
    totalGaps: number;
    highPriorityGaps: number;
  };
}

// Dashboard Types
export interface DashboardData {
  recentAnalyses: AnalysisJob[];
  recentAssessments: AssessmentJob[];
  statistics: {
    totalAnalyses: number;
    totalAssessments: number;
    averageScore: number;
    successRate: number;
  };
}

// Component Props Types
export interface RepositoryInputProps {
  onSubmit: (request: AnalysisRequest) => void;
  loading?: boolean;
  error?: string;
}

export interface AnalysisStatusProps {
  job: AnalysisJob;
  onCancel?: (jobId: string) => void;
  onRestart?: (jobId: string) => void;
  showActions?: boolean;
}

// Utility Types
export interface LoadingState {
  loading: boolean;
  error?: string;
}

export interface PaginationParams {
  limit: number;
  offset: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export interface FilterParams {
  status?: string;
  repositoryUrl?: string;
  dateFrom?: string;
  dateTo?: string;
}

// Theme and UI Types
export interface ThemeMode {
  mode: 'light' | 'dark';
  toggleMode: () => void;
}

// Error Types
export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: any;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'select' | 'checkbox' | 'number';
  required?: boolean;
  options?: Array<{ value: string; label: string }>;
  validation?: (value: any) => string | undefined;
}

// Chart and Visualization Types
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string[];
    borderColor?: string[];
  }>;
}

export interface FactorScoreData {
  factor: string;
  score: number;
  compliant: boolean;
  trend?: 'up' | 'down' | 'stable';
}

// Route Types
export interface RouteConfig {
  path: string;
  title: string;
  icon?: string;
  component: React.ComponentType;
  requiresAuth?: boolean;
}

// API Client Types
export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  headers?: { [key: string]: string };
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  };
}

// Context Types

export interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// Export commonly used type unions
export type AnalysisType = 'full' | 'quick' | 'dependencies' | 'security' | 'quality';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type Priority = 'low' | 'medium' | 'high';
export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type Grade = 'A' | 'B' | 'C' | 'D' | 'F';