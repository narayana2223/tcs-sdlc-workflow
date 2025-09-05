'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from './useWebSocket';
import { DashboardState, FlightDisruption, AgentDecision, FinancialMetrics, PassengerMetrics, PerformanceMetrics, Alert } from '@/types';

const initialDashboardState: DashboardState = {
  disruptions: [],
  agentDecisions: [],
  financialMetrics: {
    totalCostSavings: 0,
    revenueProtected: 0,
    compensationPaid: 0,
    operationalCosts: 0,
    savingsPerMinute: 0,
    roi: 0,
  },
  passengerMetrics: {
    totalAffected: 0,
    rebooked: 0,
    inProgress: 0,
    satisfied: 0,
    averageSatisfaction: 0,
    averageRebookingTime: 0,
  },
  performanceMetrics: {
    predictionsAccuracy: 0,
    responseTime: 0,
    systemUptime: 0,
    agentEfficiency: 0,
    disruptionsHandled: 0,
    successRate: 0,
  },
  alerts: [],
  isSimulationMode: false,
  lastUpdated: new Date(),
};

export function useRealTimeData() {
  const [dashboardState, setDashboardState] = useState<DashboardState>(initialDashboardState);
  const { socket, isConnected, connectionStatus } = useWebSocket();

  useEffect(() => {
    if (!socket || !isConnected) return;

    // Subscribe to real-time events
    socket.on('disruption_update', (disruption: FlightDisruption) => {
      setDashboardState(prev => ({
        ...prev,
        disruptions: updateArrayById(prev.disruptions, disruption),
        lastUpdated: new Date(),
      }));
    });

    socket.on('agent_decision', (decision: AgentDecision) => {
      setDashboardState(prev => ({
        ...prev,
        agentDecisions: [decision, ...prev.agentDecisions.slice(0, 49)], // Keep last 50
        lastUpdated: new Date(),
      }));
    });

    socket.on('financial_update', (metrics: FinancialMetrics) => {
      setDashboardState(prev => ({
        ...prev,
        financialMetrics: metrics,
        lastUpdated: new Date(),
      }));
    });

    socket.on('passenger_update', (metrics: PassengerMetrics) => {
      setDashboardState(prev => ({
        ...prev,
        passengerMetrics: metrics,
        lastUpdated: new Date(),
      }));
    });

    socket.on('performance_update', (metrics: PerformanceMetrics) => {
      setDashboardState(prev => ({
        ...prev,
        performanceMetrics: metrics,
        lastUpdated: new Date(),
      }));
    });

    socket.on('alert', (alert: Alert) => {
      setDashboardState(prev => ({
        ...prev,
        alerts: [alert, ...prev.alerts.slice(0, 19)], // Keep last 20
        lastUpdated: new Date(),
      }));
    });

    socket.on('simulation_mode_changed', (isSimulation: boolean) => {
      setDashboardState(prev => ({
        ...prev,
        isSimulationMode: isSimulation,
        lastUpdated: new Date(),
      }));
    });

    // Initial data fetch
    socket.emit('request_dashboard_data');

    return () => {
      socket.off('disruption_update');
      socket.off('agent_decision');
      socket.off('financial_update');
      socket.off('passenger_update');
      socket.off('performance_update');
      socket.off('alert');
      socket.off('simulation_mode_changed');
    };
  }, [socket, isConnected]);

  const triggerSimulation = (scenarioId: string) => {
    if (socket) {
      socket.emit('trigger_simulation', { scenarioId });
    }
  };

  const acknowledgeAlert = (alertId: string) => {
    if (socket) {
      socket.emit('acknowledge_alert', { alertId });
    }
    
    setDashboardState(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert => 
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      ),
    }));
  };

  return {
    dashboardState,
    isConnected,
    connectionStatus,
    triggerSimulation,
    acknowledgeAlert,
  };
}

function updateArrayById<T extends { id: string }>(array: T[], newItem: T): T[] {
  const existingIndex = array.findIndex(item => item.id === newItem.id);
  if (existingIndex >= 0) {
    const newArray = [...array];
    newArray[existingIndex] = newItem;
    return newArray;
  }
  return [newItem, ...array];
}