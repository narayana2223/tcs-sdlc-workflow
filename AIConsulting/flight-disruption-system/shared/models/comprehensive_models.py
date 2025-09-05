"""
Comprehensive Data Models for Flight Disruption Management System
Advanced Pydantic models with validation, business logic, and relationships
"""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any, Tuple
from uuid import UUID, uuid4
import re

from pydantic import BaseModel, Field, validator, root_validator, EmailStr
from geopy.distance import geodesic
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class FlightStatus(str, Enum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding" 
    DEPARTED = "departed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"
    ARRIVED = "arrived"

class DisruptionType(str, Enum):
    WEATHER = "weather"
    TECHNICAL = "technical"
    CREW = "crew"
    ATC = "atc"
    SECURITY = "security"
    OPERATIONAL = "operational"
    STRIKE = "strike"
    BIRD_STRIKE = "bird_strike"
    MEDICAL = "medical"
    RUNWAY_CLOSURE = "runway_closure"

class DisruptionSeverity(int, Enum):
    MINOR = 1      # < 30 min delay
    MODERATE = 2   # 30-60 min delay
    SIGNIFICANT = 3 # 1-3 hour delay
    MAJOR = 4      # 3-6 hour delay or cancellation
    CRITICAL = 5   # > 6 hour delay or multiple day impact

class PassengerStatus(str, Enum):
    ACTIVE = "active"
    CHECKED_IN = "checked_in"
    REBOOKED = "rebooked"
    COMPENSATED = "compensated"
    REFUNDED = "refunded"
    NO_SHOW = "no_show"
    UPGRADED = "upgraded"

class LoyaltyTier(str, Enum):
    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class SeatClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"

class CompensationStatus(str, Enum):
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    DISPUTED = "disputed"

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"
    VOICE_CALL = "voice_call"

class ResourceType(str, Enum):
    HOTEL = "hotel"
    TRANSPORT = "transport"
    MEAL_VOUCHER = "meal_voucher"
    LOUNGE_ACCESS = "lounge_access"
    WIFI_VOUCHER = "wifi_voucher"
    PHONE_CARD = "phone_card"

class DecisionType(str, Enum):
    REBOOKING = "rebooking"
    COMPENSATION = "compensation"
    RESOURCE_ALLOCATION = "resource_allocation"
    COMMUNICATION = "communication"
    ROUTING = "routing"

# ============================================================================
# CORE MODELS
# ============================================================================

class Airport(BaseModel):
    """Enhanced Airport model with operational data"""
    id: UUID = Field(default_factory=uuid4)
    iata_code: str = Field(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$')
    icao_code: str = Field(..., min_length=4, max_length=4, regex=r'^[A-Z]{4}$')
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=2, max_length=3, regex=r'^[A-Z]{2,3}$')
    timezone: str = Field(..., regex=r'^[A-Za-z]+/[A-Za-z_]+$')
    
    # Geographic coordinates
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
    # Operational data
    hub_airline_codes: List[str] = Field(default_factory=list)
    slots_per_hour: int = Field(default=60, ge=1, le=200)
    ground_handling_capacity: int = Field(default=100, ge=1)
    customs_processing_time: int = Field(default=30, ge=5, le=120)  # minutes
    minimum_connection_time: int = Field(default=45, ge=20, le=180)  # minutes
    
    # Weather and operational factors
    weather_impact_factor: float = Field(default=1.0, ge=0.1, le=5.0)
    historical_delay_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "iata_code": "LHR",
                "icao_code": "EGLL",
                "name": "London Heathrow Airport",
                "city": "London",
                "country": "GBR",
                "timezone": "Europe/London",
                "latitude": 51.4700,
                "longitude": -0.4543,
                "hub_airline_codes": ["BA", "VS"],
                "slots_per_hour": 80
            }
        }

