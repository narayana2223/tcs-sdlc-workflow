"""
Advanced Database Relationships and Constraints
Comprehensive SQLAlchemy models with relationships, constraints, and indexes for the flight disruption system
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, UniqueConstraint, CheckConstraint, Index, Table,
    Numeric, BigInteger, SmallInteger, Date, Time, Interval
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.dialects.postgresql import UUID, ENUM, ARRAY
from sqlalchemy.schema import DDL
from sqlalchemy.event import listens_for

# Import enums from models
from ..models.comprehensive_models import (
    FlightStatus, DisruptionType, DisruptionCause, PassengerStatus,
    LoyaltyTier, BookingStatus, CompensationType, PaymentStatus,
    CommunicationMethod, ResourceType, Priority
)

Base = declarative_base()

# Association tables for many-to-many relationships
flight_crew_association = Table(
    'flight_crew_assignments',
    Base.metadata,
    Column('flight_id', UUID(as_uuid=True), ForeignKey('flights.id'), primary_key=True),
    Column('crew_member_id', UUID(as_uuid=True), ForeignKey('crew_members.id'), primary_key=True),
    Column('role', String(50), nullable=False),
    Column('assignment_time', DateTime, default=datetime.utcnow),
    Index('idx_flight_crew_flight', 'flight_id'),
    Index('idx_flight_crew_member', 'crew_member_id')
)

passenger_special_services = Table(
    'passenger_special_services',
    Base.metadata,
    Column('passenger_id', UUID(as_uuid=True), ForeignKey('passengers.id'), primary_key=True),
    Column('service_code', String(10), primary_key=True),
    Column('service_description', String(200)),
    Column('created_at', DateTime, default=datetime.utcnow)
)

disruption_affected_flights = Table(
    'disruption_affected_flights',
    Base.metadata,
    Column('disruption_id', UUID(as_uuid=True), ForeignKey('disruptions.id'), primary_key=True),
    Column('flight_id', UUID(as_uuid=True), ForeignKey('flights.id'), primary_key=True),
    Column('impact_severity', String(20), default='medium'),
    Column('estimated_delay_minutes', Integer),
    Index('idx_disruption_flights', 'disruption_id'),
    Index('idx_affected_flight', 'flight_id')
)


class Airline(Base):
    """Airline database model with comprehensive constraints"""
    __tablename__ = 'airlines'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iata_code = Column(String(2), unique=True, nullable=False, index=True)
    icao_code = Column(String(3), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    hub_airports = Column(ARRAY(String(3)))  # Array of IATA codes
    fleet_size = Column(Integer, default=0)
    founded_year = Column(SmallInteger)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Business data
    cost_per_delay_hour = Column(Numeric(10, 2), default=5000.00)
    compensation_budget_monthly = Column(Numeric(12, 2), default=1000000.00)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flights = relationship("Flight", back_populates="airline", cascade="all, delete-orphan")
    crew_members = relationship("CrewMember", back_populates="airline")
    aircraft = relationship("Aircraft", back_populates="airline")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(iata_code) = 2', name='chk_iata_length'),
        CheckConstraint('length(icao_code) = 3', name='chk_icao_length'),
        CheckConstraint('fleet_size >= 0', name='chk_fleet_size_positive'),
        CheckConstraint('founded_year >= 1900 AND founded_year <= EXTRACT(YEAR FROM CURRENT_DATE)', 
                       name='chk_founded_year_valid'),
        CheckConstraint('cost_per_delay_hour > 0', name='chk_cost_positive'),
        Index('idx_airline_active', 'is_active'),
        Index('idx_airline_country', 'country'),
    )


class Airport(Base):
    """Airport database model with geographical and operational constraints"""
    __tablename__ = 'airports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    
    # Geographical data
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    elevation_feet = Column(Integer)
    timezone = Column(String(50), nullable=False)
    
    # Operational data
    runways_count = Column(SmallInteger, default=1)
    max_aircraft_size = Column(String(20), default='large')  # small, medium, large, super
    weather_reliability_score = Column(Float, default=0.8)  # 0-1 scale
    is_hub = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Capacity and delays
    hourly_capacity = Column(SmallInteger, default=30)
    average_delay_minutes = Column(Float, default=15.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    departing_flights = relationship("Flight", foreign_keys="Flight.departure_airport_id", 
                                   back_populates="departure_airport")
    arriving_flights = relationship("Flight", foreign_keys="Flight.arrival_airport_id", 
                                  back_populates="arrival_airport")
    disruptions = relationship("Disruption", back_populates="airport")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(iata_code) = 3', name='chk_airport_iata_length'),
        CheckConstraint('length(icao_code) = 4', name='chk_airport_icao_length'),
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='chk_latitude_valid'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='chk_longitude_valid'),
        CheckConstraint('elevation_feet >= -1500 AND elevation_feet <= 30000', name='chk_elevation_valid'),
        CheckConstraint('runways_count > 0', name='chk_runways_positive'),
        CheckConstraint('hourly_capacity > 0 AND hourly_capacity <= 200', name='chk_capacity_valid'),
        CheckConstraint('weather_reliability_score >= 0 AND weather_reliability_score <= 1', 
                       name='chk_weather_score_valid'),
        CheckConstraint('average_delay_minutes >= 0', name='chk_delay_positive'),
        Index('idx_airport_country', 'country'),
        Index('idx_airport_city', 'city'),
        Index('idx_airport_location', 'latitude', 'longitude'),
        Index('idx_airport_hub', 'is_hub'),
    )


class Aircraft(Base):
    """Aircraft database model with technical and operational constraints"""
    __tablename__ = 'aircraft'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airline_id = Column(UUID(as_uuid=True), ForeignKey('airlines.id'), nullable=False)
    registration = Column(String(10), unique=True, nullable=False, index=True)
    aircraft_type = Column(String(50), nullable=False)  # e.g., 'Boeing 737-800'
    manufacturer = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    
    # Capacity and configuration
    total_seats = Column(SmallInteger, nullable=False)
    business_seats = Column(SmallInteger, default=0)
    premium_economy_seats = Column(SmallInteger, default=0)
    economy_seats = Column(SmallInteger, nullable=False)
    
    # Technical specifications
    max_range_km = Column(Integer, nullable=False)
    cruise_speed_kmh = Column(Integer, nullable=False)
    fuel_capacity_liters = Column(Integer)
    max_takeoff_weight_kg = Column(Integer)
    
    # Operational data
    year_manufactured = Column(SmallInteger)
    last_maintenance_date = Column(Date)
    next_maintenance_due = Column(Date)
    maintenance_status = Column(String(20), default='serviceable')
    current_location = Column(String(3))  # IATA airport code
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Performance tracking
    on_time_performance = Column(Float, default=0.85)  # 0-1 scale
    technical_reliability = Column(Float, default=0.95)  # 0-1 scale
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    airline = relationship("Airline", back_populates="aircraft")
    flights = relationship("Flight", back_populates="aircraft")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_seats > 0 AND total_seats <= 1000', name='chk_total_seats_valid'),
        CheckConstraint('business_seats >= 0', name='chk_business_seats_positive'),
        CheckConstraint('economy_seats > 0', name='chk_economy_seats_positive'),
        CheckConstraint('total_seats = business_seats + premium_economy_seats + economy_seats', 
                       name='chk_seat_configuration_valid'),
        CheckConstraint('max_range_km > 0', name='chk_range_positive'),
        CheckConstraint('cruise_speed_kmh > 200 AND cruise_speed_kmh < 2000', name='chk_speed_valid'),
        CheckConstraint('year_manufactured >= 1950 AND year_manufactured <= EXTRACT(YEAR FROM CURRENT_DATE)', 
                       name='chk_manufacture_year_valid'),
        CheckConstraint('on_time_performance >= 0 AND on_time_performance <= 1', 
                       name='chk_otp_valid'),
        CheckConstraint('technical_reliability >= 0 AND technical_reliability <= 1', 
                       name='chk_reliability_valid'),
        Index('idx_aircraft_airline', 'airline_id'),
        Index('idx_aircraft_type', 'aircraft_type'),
        Index('idx_aircraft_location', 'current_location'),
        Index('idx_aircraft_maintenance', 'next_maintenance_due'),
    )


class CrewMember(Base):
    """Crew member database model with certification and scheduling constraints"""
    __tablename__ = 'crew_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airline_id = Column(UUID(as_uuid=True), ForeignKey('airlines.id'), nullable=False)
    employee_id = Column(String(20), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Professional data
    position = Column(String(30), nullable=False)  # captain, first_officer, flight_attendant
    seniority_number = Column(Integer)
    hire_date = Column(Date, nullable=False)
    base_airport = Column(String(3), nullable=False)  # IATA code
    
    # Certifications and qualifications
    license_number = Column(String(20))
    license_expiry = Column(Date)
    aircraft_certifications = Column(ARRAY(String(50)))  # Array of aircraft types
    language_codes = Column(ARRAY(String(2)), default=['EN'])  # ISO language codes
    
    # Scheduling and availability
    current_location = Column(String(3))  # IATA airport code
    duty_start_time = Column(DateTime)
    duty_end_time = Column(DateTime)
    monthly_flight_hours = Column(Float, default=0.0)
    yearly_flight_hours = Column(Float, default=0.0)
    max_monthly_hours = Column(Float, default=100.0)
    max_yearly_hours = Column(Float, default=1000.0)
    
    # Status and availability
    status = Column(String(20), default='available')  # available, on_duty, off_duty, sick, vacation
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    airline = relationship("Airline", back_populates="crew_members")
    assigned_flights = relationship("Flight", secondary=flight_crew_association, back_populates="crew_members")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('airline_id', 'employee_id', name='uq_airline_employee_id'),
        CheckConstraint('monthly_flight_hours >= 0', name='chk_monthly_hours_positive'),
        CheckConstraint('yearly_flight_hours >= 0', name='chk_yearly_hours_positive'),
        CheckConstraint('max_monthly_hours > 0 AND max_monthly_hours <= 200', name='chk_max_monthly_valid'),
        CheckConstraint('max_yearly_hours > 0 AND max_yearly_hours <= 2400', name='chk_max_yearly_valid'),
        CheckConstraint('monthly_flight_hours <= max_monthly_hours', name='chk_monthly_within_limit'),
        CheckConstraint('yearly_flight_hours <= max_yearly_hours', name='chk_yearly_within_limit'),
        Index('idx_crew_airline', 'airline_id'),
        Index('idx_crew_position', 'position'),
        Index('idx_crew_base', 'base_airport'),
        Index('idx_crew_status', 'status'),
        Index('idx_crew_certifications', 'aircraft_certifications'),
    )


class Flight(Base):
    """Flight database model with comprehensive operational constraints"""
    __tablename__ = 'flights'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airline_id = Column(UUID(as_uuid=True), ForeignKey('airlines.id'), nullable=False)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey('aircraft.id'))
    
    # Flight identification
    flight_number = Column(String(10), nullable=False)
    departure_airport_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    arrival_airport_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    
    # Scheduled times
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    scheduled_duration_minutes = Column(Integer, nullable=False)
    
    # Actual times
    actual_departure = Column(DateTime)
    actual_arrival = Column(DateTime)
    actual_duration_minutes = Column(Integer)
    
    # Operational data
    status = Column(ENUM(FlightStatus), default=FlightStatus.SCHEDULED, nullable=False)
    gate_departure = Column(String(10))
    gate_arrival = Column(String(10))
    terminal_departure = Column(String(5))
    terminal_arrival = Column(String(5))
    
    # Performance metrics
    delay_minutes = Column(Integer, default=0)
    delay_code = Column(String(10))  # IATA delay codes
    cancellation_reason = Column(String(100))
    
    # Capacity and loading
    total_seats = Column(SmallInteger, nullable=False)
    seats_sold = Column(SmallInteger, default=0)
    passengers_boarded = Column(SmallInteger, default=0)
    load_factor = Column(Float, default=0.0)  # 0-1 scale
    
    # Distance and fuel
    distance_km = Column(Integer, nullable=False)
    estimated_fuel_consumption = Column(Integer)  # liters
    
    # Weather and conditions
    departure_weather_code = Column(String(10))
    arrival_weather_code = Column(String(10))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    airline = relationship("Airline", back_populates="flights")
    aircraft = relationship("Aircraft", back_populates="flights")
    departure_airport = relationship("Airport", foreign_keys=[departure_airport_id], 
                                   back_populates="departing_flights")
    arrival_airport = relationship("Airport", foreign_keys=[arrival_airport_id], 
                                 back_populates="arriving_flights")
    bookings = relationship("Booking", back_populates="flight", cascade="all, delete-orphan")
    crew_members = relationship("CrewMember", secondary=flight_crew_association, back_populates="assigned_flights")
    disruptions = relationship("Disruption", secondary=disruption_affected_flights, back_populates="affected_flights")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('airline_id', 'flight_number', 'scheduled_departure', 
                        name='uq_flight_airline_number_date'),
        CheckConstraint('departure_airport_id != arrival_airport_id', name='chk_different_airports'),
        CheckConstraint('scheduled_arrival > scheduled_departure', name='chk_arrival_after_departure'),
        CheckConstraint('scheduled_duration_minutes > 0', name='chk_duration_positive'),
        CheckConstraint('delay_minutes >= -60 AND delay_minutes <= 1440', name='chk_delay_reasonable'),
        CheckConstraint('seats_sold >= 0 AND seats_sold <= total_seats', name='chk_seats_sold_valid'),
        CheckConstraint('passengers_boarded >= 0 AND passengers_boarded <= seats_sold', 
                       name='chk_passengers_boarded_valid'),
        CheckConstraint('load_factor >= 0 AND load_factor <= 1', name='chk_load_factor_valid'),
        CheckConstraint('distance_km > 0', name='chk_distance_positive'),
        Index('idx_flight_airline', 'airline_id'),
        Index('idx_flight_number', 'flight_number'),
        Index('idx_flight_departure_airport', 'departure_airport_id'),
        Index('idx_flight_arrival_airport', 'arrival_airport_id'),
        Index('idx_flight_scheduled_departure', 'scheduled_departure'),
        Index('idx_flight_status', 'status'),
        Index('idx_flight_aircraft', 'aircraft_id'),
        Index('idx_flight_route', 'departure_airport_id', 'arrival_airport_id'),
        Index('idx_flight_date_route', 'scheduled_departure', 'departure_airport_id', 'arrival_airport_id'),
    )


class Passenger(Base):
    """Passenger database model with personal and preference constraints"""
    __tablename__ = 'passengers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Personal information
    title = Column(String(10))
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(1))  # M, F, X
    nationality = Column(String(2))  # ISO country code
    
    # Contact information
    email = Column(String(255), index=True)
    phone_primary = Column(String(20))
    phone_secondary = Column(String(20))
    
    # Address
    address_line1 = Column(String(100))
    address_line2 = Column(String(100))
    city = Column(String(50))
    state_province = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(2))  # ISO country code
    
    # Travel profile
    frequent_flyer_programs = Column(JSON)  # {airline_code: membership_number}
    loyalty_tier = Column(ENUM(LoyaltyTier), default=LoyaltyTier.BASIC)
    total_flights = Column(Integer, default=0)
    total_miles = Column(BigInteger, default=0)
    
    # Preferences
    preferred_seat_type = Column(String(20), default='window')
    preferred_meal = Column(String(20), default='standard')
    communication_preferences = Column(ARRAY(ENUM(CommunicationMethod)))
    language_preference = Column(String(2), default='EN')
    
    # Special requirements
    mobility_assistance = Column(Boolean, default=False)
    medical_conditions = Column(ARRAY(String(50)))
    dietary_restrictions = Column(ARRAY(String(30)))
    
    # Status and metadata
    status = Column(ENUM(PassengerStatus), default=PassengerStatus.ACTIVE)
    is_minor = Column(Boolean, default=False)
    guardian_passenger_id = Column(UUID(as_uuid=True), ForeignKey('passengers.id'))
    
    # Risk and security
    security_screening_level = Column(String(20), default='standard')
    no_fly_list = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_flight_date = Column(Date)
    
    # Relationships
    bookings = relationship("Booking", back_populates="passenger", cascade="all, delete-orphan")
    guardian = relationship("Passenger", remote_side=[id], backref="minors")
    special_services = relationship("Passenger", secondary=passenger_special_services, backref="passengers")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('gender IN (\'M\', \'F\', \'X\') OR gender IS NULL', name='chk_gender_valid'),
        CheckConstraint('date_of_birth IS NULL OR date_of_birth < CURRENT_DATE', name='chk_dob_past'),
        CheckConstraint('total_flights >= 0', name='chk_total_flights_positive'),
        CheckConstraint('total_miles >= 0', name='chk_total_miles_positive'),
        CheckConstraint('email IS NULL OR email LIKE \'%@%\'', name='chk_email_format'),
        Index('idx_passenger_email', 'email'),
        Index('idx_passenger_name', 'last_name', 'first_name'),
        Index('idx_passenger_loyalty', 'loyalty_tier'),
        Index('idx_passenger_status', 'status'),
        Index('idx_passenger_country', 'nationality'),
    )


class Booking(Base):
    """Booking database model with pricing and modification constraints"""
    __tablename__ = 'bookings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_id = Column(UUID(as_uuid=True), ForeignKey('flights.id'), nullable=False)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey('passengers.id'), nullable=False)
    
    # Booking identification
    booking_reference = Column(String(6), unique=True, nullable=False, index=True)
    ticket_number = Column(String(13), unique=True, index=True)
    
    # Seating
    seat_number = Column(String(5))
    seat_class = Column(String(20), nullable=False, default='economy')
    is_window_seat = Column(Boolean)
    is_aisle_seat = Column(Boolean)
    
    # Pricing
    base_fare = Column(Numeric(10, 2), nullable=False)
    taxes_fees = Column(Numeric(10, 2), default=0.00)
    total_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='GBP')
    
    # Booking details
    booking_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    booking_channel = Column(String(30), default='online')  # online, phone, travel_agent
    payment_method = Column(String(20), default='credit_card')
    payment_status = Column(ENUM(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Status and modifications
    status = Column(ENUM(BookingStatus), default=BookingStatus.CONFIRMED)
    check_in_time = Column(DateTime)
    boarding_pass_issued = Column(Boolean, default=False)
    baggage_count = Column(SmallInteger, default=0)
    
    # Changes and fees
    change_count = Column(SmallInteger, default=0)
    change_fees_paid = Column(Numeric(8, 2), default=0.00)
    original_flight_id = Column(UUID(as_uuid=True), ForeignKey('flights.id'))
    
    # Special services
    meal_preference = Column(String(20), default='standard')
    special_assistance = Column(ARRAY(String(30)))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flight = relationship("Flight", foreign_keys=[flight_id], back_populates="bookings")
    original_flight = relationship("Flight", foreign_keys=[original_flight_id])
    passenger = relationship("Passenger", back_populates="bookings")
    rebooking_records = relationship("RebookingRecord", back_populates="booking", cascade="all, delete-orphan")
    compensation_claims = relationship("EU261Compensation", back_populates="booking", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('flight_id', 'seat_number', name='uq_flight_seat'),
        CheckConstraint('base_fare > 0', name='chk_base_fare_positive'),
        CheckConstraint('taxes_fees >= 0', name='chk_taxes_positive'),
        CheckConstraint('total_paid >= base_fare', name='chk_total_at_least_base'),
        CheckConstraint('baggage_count >= 0 AND baggage_count <= 20', name='chk_baggage_reasonable'),
        CheckConstraint('change_count >= 0', name='chk_changes_positive'),
        CheckConstraint('change_fees_paid >= 0', name='chk_change_fees_positive'),
        CheckConstraint('length(booking_reference) = 6', name='chk_booking_ref_length'),
        Index('idx_booking_flight', 'flight_id'),
        Index('idx_booking_passenger', 'passenger_id'),
        Index('idx_booking_reference', 'booking_reference'),
        Index('idx_booking_status', 'status'),
        Index('idx_booking_date', 'booking_date'),
        Index('idx_booking_check_in', 'check_in_time'),
    )


class Disruption(Base):
    """Disruption database model with impact and resolution constraints"""
    __tablename__ = 'disruptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    airport_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'))
    
    # Disruption identification
    disruption_code = Column(String(20), unique=True, nullable=False, index=True)
    disruption_type = Column(ENUM(DisruptionType), nullable=False)
    cause = Column(ENUM(DisruptionCause), nullable=False)
    
    # Impact details
    severity = Column(String(20), nullable=False, default='medium')  # low, medium, high, critical
    affected_passengers_count = Column(Integer, default=0)
    affected_flights_count = Column(Integer, default=0)
    estimated_duration_hours = Column(Float)
    actual_duration_hours = Column(Float)
    
    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    predicted_end_time = Column(DateTime)
    
    # Description and details
    title = Column(String(200), nullable=False)
    description = Column(Text)
    external_reference = Column(String(50))  # Reference to external systems
    
    # Resolution tracking
    status = Column(String(20), default='active')  # active, resolved, monitoring
    resolution_actions = Column(JSON)  # Array of actions taken
    lessons_learned = Column(Text)
    
    # Cost impact
    estimated_cost = Column(Numeric(12, 2))
    actual_cost = Column(Numeric(12, 2))
    compensation_cost = Column(Numeric(12, 2), default=0.00)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50))  # System or user that created the disruption
    
    # Relationships
    airport = relationship("Airport", back_populates="disruptions")
    affected_flights = relationship("Flight", secondary=disruption_affected_flights, back_populates="disruptions")
    rebooking_records = relationship("RebookingRecord", back_populates="disruption")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('end_time IS NULL OR end_time > start_time', name='chk_end_after_start'),
        CheckConstraint('estimated_duration_hours IS NULL OR estimated_duration_hours > 0', 
                       name='chk_estimated_duration_positive'),
        CheckConstraint('actual_duration_hours IS NULL OR actual_duration_hours > 0', 
                       name='chk_actual_duration_positive'),
        CheckConstraint('affected_passengers_count >= 0', name='chk_passengers_positive'),
        CheckConstraint('affected_flights_count >= 0', name='chk_flights_positive'),
        CheckConstraint('estimated_cost IS NULL OR estimated_cost >= 0', name='chk_estimated_cost_positive'),
        CheckConstraint('actual_cost IS NULL OR actual_cost >= 0', name='chk_actual_cost_positive'),
        CheckConstraint('compensation_cost >= 0', name='chk_compensation_positive'),
        Index('idx_disruption_type', 'disruption_type'),
        Index('idx_disruption_severity', 'severity'),
        Index('idx_disruption_status', 'status'),
        Index('idx_disruption_start_time', 'start_time'),
        Index('idx_disruption_airport', 'airport_id'),
        Index('idx_disruption_cause', 'cause'),
    )


class RebookingRecord(Base):
    """Rebooking record database model with change tracking constraints"""
    __tablename__ = 'rebooking_records'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey('bookings.id'), nullable=False)
    disruption_id = Column(UUID(as_uuid=True), ForeignKey('disruptions.id'))
    
    # Original booking details
    original_flight_id = Column(UUID(as_uuid=True), ForeignKey('flights.id'), nullable=False)
    original_seat_number = Column(String(5))
    original_seat_class = Column(String(20), nullable=False)
    
    # New booking details
    new_flight_id = Column(UUID(as_uuid=True), ForeignKey('flights.id'), nullable=False)
    new_seat_number = Column(String(5))
    new_seat_class = Column(String(20), nullable=False)
    
    # Change details
    reason = Column(String(100), nullable=False)
    rebooking_type = Column(String(30), default='automatic')  # automatic, manual, passenger_requested
    priority_score = Column(Float, default=0.5)
    
    # Financial impact
    fare_difference = Column(Numeric(10, 2), default=0.00)
    change_fee = Column(Numeric(8, 2), default=0.00)
    refund_amount = Column(Numeric(10, 2), default=0.00)
    
    # Processing details
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_by = Column(String(50))  # system or agent ID
    processing_time_seconds = Column(Integer)
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, confirmed, failed
    confirmation_sent = Column(Boolean, default=False)
    passenger_notified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="rebooking_records")
    original_flight = relationship("Flight", foreign_keys=[original_flight_id])
    new_flight = relationship("Flight", foreign_keys=[new_flight_id])
    disruption = relationship("Disruption", back_populates="rebooking_records")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('original_flight_id != new_flight_id', name='chk_different_flights'),
        CheckConstraint('priority_score >= 0 AND priority_score <= 1', name='chk_priority_valid'),
        CheckConstraint('processing_time_seconds IS NULL OR processing_time_seconds > 0', 
                       name='chk_processing_time_positive'),
        CheckConstraint('refund_amount >= 0', name='chk_refund_positive'),
        Index('idx_rebooking_booking', 'booking_id'),
        Index('idx_rebooking_original_flight', 'original_flight_id'),
        Index('idx_rebooking_new_flight', 'new_flight_id'),
        Index('idx_rebooking_disruption', 'disruption_id'),
        Index('idx_rebooking_status', 'status'),
        Index('idx_rebooking_processed', 'processed_at'),
    )


class EU261Compensation(Base):
    """EU261 compensation database model with regulatory compliance constraints"""
    __tablename__ = 'eu261_compensations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey('bookings.id'), nullable=False)
    claim_reference = Column(String(20), unique=True, nullable=False, index=True)
    
    # Regulatory assessment
    is_eligible = Column(Boolean, nullable=False)
    eligibility_reason = Column(String(200))
    compensation_amount = Column(Numeric(8, 2))
    currency = Column(String(3), default='EUR')
    
    # Flight details for compensation calculation
    flight_distance_km = Column(Integer, nullable=False)
    delay_minutes = Column(Integer)
    is_cancelled = Column(Boolean, default=False)
    is_eu_flight = Column(Boolean, nullable=False)
    
    # Calculation details
    base_compensation = Column(Numeric(8, 2))
    reduction_percentage = Column(Float, default=0.0)
    final_compensation = Column(Numeric(8, 2))
    
    # Claim processing
    claim_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    assessment_date = Column(DateTime)
    payment_date = Column(DateTime)
    status = Column(ENUM(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Documentation
    supporting_documents = Column(ARRAY(String(200)))  # Array of document paths/URLs
    passenger_statement = Column(Text)
    airline_response = Column(Text)
    
    # Payment details
    payment_method = Column(String(30))
    payment_reference = Column(String(50))
    bank_details = Column(JSON)  # Encrypted bank details for transfer
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="compensation_claims")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('compensation_amount IS NULL OR compensation_amount > 0', 
                       name='chk_compensation_positive'),
        CheckConstraint('flight_distance_km > 0', name='chk_distance_positive'),
        CheckConstraint('delay_minutes IS NULL OR delay_minutes >= 0', name='chk_delay_positive'),
        CheckConstraint('reduction_percentage >= 0 AND reduction_percentage <= 1', 
                       name='chk_reduction_valid'),
        CheckConstraint('base_compensation IS NULL OR base_compensation > 0', 
                       name='chk_base_compensation_positive'),
        CheckConstraint('final_compensation IS NULL OR final_compensation >= 0', 
                       name='chk_final_compensation_positive'),
        CheckConstraint('payment_date IS NULL OR payment_date >= assessment_date', 
                       name='chk_payment_after_assessment'),
        Index('idx_compensation_booking', 'booking_id'),
        Index('idx_compensation_claim_ref', 'claim_reference'),
        Index('idx_compensation_status', 'status'),
        Index('idx_compensation_eligibility', 'is_eligible'),
        Index('idx_compensation_claim_date', 'claim_date'),
    )


class AgentDecision(Base):
    """Agent decision database model with AI decision tracking constraints"""
    __tablename__ = 'agent_decisions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Decision context
    decision_type = Column(String(50), nullable=False)
    context_factors = Column(JSON, nullable=False)
    decision_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Agent information
    agent_version = Column(String(20), nullable=False)
    model_version = Column(String(20), nullable=False)
    
    # Decision process
    alternatives_considered = Column(JSON)  # Array of alternative options
    reasoning_steps = Column(JSON)  # Array of reasoning steps
    confidence_score = Column(Float, nullable=False)
    
    # Decision outcome
    selected_option = Column(JSON, nullable=False)
    expected_impact = Column(JSON)
    actual_outcome = Column(JSON)
    
    # Performance metrics
    decision_quality_score = Column(Float)
    passenger_feedback = Column(Float)  # 1-5 scale
    operational_effectiveness = Column(Float)
    cost_effectiveness = Column(Float)
    
    # Learning data
    success_metrics = Column(JSON, default={})
    learning_points = Column(ARRAY(String(500)))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='chk_confidence_valid'),
        CheckConstraint('decision_quality_score IS NULL OR (decision_quality_score >= 0 AND decision_quality_score <= 1)', 
                       name='chk_quality_score_valid'),
        CheckConstraint('passenger_feedback IS NULL OR (passenger_feedback >= 1 AND passenger_feedback <= 5)', 
                       name='chk_feedback_valid'),
        CheckConstraint('operational_effectiveness IS NULL OR (operational_effectiveness >= 0 AND operational_effectiveness <= 1)', 
                       name='chk_operational_valid'),
        CheckConstraint('cost_effectiveness IS NULL OR cost_effectiveness >= 0', 
                       name='chk_cost_effectiveness_positive'),
        Index('idx_agent_decision_type', 'decision_type'),
        Index('idx_agent_decision_timestamp', 'decision_timestamp'),
        Index('idx_agent_version', 'agent_version'),
        Index('idx_agent_confidence', 'confidence_score'),
        Index('idx_agent_quality', 'decision_quality_score'),
    )


class ResourceAllocation(Base):
    """Resource allocation database model with capacity and constraint tracking"""
    __tablename__ = 'resource_allocations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disruption_id = Column(UUID(as_uuid=True), ForeignKey('disruptions.id'))
    
    # Resource details
    resource_type = Column(ENUM(ResourceType), nullable=False)
    resource_name = Column(String(100), nullable=False)
    location = Column(String(100))
    
    # Capacity and allocation
    total_capacity = Column(Integer, nullable=False)
    allocated_capacity = Column(Integer, default=0)
    reserved_capacity = Column(Integer, default=0)
    available_capacity = Column(Integer, nullable=False)
    
    # Timing
    allocation_start = Column(DateTime, nullable=False)
    allocation_end = Column(DateTime, nullable=False)
    
    # Cost tracking
    cost_per_unit = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), default=0.00)
    
    # Priority and constraints
    priority_level = Column(ENUM(Priority), default=Priority.MEDIUM)
    min_capacity_required = Column(Integer, default=1)
    max_capacity_allowed = Column(Integer)
    
    # Status
    status = Column(String(20), default='allocated')  # allocated, in_use, completed, cancelled
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('allocation_end > allocation_start', name='chk_end_after_start'),
        CheckConstraint('total_capacity > 0', name='chk_total_capacity_positive'),
        CheckConstraint('allocated_capacity >= 0 AND allocated_capacity <= total_capacity', 
                       name='chk_allocated_valid'),
        CheckConstraint('reserved_capacity >= 0 AND reserved_capacity <= total_capacity', 
                       name='chk_reserved_valid'),
        CheckConstraint('available_capacity >= 0 AND available_capacity <= total_capacity', 
                       name='chk_available_valid'),
        CheckConstraint('allocated_capacity + reserved_capacity + available_capacity = total_capacity', 
                       name='chk_capacity_balance'),
        CheckConstraint('cost_per_unit > 0', name='chk_cost_per_unit_positive'),
        CheckConstraint('total_cost >= 0', name='chk_total_cost_positive'),
        CheckConstraint('min_capacity_required > 0', name='chk_min_capacity_positive'),
        CheckConstraint('max_capacity_allowed IS NULL OR max_capacity_allowed >= min_capacity_required', 
                       name='chk_max_gte_min_capacity'),
        Index('idx_resource_type', 'resource_type'),
        Index('idx_resource_location', 'location'),
        Index('idx_resource_allocation_time', 'allocation_start', 'allocation_end'),
        Index('idx_resource_status', 'status'),
        Index('idx_resource_disruption', 'disruption_id'),
    )


# Database triggers and functions for data consistency
@listens_for(Aircraft, 'before_update')
def update_aircraft_maintenance_status(mapper, connection, target):
    """Update maintenance status based on dates"""
    if target.next_maintenance_due and target.next_maintenance_due <= datetime.now().date():
        target.maintenance_status = 'maintenance_due'


@listens_for(Flight, 'before_update')
def calculate_flight_metrics(mapper, connection, target):
    """Calculate flight performance metrics on update"""
    if target.actual_departure and target.scheduled_departure:
        delay = (target.actual_departure - target.scheduled_departure).total_seconds() / 60
        target.delay_minutes = int(delay)
    
    if target.seats_sold and target.total_seats:
        target.load_factor = target.seats_sold / target.total_seats


@listens_for(Booking, 'after_insert')
def update_flight_capacity(mapper, connection, target):
    """Update flight capacity when booking is created"""
    connection.execute(
        f"UPDATE flights SET seats_sold = seats_sold + 1 WHERE id = '{target.flight_id}'"
    )


@listens_for(ResourceAllocation, 'before_update')
def validate_capacity_allocation(mapper, connection, target):
    """Validate capacity allocation doesn't exceed limits"""
    if (target.allocated_capacity + target.reserved_capacity) > target.total_capacity:
        raise ValueError("Allocated + Reserved capacity cannot exceed total capacity")


