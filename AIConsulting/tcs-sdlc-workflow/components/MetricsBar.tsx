'use client';

import { useWorkflowStore } from '@/lib/store';
import workflowsData from '@/data/workflows.json';
import { Clock, Users, TrendingUp, Zap, DollarSign, Activity } from 'lucide-react';

export function MetricsBar() {
  const { maturityLevel } = useWorkflowStore();

  const metrics = workflowsData[maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5'].totalMetrics;

  const metricsConfig = [
    {
      icon: Clock,
      label: 'Total Duration',
      value: metrics.duration,
      color: 'text-blue-600',
    },
    {
      icon: Users,
      label: 'Human Gates',
      value: metrics.humanTouchpoints.toString(),
      color: 'text-purple-600',
    },
    {
      icon: TrendingUp,
      label: 'Time Saved',
      value: metrics.timeSaved,
      color: 'text-green-600',
    },
    {
      icon: Zap,
      label: 'Deploys/Week',
      value: metrics.deploymentFrequency,
      color: 'text-orange-600',
    },
    {
      icon: Activity,
      label: 'MTTR',
      value: metrics.mttr,
      color: 'text-red-600',
    },
    {
      icon: DollarSign,
      label: 'Annual Savings',
      value: metrics.annualSavings,
      color: 'text-emerald-600',
    },
  ];

  return (
    <div className="border-t bg-gradient-to-r from-gray-50 to-white py-6">
      <div className="container px-8">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase text-gray-600">
            {maturityLevel} Performance Metrics
          </h3>
          <p className="text-sm text-gray-500">
            ROI: <span className="font-bold text-green-600">{metrics.roi}</span>
          </p>
        </div>
        <div className="grid grid-cols-6 gap-4">
          {metricsConfig.map((metric, index) => (
            <div
              key={index}
              className="flex flex-col items-center rounded-lg bg-white p-4 shadow-sm"
            >
              <metric.icon className={`mb-2 ${metric.color}`} size={24} />
              <p className="text-xs text-gray-600">{metric.label}</p>
              <p className="mt-1 text-lg font-bold text-gray-900">
                {metric.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
