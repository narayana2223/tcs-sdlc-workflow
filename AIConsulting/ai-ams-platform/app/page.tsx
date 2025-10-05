"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, TrendingUp, Clock, DollarSign } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-16 sm:py-24">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <h1 className="mb-6 text-6xl font-bold tracking-tight text-gray-900 sm:text-7xl">
            The AI-AMS <span className="gradient-text">Inflection Point</span>
          </h1>
        </motion.div>

        {/* Animated Metrics */}
        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            icon={<DollarSign className="h-8 w-8" />}
            value="$50B"
            label="Market Under Disruption"
            delay={0.2}
          />
          <MetricCard
            icon={<Clock className="h-8 w-8" />}
            value="18-36"
            label="Months Until Displacement"
            delay={0.4}
          />
          <MetricCard
            icon={<TrendingUp className="h-8 w-8" />}
            value="285%"
            label="ROI for Early Movers"
            delay={0.6}
          />
        </div>

        {/* Value Proposition */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          className="mt-16 text-center"
        >
          <p className="mx-auto max-w-3xl text-2xl leading-relaxed text-gray-700">
            <span className="font-semibold text-gray-900">Traditional AMS is dead.</span>
            <br />
            AI-native competitors are taking{" "}
            <span className="font-bold text-red-600">51-61%</span> of your business.
            <br />
            <span className="font-semibold text-blue-600">Here's how to fight back.</span>
          </p>
        </motion.div>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.6 }}
          className="mt-12 flex justify-center"
        >
          <Link
            href="/competitive-intelligence"
            className="group inline-flex items-center gap-2 rounded-full bg-blue-600 px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all hover:bg-blue-700 hover:shadow-xl"
          >
            Start the Journey
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>
        </motion.div>

        {/* Sources Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
          className="mt-20 border-t border-gray-200 pt-8 text-center"
        >
          <p className="text-sm text-gray-500">
            <span className="font-medium text-gray-700">Sources:</span> McKinsey AI
            Productivity Study 2024 | Gartner AI-AMS Market Research | Crunchbase Startup
            Ecosystem Analysis
          </p>
        </motion.div>
      </div>
    </main>
  );
}

function MetricCard({
  icon,
  value,
  label,
  delay,
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.5 }}
      className="metric-card group cursor-pointer transition-transform hover:scale-105"
    >
      <div className="mb-4 flex justify-center text-blue-600">{icon}</div>
      <div className="mb-2 text-center text-5xl font-bold text-gray-900">
        {value}
      </div>
      <div className="text-center text-sm font-medium uppercase tracking-wide text-gray-600">
        {label}
      </div>
    </motion.div>
  );
}
