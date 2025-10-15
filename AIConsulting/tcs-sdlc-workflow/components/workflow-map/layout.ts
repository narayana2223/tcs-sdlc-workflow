// Layout configuration for A16Z-style workflow map
// All positions in pixels, based on a 2400px x 1200px canvas

export interface Position {
  x: number;
  y: number;
}

export interface NodeLayout extends Position {
  width?: number;
  height?: number;
}

// Zone 1: Requirements & Feedback (Left Column)
export const requirementsZone = {
  users: { x: 80, y: 60 },
  nexoro: { x: 70, y: 160 },
  requirements: { x: 60, y: 260 },
  feedbackDB: { x: 20, y: 360, width: 250, height: 200 },
};

// Zone 2: Planning & Wiki/Jira Hub (Center-Left)
export const planningZone = {
  pmArchitect: { x: 380, y: 140 },
  traycer: { x: 400, y: 240 },
  wikiJira: { x: 350, y: 400, width: 400, height: 300 }, // LARGE HUB
};

// Zone 3: Design Track (Top-Center)
export const designTrack = {
  uiDesigner: { x: 800, y: 120 },
  figma: { x: 900, y: 200 },
  uiAssets: { x: 900, y: 300 },
  lovable: { x: 900, y: 400 },
};

// Zone 4: Development Track (Center)
export const developmentTrack = {
  swEngineer: { x: 850, y: 480 },
  codingTool: { x: 950, y: 560 }, // Cursor or Devin
  pr: { x: 950, y: 640 },
  coderabbit: { x: 950, y: 720 },
};

// Zone 5: GitHub Hub (Center-Right)
export const githubZone = {
  github: { x: 1200, y: 450, width: 500, height: 350 }, // LARGE HUB
};

// Zone 6: QA Track (Lower-Center)
export const qaTrack = {
  qaEngineer: { x: 850, y: 870 },
  qaTool: { x: 950, y: 950 }, // QA Wolf or QA Wolf + Mabl
  tests: { x: 950, y: 1030 },
};

// Zone 7: Documentation Cluster (Right)
export const documentationCluster = {
  docEditor: { x: 1750, y: 220 },
  aiDoc: { x: 1850, y: 300 },
  mintlify: { x: 1850, y: 420 },
  complianceAI: { x: 1850, y: 540 },
  docsPortal: { x: 1750, y: 650, width: 350, height: 220 },
};

// Zone 8: Deployment (Bottom-Right)
export const deploymentZone = {
  devops: { x: 1750, y: 920 },
  harness: { x: 1850, y: 980 },
  production: { x: 1750, y: 1060, width: 350, height: 200 },
};

// Zone 9: Operations (Far-Right)
export const operationsZone = {
  sreTeam: { x: 2150, y: 920 },
  resolveAI: { x: 2250, y: 980 },
  metricsDB: { x: 2150, y: 1060, width: 250, height: 200 },
};

// Infrastructure Layer (L4/L5 only)
export const infrastructureLayer = {
  e2b: { x: 950, y: 800 },
  buildbuddy: { x: 1100, y: 900 },
  conductor: { x: 500, y: 550 }, // L5 only
};

// Complete layout export
export const layout = {
  canvas: {
    width: 2400,
    height: 1300,
    minWidth: 1400, // For responsive design
  },
  zones: {
    requirements: requirementsZone,
    planning: planningZone,
    design: designTrack,
    development: developmentTrack,
    github: githubZone,
    qa: qaTrack,
    documentation: documentationCluster,
    deployment: deploymentZone,
    operations: operationsZone,
    infrastructure: infrastructureLayer,
  },
};

// Connection definitions for labeled arrows
export interface Connection {
  id: string;
  start: keyof typeof requirementsZone | keyof typeof planningZone | keyof typeof designTrack |
         keyof typeof developmentTrack | keyof typeof githubZone | keyof typeof qaTrack |
         keyof typeof documentationCluster | keyof typeof deploymentZone | keyof typeof operationsZone |
         keyof typeof infrastructureLayer | string;
  end: string;
  label?: string;
  type?: 'solid' | 'dashed' | 'dotted' | 'bidirectional';
  color?: string;
  curve?: 'straight' | 'smooth' | 'step';
  animated?: boolean;
  maturityLevel?: ('L3' | 'L4' | 'L5')[]; // Only show for specific levels
}

