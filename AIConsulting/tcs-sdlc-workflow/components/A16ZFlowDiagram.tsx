'use client';

import { useWorkflowStore } from '@/lib/store';
import { HumanBox } from './flow-boxes/HumanBox';
import { AIBox } from './flow-boxes/AIBox';
import { DataBox } from './flow-boxes/DataBox';
import { SoRBox } from './flow-boxes/SoRBox';
import { Arrow } from './flow-boxes/Arrow';
import { BidirectionalArrow } from './flow-boxes/BidirectionalArrow';

export function A16ZFlowDiagram() {
  const { maturityLevel } = useWorkflowStore();

  const isL4 = maturityLevel === 'L4';
  const isL5 = maturityLevel === 'L5';

  return (
    <div className="overflow-x-auto bg-[#FAF9F6] p-8 rounded-lg">
      {/* Legend */}
      <div className="absolute top-8 right-8 bg-white p-4 rounded-lg shadow-md border border-gray-200">
        <h4 className="text-xs font-bold text-gray-700 mb-2">Key</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#4A90E2] rounded"></div>
            <span className="text-xs text-gray-700">Humans</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#D4C5B9] rounded"></div>
            <span className="text-xs text-gray-700">Data</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#E94B3C] rounded"></div>
            <span className="text-xs text-gray-700">AI</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#D4C5B9] border-2 border-dashed border-[#999] rounded"></div>
            <span className="text-xs text-gray-700">SoR</span>
          </div>
        </div>
      </div>

      {/* Flow Container */}
      <div className="flex gap-8 pb-8" style={{ minWidth: '2400px' }}>
        {/* STAGE 1: Input */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[200px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Requirements</div>
          <HumanBox role="Users" />
          <Arrow direction="down" />
          <AIBox tool="Nexoro" label="Aggregate Feedback" />
          <Arrow direction="down" />
          <DataBox artifact="Requirements" />
          <Arrow direction="down" dashed />
          <SoRBox system="Customer Feedback DB" contains={["Categorized feedback", "Sentiment analysis"]} />
        </div>

        {/* STAGE 2: Planning */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[220px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Planning</div>
          <HumanBox role="PM & Architect" />
          <Arrow direction="down" />
          <AIBox tool="Traycer" label="Planning & Architecture" />
          <Arrow direction="down" />
          <DataBox artifact="High Level Spec" />
          <Arrow direction="down" dashed />
          <SoRBox system="Wiki/Jira" contains={["High Level Spec", "Detailed Stories"]} />
          <Arrow direction="down" />
          <DataBox artifact="Detailed Spec" />
        </div>

        {/* STAGE 3: Design */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[200px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Design</div>
          <div className="flex items-center gap-2">
            <HumanBox role="UI Designer" />
            <BidirectionalArrow direction="horizontal" />
            <AIBox tool="Figma" label="UI Design Tool with AI" />
          </div>
          <Arrow direction="down" />
          <DataBox artifact="UI Assets" />
          <Arrow direction="down" />
          <AIBox tool="Lovable" label="Prototype UI & Applications" />
        </div>

        {/* STAGE 4: Development */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[240px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Development</div>
          <div className="flex items-center gap-2">
            <HumanBox role="SW Engineer" />
            <BidirectionalArrow direction="horizontal" />
            <AIBox tool={isL5 ? "Devin" : "Cursor"} label={isL5 ? "Agentic" : "AI-Assisted IDE"} />
          </div>
          <Arrow direction="down" />
          <DataBox artifact="PR" />
          <Arrow direction="down" />
          <AIBox tool="CodeRabbit" label="PR Review" />
          {isL4 || isL5 ? (
            <>
              <Arrow direction="down" animated />
              <DataBox artifact="Code & PRs" />
              <Arrow direction="down" dashed />
              <SoRBox system="GitHub" contains={isL5 ? ["70% Auto-merged PRs", "Code Repository"] : ["Code Repository", "PR History"]} />
            </>
          ) : (
            <>
              <Arrow direction="down" />
              <DataBox artifact="Code & PRs" />
              <Arrow direction="down" dashed />
              <SoRBox system="GitHub" contains={["Code Repository"]} />
            </>
          )}
        </div>

        {/* STAGE 5: Testing */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[220px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Testing</div>
          <div className="flex items-center gap-2">
            <HumanBox role="QA Engineer" />
            <BidirectionalArrow direction="horizontal" />
            <AIBox tool={isL5 ? "QA Wolf + Mabl" : "QA Wolf"} label="AI Testing" />
          </div>
          <Arrow direction="down" />
          <DataBox artifact="Tests" />
          <Arrow direction="down" />
          <DataBox artifact="Test Results" />
        </div>

        {/* STAGE 6: Documentation */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[200px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Documentation</div>
          <HumanBox role="Doc Editor" />
          <Arrow direction="down" />
          <AIBox tool="Mintlify" label="AI Doc" />
          <Arrow direction="down" />
          <DataBox artifact="User Docs" />
          <Arrow direction="down" />
          <DataBox artifact="API Docs" />
          <Arrow direction="down" />
          <DataBox artifact="Compliance Docs" />
        </div>

        {/* STAGE 7: Deployment */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[200px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Deployment</div>
          <HumanBox role="DevOps" />
          <Arrow direction="down" />
          <AIBox tool="Harness" label="CI/CD Pipeline" />
          <Arrow direction="down" />
          <DataBox artifact="Production" />
        </div>

        {/* STAGE 8: Operations */}
        <div className="flex flex-col items-center bg-white/50 rounded-lg p-6 min-w-[220px]">
          <div className="text-xs font-bold text-gray-600 mb-4 uppercase">Operations</div>
          <div className="flex items-center gap-2">
            <HumanBox role="SRE Team" />
            <BidirectionalArrow direction="horizontal" />
            <AIBox tool="Resolve.ai" label="AI Monitoring" />
          </div>
          <Arrow direction="down" />
          <DataBox artifact="Metrics & Logs" />
          <Arrow direction="down" />
          <DataBox artifact={isL5 ? "80% Auto-remediated" : "Incident Reports"} />
        </div>
      </div>
    </div>
  );
}
