'use client';

import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeTypes,
  ConnectionLineType,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { HumanNode } from './nodes/HumanNode';
import { AIAppNode } from './nodes/AIAppNode';
import { InfraNode } from './nodes/InfraNode';
import { DataNode } from './nodes/DataNode';
import { useWorkflowStore } from '@/lib/store';

const nodeTypes: NodeTypes = {
  human: HumanNode,
  aiApp: AIAppNode,
  infra: InfraNode,
  data: DataNode,
};

export function SDLCFlowDiagram() {
  const { maturityLevel } = useWorkflowStore();

  // Define nodes - A16Z CORRECT STRUCTURE: AI Apps as primary workflow
  const nodes: Node[] = useMemo(() => {
    const l3Tools = maturityLevel === 'L3';
    const l4Tools = maturityLevel === 'L4';
    const l5Tools = maturityLevel === 'L5';

    // Stage X positions (WIDER spacing for clean A16Z style)
    const STAGE_1_X = 100;
    const STAGE_2_X = 600;
    const STAGE_3_X = 1100;
    const STAGE_4_X = 1600;
    const STAGE_5_X = 2100;
    const STAGE_6_X = 2600;

    // Layer Y positions (CONSISTENT horizontal lines)
    const HUMAN_Y = 40;
    const AI_APP_Y = 200;  // AI Apps are PRIMARY
    const OUTPUT_Y = 420;  // Data outputs
    const SOR_Y = 600;     // System of Record
    const INFRA_Y = 800;   // Infrastructure

    const baseNodes: Node[] = [
      // ===== STAGE 1: User Feedback =====
      { id: 'users', type: 'human', position: { x: STAGE_1_X, y: HUMAN_Y }, data: { label: 'Users' } },
      {
        id: 'aggregate-feedback',
        type: 'aiApp',
        position: { x: STAGE_1_X - 50, y: AI_APP_Y },
        data: {
          label: 'Aggregate Feedback',
          tools: ['Nexoro'],
        }
      },
      { id: 'requirements', type: 'data', position: { x: STAGE_1_X - 20, y: OUTPUT_Y }, data: { label: 'Requirements' } },
      { id: 'feedback-db', type: 'data', position: { x: STAGE_1_X - 20, y: SOR_Y }, data: { label: 'Customer Feedback DB', isSystemOfRecord: true } },

      // ===== STAGE 2: Planning =====
      { id: 'pm-architect', type: 'human', position: { x: STAGE_2_X, y: HUMAN_Y }, data: { label: 'PM & Architect' } },
      {
        id: 'planning',
        type: 'aiApp',
        position: { x: STAGE_2_X - 80, y: AI_APP_Y },
        data: {
          label: 'Planning & Architecture',
          tools: ['Traycer'],
        }
      },
      { id: 'specs', type: 'data', position: { x: STAGE_2_X - 30, y: OUTPUT_Y }, data: { label: 'Specs & Architecture' } },
      { id: 'wiki-jira', type: 'data', position: { x: STAGE_2_X - 30, y: SOR_Y }, data: { label: 'Wiki/Jira', isSystemOfRecord: true } },

      // ===== STAGE 3: Build =====
      { id: 'sw-engineer', type: 'human', position: { x: STAGE_3_X, y: HUMAN_Y }, data: { label: 'SW Engineer' } },
      {
        id: 'coding-tool',
        type: 'aiApp',
        position: { x: STAGE_3_X - 80, y: AI_APP_Y },
        data: {
          label: l5Tools ? 'Agentic Coding' : 'AI-Assisted IDE',
          tools: l5Tools ? ['Devin', 'Cursor'] : l4Tools ? ['Cursor', 'CodeRabbit'] : ['Cursor'],
        }
      },
      { id: 'code', type: 'data', position: { x: STAGE_3_X - 30, y: OUTPUT_Y }, data: { label: 'Code & PRs' } },
      { id: 'github', type: 'data', position: { x: STAGE_3_X - 30, y: SOR_Y }, data: { label: 'GitHub', isSystemOfRecord: true } },

      // ===== STAGE 4: QA =====
      { id: 'qa-engineer', type: 'human', position: { x: STAGE_4_X, y: HUMAN_Y }, data: { label: 'QA Engineer' } },
      {
        id: 'qa-tool',
        type: 'aiApp',
        position: { x: STAGE_4_X - 80, y: AI_APP_Y },
        data: {
          label: 'AI Testing',
          tools: l5Tools ? ['QA Wolf', 'Mabl'] : ['QA Wolf'],
        }
      },
      { id: 'tests', type: 'data', position: { x: STAGE_4_X - 30, y: OUTPUT_Y }, data: { label: 'Tests' } },

      // ===== STAGE 5: Documentation =====
      { id: 'doc-editor', type: 'human', position: { x: STAGE_5_X, y: HUMAN_Y }, data: { label: 'Doc Editor' } },
      {
        id: 'ai-doc',
        type: 'aiApp',
        position: { x: STAGE_5_X - 80, y: AI_APP_Y },
        data: {
          label: 'AI Documentation',
          tools: ['Mintlify'],
        }
      },
      { id: 'docs', type: 'data', position: { x: STAGE_5_X - 30, y: OUTPUT_Y }, data: { label: 'Documentation' } },

      // ===== STAGE 6: Deploy =====
      { id: 'devops', type: 'human', position: { x: STAGE_6_X, y: HUMAN_Y }, data: { label: 'DevOps' } },
      {
        id: 'deploy',
        type: 'aiApp',
        position: { x: STAGE_6_X - 80, y: AI_APP_Y },
        data: {
          label: 'CI/CD Pipeline',
          tools: l5Tools ? ['Harness', 'ArgoCD'] : ['Harness'],
        }
      },
      { id: 'production', type: 'data', position: { x: STAGE_6_X - 30, y: OUTPUT_Y }, data: { label: 'Production' } },
    ];

    // Add infrastructure layer for L4/L5 (REDUCED - only key tools)
    if (maturityLevel !== 'L3') {
      const infraNodes: Node[] = [
        // Key infrastructure only
        { id: 'e2b', type: 'infra', position: { x: STAGE_3_X - 50, y: INFRA_Y }, data: { label: 'e2b', purpose: 'Sandbox' } },
        { id: 'buildbuddy', type: 'infra', position: { x: STAGE_4_X - 50, y: INFRA_Y }, data: { label: 'BuildBuddy', purpose: 'Build cache' } },
      ];

      if (l5Tools) {
        infraNodes.push(
          { id: 'conductor', type: 'infra', position: { x: STAGE_2_X - 50, y: INFRA_Y }, data: { label: 'conductor', purpose: 'Orchestration' } },
        );
      }

      baseNodes.push(...infraNodes);
    }

    return baseNodes;
  }, [maturityLevel]);

  // Define edges - SIMPLIFIED A16Z PATTERN: Clean left-to-right flow
  const edges: Edge[] = useMemo(() => {
    const baseEdges: Edge[] = [
      // Stage 1: Users → Aggregate Feedback → Requirements
      { id: 'e-users-aggregate', source: 'users', target: 'aggregate-feedback', animated: true },
      { id: 'e-aggregate-req', source: 'aggregate-feedback', target: 'requirements' },
      { id: 'e-aggregate-db', source: 'aggregate-feedback', target: 'feedback-db' },
      { id: 'e-req-db', source: 'requirements', target: 'feedback-db' },

      // Stage 1 → 2: Requirements → PM → Planning
      { id: 'e-req-pm', source: 'requirements', target: 'pm-architect', animated: true },
      { id: 'e-pm-planning', source: 'pm-architect', target: 'planning' },
      { id: 'e-planning-specs', source: 'planning', target: 'specs' },
      { id: 'e-specs-wiki', source: 'specs', target: 'wiki-jira' },

      // Stage 2 → 3: Specs → Engineer → Coding
      { id: 'e-specs-engineer', source: 'specs', target: 'sw-engineer', animated: true },
      { id: 'e-engineer-coding', source: 'sw-engineer', target: 'coding-tool' },
      { id: 'e-coding-code', source: 'coding-tool', target: 'code' },
      { id: 'e-code-github', source: 'code', target: 'github' },

      // Stage 3 → 4: Code → QA → Testing
      { id: 'e-code-qa', source: 'code', target: 'qa-engineer', animated: true },
      { id: 'e-qa-qatool', source: 'qa-engineer', target: 'qa-tool' },
      { id: 'e-qatool-tests', source: 'qa-tool', target: 'tests' },

      // Stage 4 → 5: Tests → Doc Editor → Documentation
      { id: 'e-tests-doceditor', source: 'tests', target: 'doc-editor', animated: true },
      { id: 'e-doceditor-aidoc', source: 'doc-editor', target: 'ai-doc' },
      { id: 'e-aidoc-docs', source: 'ai-doc', target: 'docs' },

      // Stage 5 → 6: Docs → DevOps → Deploy
      { id: 'e-docs-devops', source: 'docs', target: 'devops', animated: true },
      { id: 'e-github-devops', source: 'github', target: 'devops', style: { strokeDasharray: '5,5', opacity: 0.5 } },
      { id: 'e-devops-deploy', source: 'devops', target: 'deploy' },
      { id: 'e-deploy-production', source: 'deploy', target: 'production' },
    ];

    // Infrastructure connections (SUBTLE orange dashed, reduced opacity)
    if (maturityLevel !== 'L3') {
      const infraEdges: Edge[] = [
        { id: 'e-coding-e2b', source: 'coding-tool', target: 'e2b', style: { stroke: '#F5A623', strokeWidth: 1, strokeDasharray: '3,3', opacity: 0.4 } },
        { id: 'e-qa-buildbuddy', source: 'qa-tool', target: 'buildbuddy', style: { stroke: '#F5A623', strokeWidth: 1, strokeDasharray: '3,3', opacity: 0.4 } },
      ];

      if (maturityLevel === 'L5') {
        infraEdges.push(
          { id: 'e-planning-conductor', source: 'planning', target: 'conductor', style: { stroke: '#F5A623', strokeWidth: 1, strokeDasharray: '3,3', opacity: 0.4 } },
        );
      }

      baseEdges.push(...infraEdges);
    }

    return baseEdges.map(edge => ({
      ...edge,
      type: ConnectionLineType.SmoothStep,
      markerEnd: { type: MarkerType.ArrowClosed, width: 15, height: 15 },
    }));
  }, [maturityLevel]);

  return (
    <div className="h-[800px] w-full rounded-lg border-2 border-gray-300 bg-white shadow-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.5,
          maxZoom: 1,
        }}
        minZoom={0.3}
        maxZoom={1.2}
        defaultEdgeOptions={{
          type: ConnectionLineType.SmoothStep,
          animated: false,
        }}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={true}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            switch (node.type) {
              case 'human': return '#4A90E2';
              case 'aiApp': return '#E94B3C';
              case 'infra': return '#F5A623';
              case 'data': return '#D4C5B9';
              default: return '#ccc';
            }
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{ backgroundColor: '#f9fafb' }}
        />
      </ReactFlow>
    </div>
  );
}
