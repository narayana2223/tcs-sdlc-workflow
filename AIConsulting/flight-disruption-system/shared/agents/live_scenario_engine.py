"""
Live Scenario Execution Engine

This module provides real-time execution of airline disruption scenarios
with autonomous agent responses, performance tracking, and executive controls.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, field
import uuid
import structlog

from .agentic_intelligence import AgenticIntelligenceEngine, ReasoningType, ConflictType
from .autonomous_orchestrator import AutonomousAgentOrchestrator

logger = structlog.get_logger()


class ScenarioStatus(Enum):
    """Status of scenario execution"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RESET = "reset"


class ExecutionSpeed(Enum):
    """Scenario execution speed multipliers"""
    SLOW = 0.5
    NORMAL = 1.0
    FAST = 2.0
    VERY_FAST = 5.0
    ULTRA_FAST = 10.0


@dataclass
class ScenarioEvent:
    """Individual event in a scenario timeline"""
    event_id: str
    timestamp: float  # Seconds from scenario start
    agent_id: str
    agent_type: str
    event_type: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None
    cost_impact: Optional[float] = None
    passengers_affected: Optional[int] = None
    duration: Optional[float] = None
    status: str = "pending"


@dataclass
class ScenarioMetrics:
    """Real-time scenario performance metrics"""
    start_time: datetime
    current_time: datetime
    elapsed_seconds: float
    total_passengers: int
    passengers_processed: int
    passengers_accommodated: int
    passengers_pending: int
    total_cost: float
    cost_savings: float
    traditional_cost_estimate: float
    agent_decisions: int
    successful_decisions: int
    average_confidence: float
    completion_percentage: float
    estimated_completion_time: Optional[float] = None


@dataclass
class PerformanceComparison:
    """Comparison between agentic and traditional approaches"""
    scenario_name: str
    agentic_timeline: float  # Minutes
    traditional_timeline: float  # Minutes
    agentic_cost: float
    traditional_cost: float
    cost_savings: float
    cost_savings_percentage: float
    agentic_satisfaction: float  # 0-1 scale
    traditional_satisfaction: float
    efficiency_gain: float
    staff_hours_saved: float
    automation_rate: float  # Percentage of decisions made autonomously


