"""
EU261 Compensation Calculator
Comprehensive implementation of EU Regulation 261/2004 for flight compensation
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ..models.comprehensive_models import (
    Flight, PassengerProfile, Booking, Disruption, DisruptionType,
    EU261CompensationCalculation, CompensationStatus
)


class ExtraordinaryCircumstance(str, Enum):
    """Types of extraordinary circumstances that may exempt compensation"""
    WEATHER_SEVERE = "severe_weather"
    AIR_TRAFFIC_CONTROL = "air_traffic_control_strike"
    SECURITY_ALERT = "security_alert"
    POLITICAL_INSTABILITY = "political_instability"
    NATURAL_DISASTER = "natural_disaster"
    BIRD_STRIKE = "bird_strike"
    MEDICAL_EMERGENCY = "medical_emergency"
    RUNWAY_CLOSURE = "runway_closure"
    AIRPORT_CLOSURE = "airport_closure"


class EU261Calculator:
    """
    Comprehensive EU261 compensation calculator implementing all aspects
    of European Union Regulation 261/2004
    """
    
    # EU/EEA country codes for regulation applicability
    EU_COUNTRIES = {
        'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA',
        'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD',
        'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 'GBR', 'NOR', 'ISL', 'CHE'
    }
    
    # Compensation amounts by distance (in EUR)
    COMPENSATION_RATES = {
        'short_haul': Decimal('250'),      # ≤ 1500km
        'medium_haul': Decimal('400'),     # 1501-3500km
        'long_haul': Decimal('600'),       # > 3500km
        'long_haul_reduced': Decimal('300') # > 3500km with 3-4h delay
    }
    
    # Care service limits per passenger per day (in EUR)
    CARE_LIMITS = {
        'meal_short': Decimal('25'),       # Short haul flights
        'meal_medium': Decimal('35'),      # Medium haul flights  
        'meal_long': Decimal('50'),        # Long haul flights
        'hotel_per_night': Decimal('150'), # Hotel accommodation
        'transport': Decimal('50'),        # Airport-hotel transport
        'communication': Decimal('15')     # Phone calls/internet
    }
    
    def __init__(self):
        """Initialize the EU261 calculator"""
        self.calculation_history: List[EU261CompensationCalculation] = []
    
    def calculate_compensation(
        self,
        flight: Flight,
        passenger: PassengerProfile,
        booking: Booking,
        disruption: Disruption,
        additional_context: Optional[Dict] = None
    ) -> EU261CompensationCalculation:
        """
        Calculate complete EU261 compensation for a passenger
        
        Args:
            flight: Flight details
            passenger: Passenger profile
            booking: Booking information
            disruption: Disruption details
            additional_context: Additional context for calculation
            
        Returns:
            Complete compensation calculation
        """
        context = additional_context or {}
        
        # Create calculation object
        calculation = EU261CompensationCalculation(
            booking_id=booking.id,
            flight_id=flight.id,
            passenger_id=passenger.id,
            disruption_id=disruption.id,
            flight_distance_km=int(flight.distance_km),
            departure_country=flight.departure_airport.country,
            arrival_country=flight.arrival_airport.country,
            is_eu_carrier=self._is_eu_carrier(flight),
            delay_minutes=disruption.delay_minutes,
            cancellation=flight.status.value == 'cancelled',
            denied_boarding=context.get('denied_boarding', False),
            missed_connection=context.get('missed_connection', False)
        )
        
        # Step 1: Check regulation applicability
        if not self._is_regulation_applicable(flight):
            calculation.eligibility_status = CompensationStatus.NOT_ELIGIBLE
            calculation.legal_basis = "Flight not subject to EU261/2004"
            return calculation
        
        # Step 2: Check extraordinary circumstances
        extraordinary, circumstances = self._assess_extraordinary_circumstances(
            disruption, context
        )
        calculation.extraordinary_circumstances = extraordinary
        calculation.circumstance_details = circumstances
        
        if extraordinary:
            calculation.eligibility_status = CompensationStatus.NOT_ELIGIBLE
            calculation.legal_basis = "EU261/2004 Art. 5(3) - Extraordinary circumstances"
            return calculation
        
        # Step 3: Check passenger contribution/fault
        passenger_fault = self._assess_passenger_contribution(passenger, context)
        calculation.passenger_contribution = passenger_fault
        
        # Step 4: Assess advance notice and alternatives
        advance_notice = context.get('advance_notice_hours')
        alternative_offered = context.get('alternative_offered', False)
        calculation.advance_notice_hours = advance_notice
        calculation.alternative_offered = alternative_offered
        calculation.alternative_details = context.get('alternative_details')
        
        # Step 5: Calculate base compensation
        base_compensation = self._calculate_base_compensation(
            flight, disruption, advance_notice, alternative_offered
        )
        calculation.base_compensation_eur = base_compensation
        
        # Step 6: Apply adjustments
        percentage = self._calculate_compensation_percentage(
            flight, disruption, passenger, advance_notice, alternative_offered, passenger_fault
        )
        calculation.compensation_percentage = percentage
        
        # Step 7: Calculate care services
        care_costs = self._calculate_care_services(flight, disruption, passenger, context)
        calculation.care_services_eur = care_costs['meals']
        calculation.accommodation_eur = care_costs['accommodation']
        calculation.transport_eur = care_costs['transport']
        
        # Step 8: Determine eligibility status
        if calculation.final_compensation_eur > 0 or sum(care_costs.values()) > 0:
            calculation.eligibility_status = CompensationStatus.ELIGIBLE
        else:
            calculation.eligibility_status = CompensationStatus.NOT_ELIGIBLE
        
        # Step 9: Check if review is required
        calculation.review_required = self._requires_manual_review(calculation, context)
        
        # Store calculation
        self.calculation_history.append(calculation)
        
        return calculation
    
    def _is_regulation_applicable(self, flight: Flight) -> bool:
        """
        Check if EU261 regulation applies to this flight
        
        EU261 applies to:
        1. Flights departing from EU airport (any airline)
        2. Flights arriving at EU airport operated by EU carrier
        """
        dep_eu = flight.departure_airport.country in self.EU_COUNTRIES
        arr_eu = flight.arrival_airport.country in self.EU_COUNTRIES
        eu_carrier = self._is_eu_carrier(flight)
        
        return dep_eu or (arr_eu and eu_carrier)
    
    def _is_eu_carrier(self, flight: Flight) -> bool:
        """Check if airline is EU-based (simplified check)"""
        # This would be enhanced with a comprehensive airline database
        eu_airline_prefixes = ['BA', 'LH', 'AF', 'KL', 'AZ', 'IB', 'EI', 'SK', 'AY']
        return any(flight.flight_number.startswith(prefix) for prefix in eu_airline_prefixes)
    
    def _assess_extraordinary_circumstances(
        self, 
        disruption: Disruption, 
        context: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Assess if extraordinary circumstances apply
        
        Returns:
            Tuple of (is_extraordinary, list_of_circumstances)
        """
        extraordinary = False
        circumstances = []
        
        # Weather-related circumstances
        if disruption.type == DisruptionType.WEATHER:
            weather = disruption.weather_data
            if weather.get('severe_weather_warning', False):
                extraordinary = True
                circumstances.append("Severe weather conditions")
            elif weather.get('visibility_m', 10000) < 150:
                extraordinary = True
                circumstances.append("Extremely low visibility")
            elif weather.get('wind_speed_kt', 0) > 65:
                extraordinary = True
                circumstances.append("Dangerous wind conditions")
        
        # ATC and security circumstances
        if disruption.type == DisruptionType.ATC:
            if context.get('atc_strike', False):
                extraordinary = True
                circumstances.append("Air traffic control strike")
            elif context.get('airspace_closure', False):
                extraordinary = True
                circumstances.append("Airspace closure by authorities")
        
        if disruption.type == DisruptionType.SECURITY:
            extraordinary = True
            circumstances.append("Security alert or threat")
        
        # Medical emergencies
        if disruption.type == DisruptionType.MEDICAL:
            if context.get('passenger_medical_emergency', False):
                extraordinary = True
                circumstances.append("Passenger medical emergency")
        
        # Bird strikes and other natural events
        if disruption.type == DisruptionType.BIRD_STRIKE:
            extraordinary = True
            circumstances.append("Bird strike incident")
        
        # Check for hidden technical issues that might not be extraordinary
        if disruption.type == DisruptionType.TECHNICAL:
            # Manufacturing defects discovered after delivery are extraordinary
            if context.get('manufacturing_defect', False):
                extraordinary = True
                circumstances.append("Manufacturing defect")
            # Sabotage or third-party damage
            elif context.get('sabotage', False):
                extraordinary = True
                circumstances.append("Third-party sabotage or damage")
        
        return extraordinary, circumstances
    
    def _assess_passenger_contribution(
        self, 
        passenger: PassengerProfile, 
        context: Dict
    ) -> bool:
        """
        Assess if passenger contributed to the disruption
        
        Returns:
            True if passenger contributed to the issue
        """
        # Late arrival at airport
        if context.get('passenger_late_arrival', False):
            return True
        
        # Missing or invalid documents
        if context.get('invalid_documents', False):
            return True
        
        # Disruptive behavior
        if context.get('disruptive_behavior', False):
            return True
        
        # Medical issues that weren't declared
        if context.get('undeclared_medical_condition', False):
            return True
        
        # High no-show rate indicating habitual non-compliance
        if passenger.no_show_rate > 0.2:
            return True
        
        return False
    
    def _calculate_base_compensation(
        self,
        flight: Flight,
        disruption: Disruption,
        advance_notice: Optional[int],
        alternative_offered: bool
    ) -> Decimal:
        """
        Calculate base compensation amount according to EU261 Article 7
        
        Returns:
            Base compensation amount in EUR
        """
        distance = flight.distance_km
        delay = disruption.delay_minutes
        cancelled = flight.status.value == 'cancelled'
        
        # No compensation for short delays
        if delay < 180 and not cancelled:
            return Decimal('0')
        
        # Distance-based compensation rates
        if distance <= 1500:
            base_amount = self.COMPENSATION_RATES['short_haul']
        elif distance <= 3500:
            base_amount = self.COMPENSATION_RATES['medium_haul']
        else:
            # Long haul flights have special rules
            if delay >= 240 or cancelled:
                base_amount = self.COMPENSATION_RATES['long_haul']
            else:
                # 3-4 hour delays get reduced compensation
                base_amount = self.COMPENSATION_RATES['long_haul_reduced']
        
        # Reductions for advance notice (cancellations only)
        if cancelled and advance_notice:
            if advance_notice >= 336:  # 14 days
                return Decimal('0')
            elif advance_notice >= 168:  # 7 days
                # Check if alternative offered arrives within time limits
                if alternative_offered:
                    return Decimal('0')  # Would need to check alternative times
        
        return base_amount
    
    def _calculate_compensation_percentage(
        self,
        flight: Flight,
        disruption: Disruption,
        passenger: PassengerProfile,
        advance_notice: Optional[int],
        alternative_offered: bool,
        passenger_fault: bool
    ) -> float:
        """
        Calculate the percentage of compensation to award
        
        Returns:
            Percentage as decimal (0.0 to 1.0)
        """
        percentage = 1.0
        
        # Reduce for passenger contribution
        if passenger_fault:
            percentage *= 0.5
        
        # Adjust for passenger loyalty (business decision, not legal requirement)
        if passenger.loyalty_tier.value in ['platinum', 'diamond']:
            percentage = min(1.0, percentage * 1.1)
        
        # Check for alternative transport offered
        if alternative_offered and advance_notice and advance_notice >= 168:
            # Significant reduction if good alternative provided with notice
            percentage *= 0.25
        
        return percentage
    
    def _calculate_care_services(
        self,
        flight: Flight,
        disruption: Disruption,
        passenger: PassengerProfile,
        context: Dict
    ) -> Dict[str, Decimal]:
        """
        Calculate care services compensation (meals, accommodation, transport)
        
        Returns:
            Dictionary with care service costs
        """
        care_costs = {
            'meals': Decimal('0'),
            'accommodation': Decimal('0'),
            'transport': Decimal('0'),
            'communication': Decimal('0')
        }
        
        delay_hours = max(disruption.delay_minutes / 60, 0)
        distance = flight.distance_km
        
        # Meal allowances based on delay duration and distance
        if distance <= 1500:  # Short haul
            if delay_hours >= 2:
                care_costs['meals'] = self.CARE_LIMITS['meal_short']
        elif distance <= 3500:  # Medium haul
            if delay_hours >= 3:
                care_costs['meals'] = self.CARE_LIMITS['meal_medium']
        else:  # Long haul
            if delay_hours >= 4:
                care_costs['meals'] = self.CARE_LIMITS['meal_long']
        
        # Accommodation for overnight delays
        if delay_hours >= 8 or context.get('overnight_delay', False):
            nights = max(1, int(delay_hours / 24))
            care_costs['accommodation'] = self.CARE_LIMITS['hotel_per_night'] * nights
            care_costs['transport'] = self.CARE_LIMITS['transport']
        
        # Communication allowances
        if delay_hours >= 1:
            care_costs['communication'] = self.CARE_LIMITS['communication']
        
        # Adjust for passenger special needs
        if passenger.mobility_assistance:
            care_costs['accommodation'] *= Decimal('1.2')  # Premium accessible room
            care_costs['transport'] *= Decimal('1.5')  # Special transport
        
        return care_costs
    
    def _requires_manual_review(
        self, 
        calculation: EU261CompensationCalculation, 
        context: Dict
    ) -> bool:
        """
        Determine if calculation requires manual review
        
        Returns:
            True if manual review is needed
        """
        # High-value claims
        if calculation.total_entitlement_eur > 1000:
            return True
        
        # Complex circumstances
        if len(calculation.circumstance_details) > 2:
            return True
        
        # Disputed extraordinary circumstances
        if calculation.extraordinary_circumstances and context.get('disputed', False):
            return True
        
        # VIP passengers
        if context.get('vip_passenger', False):
            return True
        
        # Legal complexity indicators
        if context.get('legal_complexity', False):
            return True
        
        # Previous complaints or legal action
        if context.get('previous_legal_action', False):
            return True
        
        return False
    
    def calculate_batch_compensation(
        self,
        affected_passengers: List[Tuple[Flight, PassengerProfile, Booking, Disruption]],
        shared_context: Optional[Dict] = None
    ) -> List[EU261CompensationCalculation]:
        """
        Calculate compensation for multiple passengers affected by same disruption
        
        Args:
            affected_passengers: List of (flight, passenger, booking, disruption) tuples
            shared_context: Context shared across all passengers
            
        Returns:
            List of compensation calculations
        """
        calculations = []
        shared_context = shared_context or {}
        
        for flight, passenger, booking, disruption in affected_passengers:
            # Merge shared context with passenger-specific context
            passenger_context = dict(shared_context)
            
            calculation = self.calculate_compensation(
                flight, passenger, booking, disruption, passenger_context
            )
            calculations.append(calculation)
        
        return calculations
    
    def get_compensation_summary(self) -> Dict:
        """
        Get summary statistics for all calculations
        
        Returns:
            Summary statistics dictionary
        """
        if not self.calculation_history:
            return {}
        
        total_calculations = len(self.calculation_history)
        eligible_calculations = [c for c in self.calculation_history 
                               if c.eligibility_status == CompensationStatus.ELIGIBLE]
        
        total_compensation = sum(c.final_compensation_eur for c in eligible_calculations)
        total_care_services = sum(c.care_services_eur + c.accommodation_eur + c.transport_eur 
                                for c in self.calculation_history)
        
        return {
            'total_calculations': total_calculations,
            'eligible_count': len(eligible_calculations),
            'eligibility_rate': len(eligible_calculations) / total_calculations,
            'total_compensation_eur': total_compensation,
            'total_care_services_eur': total_care_services,
            'average_compensation_eur': total_compensation / max(len(eligible_calculations), 1),
            'review_required_count': sum(1 for c in self.calculation_history if c.review_required),
            'extraordinary_circumstances_count': sum(1 for c in self.calculation_history 
                                                   if c.extraordinary_circumstances)
        }
    
    def validate_calculation(self, calculation: EU261CompensationCalculation) -> List[str]:
        """
        Validate a compensation calculation for compliance and accuracy
        
        Args:
            calculation: Compensation calculation to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check compensation amounts are within expected ranges
        if calculation.base_compensation_eur > 600:
            errors.append("Base compensation exceeds maximum EU261 amount")
        
        if calculation.final_compensation_eur < 0:
            errors.append("Final compensation cannot be negative")
        
        # Check care service limits
        if calculation.care_services_eur > self.CARE_LIMITS['meal_long'] * 3:
            errors.append("Care services amount seems excessive")
        
        if calculation.accommodation_eur > self.CARE_LIMITS['hotel_per_night'] * 7:
            errors.append("Accommodation costs seem excessive for delay duration")
        
        # Check logical consistency
        if (calculation.extraordinary_circumstances and 
            calculation.final_compensation_eur > 0):
            errors.append("Compensation awarded despite extraordinary circumstances")
        
        if (calculation.delay_minutes < 180 and 
            not calculation.cancellation and 
            calculation.final_compensation_eur > 0):
            errors.append("Compensation awarded for delay under 3 hours")
        
        return errors