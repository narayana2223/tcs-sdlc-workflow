'use client'

import { useState, useEffect } from 'react'
import { 
  PaperAirplaneIcon, 
  ExclamationTriangleIcon, 
  UsersIcon, 
  CpuChipIcon,
  ClockIcon,
  CurrencyPoundIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import FlightOperationsGrid from '@/components/FlightOperationsGrid'
import DisruptionManagementPanel from '@/components/DisruptionManagementPanel'
import AIAgentMonitor from '@/components/AIAgentMonitor'
import ResourceAllocationPanel from '@/components/ResourceAllocationPanel'

export default function OperationsControlCenter() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [systemStatus, setSystemStatus] = useState('operational')
  const [activeDisruptions, setActiveDisruptions] = useState(12)
  const [passengerImpact, setPassengerImpact] = useState(3456)
  const [aiAgentsActive, setAiAgentsActive] = useState(6)
  const [costSavings, setCostSavings] = useState(2450000)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const metrics = [
    {
      name: 'Active Flights',
      value: '847',
      change: '+12',
      changeType: 'increase',
      icon: PaperAirplaneIcon,
      color: 'blue'
    },
    {
      name: 'Active Disruptions',
      value: activeDisruptions.toString(),
      change: '-3',
      changeType: 'decrease',
      icon: ExclamationTriangleIcon,
      color: 'red'
    },
    {
      name: 'Passengers Impacted',
      value: passengerImpact.toLocaleString(),
      change: '-156',
      changeType: 'decrease',
      icon: UsersIcon,
      color: 'yellow'
    },
    {
      name: 'AI Agents Active',
      value: aiAgentsActive.toString(),
      change: '+1',
      changeType: 'increase',
      icon: CpuChipIcon,
      color: 'green'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-400'
      case 'degraded': return 'text-yellow-400'
      case 'critical': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-[1920px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  Operations Control Center
                </h1>
                <p className="text-gray-300">
                  Real-time flight disruption management and AI agent coordination
                </p>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <p className="text-sm text-gray-400">System Time</p>
                  <p className="text-xl font-mono text-white">
                    {currentTime.toLocaleTimeString('en-GB')}
                  </p>
                  <p className="text-sm text-gray-400">
                    {currentTime.toLocaleDateString('en-GB')}
                  </p>
                </div>
                
                <div className="text-right">
                  <p className="text-sm text-gray-400">System Status</p>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${systemStatus === 'operational' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                    <span className={`text-lg font-semibold ${getStatusColor(systemStatus)} capitalize`}>
                      {systemStatus}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric) => {
            const Icon = metric.icon
            return (
              <div key={metric.name} className="metric-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm font-medium">{metric.name}</p>
                    <p className="text-2xl font-bold text-white mt-1">{metric.value}</p>
                    <div className="flex items-center mt-2">
                      <span className={`text-sm font-medium ${
                        metric.changeType === 'increase' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {metric.change}
                      </span>
                      <span className="text-gray-400 text-sm ml-1">from last hour</span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-full bg-${metric.color}-500/20`}>
                    <Icon className={`h-6 w-6 text-${metric.color}-400`} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Real-time Cost Savings Counter */}
        <div className="mb-8">
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  AI-Generated Cost Savings (Today)
                </h3>
                <div className="flex items-center space-x-4">
                  <div className="text-4xl font-bold gradient-text">
                    £{costSavings.toLocaleString()}
                  </div>
                  <div className="text-green-400 text-lg font-semibold">
                    +£12,500 (last hour)
                  </div>
                </div>
                <p className="text-gray-400 text-sm mt-2">
                  Autonomous optimization vs traditional manual processes
                </p>
              </div>
              
              <div className="text-right">
                <div className="flex items-center space-x-2 mb-4">
                  <CurrencyPoundIcon className="h-5 w-5 text-green-400" />
                  <span className="text-green-400 font-semibold">ROI: 342%</span>
                </div>
                <div className="text-gray-400 text-sm">
                  <p>Average per disruption: £25,600</p>
                  <p>Traditional cost: £45,200</p>
                </div>
              </div>
            </div>
            
            {/* Progress bar showing daily target */}
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-400 mb-2">
                <span>Daily Target Progress</span>
                <span>£{costSavings.toLocaleString()} / £3,000,000 (82%)</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-1000"
                  style={{ width: '82%' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
          {/* Flight Operations */}
          <div className="xl:col-span-2">
            <FlightOperationsGrid />
          </div>
          
          {/* AI Agent Monitor */}
          <div>
            <AIAgentMonitor />
          </div>
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          {/* Disruption Management */}
          <div>
            <DisruptionManagementPanel />
          </div>
          
          {/* Resource Allocation */}
          <div>
            <ResourceAllocationPanel />
          </div>
        </div>

        {/* Emergency Controls */}
        <div className="mt-8">
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  Emergency Response Controls
                </h3>
                <p className="text-gray-400 text-sm">
                  Manual override controls for critical situations
                </p>
              </div>
              
              <div className="flex space-x-4">
                <button className="btn-secondary flex items-center space-x-2">
                  <PlayIcon className="h-4 w-4" />
                  <span>Start Emergency Protocol</span>
                </button>
                <button className="btn-secondary flex items-center space-x-2">
                  <PauseIcon className="h-4 w-4" />
                  <span>Pause AI Agents</span>
                </button>
                <button className="btn-primary flex items-center space-x-2">
                  <ArrowPathIcon className="h-4 w-4" />
                  <span>System Reset</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}