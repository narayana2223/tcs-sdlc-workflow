/**
 * DataFlowVisualization Component
 * 
 * Visualizes real-time data flow and communication between modules,
 * showing how decisions propagate across Operations Control Center,
 * Executive Dashboard, and Passenger Portal.
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import {
  ArrowRight,
  ArrowDown,
  Database,
  Monitor,
  Users,
  Smartphone,
  Cpu,
  Zap,
  Activity,
  GitBranch,
  Radio,
  Send,
  Inbox,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface DataFlowEvent {
  id: string
  source_module: 'operations_center' | 'executive_dashboard' | 'passenger_portal' | 'decision_api'
  target_module: 'operations_center' | 'executive_dashboard' | 'passenger_portal' | 'decision_api'
  data_type: 'decision' | 'passenger_update' | 'system_metric' | 'collaboration' | 'demo_control'
  content: string
  timestamp: string
  status: 'sending' | 'delivered' | 'processed' | 'failed'
  path: string[]
  metadata: {
    agent_id?: string
    passenger_count?: number
    cost_impact?: number
    priority?: number
  }
}

interface ModuleStatus {
  id: string
  name: string
  status: 'online' | 'offline' | 'degraded'
  connections: number
  messages_sent: number
  messages_received: number
  last_activity: string
}

interface DataFlowVisualizationProps {
  className?: string
  showPaths?: boolean
  highlightModule?: string
  maxEvents?: number
}

const DataFlowVisualization: React.FC<DataFlowVisualizationProps> = ({
  className = "",
  showPaths = true,
  highlightModule,
  maxEvents = 20
}) => {
  const [dataFlows, setDataFlows] = useState<DataFlowEvent[]>([])
  const [activeFlows, setActiveFlows] = useState<Set<string>>(new Set())
  const [moduleStats, setModuleStats] = useState<ModuleStatus[]>([
    {
      id: 'operations_center',
      name: 'Operations Control Center',
      status: 'online',
      connections: 12,
      messages_sent: 847,
      messages_received: 623,
      last_activity: new Date().toISOString()
    },
    {
      id: 'executive_dashboard',
      name: 'Executive Dashboard',
      status: 'online',
      connections: 8,
      messages_sent: 234,
      messages_received: 891,
      last_activity: new Date().toISOString()
    },
    {
      id: 'passenger_portal',
      name: 'Passenger Portal',
      status: 'online',
      connections: 156,
      messages_sent: 445,
      messages_received: 223,
      last_activity: new Date().toISOString()
    },
    {
      id: 'decision_api',
      name: 'Decision Stream API',
      status: 'online',
      connections: 3,
      messages_sent: 1234,
      messages_received: 0,
      last_activity: new Date().toISOString()
    }
  ])
  const [selectedFlow, setSelectedFlow] = useState<DataFlowEvent | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('connected')
  
  const wsRef = useRef<WebSocket | null>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    connectWebSocket()
    startAnimation()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8014/ws/all`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        setConnectionStatus('connected')
        console.log('Connected to data flow stream')
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error parsing data flow message:', error)
        }
      }
      
      ws.onclose = () => {
        setConnectionStatus('disconnected')
        wsRef.current = null
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
    const flowEvent: DataFlowEvent = {
      id: `flow_${Date.now()}_${Math.random()}`,
      source_module: determineSourceModule(message),
      target_module: determineTargetModule(message),
      data_type: message.type === 'decision_event' ? 'decision' :
                 message.type === 'collaboration_event' ? 'collaboration' :
                 message.type === 'system_analytics' ? 'system_metric' : 'passenger_update',
      content: getFlowContent(message),
      timestamp: message.timestamp || new Date().toISOString(),
      status: 'sending',
      path: generateFlowPath(message),
      metadata: {
        agent_id: message.data?.agent,
        passenger_count: message.data?.impact?.passengers,
        cost_impact: message.data?.impact?.cost,
        priority: getPriority(message)
      }
    }
    
    addDataFlow(flowEvent)
  }

  const addDataFlow = (flow: DataFlowEvent) => {
    setDataFlows(prev => [flow, ...prev.slice(0, maxEvents - 1)])
    
    // Add to active flows for animation
    setActiveFlows(prev => new Set([...prev, flow.id]))
    
    // Simulate flow progression
    setTimeout(() => {
      setDataFlows(prev => prev.map(f => 
        f.id === flow.id ? { ...f, status: 'delivered' } : f
      ))
    }, 1000)
    
    setTimeout(() => {
      setDataFlows(prev => prev.map(f => 
        f.id === flow.id ? { ...f, status: 'processed' } : f
      ))
    }, 2000)
    
    setTimeout(() => {
      setActiveFlows(prev => {
        const updated = new Set(prev)
        updated.delete(flow.id)
        return updated
      })
    }, 3000)
  }

  const startAnimation = () => {
    // Generate demo flows periodically
    const generateDemoFlow = () => {
      const demoFlows = [
        {
          source: 'decision_api',
          target: 'operations_center',
          type: 'decision',
          content: 'Prediction Agent: Weather delay analysis for LHR'
        },
        {
          source: 'operations_center',
          target: 'executive_dashboard',
          type: 'system_metric',
          content: 'Updated cost savings: £2.45M (+£12.5K)'
        },
        {
          source: 'executive_dashboard',
          target: 'passenger_portal',
          type: 'passenger_update',
          content: 'Passenger rebooking completed for Sarah Chen'
        }
      ]
      
      const demo = demoFlows[Math.floor(Math.random() * demoFlows.length)]
      const flow: DataFlowEvent = {
        id: `demo_${Date.now()}_${Math.random()}`,
        source_module: demo.source as any,
        target_module: demo.target as any,
        data_type: demo.type as any,
        content: demo.content,
        timestamp: new Date().toISOString(),
        status: 'sending',
        path: [demo.source, demo.target],
        metadata: {
          passenger_count: Math.floor(Math.random() * 50),
          cost_impact: Math.floor(Math.random() * 50000),
          priority: Math.floor(Math.random() * 10)
        }
      }
      
      addDataFlow(flow)
    }
    
    // Generate demo flows every 5 seconds
    const interval = setInterval(generateDemoFlow, 5000)
    
    return () => clearInterval(interval)
  }

  const getModuleIcon = (moduleId: string) => {
    switch (moduleId) {
      case 'operations_center': return Monitor
      case 'executive_dashboard': return Database
      case 'passenger_portal': return Smartphone
      case 'decision_api': return Cpu
      default: return Radio
    }
  }

  const getModuleColor = (moduleId: string) => {
    switch (moduleId) {
      case 'operations_center': return 'text-blue-400 bg-blue-400/10 border-blue-400/20'
      case 'executive_dashboard': return 'text-purple-400 bg-purple-400/10 border-purple-400/20'
      case 'passenger_portal': return 'text-green-400 bg-green-400/10 border-green-400/20'
      case 'decision_api': return 'text-orange-400 bg-orange-400/10 border-orange-400/20'
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sending': return 'text-yellow-400'
      case 'delivered': return 'text-blue-400'
      case 'processed': return 'text-green-400'
      case 'failed': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getDataTypeIcon = (dataType: string) => {
    switch (dataType) {
      case 'decision': return Cpu
      case 'collaboration': return Users
      case 'system_metric': return Activity
      case 'passenger_update': return Smartphone
      default: return Radio
    }
  }

  // Helper functions
  const determineSourceModule = (message: any): any => {
    if (message.type === 'decision_event') return 'decision_api'
    if (message.type === 'system_analytics') return 'operations_center'
    return 'decision_api'
  }

  const determineTargetModule = (message: any): any => {
    if (message.type === 'decision_event') return 'operations_center'
    if (message.type === 'passenger_update') return 'passenger_portal'
    return 'executive_dashboard'
  }

  const getFlowContent = (message: any): string => {
    if (message.data?.summary) return message.data.summary
    if (message.data?.agent) return `${message.data.agent}: ${message.type}`
    return `${message.type} event`
  }

  const generateFlowPath = (message: any): string[] => {
    const source = determineSourceModule(message)
    const target = determineTargetModule(message)
    return [source, target]
  }

  const getPriority = (message: any): number => {
    if (message.type === 'decision_event') return 8
    if (message.type === 'collaboration_event') return 7
    if (message.type === 'system_analytics') return 5
    return 3
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <GitBranch className="h-6 w-6 text-indigo-400" />
            <div>
              <h3 className="text-lg font-semibold text-white">Inter-Module Data Flow</h3>
              <p className="text-sm text-gray-400">Real-time communication and data propagation</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-gray-400 capitalize">{connectionStatus}</span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Module Status Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {moduleStats.map((module) => {
            const ModuleIcon = getModuleIcon(module.id)
            const isHighlighted = highlightModule === module.id
            
            return (
              <div 
                key={module.id}
                className={`p-4 rounded-lg border transition-all duration-200 ${
                  getModuleColor(module.id)
                } ${isHighlighted ? 'ring-2 ring-current' : ''}`}
              >
                <div className="flex items-center space-x-2 mb-3">
                  <ModuleIcon className="h-4 w-4" />
                  <span className="text-sm font-medium text-white">{module.name}</span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Connections:</span>
                    <span className="text-white">{module.connections}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Sent:</span>
                    <span className="text-white">{module.messages_sent.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Received:</span>
                    <span className="text-white">{module.messages_received.toLocaleString()}</span>
                  </div>
                </div>
                
                <div className={`mt-2 px-2 py-1 rounded text-xs text-center ${
                  module.status === 'online' ? 'bg-green-400/20 text-green-400' :
                  module.status === 'degraded' ? 'bg-yellow-400/20 text-yellow-400' :
                  'bg-red-400/20 text-red-400'
                }`}>
                  {module.status.toUpperCase()}
                </div>
              </div>
            )
          })}
        </div>

        {/* Data Flow Stream */}
        <div>
          <h4 className="text-sm font-semibold text-white mb-4 flex items-center">
            <Activity className="h-4 w-4 mr-2 text-indigo-400" />
            Live Data Flows
          </h4>
          
          <div className="max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800 space-y-2">
            {dataFlows.length === 0 ? (
              <div className="text-center py-8">
                <Radio className="h-8 w-8 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">No data flows detected</p>
              </div>
            ) : (
              dataFlows.map((flow) => {
                const DataIcon = getDataTypeIcon(flow.data_type)
                const isActive = activeFlows.has(flow.id)
                
                return (
                  <div 
                    key={flow.id}
                    className={`p-3 bg-gray-800 rounded-lg border border-gray-700 transition-all duration-300 cursor-pointer hover:border-gray-600 ${
                      isActive ? 'animate-pulse border-indigo-500' : ''
                    } ${selectedFlow?.id === flow.id ? 'ring-1 ring-indigo-500' : ''}`}
                    onClick={() => setSelectedFlow(selectedFlow?.id === flow.id ? null : flow)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <DataIcon className="h-4 w-4 text-indigo-400" />
                        <div>
                          <div className="text-sm text-white font-medium">
                            {flow.content}
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            {moduleStats.find(m => m.id === flow.source_module)?.name} → 
                            {moduleStats.find(m => m.id === flow.target_module)?.name}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          flow.status === 'processed' ? 'bg-green-400/20 text-green-400' :
                          flow.status === 'delivered' ? 'bg-blue-400/20 text-blue-400' :
                          flow.status === 'sending' ? 'bg-yellow-400/20 text-yellow-400' :
                          'bg-red-400/20 text-red-400'
                        }`}>
                          {flow.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(flow.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    
                    {/* Expanded Details */}
                    {selectedFlow?.id === flow.id && (
                      <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>
                            <span className="text-gray-400">Data Type:</span>
                            <div className="text-white font-medium capitalize">{flow.data_type.replace('_', ' ')}</div>
                          </div>
                          <div>
                            <span className="text-gray-400">Priority:</span>
                            <div className="text-white font-medium">{flow.metadata.priority || 'N/A'}</div>
                          </div>
                          {flow.metadata.passenger_count && (
                            <div>
                              <span className="text-gray-400">Passengers:</span>
                              <div className="text-white font-medium">{flow.metadata.passenger_count}</div>
                            </div>
                          )}
                          {flow.metadata.cost_impact && (
                            <div>
                              <span className="text-gray-400">Cost Impact:</span>
                              <div className="text-white font-medium">£{flow.metadata.cost_impact.toLocaleString()}</div>
                            </div>
                          )}
                        </div>
                        
                        <div className="mt-2">
                          <span className="text-gray-400 text-xs">Flow Path:</span>
                          <div className="flex items-center space-x-2 mt-1">
                            {flow.path.map((step, index) => (
                              <React.Fragment key={index}>
                                <span className="text-xs bg-gray-700 px-2 py-1 rounded text-white">
                                  {step.replace('_', ' ').toUpperCase()}
                                </span>
                                {index < flow.path.length - 1 && (
                                  <ArrowRight className="h-3 w-3 text-gray-400" />
                                )}
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DataFlowVisualization