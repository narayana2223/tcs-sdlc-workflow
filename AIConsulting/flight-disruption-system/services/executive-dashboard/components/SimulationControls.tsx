'use client';

import React, { useState } from 'react';
import { SimulationScenario } from '@/types';
import { Play, Pause, RotateCcw, Settings, Zap, Cloud, Wrench, Users, AlertTriangle } from 'lucide-react';

interface SimulationControlsProps {
  onTriggerSimulation: (scenarioId: string) => void;
  isSimulationMode: boolean;
}

const simulationScenarios: SimulationScenario[] = [
  {
    id: 'weather_storm',
    name: 'Severe Weather Event',
    description: 'Major storm system affecting multiple airports with widespread delays and cancellations',
    severity: 'severe',
    affectedFlights: 150,
    estimatedDuration: 6,
  },
  {
    id: 'atc_strike',
    name: 'Air Traffic Control Strike',
    description: 'ATC strike causing significant disruptions to flight operations',
    severity: 'severe',
    affectedFlights: 200,
    estimatedDuration: 12,
  },
  {
    id: 'runway_closure',
    name: 'Emergency Runway Closure',
    description: 'Runway closure at major hub due to technical issues',
    severity: 'major',
    affectedFlights: 80,
    estimatedDuration: 4,
  },
  {
    id: 'system_outage',
    name: 'IT System Outage',
    description: 'Check-in and baggage handling system failure',
    severity: 'major',
    affectedFlights: 60,
    estimatedDuration: 3,
  },
  {
    id: 'crew_shortage',
    name: 'Crew Availability Crisis',
    description: 'Sudden crew shortage due to illness affecting multiple routes',
    severity: 'major',
    affectedFlights: 45,
    estimatedDuration: 8,
  },
  {
    id: 'minor_delay',
    name: 'Air Traffic Delays',
    description: 'Minor air traffic control delays during peak hours',
    severity: 'minor',
    affectedFlights: 25,
    estimatedDuration: 2,
  },
];

const scenarioIcons = {
  weather_storm: Cloud,
  atc_strike: Users,
  runway_closure: AlertTriangle,
  system_outage: Settings,
  crew_shortage: Users,
  minor_delay: Zap,
};

const severityColors = {
  minor: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-700',
    badge: 'bg-yellow-100 text-yellow-800',
  },
  major: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    text: 'text-orange-700',
    badge: 'bg-orange-100 text-orange-800',
  },
  severe: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
    badge: 'bg-red-100 text-red-800',
  },
};

