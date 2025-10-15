'use client';

import { useWorkflowStore } from '@/lib/store';
import securityData from '@/data/security-tools.json';
import governanceData from '@/data/governance-rules.json';
import { DataSourceBadge } from '@/components/DataSourceBadge';
import { Shield, CheckCircle, AlertTriangle, FileCheck, Lock, Users } from 'lucide-react';

export default function GovernancePage() {
  const { maturityLevel } = useWorkflowStore();
  const level = maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5';

  const security = securityData.securityLayers[level];
  const governance = governanceData.approvalGates[level];
  const compliance = securityData.complianceFrameworks;
  const incidents = securityData.securityIncidents[level];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Governance & Security</h1>
              <p className="mt-2 text-gray-600">
                Enterprise-grade AI governance, security controls, and compliance management for {maturityLevel}
              </p>
            </div>
            <div className="text-xs text-gray-500">
              Hover over badges for data sources
            </div>
          </div>
        </div>

        {/* Key Security Metrics */}
        <div className="mb-8 grid grid-cols-4 gap-6">
          <MetricCard
            icon={Shield}
            label="Compliance Score"
            value={`${security.metrics.complianceScore}%`}
            color="purple"
            trend="+5% from last month"
          />
          <MetricCard
            icon={Lock}
            label="Security Incidents"
            value={incidents.total.toString()}
            color={incidents.total === 0 ? 'green' : 'red'}
            trend={incidents.total === 0 ? 'Zero incidents' : `${incidents.critical} critical`}
          />
          <MetricCard
            icon={CheckCircle}
            label="Auto-Remediated"
            value={`${security.metrics.autoFixed}/${security.metrics.vulnerabilitiesDetected}`}
            color="green"
            trend={`${Math.round((security.metrics.autoFixed / Math.max(security.metrics.vulnerabilitiesDetected, 1)) * 100)}% success rate`}
          />
          <MetricCard
            icon={FileCheck}
            label="Audit Compliance"
            value={`${governanceData.metricsTracking.complianceMetrics.auditScore[level]}%`}
            color="blue"
            trend="SOC2 Type II ready"
          />
        </div>

        {/* Approval Gates Overview */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <CheckCircle className="text-orange-600" size={28} />
              Approval Gates & Human-in-the-Loop Controls
            </h2>
            <DataSourceBadge type="research" tooltip="Gate counts (95→25→8) from your existing platform data. Auto-approval rates based on AI confidence thresholds." />
          </div>

          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-lg">
              <div className="text-4xl font-bold text-orange-600 mb-2">{governance.totalGates}</div>
              <div className="text-sm font-medium text-gray-700">Total Approval Gates</div>
              <div className="text-xs text-gray-600 mt-2">
                {maturityLevel === 'L3' && 'Human approval for all decisions'}
                {maturityLevel === 'L4' && '74% reduction from L3'}
                {maturityLevel === 'L5' && '92% reduction from L3'}
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
              <div className="text-4xl font-bold text-green-600 mb-2">
                {governanceData.metricsTracking.approvalMetrics.autoApprovalRate[level]}
              </div>
              <div className="text-sm font-medium text-gray-700">Auto-Approval Rate</div>
              <div className="text-xs text-gray-600 mt-2">
                {maturityLevel === 'L3' && 'All decisions require human approval'}
                {maturityLevel === 'L4' && 'AI confidence ≥ 85%'}
                {maturityLevel === 'L5' && 'Fully autonomous swarms'}
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {governanceData.metricsTracking.approvalMetrics.avgApprovalTime[level]}
              </div>
              <div className="text-sm font-medium text-gray-700">Avg Approval Time</div>
              <div className="text-xs text-gray-600 mt-2">
                {maturityLevel === 'L3' && 'Manual review process'}
                {maturityLevel === 'L4' && '94% faster than L3'}
                {maturityLevel === 'L5' && '99% faster than L3'}
              </div>
            </div>
          </div>

          {/* Gates by Category */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Gates by Category</h3>
            <div className="grid grid-cols-6 gap-4">
              {Object.entries(governance.categories).map(([category, count]) => (
                <div key={category} className="bg-gray-50 p-4 rounded-lg text-center border border-gray-200">
                  <div className="text-3xl font-bold text-gray-900 mb-1">{count}</div>
                  <div className="text-xs text-gray-600 capitalize">
                    {category.replace(/([A-Z])/g, ' $1').trim()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sample Gates */}
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Example Approval Gates</h3>
            <div className="space-y-3">
              {governance.gates.slice(0, 3).map((gate) => (
                <div key={gate.id} className="border border-gray-200 rounded-lg p-4 hover:border-[#E94B3C] transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{gate.name}</div>
                      <div className="text-sm text-gray-600 mt-1">
                        Stage: <span className="capitalize">{gate.stage}</span> |
                        Trigger: <span className="font-medium">{gate.trigger.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="text-sm text-gray-500 mt-2">
                        Approver: {gate.approver} • SLA: {gate.sla}
                      </div>
                    </div>
                    <div className="ml-4">
                      {gate.autoApprove ? (
                        <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">
                          Auto-approve enabled
                        </span>
                      ) : (
                        <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-3 py-1 rounded-full">
                          Manual review required
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Security Tools & Compliance */}
        <div className="grid grid-cols-2 gap-8 mb-8">
          {/* Security Tools */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Shield className="text-purple-600" size={28} />
                Security Scanning Tools
              </h2>
              <DataSourceBadge type="research" tooltip="Real security tools: Snyk, GitGuardian, Semgrep, CodeQL. Actual vendor products." />
            </div>
            <div className="space-y-4">
              {security.tools.map((tool) => (
                <div key={tool.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-900">{tool.name}</div>
                    <div className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded">
                      {tool.coverage}% coverage
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 mb-2 capitalize">{tool.type.replace(/-/g, ' ')}</div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>Stage: {tool.stage}</span>
                    <span>•</span>
                    <span>Avg: {tool.avgTime}</span>
                    {tool.autoFixed !== undefined && (
                      <>
                        <span>•</span>
                        <span className="text-green-600 font-medium">{tool.autoFixed} auto-fixed</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Compliance Frameworks */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <FileCheck className="text-blue-600" size={28} />
                Compliance Frameworks
              </h2>
              <DataSourceBadge type="research" tooltip="Real compliance standards: SOC2, GDPR, HIPAA, ISO 27001. Coverage scores are benchmarks." />
            </div>
            <div className="space-y-4">
              {Object.entries(compliance).map(([key, framework]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-semibold text-gray-900">{framework.name}</div>
                    <div className={`text-xs font-semibold px-2 py-1 rounded ${
                      framework.coverage[level] === 100
                        ? 'bg-green-100 text-green-800'
                        : framework.coverage[level] >= 85
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {framework.coverage[level]}% compliant
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${framework.coverage[level]}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-600">
                    {framework.requirements.slice(0, 3).join(' • ')}
                    {framework.requirements.length > 3 && ` • +${framework.requirements.length - 3} more`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Security Incidents */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <AlertTriangle className={`${incidents.total === 0 ? 'text-green-600' : 'text-red-600'}`} size={28} />
              Security Incidents
            </h2>
            <DataSourceBadge type="benchmark" tooltip="Incident counts are illustrative benchmarks. Zero incidents at L5 demonstrates mature security posture." />
          </div>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-gray-900">{incidents.total}</div>
              <div className="text-sm text-gray-600 mt-1">Total Incidents</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-red-600">{incidents.critical}</div>
              <div className="text-sm text-gray-600 mt-1">Critical</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-orange-600">{incidents.high}</div>
              <div className="text-sm text-gray-600 mt-1">High</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-blue-600">{incidents.avgResolutionTime}</div>
              <div className="text-sm text-gray-600 mt-1">Avg Resolution</div>
            </div>
          </div>

          {incidents.total > 0 ? (
            <div className="space-y-3">
              {incidents.incidents && incidents.incidents.map((incident, idx) => (
                <div key={idx} className="border-l-4 border-red-500 bg-red-50 p-4 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-900">{incident.type}</div>
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      incident.severity === 'critical'
                        ? 'bg-red-600 text-white'
                        : incident.severity === 'high'
                        ? 'bg-orange-500 text-white'
                        : 'bg-yellow-500 text-white'
                    }`}>
                      {incident.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    Detected by: {incident.detectedBy} • Resolved in: {incident.resolutionTime}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <CheckCircle className="mx-auto text-green-600 mb-3" size={48} />
              <div className="text-lg font-semibold text-green-900">No Security Incidents</div>
              <div className="text-sm text-green-700 mt-1">
                {maturityLevel} maturity level maintains zero-incident status
              </div>
            </div>
          )}
        </div>

        {/* Role-Based Access Control */}
        <div className="mt-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Users className="text-purple-600" size={28} />
              Role-Based Access Control
            </h2>
            <DataSourceBadge type="sample" tooltip="Example RBAC definitions. Customize roles, permissions, and restrictions for your organization." />
          </div>
          <div className="grid grid-cols-2 gap-6">
            {governanceData.roleBasedAccess.roles.map((role) => (
              <div key={role.name} className="border border-gray-200 rounded-lg p-4">
                <div className="font-semibold text-gray-900 mb-3">{role.name}</div>
                <div className="mb-3">
                  <div className="text-xs font-semibold text-gray-600 mb-2">PERMISSIONS</div>
                  <div className="flex flex-wrap gap-1">
                    {role.permissions.slice(0, 3).map((perm) => (
                      <span key={perm} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        {perm.replace(/_/g, ' ')}
                      </span>
                    ))}
                    {role.permissions.length > 3 && (
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                        +{role.permissions.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
                {role.restrictions.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-600 mb-2">RESTRICTIONS</div>
                    <div className="flex flex-wrap gap-1">
                      {role.restrictions.map((restriction) => (
                        <span key={restriction} className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                          {restriction.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
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
  color: 'blue' | 'green' | 'purple' | 'red';
  trend: string;
}

function MetricCard({ icon: Icon, label, value, color, trend }: MetricCardProps) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
    red: 'text-red-600 bg-red-50',
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
      <div className="text-xs text-gray-500 mt-1">{trend}</div>
    </div>
  );
}
