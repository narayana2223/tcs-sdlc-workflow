// Core data types for AI-AMS Platform

export interface Competitor {
  name: string;
  platform: string;
  investment: string;
  approach: string;
  threatLevel: number; // 1-10
  keyDifferentiators: string[];
  aiCapabilities: string[];
  pricingModel: string;
}

export interface Startup {
  name: string;
  stage: string;
  funding: string;
  valuation: string;
  founded: number;
  productivityImpact: string;
  threatLevel: "Very High" | "High" | "Medium" | "Low";
  segment: string;
  description: string;
}

export interface UseCase {
  id: string;
  name: string;
  description: string;
  aiTechnology: string;
  productivityImpact: string;
  marketLeaders: string[];
  implementation: string;
}

export interface SDLCPhase {
  id: string;
  name: string;
  why: string[]; // Pain points
  what: UseCase[]; // AI use cases
  how: {
    outcome: string;
    metrics: {
      label: string;
      value: string;
    }[];
    tools: string[];
  };
  sources: Source[];
}

export interface FinancialMetric {
  year: number;
  investment: number;
  savings: number;
  net: number;
}

export interface ROIData {
  npv: number;
  roi: number;
  paybackMonths: number;
  costReduction: number;
  threeYearProjection: FinancialMetric[];
  costBreakdown: {
    category: string;
    baseline: number;
    aiAugmented: number;
    savings: number;
    savingsPercent: number;
  }[];
  productivityGains: {
    metric: string;
    before: string;
    after: string;
    improvement: number;
  }[];
}

export interface Source {
  title: string;
  type: "study" | "report" | "data" | "research";
  year: number;
  organization: string;
}

export interface Calculation {
  formula: string;
  assumptions: string[];
  inputs: {
    name: string;
    value: string | number;
  }[];
  result: string;
}

export interface WorkforceRole {
  traditional: string;
  new: string;
  count: {
    before: number;
    after: number;
  };
  salary: {
    min: number;
    max: number;
  };
  skills: string[];
  transition: string;
}

export interface RiskItem {
  category: string;
  threat: string;
  severity: "Low" | "Medium" | "High" | "Very High";
  mitigation: string;
  mitigationEffectiveness: number;
}
