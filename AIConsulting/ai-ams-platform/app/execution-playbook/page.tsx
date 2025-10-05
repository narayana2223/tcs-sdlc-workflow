"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ArrowLeft, Users, Shield, Handshake } from "lucide-react";
import { SourceCard } from "@/components/SourceCard";
import workforceData from "@/data/workforce-data.json";
import riskData from "@/data/risk-data.json";
import competitiveData from "@/data/competitive-intelligence.json";

const tabs = [
  { id: "workforce", label: "Workforce Transformation", icon: Users },
  { id: "risk", label: "Risk & Governance", icon: Shield },
  { id: "ecosystem", label: "Startup Ecosystem", icon: Handshake },
];

export default function ExecutionPlaybook() {
  const [activeTab, setActiveTab] = useState("workforce");

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <Link
            href="/value-chain"
            className="mb-6 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Value Chain
          </Link>
          <h1 className="section-heading mb-4">
            The Execution Playbook: <span className="gradient-text">How to Win</span>
          </h1>
          <p className="text-xl text-gray-600">
            Workforce, Risk, and Ecosystem - the implementation trinity
          </p>
        </motion.div>

        {/* Tab Navigation */}
        <div className="mb-8 flex gap-2 border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 border-b-2 px-6 py-3 font-semibold transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-blue-600"
                }`}
              >
                <Icon className="h-5 w-5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "workforce" && <WorkforceTab />}
          {activeTab === "risk" && <RiskTab />}
          {activeTab === "ecosystem" && <EcosystemTab />}
        </motion.div>

        {/* Navigation */}
        <div className="mt-12 flex items-center justify-between">
          <Link
            href="/value-chain"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Value Chain
          </Link>
          <Link
            href="/next-steps"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Next: Decision Framework
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </main>
  );
}

function WorkforceTab() {
  return (
    <div className="space-y-8">
      {/* Summary Banner */}
      <div className="rounded-2xl bg-purple-50 border-2 border-purple-200 p-8">
        <h2 className="mb-4 text-2xl font-bold text-purple-900">THE PEOPLE CHALLENGE</h2>
        <div className="grid gap-6 md:grid-cols-4">
          <div>
            <div className="text-3xl font-bold text-purple-600">{workforceData.executiveSummary.l1Reduction}</div>
            <div className="text-sm text-purple-700">L1 Role Reduction</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">{workforceData.executiveSummary.l2Evolution}</div>
            <div className="text-sm text-purple-700">L2 Role Evolution</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">{workforceData.executiveSummary.annualSavings}</div>
            <div className="text-sm text-purple-700">Annual Savings</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">{workforceData.trainingROI.roi}</div>
            <div className="text-sm text-purple-700">Training ROI</div>
          </div>
        </div>
      </div>

      {/* Role Transformations */}
      <div>
        <h3 className="subsection-heading mb-6">Role Evolution</h3>
        <div className="space-y-4">
          {workforceData.roleTransformations.map((transformation, index) => (
            <div key={index} className="bcg-card">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex-1">
                  <div className="mb-2 font-semibold text-gray-900">{transformation.from}</div>
                  <div className="text-sm text-gray-600">→ {transformation.to}</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-600">
                    {transformation.automation || transformation.evolution}
                  </div>
                  <div className="text-sm text-gray-600">{transformation.timeline}</div>
                </div>
              </div>
              <div className="rounded bg-purple-50 px-3 py-2 text-sm text-purple-700">
                ✓ {transformation.successMetric}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* New Roles */}
      <div>
        <h3 className="subsection-heading mb-6">New AI Specialist Roles</h3>
        <div className="grid gap-6 md:grid-cols-2">
          {workforceData.newRoles.map((role, index) => (
            <div key={index} className="bcg-card">
              <h4 className="mb-2 text-xl font-bold text-gray-900">{role.title}</h4>
              <div className="mb-4 text-lg font-semibold text-green-600">{role.salaryRange}</div>
              <div className="mb-3 space-y-1 text-sm text-gray-600">
                {role.evolution && <div><strong>Evolution:</strong> {role.evolution}</div>}
                {role.focus && <div><strong>Focus:</strong> {role.focus}</div>}
              </div>
              <div className="flex flex-wrap gap-2">
                {role.skills.map((skill, idx) => (
                  <span key={idx} className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Training ROI */}
      <div className="rounded-2xl bg-gradient-to-r from-green-600 to-green-800 p-8 text-white">
        <h3 className="mb-6 text-2xl font-bold">Training Investment & ROI</h3>
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <div className="mb-2 text-3xl font-bold">${(workforceData.trainingROI.investment / 1000000).toFixed(1)}M</div>
            <div className="text-green-200">Training Investment</div>
          </div>
          <div>
            <div className="mb-2 text-3xl font-bold">${(workforceData.trainingROI.annualReturn / 1000000).toFixed(1)}M</div>
            <div className="text-green-200">Annual Return</div>
          </div>
          <div>
            <div className="mb-2 text-3xl font-bold">{workforceData.trainingROI.roi}</div>
            <div className="text-green-200">3-Year ROI</div>
          </div>
        </div>
      </div>

      <SourceCard sources={workforceData.sources} />
    </div>
  );
}

function RiskTab() {
  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="rounded-2xl bg-red-50 border-2 border-red-200 p-8">
        <h2 className="mb-4 text-2xl font-bold text-red-900">THE RISK REALITY</h2>
        <p className="text-lg text-red-800">
          Risk Mitigation Value: <span className="font-bold">{riskData.riskMitigationValue.penaltyAvoidance}</span> penalty avoidance
        </p>
      </div>

      {/* Security Threats */}
      <div>
        <h3 className="subsection-heading mb-6">AI Security Threats</h3>
        <div className="overflow-x-auto">
          <table className="w-full rounded-lg border bg-white">
            <thead className="bg-red-50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Threat</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Severity</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Mitigation</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Effectiveness</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {riskData.securityThreats.map((threat, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-semibold text-gray-900">{threat.threat}</td>
                  <td className="px-6 py-4">
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${
                      threat.severity === "Very High" ? "bg-red-100 text-red-800" : "bg-orange-100 text-orange-800"
                    }`}>
                      {threat.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{threat.mitigation}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-20 overflow-hidden rounded-full bg-gray-200">
                        <div className="h-full bg-green-500" style={{ width: threat.effectiveness }} />
                      </div>
                      <span className="text-sm text-gray-600">{threat.effectiveness}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Regulatory Compliance */}
      <div>
        <h3 className="subsection-heading mb-6">Regulatory Compliance</h3>
        <div className="space-y-4">
          {riskData.regulatoryCompliance.map((reg, index) => (
            <div key={index} className="bcg-card">
              <div className="mb-3 flex items-start justify-between">
                <h4 className="text-xl font-bold text-gray-900">{reg.regulation}</h4>
                <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-800">
                  {reg.timeline}
                </span>
              </div>
              <div className="space-y-2 text-sm text-gray-600">
                <div><strong>Requirement:</strong> {reg.requirement}</div>
                <div className="text-red-600"><strong>Penalty:</strong> {reg.penalty}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Governance Framework */}
      <div className="rounded-2xl bg-blue-50 border-2 border-blue-200 p-8">
        <h3 className="mb-4 text-xl font-bold text-blue-900">Governance Framework</h3>
        <div className="mb-4">
          <strong className="text-blue-900">{riskData.governanceFramework.chiefAIOfficer}</strong>
        </div>
        <ul className="space-y-2">
          {riskData.governanceFramework.committees.map((committee, index) => (
            <li key={index} className="flex items-start gap-2 text-blue-800">
              <span>•</span>
              <span>{committee}</span>
            </li>
          ))}
        </ul>
      </div>

      <SourceCard sources={riskData.sources} />
    </div>
  );
}

