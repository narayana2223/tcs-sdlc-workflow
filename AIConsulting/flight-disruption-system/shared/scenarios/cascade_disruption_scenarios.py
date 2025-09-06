"""
Cascade Disruption Scenarios - Complex Multi-Flight Disruptions
Affecting 150+ Passengers with Interconnected Dependencies

This module creates realistic cascade disruption scenarios that demonstrate
the system's ability to handle complex, multi-layered disruptions with
competing passenger priorities and resource constraints.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class DisruptionType(Enum):
    WEATHER_SYSTEM = "weather_system"
    CREW_STRIKE = "crew_strike"
    TECHNICAL_CASCADE = "technical_cascade"
    AIRPORT_CLOSURE = "airport_closure"
    AIR_TRAFFIC_CONTROL = "air_traffic_control"

class PassengerPriority(Enum):
    CRITICAL_MEDICAL = 10
    DIAMOND_VIP = 9
    PREGNANT_ELDERLY = 8
    BUSINESS_GROUP = 7
    UNACCOMPANIED_MINOR = 6
    FAMILY_GROUP = 5
    BUSINESS_INDIVIDUAL = 4
    EMERGENCY_TRAVEL = 8
    STANDARD = 3
    BUDGET = 2

@dataclass
class CascadePassenger:
    id: str
    name: str
    pnr: str
    flight_id: str
    priority: PassengerPriority
    group_id: str = None
    dependencies: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    special_needs: List[str] = field(default_factory=list)
    booking_value: float = 0
    satisfaction_target: float = 4.0

@dataclass
class CascadeFlight:
    id: str
    flight_number: str
    airline: str
    departure_airport: str
    arrival_airport: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    passenger_count: int
    aircraft_type: str
    disruption_reason: str
    estimated_delay: int = 0
    cancellation_probability: float = 0.0

@dataclass
class ResourceConstraint:
    resource_type: str
    available_capacity: int
    competing_passengers: List[str]
    allocation_criteria: List[str]
    cost_impact: float

@dataclass
class CascadeScenario:
    id: str
    name: str
    description: str
    disruption_type: DisruptionType
    affected_flights: List[CascadeFlight]
    affected_passengers: List[CascadePassenger]
    resource_constraints: List[ResourceConstraint]
    timeline_hours: int
    estimated_cost_impact: float
    complexity_score: int
    agent_coordination_required: List[str]

# Major Cascade Scenarios

def create_weather_system_cascade() -> CascadeScenario:
    """
    Storm Eunice Redux - Major Weather System Affecting 150+ Passengers
    Complex multi-airport closure with cascading delays across Europe
    """
    
    # Affected flights with realistic passenger distributions
    affected_flights = [
        CascadeFlight(
            id="flight_wx_001", flight_number="BA1234", airline="British Airways",
            departure_airport="LHR", arrival_airport="CDG", 
            scheduled_departure=datetime.now() + timedelta(hours=2),
            scheduled_arrival=datetime.now() + timedelta(hours=3.5),
            passenger_count=180, aircraft_type="Airbus A320",
            disruption_reason="Storm system - winds 45mph, visibility <500m",
            estimated_delay=240, cancellation_probability=0.7
        ),
        CascadeFlight(
            id="flight_wx_002", flight_number="AF8847", airline="Air France", 
            departure_airport="CDG", arrival_airport="FRA",
            scheduled_departure=datetime.now() + timedelta(hours=1.5),
            scheduled_arrival=datetime.now() + timedelta(hours=3),
            passenger_count=165, aircraft_type="Airbus A319",
            disruption_reason="Paris CDG closure - storm conditions",
            estimated_delay=300, cancellation_probability=0.8
        ),
        CascadeFlight(
            id="flight_wx_003", flight_number="LH902", airline="Lufthansa",
            departure_airport="FRA", arrival_airport="MUC",
            scheduled_departure=datetime.now() + timedelta(hours=3),
            scheduled_arrival=datetime.now() + timedelta(hours=4.2),
            passenger_count=145, aircraft_type="Boeing 737-800",
            disruption_reason="Frankfurt hub disruption - crew positioning issues", 
            estimated_delay=180, cancellation_probability=0.6
        ),
        CascadeFlight(
            id="flight_wx_004", flight_number="EZY3456", airline="easyJet",
            departure_airport="LGW", arrival_airport="AMS",
            scheduled_departure=datetime.now() + timedelta(hours=1),
            scheduled_arrival=datetime.now() + timedelta(hours=2.5),
            passenger_count=160, aircraft_type="Airbus A320",
            disruption_reason="London Gatwick slot restrictions due to weather",
            estimated_delay=210, cancellation_probability=0.65
        )
    ]
    
    # Generate 150+ passengers with complex interdependencies
    passengers = []
    passenger_id = 1
    
    # Business Group (TechCorp) - 25 passengers across multiple flights
    techcorp_group = []
    for i in range(25):
        flight_assignment = affected_flights[i % 4]  # Distribute across flights
        passenger = CascadePassenger(
            id=f"pax_techcorp_{i+1:03d}",
            name=f"TechCorp Executive {i+1}",
            pnr=f"TCP{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.BUSINESS_GROUP,
            group_id="techcorp_acquisition_team",
            dependencies=[f"pax_techcorp_{j+1:03d}" for j in range(25) if j != i],
            constraints={
                "must_travel_together": True,
                "meeting_deadline": datetime.now() + timedelta(hours=8),
                "confidentiality_required": True,
                "business_class_required": True
            },
            booking_value=85000,
            satisfaction_target=4.9
        )
        passengers.append(passenger)
        techcorp_group.append(passenger.id)
    
    # Medical Priority Group - 15 passengers with urgent needs
    medical_passengers = [
        CascadePassenger(
            id="pax_medical_001", name="Dr. Patricia Ward - Heart Surgery",
            pnr="MED001", flight_id="flight_wx_001",
            priority=PassengerPriority.CRITICAL_MEDICAL,
            constraints={
                "surgery_deadline": datetime.now() + timedelta(hours=12),
                "medical_equipment": True,
                "wheelchair_required": True
            },
            special_needs=["cardiac_monitor", "oxygen", "medical_escort"],
            booking_value=2400, satisfaction_target=4.8
        ),
        CascadePassenger(
            id="pax_medical_002", name="Maria Santos - Dialysis Patient", 
            pnr="MED002", flight_id="flight_wx_002",
            priority=PassengerPriority.CRITICAL_MEDICAL,
            constraints={
                "dialysis_appointment": datetime.now() + timedelta(hours=10),
                "cannot_miss_treatment": True
            },
            special_needs=["medical_clearance", "priority_boarding"],
            booking_value=890, satisfaction_target=4.7
        ),
        CascadePassenger(
            id="pax_medical_003", name="James Mitchell - Emergency Surgery",
            pnr="MED003", flight_id="flight_wx_003", 
            priority=PassengerPriority.CRITICAL_MEDICAL,
            constraints={
                "surgery_tonight": datetime.now() + timedelta(hours=8),
                "family_emergency": True
            },
            special_needs=["emergency_priority", "any_available_seat"],
            booking_value=1200, satisfaction_target=4.6
        )
    ]
    passengers.extend(medical_passengers)
    
    # Diamond VIP Passengers - 8 high-value customers
    vip_passengers = []
    for i in range(8):
        flight_assignment = affected_flights[i % 4]
        vip = CascadePassenger(
            id=f"pax_diamond_{i+1:03d}",
            name=f"Diamond Elite Member {i+1}",
            pnr=f"DIA{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.DIAMOND_VIP,
            constraints={
                "first_class_only": True,
                "automatic_rebooking": True,
                "concierge_service": True
            },
            booking_value=12000,
            satisfaction_target=4.95
        )
        passengers.append(vip)
        vip_passengers.append(vip.id)
    
    # Family Groups - 35 passengers in 8 family groups
    family_groups = []
    for family_idx in range(8):
        family_size = [3, 4, 5, 6, 3, 4, 4, 5][family_idx]
        flight_assignment = affected_flights[family_idx % 4]
        family_id = f"family_group_{family_idx+1:02d}"
        
        for member_idx in range(family_size):
            passenger = CascadePassenger(
                id=f"pax_family_{family_idx+1:02d}_{member_idx+1:02d}",
                name=f"Family {family_idx+1} Member {member_idx+1}",
                pnr=f"FAM{family_idx+1:02d}{member_idx+1:02d}",
                flight_id=flight_assignment.id,
                priority=PassengerPriority.FAMILY_GROUP,
                group_id=family_id,
                dependencies=[f"pax_family_{family_idx+1:02d}_{j+1:02d}" 
                            for j in range(family_size) if j != member_idx],
                constraints={
                    "family_seating_together": True,
                    "children_supervision": member_idx in [2, 3, 4],
                    "vacation_package": True
                },
                booking_value=1400 * family_size,
                satisfaction_target=4.3
            )
            passengers.append(passenger)
            
        family_groups.append(family_id)
    
    # Unaccompanied Minors - 6 children traveling alone
    for i in range(6):
        flight_assignment = affected_flights[i % 4]
        minor = CascadePassenger(
            id=f"pax_minor_{i+1:03d}",
            name=f"Unaccompanied Minor {i+1}",
            pnr=f"MIN{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.UNACCOMPANIED_MINOR,
            constraints={
                "guardian_notification_required": True,
                "special_supervision": True,
                "custody_schedule": datetime.now() + timedelta(hours=6)
            },
            special_needs=["um_service", "child_meal", "entertainment"],
            booking_value=280,
            satisfaction_target=4.7
        )
        passengers.append(minor)
    
    # Pregnant/Elderly Priority - 12 passengers
    priority_passengers = []
    for i in range(12):
        flight_assignment = affected_flights[i % 4] 
        if i < 6:  # Pregnant passengers
            passenger = CascadePassenger(
                id=f"pax_pregnant_{i+1:03d}",
                name=f"Pregnant Traveler {i+1}",
                pnr=f"PRG{i+1:03d}",
                flight_id=flight_assignment.id,
                priority=PassengerPriority.PREGNANT_ELDERLY,
                constraints={
                    "pregnancy_week": 20 + i*2,
                    "medical_clearance": True,
                    "comfort_priority": True
                },
                special_needs=["extra_legroom", "priority_boarding"],
                booking_value=450,
                satisfaction_target=4.6
            )
        else:  # Elderly passengers
            passenger = CascadePassenger(
                id=f"pax_elderly_{i-5:03d}",
                name=f"Elderly Passenger {i-5}",
                pnr=f"ELD{i-5:03d}",
                flight_id=flight_assignment.id,
                priority=PassengerPriority.PREGNANT_ELDERLY,
                constraints={
                    "age": 75 + (i-6),
                    "mobility_assistance": True,
                    "medication_schedule": True
                },
                special_needs=["wheelchair", "medical_assistance"],
                booking_value=320,
                satisfaction_target=4.5
            )
        passengers.append(passenger)
    
    # Standard Passengers - Fill remaining slots to reach 150+ total
    remaining_slots = max(0, 150 - len(passengers))
    for i in range(remaining_slots):
        flight_assignment = affected_flights[i % 4]
        standard = CascadePassenger(
            id=f"pax_standard_{i+1:03d}",
            name=f"Standard Passenger {i+1}",
            pnr=f"STD{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.STANDARD,
            constraints={},
            booking_value=200 + (i * 10),
            satisfaction_target=4.0
        )
        passengers.append(standard)
    
    # Resource constraints during the disruption
    resource_constraints = [
        ResourceConstraint(
            resource_type="premium_hotel_rooms",
            available_capacity=45,
            competing_passengers=techcorp_group + vip_passengers,
            allocation_criteria=["tier_status", "group_priority", "booking_value"],
            cost_impact=15000
        ),
        ResourceConstraint(
            resource_type="wheelchair_accessible_transport",
            available_capacity=8,
            competing_passengers=[p.id for p in passengers if "wheelchair" in p.special_needs],
            allocation_criteria=["medical_priority", "age", "mobility_severity"],
            cost_impact=2400
        ),
        ResourceConstraint(
            resource_type="medical_assistance_crew",
            available_capacity=3,
            competing_passengers=[p.id for p in passengers 
                                if p.priority == PassengerPriority.CRITICAL_MEDICAL],
            allocation_criteria=["medical_urgency", "safety_risk"],
            cost_impact=1200
        ),
        ResourceConstraint(
            resource_type="child_supervision_staff",
            available_capacity=2,
            competing_passengers=[p.id for p in passengers 
                                if p.priority == PassengerPriority.UNACCOMPANIED_MINOR],
            allocation_criteria=["age", "custody_urgency", "guardian_distance"],
            cost_impact=800
        ),
        ResourceConstraint(
            resource_type="business_class_alternatives",
            available_capacity=28,
            competing_passengers=techcorp_group + vip_passengers + 
                               [p.id for p in passengers 
                                if p.constraints.get("first_class_only") or 
                                   p.constraints.get("business_class_required")],
            allocation_criteria=["status", "booking_value", "group_priority"],
            cost_impact=25000
        )
    ]
    
    return CascadeScenario(
        id="weather_cascade_001",
        name="Storm Eunice Redux - Multi-Airport Weather Cascade",
        description="Major storm system affecting 4 airports with 150+ passengers requiring complex resource allocation and competing priorities",
        disruption_type=DisruptionType.WEATHER_SYSTEM,
        affected_flights=affected_flights,
        affected_passengers=passengers,
        resource_constraints=resource_constraints,
        timeline_hours=12,
        estimated_cost_impact=425000,
        complexity_score=9,
        agent_coordination_required=[
            "prediction_agent", "passenger_agent", "resource_agent", 
            "coordinator_agent", "communication_agent", "finance_agent"
        ]
    )


def create_crew_strike_cascade() -> CascadeScenario:
    """
    Multi-Airline Crew Strike - 180+ Passengers Affected
    Strike action spreading across multiple carriers with crew shortages
    """
    
    affected_flights = [
        CascadeFlight(
            id="flight_strike_001", flight_number="IB3847", airline="Iberia",
            departure_airport="LHR", arrival_airport="MAD",
            scheduled_departure=datetime.now() + timedelta(hours=1),
            scheduled_arrival=datetime.now() + timedelta(hours=4),
            passenger_count=155, aircraft_type="Airbus A321",
            disruption_reason="Ground handling crew strike - baggage and catering affected",
            estimated_delay=360, cancellation_probability=0.9
        ),
        CascadeFlight(
            id="flight_strike_002", flight_number="VY8204", airline="Vueling",
            departure_airport="BCN", arrival_airport="LHR", 
            scheduled_departure=datetime.now() + timedelta(hours=2),
            scheduled_arrival=datetime.now() + timedelta(hours=5),
            passenger_count=168, aircraft_type="Airbus A320",
            disruption_reason="Flight crew strike - pilot union action",
            estimated_delay=480, cancellation_probability=0.85
        ),
        CascadeFlight(
            id="flight_strike_003", flight_number="FR2847", airline="Ryanair",
            departure_airport="STN", arrival_airport="PMI",
            scheduled_departure=datetime.now() + timedelta(hours=1.5),
            scheduled_arrival=datetime.now() + timedelta(hours=4.5),
            passenger_count=189, aircraft_type="Boeing 737-800",
            disruption_reason="Cabin crew shortage - strike solidarity action",
            estimated_delay=420, cancellation_probability=0.8
        )
    ]
    
    # Generate passenger mix for strike scenario - more leisure travelers
    passengers = []
    
    # Large Tour Groups - 45 passengers in vacation packages  
    for group_idx in range(3):
        group_size = 15
        flight_assignment = affected_flights[group_idx]
        group_id = f"tour_group_{group_idx+1:02d}"
        
        for member_idx in range(group_size):
            passenger = CascadePassenger(
                id=f"pax_tour_{group_idx+1:02d}_{member_idx+1:02d}",
                name=f"Tour Group {group_idx+1} Member {member_idx+1}",
                pnr=f"TGR{group_idx+1:02d}{member_idx+1:02d}",
                flight_id=flight_assignment.id,
                priority=PassengerPriority.STANDARD,
                group_id=group_id,
                constraints={
                    "package_holiday": True,
                    "hotel_vouchers_expire": datetime.now() + timedelta(hours=24),
                    "group_activities_booked": True
                },
                booking_value=680,
                satisfaction_target=3.8
            )
            passengers.append(passenger)
    
    # Budget Travelers - 60 passengers with cost constraints
    for i in range(60):
        flight_assignment = affected_flights[i % 3]
        budget = CascadePassenger(
            id=f"pax_budget_{i+1:03d}",
            name=f"Budget Traveler {i+1}",
            pnr=f"BGT{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.BUDGET,
            constraints={
                "budget_limit": 200,
                "no_hotel_budget": True,
                "flexible_dates": True
            },
            booking_value=89,
            satisfaction_target=3.5
        )
        passengers.append(budget)
    
    # Business Travelers - 35 passengers with time constraints
    for i in range(35):
        flight_assignment = affected_flights[i % 3]
        business = CascadePassenger(
            id=f"pax_business_{i+1:03d}",
            name=f"Business Traveler {i+1}",
            pnr=f"BIZ{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.BUSINESS_INDIVIDUAL,
            constraints={
                "meeting_tomorrow": datetime.now() + timedelta(hours=18),
                "expense_account": True,
                "flexible_routing": True
            },
            booking_value=450,
            satisfaction_target=4.1
        )
        passengers.append(business)
    
    # Emergency Cases - 8 urgent travelers
    for i in range(8):
        flight_assignment = affected_flights[i % 3]
        emergency = CascadePassenger(
            id=f"pax_emergency_{i+1:03d}",
            name=f"Emergency Traveler {i+1}",
            pnr=f"EMG{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.EMERGENCY_TRAVEL,
            constraints={
                "family_emergency": True,
                "time_critical": True,
                "any_airline_acceptable": True
            },
            booking_value=340,
            satisfaction_target=4.4
        )
        passengers.append(emergency)
    
    # Fill to 180+ passengers with remaining standard travelers
    remaining = max(0, 180 - len(passengers))
    for i in range(remaining):
        flight_assignment = affected_flights[i % 3]
        standard = CascadePassenger(
            id=f"pax_standard_strike_{i+1:03d}",
            name=f"Standard Passenger {i+1}",
            pnr=f"STS{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.STANDARD,
            constraints={},
            booking_value=180,
            satisfaction_target=3.9
        )
        passengers.append(standard)
    
    resource_constraints = [
        ResourceConstraint(
            resource_type="alternative_airline_seats",
            available_capacity=65,
            competing_passengers=[p.id for p in passengers],
            allocation_criteria=["booking_value", "urgency", "flexibility"],
            cost_impact=35000
        ),
        ResourceConstraint(
            resource_type="accommodation_vouchers",
            available_capacity=120,
            competing_passengers=[p.id for p in passengers 
                                if not p.constraints.get("no_hotel_budget")],
            allocation_criteria=["distance_from_home", "group_priority"],
            cost_impact=18000
        )
    ]
    
    return CascadeScenario(
        id="crew_strike_001", 
        name="Multi-Airline Crew Strike Cascade",
        description="Coordinated strike action affecting multiple airlines with 180+ passengers requiring alternative arrangements",
        disruption_type=DisruptionType.CREW_STRIKE,
        affected_flights=affected_flights,
        affected_passengers=passengers,
        resource_constraints=resource_constraints,
        timeline_hours=18,
        estimated_cost_impact=285000,
        complexity_score=8,
        agent_coordination_required=[
            "passenger_agent", "resource_agent", "coordinator_agent",
            "communication_agent", "finance_agent"
        ]
    )


def create_technical_cascade() -> CascadeScenario:
    """
    Aircraft Technical Cascade - Fleet Grounding Scenario
    Technical issue affecting multiple aircraft of same type, 200+ passengers
    """
    
    affected_flights = [
        CascadeFlight(
            id="flight_tech_001", flight_number="BA456", airline="British Airways",
            departure_airport="LHR", arrival_airport="DUB",
            scheduled_departure=datetime.now() + timedelta(hours=1),
            scheduled_arrival=datetime.now() + timedelta(hours=2.5),
            passenger_count=180, aircraft_type="Boeing 737 MAX",
            disruption_reason="Mandatory safety inspection - software update required",
            estimated_delay=600, cancellation_probability=0.95
        ),
        CascadeFlight(
            id="flight_tech_002", flight_number="BA892", airline="British Airways", 
            departure_airport="LGW", arrival_airport="EDI",
            scheduled_departure=datetime.now() + timedelta(hours=2),
            scheduled_arrival=datetime.now() + timedelta(hours=3.5),
            passenger_count=175, aircraft_type="Boeing 737 MAX",
            disruption_reason="Fleet grounding - same aircraft type safety directive",
            estimated_delay=720, cancellation_probability=1.0
        ),
        CascadeFlight(
            id="flight_tech_003", flight_number="BA1247", airline="British Airways",
            departure_airport="MAN", arrival_airport="BFS",
            scheduled_departure=datetime.now() + timedelta(hours=1.5), 
            scheduled_arrival=datetime.now() + timedelta(hours=3),
            passenger_count=168, aircraft_type="Boeing 737 MAX",
            disruption_reason="Precautionary grounding - fleet safety inspection",
            estimated_delay=660, cancellation_probability=0.98
        )
    ]
    
    # Generate passengers - mix of business and leisure with high rebooking urgency
    passengers = []
    
    # High-value business travelers - 40 passengers
    for i in range(40):
        flight_assignment = affected_flights[i % 3]
        business = CascadePassenger(
            id=f"pax_corp_{i+1:03d}",
            name=f"Corporate Traveler {i+1}",
            pnr=f"CRP{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.BUSINESS_INDIVIDUAL,
            constraints={
                "same_day_requirement": True,
                "flexible_destination": False,
                "expense_account": True
            },
            booking_value=650,
            satisfaction_target=4.3
        )
        passengers.append(business)
    
    # Weekend leisure travelers - 80 passengers
    for i in range(80):
        flight_assignment = affected_flights[i % 3]
        leisure = CascadePassenger(
            id=f"pax_leisure_{i+1:03d}",
            name=f"Leisure Traveler {i+1}",
            pnr=f"LSR{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.STANDARD,
            constraints={
                "weekend_break": True,
                "hotel_non_refundable": True,
                "return_flight_booked": True
            },
            booking_value=180,
            satisfaction_target=3.7
        )
        passengers.append(leisure)
    
    # Domestic business - 45 passengers
    for i in range(45):
        flight_assignment = affected_flights[i % 3]
        domestic_biz = CascadePassenger(
            id=f"pax_domestic_{i+1:03d}",
            name=f"Domestic Business {i+1}",
            pnr=f"DOM{i+1:03d}",
            flight_id=flight_assignment.id,
            priority=PassengerPriority.BUSINESS_INDIVIDUAL,
            constraints={
                "regional_meeting": True,
                "ground_transport_option": True,
                "time_sensitive": True
            },
            booking_value=280,
            satisfaction_target=4.0
        )
        passengers.append(domestic_biz)
    
    # Family travelers - 35 passengers in groups
    for i in range(7):  # 7 families, 5 members average
        flight_assignment = affected_flights[i % 3]
        family_id = f"family_tech_{i+1:02d}"
        
        for member in range(5):
            family_member = CascadePassenger(
                id=f"pax_family_tech_{i+1:02d}_{member+1:02d}",
                name=f"Family {i+1} Member {member+1}",
                pnr=f"FMT{i+1:02d}{member+1:02d}",
                flight_id=flight_assignment.id,
                priority=PassengerPriority.FAMILY_GROUP,
                group_id=family_id,
                constraints={
                    "family_together": True,
                    "children_present": member > 2,
                    "school_holidays": True
                },
                booking_value=890,
                satisfaction_target=4.2
            )
            passengers.append(family_member)
    
    resource_constraints = [
        ResourceConstraint(
            resource_type="alternative_aircraft",
            available_capacity=2,
            competing_passengers=[p.id for p in passengers[:100]],  # Priority passengers
            allocation_criteria=["booking_value", "status", "urgency"],
            cost_impact=180000
        ),
        ResourceConstraint(
            resource_type="ground_transport_alternatives",
            available_capacity=80,
            competing_passengers=[p.id for p in passengers 
                                if p.constraints.get("ground_transport_option")],
            allocation_criteria=["distance", "time_sensitivity", "group_size"],
            cost_impact=12000
        ),
        ResourceConstraint(
            resource_type="competitor_airline_seats",
            available_capacity=150,
            competing_passengers=[p.id for p in passengers],
            allocation_criteria=["booking_value", "flexibility", "loyalty_status"],
            cost_impact=65000
        )
    ]
    
    return CascadeScenario(
        id="technical_cascade_001",
        name="Boeing 737 MAX Fleet Grounding Cascade", 
        description="Mandatory safety inspection requiring fleet grounding, affecting 200+ passengers with urgent rebooking needs",
        disruption_type=DisruptionType.TECHNICAL_CASCADE,
        affected_flights=affected_flights,
        affected_passengers=passengers,
        resource_constraints=resource_constraints,
        timeline_hours=24,
        estimated_cost_impact=520000,
        complexity_score=10,
        agent_coordination_required=[
            "prediction_agent", "passenger_agent", "resource_agent",
            "coordinator_agent", "communication_agent", "finance_agent"
        ]
    )


# Scenario Registry
CASCADE_SCENARIOS = {
    "weather_system": create_weather_system_cascade,
    "crew_strike": create_crew_strike_cascade, 
    "technical_cascade": create_technical_cascade,
}

def get_cascade_scenario(scenario_type: str) -> CascadeScenario:
    """Get a specific cascade scenario by type"""
    if scenario_type not in CASCADE_SCENARIOS:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    return CASCADE_SCENARIOS[scenario_type]()

def get_all_scenarios() -> List[CascadeScenario]:
    """Get all available cascade scenarios"""
    return [scenario_func() for scenario_func in CASCADE_SCENARIOS.values()]

def get_scenario_summary() -> Dict[str, Any]:
    """Get summary statistics of all scenarios"""
    scenarios = get_all_scenarios()
    
    return {
        "total_scenarios": len(scenarios),
        "total_passengers": sum(len(s.affected_passengers) for s in scenarios),
        "total_flights": sum(len(s.affected_flights) for s in scenarios),
        "complexity_scores": [s.complexity_score for s in scenarios],
        "estimated_costs": [s.estimated_cost_impact for s in scenarios],
        "disruption_types": list(set(s.disruption_type.value for s in scenarios)),
        "max_timeline": max(s.timeline_hours for s in scenarios),
    }