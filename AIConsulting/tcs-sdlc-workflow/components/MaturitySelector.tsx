'use client';

import { useWorkflowStore } from '@/lib/store';
import { MaturityLevel } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

const maturityLevels: { level: MaturityLevel; label: string; description: string }[] = [
  {
    level: 'L3',
    label: 'L3 Supervised',
    description: '95 gates • 14.5 weeks • 44% faster',
  },
  {
    level: 'L4',
    label: 'L4 Autonomous',
    description: '25 gates • 8.5 weeks • 67% faster',
  },
  {
    level: 'L5',
    label: 'L5 Agentic Workforce',
    description: '8 gates • 3.5 weeks • 87% faster',
  },
];

export function MaturitySelector() {
  const { maturityLevel, setMaturityLevel } = useWorkflowStore();

  return (
    <div className="flex items-center justify-center border-b bg-gradient-to-r from-gray-50 to-gray-100 py-6">
      <div className="flex flex-col items-center gap-4">
        <p className="text-sm font-medium text-gray-600">
          Select Maturity Level
        </p>
        <div className="relative inline-flex rounded-lg bg-white p-1 shadow-sm">
          {maturityLevels.map((item) => (
            <button
              key={item.level}
              onClick={() => setMaturityLevel(item.level)}
              className={cn(
                'relative z-10 px-6 py-3 text-sm font-medium transition-colors',
                maturityLevel === item.level
                  ? 'text-white'
                  : 'text-gray-700 hover:text-gray-900'
              )}
            >
              <div className="flex flex-col items-center gap-1">
                <span className="font-semibold">{item.label}</span>
                <span className="text-xs opacity-75">{item.description}</span>
              </div>
              {maturityLevel === item.level && (
                <motion.div
                  layoutId="active-pill"
                  className="absolute inset-0 rounded-md bg-gradient-to-r from-[#E94B3C] to-[#C23729]"
                  style={{ zIndex: -1 }}
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
