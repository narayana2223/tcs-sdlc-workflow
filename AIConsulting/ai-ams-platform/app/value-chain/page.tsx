"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ArrowLeft, ChevronRight, Code, TestTube, Rocket, Eye, Wrench, Settings } from "lucide-react";
import { SourceCard } from "@/components/SourceCard";
import valueChainData from "@/data/value-chain.json";

const phaseIcons = {
  requirements: Code,
  development: Code,
  testing: TestTube,
  deployment: Rocket,
  monitoring: Eye,
  support: Wrench,
  change: Settings,
};

export default function ValueChain() {
  const [selectedPhase, setSelectedPhase] = useState(0);
  const currentPhase = valueChainData.phases[selectedPhase];
  const PhaseIcon = phaseIcons[currentPhase.id as keyof typeof phaseIcons];

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
            href="/business-case"
            className="mb-6 inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Business Case
          </Link>
          <h1 className="section-heading mb-4">
            The AI-AMS Value Chain: <span className="gradient-text">Your Weapon System</span>
          </h1>
          <p className="text-xl text-gray-600">
            How AI transforms every stage of software delivery
          </p>
        </motion.div>

        {/* Summary Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-12 rounded-2xl bg-blue-600 p-8 text-white"
        >
          <h2 className="mb-4 text-2xl font-bold">
            55+ AI Use Cases That Cut Costs 66% and Double Velocity
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <div className="text-3xl font-bold">60-80%</div>
              <div className="text-sm text-blue-200">Productivity Gains</div>
            </div>
            <div>
              <div className="text-3xl font-bold">90%</div>
              <div className="text-sm text-blue-200">Incident Noise Reduction</div>
            </div>
            <div>
              <div className="text-3xl font-bold">70%</div>
              <div className="text-sm text-blue-200">Faster Deployments</div>
            </div>
            <div>
              <div className="text-3xl font-bold">$2.5M</div>
              <div className="text-sm text-blue-200">Annual Savings/100 devs</div>
            </div>
          </div>
        </motion.div>

        {/* Interactive Timeline */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-12"
        >
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-2 min-w-max">
              {valueChainData.phases.map((phase, index) => {
                const Icon = phaseIcons[phase.id as keyof typeof phaseIcons];
                return (
                  <button
                    key={phase.id}
                    onClick={() => setSelectedPhase(index)}
                    className={`flex flex-col items-center gap-2 rounded-lg p-4 transition-all ${
                      selectedPhase === index
                        ? "bg-blue-600 text-white shadow-lg scale-105"
                        : "bg-white text-gray-700 hover:bg-blue-50"
                    }`}
                  >
                    <Icon className="h-6 w-6" />
                    <div className="text-center">
                      <div className="text-sm font-semibold whitespace-nowrap">{phase.name}</div>
                      <div className="text-xs opacity-75">{phase.useCases.length} AI use cases</div>
                    </div>
                    {index < valueChainData.phases.length - 1 && (
                      <ChevronRight className="absolute right-0 h-4 w-4 opacity-50" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* Phase Detail */}
        <motion.div
          key={selectedPhase}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-12"
        >
          <div className="rounded-2xl border-2 border-blue-200 bg-white p-8 shadow-xl">
            {/* Phase Header */}
            <div className="mb-8 flex items-center gap-4">
              <div className="rounded-full bg-blue-100 p-4">
                <PhaseIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-gray-900">PHASE: {currentPhase.name}</h2>
              </div>
            </div>

            {/* THE PROBLEM (Why?) */}
            {currentPhase.why && currentPhase.why.length > 0 && (
              <div className="mb-8">
                <h3 className="mb-4 text-xl font-bold text-gray-900">THE PROBLEM (Why?)</h3>
                <ul className="space-y-2">
                  {currentPhase.why.map((problem, index) => (
                    <li key={index} className="flex items-start gap-2 text-gray-700">
                      <span className="mt-1 text-red-500">•</span>
                      <span>{problem}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* THE AI SOLUTION (What?) */}
            <div className="mb-8">
              <h3 className="mb-4 text-xl font-bold text-gray-900">THE AI SOLUTION (What?)</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {currentPhase.useCases.slice(0, 6).map((useCase, index) => (
                  <UseCaseCard key={index} useCase={useCase} />
                ))}
              </div>
              {currentPhase.useCases.length > 6 && (
                <button className="mt-4 text-sm text-blue-600 hover:text-blue-800">
                  + {currentPhase.useCases.length - 6} more use cases →
                </button>
              )}
            </div>

            {/* THE OUTCOME (How?) */}
            {currentPhase.outcome && (
              <div className="rounded-lg bg-green-50 p-6">
                <h3 className="mb-4 text-xl font-bold text-gray-900">THE OUTCOME (How?)</h3>
                <div className="mb-4 text-2xl font-bold text-green-700">
                  {currentPhase.outcome.summary}
                </div>
                {currentPhase.outcome.metrics && (
                  <div className="grid gap-4 md:grid-cols-2">
                    {currentPhase.outcome.metrics.map((metric, index) => (
                      <div key={index} className="rounded bg-white p-4">
                        <div className="mb-1 text-sm font-medium text-gray-600">{metric.label}</div>
                        {metric.before && metric.after && (
                          <div className="text-lg">
                            <span className="text-gray-500">{metric.before}</span>
                            <span className="mx-2">→</span>
                            <span className="font-bold text-green-600">{metric.after}</span>
                          </div>
                        )}
                        {metric.improvement && (
                          <div className="mt-1 text-sm font-semibold text-green-600">
                            {metric.improvement}% improvement
                          </div>
                        )}
                        {'value' in metric && metric.value && (
                          <div className="text-lg font-bold text-green-600">{metric.value}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Sources */}
            {currentPhase.sources && (
              <SourceCard sources={currentPhase.sources} className="mt-6" />
            )}
          </div>
        </motion.div>

        {/* Phase Navigation */}
        <div className="mb-12 flex items-center justify-between">
          <button
            onClick={() => setSelectedPhase(Math.max(0, selectedPhase - 1))}
            disabled={selectedPhase === 0}
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-gray-600 transition-colors hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="h-5 w-5" />
            Previous Phase
          </button>
          <div className="text-sm text-gray-500">
            Phase {selectedPhase + 1} of {valueChainData.phases.length}
          </div>
          <button
            onClick={() => setSelectedPhase(Math.min(valueChainData.phases.length - 1, selectedPhase + 1))}
            disabled={selectedPhase === valueChainData.phases.length - 1}
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-gray-600 transition-colors hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next Phase
            <ArrowRight className="h-5 w-5" />
          </button>
        </div>

        {/* Overall Impact Summary */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-12 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 p-8 text-white"
        >
          <h2 className="mb-6 text-3xl font-bold">Overall Impact</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <div className="mb-2 text-4xl font-bold">{valueChainData.overallImpact.totalUseCases}</div>
              <div className="text-blue-200">Total AI Use Cases</div>
            </div>
            <div>
              <div className="mb-2 text-4xl font-bold">{valueChainData.overallImpact.averageProductivityGain}</div>
              <div className="text-blue-200">Average Productivity Gain</div>
            </div>
            <div>
              <div className="mb-2 text-4xl font-bold">{valueChainData.overallImpact.costReduction}</div>
              <div className="text-blue-200">Annual Cost Savings</div>
            </div>
          </div>
          <div className="mt-6 border-t border-white/20 pt-6">
            <div className="text-xl font-semibold">
              Time-to-Market: {valueChainData.overallImpact.timeToMarket}
            </div>
          </div>
        </motion.div>

        {/* Page Navigation */}
        <div className="flex items-center justify-between">
          <Link
            href="/business-case"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Business Case
          </Link>
          <Link
            href="/execution-playbook"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Next: Execution Playbook
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </main>
  );
}

function UseCaseCard({ useCase }: { useCase: any }) {
  return (
    <div className="group relative overflow-hidden rounded-lg border border-gray-200 bg-white p-4 transition-all hover:border-blue-300 hover:shadow-md">
      <h4 className="mb-2 font-semibold text-gray-900">{useCase.name}</h4>
      <p className="mb-3 text-sm text-gray-600 line-clamp-2">{useCase.description}</p>
      <div className="space-y-2">
        <div className="text-xs text-gray-500">
          <span className="font-medium">Tech:</span> {useCase.aiTechnology}
        </div>
        <div className="rounded bg-green-50 px-2 py-1 text-sm font-semibold text-green-700">
          {useCase.productivityImpact}
        </div>
        <div className="text-xs text-gray-500">
          <span className="font-medium">Leaders:</span> {useCase.marketLeaders.join(", ")}
        </div>
      </div>
    </div>
  );
}
