'use client'

import { useState } from 'react'
import { 
  PaperAirplaneIcon,
  MapPinIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

const mockFlights = [
  {
    id: 'BA123',
    route: 'LHR → JFK',
    departure: '08:30',
    arrival: '13:45',
    status: 'on-time',
    aircraft: 'B787-9',
    passengers: 298,
    gate: 'A12',
    delay: 0
  },
  {
    id: 'VS456',
    route: 'MAN → LAX',
    departure: '11:15',
    arrival: '15:30',
    status: 'delayed',
    aircraft: 'A350-1000',
    passengers: 335,
    gate: 'B8',
    delay: 45
  },
  {
    id: 'EZY789',
    route: 'LGW → BCN',
    departure: '06:45',
    arrival: '10:15',
    status: 'cancelled',
    aircraft: 'A320',
    passengers: 186,
    gate: '-',
    delay: 0
  },
  {
    id: 'FR234',
    route: 'STN → DUB',
    departure: '14:20',
    arrival: '15:45',
    status: 'boarding',
    aircraft: 'B737-800',
    passengers: 189,
    gate: 'C15',
    delay: 0
  },
  {
    id: 'BA567',
    route: 'LHR → SYD',
    departure: '21:30',
    arrival: '18:15+1',
    status: 'on-time',
    aircraft: 'A380',
    passengers: 469,
    gate: 'T5-A1',
    delay: 0
  },
  {
    id: 'VS890',
    route: 'LHR → HKG',
    departure: '23:45',
    arrival: '18:30+1',
    status: 'delayed',
    aircraft: 'B787-9',
    passengers: 274,
    gate: 'T3-B12',
    delay: 90
  }
]

export default function FlightOperationsGrid() {
  const [filter, setFilter] = useState('all')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-time': return 'text-green-400 bg-green-400/20'
      case 'delayed': return 'text-yellow-400 bg-yellow-400/20'
      case 'cancelled': return 'text-red-400 bg-red-400/20'
      case 'boarding': return 'text-blue-400 bg-blue-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'on-time': return <CheckCircleIcon className="h-4 w-4" />
      case 'delayed': return <ClockIcon className="h-4 w-4" />
      case 'cancelled': return <XMarkIcon className="h-4 w-4" />
      case 'boarding': return <PaperAirplaneIcon className="h-4 w-4" />
      default: return <ClockIcon className="h-4 w-4" />
    }
  }

  const filteredFlights = filter === 'all' 
    ? mockFlights 
    : mockFlights.filter(flight => flight.status === filter)

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white">Flight Operations</h3>
        
        {/* Filter buttons */}
        <div className="flex space-x-2">
          {['all', 'on-time', 'delayed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
                filter === status
                  ? 'bg-blue-500 text-white'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1).replace('-', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {filteredFlights.map((flight) => (
          <div key={flight.id} className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="font-bold text-white text-lg">{flight.id}</div>
                <div className="flex items-center text-gray-300">
                  <MapPinIcon className="h-4 w-4 mr-1" />
                  <span>{flight.route}</span>
                </div>
                <div className={`status-indicator ${getStatusColor(flight.status)} flex items-center space-x-1`}>
                  {getStatusIcon(flight.status)}
                  <span className="capitalize">{flight.status.replace('-', ' ')}</span>
                </div>
              </div>
              
              {flight.delay > 0 && (
                <div className="flex items-center text-yellow-400 text-sm">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                  <span>+{flight.delay}min</span>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-300">
              <div>
                <p className="text-gray-400">Departure</p>
                <p className="font-semibold">{flight.departure}</p>
              </div>
              <div>
                <p className="text-gray-400">Arrival</p>
                <p className="font-semibold">{flight.arrival}</p>
              </div>
              <div>
                <p className="text-gray-400">Aircraft</p>
                <p className="font-semibold">{flight.aircraft}</p>
              </div>
              <div>
                <p className="text-gray-400">Gate</p>
                <p className="font-semibold">{flight.gate}</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
              <div className="text-sm text-gray-300">
                <span className="font-medium">{flight.passengers}</span> passengers
              </div>
              
              {flight.status === 'delayed' || flight.status === 'cancelled' ? (
                <button className="btn-primary text-xs py-1 px-3">
                  Manage Disruption
                </button>
              ) : (
                <div className="flex space-x-2">
                  <button className="btn-secondary text-xs py-1 px-3">
                    View Details
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}