from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Numeric, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

Base = declarative_base()

# Enums
class FlightStatus(str, Enum):
    SCHEDULED = "scheduled"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"
    BOARDING = "boarding"
    DEPARTED = "departed"
    ARRIVED = "arrived"

class DisruptionType(str, Enum):
    WEATHER = "weather"
    TECHNICAL = "technical"
    CREW = "crew"
    ATC = "atc"
    SECURITY = "security"
    OPERATIONAL = "operational"
    STRIKE = "strike"

class PassengerStatus(str, Enum):
    ACTIVE = "active"
    REBOOKED = "rebooked"
    COMPENSATED = "compensated"
    REFUNDED = "refunded"
    NO_SHOW = "no_show"

class CompensationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

class NotificationType(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    WHATSAPP = "whatsapp"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

# Models
class Airline(Base):
    __tablename__ = "airlines"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(3), nullable=False)
    contact_email = Column(String(255))
    pss_system = Column(String(50))  # amadeus, sabre, travelport
    api_credentials = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    flights = relationship("Flight", back_populates="airline")
    aircraft = relationship("Aircraft", back_populates="airline")

class Airport(Base):
    __tablename__ = "airports"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    country = Column(String(3), nullable=False)
    timezone = Column(String(50), nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    departing_flights = relationship("Flight", foreign_keys="Flight.departure_airport_id", back_populates="departure_airport")
    arriving_flights = relationship("Flight", foreign_keys="Flight.arrival_airport_id", back_populates="arrival_airport")

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    airline_id = Column(PGUUID(as_uuid=True), ForeignKey("airlines.id"))
    registration = Column(String(10), unique=True, nullable=False)
    aircraft_type = Column(String(50), nullable=False)
    seat_capacity = Column(Integer, nullable=False)
    business_class_seats = Column(Integer, default=0)
    economy_class_seats = Column(Integer, nullable=False)
    maintenance_status = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    airline = relationship("Airline", back_populates="aircraft")
    flights = relationship("Flight", back_populates="aircraft")

class Flight(Base):
    __tablename__ = "flights"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    airline_id = Column(PGUUID(as_uuid=True), ForeignKey("airlines.id"))
    flight_number = Column(String(10), nullable=False)
    departure_airport_id = Column(PGUUID(as_uuid=True), ForeignKey("airports.id"))
    arrival_airport_id = Column(PGUUID(as_uuid=True), ForeignKey("airports.id"))
    aircraft_id = Column(PGUUID(as_uuid=True), ForeignKey("aircraft.id"))
    scheduled_departure = Column(DateTime(timezone=True), nullable=False)
    scheduled_arrival = Column(DateTime(timezone=True), nullable=False)
    actual_departure = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    status = Column(ENUM(FlightStatus), default=FlightStatus.SCHEDULED)
    gate = Column(String(10))
    terminal = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    airline = relationship("Airline", back_populates="flights")
    departure_airport = relationship("Airport", foreign_keys=[departure_airport_id], back_populates="departing_flights")
    arrival_airport = relationship("Airport", foreign_keys=[arrival_airport_id], back_populates="arriving_flights")
    aircraft = relationship("Aircraft", back_populates="flights")
    bookings = relationship("Booking", back_populates="flight")
    disruptions = relationship("Disruption", back_populates="flight")
    predictions = relationship("DisruptionPrediction", back_populates="flight")
    
    # Indexes
    __table_args__ = (
        Index('idx_flight_departure_time', 'scheduled_departure'),
        Index('idx_flight_status', 'status'),
        Index('idx_flight_airline', 'airline_id'),
    )

class Passenger(Base):
    __tablename__ = "passengers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pnr = Column(String(10), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20), index=True)
    nationality = Column(String(3))
    passport_number = Column(String(20))
    date_of_birth = Column(Date)
    frequent_flyer_number = Column(String(50))
    mobility_assistance = Column(Boolean, default=False)
    dietary_requirements = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    bookings = relationship("Booking", back_populates="passenger")
    rebookings = relationship("Rebooking", back_populates="passenger")
    compensations = relationship("EU261Compensation", back_populates="passenger")
    notifications = relationship("Notification", back_populates="passenger")
    hotel_accommodations = relationship("HotelAccommodation", back_populates="passenger")
    transport_arrangements = relationship("TransportArrangement", back_populates="passenger")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"))
    flight_id = Column(PGUUID(as_uuid=True), ForeignKey("flights.id"))
    seat_number = Column(String(10))
    class_ = Column("class", String(20), nullable=False)  # business, economy
    booking_reference = Column(String(10), nullable=False, index=True)
    booking_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(ENUM(PassengerStatus), default=PassengerStatus.ACTIVE, index=True)
    original_price = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    passenger = relationship("Passenger", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")
    original_rebookings = relationship("Rebooking", back_populates="original_booking")
    compensations = relationship("EU261Compensation", back_populates="booking")

class Disruption(Base):
    __tablename__ = "disruptions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_id = Column(PGUUID(as_uuid=True), ForeignKey("flights.id"))
    type = Column(ENUM(DisruptionType), nullable=False, index=True)
    severity = Column(Integer)  # 1-5 scale
    predicted_at = Column(DateTime(timezone=True), index=True)
    confirmed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    delay_minutes = Column(Integer, default=0)
    description = Column(Text)
    cause_details = Column(JSONB)
    weather_data = Column(JSONB)
    affected_passenger_count = Column(Integer, default=0)
    estimated_cost = Column(Numeric(12, 2))
    actual_cost = Column(Numeric(12, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    flight = relationship("Flight", back_populates="disruptions")
    rebookings = relationship("Rebooking", back_populates="disruption")
    compensations = relationship("EU261Compensation", back_populates="disruption")
    notifications = relationship("Notification", back_populates="disruption")
    hotel_accommodations = relationship("HotelAccommodation", back_populates="disruption")
    transport_arrangements = relationship("TransportArrangement", back_populates="disruption")
    cost_optimizations = relationship("CostOptimizationRecord", back_populates="disruption")
    
    # Indexes
    __table_args__ = (
        Index('idx_disruption_severity', 'severity'),
    )

class Rebooking(Base):
    __tablename__ = "rebookings"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    original_booking_id = Column(PGUUID(as_uuid=True), ForeignKey("bookings.id"), index=True)
    new_flight_id = Column(PGUUID(as_uuid=True), ForeignKey("flights.id"))
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"), index=True)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"), index=True)
    rebooking_reason = Column(Text)
    cost_difference = Column(Numeric(10, 2), default=0)
    created_by = Column(String(50), default="system")  # system, agent, passenger
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    original_booking = relationship("Booking", back_populates="original_rebookings")
    new_flight = relationship("Flight")
    passenger = relationship("Passenger", back_populates="rebookings")
    disruption = relationship("Disruption", back_populates="rebookings")

class EU261Compensation(Base):
    __tablename__ = "eu261_compensation"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id = Column(PGUUID(as_uuid=True), ForeignKey("bookings.id"), index=True)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"))
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"), index=True)
    flight_distance_km = Column(Integer, nullable=False)
    delay_minutes = Column(Integer, nullable=False)
    compensation_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    reason = Column(Text, nullable=False)
    status = Column(ENUM(CompensationStatus), default=CompensationStatus.PENDING, index=True)
    processed_at = Column(DateTime(timezone=True))
    payment_reference = Column(String(100))
    exceptional_circumstances = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="compensations")
    disruption = relationship("Disruption", back_populates="compensations")
    passenger = relationship("Passenger", back_populates="compensations")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"), index=True)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"))
    type = Column(ENUM(NotificationType), nullable=False, index=True)
    recipient = Column(String(255), nullable=False)  # email or phone
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    status = Column(ENUM(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    sent_at = Column(DateTime(timezone=True), index=True)
    delivered_at = Column(DateTime(timezone=True))
    failed_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    passenger = relationship("Passenger", back_populates="notifications")
    disruption = relationship("Disruption", back_populates="notifications")

class HotelAccommodation(Base):
    __tablename__ = "hotel_accommodations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"), index=True)
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"), index=True)
    hotel_name = Column(String(255), nullable=False)
    hotel_address = Column(Text)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    room_type = Column(String(100))
    cost_per_night = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    booking_reference = Column(String(50))
    status = Column(String(20), default="booked", index=True)  # booked, confirmed, cancelled, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    disruption = relationship("Disruption", back_populates="hotel_accommodations")
    passenger = relationship("Passenger", back_populates="hotel_accommodations")