class Aircraft(BaseModel):
    """Enhanced Aircraft model with maintenance and performance data"""
    id: UUID = Field(default_factory=uuid4)
    airline_id: UUID
    registration: str = Field(..., min_length=3, max_length=12)
    aircraft_type: str = Field(..., min_length=3, max_length=50)
    manufacturer: str = Field(..., min_length=2, max_length=50)
    model: str = Field(..., min_length=2, max_length=50)
    
    # Capacity and configuration
    total_seats: int = Field(..., ge=1, le=900)
    first_class_seats: int = Field(default=0, ge=0)
    business_class_seats: int = Field(default=0, ge=0)
    premium_economy_seats: int = Field(default=0, ge=0)
    economy_seats: int = Field(..., ge=1)
    
    # Technical specifications
    max_range_km: int = Field(..., ge=100, le=20000)
    cruise_speed_kmh: int = Field(..., ge=200, le=1500)
    fuel_capacity_liters: int = Field(..., ge=1000, le=500000)
    
    # Maintenance and reliability
    manufacture_date: date
    last_maintenance: date
    next_maintenance_due: date
    maintenance_status: str = Field(default="serviceable")
    reliability_score: float = Field(default=0.95, ge=0.0, le=1.0)
    
    # Operational factors
    weather_performance: Dict[str, float] = Field(default_factory=dict)
    historical_on_time_rate: float = Field(default=0.85, ge=0.0, le=1.0)
    average_turnaround_time: int = Field(default=45, ge=20, le=180)  # minutes
    
    @validator('economy_seats')
    def validate_seat_totals(cls, v, values):
        if 'total_seats' in values:
            first = values.get('first_class_seats', 0)
            business = values.get('business_class_seats', 0)
            premium = values.get('premium_economy_seats', 0)
            total_configured = first + business + premium + v
            if total_configured != values['total_seats']:
                raise ValueError('Sum of class seats must equal total seats')
        return v
    
    @validator('next_maintenance_due')
    def validate_maintenance_dates(cls, v, values):
        if 'last_maintenance' in values and v <= values['last_maintenance']:
            raise ValueError('Next maintenance must be after last maintenance')
        return v
    
    @property
    def age_years(self) -> float:
        return (date.today() - self.manufacture_date).days / 365.25
    
    @property
    def days_since_maintenance(self) -> int:
        return (date.today() - self.last_maintenance).days
    
    @property
    def maintenance_risk_factor(self) -> float:
        """Calculate maintenance risk factor based on age and time since maintenance"""
        age_factor = min(self.age_years / 25, 1.0)  # Normalize to 25 years
        maint_factor = min(self.days_since_maintenance / 365, 1.0)  # Normalize to 1 year
        return (age_factor + maint_factor) / 2

class Crew(BaseModel):
    """Flight crew model with qualifications and availability"""
    id: UUID = Field(default_factory=uuid4)
    airline_id: UUID
    crew_type: str = Field(..., regex=r'^(pilot|cabin|maintenance)$')
    employee_id: str = Field(..., min_length=3, max_length=20)
    
    # Personal information
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    nationality: str = Field(..., min_length=2, max_length=3)
    
    # Qualifications
    license_number: str = Field(..., min_length=5, max_length=20)
    license_expiry: date
    aircraft_qualifications: List[str] = Field(default_factory=list)
    language_skills: List[str] = Field(default_factory=list)
    
    # Availability and scheduling
    base_airport: str = Field(..., min_length=3, max_length=3)
    current_location: Optional[str] = None
    duty_start: Optional[datetime] = None
    duty_end: Optional[datetime] = None
    flight_hours_this_month: int = Field(default=0, ge=0, le=100)
    duty_hours_this_month: int = Field(default=0, ge=0, le=200)
    
    # Performance metrics
    on_time_rate: float = Field(default=0.95, ge=0.0, le=1.0)
    customer_rating: float = Field(default=4.0, ge=1.0, le=5.0)
    incident_count: int = Field(default=0, ge=0)
    
    @property
    def is_available(self) -> bool:
        """Check if crew member is available for duty"""
        now = datetime.now()
        if self.duty_start and self.duty_end:
            return now < self.duty_start or now > self.duty_end
        return True
    
    @property
    def regulatory_compliance_score(self) -> float:
        """Calculate regulatory compliance score"""
        # Check license validity
        days_to_expiry = (self.license_expiry - date.today()).days
        license_score = 1.0 if days_to_expiry > 30 else max(0.0, days_to_expiry / 30)
        
        # Check flight hour limits
        hour_score = 1.0 - (self.flight_hours_this_month / 100)
        
        return min(license_score, hour_score)

