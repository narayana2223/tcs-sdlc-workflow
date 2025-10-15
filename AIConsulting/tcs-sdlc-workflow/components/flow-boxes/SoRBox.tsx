'use client';

import { Server } from 'lucide-react';

interface SoRBoxProps {
  system: string;
  contains?: string[];
  onClick?: () => void;
}

export function SoRBox({ system, contains, onClick }: SoRBoxProps) {
  return (
    <div
      onClick={onClick}
      className="inline-flex flex-col gap-1 rounded-lg border-2 border-dashed border-[#999999] bg-[#D4C5B9] px-4 py-3 shadow-sm transition-transform hover:scale-105 cursor-pointer min-w-[180px]"
      title={`System of Record: ${system}`}
    >
      <div className="flex items-center gap-2">
        <Server size={16} className="text-gray-700 flex-shrink-0" />
        <span className="text-sm font-bold text-gray-900">{system}</span>
      </div>
      {contains && contains.length > 0 && (
        <ul className="mt-1 space-y-0.5">
          {contains.map((item, idx) => (
            <li key={idx} className="text-xs text-gray-700">
              • {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
