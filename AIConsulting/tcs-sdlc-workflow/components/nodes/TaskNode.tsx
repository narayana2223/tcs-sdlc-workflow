'use client';

import { Handle, Position } from '@xyflow/react';
import { FileText } from 'lucide-react';

interface TaskNodeProps {
  data: {
    label: string;
    aiTools?: string[]; // AI tools that help with this task
    description?: string;
  };
}

export function TaskNode({ data }: TaskNodeProps) {
  return (
    <div className="min-w-[160px] rounded-lg bg-[#D4C5B9] px-4 py-3 shadow-md">
      <Handle type="target" position={Position.Top} className="!bg-[#8B7355]" />
      <Handle type="target" position={Position.Left} className="!bg-[#8B7355]" />

      <div className="flex flex-col gap-2">
        <div className="flex items-start gap-2">
          <FileText size={16} className="mt-0.5 flex-shrink-0 text-gray-700" />
          <div className="flex-1">
            <p className="text-sm font-bold text-gray-900">{data.label}</p>
            {data.description && (
              <p className="mt-0.5 text-xs text-gray-700">{data.description}</p>
            )}
          </div>
        </div>

        {/* AI Tools as enablers/annotations */}
        {data.aiTools && data.aiTools.length > 0 && (
          <div className="flex flex-wrap gap-1 border-t border-gray-400 pt-2">
            {data.aiTools.map((tool, idx) => (
              <div
                key={idx}
                className="rounded bg-[#E94B3C] px-2 py-0.5 text-xs font-medium text-white"
              >
                {tool}
              </div>
            ))}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!bg-[#8B7355]" />
      <Handle type="source" position={Position.Bottom} className="!bg-[#8B7355]" />
    </div>
  );
}
