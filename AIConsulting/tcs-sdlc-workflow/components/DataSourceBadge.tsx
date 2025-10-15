'use client';

import * as Tooltip from '@radix-ui/react-tooltip';
import { CheckCircle2, BarChart3, FileText } from 'lucide-react';

export type DataSourceType = 'research' | 'benchmark' | 'sample';

interface DataSourceBadgeProps {
  type: DataSourceType;
  tooltip?: string;
  size?: 'sm' | 'md';
}

const badgeConfig = {
  research: {
    icon: CheckCircle2,
    label: 'Research-backed',
    color: 'bg-green-100 text-green-800 border-green-300',
    description: 'Based on verified research, actual tool pricing, and your existing platform data',
  },
  benchmark: {
    icon: BarChart3,
    label: 'Industry benchmark',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    description: 'Based on industry standards, typical enterprise patterns, and a16z framework analysis',
  },
  sample: {
    icon: FileText,
    label: 'Sample data',
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    description: 'Illustrative example - customize with your organization\'s actual metrics',
  },
};

export function DataSourceBadge({ type, tooltip, size = 'sm' }: DataSourceBadgeProps) {
  const config = badgeConfig[type];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
  };

  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <span
            className={`inline-flex items-center gap-1 rounded-full border font-medium cursor-help ${config.color} ${sizeClasses[size]}`}
          >
            <Icon size={size === 'sm' ? 12 : 14} />
            {config.label}
          </span>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className="max-w-xs rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-lg"
            sideOffset={5}
          >
            <div className="font-semibold mb-1">{config.label}</div>
            <div className="text-gray-300">
              {tooltip || config.description}
            </div>
            <Tooltip.Arrow className="fill-gray-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}

// Convenience wrapper for inline usage
interface InlineDataSourceProps {
  type: DataSourceType;
  tooltip?: string;
}

export function InlineDataSource({ type, tooltip }: InlineDataSourceProps) {
  return (
    <span className="ml-2 inline-block">
      <DataSourceBadge type={type} tooltip={tooltip} size="sm" />
    </span>
  );
}
