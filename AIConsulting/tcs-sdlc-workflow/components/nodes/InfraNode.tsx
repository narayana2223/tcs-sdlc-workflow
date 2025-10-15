'use client';

import { Handle, Position } from '@xyflow/react';
import { Settings } from 'lucide-react';

interface InfraNodeProps {
  data: {
    label: string;
    purpose?: string;
  };
}

export function InfraNode({ data }: InfraNodeProps) {
  return (
    <div className="rounded-lg bg-[#F5A623] px-3 py-2 shadow-md">
      <Handle type="target" position={Position.Top} className="!bg-black" />
      <div className="flex items-center gap-2">
        <Settings size={14} className="text-black" />
        <div>
          <p className="text-xs font-semibold text-black">{data.label}</p>
          {data.purpose && (
            <p className="text-xs text-black/70">{data.purpose}</p>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-black" />
    </div>
  );
}
