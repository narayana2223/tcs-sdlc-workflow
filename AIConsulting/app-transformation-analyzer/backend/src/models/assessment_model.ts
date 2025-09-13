/**
 * Data models for 12-factor assessment
 * Defines interfaces and types for assessment requests, responses, and results
 */

export enum AssessmentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum FactorScore {
  EXCELLENT = 5,
  GOOD = 4,
  FAIR = 3,
  POOR = 2,
  MISSING = 1,
  UNKNOWN = 0
}

export enum RecommendationPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum ImplementationComplexity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  VERY_HIGH = 'very_high'
}

export enum GapType {
  MISSING = 'missing',
  PARTIAL = 'partial',
  POOR_QUALITY = 'poor_quality',
  ANTI_PATTERN = 'anti_pattern',
  SYSTEMIC = 'systemic'
}

// Request interfaces
export interface AssessmentRequest {
  analysisJobId: string; // Reference to completed analysis
  options?: AssessmentOptions;
}

export interface AssessmentOptions {
  includeRecommendations?: boolean;
  detailedEvidence?: boolean;
  generateRoadmap?: boolean;
  customWeights?: { [factorName: string]: number };
}

// Assessment job tracking
export interface AssessmentJob {
  id: string;
  userId: string;
  analysisJobId: string;
  repositoryUrl: string;
  options: AssessmentOptions;
  status: AssessmentStatus;
  progress: number; // 0-100
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  results?: TwelveFactorAssessment;
  metadata: {
    requestId: string;
    userAgent?: string;
    ipAddress?: string;
  };
}

// Core assessment models
export interface FactorEvidence {
  type: 'positive' | 'negative' | 'neutral';
  description: string;
  file_path?: string;
  line_number?: number;
  code_snippet?: string;
  confidence: number; // 0.0 to 1.0
}

export interface FactorEvaluation {
  factor_name: string;
  factor_description: string;
  score: number;
  score_name: string;
  score_reasoning: string;
  evidence: FactorEvidence[];
  confidence: number;
  weight: number;
}

export interface Gap {
  factor_name: string;
  gap_type: string;
  description: string;
  impact: string;
  current_state: string;
  desired_state: string;
  severity: string;
  affected_components: string[];
}

export interface Recommendation {
  id: string;
  factor_name: string;
  title: string;
  description: string;
  rationale: string;
  implementation_steps: string[];
  priority: string;
  complexity: string;
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
  repository_url: string;
  assessment_id: string;
  timestamp: string;
  factor_evaluations: { [factorName: string]: FactorEvaluation };
  overall_score: number;
  weighted_score: number;
  grade: string; // A, B, C, D, F
  gaps: Gap[];
  recommendations: Recommendation[];
  confidence: number;
  coverage: number; // Percentage of factors that could be evaluated
  score_distribution: { [scoreName: string]: number };
  priority_distribution: { [priority: string]: number };
  summary: {
    total_factors: number;
    total_gaps: number;
    total_recommendations: number;
    critical_issues: number;
    excellent_factors: number;
    poor_factors: number;
  };
}

// 12-Factor definitions
export interface TwelveFactorDefinition {
  name: string;
  title: string;
  description: string;
  rationale: string;
  indicators: {
    positive: string[];
    negative: string[];
  };
  weight: number;
  evaluation_criteria: string[];
}

// Response interfaces
export interface AssessmentResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AssessmentStatus;
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

export interface AssessmentStatusResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AssessmentStatus;
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

export interface AssessmentResultsResponse {
  success: boolean;
  data?: {
    jobId: string;
    status: AssessmentStatus;
    assessment: TwelveFactorAssessment;
    summary: AssessmentSummary;
    roadmap?: ImplementationRoadmap;
    metadata: {
      assessmentTime: number; // seconds
      factorsEvaluated: number;
      evidenceCount: number;
    };
  };
  error?: {
    code: string;
    message: string;
  };
  timestamp: string;
  requestId: string;
}

// Additional response types
export interface AssessmentSummary {
  overview: {
    grade: string;
    overall_score: number;
    weighted_score: number;
    confidence: number;
    coverage: number;
  };
  factor_breakdown: {
    excellent: { count: number; factors: string[] };
    good: { count: number; factors: string[] };
    fair: { count: number; factors: string[] };
    poor: { count: number; factors: string[] };
  };
  gaps: {
    summary: string;
    health_score: number;
    status: string;
    breakdown: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  recommendations: {
    total: number;
    critical: number;
    high: number;
    roadmap: ImplementationRoadmap;
  };
  insights: string[];
  next_steps: string[];
}

export interface ImplementationRoadmap {
  total_recommendations: number;
  phases: {
    phase_1_immediate: RoadmapPhase;
    phase_2_short_term: RoadmapPhase;
    phase_3_medium_term: RoadmapPhase;
    phase_4_long_term: RoadmapPhase;
  };
  estimated_total_effort: string;
  quick_wins: number;
}

export interface RoadmapPhase {
  description: string;
  timeline: string;
  recommendations: string[]; // recommendation IDs
  count: number;
}

// Comparison interface for tracking progress
export interface AssessmentComparison {
  overall_progress: {
    score_change: number;
    grade_changed: boolean;
    previous_grade: string;
    current_grade: string;
  };
  factor_changes: {
    [factorName: string]: {
      previous: number;
      current: number;
      change: number;
    };
  };
  recommendations: {
    previous_count: number;
    current_count: number;
    change: number;
  };
  assessment_dates: {
    previous: string;
    current: string;
  };
  summary: string;
}

// Error types
export class AssessmentError extends Error {
  public statusCode: number;
  public code: string;

