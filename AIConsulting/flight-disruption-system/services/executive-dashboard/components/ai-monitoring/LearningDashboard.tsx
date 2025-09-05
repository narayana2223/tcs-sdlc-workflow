'use client';

import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  Database, 
  Zap, 
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  Activity,
  RefreshCw
} from 'lucide-react';

interface MLMetrics {
  modelAccuracy: number;
  predictionLatency: number;
  trainingProgress: number;
  dataQuality: number;
  modelDrift: number;
  featureImportance: Record<string, number>;
}

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

interface LearningDashboardProps {
  mlMetrics: MLMetrics;
  decisions: AgentDecision[];
}

interface ModelPerformance {
  modelName: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  lastUpdated: Date;
  trainingStatus: 'training' | 'completed' | 'pending' | 'failed';
  dataPoints: number;
}

const mockModelPerformance: ModelPerformance[] = [
  {
    modelName: 'Weather Impact Predictor',
    accuracy: 94.8,
    precision: 92.3,
    recall: 96.1,
    f1Score: 94.2,
    lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000),
    trainingStatus: 'completed',
    dataPoints: 45678
  },
  {
    modelName: 'Delay Duration Estimator',
    accuracy: 87.5,
    precision: 89.2,
    recall: 85.8,
    f1Score: 87.5,
    lastUpdated: new Date(Date.now() - 4 * 60 * 60 * 1000),
    trainingStatus: 'training',
    dataPoints: 32451
  },
  {
    modelName: 'Passenger Behavior Classifier',
    accuracy: 91.2,
    precision: 88.7,
    recall: 93.4,
    f1Score: 91.0,
    lastUpdated: new Date(Date.now() - 6 * 60 * 60 * 1000),
    trainingStatus: 'completed',
    dataPoints: 28934
  },
  {
    modelName: 'Cost Optimization Engine',
    accuracy: 96.1,
    precision: 94.8,
    recall: 97.3,
    f1Score: 96.0,
    lastUpdated: new Date(Date.now() - 1 * 60 * 60 * 1000),
    trainingStatus: 'completed',
    dataPoints: 51203
  }
];

const trainingHistory = {
  labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Current'],
  accuracy: [87.2, 89.1, 91.5, 93.2, 94.8],
  dataQuality: [92.1, 93.5, 95.2, 96.8, 96.2],
  processingTime: [2.8, 2.5, 2.1, 1.9, 1.8]
};

