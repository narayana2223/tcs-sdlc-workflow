import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, RotateCcw, Clock, Users, Plane, AlertTriangle, DollarSign, TrendingUp } from 'lucide-react';

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  passengerCount: number;
  flightCount: number;
  estimatedCost: number;
  complexityScore: number;
  duration: number; // in minutes
  icon: string;
  color: string;
}

interface DemoState {
  currentScenario: string | null;
  isRunning: boolean;
  isPaused: boolean;
  progress: number;
  startTime: Date | null;
  elapsedTime: number;
  metrics: {
    passengersProcessed: number;
    decisionsMade: number;
    costSavings: number;
    averageResolutionTime: number;
    satisfactionScore: number;
  };
}

interface DemoControllerProps {
  onScenarioStart?: (scenarioId: string) => void;
  onScenarioPause?: () => void;
  onScenarioStop?: () => void;
  onScenarioReset?: () => void;
  className?: string;
}

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'weather_system',
    name: 'Storm Eunice Redux - Weather Cascade',
    description: 'Major storm system affecting 4 airports with 150+ passengers, resource competition, and VIP priority conflicts',
    passengerCount: 156,
    flightCount: 4,
    estimatedCost: 425000,
    complexityScore: 9,
    duration: 8,
    icon: '🌪️',
    color: 'from-blue-600 to-indigo-700'
  },
  {
    id: 'crew_strike',
    name: 'Multi-Airline Crew Strike',
    description: 'Coordinated strike action affecting 3 airlines with 180+ passengers requiring alternative arrangements',
    passengerCount: 182,
    flightCount: 3,
    estimatedCost: 285000,
    complexityScore: 8,
    duration: 12,
    icon: '✊',
    color: 'from-red-600 to-pink-700'
  },
  {
    id: 'technical_cascade',
    name: 'Boeing 737 MAX Fleet Grounding',
    description: 'Mandatory safety inspection requiring fleet grounding, 200+ passengers with urgent rebooking needs',
    passengerCount: 208,
    flightCount: 3,
    estimatedCost: 520000,
    complexityScore: 10,
    duration: 15,
    icon: '🔧',
    color: 'from-orange-600 to-red-700'
  },
  {
    id: 'airport_closure',
    name: 'Heathrow Fog Closure',
    description: 'Dense fog closing LHR with 300+ passengers across 8 flights requiring comprehensive re-routing',
    passengerCount: 312,
    flightCount: 8,
    estimatedCost: 680000,
    complexityScore: 9,
    duration: 10,
    icon: '🌫️',
    color: 'from-gray-600 to-slate-700'
  },
  {
    id: 'cyber_incident',
    name: 'Airline Systems Cyber Attack',
    description: 'Ransomware attack on reservation systems affecting 250+ passengers with manual processing required',
    passengerCount: 267,
    flightCount: 6,
    estimatedCost: 390000,
    complexityScore: 8,
    duration: 18,
    icon: '🛡️',
    color: 'from-purple-600 to-violet-700'
  }
];