class TransportArrangement(Base):
    __tablename__ = "transport_arrangements"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"), index=True)
    passenger_id = Column(PGUUID(as_uuid=True), ForeignKey("passengers.id"), index=True)
    transport_type = Column(String(50), nullable=False)  # taxi, bus, train, rental_car
    pickup_location = Column(Text, nullable=False)
    destination = Column(Text, nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    booking_reference = Column(String(50))
    status = Column(String(20), default="scheduled", index=True)  # scheduled, confirmed, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    disruption = relationship("Disruption", back_populates="transport_arrangements")
    passenger = relationship("Passenger", back_populates="transport_arrangements")

class CostOptimizationRecord(Base):
    __tablename__ = "cost_optimization_records"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"), index=True)
    optimization_type = Column(String(50), nullable=False, index=True)  # hotel, transport, compensation, rebooking
    original_cost = Column(Numeric(12, 2), nullable=False)
    optimized_cost = Column(Numeric(12, 2), nullable=False)
    algorithm_used = Column(String(100))
    optimization_factors = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    disruption = relationship("Disruption", back_populates="cost_optimizations")
    
    # Computed property
    @property
    def savings(self) -> Decimal:
        return self.original_cost - self.optimized_cost

class PredictionModel(Base):
    __tablename__ = "prediction_models"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False, index=True)  # weather, technical, operational
    accuracy_score = Column(Numeric(5, 4))
    precision_score = Column(Numeric(5, 4))
    recall_score = Column(Numeric(5, 4))
    f1_score = Column(Numeric(5, 4))
    training_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    model_config = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    predictions = relationship("DisruptionPrediction", back_populates="model")

class DisruptionPrediction(Base):
    __tablename__ = "disruption_predictions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_id = Column(PGUUID(as_uuid=True), ForeignKey("flights.id"), index=True)
    model_id = Column(PGUUID(as_uuid=True), ForeignKey("prediction_models.id"))
    predicted_disruption_type = Column(ENUM(DisruptionType), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False, index=True)
    predicted_delay_minutes = Column(Integer)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    prediction_horizon_hours = Column(Integer, nullable=False, index=True)  # how far in advance
    input_features = Column(JSONB)
    was_accurate = Column(Boolean)  # filled after the fact
    actual_disruption_id = Column(PGUUID(as_uuid=True), ForeignKey("disruptions.id"))
    
    # Relationships
    flight = relationship("Flight", back_populates="predictions")
    model = relationship("PredictionModel", back_populates="predictions")
    actual_disruption = relationship("Disruption")

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    operation = Column(String(10), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    changed_by = Column(String(100))
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)