import React, { useState, useEffect } from 'react';
import { TrendingDown, TrendingUp, Clock, DollarSign, Users, Phone, Bot, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface ComparisonMetrics {
  resolutionTime: number; // in minutes
  costPerPassenger: number; // in GBP
  satisfactionScore: number; // out of 5
  automationRate: number; // percentage
  errorRate: number; // percentage
  staffRequired: number; // number of staff
  customerContacts: number; // calls per passenger
  escalationRate: number; // percentage requiring escalation
}

interface TraditionalVsAIProps {
  passengerCount?: number;
  scenarioComplexity?: number; // 1-10
  className?: string;
  animated?: boolean;
}

const TRADITIONAL_BASELINE: ComparisonMetrics = {
  resolutionTime: 240, // 4 hours average
  costPerPassenger: 180, // High manual processing cost
  satisfactionScore: 2.1,
  automationRate: 15,
  errorRate: 12,
  staffRequired: 25,
  customerContacts: 3.2,
  escalationRate: 35,
};

const AI_ENHANCED: ComparisonMetrics = {
  resolutionTime: 22, // 22 minutes average
  costPerPassenger: 12, // Highly optimized
  satisfactionScore: 4.7,
  automationRate: 95,
  errorRate: 1.8,
  staffRequired: 2,
  customerContacts: 0.3,
  escalationRate: 5,
};

export default function TraditionalVsAI({ 
  passengerCount = 150, 
  scenarioComplexity = 8,
  className = '',
  animated = true 
}: TraditionalVsAIProps) {
  const [showComparison, setShowComparison] = useState(false);
  const [animationProgress, setAnimationProgress] = useState(0);

  useEffect(() => {
    if (animated) {
      const timer = setInterval(() => {
        setAnimationProgress(prev => {
          if (prev >= 100) {
            clearInterval(timer);
            return 100;
          }
          return prev + 2;
        });
      }, 100);

      return () => clearInterval(timer);
    } else {
      setAnimationProgress(100);
    }
  }, [animated]);

  const calculateScenarioAdjustedMetrics = (baseMetrics: ComparisonMetrics, isAI: boolean) => {
    const complexityMultiplier = 1 + (scenarioComplexity - 5) * 0.1;
    const passengerMultiplier = Math.log10(passengerCount / 100 + 1);

    return {
      resolutionTime: Math.round(baseMetrics.resolutionTime * complexityMultiplier * (isAI ? 1 : passengerMultiplier)),
      costPerPassenger: Math.round(baseMetrics.costPerPassenger * complexityMultiplier),
      satisfactionScore: Math.max(1, Math.min(5, baseMetrics.satisfactionScore - (isAI ? 0 : complexityMultiplier * 0.3))),
      automationRate: Math.max(0, Math.min(100, baseMetrics.automationRate - (isAI ? 0 : complexityMultiplier * 5))),
      errorRate: Math.max(0, baseMetrics.errorRate * (isAI ? 1 : complexityMultiplier)),
      staffRequired: Math.round(baseMetrics.staffRequired * (isAI ? 1 : complexityMultiplier)),
      customerContacts: baseMetrics.customerContacts * (isAI ? 1 : complexityMultiplier),
      escalationRate: Math.max(0, Math.min(100, baseMetrics.escalationRate * (isAI ? 1 : complexityMultiplier))),
    };
  };

  const traditionalMetrics = calculateScenarioAdjustedMetrics(TRADITIONAL_BASELINE, false);
  const aiMetrics = calculateScenarioAdjustedMetrics(AI_ENHANCED, true);

  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}min`;
  };

  const formatCurrency = (amount: number): string => `£${amount}`;

  const calculateSavings = (traditional: number, ai: number): { absolute: number; percentage: number } => {
    const absolute = traditional - ai;
    const percentage = ((absolute / traditional) * 100);
    return { absolute, percentage };
  };

  const getProgressWidth = (percentage: number): string => {
    return `${(percentage * animationProgress) / 100}%`;
  };

  const MetricCard = ({ 
    icon: Icon, 
    title, 
    traditionalValue, 
    aiValue, 
    formatter = (val: any) => val.toString(),
    isInverse = false 
  }: {
    icon: any;
    title: string;
    traditionalValue: number;
    aiValue: number;
    formatter?: (val: any) => string;
    isInverse?: boolean;
  }) => {
    const savings = calculateSavings(traditionalValue, aiValue);
    const improvement = isInverse ? -savings.percentage : savings.percentage;

    return (
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
        <div className="flex items-center justify-between mb-4">
          <Icon className="w-8 h-8 text-blue-400" />
          <div className={`text-sm font-medium px-2 py-1 rounded-full ${
            improvement > 0 
              ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
              : improvement < 0 
              ? 'bg-red-500/20 text-red-300 border border-red-500/30'
              : 'bg-gray-500/20 text-gray-300 border border-gray-500/30'
          }`}>
            {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
          </div>
        </div>
        
        <h4 className="text-white font-semibold mb-4">{title}</h4>
        
        {/* Traditional Approach */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-300 flex items-center">
              <Phone className="w-4 h-4 mr-1" />
              Traditional
            </span>
            <span className="text-red-300 font-bold">{formatter(traditionalValue)}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-red-500 to-red-600 h-2 rounded-full transition-all duration-2000"
              style={{ width: getProgressWidth(100) }}
            ></div>
          </div>
        </div>

        {/* AI-Enhanced Approach */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-300 flex items-center">
              <Bot className="w-4 h-4 mr-1" />
              AI-Enhanced
            </span>
            <span className="text-green-300 font-bold">{formatter(aiValue)}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-green-400 to-green-500 h-2 rounded-full transition-all duration-2000"
              style={{ width: getProgressWidth((aiValue / traditionalValue) * 100) }}
            ></div>
          </div>
        </div>

        {/* Improvement */}
        <div className="pt-3 border-t border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Improvement</span>
            <div className="flex items-center space-x-1">
              {improvement > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span className={`text-sm font-bold ${improvement > 0 ? 'text-green-300' : 'text-red-300'}`}>
                {Math.abs(improvement).toFixed(1)}% {improvement > 0 ? 'better' : 'worse'}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const totalTraditionalCost = traditionalMetrics.costPerPassenger * passengerCount;
  const totalAICost = aiMetrics.costPerPassenger * passengerCount;
  const totalSavings = calculateSavings(totalTraditionalCost, totalAICost);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-4">
          Traditional vs AI-Enhanced Disruption Management
        </h2>
        <p className="text-gray-300 max-w-2xl mx-auto">
          Real-world comparison of manual processes vs autonomous agentic intelligence for managing 
          {' '}{passengerCount} passengers in a complexity {scenarioComplexity}/10 disruption scenario.
        </p>
      </div>

      {/* High-Level Impact Summary */}
      <div className="bg-gradient-to-r from-green-600/20 to-emerald-700/20 rounded-2xl p-6 border border-green-400/30 mb-8">
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-white mb-2">Executive Impact Summary</h3>
          <p className="text-green-300">AI-Enhanced Autonomous Intelligence delivers transformational results</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              £{(totalSavings.absolute / 1000).toFixed(0)}K
            </div>
            <div className="text-sm text-green-300">Total Cost Savings</div>
            <div className="text-xs text-gray-400 mt-1">
              {totalSavings.percentage.toFixed(1)}% reduction
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              {((traditionalMetrics.resolutionTime - aiMetrics.resolutionTime) / 60).toFixed(1)}h
            </div>
            <div className="text-sm text-blue-300">Time Saved</div>
            <div className="text-xs text-gray-400 mt-1">
              {(((traditionalMetrics.resolutionTime - aiMetrics.resolutionTime) / traditionalMetrics.resolutionTime) * 100).toFixed(1)}% faster
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              +{(aiMetrics.satisfactionScore - traditionalMetrics.satisfactionScore).toFixed(1)}
            </div>
            <div className="text-sm text-purple-300">Satisfaction Boost</div>
            <div className="text-xs text-gray-400 mt-1">
              {((((aiMetrics.satisfactionScore - traditionalMetrics.satisfactionScore) / traditionalMetrics.satisfactionScore) * 100)).toFixed(1)}% improvement
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              {((aiMetrics.automationRate - traditionalMetrics.automationRate)).toFixed(0)}%
            </div>
            <div className="text-sm text-orange-300">More Automation</div>
            <div className="text-xs text-gray-400 mt-1">
              Reduced manual work
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Metrics Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard
          icon={Clock}
          title="Resolution Time"
          traditionalValue={traditionalMetrics.resolutionTime}
          aiValue={aiMetrics.resolutionTime}
          formatter={formatTime}
        />
        
        <MetricCard
          icon={DollarSign}
          title="Cost per Passenger"
          traditionalValue={traditionalMetrics.costPerPassenger}
          aiValue={aiMetrics.costPerPassenger}
          formatter={formatCurrency}
        />
        
        <MetricCard
          icon={TrendingUp}
          title="Customer Satisfaction"
          traditionalValue={traditionalMetrics.satisfactionScore}
          aiValue={aiMetrics.satisfactionScore}
          formatter={(val) => `${val.toFixed(1)}/5`}
          isInverse={true}
        />
        
        <MetricCard
          icon={Bot}
          title="Automation Rate"
          traditionalValue={traditionalMetrics.automationRate}
          aiValue={aiMetrics.automationRate}
          formatter={(val) => `${val}%`}
          isInverse={true}
        />
        
        <MetricCard
          icon={Users}
          title="Staff Required"
          traditionalValue={traditionalMetrics.staffRequired}
          aiValue={aiMetrics.staffRequired}
          formatter={(val) => `${val} people`}
        />
        
        <MetricCard
          icon={AlertTriangle}
          title="Error Rate"
          traditionalValue={traditionalMetrics.errorRate}
          aiValue={aiMetrics.errorRate}
          formatter={(val) => `${val.toFixed(1)}%`}
        />
      </div>

      {/* Process Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traditional Process */}
        <div className="bg-red-600/10 backdrop-blur-xl rounded-2xl p-6 border border-red-400/30">
          <div className="flex items-center space-x-3 mb-4">
            <Phone className="w-8 h-8 text-red-400" />
            <h3 className="text-xl font-bold text-white">Traditional Manual Process</h3>
          </div>
          <div className="space-y-3">
            {[
              { step: 'Passengers call overloaded call center', time: '45min wait', status: 'negative' },
              { step: 'Manual rebooking with limited visibility', time: '30min each', status: 'negative' },
              { step: 'Hotel booking via phone calls', time: '25min each', status: 'negative' },
              { step: 'Manual compensation calculation', time: '20min each', status: 'negative' },
              { step: 'Multiple follow-up calls required', time: '15min each', status: 'negative' },
              { step: 'Escalation to supervisors', time: '+60min', status: 'negative' },
            ].map((item, index) => (
              <div key={index} className="flex items-center space-x-3 py-2">
                <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                <div className="flex-1">
                  <span className="text-white text-sm">{item.step}</span>
                  <div className="text-red-300 text-xs">{item.time}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-red-400/30">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-300">{formatTime(traditionalMetrics.resolutionTime)}</div>
              <div className="text-sm text-gray-400">Average Total Time</div>
            </div>
          </div>
        </div>

        {/* AI-Enhanced Process */}
        <div className="bg-green-600/10 backdrop-blur-xl rounded-2xl p-6 border border-green-400/30">
          <div className="flex items-center space-x-3 mb-4">
            <Bot className="w-8 h-8 text-green-400" />
            <h3 className="text-xl font-bold text-white">AI-Enhanced Autonomous Process</h3>
          </div>
          <div className="space-y-3">
            {[
              { step: 'Proactive passenger notification', time: '2min', status: 'positive' },
              { step: 'Autonomous AI rebooking optimization', time: '3min', status: 'positive' },
              { step: 'Automated hotel & transport booking', time: '4min', status: 'positive' },
              { step: 'AI-calculated compensation processing', time: '1min', status: 'positive' },
              { step: 'Real-time status updates via app', time: 'Instant', status: 'positive' },
              { step: 'Self-service options with AI assistance', time: '2min', status: 'positive' },
            ].map((item, index) => (
              <div key={index} className="flex items-center space-x-3 py-2">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <div className="flex-1">
                  <span className="text-white text-sm">{item.step}</span>
                  <div className="text-green-300 text-xs">{item.time}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-green-400/30">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-300">{formatTime(aiMetrics.resolutionTime)}</div>
              <div className="text-sm text-gray-400">Average Total Time</div>
            </div>
          </div>
        </div>
      </div>

      {/* ROI Analysis */}
      <div className="bg-gradient-to-r from-purple-600/20 to-pink-700/20 rounded-2xl p-6 border border-purple-400/30">
        <h3 className="text-xl font-bold text-white mb-4 text-center">Return on Investment Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-300 mb-1">£{((totalSavings.absolute * 12) / 1000).toFixed(0)}K</div>
            <div className="text-sm text-white">Annual Savings Potential</div>
            <div className="text-xs text-gray-400">Based on monthly disruptions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-pink-300 mb-1">{traditionalMetrics.staffRequired - aiMetrics.staffRequired}</div>
            <div className="text-sm text-white">FTE Reduction</div>
            <div className="text-xs text-gray-400">Redeployed to higher-value work</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-300 mb-1">{(((aiMetrics.satisfactionScore - traditionalMetrics.satisfactionScore) / traditionalMetrics.satisfactionScore) * 100).toFixed(0)}%</div>
            <div className="text-sm text-white">Customer Loyalty Impact</div>
            <div className="text-xs text-gray-400">Satisfaction improvement</div>
          </div>
        </div>
      </div>
    </div>
  );
}