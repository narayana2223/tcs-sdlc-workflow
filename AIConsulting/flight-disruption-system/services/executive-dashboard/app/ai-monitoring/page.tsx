'use client';

import React, { useState, useEffect } from 'react';
import { useRealTimeData } from '@/hooks/useRealTimeData';
import AgentActivityMonitor from '@/components/ai-monitoring/AgentActivityMonitor';
import DecisionTreeVisualizer from '@/components/ai-monitoring/DecisionTreeVisualizer';
import PerformanceAnalytics from '@/components/ai-monitoring/PerformanceAnalytics';
import LearningDashboard from '@/components/ai-monitoring/LearningDashboard';
import SystemHealthMonitor from '@/components/ai-monitoring/SystemHealthMonitor';
import DemoControls from '@/components/ai-monitoring/DemoControls';
import { 
  Brain, 
  Activity, 
  TrendingUp, 
  Cpu, 
  Network, 
  Zap,
  ArrowLeft,
  Maximize2,
  RefreshCw,
  Play,
  Pause
} from 'lucide-react';
import Link from 'next/link';

interface AgentDecision {
  id: string;
  agentType: 'prediction' | 'passenger' | 'resource' | 'communication' | 'coordinator';
  timestamp: Date;
  decision: string;
  reasoning: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  cost?: number;
  passengersBenefited?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  executionTime?: number;
  parentDecisionId?: string;
  childDecisions?: string[];
}

interface MLMetrics {
  modelAccuracy: number;
  predictionLatency: number;
  trainingProgress: number;
  dataQuality: number;
  modelDrift: number;
  featureImportance: Record<string, number>;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage?: number;
  networkLatency: number;
  throughput: number;
  errorRate: number;
  uptime: number;
}