  constructor(message: string, statusCode: number = 500, code: string = 'ASSESSMENT_ERROR') {
    super(message);
    this.name = 'AssessmentError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export class AssessmentNotFoundError extends AssessmentError {
  constructor(jobId: string) {
    super(`Assessment job not found: ${jobId}`, 404, 'ASSESSMENT_NOT_FOUND');
    this.name = 'AssessmentNotFoundError';
  }
}

export class AnalysisNotCompleteError extends AssessmentError {
  constructor(analysisJobId: string) {
    super(`Referenced analysis job not completed: ${analysisJobId}`, 400, 'ANALYSIS_NOT_COMPLETE');
    this.name = 'AnalysisNotCompleteError';
  }
}

export class AssessmentTimeoutError extends AssessmentError {
  constructor(timeoutMinutes: number) {
    super(`Assessment timed out after ${timeoutMinutes} minutes`, 408, 'ASSESSMENT_TIMEOUT');
    this.name = 'AssessmentTimeoutError';
  }
}

// Utility functions
export const getDefaultAssessmentOptions = (): AssessmentOptions => ({
  includeRecommendations: true,
  detailedEvidence: true,
  generateRoadmap: true,
  customWeights: undefined,
});

export const getFactorScoreName = (score: number): string => {
  switch (score) {
    case 5: return 'EXCELLENT';
    case 4: return 'GOOD';
    case 3: return 'FAIR';
    case 2: return 'POOR';
    case 1: return 'MISSING';
    default: return 'UNKNOWN';
  }
};

export const getGradeFromScore = (weightedScore: number): string => {
  if (weightedScore >= 4.5) return 'A';
  if (weightedScore >= 3.5) return 'B';
  if (weightedScore >= 2.5) return 'C';
  if (weightedScore >= 1.5) return 'D';
  return 'F';
};

export const calculateHealthScore = (gaps: Gap[]): number => {
  if (!gaps.length) return 100;
  
  const severityWeights = {
    [RecommendationPriority.CRITICAL]: 25,
    [RecommendationPriority.HIGH]: 15,
    [RecommendationPriority.MEDIUM]: 8,
    [RecommendationPriority.LOW]: 3,
  };

  const totalPenalty = gaps.reduce((penalty, gap) => {
    return penalty + (severityWeights[gap.severity as RecommendationPriority] || 0);
  }, 0);

  return Math.max(0, 100 - totalPenalty);
};

export const estimateAssessmentTime = (
  options: AssessmentOptions
): number => {
  let estimatedMinutes = 2; // Base assessment time

  if (options.detailedEvidence) estimatedMinutes += 1;
  if (options.generateRoadmap) estimatedMinutes += 1;
  if (options.customWeights) estimatedMinutes += 0.5;

  return Math.ceil(estimatedMinutes);
};

// 12-Factor definitions (matching Python model)
export const TWELVE_FACTOR_DEFINITIONS: { [name: string]: TwelveFactorDefinition } = {
  natural_language_to_tool_calls: {
    name: 'natural_language_to_tool_calls',
    title: 'Natural Language to Tool Calls',
    description: 'Agents should convert natural language requests into structured tool calls rather than generating raw text',
    rationale: 'Tool calls provide structured, verifiable outputs that can be chained and composed reliably',
    indicators: {
      positive: [
        'Function/tool calling interfaces',
        'Structured output parsing',
        'API integration patterns',
        'Schema validation'
      ],
      negative: [
        'Raw text generation without structure',
        'String parsing for commands',
        'Unvalidated outputs'
      ]
    },
    weight: 1.2,
    evaluation_criteria: [
      'Presence of structured function/tool interfaces',
      'Input validation and schema enforcement',
      'Separation of natural language understanding from tool execution',
      'Error handling for malformed requests'
    ]
  },
  
  own_your_prompts: {
    name: 'own_your_prompts',
    title: 'Own Your Prompts',
    description: 'Prompts should be version-controlled, templated, and managed as first-class assets',
    rationale: 'Treating prompts as code enables proper versioning, testing, and optimization',
    indicators: {
      positive: [
        'Template engines for prompts',
        'Version controlled prompt files',
        'Prompt testing frameworks',
        'Prompt optimization tools'
      ],
      negative: [
        'Hardcoded prompts in source code',
        'Ad-hoc prompt construction',
        'No prompt versioning or testing'
      ]
    },
    weight: 1.1,
    evaluation_criteria: [
      'Prompts stored as separate, version-controlled assets',
      'Template system for prompt composition',
      'Testing infrastructure for prompt validation',
      'Prompt performance monitoring'
    ]
  },
  
  own_your_context_window: {
    name: 'own_your_context_window',
    title: 'Own Your Context Window',
    description: 'Actively manage context window usage with strategies for relevance, compression, and overflow handling',
    rationale: 'Context window is a limited resource that must be managed strategically for optimal performance',
    indicators: {
      positive: [
        'Context compression algorithms',
        'Relevance scoring systems',
        'Context window monitoring',
        'Dynamic context management'
      ],
      negative: [
        'Naive context stuffing',
        'No context size monitoring',
        'Poor context relevance filtering'
      ]
    },
    weight: 1.0,
    evaluation_criteria: [
      'Context size monitoring and limits',
      'Relevance-based context selection',
      'Context compression or summarization',
      'Graceful handling of context overflow'
    ]
  }
  
  // Additional factors would be defined here...
};