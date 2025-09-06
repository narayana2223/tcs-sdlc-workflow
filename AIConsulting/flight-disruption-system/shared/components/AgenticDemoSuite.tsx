import React, { useState, useEffect } from 'react';
import { Play, Pause, BarChart3, Settings, Monitor } from 'lucide-react';
import DemoController from './DemoController';
import TraditionalVsAI from './TraditionalVsAI';
import DecisionStream from './DecisionStream';
import AgentCollaboration from './AgentCollaboration';
import DataFlowVisualization from './DataFlowVisualization';

type DemoMode = 'controller' | 'comparison' | 'decisions' | 'collaboration' | 'dataflow';

interface DemoState {
  activeScenario: string | null;
  isRunning: boolean;
  isPaused: boolean;
  currentPassengers: number;
  scenarioComplexity: number;
  elapsedTime: number;
}

interface AgenticDemoSuiteProps {
  interfaceType: 'executive' | 'operations' | 'passenger';
  className?: string;
  onStateChange?: (state: DemoState) => void;
}

export default function AgenticDemoSuite({ 
  interfaceType, 
  className = '',
  onStateChange 
}: AgenticDemoSuiteProps) {
  const [currentMode, setCurrentMode] = useState<DemoMode>('controller');
  const [demoState, setDemoState] = useState<DemoState>({
    activeScenario: null,
    isRunning: false,
    isPaused: false,
    currentPassengers: 0,
    scenarioComplexity: 1,
    elapsedTime: 0
  });

  // Scenario configurations for different passenger counts and complexity
  const scenarioConfigs = {
    'weather_system': { passengers: 156, complexity: 9 },
    'crew_strike': { passengers: 182, complexity: 8 },
    'technical_cascade': { passengers: 208, complexity: 10 },
    'airport_closure': { passengers: 312, complexity: 9 },
    'cyber_incident': { passengers: 267, complexity: 8 }
  };

  const modeConfig = {
    controller: {
      title: 'Demo Control Center',
      description: 'Launch and manage live agentic intelligence demonstrations',
      icon: Play,
      color: 'from-blue-600 to-indigo-700'
    },
    comparison: {
      title: 'Traditional vs AI Analysis',
      description: 'Executive-level ROI and performance comparison analysis',
      icon: BarChart3,
      color: 'from-green-600 to-emerald-700'
    },
    decisions: {
      title: 'Live Decision Intelligence',
      description: 'Real-time AI decision-making with transparent reasoning chains',
      icon: Settings,
      color: 'from-purple-600 to-violet-700'
    },
    collaboration: {
      title: 'Agent Collaboration Network',
      description: 'Multi-agent coordination and consensus building visualization',
      icon: Monitor,
      color: 'from-orange-600 to-red-700'
    },
    dataflow: {
      title: 'Cross-Module Data Flow',
      description: 'Inter-module communication and state synchronization monitoring',
      icon: Monitor,
      color: 'from-pink-600 to-rose-700'
    }
  };

  // Update demo state based on scenario selection
  useEffect(() => {
    if (demoState.activeScenario && scenarioConfigs[demoState.activeScenario as keyof typeof scenarioConfigs]) {
      const config = scenarioConfigs[demoState.activeScenario as keyof typeof scenarioConfigs];
      setDemoState(prev => ({
        ...prev,
        currentPassengers: config.passengers,
        scenarioComplexity: config.complexity
      }));
    }
  }, [demoState.activeScenario]);

  // Notify parent of state changes
  useEffect(() => {
    onStateChange?.(demoState);
  }, [demoState, onStateChange]);

  const handleScenarioStart = (scenarioId: string) => {
    const config = scenarioConfigs[scenarioId as keyof typeof scenarioConfigs];
    setDemoState(prev => ({
      ...prev,
      activeScenario: scenarioId,
      isRunning: true,
      isPaused: false,
      currentPassengers: config?.passengers || 150,
      scenarioComplexity: config?.complexity || 8,
      elapsedTime: 0
    }));
  };

  const handleScenarioPause = () => {
    setDemoState(prev => ({ ...prev, isPaused: !prev.isPaused }));
  };

  const handleScenarioStop = () => {
    setDemoState(prev => ({ ...prev, isRunning: false, isPaused: false }));
  };

  const handleScenarioReset = () => {
    setDemoState({
      activeScenario: null,
      isRunning: false,
      isPaused: false,
      currentPassengers: 0,
      scenarioComplexity: 1,
      elapsedTime: 0
    });
  };

  const ModeSelector = () => (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-white mb-4 text-center">
        Agentic Intelligence Demonstration Suite
      </h2>
      <p className="text-gray-300 text-center mb-6">
        Interactive showcase of autonomous AI decision-making capabilities for {interfaceType} stakeholders
      </p>
      
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {Object.entries(modeConfig).map(([mode, config]) => {
          const Icon = config.icon;
          const isActive = currentMode === mode;
          
          return (
            <button
              key={mode}
              onClick={() => setCurrentMode(mode as DemoMode)}
              className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${
                isActive
                  ? 'border-white/50 bg-white/10 shadow-lg'
                  : 'border-white/20 bg-white/5 hover:bg-white/10 hover:border-white/30'
              }`}
            >
              <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${config.color} ${
                isActive ? 'opacity-20' : 'opacity-10'
              } transition-opacity duration-300`}></div>
              
              <div className="relative">
                <Icon className={`w-8 h-8 mx-auto mb-3 ${
                  isActive ? 'text-white' : 'text-gray-300'
                } transition-colors duration-300`} />
                <h3 className={`font-semibold text-sm mb-2 ${
                  isActive ? 'text-white' : 'text-gray-300'
                } transition-colors duration-300`}>
                  {config.title}
                </h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  {config.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );

  const renderCurrentMode = () => {
    switch (currentMode) {
      case 'controller':
        return (
          <DemoController
            onScenarioStart={handleScenarioStart}
            onScenarioPause={handleScenarioPause}
            onScenarioStop={handleScenarioStop}
            onScenarioReset={handleScenarioReset}
            className="w-full"
          />
        );
        
      case 'comparison':
        return (
          <TraditionalVsAI
            passengerCount={demoState.currentPassengers || 150}
            scenarioComplexity={demoState.scenarioComplexity || 8}
            animated={demoState.isRunning}
            className="w-full"
          />
        );
        
      case 'decisions':
        return (
          <div className="space-y-6">
            <DecisionStream
              isActive={demoState.isRunning}
              scenarioId={demoState.activeScenario}
              className="w-full"
            />
            {!demoState.isRunning && (
              <div className="text-center p-12 bg-white/5 rounded-2xl border border-white/20">
                <div className="text-6xl mb-4">🤖</div>
                <h3 className="text-xl font-bold text-white mb-2">No Active Demo</h3>
                <p className="text-gray-300 mb-4">
                  Start a scenario from the Demo Control Center to see live AI decisions
                </p>
                <button
                  onClick={() => setCurrentMode('controller')}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-xl font-semibold hover:from-blue-500 hover:to-indigo-600 transition-all duration-300"
                >
                  Launch Demo Controller
                </button>
              </div>
            )}
          </div>
        );
        
      case 'collaboration':
        return (
          <div className="space-y-6">
            <AgentCollaboration
              isActive={demoState.isRunning}
              scenarioId={demoState.activeScenario}
              passengerCount={demoState.currentPassengers}
              className="w-full"
            />
            {!demoState.isRunning && (
              <div className="text-center p-12 bg-white/5 rounded-2xl border border-white/20">
                <div className="text-6xl mb-4">🤝</div>
                <h3 className="text-xl font-bold text-white mb-2">No Active Collaboration</h3>
                <p className="text-gray-300 mb-4">
                  Start a scenario to see live agent collaboration and consensus building
                </p>
                <button
                  onClick={() => setCurrentMode('controller')}
                  className="px-6 py-3 bg-gradient-to-r from-orange-600 to-red-700 text-white rounded-xl font-semibold hover:from-orange-500 hover:to-red-600 transition-all duration-300"
                >
                  Launch Demo Controller
                </button>
              </div>
            )}
          </div>
        );
        
      case 'dataflow':
        return (
          <div className="space-y-6">
            <DataFlowVisualization
              isActive={demoState.isRunning}
              interfaceType={interfaceType}
              className="w-full"
            />
            {!demoState.isRunning && (
              <div className="text-center p-12 bg-white/5 rounded-2xl border border-white/20">
                <div className="text-6xl mb-4">🔄</div>
                <h3 className="text-xl font-bold text-white mb-2">No Active Data Flow</h3>
                <p className="text-gray-300 mb-4">
                  Start a scenario to see live cross-module communication and data synchronization
                </p>
                <button
                  onClick={() => setCurrentMode('controller')}
                  className="px-6 py-3 bg-gradient-to-r from-pink-600 to-rose-700 text-white rounded-xl font-semibold hover:from-pink-500 hover:to-rose-600 transition-all duration-300"
                >
                  Launch Demo Controller
                </button>
              </div>
            )}
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6 ${className}`}>
      <div className="max-w-7xl mx-auto">
        <ModeSelector />
        
        {/* Demo Status Bar */}
        {demoState.isRunning && (
          <div className="mb-6 p-4 bg-gradient-to-r from-green-600/20 to-emerald-700/20 rounded-2xl border border-green-400/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-3 h-3 rounded-full ${
                  demoState.isPaused ? 'bg-yellow-400 animate-pulse' : 'bg-green-400 animate-pulse'
                }`}></div>
                <span className="text-white font-semibold">
                  Demo Active: {demoState.activeScenario?.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="flex items-center space-x-6 text-sm">
                <span className="text-gray-300">
                  Passengers: <span className="text-white font-semibold">{demoState.currentPassengers}</span>
                </span>
                <span className="text-gray-300">
                  Complexity: <span className="text-white font-semibold">{demoState.scenarioComplexity}/10</span>
                </span>
                <span className="text-gray-300">
                  Status: <span className={`font-semibold ${
                    demoState.isPaused ? 'text-yellow-300' : 'text-green-300'
                  }`}>
                    {demoState.isPaused ? 'Paused' : 'Running'}
                  </span>
                </span>
              </div>
            </div>
          </div>
        )}
        
        {/* Main Demo Content */}
        <div className="space-y-8">
          {renderCurrentMode()}
        </div>
        
        {/* Quick Actions */}
        {demoState.isRunning && currentMode !== 'controller' && (
          <div className="fixed bottom-6 right-6 flex space-x-3">
            <button
              onClick={handleScenarioPause}
              className="flex items-center space-x-2 px-4 py-3 bg-gradient-to-r from-yellow-600 to-orange-700 text-white rounded-xl font-semibold shadow-lg hover:from-yellow-500 hover:to-orange-600 transition-all duration-300"
            >
              {demoState.isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
              <span>{demoState.isPaused ? 'Resume' : 'Pause'}</span>
            </button>
            <button
              onClick={() => setCurrentMode('controller')}
              className="flex items-center space-x-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-xl font-semibold shadow-lg hover:from-blue-500 hover:to-indigo-600 transition-all duration-300"
            >
              <Settings className="w-5 h-5" />
              <span>Controls</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}