import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass
import redis.asyncio as redis
import httpx
from database import Database
from config import settings

logger = structlog.get_logger()

@dataclass
class OptimizationWeights:
    cost: float = 0.4
    satisfaction: float = 0.35
    time: float = 0.25

class OptimizationEngine:
    """Advanced cost optimization engine using multi-criteria optimization"""
    
    def __init__(self, db: Database, redis_client: redis.Redis, http_client: httpx.AsyncClient):
        self.db = db
        self.redis = redis_client
        self.http_client = http_client
        self.weights = OptimizationWeights()
    
    async def optimize_disruption_costs(
        self,
        disruption_context: Dict[str, Any],
        passenger_profiles: List[Dict[str, Any]], 
        budget_constraints: Dict[str, float],
        optimization_priorities: List[str]
    ) -> Dict[str, Any]:
        """Run comprehensive cost optimization for disruption"""
        
        try:
            logger.info(
                "Starting cost optimization",
                disruption_id=disruption_context.get('disruption_id'),
                passenger_count=len(passenger_profiles)
            )
            
            # Update weights based on priorities
            self._update_optimization_weights(optimization_priorities)
            
            # Initialize optimization result
            optimization_result = {
                'optimization_id': f"opt_{disruption_context.get('disruption_id')}_{int(datetime.utcnow().timestamp())}",
                'disruption_id': disruption_context.get('disruption_id'),
                'total_cost': 0.0,
                'cost_breakdown': {},
                'passenger_allocations': [],
                'vendor_bookings': [],
                'compensation_calculations': [],
                'estimated_savings': 0.0,
                'confidence_score': 0.8,
                'recommendations': []
            }
            
            # Process each passenger
            for passenger in passenger_profiles:
                passenger_allocation = await self._optimize_passenger_allocation(
                    passenger,
                    disruption_context,
                    budget_constraints
                )
                
                optimization_result['passenger_allocations'].append(passenger_allocation)
                optimization_result['total_cost'] += passenger_allocation.get('total_cost', 0)
            
            # Optimize vendor selections
            vendor_optimizations = await self._optimize_vendor_selections(
                optimization_result['passenger_allocations'],
                disruption_context
            )
            
            optimization_result['vendor_bookings'] = vendor_optimizations['bookings']
            optimization_result['total_cost'] = vendor_optimizations['optimized_cost']
            optimization_result['estimated_savings'] = vendor_optimizations['savings']
            
            # Calculate cost breakdown
            optimization_result['cost_breakdown'] = self._calculate_cost_breakdown(
                optimization_result['passenger_allocations']
            )
            
            # Generate recommendations
            optimization_result['recommendations'] = self._generate_recommendations(
                optimization_result,
                disruption_context
            )
            
            # Calculate confidence score
            optimization_result['confidence_score'] = self._calculate_confidence_score(
                optimization_result,
                disruption_context
            )
            
            logger.info(
                "Cost optimization completed",
                optimization_id=optimization_result['optimization_id'],
                total_cost=optimization_result['total_cost'],
                estimated_savings=optimization_result['estimated_savings']
            )
            
            return optimization_result
            
        except Exception as e:
            logger.error("Cost optimization failed", error=str(e))
            raise
    
    async def _optimize_passenger_allocation(
        self,
        passenger: Dict[str, Any],
        disruption_context: Dict[str, Any],
        budget_constraints: Dict[str, float]
    ) -> Dict[str, Any]:
        """Optimize allocation for individual passenger"""
        
        allocation = {
            'passenger_id': passenger['passenger_id'],
            'loyalty_tier': passenger.get('loyalty_tier'),
            'hotel_allocation': None,
            'transport_allocation': None,
            'meal_allocation': None,
            'compensation_allocation': None,
            'total_cost': 0.0
        }
        
        delay_hours = disruption_context.get('estimated_delay_hours', 4)
        
        # Hotel allocation (if overnight delay)
        if delay_hours >= 8 or self._requires_overnight_stay(disruption_context):
            hotel_options = await self._get_hotel_options(passenger, disruption_context)
            best_hotel = self._select_best_hotel(hotel_options, passenger, budget_constraints)
            
            if best_hotel:
                allocation['hotel_allocation'] = best_hotel
                allocation['total_cost'] += best_hotel['cost']
        
        # Transport allocation
        transport_options = await self._get_transport_options(passenger, disruption_context)
        best_transport = self._select_best_transport(transport_options, passenger, budget_constraints)
        
        if best_transport:
            allocation['transport_allocation'] = best_transport
            allocation['total_cost'] += best_transport['cost']
        
        # Meal allocation
        meal_allocation = await self._calculate_meal_allocation(passenger, delay_hours)
        allocation['meal_allocation'] = meal_allocation
        allocation['total_cost'] += meal_allocation['cost']
        
        # Compensation calculation
        compensation = await self._calculate_passenger_compensation(passenger, disruption_context)
        allocation['compensation_allocation'] = compensation
        allocation['total_cost'] += compensation['total_amount']
        
        return allocation
    
    async def _get_hotel_options(self, passenger: Dict[str, Any], disruption_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get hotel options for passenger"""
        
        # Mock hotel options with different price/quality tiers
        base_options = [
            {
                'hotel_id': 'budget_hotel_001',
                'name': 'Budget Inn Airport',
                'rating': 2.5,
                'price_per_night': 80,
                'distance_from_airport': 2,
                'amenities': ['wifi', 'breakfast'],
                'accessibility': False
            },
            {
                'hotel_id': 'mid_range_hotel_001',
                'name': 'Airport Express Hotel',
                'rating': 3.5,
                'price_per_night': 120,
                'distance_from_airport': 1,
                'amenities': ['wifi', 'breakfast', 'shuttle', 'gym'],
                'accessibility': True
            },
            {
                'hotel_id': 'premium_hotel_001',
                'name': 'Premium Airport Suites',
                'rating': 4.5,
                'price_per_night': 200,
                'distance_from_airport': 0.5,
                'amenities': ['wifi', 'breakfast', 'shuttle', 'gym', 'spa', 'lounge'],
                'accessibility': True
            }
        ]
        
        # Filter based on passenger needs
        filtered_options = []
        for option in base_options:
            if passenger.get('mobility_assistance') and not option.get('accessibility'):
                continue
            
            # Adjust pricing based on loyalty tier
            adjusted_option = option.copy()
            loyalty_tier = passenger.get('loyalty_tier', 'standard')
            
            if loyalty_tier == 'gold':
                adjusted_option['price_per_night'] *= 0.9  # 10% discount
            elif loyalty_tier == 'platinum':
                adjusted_option['price_per_night'] *= 0.8  # 20% discount
            
            filtered_options.append(adjusted_option)
        
        return filtered_options
    
    async def _get_transport_options(self, passenger: Dict[str, Any], disruption_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get transport options for passenger"""
        
        base_options = [
            {
                'transport_id': 'bus_001',
                'type': 'bus',
                'provider': 'Airport Express Bus',
                'cost': 15,
                'duration_minutes': 45,
                'comfort_level': 2,
                'accessibility': True
            },
            {
                'transport_id': 'taxi_001',
                'type': 'taxi',
                'provider': 'Airport Taxi Service',
                'cost': 35,
                'duration_minutes': 25,
                'comfort_level': 3,
                'accessibility': True
            },
            {
                'transport_id': 'ride_share_001',
                'type': 'ride_share',
                'provider': 'Uber/Lyft',
                'cost': 25,
                'duration_minutes': 30,
                'comfort_level': 3,
                'accessibility': False
            },
            {
                'transport_id': 'premium_car_001',
                'type': 'premium_car',
                'provider': 'Executive Car Service',
                'cost': 80,
                'duration_minutes': 20,
                'comfort_level': 5,
                'accessibility': True
            }
        ]
        
        # Filter based on passenger needs and preferences
        filtered_options = []
        for option in base_options:
            if passenger.get('mobility_assistance') and not option.get('accessibility'):
                continue
            
            # Upgrade based on loyalty tier
            loyalty_tier = passenger.get('loyalty_tier', 'standard')
            adjusted_option = option.copy()
            
            if loyalty_tier in ['gold', 'platinum']:
                # Prioritize higher comfort options
                adjusted_option['priority_boost'] = option['comfort_level'] * 0.2
            
            filtered_options.append(adjusted_option)
        
        return filtered_options
    
    def _select_best_hotel(self, options: List[Dict[str, Any]], passenger: Dict[str, Any], budget_constraints: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Select best hotel option using multi-criteria optimization"""
        
        if not options:
            return None
        
        max_budget = budget_constraints.get('hotel_max', settings.max_hotel_price_per_night)
        
        best_option = None
        best_score = -1
        
        for option in options:
            if option['price_per_night'] > max_budget:
                continue
            
            # Calculate optimization score
            cost_score = 1 - (option['price_per_night'] / max_budget)  # Lower cost = higher score
            quality_score = option['rating'] / 5.0  # Hotel rating normalized
            convenience_score = 1 - (option['distance_from_airport'] / 10)  # Closer = better
            
            # Weighted score
            total_score = (
                self.weights.cost * cost_score +
                self.weights.satisfaction * quality_score +
                self.weights.time * convenience_score
            )
            
            if total_score > best_score:
                best_score = total_score
                best_option = {
                    'hotel_data': option,
                    'cost': option['price_per_night'],
                    'selection_score': total_score
                }
        
        return best_option
    
    def _select_best_transport(self, options: List[Dict[str, Any]], passenger: Dict[str, Any], budget_constraints: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Select best transport option using multi-criteria optimization"""
        
        if not options:
            return None
        
        max_budget = budget_constraints.get('transport_max', settings.max_transport_cost)
        
        best_option = None
        best_score = -1
        
        for option in options:
            if option['cost'] > max_budget:
                continue
            
            # Calculate optimization score
            cost_score = 1 - (option['cost'] / max_budget)
            comfort_score = option['comfort_level'] / 5.0
            time_score = 1 - (option['duration_minutes'] / 60)  # Faster = better
            
            # Apply loyalty boost if present
            priority_boost = option.get('priority_boost', 0)
            
            # Weighted score
            total_score = (
                self.weights.cost * cost_score +
                self.weights.satisfaction * (comfort_score + priority_boost) +
                self.weights.time * time_score
            )
            
            if total_score > best_score:
                best_score = total_score
                best_option = {
                    'transport_data': option,
                    'cost': option['cost'],
                    'selection_score': total_score
                }
        
        return best_option
    
    async def _calculate_meal_allocation(self, passenger: Dict[str, Any], delay_hours: int) -> Dict[str, Any]:
        """Calculate meal voucher allocation"""
        
        base_rate = settings.meal_voucher_rate_per_hour
        
        # Adjust based on delay duration
        if delay_hours < 2:
            meal_cost = 0
            vouchers = []
        elif delay_hours < 4:
            meal_cost = base_rate
            vouchers = [{'type': 'snack', 'value': base_rate}]
        elif delay_hours < 8:
            meal_cost = base_rate * 2
            vouchers = [
                {'type': 'meal', 'value': base_rate * 1.5},
                {'type': 'snack', 'value': base_rate * 0.5}
            ]
        else:
            meal_cost = base_rate * 3
            vouchers = [
                {'type': 'dinner', 'value': base_rate * 1.5},
                {'type': 'breakfast', 'value': base_rate},
                {'type': 'snacks', 'value': base_rate * 0.5}
            ]
        
        # Adjust for dietary requirements
        dietary_requirements = passenger.get('dietary_requirements')
        if dietary_requirements:
            meal_cost *= 1.2  # 20% premium for special dietary needs
        
        # Adjust for loyalty tier
        loyalty_tier = passenger.get('loyalty_tier', 'standard')
        if loyalty_tier == 'gold':
            meal_cost *= 1.1
        elif loyalty_tier == 'platinum':
            meal_cost *= 1.2
        
        return {
            'cost': meal_cost,
            'vouchers': vouchers,
            'dietary_adjustments': dietary_requirements is not None
        }
    
    async def _calculate_passenger_compensation(self, passenger: Dict[str, Any], disruption_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total passenger compensation"""
        
        delay_hours = disruption_context.get('estimated_delay_hours', 4)
        disruption_type = disruption_context.get('disruption_type', 'weather')
        
        # Mock flight details for calculation
        flight_distance = 2500  # km - mock medium haul
        
        # Calculate EU261 compensation
        eu261_amount = await self.calculate_eu261_compensation(
            delay_hours=delay_hours,
            flight_distance_km=flight_distance,
            disruption_type=disruption_type
        )
        
        # Calculate additional airline compensation
        additional_amount = await self.calculate_additional_compensation(
            ticket_price=300,  # Mock ticket price
            passenger_class='economy',
            delay_hours=delay_hours,
            disruption_type=disruption_type
        )
        
        # Loyalty tier adjustments
        loyalty_multiplier = 1.0
        loyalty_tier = passenger.get('loyalty_tier', 'standard')
        if loyalty_tier == 'gold':
            loyalty_multiplier = 1.1
        elif loyalty_tier == 'platinum':
            loyalty_multiplier = 1.25
        
        total_amount = (eu261_amount + additional_amount) * loyalty_multiplier
        
        return {
            'eu261_amount': eu261_amount,
            'additional_amount': additional_amount,
            'loyalty_adjustment': loyalty_multiplier - 1.0,
            'total_amount': total_amount
        }
    
    async def calculate_eu261_compensation(self, delay_hours: int, flight_distance_km: int, disruption_type: str) -> float:
        """Calculate EU261 compensation based on delay and distance"""
        
        # No compensation for delays under 3 hours or certain circumstances
        if delay_hours < 3:
            return 0.0
        
        # No compensation for extraordinary circumstances (weather, strikes, etc.)
        extraordinary_circumstances = ['weather', 'atc', 'security', 'strike']
        if disruption_type in extraordinary_circumstances:
            return 0.0
        
        # EU261 compensation tiers
        if flight_distance_km <= 1500:
            return settings.eu261_short_haul
        elif flight_distance_km <= 3500:
            return settings.eu261_medium_haul
        else:
            return settings.eu261_long_haul
    
    async def calculate_additional_compensation(self, ticket_price: float, passenger_class: str, delay_hours: int, disruption_type: str) -> float:
        """Calculate additional airline compensation beyond EU261"""
        
        base_compensation = 0.0
        
        # Additional compensation based on delay severity
        if delay_hours >= 6:
            base_compensation = ticket_price * 0.1  # 10% of ticket price
        elif delay_hours >= 4:
            base_compensation = ticket_price * 0.05  # 5% of ticket price
        
        # Class-based adjustments
        class_multipliers = {
            'economy': 1.0,
            'premium_economy': 1.2,
            'business': 1.5,
            'first': 2.0
        }
        
        base_compensation *= class_multipliers.get(passenger_class, 1.0)
        
        return base_compensation
    
    async def calculate_meal_vouchers(self, delay_hours: int, passenger_class: str) -> Dict[str, Any]:
        """Calculate meal voucher entitlements"""
        
        base_value = settings.meal_voucher_rate_per_hour
        
        # Calculate total voucher value based on delay
        if delay_hours < 2:
            total_value = 0
            voucher_count = 0
        elif delay_hours < 4:
            total_value = base_value
            voucher_count = 1
        elif delay_hours < 8:
            total_value = base_value * 2
            voucher_count = 2
        else:
            total_value = base_value * 3
            voucher_count = 3
        
        # Class-based adjustments
        class_multipliers = {
            'economy': 1.0,
            'premium_economy': 1.2,
            'business': 1.5,
            'first': 2.0
        }
        
        total_value *= class_multipliers.get(passenger_class, 1.0)
        
        return {
            'total_value': total_value,
            'voucher_count': voucher_count,
            'per_voucher_value': total_value / max(voucher_count, 1)
        }
    
    async def _optimize_vendor_selections(self, passenger_allocations: List[Dict[str, Any]], disruption_context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize vendor selections for bulk bookings"""
        
        # Group bookings by vendor type for bulk discounts
        hotel_bookings = []
        transport_bookings = []
        
        for allocation in passenger_allocations:
            if allocation.get('hotel_allocation'):
                hotel_bookings.append(allocation['hotel_allocation'])
            
            if allocation.get('transport_allocation'):
                transport_bookings.append(allocation['transport_allocation'])
        
        # Calculate bulk pricing
        optimized_cost = 0.0
        bulk_savings = 0.0
        
        # Hotel bulk discount
        if len(hotel_bookings) >= 10:
            hotel_discount = 0.15  # 15% bulk discount
        elif len(hotel_bookings) >= 5:
            hotel_discount = 0.10  # 10% bulk discount
        else:
            hotel_discount = 0.0
        
        for booking in hotel_bookings:
            original_cost = booking['cost']
            discounted_cost = original_cost * (1 - hotel_discount)
            optimized_cost += discounted_cost
            bulk_savings += original_cost - discounted_cost
        
        # Transport bulk discount
        if len(transport_bookings) >= 20:
            transport_discount = 0.20  # 20% bulk discount
        elif len(transport_bookings) >= 10:
            transport_discount = 0.15  # 15% bulk discount
        else:
            transport_discount = 0.0
        
        for booking in transport_bookings:
            original_cost = booking['cost']
            discounted_cost = original_cost * (1 - transport_discount)
            optimized_cost += discounted_cost
            bulk_savings += original_cost - discounted_cost
        
        # Add other costs (meals, compensation) without bulk discounts
        for allocation in passenger_allocations:
            if allocation.get('meal_allocation'):
                optimized_cost += allocation['meal_allocation']['cost']
            if allocation.get('compensation_allocation'):
                optimized_cost += allocation['compensation_allocation']['total_amount']
        
        return {
            'optimized_cost': optimized_cost,
            'savings': bulk_savings,
            'bookings': hotel_bookings + transport_bookings,
            'bulk_discounts': {
                'hotel_discount': hotel_discount,
                'transport_discount': transport_discount
            }
        }
    
    def _calculate_cost_breakdown(self, passenger_allocations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate detailed cost breakdown"""
        
        breakdown = {
            'hotels': 0.0,
            'transport': 0.0,
            'meals': 0.0,
            'compensation': 0.0,
            'total': 0.0
        }
        
        for allocation in passenger_allocations:
            if allocation.get('hotel_allocation'):
                breakdown['hotels'] += allocation['hotel_allocation']['cost']
            
            if allocation.get('transport_allocation'):
                breakdown['transport'] += allocation['transport_allocation']['cost']
            
            if allocation.get('meal_allocation'):
                breakdown['meals'] += allocation['meal_allocation']['cost']
            
            if allocation.get('compensation_allocation'):
                breakdown['compensation'] += allocation['compensation_allocation']['total_amount']
        
        breakdown['total'] = sum(breakdown.values())
        
        return breakdown
    
    def _generate_recommendations(self, optimization_result: Dict[str, Any], disruption_context: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        total_cost = optimization_result.get('total_cost', 0)
        passenger_count = len(optimization_result.get('passenger_allocations', []))
        
        # Cost per passenger analysis
        if passenger_count > 0:
            cost_per_passenger = total_cost / passenger_count
            
            if cost_per_passenger > 500:
                recommendations.append("Consider negotiating group rates with preferred vendors to reduce per-passenger costs")
            
            if cost_per_passenger < 200:
                recommendations.append("Excellent cost optimization achieved - consider this as a benchmark for future disruptions")
        
        # Vendor selection recommendations
        cost_breakdown = optimization_result.get('cost_breakdown', {})
        
        if cost_breakdown.get('hotels', 0) > cost_breakdown.get('transport', 0) * 2:
            recommendations.append("Hotel costs are significantly higher than transport - consider alternative accommodation strategies")
        
        # Seasonal recommendations
        current_month = datetime.now().month
        if current_month in [11, 12, 1, 2]:  # Winter months
            recommendations.append("Winter period - ensure enhanced comfort options for passengers due to weather conditions")
        
        return recommendations
    
    def _calculate_confidence_score(self, optimization_result: Dict[str, Any], disruption_context: Dict[str, Any]) -> float:
        """Calculate confidence score for the optimization"""
        
        confidence = 0.8  # Base confidence
        
        # Adjust based on passenger count (more passengers = better bulk optimization)
        passenger_count = len(optimization_result.get('passenger_allocations', []))
        if passenger_count >= 20:
            confidence += 0.1
        elif passenger_count < 5:
            confidence -= 0.1
        
        # Adjust based on disruption type (some types have more predictable costs)
        disruption_type = disruption_context.get('disruption_type', 'unknown')
        if disruption_type in ['technical', 'crew']:
            confidence += 0.05  # More predictable
        elif disruption_type in ['weather', 'atc']:
            confidence -= 0.05  # Less predictable
        
        # Adjust based on estimated savings
        estimated_savings = optimization_result.get('estimated_savings', 0)
        if estimated_savings > 1000:
            confidence += 0.05
        
        return min(max(confidence, 0.1), 0.95)  # Clamp between 0.1 and 0.95
    
    def _update_optimization_weights(self, priorities: List[str]):
        """Update optimization weights based on priorities"""
        
        if 'cost' in priorities[:2]:  # Cost is top 2 priority
            self.weights.cost = 0.5
            self.weights.satisfaction = 0.3
            self.weights.time = 0.2
        elif 'passenger_satisfaction' in priorities[:2]:  # Satisfaction is top 2 priority
            self.weights.cost = 0.3
            self.weights.satisfaction = 0.5
            self.weights.time = 0.2
        elif 'time' in priorities[:2]:  # Time is top 2 priority
            self.weights.cost = 0.3
            self.weights.satisfaction = 0.2
            self.weights.time = 0.5
    
    def _requires_overnight_stay(self, disruption_context: Dict[str, Any]) -> bool:
        """Determine if disruption requires overnight accommodation"""
        
        delay_hours = disruption_context.get('estimated_delay_hours', 0)
        original_departure = disruption_context.get('original_departure')
        
        if delay_hours >= 8:
            return True
        
        # Check if delay pushes departure to overnight hours
        if original_departure:
            if isinstance(original_departure, str):
                original_departure = datetime.fromisoformat(original_departure.replace('Z', '+00:00'))
            
            new_departure_hour = (original_departure + timedelta(hours=delay_hours)).hour
            if 22 <= new_departure_hour or new_departure_hour <= 6:  # Late night or early morning
                return True
        
        return False
    
    async def calculate_rebooking_costs(self, passenger_id: str, rebooking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs associated with rebooking"""
        
        # Mock calculation for rebooking costs
        fare_difference = rebooking_data.get('fare_difference', 0.0)
        change_fees = rebooking_data.get('change_fees', 50.0)  # Standard change fee
        
        # Additional costs based on rebooking complexity
        if rebooking_data.get('requires_hotel'):
            hotel_costs = 120.0  # One night hotel
        else:
            hotel_costs = 0.0
        
        if rebooking_data.get('requires_transport'):
            transport_costs = 35.0  # Airport transport
        else:
            transport_costs = 0.0
        
        meal_costs = rebooking_data.get('delay_hours', 2) * 15.0  # Meal vouchers
        
        total_cost = fare_difference + change_fees + hotel_costs + transport_costs + meal_costs
        
        return {
            'fare_difference': fare_difference,
            'change_fees': change_fees,
            'hotel_costs': hotel_costs,
            'transport_costs': transport_costs,
            'meal_costs': meal_costs,
            'total_cost': total_cost
        }