# Database views for common queries
create_flight_summary_view = DDL("""
CREATE OR REPLACE VIEW flight_summary AS
SELECT 
    f.id,
    f.flight_number,
    al.name as airline_name,
    dep.iata_code as departure_airport,
    arr.iata_code as arrival_airport,
    f.scheduled_departure,
    f.scheduled_arrival,
    f.actual_departure,
    f.actual_arrival,
    f.status,
    f.delay_minutes,
    f.seats_sold,
    f.total_seats,
    f.load_factor,
    COALESCE(f.passengers_boarded, 0) as passengers_boarded
FROM flights f
JOIN airlines al ON f.airline_id = al.id
JOIN airports dep ON f.departure_airport_id = dep.id
JOIN airports arr ON f.arrival_airport_id = arr.id
""")

create_disruption_impact_view = DDL("""
CREATE OR REPLACE VIEW disruption_impact AS
SELECT 
    d.id,
    d.disruption_code,
    d.disruption_type,
    d.severity,
    d.start_time,
    d.end_time,
    COUNT(DISTINCT daf.flight_id) as affected_flights,
    COUNT(DISTINCT b.id) as affected_bookings,
    SUM(COALESCE(d.compensation_cost, 0)) as total_compensation,
    AVG(COALESCE(f.delay_minutes, 0)) as avg_delay_minutes
FROM disruptions d
LEFT JOIN disruption_affected_flights daf ON d.id = daf.disruption_id
LEFT JOIN flights f ON daf.flight_id = f.id
LEFT JOIN bookings b ON f.id = b.flight_id
GROUP BY d.id, d.disruption_code, d.disruption_type, d.severity, d.start_time, d.end_time
""")

