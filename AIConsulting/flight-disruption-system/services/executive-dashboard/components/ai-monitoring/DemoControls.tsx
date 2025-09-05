'use client';

import React, { useState } from 'react';
import { 
  PlayCircle, 
  PauseCircle, 
  SkipForward, 
  RefreshCw, 
  Settings, 
  Zap,
  CloudRain,
  Wrench,
  Users,
  Plane,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target
} from 'lucide-react';

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  duration: number;
  complexity: 'simple' | 'moderate' | 'complex';
  triggers: string[];
  expectedOutcomes: string[];
  color: string;
}

const demoScenarios: DemoScenario[] = [
  {
    id: 'weather-disruption',
    name: 'Severe Weather Event',
    description: 'Storm system affecting multiple airports with cascading delays',
    icon: CloudRain,
    duration: 300,
    complexity: 'complex',
    triggers: [
      'Weather alert activation',
      'Multiple flight delays predicted',
      'Passenger rebooking cascade',
      'Cost optimization triggered'
    ],
    expectedOutcomes: [
      'Proactive passenger notifications',
      'Optimized rebooking recommendations',
      'Cost-effective accommodation arrangements',
      'EU261 compliance handling'
    ],
    color: 'blue'
  },
  {
    id: 'aircraft-maintenance',
    name: 'Aircraft Technical Issue',
    description: 'Unscheduled maintenance requiring fleet adjustment',
    icon: Wrench,
    duration: 180,
    complexity: 'moderate',
    triggers: [
      'Maintenance alert detection',
      'Flight cancellation initiated',
      'Alternative aircraft search',
      'Passenger impact assessment'
    ],
    expectedOutcomes: [
      'Rapid passenger rebooking',
      'Alternative flight options',
      'Compensation calculations',
      'Maintenance crew coordination'
    ],
    color: 'orange'
  },
  {
    id: 'crew-shortage',
    name: 'Crew Availability Crisis',
    description: 'Multiple crew members unavailable due to illness',
    icon: Users,
    duration: 240,
    complexity: 'complex',
    triggers: [
      'Crew availability check',
      'Standby crew activation',
      'Flight schedule optimization',
      'Passenger communication'
    ],
    expectedOutcomes: [
      'Optimized crew scheduling',
      'Minimal flight disruptions',
      'Passenger satisfaction maintained',
      'Cost impact minimized'
    ],
    color: 'purple'
  },
  {
    id: 'airport-closure',
    name: 'Airport Temporary Closure',
    description: 'Security incident causing temporary airport shutdown',
    icon: AlertTriangle,
    duration: 420,
    complexity: 'complex',
    triggers: [
      'Security alert received',
      'All flights suspended',
      'Passenger safety protocols',
      'Alternative airport routing'
    ],
    expectedOutcomes: [
      'Coordinated passenger evacuation',
      'Alternative routing activated',
      'Real-time passenger updates',
      'Emergency accommodation'
    ],
    color: 'red'
  },
  {
    id: 'high-demand',
    name: 'Peak Travel Demand',
    description: 'Holiday rush with high passenger volume and limited capacity',
    icon: Plane,
    duration: 360,
    complexity: 'moderate',
    triggers: [
      'Capacity demand analysis',
      'Overbooking management',
      'Priority passenger handling',
      'Revenue optimization'
    ],
    expectedOutcomes: [
      'Optimized seat allocation',
      'VIP passenger prioritization',
      'Revenue maximization',
      'Customer satisfaction balance'
    ],
    color: 'green'
  }
];

