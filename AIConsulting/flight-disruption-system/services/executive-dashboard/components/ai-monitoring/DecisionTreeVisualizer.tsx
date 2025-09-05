'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  GitBranch, 
  ArrowRight, 
  Brain, 
  Users, 
  Cpu, 
  MessageCircle, 
  Target,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Activity,
  Maximize,
  Minimize
} from 'lucide-react';

interface AgentDecision {
  id: string;
  agentType: 'prediction' | 'passenger' | 'resource' | 'communication' | 'coordinator';
  timestamp: Date;
  decision: string;
  reasoning: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  cost?: number;
  passengersBenefited?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  executionTime?: number;
  parentDecisionId?: string;
  childDecisions?: string[];
}

interface DecisionTreeVisualizerProps {
  decisions: AgentDecision[];
  selectedDecision?: string | null;
}

interface TreeNode {
  decision: AgentDecision;
  children: TreeNode[];
  level: number;
  x: number;
  y: number;
  expanded: boolean;
}

const agentIcons = {
  prediction: Brain,
  passenger: Users,
  resource: Cpu,
  communication: MessageCircle,
  coordinator: Target
};

const agentColors = {
  prediction: 'purple',
  passenger: 'blue', 
  resource: 'green',
  communication: 'orange',
  coordinator: 'red'
};

const statusIcons = {
  pending: Clock,
  processing: Activity,
  completed: CheckCircle,
  failed: XCircle
};

const statusColors = {
  pending: 'slate',
  processing: 'yellow',
  completed: 'green',
  failed: 'red'
};

const impactColors = {
  low: 'slate',
  medium: 'yellow',
  high: 'orange',
  critical: 'red'
};