create_passenger_travel_summary = DDL("""
CREATE OR REPLACE VIEW passenger_travel_summary AS
SELECT 
    p.id,
    p.first_name,
    p.last_name,
    p.loyalty_tier,
    COUNT(b.id) as total_bookings,
    COUNT(CASE WHEN f.status = 'completed' THEN 1 END) as completed_flights,
    COUNT(CASE WHEN f.status = 'cancelled' THEN 1 END) as cancelled_flights,
    AVG(CASE WHEN f.delay_minutes > 0 THEN f.delay_minutes END) as avg_delay_experienced,
    SUM(b.total_paid) as total_spent,
    MAX(b.booking_date) as last_booking_date
FROM passengers p
LEFT JOIN bookings b ON p.id = b.passenger_id
LEFT JOIN flights f ON b.flight_id = f.id
GROUP BY p.id, p.first_name, p.last_name, p.loyalty_tier
""")

# Apply views to metadata
listens_for(Base.metadata, 'after_create')(lambda target, connection, **kw: connection.execute(create_flight_summary_view))
listens_for(Base.metadata, 'after_create')(lambda target, connection, **kw: connection.execute(create_disruption_impact_view))
listens_for(Base.metadata, 'after_create')(lambda target, connection, **kw: connection.execute(create_passenger_travel_summary))