export default function DemoControls() {
  const [isRunning, setIsRunning] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [scenarioSpeed, setScenarioSpeed] = useState<'normal' | 'fast' | 'slow'>('normal');
  const [autoProgress, setAutoProgress] = useState(true);
  const [scenarioProgress, setScenarioProgress] = useState(0);

  const getColorClass = (color: string, variant: 'bg' | 'text' | 'border' = 'bg') => {
    const colorMap = {
      purple: { bg: 'bg-purple-500', text: 'text-purple-600', border: 'border-purple-200' },
      blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-200' },
      green: { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-200' },
      orange: { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200' },
      red: { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200' },
      yellow: { bg: 'bg-yellow-500', text: 'text-yellow-600', border: 'border-yellow-200' },
      slate: { bg: 'bg-slate-500', text: 'text-slate-600', border: 'border-slate-200' }
    };
    return colorMap[color as keyof typeof colorMap]?.[variant] || colorMap.slate[variant];
  };

  const handleStartScenario = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    setIsRunning(true);
    setCurrentStep(0);
    setScenarioProgress(0);
    
    // Simulate scenario progress
    const interval = setInterval(() => {
      setScenarioProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + (scenarioSpeed === 'fast' ? 5 : scenarioSpeed === 'slow' ? 1 : 2);
      });
    }, 1000);
  };

  const handlePauseResume = () => {
    setIsRunning(!isRunning);
  };

  const handleReset = () => {
    setIsRunning(false);
    setSelectedScenario(null);
    setCurrentStep(0);
    setScenarioProgress(0);
  };

  const handleNextStep = () => {
    const scenario = demoScenarios.find(s => s.id === selectedScenario);
    if (scenario && currentStep < scenario.triggers.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const getComplexityColor = (complexity: string) => {
    const colors = {
      simple: 'green',
      moderate: 'yellow',
      complex: 'red'
    };
    return colors[complexity as keyof typeof colors] || 'slate';
  };

  const renderScenarioCards = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {demoScenarios.map((scenario) => {
          const Icon = scenario.icon;
          const isSelected = selectedScenario === scenario.id;
          const complexityColor = getComplexityColor(scenario.complexity);
          
          return (
            <div
              key={scenario.id}
              onClick={() => !isRunning && setSelectedScenario(scenario.id)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                isSelected 
                  ? `${getColorClass(scenario.color, 'border')} bg-opacity-10 ${getColorClass(scenario.color)}` 
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              } ${isRunning && !isSelected ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-start space-x-3 mb-3">
                <div className={`p-2 ${getColorClass(scenario.color)} rounded-lg flex-shrink-0`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-800 text-sm mb-1">{scenario.name}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{scenario.description}</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span className="text-slate-600">{Math.floor(scenario.duration / 60)}m</span>
                </div>
                <div className={`px-2 py-1 rounded-full ${getColorClass(complexityColor)} bg-opacity-20`}>
                  <span className={`text-xs font-medium ${getColorClass(complexityColor, 'text')} capitalize`}>
                    {scenario.complexity}
                  </span>
                </div>
              </div>

              {isSelected && !isRunning && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartScenario(scenario.id);
                  }}
                  className={`w-full mt-3 px-3 py-2 ${getColorClass(scenario.color)} text-white rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center space-x-2`}
                >
                  <PlayCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Start Scenario</span>
                </button>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderActiveScenario = () => {
    if (!selectedScenario) return null;

    const scenario = demoScenarios.find(s => s.id === selectedScenario);
    if (!scenario) return null;

    const Icon = scenario.icon;

    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-3 ${getColorClass(scenario.color)} rounded-lg`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800">{scenario.name}</h3>
              <p className="text-sm text-slate-600">Active Demo Scenario</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {isRunning ? (
              <button
                onClick={handlePauseResume}
                className="p-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
              >
                <PauseCircle className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={handlePauseResume}
                className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                <PlayCircle className="w-5 h-5" />
              </button>
            )}
            
            <button
              onClick={handleNextStep}
              className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <SkipForward className="w-5 h-5" />
            </button>
            
            <button
              onClick={handleReset}
              className="p-2 bg-slate-500 text-white rounded-lg hover:bg-slate-600 transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-700">Scenario Progress</span>
            <span className="text-sm text-slate-600">{scenarioProgress.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-1000 ${getColorClass(scenario.color)}`}
              style={{ width: `${scenarioProgress}%` }}
            ></div>
          </div>
        </div>

        {/* Current Triggers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-slate-800 mb-3 flex items-center space-x-2">
              <Target className="w-4 h-4" />
              <span>Active Triggers</span>
            </h4>
            <div className="space-y-2">
              {scenario.triggers.map((trigger, index) => {
                const isActive = index <= currentStep;
                const isCompleted = index < currentStep || scenarioProgress >= ((index + 1) / scenario.triggers.length) * 100;
                
                return (
                  <div
                    key={index}
                    className={`flex items-center space-x-3 p-3 rounded-lg border-2 ${
                      isCompleted 
                        ? 'border-green-200 bg-green-50' 
                        : isActive 
                        ? `${getColorClass(scenario.color, 'border')} bg-opacity-10 ${getColorClass(scenario.color)}`
                        : 'border-slate-200 bg-slate-50'
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {isCompleted ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : isActive ? (
                        <div className={`w-4 h-4 rounded-full ${getColorClass(scenario.color)} animate-pulse`} />
                      ) : (
                        <Clock className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                    <span className={`text-sm ${
                      isCompleted 
                        ? 'text-green-700 font-medium' 
                        : isActive 
                        ? 'text-slate-800 font-medium' 
                        : 'text-slate-500'
                    }`}>
                      {trigger}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h4 className="font-medium text-slate-800 mb-3 flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span>Expected Outcomes</span>
            </h4>
            <div className="space-y-2">
              {scenario.expectedOutcomes.map((outcome, index) => {
                const isAchieved = scenarioProgress >= ((index + 1) / scenario.expectedOutcomes.length) * 100;
                
                return (
                  <div
                    key={index}
                    className={`flex items-center space-x-3 p-3 rounded-lg border ${
                      isAchieved 
                        ? 'border-green-200 bg-green-50' 
                        : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex-shrink-0">
                      {isAchieved ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
                      )}
                    </div>
                    <span className={`text-sm ${
                      isAchieved ? 'text-green-700 font-medium' : 'text-slate-600'
                    }`}>
                      {outcome}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderControlPanel = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Settings className="w-5 h-5" />
          <span>Demo Configuration</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Speed Control */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Scenario Speed
            </label>
            <select
              value={scenarioSpeed}
              onChange={(e) => setScenarioSpeed(e.target.value as any)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            >
              <option value="slow">Slow (Detailed)</option>
              <option value="normal">Normal</option>
              <option value="fast">Fast (Overview)</option>
            </select>
          </div>

          {/* Auto Progress */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Auto Progress
            </label>
            <label className="flex items-center space-x-2 p-2 border border-slate-200 rounded-lg">
              <input
                type="checkbox"
                checked={autoProgress}
                onChange={(e) => setAutoProgress(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-slate-700">Automatic progression</span>
            </label>
          </div>

          {/* Reset All */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Quick Actions
            </label>
            <button
              onClick={handleReset}
              className="w-full px-3 py-2 bg-slate-500 text-white rounded-lg hover:bg-slate-600 transition-colors text-sm flex items-center justify-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset All</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
          <PlayCircle className="w-6 h-6" />
          <span>Demo Controls</span>
        </h2>
        
        {selectedScenario && (
          <div className="flex items-center space-x-2 text-sm">
            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`}></div>
            <span className="font-medium text-slate-700">
              {isRunning ? 'Running' : 'Paused'}
            </span>
          </div>
        )}
      </div>

      {/* Active Scenario */}
      {renderActiveScenario()}

      {/* Scenario Cards */}
      {renderScenarioCards()}

      {/* Control Panel */}
      {renderControlPanel()}
    </div>
  );
}