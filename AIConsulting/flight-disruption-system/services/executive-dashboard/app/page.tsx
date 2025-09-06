'use client';

import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  Users, 
  Zap,
  Activity,
  Shield,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  Bot,
  Plane,
  MapPin,
  Phone,
  Calculator,
  MessageSquare,
  Settings,
  Maximize2
} from 'lucide-react';
// Shared components temporarily disabled due to dependency issues
// import DecisionStream from '../../../shared/components/DecisionStream';
// import AgentCollaboration from '../../../shared/components/AgentCollaboration';
// import DataFlowVisualization from '../../../shared/components/DataFlowVisualization';

interface LiveMetrics {
  todaysSavings: number;
  activeDisruptions: number;
  customerSatisfaction: number;
  revenueProtected: number;
  recoveryRate: number;
  humanInterventions: number;
}

interface AgentStatus {
  name: string;
  status: string;
  metric: string;
  accuracy: number;
  color: string;
  icon: React.ElementType;
}

interface CompetitiveMetric {
  name: string;
  ourValue: string;
  industryValue: string;
  improvement: string;
  color: string;
}

interface LiveDecision {
  id: string;
  time: string;
  agent: string;
  decision: string;
  impact: string;
  color: string;
}

export default function CXOOperationsCommandCenter() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics>({
    todaysSavings: 847600,
    activeDisruptions: 14,
    customerSatisfaction: 4.7,
    revenueProtected: 2300000,
    recoveryRate: 94,
    humanInterventions: 0
  });

  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([
    {
      name: 'DisruptionAgent',
      status: 'Monitoring 847 flights, 89% prediction accuracy',
      metric: '89%',
      accuracy: 89,
      color: 'text-green-600',
      icon: Activity
    },
    {
      name: 'PassengerAgent', 
      status: 'Managing 12,400 passengers, 0.3% escalation rate',
      metric: '0.3%',
      accuracy: 97,
      color: 'text-blue-600',
      icon: Users
    },
    {
      name: 'FinanceAgent',
      status: 'Optimizing costs, £156/passenger (vs £289 industry avg)',
      metric: '£156',
      accuracy: 94,
      color: 'text-purple-600',
      icon: Calculator
    },
    {
      name: 'CommunicationAgent',
      status: '94,600 messages sent, 97% satisfaction',
      metric: '97%',
      accuracy: 97,
      color: 'text-orange-600',
      icon: MessageSquare
    }
  ]);

  const [competitiveMetrics, setCompetitiveMetrics] = useState<CompetitiveMetric[]>([
    {
      name: 'Resolution Speed',
      ourValue: '18 minutes',
      industryValue: '4.2 hours',
      improvement: '+1300%',
      color: 'text-green-600'
    },
    {
      name: 'Cost Efficiency', 
      ourValue: '43% reduction',
      industryValue: 'Manual processes',
      improvement: '£156K saved',
      color: 'text-blue-600'
    },
    {
      name: 'Customer Retention',
      ourValue: '+67%',
      industryValue: 'During disruptions',
      improvement: '4.7/5 rating',
      color: 'text-purple-600'
    },
    {
      name: 'Staff Productivity',
      ourValue: '89% reduction',
      industryValue: 'Manual work',
      improvement: 'Full automation',
      color: 'text-orange-600'
    },
    {
      name: 'Predictive Accuracy',
      ourValue: '4.2 hours',
      industryValue: 'Advance warning',
      improvement: '89% accuracy',
      color: 'text-red-600'
    }
  ]);

  const [liveDecisions, setLiveDecisions] = useState<LiveDecision[]>([
    {
      id: '1',
      time: '14:23',
      agent: 'PredictionAgent',
      decision: 'Fog risk LHR 16:45, preemptive action initiated',
      impact: '340 passengers protected',
      color: 'text-yellow-600'
    },
    {
      id: '2', 
      time: '14:24',
      agent: 'ResourceAgent',
      decision: '340 hotel rooms secured £67/night (32% below market)',
      impact: '£73K saved vs market rate',
      color: 'text-green-600'
    },
    {
      id: '3',
      time: '14:25',
      agent: 'PassengerAgent',
      decision: '1,247 passengers notified, rebooking 89% complete',
      impact: 'Avg satisfaction: 4.8/5',
      color: 'text-blue-600'
    },
    {
      id: '4',
      time: '14:26',
      agent: 'FinanceAgent',
      decision: 'Revenue protection active, £156K preserved',
      impact: '94% recovery rate maintained',
      color: 'text-purple-600'
    },
    {
      id: '5',
      time: '14:27',
      agent: 'CommunicationAgent',
      decision: 'Satisfaction scores averaging 4.8/5',
      impact: '97% positive feedback',
      color: 'text-orange-600'
    }
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      
      // Update metrics slightly to show live changes
      setLiveMetrics(prev => ({
        ...prev,
        todaysSavings: prev.todaysSavings + Math.floor(Math.random() * 5000),
        customerSatisfaction: 4.7 + (Math.random() * 0.2 - 0.1),
        revenueProtected: prev.revenueProtected + Math.floor(Math.random() * 10000)
      }));

      // Occasionally add new decisions
      if (Math.random() < 0.1) {
        const newDecision: LiveDecision = {
          id: Date.now().toString(),
          time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
          agent: ['PredictionAgent', 'PassengerAgent', 'FinanceAgent', 'CommunicationAgent'][Math.floor(Math.random() * 4)],
          decision: 'New autonomous decision executed',
          impact: '£' + Math.floor(Math.random() * 50000) + ' impact',
          color: ['text-green-600', 'text-blue-600', 'text-purple-600', 'text-orange-600'][Math.floor(Math.random() * 4)]
        };
        
        setLiveDecisions(prev => [newDecision, ...prev.slice(0, 4)]);
      }
    }, 3000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-950 via-purple-950 to-indigo-950 text-white">
      {/* TOP BANNER - LIVE BUSINESS IMPACT */}
      <div className="bg-gradient-to-r from-emerald-600 via-cyan-500 to-blue-600 backdrop-blur-md border-b border-cyan-400/30 shadow-2xl">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-4 h-4 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
                <div className="w-4 h-4 bg-emerald-400 rounded-full animate-ping absolute top-0 left-0 opacity-30"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white tracking-wide">✦ LIVE OPERATIONS COMMAND CENTER</h1>
                <p className="text-emerald-100 text-sm font-medium">Real-time Autonomous Intelligence Platform</p>
              </div>
            </div>
            <div className="text-right bg-black/20 backdrop-blur-sm rounded-2xl px-4 py-3 border border-cyan-300/20">
              <div className="text-sm text-cyan-200 font-medium">Live Updates Every 3 Seconds</div>
              <div className="text-xl font-mono text-white font-bold">{currentTime.toLocaleTimeString()}</div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-emerald-400/30 shadow-xl hover:shadow-2xl hover:shadow-emerald-500/20 transition-all duration-300 group">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-emerald-500/20 rounded-2xl group-hover:bg-emerald-500/30 transition-colors">
                  <DollarSign className="w-6 h-6 text-emerald-400" />
                </div>
                <span className="text-sm font-semibold text-emerald-100">Today's Savings</span>
              </div>
              <div className="text-3xl font-bold text-emerald-400 mb-1 bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                £{liveMetrics.todaysSavings.toLocaleString()}
              </div>
              <div className="text-xs text-emerald-200/80 font-medium">vs traditional methods</div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-amber-400/30 shadow-xl hover:shadow-2xl hover:shadow-amber-500/20 transition-all duration-300 group">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-amber-500/20 rounded-2xl group-hover:bg-amber-500/30 transition-colors">
                  <Zap className="w-6 h-6 text-amber-400" />
                </div>
                <span className="text-sm font-semibold text-amber-100">Active Disruptions</span>
              </div>
              <div className="text-3xl font-bold text-amber-400 mb-1">{liveMetrics.activeDisruptions}</div>
              <div className="text-xs text-amber-200/80 font-medium">all managed autonomously</div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-cyan-400/30 shadow-xl hover:shadow-2xl hover:shadow-cyan-500/20 transition-all duration-300 group">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-cyan-500/20 rounded-2xl group-hover:bg-cyan-500/30 transition-colors">
                  <Users className="w-6 h-6 text-cyan-400" />
                </div>
                <span className="text-sm font-semibold text-cyan-100">Customer Satisfaction</span>
              </div>
              <div className="text-3xl font-bold text-cyan-400 mb-1 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                {liveMetrics.customerSatisfaction.toFixed(1)}/5
              </div>
              <div className="text-xs text-cyan-200/80 font-medium">industry avg: 2.3/5</div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-violet-400/30 shadow-xl hover:shadow-2xl hover:shadow-violet-500/20 transition-all duration-300 group">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-violet-500/20 rounded-2xl group-hover:bg-violet-500/30 transition-colors">
                  <TrendingUp className="w-6 h-6 text-violet-400" />
                </div>
                <span className="text-sm font-semibold text-violet-100">Revenue Protected</span>
              </div>
              <div className="text-3xl font-bold text-violet-400 mb-1 bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                £{(liveMetrics.revenueProtected / 1000000).toFixed(1)}M
              </div>
              <div className="text-xs text-violet-200/80 font-medium">{liveMetrics.recoveryRate}% recovery rate</div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-rose-400/30 shadow-xl hover:shadow-2xl hover:shadow-rose-500/20 transition-all duration-300 group">
              <div className="flex items-center space-x-3 mb-3">
                <div className="p-2 bg-rose-500/20 rounded-2xl group-hover:bg-rose-500/30 transition-colors">
                  <Shield className="w-6 h-6 text-rose-400" />
                </div>
                <span className="text-sm font-semibold text-rose-100">Human Interventions</span>
              </div>
              <div className="text-3xl font-bold text-rose-400 mb-1">{liveMetrics.humanInterventions}</div>
              <div className="text-xs text-rose-200/80 font-medium">100% autonomous operation</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 p-8">
        {/* LEFT PANEL - LIVE AGENT INTELLIGENCE */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-500">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4 mb-2">
                <div className="p-3 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl border border-cyan-400/30">
                  <Bot className="w-7 h-7 text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">🤖 AGENTIC AI STATUS</h2>
                  <p className="text-sm text-emerald-400 font-bold bg-emerald-400/10 px-3 py-1 rounded-full border border-emerald-400/30">FULLY AUTONOMOUS</p>
                </div>
              </div>
            </div>
            <div className="p-6 space-y-6">
              {agentStatuses.map((agent, index) => (
                <div key={index} className="bg-white/5 backdrop-blur-sm rounded-2xl p-5 border border-white/10 hover:border-white/20 transition-all duration-300 group hover:shadow-lg hover:shadow-cyan-500/5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 bg-gradient-to-r ${
                        agent.color.includes('green') ? 'from-emerald-500/20 to-green-500/20 border-emerald-400/30' :
                        agent.color.includes('blue') ? 'from-cyan-500/20 to-blue-500/20 border-cyan-400/30' :
                        agent.color.includes('purple') ? 'from-violet-500/20 to-purple-500/20 border-violet-400/30' :
                        'from-amber-500/20 to-orange-500/20 border-amber-400/30'
                      } rounded-xl border`}>
                        <agent.icon className={`w-5 h-5 ${
                          agent.color.includes('green') ? 'text-emerald-400' :
                          agent.color.includes('blue') ? 'text-cyan-400' :
                          agent.color.includes('purple') ? 'text-violet-400' :
                          'text-amber-400'
                        }`} />
                      </div>
                      <span className="font-bold text-white text-sm">{agent.name}</span>
                    </div>
                    <span className={`font-bold text-lg ${
                      agent.color.includes('green') ? 'text-emerald-400' :
                      agent.color.includes('blue') ? 'text-cyan-400' :
                      agent.color.includes('purple') ? 'text-violet-400' :
                      'text-amber-400'
                    }`}>{agent.metric}</span>
                  </div>
                  <p className="text-sm text-slate-200 mb-3">{agent.status}</p>
                  <div className="bg-white/5 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`h-3 rounded-full transition-all duration-700 ${
                        agent.color.includes('green') ? 'bg-gradient-to-r from-emerald-500 to-green-400' :
                        agent.color.includes('blue') ? 'bg-gradient-to-r from-cyan-500 to-blue-400' :
                        agent.color.includes('purple') ? 'bg-gradient-to-r from-violet-500 to-purple-400' :
                        'bg-gradient-to-r from-amber-500 to-orange-400'
                      } shadow-lg`}
                      style={{ width: `${agent.accuracy}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CENTER - LIVE OPERATIONAL MAP */}
        <div className="lg:col-span-2">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl hover:shadow-emerald-500/10 transition-all duration-500 h-full">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-r from-emerald-500/20 to-green-500/20 rounded-2xl border border-emerald-400/30">
                  <MapPin className="w-7 h-7 text-emerald-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">🗺️ REAL-TIME FLIGHT OPERATIONS</h2>
                  <p className="text-sm text-emerald-400 font-medium">Live Intelligence Network</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              {/* Simulated Map View */}
              <div className="bg-gradient-to-br from-indigo-950/50 via-purple-950/50 to-blue-950/50 rounded-2xl h-96 relative border border-cyan-500/20 overflow-hidden backdrop-blur-sm">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_rgba(0,0,0,0.3)_100%)]">
                  {/* Animated Background Grid */}
                  <div className="absolute inset-0 opacity-20">
                    <div className="absolute inset-0 bg-[linear-gradient(90deg,_rgba(6,182,212,0.1)_1px,_transparent_1px),_linear-gradient(0deg,_rgba(6,182,212,0.1)_1px,_transparent_1px)] bg-[size:20px_20px]"></div>
                  </div>
                  
                  {/* UK Map Outline */}
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <div className="text-6xl filter drop-shadow-lg">🗺️</div>
                  </div>
                  
                  {/* Live Flight Indicators */}
                  <div className="absolute top-20 left-20 flex items-center space-x-3 bg-black/40 backdrop-blur-sm rounded-2xl px-4 py-2 border border-emerald-400/30">
                    <div className="relative">
                      <div className="w-4 h-4 bg-emerald-500 rounded-full animate-pulse shadow-lg shadow-emerald-500/50"></div>
                      <div className="w-4 h-4 bg-emerald-500 rounded-full animate-ping absolute top-0 left-0 opacity-30"></div>
                    </div>
                    <span className="text-sm font-semibold text-emerald-400">LHR: 247 flights - Normal</span>
                  </div>
                  
                  <div className="absolute top-32 left-32 flex items-center space-x-3 bg-black/40 backdrop-blur-sm rounded-2xl px-4 py-2 border border-amber-400/30">
                    <div className="relative">
                      <div className="w-4 h-4 bg-amber-500 rounded-full animate-pulse shadow-lg shadow-amber-500/50"></div>
                      <div className="w-4 h-4 bg-amber-500 rounded-full animate-ping absolute top-0 left-0 opacity-30"></div>
                    </div>
                    <span className="text-sm font-semibold text-amber-400">LGW: 89 flights - Watch</span>
                  </div>
                  
                  <div className="absolute top-40 left-16 flex items-center space-x-3 bg-black/40 backdrop-blur-sm rounded-2xl px-4 py-2 border border-red-400/30">
                    <div className="relative">
                      <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse shadow-lg shadow-red-500/50"></div>
                      <div className="w-4 h-4 bg-red-500 rounded-full animate-ping absolute top-0 left-0 opacity-30"></div>
                    </div>
                    <span className="text-sm font-semibold text-red-400">MAN: 45 flights - Action</span>
                  </div>

                  {/* Weather Overlay */}
                  <div className="absolute bottom-6 left-6 bg-black/60 backdrop-blur-md rounded-2xl p-4 border border-cyan-400/30">
                    <h4 className="text-sm font-bold text-cyan-400 mb-3">⛈️ Predictive Weather</h4>
                    <div className="space-y-1">
                      <div className="text-sm text-amber-400 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                        <span>Fog risk LHR 16:45</span>
                      </div>
                      <div className="text-sm text-cyan-400 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
                        <span>Rain approaching EDI 18:30</span>
                      </div>
                    </div>
                  </div>

                  {/* Agent Actions Overlay */}
                  <div className="absolute bottom-6 right-6 bg-black/60 backdrop-blur-md rounded-2xl p-4 border border-violet-400/30">
                    <h4 className="text-sm font-bold text-violet-400 mb-3">🤖 Live Agent Actions</h4>
                    <div className="space-y-1">
                      <div className="text-sm text-emerald-400 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                        <span>340 hotels being booked</span>
                      </div>
                      <div className="text-sm text-cyan-400 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                        <span>1,247 passengers rebooking</span>
                      </div>
                      <div className="text-sm text-violet-400 flex items-center space-x-2">
                        <div className="w-2 h-2 bg-violet-400 rounded-full animate-pulse"></div>
                        <span>£156K cost optimization</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Live Passenger Flow */}
              <div className="mt-6 grid grid-cols-3 gap-4">
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 text-center border border-emerald-400/20 hover:border-emerald-400/40 transition-all duration-300">
                  <div className="text-2xl font-bold text-emerald-400 mb-1">12,400</div>
                  <div className="text-xs text-emerald-200/80 font-medium">Passengers Monitored</div>
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 text-center border border-amber-400/20 hover:border-amber-400/40 transition-all duration-300">
                  <div className="text-2xl font-bold text-amber-400 mb-1">847</div>
                  <div className="text-xs text-amber-200/80 font-medium">Flights Tracked</div>
                </div>
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 text-center border border-cyan-400/20 hover:border-cyan-400/40 transition-all duration-300">
                  <div className="text-2xl font-bold text-cyan-400 mb-1">94%</div>
                  <div className="text-xs text-cyan-200/80 font-medium">Automation Rate</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL - COMPETITIVE ADVANTAGE TRACKER */}
        <div className="lg:col-span-1">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl hover:shadow-violet-500/10 transition-all duration-500 h-full">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4 mb-2">
                <div className="p-3 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-2xl border border-violet-400/30">
                  <Target className="w-7 h-7 text-violet-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">🏆 vs COMPETITION</h2>
                  <p className="text-sm text-violet-400 font-medium">TRADITIONAL METHODS</p>
                </div>
              </div>
            </div>
            <div className="p-6 space-y-6">
              {competitiveMetrics.map((metric, index) => (
                <div key={index} className="bg-white/5 backdrop-blur-sm rounded-2xl p-5 border border-white/10 hover:border-white/20 transition-all duration-300 group hover:shadow-lg hover:shadow-violet-500/5">
                  <div className="mb-3">
                    <div className="text-sm font-bold text-white mb-2">{metric.name}</div>
                    <div className={`text-xl font-bold mb-1 ${
                      metric.color.includes('green') ? 'text-emerald-400 bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent' :
                      metric.color.includes('blue') ? 'text-cyan-400 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent' :
                      metric.color.includes('purple') ? 'text-violet-400 bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent' :
                      metric.color.includes('orange') ? 'text-amber-400 bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent' :
                      'text-rose-400 bg-gradient-to-r from-rose-400 to-red-400 bg-clip-text text-transparent'
                    }`}>{metric.ourValue}</div>
                    <div className="text-xs text-slate-300 mb-1">vs {metric.industryValue}</div>
                    <div className={`text-xs font-bold px-2 py-1 rounded-full ${
                      metric.color.includes('green') ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-400/20' :
                      metric.color.includes('blue') ? 'text-cyan-400 bg-cyan-400/10 border border-cyan-400/20' :
                      metric.color.includes('purple') ? 'text-violet-400 bg-violet-400/10 border border-violet-400/20' :
                      metric.color.includes('orange') ? 'text-amber-400 bg-amber-400/10 border border-amber-400/20' :
                      'text-rose-400 bg-rose-400/10 border border-rose-400/20'
                    }`}>{metric.improvement}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ENHANCED AGENTIC INTELLIGENCE PANELS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 px-8">
        {/* Real-time Decision Stream */}
        <div className="lg:col-span-1">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl border border-cyan-400/30">
                  <Activity className="w-7 h-7 text-cyan-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">🔄 DECISION STREAM</h2>
                  <p className="text-sm text-cyan-400 font-medium">Live AI Reasoning</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-2">🔄</div>
                <p className="text-sm">Decision Stream Component</p>
                <p className="text-xs text-gray-500">Available in Agentic Intelligence page</p>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Collaboration Monitor */}
        <div className="lg:col-span-1">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-2xl border border-violet-400/30">
                  <Bot className="w-7 h-7 text-violet-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">🤝 AGENT COLLABORATION</h2>
                  <p className="text-sm text-violet-400 font-medium">Multi-Agent Consensus</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-2">🤝</div>
                <p className="text-sm">Agent Collaboration Component</p>
                <p className="text-xs text-gray-500">Available in Agentic Intelligence page</p>
              </div>
            </div>
          </div>
        </div>

        {/* Data Flow Visualization */}
        <div className="lg:col-span-1">
          <div className="bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl">
            <div className="p-6 border-b border-white/10">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-r from-emerald-500/20 to-green-500/20 rounded-2xl border border-emerald-400/30">
                  <MapPin className="w-7 h-7 text-emerald-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide">📊 DATA FLOW</h2>
                  <p className="text-sm text-emerald-400 font-medium">Inter-Module Communication</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-2">📊</div>
                <p className="text-sm">Data Flow Visualization Component</p>
                <p className="text-xs text-gray-500">Available in Agentic Intelligence page</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM TICKER - LIVE AGENT DECISIONS */}
      <div className="bg-gradient-to-r from-indigo-900/80 via-purple-900/80 to-blue-900/80 backdrop-blur-xl border-t border-cyan-400/30 shadow-2xl">
        <div className="px-8 py-6">
          <div className="flex items-center space-x-6 mb-4">
            <div className="p-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl border border-cyan-400/30">
              <Activity className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white tracking-wide">🔄 LIVE AGENTIC DECISIONS STREAM</h2>
              <div className="text-sm text-cyan-400 font-medium">Real-time autonomous intelligence</div>
            </div>
          </div>
          
          <div className="space-y-3 max-h-40 overflow-y-auto custom-scrollbar">
            {liveDecisions.map((decision) => (
              <div key={decision.id} className="flex items-center justify-between bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10 hover:border-white/20 transition-all duration-300 group">
                <div className="flex items-center space-x-6">
                  <div className="bg-black/30 rounded-xl px-3 py-1">
                    <span className="text-sm text-slate-300 font-mono font-bold">{decision.time}</span>
                  </div>
                  <div className={`font-bold text-sm px-3 py-1 rounded-full ${
                    decision.color.includes('yellow') ? 'text-amber-400 bg-amber-400/10 border border-amber-400/20' :
                    decision.color.includes('green') ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-400/20' :
                    decision.color.includes('blue') ? 'text-cyan-400 bg-cyan-400/10 border border-cyan-400/20' :
                    decision.color.includes('purple') ? 'text-violet-400 bg-violet-400/10 border border-violet-400/20' :
                    'text-rose-400 bg-rose-400/10 border border-rose-400/20'
                  }`}>{decision.agent}</div>
                  <span className="text-sm text-white font-medium">{decision.decision}</span>
                </div>
                <div className="bg-emerald-400/10 border border-emerald-400/20 rounded-xl px-4 py-2">
                  <span className="text-sm text-emerald-400 font-bold">{decision.impact}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Executive Action Bar */}
      <div className="bg-black/40 backdrop-blur-xl border-t border-white/10 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
              <span className="text-white font-medium">System Status: </span>
              <span className="text-emerald-400 font-bold">OPERATIONAL</span>
            </div>
            <div className="w-px h-4 bg-white/20"></div>
            <div className="text-slate-300">
              <span className="text-white font-medium">Last Update: </span>
              <span className="font-mono">{currentTime.toLocaleTimeString()}</span>
            </div>
            <div className="w-px h-4 bg-white/20"></div>
            <div className="text-emerald-400 font-bold">100% Autonomous Operation</div>
          </div>
          <div className="flex items-center space-x-4">
            <button className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-2xl text-sm font-semibold transition-all duration-300 border border-cyan-400/30 shadow-lg hover:shadow-cyan-500/20">
              Export Report
            </button>
            <button className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white rounded-2xl text-sm font-semibold transition-all duration-300 border border-emerald-400/30 shadow-lg hover:shadow-emerald-500/20">
              Board Presentation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}