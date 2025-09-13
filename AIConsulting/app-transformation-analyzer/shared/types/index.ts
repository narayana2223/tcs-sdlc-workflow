// Common types used across frontend and backend

export interface AnalysisRequest {
  repositoryUrl: string;
  branchName?: string;
  analysisType: 'full' | 'quick' | 'security' | 'performance';
  options?: AnalysisOptions;
}

export interface AnalysisOptions {
  includeTests?: boolean;
  includeDependencies?: boolean;
  performanceMetrics?: boolean;
  securityScan?: boolean;
  codeQuality?: boolean;
}

export interface AnalysisResult {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  results?: TransformationAnalysis;
  error?: string;
  createdAt: Date;
  completedAt?: Date;
}

export interface TransformationAnalysis {
  overview: ProjectOverview;
  codeMetrics: CodeMetrics;
  dependencies: DependencyAnalysis;
  architecture: ArchitectureAnalysis;
  recommendations: TransformationRecommendation[];
  riskAssessment: RiskAssessment;
}

export interface ProjectOverview {
  name: string;
  language: string;
  framework?: string;
  linesOfCode: number;
  fileCount: number;
  testCoverage?: number;
}

export interface CodeMetrics {
  complexity: ComplexityMetrics;
  maintainability: MaintainabilityMetrics;
  duplications: DuplicationMetrics;
}

export interface ComplexityMetrics {
  cyclomaticComplexity: number;
  cognitiveComplexity: number;
  nestingDepth: number;
}

export interface MaintainabilityMetrics {
  maintainabilityIndex: number;
  technicalDebt: number;
  codeSmells: number;
}

export interface DuplicationMetrics {
  duplicatedLines: number;
  duplicatedBlocks: number;
  duplicatedFiles: number;
}

export interface DependencyAnalysis {
  totalDependencies: number;
  outdatedDependencies: OutdatedDependency[];
  vulnerabilities: SecurityVulnerability[];
  licenseIssues: LicenseIssue[];
}

export interface OutdatedDependency {
  name: string;
  currentVersion: string;
  latestVersion: string;
  severity: 'low' | 'medium' | 'high';
}

export interface SecurityVulnerability {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affectedPackage: string;
  fixVersion?: string;
}

export interface LicenseIssue {
  package: string;
  license: string;
  risk: 'low' | 'medium' | 'high';
  description: string;
}

export interface ArchitectureAnalysis {
  patterns: string[];
  antipatterns: string[];
  modularity: ModularityMetrics;
  coupling: CouplingMetrics;
}

export interface ModularityMetrics {
  cohesion: number;
  moduleCount: number;
  averageModuleSize: number;
}

export interface CouplingMetrics {
  afferentCoupling: number;
  efferentCoupling: number;
  instability: number;
}

export interface TransformationRecommendation {
  id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: 'architecture' | 'performance' | 'security' | 'maintainability';
  title: string;
  description: string;
  impact: string;
  effort: 'low' | 'medium' | 'high';
  implementation: string[];
}

export interface RiskAssessment {
  overallRisk: 'low' | 'medium' | 'high' | 'critical';
  risks: Risk[];
  mitigationStrategies: string[];
}

export interface Risk {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  impact: string;
  description: string;
}