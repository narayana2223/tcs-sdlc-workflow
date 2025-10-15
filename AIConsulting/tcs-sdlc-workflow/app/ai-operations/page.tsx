'use client';

import { useWorkflowStore } from '@/lib/store';
import securityData from '@/data/security-tools.json';
import governanceData from '@/data/governance-rules.json';
import costData from '@/data/cost-metrics.json';
import { DataSourceBadge } from '@/components/DataSourceBadge';
import { Activity, DollarSign, Shield, CheckCircle, AlertCircle, Clock, Zap } from 'lucide-react';

export default function AIOperationsPage() {
  const { maturityLevel } = useWorkflowStore();
  const level = maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5';

  const security = securityData.securityLayers[level];
  const governance = governanceData.approvalGates[level];
  const cost = costData[level];

  // Mock real-time tool status
  const toolStatus = [
    { name: 'Cursor', status: 'healthy', latency: '98ms', uptime: 99.9 },
    { name: level === 'l5' ? 'Devin' : 'Cursor', status: 'healthy', latency: level === 'l5' ? '1.2s' : '98ms', uptime: level === 'l5' ? 99.5 : 99.9 },
    { name: 'CodeRabbit', status: 'healthy', latency: '145ms', uptime: 99.9 },
    { name: 'QA Wolf', status: 'healthy', latency: '200ms', uptime: 99.8 },
    { name: 'e2b Sandbox', status: 'healthy', latency: '50ms', uptime: 99.95 },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Operations Center</h1>
              <p className="mt-2 text-gray-600">
                Real-time monitoring, cost tracking, and governance oversight for {maturityLevel}
              </p>
            </div>
            <div className="text-xs text-gray-500">
              Hover over badges for data sources
            </div>
          </div>
        </div>

        {/* Key Metrics Row */}
        <div className="mb-8 grid grid-cols-4 gap-6">
          <MetricCard
            icon={Activity}
            label="AI Tools Active"
            value={toolStatus.length.toString()}
            color="blue"
            subtext="All systems operational"
          />
          <MetricCard
            icon={DollarSign}
            label="Daily Spend"
            value={`$${cost.dailySpend.toLocaleString()}`}
            color="green"
            subtext={`$${cost.monthlyForecast.toLocaleString()}/mo forecast`}
          />
          <MetricCard
            icon={Shield}
            label="Security Score"
            value={`${security.metrics.complianceScore}%`}
            color="purple"
            subtext={`${security.metrics.vulnerabilitiesDetected} vulns detected`}
          />
          <MetricCard
            icon={CheckCircle}
            label="Approval Gates"
            value={governance.totalGates.toString()}
            color="orange"
            subtext={`${governanceData.metricsTracking.approvalMetrics.autoApprovalRate[level]} auto-approved`}
          />
        </div>

        {/* Tool Status Monitor */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Activity className="text-blue-600" size={24} />
              Real-Time Tool Status
            </h2>
            <DataSourceBadge type="sample" tooltip="Representative uptime/latency values - connect to actual monitoring tools" />
          </div>
          <div className="space-y-3">
            {toolStatus.map((tool) => (
              <ToolStatusRow key={tool.name} tool={tool} />
            ))}
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-2 gap-8">
          {/* Cost Breakdown */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <DollarSign className="text-green-600" size={24} />
                Cost Breakdown
              </h2>
              <DataSourceBadge type="benchmark" tooltip="Based on actual tool pricing and your $4-7M annual savings target" />
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Daily Spend</span>
                <span className="text-lg font-bold">${cost.dailySpend.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Monthly Forecast</span>
                <span className="text-lg font-bold">${cost.monthlyForecast.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Cost per Developer</span>
                <span className="text-lg font-bold">${cost.costPerDeveloper}/day</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Annual Savings vs Traditional</span>
                <span className="text-lg font-bold text-green-600">
                  ${(cost.savingsVsTraditional / 1000000).toFixed(1)}M
                </span>
              </div>
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Spending Tools</h3>
                <div className="space-y-2">
                  {cost.toolCosts
                    .filter(t => t.category !== 'savings' && t.dailyCost > 0)
                    .sort((a, b) => b.dailyCost - a.dailyCost)
                    .slice(0, 5)
                    .map(tool => (
                      <div key={tool.tool} className="flex justify-between text-sm">
                        <span className="text-gray-600">{tool.tool}</span>
                        <span className="font-medium">${tool.dailyCost}/day</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>

          {/* Security & Compliance */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Shield className="text-purple-600" size={24} />
                Security & Compliance
              </h2>
              <DataSourceBadge type="benchmark" tooltip="Based on typical enterprise security automation patterns" />
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Compliance Score</span>
                <span className="text-lg font-bold">{security.metrics.complianceScore}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Scans</span>
                <span className="text-lg font-bold">{security.metrics.totalScans}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Vulnerabilities Detected</span>
                <span className="text-lg font-bold">{security.metrics.vulnerabilitiesDetected}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Auto-Fixed</span>
                <span className="text-lg font-bold text-green-600">{security.metrics.autoFixed}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Requires Review</span>
                <span className="text-lg font-bold text-orange-600">{security.metrics.manualReview}</span>
              </div>
              <div className="border-t pt-4 mt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Active Security Tools</h3>
                <div className="space-y-2">
                  {security.tools.map(tool => (
                    <div key={tool.id} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{tool.name}</span>
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        {tool.coverage}% coverage
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Governance Overview */}
        <div className="mt-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <CheckCircle className="text-orange-600" size={24} />
              Governance Overview
            </h2>
            <DataSourceBadge type="research" tooltip="Approval gate counts (95→25→8) from your existing platform data" />
          </div>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-600 mb-1">Total Approval Gates</div>
              <div className="text-3xl font-bold">{governance.totalGates}</div>
              <div className="text-xs text-gray-500 mt-1">
                Down from {maturityLevel === 'L3' ? '95 (baseline)' : maturityLevel === 'L4' ? '95 (-74%)' : '95 (-92%)'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Avg Approval Time</div>
              <div className="text-3xl font-bold">{governanceData.metricsTracking.approvalMetrics.avgApprovalTime[level]}</div>
              <div className="text-xs text-gray-500 mt-1">
                {maturityLevel === 'L3' ? 'Manual review' : maturityLevel === 'L4' ? '94% faster' : '99% faster'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Auto-Approval Rate</div>
              <div className="text-3xl font-bold">{governanceData.metricsTracking.approvalMetrics.autoApprovalRate[level]}</div>
              <div className="text-xs text-gray-500 mt-1">
                {maturityLevel === 'L3' ? 'All manual' : maturityLevel === 'L4' ? 'AI-assisted' : 'Fully autonomous'}
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-6 gap-3">
            {Object.entries(governance.categories).map(([category, count]) => (
              <div key={category} className="bg-gray-50 p-3 rounded-lg text-center">
                <div className="text-xs text-gray-600 capitalize mb-1">{category.replace(/([A-Z])/g, ' $1').trim()}</div>
                <div className="text-xl font-bold text-gray-900">{count}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent AI Decisions Log */}
        <div className="mt-8 rounded-lg bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="text-gray-600" size={24} />
            Recent AI Decisions
          </h2>
          <div className="space-y-2">
            <AuditLogEntry
              time="2 min ago"
              action="CodeRabbit auto-approved PR #1234"
              confidence={92}
              user="AI Agent"
            />
            <AuditLogEntry
              time="5 min ago"
              action="Devin completed feature implementation"
              confidence={88}
              user="AI Agent"
            />
            <AuditLogEntry
              time="12 min ago"
              action="QA Wolf escalated test failure to human"
              confidence={45}
              user="QA Wolf → Sarah Chen"
            />
            <AuditLogEntry
              time="18 min ago"
              action="Security scan completed - 0 issues"
              confidence={100}
              user="Snyk"
            />
            <AuditLogEntry
              time="24 min ago"
              action="Architectural change approved"
              confidence={null}
              user="John Smith (Architect)"
            />
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
  subtext: string;
}

function MetricCard({ icon: Icon, label, value, color, subtext }: MetricCardProps) {
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
      <div className="text-xs text-gray-500 mt-1">{subtext}</div>
    </div>
  );
}

interface ToolStatusRowProps {
  tool: {
    name: string;
    status: string;
    latency: string;
    uptime: number;
  };
}

function ToolStatusRow({ tool }: ToolStatusRowProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
          <CheckCircle className="text-green-600" size={20} />
        </div>
        <div>
          <div className="font-semibold text-gray-900">{tool.name}</div>
          <div className="text-sm text-gray-500">Status: {tool.status}</div>
        </div>
      </div>
      <div className="flex gap-8 text-sm">
        <div>
          <div className="text-gray-500">Latency</div>
          <div className="font-semibold text-gray-900">{tool.latency}</div>
        </div>
        <div>
          <div className="text-gray-500">Uptime</div>
          <div className="font-semibold text-gray-900">{tool.uptime}%</div>
        </div>
      </div>
    </div>
  );
}

interface AuditLogEntryProps {
  time: string;
  action: string;
  confidence: number | null;
  user: string;
}

function AuditLogEntry({ time, action, confidence, user }: AuditLogEntryProps) {
  return (
    <div className="flex items-start justify-between border-l-2 border-gray-200 pl-4 py-2 hover:border-[#E94B3C] transition-colors">
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-900">{action}</div>
        <div className="text-xs text-gray-500 mt-1">
          <Clock size={12} className="inline mr-1" />
          {time} • {user}
        </div>
      </div>
      {confidence !== null && (
        <div className={`ml-4 px-2 py-1 rounded text-xs font-semibold ${
          confidence >= 85 ? 'bg-green-100 text-green-800' :
          confidence >= 50 ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {confidence}% confidence
        </div>
      )}
    </div>
  );
}
