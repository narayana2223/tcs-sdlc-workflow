'use client';

import { useState } from 'react';
import { useWorkflowStore } from '@/lib/store';
import { SoRHub } from './workflow-map/SoRHub';
import { HumanBox } from './flow-boxes/HumanBox';
import { AIBox } from './flow-boxes/AIBox';
import { DataBox } from './flow-boxes/DataBox';
import { LabeledConnection } from './workflow-map/LabeledConnection';
import { DiagramModal } from './DiagramModal';
import { layout, connections, getNodePosition } from './workflow-map/layout';
import { Bot } from 'lucide-react';
import mermaidData from '@/data/mermaid-diagrams.json';

export function A16ZWorkflowMap() {
  const { maturityLevel } = useWorkflowStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const isL3 = maturityLevel === 'L3';
  const isL4 = maturityLevel === 'L4';
  const isL5 = maturityLevel === 'L5';

  // Handle stage click to open modal
  const handleStageClick = (stage: string) => {
    setSelectedStage(stage);
    setModalOpen(true);
  };

  // Get diagram data for selected stage
  const getDiagramData = () => {
    if (!selectedStage) return null;

    interface MaturityLevelData {
      diagram: string;
      description: string;
    }

    interface StageData {
      title: string;
      l3: MaturityLevelData;
      l4: MaturityLevelData;
      l5: MaturityLevelData;
    }

    const stageData = (mermaidData as Record<string, StageData>)[selectedStage];
    if (!stageData) return null;

    const levelKey = maturityLevel.toLowerCase() as 'l3' | 'l4' | 'l5';
    const levelData = stageData[levelKey];

    return {
      title: stageData.title,
      diagram: levelData.diagram,
      description: levelData.description,
      maturityLevel: maturityLevel,
    };
  };

  const diagramData = getDiagramData();

  // Filter connections based on maturity level
  const visibleConnections = connections.filter(conn => {
    if (!conn.maturityLevel) return true;
    return conn.maturityLevel.includes(maturityLevel);
  });

  // Get node center position for connections
  const getNodeCenter = (nodeId: string, defaultWidth = 160, defaultHeight = 60) => {
    const pos = getNodePosition(nodeId);
    if (!pos) return { x: 0, y: 0 };

    const width = pos.width || defaultWidth;
    const height = pos.height || defaultHeight;

    return {
      x: pos.x + width / 2,
      y: pos.y + height / 2,
    };
  };

  return (
    <div className={`${isFullscreen ? 'fixed inset-0 z-[100]' : 'relative'} bg-[#FAF9F6] rounded-lg shadow-xl overflow-hidden`}>
      {/* Fullscreen Toggle Button */}
      <button
        onClick={() => setIsFullscreen(!isFullscreen)}
        className="absolute top-6 left-6 bg-white px-4 py-2 rounded-lg shadow-md border border-gray-200 z-50 hover:bg-gray-100 transition-colors flex items-center gap-2"
        title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
      >
        {isFullscreen ? (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
            </svg>
            <span className="text-sm font-semibold">Exit Fullscreen</span>
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
            <span className="text-sm font-semibold">Fullscreen View</span>
          </>
        )}
      </button>

      {/* Legend */}
      <div className="absolute top-6 right-6 bg-white p-4 rounded-lg shadow-md border border-gray-200 z-50">
        <h4 className="text-xs font-bold text-gray-700 mb-2">Key</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#4A90E2] rounded"></div>
            <span className="text-xs text-gray-700">Humans</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#E94B3C] rounded"></div>
            <span className="text-xs text-gray-700">AI Apps</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#D4C5B9] rounded"></div>
            <span className="text-xs text-gray-700">Data</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-12 h-6 bg-[#D4C5B9] border-2 border-dashed border-[#999] rounded"></div>
            <span className="text-xs text-gray-700">SoR</span>
          </div>
          {(isL4 || isL5) && (
            <div className="flex items-center gap-2">
              <div className="w-12 h-6 bg-[#F5A623] rounded"></div>
              <span className="text-xs text-gray-700">Infra</span>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable Canvas */}
      <div
        className="overflow-x-auto overflow-y-auto"
        style={{ maxHeight: isFullscreen ? '100vh' : '900px', height: isFullscreen ? '100vh' : 'auto' }}
      >
        <div
          className="relative"
          style={{
            width: `${layout.canvas.width}px`,
            height: `${layout.canvas.height}px`,
            minWidth: `${layout.canvas.minWidth}px`,
          }}
        >
          {/* SVG Layer for Connections */}
          <svg
            className="absolute inset-0 pointer-events-none"
            style={{ width: '100%', height: '100%', zIndex: 1 }}
          >
            {visibleConnections.map((conn) => {
              const start = getNodeCenter(conn.start);
              const end = getNodeCenter(conn.end);

              return (
                <LabeledConnection
                  key={conn.id}
                  start={start}
                  end={end}
                  label={conn.label}
                  type={conn.type}
                  color={conn.color}
                  curve={conn.curve}
                  animated={conn.animated}
                />
              );
            })}
          </svg>

          {/* Components Layer */}
          <div className="relative" style={{ zIndex: 2 }}>

            {/* ===== ZONE 1: REQUIREMENTS & FEEDBACK ===== */}
            <div className="absolute" style={{ left: layout.zones.requirements.users.x, top: layout.zones.requirements.users.y }}>
              <HumanBox role="Users" />
            </div>

            <div className="absolute" style={{ left: layout.zones.requirements.nexoro.x, top: layout.zones.requirements.nexoro.y }}>
              <AIBox tool="Nexoro" label="Aggregate Feedback" />
            </div>

            <div className="absolute" style={{ left: layout.zones.requirements.requirements.x, top: layout.zones.requirements.requirements.y }}>
              <DataBox artifact="Requirements" />
            </div>

            <div className="absolute" style={{ left: layout.zones.requirements.feedbackDB.x, top: layout.zones.requirements.feedbackDB.y }}>
              <SoRHub
                title="Customer Feedback DB"
                artifacts={[
                  'Categorized feedback',
                  'Sentiment analysis',
                  'Priority scores'
                ]}
                width={layout.zones.requirements.feedbackDB.width}
                height={layout.zones.requirements.feedbackDB.height}
              />
            </div>

            {/* ===== ZONE 2: PLANNING & WIKI/JIRA HUB ===== */}
            <div className="absolute" style={{ left: layout.zones.planning.pmArchitect.x, top: layout.zones.planning.pmArchitect.y }}>
              <HumanBox role="PM & Architect" />
            </div>

            <div className="absolute" style={{ left: layout.zones.planning.traycer.x, top: layout.zones.planning.traycer.y }}>
              <AIBox tool="Traycer" label="Planning & Architecture" />
            </div>

            <div className="absolute" style={{ left: layout.zones.planning.wikiJira.x, top: layout.zones.planning.wikiJira.y }}>
              <SoRHub
                title="Wiki/Jira"
                artifacts={[
                  'High Level Spec',
                  'Detailed Stories',
                  'Architecture Diagrams',
                  'Feature Requirements'
                ]}
                width={layout.zones.planning.wikiJira.width}
                height={layout.zones.planning.wikiJira.height}
                highlightColor="#7B68EE"
              />
            </div>

            {/* ===== ZONE 3: DESIGN TRACK ===== */}
            <div className="absolute" style={{ left: layout.zones.design.uiDesigner.x, top: layout.zones.design.uiDesigner.y }}>
              <HumanBox role="UI Designer" />
            </div>

            <div className="absolute" style={{ left: layout.zones.design.figma.x, top: layout.zones.design.figma.y }}>
              <AIBox tool="Figma" label="UI Design Tool with AI" />
            </div>

            <div className="absolute" style={{ left: layout.zones.design.uiAssets.x, top: layout.zones.design.uiAssets.y }}>
              <DataBox artifact="UI Assets" />
            </div>

            <div className="absolute" style={{ left: layout.zones.design.lovable.x, top: layout.zones.design.lovable.y }}>
              <AIBox tool="Lovable" label="Prototype UI & Applications" />
            </div>

            {/* ===== ZONE 4: DEVELOPMENT TRACK ===== */}
            <div className="absolute" style={{ left: layout.zones.development.swEngineer.x, top: layout.zones.development.swEngineer.y }}>
              <HumanBox role="SW Engineer" />
            </div>

            <div className="absolute" style={{ left: layout.zones.development.codingTool.x, top: layout.zones.development.codingTool.y }}>
              <AIBox
                tool={isL5 ? 'Devin' : 'Cursor'}
                label={isL5 ? 'Agentic Coding' : 'AI-Assisted IDE'}
              />
            </div>

            <div className="absolute" style={{ left: layout.zones.development.pr.x, top: layout.zones.development.pr.y }}>
              <DataBox artifact="PR" />
            </div>

            {(isL4 || isL5) && (
              <div className="absolute" style={{ left: layout.zones.development.coderabbit.x, top: layout.zones.development.coderabbit.y }}>
                <AIBox tool="CodeRabbit" label="PR Review" />
              </div>
            )}

            {/* ===== ZONE 5: GITHUB HUB ===== */}
            <div className="absolute" style={{ left: layout.zones.github.github.x, top: layout.zones.github.github.y }}>
              <SoRHub
                title="GitHub"
                artifacts={[
                  'Code Repository',
                  'UI Assets',
                  'Tests',
                  isL5 ? '95% Auto-merged PRs' : isL4 ? '70% Auto-merged PRs' : 'PR History',
                  'CI/CD Workflows'
                ]}
                width={layout.zones.github.github.width}
                height={layout.zones.github.github.height}
                highlightColor="#FF6B6B"
              />
            </div>

            {/* ===== ZONE 6: QA TRACK ===== */}
            <div className="absolute" style={{ left: layout.zones.qa.qaEngineer.x, top: layout.zones.qa.qaEngineer.y }}>
              <HumanBox role="QA Engineer" />
            </div>

            <div className="absolute" style={{ left: layout.zones.qa.qaTool.x, top: layout.zones.qa.qaTool.y }}>
              <AIBox
                tool={isL5 ? 'QA Wolf + Mabl' : 'QA Wolf'}
                label="AI Testing"
              />
            </div>

            <div className="absolute" style={{ left: layout.zones.qa.tests.x, top: layout.zones.qa.tests.y }}>
              <DataBox artifact="Tests" />
            </div>

            {/* ===== ZONE 7: DOCUMENTATION CLUSTER ===== */}
            <div className="absolute" style={{ left: layout.zones.documentation.docEditor.x, top: layout.zones.documentation.docEditor.y }}>
              <HumanBox role="Doc Editor" />
            </div>

            <div className="absolute" style={{ left: layout.zones.documentation.aiDoc.x, top: layout.zones.documentation.aiDoc.y }}>
              <AIBox tool="AI Doc" label="User Documentation" />
            </div>

            <div className="absolute" style={{ left: layout.zones.documentation.mintlify.x, top: layout.zones.documentation.mintlify.y }}>
              <AIBox tool="Mintlify" label="API Documentation" />
            </div>

            <div className="absolute" style={{ left: layout.zones.documentation.complianceAI.x, top: layout.zones.documentation.complianceAI.y }}>
              <AIBox tool="Delive" label="Compliance Docs" />
            </div>

            <div className="absolute" style={{ left: layout.zones.documentation.docsPortal.x, top: layout.zones.documentation.docsPortal.y }}>
              <SoRHub
                title="Docs Portal"
                artifacts={[
                  'User Documentation',
                  'API Documentation',
                  'Compliance Documentation'
                ]}
                width={layout.zones.documentation.docsPortal.width}
                height={layout.zones.documentation.docsPortal.height}
              />
            </div>

            {/* ===== ZONE 8: DEPLOYMENT ===== */}
            <div className="absolute" style={{ left: layout.zones.deployment.devops.x, top: layout.zones.deployment.devops.y }}>
              <HumanBox role="DevOps" />
            </div>

            <div className="absolute" style={{ left: layout.zones.deployment.harness.x, top: layout.zones.deployment.harness.y }}>
              <AIBox tool="Harness" label="CI/CD Pipeline" />
            </div>

            <div className="absolute" style={{ left: layout.zones.deployment.production.x, top: layout.zones.deployment.production.y }}>
              <SoRHub
                title="Production"
                artifacts={[
                  'Cloud Infrastructure',
                  'Deployed Applications',
                  'Monitoring & Alerts'
                ]}
                width={layout.zones.deployment.production.width}
                height={layout.zones.deployment.production.height}
              />
            </div>

            {/* ===== ZONE 9: OPERATIONS ===== */}
            <div className="absolute" style={{ left: layout.zones.operations.sreTeam.x, top: layout.zones.operations.sreTeam.y }}>
              <HumanBox role="SRE Team" />
            </div>

            <div className="absolute" style={{ left: layout.zones.operations.resolveAI.x, top: layout.zones.operations.resolveAI.y }}>
              <AIBox tool="Resolve.ai" label="AI Monitoring" />
            </div>

            <div className="absolute" style={{ left: layout.zones.operations.metricsDB.x, top: layout.zones.operations.metricsDB.y }}>
              <SoRHub
                title="Metrics & Logs DB"
                artifacts={[
                  'Application Metrics',
                  'System Logs',
                  isL5 ? '95% Auto-remediated' : isL4 ? '80% Auto-remediated' : 'Incident Reports'
                ]}
                width={layout.zones.operations.metricsDB.width}
                height={layout.zones.operations.metricsDB.height}
              />
            </div>

            {/* ===== INFRASTRUCTURE LAYER (L4/L5 only) ===== */}
            {(isL4 || isL5) && (
              <>
                <div className="absolute" style={{ left: layout.zones.infrastructure.e2b.x, top: layout.zones.infrastructure.e2b.y }}>
                  <div className="inline-flex items-center gap-2 rounded-lg bg-[#F5A623] px-3 py-2 shadow-md">
                    <Bot size={16} className="text-white" />
                    <span className="text-xs font-semibold text-white">e2b Sandbox</span>
                  </div>
                </div>

                <div className="absolute" style={{ left: layout.zones.infrastructure.buildbuddy.x, top: layout.zones.infrastructure.buildbuddy.y }}>
                  <div className="inline-flex items-center gap-2 rounded-lg bg-[#F5A623] px-3 py-2 shadow-md">
                    <Bot size={16} className="text-white" />
                    <span className="text-xs font-semibold text-white">BuildBuddy</span>
                  </div>
                </div>
              </>
            )}

            {isL5 && (
              <div className="absolute" style={{ left: layout.zones.infrastructure.conductor.x, top: layout.zones.infrastructure.conductor.y }}>
                <div className="inline-flex items-center gap-2 rounded-lg bg-[#F5A623] px-3 py-2 shadow-md border-2 border-orange-600">
                  <Bot size={16} className="text-white" />
                  <span className="text-xs font-semibold text-white">Conductor (Orchestration)</span>
                </div>
              </div>
            )}

          </div>

          {/* Maturity Level Indicator */}
          <div className="absolute bottom-6 left-6 bg-white px-6 py-3 rounded-lg shadow-lg border-2 border-gray-300 z-50">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-700">Current View:</span>
              <span className="text-lg font-bold text-[#E94B3C]">{maturityLevel}</span>
              <span className="text-xs text-gray-600">
                {isL3 && '(Supervised Agent - 95 gates)'}
                {isL4 && '(Autonomous Agent - 25 gates)'}
                {isL5 && '(Agentic Workforce - 8 gates)'}
              </span>
            </div>
          </div>

          {/* Clickable Zone Overlays for Stage Details */}
          <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 3 }}>
            {/* Zone 1: Requirements */}
            <button
              onClick={() => handleStageClick('requirements')}
              className="absolute pointer-events-auto bg-transparent hover:bg-blue-100/20 transition-all rounded-lg border-2 border-transparent hover:border-blue-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.requirements.users.x - 10,
                top: layout.zones.requirements.users.y - 10,
                width: layout.zones.requirements.feedbackDB.width! + 40,
                height: layout.zones.requirements.feedbackDB.y + layout.zones.requirements.feedbackDB.height! - layout.zones.requirements.users.y + 20,
              }}
              title="Click to see detailed Requirements workflow"
              aria-label="View Requirements workflow diagram"
            />

            {/* Zone 2: Planning */}
            <button
              onClick={() => handleStageClick('planning')}
              className="absolute pointer-events-auto bg-transparent hover:bg-purple-100/20 transition-all rounded-lg border-2 border-transparent hover:border-purple-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.planning.pmArchitect.x - 10,
                top: layout.zones.planning.pmArchitect.y - 10,
                width: layout.zones.planning.wikiJira.width! + 60,
                height: layout.zones.planning.wikiJira.y + layout.zones.planning.wikiJira.height! - layout.zones.planning.pmArchitect.y + 20,
              }}
              title="Click to see detailed Planning workflow"
              aria-label="View Planning workflow diagram"
            />

            {/* Zone 3: Design */}
            <button
              onClick={() => handleStageClick('design')}
              className="absolute pointer-events-auto bg-transparent hover:bg-pink-100/20 transition-all rounded-lg border-2 border-transparent hover:border-pink-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.design.uiDesigner.x - 10,
                top: layout.zones.design.uiDesigner.y - 10,
                width: 240,
                height: layout.zones.design.lovable.y - layout.zones.design.uiDesigner.y + 100,
              }}
              title="Click to see detailed Design workflow"
              aria-label="View Design workflow diagram"
            />

            {/* Zone 4: Development */}
            <button
              onClick={() => handleStageClick('development')}
              className="absolute pointer-events-auto bg-transparent hover:bg-red-100/20 transition-all rounded-lg border-2 border-transparent hover:border-red-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.development.swEngineer.x - 10,
                top: layout.zones.development.swEngineer.y - 10,
                width: 260,
                height: layout.zones.development.coderabbit.y - layout.zones.development.swEngineer.y + 100,
              }}
              title="Click to see detailed Development workflow"
              aria-label="View Development workflow diagram"
            />

            {/* Zone 6: Testing */}
            <button
              onClick={() => handleStageClick('testing')}
              className="absolute pointer-events-auto bg-transparent hover:bg-green-100/20 transition-all rounded-lg border-2 border-transparent hover:border-green-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.qa.qaEngineer.x - 10,
                top: layout.zones.qa.qaEngineer.y - 10,
                width: 260,
                height: layout.zones.qa.tests.y - layout.zones.qa.qaEngineer.y + 90,
              }}
              title="Click to see detailed Testing workflow"
              aria-label="View Testing workflow diagram"
            />

            {/* Zone 7: Documentation */}
            <button
              onClick={() => handleStageClick('documentation')}
              className="absolute pointer-events-auto bg-transparent hover:bg-yellow-100/20 transition-all rounded-lg border-2 border-transparent hover:border-yellow-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.documentation.docEditor.x - 10,
                top: layout.zones.documentation.docEditor.y - 10,
                width: layout.zones.documentation.docsPortal.width! + 140,
                height: layout.zones.documentation.docsPortal.y + layout.zones.documentation.docsPortal.height! - layout.zones.documentation.docEditor.y + 20,
              }}
              title="Click to see detailed Documentation workflow"
              aria-label="View Documentation workflow diagram"
            />

            {/* Zone 8: Deployment */}
            <button
              onClick={() => handleStageClick('deployment')}
              className="absolute pointer-events-auto bg-transparent hover:bg-orange-100/20 transition-all rounded-lg border-2 border-transparent hover:border-orange-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.deployment.devops.x - 10,
                top: layout.zones.deployment.devops.y - 10,
                width: layout.zones.deployment.production.width! + 130,
                height: layout.zones.deployment.production.y + layout.zones.deployment.production.height! - layout.zones.deployment.devops.y + 20,
              }}
              title="Click to see detailed Deployment workflow"
              aria-label="View Deployment workflow diagram"
            />

            {/* Zone 9: Operations */}
            <button
              onClick={() => handleStageClick('operations')}
              className="absolute pointer-events-auto bg-transparent hover:bg-cyan-100/20 transition-all rounded-lg border-2 border-transparent hover:border-cyan-500 hover:border-dashed cursor-pointer"
              style={{
                left: layout.zones.operations.sreTeam.x - 10,
                top: layout.zones.operations.sreTeam.y - 10,
                width: layout.zones.operations.metricsDB.width! + 130,
                height: layout.zones.operations.metricsDB.y + layout.zones.operations.metricsDB.height! - layout.zones.operations.sreTeam.y + 20,
              }}
              title="Click to see detailed Operations workflow"
              aria-label="View Operations workflow diagram"
            />
          </div>

        </div>
      </div>

      {/* Diagram Modal */}
      {diagramData && (
        <DiagramModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={diagramData.title}
          diagram={diagramData.diagram}
          description={diagramData.description}
          maturityLevel={diagramData.maturityLevel}
        />
      )}
    </div>
  );
}
