'use client'

import { useState, useEffect } from 'react'
import {
  ExclamationTriangleIcon,
  ClockIcon,
  UsersIcon,
  CurrencyPoundIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowRightIcon,
  SignalIcon
} from '@heroicons/react/24/outline'

interface Disruption {
  id: string
  flight: string
  route: string
  type: 'delay' | 'cancellation' | 'diversion' | 'maintenance'
  severity: 'low' | 'medium' | 'high' | 'critical'
  passengers: number
  estimatedCost: number
  status: 'detected' | 'processing' | 'resolved' | 'escalated'
  aiAgentAssigned: string
  timeline: string
  impactScore: number
}

export default function DisruptionManagementPanel() {
  const [disruptions, setDisruptions] = useState<Disruption[]>([
    {
      id: 'D001',
      flight: 'BA123',
      route: 'LHR → JFK',
      type: 'delay',
      severity: 'high',
      passengers: 298,
      estimatedCost: 45600,
      status: 'processing',
      aiAgentAssigned: 'Agent Alpha',
      timeline: '2h 30m ago',
      impactScore: 87
    },
    {
      id: 'D002', 
      flight: 'VS456',
      route: 'LGW → LAX',
      type: 'cancellation',
      severity: 'critical',
      passengers: 412,
      estimatedCost: 125400,
      status: 'processing',
      aiAgentAssigned: 'Agent Beta',
      timeline: '45m ago',
      impactScore: 95
    },
    {
      id: 'D003',
      flight: 'EZY789',
      route: 'STN → BCN',
      type: 'diversion',
      severity: 'medium',
      passengers: 186,
      estimatedCost: 18200,
      status: 'resolved',
      aiAgentAssigned: 'Agent Gamma',
      timeline: '3h 15m ago',
      impactScore: 64
    }
  ])

  const [activeFilters, setActiveFilters] = useState({
    status: 'all',
    severity: 'all',
    type: 'all'
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-green-400 bg-green-400/20'
      case 'medium': return 'text-yellow-400 bg-yellow-400/20'  
      case 'high': return 'text-orange-400 bg-orange-400/20'
      case 'critical': return 'text-red-400 bg-red-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'detected': return 'text-blue-400 bg-blue-400/20'
      case 'processing': return 'text-yellow-400 bg-yellow-400/20'
      case 'resolved': return 'text-green-400 bg-green-400/20'
      case 'escalated': return 'text-red-400 bg-red-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'delay': return ClockIcon
      case 'cancellation': return XCircleIcon
      case 'diversion': return ArrowRightIcon
      case 'maintenance': return SignalIcon
      default: return ExclamationTriangleIcon
    }
  }

  const filteredDisruptions = disruptions.filter(disruption => {
    return (activeFilters.status === 'all' || disruption.status === activeFilters.status) &&
           (activeFilters.severity === 'all' || disruption.severity === activeFilters.severity) &&
           (activeFilters.type === 'all' || disruption.type === activeFilters.type)
  })

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-2">Active Disruptions</h3>
          <p className="text-gray-400 text-sm">AI-powered autonomous disruption resolution</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm font-semibold">Real-time Monitoring</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex space-x-4 mb-6">
        <select 
          className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm backdrop-blur-sm"
          value={activeFilters.status}
          onChange={(e) => setActiveFilters({...activeFilters, status: e.target.value})}
        >
          <option value="all">All Status</option>
          <option value="detected">Detected</option>
          <option value="processing">Processing</option>
          <option value="resolved">Resolved</option>
          <option value="escalated">Escalated</option>
        </select>
        
        <select 
          className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm backdrop-blur-sm"
          value={activeFilters.severity}
          onChange={(e) => setActiveFilters({...activeFilters, severity: e.target.value})}
        >
          <option value="all">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {/* Disruption List */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {filteredDisruptions.map((disruption) => {
          const TypeIcon = getTypeIcon(disruption.type)
          
          return (
            <div key={disruption.id} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-300">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <TypeIcon className="h-5 w-5 text-white" />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-semibold text-white">{disruption.flight}</h4>
                      <span className="text-gray-400 text-sm">{disruption.route}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(disruption.severity)}`}>
                        {disruption.severity.toUpperCase()}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(disruption.status)}`}>
                        {disruption.status.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div className="flex items-center space-x-2">
                        <UsersIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-300 text-sm">{disruption.passengers} passengers</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <CurrencyPoundIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-300 text-sm">£{disruption.estimatedCost.toLocaleString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-gray-400 text-sm">Assigned: {disruption.aiAgentAssigned}</span>
                      <span className="text-gray-400 text-sm">{disruption.timeline}</span>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm text-gray-400 mb-1">Impact Score</div>
                  <div className="text-lg font-bold text-white">{disruption.impactScore}</div>
                  <div className="w-16 bg-gray-700 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        disruption.impactScore >= 80 ? 'bg-red-400' :
                        disruption.impactScore >= 60 ? 'bg-yellow-400' : 'bg-green-400'
                      }`}
                      style={{ width: `${disruption.impactScore}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Statistics */}
      <div className="mt-6 pt-6 border-t border-white/20">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{disruptions.length}</div>
            <div className="text-gray-400 text-sm">Total Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {disruptions.filter(d => d.status === 'resolved').length}
            </div>
            <div className="text-gray-400 text-sm">Resolved Today</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">
              {Math.round(disruptions.reduce((acc, d) => acc + d.impactScore, 0) / disruptions.length)}
            </div>
            <div className="text-gray-400 text-sm">Avg Impact</div>
          </div>
        </div>
      </div>
    </div>
  )
}