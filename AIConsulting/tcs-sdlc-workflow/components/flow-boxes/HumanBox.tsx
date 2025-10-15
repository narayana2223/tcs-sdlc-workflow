'use client';

import { Users } from 'lucide-react';

interface HumanBoxProps {
  role: string;
  icon?: string;
  onClick?: () => void;
}

export function HumanBox({ role, icon = '👤', onClick }: HumanBoxProps) {
  return (
    <div
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-lg bg-[#4A90E2] px-4 py-3 shadow-md transition-transform hover:scale-105 cursor-pointer"
      title={`Click to view ${role} details`}
    >
      <Users size={20} className="text-white flex-shrink-0" />
      <span className="text-sm font-semibold text-white whitespace-nowrap">{role}</span>
    </div>
  );
}
