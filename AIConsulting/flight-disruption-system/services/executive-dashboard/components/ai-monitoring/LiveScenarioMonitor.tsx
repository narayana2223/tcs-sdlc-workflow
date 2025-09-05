'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Clock, 
  Users, 
  DollarSign, 
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  CheckCircle,
  AlertCircle,
  Brain,
  Zap,
  BarChart3,
  Download,
  Settings,
  Eye,
  PlayCircle,
  PauseCircle,
  Square,
  FastForward
} from 'lucide-react';

// Types for live scenario execution
interface LiveScenarioEvent {
  id: string;
  timestamp: string;
  agent: string;
  description: string;
  confidence?: number;
  cost_impact?: number;
  passengers_affected?: number;
}

interface ScenarioMetrics {
  elapsed_time: string;
  completion_percentage: string;
  passengers: {
    total: number;
    processed: number;
    accommodated: number;
    pending: number;
  };
  costs: {
    total_cost: string;
    cost_savings: string;
    traditional_estimate: string;
  };
  decisions: {
    total: number;
    successful: number;
    success_rate: string;
    average_confidence: string;
  };
  estimated_completion: string;
}

interface PerformanceComparison {
  timelines: {
    agentic_approach: string;
    traditional_approach: string;
    time_saved: string;
  };
  costs: {
    agentic_cost: string;
    traditional_cost: string;
    savings: string;
    savings_percentage: string;
  };
  satisfaction: {
    agentic_satisfaction: string;
    traditional_satisfaction: string;
    improvement: string;
  };
  efficiency: {
    efficiency_gain: string;
    staff_hours_saved: string;
    automation_rate: string;
  };
}

interface ScenarioUpdate {
  type: 'event_executed' | 'status_update' | 'scenario_completed' | 'scenario_failed';
  event?: LiveScenarioEvent;
  metrics?: ScenarioMetrics;
  performance?: PerformanceComparison;
  scenario_status?: string;
  next_event_in?: number;
  final_metrics?: ScenarioMetrics;
  performance_comparison?: PerformanceComparison;
  summary?: any;
  error?: string;
}

const availableScenarios = {
  heathrow_fog_crisis: {
    name: "Heathrow Fog Crisis",
    description: "Dense fog affecting 2,500 passengers across 18 flights",
    severity: "critical",
    passengers: 2500,
    estimatedDuration: 30
  },
  aircraft_technical_failure: {
    name: "Aircraft Technical Failure",
    description: "A320 engine warning forces cancellation with 180 passengers",
    severity: "high", 
    passengers: 180,
    estimatedDuration: 20
  },
  airport_strike_action: {
    name: "Airport Strike Action",
    description: "Ground handling strike affecting 1,200 passengers",
    severity: "critical",
    passengers: 1200,
    estimatedDuration: 45
  },
  multiple_flight_delays: {
    name: "Multiple Flight Delays",
    description: "ATC issues causing cascade delays for 3,200 passengers",
    severity: "high",
    passengers: 3200,
    estimatedDuration: 35
  },
  peak_season_overload: {
    name: "Peak Season Overload",
    description: "Christmas period overload with 450 stranded passengers",
    severity: "critical",
    passengers: 450,
    estimatedDuration: 50
  }
};

const executionSpeeds = [
  { value: 0.5, label: '0.5x (Slow)', icon: PlayCircle },
  { value: 1.0, label: '1x (Normal)', icon: Play },
  { value: 2.0, label: '2x (Fast)', icon: FastForward },
  { value: 5.0, label: '5x (Very Fast)', icon: Zap },
  { value: 10.0, label: '10x (Ultra Fast)', icon: Brain }
];