export default function AIMonitoring() {
  const { dashboardState, isConnected } = useRealTimeData();
  const [activeView, setActiveView] = useState<'overview' | 'detailed'>('overview');
  const [fullscreenPanel, setFullscreenPanel] = useState<string | null>(null);
  const [isLiveMode, setIsLiveMode] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Mock comprehensive agent decisions for demonstration
  const mockAgentDecisions: AgentDecision[] = [
    {
      id: '1',
      agentType: 'coordinator',
      timestamp: new Date(),
      decision: 'Initiated cascading disruption response protocol',
      reasoning: 'Weather system affecting LHR requires coordinated multi-agent response. Predicted 45-minute average delays across 23 flights with 2,150 affected passengers.',
      confidence: 0.94,
      impact: 'critical',
      status: 'processing',
      executionTime: 2.3,
      childDecisions: ['2', '3', '4', '5']
    },
    {
      id: '2',
      agentType: 'prediction',
      timestamp: new Date(Date.now() - 30000),
      decision: 'Weather delay prediction: 45-90 minutes for LHR departures',
      reasoning: 'Machine learning ensemble (XGBoost + LSTM) analyzing: 1) Met Office severe weather warning, 2) Historical patterns showing 89% correlation, 3) Real-time radar indicating storm intensity increase, 4) Air traffic control capacity reduced to 60%.',
      confidence: 0.91,
      impact: 'high',
      status: 'completed',
      executionTime: 1.8,
      parentDecisionId: '1'
    },
    {
      id: '3',
      agentType: 'passenger',
      timestamp: new Date(Date.now() - 45000),
      decision: 'Proactive rebooking initiated for 847 passengers',
      reasoning: 'Priority algorithm triggered: 1) 156 premium passengers (immediate rebooking), 2) 234 connection passengers (2-hour window), 3) 457 flexible bookings (next 24h alternatives). Amadeus and Sabre APIs integrated for real-time availability.',
      confidence: 0.88,
      impact: 'high',
      status: 'processing',
      executionTime: 5.2,
      cost: 125000,
      passengersBenefited: 847,
      parentDecisionId: '1'
    },
    {
      id: '4',
      agentType: 'resource',
      timestamp: new Date(Date.now() - 60000),
      decision: 'Cost optimization: Hotels and transport arranged',
      reasoning: 'Dynamic pricing analysis across 12 hotel chains and 3 transport providers. Secured: 1) 89 hotel rooms at £78/night (34% below market), 2) 45 taxi vouchers, 3) 123 meal vouchers. Total cost: £23,400 vs estimated £45,000 traditional approach.',
      confidence: 0.92,
      impact: 'medium',
      status: 'completed',
      executionTime: 3.7,
      cost: 23400,
      passengersBenefited: 257,
      parentDecisionId: '1'
    },
    {
      id: '5',
      agentType: 'communication',
      timestamp: new Date(Date.now() - 75000),
      decision: 'Multi-channel passenger notifications deployed',
      reasoning: 'Personalized communication strategy: 1) 1,245 SMS sent (delivery: 98.2%), 2) 1,189 emails (open rate: 87%), 3) 892 push notifications, 4) 234 WhatsApp messages. Content adapted based on passenger profile and disruption severity.',
      confidence: 0.96,
      impact: 'high',
      status: 'completed',
      executionTime: 0.8,
      cost: 2100,
      passengersBenefited: 1245,
      parentDecisionId: '1'
    }
  ];

  // Mock ML metrics
  const mockMLMetrics: MLMetrics = {
    modelAccuracy: 94.8,
    predictionLatency: 180,
    trainingProgress: 78,
    dataQuality: 96.2,
    modelDrift: 2.1,
    featureImportance: {
      'weather_severity': 0.34,
      'historical_delays': 0.28,
      'air_traffic_load': 0.22,
      'aircraft_maintenance': 0.16
    }
  };

  // Mock system metrics
  const mockSystemMetrics: SystemMetrics = {
    cpuUsage: 72,
    memoryUsage: 68,
    gpuUsage: 85,
    networkLatency: 45,
    throughput: 2847,
    errorRate: 0.12,
    uptime: 99.94
  };

  const agentDecisions = dashboardState.agentDecisions.length > 0 ? dashboardState.agentDecisions : mockAgentDecisions;

  if (fullscreenPanel) {
    const FullscreenComponent = () => {
      switch (fullscreenPanel) {
        case 'activity':
          return <AgentActivityMonitor decisions={agentDecisions} selectedAgent={selectedAgent} onSelectAgent={setSelectedAgent} />;
        case 'decision-tree':
          return <DecisionTreeVisualizer decisions={agentDecisions} selectedDecision={selectedAgent} />;
        case 'analytics':
          return <PerformanceAnalytics decisions={agentDecisions} mlMetrics={mockMLMetrics} />;
        case 'learning':
          return <LearningDashboard mlMetrics={mockMLMetrics} decisions={agentDecisions} />;
        case 'system':
          return <SystemHealthMonitor systemMetrics={mockSystemMetrics} />;
        default:
          return null;
      }
    };

    return (
      <div className="fixed inset-0 bg-slate-900 z-50">
        <div className="h-full p-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-bold text-white">
              {fullscreenPanel.charAt(0).toUpperCase() + fullscreenPanel.slice(1)} - Fullscreen View
            </h1>
            <button
              onClick={() => setFullscreenPanel(null)}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600"
            >
              Exit Fullscreen
            </button>
          </div>
          <div className="h-full">
            <FullscreenComponent />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                href="/"
                className="flex items-center space-x-2 text-slate-600 hover:text-slate-800 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Back to Dashboard</span>
              </Link>
              
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <Brain className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-responsive-xl font-bold text-slate-800">AI Agent Monitoring</h1>
                  <p className="text-responsive-xs text-slate-600">Real-time AI decision tracking and performance analytics</p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Live Mode Toggle */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsLiveMode(!isLiveMode)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                    isLiveMode 
                      ? 'bg-success-100 text-success-700 border border-success-200' 
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {isLiveMode ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  <span className="text-sm font-medium">
                    {isLiveMode ? 'Live' : 'Paused'}
                  </span>
                </button>
              </div>

              {/* Quick Stats */}
              <div className="flex items-center space-x-4 px-4 py-2 bg-slate-50 rounded-lg">
                <div className="flex items-center space-x-1">
                  <Activity className="w-4 h-4 text-purple-500" />
                  <span className="text-sm font-medium">{agentDecisions.length} Decisions</span>
                </div>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="w-4 h-4 text-success-500" />
                  <span className="text-sm font-medium">{mockMLMetrics.modelAccuracy}% Accuracy</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Zap className="w-4 h-4 text-warning-500" />
                  <span className="text-sm font-medium">{mockSystemMetrics.throughput}/s Events</span>
                </div>
              </div>

              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium text-slate-700">
                  {isConnected ? 'Connected' : 'Demo Mode'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {activeView === 'overview' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column - Main Monitoring */}
            <div className="lg:col-span-8 space-y-6">
              {/* Agent Activity Monitor */}
              <div className="relative bg-white rounded-xl shadow-sm border border-slate-200 min-h-[400px]">
                <button
                  onClick={() => setFullscreenPanel('activity')}
                  className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <AgentActivityMonitor 
                  decisions={agentDecisions} 
                  selectedAgent={selectedAgent} 
                  onSelectAgent={setSelectedAgent}
                />
              </div>

              {/* Decision Tree Visualizer */}
              <div className="relative bg-white rounded-xl shadow-sm border border-slate-200 min-h-[500px]">
                <button
                  onClick={() => setFullscreenPanel('decision-tree')}
                  className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <DecisionTreeVisualizer 
                  decisions={agentDecisions} 
                  selectedDecision={selectedAgent}
                />
              </div>
            </div>

            {/* Right Column - Analytics and Controls */}
            <div className="lg:col-span-4 space-y-6">
              {/* Performance Analytics */}
              <div className="relative bg-white rounded-xl shadow-sm border border-slate-200">
                <button
                  onClick={() => setFullscreenPanel('analytics')}
                  className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <PerformanceAnalytics 
                  decisions={agentDecisions} 
                  mlMetrics={mockMLMetrics}
                />
              </div>

              {/* Demo Controls */}
              <DemoControls />

              {/* System Health Quick View */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-800">System Health</h3>
                  <button
                    onClick={() => setFullscreenPanel('system')}
                    className="p-1 hover:bg-slate-100 rounded transition-colors"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">CPU Usage</span>
                    <span className="text-sm font-medium">{mockSystemMetrics.cpuUsage}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${mockSystemMetrics.cpuUsage}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Model Accuracy</span>
                    <span className="text-sm font-medium text-success-600">{mockMLMetrics.modelAccuracy}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-success-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${mockMLMetrics.modelAccuracy}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Learning Dashboard */}
            <div className="relative bg-white rounded-xl shadow-sm border border-slate-200">
              <button
                onClick={() => setFullscreenPanel('learning')}
                className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <LearningDashboard 
                mlMetrics={mockMLMetrics} 
                decisions={agentDecisions}
              />
            </div>

            {/* System Health Monitor */}
            <div className="relative bg-white rounded-xl shadow-sm border border-slate-200">
              <button
                onClick={() => setFullscreenPanel('system')}
                className="absolute top-4 right-4 z-10 p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <SystemHealthMonitor systemMetrics={mockSystemMetrics} />
            </div>
          </div>
        )}

        {/* View Toggle */}
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2">
          <div className="flex items-center bg-white rounded-full shadow-lg border border-slate-200 p-1">
            <button
              onClick={() => setActiveView('overview')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeView === 'overview'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-600 hover:text-slate-800'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveView('detailed')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeView === 'detailed'
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-600 hover:text-slate-800'
              }`}
            >
              Detailed
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}