'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Users, 
  Cpu, 
  MessageCircle, 
  Target, 
  DollarSign,
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Zap,
  TrendingUp,
  Activity,
  ArrowRight,
  MessageSquare,
  AlertTriangle,
  BookOpen,
  Network,
  Lightbulb,
  Eye,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';

// Enhanced interfaces for autonomous intelligence
interface AgentReasoning {
  agent_id: string;
  agent_type: 'prediction' | 'passenger' | 'resource' | 'finance' | 'communication' | 'coordinator';
  reasoning_type: 'analytical' | 'predictive' | 'collaborative' | 'strategic' | 'conflict_resolution' | 'learning';
  context: Record<string, any>;
  reasoning_chain: string[];
  conclusion: string;
  confidence: number;
  evidence: string[];
  assumptions: string[];
  timestamp: string;
}

interface AgentCollaboration {
  collaboration_id: string;
  participating_agents: string[];
  collaboration_type: string;
  shared_context: Record<string, any>;
  messages: Array<{
    agent_id: string;
    agent_type: string;
    message: string;
    confidence: number;
    reasoning: string[];
    timestamp: string;
  }>;
  decisions: Array<Record<string, any>>;
  outcome?: string;
  timestamp: string;
}

interface ConflictResolution {
  conflict_id: string;
  conflict_type: 'resource_allocation' | 'priority_disagreement' | 'cost_optimization' | 'passenger_preference' | 'timeline_conflict' | 'regulatory_compliance';
  involved_agents: string[];
  conflict_description: string;
  resolution_steps: string[];
  consensus_status: 'in_progress' | 'achieved' | 'failed' | 'escalated';
  final_resolution?: string;
  compromise_points: string[];
  learning_outcomes: string[];
  timestamp: string;
}

interface LearningEvent {
  event_id: string;
  agent_id: string;
  decision_context: Record<string, any>;
  predicted_outcome: any;
  actual_outcome: any;
  feedback_score: number;
  lessons_learned: string[];
  model_adjustments: Record<string, any>;
  timestamp: string;
}

interface AutonomousIntelligenceStatus {
  timestamp: string;
  live_reasoning_feed: string[];
  agent_performance: {
    total_agents: number;
    active_collaborations: number;
    resolved_conflicts: number;
    learning_events: number;
    agent_details: Record<string, any>;
    system_health: string;
  };
  active_collaborations: Array<{
    id: string;
    agents: string[];
    type: string;
    messages_count: number;
  }>;
  recent_conflicts: Array<{
    id: string;
    type: string;
    agents: string[];
    status: string;
    resolution?: string;
  }>;
  learning_insights: Array<{
    agent_id: string;
    feedback_score: number;
    key_lesson: string;
  }>;
}

const agentConfig = {
  prediction: {
    name: 'Prediction Agent',
    icon: Brain,
    color: 'purple',
    emoji: '🔮',
    description: 'AI-powered disruption forecasting'
  },
  passenger: {
    name: 'Passenger Agent',
    icon: Users,
    color: 'blue',
    emoji: '👥',
    description: 'Individual passenger management'
  },
  resource: {
    name: 'Resource Agent',
    icon: Cpu,
    color: 'green',
    emoji: '🏨',
    description: 'Resource allocation and optimization'
  },
  finance: {
    name: 'Finance Agent',
    icon: DollarSign,
    color: 'emerald',
    emoji: '💰',
    description: 'Cost optimization and revenue protection'
  },
  communication: {
    name: 'Communication Agent',
    icon: MessageCircle,
    color: 'orange',
    emoji: '📱',
    description: 'Multi-channel communication'
  },
  coordinator: {
    name: 'Coordinator Agent',
    icon: Target,
    color: 'red',
    emoji: '🎯',
    description: 'Master coordination and strategy'
  }
};

const reasoningTypeConfig = {
  analytical: { label: 'Analytical', color: 'blue', icon: Brain },
  predictive: { label: 'Predictive', color: 'purple', icon: TrendingUp },
  collaborative: { label: 'Collaborative', color: 'green', icon: Network },
  strategic: { label: 'Strategic', color: 'orange', icon: Target },
  conflict_resolution: { label: 'Conflict Resolution', color: 'red', icon: AlertTriangle },
  learning: { label: 'Learning', color: 'yellow', icon: BookOpen }
};

const conflictTypeConfig = {
  resource_allocation: { label: 'Resource Allocation', color: 'blue' },
  priority_disagreement: { label: 'Priority Disagreement', color: 'orange' },
  cost_optimization: { label: 'Cost Optimization', color: 'green' },
  passenger_preference: { label: 'Passenger Preference', color: 'purple' },
  timeline_conflict: { label: 'Timeline Conflict', color: 'red' },
  regulatory_compliance: { label: 'Regulatory Compliance', color: 'yellow' }
};

