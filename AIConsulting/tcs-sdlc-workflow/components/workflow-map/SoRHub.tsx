'use client';

import { Server } from 'lucide-react';

interface SoRHubProps {
  title: string;
  artifacts: string[];
  width?: number;
  height?: number;
  className?: string;
  highlightColor?: string;
}

export function SoRHub({
  title,
  artifacts,
  width = 400,
  height = 280,
  className = '',
  highlightColor = '#999'
}: SoRHubProps) {
  return (
    <div
      className={`relative rounded-xl border-4 border-dashed bg-[#FAF9F6] p-6 shadow-lg transition-all hover:shadow-xl ${className}`}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        borderColor: highlightColor,
        zIndex: 10,
        position: 'relative',
      }}
    >
      {/* Header */}
      <div className="mb-4 flex items-center gap-3 border-b-2 border-gray-300 pb-3">
        <Server size={24} className="text-gray-700 flex-shrink-0" />
        <h3 className="text-lg font-bold text-gray-900">{title}</h3>
      </div>

      {/* Artifacts Grid - No scrollbar, displays all items */}
      <div className="grid grid-cols-1 gap-2">
        {artifacts.map((artifact, idx) => (
          <div
            key={idx}
            className="rounded-lg bg-white px-3 py-2 shadow-sm border border-gray-200"
          >
            <div className="flex items-start gap-2">
              <span className="text-gray-400 font-mono text-xs mt-0.5">•</span>
              <span className="text-sm font-medium text-gray-800 leading-tight">
                {artifact}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* System of Record Badge */}
      <div className="absolute top-2 right-2">
        <span className="inline-block rounded-full bg-gray-700 px-2 py-1 text-xs font-bold text-white">
          SoR
        </span>
      </div>
    </div>
  );
}
