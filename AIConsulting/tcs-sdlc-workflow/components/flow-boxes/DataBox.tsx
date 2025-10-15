'use client';

import { Database } from 'lucide-react';

interface DataBoxProps {
  artifact: string;
  onClick?: () => void;
}

export function DataBox({ artifact, onClick }: DataBoxProps) {
  return (
    <div
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-lg bg-[#D4C5B9] px-4 py-3 shadow-sm transition-transform hover:scale-105 cursor-pointer"
      title={`Click to view ${artifact} details`}
    >
      <Database size={16} className="text-gray-700 flex-shrink-0" />
      <span className="text-sm font-semibold text-gray-900 whitespace-nowrap">{artifact}</span>
    </div>
  );
}
