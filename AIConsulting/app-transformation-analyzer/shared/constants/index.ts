// Shared constants across frontend and backend

export const ANALYSIS_TYPES = {
  FULL: 'full',
  QUICK: 'quick',
  SECURITY: 'security',
  PERFORMANCE: 'performance'
} as const;

export const ANALYSIS_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const;

export const PRIORITY_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
} as const;

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
} as const;

export const EFFORT_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high'
} as const;

export const RECOMMENDATION_CATEGORIES = {
  ARCHITECTURE: 'architecture',
  PERFORMANCE: 'performance',
  SECURITY: 'security',
  MAINTAINABILITY: 'maintainability'
} as const;

export const SUPPORTED_LANGUAGES = [
  'javascript',
  'typescript',
  'python',
  'java',
  'csharp',
  'go',
  'rust',
  'php',
  'ruby'
] as const;

export const SUPPORTED_FRAMEWORKS = [
  'react',
  'angular',
  'vue',
  'express',
  'nestjs',
  'spring',
  'django',
  'flask',
  'rails',
  'laravel'
] as const;

export const API_ENDPOINTS = {
  ANALYSIS: '/api/analysis',
  RESULTS: '/api/results',
  HEALTH: '/api/health'
} as const;

export const DEFAULT_ANALYSIS_OPTIONS = {
  includeTests: true,
  includeDependencies: true,
  performanceMetrics: false,
  securityScan: true,
  codeQuality: true
} as const;