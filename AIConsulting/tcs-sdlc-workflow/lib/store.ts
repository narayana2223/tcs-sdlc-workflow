import { create } from 'zustand';
import { MaturityLevel } from './types';

interface WorkflowStore {
  // Maturity Level State
  maturityLevel: MaturityLevel;
  setMaturityLevel: (level: MaturityLevel) => void;

  // Expanded Stage State
  expandedStage: string | null;
  setExpandedStage: (stageId: string | null) => void;
  toggleStage: (stageId: string) => void;

  // Selected Tool State (for modal)
  selectedTool: string | null;
  setSelectedTool: (toolId: string | null) => void;
}

export const useWorkflowStore = create<WorkflowStore>((set) => ({
  // Initial state
  maturityLevel: 'L4', // Start with L4 as default
  expandedStage: null,
  selectedTool: null,

  // Actions
  setMaturityLevel: (level) => set({ maturityLevel: level }),

  setExpandedStage: (stageId) => set({ expandedStage: stageId }),

  toggleStage: (stageId) =>
    set((state) => ({
      expandedStage: state.expandedStage === stageId ? null : stageId,
    })),

  setSelectedTool: (toolId) => set({ selectedTool: toolId }),
}));
