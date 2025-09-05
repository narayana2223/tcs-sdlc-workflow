'use client';

import React, { useEffect, useState } from 'react';
import { FinancialMetrics } from '@/types';
import { DollarSign, TrendingUp, TrendingDown, Shield, PiggyBank, Target, ArrowUp, ArrowDown } from 'lucide-react';

interface FinancialImpactPanelProps {
  metrics: FinancialMetrics;
}

export default function FinancialImpactPanel({ metrics }: FinancialImpactPanelProps) {
  const [animatedSavings, setAnimatedSavings] = useState(0);
  const [savingsChange, setSavingsChange] = useState(0);
  const [previousSavings, setPreviousSavings] = useState(0);

  useEffect(() => {
    setSavingsChange(metrics.totalCostSavings - previousSavings);
    setPreviousSavings(metrics.totalCostSavings);

    const increment = (metrics.totalCostSavings - animatedSavings) / 20;
    const timer = setInterval(() => {
      setAnimatedSavings(prev => {
        const newValue = prev + increment;
        if (Math.abs(newValue - metrics.totalCostSavings) < Math.abs(increment)) {
          clearInterval(timer);
          return metrics.totalCostSavings;
        }
        return newValue;
      });
    }, 50);

    return () => clearInterval(timer);
  }, [metrics.totalCostSavings]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatRate = (rate: number) => {
    if (rate >= 1000000) {
      return `£${(rate / 1000000).toFixed(1)}M/min`;
    } else if (rate >= 1000) {
      return `£${(rate / 1000).toFixed(1)}K/min`;
    }
    return `£${rate.toFixed(0)}/min`;
  };

  const getROIColor = (roi: number) => {
    if (roi >= 300) return 'text-success-600';
    if (roi >= 200) return 'text-warning-600';
    return 'text-danger-600';
  };

  return (
    <div className="space-y-6">
      {/* Main Cost Savings Counter */}
      <div className="card bg-gradient-to-r from-success-50 to-success-100 border-success-200">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-success-500 rounded-full text-white">
              <PiggyBank className="w-8 h-8" />
            </div>
          </div>
          <div className="mb-2">
            <div className="text-4xl font-bold text-success-700">
              {formatCurrency(animatedSavings)}
            </div>
            <div className="text-sm text-success-600">Total Cost Savings</div>
          </div>
          
          {savingsChange !== 0 && (
            <div className={`flex items-center justify-center space-x-1 text-sm ${savingsChange > 0 ? 'text-success-600' : 'text-danger-600'}`}>
              {savingsChange > 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
              <span>{formatCurrency(Math.abs(savingsChange))} this update</span>
            </div>
          )}

          <div className="mt-4 flex items-center justify-center space-x-2 text-lg font-semibold text-success-700">
            <TrendingUp className="w-5 h-5" />
            <span>{formatRate(metrics.savingsPerMinute)}</span>
          </div>
        </div>
      </div>

      {/* Key Financial Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Revenue Protected */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Shield className="w-5 h-5 text-primary-600" />
            </div>
            <TrendingUp className="w-4 h-4 text-success-500" />
          </div>
          <div className="text-2xl font-bold text-slate-800 mb-1">
            {formatCurrency(metrics.revenueProtected)}
          </div>
          <div className="text-sm text-slate-600">Revenue Protected</div>
        </div>

        {/* ROI */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
            <div className={`text-sm font-medium ${getROIColor(metrics.roi)}`}>
              {metrics.roi.toFixed(0)}%
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-800 mb-1">
            {(metrics.roi / 100).toFixed(1)}x
          </div>
          <div className="text-sm text-slate-600">Return on Investment</div>
        </div>

        {/* Compensation Paid */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-warning-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-warning-600" />
            </div>
            <TrendingDown className="w-4 h-4 text-warning-500" />
          </div>
          <div className="text-2xl font-bold text-slate-800 mb-1">
            {formatCurrency(metrics.compensationPaid)}
          </div>
          <div className="text-sm text-slate-600">Compensation Paid</div>
        </div>

        {/* Operational Costs */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-slate-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-slate-600" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-800 mb-1">
            {formatCurrency(metrics.operationalCosts)}
          </div>
          <div className="text-sm text-slate-600">Operational Costs</div>
        </div>
      </div>

      {/* Financial Breakdown Chart */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-slate-800">Financial Breakdown</h3>
        </div>
        
        <div className="space-y-4">
          {/* Cost Savings Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Cost Savings</span>
              <span className="text-sm font-semibold text-success-600">
                {formatCurrency(metrics.totalCostSavings)}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className="bg-success-500 h-3 rounded-full transition-all duration-1000"
                style={{ width: '100%' }}
              />
            </div>
          </div>

          {/* Revenue Protected Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Revenue Protected</span>
              <span className="text-sm font-semibold text-primary-600">
                {formatCurrency(metrics.revenueProtected)}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className="bg-primary-500 h-3 rounded-full transition-all duration-1000"
                style={{ width: `${Math.min(100, (metrics.revenueProtected / metrics.totalCostSavings) * 100)}%` }}
              />
            </div>
          </div>

          {/* Compensation Costs Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Compensation</span>
              <span className="text-sm font-semibold text-warning-600">
                {formatCurrency(metrics.compensationPaid)}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className="bg-warning-500 h-3 rounded-full transition-all duration-1000"
                style={{ width: `${Math.min(100, (metrics.compensationPaid / metrics.totalCostSavings) * 100)}%` }}
              />
            </div>
          </div>

          {/* Operational Costs Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Operations</span>
              <span className="text-sm font-semibold text-slate-600">
                {formatCurrency(metrics.operationalCosts)}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className="bg-slate-500 h-3 rounded-full transition-all duration-1000"
                style={{ width: `${Math.min(100, (metrics.operationalCosts / metrics.totalCostSavings) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div className="mt-6 p-4 bg-slate-50 rounded-lg">
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Key Insights</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-sm">
              <div className="text-slate-600">Efficiency Gain</div>
              <div className="font-semibold text-success-600">
                +{((metrics.roi - 100) / 100 * 100).toFixed(0)}%
              </div>
            </div>
            <div className="text-sm">
              <div className="text-slate-600">Cost Avoidance</div>
              <div className="font-semibold text-primary-600">
                {formatCurrency(metrics.totalCostSavings + metrics.revenueProtected)}
              </div>
            </div>
            <div className="text-sm">
              <div className="text-slate-600">Net Benefit</div>
              <div className="font-semibold text-success-600">
                {formatCurrency(metrics.totalCostSavings - metrics.compensationPaid - metrics.operationalCosts)}
              </div>
            </div>
            <div className="text-sm">
              <div className="text-slate-600">Savings Rate</div>
              <div className="font-semibold text-purple-600">
                {formatRate(metrics.savingsPerMinute)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}