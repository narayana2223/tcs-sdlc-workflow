"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ArrowLeft, DollarSign, TrendingUp, Clock, Download } from "lucide-react";
import { SourceCard } from "@/components/SourceCard";
import { CalculationCard } from "@/components/CalculationCard";
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils";
import roiData from "@/data/roi-data.json";

export default function BusinessCase() {
  const [teamSize, setTeamSize] = useState(500);

  // Calculate custom ROI based on team size
  const baseTeamSize = 500;
  const scaleFactor = teamSize / baseTeamSize;
  const customNPV = roiData.executiveSummary.npv * scaleFactor;
  const customPayback = Math.round(roiData.executiveSummary.paybackMonths / Math.sqrt(scaleFactor));

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
            href="/competitive-intelligence"
            className="mb-6 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Competitive Intelligence
          </Link>
          <h1 className="section-heading mb-4">
            The Business Case: <span className="gradient-text">Show Me the Money</span>
          </h1>
          <p className="text-xl text-gray-600">
            Quantified financial impact with transparent math
          </p>
        </motion.div>

        {/* Executive Financial Summary */}
        <motion.section
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12"
        >
          <h2 className="subsection-heading mb-8">Executive Financial Summary</h2>

          <div className="grid gap-6 md:grid-cols-4">
            <MetricCard
              icon={<DollarSign className="h-8 w-8" />}
              value={formatCurrency(roiData.executiveSummary.npv)}
              label="NPV"
              sublabel="3-year, 500-person org"
              color="blue"
            />
            <MetricCard
              icon={<TrendingUp className="h-8 w-8" />}
              value={`${roiData.executiveSummary.roi}%`}
              label="ROI"
              sublabel="Return on Investment"
              color="green"
            />
            <MetricCard
              icon={<Clock className="h-8 w-8" />}
              value={`${roiData.executiveSummary.paybackMonths}`}
              label="Months"
              sublabel="Payback Period"
              color="purple"
            />
            <MetricCard
              icon={<TrendingUp className="h-8 w-8" />}
              value="66%"
              label="Cost Cut"
              sublabel="Overall Efficiency"
              color="orange"
            />
          </div>

          <CalculationCard
            formula="NPV = Σ(Cash Flow_t / (1 + r)^t) - Initial Investment"
            assumptions={roiData.calculationAssumptions}
            result={`$${formatNumber(roiData.executiveSummary.npv)} over 3 years`}
          />
        </motion.section>

        {/* Three-Year P&L */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="subsection-heading mb-8">Three-Year P&L</h2>

          <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
            <table className="w-full">
              <thead className="bg-blue-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Year</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Investment</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Savings</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Net</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {roiData.threeYearProjection.map((year, index) => (
                  <motion.tr
                    key={year.year}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className="transition-colors hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 font-semibold text-gray-900">Year {year.year}</td>
                    <td className="px-6 py-4 text-right text-red-600">
                      {formatCurrency(year.investment)}
                    </td>
                    <td className="px-6 py-4 text-right text-green-600">
                      +{formatCurrency(year.savings)}
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-blue-600">
                      {formatCurrency(year.net)}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Cost Reduction Breakdown */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="subsection-heading mb-8">Cost Reduction Breakdown</h2>

          <div className="space-y-6">
            <CostCard
              title="Development"
              baseline={roiData.costReduction.development.baseline}
              aiAugmented={roiData.costReduction.development.aiAugmented}
              savings={roiData.costReduction.development.savings}
              savingsPercent={roiData.costReduction.development.savingsPercent}
            />
            <CostCard
              title="Operations"
              baseline={roiData.costReduction.operations.baseline}
              aiAugmented={roiData.costReduction.operations.aiAugmented}
              savings={roiData.costReduction.operations.savings}
              savingsPercent={roiData.costReduction.operations.savingsPercent}
            />
            <CostCard
              title="Infrastructure"
              baseline={roiData.costReduction.infrastructure.monthlyBaseline * 12}
              aiAugmented={roiData.costReduction.infrastructure.monthlyOptimized * 12}
              savings={roiData.costReduction.infrastructure.annualSavings}
              savingsPercent={roiData.costReduction.infrastructure.savingsPercent}
            />
          </div>
        </motion.section>

        {/* Productivity Gains */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="subsection-heading mb-8">Productivity Gains</h2>

          <div className="space-y-4">
            <ProductivityBar
              label="Dev Velocity"
              before="103 days"
              after="45 days"
              improvement={56}
            />
            <ProductivityBar
              label="Defect Rate"
              before="145/month"
              after="43/month"
              improvement={70}
            />
            <ProductivityBar
              label="Time-to-Market"
              before="20 weeks"
              after="9 weeks"
              improvement={55}
            />
          </div>

          <SourceCard
            sources={roiData.sources}
            className="mt-8"
          />
        </motion.section>

        {/* Interactive ROI Calculator */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-800 p-8 text-white"
        >
          <h2 className="mb-6 text-3xl font-bold">Interactive ROI Calculator</h2>

          <div className="mb-6">
            <label className="mb-2 block text-lg font-medium">
              Your Team Size: {teamSize} FTEs
            </label>
            <input
              type="range"
              min="100"
              max="1000"
              step="50"
              value={teamSize}
              onChange={(e) => setTeamSize(Number(e.target.value))}
              className="h-3 w-full cursor-pointer appearance-none rounded-lg bg-blue-400"
            />
            <div className="mt-2 flex justify-between text-sm text-blue-200">
              <span>100</span>
              <span>1000</span>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <div className="mb-1 text-sm text-blue-200">Your NPV</div>
              <div className="text-3xl font-bold">{formatCurrency(customNPV)}</div>
            </div>
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <div className="mb-1 text-sm text-blue-200">Your ROI</div>
              <div className="text-3xl font-bold">{roiData.executiveSummary.roi}%</div>
            </div>
            <div className="rounded-lg bg-white/10 p-4 backdrop-blur-sm">
              <div className="mb-1 text-sm text-blue-200">Your Payback</div>
              <div className="text-3xl font-bold">{customPayback} months</div>
            </div>
          </div>

          <div className="mt-6 text-sm text-blue-200">
            * Calculation based on 60% average AI productivity improvement and progressive adoption curve
          </div>
        </motion.section>

        {/* Download CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12 rounded-lg bg-gray-100 p-8 text-center"
        >
          <Download className="mx-auto mb-4 h-12 w-12 text-blue-600" />
          <h3 className="mb-2 text-2xl font-bold text-gray-900">
            Download Complete Financial Model
          </h3>
          <p className="mb-4 text-gray-600">
            Get the full Excel model with all calculations and assumptions
          </p>
          <button className="rounded-full bg-blue-600 px-8 py-3 font-semibold text-white hover:bg-blue-700">
            Download Excel Model
          </button>
        </motion.div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/competitive-intelligence"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Competitive Intelligence
          </Link>
          <Link
            href="/value-chain"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Next: SDLC Value Chain
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </main>
  );
}

function MetricCard({ icon, value, label, sublabel, color }: any) {
  const colorClasses = {
    blue: "text-blue-600 border-blue-200",
    green: "text-green-600 border-green-200",
    purple: "text-purple-600 border-purple-200",
    orange: "text-orange-600 border-orange-200",
  };

  return (
    <div className={`metric-card ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="mb-4 flex justify-center">{icon}</div>
      <div className="mb-2 text-center text-4xl font-bold text-gray-900">{value}</div>
      <div className="text-center text-sm font-semibold uppercase tracking-wide text-gray-700">
        {label}
      </div>
      <div className="text-center text-xs text-gray-500">{sublabel}</div>
    </div>
  );
}

function CostCard({ title, baseline, aiAugmented, savings, savingsPercent }: any) {
  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-xl font-bold text-gray-900">{title}</h3>
      <div className="flex items-end justify-between">
        <div className="flex-1">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-gray-600">Baseline: {formatCurrency(baseline)}</span>
            <span className="text-gray-600">AI-Augmented: {formatCurrency(aiAugmented)}</span>
          </div>
          <div className="h-4 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-green-600"
              style={{ width: `${savingsPercent}%` }}
            />
          </div>
        </div>
        <div className="ml-6 text-right">
          <div className="text-2xl font-bold text-green-600">{savingsPercent}%</div>
          <div className="text-sm text-gray-600">{formatCurrency(savings)}</div>
        </div>
      </div>
    </div>
  );
}

function ProductivityBar({ label, before, after, improvement }: any) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-gray-900">{label}</span>
        <span className="text-sm text-gray-600">{before} → {after}</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full bg-gradient-to-r from-blue-400 to-blue-600"
            style={{ width: `${improvement}%` }}
          />
        </div>
        <span className="text-lg font-bold text-blue-600">{improvement}%</span>
      </div>
    </div>
  );
}
