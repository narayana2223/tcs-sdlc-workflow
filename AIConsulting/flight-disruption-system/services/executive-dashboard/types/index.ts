export interface FlightDisruption {
  id: string;
  flightNumber: string;
  route: string;
  departureAirport: string;
  arrivalAirport: string;
  scheduledDeparture: Date;
  estimatedDeparture: Date;
  status: 'delayed' | 'cancelled' | 'diverted';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedPassengers: number;
  reason: string;
  coordinates: [number, number];
}

export interface AgentDecision {
  id: string;
  agentType: 'prediction' | 'passenger' | 'resource' | 'communication' | 'coordinator';
  timestamp: Date;
  decision: string;
  reasoning: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  relatedFlightId?: string;
  cost?: number;
  passengersBenefited?: number;
  status: 'processing' | 'completed' | 'failed';
}

export interface FinancialMetrics {
  totalCostSavings: number;
  revenueProtected: number;
  compensationPaid: number;
  operationalCosts: number;
  savingsPerMinute: number;
  roi: number;
}

export interface PassengerMetrics {
  totalAffected: number;
  rebooked: number;
  inProgress: number;
  satisfied: number;
  averageSatisfaction: number;
  averageRebookingTime: number;
}

export interface PerformanceMetrics {
  predictionsAccuracy: number;
  responseTime: number;
  systemUptime: number;
  agentEfficiency: number;
  disruptionsHandled: number;
  successRate: number;
}

export interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  source: string;
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  severity: 'minor' | 'major' | 'severe';
  affectedFlights: number;
  estimatedDuration: number;
}

export interface DashboardState {
  disruptions: FlightDisruption[];
  agentDecisions: AgentDecision[];
  financialMetrics: FinancialMetrics;
  passengerMetrics: PassengerMetrics;
  performanceMetrics: PerformanceMetrics;
  alerts: Alert[];
  isSimulationMode: boolean;
  lastUpdated: Date;
}