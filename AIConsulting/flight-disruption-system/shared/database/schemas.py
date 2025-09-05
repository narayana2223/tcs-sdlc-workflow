"""
Flight Disruption Management System - Database Schemas

Comprehensive database models for production-ready airline operations,
including flights, passengers, disruptions, agents, and real-time events.
"""

from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, 
    Numeric, Text, JSON, ForeignKey, Index, UniqueConstraint,
    CheckConstraint, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INET
import uuid


Base = declarative_base()


# Enums for type safety
class FlightStatus(Enum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    IN_FLIGHT = "in_flight"
    ARRIVED = "arrived"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"


class DisruptionType(Enum):
    WEATHER = "weather"
    TECHNICAL = "technical"
    CREW = "crew"
    AIRPORT_CLOSURE = "airport_closure"
    AIR_TRAFFIC = "air_traffic"
    SECURITY = "security"
    OPERATIONAL = "operational"
    EXTERNAL = "external"


class DisruptionSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PassengerStatus(Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    BOARDED = "boarded"
    NO_SHOW = "no_show"
    STANDBY = "standby"
    CANCELLED = "cancelled"


class RebookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"


class CompensationStatus(Enum):
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    PROCESSING = "processing"
    PAID = "paid"
    DISPUTED = "disputed"


# Association tables for many-to-many relationships
flight_crew_association = Table(
    'flight_crew',
    Base.metadata,
    Column('flight_id', UUID, ForeignKey('flights.flight_id')),
    Column('crew_member_id', UUID, ForeignKey('crew_members.crew_member_id'))
)

disruption_flights_association = Table(
    'disruption_flights',
    Base.metadata,
    Column('disruption_id', UUID, ForeignKey('disruptions.disruption_id')),
    Column('flight_id', UUID, ForeignKey('flights.flight_id'))
)


# Core Entities

class Airport(Base):
    """Airport master data"""
    __tablename__ = 'airports'

    airport_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    iata_code = Column(String(3), unique=True, nullable=False)
    icao_code = Column(String(4), unique=True, nullable=False)
    airport_name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    timezone = Column(String(50), nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    elevation_ft = Column(Integer)
    hub_priority = Column(Integer, default=0)  # 1=primary hub, 2=secondary hub
    operational_capacity = Column(JSON)  # Runway capacity, terminal info, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    departing_flights = relationship("Flight", foreign_keys="Flight.departure_airport_id", back_populates="departure_airport")
    arriving_flights = relationship("Flight", foreign_keys="Flight.arrival_airport_id", back_populates="arrival_airport")


class Aircraft(Base):
    """Aircraft fleet data"""
    __tablename__ = 'aircraft'

    aircraft_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    registration = Column(String(20), unique=True, nullable=False)
    aircraft_type = Column(String(50), nullable=False)  # A320, B737, etc.
    manufacturer = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    seat_capacity = Column(Integer, nullable=False)
    seat_configuration = Column(JSON)  # Class breakdown
    range_km = Column(Integer)
    max_speed_kmh = Column(Integer)
    maintenance_status = Column(String(20), default='operational')
    last_maintenance_date = Column(Date)
    next_maintenance_date = Column(Date)
    operational_status = Column(String(20), default='available')
    current_location = Column(String(3))  # Airport IATA code
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flights = relationship("Flight", back_populates="aircraft")


class CrewMember(Base):
    """Crew member information"""
    __tablename__ = 'crew_members'

    crew_member_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # pilot, co-pilot, cabin_crew
    rank = Column(String(20))  # captain, first_officer, senior_cabin_crew
    base_airport = Column(String(3), nullable=False)
    qualifications = Column(ARRAY(String))  # Aircraft types qualified for
    availability_status = Column(String(20), default='available')
    current_location = Column(String(3))
    duty_start_time = Column(DateTime)
    duty_end_time = Column(DateTime)
    max_flight_hours_month = Column(Integer, default=100)
    current_flight_hours_month = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flights = relationship("Flight", secondary=flight_crew_association, back_populates="crew_members")


class Flight(Base):
    """Flight schedule and operational data"""
    __tablename__ = 'flights'

    flight_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    flight_number = Column(String(10), nullable=False)
    airline_code = Column(String(3), nullable=False)
    aircraft_id = Column(UUID, ForeignKey('aircraft.aircraft_id'))
    departure_airport_id = Column(UUID, ForeignKey('airports.airport_id'), nullable=False)
    arrival_airport_id = Column(UUID, ForeignKey('airports.airport_id'), nullable=False)
    
    # Schedule information
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    actual_departure = Column(DateTime)
    actual_arrival = Column(DateTime)
    estimated_departure = Column(DateTime)
    estimated_arrival = Column(DateTime)
    
    # Operational details
    flight_status = Column(String(20), nullable=False, default='scheduled')
    gate = Column(String(10))
    terminal = Column(String(10))
    baggage_claim = Column(String(10))
    delay_minutes = Column(Integer, default=0)
    delay_reason = Column(Text)
    
    # Capacity and booking
    seat_capacity = Column(Integer, nullable=False)
    seats_booked = Column(Integer, default=0)
    seats_available = Column(Integer)
    
    # Route and operational data
    route_distance_km = Column(Integer)
    planned_flight_time_minutes = Column(Integer)
    actual_flight_time_minutes = Column(Integer)
    fuel_planned_kg = Column(Integer)
    fuel_actual_kg = Column(Integer)
    
    # Financial data
    base_fare = Column(Numeric(10, 2))
    revenue_total = Column(Numeric(12, 2))
    cost_total = Column(Numeric(12, 2))
    
    # Operational flags
    is_codeshare = Column(Boolean, default=False)
    is_charter = Column(Boolean, default=False)
    priority_level = Column(Integer, default=0)  # For hub operations
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    aircraft = relationship("Aircraft", back_populates="flights")
    departure_airport = relationship("Airport", foreign_keys=[departure_airport_id])
    arrival_airport = relationship("Airport", foreign_keys=[arrival_airport_id])
    crew_members = relationship("CrewMember", secondary=flight_crew_association, back_populates="flights")
    passengers = relationship("Passenger", back_populates="flight")
    disruptions = relationship("Disruption", secondary=disruption_flights_association, back_populates="affected_flights")

    # Indexes for performance
    __table_args__ = (
        Index('ix_flight_departure_time', 'scheduled_departure'),
        Index('ix_flight_arrival_time', 'scheduled_arrival'),
        Index('ix_flight_status', 'flight_status'),
        Index('ix_flight_number_date', 'flight_number', 'scheduled_departure'),
    )


class Passenger(Base):
    """Passenger booking and travel data"""
    __tablename__ = 'passengers'

    passenger_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    pnr = Column(String(20), nullable=False)  # Passenger Name Record
    flight_id = Column(UUID, ForeignKey('flights.flight_id'), nullable=False)
    
    # Personal information
    title = Column(String(10))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    date_of_birth = Column(Date)
    nationality = Column(String(3))
    passport_number = Column(String(20))
    
    # Booking details
    booking_reference = Column(String(20), nullable=False)
    ticket_number = Column(String(20))
    seat_number = Column(String(10))
    class_of_service = Column(String(20), nullable=False)  # economy, premium, business, first
    fare_type = Column(String(20))  # flexible, standard, basic
    fare_amount = Column(Numeric(10, 2))
    
    # Status and preferences
    passenger_status = Column(String(20), default='confirmed')
    check_in_time = Column(DateTime)
    boarding_time = Column(DateTime)
    special_requests = Column(ARRAY(String))  # wheelchair, meal, etc.
    frequent_flyer_number = Column(String(20))
    frequent_flyer_tier = Column(String(20))
    
    # Disruption handling
    is_disrupted = Column(Boolean, default=False)
    disruption_notified = Column(Boolean, default=False)
    notification_preferences = Column(JSON)  # email, sms, push, whatsapp
    rebooking_preferences = Column(JSON)  # time, cost, convenience
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flight = relationship("Flight", back_populates="passengers")
    rebookings = relationship("Rebooking", back_populates="passenger")
    compensations = relationship("Compensation", back_populates="passenger")

    # Indexes
    __table_args__ = (
        Index('ix_passenger_pnr', 'pnr'),
        Index('ix_passenger_booking_ref', 'booking_reference'),
        Index('ix_passenger_email', 'email'),
    )


class Disruption(Base):
    """Flight disruption events and management"""
    __tablename__ = 'disruptions'

    disruption_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    disruption_type = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default='active')
    
    # Timing
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    estimated_start = Column(DateTime)
    estimated_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Location and scope
    primary_airport = Column(String(3))
    affected_airports = Column(ARRAY(String))
    geographical_scope = Column(String(50))  # local, regional, national, international
    
    # Description and cause
    title = Column(String(255), nullable=False)
    description = Column(Text)
    root_cause = Column(Text)
    external_reference = Column(String(100))  # Weather event ID, NOTAM, etc.
    
    # Impact assessment
    flights_affected_count = Column(Integer, default=0)
    passengers_affected_count = Column(Integer, default=0)
    estimated_cost_impact = Column(Numeric(12, 2))
    actual_cost_impact = Column(Numeric(12, 2))
    
    # Management
    responsible_department = Column(String(50))
    assigned_coordinator = Column(String(100))
    escalation_level = Column(Integer, default=1)  # 1=ops, 2=management, 3=executive
    
    # Recovery
    recovery_strategy = Column(Text)
    recovery_progress = Column(Integer, default=0)  # 0-100%
    lessons_learned = Column(Text)
    
    # AI/Agent processing
    ai_confidence_score = Column(Numeric(5, 2))  # 0.00-1.00
    agent_recommendations = Column(JSON)
    automated_actions_taken = Column(JSON)
    human_overrides = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    affected_flights = relationship("Flight", secondary=disruption_flights_association, back_populates="disruptions")
    agent_decisions = relationship("AgentDecision", back_populates="disruption")

    # Indexes
    __table_args__ = (
        Index('ix_disruption_detected_at', 'detected_at'),
        Index('ix_disruption_status', 'status'),
        Index('ix_disruption_severity', 'severity'),
        Index('ix_disruption_type', 'disruption_type'),
    )


class Rebooking(Base):
    """Passenger rebooking records"""
    __tablename__ = 'rebookings'

    rebooking_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    passenger_id = Column(UUID, ForeignKey('passengers.passenger_id'), nullable=False)
    original_flight_id = Column(UUID, ForeignKey('flights.flight_id'), nullable=False)
    new_flight_id = Column(UUID, ForeignKey('flights.flight_id'))
    
    # Rebooking details
    rebooking_status = Column(String(20), default='pending')
    rebooking_type = Column(String(20), nullable=False)  # same_day, next_day, alternative_route
    initiated_by = Column(String(20), default='system')  # system, passenger, agent
    reason = Column(String(100), nullable=False)
    
    # Options and preferences
    options_presented = Column(JSON)  # All options shown to passenger
    option_selected = Column(JSON)  # Selected option details
    passenger_preferences = Column(JSON)  # Time, cost, convenience weights
    
    # Timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Costs and fees
    fare_difference = Column(Numeric(10, 2), default=0)
    rebooking_fee = Column(Numeric(10, 2), default=0)
    total_cost_change = Column(Numeric(10, 2), default=0)
    waived_fees = Column(Numeric(10, 2), default=0)
    
    # Service recovery
    compensation_offered = Column(Numeric(10, 2), default=0)
    vouchers_issued = Column(JSON)  # Meal, hotel, transport vouchers
    service_recovery_score = Column(Integer)  # 1-5 satisfaction rating
    
    # AI processing
    ai_recommended = Column(Boolean, default=False)
    ai_confidence = Column(Numeric(5, 2))
    processing_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    passenger = relationship("Passenger", back_populates="rebookings")
    original_flight = relationship("Flight", foreign_keys=[original_flight_id])
    new_flight = relationship("Flight", foreign_keys=[new_flight_id])


class Compensation(Base):
    """EU261 and other compensation claims"""
    __tablename__ = 'compensations'

    compensation_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    passenger_id = Column(UUID, ForeignKey('passengers.passenger_id'), nullable=False)
    flight_id = Column(UUID, ForeignKey('flights.flight_id'), nullable=False)
    disruption_id = Column(UUID, ForeignKey('disruptions.disruption_id'))
    
    # Legal basis
    regulation_type = Column(String(20), nullable=False)  # EU261, DOT, etc.
    claim_basis = Column(String(50), nullable=False)  # delay, cancellation, denied_boarding
    
    # Eligibility assessment
    compensation_status = Column(String(20), default='not_eligible')
    eligibility_reason = Column(Text)
    automatic_assessment = Column(Boolean, default=True)
    manual_review_required = Column(Boolean, default=False)
    
    # Compensation details
    base_compensation_amount = Column(Numeric(10, 2))
    additional_compensation = Column(Numeric(10, 2))
    total_compensation = Column(Numeric(10, 2))
    currency = Column(String(3), default='EUR')
    
    # Processing
    claim_submitted_at = Column(DateTime, default=datetime.utcnow)
    assessed_at = Column(DateTime)
    approved_at = Column(DateTime)
    paid_at = Column(DateTime)
    payment_method = Column(String(20))  # bank_transfer, voucher, cash
    payment_reference = Column(String(100))
    
    # Dispute handling
    disputed_at = Column(DateTime)
    dispute_reason = Column(Text)
    dispute_resolution = Column(Text)
    final_amount = Column(Numeric(10, 2))
    
    # AI processing
    ai_assessed = Column(Boolean, default=False)
    ai_confidence = Column(Numeric(5, 2))
    assessment_factors = Column(JSON)  # Factors considered in decision
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    passenger = relationship("Passenger", back_populates="compensations")
    flight = relationship("Flight")
    disruption = relationship("Disruption")


# Agent and AI System Tables

class AgentDecision(Base):
    """AI agent decision tracking"""
    __tablename__ = 'agent_decisions'

    decision_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    disruption_id = Column(UUID, ForeignKey('disruptions.disruption_id'))
    
    # Decision context
    decision_type = Column(String(50), nullable=False)
    context_data = Column(JSON, nullable=False)
    alternatives_considered = Column(JSON)
    
    # Decision details
    selected_option = Column(JSON)
    reasoning = Column(Text, nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    estimated_cost = Column(Numeric(12, 2))
    estimated_benefit = Column(Numeric(12, 2))
    estimated_impact = Column(JSON)
    
    # Execution
    tools_used = Column(ARRAY(String))
    execution_time_ms = Column(Integer)
    status = Column(String(20), default='executed')
    
    # Outcomes and learning
    actual_cost = Column(Numeric(12, 2))
    actual_benefit = Column(Numeric(12, 2))
    actual_impact = Column(JSON)
    success_score = Column(Numeric(5, 2))
    feedback_received = Column(JSON)
    
    # Performance tracking
    cost_accuracy = Column(Numeric(5, 2))  # How accurate cost estimate was
    benefit_accuracy = Column(Numeric(5, 2))  # How accurate benefit estimate was
    decision_quality = Column(Numeric(5, 2))  # Overall decision quality rating
    
    decided_at = Column(DateTime, default=datetime.utcnow)
    outcome_recorded_at = Column(DateTime)
    
    # Relationships
    disruption = relationship("Disruption", back_populates="agent_decisions")

    # Indexes
    __table_args__ = (
        Index('ix_agent_decisions_agent_type', 'agent_type'),
        Index('ix_agent_decisions_decided_at', 'decided_at'),
        Index('ix_agent_decisions_confidence', 'confidence_score'),
    )


class SystemEvent(Base):
    """Real-time system events for streaming and monitoring"""
    __tablename__ = 'system_events'

    event_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(30), nullable=False)  # flight, passenger, disruption, agent
    
    # Event source and targeting
    source_system = Column(String(50), nullable=False)
    source_id = Column(String(100))  # ID from source system
    correlation_id = Column(UUID)  # For event correlation
    
    # Event data
    event_data = Column(JSON, nullable=False)
    previous_state = Column(JSON)
    new_state = Column(JSON)
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    processing_duration_ms = Column(Integer)
    
    # Routing and delivery
    target_services = Column(ARRAY(String))
    delivered_to = Column(ARRAY(String))
    failed_deliveries = Column(ARRAY(String))
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for real-time processing
    __table_args__ = (
        Index('ix_system_events_created_at', 'created_at'),
        Index('ix_system_events_type', 'event_type'),
        Index('ix_system_events_processed', 'processed'),
        Index('ix_system_events_correlation', 'correlation_id'),
    )


# Performance and Analytics Tables

class SystemMetrics(Base):
    """System performance metrics"""
    __tablename__ = 'system_metrics'

    metric_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)
    
    # Metric data
    value = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20))
    tags = Column(JSON)  # Additional metric dimensions
    
    # Context
    service_name = Column(String(50))
    instance_id = Column(String(100))
    environment = Column(String(20), default='production')
    
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('ix_system_metrics_recorded_at', 'recorded_at'),
        Index('ix_system_metrics_name_time', 'metric_name', 'recorded_at'),
        Index('ix_system_metrics_category', 'metric_category'),
    )


# Configuration and Reference Data

class Configuration(Base):
    """System configuration parameters"""
    __tablename__ = 'configurations'

    config_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(JSON, nullable=False)
    config_type = Column(String(30), nullable=False)  # agent, system, business_rule
    description = Column(Text)
    
    # Metadata
    environment = Column(String(20), default='production')
    is_sensitive = Column(Boolean, default=False)
    requires_restart = Column(Boolean, default=False)
    
    # Change tracking
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_config_key', 'config_key'),
        Index('ix_config_type', 'config_type'),
    )