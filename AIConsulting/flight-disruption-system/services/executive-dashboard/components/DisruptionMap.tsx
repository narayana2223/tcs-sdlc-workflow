'use client';

import React, { useEffect, useRef, useState } from 'react';
import { FlightDisruption } from '@/types';
import { MapPin, Plane, AlertTriangle, Clock, Users } from 'lucide-react';

interface DisruptionMapProps {
  disruptions: FlightDisruption[];
}

const ukAirports = {
  LHR: { name: 'London Heathrow', coords: [51.4700, -0.4543] },
  LGW: { name: 'London Gatwick', coords: [51.1537, -0.1821] },
  STN: { name: 'London Stansted', coords: [51.8860, 0.2389] },
  LTN: { name: 'London Luton', coords: [51.8763, -0.3717] },
  MAN: { name: 'Manchester', coords: [53.3537, -2.2750] },
  BHX: { name: 'Birmingham', coords: [52.4539, -1.7381] },
  EDI: { name: 'Edinburgh', coords: [55.9500, -3.3725] },
  GLA: { name: 'Glasgow', coords: [55.8719, -4.4331] },
  NCL: { name: 'Newcastle', coords: [55.0375, -1.6917] },
  BRS: { name: 'Bristol', coords: [51.3827, -2.7191] },
  LBA: { name: 'Leeds Bradford', coords: [53.8659, -1.6606] },
  LPL: { name: 'Liverpool', coords: [53.3336, -2.8497] },
};

