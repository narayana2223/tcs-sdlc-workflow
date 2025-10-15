'use client';

import { Bot } from 'lucide-react';

interface AIBoxProps {
  tool: string;
  label: string;
  onClick?: () => void;
}

export function AIBox({ tool, label, onClick }: AIBoxProps) {
  return (
    <div
      onClick={onClick}
      className="inline-flex flex-col gap-1 rounded-lg bg-[#E94B3C] px-4 py-3 shadow-md transition-transform hover:scale-105 cursor-pointer min-w-[180px]"
      title={`Click to view ${tool} details`}
    >
      <div className="flex items-center gap-2">
        <Bot size={18} className="text-white flex-shrink-0" />
        <span className="text-sm font-bold text-white">{label}</span>
      </div>
      <span className="text-xs text-white/90">({tool})</span>
    </div>
  );
}
