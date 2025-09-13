/**
 * TypeScript interfaces for D3.js visualization components
 * Provides proper typing for complex D3 data structures and interactions
 */

import * as d3 from 'd3';

// Architecture Visualization Types
export interface ArchitectureNode {
  id: string;
  name: string;
  type: 'component' | 'service' | 'database' | 'external';
  group: string;
  layer: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface ArchitectureLink {
  source: string | ArchitectureNode;
  target: string | ArchitectureNode;
  type: 'dependency' | 'data' | 'api' | 'event';
  protocol?: 'HTTP' | 'HTTPS' | 'WebSocket' | 'gRPC' | 'TCP' | 'UDP';
  weight?: number;
}

export interface IntegrationPoint {
  from: string;
  to: string;
  protocol: string;
  direction: 'bidirectional' | 'unidirectional';
  security: 'encrypted' | 'plain';
}

// Gap Analysis Types
export interface GapAnalysisData {
  factor: string;
  severity: number; // 1-4 (low to critical)
  impact: number; // 1-3 (low to high)
  confidence: number; // 0-1
  description: string;
}

export interface RadarChartData {
  factor: string;
  value: number; // 0-1 normalized score
  fullMark: number;
}

// Technology Stack Types
export interface TechnologyNode {
  id: string;
  name: string;
  version: string;
  type: 'language' | 'framework' | 'library' | 'tool';
  category: string;
  outdated: boolean;
  vulnerable: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
  usage?: number; // frequency of use
  size?: number; // for visualization sizing
}

export interface DependencyHierarchy {
  name: string;
  children?: DependencyHierarchy[];
  id?: string;
  version?: string;
  outdated?: boolean;
  vulnerable?: boolean;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  value?: number; // for pack layout
}

// D3 Hierarchy Node with our custom data
export interface CustomHierarchyNode extends d3.HierarchyNode<DependencyHierarchy> {
  r?: number; // radius for pack layout
  x?: number;
  y?: number;
}

export interface PieChartData {
  label: string;
  value: number;
  color?: string;
  percentage?: number;
}

// Security Analysis Types
export interface SecurityIndicator {
  type: 'vulnerability' | 'outdated' | 'warning';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  package: string;
  version: string;
}

// Chart Configuration Types
export interface ChartDimensions {
  width: number;
  height: number;
  margin: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
}

export interface ChartConfig {
  dimensions: ChartDimensions;
  colors: string[];
  animation: {
    duration: number;
    easing: string;
  };
}

// Visualization Component Props
export interface VisualizationProps {
  data: any;
  width?: number;
  height?: number;
  config?: Partial<ChartConfig>;
  onNodeClick?: (node: any) => void;
  onLinkClick?: (link: any) => void;
  className?: string;
}

// Export Utilities Types
export interface ExportOptions {
  format: 'png' | 'svg' | 'pdf';
  quality?: number;
  filename?: string;
  dimensions?: {
    width: number;
    height: number;
  };
}

// D3 Scale Types (for better type inference)
export type ColorScale = d3.ScaleOrdinal<string, string>;
export type LinearScale = d3.ScaleLinear<number, number>;
export type BandScale = d3.ScaleBand<string>;

// Force Simulation Types
export interface SimulationNode extends d3.SimulationNodeDatum {
  id: string;
  group?: string;
  type?: string;
}

export interface SimulationLink extends d3.SimulationLinkDatum<SimulationNode> {
  type?: string;
  protocol?: string;
}

// View Types for component switching
export type ViewType = 'languages' | 'dependencies' | 'frameworks' | 'security';

export type ViewConfig = Record<ViewType, {
  title: string;
  description: string;
  component: React.ComponentType<any>;
}>;

// Animation and Transition Types
export interface TransitionConfig {
  duration: number;
  delay?: number;
  ease?: (t: number) => number;
}

// Tooltip Types
export interface TooltipData {
  title: string;
  content: Array<{
    label: string;
    value: string | number;
    color?: string;
  }>;
  position: {
    x: number;
    y: number;
  };
}