// Primary workflow connections
export const connections: Connection[] = [
  // Requirements Flow
  { id: 'c1', start: 'users', end: 'nexoro', label: 'Submit feedback', type: 'solid', animated: true },
  { id: 'c2', start: 'nexoro', end: 'requirements', label: 'Aggregate', type: 'solid' },
  { id: 'c3', start: 'requirements', end: 'feedbackDB', label: 'Store analyzed', type: 'dashed' },

  // Planning Flow
  { id: 'c4', start: 'requirements', end: 'pmArchitect', type: 'solid', animated: true },
  { id: 'c5', start: 'pmArchitect', end: 'traycer', label: 'Define requirements', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c6', start: 'traycer', end: 'wikiJira', label: 'Store specs', type: 'solid' },

  // Design Track
  { id: 'c7', start: 'wikiJira', end: 'uiDesigner', label: 'UI requirements', type: 'solid', curve: 'smooth' },
  { id: 'c8', start: 'uiDesigner', end: 'figma', label: 'Design interface', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c9', start: 'figma', end: 'uiAssets', label: 'Generate assets', type: 'solid' },
  { id: 'c10', start: 'uiAssets', end: 'lovable', type: 'solid' },
  { id: 'c11', start: 'lovable', end: 'github', label: 'UI Assets', type: 'solid', curve: 'smooth' },

  // Development Track
  { id: 'c12', start: 'wikiJira', end: 'swEngineer', label: 'Implementation spec', type: 'solid', curve: 'smooth' },
  { id: 'c13', start: 'swEngineer', end: 'codingTool', label: 'Write code', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c14', start: 'codingTool', end: 'pr', type: 'solid' },
  { id: 'c15', start: 'pr', end: 'coderabbit', label: 'Review', type: 'solid' },
  { id: 'c16', start: 'coderabbit', end: 'github', label: 'Merge (70-95% auto)', type: 'solid', animated: true },

  // QA Track
  { id: 'c17', start: 'wikiJira', end: 'qaEngineer', label: 'Test requirements', type: 'solid', curve: 'smooth' },
  { id: 'c18', start: 'qaEngineer', end: 'qaTool', label: 'Execute tests', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c19', start: 'qaTool', end: 'tests', type: 'solid' },
  { id: 'c20', start: 'tests', end: 'github', label: 'Test results', type: 'solid', curve: 'smooth' },

  // Documentation Cluster
  { id: 'c21', start: 'github', end: 'docEditor', type: 'solid', curve: 'smooth' },
  { id: 'c22', start: 'docEditor', end: 'aiDoc', label: 'Generate docs', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c23', start: 'aiDoc', end: 'docsPortal', label: 'User Docs', type: 'solid' },
  { id: 'c24', start: 'github', end: 'mintlify', label: 'Extract APIs', type: 'solid', curve: 'smooth' },
  { id: 'c25', start: 'mintlify', end: 'docsPortal', label: 'API Docs', type: 'solid' },
  { id: 'c26', start: 'tests', end: 'complianceAI', type: 'solid', curve: 'smooth' },
  { id: 'c27', start: 'complianceAI', end: 'docsPortal', label: 'Compliance Docs', type: 'solid' },

  // Deployment
  { id: 'c28', start: 'github', end: 'devops', type: 'solid', curve: 'step' },
  { id: 'c29', start: 'docsPortal', end: 'devops', type: 'dashed' },
  { id: 'c30', start: 'devops', end: 'harness', label: 'Deploy', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c31', start: 'harness', end: 'production', type: 'solid', animated: true },

  // Operations
  { id: 'c32', start: 'production', end: 'sreTeam', type: 'solid', curve: 'smooth' },
  { id: 'c33', start: 'sreTeam', end: 'resolveAI', label: 'Monitor', type: 'bidirectional', color: '#4A90E2' },
  { id: 'c34', start: 'resolveAI', end: 'metricsDB', label: 'Auto-remediate', type: 'solid' },

  // Infrastructure connections (L4/L5 only)
  { id: 'c35', start: 'codingTool', end: 'e2b', label: 'Execute', type: 'dotted', color: '#F5A623', maturityLevel: ['L4', 'L5'] },
  { id: 'c36', start: 'qaTool', end: 'buildbuddy', label: 'Build cache', type: 'dotted', color: '#F5A623', maturityLevel: ['L4', 'L5'] },
  { id: 'c37', start: 'traycer', end: 'conductor', label: 'Orchestrate', type: 'dotted', color: '#F5A623', maturityLevel: ['L5'] },
];

// Helper function to get node position
export function getNodePosition(nodeId: string): NodeLayout | null {
  const allNodes = {
    ...requirementsZone,
    ...planningZone,
    ...designTrack,
    ...developmentTrack,
    ...githubZone,
    ...qaTrack,
    ...documentationCluster,
    ...deploymentZone,
    ...operationsZone,
    ...infrastructureLayer,
  };

  return (allNodes as Record<string, NodeLayout>)[nodeId] || null;
}