class Flight(BaseModel):
    """Comprehensive Flight model with operational data"""
    id: UUID = Field(default_factory=uuid4)
    airline_id: UUID
    flight_number: str = Field(..., min_length=3, max_length=10, regex=r'^[A-Z]{2,3}[0-9]{1,4}[A-Z]?$')
    
    # Route information
    departure_airport_id: UUID
    arrival_airport_id: UUID
    departure_airport: Airport
    arrival_airport: Airport
    
    # Schedule
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    
    # Aircraft and crew
    aircraft_id: UUID
    aircraft: Aircraft
    crew_assignments: List[UUID] = Field(default_factory=list)
    
    # Status and operations
    status: FlightStatus = FlightStatus.SCHEDULED
    gate: Optional[str] = Field(None, regex=r'^[A-Z]?[0-9]{1,3}[A-Z]?$')
    terminal: Optional[str] = Field(None, regex=r'^[0-9T][A-Z0-9]*$')
    
    # Commercial information
    booking_class_availability: Dict[SeatClass, int] = Field(default_factory=dict)
    passenger_count: int = Field(default=0, ge=0)
    baggage_count: int = Field(default=0, ge=0)
    cargo_weight_kg: float = Field(default=0.0, ge=0.0)
    
    # Operational factors
    weather_conditions: Dict[str, Any] = Field(default_factory=dict)
    atc_slot: Optional[datetime] = None
    fuel_planned_kg: float = Field(default=0.0, ge=0.0)
    fuel_actual_kg: Optional[float] = None
    
    # Performance metrics
    on_time_performance: float = Field(default=0.85, ge=0.0, le=1.0)
    delay_risk_score: float = Field(default=0.2, ge=0.0, le=1.0)
    
    @validator('scheduled_arrival')
    def validate_flight_times(cls, v, values):
        if 'scheduled_departure' in values and v <= values['scheduled_departure']:
            raise ValueError('Arrival must be after departure')
        return v
    
    @validator('passenger_count')
    def validate_passenger_capacity(cls, v, values):
        if 'aircraft' in values and v > values['aircraft'].total_seats:
            raise ValueError('Passenger count exceeds aircraft capacity')
        return v
    
    @property
    def scheduled_duration(self) -> timedelta:
        return self.scheduled_arrival - self.scheduled_departure
    
    @property
    def actual_duration(self) -> Optional[timedelta]:
        if self.actual_departure and self.actual_arrival:
            return self.actual_arrival - self.actual_departure
        return None
    
    @property
    def delay_minutes(self) -> int:
        if self.actual_departure:
            delay = self.actual_departure - self.scheduled_departure
            return max(0, int(delay.total_seconds() / 60))
        return 0
    
    @property
    def distance_km(self) -> float:
        """Calculate great circle distance between airports"""
        dep_coords = (self.departure_airport.latitude, self.departure_airport.longitude)
        arr_coords = (self.arrival_airport.latitude, self.arrival_airport.longitude)
        return geodesic(dep_coords, arr_coords).kilometers
    
    @property
    def is_domestic(self) -> bool:
        return self.departure_airport.country == self.arrival_airport.country
    
    @property
    def is_eu_regulation_applicable(self) -> bool:
        """Check if EU261 regulation applies"""
        eu_countries = {
            'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA',
            'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD',
            'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 'GBR', 'NOR', 'ISL', 'CHE'
        }
        
        return (self.departure_airport.country in eu_countries or 
                self.arrival_airport.country in eu_countries)

