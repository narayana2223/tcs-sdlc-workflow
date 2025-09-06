/**
 * Executive Demo Controls Component
 * 
 * Interactive controls for executive presentations and board demonstrations,
 * allowing real-time triggering of complex scenarios and agent behaviors
 * with transparent reasoning and ROI visualization.
 */

'use client'

import React, { useState, useEffect } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  Settings,
  Users,
  Zap,
  TrendingUp,
  Clock,
  DollarSign,
  Activity,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  Layers,
  Cpu,
  Globe,
  Calendar,
  Timer,
  Gauge
} from 'lucide-react'

interface DemoScenario {
  id: string
  name: string
  description: string
  complexity: 'low' | 'medium' | 'high' | 'extreme'
  duration: number
  passengerCount: number
  agentCount: number
  costImpact: number
  expectedSavings: number
  satisfactionTarget: number
  keyFeatures: string[]
  executiveValue: string[]
}

interface DemoMetrics {
  scenario_status: 'idle' | 'running' | 'paused' | 'completed'
  elapsed_time: number
  total_decisions: number
  active_agents: number
  passengers_processed: number
  cost_savings: number
  satisfaction_score: number
  conflicts_resolved: number
  automation_rate: number
}

interface ExecutiveDemoControlsProps {
  className?: string
  onScenarioStart?: (scenario: DemoScenario) => void
  onScenarioStop?: () => void
  onMetricsUpdate?: (metrics: DemoMetrics) => void
}

