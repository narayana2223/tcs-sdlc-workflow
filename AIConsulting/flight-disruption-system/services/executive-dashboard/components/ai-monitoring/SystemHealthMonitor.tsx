'use client';

import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  Cpu, 
  HardDrive, 
  Wifi, 
  Zap, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  Server,
  Database,
  Cloud,
  Shield
} from 'lucide-react';

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage?: number;
  networkLatency: number;
  throughput: number;
  errorRate: number;
  uptime: number;
}

interface SystemHealthMonitorProps {
  systemMetrics: SystemMetrics;
}

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'warning' | 'critical' | 'down';
  responseTime: number;
  uptime: number;
  errorRate: number;
  lastCheck: Date;
  description: string;
}

const mockServiceHealth: ServiceHealth[] = [
  {
    name: 'Prediction Engine',
    status: 'healthy',
    responseTime: 180,
    uptime: 99.94,
    errorRate: 0.02,
    lastCheck: new Date(),
    description: 'ML model inference and prediction processing'
  },
  {
    name: 'Agent Orchestrator',
    status: 'healthy',
    responseTime: 120,
    uptime: 99.97,
    errorRate: 0.01,
    lastCheck: new Date(),
    description: 'LangGraph multi-agent coordination system'
  },
  {
    name: 'Database Cluster',
    status: 'warning',
    responseTime: 450,
    uptime: 99.85,
    errorRate: 0.15,
    lastCheck: new Date(),
    description: 'PostgreSQL primary and read replicas'
  },
  {
    name: 'Redis Cache',
    status: 'healthy',
    responseTime: 15,
    uptime: 99.99,
    errorRate: 0.00,
    lastCheck: new Date(),
    description: 'In-memory caching and session storage'
  },
  {
    name: 'Kafka Streams',
    status: 'healthy',
    responseTime: 85,
    uptime: 99.92,
    errorRate: 0.03,
    lastCheck: new Date(),
    description: 'Real-time event streaming and processing'
  },
  {
    name: 'External APIs',
    status: 'critical',
    responseTime: 2500,
    uptime: 98.12,
    errorRate: 1.25,
    lastCheck: new Date(),
    description: 'Weather, airline PSS, and vendor integrations'
  }
];

const performanceHistory = {
  labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'],
  cpu: [45, 52, 68, 75, 72, 65, 72],
  memory: [60, 58, 65, 70, 68, 64, 68],
  network: [25, 30, 45, 55, 50, 40, 45],
  throughput: [1800, 2100, 2800, 3200, 2900, 2400, 2847]
};

