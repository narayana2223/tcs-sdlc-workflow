/**
 * AgentCollaboration Component
 * 
 * Visualizes real-time agent collaboration, conflict resolution,
 * and consensus building with transparent negotiation processes.
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import {
  Users,
  MessageCircle,
  Handshake,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  ArrowRight,
  Zap,
  Target,
  Brain,
  Database,
  Phone,
  Crown,
  GitMerge,
  Timer,
  DollarSign
} from 'lucide-react'

interface CollaborationData {
  id: string
  agents: string[]
  type: string
  conflict: string
  status: 'Completed' | 'In Progress' | 'Failed'
  duration: string
  negotiation_steps: string[]
  consensus: string
  success: boolean
  outcomes: {
    efficiency_gain: string
    cost_optimization: string
    satisfaction_impact: string
  }
}

interface CollaborationEvent {
  type: string
  event_type: string
  timestamp: string
  data: CollaborationData
}

interface AgentCollaborationProps {
  className?: string
  maxCollaborations?: number
  showFilters?: boolean
  compactMode?: boolean
  onCollaborationClick?: (collaboration: CollaborationData) => void
}

const AgentCollaboration: React.FC<AgentCollaborationProps> = ({
  className = "",
  maxCollaborations = 8,
  showFilters = true,
  compactMode = false,
  onCollaborationClick
}) => {
  const [collaborations, setCollaborations] = useState<CollaborationData[]>([])
  const [expandedCollabs, setExpandedCollabs] = useState<Set<string>>(new Set())
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [animatingCollabs, setAnimatingCollabs] = useState<Set<string>>(new Set())
  
  const wsRef = useRef<WebSocket | null>(null)
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

  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting')
      
      const wsUrl = `ws://localhost:8014/ws/collaborations`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setConnectionStatus('connected')
        reconnectAttempts.current = 0
        console.log('Connected to collaboration stream')
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error parsing collaboration message:', error)
        }
      }
      
      ws.onclose = () => {
        setConnectionStatus('disconnected')
        wsRef.current = null
        
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
    if (message.type === 'collaboration_event') {
      const collabData = message.data as CollaborationData
      
      setCollaborations(prev => {
        const updated = [collabData, ...prev.slice(0, maxCollaborations - 1)]
        return updated
      })
      
      // Add animation effect for new collaborations
      setAnimatingCollabs(prev => {
        const newSet = new Set(prev)
        newSet.add(collabData.id)
        return newSet
      })
      
      setTimeout(() => {
        setAnimatingCollabs(prev => {
          const updated = new Set(prev)
          updated.delete(collabData.id)
          return updated
        })
      }, 2000)
      
      // Auto-expand new collaborations
      setExpandedCollabs(prev => {
        const newSet = new Set(prev)
        newSet.add(collabData.id)
        return newSet
      })
    }
  }

  const toggleExpanded = (collabId: string) => {
    setExpandedCollabs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(collabId)) {
        newSet.delete(collabId)
      } else {
        newSet.add(collabId)
      }
      return newSet
    })
  }

  const filteredCollaborations = collaborations.filter(collab => {
    if (selectedStatus !== 'all' && collab.status !== selectedStatus) {
      return false
    }
    return true
  })

  const getAgentIcon = (agent: string) => {
    if (agent.includes('Prediction')) return Brain
    if (agent.includes('Passenger')) return Users
    if (agent.includes('Resource')) return Database
    if (agent.includes('Communication')) return Phone
    if (agent.includes('Coordinator')) return Crown
    return Target
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-green-400 bg-green-400/10'
      case 'In Progress': return 'text-blue-400 bg-blue-400/10'
      case 'Failed': return 'text-red-400 bg-red-400/10'
      default: return 'text-gray-400 bg-gray-400/10'
    }
  }

  const getSuccessIcon = (success: boolean, status: string) => {
    if (status === 'In Progress') return <Timer className="h-4 w-4 text-blue-400 animate-spin" />
    if (success) return <CheckCircle className="h-4 w-4 text-green-400" />
    return <AlertCircle className="h-4 w-4 text-red-400" />
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Users className="h-6 w-6 text-purple-400" />
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-400' : 
                connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Agent Collaboration</h3>
              <p className="text-sm text-gray-400">Real-time agent negotiation and consensus building</p>
            </div>
          </div>
          
          {showFilters && (
            <select 
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-gray-800 border border-gray-600 text-white rounded px-3 py-1 text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="In Progress">In Progress</option>
              <option value="Failed">Failed</option>
            </select>
          )}
        </div>
      </div>

      {/* Collaboration Stream */}
      <div className="max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
        {filteredCollaborations.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No collaborations to display</p>
            <p className="text-sm text-gray-500 mt-2">
              {connectionStatus === 'connected' 
                ? 'Waiting for agent collaborations...' 
                : `Connection status: ${connectionStatus}`
              }
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {filteredCollaborations.map((collab) => {
              const isExpanded = expandedCollabs.has(collab.id)
              const isAnimating = animatingCollabs.has(collab.id)
              
              return (
                <div 
                  key={collab.id}
                  className={`bg-gray-800 rounded-lg border border-gray-700 transition-all duration-500 ${
                    isAnimating ? 'animate-pulse border-purple-500 ring-1 ring-purple-500/20' : ''
                  } ${isExpanded ? 'shadow-lg' : 'hover:border-gray-600'}`}
                >
                  {/* Collaboration Header */}
                  <div 
                    className="p-4 cursor-pointer"
                    onClick={() => toggleExpanded(collab.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <GitMerge className="h-5 w-5 text-purple-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-sm font-medium text-purple-400">
                              {collab.type}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${getStatusColor(collab.status)}`}>
                              {collab.status}
                            </span>
                            <span className="text-xs text-gray-400">
                              {collab.duration}
                            </span>
                          </div>
                          
                          {/* Participating Agents */}
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            {collab.agents.map((agent, index) => {
                              const AgentIcon = getAgentIcon(agent)
                              return (
                                <div key={index} className="flex items-center space-x-1 bg-gray-700 rounded-full px-2 py-1">
                                  <AgentIcon className="h-3 w-3 text-blue-400" />
                                  <span className="text-xs text-white">{agent}</span>
                                </div>
                              )
                            })}
                          </div>
                          
                          <p className="text-white text-sm leading-relaxed mb-2">
                            <span className="text-orange-400 font-medium">Conflict: </span>
                            {collab.conflict}
                          </p>
                          
                          <p className="text-gray-300 text-sm">
                            <span className="text-green-400 font-medium">Resolution: </span>
                            {collab.consensus}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3 flex-shrink-0 ml-4">
                        <div className="text-right">
                          {getSuccessIcon(collab.success, collab.status)}
                        </div>
                        <ArrowRight className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t border-gray-700 p-4 space-y-4">
                      {/* Negotiation Process */}
                      {collab.negotiation_steps.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                            <MessageCircle className="h-4 w-4 mr-2 text-blue-400" />
                            Negotiation Process
                          </h4>
                          <div className="space-y-3">
                            {collab.negotiation_steps.map((step, index) => (
                              <div key={index} className="flex items-start space-x-3">
                                <div className="flex items-center justify-center w-6 h-6 bg-blue-500 text-white text-xs rounded-full flex-shrink-0 mt-0.5">
                                  {index + 1}
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm text-gray-300 leading-relaxed">
                                    {step}
                                  </p>
                                </div>
                                <div className="text-xs text-blue-400">
                                  Step {index + 1}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Collaboration Outcomes */}
                      <div>
                        <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                          <TrendingUp className="h-4 w-4 mr-2 text-green-400" />
                          Collaboration Outcomes
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <div className="flex items-center space-x-2 mb-2">
                              <Zap className="h-4 w-4 text-yellow-400" />
                              <span className="text-sm font-medium text-white">Efficiency Gain</span>
                            </div>
                            <div className="text-lg font-semibold text-yellow-400">
                              {collab.outcomes.efficiency_gain}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Improved process efficiency
                            </div>
                          </div>
                          
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <div className="flex items-center space-x-2 mb-2">
                              <DollarSign className="h-4 w-4 text-green-400" />
                              <span className="text-sm font-medium text-white">Cost Optimization</span>
                            </div>
                            <div className="text-lg font-semibold text-green-400">
                              {collab.outcomes.cost_optimization}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Financial savings achieved
                            </div>
                          </div>
                          
                          <div className="bg-gray-900 rounded-lg p-3 border border-gray-700">
                            <div className="flex items-center space-x-2 mb-2">
                              <Users className="h-4 w-4 text-blue-400" />
                              <span className="text-sm font-medium text-white">Satisfaction Impact</span>
                            </div>
                            <div className="text-lg font-semibold text-blue-400">
                              {collab.outcomes.satisfaction_impact}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              Passenger satisfaction improvement
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Collaboration Analysis */}
                      <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                        <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                          <Brain className="h-4 w-4 mr-2 text-purple-400" />
                          Collaboration Analysis
                        </h4>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Participating Agents:</span>
                            <div className="text-white font-medium">{collab.agents.length} agents</div>
                          </div>
                          <div>
                            <span className="text-gray-400">Negotiation Duration:</span>
                            <div className="text-white font-medium">{collab.duration}</div>
                          </div>
                          <div>
                            <span className="text-gray-400">Consensus Achieved:</span>
                            <div className={`font-medium ${collab.success ? 'text-green-400' : 'text-red-400'}`}>
                              {collab.success ? 'Yes' : 'No'}
                            </div>
                          </div>
                          <div>
                            <span className="text-gray-400">Negotiation Steps:</span>
                            <div className="text-white font-medium">{collab.negotiation_steps.length} steps</div>
                          </div>
                        </div>

                        <div className="mt-4 pt-3 border-t border-gray-700">
                          <span className="text-gray-400 text-sm">Collaboration Type:</span>
                          <div className="text-white font-medium mt-1">
                            {collab.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                        </div>
                      </div>

                      {/* Action Button */}
                      {onCollaborationClick && (
                        <div className="pt-2 border-t border-gray-700">
                          <button
                            onClick={() => onCollaborationClick(collab)}
                            className="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded text-sm font-medium transition-colors duration-200 flex items-center justify-center"
                          >
                            <Handshake className="h-4 w-4 mr-2" />
                            View Collaboration Details
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

export default AgentCollaboration