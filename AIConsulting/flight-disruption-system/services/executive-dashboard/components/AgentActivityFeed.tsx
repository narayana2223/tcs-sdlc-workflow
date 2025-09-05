'use client';

import React, { useState } from 'react';
import { AgentDecision } from '@/types';
import { Brain, Users, DollarSign, MessageCircle, Zap, Clock, TrendingUp, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

interface AgentActivityFeedProps {
  decisions: AgentDecision[];
}

const agentIcons = {
  prediction: Brain,
  passenger: Users,
  resource: DollarSign,
  communication: MessageCircle,
  coordinator: Zap,
};

const agentColors = {
  prediction: 'bg-blue-500',
  passenger: 'bg-green-500',
  resource: 'bg-purple-500',
  communication: 'bg-orange-500',
  coordinator: 'bg-red-500',
};

const statusIcons = {
  processing: Clock,
  completed: CheckCircle,
  failed: XCircle,
};

const statusColors = {
  processing: 'text-warning-600',
  completed: 'text-success-600',
  failed: 'text-danger-600',
};

export default function AgentActivityFeed({ decisions }: AgentActivityFeedProps) {
  const [filter, setFilter] = useState<'all' | AgentDecision['agentType']>('all');
  const [expandedDecision, setExpandedDecision] = useState<string | null>(null);

  const filteredDecisions = decisions.filter(
    decision => filter === 'all' || decision.agentType === filter
  );

  const getTimeSince = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    if (minutes > 0) {
      return `${minutes}m ago`;
    }
    return `${seconds}s ago`;
  };

  return (
    <div className="card h-full flex flex-col">
      <div className="card-header">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">AI Agent Activity</h2>
          <p className="text-sm text-slate-600">Live decision-making with reasoning</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="px-3 py-1 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Agents</option>
            <option value="prediction">Prediction</option>
            <option value="passenger">Passenger</option>
            <option value="resource">Resource</option>
            <option value="communication">Communication</option>
            <option value="coordinator">Coordinator</option>
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="space-y-3">
          {filteredDecisions.map((decision) => {
            const AgentIcon = agentIcons[decision.agentType];
            const StatusIcon = statusIcons[decision.status];
            const isExpanded = expandedDecision === decision.id;

            return (
              <div
                key={decision.id}
                className="bg-slate-50 border border-slate-200 rounded-lg p-4 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {/* Agent Icon */}
                    <div className={`p-2 rounded-lg ${agentColors[decision.agentType]} text-white`}>
                      <AgentIcon className="w-4 h-4" />
                    </div>

                    {/* Decision Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-sm font-medium text-slate-800 capitalize">
                          {decision.agentType} Agent
                        </h3>
                        <div className="flex items-center space-x-2">
                          <StatusIcon className={`w-4 h-4 ${statusColors[decision.status]}`} />
                          <span className="text-xs text-slate-500">
                            {getTimeSince(decision.timestamp)}
                          </span>
                        </div>
                      </div>

                      <p className="text-sm text-slate-700 mb-2 line-clamp-2">
                        {decision.decision}
                      </p>

                      {/* Metrics */}
                      <div className="flex items-center space-x-4 mb-2">
                        <div className="flex items-center space-x-1">
                          <TrendingUp className="w-3 h-3 text-slate-500" />
                          <span className="text-xs text-slate-600">
                            {Math.round(decision.confidence * 100)}% confidence
                          </span>
                        </div>
                        <div className={`status-badge status-${decision.impact === 'low' ? 'success' : decision.impact === 'medium' ? 'warning' : 'danger'}`}>
                          {decision.impact} impact
                        </div>
                        {decision.cost && (
                          <div className="flex items-center space-x-1">
                            <DollarSign className="w-3 h-3 text-slate-500" />
                            <span className="text-xs text-slate-600">
                              £{decision.cost.toLocaleString()}
                            </span>
                          </div>
                        )}
                        {decision.passengersBenefited && (
                          <div className="flex items-center space-x-1">
                            <Users className="w-3 h-3 text-slate-500" />
                            <span className="text-xs text-slate-600">
                              {decision.passengersBenefited} passengers
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Expand/Collapse Button */}
                      <button
                        onClick={() => setExpandedDecision(isExpanded ? null : decision.id)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {isExpanded ? 'Hide reasoning' : 'Show reasoning'}
                      </button>

                      {/* Expanded Reasoning */}
                      {isExpanded && (
                        <div className="mt-3 p-3 bg-white rounded-lg border border-slate-200">
                          <h4 className="text-sm font-medium text-slate-800 mb-2">
                            AI Reasoning:
                          </h4>
                          <p className="text-sm text-slate-700 leading-relaxed">
                            {decision.reasoning}
                          </p>
                          {decision.relatedFlightId && (
                            <div className="mt-2 text-xs text-slate-600">
                              Related to flight: <span className="font-mono">{decision.relatedFlightId}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {filteredDecisions.length === 0 && (
            <div className="text-center py-8">
              <Brain className="w-12 h-12 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-600">No agent decisions yet</p>
              <p className="text-sm text-slate-500">Decisions will appear here in real-time</p>
            </div>
          )}
        </div>
      </div>

      {/* Agent Statistics */}
      <div className="mt-4 pt-4 border-t border-slate-200">
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(agentIcons).map(([type, Icon]) => {
            const count = decisions.filter(d => d.agentType === type).length;
            const avgConfidence = decisions
              .filter(d => d.agentType === type)
              .reduce((sum, d) => sum + d.confidence, 0) / Math.max(count, 1);

            return (
              <div key={type} className="text-center">
                <div className={`inline-flex items-center justify-center w-8 h-8 rounded-lg ${agentColors[type as keyof typeof agentColors]} text-white mb-1`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="text-xs font-medium text-slate-800">{count}</div>
                <div className="text-xs text-slate-600">
                  {count > 0 ? `${Math.round(avgConfidence * 100)}%` : '-'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}