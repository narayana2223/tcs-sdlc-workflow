'use client';

import { Handle, Position } from '@xyflow/react';
import { FileText } from 'lucide-react';

interface DataNodeProps {
  data: {
    label: string;
    isSystemOfRecord?: boolean; // For dashed border
  };
}

export function DataNode({ data }: DataNodeProps) {
  return (
    <div
      className={`w-[160px] rounded-lg bg-[#D4C5B9] px-4 py-3 shadow-sm ${
        data.isSystemOfRecord
          ? 'border-2 border-dashed border-[#8B7355]'
          : 'border border-[#A89780]'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-[#8B7355] !h-2 !w-2" />
      <Handle type="target" position={Position.Left} className="!bg-[#8B7355] !h-2 !w-2" />

      <div className="flex items-center justify-center gap-2">
        <FileText size={16} className="text-gray-800" />
        <p className="text-sm font-bold text-gray-900 text-center">{data.label}</p>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-[#8B7355] !h-2 !w-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-[#8B7355] !h-2 !w-2" />
    </div>
  );
}
