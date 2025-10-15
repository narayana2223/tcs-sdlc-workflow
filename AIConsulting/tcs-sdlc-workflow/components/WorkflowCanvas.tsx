'use client';

import { Stage } from './Stage';
import stagesData from '@/data/stages.json';
import { Stage as StageType } from '@/lib/types';
import { ArrowRight } from 'lucide-react';

export function WorkflowCanvas() {
  // Convert stages object to array and sort by order
  const stages = Object.values(stagesData).sort(
    (a, b) => a.order - b.order
  ) as StageType[];

  return (
    <div className="relative">
      {/* Horizontal Scrollable Container */}
      <div className="horizontal-scroll overflow-x-auto overflow-y-hidden pb-8">
        <div className="flex items-center gap-6 px-8 py-8">
          {stages.map((stage, index) => (
            <div key={stage.id} className="flex items-center gap-6">
              <Stage stage={stage} />

              {/* Arrow connector between stages */}
              {index < stages.length - 1 && (
                <div className="flex flex-col items-center">
                  <ArrowRight
                    size={32}
                    className="text-gray-400"
                    strokeWidth={2}
                  />
                  <span className="mt-1 text-xs text-gray-500">Flow</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Scroll hint (shows on initial load) */}
      <div className="absolute bottom-2 right-8 flex items-center gap-2 text-xs text-gray-500">
        <span>Scroll horizontally to explore →</span>
      </div>
    </div>
  );
}
