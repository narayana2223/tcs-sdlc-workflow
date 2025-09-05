'use client';

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Target, 
  Zap, 
  Brain,
  Users,
  DollarSign,
  Award,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

interface AgentDecision {
  id: string;
  agentType: 'prediction' | 'passenger' | 'resource' | 'communication' | 'coordinator';
  timestamp: Date;
  decision: string;
  reasoning: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  cost?: number;
  passengersBenefited?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  executionTime?: number;
  parentDecisionId?: string;
  childDecisions?: string[];
}

interface MLMetrics {
  modelAccuracy: number;
  predictionLatency: number;
  trainingProgress: number;
  dataQuality: number;
  modelDrift: number;
  featureImportance: Record<string, number>;
}

interface PerformanceAnalyticsProps {
  decisions: AgentDecision[];
  mlMetrics: MLMetrics;
}

interface AgentPerformance {
  agentType: string;
  totalDecisions: number;
  successRate: number;
  avgConfidence: number;
  avgExecutionTime: number;
  totalCost: number;
  totalBenefited: number;
  impactDistribution: Record<string, number>;
}

const agentNames = {
  prediction: 'Prediction Agent',
  passenger: 'Passenger Agent',
  resource: 'Resource Agent',
  communication: 'Communication Agent',
  coordinator: 'Coordinator Agent'
};

const agentColors = {
  prediction: 'purple',
  passenger: 'blue',
  resource: 'green',
  communication: 'orange',
  coordinator: 'red'
};

