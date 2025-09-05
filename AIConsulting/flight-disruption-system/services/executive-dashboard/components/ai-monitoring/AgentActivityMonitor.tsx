'use client';

import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Users, 
  Cpu, 
  MessageCircle, 
  Target, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Zap,
  TrendingUp,
  DollarSign,
  Activity
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

interface AgentActivityMonitorProps {
  decisions: AgentDecision[];
  selectedAgent?: string | null;
  onSelectAgent?: (agentId: string) => void;
}

const agentConfig = {
  prediction: {
    name: 'Prediction Agent',
    icon: Brain,
    color: 'purple',
    description: 'ML-powered disruption forecasting'
  },
  passenger: {
    name: 'Passenger Agent',
    icon: Users,
    color: 'blue',
    description: 'Individual passenger management'
  },
  resource: {
    name: 'Resource Agent',
    icon: Cpu,
    color: 'green',
    description: 'Cost optimization and resource management'
  },
  communication: {
    name: 'Communication Agent',
    icon: MessageCircle,
    color: 'orange',
    description: 'Multi-channel communication'
  },
  coordinator: {
    name: 'Coordinator Agent',
    icon: Target,
    color: 'red',
    description: 'Master coordination and strategy'
  }
};

const statusConfig = {
  pending: { icon: Clock, color: 'slate', label: 'Pending' },
  processing: { icon: Activity, color: 'yellow', label: 'Processing' },
  completed: { icon: CheckCircle, color: 'green', label: 'Completed' },
  failed: { icon: XCircle, color: 'red', label: 'Failed' }
};

const impactConfig = {
  low: { color: 'slate', label: 'Low Impact', priority: 1 },
  medium: { color: 'yellow', label: 'Medium Impact', priority: 2 },
  high: { color: 'orange', label: 'High Impact', priority: 3 },
  critical: { color: 'red', label: 'Critical Impact', priority: 4 }
};

