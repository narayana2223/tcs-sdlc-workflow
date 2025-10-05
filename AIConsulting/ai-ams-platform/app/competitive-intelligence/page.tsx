"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ArrowLeft, Shield, TrendingUp, Zap } from "lucide-react";
import { SourceCard } from "@/components/SourceCard";
import competitiveData from "@/data/competitive-intelligence.json";

export default function CompetitiveIntelligence() {
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
            href="/"
            className="mb-6 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Link>
          <h1 className="section-heading mb-4">
            Competitive Intelligence: <span className="gradient-text">Know Your Enemy</span>
          </h1>
          <p className="text-xl text-gray-600">
            Who's coming for your business and how they're winning
          </p>
        </motion.div>

        {/* Key Insight Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12 rounded-2xl bg-red-50 border-2 border-red-200 p-8"
        >
          <h2 className="mb-4 text-2xl font-bold text-red-900">
            ⚠️ The Market is Being Attacked from Three Sides
          </h2>
          <p className="text-lg text-red-800">
            You have <span className="font-bold">18 months</span> to respond before significant market displacement.
          </p>
        </motion.div>

        {/* Section A: Big 4 Consulting Giants */}
        <section className="mb-16">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="subsection-heading mb-8"
          >
            A. The Big 4 Consulting Giants
          </motion.h2>

          <div className="overflow-x-auto">
            <table className="w-full rounded-lg border bg-white shadow-sm">
              <thead className="bg-blue-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Company</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Platform</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Scale</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Investment</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Threat Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {competitiveData.big4.map((company, index) => (
                  <motion.tr
                    key={company.company}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className="transition-colors hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 font-semibold text-gray-900">{company.company}</td>
                    <td className="px-6 py-4 text-gray-700">{company.platform}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{company.scale}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{company.investment}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                          <div
                            className="h-full bg-red-500"
                            style={{ width: `${company.threatLevel * 10}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-700">
                          {company.threatLevel}/10
                        </span>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-6 rounded-lg bg-blue-50 p-6"
          >
            <p className="text-lg font-semibold text-blue-900">
              💡 Key Insight: They're all pricing 20-30% premium with AI story
            </p>
          </motion.div>

          <SourceCard sources={["Company investor decks Q3 2024", "Public company filings"]} />
        </section>

        {/* Section B: Platform Giants */}
        <section className="mb-16">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="subsection-heading mb-8"
          >
            B. Platform Giants Eating the Stack
          </motion.h2>

          <div className="grid gap-6 md:grid-cols-2">
            {competitiveData.platformGiants.map((platform, index) => (
              <motion.div
                key={platform.company}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bcg-card"
              >
                <div className="mb-4 flex items-start justify-between">
                  <h3 className="text-xl font-bold text-gray-900">{platform.company}</h3>
                  <Shield className="h-6 w-6 text-red-500" />
                </div>
                <div className="space-y-2 text-sm text-gray-600">
                  {platform.revenue && <p><strong>Revenue:</strong> {platform.revenue}</p>}
                  {platform.marketCap && <p><strong>Market Cap:</strong> {platform.marketCap}</p>}
                  {platform.penetration && <p><strong>Penetration:</strong> {platform.penetration}</p>}
                  <p><strong>AI Capability:</strong> {platform.aiCapability}</p>
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full bg-red-600"
                      style={{ width: `${platform.threatLevel * 10}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-red-600">
                    Threat: {platform.threatLevel}/10
                  </span>
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-6 rounded-lg bg-red-50 p-6"
          >
            <p className="text-lg font-semibold text-red-900">
              💡 Key Insight: They're automating L1/L2 support out of existence
            </p>
          </motion.div>

          <SourceCard sources={["Public company filings", "Gartner Market Research"]} />
        </section>

        {/* Section C: Startup Swarm */}
        <section className="mb-16">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="subsection-heading mb-8"
          >
            C. The Startup Swarm ({competitiveData.startupSwarm.totalStartups} Disruptors)
          </motion.h2>

          <div className="mb-8 rounded-2xl bg-gradient-to-br from-orange-50 to-red-50 p-8">
            <div className="mb-6 grid gap-6 md:grid-cols-3">
              <div className="text-center">
                <div className="mb-2 text-4xl font-bold text-orange-600">
                  {competitiveData.startupSwarm.veryHighThreat.count}
                </div>
                <div className="text-sm font-medium text-gray-700">Very High Threat</div>
                <div className="mt-2 text-xs text-gray-600">
                  {competitiveData.startupSwarm.veryHighThreat.percentage}
                </div>
              </div>
              <div className="text-center">
                <div className="mb-2 text-4xl font-bold text-orange-500">
                  {competitiveData.startupSwarm.highThreat.count}
                </div>
                <div className="text-sm font-medium text-gray-700">High Threat</div>
                <div className="mt-2 text-xs text-gray-600">
                  {competitiveData.startupSwarm.highThreat.percentage}
                </div>
              </div>
              <div className="text-center">
                <div className="mb-2 text-4xl font-bold text-orange-400">
                  {competitiveData.startupSwarm.mediumThreat.count}
                </div>
                <div className="text-sm font-medium text-gray-700">Medium Threat</div>
                <div className="mt-2 text-xs text-gray-600">
                  {competitiveData.startupSwarm.mediumThreat.percentage}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="mb-2 font-semibold text-gray-900">Very High Threat Examples:</h4>
                <div className="flex flex-wrap gap-2">
                  {competitiveData.startupSwarm.veryHighThreat.examples.map((startup) => (
                    <span
                      key={startup}
                      className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800"
                    >
                      {startup}
                    </span>
                  ))}
                </div>
              </div>
              <p className="text-sm text-gray-700">
                <strong>Characteristics:</strong>{" "}
                {competitiveData.startupSwarm.veryHighThreat.characteristics}
              </p>
              <p className="text-lg font-semibold text-orange-900">
                💰 Total Funding: {competitiveData.startupSwarm.totalFunding}
              </p>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="rounded-lg bg-orange-50 p-6"
          >
            <p className="text-lg font-semibold text-orange-900">
              💡 Key Insight: Clients will buy these directly unless you integrate them
            </p>
          </motion.div>

          <SourceCard sources={["Crunchbase 2024-2025", "CB Insights", "TechCrunch"]} />
        </section>

        {/* Key Insights Summary */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-800 p-8 text-white"
        >
          <h2 className="mb-6 text-3xl font-bold">Strategic Takeaways</h2>
          <ul className="space-y-3">
            {competitiveData.keyInsights.map((insight, index) => (
              <li key={index} className="flex items-start gap-3">
                <Zap className="mt-1 h-5 w-5 flex-shrink-0" />
                <span className="text-lg">{insight}</span>
              </li>
            ))}
          </ul>
        </motion.section>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Home
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