export default function DisruptionMap({ disruptions }: DisruptionMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [selectedDisruption, setSelectedDisruption] = useState<FlightDisruption | null>(null);

  const getSeverityColor = (severity: FlightDisruption['severity']) => {
    switch (severity) {
      case 'low': return '#22c55e';
      case 'medium': return '#f59e0b';
      case 'high': return '#ef4444';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: FlightDisruption['status']) => {
    switch (status) {
      case 'delayed': return <Clock className="w-4 h-4" />;
      case 'cancelled': return <AlertTriangle className="w-4 h-4" />;
      case 'diverted': return <Plane className="w-4 h-4" />;
      default: return <MapPin className="w-4 h-4" />;
    }
  };

  return (
    <div className="card h-full">
      <div className="card-header">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Live Disruption Map</h2>
          <p className="text-sm text-slate-600">Real-time flight disruptions across UK</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-success-500"></div>
            <span className="text-xs text-slate-600">Normal</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-warning-500"></div>
            <span className="text-xs text-slate-600">Delayed</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-danger-500"></div>
            <span className="text-xs text-slate-600">Critical</span>
          </div>
        </div>
      </div>

      <div className="relative h-96 bg-slate-100 rounded-lg overflow-hidden">
        {/* UK Map Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-blue-100">
          <svg
            viewBox="0 0 400 600"
            className="w-full h-full"
            style={{ transform: 'scale(1.2) translateY(-10%)' }}
          >
            {/* Simplified UK outline */}
            <path
              d="M100 100 L300 100 L320 150 L310 200 L320 250 L300 300 L280 350 L260 400 L240 450 L220 500 L200 520 L180 500 L160 480 L140 450 L120 400 L100 350 L90 300 L85 250 L90 200 L95 150 Z"
              fill="#e2e8f0"
              stroke="#cbd5e1"
              strokeWidth="2"
            />
          </svg>
        </div>

        {/* Airport markers */}
        {Object.entries(ukAirports).map(([code, airport]) => {
          const airportDisruptions = disruptions.filter(
            d => d.departureAirport === code || d.arrivalAirport === code
          );
          const hasDisruptions = airportDisruptions.length > 0;
          const severity = hasDisruptions 
            ? airportDisruptions.reduce((max, d) => 
                ['low', 'medium', 'high', 'critical'].indexOf(d.severity) > ['low', 'medium', 'high', 'critical'].indexOf(max) ? d.severity : max
              , 'low')
            : 'low';

          return (
            <div
              key={code}
              className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer"
              style={{
                left: `${((airport.coords[1] + 8) / 16) * 100}%`,
                top: `${((60 - airport.coords[0]) / 10) * 100}%`,
              }}
              onMouseEnter={() => setSelectedDisruption(airportDisruptions[0] || null)}
              onMouseLeave={() => setSelectedDisruption(null)}
            >
              <div className={`relative ${hasDisruptions ? 'animate-pulse' : ''}`}>
                <div
                  className="w-4 h-4 rounded-full border-2 border-white shadow-lg"
                  style={{ backgroundColor: getSeverityColor(severity) }}
                />
                {hasDisruptions && (
                  <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                    {airportDisruptions.length}
                  </div>
                )}
              </div>
              <div className="absolute top-6 left-1/2 transform -translate-x-1/2 bg-slate-800 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 hover:opacity-100 transition-opacity z-10">
                {airport.name} ({code})
                {hasDisruptions && (
                  <div className="text-xs mt-1">
                    {airportDisruptions.length} disruption{airportDisruptions.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Flight paths for disrupted flights */}
        {disruptions.slice(0, 10).map((disruption) => {
          const depAirport = ukAirports[disruption.departureAirport as keyof typeof ukAirports];
          const arrAirport = ukAirports[disruption.arrivalAirport as keyof typeof ukAirports];
          
          if (!depAirport || !arrAirport) return null;

          const x1 = ((depAirport.coords[1] + 8) / 16) * 100;
          const y1 = ((60 - depAirport.coords[0]) / 10) * 100;
          const x2 = ((arrAirport.coords[1] + 8) / 16) * 100;
          const y2 = ((60 - arrAirport.coords[0]) / 10) * 100;

          return (
            <svg
              key={disruption.id}
              className="absolute inset-0 w-full h-full pointer-events-none"
            >
              <defs>
                <marker
                  id={`arrow-${disruption.id}`}
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 10 3.5, 0 7"
                    fill={getSeverityColor(disruption.severity)}
                  />
                </marker>
              </defs>
              <line
                x1={`${x1}%`}
                y1={`${y1}%`}
                x2={`${x2}%`}
                y2={`${y2}%`}
                stroke={getSeverityColor(disruption.severity)}
                strokeWidth="2"
                strokeDasharray={disruption.status === 'cancelled' ? '5,5' : '0'}
                markerEnd={`url(#arrow-${disruption.id})`}
                opacity="0.7"
              />
            </svg>
          );
        })}
      </div>

      {/* Disruption Details Panel */}
      {selectedDisruption && (
        <div className="mt-4 p-4 bg-slate-50 rounded-lg border">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              {getStatusIcon(selectedDisruption.status)}
              <span className="font-medium text-slate-800">
                {selectedDisruption.flightNumber}
              </span>
              <span className={`status-badge status-${selectedDisruption.severity === 'low' ? 'success' : selectedDisruption.severity === 'medium' ? 'warning' : 'danger'}`}>
                {selectedDisruption.severity}
              </span>
            </div>
            <div className="flex items-center space-x-1 text-slate-600">
              <Users className="w-4 h-4" />
              <span className="text-sm">{selectedDisruption.affectedPassengers}</span>
            </div>
          </div>
          <div className="text-sm text-slate-600">
            <p className="mb-1">
              <strong>Route:</strong> {selectedDisruption.departureAirport} → {selectedDisruption.arrivalAirport}
            </p>
            <p className="mb-1">
              <strong>Status:</strong> {selectedDisruption.status.charAt(0).toUpperCase() + selectedDisruption.status.slice(1)}
            </p>
            <p>
              <strong>Reason:</strong> {selectedDisruption.reason}
            </p>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="mt-4 grid grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800">
            {disruptions.filter(d => d.status === 'delayed').length}
          </div>
          <div className="text-xs text-slate-600">Delayed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800">
            {disruptions.filter(d => d.status === 'cancelled').length}
          </div>
          <div className="text-xs text-slate-600">Cancelled</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800">
            {disruptions.filter(d => d.status === 'diverted').length}
          </div>
          <div className="text-xs text-slate-600">Diverted</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-800">
            {disruptions.reduce((sum, d) => sum + d.affectedPassengers, 0)}
          </div>
          <div className="text-xs text-slate-600">Passengers</div>
        </div>
      </div>
    </div>
  );
}