class PassengerProfile(BaseModel):
    """Comprehensive passenger profile with preferences and history"""
    id: UUID = Field(default_factory=uuid4)
    
    # Personal information
    pnr: str = Field(..., min_length=6, max_length=10, regex=r'^[A-Z0-9]{6,10}$')
    title: Optional[str] = Field(None, regex=r'^(Mr|Mrs|Ms|Miss|Dr|Prof)$')
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    
    # Contact information
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None
    
    # Travel document
    nationality: str = Field(..., min_length=2, max_length=3)
    passport_number: Optional[str] = Field(None, min_length=5, max_length=20)
    passport_expiry: Optional[date] = None
    
    # Personal details
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, regex=r'^(M|F|X)$')
    
    # Loyalty and preferences
    loyalty_tier: LoyaltyTier = LoyaltyTier.NONE
    frequent_flyer_number: Optional[str] = None
    lifetime_miles: int = Field(default=0, ge=0)
    tier_miles_current_year: int = Field(default=0, ge=0)
    
    # Travel preferences
    preferred_seat_type: Optional[str] = Field(None, regex=r'^(aisle|window|middle)$')
    preferred_meal: Optional[str] = None
    communication_preferences: List[NotificationType] = Field(default_factory=list)
    language_preference: str = Field(default="EN", min_length=2, max_length=3)
    
    # Special requirements
    special_assistance: List[str] = Field(default_factory=list)
    mobility_assistance: bool = False
    dietary_requirements: List[str] = Field(default_factory=list)
    medical_conditions: List[str] = Field(default_factory=list)
    
    # Travel patterns
    home_airport: Optional[str] = Field(None, min_length=3, max_length=3)
    frequent_routes: List[str] = Field(default_factory=list)
    travel_frequency_per_year: int = Field(default=0, ge=0)
    average_booking_lead_time_days: int = Field(default=14, ge=0)
    
    # Compensation and service history
    compensation_history: List[Dict[str, Any]] = Field(default_factory=list)
    service_failures: int = Field(default=0, ge=0)
    complaint_count: int = Field(default=0, ge=0)
    compliment_count: int = Field(default=0, ge=0)
    
    # Risk assessment
    no_show_rate: float = Field(default=0.02, ge=0.0, le=1.0)
    disruption_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    rebooking_flexibility: float = Field(default=0.7, ge=0.0, le=1.0)
    
    @validator('phone', 'alternative_phone')
    def validate_phone(cls, v):
        if v:
            try:
                parsed = phonenumbers.parse(v, None)
                if not phonenumbers.is_valid_number(parsed):
                    raise ValueError('Invalid phone number')
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            except NumberParseException:
                raise ValueError('Invalid phone number format')
        return v
    
    @validator('passport_expiry')
    def validate_passport_expiry(cls, v, values):
        if v and v <= date.today():
            raise ValueError('Passport must not be expired')
        return v
    
    @property
    def age(self) -> Optional[int]:
        if self.date_of_birth:
            return (date.today() - self.date_of_birth).days // 365
        return None
    
    @property
    def priority_score(self) -> float:
        """Calculate passenger priority score for rebooking"""
        score = 0.0
        
        # Loyalty tier scoring
        tier_scores = {
            LoyaltyTier.NONE: 0.0,
            LoyaltyTier.BRONZE: 0.1,
            LoyaltyTier.SILVER: 0.3,
            LoyaltyTier.GOLD: 0.6,
            LoyaltyTier.PLATINUM: 0.8,
            LoyaltyTier.DIAMOND: 1.0
        }
        score += tier_scores[self.loyalty_tier] * 40
        
        # Special needs (high priority)
        if self.mobility_assistance or self.special_assistance:
            score += 30
        
        # Travel frequency
        if self.travel_frequency_per_year > 50:
            score += 20
        elif self.travel_frequency_per_year > 20:
            score += 10
        elif self.travel_frequency_per_year > 10:
            score += 5
        
        # Service history (negative impact for complaints)
        if self.service_failures > 5:
            score += 15  # Compensation for poor service
        score -= self.complaint_count * 2
        score += self.compliment_count * 1
        
        # Age considerations
        if self.age and (self.age >= 65 or self.age <= 12):
            score += 10
        
        return min(100.0, max(0.0, score))
    
    @property
    def compensation_eligibility_factor(self) -> float:
        """Factor affecting compensation calculations"""
        base_factor = 1.0
        
        # Increase for high-tier passengers
        if self.loyalty_tier in [LoyaltyTier.PLATINUM, LoyaltyTier.DIAMOND]:
            base_factor *= 1.2
        
        # Increase for passengers with service failures
        if self.service_failures > 3:
            base_factor *= 1.1
        
        # Decrease for frequent no-shows
        if self.no_show_rate > 0.1:
            base_factor *= 0.9
        
        return base_factor

