'use client';

import { useWorkflowStore } from '@/lib/store';
import costData from '@/data/cost-metrics.json';
import { DataSourceBadge } from '@/components/DataSourceBadge';
import { DollarSign, TrendingUp, TrendingDown, PieChart, BarChart3, Zap, AlertCircle } from 'lucide-react';

export default function CostManagementPage() {
  const { maturityLevel } = useWorkflowStore();
  const level = maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5';

  const cost = costData[level];
  const budgetAlerts = costData.budgetAlerts;
  const optimization = costData.costOptimizationStrategies;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Cost Management & Optimization</h1>
              <p className="mt-2 text-gray-600">
                Comprehensive AI spend tracking, forecasting, and optimization for {maturityLevel}
              </p>
            </div>
            <div className="text-xs text-gray-500">
              Hover over badges for data sources
            </div>
          </div>
        </div>

        {/* Key Cost Metrics */}
        <div className="mb-8 grid grid-cols-4 gap-6">
          <MetricCard
            icon={DollarSign}
            label="Daily Spend"
            value={`$${cost.dailySpend.toLocaleString()}`}
            color="blue"
            trend={`${Math.round((cost.dailySpend / budgetAlerts.daily.threshold) * 100)}% of budget`}
            positive={cost.dailySpend < budgetAlerts.daily.threshold}
          />
          <MetricCard
            icon={TrendingUp}
            label="Monthly Forecast"
            value={`$${cost.monthlyForecast.toLocaleString()}`}
            color="purple"
            trend={`${Math.round((cost.monthlyForecast / budgetAlerts.monthly.threshold) * 100)}% of budget`}
            positive={cost.monthlyForecast < budgetAlerts.monthly.threshold}
          />
          <MetricCard
            icon={TrendingDown}
            label="Annual Savings"
            value={`$${(cost.savingsVsTraditional / 1000000).toFixed(1)}M`}
            color="green"
            trend={`ROI: ${cost.roiPercentage}%`}
            positive={true}
          />
          <MetricCard
            icon={Zap}
            label="Cost per Developer"
            value={`$${cost.costPerDeveloper}/day`}
            color="orange"
            trend={`$${(cost.costPerDeveloper * 20).toLocaleString()}/month`}
            positive={true}
          />
        </div>

        {/* Budget Status */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="text-blue-600" size={28} />
              Budget Status
            </h2>
            <DataSourceBadge type="sample" tooltip="Sample budget thresholds. Configure actual daily/monthly budgets for your organization." />
          </div>

          <div className="grid grid-cols-2 gap-8">
            {/* Daily Budget */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold text-gray-700">Daily Budget</div>
                <div className={`text-sm font-bold ${
                  budgetAlerts.daily.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {budgetAlerts.daily.status.toUpperCase()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                <div
                  className={`h-4 rounded-full transition-all ${
                    budgetAlerts.daily.currentSpend / budgetAlerts.daily.threshold < 0.8
                      ? 'bg-green-500'
                      : budgetAlerts.daily.currentSpend / budgetAlerts.daily.threshold < 0.95
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((budgetAlerts.daily.currentSpend / budgetAlerts.daily.threshold) * 100, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>${budgetAlerts.daily.currentSpend.toLocaleString()} spent</span>
                <span>${budgetAlerts.daily.threshold.toLocaleString()} budget</span>
              </div>
            </div>

            {/* Monthly Budget */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold text-gray-700">Monthly Budget</div>
                <div className={`text-sm font-bold ${
                  budgetAlerts.monthly.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {budgetAlerts.monthly.status.toUpperCase()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                <div
                  className={`h-4 rounded-full transition-all ${
                    budgetAlerts.monthly.currentProjection / budgetAlerts.monthly.threshold < 0.8
                      ? 'bg-green-500'
                      : budgetAlerts.monthly.currentProjection / budgetAlerts.monthly.threshold < 0.95
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((budgetAlerts.monthly.currentProjection / budgetAlerts.monthly.threshold) * 100, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>${budgetAlerts.monthly.currentProjection.toLocaleString()} projected</span>
                <span>${budgetAlerts.monthly.threshold.toLocaleString()} budget</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tool Cost Breakdown */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <PieChart className="text-purple-600" size={28} />
              Cost Breakdown by Tool
            </h2>
            <DataSourceBadge type="research" tooltip="Based on actual tool pricing (Cursor $20, Devin $500, etc.) and your team size across maturity levels." />
          </div>

          <div className="space-y-3">
            {cost.toolCosts
              .filter(t => t.category !== 'savings' && t.dailyCost > 0)
              .sort((a, b) => b.dailyCost - a.dailyCost)
              .map((tool) => {
                const percentage = (tool.dailyCost / cost.toolCosts.filter(t => t.category !== 'savings' && t.dailyCost > 0).reduce((sum, t) => sum + t.dailyCost, 0)) * 100;
                return (
                  <div key={tool.tool} className="border border-gray-200 rounded-lg p-4 hover:border-[#E94B3C] transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold text-gray-900">{tool.tool}</div>
                        <div className="text-sm text-gray-600 capitalize">{tool.category.replace(/-/g, ' ')}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">${tool.dailyCost}/day</div>
                        <div className="text-sm text-gray-600">${tool.monthlyCost}/mo</div>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{tool.usage}</span>
                      <span className="font-semibold text-green-600">{tool.roi}</span>
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Savings */}
          <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-green-900">Reduced Manual Labor Costs</div>
                <div className="text-xs text-green-700 mt-1">{cost.efficiency}</div>
              </div>
              <div className="text-3xl font-bold text-green-600">
                -${Math.abs(cost.toolCosts.find(t => t.category === 'savings')?.dailyCost || 0).toLocaleString()}/day
              </div>
            </div>
          </div>
        </div>

        {/* Cost Attribution */}
        {cost.costAttribution && (
          <div className="mb-8 grid grid-cols-2 gap-8">
            {/* By Team */}
            {cost.costAttribution.byTeam && (
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-900">Cost by Team</h2>
                  <DataSourceBadge type="sample" tooltip="Sample cost attribution by team. Connect to actual usage tracking for real data." />
                </div>
                <div className="space-y-3">
                  {Object.entries(cost.costAttribution.byTeam).map(([team, data]: [string, any]) => (
                    <div key={team} className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="capitalize font-medium text-gray-700">{team}</div>
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all"
                            style={{ width: `${data.percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="ml-4 text-sm font-semibold text-gray-900">
                        ${data.daily}/day ({data.percentage}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* By Project */}
            {cost.costAttribution.byProject && (
              <div className="rounded-lg bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-900">Cost by Project</h2>
                  <DataSourceBadge type="sample" tooltip="Sample cost attribution by project. Connect to project tracking for real data." />
                </div>
                <div className="space-y-3">
                  {Object.entries(cost.costAttribution.byProject).map(([project, data]: [string, any]) => (
                    <div key={project} className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="capitalize font-medium text-gray-700">{project.replace(/_/g, ' ')}</div>
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full transition-all"
                            style={{ width: `${data.percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="ml-4 text-sm font-semibold text-gray-900">
                        ${data.daily}/day ({data.percentage}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Cost Optimization Strategies */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Zap className="text-orange-600" size={28} />
              Cost Optimization Strategies
            </h2>
            <DataSourceBadge type="benchmark" tooltip="Standard enterprise cost optimization tactics. Savings potential based on industry benchmarks." />
          </div>

          <div className="grid grid-cols-3 gap-6">
            {/* Multi-Model Routing */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`h-3 w-3 rounded-full ${optimization.multiModelRouting.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div className="font-semibold text-gray-900">Multi-Model Routing</div>
              </div>
              <div className="text-sm text-gray-600 mb-3">{optimization.multiModelRouting.strategy}</div>
              <div className="text-xs text-green-600 font-semibold">{optimization.multiModelRouting.savingsPotential}</div>
            </div>

            {/* Caching */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`h-3 w-3 rounded-full ${optimization.caching.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div className="font-semibold text-gray-900">Response Caching</div>
              </div>
              <div className="text-sm text-gray-600 mb-3">
                {optimization.caching.strategy}
                <div className="mt-2 text-xs">Hit Rate: {optimization.caching.hitRate}%</div>
              </div>
              <div className="text-xs text-green-600 font-semibold">{optimization.caching.savingsPotential}</div>
            </div>

            {/* Batch Processing */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`h-3 w-3 rounded-full ${optimization.batchProcessing.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div className="font-semibold text-gray-900">Batch Processing</div>
              </div>
              <div className="text-sm text-gray-600 mb-3">{optimization.batchProcessing.strategy}</div>
              <div className="text-xs text-green-600 font-semibold">{optimization.batchProcessing.savingsPotential}</div>
            </div>
          </div>
        </div>

        {/* Vendor Negotiations */}
        {cost.vendorNegotiations && (
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <AlertCircle className="text-blue-600" size={28} />
                Vendor Optimization Opportunities
              </h2>
              <DataSourceBadge type="sample" tooltip="Example vendor negotiation opportunities. Actual savings vary based on your contract terms." />
            </div>

            <div className="space-y-4">
              {cost.vendorNegotiations.volumeDiscounts && Object.entries(cost.vendorNegotiations.volumeDiscounts).map(([vendor, data]: [string, any]) => (
                <div key={vendor} className="border border-blue-200 bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-900 capitalize">{vendor}</div>
                    <span className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Optimization Available
                    </span>
                  </div>
                  <div className="text-sm text-gray-700">
                    {data.currentSeats && (
                      <div>Current seats: {data.currentSeats} • Next tier at: {data.nextTierAt}</div>
                    )}
                    {data.currentAgents && (
                      <div>Current agents: {data.currentAgents} • Rate: ${data.negotiatedRate}</div>
                    )}
                  </div>
                  <div className="text-sm font-semibold text-blue-600 mt-2">{data.potentialSavings}</div>
                </div>
              ))}

              {cost.vendorNegotiations.annualCommitments && (
                <div className="border border-green-200 bg-green-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-gray-900">Annual Commitment Discounts</div>
                      <div className="text-sm text-gray-700 mt-1">{cost.vendorNegotiations.annualCommitments.recommendation}</div>
                    </div>
                    <div className="text-xl font-bold text-green-600">{cost.vendorNegotiations.annualCommitments.estimatedSavings}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ROI Summary */}
        <div className="mt-8 rounded-lg bg-gradient-to-br from-[#E94B3C] to-[#C23729] p-8 text-white shadow-lg">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-3xl font-bold">Return on Investment (ROI)</h2>
            <DataSourceBadge type="research" tooltip="ROI calculations based on your existing platform data ($4-7M savings target) and actual tool costs." />
          </div>
          <div className="grid grid-cols-3 gap-8">
            <div>
              <div className="text-sm opacity-90 mb-2">Annual AI Investment</div>
              <div className="text-4xl font-bold">${cost.annualProjection.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm opacity-90 mb-2">Annual Savings vs Traditional</div>
              <div className="text-4xl font-bold">${(cost.savingsVsTraditional / 1000000).toFixed(1)}M</div>
            </div>
            <div>
              <div className="text-sm opacity-90 mb-2">Net ROI</div>
              <div className="text-4xl font-bold">{cost.roiPercentage}%</div>
            </div>
          </div>
          <div className="mt-6 text-sm opacity-90">
            {maturityLevel === 'L3' && 'Baseline maturity level with 44% efficiency improvement'}
            {maturityLevel === 'L4' && 'Advanced automation delivering 67% efficiency improvement and $4.2M annual savings'}
            {maturityLevel === 'L5' && 'Autonomous agentic workforce achieving 87% efficiency improvement and $7.2M annual savings'}
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  value: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
  trend: string;
  positive: boolean;
}

function MetricCard({ icon: Icon, label, value, color, trend, positive }: MetricCardProps) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
    orange: 'text-orange-600 bg-orange-50',
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon size={24} />
        </div>
        <div className="text-sm font-medium text-gray-600">{label}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <div className={`text-xs mt-1 font-medium ${positive ? 'text-green-600' : 'text-red-600'}`}>
        {positive ? <TrendingUp size={12} className="inline mr-1" /> : <TrendingDown size={12} className="inline mr-1" />}
        {trend}
      </div>
    </div>
  );
}