export default function AutonomousAgentMonitor() {
  const [status, setStatus] = useState<AutonomousIntelligenceStatus | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'reasoning' | 'collaboration' | 'conflicts' | 'learning'>('reasoning');
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Simulate real-time data updates
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        // In production, this would be an API call to the autonomous orchestrator
        const mockStatus: AutonomousIntelligenceStatus = {
          timestamp: new Date().toISOString(),
          live_reasoning_feed: [
            `[${new Date().toLocaleTimeString()}] 🔮 PredictionAgent: Weather data indicates 78% probability of fog at LHR by 14:30. Initiating early warning protocol.`,
            `[${new Date(Date.now() - 30000).toLocaleTimeString()}] 👥 PassengerAgent: Analyzing 1,247 affected passengers. Priority ranking: 89 business class, 156 tight connections, 45 special needs.`,
            `[${new Date(Date.now() - 60000).toLocaleTimeString()}] 🏨 ResourceAgent: Negotiating hotel rates. Secured 340 rooms at 28% below standard rates. Transport coordination in progress.`,
            `[${new Date(Date.now() - 90000).toLocaleTimeString()}] 💰 FinanceAgent: Cost optimization complete. Projected savings: £156,300 vs traditional approach. Revenue protection: 94%.`,
            `[${new Date(Date.now() - 120000).toLocaleTimeString()}] 🎯 CoordinatorAgent: All agents aligned. Executing coordinated response. Passenger notifications initiating in 3... 2... 1...`,
            `[${new Date(Date.now() - 150000).toLocaleTimeString()}] 🧠 PassengerAgent: Learning from outcome (score: 0.92). Key insight: Early prediction enables 23% faster rebooking`,
            `[${new Date(Date.now() - 180000).toLocaleTimeString()}] 🤝 Collaboration initiated: Finance + Resource + Communication agents coordinating cost-optimal passenger care`,
            `[${new Date(Date.now() - 210000).toLocaleTimeString()}] ⚖️ Conflict resolved: Resource allocation vs passenger satisfaction. Consensus achieved through multi-criteria analysis.`
          ],
          agent_performance: {
            total_agents: 6,
            active_collaborations: 2,
            resolved_conflicts: 3,
            learning_events: 8,
            agent_details: {
              prediction_agent_01: { decisions_count: 24, success_rate: 0.94, avg_confidence: 0.87 },
              passenger_agent_01: { decisions_count: 156, success_rate: 0.91, avg_confidence: 0.83 },
              resource_agent_01: { decisions_count: 89, success_rate: 0.88, avg_confidence: 0.79 },
              finance_agent_01: { decisions_count: 34, success_rate: 0.96, avg_confidence: 0.91 },
              communication_agent_01: { decisions_count: 78, success_rate: 0.93, avg_confidence: 0.85 },
              coordinator_agent_01: { decisions_count: 45, success_rate: 0.89, avg_confidence: 0.82 }
            },
            system_health: 'healthy'
          },
          active_collaborations: [
            {
              id: 'collab_abc123',
              agents: ['finance_agent_01', 'resource_agent_01', 'passenger_agent_01'],
              type: 'cost_optimization',
              messages_count: 12
            },
            {
              id: 'collab_def456',
              agents: ['communication_agent_01', 'coordinator_agent_01'],
              type: 'passenger_communication',
              messages_count: 8
            }
          ],
          recent_conflicts: [
            {
              id: 'conflict_xyz789',
              type: 'resource_allocation',
              agents: ['resource_agent_01', 'finance_agent_01'],
              status: 'achieved',
              resolution: 'Resource allocation optimized for both cost and passenger satisfaction'
            },
            {
              id: 'conflict_uvw012',
              type: 'priority_disagreement',
              agents: ['passenger_agent_01', 'coordinator_agent_01'],
              status: 'achieved',
              resolution: 'Priority consensus achieved through multi-criteria analysis'
            }
          ],
          learning_insights: [
            {
              agent_id: 'prediction_agent_01',
              feedback_score: 0.94,
              key_lesson: 'Weather correlation models improved accuracy by 12%'
            },
            {
              agent_id: 'finance_agent_01',
              feedback_score: 0.89,
              key_lesson: 'Dynamic pricing negotiations save average 18% on accommodation'
            },
            {
              agent_id: 'passenger_agent_01',
              feedback_score: 0.91,
              key_lesson: 'Proactive rebooking reduces compensation claims by 31%'
            }
          ]
        };

        setStatus(mockStatus);
      } catch (error) {
        console.error('Error fetching autonomous intelligence status:', error);
      }
    };

    // Initial fetch
    fetchStatus();

    // Set up real-time updates if live
    let interval: NodeJS.Timeout;
    if (isLive) {
      interval = setInterval(fetchStatus, 2000); // Update every 2 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLive]);

  // Auto-scroll to bottom when new reasoning appears
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [status?.live_reasoning_feed, autoScroll]);

  const getColorClasses = (color: string, variant: 'bg' | 'text' | 'border' = 'bg') => {
    const colorMap: Record<string, Record<string, string>> = {
      purple: { bg: 'bg-purple-500', text: 'text-purple-600', border: 'border-purple-200' },
      blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-200' },
      green: { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-200' },
      emerald: { bg: 'bg-emerald-500', text: 'text-emerald-600', border: 'border-emerald-200' },
      orange: { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200' },
      red: { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200' },
      yellow: { bg: 'bg-yellow-500', text: 'text-yellow-600', border: 'border-yellow-200' }
    };
    return colorMap[color]?.[variant] || colorMap.blue[variant];
  };

  const formatConfidenceBar = (confidence: number) => {
    const width = confidence * 100;
    return (
      <div className="w-full bg-slate-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-500 ${
            confidence >= 0.8 ? 'bg-green-500' : 
            confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
          }`}
          style={{ width: `${width}%` }}
        />
      </div>
    );
  };

  if (!status) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-slate-400 mx-auto mb-4 animate-spin" />
          <p className="text-slate-500">Loading autonomous intelligence status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-slate-800 flex items-center space-x-3">
            <div className="relative">
              <Brain className="w-8 h-8 text-purple-600" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            </div>
            <span>Autonomous Agent Intelligence</span>
          </h1>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="text-sm text-slate-600">{isLive ? 'Live' : 'Paused'}</span>
            </div>
            <button
              onClick={() => setIsLive(!isLive)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isLive ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isLive ? (
                <>
                  <Pause className="w-4 h-4 inline mr-1" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 inline mr-1" />
                  Resume
                </>
              )}
            </button>
          </div>
        </div>

        {/* System Health Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-slate-800">{status.agent_performance.total_agents}</div>
            <div className="text-sm text-slate-600">Active Agents</div>
            <div className={`text-xs mt-1 px-2 py-1 rounded-full inline-block ${
              status.agent_performance.system_health === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {status.agent_performance.system_health.toUpperCase()}
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{status.agent_performance.active_collaborations}</div>
            <div className="text-sm text-slate-600">Active Collaborations</div>
            <div className="text-xs text-slate-500 mt-1">Real-time cooperation</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{status.agent_performance.resolved_conflicts}</div>
            <div className="text-sm text-slate-600">Conflicts Resolved</div>
            <div className="text-xs text-slate-500 mt-1">Autonomous consensus</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{status.agent_performance.learning_events}</div>
            <div className="text-sm text-slate-600">Learning Events</div>
            <div className="text-xs text-slate-500 mt-1">Continuous improvement</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-slate-100 rounded-lg p-1">
          {[
            { id: 'reasoning', label: 'Live Reasoning', icon: Eye },
            { id: 'collaboration', label: 'Agent Collaboration', icon: Network },
            { id: 'conflicts', label: 'Conflict Resolution', icon: AlertTriangle },
            { id: 'learning', label: 'Learning Events', icon: Lightbulb }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  selectedTab === tab.id
                    ? 'bg-white text-slate-800 shadow-sm'
                    : 'text-slate-600 hover:text-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {selectedTab === 'reasoning' && (
          <div className="h-full flex flex-col">
            <div className="p-4 bg-slate-50 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">Live Agent Reasoning Feed</h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setAutoScroll(!autoScroll)}
                    className={`px-3 py-1 rounded text-xs font-medium ${
                      autoScroll ? 'bg-green-500 text-white' : 'bg-slate-300 text-slate-600'
                    }`}
                  >
                    Auto-scroll {autoScroll ? 'ON' : 'OFF'}
                  </button>
                  <div className="text-xs text-slate-500">
                    {status.live_reasoning_feed.length} entries
                  </div>
                </div>
              </div>
            </div>
            
            <div 
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-sm"
            >
              {status.live_reasoning_feed.map((entry, index) => (
                <div key={index} className="bg-slate-900 text-green-400 p-3 rounded-lg border-l-4 border-green-500">
                  {entry}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'collaboration' && (
          <div className="p-6 overflow-y-auto">
            <div className="space-y-6">
              {status.active_collaborations.map((collab) => (
                <div key={collab.id} className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-slate-800">Collaboration: {collab.type}</h3>
                      <div className="text-sm text-slate-600">ID: {collab.id}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">{collab.messages_count}</div>
                      <div className="text-xs text-slate-500">Messages exchanged</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 mb-3">
                    <span className="text-sm font-medium text-slate-600">Participating Agents:</span>
                    {collab.agents.map((agent_id, idx) => {
                      const agentType = agent_id.split('_')[0] as keyof typeof agentConfig;
                      const config = agentConfig[agentType];
                      return (
                        <div key={idx} className="flex items-center space-x-1">
                          <span className="text-lg">{config?.emoji || '🤖'}</span>
                          <span className="text-sm text-slate-600">{config?.name || agent_id}</span>
                          {idx < collab.agents.length - 1 && <ArrowRight className="w-4 h-4 text-slate-400" />}
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="bg-white rounded p-3 text-sm">
                    <div className="text-slate-600">
                      🤝 Agents are actively collaborating on {collab.type.replace('_', ' ')} with {collab.messages_count} decision points analyzed.
                    </div>
                  </div>
                </div>
              ))}

              {status.active_collaborations.length === 0 && (
                <div className="text-center py-12">
                  <Network className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">No active collaborations</h3>
                  <p className="text-slate-500">Agents will initiate collaborations as needed for complex scenarios</p>
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'conflicts' && (
          <div className="p-6 overflow-y-auto">
            <div className="space-y-6">
              {status.recent_conflicts.map((conflict) => (
                <div key={conflict.id} className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-slate-800">
                        Conflict: {conflictTypeConfig[conflict.type as keyof typeof conflictTypeConfig]?.label || conflict.type}
                      </h3>
                      <div className="text-sm text-slate-600">ID: {conflict.id}</div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      conflict.status === 'achieved' ? 'bg-green-100 text-green-700' :
                      conflict.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' :
                      conflict.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {conflict.status.toUpperCase()}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 mb-3">
                    <span className="text-sm font-medium text-slate-600">Involved Agents:</span>
                    {conflict.agents.map((agent_id, idx) => {
                      const agentType = agent_id.split('_')[0] as keyof typeof agentConfig;
                      const config = agentConfig[agentType];
                      return (
                        <div key={idx} className="flex items-center space-x-1">
                          <span className="text-lg">{config?.emoji || '🤖'}</span>
                          <span className="text-sm text-slate-600">{config?.name || agent_id}</span>
                          {idx < conflict.agents.length - 1 && <span className="text-slate-400">vs</span>}
                        </div>
                      );
                    })}
                  </div>

                  {conflict.resolution && (
                    <div className="bg-white rounded p-3 text-sm">
                      <div className="font-medium text-slate-700 mb-1">Resolution:</div>
                      <div className="text-slate-600">{conflict.resolution}</div>
                    </div>
                  )}
                </div>
              ))}

              {status.recent_conflicts.length === 0 && (
                <div className="text-center py-12">
                  <AlertTriangle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">No recent conflicts</h3>
                  <p className="text-slate-500">The system is running smoothly with agent consensus</p>
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'learning' && (
          <div className="p-6 overflow-y-auto">
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
                <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
                  <Lightbulb className="w-5 h-5 text-yellow-500" />
                  <span>Recent Learning Insights</span>
                </h3>
                
                <div className="space-y-4">
                  {status.learning_insights.map((insight, idx) => {
                    const agentType = insight.agent_id.split('_')[0] as keyof typeof agentConfig;
                    const config = agentConfig[agentType];
                    
                    return (
                      <div key={idx} className="bg-white rounded-lg p-4 border border-slate-200">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{config?.emoji || '🤖'}</span>
                            <span className="font-medium text-slate-700">{config?.name || insight.agent_id}</span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-slate-800">
                              Score: {(insight.feedback_score * 100).toFixed(0)}%
                            </div>
                            {formatConfidenceBar(insight.feedback_score)}
                          </div>
                        </div>
                        
                        <div className="text-sm text-slate-600">
                          <span className="font-medium">Key Learning:</span> {insight.key_lesson}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Agent Performance Details */}
              <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                <h3 className="font-semibold text-slate-800 mb-4">Agent Performance Metrics</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(status.agent_performance.agent_details).map(([agent_id, metrics]) => {
                    const agentType = agent_id.split('_')[0] as keyof typeof agentConfig;
                    const config = agentConfig[agentType];
                    
                    return (
                      <div key={agent_id} className="bg-white rounded-lg p-4 border border-slate-200">
                        <div className="flex items-center space-x-2 mb-3">
                          <span className="text-lg">{config?.emoji || '🤖'}</span>
                          <span className="font-medium text-slate-700">{config?.name || agent_id}</span>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-600">Decisions:</span>
                            <span className="font-medium">{(metrics as any).decisions_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Success Rate:</span>
                            <span className="font-medium">{((metrics as any).success_rate * 100).toFixed(0)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Avg Confidence:</span>
                            <span className="font-medium">{((metrics as any).avg_confidence * 100).toFixed(0)}%</span>
                          </div>
                          <div className="mt-2">
                            {formatConfidenceBar((metrics as any).avg_confidence)}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}