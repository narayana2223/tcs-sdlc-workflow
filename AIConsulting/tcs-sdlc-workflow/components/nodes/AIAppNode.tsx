'use client';

import { Handle, Position } from '@xyflow/react';
import { Bot } from 'lucide-react';

interface AIAppNodeProps {
  data: {
    label: string;
    tools: string[]; // Specific tool names (Cursor, Devin, etc.)
    description?: string;
  };
}

export function AIAppNode({ data }: AIAppNodeProps) {
  return (
    <div className="w-[200px] cursor-pointer rounded-xl bg-[#E94B3C] px-5 py-4 shadow-lg transition-transform hover:scale-105">
      <Handle type="target" position={Position.Top} className="!bg-white !h-3 !w-3" />
      <Handle type="target" position={Position.Left} className="!bg-white !h-3 !w-3" />

      <div className="flex flex-col gap-2">
        <div className="flex items-start gap-2">
          <Bot size={20} className="mt-0.5 flex-shrink-0 text-white" />
          <div className="flex-1">
            <p className="text-base font-bold text-white leading-tight">{data.label}</p>
            <p className="mt-1 text-xs text-white/90">
              ({data.tools.join(', ')})
            </p>
            {data.description && (
              <p className="mt-1 text-xs text-white/75 italic">{data.description}</p>
            )}
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-white !h-3 !w-3" />
      <Handle type="source" position={Position.Bottom} className="!bg-white !h-3 !w-3" />
    </div>
  );
}