class LiveScenarioEngine:
    """
    Live Scenario Execution Engine
    
    Executes realistic airline disruption scenarios in real-time with
    autonomous agent responses and executive controls.
    """
    
    def __init__(
        self,
        orchestrator: AutonomousAgentOrchestrator,
        openai_api_key: str
    ):
        self.orchestrator = orchestrator
        self.openai_api_key = openai_api_key
        
        # Execution state
        self.current_scenario: Optional[str] = None
        self.scenario_status = ScenarioStatus.PENDING
        self.execution_speed = ExecutionSpeed.NORMAL
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.total_paused_duration = 0.0
        
        # Event tracking
        self.scenario_events: List[ScenarioEvent] = []
        self.executed_events: List[ScenarioEvent] = []
        self.pending_events: List[ScenarioEvent] = []
        
        # Real-time metrics
        self.current_metrics: Optional[ScenarioMetrics] = None
        self.performance_comparison: Optional[PerformanceComparison] = None
        
        # Event subscribers for live updates
        self.event_subscribers: List[Callable] = []
        
        # Predefined scenarios
        self.scenarios = self._initialize_scenarios()
        
        logger.info("Live Scenario Engine initialized")
    
    def _initialize_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined realistic disruption scenarios"""
        
        return {
            "heathrow_fog_crisis": {
                "name": "Heathrow Fog Crisis",
                "description": "Dense fog at LHR affecting 2,500 passengers across 18 flights",
                "duration_estimate": 30,  # minutes
                "severity": "critical",
                "context": {
                    "airport_code": "LHR",
                    "weather_condition": "dense_fog",
                    "visibility": "50m",
                    "affected_flights": 18,
                    "total_passengers": 2500,
                    "business_passengers": 340,
                    "connecting_passengers": 890,
                    "international_passengers": 1870,
                    "estimated_delay_hours": 4,
                    "peak_season": True
                },
                "traditional_baseline": {
                    "resolution_time_hours": 5.5,
                    "staff_hours_required": 180,
                    "cost_estimate": 487500,
                    "passenger_satisfaction": 2.1,
                    "manual_decisions": 45,
                    "automation_rate": 0.15
                },
                "events": [
                    {"time": 0, "agent": "system", "type": "scenario_start", "desc": "Heathrow Fog Crisis scenario initiated"},
                    {"time": 3, "agent": "prediction", "type": "weather_analysis", "desc": "Fog probability analysis: 89% dense fog for 4+ hours"},
                    {"time": 7, "agent": "prediction", "type": "impact_prediction", "desc": "Passenger impact analysis: 2,500 passengers, 18 flights affected"},
                    {"time": 12, "agent": "passenger", "type": "passenger_analysis", "desc": "Passenger categorization: 340 business, 890 connecting, priority ranking complete"},
                    {"time": 18, "agent": "resource", "type": "hotel_search", "desc": "Hotel inventory search: 890 rooms identified across 12 properties"},
                    {"time": 25, "agent": "finance", "type": "cost_analysis", "desc": "Cost optimization: Negotiating bulk rates, target 25% below standard"},
                    {"time": 32, "agent": "resource", "type": "hotel_booking", "desc": "Hotel confirmation: 890 rooms secured at 28% below market rate"},
                    {"time": 38, "agent": "communication", "type": "notification_prep", "desc": "Personalized message creation: 2,500 unique notifications prepared"},
                    {"time": 45, "agent": "communication", "type": "mass_notification", "desc": "Mass notification sent: 2,500 passengers notified via preferred channels"},
                    {"time": 52, "agent": "resource", "type": "transport_coordination", "desc": "Transport coordination: 45 coaches arranged for hotel transfers"},
                    {"time": 58, "agent": "passenger", "type": "rebooking_start", "desc": "Automated rebooking initiated: Processing 2,500 passengers"},
                    {"time": 75, "agent": "finance", "type": "compensation_calc", "desc": "EU261 compensation calculated: £625,000 total, optimization in progress"},
                    {"time": 82, "agent": "coordinator", "type": "progress_check", "desc": "Progress assessment: 94% passengers accommodated, on-track completion"},
                    {"time": 95, "agent": "passenger", "type": "rebooking_complete", "desc": "Rebooking completed: 2,347 passengers rebooked, 153 pending"},
                    {"time": 102, "agent": "communication", "type": "update_notification", "desc": "Status updates sent: Real-time updates to all affected passengers"},
                    {"time": 115, "agent": "finance", "type": "cost_savings", "desc": "Cost savings achieved: £247,600 vs traditional approach"},
                    {"time": 120, "agent": "coordinator", "type": "scenario_complete", "desc": "Scenario complete: 96% success rate, significant cost savings achieved"}
                ]
            },
            
            "aircraft_technical_failure": {
                "name": "Aircraft Technical Failure",
                "description": "A320 engine warning forces last-minute cancellation with 180 passengers",
                "duration_estimate": 20,
                "severity": "high",
                "context": {
                    "airport_code": "MAN",
                    "aircraft_type": "Airbus A320",
                    "flight_number": "EZY842",
                    "total_passengers": 180,
                    "connecting_passengers": 67,
                    "business_passengers": 24,
                    "route": "MAN-BCN",
                    "technical_issue": "engine_warning_light",
                    "maintenance_required": "90_minutes"
                },
                "traditional_baseline": {
                    "resolution_time_hours": 3.5,
                    "staff_hours_required": 25,
                    "cost_estimate": 89000,
                    "passenger_satisfaction": 2.3,
                    "manual_decisions": 18,
                    "automation_rate": 0.20
                },
                "events": [
                    {"time": 0, "agent": "system", "type": "scenario_start", "desc": "Technical failure scenario: A320 engine warning detected"},
                    {"time": 2, "agent": "prediction", "type": "technical_analysis", "desc": "Technical assessment: Engine inspection required, 90-minute delay minimum"},
                    {"time": 5, "agent": "passenger", "type": "passenger_count", "desc": "Passenger manifest analysis: 180 passengers, 67 connections at risk"},
                    {"time": 8, "agent": "resource", "type": "aircraft_search", "desc": "Alternative aircraft search: Spare A320 available in 45 minutes"},
                    {"time": 12, "agent": "finance", "type": "cost_comparison", "desc": "Cost analysis: Spare aircraft vs passenger accommodation comparison"},
                    {"time": 18, "agent": "coordinator", "type": "decision_made", "desc": "Decision: Deploy spare aircraft, minimize passenger impact"},
                    {"time": 25, "agent": "passenger", "type": "connection_analysis", "desc": "Connection risk analysis: 67 passengers require rebooking assistance"},
                    {"time": 32, "agent": "communication", "type": "passenger_notification", "desc": "Passenger notification: Technical delay, alternative aircraft deployed"},
                    {"time": 45, "agent": "resource", "type": "aircraft_ready", "desc": "Spare aircraft ready: Boarding can commence in 15 minutes"},
                    {"time": 52, "agent": "passenger", "type": "priority_boarding", "desc": "Priority boarding: Tight connection passengers board first"},
                    {"time": 65, "agent": "communication", "type": "connection_updates", "desc": "Connection updates: Downstream flights notified of passenger status"},
                    {"time": 78, "agent": "finance", "type": "cost_savings", "desc": "Cost optimization: £18,400 saved vs traditional handling"},
                    {"time": 85, "agent": "coordinator", "type": "scenario_complete", "desc": "Flight departed: 92% on-time connections maintained"}
                ]
            },
            
            "airport_strike_action": {
                "name": "Airport Strike Action", 
                "description": "Ground handling strike at Gatwick affecting 15 flights and 1,200 passengers",
                "duration_estimate": 45,
                "severity": "critical",
                "context": {
                    "airport_code": "LGW",
                    "strike_type": "ground_handling",
                    "affected_flights": 15,
                    "total_passengers": 1200,
                    "strike_duration": "6_hours",
                    "alternative_handling": "limited",
                    "peak_time": True
                },
                "traditional_baseline": {
                    "resolution_time_hours": 6.5,
                    "staff_hours_required": 95,
                    "cost_estimate": 298000,
                    "passenger_satisfaction": 1.8,
                    "manual_decisions": 35,
                    "automation_rate": 0.10
                },
                "events": [
                    {"time": 0, "agent": "system", "type": "scenario_start", "desc": "Ground handling strike at LGW: 15 flights affected"},
                    {"time": 4, "agent": "prediction", "type": "strike_impact", "desc": "Strike impact analysis: 6-hour duration, limited alternative handling"},
                    {"time": 8, "agent": "resource", "type": "handling_alternatives", "desc": "Alternative handling search: Partner airline resources identified"},
                    {"time": 15, "agent": "passenger", "type": "passenger_priorities", "desc": "Passenger prioritization: Medical, business, connection-critical ranking"},
                    {"time": 22, "agent": "finance", "type": "cost_mitigation", "desc": "Cost mitigation strategy: Partner handling at 40% premium acceptable"},
                    {"time": 28, "agent": "coordinator", "type": "resource_allocation", "desc": "Resource allocation: 8 flights via partner handling, 7 delayed"},
                    {"time": 35, "agent": "communication", "type": "strike_notification", "desc": "Strike communication: Transparent updates to all 1,200 passengers"},
                    {"time": 42, "agent": "resource", "type": "accommodation_booking", "desc": "Accommodation arranged: Hotels for 485 overnight passengers"},
                    {"time": 58, "agent": "passenger", "type": "rebooking_complex", "desc": "Complex rebooking: Multi-day itinerary adjustments for 1,200 passengers"},
                    {"time": 75, "agent": "finance", "type": "compensation_processing", "desc": "Compensation processing: Automated EU261 calculations"},
                    {"time": 95, "agent": "communication", "type": "recovery_updates", "desc": "Recovery updates: Timeline and alternatives communicated"},
                    {"time": 125, "agent": "coordinator", "type": "partial_recovery", "desc": "Partial recovery: 8 flights operating, 7 rescheduled for next day"},
                    {"time": 150, "agent": "finance", "type": "final_cost_savings", "desc": "Final cost analysis: £89,200 saved through partner agreements"},
                    {"time": 180, "agent": "coordinator", "type": "scenario_complete", "desc": "Strike response complete: 78% same-day travel achieved"}
                ]
            },
            
            "multiple_flight_delays": {
                "name": "Multiple Flight Delays",
                "description": "Cascade effect: Air traffic control issues causing 25 flight delays",
                "duration_estimate": 35,
                "severity": "high", 
                "context": {
                    "cause": "air_traffic_control",
                    "affected_airports": ["LHR", "LGW", "STN"],
                    "affected_flights": 25,
                    "total_passengers": 3200,
                    "cascade_risk": "high",
                    "european_connections": 1240,
                    "delay_range": "1-4_hours"
                },
                "traditional_baseline": {
                    "resolution_time_hours": 4.8,
                    "staff_hours_required": 145,
                    "cost_estimate": 675000,
                    "passenger_satisfaction": 2.0,
                    "manual_decisions": 58,
                    "automation_rate": 0.12
                },
                "events": [
                    {"time": 0, "agent": "system", "type": "scenario_start", "desc": "ATC delays: 25 flights affected across London airports"},
                    {"time": 3, "agent": "prediction", "type": "cascade_analysis", "desc": "Cascade effect prediction: 1,240 European connections at risk"},
                    {"time": 8, "agent": "coordinator", "type": "priority_matrix", "desc": "Priority matrix created: Route criticality and passenger impact analysis"},
                    {"time": 15, "agent": "passenger", "type": "connection_mapping", "desc": "Connection mapping: 1,240 passengers require proactive rebooking"},
                    {"time": 22, "agent": "resource", "type": "capacity_analysis", "desc": "Alternative capacity analysis: Spare seats identified across 48 flights"},
                    {"time": 28, "agent": "finance", "type": "bulk_negotiation", "desc": "Bulk rate negotiation: Partner airlines offering 15% discount"},
                    {"time": 35, "agent": "communication", "type": "proactive_updates", "desc": "Proactive updates: 3,200 passengers notified before official delays"},
                    {"time": 42, "agent": "passenger", "type": "mass_rebooking", "desc": "Mass rebooking initiated: AI processing 3,200 passenger itineraries"},
                    {"time": 65, "agent": "resource", "type": "ground_coordination", "desc": "Ground coordination: Lounges, meals, and facilities arranged"},
                    {"time": 78, "agent": "finance", "type": "cost_tracking", "desc": "Real-time cost tracking: £156,000 saved through predictive rebooking"},
                    {"time": 95, "agent": "passenger", "type": "rebooking_progress", "desc": "Rebooking progress: 2,840 passengers successfully rebooked"},
                    {"time": 115, "agent": "communication", "type": "satisfaction_survey", "desc": "Live satisfaction survey: 4.2/5 rating despite delays"},
                    {"time": 140, "agent": "coordinator", "type": "recovery_complete", "desc": "Recovery coordination complete: 89% passengers on revised schedules"},
                    {"time": 155, "agent": "finance", "type": "final_savings", "desc": "Final cost savings: £267,800 through autonomous coordination"}
                ]
            },
            
            "peak_season_overload": {
                "name": "Peak Season Overload",
                "description": "Christmas period: High demand, limited alternatives, 450 passengers stranded",
                "duration_estimate": 50,
                "severity": "critical",
                "context": {
                    "season": "christmas_peak",
                    "airport_code": "EDI",
                    "stranded_passengers": 450,
                    "available_alternatives": "very_limited",
                    "family_groups": 89,
                    "unaccompanied_minors": 12,
                    "elderly_passengers": 67,
                    "hotel_availability": "scarce"
                },
                "traditional_baseline": {
                    "resolution_time_hours": 8.5,
                    "staff_hours_required": 200,
                    "cost_estimate": 892000,
                    "passenger_satisfaction": 1.6,
                    "manual_decisions": 78,
                    "automation_rate": 0.08
                },
                "events": [
                    {"time": 0, "agent": "system", "type": "scenario_start", "desc": "Peak season overload: 450 passengers stranded during Christmas period"},
                    {"time": 5, "agent": "passenger", "type": "vulnerable_analysis", "desc": "Vulnerable passenger analysis: 12 unaccompanied minors, 67 elderly priority"},
                    {"time": 12, "agent": "resource", "type": "accommodation_crisis", "desc": "Accommodation crisis: Hotel availability at 15%, premium rates required"},
                    {"time": 18, "agent": "finance", "type": "budget_escalation", "desc": "Budget escalation approved: Christmas period emergency spending authorized"},
                    {"time": 25, "agent": "coordinator", "type": "multi_modal", "desc": "Multi-modal transport: Train, bus, and partner airline combinations"},
                    {"time": 35, "agent": "communication", "type": "family_liaison", "desc": "Family liaison: Specialized support for 89 family groups"},
                    {"time": 45, "agent": "resource", "type": "creative_solutions", "desc": "Creative solutions: University accommodation and serviced apartments secured"},
                    {"time": 58, "agent": "passenger", "type": "alternative_routing", "desc": "Alternative routing: Edinburgh-London-destination combinations"},
                    {"time": 75, "agent": "finance", "type": "premium_negotiation", "desc": "Premium rate negotiation: 32% reduction from Christmas premium rates"},
                    {"time": 95, "agent": "communication", "type": "goodwill_gestures", "desc": "Goodwill gestures: Christmas meal vouchers and compensation upgrades"},
                    {"time": 125, "agent": "coordinator", "type": "vulnerable_complete", "desc": "Vulnerable passengers: All 79 high-priority passengers accommodated"},
                    {"time": 155, "agent": "passenger", "type": "family_reunification", "desc": "Family reunification: All 89 family groups kept together"},
                    {"time": 185, "agent": "resource", "type": "final_placements", "desc": "Final placements: 447 of 450 passengers accommodated"},
                    {"time": 220, "agent": "finance", "type": "christmas_savings", "desc": "Christmas period savings: £178,900 saved despite peak constraints"},
                    {"time": 240, "agent": "coordinator", "type": "scenario_complete", "desc": "Peak season response complete: 99.3% passenger accommodation achieved"}
                ]
            }
        }
    
    async def load_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Load and prepare a scenario for execution"""
        
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        
        # Create scenario events
        self.scenario_events = []
        for event_data in scenario["events"]:
            event = ScenarioEvent(
                event_id=f"{scenario_name}_{event_data['time']:03d}",
                timestamp=event_data["time"],
                agent_id=f"{event_data['agent']}_agent_01",
                agent_type=event_data["agent"],
                event_type=event_data["type"],
                description=event_data["desc"],
                data=scenario["context"]
            )
            self.scenario_events.append(event)
        
        # Sort events by timestamp
        self.scenario_events.sort(key=lambda x: x.timestamp)
        
        # Initialize metrics
        self._initialize_scenario_metrics(scenario)
        
        # Create performance comparison baseline
        self._initialize_performance_comparison(scenario)
        
        self.current_scenario = scenario_name
        self.scenario_status = ScenarioStatus.PENDING
        self.executed_events = []
        self.pending_events = self.scenario_events.copy()
        
        logger.info(f"Scenario loaded: {scenario_name} with {len(self.scenario_events)} events")
        
        return {
            "scenario_name": scenario_name,
            "scenario_info": scenario,
            "total_events": len(self.scenario_events),
            "estimated_duration": scenario["duration_estimate"],
            "status": "loaded"
        }
    
    def _initialize_scenario_metrics(self, scenario: Dict[str, Any]):
        """Initialize real-time scenario metrics"""
        
        context = scenario["context"]
        
        self.current_metrics = ScenarioMetrics(
            start_time=datetime.utcnow(),
            current_time=datetime.utcnow(),
            elapsed_seconds=0.0,
            total_passengers=context.get("total_passengers", 0),
            passengers_processed=0,
            passengers_accommodated=0,
            passengers_pending=context.get("total_passengers", 0),
            total_cost=0.0,
            cost_savings=0.0,
            traditional_cost_estimate=scenario["traditional_baseline"]["cost_estimate"],
            agent_decisions=0,
            successful_decisions=0,
            average_confidence=0.0,
            completion_percentage=0.0
        )
    
    def _initialize_performance_comparison(self, scenario: Dict[str, Any]):
        """Initialize performance comparison with traditional approach"""
        
        baseline = scenario["traditional_baseline"]
        
        self.performance_comparison = PerformanceComparison(
            scenario_name=scenario["name"],
            agentic_timeline=scenario["duration_estimate"],
            traditional_timeline=baseline["resolution_time_hours"] * 60,
            agentic_cost=0.0,  # Will be updated during execution
            traditional_cost=baseline["cost_estimate"],
            cost_savings=0.0,
            cost_savings_percentage=0.0,
            agentic_satisfaction=4.5,  # Expected satisfaction
            traditional_satisfaction=baseline["passenger_satisfaction"],
            efficiency_gain=0.0,
            staff_hours_saved=baseline["staff_hours_required"],
            automation_rate=0.95  # Expected automation rate
        )
    
    async def start_scenario(self) -> Dict[str, Any]:
        """Start executing the loaded scenario"""
        
        if not self.current_scenario:
            raise ValueError("No scenario loaded")
        
        if self.scenario_status != ScenarioStatus.PENDING:
            raise ValueError(f"Cannot start scenario in {self.scenario_status.value} state")
        
        # Initialize orchestrator if needed
        if not self.orchestrator.agents:
            await self.orchestrator.initialize_agent_system()
        
        self.start_time = datetime.utcnow()
        self.scenario_status = ScenarioStatus.RUNNING
        self.total_paused_duration = 0.0
        
        logger.info(f"Started scenario: {self.current_scenario}")
        
        # Notify subscribers
        await self._notify_subscribers("scenario_started", {
            "scenario": self.current_scenario,
            "start_time": self.start_time.isoformat()
        })
        
        return {
            "status": "started",
            "scenario": self.current_scenario,
            "start_time": self.start_time.isoformat(),
            "estimated_duration": self.scenarios[self.current_scenario]["duration_estimate"]
        }
    
    async def execute_scenario_live(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute scenario in real-time with live updates"""
        
        if self.scenario_status != ScenarioStatus.RUNNING:
            raise ValueError("Scenario must be started before execution")
        
        try:
            while (self.scenario_status == ScenarioStatus.RUNNING and 
                   len(self.pending_events) > 0):
                
                current_time = datetime.utcnow()
                elapsed_seconds = (current_time - self.start_time).total_seconds() - self.total_paused_duration
                adjusted_elapsed = elapsed_seconds * self.execution_speed.value
                
                # Find events ready to execute
                ready_events = [
                    event for event in self.pending_events 
                    if event.timestamp <= adjusted_elapsed
                ]
                
                # Execute ready events
                for event in ready_events:
                    await self._execute_event(event)
                    self.pending_events.remove(event)
                    self.executed_events.append(event)
                    
                    # Update metrics
                    await self._update_metrics(event)
                    
                    # Yield live update
                    yield {
                        "type": "event_executed",
                        "event": {
                            "id": event.event_id,
                            "timestamp": f"{event.timestamp:05.1f}s",
                            "agent": event.agent_type,
                            "description": event.description,
                            "confidence": event.confidence,
                            "cost_impact": event.cost_impact,
                            "passengers_affected": event.passengers_affected
                        },
                        "metrics": self._get_current_metrics(),
                        "performance": self._get_performance_comparison(),
                        "scenario_status": self.scenario_status.value
                    }
                
                # Yield periodic status updates
                if len(ready_events) == 0:
                    yield {
                        "type": "status_update",
                        "metrics": self._get_current_metrics(),
                        "performance": self._get_performance_comparison(),
                        "scenario_status": self.scenario_status.value,
                        "next_event_in": self._get_next_event_time(adjusted_elapsed)
                    }
                
                # Small delay to prevent overwhelming updates
                await asyncio.sleep(0.1)
            
            # Scenario completion
            if len(self.pending_events) == 0:
                self.scenario_status = ScenarioStatus.COMPLETED
                
                final_metrics = self._get_current_metrics()
                final_performance = self._get_performance_comparison()
                
                await self._notify_subscribers("scenario_completed", {
                    "scenario": self.current_scenario,
                    "final_metrics": final_metrics,
                    "performance_comparison": final_performance
                })
                
                yield {
                    "type": "scenario_completed",
                    "final_metrics": final_metrics,
                    "performance_comparison": final_performance,
                    "scenario_status": "completed",
                    "summary": self._generate_completion_summary()
                }
            
        except Exception as e:
            self.scenario_status = ScenarioStatus.FAILED
            logger.error(f"Scenario execution failed: {e}")
            
            yield {
                "type": "scenario_failed",
                "error": str(e),
                "scenario_status": "failed"
            }
    
    async def _execute_event(self, event: ScenarioEvent):
        """Execute a single scenario event"""
        
        try:
            # Simulate agent processing based on event type
            if event.event_type in ["weather_analysis", "technical_analysis", "strike_impact"]:
                # Prediction agent events
                confidence = 0.85 + (0.15 * (event.timestamp / 120))  # Confidence increases over time
                cost_impact = -1000 * (event.timestamp / 60)  # Early detection saves costs
                passengers_affected = event.data.get("total_passengers", 0)
                
            elif event.event_type in ["passenger_analysis", "rebooking_start", "rebooking_complete"]:
                # Passenger agent events
                confidence = 0.82 + (0.13 * (len(self.executed_events) / len(self.scenario_events)))
                cost_impact = -500 * (passengers_affected if 'passengers_affected' in locals() else 100)
                passengers_affected = event.data.get("total_passengers", 0)
                
            elif event.event_type in ["hotel_booking", "transport_coordination", "accommodation_booking"]:
                # Resource agent events
                confidence = 0.88
                cost_impact = -15000 if "hotel" in event.event_type else -3000
                passengers_affected = min(1000, event.data.get("total_passengers", 0))
                
            elif event.event_type in ["cost_analysis", "cost_savings", "compensation_calc"]:
                # Finance agent events
                confidence = 0.91
                cost_impact = -25000 if "savings" in event.event_type else 0
                passengers_affected = 0
                
            elif event.event_type in ["notification_prep", "mass_notification", "passenger_notification"]:
                # Communication agent events
                confidence = 0.89
                cost_impact = -200 * (event.data.get("total_passengers", 0) / 100)
                passengers_affected = event.data.get("total_passengers", 0)
                
            else:
                # Coordinator or system events
                confidence = 0.86
                cost_impact = 0
                passengers_affected = 0
            
            # Update event with execution results
            event.confidence = min(0.98, max(0.65, confidence))
            event.cost_impact = cost_impact
            event.passengers_affected = passengers_affected
            event.status = "completed"
            event.duration = 1.5 + (0.5 * (event.timestamp / 60))  # Longer events take more time
            
            # Simulate actual agent interaction (simplified)
            if event.agent_id != "system_agent_01":
                try:
                    # In production, this would trigger actual agent reasoning
                    reasoning_context = {
                        "event_type": event.event_type,
                        "scenario_data": event.data,
                        "execution_time": event.timestamp
                    }
                    
                    # Simulate processing delay
                    await asyncio.sleep(0.05)  # Small delay for realism
                    
                except Exception as agent_error:
                    logger.warning(f"Agent simulation error: {agent_error}")
                    event.confidence = 0.7
            
            logger.info(f"Executed event: {event.event_id} - {event.description}")
            
        except Exception as e:
            event.status = "failed"
            event.confidence = 0.5
            logger.error(f"Event execution failed: {e}")
    
    async def _update_metrics(self, event: ScenarioEvent):
        """Update real-time scenario metrics based on executed event"""
        
        if not self.current_metrics:
            return
        
        # Update timing
        self.current_metrics.current_time = datetime.utcnow()
        self.current_metrics.elapsed_seconds = (
            (self.current_metrics.current_time - self.current_metrics.start_time).total_seconds() 
            - self.total_paused_duration
        )
        
        # Update passenger metrics based on event type
        if "rebooking" in event.event_type or "accommodation" in event.event_type:
            if event.passengers_affected:
                self.current_metrics.passengers_processed += event.passengers_affected
                self.current_metrics.passengers_accommodated += int(event.passengers_affected * (event.confidence or 0.85))
                self.current_metrics.passengers_pending = max(
                    0, 
                    self.current_metrics.total_passengers - self.current_metrics.passengers_processed
                )
        
        # Update cost metrics
        if event.cost_impact:
            if event.cost_impact < 0:  # Savings
                self.current_metrics.cost_savings += abs(event.cost_impact)
            else:  # Costs
                self.current_metrics.total_cost += event.cost_impact
        
        # Update decision metrics
        if event.confidence:
            self.current_metrics.agent_decisions += 1
            if event.confidence > 0.7:
                self.current_metrics.successful_decisions += 1
            
            # Update average confidence
            total_confidence = (
                self.current_metrics.average_confidence * (self.current_metrics.agent_decisions - 1) +
                event.confidence
            )
            self.current_metrics.average_confidence = total_confidence / self.current_metrics.agent_decisions
        
        # Update completion percentage
        self.current_metrics.completion_percentage = (
            len(self.executed_events) / len(self.scenario_events) * 100
        )
        
        # Estimate completion time
        if self.current_metrics.completion_percentage > 10:
            rate = self.current_metrics.completion_percentage / self.current_metrics.elapsed_seconds
            self.current_metrics.estimated_completion_time = 100 / rate
        
        # Update performance comparison
        await self._update_performance_comparison()
    
    async def _update_performance_comparison(self):
        """Update performance comparison metrics"""
        
        if not self.performance_comparison or not self.current_metrics:
            return
        
        # Update agentic costs
        self.performance_comparison.agentic_cost = (
            self.current_metrics.total_cost - self.current_metrics.cost_savings
        )
        
        # Calculate savings
        self.performance_comparison.cost_savings = (
            self.performance_comparison.traditional_cost - self.performance_comparison.agentic_cost
        )
        
        self.performance_comparison.cost_savings_percentage = (
            self.performance_comparison.cost_savings / self.performance_comparison.traditional_cost * 100
            if self.performance_comparison.traditional_cost > 0 else 0
        )
        
        # Calculate efficiency gain
        traditional_minutes = self.performance_comparison.traditional_timeline
        agentic_minutes = self.current_metrics.elapsed_seconds / 60
        
        self.performance_comparison.efficiency_gain = (
            (traditional_minutes - agentic_minutes) / traditional_minutes * 100
            if traditional_minutes > 0 else 0
        )
    
    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current scenario metrics for live updates"""
        
        if not self.current_metrics:
            return {}
        
        return {
            "elapsed_time": f"{self.current_metrics.elapsed_seconds:.1f}s",
            "completion_percentage": f"{self.current_metrics.completion_percentage:.1f}%",
            "passengers": {
                "total": self.current_metrics.total_passengers,
                "processed": self.current_metrics.passengers_processed,
                "accommodated": self.current_metrics.passengers_accommodated,
                "pending": self.current_metrics.passengers_pending
            },
            "costs": {
                "total_cost": f"£{self.current_metrics.total_cost:,.0f}",
                "cost_savings": f"£{self.current_metrics.cost_savings:,.0f}",
                "traditional_estimate": f"£{self.current_metrics.traditional_cost_estimate:,.0f}"
            },
            "decisions": {
                "total": self.current_metrics.agent_decisions,
                "successful": self.current_metrics.successful_decisions,
                "success_rate": f"{(self.current_metrics.successful_decisions / max(1, self.current_metrics.agent_decisions)) * 100:.1f}%",
                "average_confidence": f"{self.current_metrics.average_confidence * 100:.1f}%"
            },
            "estimated_completion": f"{self.current_metrics.estimated_completion_time or 0:.1f}s"
        }
    
    def _get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison for live updates"""
        
        if not self.performance_comparison:
            return {}
        
        return {
            "timelines": {
                "agentic_approach": f"{self.performance_comparison.agentic_timeline:.1f} min",
                "traditional_approach": f"{self.performance_comparison.traditional_timeline:.1f} min",
                "time_saved": f"{self.performance_comparison.traditional_timeline - self.performance_comparison.agentic_timeline:.1f} min"
            },
            "costs": {
                "agentic_cost": f"£{self.performance_comparison.agentic_cost:,.0f}",
                "traditional_cost": f"£{self.performance_comparison.traditional_cost:,.0f}",
                "savings": f"£{self.performance_comparison.cost_savings:,.0f}",
                "savings_percentage": f"{self.performance_comparison.cost_savings_percentage:.1f}%"
            },
            "satisfaction": {
                "agentic_satisfaction": f"{self.performance_comparison.agentic_satisfaction:.1f}/5",
                "traditional_satisfaction": f"{self.performance_comparison.traditional_satisfaction:.1f}/5",
                "improvement": f"{(self.performance_comparison.agentic_satisfaction - self.performance_comparison.traditional_satisfaction):.1f} points"
            },
            "efficiency": {
                "efficiency_gain": f"{self.performance_comparison.efficiency_gain:.1f}%",
                "staff_hours_saved": f"{self.performance_comparison.staff_hours_saved:.1f} hours",
                "automation_rate": f"{self.performance_comparison.automation_rate * 100:.1f}%"
            }
        }
    
    def _get_next_event_time(self, current_adjusted_time: float) -> Optional[float]:
        """Get time until next event"""
        
        if not self.pending_events:
            return None
        
        next_event = min(self.pending_events, key=lambda x: x.timestamp)
        return max(0, next_event.timestamp - current_adjusted_time)
    
    def _generate_completion_summary(self) -> Dict[str, Any]:
        """Generate scenario completion summary"""
        
        if not self.current_metrics or not self.performance_comparison:
            return {}
        
        return {
            "scenario_name": self.scenarios[self.current_scenario]["name"],
            "execution_time": f"{self.current_metrics.elapsed_seconds:.1f} seconds",
            "passengers_handled": self.current_metrics.passengers_accommodated,
            "success_rate": f"{(self.current_metrics.passengers_accommodated / self.current_metrics.total_passengers) * 100:.1f}%",
            "cost_savings": f"£{self.current_metrics.cost_savings:,.0f}",
            "efficiency_gain": f"{self.performance_comparison.efficiency_gain:.1f}%",
            "decision_accuracy": f"{self.current_metrics.average_confidence * 100:.1f}%",
            "autonomous_decisions": self.current_metrics.agent_decisions,
            "key_achievements": [
                f"Processed {self.current_metrics.passengers_accommodated:,} passengers",
                f"Saved £{self.current_metrics.cost_savings:,.0f} vs traditional approach",
                f"Achieved {self.current_metrics.average_confidence * 100:.1f}% decision confidence",
                f"Completed {self.performance_comparison.efficiency_gain:.1f}% faster than manual process"
            ]
        }
    
    # Executive control methods
    
    async def pause_scenario(self) -> Dict[str, Any]:
        """Pause scenario execution"""
        
        if self.scenario_status != ScenarioStatus.RUNNING:
            raise ValueError("Can only pause running scenario")
        
        self.pause_time = datetime.utcnow()
        self.scenario_status = ScenarioStatus.PAUSED
        
        await self._notify_subscribers("scenario_paused", {
            "pause_time": self.pause_time.isoformat()
        })
        
        return {"status": "paused", "pause_time": self.pause_time.isoformat()}
    
    async def resume_scenario(self) -> Dict[str, Any]:
        """Resume paused scenario"""
        
        if self.scenario_status != ScenarioStatus.PAUSED or not self.pause_time:
            raise ValueError("Can only resume paused scenario")
        
        # Add paused duration to total
        pause_duration = (datetime.utcnow() - self.pause_time).total_seconds()
        self.total_paused_duration += pause_duration
        
        self.scenario_status = ScenarioStatus.RUNNING
        self.pause_time = None
        
        await self._notify_subscribers("scenario_resumed", {
            "pause_duration": pause_duration
        })
        
        return {"status": "resumed", "pause_duration": pause_duration}
    
    def set_execution_speed(self, speed: ExecutionSpeed) -> Dict[str, Any]:
        """Set scenario execution speed"""
        
        self.execution_speed = speed
        
        return {
            "execution_speed": speed.value,
            "description": f"{speed.value}x real-time"
        }
    
    async def reset_scenario(self) -> Dict[str, Any]:
        """Reset scenario to initial state"""
        
        self.scenario_status = ScenarioStatus.RESET
        self.start_time = None
        self.pause_time = None
        self.total_paused_duration = 0.0
        self.executed_events = []
        
        if self.current_scenario:
            # Reload scenario to reset events
            await self.load_scenario(self.current_scenario)
            self.scenario_status = ScenarioStatus.PENDING
        
        await self._notify_subscribers("scenario_reset", {
            "scenario": self.current_scenario
        })
        
        return {"status": "reset", "scenario": self.current_scenario}
    
    def get_scenario_status(self) -> Dict[str, Any]:
        """Get current scenario status"""
        
        return {
            "current_scenario": self.current_scenario,
            "status": self.scenario_status.value,
            "execution_speed": self.execution_speed.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_time": (
                (datetime.utcnow() - self.start_time).total_seconds() - self.total_paused_duration
                if self.start_time else 0
            ),
            "events": {
                "total": len(self.scenario_events),
                "executed": len(self.executed_events), 
                "pending": len(self.pending_events)
            },
            "metrics": self._get_current_metrics(),
            "performance_comparison": self._get_performance_comparison()
        }
    
    def get_available_scenarios(self) -> Dict[str, Any]:
        """Get list of available scenarios"""
        
        return {
            scenario_key: {
                "name": scenario["name"],
                "description": scenario["description"],
                "duration_estimate": scenario["duration_estimate"],
                "severity": scenario["severity"],
                "total_passengers": scenario["context"].get("total_passengers", 0),
                "traditional_cost": scenario["traditional_baseline"]["cost_estimate"],
                "traditional_time": scenario["traditional_baseline"]["resolution_time_hours"]
            }
            for scenario_key, scenario in self.scenarios.items()
        }
    
    # Subscriber management for live updates
    
    def subscribe_to_updates(self, callback: Callable):
        """Subscribe to live scenario updates"""
        self.event_subscribers.append(callback)
    
    def unsubscribe_from_updates(self, callback: Callable):
        """Unsubscribe from live scenario updates"""
        if callback in self.event_subscribers:
            self.event_subscribers.remove(callback)
    
    async def _notify_subscribers(self, event_type: str, data: Dict[str, Any]):
        """Notify all subscribers of scenario events"""
        
        notification = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        for callback in self.event_subscribers:
            try:
                await callback(notification)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def export_scenario_results(self) -> Dict[str, Any]:
        """Export scenario results for business case development"""
        
        if self.scenario_status != ScenarioStatus.COMPLETED:
            raise ValueError("Can only export results from completed scenarios")
        
        return {
            "scenario_info": self.scenarios[self.current_scenario],
            "execution_results": {
                "total_execution_time": self.current_metrics.elapsed_seconds,
                "events_executed": [
                    {
                        "timestamp": event.timestamp,
                        "agent": event.agent_type,
                        "description": event.description,
                        "confidence": event.confidence,
                        "cost_impact": event.cost_impact,
                        "passengers_affected": event.passengers_affected,
                        "duration": event.duration
                    }
                    for event in self.executed_events
                ]
            },
            "final_metrics": self._get_current_metrics(),
            "performance_comparison": self._get_performance_comparison(),
            "business_case": {
                "cost_savings": self.performance_comparison.cost_savings,
                "time_savings": self.performance_comparison.traditional_timeline - self.performance_comparison.agentic_timeline,
                "efficiency_improvement": self.performance_comparison.efficiency_gain,
                "passenger_satisfaction_improvement": (
                    self.performance_comparison.agentic_satisfaction - 
                    self.performance_comparison.traditional_satisfaction
                ),
                "automation_achieved": self.performance_comparison.automation_rate,
                "staff_hours_saved": self.performance_comparison.staff_hours_saved
            },
            "recommendations": [
                "Deploy autonomous agent system for similar disruption scenarios",
                f"Expect {self.performance_comparison.cost_savings_percentage:.1f}% cost savings on average",
                f"Achieve {self.performance_comparison.efficiency_gain:.1f}% faster resolution times",
                "Improve passenger satisfaction through proactive communication",
                "Reduce manual staff workload by 80-95%"
            ]
        }