export default function SimulationControls({ onTriggerSimulation, isSimulationMode }: SimulationControlsProps) {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleTriggerSimulation = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    setIsRunning(true);
    onTriggerSimulation(scenarioId);
    
    // Auto-stop after scenario duration for demo purposes
    const scenario = simulationScenarios.find(s => s.id === scenarioId);
    if (scenario) {
      setTimeout(() => {
        setIsRunning(false);
        setSelectedScenario(null);
      }, scenario.estimatedDuration * 1000 * 10); // 10 seconds per hour for demo
    }
  };

  const ScenarioCard = ({ scenario }: { scenario: SimulationScenario }) => {
    const Icon = scenarioIcons[scenario.id as keyof typeof scenarioIcons] || Settings;
    const colors = severityColors[scenario.severity];
    const isActive = selectedScenario === scenario.id && isRunning;

    return (
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer ${isActive ? 'ring-2 ring-primary-500' : ''}`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`p-2 ${colors.badge} rounded-lg`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className={`font-semibold ${colors.text}`}>{scenario.name}</h3>
              <span className={`status-badge ${colors.badge} text-xs`}>
                {scenario.severity}
              </span>
            </div>
          </div>
          {isActive && (
            <div className="flex items-center space-x-1 text-primary-600">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-medium">ACTIVE</span>
            </div>
          )}
        </div>

        <p className={`text-sm mb-3 ${colors.text}`}>
          {scenario.description}
        </p>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center">
            <div className={`text-lg font-bold ${colors.text}`}>
              {scenario.affectedFlights}
            </div>
            <div className="text-xs text-slate-600">Affected Flights</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-bold ${colors.text}`}>
              {scenario.estimatedDuration}h
            </div>
            <div className="text-xs text-slate-600">Duration</div>
          </div>
        </div>

        <button
          onClick={() => handleTriggerSimulation(scenario.id)}
          disabled={isRunning}
          className={`w-full px-4 py-2 rounded-lg font-medium text-sm transition-all ${
            isActive
              ? 'bg-primary-500 text-white'
              : isRunning
              ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
              : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
          }`}
        >
          {isActive ? 'Running...' : isRunning ? 'Scenario Active' : 'Trigger Scenario'}
        </button>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 flex items-center space-x-2">
            <Play className="w-6 h-6" />
            <span>Simulation Controls</span>
          </h2>
          <p className="text-sm text-slate-600">Trigger disruption scenarios to test AI agents</p>
        </div>
        
        <div className="flex items-center space-x-2">
          {isSimulationMode && (
            <div className="flex items-center space-x-2 px-3 py-1 bg-primary-100 text-primary-700 rounded-full">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Demo Mode</span>
            </div>
          )}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Control Panel */}
      <div className="flex items-center justify-between mb-6 p-4 bg-slate-50 rounded-lg">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            {isRunning ? (
              <>
                <Pause className="w-5 h-5 text-primary-600" />
                <span className="font-medium text-primary-700">Simulation Active</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700">Ready to Simulate</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setIsRunning(false);
              setSelectedScenario(null);
            }}
            disabled={!isRunning}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
              isRunning
                ? 'bg-danger-100 text-danger-700 hover:bg-danger-200'
                : 'bg-slate-200 text-slate-500 cursor-not-allowed'
            }`}
          >
            Stop Simulation
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Advanced Controls */}
      {showAdvanced && (
        <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-800 mb-3">Advanced Settings</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-600 mb-1">Simulation Speed</label>
              <select className="w-full px-2 py-1 border border-slate-300 rounded text-sm">
                <option>Real-time</option>
                <option>2x Speed</option>
                <option>5x Speed</option>
                <option>10x Speed</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-600 mb-1">Auto-resolve</label>
              <select className="w-full px-2 py-1 border border-slate-300 rounded text-sm">
                <option>Enabled</option>
                <option>Disabled</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Scenario Selection */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">Available Scenarios</h3>
          <div className="flex items-center space-x-2 text-sm">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span className="text-slate-600">Minor</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <span className="text-slate-600">Major</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-slate-600">Severe</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {simulationScenarios.map(scenario => (
            <ScenarioCard key={scenario.id} scenario={scenario} />
          ))}
        </div>
      </div>

      {/* Simulation Status */}
      {selectedScenario && isRunning && (
        <div className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <h4 className="text-sm font-semibold text-primary-800 mb-2">
            Current Simulation: {simulationScenarios.find(s => s.id === selectedScenario)?.name}
          </h4>
          <div className="text-sm text-primary-700">
            Watch the dashboard panels above to see how AI agents respond to this disruption scenario in real-time.
          </div>
          <div className="mt-2 flex items-center space-x-4 text-xs text-primary-600">
            <div>Agent decisions will appear in the activity feed</div>
            <div>•</div>
            <div>Financial impact will be calculated live</div>
            <div>•</div>
            <div>Passenger rebooking will be tracked</div>
          </div>
        </div>
      )}

      {/* Demo Instructions */}
      {!isRunning && (
        <div className="mt-6 p-4 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Demo Instructions</h4>
          <ul className="text-sm text-slate-600 space-y-1">
            <li>• Select a scenario above to trigger a realistic disruption simulation</li>
            <li>• Watch real-time updates across all dashboard panels</li>
            <li>• Observe AI agent decision-making and reasoning</li>
            <li>• Monitor financial impact and passenger satisfaction metrics</li>
            <li>• Compare performance with traditional manual processes</li>
          </ul>
        </div>
      )}
    </div>
  );
}