export default function DemoController({ 
  onScenarioStart, 
  onScenarioPause, 
  onScenarioStop, 
  onScenarioReset,
  className = '' 
}: DemoControllerProps) {
  const [demoState, setDemoState] = useState<DemoState>({
    currentScenario: null,
    isRunning: false,
    isPaused: false,
    progress: 0,
    startTime: null,
    elapsedTime: 0,
    metrics: {
      passengersProcessed: 0,
      decisionsMade: 0,
      costSavings: 0,
      averageResolutionTime: 0,
      satisfactionScore: 4.2
    }
  });

  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  // Timer effect for demo progress
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (demoState.isRunning && !demoState.isPaused && demoState.currentScenario) {
      const scenario = DEMO_SCENARIOS.find(s => s.id === demoState.currentScenario);
      if (scenario) {
        interval = setInterval(() => {
          setDemoState(prev => {
            const newElapsedTime = prev.elapsedTime + 1;
            const progress = Math.min((newElapsedTime / (scenario.duration * 60)) * 100, 100);
            
            // Simulate realistic metrics progression
            const progressFactor = progress / 100;
            const passengersProcessed = Math.floor(scenario.passengerCount * progressFactor);
            const decisionsMade = Math.floor(passengersProcessed * 1.8 + Math.random() * 10);
            const costSavings = Math.floor(scenario.estimatedCost * 0.35 * progressFactor);
            const averageResolutionTime = Math.floor(25 - (progressFactor * 12)); // Decreases as system optimizes
            const satisfactionScore = 4.2 + (progressFactor * 0.6); // Increases with successful resolutions

            return {
              ...prev,
              progress,
              elapsedTime: newElapsedTime,
              metrics: {
                passengersProcessed,
                decisionsMade,
                costSavings,
                averageResolutionTime,
                satisfactionScore: parseFloat(satisfactionScore.toFixed(1))
              }
            };
          });
        }, 1000);
      }
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [demoState.isRunning, demoState.isPaused, demoState.currentScenario]);

  const startScenario = (scenarioId: string) => {
    setDemoState({
      currentScenario: scenarioId,
      isRunning: true,
      isPaused: false,
      progress: 0,
      startTime: new Date(),
      elapsedTime: 0,
      metrics: {
        passengersProcessed: 0,
        decisionsMade: 0,
        costSavings: 0,
        averageResolutionTime: 30,
        satisfactionScore: 4.2
      }
    });
    onScenarioStart?.(scenarioId);
  };

  const pauseScenario = () => {
    setDemoState(prev => ({ ...prev, isPaused: !prev.isPaused }));
    onScenarioPause?.();
  };

  const stopScenario = () => {
    setDemoState(prev => ({ 
      ...prev, 
      isRunning: false, 
      isPaused: false 
    }));
    onScenarioStop?.();
  };

  const resetScenario = () => {
    setDemoState({
      currentScenario: null,
      isRunning: false,
      isPaused: false,
      progress: 0,
      startTime: null,
      elapsedTime: 0,
      metrics: {
        passengersProcessed: 0,
        decisionsMade: 0,
        costSavings: 0,
        averageResolutionTime: 0,
        satisfactionScore: 4.2
      }
    });
    setSelectedScenario(null);
    onScenarioReset?.();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatCurrency = (amount: number): string => {
    return `£${(amount / 1000).toFixed(0)}K`;
  };

  const currentScenarioData = demoState.currentScenario 
    ? DEMO_SCENARIOS.find(s => s.id === demoState.currentScenario)
    : null;

  return (
    <div className={`bg-white/10 backdrop-blur-2xl rounded-3xl border border-white/20 shadow-2xl ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            <h3 className="text-xl font-bold text-white">Agentic Intelligence Demo Controller</h3>
          </div>
          {demoState.isRunning && (
            <div className="flex items-center space-x-2 text-sm text-green-300">
              <Clock className="w-4 h-4" />
              <span>{formatTime(demoState.elapsedTime)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Scenario Selection */}
      {!demoState.isRunning && (
        <div className="p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Select Disruption Scenario</h4>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {DEMO_SCENARIOS.map((scenario) => (
              <div
                key={scenario.id}
                className={`relative p-4 rounded-xl border-2 transition-all duration-300 cursor-pointer ${
                  selectedScenario === scenario.id
                    ? 'border-white/50 bg-white/10'
                    : 'border-white/20 bg-white/5 hover:bg-white/10'
                }`}
                onClick={() => setSelectedScenario(scenario.id)}
              >
                <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${scenario.color} opacity-10`}></div>
                <div className="relative">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{scenario.icon}</span>
                      <div>
                        <h5 className="font-bold text-white">{scenario.name}</h5>
                        <div className="flex items-center space-x-4 text-sm text-gray-300 mt-1">
                          <span className="flex items-center space-x-1">
                            <Users className="w-4 h-4" />
                            <span>{scenario.passengerCount}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Plane className="w-4 h-4" />
                            <span>{scenario.flightCount}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Clock className="w-4 h-4" />
                            <span>{scenario.duration}min</span>
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-300">Complexity</div>
                      <div className="text-lg font-bold text-white">{scenario.complexityScore}/10</div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-300 mb-3">{scenario.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Est. Cost Impact</span>
                    <span className="font-bold text-orange-300">{formatCurrency(scenario.estimatedCost)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Demo Controls */}
      <div className="p-6 border-t border-white/10">
        <div className="flex items-center justify-center space-x-4">
          {!demoState.isRunning ? (
            <button
              onClick={() => selectedScenario && startScenario(selectedScenario)}
              disabled={!selectedScenario}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-700 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-green-500 hover:to-emerald-600 transition-all duration-300"
            >
              <Play className="w-5 h-5" />
              <span>Start Demo</span>
            </button>
          ) : (
            <>
              <button
                onClick={pauseScenario}
                className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-700 text-white rounded-xl font-semibold hover:from-yellow-500 hover:to-orange-600 transition-all duration-300"
              >
                {demoState.isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
                <span>{demoState.isPaused ? 'Resume' : 'Pause'}</span>
              </button>
              <button
                onClick={stopScenario}
                className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-red-600 to-pink-700 text-white rounded-xl font-semibold hover:from-red-500 hover:to-pink-600 transition-all duration-300"
              >
                <Square className="w-5 h-5" />
                <span>Stop</span>
              </button>
            </>
          )}
          <button
            onClick={resetScenario}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-gray-600 to-slate-700 text-white rounded-xl font-semibold hover:from-gray-500 hover:to-slate-600 transition-all duration-300"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Progress and Metrics */}
      {demoState.isRunning && currentScenarioData && (
        <div className="p-6 border-t border-white/10">
          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white">Demo Progress</span>
              <span className="text-sm text-gray-300">{Math.round(demoState.progress)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${demoState.progress}%` }}
              ></div>
            </div>
          </div>

          {/* Current Scenario Info */}
          <div className="mb-6 p-4 bg-white/5 rounded-xl">
            <div className="flex items-center space-x-3 mb-2">
              <span className="text-2xl">{currentScenarioData.icon}</span>
              <div>
                <h5 className="font-bold text-white">{currentScenarioData.name}</h5>
                <p className="text-sm text-gray-300">{currentScenarioData.description}</p>
              </div>
            </div>
          </div>

          {/* Real-time Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-white/5 rounded-xl">
              <Users className="w-6 h-6 text-blue-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-white">{demoState.metrics.passengersProcessed}</div>
              <div className="text-xs text-gray-400">Passengers Processed</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-purple-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-white">{demoState.metrics.decisionsMade}</div>
              <div className="text-xs text-gray-400">AI Decisions Made</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-xl">
              <DollarSign className="w-6 h-6 text-green-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-white">{formatCurrency(demoState.metrics.costSavings)}</div>
              <div className="text-xs text-gray-400">Cost Savings</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-xl">
              <Clock className="w-6 h-6 text-orange-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-white">{demoState.metrics.averageResolutionTime}min</div>
              <div className="text-xs text-gray-400">Avg Resolution</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-xl">
              <TrendingUp className="w-6 h-6 text-pink-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-white">{demoState.metrics.satisfactionScore}/5</div>
              <div className="text-xs text-gray-400">Satisfaction</div>
            </div>
          </div>
        </div>
      )}

      {/* Demo Completed */}
      {demoState.isRunning && demoState.progress >= 100 && (
        <div className="p-6 border-t border-white/10">
          <div className="text-center p-6 bg-gradient-to-r from-green-600/20 to-emerald-700/20 rounded-xl border border-green-400/30">
            <div className="text-4xl mb-3">🎉</div>
            <h4 className="text-xl font-bold text-white mb-2">Scenario Completed Successfully!</h4>
            <p className="text-green-300 mb-4">
              All {currentScenarioData?.passengerCount} passengers processed with autonomous intelligence
            </p>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-300">Total Decisions:</span>
                <div className="font-bold text-white">{demoState.metrics.decisionsMade}</div>
              </div>
              <div>
                <span className="text-gray-300">Cost Savings:</span>
                <div className="font-bold text-green-300">{formatCurrency(demoState.metrics.costSavings)}</div>
              </div>
              <div>
                <span className="text-gray-300">Avg Resolution:</span>
                <div className="font-bold text-blue-300">{demoState.metrics.averageResolutionTime} min</div>
              </div>
              <div>
                <span className="text-gray-300">Satisfaction:</span>
                <div className="font-bold text-pink-300">{demoState.metrics.satisfactionScore}/5</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}