class Booking(BaseModel):
    """Enhanced booking model with commercial and operational data"""
    id: UUID = Field(default_factory=uuid4)
    passenger_id: UUID
    flight_id: UUID
    
    # Booking details
    booking_reference: str = Field(..., min_length=6, max_length=10, regex=r'^[A-Z0-9]{6,10}$')
    booking_date: datetime
    booking_channel: str = Field(default="web")  # web, mobile, agent, api
    
    # Seat and service
    seat_number: Optional[str] = Field(None, regex=r'^[0-9]{1,3}[A-Z]$')
    seat_class: SeatClass = SeatClass.ECONOMY
    fare_class: str = Field(..., min_length=1, max_length=3)
    
    # Pricing
    base_fare: Decimal = Field(..., ge=0)
    taxes: Decimal = Field(default=Decimal(0), ge=0)
    fees: Decimal = Field(default=Decimal(0), ge=0)
    total_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    
    # Services
    baggage_allowance: Dict[str, int] = Field(default_factory=dict)
    additional_services: List[Dict[str, Any]] = Field(default_factory=list)
    meal_preference: Optional[str] = None
    
    # Status and history
    status: PassengerStatus = PassengerStatus.ACTIVE
    check_in_time: Optional[datetime] = None
    boarding_group: Optional[str] = None
    
    # Commercial data
    revenue_contribution: Decimal = Field(default=Decimal(0), ge=0)
    cost_to_airline: Decimal = Field(default=Decimal(0), ge=0)
    profit_margin: Optional[float] = None
    
    # Rebooking and changes
    original_booking_id: Optional[UUID] = None
    change_count: int = Field(default=0, ge=0)
    change_fees_paid: Decimal = Field(default=Decimal(0), ge=0)
    
    @validator('total_price')
    def validate_total_price(cls, v, values):
        base = values.get('base_fare', Decimal(0))
        taxes = values.get('taxes', Decimal(0))
        fees = values.get('fees', Decimal(0))
        calculated_total = base + taxes + fees
        if abs(v - calculated_total) > Decimal('0.01'):
            raise ValueError('Total price must equal base fare + taxes + fees')
        return v
    
    @property
    def is_premium_booking(self) -> bool:
        return self.seat_class in [SeatClass.BUSINESS, SeatClass.FIRST]
    
    @property
    def rebooking_cost_limit(self) -> Decimal:
        """Maximum additional cost for rebooking based on original fare"""
        if self.seat_class == SeatClass.FIRST:
            return self.total_price * Decimal('0.3')
        elif self.seat_class == SeatClass.BUSINESS:
            return self.total_price * Decimal('0.5')
        elif self.seat_class == SeatClass.PREMIUM_ECONOMY:
            return self.total_price * Decimal('0.7')
        else:
            return self.total_price * Decimal('1.0')

class Disruption(BaseModel):
    """Comprehensive disruption model with impact analysis"""
    id: UUID = Field(default_factory=uuid4)
    flight_id: UUID
    
    # Classification
    type: DisruptionType
    severity: DisruptionSeverity
    category: str = Field(default="operational")  # operational, weather, security, etc.
    
    # Timing
    predicted_at: Optional[datetime] = None
    detected_at: datetime = Field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Impact assessment
    delay_minutes: int = Field(default=0, ge=0)
    cancellation_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    diversion_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Cause and description
    primary_cause: str = Field(..., min_length=1, max_length=500)
    contributing_factors: List[str] = Field(default_factory=list)
    description: str = Field(..., min_length=1, max_length=2000)
    
    # Affected entities
    affected_passenger_count: int = Field(default=0, ge=0)
    affected_crew_count: int = Field(default=0, ge=0)
    downstream_flight_impact: int = Field(default=0, ge=0)
    
    # External data
    weather_data: Dict[str, Any] = Field(default_factory=dict)
    atc_data: Dict[str, Any] = Field(default_factory=dict)
    airport_status: Dict[str, Any] = Field(default_factory=dict)
    
    # Cost estimates
    estimated_cost: Decimal = Field(default=Decimal(0), ge=0)
    actual_cost: Optional[Decimal] = None
    cost_breakdown: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Operational response
    contingency_plans: List[Dict[str, Any]] = Field(default_factory=list)
    resources_required: List[ResourceType] = Field(default_factory=list)
    communication_sent: bool = Field(default=False)
    
    # Learning and analytics
    predictability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    response_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @property
    def duration_hours(self) -> Optional[float]:
        if self.confirmed_at and self.resolved_at:
            delta = self.resolved_at - self.confirmed_at
            return delta.total_seconds() / 3600
        return None
    
    @property
    def prediction_accuracy_hours(self) -> Optional[float]:
        """Hours between prediction and confirmation"""
        if self.predicted_at and self.confirmed_at:
            delta = self.confirmed_at - self.predicted_at
            return delta.total_seconds() / 3600
        return None
    
    @property
    def severity_classification(self) -> str:
        """Human-readable severity classification"""
        classifications = {
            DisruptionSeverity.MINOR: "Minor delay (< 30 min)",
            DisruptionSeverity.MODERATE: "Moderate delay (30-60 min)",
            DisruptionSeverity.SIGNIFICANT: "Significant delay (1-3 hours)",
            DisruptionSeverity.MAJOR: "Major disruption (3-6 hours or cancellation)",
            DisruptionSeverity.CRITICAL: "Critical disruption (> 6 hours or multi-day impact)"
        }
        return classifications[self.severity]
    
    @property
    def compensation_trigger(self) -> bool:
        """Check if disruption triggers EU261 compensation"""
        return (self.delay_minutes >= 180 or 
                self.type in [DisruptionType.TECHNICAL, DisruptionType.OPERATIONAL] or
                self.cancellation_probability > 0.8)

