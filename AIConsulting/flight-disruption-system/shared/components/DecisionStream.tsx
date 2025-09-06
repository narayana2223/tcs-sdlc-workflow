/**
 * DecisionStream Component
 * 
 * Real-time decision stream visualization showing agent reasoning chains,
 * data sources, and decision confidence with executive-grade transparency.
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import { 
  Brain, 
  Zap, 
  TrendingUp, 
  Users, 
  Clock,
  CheckCircle,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronRight,
  Database,
  Target,
  BarChart3,
  Lightbulb,
  ArrowRight,
  Cpu
} from 'lucide-react'

// Types for decision data
interface DataPoint {
  source: string
  description: string
  value: string
  confidence: number
  relevance: number
}

interface ReasoningStep {
  step: string
  description: string
  logic: string
  data_points: number
  confidence_impact: number
}

interface DecisionData {
  id: string
  agent: string
  type: string
  summary: string
  confidence: {
    score: number
    level: string
    bar: string
    percentage: string
  }
  reasoning_steps: ReasoningStep[]
  data_sources: DataPoint[]
  alternatives: Array<{
    description: string
    pros: string[]
    cons: string[]
    why_not_chosen: string
  }>
  impact: {
    passengers: number
    cost: string
    time: string
    satisfaction: string
    cascading_effects: string[]
  }
  timestamp: string
  execution_status: string
}

interface DecisionStreamEvent {
  type: string
  event_type: string
  timestamp: string
  data: DecisionData
}

interface DecisionStreamProps {
  className?: string
  maxDecisions?: number
  showFilters?: boolean
  compactMode?: boolean
  highlightAgents?: string[]
  onDecisionClick?: (decision: DecisionData) => void
}

const DecisionStream: React.FC<DecisionStreamProps> = ({
  className = "",
  maxDecisions = 10,
  showFilters = true,
  compactMode = false,
  highlightAgents = [],
  onDecisionClick
}) => {
  const [decisions, setDecisions] = useState<DecisionData[]>([])
  const [expandedDecisions, setExpandedDecisions] = useState<Set<string>>(new Set())
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [selectedAgent, setSelectedAgent] = useState<string>('all')
  const [selectedType, setSelectedType] = useState<string>('all')
  const [autoScroll, setAutoScroll] = useState(true)
  
  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<HTMLDivElement>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (autoScroll && streamRef.current) {
      streamRef.current.scrollTop = 0
    }
  }, [decisions, autoScroll])

  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting')
      
      // Connect to decision stream API
      const wsUrl = `ws://localhost:8014/ws/decisions`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setConnectionStatus('connected')
        reconnectAttempts.current = 0
        console.log('Connected to decision stream')
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        setConnectionStatus('disconnected')
        wsRef.current = null
        
        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < 5) {
          const delay = Math.pow(2, reconnectAttempts.current) * 1000
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connectWebSocket()
          }, delay)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('disconnected')
      }
      
      wsRef.current = ws
      
    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
      setConnectionStatus('disconnected')
    }
  }

  const handleMessage = (message: any) => {
    if (message.type === 'decision_event') {
      const decisionData = message.data as DecisionData
      
      setDecisions(prev => {
        const updated = [decisionData, ...prev.slice(0, maxDecisions - 1)]
        return updated
      })
      
      // Auto-expand new decisions for a few seconds
      setExpandedDecisions(prev => {
        const newSet = new Set(prev)
        newSet.add(decisionData.id)
        
        // Auto-collapse after 10 seconds
        setTimeout(() => {
          setExpandedDecisions(current => {
            const updated = new Set(current)
            updated.delete(decisionData.id)
            return updated
          })
        }, 10000)
        
        return newSet
      })
    }
  }

  const toggleExpanded = (decisionId: string) => {
    setExpandedDecisions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(decisionId)) {
        newSet.delete(decisionId)
      } else {
        newSet.add(decisionId)
      }
      return newSet
    })
  }

  const filteredDecisions = decisions.filter(decision => {
    if (selectedAgent !== 'all' && !decision.agent.toLowerCase().includes(selectedAgent.toLowerCase())) {
      return false
    }
    if (selectedType !== 'all' && decision.type !== selectedType) {
      return false
    }
    return true
  })

  const getAgentIcon = (agent: string) => {
    if (agent.includes('Prediction')) return Brain
    if (agent.includes('Passenger')) return Users
    if (agent.includes('Resource')) return Database
    if (agent.includes('Communication')) return Zap
    if (agent.includes('Coordinator')) return Target
    return Cpu
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    if (score >= 0.4) return 'text-orange-400'
    return 'text-red-400'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400'
      case 'executing': return 'text-blue-400'
      case 'failed': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Cpu className="h-6 w-6 text-blue-400" />
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400' : 
                connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">AI Decision Stream</h3>
              <p className="text-sm text-gray-400">Real-time agent reasoning and decision-making</p>
            </div>
          </div>
          
          {showFilters && (
            <div className="flex items-center space-x-4">
              <select 
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="bg-gray-800 border border-gray-600 text-white rounded px-3 py-1 text-sm"
              >
                <option value="all">All Agents</option>
                <option value="prediction">Prediction Agent</option>
                <option value="passenger">Passenger Agent</option>
                <option value="resource">Resource Agent</option>
                <option value="communication">Communication Agent</option>
                <option value="coordinator">Coordinator Agent</option>
              </select>
              
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`px-3 py-1 rounded text-sm ${
                  autoScroll ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'
                }`}
              >
                Auto-scroll
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Decision Stream */}
      <div 
        ref={streamRef}
        className="max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800"
      >
        {filteredDecisions.length === 0 ? (
          <div className="p-8 text-center">
            <Cpu className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No decisions to display</p>
            <p className="text-sm text-gray-500 mt-2">
              {connectionStatus === 'connected' 
                ? 'Waiting for agent decisions...' 
                : `Connection status: ${connectionStatus}`
              }
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {filteredDecisions.map((decision) => {
              const isExpanded = expandedDecisions.has(decision.id)
              const AgentIcon = getAgentIcon(decision.agent)
              const isHighlighted = highlightAgents.some(agent => 
                decision.agent.toLowerCase().includes(agent.toLowerCase())
              )
              
              return (
                <div 
                  key={decision.id}
                  className={`bg-gray-800 rounded-lg border transition-all duration-200 ${
                    isHighlighted ? 'border-blue-500 ring-1 ring-blue-500/20' : 'border-gray-700'
                  } ${isExpanded ? 'shadow-lg' : 'hover:border-gray-600'}`}
                >
                  {/* Decision Header */}
                  <div 
                    className="p-4 cursor-pointer"
                    onClick={() => toggleExpanded(decision.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <AgentIcon className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-sm font-medium text-blue-400">
                              {decision.agent}
                            </span>
                            <span className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded">
                              {decision.type}
                            </span>
                            <span className={`text-xs ${getStatusColor(decision.execution_status)}`}>
                              {decision.execution_status}
                            </span>
                          </div>
                          <p className="text-white text-sm leading-relaxed">
                            {decision.summary}
                          </p>
                          <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                            <span>{new Date(decision.timestamp).toLocaleTimeString()}</span>
                            <span>Impact: {decision.impact.passengers} passengers</span>
                            <span>Cost: {decision.impact.cost}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3 flex-shrink-0 ml-4">
                        <div className="text-right">
                          <div className={`text-sm font-semibold ${getConfidenceColor(decision.confidence.score)}`}>
                            {decision.confidence.percentage}
                          </div>
                          <div className="w-16 h-1 bg-gray-700 rounded-full overflow-hidden">
                            <div 
                              className={`h-full transition-all duration-300 ${
                                decision.confidence.score >= 0.8 ? 'bg-green-400' :
                                decision.confidence.score >= 0.6 ? 'bg-yellow-400' :
                                decision.confidence.score >= 0.4 ? 'bg-orange-400' : 'bg-red-400'
                              }`}
                              style={{ width: `${decision.confidence.score * 100}%` }}
                            />
                          </div>
                        </div>
                        
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-700 p-4 space-y-4">
                      {/* Reasoning Steps */}
                      {decision.reasoning_steps.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                            <Lightbulb className="h-4 w-4 mr-2 text-yellow-400" />
                            Reasoning Process
                          </h4>
                          <div className="space-y-2">
                            {decision.reasoning_steps.map((step, index) => (
                              <div key={index} className="flex items-start space-x-3">
                                <div className="flex items-center justify-center w-6 h-6 bg-blue-500 text-white text-xs rounded-full flex-shrink-0 mt-0.5">
                                  {index + 1}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-white">
                                    {step.step}
                                  </div>
                                  <div className="text-sm text-gray-300 mt-1">
                                    {step.description}
                                  </div>
                                  <div className="text-xs text-gray-400 mt-1">
                                    Logic: {step.logic}
                                  </div>
                                  {step.data_points > 0 && (
                                    <div className="text-xs text-blue-400 mt-1">
                                      Used {step.data_points} data points
                                    </div>
                                  )}
                                </div>
                                <div className="text-xs text-green-400 flex-shrink-0">
                                  +{(step.confidence_impact * 100).toFixed(1)}%
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Data Sources */}
                      {decision.data_sources.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                            <Database className="h-4 w-4 mr-2 text-green-400" />
                            Data Sources Used
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {decision.data_sources.map((source, index) => (
                              <div key={index} className="bg-gray-900 rounded p-3 border border-gray-700">
                                <div className="flex justify-between items-start mb-2">
                                  <span className="text-sm font-medium text-green-400">
                                    {source.source}
                                  </span>
                                  <span className="text-xs text-gray-400">
                                    {(source.confidence * 100).toFixed(0)}% confidence
                                  </span>
                                </div>
                                <p className="text-xs text-gray-300 mb-1">
                                  {source.description}
                                </p>
                                <p className="text-xs text-white font-mono">
                                  {source.value}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Alternatives Considered */}
                      {decision.alternatives.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                            <BarChart3 className="h-4 w-4 mr-2 text-purple-400" />
                            Alternatives Considered
                          </h4>
                          <div className="space-y-3">
                            {decision.alternatives.map((alt, index) => (
                              <div key={index} className="bg-gray-900 rounded p-3 border border-gray-700">
                                <p className="text-sm text-white mb-2">
                                  {alt.description}
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                  <div>
                                    <span className="text-xs font-medium text-green-400">Pros:</span>
                                    <ul className="text-xs text-gray-300 mt-1 space-y-1">
                                      {alt.pros.map((pro, i) => (
                                        <li key={i}>• {pro}</li>
                                      ))}
                                    </ul>
                                  </div>
                                  <div>
                                    <span className="text-xs font-medium text-red-400">Cons:</span>
                                    <ul className="text-xs text-gray-300 mt-1 space-y-1">
                                      {alt.cons.map((con, i) => (
                                        <li key={i}>• {con}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                                <div className="mt-2 pt-2 border-t border-gray-700">
                                  <span className="text-xs text-gray-400">Why not chosen: </span>
                                  <span className="text-xs text-gray-300">{alt.why_not_chosen}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Impact Assessment */}
                      <div>
                        <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                          <TrendingUp className="h-4 w-4 mr-2 text-orange-400" />
                          Expected Impact
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {decision.impact.passengers}
                            </div>
                            <div className="text-xs text-gray-400">Passengers</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {decision.impact.cost}
                            </div>
                            <div className="text-xs text-gray-400">Cost Impact</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {decision.impact.time}
                            </div>
                            <div className="text-xs text-gray-400">Time</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {decision.impact.satisfaction}
                            </div>
                            <div className="text-xs text-gray-400">Satisfaction</div>
                          </div>
                        </div>
                        
                        {decision.impact.cascading_effects.length > 0 && (
                          <div className="mt-3">
                            <span className="text-xs font-medium text-orange-400">Cascading Effects:</span>
                            <ul className="text-xs text-gray-300 mt-1 space-y-1">
                              {decision.impact.cascading_effects.map((effect, i) => (
                                <li key={i}>• {effect}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Action Button */}
                      {onDecisionClick && (
                        <div className="pt-2 border-t border-gray-700">
                          <button
                            onClick={() => onDecisionClick(decision)}
                            className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium transition-colors duration-200 flex items-center justify-center"
                          >
                            <ArrowRight className="h-4 w-4 mr-2" />
                            View Full Details
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default DecisionStream