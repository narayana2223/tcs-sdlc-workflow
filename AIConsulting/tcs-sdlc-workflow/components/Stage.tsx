'use client';

import { Stage as StageType } from '@/lib/types';
import { useWorkflowStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { ChevronDown, Clock, Users, TrendingDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface StageProps {
  stage: StageType;
}

export function Stage({ stage }: StageProps) {
  const { maturityLevel, expandedStage, toggleStage } = useWorkflowStore();
  const isExpanded = expandedStage === stage.id;

  // Get metrics for current maturity level
  const metrics = stage.metrics[maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5'];

  return (
    <div
      className={cn(
        'inline-block snap-center transition-all duration-300',
        isExpanded ? 'w-[800px]' : `w-[${stage.width}px]`
      )}
      style={{ width: isExpanded ? '800px' : `${stage.width}px` }}
    >
      <div className="flex h-full flex-col rounded-lg border-2 border-gray-200 bg-white shadow-sm">
        {/* Stage Header */}
        <div className="border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{stage.title}</h3>
              <p className="text-xs text-gray-600">{stage.subtitle}</p>
            </div>
            <button
              onClick={() => toggleStage(stage.id)}
              className="rounded-md p-1 hover:bg-gray-100"
            >
              <ChevronDown
                size={20}
                className={cn(
                  'transition-transform',
                  isExpanded && 'rotate-180'
                )}
              />
            </button>
          </div>
        </div>

        {/* Stage Content */}
        <div className="flex-1 p-4">
          {/* Actors */}
          <div className="mb-4">
            <p className="mb-2 text-xs font-semibold uppercase text-gray-500">
              Human Actors
            </p>
            <div className="flex flex-wrap gap-2">
              {stage.actors.map((actor, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 rounded-md bg-[#4A90E2] px-3 py-1.5 text-sm font-medium text-white"
                >
                  <span>{actor.icon}</span>
                  <span>{actor.role}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Applications */}
          <div className="mb-4">
            <p className="mb-2 text-xs font-semibold uppercase text-gray-500">
              AI Applications
            </p>
            <div className="flex flex-wrap gap-2">
              {stage.aiApplications.slice(0, isExpanded ? undefined : 3).map((appId) => (
                <div
                  key={appId}
                  className="cursor-pointer rounded-md bg-[#E94B3C] px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90"
                  title={`Click to view ${appId} details`}
                >
                  🤖 {appId}
                </div>
              ))}
              {!isExpanded && stage.aiApplications.length > 3 && (
                <div className="flex items-center rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-600">
                  +{stage.aiApplications.length - 3} more
                </div>
              )}
            </div>
          </div>

          {/* Infrastructure (only show if expanded or L4/L5) */}
          <AnimatePresence>
            {(isExpanded || maturityLevel !== 'L3') && stage.infrastructureTools.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4"
              >
                <p className="mb-2 text-xs font-semibold uppercase text-gray-500">
                  Agent Infrastructure
                </p>
                <div className="flex flex-wrap gap-2">
                  {stage.infrastructureTools.map((infraId) => (
                    <div
                      key={infraId}
                      className="rounded-md bg-[#F5A623] px-2 py-1 text-xs font-medium text-black"
                    >
                      ⚙️ {infraId}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Data Stores */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase text-gray-500">
              System of Record
            </p>
            {stage.dataStores.map((ds, idx) => (
              <div
                key={idx}
                className="rounded-md border border-dashed border-[#999999] bg-[#D4C5B9] p-3"
              >
                <p className="text-sm font-semibold text-gray-900">{ds.name}</p>
                <ul className="mt-1 space-y-0.5">
                  {ds.artifacts.slice(0, isExpanded ? undefined : 2).map((artifact, i) => (
                    <li key={i} className="text-xs text-gray-700">
                      • {artifact}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Metrics Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-4 py-3">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="flex items-center justify-center gap-1 text-xs text-gray-600">
                <Clock size={12} />
                <span>Duration</span>
              </div>
              <p className="mt-0.5 text-sm font-bold text-gray-900">
                {metrics.duration}
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center gap-1 text-xs text-gray-600">
                <Users size={12} />
                <span>Gates</span>
              </div>
              <p className="mt-0.5 text-sm font-bold text-gray-900">
                {metrics.humanTouchpoints}
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center gap-1 text-xs text-gray-600">
                <TrendingDown size={12} />
                <span>Saved</span>
              </div>
              <p className="mt-0.5 text-sm font-bold text-green-600">
                {metrics.timeSaved}
              </p>
            </div>
          </div>
          {!isExpanded && (
            <button
              onClick={() => toggleStage(stage.id)}
              className="mt-2 w-full rounded-md bg-white py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100"
            >
              Click to expand →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