function EcosystemTab() {
  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="rounded-2xl bg-orange-50 border-2 border-orange-200 p-8">
        <h2 className="mb-4 text-2xl font-bold text-orange-900">PARTNER OR PERISH</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <div className="text-3xl font-bold text-orange-600">{competitiveData.startupSwarm.totalStartups}</div>
            <div className="text-sm text-orange-700">Total Startups</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-orange-600">{competitiveData.startupSwarm.totalFunding}</div>
            <div className="text-sm text-orange-700">Total Funding</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-orange-600">-$51M</div>
            <div className="text-sm text-orange-700">Risk without integration</div>
          </div>
        </div>
      </div>

      {/* Integration Strategy */}
      <div>
        <h3 className="subsection-heading mb-6">Your Integration Strategy</h3>

        <div className="space-y-6">
          {/* Tier 1 */}
          <div className="bcg-card bg-red-50">
            <h4 className="mb-4 text-xl font-bold text-red-900">TIER 1: Must-Partner (Cannot Build)</h4>
            <div className="mb-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Cursor/Codeium (Code generation)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Snyk/Socket (Security scanning)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>CloudZero (FinOps)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Glean (Enterprise search)</span>
              </div>
            </div>
            <div className="rounded bg-white px-4 py-2 text-sm font-medium text-red-700">
              → Revenue share model: 70/30 split
            </div>
          </div>

          {/* Tier 2 */}
          <div className="bcg-card bg-orange-50">
            <h4 className="mb-4 text-xl font-bold text-orange-900">TIER 2: Selective Integration</h4>
            <div className="mb-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>testRigor, Mabl (Testing automation)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>incident.io (Incident management)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Stainless (API generation)</span>
              </div>
            </div>
            <div className="rounded bg-white px-4 py-2 text-sm font-medium text-orange-700">
              → White-label or reseller agreements
            </div>
          </div>

          {/* Tier 3 */}
          <div className="bcg-card bg-green-50">
            <h4 className="mb-4 text-xl font-bold text-green-900">TIER 3: Build & Differentiate</h4>
            <div className="mb-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Knowledge management (proprietary)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Agentic workflows (competitive moat)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">•</span>
                <span>Industry-specific compliance</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Financial Impact */}
      <div className="rounded-2xl bg-gradient-to-r from-orange-600 to-red-600 p-8 text-white">
        <h3 className="mb-6 text-2xl font-bold">Financial Impact</h3>
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <div className="mb-2 text-3xl font-bold">-$51M</div>
            <div className="text-orange-200">Displacement risk without integration</div>
          </div>
          <div>
            <div className="mb-2 text-3xl font-bold">+$63M</div>
            <div className="text-orange-200">New revenue with smart partnerships</div>
          </div>
          <div>
            <div className="mb-2 text-3xl font-bold">+$12M</div>
            <div className="text-orange-200">Net impact (12% growth)</div>
          </div>
        </div>
      </div>

      <SourceCard sources={["Crunchbase startup data 2024-2025", "Vendor partnership models", "Revenue projection analysis"]} />
    </div>
  );
}
