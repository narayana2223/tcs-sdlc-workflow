'use client';

import { Handle, Position } from '@xyflow/react';
import { Users } from 'lucide-react';

interface HumanNodeProps {
  data: {
    label: string;
    icon?: string;
  };
}

export function HumanNode({ data }: HumanNodeProps) {
  return (
    <div className="rounded-xl border-2 border-[#4A90E2] bg-white px-4 py-3 shadow-md">
      <Handle type="target" position={Position.Left} className="!bg-[#4A90E2]" />
      <div className="flex items-center gap-2">
        <Users size={18} className="text-[#4A90E2]" />
        <div>
          <p className="text-sm font-semibold text-gray-900">{data.label}</p>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-[#4A90E2]" />
      <Handle type="source" position={Position.Bottom} className="!bg-[#4A90E2]" />
    </div>
  );
}