export default function SystemHealthMonitor({ systemMetrics }: SystemHealthMonitorProps) {
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [alertThreshold, setAlertThreshold] = useState<'low' | 'medium' | 'high'>('medium');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const getStatusColor = (status: string) => {
    const colors = {
      healthy: 'green',
      warning: 'yellow',
      critical: 'red',
      down: 'slate'
    };
    return colors[status as keyof typeof colors] || 'slate';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      healthy: CheckCircle,
      warning: AlertTriangle,
      critical: XCircle,
      down: XCircle
    };
    return icons[status as keyof typeof icons] || CheckCircle;
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

  const getThresholdColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'red';
    if (value >= thresholds.warning) return 'yellow';
    return 'green';
  };

  const renderSystemOverview = () => {
    const cpuThresholds = { warning: 70, critical: 85 };
    const memoryThresholds = { warning: 75, critical: 90 };
    const latencyThresholds = { warning: 200, critical: 500 };
    const errorThresholds = { warning: 0.5, critical: 1.0 };

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* CPU Usage */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <span className="font-medium text-slate-800">CPU Usage</span>
            </div>
            <span className={`text-sm font-semibold ${
              getColorClass(getThresholdColor(systemMetrics.cpuUsage, cpuThresholds), 'text')
            }`}>
              {systemMetrics.cpuUsage}%
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-1000 ${
                getColorClass(getThresholdColor(systemMetrics.cpuUsage, cpuThresholds))
              }`}
              style={{ width: `${systemMetrics.cpuUsage}%` }}
            ></div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-5 h-5 text-green-500" />
              <span className="font-medium text-slate-800">Memory</span>
            </div>
            <span className={`text-sm font-semibold ${
              getColorClass(getThresholdColor(systemMetrics.memoryUsage, memoryThresholds), 'text')
            }`}>
              {systemMetrics.memoryUsage}%
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-1000 ${
                getColorClass(getThresholdColor(systemMetrics.memoryUsage, memoryThresholds))
              }`}
              style={{ width: `${systemMetrics.memoryUsage}%` }}
            ></div>
          </div>
        </div>

        {/* Network Latency */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Wifi className="w-5 h-5 text-orange-500" />
              <span className="font-medium text-slate-800">Latency</span>
            </div>
            <span className={`text-sm font-semibold ${
              getColorClass(getThresholdColor(systemMetrics.networkLatency, latencyThresholds), 'text')
            }`}>
              {systemMetrics.networkLatency}ms
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-1000 ${
                getColorClass(getThresholdColor(systemMetrics.networkLatency, latencyThresholds))
              }`}
              style={{ width: `${Math.min(systemMetrics.networkLatency / 5, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Error Rate */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="font-medium text-slate-800">Error Rate</span>
            </div>
            <span className={`text-sm font-semibold ${
              getColorClass(getThresholdColor(systemMetrics.errorRate, errorThresholds), 'text')
            }`}>
              {systemMetrics.errorRate}%
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-1000 ${
                getColorClass(getThresholdColor(systemMetrics.errorRate, errorThresholds))
              }`}
              style={{ width: `${Math.min(systemMetrics.errorRate * 20, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>
    );
  };

  const renderServiceHealth = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center space-x-2">
            <Server className="w-5 h-5" />
            <span>Service Health</span>
          </h3>
          
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span>Auto-refresh</span>
            </label>
          </div>
        </div>

        <div className="space-y-3">
          {mockServiceHealth.map((service) => {
            const StatusIcon = getStatusIcon(service.status);
            const statusColor = getStatusColor(service.status);
            
            return (
              <div
                key={service.name}
                onClick={() => setSelectedService(
                  selectedService === service.name ? null : service.name
                )}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedService === service.name 
                    ? 'border-blue-200 bg-blue-50' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 ${getColorClass(statusColor)} bg-opacity-20 rounded-lg`}>
                      <StatusIcon className={`w-4 h-4 ${getColorClass(statusColor, 'text')}`} />
                    </div>
                    <div>
                      <h4 className="font-medium text-slate-800">{service.name}</h4>
                      <p className="text-sm text-slate-600">{service.description}</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={`text-sm font-semibold ${getColorClass(statusColor, 'text')} capitalize`}>
                      {service.status}
                    </div>
                    <div className="text-xs text-slate-500">
                      {service.responseTime}ms
                    </div>
                  </div>
                </div>

                {selectedService === service.name && (
                  <div className="mt-4 pt-4 border-t border-slate-200">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Uptime:</span>
                        <span className="ml-2 font-medium">{service.uptime}%</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Error Rate:</span>
                        <span className="ml-2 font-medium">{service.errorRate}%</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Last Check:</span>
                        <span className="ml-2 font-medium">
                          {service.lastCheck.toLocaleTimeString()}
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

  const renderPerformanceChart = () => {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Activity className="w-5 h-5" />
          <span>Performance Trends</span>
        </h3>

        <div className="space-y-6">
          {/* CPU Trend */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">CPU Usage (%)</span>
              <span className="text-sm text-slate-600">Current: {systemMetrics.cpuUsage}%</span>
            </div>
            <div className="space-y-1">
              {performanceHistory.cpu.map((value, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="text-xs text-slate-500 w-12">
                    {performanceHistory.labels[index]}
                  </span>
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${
                        index === performanceHistory.cpu.length - 1 
                          ? 'bg-blue-500' 
                          : 'bg-slate-400'
                      }`}
                      style={{ 
                        width: `${value}%`,
                        animationDelay: `${index * 100}ms`
                      }}
                    ></div>
                  </div>
                  <span className="text-xs text-slate-600 w-8">{value}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Throughput Trend */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Throughput (events/sec)</span>
              <span className="text-sm text-slate-600">Current: {systemMetrics.throughput}/s</span>
            </div>
            <div className="space-y-1">
              {performanceHistory.throughput.map((value, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="text-xs text-slate-500 w-12">
                    {performanceHistory.labels[index]}
                  </span>
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${
                        index === performanceHistory.throughput.length - 1 
                          ? 'bg-green-500' 
                          : 'bg-slate-400'
                      }`}
                      style={{ 
                        width: `${(value / 4000) * 100}%`,
                        animationDelay: `${index * 100}ms`
                      }}
                    ></div>
                  </div>
                  <span className="text-xs text-slate-600 w-12">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSystemInfo = () => {
    const healthyServices = mockServiceHealth.filter(s => s.status === 'healthy').length;
    const totalServices = mockServiceHealth.length;
    const systemScore = ((healthyServices / totalServices) * 100).toFixed(1);

    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <Monitor className="w-5 h-5" />
          <span>System Overview</span>
        </h3>

        <div className="space-y-4">
          {/* Overall Health Score */}
          <div className="text-center py-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-slate-800 mb-1">{systemScore}%</div>
            <div className="text-sm text-slate-600">System Health Score</div>
            <div className="text-xs text-slate-500 mt-1">
              {healthyServices} of {totalServices} services healthy
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Uptime</span>
              <span className="font-semibold text-green-600">{systemMetrics.uptime}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Throughput</span>
              <span className="font-semibold text-blue-600">{systemMetrics.throughput}/s</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">GPU Usage</span>
              <span className="font-semibold text-purple-600">
                {systemMetrics.gpuUsage || 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Error Rate</span>
              <span className={`font-semibold ${
                systemMetrics.errorRate < 0.5 ? 'text-green-600' : 'text-red-600'
              }`}>
                {systemMetrics.errorRate}%
              </span>
            </div>
          </div>

          {/* Resource Allocation */}
          <div className="pt-4 border-t border-slate-200">
            <h4 className="text-sm font-medium text-slate-700 mb-3">Resource Allocation</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">AI/ML Processing</span>
                <span className="font-medium">45%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Web Services</span>
                <span className="font-medium">25%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Data Processing</span>
                <span className="font-medium">20%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Monitoring</span>
                <span className="font-medium">10%</span>
              </div>
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
            <Monitor className="w-6 h-6" />
            <span>System Health Monitor</span>
          </h2>
          
          {/* Status indicator */}
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-slate-700">All Systems Operational</span>
          </div>
        </div>

        {/* System overview metrics */}
        {renderSystemOverview()}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left Column - Service Health */}
          <div className="xl:col-span-2">
            {renderServiceHealth()}
          </div>

          {/* Right Column - System Info and Performance */}
          <div className="space-y-6">
            {renderSystemInfo()}
            {renderPerformanceChart()}
          </div>
        </div>
      </div>
    </div>
  );
}