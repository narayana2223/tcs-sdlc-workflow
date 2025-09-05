"""
Flight Data API Client
Integration with airline systems and flight data providers
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_client import BaseAPIClient, APIConfig, APIResponse, CachedAPIClient


@dataclass
class FlightInfo:
    """Flight information data structure"""
    flight_id: str
    flight_number: str
    airline_code: str
    departure_airport: str
    arrival_airport: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str = "scheduled"
    delay_minutes: int = 0
    gate: Optional[str] = None
    terminal: Optional[str] = None
    aircraft_type: Optional[str] = None
    registration: Optional[str] = None


class FlightDataClient(CachedAPIClient):
    """Client for flight data APIs (FlightAware, AODB, etc.)"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config, cache_ttl=60)  # 1 minute cache
        self.logger = logging.getLogger(__name__)
    
    def _get_health_endpoint(self) -> str:
        return "health"
    
    async def authenticate(self) -> bool:
        """Authenticate with flight data API"""
        if self.config.mock_mode:
            return True
        
        try:
            response = await self._make_request('POST', 'auth/token', {
                'api_key': self.config.api_key,
                'client_id': self.config.default_headers.get('User-Agent', 'unknown')
            })
            
            if response.success and response.data:
                token = response.data.get('access_token')
                if token:
                    self.config.default_headers['Authorization'] = f'Bearer {token}'
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    async def get_flight_info(self, flight_number: str, date: str) -> Optional[FlightInfo]:
        """Get detailed flight information"""
        if self.config.mock_mode:
            return self._generate_mock_flight_info(flight_number, date)
        
        try:
            response = await self._make_cached_request(
                'GET',
                f'flights/{flight_number}',
                params={'date': date}
            )
            
            if response.success and response.data:
                return self._parse_flight_info(response.data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get flight info for {flight_number}: {e}")
            return None
    
    async def get_flights_by_route(
        self,
        departure_airport: str,
        arrival_airport: str,
        date: str
    ) -> List[FlightInfo]:
        """Get all flights for a specific route"""
        if self.config.mock_mode:
            return self._generate_mock_route_flights(departure_airport, arrival_airport, date)
        
        try:
            response = await self._make_cached_request(
                'GET',
                'flights/route',
                params={
                    'departure': departure_airport,
                    'arrival': arrival_airport,
                    'date': date
                }
            )
            
            if response.success and response.data:
                flights = []
                for flight_data in response.data.get('flights', []):
                    flight_info = self._parse_flight_info(flight_data)
                    if flight_info:
                        flights.append(flight_info)
                return flights
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get route flights: {e}")
            return []
    
    async def get_airport_departures(
        self,
        airport_code: str,
        hours_ahead: int = 24
    ) -> List[FlightInfo]:
        """Get departure flights from an airport"""
        if self.config.mock_mode:
            return self._generate_mock_airport_departures(airport_code, hours_ahead)
        
        try:
            end_time = datetime.now() + timedelta(hours=hours_ahead)
            
            response = await self._make_cached_request(
                'GET',
                f'airports/{airport_code}/departures',
                params={
                    'start_time': datetime.now().isoformat(),
                    'end_time': end_time.isoformat()
                }
            )
            
            if response.success and response.data:
                flights = []
                for flight_data in response.data.get('departures', []):
                    flight_info = self._parse_flight_info(flight_data)
                    if flight_info:
                        flights.append(flight_info)
                return flights
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get airport departures: {e}")
            return []
    
    async def get_airport_arrivals(
        self,
        airport_code: str,
        hours_ahead: int = 24
    ) -> List[FlightInfo]:
        """Get arrival flights to an airport"""
        if self.config.mock_mode:
            return self._generate_mock_airport_arrivals(airport_code, hours_ahead)
        
        try:
            end_time = datetime.now() + timedelta(hours=hours_ahead)
            
            response = await self._make_cached_request(
                'GET',
                f'airports/{airport_code}/arrivals',
                params={
                    'start_time': datetime.now().isoformat(),
                    'end_time': end_time.isoformat()
                }
            )
            
            if response.success and response.data:
                flights = []
                for flight_data in response.data.get('arrivals', []):
                    flight_info = self._parse_flight_info(flight_data)
                    if flight_info:
                        flights.append(flight_info)
                return flights
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get airport arrivals: {e}")
            return []
    
    async def get_flight_status_updates(
        self,
        flight_ids: List[str],
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get status updates for multiple flights"""
        if self.config.mock_mode:
            return self._generate_mock_status_updates(flight_ids)
        
        try:
            params = {'flight_ids': ','.join(flight_ids)}
            if since:
                params['since'] = since.isoformat()
            
            response = await self._make_request(
                'GET',
                'flights/status_updates',
                params=params
            )
            
            if response.success and response.data:
                return response.data.get('updates', [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get status updates: {e}")
            return []
    
    async def subscribe_to_flight_updates(
        self,
        flight_ids: List[str],
        callback_url: str
    ) -> bool:
        """Subscribe to real-time flight updates"""
        if self.config.mock_mode:
            self.logger.info(f"Mock: Subscribed to updates for {len(flight_ids)} flights")
            return True
        
        try:
            response = await self._make_request(
                'POST',
                'subscriptions/flights',
                data={
                    'flight_ids': flight_ids,
                    'callback_url': callback_url,
                    'events': ['departure', 'arrival', 'delay', 'cancellation', 'gate_change']
                }
            )
            
            return response.success
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to flight updates: {e}")
            return False
    
    def _parse_flight_info(self, data: Dict[str, Any]) -> Optional[FlightInfo]:
        """Parse API response into FlightInfo object"""
        try:
            return FlightInfo(
                flight_id=data.get('flight_id', ''),
                flight_number=data.get('flight_number', ''),
                airline_code=data.get('airline_code', ''),
                departure_airport=data.get('departure_airport', ''),
                arrival_airport=data.get('arrival_airport', ''),
                scheduled_departure=self._parse_datetime(data.get('scheduled_departure')),
                scheduled_arrival=self._parse_datetime(data.get('scheduled_arrival')),
                actual_departure=self._parse_datetime(data.get('actual_departure')),
                actual_arrival=self._parse_datetime(data.get('actual_arrival')),
                status=data.get('status', 'scheduled'),
                delay_minutes=data.get('delay_minutes', 0),
                gate=data.get('gate'),
                terminal=data.get('terminal'),
                aircraft_type=data.get('aircraft_type'),
                registration=data.get('registration')
            )
        except Exception as e:
            self.logger.error(f"Failed to parse flight info: {e}")
            return None
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_str:
            return None
        
        try:
            # Handle various datetime formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
    
    # Mock data generation methods
    def _generate_mock_flight_info(self, flight_number: str, date: str) -> FlightInfo:
        """Generate mock flight information"""
        import random
        from uuid import uuid4
        
        base_time = datetime.now() + timedelta(hours=random.randint(1, 24))
        
        return FlightInfo(
            flight_id=str(uuid4()),
            flight_number=flight_number,
            airline_code=flight_number[:2],
            departure_airport="LHR",
            arrival_airport="CDG",
            scheduled_departure=base_time,
            scheduled_arrival=base_time + timedelta(hours=2),
            actual_departure=base_time + timedelta(minutes=random.randint(-10, 30)) if random.random() > 0.3 else None,
            actual_arrival=None,
            status=random.choice(["scheduled", "boarding", "departed", "delayed"]),
            delay_minutes=random.randint(0, 60) if random.random() > 0.7 else 0,
            gate=f"A{random.randint(1, 20)}",
            terminal="1",
            aircraft_type="Boeing 737-800",
            registration=f"G-{random.choice(['EUU', 'EUR', 'EUS'])}{random.randint(100, 999)}"
        )
    
    def _generate_mock_route_flights(
        self,
        departure: str,
        arrival: str,
        date: str
    ) -> List[FlightInfo]:
        """Generate mock flights for a route"""
        import random
        from uuid import uuid4
        
        flights = []
        base_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        for i in range(random.randint(5, 15)):
            flight_time = base_date + timedelta(hours=i * 2 + random.randint(0, 120) / 60)
            
            flights.append(FlightInfo(
                flight_id=str(uuid4()),
                flight_number=f"BA{1000 + i}",
                airline_code="BA",
                departure_airport=departure,
                arrival_airport=arrival,
                scheduled_departure=flight_time,
                scheduled_arrival=flight_time + timedelta(hours=random.randint(1, 8)),
                status=random.choice(["scheduled", "delayed", "on_time"]),
                delay_minutes=random.randint(0, 60) if random.random() > 0.8 else 0,
                gate=f"B{random.randint(1, 30)}",
                terminal=str(random.randint(1, 5))
            ))
        
        return flights
    
    def _generate_mock_airport_departures(self, airport: str, hours: int) -> List[FlightInfo]:
        """Generate mock departure flights"""
        import random
        from uuid import uuid4
        
        flights = []
        current_time = datetime.now()
        
        destinations = ["CDG", "FRA", "AMS", "MAD", "FCO", "MUC", "ZUR", "VIE", "BRU", "CPH"]
        airlines = ["BA", "LH", "AF", "KL", "IB"]
        
        for i in range(random.randint(20, 50)):
            departure_time = current_time + timedelta(minutes=random.randint(30, hours * 60))
            
            flights.append(FlightInfo(
                flight_id=str(uuid4()),
                flight_number=f"{random.choice(airlines)}{random.randint(100, 999)}",
                airline_code=random.choice(airlines),
                departure_airport=airport,
                arrival_airport=random.choice(destinations),
                scheduled_departure=departure_time,
                scheduled_arrival=departure_time + timedelta(hours=random.randint(1, 6)),
                status=random.choice(["scheduled", "boarding", "delayed", "departed"]),
                delay_minutes=random.randint(0, 120) if random.random() > 0.7 else 0,
                gate=f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 30)}",
                terminal=str(random.randint(1, 5))
            ))
        
        return sorted(flights, key=lambda f: f.scheduled_departure)
    
    def _generate_mock_airport_arrivals(self, airport: str, hours: int) -> List[FlightInfo]:
        """Generate mock arrival flights"""
        import random
        from uuid import uuid4
        
        flights = []
        current_time = datetime.now()
        
        origins = ["CDG", "FRA", "AMS", "MAD", "FCO", "MUC", "ZUR", "VIE", "BRU", "CPH"]
        airlines = ["BA", "LH", "AF", "KL", "IB"]
        
        for i in range(random.randint(20, 50)):
            arrival_time = current_time + timedelta(minutes=random.randint(30, hours * 60))
            
            flights.append(FlightInfo(
                flight_id=str(uuid4()),
                flight_number=f"{random.choice(airlines)}{random.randint(100, 999)}",
                airline_code=random.choice(airlines),
                departure_airport=random.choice(origins),
                arrival_airport=airport,
                scheduled_departure=arrival_time - timedelta(hours=random.randint(1, 6)),
                scheduled_arrival=arrival_time,
                status=random.choice(["en_route", "approaching", "landed", "delayed"]),
                delay_minutes=random.randint(0, 120) if random.random() > 0.7 else 0,
                gate=f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 30)}",
                terminal=str(random.randint(1, 5))
            ))
        
        return sorted(flights, key=lambda f: f.scheduled_arrival)
    
    def _generate_mock_status_updates(self, flight_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate mock status updates"""
        import random
        
        updates = []
        statuses = ["delayed", "on_time", "cancelled", "diverted", "gate_changed"]
        
        for flight_id in flight_ids:
            if random.random() > 0.5:  # 50% chance of having an update
                updates.append({
                    'flight_id': flight_id,
                    'status': random.choice(statuses),
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Flight status updated to {random.choice(statuses)}",
                    'delay_minutes': random.randint(15, 180) if random.random() > 0.6 else None,
                    'new_gate': f"B{random.randint(1, 30)}" if random.random() > 0.8 else None
                })
        
        return updates


class AirlineSystemClient(BaseAPIClient):
    """Client for airline-specific systems (PSS, DCS, etc.)"""
    
    def __init__(self, config: APIConfig, airline_code: str):
        super().__init__(config)
        self.airline_code = airline_code
        self.logger = logging.getLogger(__name__)
    
    def _get_health_endpoint(self) -> str:
        return "system/health"
    
    async def authenticate(self) -> bool:
        """Authenticate with airline system"""
        if self.config.mock_mode:
            return True
        
        try:
            response = await self._make_request('POST', 'auth/login', {
                'username': self.config.api_key,
                'password': self.config.default_headers.get('X-API-Secret'),
                'system': 'disruption_management'
            })
            
            if response.success and response.data:
                session_token = response.data.get('session_token')
                if session_token:
                    self.config.default_headers['X-Session-Token'] = session_token
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    async def get_passenger_list(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get passenger manifest for a flight"""
        if self.config.mock_mode:
            return self._generate_mock_passenger_list(flight_id)
        
        try:
            response = await self._make_request(
                'GET',
                f'flights/{flight_id}/passengers'
            )
            
            if response.success and response.data:
                return response.data.get('passengers', [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get passenger list: {e}")
            return []
    
    async def initiate_rebooking(
        self,
        passenger_id: str,
        original_flight_id: str,
        new_flight_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Initiate passenger rebooking"""
        if self.config.mock_mode:
            return {
                'success': True,
                'rebooking_id': f"RB{hash(passenger_id) % 100000}",
                'confirmation_code': f"C{hash(new_flight_id) % 1000000}",
                'seat_assignment': f"12{chr(65 + hash(passenger_id) % 6)}"
            }
        
        try:
            response = await self._make_request(
                'POST',
                'rebooking/initiate',
                data={
                    'passenger_id': passenger_id,
                    'original_flight_id': original_flight_id,
                    'new_flight_id': new_flight_id,
                    'reason': reason,
                    'priority': 'high'
                }
            )
            
            if response.success and response.data:
                return response.data
            
            return {'success': False, 'error': response.error_message}
            
        except Exception as e:
            self.logger.error(f"Failed to initiate rebooking: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_mock_passenger_list(self, flight_id: str) -> List[Dict[str, Any]]:
        """Generate mock passenger list"""
        import random
        from uuid import uuid4
        
        passengers = []
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        for i in range(random.randint(50, 180)):
            passengers.append({
                'passenger_id': str(uuid4()),
                'booking_reference': f"ABC{random.randint(100, 999)}",
                'first_name': random.choice(first_names),
                'last_name': random.choice(last_names),
                'seat_number': f"{random.randint(1, 30)}{random.choice('ABCDEF')}",
                'class': random.choice(["economy", "business", "first"]),
                'frequent_flyer_number': f"FF{random.randint(1000000, 9999999)}" if random.random() > 0.6 else None,
                'special_needs': random.choice([[], ["wheelchair"], ["unaccompanied_minor"], ["special_meal"]]),
                'checked_in': random.random() > 0.3,
                'contact_email': f"passenger{i}@example.com",
                'contact_phone': f"+44{random.randint(1000000, 9999999)}"
            })
        
        return passengers