# ============================================================================
# BUSINESS LOGIC MODELS
# ============================================================================

class RebookingOption(BaseModel):
    """Detailed rebooking option with scoring and costs"""
    id: UUID = Field(default_factory=uuid4)
    original_booking_id: UUID
    alternative_flight_id: UUID
    
    # Flight details
    new_departure: datetime
    new_arrival: datetime
    route_changes: List[Dict[str, Any]] = Field(default_factory=list)
    connection_count: int = Field(default=0, ge=0)
    
    # Costs and pricing
    fare_difference: Decimal = Field(default=Decimal(0))
    change_fee: Decimal = Field(default=Decimal(0), ge=0)
    total_additional_cost: Decimal = Field(default=Decimal(0))
    
    # Service levels
    seat_class_match: bool = True
    seat_assignment: Optional[str] = None
    meal_service_match: bool = True
    
    # Scoring factors
    time_convenience_score: float = Field(..., ge=0.0, le=1.0)
    cost_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    service_level_score: float = Field(..., ge=0.0, le=1.0)
    passenger_preference_score: float = Field(..., ge=0.0, le=1.0)
    
    # Overall metrics
    overall_score: float = Field(..., ge=0.0, le=1.0)
    recommendation_rank: int = Field(..., ge=1)
    
    # Operational considerations
    availability_confirmed: bool = False
    booking_deadline: datetime
    special_handling_required: bool = False
    
    @property
    def time_difference_hours(self) -> float:
        """Time difference from original departure"""
        # This would be calculated based on original flight timing
        # Placeholder implementation
        return 0.0
    
    @property
    def journey_duration_change_minutes(self) -> int:
        """Change in total journey duration"""
        # This would be calculated based on original vs new journey
        # Placeholder implementation
        return 0

class ResourceAllocation(BaseModel):
    """Resource allocation for disrupted passengers"""
    id: UUID = Field(default_factory=uuid4)
    disruption_id: UUID
    passenger_id: UUID
    
    # Resource types and details
    hotel: Optional[Dict[str, Any]] = None
    transport: Optional[Dict[str, Any]] = None
    meals: Optional[Dict[str, Any]] = None
    communication: Optional[Dict[str, Any]] = None
    
    # Costs and budgets
    total_cost: Decimal = Field(default=Decimal(0), ge=0)
    budget_allocated: Decimal = Field(default=Decimal(0), ge=0)
    cost_efficiency: float = Field(default=1.0, ge=0.0, le=2.0)
    
    # Quality metrics
    passenger_satisfaction_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    service_quality_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    
    # Operational
    allocation_time: datetime = Field(default_factory=datetime.now)
    fulfillment_status: str = Field(default="pending")
    provider_references: Dict[str, str] = Field(default_factory=dict)