export default function DecisionTreeVisualizer({ decisions, selectedDecision }: DecisionTreeVisualizerProps) {
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<string | null>(selectedDecision || null);
  const [viewMode, setViewMode] = useState<'tree' | 'timeline'>('tree');
  const svgRef = useRef<SVGSVGElement>(null);

  // Build decision tree structure
  useEffect(() => {
    const buildTree = () => {
      // Create a map of decisions
      const decisionMap = new Map(decisions.map(d => [d.id, d]));
      
      // Find root nodes (decisions without parents or parents not in current set)
      const rootDecisions = decisions.filter(d => 
        !d.parentDecisionId || !decisionMap.has(d.parentDecisionId)
      );

      // Build tree nodes recursively
      const buildNode = (decision: AgentDecision, level: number = 0): TreeNode => {
        const children = (decision.childDecisions || [])
          .map(childId => decisionMap.get(childId))
          .filter(Boolean)
          .map(child => buildNode(child!, level + 1));

        return {
          decision,
          children,
          level,
          x: 0,
          y: 0,
          expanded: expandedNodes.has(decision.id) || level === 0
        };
      };

      const trees = rootDecisions.map(root => buildNode(root));
      
      // Calculate positions
      let currentY = 0;
      const nodeHeight = 120;
      const levelWidth = 300;

      const positionNodes = (nodes: TreeNode[], startY: number = 0): number => {
        let y = startY;
        
        for (const node of nodes) {
          node.x = node.level * levelWidth;
          node.y = y;
          y += nodeHeight;
          
          if (node.expanded && node.children.length > 0) {
            y = positionNodes(node.children, y);
          }
        }
        
        return y;
      };

      positionNodes(trees);
      setTreeData(trees);
    };

    buildTree();
  }, [decisions, expandedNodes]);

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getColorClass = (color: string, variant: 'bg' | 'text' | 'border' = 'bg') => {
    const colorMap = {
      purple: { bg: 'bg-purple-500', text: 'text-purple-600', border: 'border-purple-200' },
      blue: { bg: 'bg-blue-500', text: 'text-blue-600', border: 'border-blue-200' },
      green: { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-200' },
      orange: { bg: 'bg-orange-500', text: 'text-orange-600', border: 'border-orange-200' },
      red: { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-200' },
      yellow: { bg: 'bg-yellow-500', text: 'text-yellow-600', border: 'border-yellow-200' },
      slate: { bg: 'bg-slate-500', text: 'text-slate-600', border: 'border-slate-200' }
    };
    return colorMap[color as keyof typeof colorMap]?.[variant] || colorMap.slate[variant];
  };

  const renderNode = (node: TreeNode, index: number) => {
    const AgentIcon = agentIcons[node.decision.agentType];
    const StatusIcon = statusIcons[node.decision.status];
    const agentColor = agentColors[node.decision.agentType];
    const statusColor = statusColors[node.decision.status];
    const impactColor = impactColors[node.decision.impact];
    
    const isSelected = selectedNode === node.decision.id;
    const hasChildren = node.children.length > 0;

    return (
      <g key={node.decision.id}>
        {/* Connection lines to children */}
        {node.expanded && node.children.map((child, childIndex) => (
          <line
            key={`line-${node.decision.id}-${child.decision.id}`}
            x1={node.x + 280}
            y1={node.y + 50}
            x2={child.x}
            y2={child.y + 50}
            stroke="#e2e8f0"
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
          />
        ))}
        
        {/* Node container */}
        <g 
          transform={`translate(${node.x}, ${node.y})`}
          onClick={() => setSelectedNode(node.decision.id)}
          className="cursor-pointer"
        >
          {/* Main node rectangle */}
          <rect
            width="280"
            height="100"
            rx="8"
            fill={isSelected ? '#f8fafc' : 'white'}
            stroke={isSelected ? '#8b5cf6' : '#e2e8f0'}
            strokeWidth={isSelected ? 2 : 1}
            className="hover:stroke-slate-400 transition-colors"
          />
          
          {/* Agent icon and type */}
          <g transform="translate(12, 12)">
            <rect
              width="24"
              height="24"
              rx="6"
              className={getColorClass(agentColor)}
            />
            <AgentIcon 
              className="w-4 h-4 text-white" 
              style={{ transform: 'translate(4px, 4px)' }}
            />
          </g>
          
          {/* Status indicator */}
          <g transform="translate(44, 12)">
            <rect
              width="20"
              height="20"
              rx="4"
              className={`${getColorClass(statusColor)} bg-opacity-20`}
            />
            <StatusIcon 
              className={`w-3 h-3 ${getColorClass(statusColor, 'text')}`}
              style={{ transform: 'translate(2px, 2px)' }}
            />
          </g>

          {/* Decision text */}
          <text
            x="12"
            y="52"
            className="text-sm font-semibold fill-slate-800"
            textLength="250"
            lengthAdjust="spacingAndGlyphs"
          >
            {node.decision.decision.length > 35 
              ? `${node.decision.decision.slice(0, 35)}...` 
              : node.decision.decision
            }
          </text>

          {/* Confidence and timing */}
          <text x="12" y="70" className="text-xs fill-slate-600">
            Confidence: {(node.decision.confidence * 100).toFixed(0)}%
          </text>
          
          {node.decision.executionTime && (
            <text x="120" y="70" className="text-xs fill-slate-600">
              {node.decision.executionTime}s execution
            </text>
          )}

          {/* Impact indicator */}
          <rect
            x="12"
            y="80"
            width="40"
            height="12"
            rx="6"
            className={`${getColorClass(impactColor)} bg-opacity-20`}
          />
          <text
            x="32"
            y="89"
            className={`text-xs ${getColorClass(impactColor, 'text')} font-medium`}
            textAnchor="middle"
          >
            {node.decision.impact}
          </text>

          {/* Expand/collapse button */}
          {hasChildren && (
            <g 
              transform="translate(250, 40)"
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.decision.id);
              }}
              className="cursor-pointer"
            >
              <rect
                width="20"
                height="20"
                rx="4"
                fill="white"
                stroke="#e2e8f0"
                className="hover:stroke-slate-400"
              />
              {node.expanded ? (
                <Minimize className="w-3 h-3 text-slate-600" style={{ transform: 'translate(2px, 2px)' }} />
              ) : (
                <Maximize className="w-3 h-3 text-slate-600" style={{ transform: 'translate(2px, 2px)' }} />
              )}
            </g>
          )}

          {/* Child count */}
          {hasChildren && (
            <text
              x="232"
              y="70"
              className="text-xs fill-slate-500 font-medium"
              textAnchor="middle"
            >
              {node.children.length}
            </text>
          )}
        </g>
      </g>
    );
  };

  const renderTimeline = () => {
    const sortedDecisions = [...decisions].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    
    return (
      <div className="space-y-4">
        {sortedDecisions.map((decision, index) => {
          const AgentIcon = agentIcons[decision.agentType];
          const StatusIcon = statusIcons[decision.status];
          const agentColor = agentColors[decision.agentType];
          const statusColor = statusColors[decision.status];
          const isSelected = selectedNode === decision.id;

          return (
            <div
              key={decision.id}
              onClick={() => setSelectedNode(decision.id)}
              className={`relative p-4 rounded-lg border-2 transition-all cursor-pointer ${
                isSelected 
                  ? 'border-purple-200 bg-purple-50' 
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
            >
              {/* Timeline connector */}
              {index < sortedDecisions.length - 1 && (
                <div className="absolute left-8 top-full w-px h-4 bg-slate-300"></div>
              )}
              
              <div className="flex items-start space-x-4">
                {/* Agent icon */}
                <div className={`p-3 ${getColorClass(agentColor)} rounded-lg flex-shrink-0`}>
                  <AgentIcon className="w-5 h-5 text-white" />
                </div>
                
                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-slate-800 capitalize">
                        {decision.agentType} Agent
                      </h4>
                      <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${getColorClass(statusColor)} bg-opacity-20`}>
                        <StatusIcon className={`w-3 h-3 ${getColorClass(statusColor, 'text')}`} />
                        <span className={`text-xs ${getColorClass(statusColor, 'text')}`}>
                          {decision.status}
                        </span>
                      </div>
                    </div>
                    <div className="text-sm text-slate-500">
                      {decision.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  
                  {/* Decision */}
                  <h5 className="font-medium text-slate-800 mb-2">{decision.decision}</h5>
                  
                  {/* Reasoning */}
                  <p className="text-sm text-slate-600 mb-3 leading-relaxed">
                    {decision.reasoning}
                  </p>
                  
                  {/* Metrics */}
                  <div className="flex items-center space-x-6 text-sm">
                    <div>
                      <span className="text-slate-500">Confidence:</span>
                      <span className="ml-1 font-medium">{(decision.confidence * 100).toFixed(0)}%</span>
                    </div>
                    
                    {decision.executionTime && (
                      <div>
                        <span className="text-slate-500">Execution:</span>
                        <span className="ml-1 font-medium">{decision.executionTime}s</span>
                      </div>
                    )}
                    
                    {decision.cost && (
                      <div>
                        <span className="text-slate-500">Cost:</span>
                        <span className="ml-1 font-medium">£{decision.cost.toLocaleString()}</span>
                      </div>
                    )}
                    
                    {decision.passengersBenefited && (
                      <div>
                        <span className="text-slate-500">Passengers:</span>
                        <span className="ml-1 font-medium">{decision.passengersBenefited}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderTreeNodes = (nodes: TreeNode[]): React.ReactNode[] => {
    const result: React.ReactNode[] = [];
    
    const traverse = (nodeList: TreeNode[]) => {
      for (const node of nodeList) {
        result.push(renderNode(node, result.length));
        if (node.expanded && node.children.length > 0) {
          traverse(node.children);
        }
      }
    };
    
    traverse(nodes);
    return result;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
            <GitBranch className="w-6 h-6" />
            <span>Decision Tree Visualizer</span>
          </h2>
          
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('tree')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'tree' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-600'
              }`}
            >
              Tree View
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'timeline' 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-600'
              }`}
            >
              Timeline
            </button>
          </div>
        </div>

        {/* Selected Decision Details */}
        {selectedNode && (
          <div className="bg-slate-50 rounded-lg p-4">
            {(() => {
              const decision = decisions.find(d => d.id === selectedNode);
              if (!decision) return null;
              
              const AgentIcon = agentIcons[decision.agentType];
              const agentColor = agentColors[decision.agentType];
              
              return (
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`p-2 ${getColorClass(agentColor)} rounded-lg`}>
                      <AgentIcon className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="font-semibold text-slate-800 capitalize">
                      {decision.agentType} Agent Decision
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600">{decision.reasoning}</p>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'tree' ? (
          <div className="p-6">
            <svg
              ref={svgRef}
              width="100%"
              height={Math.max(600, treeData.length * 120)}
              className="border border-slate-200 rounded-lg bg-white"
            >
              {/* Arrow marker definition */}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon
                    points="0 0, 10 3.5, 0 7"
                    fill="#e2e8f0"
                  />
                </marker>
              </defs>
              
              {renderTreeNodes(treeData)}
            </svg>
          </div>
        ) : (
          <div className="p-6">
            {renderTimeline()}
          </div>
        )}
      </div>
    </div>
  );
}