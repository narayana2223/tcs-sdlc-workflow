"""
Cost Optimization Engine
Advanced algorithms for optimizing costs across hotels, transport, and compensation
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import math
from dataclasses import dataclass
import itertools

from ..models.comprehensive_models import (
    Flight, PassengerProfile, Booking, Disruption, DisruptionType,
    ResourceType, ResourceAllocation, CostOptimizationModel
)


class OptimizationObjective(str, Enum):
    """Optimization objectives"""
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_SATISFACTION = "maximize_satisfaction"
    BALANCED = "balanced"
    MINIMIZE_TIME = "minimize_time"
    MAXIMIZE_LOYALTY_IMPACT = "maximize_loyalty_impact"


class ResourceQuality(str, Enum):
    """Quality levels for resources"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"


@dataclass
class HotelOption:
    """Hotel accommodation option"""
    hotel_id: str
    name: str
    category: str  # 1-5 star rating
    distance_from_airport_km: float
    shuttle_available: bool
    cost_per_night: Decimal
    availability: int
    amenities: List[str]
    accessibility_features: List[str]
    customer_rating: float
    cancellation_policy: str
    loyalty_program: Optional[str] = None


@dataclass
class TransportOption:
    """Transport option"""
    transport_id: str
    type: str  # taxi, bus, train, car_rental
    cost: Decimal
    duration_minutes: int
    capacity: int
    comfort_level: ResourceQuality
    availability: bool
    pickup_location: str
    dropoff_location: str
    special_requirements: List[str]


@dataclass
class MealOption:
    """Meal voucher option"""
    vendor_id: str
    name: str
    cost: Decimal
    meal_type: str  # breakfast, lunch, dinner, snack
    dietary_options: List[str]
    location: str
    operating_hours: str


