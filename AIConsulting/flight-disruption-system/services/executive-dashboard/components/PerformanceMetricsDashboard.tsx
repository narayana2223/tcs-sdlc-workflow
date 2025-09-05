'use client';

import React from 'react';
import { PerformanceMetrics } from '@/types';
import { Activity, Clock, Target, Zap, TrendingUp, CheckCircle, BarChart3, Gauge } from 'lucide-react';

interface PerformanceMetricsDashboardProps {
  metrics: PerformanceMetrics;
}

export default function PerformanceMetricsDashboard({ metrics }: PerformanceMetricsDashboardProps) {
  const getPerformanceColor = (value: number, thresholds: { excellent: number; good: number }) => {
    if (value >= thresholds.excellent) return 'success';
    if (value >= thresholds.good) return 'warning';
    return 'danger';
  };

  const formatUptime = (uptime: number) => {
    const uptimePercentage = uptime * 100;
    return `${uptimePercentage.toFixed(2)}%`;
  };

  const formatResponseTime = (time: number) => {
    if (time < 1000) return `${Math.round(time)}ms`;
    return `${(time / 1000).toFixed(2)}s`;
  };

  // Performance thresholds
  const thresholds = {
    accuracy: { excellent: 95, good: 85 },
    responseTime: { excellent: 1000, good: 2000 }, // in ms (lower is better)
    uptime: { excellent: 99.9, good: 99.0 },
    efficiency: { excellent: 90, good: 75 },
    successRate: { excellent: 95, good: 85 }
  };

  const CircularProgress = ({ value, max, color, size = 120 }: { value: number; max: number; color: string; size?: number }) => {
    const percentage = Math.min((value / max) * 100, 100);
    const circumference = 2 * Math.PI * 45;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="transform -rotate-90"
          width={size}
          height={size}
          viewBox="0 0 100 100"
        >
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="transparent"
            stroke="#e2e8f0"
            strokeWidth="6"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="transparent"
            stroke={color === 'success' ? '#22c55e' : color === 'warning' ? '#f59e0b' : '#ef4444'}
            strokeWidth="6"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-slate-800">
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-slate-800 flex items-center space-x-2">
            <Activity className="w-6 h-6" />
            <span>System Performance Overview</span>
          </h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Prediction Accuracy */}
          <div className="text-center">
            <CircularProgress
              value={metrics.predictionsAccuracy}
              max={100}
              color={getPerformanceColor(metrics.predictionsAccuracy, thresholds.accuracy)}
            />
            <div className="mt-3">
              <div className="text-sm font-medium text-slate-700">Prediction Accuracy</div>
              <div className={`text-xs status-badge status-${getPerformanceColor(metrics.predictionsAccuracy, thresholds.accuracy)}`}>
                {metrics.predictionsAccuracy >= thresholds.accuracy.excellent ? 'Excellent' : 
                 metrics.predictionsAccuracy >= thresholds.accuracy.good ? 'Good' : 'Needs Attention'}
              </div>
            </div>
          </div>

          {/* System Uptime */}
          <div className="text-center">
            <CircularProgress
              value={metrics.systemUptime * 100}
              max={100}
              color={getPerformanceColor(metrics.systemUptime * 100, thresholds.uptime)}
            />
            <div className="mt-3">
              <div className="text-sm font-medium text-slate-700">System Uptime</div>
              <div className={`text-xs status-badge status-${getPerformanceColor(metrics.systemUptime * 100, thresholds.uptime)}`}>
                {formatUptime(metrics.systemUptime)}
              </div>
            </div>
          </div>

          {/* Agent Efficiency */}
          <div className="text-center">
            <CircularProgress
              value={metrics.agentEfficiency}
              max={100}
              color={getPerformanceColor(metrics.agentEfficiency, thresholds.efficiency)}
            />
            <div className="mt-3">
              <div className="text-sm font-medium text-slate-700">Agent Efficiency</div>
              <div className={`text-xs status-badge status-${getPerformanceColor(metrics.agentEfficiency, thresholds.efficiency)}`}>
                {metrics.agentEfficiency.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Success Rate */}
          <div className="text-center">
            <CircularProgress
              value={metrics.successRate}
              max={100}
              color={getPerformanceColor(metrics.successRate, thresholds.successRate)}
            />
            <div className="mt-3">
              <div className="text-sm font-medium text-slate-700">Success Rate</div>
              <div className={`text-xs status-badge status-${getPerformanceColor(metrics.successRate, thresholds.successRate)}`}>
                {metrics.successRate.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Response Time Metrics */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span>Response Time</span>
            </h3>
          </div>

          <div className="text-center mb-6">
            <div className="text-4xl font-bold text-primary-600 mb-2">
              {formatResponseTime(metrics.responseTime)}
            </div>
            <div className="text-sm text-slate-600">Average Response Time</div>
          </div>

          {/* Response Time Gauge */}
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">Target: &lt;1s</span>
              <span className={`font-medium ${
                metrics.responseTime < 1000 ? 'text-success-600' : 
                metrics.responseTime < 2000 ? 'text-warning-600' : 'text-danger-600'
              }`}>
                {metrics.responseTime < 1000 ? '✓ Excellent' : 
                 metrics.responseTime < 2000 ? '⚠ Good' : '⚠ Slow'}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-4">
              <div 
                className={`h-4 rounded-full transition-all duration-1000 ${
                  metrics.responseTime < 1000 ? 'bg-success-500' : 
                  metrics.responseTime < 2000 ? 'bg-warning-500' : 'bg-danger-500'
                }`}
                style={{ width: `${Math.min(100, (metrics.responseTime / 3000) * 100)}%` }}
              />
            </div>
            <div className="grid grid-cols-3 text-xs text-slate-600">
              <div>0ms</div>
              <div className="text-center">1.5s</div>
              <div className="text-right">3s+</div>
            </div>
          </div>
        </div>

        {/* Disruptions Handled */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center space-x-2">
              <BarChart3 className="w-5 h-5" />
              <span>Activity Volume</span>
            </h3>
          </div>

          <div className="text-center mb-6">
            <div className="text-4xl font-bold text-purple-600 mb-2">
              {metrics.disruptionsHandled.toLocaleString()}
            </div>
            <div className="text-sm text-slate-600">Disruptions Handled</div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Total Processed</span>
              </div>
              <span className="text-sm font-bold text-purple-700">
                {metrics.disruptionsHandled.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-success-600" />
                <span className="text-sm font-medium text-success-700">Successful</span>
              </div>
              <span className="text-sm font-bold text-success-700">
                {Math.round((metrics.successRate / 100) * metrics.disruptionsHandled).toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-slate-600" />
                <span className="text-sm font-medium text-slate-700">Processing Rate</span>
              </div>
              <span className="text-sm font-bold text-slate-700">
                {Math.round(metrics.disruptionsHandled / 24)}/hour
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Trends */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center space-x-2">
            <Gauge className="w-5 h-5" />
            <span>Performance Benchmarks</span>
          </h3>
        </div>

        <div className="space-y-6">
          {/* Prediction Accuracy Trend */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Prediction Accuracy</span>
              <span className="text-sm font-bold text-slate-800">
                {metrics.predictionsAccuracy.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all duration-1000 ${
                  metrics.predictionsAccuracy >= 95 ? 'bg-success-500' : 
                  metrics.predictionsAccuracy >= 85 ? 'bg-warning-500' : 'bg-danger-500'
                }`}
                style={{ width: `${Math.min(100, metrics.predictionsAccuracy)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0%</span>
              <span>Target: 95%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Agent Efficiency */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Agent Efficiency</span>
              <span className="text-sm font-bold text-slate-800">
                {metrics.agentEfficiency.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all duration-1000 ${
                  metrics.agentEfficiency >= 90 ? 'bg-success-500' : 
                  metrics.agentEfficiency >= 75 ? 'bg-warning-500' : 'bg-danger-500'
                }`}
                style={{ width: `${Math.min(100, metrics.agentEfficiency)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0%</span>
              <span>Target: 90%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Success Rate */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Success Rate</span>
              <span className="text-sm font-bold text-slate-800">
                {metrics.successRate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all duration-1000 ${
                  metrics.successRate >= 95 ? 'bg-success-500' : 
                  metrics.successRate >= 85 ? 'bg-warning-500' : 'bg-danger-500'
                }`}
                style={{ width: `${Math.min(100, metrics.successRate)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0%</span>
              <span>Target: 95%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="mt-6 p-4 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-semibold text-slate-800 mb-3">System Health Summary</h4>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`text-lg font-bold ${
                metrics.systemUptime >= 0.999 ? 'text-success-600' : 'text-warning-600'
              }`}>
                {formatUptime(metrics.systemUptime)}
              </div>
              <div className="text-xs text-slate-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-primary-600">
                {formatResponseTime(metrics.responseTime)}
              </div>
              <div className="text-xs text-slate-600">Response</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-purple-600">
                {Math.round(metrics.disruptionsHandled / 24)}
              </div>
              <div className="text-xs text-slate-600">Per Hour</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-success-600">
                {((metrics.predictionsAccuracy + metrics.agentEfficiency + metrics.successRate) / 3).toFixed(1)}%
              </div>
              <div className="text-xs text-slate-600">Overall</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}