export default function PerformanceAnalytics({ decisions, mlMetrics }: PerformanceAnalyticsProps) {
  const [timeWindow, setTimeWindow] = useState<'1h' | '6h' | '24h' | '7d'>('24h');
  const [selectedMetric, setSelectedMetric] = useState<'accuracy' | 'speed' | 'cost' | 'impact'>('accuracy');
  const [comparisonMode, setComparisonMode] = useState<'agents' | 'historical'>('agents');

  // Calculate agent performance metrics
  const agentPerformance: AgentPerformance[] = Object.keys(agentNames).map(agentType => {
    const agentDecisions = decisions.filter(d => d.agentType === agentType);
    
    const totalDecisions = agentDecisions.length;
    const completedDecisions = agentDecisions.filter(d => d.status === 'completed');
    const successRate = totalDecisions > 0 ? (completedDecisions.length / totalDecisions) * 100 : 0;
    const avgConfidence = totalDecisions > 0 ? 
      (agentDecisions.reduce((sum, d) => sum + d.confidence, 0) / totalDecisions) * 100 : 0;
    const executionTimes = agentDecisions.filter(d => d.executionTime).map(d => d.executionTime!);
    const avgExecutionTime = executionTimes.length > 0 ? 
      executionTimes.reduce((sum, t) => sum + t, 0) / executionTimes.length : 0;
    const totalCost = agentDecisions.reduce((sum, d) => sum + (d.cost || 0), 0);
    const totalBenefited = agentDecisions.reduce((sum, d) => sum + (d.passengersBenefited || 0), 0);
    
    const impactDistribution = ['low', 'medium', 'high', 'critical'].reduce((dist, impact) => {
      dist[impact] = agentDecisions.filter(d => d.impact === impact).length;
      return dist;
    }, {} as Record<string, number>);

    return {
      agentType,
      totalDecisions,
      successRate,
      avgConfidence,
      avgExecutionTime,
      totalCost,
      totalBenefited,
      impactDistribution
    };
  });

  // Historical comparison data (mock for demonstration)
  const historicalData = {
    lastWeek: {
      avgAccuracy: 91.2,
      avgResponseTime: 2.8,
      totalCost: 450000,
      successRate: 87.5
    },
    thisWeek: {
      avgAccuracy: 94.8,
      avgResponseTime: 1.9,
      totalCost: 320000,
      successRate: 92.1
    }
  };

  const getColorClass = (color: string, variant: 'bg' | 'text' | 'border' = 'bg') => {
    const colorMap = {
      purple: { bg: 'bg-purple-500', text: 'text-purple-600', border: 'border-purple-200' },
      blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-200' },
      green: { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-200' },
      orange: { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200' },
      red: { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200' },
      yellow: { bg: 'bg-yellow-500', text: 'text-yellow-600', border: 'border-yellow-200' },
      slate: { bg: 'bg-slate-500', text: 'text-slate-600', border: 'border-slate-200' }
    };
    return colorMap[color as keyof typeof colorMap]?.[variant] || colorMap.slate[variant];
  };

  const renderMetricCard = (title: string, value: string | number, change: number, icon: React.ComponentType<any>, color: string) => {
    const Icon = icon;
    const isPositive = change >= 0;
    
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 ${getColorClass(color)} rounded-lg`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${
            isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="text-sm font-medium">
              {isPositive ? '+' : ''}{change.toFixed(1)}%
            </span>
          </div>
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-800 mb-1">{value}</div>
          <div className="text-sm text-slate-600">{title}</div>
        </div>
      </div>
    );
  };

  const renderAgentComparison = () => (
    <div className="space-y-4">
      {agentPerformance.map((agent) => {
        const color = agentColors[agent.agentType as keyof typeof agentColors];
        
        return (
          <div key={agent.agentType} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">
                {agentNames[agent.agentType as keyof typeof agentNames]}
              </h3>
              <div className="text-sm text-slate-500">
                {agent.totalDecisions} decisions
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Success Rate</div>
                <div className="font-semibold text-slate-800">{agent.successRate.toFixed(1)}%</div>
                <div className="w-full bg-slate-200 rounded-full h-1 mt-1">
                  <div 
                    className={`${getColorClass(color)} h-1 rounded-full transition-all duration-500`}
                    style={{ width: `${agent.successRate}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">Avg Confidence</div>
                <div className="font-semibold text-slate-800">{agent.avgConfidence.toFixed(1)}%</div>
                <div className="w-full bg-slate-200 rounded-full h-1 mt-1">
                  <div 
                    className={`${getColorClass(color)} h-1 rounded-full transition-all duration-500`}
                    style={{ width: `${agent.avgConfidence}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">Avg Execution</div>
                <div className="font-semibold text-slate-800">{agent.avgExecutionTime.toFixed(1)}s</div>
                <div className="w-full bg-slate-200 rounded-full h-1 mt-1">
                  <div 
                    className={`${getColorClass(color)} h-1 rounded-full transition-all duration-500`}
                    style={{ width: `${Math.min(agent.avgExecutionTime * 10, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-500 mb-1">Cost Impact</div>
                <div className="font-semibold text-slate-800">£{(agent.totalCost / 1000).toFixed(0)}K</div>
              </div>
            </div>

            {/* Impact Distribution */}
            <div>
              <div className="text-xs text-slate-500 mb-2">Impact Distribution</div>
              <div className="flex items-center space-x-2">
                {Object.entries(agent.impactDistribution).map(([impact, count]) => {
                  const impactColors = {
                    low: 'slate',
                    medium: 'yellow',
                    high: 'orange',
                    critical: 'red'
                  };
                  const impactColor = impactColors[impact as keyof typeof impactColors];
                  
                  return (
                    <div key={impact} className="flex items-center space-x-1">
                      <div className={`w-3 h-3 ${getColorClass(impactColor)} rounded-full`}></div>
                      <span className="text-xs text-slate-600">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderHistoricalComparison = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4">Accuracy Trends</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">This Week</span>
              <span className="font-semibold text-slate-800">{historicalData.thisWeek.avgAccuracy}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${historicalData.thisWeek.avgAccuracy}%` }}
              ></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">Last Week</span>
              <span className="font-semibold text-slate-800">{historicalData.lastWeek.avgAccuracy}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-slate-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${historicalData.lastWeek.avgAccuracy}%` }}
              ></div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <div className="flex items-center space-x-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-green-600 font-medium">
                +{(historicalData.thisWeek.avgAccuracy - historicalData.lastWeek.avgAccuracy).toFixed(1)}% improvement
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4">Response Time Trends</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">This Week</span>
              <span className="font-semibold text-slate-800">{historicalData.thisWeek.avgResponseTime}s</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(5 - historicalData.thisWeek.avgResponseTime) * 20}%` }}
              ></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">Last Week</span>
              <span className="font-semibold text-slate-800">{historicalData.lastWeek.avgResponseTime}s</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-slate-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(5 - historicalData.lastWeek.avgResponseTime) * 20}%` }}
              ></div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <div className="flex items-center space-x-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-green-600 font-medium">
                {((historicalData.lastWeek.avgResponseTime - historicalData.thisWeek.avgResponseTime) / historicalData.lastWeek.avgResponseTime * 100).toFixed(1)}% faster
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4">Cost Efficiency</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">This Week</span>
              <span className="font-semibold text-slate-800">£{(historicalData.thisWeek.totalCost / 1000).toFixed(0)}K</span>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">Last Week</span>
              <span className="font-semibold text-slate-800">£{(historicalData.lastWeek.totalCost / 1000).toFixed(0)}K</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <div className="flex items-center space-x-2 text-sm">
              <TrendingDown className="w-4 h-4 text-green-600" />
              <span className="text-green-600 font-medium">
                £{((historicalData.lastWeek.totalCost - historicalData.thisWeek.totalCost) / 1000).toFixed(0)}K saved
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4">Success Rate</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">This Week</span>
              <span className="font-semibold text-slate-800">{historicalData.thisWeek.successRate}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${historicalData.thisWeek.successRate}%` }}
              ></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">Last Week</span>
              <span className="font-semibold text-slate-800">{historicalData.lastWeek.successRate}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-slate-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${historicalData.lastWeek.successRate}%` }}
              ></div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-200">
            <div className="flex items-center space-x-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-green-600 font-medium">
                +{(historicalData.thisWeek.successRate - historicalData.lastWeek.successRate).toFixed(1)}% improvement
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
            <BarChart3 className="w-6 h-6" />
            <span>Performance Analytics</span>
          </h2>
          
          {/* Comparison Mode Toggle */}
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setComparisonMode('agents')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                comparisonMode === 'agents' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-600'
              }`}
            >
              Agent Comparison
            </button>
            <button
              onClick={() => setComparisonMode('historical')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                comparisonMode === 'historical' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-600'
              }`}
            >
              Historical
            </button>
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {renderMetricCard(
            "Model Accuracy", 
            `${mlMetrics.modelAccuracy}%`, 
            3.6,
            Brain,
            'purple'
          )}
          
          {renderMetricCard(
            "Avg Response Time", 
            `${mlMetrics.predictionLatency / 1000}s`, 
            -12.5,
            Zap,
            'blue'
          )}
          
          {renderMetricCard(
            "Total Cost Savings", 
            `£${(agentPerformance.reduce((sum, agent) => sum + agent.totalCost, 0) / 1000).toFixed(0)}K`, 
            8.2,
            DollarSign,
            'green'
          )}
          
          {renderMetricCard(
            "Passengers Helped", 
            agentPerformance.reduce((sum, agent) => sum + agent.totalBenefited, 0).toLocaleString(), 
            15.7,
            Users,
            'orange'
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {comparisonMode === 'agents' ? renderAgentComparison() : renderHistoricalComparison()}
      </div>
    </div>
  );
}