class AgentDecision(BaseModel):
    """AI agent decision tracking and learning"""
    id: UUID = Field(default_factory=uuid4)
    decision_type: DecisionType
    context_id: UUID  # Reference to disruption, booking, etc.
    
    # Decision details
    decision_timestamp: datetime = Field(default_factory=datetime.now)
    agent_version: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    
    # Input data
    input_data: Dict[str, Any] = Field(default_factory=dict)
    context_factors: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    
    # Decision process
    reasoning_steps: List[Dict[str, Any]] = Field(default_factory=list)
    alternatives_considered: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Decision output
    decision_outcome: Dict[str, Any] = Field(default_factory=dict)
    expected_impact: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance tracking
    actual_outcome: Optional[Dict[str, Any]] = None
    success_metrics: Dict[str, float] = Field(default_factory=dict)
    learning_points: List[str] = Field(default_factory=list)
    
    # Feedback
    passenger_feedback: Optional[float] = Field(None, ge=1.0, le=5.0)
    operational_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    cost_effectiveness: Optional[float] = Field(None, ge=0.0, le=2.0)
    
    @property
    def decision_quality_score(self) -> float:
        """Overall quality score for the decision"""
        if not self.actual_outcome:
            return self.confidence_score
        
        # Calculate weighted score based on available metrics
        scores = []
        weights = []
        
        if self.passenger_feedback:
            scores.append(self.passenger_feedback / 5.0)
            weights.append(0.4)
        
        if self.operational_effectiveness:
            scores.append(self.operational_effectiveness)
            weights.append(0.3)
            
        if self.cost_effectiveness:
            scores.append(min(self.cost_effectiveness, 1.0))
            weights.append(0.3)
        
        if not scores:
            return self.confidence_score
        
        return sum(s * w for s, w in zip(scores, weights)) / sum(weights)

# ============================================================================
# SPECIALIZED BUSINESS MODELS
# ============================================================================

class EU261CompensationCalculation(BaseModel):
    """EU261 compensation calculation with full regulatory compliance"""
    id: UUID = Field(default_factory=uuid4)
    booking_id: UUID
    flight_id: UUID
    passenger_id: UUID
    disruption_id: UUID
    
    # Flight details for calculation
    flight_distance_km: int = Field(..., ge=0)
    departure_country: str = Field(..., min_length=2, max_length=3)
    arrival_country: str = Field(..., min_length=2, max_length=3)
    is_eu_carrier: bool
    
    # Disruption details
    delay_minutes: int = Field(..., ge=0)
    cancellation: bool = False
    denied_boarding: bool = False
    missed_connection: bool = False
    
    # Circumstances
    extraordinary_circumstances: bool = False
    circumstance_details: List[str] = Field(default_factory=list)
    advance_notice_hours: Optional[int] = Field(None, ge=0)
    alternative_offered: bool = False
    alternative_details: Optional[Dict[str, Any]] = None
    
    # Passenger factors
    passenger_contribution: bool = False  # Late arrival, missing documents, etc.
    no_show_history: bool = False
    
    # Compensation calculation
    base_compensation_eur: Decimal = Field(default=Decimal(0), ge=0)
    compensation_percentage: float = Field(default=1.0, ge=0.0, le=1.0)
    final_compensation_eur: Decimal = Field(default=Decimal(0), ge=0)
    
    # Additional entitlements
    care_services_eur: Decimal = Field(default=Decimal(0), ge=0)
    accommodation_eur: Decimal = Field(default=Decimal(0), ge=0)
    transport_eur: Decimal = Field(default=Decimal(0), ge=0)
    
    # Processing
    eligibility_status: CompensationStatus = CompensationStatus.ELIGIBLE
    calculation_date: datetime = Field(default_factory=datetime.now)
    review_required: bool = False
    legal_basis: str = Field(default="EU261/2004")
    
    @validator('base_compensation_eur', always=True)
    def calculate_base_compensation(cls, v, values):
        """Calculate base compensation according to EU261"""
        distance = values.get('flight_distance_km', 0)
        delay = values.get('delay_minutes', 0)
        cancelled = values.get('cancellation', False)
        denied = values.get('denied_boarding', False)
        
        # No compensation for delays under 3 hours (unless other factors)
        if delay < 180 and not cancelled and not denied:
            return Decimal(0)
        
        # Distance-based compensation rates
        if distance <= 1500:
            base = Decimal(250)  # €250 for short haul
        elif distance <= 3500:
            base = Decimal(400)  # €400 for medium haul
        else:
            base = Decimal(600)  # €600 for long haul
        
        # Reduce compensation for delays between 3-4 hours on long haul
        if distance > 3500 and 180 <= delay < 240 and not cancelled:
            base = Decimal(300)  # 50% reduction
        
        return base
    
    @validator('final_compensation_eur', always=True)
    def calculate_final_compensation(cls, v, values):
        """Calculate final compensation after adjustments"""
        base = values.get('base_compensation_eur', Decimal(0))
        percentage = values.get('compensation_percentage', 1.0)
        extraordinary = values.get('extraordinary_circumstances', False)
        passenger_fault = values.get('passenger_contribution', False)
        
        # No compensation for extraordinary circumstances
        if extraordinary:
            return Decimal(0)
        
        # Reduce compensation if passenger contributed to the issue
        if passenger_fault:
            percentage *= 0.5
        
        return base * Decimal(str(percentage))
    
    @property
    def total_entitlement_eur(self) -> Decimal:
        """Total compensation including care services"""
        return (self.final_compensation_eur + 
                self.care_services_eur + 
                self.accommodation_eur + 
                self.transport_eur)
    
    @property
    def processing_priority(self) -> int:
        """Priority for processing (1=highest, 5=lowest)"""
        if self.final_compensation_eur >= 600:
            return 1  # High value claims
        elif self.review_required:
            return 2  # Complex cases
        elif self.final_compensation_eur >= 400:
            return 3  # Medium value
        elif self.final_compensation_eur >= 250:
            return 4  # Standard claims
        else:
            return 5  # Low priority

