"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, ArrowRight, AlertTriangle, Target, Rocket, Crown, Calendar, DollarSign, TrendingUp, Shield, Zap, CheckCircle2 } from "lucide-react";
import { SourceCard } from "@/components/SourceCard";
import nextStepsData from "@/data/next-steps.json";

const pathIcons = {
  "fast-follower": Shield,
  "market-leader": Target,
  "industry-disruptor": Crown,
};

const pathColors = {
  "fast-follower": {
    bg: "from-blue-500 to-blue-600",
    border: "border-blue-200",
    text: "text-blue-600",
    bgLight: "bg-blue-50"
  },
  "market-leader": {
    bg: "from-green-500 to-green-600",
    border: "border-green-200",
    text: "text-green-600",
    bgLight: "bg-green-50"
  },
  "industry-disruptor": {
    bg: "from-purple-500 to-purple-600",
    border: "border-purple-200",
    text: "text-purple-600",
    bgLight: "bg-purple-50"
  },
};

export default function NextSteps() {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

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
            href="/execution-playbook"
            className="mb-6 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Execution Playbook
          </Link>
          <h1 className="section-heading mb-4">
            Next Steps: <span className="gradient-text">Choose Your Path</span>
          </h1>
          <p className="text-xl text-gray-600">
            Three strategic options to capture the $50B AI-AMS opportunity
          </p>
        </motion.div>

        {/* Cost of Inaction Warning */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12 rounded-2xl border-2 border-red-200 bg-red-50 p-8"
        >
          <div className="flex items-start gap-4">
            <div className="rounded-full bg-red-100 p-3">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <div className="flex-1">
              <h2 className="mb-2 text-2xl font-bold text-red-900">
                {nextStepsData.inactionCost.title}
              </h2>
              <div className="mb-4 text-3xl font-bold text-red-600">
                {nextStepsData.inactionCost.marketShare} in {nextStepsData.inactionCost.timeframe}
              </div>
              <ul className="space-y-2">
                {nextStepsData.inactionCost.consequences.map((consequence, index) => (
                  <li key={index} className="flex items-start gap-2 text-gray-700">
                    <span className="mt-1 text-red-500">•</span>
                    <span>{consequence}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Strategic Paths */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-12"
        >
          <h2 className="mb-8 text-3xl font-bold text-gray-900">Three Strategic Paths</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {nextStepsData.strategicPaths.map((path, index) => {
              const Icon = pathIcons[path.id as keyof typeof pathIcons];
              const colors = pathColors[path.id as keyof typeof pathColors];
              const isSelected = selectedPath === path.id;

              return (
                <motion.div
                  key={path.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  onClick={() => setSelectedPath(isSelected ? null : path.id)}
                  className={`cursor-pointer rounded-2xl border-2 bg-white p-6 shadow-lg transition-all hover:shadow-xl ${
                    isSelected ? `${colors.border} ring-4 ring-offset-2` : "border-gray-200"
                  }`}
                >
                  {/* Path Header */}
                  <div className="mb-6">
                    <div className={`mb-4 inline-flex rounded-full bg-gradient-to-r ${colors.bg} p-3`}>
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="mb-2 text-2xl font-bold text-gray-900">{path.name}</h3>
                    <p className="mb-4 text-gray-600">{path.description}</p>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">{path.timeline}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">{path.investment}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Target className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">{path.targetOutcome}</span>
                      </div>
                    </div>
                  </div>

                  {/* Key Outcomes */}
                  <div className={`mb-4 rounded-lg ${colors.bgLight} p-4`}>
                    <h4 className="mb-3 font-semibold text-gray-900">Key Outcomes</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Cost Reduction:</span>
                        <span className={`font-bold ${colors.text}`}>{path.outcomes.costReduction}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Productivity:</span>
                        <span className={`font-bold ${colors.text}`}>{path.outcomes.productivityGain}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Time-to-Market:</span>
                        <span className={`font-bold ${colors.text}`}>{path.outcomes.timeToMarket}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Market Position:</span>
                        <span className={`font-bold ${colors.text}`}>{path.outcomes.marketPosition}</span>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Details */}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-4"
                    >
                      {/* Key Initiatives */}
                      <div>
                        <h4 className="mb-2 font-semibold text-gray-900">Key Initiatives</h4>
                        <ul className="space-y-1">
                          {path.keyInitiatives.map((initiative, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                              <CheckCircle2 className={`mt-0.5 h-4 w-4 flex-shrink-0 ${colors.text}`} />
                              <span>{initiative}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Risks */}
                      <div>
                        <h4 className="mb-2 font-semibold text-gray-900">Key Risks</h4>
                        <ul className="space-y-1">
                          {path.risks.map((risk, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                              <span className="mt-1 text-red-500">•</span>
                              <span>{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Best For */}
                      <div className={`rounded-lg border-2 ${colors.border} ${colors.bgLight} p-3`}>
                        <p className="text-sm font-semibold text-gray-900">
                          Best For: {path.bestFor}
                        </p>
                      </div>
                    </motion.div>
                  )}

                  <button
                    className={`mt-4 w-full rounded-lg ${
                      isSelected
                        ? `bg-gradient-to-r ${colors.bg} text-white`
                        : "bg-gray-100 text-gray-700"
                    } px-4 py-2 font-semibold transition-all hover:shadow-md`}
                  >
                    {isSelected ? "Selected" : "View Details"}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Decision Framework */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12 rounded-2xl border-2 border-blue-200 bg-white p-8 shadow-xl"
        >
          <h2 className="mb-6 text-3xl font-bold text-gray-900">
            {nextStepsData.decisionFramework.title}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="pb-4 pr-4 text-left font-semibold text-gray-900">Factor</th>
                  <th className="pb-4 px-4 text-left font-semibold text-blue-600">Fast Follower</th>
                  <th className="pb-4 px-4 text-left font-semibold text-green-600">Market Leader</th>
                  <th className="pb-4 pl-4 text-left font-semibold text-purple-600">Industry Disruptor</th>
                </tr>
              </thead>
              <tbody>
                {nextStepsData.decisionFramework.factors.map((row, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-4 pr-4 font-medium text-gray-900">{row.factor}</td>
                    <td className="py-4 px-4 text-sm text-gray-700">{row.fastFollower}</td>
                    <td className="py-4 px-4 text-sm text-gray-700">{row.marketLeader}</td>
                    <td className="py-4 pl-4 text-sm text-gray-700">{row.industryDisruptor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Recommended Actions Timeline */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="mb-8 text-3xl font-bold text-gray-900">Recommended Actions</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {/* Immediate */}
            <div className="rounded-2xl border-2 border-orange-200 bg-orange-50 p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-full bg-orange-100 p-2">
                  <Zap className="h-6 w-6 text-orange-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">Immediate</h3>
              </div>
              <ul className="space-y-3">
                {nextStepsData.recommendedActions.immediate.map((action, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-600" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 30 Days */}
            <div className="rounded-2xl border-2 border-blue-200 bg-blue-50 p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-full bg-blue-100 p-2">
                  <TrendingUp className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">30 Days</h3>
              </div>
              <ul className="space-y-3">
                {nextStepsData.recommendedActions["30days"].map((action, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 90 Days */}
            <div className="rounded-2xl border-2 border-green-200 bg-green-50 p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-full bg-green-100 p-2">
                  <Rocket className="h-6 w-6 text-green-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900">90 Days</h3>
              </div>
              <ul className="space-y-3">
                {nextStepsData.recommendedActions["90days"].map((action, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Call to Action */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="mb-12 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-white"
        >
          <div className="text-center">
            <h2 className="mb-4 text-3xl font-bold">{nextStepsData.callToAction.title}</h2>
            <p className="mb-2 text-xl font-semibold text-blue-100">
              {nextStepsData.callToAction.urgency}
            </p>
            <p className="mb-8 text-lg">{nextStepsData.callToAction.message}</p>
            <div className="mx-auto max-w-2xl space-y-3">
              {nextStepsData.callToAction.nextSteps.map((step, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 rounded-lg bg-white/10 px-6 py-4 backdrop-blur"
                >
                  <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
                  <span className="text-left">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Sources */}
        <SourceCard sources={nextStepsData.sources} className="mb-12" />

        {/* Page Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/execution-playbook"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Execution Playbook
          </Link>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Return to Home
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </main>
  );
}