# Database maintenance functions
def create_database_indexes():
    """Create additional performance indexes"""
    additional_indexes = [
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flight_performance ON flights (status, delay_minutes, scheduled_departure)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_booking_passenger_status ON bookings (passenger_id, status, booking_date)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_disruption_active ON disruptions (status, start_time) WHERE status = 'active'",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_compensation_pending ON eu261_compensations (status, claim_date) WHERE status = 'pending'",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rebooking_priority ON rebooking_records (priority_score DESC, processed_at)",
    ]
    return additional_indexes


def create_database_constraints():
    """Create additional business rule constraints"""
    additional_constraints = [
        "ALTER TABLE flights ADD CONSTRAINT chk_flight_turnaround CHECK (scheduled_departure >= CURRENT_TIMESTAMP - INTERVAL '24 hours')",
        "ALTER TABLE bookings ADD CONSTRAINT chk_booking_future CHECK (booking_date <= CURRENT_TIMESTAMP)",
        "ALTER TABLE crew_members ADD CONSTRAINT chk_license_not_expired CHECK (license_expiry IS NULL OR license_expiry > CURRENT_DATE)",
        "ALTER TABLE aircraft ADD CONSTRAINT chk_maintenance_schedule CHECK (next_maintenance_due IS NULL OR next_maintenance_due > last_maintenance_date)",
    ]
    return additional_constraints