const ExecutiveDemoControls: React.FC<ExecutiveDemoControlsProps> = ({
  className = "",
  onScenarioStart,
  onScenarioStop,
  onMetricsUpdate
}) => {
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null)
  const [demoStatus, setDemoStatus] = useState<'idle' | 'running' | 'paused' | 'completed'>('idle')
  const [metrics, setMetrics] = useState<DemoMetrics>({
    scenario_status: 'idle',
    elapsed_time: 0,
    total_decisions: 0,
    active_agents: 0,
    passengers_processed: 0,
    cost_savings: 0,
    satisfaction_score: 0,
    conflicts_resolved: 0,
    automation_rate: 0
  })
  const [showAdvancedControls, setShowAdvancedControls] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)

  const demoScenarios: DemoScenario[] = [
    {
      id: 'london_weather_showcase',
      name: 'London Weather Crisis',
      description: 'Thunderstorm closes all London airports - 187 passengers, 4 hours',
      complexity: 'high',
      duration: 240,
      passengerCount: 187,
      agentCount: 6,
      costImpact: 680000,
      expectedSavings: 340000,
      satisfactionTarget: 4.2,
      keyFeatures: [
        'Multi-airport coordination',
        'Premium passenger conflicts',
        'Medical emergency handling',
        'Group booking optimization'
      ],
      executiveValue: [
        '91.7% faster resolution vs traditional',
        '£340K cost savings through AI optimization', 
        '4.2/5 satisfaction vs 2.1/5 traditional',
        '98% autonomous decision success rate'
      ]
    },
    {
      id: 'crew_strike_cascade',
      name: 'European Crew Strike',
      description: 'Multi-airline strikes - 203 passengers, complex crew scheduling',
      complexity: 'extreme',
      duration: 180,
      passengerCount: 203,
      agentCount: 7,
      costImpact: 890000,
      expectedSavings: 445000,
      satisfactionTarget: 4.0,
      keyFeatures: [
        'Cross-airline coordination',
        'Union compliance protocols',
        'Unaccompanied minor handling',
        'Regulatory adherence'
      ],
      executiveValue: [
        '75% flight operations maintained',
        '100% regulatory compliance achieved',
        '£445K savings vs manual coordination',
        'Zero legal compliance violations'
      ]
    },
    {
      id: 'atc_failure_demo',
      name: 'ATC System Failure',
      description: 'UK airspace closed - 267 passengers, international diversions',
      complexity: 'extreme',
      duration: 360,
      passengerCount: 267,
      agentCount: 8,
      costImpact: 1200000,
      expectedSavings: 600000,
      satisfactionTarget: 3.8,
      keyFeatures: [
        'Network optimization',
        'International coordination', 
        'Visa/customs handling',
        'Long-haul disruptions'
      ],
      executiveValue: [
        '95% successful European diversions',
        '98% passenger accommodation achieved',
        '£600K operational savings',
        'International compliance maintained'
      ]
    },
    {
      id: 'quick_demo_5min',
      name: '5-Minute Executive Demo',
      description: 'Condensed scenario - 45 passengers, key AI capabilities',
      complexity: 'medium',
      duration: 5,
      passengerCount: 45,
      agentCount: 4,
      costImpact: 125000,
      expectedSavings: 62500,
      satisfactionTarget: 4.5,
      keyFeatures: [
        'Rapid decision-making',
        'Transparent reasoning',
        'Cost optimization',
        'Conflict resolution'
      ],
      executiveValue: [
        'Sub-30-second decisions',
        'Transparent AI reasoning',
        '50% cost reduction achieved',
        'Board-ready visualization'
      ]
    }
  ]

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsConnection) {
        wsConnection.close()
      }
    }
  }, [])

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    if (demoStatus === 'running') {
      interval = setInterval(() => {
        setMetrics(prev => ({
          ...prev,
          elapsed_time: prev.elapsed_time + 1,
          total_decisions: prev.total_decisions + Math.floor(Math.random() * 3),
          passengers_processed: Math.min(
            prev.passengers_processed + Math.floor(Math.random() * 5), 
            selectedScenario?.passengerCount || 0
          ),
          cost_savings: prev.cost_savings + Math.floor(Math.random() * 5000),
          satisfaction_score: Math.min(4.8, prev.satisfaction_score + Math.random() * 0.1),
          conflicts_resolved: prev.conflicts_resolved + (Math.random() > 0.7 ? 1 : 0),
          automation_rate: Math.min(98, prev.automation_rate + Math.random() * 2)
        }))

        if (onMetricsUpdate) {
          onMetricsUpdate(metrics)
        }
      }, 1000 / playbackSpeed)
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [demoStatus, playbackSpeed, selectedScenario, metrics, onMetricsUpdate])

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8014/ws/demo_controls')
      
      ws.onopen = () => {
        setWsConnection(ws)
        console.log('Connected to demo controls')
      }
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        if (message.type === 'demo_metrics') {
          setMetrics(prev => ({ ...prev, ...message.data }))
        }
      }
      
      ws.onclose = () => {
        setWsConnection(null)
      }
      
    } catch (error) {
      console.error('WebSocket connection failed:', error)
    }
  }

  const startScenario = (scenario: DemoScenario) => {
    setSelectedScenario(scenario)
    setDemoStatus('running')
    setMetrics({
      scenario_status: 'running',
      elapsed_time: 0,
      total_decisions: 0,
      active_agents: scenario.agentCount,
      passengers_processed: 0,
      cost_savings: 0,
      satisfaction_score: 3.5,
      conflicts_resolved: 0,
      automation_rate: 85
    })

    // Trigger scenario via WebSocket
    if (wsConnection) {
      wsConnection.send(JSON.stringify({
        type: 'start_scenario',
        scenario_id: scenario.id,
        playback_speed: playbackSpeed
      }))
    }

    if (onScenarioStart) {
      onScenarioStart(scenario)
    }
  }

  const pauseScenario = () => {
    setDemoStatus('paused')
    if (wsConnection) {
      wsConnection.send(JSON.stringify({ type: 'pause_scenario' }))
    }
  }

  const resumeScenario = () => {
    setDemoStatus('running')
    if (wsConnection) {
      wsConnection.send(JSON.stringify({ type: 'resume_scenario' }))
    }
  }

  const resetScenario = () => {
    setDemoStatus('idle')
    setSelectedScenario(null)
    setMetrics({
      scenario_status: 'idle',
      elapsed_time: 0,
      total_decisions: 0,
      active_agents: 0,
      passengers_processed: 0,
      cost_savings: 0,
      satisfaction_score: 0,
      conflicts_resolved: 0,
      automation_rate: 0
    })

    if (wsConnection) {
      wsConnection.send(JSON.stringify({ type: 'reset_scenario' }))
    }

    if (onScenarioStop) {
      onScenarioStop()
    }
  }

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'text-green-400 bg-green-400/10'
      case 'medium': return 'text-yellow-400 bg-yellow-400/10'
      case 'high': return 'text-orange-400 bg-orange-400/10'
      case 'extreme': return 'text-red-400 bg-red-400/10'
      default: return 'text-gray-400 bg-gray-400/10'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Target className="h-6 w-6 text-indigo-400" />
            <div>
              <h3 className="text-lg font-semibold text-white">Executive Demo Controls</h3>
              <p className="text-sm text-gray-400">Interactive agentic intelligence demonstrations</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvancedControls(!showAdvancedControls)}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
              title="Advanced Controls"
            >
              <Settings className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Scenario Selection */}
        <div>
          <h4 className="text-sm font-semibold text-white mb-4 flex items-center">
            <Layers className="h-4 w-4 mr-2 text-indigo-400" />
            Select Demonstration Scenario
          </h4>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {demoScenarios.map((scenario) => (
              <div
                key={scenario.id}
                className={`p-4 rounded-lg border transition-all duration-200 cursor-pointer ${
                  selectedScenario?.id === scenario.id
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                }`}
                onClick={() => demoStatus === 'idle' && setSelectedScenario(scenario)}
              >
                <div className="flex justify-between items-start mb-3">
                  <h5 className="font-medium text-white">{scenario.name}</h5>
                  <span className={`text-xs px-2 py-1 rounded ${getComplexityColor(scenario.complexity)}`}>
                    {scenario.complexity.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-sm text-gray-400 mb-3">{scenario.description}</p>
                
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                  <div className="flex items-center text-gray-400">
                    <Timer className="h-3 w-3 mr-1" />
                    {scenario.duration < 60 ? `${scenario.duration}m` : `${Math.floor(scenario.duration/60)}h ${scenario.duration%60}m`}
                  </div>
                  <div className="flex items-center text-gray-400">
                    <Users className="h-3 w-3 mr-1" />
                    {scenario.passengerCount} passengers
                  </div>
                  <div className="flex items-center text-gray-400">
                    <Cpu className="h-3 w-3 mr-1" />
                    {scenario.agentCount} agents
                  </div>
                  <div className="flex items-center text-green-400">
                    <DollarSign className="h-3 w-3 mr-1" />
                    £{(scenario.expectedSavings/1000).toFixed(0)}K saved
                  </div>
                </div>

                {selectedScenario?.id === scenario.id && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="text-xs text-gray-400 mb-2">Executive Value:</div>
                    <div className="space-y-1">
                      {scenario.executiveValue.map((value, index) => (
                        <div key={index} className="text-xs text-green-400 flex items-center">
                          <CheckCircle className="h-3 w-3 mr-1 flex-shrink-0" />
                          {value}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Control Buttons */}
        <div>
          <h4 className="text-sm font-semibold text-white mb-4 flex items-center">
            <Activity className="h-4 w-4 mr-2 text-indigo-400" />
            Demo Controls
          </h4>
          
          <div className="flex items-center space-x-4">
            {demoStatus === 'idle' ? (
              <button
                onClick={() => selectedScenario && startScenario(selectedScenario)}
                disabled={!selectedScenario}
                className="flex items-center space-x-2 px-6 py-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <Play className="h-4 w-4" />
                <span>Start Demo</span>
              </button>
            ) : demoStatus === 'running' ? (
              <button
                onClick={pauseScenario}
                className="flex items-center space-x-2 px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-medium transition-colors"
              >
                <Pause className="h-4 w-4" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={resumeScenario}
                className="flex items-center space-x-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
              >
                <Play className="h-4 w-4" />
                <span>Resume</span>
              </button>
            )}

            <button
              onClick={resetScenario}
              disabled={demoStatus === 'idle'}
              className="flex items-center space-x-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </button>
          </div>

          {showAdvancedControls && (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
              <div className="flex items-center space-x-4">
                <div>
                  <label className="text-xs text-gray-400">Playback Speed:</label>
                  <select
                    value={playbackSpeed}
                    onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                    className="ml-2 bg-gray-700 border border-gray-600 text-white rounded px-2 py-1 text-sm"
                  >
                    <option value={0.5}>0.5x</option>
                    <option value={1}>1x</option>
                    <option value={2}>2x</option>
                    <option value={5}>5x</option>
                    <option value={10}>10x</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Live Metrics */}
        {demoStatus !== 'idle' && selectedScenario && (
          <div>
            <h4 className="text-sm font-semibold text-white mb-4 flex items-center">
              <BarChart3 className="h-4 w-4 mr-2 text-indigo-400" />
              Live Performance Metrics
            </h4>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <Clock className="h-4 w-4 text-blue-400" />
                  <span className="text-sm text-gray-400">Elapsed</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {formatTime(metrics.elapsed_time)}
                </div>
                <div className="text-xs text-gray-400">
                  / {formatTime(selectedScenario.duration * 60)}
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <Users className="h-4 w-4 text-green-400" />
                  <span className="text-sm text-gray-400">Processed</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {metrics.passengers_processed}
                </div>
                <div className="text-xs text-gray-400">
                  / {selectedScenario.passengerCount}
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <DollarSign className="h-4 w-4 text-yellow-400" />
                  <span className="text-sm text-gray-400">Savings</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  £{(metrics.cost_savings/1000).toFixed(0)}K
                </div>
                <div className="text-xs text-gray-400">
                  Target: £{(selectedScenario.expectedSavings/1000).toFixed(0)}K
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                <div className="flex items-center justify-between mb-1">
                  <TrendingUp className="h-4 w-4 text-purple-400" />
                  <span className="text-sm text-gray-400">Satisfaction</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {metrics.satisfaction_score.toFixed(1)}/5
                </div>
                <div className="text-xs text-gray-400">
                  Target: {selectedScenario.satisfactionTarget}/5
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{metrics.total_decisions}</div>
                <div className="text-xs text-gray-400">AI Decisions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{metrics.active_agents}</div>
                <div className="text-xs text-gray-400">Active Agents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400">{metrics.conflicts_resolved}</div>
                <div className="text-xs text-gray-400">Conflicts Resolved</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{metrics.automation_rate.toFixed(1)}%</div>
                <div className="text-xs text-gray-400">Automation Rate</div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>Scenario Progress</span>
                <span>{((metrics.passengers_processed / selectedScenario.passengerCount) * 100).toFixed(0)}% Complete</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${(metrics.passengers_processed / selectedScenario.passengerCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Status Indicator */}
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              demoStatus === 'running' ? 'bg-green-400 animate-pulse' :
              demoStatus === 'paused' ? 'bg-yellow-400' :
              demoStatus === 'completed' ? 'bg-blue-400' : 'bg-gray-400'
            }`} />
            <span className="text-white font-medium">
              {demoStatus === 'running' ? 'Demo Running' :
               demoStatus === 'paused' ? 'Demo Paused' :
               demoStatus === 'completed' ? 'Demo Completed' : 'Demo Ready'}
            </span>
          </div>

          {selectedScenario && (
            <div className="text-right">
              <div className="text-sm font-medium text-white">{selectedScenario.name}</div>
              <div className="text-xs text-gray-400">{selectedScenario.passengerCount} passengers • {selectedScenario.agentCount} agents</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ExecutiveDemoControls