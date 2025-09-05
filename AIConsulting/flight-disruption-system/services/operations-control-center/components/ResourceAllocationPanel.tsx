'use client'

import { useState, useEffect } from 'react'
import {
  UserGroupIcon,
  TruckIcon,
  BuildingStorefrontIcon,
  CogIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CurrencyPoundIcon,
  MapPinIcon
} from '@heroicons/react/24/outline'

interface Resource {
  id: string
  type: 'crew' | 'aircraft' | 'gate' | 'equipment' | 'hotel' | 'transport'
  name: string
  status: 'available' | 'allocated' | 'maintenance' | 'unavailable'
  location: string
  capacity: number
  utilized: number
  cost: number
  nextAvailable: string
  assignedTo?: string
}

interface AllocationRequest {
  id: string
  type: 'urgent' | 'scheduled' | 'maintenance'
  resource: string
  flight: string
  quantity: number
  duration: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'approved' | 'rejected' | 'fulfilled'
  estimatedCost: number
  requestedBy: string
  timestamp: string
}

export default function ResourceAllocationPanel() {
  const [resources, setResources] = useState<Resource[]>([
    {
      id: 'R001',
      type: 'crew',
      name: 'Cabin Crew Alpha',
      status: 'allocated',
      location: 'LHR Terminal 5',
      capacity: 6,
      utilized: 6,
      cost: 1200,
      nextAvailable: '14:30',
      assignedTo: 'BA123'
    },
    {
      id: 'R002',
      type: 'aircraft',
      name: 'Airbus A320 G-VTII',
      status: 'available',
      location: 'LHR Gate 12',
      capacity: 186,
      utilized: 0,
      cost: 25000,
      nextAvailable: 'Now'
    },
    {
      id: 'R003',
      type: 'gate',
      name: 'Terminal 5 Gate A15',
      status: 'allocated',
      location: 'LHR T5',
      capacity: 400,
      utilized: 298,
      cost: 800,
      nextAvailable: '16:45',
      assignedTo: 'VS456'
    },
    {
      id: 'R004',
      type: 'hotel',
      name: 'Premier Inn Heathrow',
      status: 'available',
      location: 'LHR Area',
      capacity: 150,
      utilized: 89,
      cost: 12500,
      nextAvailable: 'Now'
    },
    {
      id: 'R005',
      type: 'transport',
      name: 'Coach Fleet Alpha',
      status: 'allocated',
      location: 'LHR Pickup Point',
      capacity: 54,
      utilized: 54,
      cost: 850,
      nextAvailable: '15:20',
      assignedTo: 'BA123 Passengers'
    },
    {
      id: 'R006',
      type: 'equipment',
      name: 'Ground Support Unit 4',
      status: 'maintenance',
      location: 'LHR Maintenance Bay',
      capacity: 1,
      utilized: 0,
      cost: 200,
      nextAvailable: '18:00'
    }
  ])

  const [allocationRequests, setAllocationRequests] = useState<AllocationRequest[]>([
    {
      id: 'AR001',
      type: 'urgent',
      resource: 'Hotel Accommodation',
      flight: 'VS456',
      quantity: 412,
      duration: '1 night',
      priority: 'critical',
      status: 'pending',
      estimatedCost: 41200,
      requestedBy: 'Agent Beta',
      timestamp: '2 min ago'
    },
    {
      id: 'AR002',
      type: 'scheduled',
      resource: 'Cabin Crew',
      flight: 'BA789',
      quantity: 8,
      duration: '4 hours',
      priority: 'high',
      status: 'approved',
      estimatedCost: 1600,
      requestedBy: 'Agent Gamma',
      timestamp: '5 min ago'
    },
    {
      id: 'AR003',
      type: 'urgent',
      resource: 'Ground Transport',
      flight: 'EZY123',
      quantity: 3,
      duration: '2 hours',
      priority: 'medium',
      status: 'fulfilled',
      estimatedCost: 450,
      requestedBy: 'Agent Delta',
      timestamp: '8 min ago'
    }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-green-400 bg-green-400/20'
      case 'allocated': return 'text-blue-400 bg-blue-400/20'
      case 'maintenance': return 'text-yellow-400 bg-yellow-400/20'
      case 'unavailable': return 'text-red-400 bg-red-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-400 bg-red-400/20'
      case 'high': return 'text-orange-400 bg-orange-400/20'
      case 'medium': return 'text-yellow-400 bg-yellow-400/20'
      case 'low': return 'text-green-400 bg-green-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getRequestStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400 bg-yellow-400/20'
      case 'approved': return 'text-blue-400 bg-blue-400/20'
      case 'rejected': return 'text-red-400 bg-red-400/20'
      case 'fulfilled': return 'text-green-400 bg-green-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'crew': return UserGroupIcon
      case 'aircraft': return CogIcon
      case 'gate': return BuildingStorefrontIcon
      case 'equipment': return CogIcon
      case 'hotel': return BuildingStorefrontIcon
      case 'transport': return TruckIcon
      default: return ChartBarIcon
    }
  }

  const utilizationPercentage = (resource: Resource) => {
    return resource.capacity > 0 ? (resource.utilized / resource.capacity) * 100 : 0
  }

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-2">Resource Allocation</h3>
          <p className="text-gray-400 text-sm">Real-time resource optimization and allocation</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-green-400 text-sm font-semibold">£89.3k saved</div>
            <div className="text-gray-400 text-xs">vs manual allocation</div>
          </div>
          <button className="btn-secondary text-xs py-1 px-3">Auto-Optimize</button>
        </div>
      </div>

      {/* Resource Overview */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {resources.map((resource) => {
          const ResourceIcon = getResourceIcon(resource.type)
          const utilization = utilizationPercentage(resource)
          
          return (
            <div key={resource.id} className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all duration-300">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <ResourceIcon className="h-4 w-4 text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-white truncate">{resource.name}</h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(resource.status)}`}>
                        {resource.status.toUpperCase()}
                      </span>
                      <span className="text-gray-400 text-xs capitalize">{resource.type}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white text-sm font-semibold">£{resource.cost.toLocaleString()}</div>
                  <div className="text-gray-400 text-xs">Daily Cost</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Location:</span>
                  <span className="text-gray-300">{resource.location}</span>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Utilization:</span>
                  <span className="text-white">{resource.utilized}/{resource.capacity}</span>
                </div>
                
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      utilization >= 90 ? 'bg-red-400' :
                      utilization >= 70 ? 'bg-yellow-400' : 'bg-green-400'
                    }`}
                    style={{ width: `${utilization}%` }}
                  />
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Next Available:</span>
                  <span className="text-gray-300">{resource.nextAvailable}</span>
                </div>
                
                {resource.assignedTo && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Assigned:</span>
                    <span className="text-blue-400">{resource.assignedTo}</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Allocation Requests */}
      <div className="border-t border-white/20 pt-6">
        <h4 className="text-lg font-semibold text-white mb-4">Recent Allocation Requests</h4>
        <div className="space-y-3">
          {allocationRequests.map((request) => (
            <div key={request.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-white font-semibold">{request.resource}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                      {request.priority.toUpperCase()}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRequestStatusColor(request.status)}`}>
                      {request.status.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Flight:</span>
                        <span className="text-gray-300">{request.flight}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Quantity:</span>
                        <span className="text-gray-300">{request.quantity}</span>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Duration:</span>
                        <span className="text-gray-300">{request.duration}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Cost:</span>
                        <span className="text-gray-300">£{request.estimatedCost.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                    <span>Requested by {request.requestedBy}</span>
                    <span>{request.timestamp}</span>
                  </div>
                </div>
                
                <div className="ml-4 flex flex-col space-y-2">
                  {request.status === 'pending' && (
                    <>
                      <button className="btn-primary text-xs py-1 px-3">Approve</button>
                      <button className="btn-secondary text-xs py-1 px-3">Reject</button>
                    </>
                  )}
                  {request.status === 'approved' && (
                    <button className="btn-secondary text-xs py-1 px-3">Fulfill</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Summary */}
      <div className="border-t border-white/20 pt-6 mt-6">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{resources.filter(r => r.status === 'available').length}</div>
            <div className="text-gray-400 text-sm">Available</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{resources.filter(r => r.status === 'allocated').length}</div>
            <div className="text-gray-400 text-sm">Allocated</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{allocationRequests.filter(r => r.status === 'pending').length}</div>
            <div className="text-gray-400 text-sm">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              £{resources.reduce((sum, r) => sum + r.cost, 0).toLocaleString()}
            </div>
            <div className="text-gray-400 text-sm">Daily Total</div>
          </div>
        </div>
      </div>
    </div>
  )
}