export default function AgentActivityMonitor({ decisions, selectedAgent, onSelectAgent }: AgentActivityMonitorProps) {
  const [filter, setFilter] = useState<'all' | 'prediction' | 'passenger' | 'resource' | 'communication' | 'coordinator'>('all');
  const [timeWindow, setTimeWindow] = useState<'5m' | '15m' | '1h' | '24h'>('15m');
  const [sortBy, setSortBy] = useState<'timestamp' | 'impact' | 'confidence'>('timestamp');

  // Filter and sort decisions
  const filteredDecisions = decisions
    .filter(decision => {
      if (filter !== 'all' && decision.agentType !== filter) return false;
      
      const timeWindowMs = {
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000
      }[timeWindow];
      
      return Date.now() - decision.timestamp.getTime() <= timeWindowMs;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'timestamp':
          return b.timestamp.getTime() - a.timestamp.getTime();
        case 'impact':
          return impactConfig[b.impact].priority - impactConfig[a.impact].priority;
        case 'confidence':
          return b.confidence - a.confidence;
        default:
          return 0;
      }
    });

  // Agent statistics
  const agentStats = Object.keys(agentConfig).reduce((stats, agentType) => {
    const agentDecisions = decisions.filter(d => d.agentType === agentType);
    stats[agentType] = {
      total: agentDecisions.length,
      completed: agentDecisions.filter(d => d.status === 'completed').length,
      processing: agentDecisions.filter(d => d.status === 'processing').length,
      avgConfidence: agentDecisions.length > 0 ? 
        agentDecisions.reduce((sum, d) => sum + d.confidence, 0) / agentDecisions.length : 0,
      avgExecutionTime: agentDecisions.filter(d => d.executionTime).length > 0 ?
        agentDecisions.filter(d => d.executionTime).reduce((sum, d) => sum + (d.executionTime || 0), 0) / 
        agentDecisions.filter(d => d.executionTime).length : 0,
      totalCost: agentDecisions.reduce((sum, d) => sum + (d.cost || 0), 0),
      totalBenefited: agentDecisions.reduce((sum, d) => sum + (d.passengersBenefited || 0), 0)
    };
    return stats;
  }, {} as any);

  const formatTimeAgo = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return timestamp.toLocaleDateString();
  };

  const getColorClasses = (color: string, variant: 'bg' | 'text' | 'border' = 'bg') => {
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

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
            <Activity className="w-6 h-6" />
            <span>Agent Activity Monitor</span>
          </h2>
          <div className="text-sm text-slate-500">
            {filteredDecisions.length} decisions in last {timeWindow}
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Agent Filter */}
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="all">All Agents</option>
            {Object.entries(agentConfig).map(([key, config]) => (
              <option key={key} value={key}>{config.name}</option>
            ))}
          </select>

          {/* Time Window */}
          <select 
            value={timeWindow} 
            onChange={(e) => setTimeWindow(e.target.value as any)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="5m">Last 5 minutes</option>
            <option value="15m">Last 15 minutes</option>
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
          </select>

          {/* Sort By */}
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="timestamp">Latest First</option>
            <option value="impact">High Impact First</option>
            <option value="confidence">High Confidence First</option>
          </select>
        </div>
      </div>

      {/* Agent Overview Cards */}
      <div className="p-6 border-b border-slate-200">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          {Object.entries(agentConfig).map(([agentType, config]) => {
            const stats = agentStats[agentType];
            const Icon = config.icon;
            
            return (
              <div 
                key={agentType}
                onClick={() => onSelectAgent?.(agentType)}
                className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  selectedAgent === agentType 
                    ? `${getColorClasses(config.color, 'border')} bg-slate-50` 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className={`p-2 ${getColorClasses(config.color)} rounded-lg`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-800 text-sm">{config.name}</h3>
                    <p className="text-xs text-slate-500">{config.description}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <div className="text-slate-500">Decisions</div>
                    <div className="font-semibold">{stats.total}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">Completed</div>
                    <div className="font-semibold text-success-600">{stats.completed}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">Avg Confidence</div>
                    <div className="font-semibold">{(stats.avgConfidence * 100).toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-500">Avg Time</div>
                    <div className="font-semibold">{stats.avgExecutionTime.toFixed(1)}s</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Feed */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="space-y-4">
            {filteredDecisions.map((decision) => {
              const agentConfig_ = agentConfig[decision.agentType];
              const statusConfig_ = statusConfig[decision.status];
              const impactConfig_ = impactConfig[decision.impact];
              const AgentIcon = agentConfig_.icon;
              const StatusIcon = statusConfig_.icon;

              return (
                <div 
                  key={decision.id}
                  className={`bg-white border-2 rounded-lg p-4 transition-all ${
                    selectedAgent === decision.id 
                      ? 'border-purple-200 bg-purple-50' 
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {/* Decision Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 ${getColorClasses(agentConfig_.color)} rounded-lg`}>
                        <AgentIcon className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-slate-800">{agentConfig_.name}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getColorClasses(impactConfig_.color)} text-white`}>
                            {impactConfig_.label}
                          </span>
                        </div>
                        <div className="text-sm text-slate-500">{formatTimeAgo(decision.timestamp)}</div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${getColorClasses(statusConfig_.color, 'bg')} bg-opacity-10`}>
                        <StatusIcon className={`w-4 h-4 ${getColorClasses(statusConfig_.color, 'text')}`} />
                        <span className={`text-xs font-medium ${getColorClasses(statusConfig_.color, 'text')}`}>
                          {statusConfig_.label}
                        </span>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-semibold text-slate-800">{(decision.confidence * 100).toFixed(0)}%</div>
                        <div className="text-xs text-slate-500">confidence</div>
                      </div>
                    </div>
                  </div>

                  {/* Decision Content */}
                  <div className="mb-3">
                    <h4 className="font-semibold text-slate-800 mb-1">{decision.decision}</h4>
                    <p className="text-sm text-slate-600 leading-relaxed">{decision.reasoning}</p>
                  </div>

                  {/* Metrics */}
                  {(decision.cost || decision.passengersBenefited || decision.executionTime) && (
                    <div className="flex items-center space-x-6 text-sm">
                      {decision.cost && (
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-4 h-4 text-green-600" />
                          <span className="text-slate-600">Cost: £{decision.cost.toLocaleString()}</span>
                        </div>
                      )}
                      {decision.passengersBenefited && (
                        <div className="flex items-center space-x-1">
                          <Users className="w-4 h-4 text-blue-600" />
                          <span className="text-slate-600">{decision.passengersBenefited} passengers</span>
                        </div>
                      )}
                      {decision.executionTime && (
                        <div className="flex items-center space-x-1">
                          <Zap className="w-4 h-4 text-yellow-600" />
                          <span className="text-slate-600">{decision.executionTime}s execution</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {filteredDecisions.length === 0 && (
            <div className="text-center py-12">
              <Activity className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-600 mb-2">No agent decisions found</h3>
              <p className="text-slate-500">Try adjusting your filters or time window</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}