class CostOptimizationModel(BaseModel):
    """Cost optimization model for resource allocation"""
    id: UUID = Field(default_factory=uuid4)
    optimization_scenario: str
    disruption_id: UUID
    
    # Optimization parameters
    passenger_count: int = Field(..., ge=1)
    budget_constraint: Decimal = Field(..., ge=0)
    time_constraint_hours: int = Field(..., ge=1)
    quality_target: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Cost components
    hotel_costs: List[Dict[str, Any]] = Field(default_factory=list)
    transport_costs: List[Dict[str, Any]] = Field(default_factory=list)
    meal_costs: List[Dict[str, Any]] = Field(default_factory=list)
    compensation_costs: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Optimization results
    recommended_allocation: Dict[str, Any] = Field(default_factory=dict)
    total_optimized_cost: Decimal = Field(default=Decimal(0), ge=0)
    cost_savings: Decimal = Field(default=Decimal(0))
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Algorithm details
    algorithm_used: str = Field(default="multi_objective_optimization")
    optimization_time_seconds: float = Field(default=0.0, ge=0.0)
    solution_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    @property
    def cost_per_passenger(self) -> Decimal:
        """Average cost per passenger"""
        if self.passenger_count > 0:
            return self.total_optimized_cost / self.passenger_count
        return Decimal(0)
    
    @property
    def efficiency_ratio(self) -> float:
        """Quality to cost ratio"""
        if self.total_optimized_cost > 0:
            return float(self.quality_score / (self.total_optimized_cost / 1000))
        return 0.0

# ============================================================================
# RESPONSE MODELS FOR APIs
# ============================================================================

class FlightDisruptionResponse(BaseModel):
    """Comprehensive response for flight disruption queries"""
    flight: Flight
    disruption: Optional[Disruption] = None
    affected_passengers: List[PassengerProfile] = Field(default_factory=list)
    rebooking_options: List[RebookingOption] = Field(default_factory=list)
    resource_allocations: List[ResourceAllocation] = Field(default_factory=list)
    compensation_calculations: List[EU261CompensationCalculation] = Field(default_factory=list)
    total_estimated_cost: Decimal = Field(default=Decimal(0))
    response_timestamp: datetime = Field(default_factory=datetime.now)

class PassengerServiceResponse(BaseModel):
    """Response for passenger service operations"""
    passenger: PassengerProfile
    current_bookings: List[Booking] = Field(default_factory=list)
    disruption_history: List[Disruption] = Field(default_factory=list)
    compensation_history: List[EU261CompensationCalculation] = Field(default_factory=list)
    priority_score: float
    recommended_actions: List[str] = Field(default_factory=list)

class OptimizationResponse(BaseModel):
    """Response for cost optimization operations"""
    optimization_model: CostOptimizationModel
    cost_breakdown: Dict[str, Decimal] = Field(default_factory=dict)
    savings_analysis: Dict[str, Any] = Field(default_factory=dict)
    implementation_plan: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Dict[str, float] = Field(default_factory=dict)