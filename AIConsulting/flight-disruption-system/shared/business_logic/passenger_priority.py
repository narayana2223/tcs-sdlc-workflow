"""
Passenger Priority Ranking System
Advanced algorithms for prioritizing passengers during flight disruptions
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math

from ..models.comprehensive_models import (
    Flight, PassengerProfile, Booking, Disruption, DisruptionType,
    LoyaltyTier, SeatClass, PassengerStatus
)


class PriorityCategory(str, Enum):
    """Priority categories for passenger handling"""
    CRITICAL = "critical"        # Immediate attention required
    HIGH = "high"               # High priority
    STANDARD = "standard"       # Normal priority
    LOW = "low"                # Lower priority
    FLEXIBLE = "flexible"       # Most flexible passengers


class PriorityFactor(str, Enum):
    """Factors that influence passenger priority"""
    LOYALTY_TIER = "loyalty_tier"
    SPECIAL_NEEDS = "special_needs"
    CONNECTIONS = "connections"
    BOOKING_CLASS = "booking_class"
    REVENUE_VALUE = "revenue_value"
    SERVICE_RECOVERY = "service_recovery"
    TIME_SENSITIVITY = "time_sensitivity"
    GROUP_TRAVEL = "group_travel"
    OPERATIONAL_IMPACT = "operational_impact"


class PassengerPriorityEngine:
    """
    Advanced passenger priority ranking engine for disruption management
    """
    
    # Base weights for different priority factors
    FACTOR_WEIGHTS = {
        PriorityFactor.LOYALTY_TIER: 25.0,
        PriorityFactor.SPECIAL_NEEDS: 30.0,
        PriorityFactor.CONNECTIONS: 20.0,
        PriorityFactor.BOOKING_CLASS: 15.0,
        PriorityFactor.REVENUE_VALUE: 10.0,
        PriorityFactor.SERVICE_RECOVERY: 20.0,
        PriorityFactor.TIME_SENSITIVITY: 15.0,
        PriorityFactor.GROUP_TRAVEL: 8.0,
        PriorityFactor.OPERATIONAL_IMPACT: 12.0
    }
    
    # Loyalty tier scoring
    LOYALTY_SCORES = {
        LoyaltyTier.DIAMOND: 100.0,
        LoyaltyTier.PLATINUM: 85.0,
        LoyaltyTier.GOLD: 70.0,
        LoyaltyTier.SILVER: 50.0,
        LoyaltyTier.BRONZE: 25.0,
        LoyaltyTier.NONE: 0.0
    }
    
    # Seat class scoring
    CLASS_SCORES = {
        SeatClass.FIRST: 100.0,
        SeatClass.BUSINESS: 80.0,
        SeatClass.PREMIUM_ECONOMY: 60.0,
        SeatClass.ECONOMY: 40.0
    }
    
    def __init__(self):
        """Initialize the passenger priority engine"""
        self.priority_history: List[Dict] = []
        self.custom_rules: List[Dict] = []
    
    def calculate_passenger_priority(
        self,
        passenger: PassengerProfile,
        booking: Booking,
        flight: Flight,
        disruption: Disruption,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive priority score for a passenger
        
        Args:
            passenger: Passenger profile
            booking: Booking information
            flight: Flight details
            disruption: Disruption details
            context: Additional context for priority calculation
            
        Returns:
            Dictionary containing priority score and breakdown
        """
        context = context or {}
        
        priority_scores = {}
        
        # Factor 1: Loyalty tier scoring
        priority_scores[PriorityFactor.LOYALTY_TIER] = self._calculate_loyalty_score(
            passenger, context
        )
        
        # Factor 2: Special needs and assistance
        priority_scores[PriorityFactor.SPECIAL_NEEDS] = self._calculate_special_needs_score(
            passenger, context
        )
        
        # Factor 3: Connection urgency
        priority_scores[PriorityFactor.CONNECTIONS] = self._calculate_connection_score(
            passenger, flight, disruption, context
        )
        
        # Factor 4: Booking class value
        priority_scores[PriorityFactor.BOOKING_CLASS] = self._calculate_class_score(
            booking, context
        )
        
        # Factor 5: Revenue value to airline
        priority_scores[PriorityFactor.REVENUE_VALUE] = self._calculate_revenue_score(
            passenger, booking, context
        )
        
        # Factor 6: Service recovery needs
        priority_scores[PriorityFactor.SERVICE_RECOVERY] = self._calculate_service_recovery_score(
            passenger, context
        )
        
        # Factor 7: Time sensitivity
        priority_scores[PriorityFactor.TIME_SENSITIVITY] = self._calculate_time_sensitivity_score(
            passenger, flight, context
        )
        
        # Factor 8: Group travel considerations
        priority_scores[PriorityFactor.GROUP_TRAVEL] = self._calculate_group_travel_score(
            passenger, context
        )
        
        # Factor 9: Operational impact
        priority_scores[PriorityFactor.OPERATIONAL_IMPACT] = self._calculate_operational_impact_score(
            passenger, booking, disruption, context
        )
        
        # Calculate weighted total score
        total_score = 0.0
        for factor, score in priority_scores.items():
            weight = self.FACTOR_WEIGHTS.get(factor, 10.0)
            total_score += score * (weight / 100.0)
        
        # Apply custom rules and adjustments
        total_score = self._apply_custom_rules(
            total_score, passenger, booking, flight, disruption, context
        )
        
        # Determine priority category
        category = self._determine_priority_category(total_score, priority_scores)
        
        # Calculate rebooking flexibility
        flexibility_score = self._calculate_flexibility_score(passenger, booking, context)
        
        # Build comprehensive priority result
        priority_result = {
            'passenger_id': passenger.id,
            'booking_id': booking.id,
            'total_score': round(total_score, 2),
            'category': category,
            'flexibility_score': flexibility_score,
            'factor_scores': {k.value: round(v, 2) for k, v in priority_scores.items()},
            'recommendations': self._generate_priority_recommendations(
                total_score, priority_scores, passenger, booking
            ),
            'estimated_wait_tolerance_minutes': self._calculate_wait_tolerance(
                passenger, total_score
            ),
            'rebooking_urgency': self._calculate_rebooking_urgency(
                total_score, disruption, context
            ),
            'calculated_at': datetime.now()
        }
        
        # Store in history
        self.priority_history.append(priority_result)
        
        return priority_result
    
    def _calculate_loyalty_score(self, passenger: PassengerProfile, context: Dict) -> float:
        """Calculate score based on loyalty tier and status"""
        base_score = self.LOYALTY_SCORES[passenger.loyalty_tier]
        
        # Bonus for high lifetime miles
        if passenger.lifetime_miles > 1000000:  # Million miler
            base_score *= 1.2
        elif passenger.lifetime_miles > 500000:
            base_score *= 1.1
        
        # Bonus for high annual activity
        if passenger.tier_miles_current_year > 100000:
            base_score *= 1.15
        
        # Bonus for frequent flyer on this route
        route_key = context.get('route', '')
        if route_key in passenger.frequent_routes:
            base_score *= 1.1
        
        return min(100.0, base_score)
    
    def _calculate_special_needs_score(self, passenger: PassengerProfile, context: Dict) -> float:
        """Calculate score for special assistance needs"""
        score = 0.0
        
        # Mobility assistance gets highest priority
        if passenger.mobility_assistance:
            score += 80.0
        
        # Medical conditions
        if passenger.medical_conditions:
            score += 60.0
            # Higher score for serious conditions
            serious_conditions = ['dialysis', 'oxygen', 'insulin', 'wheelchair']
            if any(condition in str(passenger.medical_conditions).lower() 
                   for condition in serious_conditions):
                score += 20.0
        
        # Age-based considerations
        if passenger.age:
            if passenger.age >= 75:
                score += 40.0
            elif passenger.age >= 65:
                score += 25.0
            elif passenger.age <= 12:
                score += 35.0
            elif passenger.age <= 2:
                score += 50.0
        
        # Special assistance requests
        if passenger.special_assistance:
            score += len(passenger.special_assistance) * 15.0
        
        # Unaccompanied minor
        if context.get('unaccompanied_minor', False):
            score += 70.0
        
        return min(100.0, score)
    
    def _calculate_connection_score(
        self, 
        passenger: PassengerProfile, 
        flight: Flight, 
        disruption: Disruption, 
        context: Dict
    ) -> float:
        """Calculate score based on connection urgency"""
        connecting_flights = context.get('connecting_flights', [])
        if not connecting_flights:
            return 10.0  # Base score for no connections
        
        score = 0.0
        max_urgency = 0.0
        
        for connection in connecting_flights:
            connection_time_minutes = connection.get('connection_time_minutes', 180)
            delay_impact = disruption.delay_minutes
            
            # Critical if connection will be missed
            buffer_time = connection_time_minutes - delay_impact
            if buffer_time < 0:
                urgency = 100.0  # Connection definitely missed
            elif buffer_time < 30:
                urgency = 90.0   # Very likely to miss
            elif buffer_time < 60:
                urgency = 70.0   # Might miss connection
            elif buffer_time < 90:
                urgency = 50.0   # Tight connection
            else:
                urgency = 20.0   # Comfortable connection
            
            # Adjust for connection importance
            if connection.get('final_destination', False):
                urgency *= 1.3
            if connection.get('last_flight_of_day', False):
                urgency *= 1.2
            if connection.get('weekend_connection', False):
                urgency *= 1.1
            
            max_urgency = max(max_urgency, urgency)
        
        return min(100.0, max_urgency)
    
    def _calculate_class_score(self, booking: Booking, context: Dict) -> float:
        """Calculate score based on seat class"""
        base_score = self.CLASS_SCORES[booking.seat_class]
        
        # Premium for highest fare class within cabin
        fare_class = booking.fare_class.upper()
        if fare_class in ['F', 'A', 'P']:  # Premium fare codes
            base_score *= 1.2
        elif fare_class in ['J', 'C', 'D', 'I']:  # Business fare codes
            base_score *= 1.1
        elif fare_class in ['W', 'S', 'Y', 'B', 'M', 'H']:  # Economy fare codes
            if booking.seat_class == SeatClass.ECONOMY:
                base_score *= 0.9  # Discounted economy
        
        return min(100.0, base_score)
    
    def _calculate_revenue_score(
        self, 
        passenger: PassengerProfile, 
        booking: Booking, 
        context: Dict
    ) -> float:
        """Calculate score based on revenue value"""
        # Base score from current booking value
        booking_value = float(booking.total_price)
        base_score = min(80.0, booking_value / 50.0)  # Normalize to max 80
        
        # Lifetime value consideration
        if passenger.lifetime_miles > 0:
            # Estimate lifetime value (rough calculation)
            estimated_lifetime_value = passenger.lifetime_miles * 0.02  # £0.02 per mile
            if estimated_lifetime_value > 10000:
                base_score *= 1.3
            elif estimated_lifetime_value > 5000:
                base_score *= 1.2
            elif estimated_lifetime_value > 2000:
                base_score *= 1.1
        
        # Annual travel frequency impact
        if passenger.travel_frequency_per_year > 50:
            base_score *= 1.2
        elif passenger.travel_frequency_per_year > 20:
            base_score *= 1.1
        
        return min(100.0, base_score)
    
    def _calculate_service_recovery_score(self, passenger: PassengerProfile, context: Dict) -> float:
        """Calculate score based on service recovery needs"""
        score = 0.0
        
        # Previous service failures
        if passenger.service_failures > 0:
            score += passenger.service_failures * 20.0
            
        # Recent complaints
        if passenger.complaint_count > 0:
            score += passenger.complaint_count * 15.0
            
        # Compensation history (indicates previous issues)
        compensation_count = len(passenger.compensation_history)
        if compensation_count > 0:
            score += compensation_count * 10.0
        
        # Social media influence (if tracked)
        if context.get('social_media_influence', False):
            score += 30.0
        
        # Corporate account
        if context.get('corporate_booking', False):
            score += 25.0
        
        return min(100.0, score)
    
    def _calculate_time_sensitivity_score(
        self, 
        passenger: PassengerProfile, 
        flight: Flight, 
        context: Dict
    ) -> float:
        """Calculate score based on time sensitivity"""
        score = 20.0  # Base score
        
        # Business travel typically more time-sensitive
        if context.get('travel_purpose') == 'business':
            score += 40.0
        
        # Events and meetings
        if context.get('critical_appointment', False):
            score += 60.0
        
        # Same-day connections
        if context.get('same_day_connections', False):
            score += 30.0
        
        # Weekend travel (leisure, more flexible)
        if flight.scheduled_departure.weekday() >= 5:  # Saturday/Sunday
            score -= 10.0
        
        # Vacation bookings (usually more flexible)
        if context.get('travel_purpose') == 'leisure':
            score -= 15.0
        
        # Advance booking (indicates planning, less flexible)
        booking_lead_days = context.get('booking_lead_days', 14)
        if booking_lead_days > 60:
            score -= 10.0
        elif booking_lead_days < 3:
            score += 20.0  # Last-minute bookings often urgent
        
        return max(0.0, min(100.0, score))
    
    def _calculate_group_travel_score(self, passenger: PassengerProfile, context: Dict) -> float:
        """Calculate score for group travel considerations"""
        group_size = context.get('group_size', 1)
        if group_size == 1:
            return 0.0
        
        score = 0.0
        
        # Larger groups get priority for rebooking together
        if group_size >= 10:
            score += 60.0
        elif group_size >= 5:
            score += 40.0
        elif group_size >= 2:
            score += 20.0
        
        # Family groups with children
        if context.get('family_group', False):
            score += 25.0
            if context.get('children_in_group', 0) > 0:
                score += 15.0
        
        # Tour group or organized travel
        if context.get('organized_group', False):
            score += 30.0
        
        return min(100.0, score)
    
    def _calculate_operational_impact_score(
        self, 
        passenger: PassengerProfile, 
        booking: Booking, 
        disruption: Disruption, 
        context: Dict
    ) -> float:
        """Calculate score based on operational impact"""
        score = 0.0
        
        # Crew members or airline staff
        if context.get('airline_employee', False):
            score += 80.0
        
        # Deadheading crew
        if context.get('deadhead_crew', False):
            score += 90.0
        
        # Passengers with tight connections affecting other flights
        if context.get('affects_other_flights', False):
            score += 50.0
        
        # VIP or special handling codes
        special_codes = context.get('special_handling_codes', [])
        if 'VIP' in special_codes:
            score += 70.0
        elif 'GOLD' in special_codes:
            score += 50.0
        
        # Media or public attention
        if context.get('media_attention', False):
            score += 40.0
        
        return min(100.0, score)
    
    def _calculate_flexibility_score(
        self, 
        passenger: PassengerProfile, 
        booking: Booking, 
        context: Dict
    ) -> float:
        """Calculate passenger flexibility for rebooking"""
        # Higher score means more flexible
        score = passenger.rebooking_flexibility * 100
        
        # Leisure travelers usually more flexible
        if context.get('travel_purpose') == 'leisure':
            score += 20.0
        
        # Advance bookings indicate planning, potentially more flexible
        booking_lead_days = context.get('booking_lead_days', 14)
        if booking_lead_days > 30:
            score += 15.0
        
        # Flexible fare classes
        fare_class = booking.fare_class.upper()
        if fare_class in ['Y', 'B', 'M']:  # Flexible economy
            score += 25.0
        elif fare_class in ['J', 'C', 'D']:  # Business class
            score += 30.0
        
        # No connections make passenger more flexible
        if not context.get('connecting_flights', []):
            score += 20.0
        
        return min(100.0, score)
    
    def _apply_custom_rules(
        self,
        base_score: float,
        passenger: PassengerProfile,
        booking: Booking,
        flight: Flight,
        disruption: Disruption,
        context: Dict
    ) -> float:
        """Apply custom business rules to adjust priority"""
        adjusted_score = base_score
        
        # Rule: Diamond passengers get minimum 90 score
        if passenger.loyalty_tier == LoyaltyTier.DIAMOND:
            adjusted_score = max(adjusted_score, 90.0)
        
        # Rule: First class passengers get minimum 85 score
        if booking.seat_class == SeatClass.FIRST:
            adjusted_score = max(adjusted_score, 85.0)
        
        # Rule: Passengers with mobility assistance get minimum 80 score
        if passenger.mobility_assistance:
            adjusted_score = max(adjusted_score, 80.0)
        
        # Rule: Reduce priority for frequent no-shows
        if passenger.no_show_rate > 0.15:
            adjusted_score *= 0.8
        
        # Rule: Increase priority for service recovery cases
        if passenger.service_failures > 3:
            adjusted_score *= 1.15
        
        # Apply any additional custom rules
        for rule in self.custom_rules:
            adjusted_score = self._apply_single_rule(
                rule, adjusted_score, passenger, booking, flight, disruption, context
            )
        
        return min(100.0, max(0.0, adjusted_score))
    
    def _apply_single_rule(
        self,
        rule: Dict,
        current_score: float,
        passenger: PassengerProfile,
        booking: Booking,
        flight: Flight,
        disruption: Disruption,
        context: Dict
    ) -> float:
        """Apply a single custom rule"""
        # This would implement custom rule logic
        # For now, return unchanged score
        return current_score
    
    def _determine_priority_category(
        self, 
        total_score: float, 
        factor_scores: Dict[PriorityFactor, float]
    ) -> PriorityCategory:
        """Determine priority category based on total score"""
        if total_score >= 90:
            return PriorityCategory.CRITICAL
        elif total_score >= 70:
            return PriorityCategory.HIGH
        elif total_score >= 40:
            return PriorityCategory.STANDARD
        elif total_score >= 20:
            return PriorityCategory.LOW
        else:
            return PriorityCategory.FLEXIBLE
    
    def _generate_priority_recommendations(
        self,
        total_score: float,
        factor_scores: Dict[PriorityFactor, float],
        passenger: PassengerProfile,
        booking: Booking
    ) -> List[str]:
        """Generate recommendations based on priority analysis"""
        recommendations = []
        
        if total_score >= 90:
            recommendations.append("Provide immediate personal assistance")
            recommendations.append("Offer premium rebooking options")
            recommendations.append("Consider upgrading service level")
        
        if factor_scores[PriorityFactor.SPECIAL_NEEDS] > 60:
            recommendations.append("Ensure special assistance continuity")
            recommendations.append("Prioritize accessible accommodations")
        
        if factor_scores[PriorityFactor.CONNECTIONS] > 70:
            recommendations.append("Focus on preserving connections")
            recommendations.append("Consider alternative routing")
        
        if factor_scores[PriorityFactor.SERVICE_RECOVERY] > 50:
            recommendations.append("Provide proactive service recovery")
            recommendations.append("Consider additional compensation")
        
        if booking.seat_class in [SeatClass.BUSINESS, SeatClass.FIRST]:
            recommendations.append("Maintain or upgrade service class")
            recommendations.append("Provide premium lounge access during wait")
        
        return recommendations
    
    def _calculate_wait_tolerance(self, passenger: PassengerProfile, priority_score: float) -> int:
        """Calculate estimated wait tolerance in minutes"""
        base_tolerance = 120  # 2 hours base tolerance
        
        # Adjust based on priority score
        if priority_score >= 90:
            return 30   # VIP passengers, very low tolerance
        elif priority_score >= 70:
            return 60   # High priority, low tolerance
        elif priority_score >= 40:
            return 90   # Standard tolerance
        else:
            return 180  # Flexible passengers, higher tolerance
    
    def _calculate_rebooking_urgency(
        self, 
        priority_score: float, 
        disruption: Disruption, 
        context: Dict
    ) -> str:
        """Calculate rebooking urgency level"""
        if priority_score >= 90:
            return "immediate"
        elif priority_score >= 70:
            return "urgent"
        elif priority_score >= 40:
            return "standard"
        else:
            return "flexible"
    
    def rank_passengers_for_rebooking(
        self,
        passengers_data: List[Tuple[PassengerProfile, Booking, Flight, Disruption]],
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple passengers for rebooking priority
        
        Args:
            passengers_data: List of (passenger, booking, flight, disruption) tuples
            context: Shared context for all passengers
            
        Returns:
            List of passengers ranked by priority (highest first)
        """
        context = context or {}
        priority_results = []
        
        for passenger, booking, flight, disruption in passengers_data:
            priority_result = self.calculate_passenger_priority(
                passenger, booking, flight, disruption, context
            )
            priority_results.append(priority_result)
        
        # Sort by total score (highest first), then by category priority
        category_order = {
            PriorityCategory.CRITICAL: 5,
            PriorityCategory.HIGH: 4,
            PriorityCategory.STANDARD: 3,
            PriorityCategory.LOW: 2,
            PriorityCategory.FLEXIBLE: 1
        }
        
        priority_results.sort(
            key=lambda x: (x['total_score'], category_order[x['category']]),
            reverse=True
        )
        
        # Add ranking information
        for i, result in enumerate(priority_results):
            result['priority_rank'] = i + 1
        
        return priority_results
    
    def add_custom_rule(self, rule: Dict):
        """Add a custom priority rule"""
        self.custom_rules.append(rule)
    
    def get_priority_statistics(self) -> Dict:
        """Get statistics about priority calculations"""
        if not self.priority_history:
            return {}
        
        scores = [p['total_score'] for p in self.priority_history]
        categories = [p['category'] for p in self.priority_history]
        
        return {
            'total_calculations': len(self.priority_history),
            'average_score': sum(scores) / len(scores),
            'score_distribution': {
                'critical': sum(1 for c in categories if c == PriorityCategory.CRITICAL),
                'high': sum(1 for c in categories if c == PriorityCategory.HIGH),
                'standard': sum(1 for c in categories if c == PriorityCategory.STANDARD),
                'low': sum(1 for c in categories if c == PriorityCategory.LOW),
                'flexible': sum(1 for c in categories if c == PriorityCategory.FLEXIBLE)
            },
            'highest_score': max(scores),
            'lowest_score': min(scores)
        }