// Maturity Levels
export type MaturityLevel = 'L3' | 'L4' | 'L5';

// Infrastructure Tool
export interface InfrastructureDependency {
  tool: string;
  purpose: string;
  critical: boolean;
  layer?: 'infrastructure' | 'foundation';
}

// Tool Categories
export type ToolCategory = 'ai-application' | 'ai-infrastructure' | 'foundation';
export type ToolSubcategory =
  | 'code-editor'
  | 'code-review'
  | 'testing'
  | 'documentation'
  | 'deployment'
  | 'monitoring'
  | 'planning'
  | 'code-execution'
  | 'code-indexing'
  | 'search'
  | 'orchestration'
  | 'build-optimization';

// Maturity Behavior
export interface MaturityBehavior {
  description: string;
  humanTouchpoints: number;
  autonomy: string;
  orchestration?: string;
}

// ROI Metrics
export interface ROIMetrics {
  timeSaved: string;
  costPerSeat?: number;
  annualSavings: number;
}

// Vendor Information
export interface VendorInfo {
  name: string;
  website: string;
  pricing: string;
}

// Tool Definition
export interface Tool {
  id: string;
  name: string;
  category: ToolCategory;
  subcategory: ToolSubcategory;
  phase: string[];
  description: string;
  infrastructure?: InfrastructureDependency[];
  capabilities: string[];
  maturityBehavior: {
    l3: MaturityBehavior;
    l4: MaturityBehavior;
    l5: MaturityBehavior;
  };
  roi: ROIMetrics;
  integrationExample?: string;
  vendor: VendorInfo;
}

// Actor (Human Role)
export interface Actor {
  role: string;
  icon: string;
  responsibilities: string[];
}

// Data Store
export interface DataStore {
  name: string;
  type: 'database' | 'repository' | 'sor' | 'cache';
  artifacts: string[];
}

// Workflow Connection
export interface WorkflowConnection {
  from: string;
  to: string;
  label?: string;
}

// Stage Metrics
export interface StageMetrics {
  duration: string;
  humanTouchpoints: number;
  timeSaved: string;
  autoMergeRate?: string;
}

// Stage Definition
export interface Stage {
  id: string;
  title: string;
  subtitle: string;
  order: number;
  width: number;
  actors: Actor[];
  aiApplications: string[]; // Tool IDs
  infrastructureTools: string[]; // Infrastructure tool IDs
  dataStores: DataStore[];
  workflow: {
    simple: string;
    detailed?: string; // Mermaid diagram
    connections: WorkflowConnection[];
  };
  metrics: {
    l3: StageMetrics;
    l4: StageMetrics;
    l5: StageMetrics;
  };
  roi: {
    annualSavings: number;
    teamSize: number;
    costReduction: string;
  };
}

// Complete Workflow
export interface Workflow {
  maturityLevel: MaturityLevel;
  stages: Stage[];
  totalMetrics: {
    duration: string;
    humanTouchpoints: number;
    timeSaved: string;
    deploymentFrequency: string;
    mttr: string;
    roi: string;
  };
}