export default function LearningDashboard({ mlMetrics, decisions }: LearningDashboardProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<'24h' | '7d' | '30d'>('7d');
  const [learningInsights, setLearningInsights] = useState<string[]>([]);

  // Generate learning insights
  useEffect(() => {
    const generateInsights = () => {
      const insights = [
        "Weather feature importance increased 12% after incorporating radar data",
        "Model drift detected in passenger behavior patterns - retraining recommended",
        "Cost optimization model achieved 96.1% accuracy with new vendor pricing data", 
        "Prediction latency improved 23% after model compression techniques",
        "New feature 'historical_delays' shows high correlation (0.84) with disruption severity"
      ];
      
      setLearningInsights(insights.slice(0, 3));
    };

    generateInsights();
  }, [decisions, mlMetrics]);

  const getStatusColor = (status: string) => {
    const colors = {
      training: 'yellow',
      completed: 'green',
      pending: 'slate',
      failed: 'red'
    };
    return colors[status as keyof typeof colors] || 'slate';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      training: RefreshCw,
      completed: CheckCircle,
      pending: Clock,
      failed: AlertTriangle
    };
    return icons[status as keyof typeof icons] || Clock;
  };

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

  const renderMetricCard = (title: string, value: string, trend: number, icon: React.ComponentType<any>, color: string) => {
    const Icon = icon;
    const isPositive = trend >= 0;
    
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2 ${getColorClass(color)} rounded-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div className={`flex items-center space-x-1 text-sm ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="font-medium">{isPositive ? '+' : ''}{trend}%</span>
          </div>
        </div>
        <div className="text-xl font-bold text-slate-800 mb-1">{value}</div>
        <div className="text-sm text-slate-600">{title}</div>
      </div>
    );
  };

  const renderFeatureImportance = () => {
    const sortedFeatures = Object.entries(mlMetrics.featureImportance)
      .sort(([,a], [,b]) => b - a);

    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Target className="w-5 h-5" />
          <span>Feature Importance</span>
        </h3>
        
        <div className="space-y-4">
          {sortedFeatures.map(([feature, importance], index) => {
            const colors = ['purple', 'blue', 'green', 'orange'];
            const color = colors[index % colors.length];
            
            return (
              <div key={feature}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-slate-700 capitalize">
                    {feature.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-slate-600">{(importance * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div 
                    className={`${getColorClass(color)} h-3 rounded-full transition-all duration-1000`}
                    style={{ width: `${importance * 100}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderModelPerformance = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Brain className="w-5 h-5" />
          <span>Model Performance</span>
        </h3>
        
        <div className="space-y-4">
          {mockModelPerformance.map((model) => {
            const StatusIcon = getStatusIcon(model.trainingStatus);
            const statusColor = getStatusColor(model.trainingStatus);
            
            return (
              <div
                key={model.modelName}
                onClick={() => setSelectedModel(
                  selectedModel === model.modelName ? null : model.modelName
                )}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedModel === model.modelName 
                    ? 'border-purple-200 bg-purple-50' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-slate-800">{model.modelName}</h4>
                  <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${
                    getColorClass(statusColor)
                  } bg-opacity-20`}>
                    <StatusIcon className={`w-3 h-3 ${getColorClass(statusColor, 'text')} ${
                      model.trainingStatus === 'training' ? 'animate-spin' : ''
                    }`} />
                    <span className={`text-xs ${getColorClass(statusColor, 'text')} capitalize`}>
                      {model.trainingStatus}
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <div className="text-slate-500 text-xs">Accuracy</div>
                    <div className="font-semibold text-slate-800">{model.accuracy}%</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Precision</div>
                    <div className="font-semibold text-slate-800">{model.precision}%</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Recall</div>
                    <div className="font-semibold text-slate-800">{model.recall}%</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">F1 Score</div>
                    <div className="font-semibold text-slate-800">{model.f1Score}%</div>
                  </div>
                </div>

                {selectedModel === model.modelName && (
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Data Points:</span>
                        <span className="ml-2 font-medium">{model.dataPoints.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Last Updated:</span>
                        <span className="ml-2 font-medium">
                          {model.lastUpdated.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderTrainingProgress = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Activity className="w-5 h-5" />
          <span>Training Progress</span>
        </h3>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-700">Current Training Cycle</span>
            <span className="text-sm text-slate-600">{mlMetrics.trainingProgress}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-1000"
              style={{ width: `${mlMetrics.trainingProgress}%` }}
            ></div>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Estimated completion: {Math.ceil((100 - mlMetrics.trainingProgress) / 10)} minutes
          </div>
        </div>

        {/* Historical Performance Chart */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-slate-700 mb-3">Historical Accuracy</h4>
          <div className="space-y-2">
            {trainingHistory.accuracy.map((accuracy, index) => (
              <div key={index} className="flex items-center space-x-3">
                <span className="text-xs text-slate-500 w-16">{trainingHistory.labels[index]}</span>
                <div className="flex-1 bg-slate-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-1000 ${
                      index === trainingHistory.accuracy.length - 1 
                        ? 'bg-gradient-to-r from-green-400 to-green-600' 
                        : 'bg-slate-400'
                    }`}
                    style={{ 
                      width: `${accuracy}%`,
                      animationDelay: `${index * 200}ms`
                    }}
                  ></div>
                </div>
                <span className="text-xs font-medium text-slate-700 w-12">{accuracy}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Data Quality Metrics */}
        <div>
          <h4 className="text-sm font-medium text-slate-700 mb-3">Data Quality Trends</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-lg font-bold text-slate-800">{mlMetrics.dataQuality}%</div>
              <div className="text-xs text-slate-500">Data Quality</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-slate-800">{mlMetrics.modelDrift.toFixed(1)}%</div>
              <div className="text-xs text-slate-500">Model Drift</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-slate-800">{mlMetrics.predictionLatency}ms</div>
              <div className="text-xs text-slate-500">Latency</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderLearningInsights = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <GraduationCap className="w-5 h-5" />
          <span>Learning Insights</span>
        </h3>
        
        <div className="space-y-4">
          {learningInsights.map((insight, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
              <div className="p-1 bg-blue-500 rounded-full flex-shrink-0 mt-1">
                <CheckCircle className="w-3 h-3 text-white" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{insight}</p>
            </div>
          ))}
          
          <div className="pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Next training cycle in:</span>
              <span className="font-medium text-slate-800">2h 15m</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
            <GraduationCap className="w-6 h-6" />
            <span>Learning Dashboard</span>
          </h2>
          
          {/* Timeframe selector */}
          <select 
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as any)}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {renderMetricCard("Model Accuracy", `${mlMetrics.modelAccuracy}%`, 3.6, Brain, 'purple')}
          {renderMetricCard("Data Quality", `${mlMetrics.dataQuality}%`, 1.2, Database, 'blue')}
          {renderMetricCard("Prediction Speed", `${mlMetrics.predictionLatency}ms`, -15.3, Zap, 'green')}
          {renderMetricCard("Model Drift", `${mlMetrics.modelDrift}%`, -8.7, AlertTriangle, 'orange')}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {renderModelPerformance()}
            {renderLearningInsights()}
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {renderTrainingProgress()}
            {renderFeatureImportance()}
          </div>
        </div>
      </div>
    </div>
  );
}