# Data archival and cleanup procedures
def create_data_archival_procedures():
    """Create procedures for data archival and cleanup"""
    archival_procedures = [
        """
        CREATE OR REPLACE FUNCTION archive_old_flights()
        RETURNS INTEGER AS $$
        DECLARE
            archived_count INTEGER;
        BEGIN
            -- Archive flights older than 2 years to archive table
            INSERT INTO flights_archive 
            SELECT * FROM flights 
            WHERE scheduled_departure < CURRENT_DATE - INTERVAL '2 years'
            AND status = 'completed';
            
            GET DIAGNOSTICS archived_count = ROW_COUNT;
            
            -- Delete archived flights from main table
            DELETE FROM flights 
            WHERE scheduled_departure < CURRENT_DATE - INTERVAL '2 years'
            AND status = 'completed';
            
            RETURN archived_count;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        CREATE OR REPLACE FUNCTION cleanup_old_agent_decisions()
        RETURNS INTEGER AS $$
        DECLARE
            cleaned_count INTEGER;
        BEGIN
            -- Delete agent decisions older than 1 year (keep summary data)
            DELETE FROM agent_decisions 
            WHERE decision_timestamp < CURRENT_DATE - INTERVAL '1 year';
            
            GET DIAGNOSTICS cleaned_count = ROW_COUNT;
            RETURN cleaned_count;
        END;
        $$ LANGUAGE plpgsql;
        """
    ]
    return archival_procedures


# Performance optimization functions
def create_performance_monitoring():
    """Create performance monitoring views and functions"""
    monitoring_views = [
        """
        CREATE OR REPLACE VIEW database_performance_summary AS
        SELECT 
            'flights' as table_name,
            COUNT(*) as row_count,
            pg_size_pretty(pg_total_relation_size('flights')) as table_size
        FROM flights
        UNION ALL
        SELECT 
            'bookings' as table_name,
            COUNT(*) as row_count,
            pg_size_pretty(pg_total_relation_size('bookings')) as table_size
        FROM bookings
        UNION ALL
        SELECT 
            'disruptions' as table_name,
            COUNT(*) as row_count,
            pg_size_pretty(pg_total_relation_size('disruptions')) as table_size
        FROM disruptions;
        """,
        """
        CREATE OR REPLACE VIEW query_performance_summary AS
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements 
        WHERE query LIKE '%flights%' OR query LIKE '%bookings%'
        ORDER BY total_time DESC
        LIMIT 20;
        """
    ]
    return monitoring_views