class CostOptimizationEngine:
    """
    Advanced cost optimization engine for disruption management resources
    """
    
    def __init__(self):
        """Initialize the cost optimization engine"""
        self.hotel_options: List[HotelOption] = []
        self.transport_options: List[TransportOption] = []
        self.meal_options: List[MealOption] = []
        self.optimization_history: List[CostOptimizationModel] = []
        
        # Cost and quality weights for different objectives
        self.objective_weights = {
            OptimizationObjective.MINIMIZE_COST: {
                'cost': 0.8, 'quality': 0.1, 'satisfaction': 0.05, 'loyalty': 0.05
            },
            OptimizationObjective.MAXIMIZE_SATISFACTION: {
                'cost': 0.2, 'quality': 0.4, 'satisfaction': 0.3, 'loyalty': 0.1
            },
            OptimizationObjective.BALANCED: {
                'cost': 0.4, 'quality': 0.25, 'satisfaction': 0.25, 'loyalty': 0.1
            },
            OptimizationObjective.MINIMIZE_TIME: {
                'cost': 0.3, 'quality': 0.2, 'satisfaction': 0.2, 'loyalty': 0.05, 'time': 0.25
            },
            OptimizationObjective.MAXIMIZE_LOYALTY_IMPACT: {
                'cost': 0.25, 'quality': 0.25, 'satisfaction': 0.2, 'loyalty': 0.3
            }
        }
    
    def optimize_disruption_costs(
        self,
        disruption: Disruption,
        affected_passengers: List[Tuple[PassengerProfile, Booking]],
        budget_constraints: Optional[Dict[str, Decimal]] = None,
        optimization_objective: OptimizationObjective = OptimizationObjective.BALANCED,
        context: Optional[Dict] = None
    ) -> CostOptimizationModel:
        """
        Optimize costs for all affected passengers in a disruption
        
        Args:
            disruption: Disruption details
            affected_passengers: List of (passenger, booking) tuples
            budget_constraints: Maximum budgets for different categories
            optimization_objective: Primary optimization objective
            context: Additional context for optimization
            
        Returns:
            Complete cost optimization model with recommendations
        """
        context = context or {}
        budget_constraints = budget_constraints or {}
        
        start_time = datetime.now()
        
        # Initialize optimization model
        optimization_model = CostOptimizationModel(
            optimization_scenario=f"disruption_{disruption.id}",
            disruption_id=disruption.id,
            passenger_count=len(affected_passengers),
            budget_constraint=budget_constraints.get('total', Decimal('50000')),
            time_constraint_hours=context.get('time_constraint_hours', 24),
            quality_target=context.get('quality_target', 0.8)
        )
        
        # Analyze passenger requirements
        passenger_requirements = self._analyze_passenger_requirements(
            affected_passengers, disruption, context
        )
        
        # Generate resource options
        hotel_allocations = self._optimize_hotel_allocations(
            passenger_requirements, budget_constraints.get('hotels', Decimal('30000')),
            optimization_objective
        )
        
        transport_allocations = self._optimize_transport_allocations(
            passenger_requirements, hotel_allocations,
            budget_constraints.get('transport', Decimal('10000')),
            optimization_objective
        )
        
        meal_allocations = self._optimize_meal_allocations(
            passenger_requirements, budget_constraints.get('meals', Decimal('5000')),
            optimization_objective
        )
        
        communication_allocations = self._optimize_communication_resources(
            passenger_requirements, budget_constraints.get('communication', Decimal('2000'))
        )
        
        # Combine all allocations
        optimization_model.hotel_costs = hotel_allocations
        optimization_model.transport_costs = transport_allocations
        optimization_model.meal_costs = meal_allocations
        
        # Calculate total costs and quality scores
        total_cost, quality_score = self._calculate_total_metrics(
            hotel_allocations, transport_allocations, meal_allocations, communication_allocations
        )
        
        optimization_model.total_optimized_cost = total_cost
        optimization_model.quality_score = quality_score
        
        # Calculate savings (compared to default/premium options)
        baseline_cost = self._calculate_baseline_cost(passenger_requirements)
        optimization_model.cost_savings = baseline_cost - total_cost
        
        # Build recommended allocation
        optimization_model.recommended_allocation = self._build_recommended_allocation(
            hotel_allocations, transport_allocations, meal_allocations, communication_allocations
        )
        
        # Set algorithm metadata
        optimization_time = (datetime.now() - start_time).total_seconds()
        optimization_model.optimization_time_seconds = optimization_time
        optimization_model.solution_confidence = self._calculate_solution_confidence(
            optimization_model, passenger_requirements
        )
        
        # Store optimization history
        self.optimization_history.append(optimization_model)
        
        return optimization_model
    
    def _analyze_passenger_requirements(
        self,
        affected_passengers: List[Tuple[PassengerProfile, Booking]],
        disruption: Disruption,
        context: Dict
    ) -> List[Dict[str, Any]]:
        """
        Analyze individual passenger requirements and constraints
        """
        requirements = []
        
        for passenger, booking in affected_passengers:
            req = {
                'passenger_id': passenger.id,
                'booking_id': booking.id,
                'loyalty_tier': passenger.loyalty_tier,
                'seat_class': booking.seat_class,
                'total_paid': booking.total_price,
                
                # Accommodation needs
                'needs_hotel': self._requires_overnight_accommodation(disruption, passenger),
                'room_type': self._determine_room_type(passenger, booking),
                'accessibility_required': passenger.mobility_assistance,
                'dietary_restrictions': passenger.dietary_requirements,
                
                # Transport needs
                'needs_transport': True,  # All passengers need airport transport
                'transport_accessibility': passenger.mobility_assistance,
                'group_size': context.get(f'group_size_{passenger.id}', 1),
                
                # Service level expectations
                'expected_service_level': self._determine_service_level(passenger, booking),
                'priority_score': passenger.priority_score,
                
                # Budget constraints
                'cost_sensitivity': self._assess_cost_sensitivity(passenger, booking),
                'loyalty_program_hotels': self._get_loyalty_hotel_chains(passenger),
                
                # Special requirements
                'special_needs': passenger.special_assistance,
                'medical_conditions': passenger.medical_conditions,
                'communication_preferences': passenger.communication_preferences
            }
            
            requirements.append(req)
        
        return requirements
    
    def _optimize_hotel_allocations(
        self,
        passenger_requirements: List[Dict[str, Any]],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """
        Optimize hotel allocations using constraint satisfaction
        """
        allocations = []
        remaining_budget = budget
        
        # Group passengers by requirements to optimize room sharing
        grouped_passengers = self._group_passengers_for_hotels(passenger_requirements)
        
        for group in grouped_passengers:
            if remaining_budget <= 0:
                break
            
            # Find best hotel option for this group
            best_option = self._find_optimal_hotel_for_group(
                group, remaining_budget, objective
            )
            
            if best_option:
                allocations.append(best_option)
                remaining_budget -= best_option['total_cost']
        
        return allocations
    
    def _optimize_transport_allocations(
        self,
        passenger_requirements: List[Dict[str, Any]],
        hotel_allocations: List[Dict[str, Any]],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """
        Optimize transport allocations considering hotel locations
        """
        allocations = []
        remaining_budget = budget
        
        # Create transport requirements based on hotel allocations
        transport_groups = self._group_passengers_for_transport(
            passenger_requirements, hotel_allocations
        )
        
        for group in transport_groups:
            if remaining_budget <= 0:
                break
            
            # Optimize transport for this group/route
            best_transport = self._find_optimal_transport_for_group(
                group, remaining_budget, objective
            )
            
            if best_transport:
                allocations.append(best_transport)
                remaining_budget -= best_transport['total_cost']
        
        return allocations
    
    def _optimize_meal_allocations(
        self,
        passenger_requirements: List[Dict[str, Any]],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """
        Optimize meal voucher allocations
        """
        allocations = []
        remaining_budget = budget
        
        for req in passenger_requirements:
            if remaining_budget <= 0:
                break
            
            # Determine meal requirements based on delay duration and time of day
            meal_needs = self._determine_meal_requirements(req)
            
            for meal_need in meal_needs:
                best_meal_option = self._find_optimal_meal_option(
                    req, meal_need, remaining_budget, objective
                )
                
                if best_meal_option:
                    allocations.append(best_meal_option)
                    remaining_budget -= best_meal_option['cost']
        
        return allocations
    
    def _optimize_communication_resources(
        self,
        passenger_requirements: List[Dict[str, Any]],
        budget: Decimal
    ) -> List[Dict[str, Any]]:
        """
        Optimize communication resource allocation (phone, wifi, etc.)
        """
        allocations = []
        cost_per_passenger = Decimal('10.0')  # Standard communication allowance
        
        for req in passenger_requirements:
            if budget >= cost_per_passenger:
                allocations.append({
                    'passenger_id': req['passenger_id'],
                    'type': 'communication_voucher',
                    'cost': cost_per_passenger,
                    'includes': ['phone_calls', 'internet_access', 'messaging'],
                    'duration_hours': 24
                })
                budget -= cost_per_passenger
        
        return allocations
    
    def _group_passengers_for_hotels(
        self, 
        passenger_requirements: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group passengers for optimal room sharing
        """
        groups = []
        remaining = passenger_requirements.copy()
        
        while remaining:
            passenger = remaining.pop(0)
            group = [passenger]
            
            # Find compatible passengers for room sharing
            if passenger['room_type'] in ['double', 'twin']:
                compatible = []
                for other in remaining[:]:
                    if self._are_passengers_compatible_for_sharing(passenger, other):
                        compatible.append(other)
                        remaining.remove(other)
                        if len(group) + len(compatible) >= 2:  # Max 2 per room typically
                            break
                
                group.extend(compatible[:1])  # Add one compatible passenger
            
            groups.append(group)
        
        return groups
    
    def _group_passengers_for_transport(
        self,
        passenger_requirements: List[Dict[str, Any]],
        hotel_allocations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group passengers for shared transport based on destinations
        """
        # Create destination-based groups
        destination_groups = {}
        
        for req in passenger_requirements:
            # Find the hotel allocation for this passenger
            hotel_destination = "airport"  # Default if no hotel
            
            for allocation in hotel_allocations:
                if req['passenger_id'] in allocation.get('passenger_ids', []):
                    hotel_destination = allocation['hotel_name']
                    break
            
            if hotel_destination not in destination_groups:
                destination_groups[hotel_destination] = []
            
            destination_groups[hotel_destination].append(req)
        
        # Convert to transport groups with capacity constraints
        transport_groups = []
        for destination, passengers in destination_groups.items():
            # Group passengers into transport capacity units (e.g., 4 per taxi, 8 per minibus)
            for i in range(0, len(passengers), 4):  # 4 passengers per vehicle
                group_passengers = passengers[i:i+4]
                transport_groups.append({
                    'destination': destination,
                    'passengers': group_passengers,
                    'passenger_count': len(group_passengers),
                    'accessibility_required': any(p.get('accessibility_required', False) 
                                                for p in group_passengers),
                    'priority_level': max(p.get('priority_score', 50) for p in group_passengers)
                })
        
        return transport_groups
    
    def _find_optimal_hotel_for_group(
        self,
        group: List[Dict[str, Any]],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> Optional[Dict[str, Any]]:
        """
        Find optimal hotel option for a group of passengers
        """
        if not self.hotel_options:
            # Mock hotel options if none provided
            self.hotel_options = self._generate_mock_hotel_options()
        
        best_option = None
        best_score = -1
        
        for hotel in self.hotel_options:
            # Check basic constraints
            if not self._hotel_meets_group_requirements(hotel, group):
                continue
            
            # Calculate cost for this group
            nights_required = self._calculate_nights_required(group[0])  # Assuming same for group
            rooms_required = len(group)  # One room per passenger (can be optimized)
            total_cost = hotel.cost_per_night * nights_required * rooms_required
            
            if total_cost > budget:
                continue
            
            # Calculate optimization score
            score = self._score_hotel_option(hotel, group, total_cost, objective)
            
            if score > best_score:
                best_score = score
                best_option = {
                    'hotel_id': hotel.hotel_id,
                    'hotel_name': hotel.name,
                    'passenger_ids': [p['passenger_id'] for p in group],
                    'rooms_required': rooms_required,
                    'nights': nights_required,
                    'cost_per_night': hotel.cost_per_night,
                    'total_cost': total_cost,
                    'quality_score': score,
                    'amenities': hotel.amenities,
                    'shuttle_available': hotel.shuttle_available
                }
        
        return best_option
    
    def _find_optimal_transport_for_group(
        self,
        group: Dict[str, Any],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> Optional[Dict[str, Any]]:
        """
        Find optimal transport option for a passenger group
        """
        if not self.transport_options:
            self.transport_options = self._generate_mock_transport_options()
        
        best_option = None
        best_score = -1
        passenger_count = group['passenger_count']
        
        for transport in self.transport_options:
            # Check capacity and requirements
            if transport.capacity < passenger_count:
                continue
            
            if group.get('accessibility_required', False) and 'wheelchair_accessible' not in transport.special_requirements:
                continue
            
            if transport.cost > budget:
                continue
            
            # Calculate score
            score = self._score_transport_option(transport, group, objective)
            
            if score > best_score:
                best_score = score
                best_option = {
                    'transport_id': transport.transport_id,
                    'type': transport.type,
                    'passenger_ids': [p['passenger_id'] for p in group['passengers']],
                    'destination': group['destination'],
                    'total_cost': transport.cost,
                    'duration_minutes': transport.duration_minutes,
                    'quality_score': score,
                    'comfort_level': transport.comfort_level
                }
        
        return best_option
    
    def _find_optimal_meal_option(
        self,
        passenger_req: Dict[str, Any],
        meal_need: Dict[str, Any],
        budget: Decimal,
        objective: OptimizationObjective
    ) -> Optional[Dict[str, Any]]:
        """
        Find optimal meal option for passenger
        """
        if not self.meal_options:
            self.meal_options = self._generate_mock_meal_options()
        
        best_option = None
        best_score = -1
        
        for meal in self.meal_options:
            # Check meal type match
            if meal.meal_type != meal_need['meal_type']:
                continue
            
            # Check dietary requirements
            if passenger_req.get('dietary_restrictions'):
                if not any(diet in meal.dietary_options 
                          for diet in passenger_req['dietary_restrictions']):
                    continue
            
            if meal.cost > budget:
                continue
            
            # Calculate score
            score = self._score_meal_option(meal, passenger_req, objective)
            
            if score > best_score:
                best_score = score
                best_option = {
                    'vendor_id': meal.vendor_id,
                    'vendor_name': meal.name,
                    'passenger_id': passenger_req['passenger_id'],
                    'meal_type': meal.meal_type,
                    'cost': meal.cost,
                    'quality_score': score,
                    'dietary_options': meal.dietary_options
                }
        
        return best_option
    
    def _score_hotel_option(
        self,
        hotel: HotelOption,
        group: List[Dict[str, Any]],
        total_cost: Decimal,
        objective: OptimizationObjective
    ) -> float:
        """
        Score a hotel option based on optimization objective
        """
        weights = self.objective_weights[objective]
        
        # Cost score (lower cost = higher score)
        cost_score = max(0, 100 - float(total_cost / 100))  # Normalize
        
        # Quality score
        quality_score = (float(hotel.customer_rating) / 5.0) * 100
        if hotel.category.isdigit():
            quality_score += float(hotel.category) * 10
        
        # Convenience score
        convenience_score = 50  # Base score
        if hotel.shuttle_available:
            convenience_score += 30
        if hotel.distance_from_airport_km < 5:
            convenience_score += 20
        
        # Passenger satisfaction factors
        satisfaction_score = 60  # Base score
        
        # Check loyalty programs
        for passenger in group:
            loyalty_programs = passenger.get('loyalty_program_hotels', [])
            if hotel.loyalty_program in loyalty_programs:
                satisfaction_score += 25
                break
        
        # Accessibility
        accessibility_needed = any(p.get('accessibility_required', False) for p in group)
        if accessibility_needed and hotel.accessibility_features:
            satisfaction_score += 20
        elif accessibility_needed and not hotel.accessibility_features:
            satisfaction_score -= 30
        
        # Calculate weighted score
        total_score = (
            cost_score * weights.get('cost', 0.4) +
            quality_score * weights.get('quality', 0.25) +
            convenience_score * weights.get('satisfaction', 0.25) +
            satisfaction_score * weights.get('loyalty', 0.1)
        )
        
        return total_score
    
    def _score_transport_option(
        self,
        transport: TransportOption,
        group: Dict[str, Any],
        objective: OptimizationObjective
    ) -> float:
        """
        Score a transport option
        """
        weights = self.objective_weights[objective]
        
        # Cost score
        cost_per_passenger = float(transport.cost) / group['passenger_count']
        cost_score = max(0, 100 - cost_per_passenger)
        
        # Quality/comfort score
        comfort_scores = {
            ResourceQuality.BASIC: 25,
            ResourceQuality.STANDARD: 50,
            ResourceQuality.PREMIUM: 75,
            ResourceQuality.LUXURY: 100
        }
        quality_score = comfort_scores.get(transport.comfort_level, 50)
        
        # Time/convenience score
        time_score = max(0, 100 - transport.duration_minutes)
        
        # Capacity efficiency
        capacity_score = (group['passenger_count'] / transport.capacity) * 100
        
        total_score = (
            cost_score * weights.get('cost', 0.4) +
            quality_score * weights.get('quality', 0.3) +
            time_score * weights.get('time', 0.2) +
            capacity_score * weights.get('satisfaction', 0.1)
        )
        
        return total_score
    
    def _score_meal_option(
        self,
        meal: MealOption,
        passenger_req: Dict[str, Any],
        objective: OptimizationObjective
    ) -> float:
        """
        Score a meal option
        """
        weights = self.objective_weights[objective]
        
        # Cost score
        cost_score = max(0, 100 - float(meal.cost))
        
        # Quality/variety score
        quality_score = len(meal.dietary_options) * 10  # More options = better
        
        # Passenger preference match
        preference_score = 50  # Base score
        if passenger_req.get('dietary_restrictions'):
            matches = sum(1 for diet in passenger_req['dietary_restrictions']
                         if diet in meal.dietary_options)
            preference_score += matches * 25
        
        total_score = (
            cost_score * weights.get('cost', 0.5) +
            quality_score * weights.get('quality', 0.3) +
            preference_score * weights.get('satisfaction', 0.2)
        )
        
        return total_score
    
    # Helper methods for requirements analysis
    def _requires_overnight_accommodation(
        self, 
        disruption: Disruption, 
        passenger: PassengerProfile
    ) -> bool:
        """Check if passenger requires overnight accommodation"""
        # If delay is more than 8 hours or spans overnight
        return disruption.delay_minutes > 480  # 8 hours
    
    def _determine_room_type(
        self, 
        passenger: PassengerProfile, 
        booking: Booking
    ) -> str:
        """Determine appropriate room type"""
        if booking.seat_class in ['first', 'business']:
            return 'suite'
        elif passenger.loyalty_tier in ['platinum', 'diamond']:
            return 'premium'
        else:
            return 'standard'
    
    def _determine_service_level(
        self, 
        passenger: PassengerProfile, 
        booking: Booking
    ) -> ResourceQuality:
        """Determine expected service level"""
        if booking.seat_class == 'first':
            return ResourceQuality.LUXURY
        elif booking.seat_class == 'business' or passenger.loyalty_tier == 'diamond':
            return ResourceQuality.PREMIUM
        elif passenger.loyalty_tier in ['platinum', 'gold']:
            return ResourceQuality.STANDARD
        else:
            return ResourceQuality.BASIC
    
    def _assess_cost_sensitivity(
        self, 
        passenger: PassengerProfile, 
        booking: Booking
    ) -> float:
        """Assess passenger's cost sensitivity (0=very sensitive, 1=not sensitive)"""
        # Higher fare and loyalty = less cost sensitive
        if booking.seat_class in ['first', 'business']:
            return 0.2  # Low cost sensitivity
        elif passenger.loyalty_tier in ['platinum', 'diamond']:
            return 0.3
        elif float(booking.total_price) > 500:
            return 0.4
        else:
            return 0.8  # High cost sensitivity
    
    def _get_loyalty_hotel_chains(self, passenger: PassengerProfile) -> List[str]:
        """Get hotel chains where passenger has loyalty status"""
        # This would be enhanced with actual loyalty program data
        chains = []
        if passenger.loyalty_tier in ['gold', 'platinum', 'diamond']:
            chains = ['Marriott', 'Hilton', 'IHG', 'Hyatt']  # Mock data
        return chains
    
    def _are_passengers_compatible_for_sharing(
        self, 
        passenger1: Dict[str, Any], 
        passenger2: Dict[str, Any]
    ) -> bool:
        """Check if two passengers can share accommodation"""
        # Basic compatibility checks
        if passenger1.get('accessibility_required') != passenger2.get('accessibility_required'):
            return False
        
        # Gender considerations for unknown passengers
        # Service level compatibility
        level1 = passenger1.get('expected_service_level')
        level2 = passenger2.get('expected_service_level')
        
        return abs(ord(level1.value[0]) - ord(level2.value[0])) <= 1  # Adjacent service levels
    
    def _calculate_nights_required(self, passenger_req: Dict[str, Any]) -> int:
        """Calculate number of nights accommodation required"""
        return 1  # Simplified - would be based on actual disruption duration
    
    def _determine_meal_requirements(self, passenger_req: Dict[str, Any]) -> List[Dict[str, str]]:
        """Determine meal requirements for passenger"""
        # Simplified - would be based on time of day and delay duration
        return [
            {'meal_type': 'lunch', 'time': '12:00'},
            {'meal_type': 'dinner', 'time': '18:00'}
        ]
    
    def _calculate_total_metrics(
        self,
        hotel_allocations: List[Dict[str, Any]],
        transport_allocations: List[Dict[str, Any]],
        meal_allocations: List[Dict[str, Any]],
        communication_allocations: List[Dict[str, Any]]
    ) -> Tuple[Decimal, float]:
        """Calculate total cost and average quality score"""
        total_cost = Decimal(0)
        quality_scores = []
        
        for allocation in hotel_allocations:
            total_cost += allocation['total_cost']
            quality_scores.append(allocation['quality_score'])
        
        for allocation in transport_allocations:
            total_cost += allocation['total_cost']
            quality_scores.append(allocation['quality_score'])
        
        for allocation in meal_allocations:
            total_cost += allocation['cost']
            quality_scores.append(allocation['quality_score'])
        
        for allocation in communication_allocations:
            total_cost += allocation['cost']
            quality_scores.append(75.0)  # Standard quality for communication
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return total_cost, avg_quality
    
    def _calculate_baseline_cost(self, passenger_requirements: List[Dict[str, Any]]) -> Decimal:
        """Calculate baseline cost without optimization"""
        # This would calculate costs using premium/default options
        passenger_count = len(passenger_requirements)
        baseline = Decimal(passenger_count * 200)  # £200 per passenger baseline
        return baseline
    
    def _build_recommended_allocation(
        self,
        hotel_allocations: List[Dict[str, Any]],
        transport_allocations: List[Dict[str, Any]],
        meal_allocations: List[Dict[str, Any]],
        communication_allocations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build final recommended allocation"""
        return {
            'hotels': hotel_allocations,
            'transport': transport_allocations,
            'meals': meal_allocations,
            'communication': communication_allocations,
            'execution_order': self._determine_execution_order(
                hotel_allocations, transport_allocations
            )
        }
    
    def _determine_execution_order(
        self,
        hotel_allocations: List[Dict[str, Any]],
        transport_allocations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Determine optimal execution order for allocations"""
        return [
            {'step': 1, 'action': 'book_hotels', 'priority': 'high'},
            {'step': 2, 'action': 'arrange_transport_to_hotels', 'priority': 'high'},
            {'step': 3, 'action': 'distribute_meal_vouchers', 'priority': 'medium'},
            {'step': 4, 'action': 'provide_communication_access', 'priority': 'medium'}
        ]
    
    def _calculate_solution_confidence(
        self,
        optimization_model: CostOptimizationModel,
        passenger_requirements: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in the optimization solution"""
        confidence = 0.8  # Base confidence
        
        # Adjust based on budget utilization
        budget_utilization = float(optimization_model.total_optimized_cost / optimization_model.budget_constraint)
        if 0.7 <= budget_utilization <= 0.95:
            confidence += 0.1  # Good budget utilization
        
        # Adjust based on quality score
        if optimization_model.quality_score > 75:
            confidence += 0.1
        
        # Adjust based on passenger coverage
        # This would check if all passengers got allocations
        
        return min(1.0, confidence)
    
    def _hotel_meets_group_requirements(
        self, 
        hotel: HotelOption, 
        group: List[Dict[str, Any]]
    ) -> bool:
        """Check if hotel meets group requirements"""
        # Check availability
        if hotel.availability < len(group):
            return False
        
        # Check accessibility
        accessibility_needed = any(p.get('accessibility_required', False) for p in group)
        if accessibility_needed and not hotel.accessibility_features:
            return False
        
        return True
    
    # Mock data generators for testing
    def _generate_mock_hotel_options(self) -> List[HotelOption]:
        """Generate mock hotel options for testing"""
        return [
            HotelOption(
                hotel_id="hotel_001",
                name="Airport Premier Inn",
                category="3",
                distance_from_airport_km=2.0,
                shuttle_available=True,
                cost_per_night=Decimal('89.00'),
                availability=50,
                amenities=['wifi', 'breakfast', 'gym'],
                accessibility_features=['wheelchair_access', 'hearing_loop'],
                customer_rating=4.2,
                cancellation_policy="flexible"
            ),
            HotelOption(
                hotel_id="hotel_002", 
                name="Hilton Airport",
                category="4",
                distance_from_airport_km=1.5,
                shuttle_available=True,
                cost_per_night=Decimal('149.00'),
                availability=30,
                amenities=['wifi', 'breakfast', 'gym', 'spa', 'restaurant'],
                accessibility_features=['wheelchair_access', 'hearing_loop', 'braille'],
                customer_rating=4.5,
                cancellation_policy="standard",
                loyalty_program="Hilton"
            )
        ]
    
    def _generate_mock_transport_options(self) -> List[TransportOption]:
        """Generate mock transport options for testing"""
        return [
            TransportOption(
                transport_id="trans_001",
                type="taxi",
                cost=Decimal('25.00'),
                duration_minutes=15,
                capacity=4,
                comfort_level=ResourceQuality.STANDARD,
                availability=True,
                pickup_location="Terminal 5",
                dropoff_location="Hotel",
                special_requirements=['wheelchair_accessible']
            ),
            TransportOption(
                transport_id="trans_002",
                type="shuttle_bus",
                cost=Decimal('8.00'),
                duration_minutes=25,
                capacity=12,
                comfort_level=ResourceQuality.BASIC,
                availability=True,
                pickup_location="Central Bus Station",
                dropoff_location="Hotel",
                special_requirements=['wheelchair_accessible']
            )
        ]
    
    def _generate_mock_meal_options(self) -> List[MealOption]:
        """Generate mock meal options for testing"""
        return [
            MealOption(
                vendor_id="meal_001",
                name="Terminal Restaurant",
                cost=Decimal('15.00'),
                meal_type="lunch",
                dietary_options=['vegetarian', 'gluten_free', 'halal'],
                location="Terminal 5",
                operating_hours="06:00-23:00"
            ),
            MealOption(
                vendor_id="meal_002",
                name="Premium Lounge",
                cost=Decimal('25.00'),
                meal_type="dinner",
                dietary_options=['vegetarian', 'vegan', 'gluten_free', 'kosher', 'halal'],
                location="Terminal 5 Lounge",
                operating_hours="05:00-24:00"
            )
        ]