export default function LiveScenarioMonitor() {
  // Scenario state
  const [selectedScenario, setSelectedScenario] = useState<string>('heathrow_fog_crisis');
  const [scenarioStatus, setScenarioStatus] = useState<'pending' | 'running' | 'paused' | 'completed' | 'failed'>('pending');
  const [executionSpeed, setExecutionSpeed] = useState<number>(1.0);
  
  // Live data
  const [currentMetrics, setCurrentMetrics] = useState<ScenarioMetrics | null>(null);
  const [performanceComparison, setPerformanceComparison] = useState<PerformanceComparison | null>(null);
  const [recentEvents, setRecentEvents] = useState<LiveScenarioEvent[]>([]);
  const [scenarioTimer, setScenarioTimer] = useState<string>('00:00');
  
  // UI state
  const [isDetailView, setIsDetailView] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const eventsScrollRef = useRef<HTMLDivElement>(null);
  
  // Simulation state
  const [simulationActive, setSimulationActive] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<Date | null>(null);

  // Mock scenario execution simulation
  useEffect(() => {
    if (simulationActive && scenarioStatus === 'running') {
      const scenario = availableScenarios[selectedScenario as keyof typeof availableScenarios];
      
      intervalRef.current = setInterval(() => {
        // Update timer
        if (startTimeRef.current) {
          const elapsed = (Date.now() - startTimeRef.current.getTime()) / 1000 * executionSpeed;
          const minutes = Math.floor(elapsed / 60);
          const seconds = Math.floor(elapsed % 60);
          setScenarioTimer(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
          
          // Simulate events and metrics updates
          simulateScenarioProgress(elapsed, scenario);
          
          // Check for completion
          if (elapsed > scenario.estimatedDuration * 60) {
            handleScenarioComplete();
          }
        }
      }, 1000);
      
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [simulationActive, scenarioStatus, executionSpeed, selectedScenario]);

  // Auto-scroll to bottom of events
  useEffect(() => {
    if (autoScroll && eventsScrollRef.current) {
      eventsScrollRef.current.scrollTop = eventsScrollRef.current.scrollHeight;
    }
  }, [recentEvents, autoScroll]);

  const simulateScenarioProgress = (elapsedSeconds: number, scenario: any) => {
    const progress = Math.min(elapsedSeconds / (scenario.estimatedDuration * 60), 1);
    
    // Simulate metrics updates
    const processedPassengers = Math.floor(scenario.passengers * progress * 0.95);
    const accommodatedPassengers = Math.floor(processedPassengers * 0.92);
    const totalCost = Math.floor(scenario.passengers * 150 * (1 - progress * 0.3));
    const savings = Math.floor(scenario.passengers * 200 * progress);
    
    setCurrentMetrics({
      elapsed_time: `${Math.floor(elapsedSeconds)}s`,
      completion_percentage: `${(progress * 100).toFixed(1)}%`,
      passengers: {
        total: scenario.passengers,
        processed: processedPassengers,
        accommodated: accommodatedPassengers,
        pending: scenario.passengers - processedPassengers
      },
      costs: {
        total_cost: `£${totalCost.toLocaleString()}`,
        cost_savings: `£${savings.toLocaleString()}`,
        traditional_estimate: `£${(scenario.passengers * 350).toLocaleString()}`
      },
      decisions: {
        total: Math.floor(progress * 25),
        successful: Math.floor(progress * 23),
        success_rate: '92.1%',
        average_confidence: '87.4%'
      },
      estimated_completion: `${Math.max(0, scenario.estimatedDuration * 60 - elapsedSeconds).toFixed(0)}s`
    });

    // Simulate performance comparison
    setPerformanceComparison({
      timelines: {
        agentic_approach: `${scenario.estimatedDuration} min`,
        traditional_approach: `${scenario.estimatedDuration * 8} min`,
        time_saved: `${scenario.estimatedDuration * 7} min`
      },
      costs: {
        agentic_cost: `£${totalCost.toLocaleString()}`,
        traditional_cost: `£${(scenario.passengers * 350).toLocaleString()}`,
        savings: `£${savings.toLocaleString()}`,
        savings_percentage: `${((savings / (scenario.passengers * 350)) * 100).toFixed(1)}%`
      },
      satisfaction: {
        agentic_satisfaction: '4.7/5',
        traditional_satisfaction: '2.1/5', 
        improvement: '2.6 points'
      },
      efficiency: {
        efficiency_gain: `${(700 / scenario.estimatedDuration).toFixed(0)}%`,
        staff_hours_saved: `${Math.floor(scenario.passengers / 20)} hours`,
        automation_rate: '94.2%'
      }
    });

    // Simulate occasional events
    if (Math.random() < 0.15 && recentEvents.length < 15) {
      const agents = ['Prediction', 'Passenger', 'Resource', 'Finance', 'Communication', 'Coordinator'];
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      
      const newEvent: LiveScenarioEvent = {
        id: `event_${Date.now()}`,
        timestamp: `${Math.floor(elapsedSeconds).toString().padStart(3, '0')}s`,
        agent: randomAgent,
        description: generateEventDescription(randomAgent, progress),
        confidence: 0.75 + Math.random() * 0.2,
        cost_impact: Math.random() > 0.5 ? -Math.floor(Math.random() * 5000) : undefined,
        passengers_affected: Math.random() > 0.7 ? Math.floor(Math.random() * 200) : undefined
      };
      
      setRecentEvents(prev => [...prev.slice(-10), newEvent]);
    }
  };

  const generateEventDescription = (agent: string, progress: number): string => {
    const descriptions = {
      'Prediction': [
        'Weather analysis indicates fog clearing in 2.5 hours with 89% confidence',
        'Impact prediction complete: cascade effects identified and modeled',
        'ML models updated with real-time data for improved accuracy'
      ],
      'Passenger': [
        'Priority passenger analysis complete: 89 business class identified',
        'EU261 compliance check passed for all affected passengers',
        'Rebooking optimization achieved 94% passenger satisfaction target'
      ],
      'Resource': [
        'Hotel inventory secured: 340 rooms at 28% below market rate',
        'Transport coordination complete: 45 coaches arranged',
        'Alternative aircraft identified: spare capacity confirmed'
      ],
      'Finance': [
        'Cost optimization achieved £47,000 savings vs traditional approach',
        'Dynamic pricing negotiation successful: 23% reduction secured',
        'ROI analysis complete: 340% return on AI investment'
      ],
      'Communication': [
        'Mass notification sent: 2,500 passengers updated via preferred channels',
        'Real-time status updates: 98% delivery rate achieved',
        'Multilingual support activated: 6 languages supported'
      ],
      'Coordinator': [
        'System coordination optimal: all agents working in harmony',
        'Strategic decision approved: resource allocation optimized',
        'Performance targets exceeded: 96% success rate maintained'
      ]
    };

    const agentDescriptions = descriptions[agent as keyof typeof descriptions] || ['Processing decision...'];
    return agentDescriptions[Math.floor(Math.random() * agentDescriptions.length)];
  };

  const handleStartScenario = async () => {
    setScenarioStatus('running');
    setSimulationActive(true);
    startTimeRef.current = new Date();
    setRecentEvents([]);
    setScenarioTimer('00:00');
  };

  const handlePauseScenario = () => {
    setScenarioStatus('paused');
    setSimulationActive(false);
  };

  const handleResumeScenario = () => {
    setScenarioStatus('running');
    setSimulationActive(true);
  };

  const handleResetScenario = () => {
    setScenarioStatus('pending');
    setSimulationActive(false);
    setCurrentMetrics(null);
    setPerformanceComparison(null);
    setRecentEvents([]);
    setScenarioTimer('00:00');
    startTimeRef.current = null;
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  const handleScenarioComplete = () => {
    setScenarioStatus('completed');
    setSimulationActive(false);
    
    // Add completion event
    const completionEvent: LiveScenarioEvent = {
      id: `completion_${Date.now()}`,
      timestamp: scenarioTimer,
      agent: 'System',
      description: '🎯 Scenario Complete: All objectives achieved with autonomous agent coordination',
      confidence: 0.96,
      cost_impact: -50000,
      passengers_affected: availableScenarios[selectedScenario as keyof typeof availableScenarios].passengers
    };
    
    setRecentEvents(prev => [...prev, completionEvent]);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'completed': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      default: return 'text-slate-600 bg-slate-100 border-slate-200';
    }
  };

  const selectedScenarioInfo = availableScenarios[selectedScenario as keyof typeof availableScenarios];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-slate-800 flex items-center space-x-3">
            <div className="relative">
              <PlayCircle className="w-8 h-8 text-blue-600" />
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse ${
                scenarioStatus === 'running' ? 'bg-green-500' : 
                scenarioStatus === 'paused' ? 'bg-yellow-500' :
                scenarioStatus === 'completed' ? 'bg-blue-500' : 'bg-slate-400'
              }`} />
            </div>
            <span>Live Scenario Execution</span>
          </h1>

          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(scenarioStatus)}`}>
              {scenarioStatus.toUpperCase()}
            </div>
            <div className="text-2xl font-mono font-bold text-slate-800">
              ⏱️ {scenarioTimer}
            </div>
          </div>
        </div>

        {/* Scenario Selection and Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scenario Selection */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-800">Select Disruption Scenario</h3>
            <select
              value={selectedScenario}
              onChange={(e) => {
                if (scenarioStatus === 'pending') {
                  setSelectedScenario(e.target.value);
                }
              }}
              disabled={scenarioStatus !== 'pending'}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm disabled:bg-slate-100"
            >
              {Object.entries(availableScenarios).map(([key, scenario]) => (
                <option key={key} value={key}>
                  {scenario.name} - {scenario.passengers.toLocaleString()} passengers
                </option>
              ))}
            </select>

            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-slate-800">{selectedScenarioInfo.name}</h4>
                <div className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(selectedScenarioInfo.severity)}`}>
                  {selectedScenarioInfo.severity.toUpperCase()}
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-3">{selectedScenarioInfo.description}</p>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500">Affected Passengers:</span>
                  <div className="font-semibold">{selectedScenarioInfo.passengers.toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-slate-500">Est. Duration:</span>
                  <div className="font-semibold">{selectedScenarioInfo.estimatedDuration} minutes</div>
                </div>
              </div>
            </div>
          </div>

          {/* Execution Controls */}
          <div className="space-y-4">
            <h3 className="font-semibold text-slate-800">Executive Controls</h3>
            
            {/* Primary Controls */}
            <div className="flex space-x-2">
              {scenarioStatus === 'pending' && (
                <button
                  onClick={handleStartScenario}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium"
                >
                  <Play className="w-4 h-4" />
                  <span>Start Scenario</span>
                </button>
              )}

              {scenarioStatus === 'running' && (
                <button
                  onClick={handlePauseScenario}
                  className="flex items-center space-x-2 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-medium"
                >
                  <Pause className="w-4 h-4" />
                  <span>Pause</span>
                </button>
              )}

              {scenarioStatus === 'paused' && (
                <button
                  onClick={handleResumeScenario}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium"
                >
                  <Play className="w-4 h-4" />
                  <span>Resume</span>
                </button>
              )}

              <button
                onClick={handleResetScenario}
                className="flex items-center space-x-2 px-4 py-2 bg-slate-500 hover:bg-slate-600 text-white rounded-lg font-medium"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset</span>
              </button>
            </div>

            {/* Speed Control */}
            <div>
              <label className="block text-sm text-slate-600 mb-2">Execution Speed</label>
              <div className="grid grid-cols-5 gap-1">
                {executionSpeeds.map((speed) => {
                  const Icon = speed.icon;
                  return (
                    <button
                      key={speed.value}
                      onClick={() => setExecutionSpeed(speed.value)}
                      className={`p-2 text-xs rounded border transition-all ${
                        executionSpeed === speed.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <Icon className="w-3 h-3 mx-auto mb-1" />
                      <div>{speed.value}x</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 xl:grid-cols-2 gap-6 p-6 overflow-hidden">
        {/* Live Metrics Panel */}
        <div className="space-y-6">
          {/* Real-time Metrics */}
          {currentMetrics && (
            <div className="bg-slate-50 rounded-lg p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Live Performance Metrics</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{currentMetrics.completion_percentage}</div>
                  <div className="text-sm text-slate-600">Complete</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{currentMetrics.decisions.success_rate}</div>
                  <div className="text-sm text-slate-600">Success Rate</div>
                </div>
              </div>

              {/* Passenger Status */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-slate-700">Passengers</span>
                  <span className="text-sm text-slate-600">
                    {currentMetrics.passengers.accommodated.toLocaleString()} / {currentMetrics.passengers.total.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${(currentMetrics.passengers.accommodated / currentMetrics.passengers.total) * 100}%` 
                    }}
                  />
                </div>
              </div>

              {/* Cost Metrics */}
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <div className="text-slate-500">Cost Savings</div>
                  <div className="font-semibold text-green-600">{currentMetrics.costs.cost_savings}</div>
                </div>
                <div>
                  <div className="text-slate-500">Decisions</div>
                  <div className="font-semibold">{currentMetrics.decisions.total}</div>
                </div>
                <div>
                  <div className="text-slate-500">Confidence</div>
                  <div className="font-semibold">{currentMetrics.decisions.average_confidence}</div>
                </div>
              </div>
            </div>
          )}

          {/* Performance Comparison */}
          {performanceComparison && (
            <div className="bg-slate-50 rounded-lg p-6">
              <h3 className="font-semibold text-slate-800 mb-4">Agentic vs Traditional Approach</h3>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-white rounded border">
                  <div>
                    <div className="text-sm text-slate-600">Resolution Time</div>
                    <div className="font-semibold text-green-600">
                      {performanceComparison.timelines.agentic_approach} 
                      <span className="text-slate-400 ml-2">vs {performanceComparison.timelines.traditional_approach}</span>
                    </div>
                  </div>
                  <TrendingDown className="w-5 h-5 text-green-500" />
                </div>

                <div className="flex justify-between items-center p-3 bg-white rounded border">
                  <div>
                    <div className="text-sm text-slate-600">Cost Savings</div>
                    <div className="font-semibold text-green-600">
                      {performanceComparison.costs.savings} 
                      <span className="text-xs text-slate-400 ml-1">({performanceComparison.costs.savings_percentage})</span>
                    </div>
                  </div>
                  <DollarSign className="w-5 h-5 text-green-500" />
                </div>

                <div className="flex justify-between items-center p-3 bg-white rounded border">
                  <div>
                    <div className="text-sm text-slate-600">Satisfaction Score</div>
                    <div className="font-semibold text-blue-600">
                      {performanceComparison.satisfaction.agentic_satisfaction}
                      <span className="text-slate-400 ml-2">vs {performanceComparison.satisfaction.traditional_satisfaction}</span>
                    </div>
                  </div>
                  <TrendingUp className="w-5 h-5 text-blue-500" />
                </div>

                <div className="flex justify-between items-center p-3 bg-white rounded border">
                  <div>
                    <div className="text-sm text-slate-600">Efficiency Gain</div>
                    <div className="font-semibold text-purple-600">{performanceComparison.efficiency.efficiency_gain}</div>
                  </div>
                  <Zap className="w-5 h-5 text-purple-500" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Live Agent Activity Feed */}
        <div className="bg-slate-50 rounded-lg p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-800">Live Agent Activity</h3>
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
                {recentEvents.length} events
              </div>
            </div>
          </div>

          <div 
            ref={eventsScrollRef}
            className="flex-1 overflow-y-auto space-y-3 pr-2"
          >
            {recentEvents.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Activity className="w-8 h-8 mx-auto mb-2" />
                <div>No agent activity yet</div>
                <div className="text-xs">Start a scenario to see live agent decisions</div>
              </div>
            ) : (
              recentEvents.map((event) => (
                <div key={event.id} className="bg-white rounded-lg p-4 border border-slate-200">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded text-xs font-medium ${
                        event.agent === 'System' ? 'bg-purple-100 text-purple-700' :
                        event.agent === 'Prediction' ? 'bg-blue-100 text-blue-700' :
                        event.agent === 'Passenger' ? 'bg-green-100 text-green-700' :
                        event.agent === 'Resource' ? 'bg-orange-100 text-orange-700' :
                        event.agent === 'Finance' ? 'bg-emerald-100 text-emerald-700' :
                        event.agent === 'Communication' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        🤖 {event.agent}Agent
                      </div>
                      <span className="text-xs text-slate-500 font-mono">{event.timestamp}</span>
                    </div>
                    {event.confidence && (
                      <div className="text-xs text-slate-600">
                        {(event.confidence * 100).toFixed(0)}% confidence
                      </div>
                    )}
                  </div>
                  
                  <p className="text-sm text-slate-700 mb-2">{event.description}</p>
                  
                  {(event.cost_impact || event.passengers_affected) && (
                    <div className="flex items-center space-x-4 text-xs text-slate-600">
                      {event.cost_impact && (
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-3 h-3" />
                          <span className={event.cost_impact < 0 ? 'text-green-600' : 'text-red-600'}>
                            {event.cost_impact < 0 ? 'Saved ' : 'Cost '}£{Math.abs(event.cost_impact).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {event.passengers_affected && (
                        <div className="flex items-center space-x-1">
                          <Users className="w-3 h-3" />
                          <span>{event.passengers_affected.toLocaleString()} passengers</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Bottom Action Bar */}
      {scenarioStatus === 'completed' && (
        <div className="border-t border-slate-200 p-4 bg-slate-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span>Scenario completed successfully</span>
              </div>
              {performanceComparison && (
                <div className="text-slate-600">
                  Saved {performanceComparison.costs.savings} ({performanceComparison.costs.savings_percentage})
                </div>
              )}
            </div>
            
            <div className="flex space-x-2">
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                <Download className="w-4 h-4" />
                <span>Export Results</span>
              </button>
              <button className="flex items-center space-x-2 px-4 py-2 bg-slate-500 hover:bg-slate-600 text-white rounded-lg text-sm">
                <Eye className="w-4 h-4" />
                <span>View Details</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}