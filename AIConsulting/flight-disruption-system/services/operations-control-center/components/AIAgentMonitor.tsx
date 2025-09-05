'use client'

import { useState, useEffect } from 'react'
import {
  CpuChipIcon,
  BoltIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowPathIcon,
  PauseIcon,
  PlayIcon
} from '@heroicons/react/24/outline'

interface AIAgent {
  id: string
  name: string
  type: 'prediction' | 'passenger' | 'resource' | 'finance' | 'communication' | 'coordinator'
  status: 'active' | 'idle' | 'processing' | 'error' | 'paused'
  tasksCompleted: number
  successRate: number
  currentTask: string
  lastActivity: string
  performance: number
  costSaved: number
  decisions: number
}

interface AgentActivity {
  id: string
  agentName: string
  action: string
  result: string
  timestamp: string
  confidence: number
  impact: 'low' | 'medium' | 'high'
}

export default function AIAgentMonitor() {
  const [agents, setAgents] = useState<AIAgent[]>([
    {
      id: 'A001',
      name: 'Prediction Agent Alpha',
      type: 'prediction',
      status: 'active',
      tasksCompleted: 1247,
      successRate: 96.4,
      currentTask: 'Weather impact analysis for LHR runway 09L',
      lastActivity: '12 sec ago',
      performance: 94,
      costSaved: 245600,
      decisions: 89
    },
    {
      id: 'A002',
      name: 'Passenger Agent Beta',
      type: 'passenger',
      status: 'processing',
      tasksCompleted: 2156,
      successRate: 98.7,
      currentTask: 'Rebooking 298 passengers from BA123 delay',
      lastActivity: '5 sec ago',
      performance: 98,
      costSaved: 189400,
      decisions: 156
    },
    {
      id: 'A003',
      name: 'Resource Agent Gamma',
      type: 'resource',
      status: 'active',
      tasksCompleted: 876,
      successRate: 92.3,
      currentTask: 'Optimizing crew allocation for route LGW-LAX',
      lastActivity: '8 sec ago',
      performance: 91,
      costSaved: 312800,
      decisions: 67
    },
    {
      id: 'A004',
      name: 'Finance Agent Delta',
      type: 'finance',
      status: 'idle',
      tasksCompleted: 543,
      successRate: 94.8,
      currentTask: 'Monitoring compensation calculations',
      lastActivity: '2 min ago',
      performance: 88,
      costSaved: 456200,
      decisions: 43
    },
    {
      id: 'A005',
      name: 'Communication Agent Epsilon',
      type: 'communication',
      status: 'active',
      tasksCompleted: 3421,
      successRate: 99.1,
      currentTask: 'Sending updates to 412 passengers via SMS/Email',
      lastActivity: '3 sec ago',
      performance: 97,
      costSaved: 89300,
      decisions: 234
    },
    {
      id: 'A006',
      name: 'Coordinator Agent Zeta',
      type: 'coordinator',
      status: 'processing',
      tasksCompleted: 654,
      successRate: 95.2,
      currentTask: 'Orchestrating multi-agent response to VS456 cancellation',
      lastActivity: '1 sec ago',
      performance: 96,
      costSaved: 567400,
      decisions: 78
    }
  ])

  const [recentActivity, setRecentActivity] = useState<AgentActivity[]>([
    {
      id: 'ACT001',
      agentName: 'Coordinator Zeta',
      action: 'Initiated emergency rebooking protocol',
      result: 'Successfully coordinated 5 agents',
      timestamp: '2 sec ago',
      confidence: 98,
      impact: 'high'
    },
    {
      id: 'ACT002',
      agentName: 'Passenger Beta',
      action: 'Alternative flight options identified',
      result: '298 passengers rebooked automatically',
      timestamp: '15 sec ago',
      confidence: 96,
      impact: 'high'
    },
    {
      id: 'ACT003',
      agentName: 'Communication Epsilon',
      action: 'Multi-channel notification sent',
      result: '99.2% delivery success rate',
      timestamp: '23 sec ago',
      confidence: 99,
      impact: 'medium'
    },
    {
      id: 'ACT004',
      agentName: 'Finance Delta',
      action: 'Compensation calculated',
      result: '£125,400 total compensation approved',
      timestamp: '35 sec ago',
      confidence: 94,
      impact: 'high'
    },
    {
      id: 'ACT005',
      agentName: 'Prediction Alpha',
      action: 'Weather disruption predicted',
      result: '3.2 hour advance warning provided',
      timestamp: '1 min ago',
      confidence: 87,
      impact: 'medium'
    }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-400/20'
      case 'processing': return 'text-blue-400 bg-blue-400/20'
      case 'idle': return 'text-gray-400 bg-gray-400/20'
      case 'error': return 'text-red-400 bg-red-400/20'
      case 'paused': return 'text-yellow-400 bg-yellow-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-green-400'
      default: return 'text-gray-400'
    }
  }

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'prediction': return ChartBarIcon
      case 'passenger': return CheckCircleIcon
      case 'resource': return BoltIcon
      case 'finance': return CpuChipIcon
      case 'communication': return ArrowPathIcon
      case 'coordinator': return ExclamationTriangleIcon
      default: return CpuChipIcon
    }
  }

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-2">AI Agent Monitor</h3>
          <p className="text-gray-400 text-sm">Real-time autonomous agent intelligence</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-semibold">6 Active</span>
          </div>
          <button className="btn-secondary text-xs py-1 px-3">
            <ArrowPathIcon className="h-3 w-3 mr-1" />
            Refresh
          </button>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        {agents.map((agent) => {
          const AgentIcon = getAgentIcon(agent.type)
          
          return (
            <div key={agent.id} className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all duration-300">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <AgentIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white">{agent.name}</h4>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                      {agent.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-green-400 text-sm font-semibold">{agent.successRate}%</div>
                  <div className="text-gray-400 text-xs">Success Rate</div>
                </div>
              </div>
              
              <div className="text-gray-300 text-sm mb-3 line-clamp-2">
                <span className="font-medium">Current:</span> {agent.currentTask}
              </div>
              
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="text-center">
                  <div className="text-white font-semibold">{agent.tasksCompleted}</div>
                  <div className="text-gray-400 text-xs">Tasks</div>
                </div>
                <div className="text-center">
                  <div className="text-green-400 font-semibold">£{(agent.costSaved / 1000).toFixed(0)}k</div>
                  <div className="text-gray-400 text-xs">Saved</div>
                </div>
                <div className="text-center">
                  <div className="text-blue-400 font-semibold">{agent.decisions}</div>
                  <div className="text-gray-400 text-xs">Decisions</div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-400 text-xs">{agent.lastActivity}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-12 bg-gray-700 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${
                        agent.performance >= 90 ? 'bg-green-400' :
                        agent.performance >= 70 ? 'bg-yellow-400' : 'bg-red-400'
                      }`}
                      style={{ width: `${agent.performance}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{agent.performance}%</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Activity Feed */}
      <div className="border-t border-white/20 pt-6">
        <h4 className="text-lg font-semibold text-white mb-4">Recent AI Decisions</h4>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="bg-white/5 border border-white/10 rounded-lg p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-blue-400 text-sm font-semibold">{activity.agentName}</span>
                    <span className={`text-xs font-medium ${getImpactColor(activity.impact)}`}>
                      {activity.impact.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-white text-sm mb-1">{activity.action}</p>
                  <p className="text-gray-400 text-xs">{activity.result}</p>
                </div>
                <div className="text-right ml-4">
                  <div className="text-gray-400 text-xs">{activity.timestamp}</div>
                  <div className="text-green-400 text-xs font-semibold">{activity.confidence}% confidence</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Controls */}
      <div className="border-t border-white/20 pt-4 mt-6">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Total Cost Savings: <span className="text-green-400 font-semibold">£1.86M today</span>
          </div>
          <div className="flex space-x-2">
            <button className="btn-secondary text-xs py-1 px-3 flex items-center space-x-1">
              <PauseIcon className="h-3 w-3" />
              <span>Pause All</span>
            </button>
            <button className="btn-primary text-xs py-1 px-3 flex items-center space-x-1">
              <PlayIcon className="h-3 w-3" />
              <span>Resume All</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}