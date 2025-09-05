import asyncio
import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import redis.asyncio as redis
from database import Database

logger = structlog.get_logger()

class RebookingEngine:
    """Intelligent rebooking engine for disrupted passengers"""
    
    def __init__(self, db: Database, redis_client: redis.Redis, http_client: httpx.AsyncClient):
        self.db = db
        self.redis = redis_client
        self.http_client = http_client
        
        # Rebooking preferences and weights
        self.weights = {
            'time_preference': 0.3,      # How close to original time
            'cost_difference': 0.25,     # Additional cost
            'travel_duration': 0.2,      # Total travel time
            'airline_preference': 0.1,   # Same airline preference
            'layovers': 0.1,            # Number of stops
            'seat_class': 0.05          # Seat class match
        }
    
    async def find_alternative_flights(
        self,
        original_booking: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find alternative flights for a disrupted booking"""
        try:
            departure_airport = original_booking.get('departure_airport')
            arrival_airport = original_booking.get('arrival_airport')
            original_departure = original_booking.get('scheduled_departure')
            preferred_class = preferences.get('class_preference', original_booking.get('class_'))
            
            if not all([departure_airport, arrival_airport, original_departure]):
                logger.error("Missing required booking information")
                return []
            
            # Determine search window
            search_start = original_departure
            search_hours = 24 if preferences.get('flexible_dates', True) else 12
            
            # Get direct flights first
            direct_flights = await self.db.find_alternative_flights(
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                departure_time=search_start,
                class_preference=preferred_class,
                hours_window=search_hours
            )
            
            alternatives = []
            
            # Process direct flights
            for flight in direct_flights:
                alternative = await self._create_flight_alternative(
                    flight, 
                    original_booking, 
                    preferences,
                    is_direct=True
                )
                if alternative:
                    alternatives.append(alternative)
            
            # If not enough direct flights, search for connecting flights
            if len(alternatives) < 5 and preferences.get('max_layovers', 2) > 0:
                connecting_flights = await self._find_connecting_flights(
                    departure_airport,
                    arrival_airport,
                    search_start,
                    search_hours,
                    preferences
                )
                alternatives.extend(connecting_flights)
            
            # Score and rank alternatives
            scored_alternatives = []
            for alt in alternatives:
                score = await self._score_alternative(alt, original_booking, preferences)
                alt['suitability_score'] = score
                scored_alternatives.append(alt)
            
            # Sort by score (higher is better)
            scored_alternatives.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            logger.info(
                "Alternative flights found",
                original_flight=f"{departure_airport}-{arrival_airport}",
                alternatives_count=len(scored_alternatives)
            )
            
            return scored_alternatives[:10]  # Return top 10 alternatives
            
        except Exception as e:
            logger.error("Failed to find alternative flights", error=str(e))
            return []
    
    async def select_best_alternative(
        self,
        alternatives: List[Dict[str, Any]],
        original_booking: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select the best alternative based on passenger preferences and constraints"""
        try:
            if not alternatives:
                return None
            
            # Filter by hard constraints
            viable_alternatives = []
            
            for alt in alternatives:
                # Check if passenger has mobility assistance requirements
                if original_booking.get('mobility_assistance', False):
                    if not alt.get('mobility_accessible', True):
                        continue
                
                # Check cost constraints (if specified)
                max_additional_cost = preferences.get('max_additional_cost')
                if max_additional_cost is not None:
                    if alt.get('cost_difference', 0) > max_additional_cost:
                        continue
                
                # Check time constraints
                preferred_departure = preferences.get('preferred_departure_time')
                if preferred_departure:
                    time_diff = abs((alt['departure_time'] - preferred_departure).total_seconds() / 3600)
                    if time_diff > preferences.get('max_time_difference_hours', 6):
                        continue
                
                viable_alternatives.append(alt)
            
            if not viable_alternatives:
                # If no alternatives meet hard constraints, relax them slightly
                viable_alternatives = alternatives[:3]  # Take top 3 by score
            
            # Select best alternative
            best_alternative = viable_alternatives[0]  # Already sorted by score
            
            # Add selection reasoning
            best_alternative['selection_reason'] = self._generate_selection_reason(
                best_alternative, 
                original_booking, 
                len(alternatives)
            )
            
            logger.info(
                "Best alternative selected",
                flight_id=str(best_alternative.get('flight_id')),
                score=best_alternative.get('suitability_score'),
                reason=best_alternative.get('selection_reason')
            )
            
            return best_alternative
            
        except Exception as e:
            logger.error("Failed to select best alternative", error=str(e))
            return alternatives[0] if alternatives else None
    
    async def _create_flight_alternative(
        self,
        flight: Dict[str, Any],
        original_booking: Dict[str, Any],
        preferences: Dict[str, Any],
        is_direct: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Create alternative flight option from flight data"""
        try:
            # Calculate cost difference (mock pricing logic)
            original_price = original_booking.get('original_price', 0)
            new_price = await self._estimate_flight_price(flight, original_booking.get('class_'))
            cost_difference = new_price - original_price
            
            # Calculate time differences
            original_departure = original_booking.get('scheduled_departure')
            new_departure = flight.get('scheduled_departure')
            time_difference_hours = (new_departure - original_departure).total_seconds() / 3600
            
            # Calculate travel duration
            travel_duration = (flight.get('scheduled_arrival') - flight.get('scheduled_departure')).total_seconds() / 3600
            
            alternative = {
                'flight_id': flight['id'],
                'flight_number': flight['flight_number'],
                'airline_name': flight['airline_name'],
                'aircraft_type': flight['aircraft_type'],
                'departure_time': flight['scheduled_departure'],
                'arrival_time': flight['scheduled_arrival'],
                'departure_airport': flight['departure_airport'],
                'arrival_airport': flight['arrival_airport'],
                'available_seats': flight.get('available_seats', 0),
                'is_direct': is_direct,
                'layovers': 0 if is_direct else 1,
                'travel_duration_hours': travel_duration,
                'time_difference_hours': time_difference_hours,
                'cost_difference': cost_difference,
                'estimated_price': new_price,
                'seat_class_available': await self._check_class_availability(flight, original_booking.get('class_')),
                'mobility_accessible': True,  # Assume accessible unless specified
                'meal_service': travel_duration > 2,  # Mock meal service logic
                'wifi_available': 'boeing' in flight.get('aircraft_type', '').lower(),  # Mock wifi logic
                'segments': [{
                    'flight_number': flight['flight_number'],
                    'departure_airport': flight['departure_airport'],
                    'arrival_airport': flight['arrival_airport'],
                    'departure_time': flight['scheduled_departure'],
                    'arrival_time': flight['scheduled_arrival'],
                    'aircraft_type': flight['aircraft_type']
                }]
            }
            
            return alternative
            
        except Exception as e:
            logger.error("Failed to create flight alternative", error=str(e))
            return None
    
    async def _find_connecting_flights(
        self,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        search_hours: int,
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find connecting flight options"""
        try:
            # Common connecting hubs for UK flights
            connecting_hubs = ['AMS', 'CDG', 'FRA', 'DUB', 'ZUR']
            
            connecting_alternatives = []
            max_layovers = preferences.get('max_layovers', 2)
            
            if max_layovers < 1:
                return []
            
            for hub in connecting_hubs:
                if hub in [departure_airport, arrival_airport]:
                    continue
                
                # Find first leg flights
                first_leg_flights = await self.db.find_alternative_flights(
                    departure_airport=departure_airport,
                    arrival_airport=hub,
                    departure_time=departure_time,
                    hours_window=search_hours
                )
                
                for first_flight in first_leg_flights[:3]:  # Limit to top 3 per hub
                    # Find connecting flights with minimum connection time
                    connection_time = first_flight['scheduled_arrival'] + timedelta(hours=1.5)  # Minimum connection
                    
                    second_leg_flights = await self.db.find_alternative_flights(
                        departure_airport=hub,
                        arrival_airport=arrival_airport,
                        departure_time=connection_time,
                        hours_window=12  # 12 hours to find connection
                    )
                    
                    for second_flight in second_leg_flights[:2]:  # Top 2 connections
                        # Create connecting flight alternative
                        connecting_alt = await self._create_connecting_alternative(
                            first_flight,
                            second_flight,
                            preferences
                        )
                        
                        if connecting_alt:
                            connecting_alternatives.append(connecting_alt)
            
            logger.info(
                "Connecting flights found",
                count=len(connecting_alternatives),
                route=f"{departure_airport}-{arrival_airport}"
            )
            
            return connecting_alternatives[:5]  # Return top 5 connecting options
            
        except Exception as e:
            logger.error("Failed to find connecting flights", error=str(e))
            return []
    
    async def _create_connecting_alternative(
        self,
        first_flight: Dict[str, Any],
        second_flight: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create connecting flight alternative"""
        try:
            # Calculate connection time
            connection_time = (second_flight['scheduled_departure'] - first_flight['scheduled_arrival']).total_seconds() / 3600
            
            if connection_time < 1.0 or connection_time > 8.0:  # Reasonable connection window
                return None
            
            # Calculate total travel time
            total_duration = (second_flight['scheduled_arrival'] - first_flight['scheduled_departure']).total_seconds() / 3600
            
            # Estimate combined pricing
            first_price = await self._estimate_flight_price(first_flight, preferences.get('class_preference', 'economy'))
            second_price = await self._estimate_flight_price(second_flight, preferences.get('class_preference', 'economy'))
            total_price = first_price + second_price
            
            connecting_alternative = {
                'flight_id': f"{first_flight['id']}-{second_flight['id']}",  # Composite ID
                'flight_number': f"{first_flight['flight_number']}/{second_flight['flight_number']}",
                'airline_name': f"{first_flight['airline_name']} + {second_flight['airline_name']}",
                'departure_time': first_flight['scheduled_departure'],
                'arrival_time': second_flight['scheduled_arrival'],
                'departure_airport': first_flight['departure_airport'],
                'arrival_airport': second_flight['arrival_airport'],
                'is_direct': False,
                'layovers': 1,
                'connection_time_hours': connection_time,
                'travel_duration_hours': total_duration,
                'estimated_price': total_price,
                'connecting_airport': second_flight['departure_airport'],
                'segments': [
                    {
                        'flight_number': first_flight['flight_number'],
                        'departure_airport': first_flight['departure_airport'],
                        'arrival_airport': first_flight['arrival_airport'],
                        'departure_time': first_flight['scheduled_departure'],
                        'arrival_time': first_flight['scheduled_arrival'],
                        'aircraft_type': first_flight['aircraft_type']
                    },
                    {
                        'flight_number': second_flight['flight_number'],
                        'departure_airport': second_flight['departure_airport'],
                        'arrival_airport': second_flight['arrival_airport'],
                        'departure_time': second_flight['scheduled_departure'],
                        'arrival_time': second_flight['scheduled_arrival'],
                        'aircraft_type': second_flight['aircraft_type']
                    }
                ]
            }
            
            return connecting_alternative
            
        except Exception as e:
            logger.error("Failed to create connecting alternative", error=str(e))
            return None
    
    async def _score_alternative(
        self,
        alternative: Dict[str, Any],
        original_booking: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> float:
        """Score an alternative flight based on multiple criteria"""
        try:
            score = 0.0
            
            # Time preference score (closer to original time is better)
            time_diff_hours = abs(alternative.get('time_difference_hours', 0))
            time_score = max(0, 1 - (time_diff_hours / 12))  # Normalize to 0-1, 12 hours max
            score += time_score * self.weights['time_preference']
            
            # Cost difference score (lower additional cost is better)
            cost_diff = alternative.get('cost_difference', 0)
            if cost_diff <= 0:
                cost_score = 1.0  # Same or cheaper price
            else:
                cost_score = max(0, 1 - (cost_diff / 500))  # Normalize with £500 as max reasonable difference
            score += cost_score * self.weights['cost_difference']
            
            # Travel duration score (shorter is better, but not too much penalty for reasonable duration)
            duration_hours = alternative.get('travel_duration_hours', 2)
            original_duration = (original_booking.get('scheduled_arrival') - original_booking.get('scheduled_departure')).total_seconds() / 3600
            duration_diff = duration_hours - original_duration
            duration_score = max(0, 1 - (max(0, duration_diff) / 6))  # 6 hour penalty max
            score += duration_score * self.weights['travel_duration']
            
            # Airline preference score (same airline is preferred)
            original_airline = original_booking.get('airline_name', '')
            current_airline = alternative.get('airline_name', '')
            airline_score = 1.0 if original_airline in current_airline else 0.5
            score += airline_score * self.weights['airline_preference']
            
            # Layovers score (direct flights preferred)
            layovers = alternative.get('layovers', 0)
            layover_score = max(0, 1 - (layovers * 0.3))  # Each layover reduces score by 0.3
            score += layover_score * self.weights['layovers']
            
            # Seat class score (same class preferred)
            original_class = original_booking.get('class_', 'economy')
            class_available = alternative.get('seat_class_available', True)
            class_score = 1.0 if class_available else 0.5
            score += class_score * self.weights['seat_class']
            
            # Bonus points for special considerations
            if alternative.get('is_direct', True):
                score += 0.1  # Direct flight bonus
            
            if alternative.get('wifi_available', False):
                score += 0.05  # WiFi bonus
            
            if alternative.get('meal_service', False):
                score += 0.03  # Meal service bonus
            
            # Penalty for very early or very late flights
            departure_hour = alternative.get('departure_time').hour
            if departure_hour < 6 or departure_hour > 22:
                score -= 0.1  # Early/late flight penalty
            
            return min(1.0, max(0.0, score))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error("Failed to score alternative", error=str(e))
            return 0.5  # Default middle score
    
    async def _estimate_flight_price(self, flight: Dict[str, Any], seat_class: str) -> float:
        """Estimate flight price (mock implementation)"""
        try:
            # Mock pricing based on route, time, and class
            base_price = 150.0  # Base economy price
            
            # Adjust for class
            class_multipliers = {
                'economy': 1.0,
                'premium_economy': 1.5,
                'business': 3.0,
                'first': 5.0
            }
            base_price *= class_multipliers.get(seat_class, 1.0)
            
            # Adjust for route distance (mock)
            departure = flight.get('departure_airport', '')
            arrival = flight.get('arrival_airport', '')
            
            # Mock distance-based pricing
            long_haul_routes = ['JFK', 'LAX', 'NRT', 'SYD']
            if any(airport in [departure, arrival] for airport in long_haul_routes):
                base_price *= 4.0
            elif departure != arrival:  # Not domestic
                base_price *= 1.5
            
            # Time-based adjustments
            departure_time = flight.get('scheduled_departure')
            if departure_time:
                hour = departure_time.hour
                if 6 <= hour <= 9 or 17 <= hour <= 20:  # Peak times
                    base_price *= 1.2
                elif hour < 6 or hour > 22:  # Off-peak times
                    base_price *= 0.8
            
            return round(base_price, 2)
            
        except Exception as e:
            logger.error("Failed to estimate flight price", error=str(e))
            return 200.0  # Default price
    
    async def _check_class_availability(self, flight: Dict[str, Any], seat_class: str) -> bool:
        """Check if requested seat class is available (mock implementation)"""
        try:
            # Mock availability check
            available_seats = flight.get('available_seats', 0)
            
            if available_seats <= 0:
                return False
            
            # Assume class availability based on aircraft type and seat count
            if seat_class in ['business', 'first']:
                # Business/First typically limited on smaller aircraft
                aircraft_type = flight.get('aircraft_type', '').lower()
                if any(ac_type in aircraft_type for ac_type in ['737', 'a320', 'regional']):
                    return available_seats > 10  # Need more seats available for premium classes
                else:
                    return available_seats > 5
            else:
                return available_seats > 0
                
        except Exception as e:
            logger.error("Failed to check class availability", error=str(e))
            return True  # Default to available
    
    def _generate_selection_reason(
        self,
        selected_alternative: Dict[str, Any],
        original_booking: Dict[str, Any],
        total_alternatives: int
    ) -> str:
        """Generate human-readable reason for alternative selection"""
        try:
            reasons = []
            
            # Score-based reason
            score = selected_alternative.get('suitability_score', 0)
            if score > 0.8:
                reasons.append("Excellent match for your preferences")
            elif score > 0.6:
                reasons.append("Good match for your requirements")
            else:
                reasons.append("Best available option")
            
            # Specific features
            if selected_alternative.get('is_direct', False):
                reasons.append("direct flight")
            
            cost_diff = selected_alternative.get('cost_difference', 0)
            if cost_diff <= 0:
                reasons.append("no additional cost")
            elif cost_diff < 50:
                reasons.append("minimal additional cost")
            
            time_diff = abs(selected_alternative.get('time_difference_hours', 0))
            if time_diff < 2:
                reasons.append("similar departure time")
            elif time_diff < 4:
                reasons.append("reasonable time difference")
            
            # Combine reasons
            reason = f"Selected from {total_alternatives} alternatives: {', '.join(reasons[:3])}"
            return reason
            
        except Exception as e:
            logger.error("Failed to generate selection reason", error=str(e))
            return f"Selected from {total_alternatives} available alternatives"