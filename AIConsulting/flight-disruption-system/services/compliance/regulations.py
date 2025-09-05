import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from config import settings

logger = structlog.get_logger()

class BaseRegulationEngine(ABC):
    """Base class for regulation-specific engines"""
    
    @abstractmethod
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        delay_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance against this regulation"""
        pass
    
    @abstractmethod
    async def get_regulation_details(self) -> Dict[str, Any]:
        """Get detailed information about this regulation"""
        pass

class EU261Engine(BaseRegulationEngine):
    """EU261/2004 Regulation Engine"""
    
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        delay_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check EU261 compliance"""
        
        try:
            result = {
                'regulation': 'EU261',
                'status': 'not_eligible',
                'compensation': 0.0,
                'breakdown': {},
                'reasons': [],
                'actions': [],
                'care_obligations': {}
            }
            
            # Basic eligibility checks
            if not self._is_eu261_applicable(flight_info):
                result['reasons'].append("Flight not covered by EU261 regulation")
                return result
            
            delay_minutes = delay_info.get('delay_minutes', 0)
            
            # Minimum delay threshold (3 hours)
            if delay_minutes < 180:
                result['reasons'].append(f"Delay of {delay_minutes} minutes is below 3-hour threshold for compensation")
                result['status'] = 'below_threshold'
                return result
            
            # Check for extraordinary circumstances
            if disruption_info.get('is_extraordinary_circumstance', False):
                result['reasons'].append("Extraordinary circumstances - no compensation under EU261")
                result['status'] = 'extraordinary_circumstances'
                # Still eligible for care obligations
                result['care_obligations'] = await self._calculate_care_obligations(
                    delay_info, passenger_info, flight_info
                )
                return result
            
            # Calculate compensation based on distance and delay
            distance_km = flight_info.get('distance_km', 1500)
            compensation = self._calculate_eu261_compensation(distance_km, delay_minutes)
            
            if compensation > 0:
                result['status'] = 'eligible'
                result['compensation'] = compensation
                result['breakdown'] = {
                    'base_compensation': compensation,
                    'distance_category': self._get_distance_category(distance_km),
                    'delay_minutes': delay_minutes
                }
                result['reasons'].append(f"Eligible for €{compensation} under EU261")
                result['actions'].append("Submit compensation claim to airline")
            
            # Always calculate care obligations for EU261 eligible flights
            result['care_obligations'] = await self._calculate_care_obligations(
                delay_info, passenger_info, flight_info
            )
            
            return result
            
        except Exception as e:
            logger.error("EU261 compliance check failed", error=str(e))
            raise
    
    def _is_eu261_applicable(self, flight_info: Dict[str, Any]) -> bool:
        """Check if EU261 applies to this flight"""
        
        departure_airport = flight_info.get('departure_airport', '')
        arrival_airport = flight_info.get('arrival_airport', '')
        
        eu_airports = {
            'CDG', 'AMS', 'FRA', 'MAD', 'FCO', 'BCN', 'MUC', 'VIE', 'BRU', 'ZUR',
            'CPH', 'ARN', 'OSL', 'HEL', 'WAW', 'PRG', 'BUD', 'OTP', 'SOF', 'ATH',
            'LIS', 'DUB', 'VNO', 'RIX', 'TLL', 'LUX', 'MLT', 'LCA'
        }
        
        # EU261 applies to flights departing from EU/EEA
        return departure_airport in eu_airports
    
    def _calculate_eu261_compensation(self, distance_km: int, delay_minutes: int) -> float:
        """Calculate EU261 compensation amount"""
        
        if delay_minutes < 180:  # Less than 3 hours
            return 0.0
        
        # Distance-based compensation
        if distance_km <= 1500:
            base_compensation = settings.eu261_short_haul
        elif distance_km <= 3500:
            base_compensation = settings.eu261_medium_haul
        else:
            base_compensation = settings.eu261_long_haul
        
        # For delays between 3-4 hours on long-haul flights, compensation is halved
        if distance_km > 3500 and 180 <= delay_minutes < 240:
            return base_compensation / 2
        
        return base_compensation
    
    def _get_distance_category(self, distance_km: int) -> str:
        """Get distance category for EU261"""
        if distance_km <= 1500:
            return "short_haul"
        elif distance_km <= 3500:
            return "medium_haul"
        else:
            return "long_haul"
    
    async def _calculate_care_obligations(
        self,
        delay_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        flight_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate EU261 care obligations"""
        
        delay_hours = delay_info.get('delay_hours', 0)
        distance_km = flight_info.get('distance_km', 1500)
        
        care_obligations = {
            'meals_and_refreshments': {'required': False, 'threshold_hours': 0},
            'accommodation': {'required': False},
            'transport_to_accommodation': {'required': False},
            'telephone_calls': {'required': True, 'calls': 2}
        }
        
        # Meals and refreshments thresholds based on distance
        if distance_km <= 1500 and delay_hours >= 2:
            care_obligations['meals_and_refreshments'] = {'required': True, 'threshold_hours': 2}
        elif 1500 < distance_km <= 3500 and delay_hours >= 3:
            care_obligations['meals_and_refreshments'] = {'required': True, 'threshold_hours': 3}
        elif distance_km > 3500 and delay_hours >= 4:
            care_obligations['meals_and_refreshments'] = {'required': True, 'threshold_hours': 4}
        
        # Accommodation for overnight delays
        if delay_hours >= 8 or self._requires_overnight_stay(delay_info):
            care_obligations['accommodation']['required'] = True
            care_obligations['transport_to_accommodation']['required'] = True
        
        return care_obligations
    
    def _requires_overnight_stay(self, delay_info: Dict[str, Any]) -> bool:
        """Check if delay requires overnight stay"""
        scheduled_departure = delay_info.get('scheduled_departure')
        delay_minutes = delay_info.get('delay_minutes', 0)
        
        if not scheduled_departure:
            return delay_info.get('delay_hours', 0) >= 8
        
        new_departure = scheduled_departure + timedelta(minutes=delay_minutes)
        hour = new_departure.hour
        return hour >= 22 or hour <= 6
    
    async def get_regulation_details(self) -> Dict[str, Any]:
        """Get EU261 regulation details"""
        return {
            'regulation_name': 'EU Regulation 261/2004',
            'jurisdiction': 'European Union',
            'applicable_flights': [
                'Flights departing from EU/EEA airports',
                'Flights arriving at EU/EEA airports operated by EU carriers'
            ],
            'compensation_tiers': {
                'short_haul': {'distance': '≤ 1,500 km', 'amount': f'€{settings.eu261_short_haul}'},
                'medium_haul': {'distance': '1,500 - 3,500 km', 'amount': f'€{settings.eu261_medium_haul}'},
                'long_haul': {'distance': '> 3,500 km', 'amount': f'€{settings.eu261_long_haul}'}
            },
            'minimum_delay': '3 hours',
            'extraordinary_circumstances': [
                'Weather conditions',
                'Security risks',
                'Political instability',
                'Strikes not related to airline',
                'Air traffic management decisions'
            ],
            'care_obligations': {
                'meals': 'Required after 2-4 hours depending on distance',
                'accommodation': 'Required for overnight delays',
                'communication': '2 telephone calls or equivalent'
            },
            'claim_period': '6 years (varies by member state)',
            'last_updated': '2024-01-01'
        }

class UKCAAEngine(BaseRegulationEngine):
    """UK Civil Aviation Authority Engine (post-Brexit)"""
    
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        delay_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check UK CAA compliance"""
        
        try:
            result = {
                'regulation': 'UK_CAA',
                'status': 'not_eligible',
                'compensation': 0.0,
                'breakdown': {},
                'reasons': [],
                'actions': [],
                'care_obligations': {}
            }
            
            # Check if UK CAA rules apply
            if not self._is_uk_caa_applicable(flight_info):
                result['reasons'].append("Flight not covered by UK CAA regulations")
                return result
            
            delay_minutes = delay_info.get('delay_minutes', 0)
            
            # Minimum delay threshold (3 hours)
            if delay_minutes < 180:
                result['reasons'].append(f"Delay of {delay_minutes} minutes is below 3-hour threshold")
                result['status'] = 'below_threshold'
                return result
            
            # Check for extraordinary circumstances
            if disruption_info.get('is_extraordinary_circumstance', False):
                result['reasons'].append("Extraordinary circumstances - no compensation under UK CAA")
                result['status'] = 'extraordinary_circumstances'
                result['care_obligations'] = await self._calculate_care_obligations(
                    delay_info, passenger_info, flight_info
                )
                return result
            
            # Calculate compensation (similar to EU261 but in GBP)
            distance_km = flight_info.get('distance_km', 1500)
            compensation = self._calculate_uk_caa_compensation(distance_km, delay_minutes)
            
            if compensation > 0:
                result['status'] = 'eligible'
                result['compensation'] = compensation
                result['breakdown'] = {
                    'base_compensation': compensation,
                    'currency': 'GBP',
                    'distance_category': self._get_distance_category(distance_km),
                    'delay_minutes': delay_minutes
                }
                result['reasons'].append(f"Eligible for £{compensation} under UK CAA rules")
                result['actions'].append("Submit compensation claim to airline")
            
            result['care_obligations'] = await self._calculate_care_obligations(
                delay_info, passenger_info, flight_info
            )
            
            return result
            
        except Exception as e:
            logger.error("UK CAA compliance check failed", error=str(e))
            raise
    
    def _is_uk_caa_applicable(self, flight_info: Dict[str, Any]) -> bool:
        """Check if UK CAA rules apply"""
        departure_airport = flight_info.get('departure_airport', '')
        arrival_airport = flight_info.get('arrival_airport', '')
        
        uk_airports = {'LHR', 'LGW', 'STN', 'MAN', 'EDI', 'BHX', 'GLA', 'BRS', 'NCL'}
        
        return departure_airport in uk_airports or arrival_airport in uk_airports
    
    def _calculate_uk_caa_compensation(self, distance_km: int, delay_minutes: int) -> float:
        """Calculate UK CAA compensation amount"""
        
        if delay_minutes < 180:
            return 0.0
        
        if distance_km <= 1500:
            base_compensation = settings.uk_caa_short_haul
        elif distance_km <= 3500:
            base_compensation = settings.uk_caa_medium_haul
        else:
            base_compensation = settings.uk_caa_long_haul
        
        # Reduced compensation for delays 3-4 hours on long-haul
        if distance_km > 3500 and 180 <= delay_minutes < 240:
            return base_compensation / 2
        
        return base_compensation
    
    def _get_distance_category(self, distance_km: int) -> str:
        """Get distance category"""
        if distance_km <= 1500:
            return "short_haul"
        elif distance_km <= 3500:
            return "medium_haul"
        else:
            return "long_haul"
    
    async def _calculate_care_obligations(
        self,
        delay_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        flight_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate UK CAA care obligations"""
        
        delay_hours = delay_info.get('delay_hours', 0)
        
        return {
            'meals': {'required': delay_hours >= 2},
            'accommodation': {'required': delay_hours >= 8},
            'communication': {'required': delay_hours >= 2, 'calls': 2},
            'transport': {'required': delay_hours >= 8}
        }
    
    async def get_regulation_details(self) -> Dict[str, Any]:
        """Get UK CAA regulation details"""
        return {
            'regulation_name': 'UK Civil Aviation Authority Rules',
            'jurisdiction': 'United Kingdom',
            'applicable_flights': [
                'Flights departing from UK airports',
                'Flights arriving at UK airports from non-EU countries'
            ],
            'compensation_tiers': {
                'short_haul': {'distance': '≤ 1,500 km', 'amount': f'£{settings.uk_caa_short_haul}'},
                'medium_haul': {'distance': '1,500 - 3,500 km', 'amount': f'£{settings.uk_caa_medium_haul}'},
                'long_haul': {'distance': '> 3,500 km', 'amount': f'£{settings.uk_caa_long_haul}'}
            },
            'minimum_delay': '3 hours',
            'claim_period': '6 years',
            'last_updated': '2024-01-01'
        }

class DOTEngine(BaseRegulationEngine):
    """US Department of Transportation Engine"""
    
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        delay_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check US DOT compliance"""
        
        try:
            result = {
                'regulation': 'US_DOT',
                'status': 'not_eligible',
                'compensation': 0.0,
                'breakdown': {},
                'reasons': [],
                'actions': [],
                'care_obligations': {}
            }
            
            # Check if DOT rules apply
            if not self._is_dot_applicable(flight_info):
                result['reasons'].append("Flight not covered by US DOT regulations")
                return result
            
            # DOT focuses on denied boarding, not delays
            # But we'll implement delay compensation based on DOT guidelines
            delay_minutes = delay_info.get('delay_minutes', 0)
            ticket_price = passenger_info.get('ticket_price', 300.0)
            
            # DOT doesn't mandate delay compensation, but some airlines provide it
            compensation = self._calculate_dot_compensation(delay_minutes, ticket_price, flight_info)
            
            if compensation > 0:
                result['status'] = 'eligible'
                result['compensation'] = compensation
                result['breakdown'] = {
                    'base_compensation': compensation,
                    'currency': 'USD',
                    'calculation_method': 'percentage_of_ticket',
                    'ticket_price': ticket_price
                }
                result['reasons'].append(f"Eligible for ${compensation} under DOT guidelines")
                result['actions'].append("Contact airline customer service for compensation")
            else:
                result['reasons'].append("No mandatory compensation under DOT for delays")
                result['actions'].append("Check airline's customer service plan for voluntary compensation")
            
            return result
            
        except Exception as e:
            logger.error("DOT compliance check failed", error=str(e))
            raise
    
    def _is_dot_applicable(self, flight_info: Dict[str, Any]) -> bool:
        """Check if DOT rules apply"""
        departure_airport = flight_info.get('departure_airport', '')
        arrival_airport = flight_info.get('arrival_airport', '')
        
        us_airports = {'JFK', 'LAX', 'ORD', 'MIA', 'DFW', 'ATL', 'BOS', 'IAD', 'SFO', 'SEA'}
        
        return departure_airport in us_airports or arrival_airport in us_airports
    
    def _calculate_dot_compensation(
        self, 
        delay_minutes: int, 
        ticket_price: float, 
        flight_info: Dict[str, Any]
    ) -> float:
        """Calculate DOT-based compensation (voluntary)"""
        
        # DOT doesn't mandate delay compensation, but we'll use reasonable guidelines
        if delay_minutes < 120:  # Less than 2 hours
            return 0.0
        
        is_domestic = self._is_domestic_flight(flight_info)
        
        if is_domestic:
            if delay_minutes >= 240:  # 4+ hours
                return min(ticket_price * 0.25, settings.dot_domestic_2x_max / 2)
            elif delay_minutes >= 180:  # 3+ hours
                return min(ticket_price * 0.15, settings.dot_domestic_2x_max / 3)
        else:
            # International flights - more generous
            if delay_minutes >= 300:  # 5+ hours
                return min(ticket_price * 0.4, settings.dot_domestic_2x_max * settings.dot_international_multiplier)
            elif delay_minutes >= 240:  # 4+ hours
                return min(ticket_price * 0.25, settings.dot_domestic_2x_max)
        
        return 0.0
    
    def _is_domestic_flight(self, flight_info: Dict[str, Any]) -> bool:
        """Check if flight is domestic US"""
        departure_airport = flight_info.get('departure_airport', '')
        arrival_airport = flight_info.get('arrival_airport', '')
        
        us_airports = {'JFK', 'LAX', 'ORD', 'MIA', 'DFW', 'ATL', 'BOS', 'IAD', 'SFO', 'SEA'}
        
        return departure_airport in us_airports and arrival_airport in us_airports
    
    async def get_regulation_details(self) -> Dict[str, Any]:
        """Get DOT regulation details"""
        return {
            'regulation_name': 'US Department of Transportation Rules',
            'jurisdiction': 'United States',
            'applicable_flights': [
                'Flights to/from US airports',
                'US carrier flights internationally'
            ],
            'primary_focus': 'Denied boarding compensation',
            'delay_compensation': 'Voluntary (not mandated)',
            'denied_boarding_compensation': {
                'domestic_1_2_hours': f'${settings.dot_domestic_2x_max}',
                'domestic_over_2_hours': f'${settings.dot_domestic_4x_max}',
                'international_multiplier': settings.dot_international_multiplier
            },
            'claim_period': '3 years',
            'last_updated': '2024-01-01'
        }

class IATAEngine(BaseRegulationEngine):
    """IATA Recommendations Engine"""
    
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        delay_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check IATA recommendations compliance"""
        
        try:
            result = {
                'regulation': 'IATA',
                'status': 'recommendations_only',
                'compensation': 0.0,
                'breakdown': {},
                'reasons': [],
                'actions': [],
                'care_obligations': {}
            }
            
            delay_minutes = delay_info.get('delay_minutes', 0)
            
            # IATA provides recommendations, not mandatory rules
            if delay_minutes >= 120:  # 2+ hours
                result['reasons'].append("IATA recommends passenger care for delays over 2 hours")
                result['actions'].append("Request care provisions as per IATA recommendations")
                
                # Calculate care provisions
                result['care_obligations'] = await self._calculate_care_provisions(
                    delay_info, passenger_info, flight_info
                )
            
            if delay_minutes >= 300:  # 5+ hours
                result['reasons'].append("IATA recommends considering compensation for severe delays")
                result['actions'].append("Discuss compensation options with airline")
            
            return result
            
        except Exception as e:
            logger.error("IATA compliance check failed", error=str(e))
            raise
    
    async def _calculate_care_provisions(
        self,
        delay_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        flight_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate IATA care provisions"""
        
        delay_hours = delay_info.get('delay_hours', 0)
        
        return {
            'meals': {'recommended': delay_hours >= 2},
            'accommodation': {'recommended': delay_hours >= 8},
            'communication': {'recommended': delay_hours >= 2},
            'information': {'required': True, 'updates_every': '30 minutes'}
        }
    
    async def get_regulation_details(self) -> Dict[str, Any]:
        """Get IATA recommendations details"""
        return {
            'organization': 'International Air Transport Association',
            'type': 'Industry recommendations',
            'binding': False,
            'applicable_flights': 'All international flights',
            'recommendations': {
                'information': 'Regular updates on delays',
                'care': 'Meals and accommodation for significant delays',
                'compensation': 'Voluntary based on airline policy'
            },
            'last_updated': '2024-01-01'
        }