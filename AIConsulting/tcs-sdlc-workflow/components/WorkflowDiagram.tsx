'use client';

import { useWorkflowStore } from '@/lib/store';
import stagesData from '@/data/stages.json';
import { Stage as StageType } from '@/lib/types';
import { Users, Bot, Settings, Database } from 'lucide-react';

export function WorkflowDiagram() {
  const { maturityLevel } = useWorkflowStore();

  // Convert stages object to array and sort by order
  const stages = Object.values(stagesData).sort(
    (a, b) => a.order - b.order
  ) as StageType[];

  return (
    <div className="relative bg-white p-8">
      {/* Workflow Container */}
      <div className="overflow-x-auto">
        <div className="inline-flex min-w-full flex-col gap-4" style={{ minWidth: '1800px' }}>

          {/* Lane Labels */}
          <div className="flex">
            <div className="w-32 flex-shrink-0" />
            <div className="flex flex-1 gap-6">
              {stages.map((stage) => (
                <div key={stage.id} className="flex-1 text-center">
                  <h3 className="text-sm font-bold text-gray-900">{stage.title}</h3>
                  <p className="text-xs text-gray-600">{stage.subtitle}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Swim Lane 1: HUMANS */}
          <div className="flex items-center">
            <div className="w-32 flex-shrink-0 pr-4 text-right">
              <div className="flex items-center justify-end gap-2">
                <Users size={16} className="text-[#4A90E2]" />
                <span className="text-xs font-semibold uppercase text-gray-700">Humans</span>
              </div>
            </div>
            <div className="relative flex flex-1 gap-6">
              {/* Connection Line */}
              <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-300" style={{ zIndex: 0 }} />

              {stages.map((stage, index) => (
                <div key={stage.id} className="relative flex-1" style={{ zIndex: 1 }}>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {stage.actors.map((actor, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border-2 border-[#4A90E2] bg-white px-3 py-2 text-xs font-medium shadow-sm"
                      >
                        <span className="mr-1">{actor.icon}</span>
                        {actor.role}
                      </div>
                    ))}
                  </div>
                  {/* Arrow to next stage */}
                  {index < stages.length - 1 && (
                    <div className="absolute -right-3 top-1/2 h-0 w-0 -translate-y-1/2 border-y-4 border-l-8 border-y-transparent border-l-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Swim Lane 2: AI APPLICATIONS */}
          <div className="flex items-center">
            <div className="w-32 flex-shrink-0 pr-4 text-right">
              <div className="flex items-center justify-end gap-2">
                <Bot size={16} className="text-[#E94B3C]" />
                <span className="text-xs font-semibold uppercase text-gray-700">AI Apps</span>
              </div>
            </div>
            <div className="relative flex flex-1 gap-6">
              {/* Connection Line */}
              <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-300" style={{ zIndex: 0 }} />

              {stages.map((stage, index) => (
                <div key={stage.id} className="relative flex-1" style={{ zIndex: 1 }}>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {stage.aiApplications.slice(0, 3).map((appId) => (
                      <div
                        key={appId}
                        className="cursor-pointer rounded-lg bg-[#E94B3C] px-3 py-2 text-xs font-medium text-white shadow-sm transition-opacity hover:opacity-90"
                      >
                        🤖 {appId}
                      </div>
                    ))}
                    {stage.aiApplications.length > 3 && (
                      <div className="rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
                        +{stage.aiApplications.length - 3}
                      </div>
                    )}
                  </div>
                  {/* Arrow to next stage */}
                  {index < stages.length - 1 && (
                    <div className="absolute -right-3 top-1/2 h-0 w-0 -translate-y-1/2 border-y-4 border-l-8 border-y-transparent border-l-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Swim Lane 3: INFRASTRUCTURE (only show for L4/L5) */}
          {maturityLevel !== 'L3' && (
            <div className="flex items-center">
              <div className="w-32 flex-shrink-0 pr-4 text-right">
                <div className="flex items-center justify-end gap-2">
                  <Settings size={16} className="text-[#F5A623]" />
                  <span className="text-xs font-semibold uppercase text-gray-700">Infrastructure</span>
                </div>
              </div>
              <div className="relative flex flex-1 gap-6">
                {/* Connection Line */}
                <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-300" style={{ zIndex: 0 }} />

                {stages.map((stage, index) => (
                  <div key={stage.id} className="relative flex-1" style={{ zIndex: 1 }}>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {stage.infrastructureTools.map((infraId) => (
                        <div
                          key={infraId}
                          className="rounded-lg bg-[#F5A623] px-3 py-2 text-xs font-medium text-black shadow-sm"
                        >
                          ⚙️ {infraId}
                        </div>
                      ))}
                    </div>
                    {/* Arrow to next stage */}
                    {index < stages.length - 1 && (
                      <div className="absolute -right-3 top-1/2 h-0 w-0 -translate-y-1/2 border-y-4 border-l-8 border-y-transparent border-l-gray-400" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Swim Lane 4: DATA / SYSTEM OF RECORD */}
          <div className="flex items-center">
            <div className="w-32 flex-shrink-0 pr-4 text-right">
              <div className="flex items-center justify-end gap-2">
                <Database size={16} className="text-[#D4C5B9]" />
                <span className="text-xs font-semibold uppercase text-gray-700">Data/SoR</span>
              </div>
            </div>
            <div className="relative flex flex-1 gap-6">
              {/* Connection Line */}
              <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-300" style={{ zIndex: 0 }} />

              {stages.map((stage, index) => (
                <div key={stage.id} className="relative flex-1" style={{ zIndex: 1 }}>
                  <div className="flex flex-col gap-2">
                    {stage.dataStores.map((ds, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-dashed border-[#999999] bg-[#D4C5B9] p-2 shadow-sm"
                      >
                        <p className="text-xs font-semibold text-gray-900">{ds.name}</p>
                        <ul className="mt-1 space-y-0.5">
                          {ds.artifacts.slice(0, 2).map((artifact, i) => (
                            <li key={i} className="text-xs text-gray-700">
                              • {artifact}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                  {/* Arrow to next stage */}
                  {index < stages.length - 1 && (
                    <div className="absolute -right-3 top-1/2 h-0 w-0 -translate-y-1/2 border-y-4 border-l-8 border-y-transparent border-l-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Metrics Row */}
          <div className="flex items-center border-t pt-4">
            <div className="w-32 flex-shrink-0 pr-4 text-right">
              <span className="text-xs font-semibold uppercase text-gray-700">Metrics</span>
            </div>
            <div className="flex flex-1 gap-6">
              {stages.map((stage) => {
                const metrics = stage.metrics[maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5'];
                return (
                  <div key={stage.id} className="flex-1 rounded-lg bg-gray-50 p-2 text-center">
                    <div className="grid grid-cols-3 gap-1 text-xs">
                      <div>
                        <p className="text-gray-600">Duration</p>
                        <p className="font-bold text-gray-900">{metrics.duration}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Gates</p>
                        <p className="font-bold text-gray-900">{metrics.humanTouchpoints}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Saved</p>
                        <p className="font-bold text-green-600">{metrics.timeSaved}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-sm border-2 border-[#4A90E2] bg-white" />
          <span>Human Actors</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-sm bg-[#E94B3C]" />
          <span>AI Applications</span>
        </div>
        {maturityLevel !== 'L3' && (
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-sm bg-[#F5A623]" />
            <span>Agent Infrastructure</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-sm border border-dashed border-gray-600 bg-[#D4C5B9]" />
          <span>System of Record</span>
        </div>
      </div>
    </div>
  );
}
