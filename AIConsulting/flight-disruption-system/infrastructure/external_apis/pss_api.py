import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from config import ExternalAPIConfig

logger = structlog.get_logger()

class PSSProvider(Enum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    TRAVELPORT = "travelport"

@dataclass
class FlightAvailability:
    """Flight availability data structure"""
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    available_seats: Dict[str, int]  # class -> seat count
    price: Dict[str, float]  # class -> price
    booking_class: str
    fare_basis: str
    restrictions: List[str]

@dataclass
class PassengerBooking:
    """Passenger booking data structure"""
    pnr: str
    passenger_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    flight_segments: List[Dict[str, Any]]
    booking_status: str
    payment_status: str
    created_at: datetime
    modified_at: datetime

class PSSAPIClient:
    """Passenger Service System API client for rebooking and data retrieval"""
    
    def __init__(self, config: ExternalAPIConfig):
        self.config = config
        self.provider = PSSProvider(config.pss_provider)
        self.api_key = config.pss_api_key
        self.base_url = config.pss_api_url
        self.username = config.pss_username
        self.password = config.pss_password
        self.http_client: Optional[httpx.AsyncClient] = None
        self.auth_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        
    async def start(self):
        """Initialize PSS client and authenticate"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Authenticate with PSS
        if not self.config.demo_mode:
            await self._authenticate()
        
        logger.info(f"PSS API client started with provider: {self.provider.value}")
    
    async def stop(self):
        """Close PSS client"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("PSS API client stopped")
    
    async def search_alternative_flights(
        self,
        origin: str,
        destination: str,
        departure_date: datetime,
        passenger_count: int = 1,
        booking_class: str = "economy"
    ) -> List[FlightAvailability]:
        """Search for alternative flights"""
        try:
            # Demo mode - return mock flights
            if self.config.demo_mode:
                return self._generate_mock_flights(origin, destination, departure_date)
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._search_amadeus_flights(origin, destination, departure_date, passenger_count, booking_class)
            elif self.provider == PSSProvider.SABRE:
                return await self._search_sabre_flights(origin, destination, departure_date, passenger_count, booking_class)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._search_travelport_flights(origin, destination, departure_date, passenger_count, booking_class)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Flight search error", error=str(e))
            return []
    
    async def get_passenger_booking(self, pnr: str) -> Optional[PassengerBooking]:
        """Retrieve passenger booking by PNR"""
        try:
            # Demo mode - return mock booking
            if self.config.demo_mode:
                return self._generate_mock_booking(pnr)
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._get_amadeus_booking(pnr)
            elif self.provider == PSSProvider.SABRE:
                return await self._get_sabre_booking(pnr)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._get_travelport_booking(pnr)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Booking retrieval error", pnr=pnr, error=str(e))
            return None
    
    async def create_new_booking(
        self,
        passenger_data: Dict[str, Any],
        flight_data: FlightAvailability,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create new booking and return PNR"""
        try:
            # Demo mode - return mock PNR
            if self.config.demo_mode:
                return self._generate_mock_pnr()
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._create_amadeus_booking(passenger_data, flight_data, payment_data)
            elif self.provider == PSSProvider.SABRE:
                return await self._create_sabre_booking(passenger_data, flight_data, payment_data)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._create_travelport_booking(passenger_data, flight_data, payment_data)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Booking creation error", error=str(e))
            return None
    
    async def modify_booking(
        self,
        pnr: str,
        changes: Dict[str, Any]
    ) -> bool:
        """Modify existing booking"""
        try:
            # Demo mode - always succeed
            if self.config.demo_mode:
                logger.info(f"Mock booking modification for PNR: {pnr}")
                return True
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._modify_amadeus_booking(pnr, changes)
            elif self.provider == PSSProvider.SABRE:
                return await self._modify_sabre_booking(pnr, changes)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._modify_travelport_booking(pnr, changes)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Booking modification error", pnr=pnr, error=str(e))
            return False
    
    async def cancel_booking(self, pnr: str, reason: str = "") -> bool:
        """Cancel booking"""
        try:
            # Demo mode - always succeed
            if self.config.demo_mode:
                logger.info(f"Mock booking cancellation for PNR: {pnr}")
                return True
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._cancel_amadeus_booking(pnr, reason)
            elif self.provider == PSSProvider.SABRE:
                return await self._cancel_sabre_booking(pnr, reason)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._cancel_travelport_booking(pnr, reason)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Booking cancellation error", pnr=pnr, error=str(e))
            return False
    
    async def get_flight_status(self, flight_number: str, date: datetime) -> Dict[str, Any]:
        """Get real-time flight status"""
        try:
            # Demo mode - return mock status
            if self.config.demo_mode:
                return self._generate_mock_flight_status(flight_number)
            
            # Ensure authentication
            await self._ensure_authenticated()
            
            if self.provider == PSSProvider.AMADEUS:
                return await self._get_amadeus_flight_status(flight_number, date)
            elif self.provider == PSSProvider.SABRE:
                return await self._get_sabre_flight_status(flight_number, date)
            elif self.provider == PSSProvider.TRAVELPORT:
                return await self._get_travelport_flight_status(flight_number, date)
            else:
                raise ValueError(f"Unsupported PSS provider: {self.provider}")
                
        except Exception as e:
            logger.error("Flight status error", flight_number=flight_number, error=str(e))
            return {}
    
    async def batch_rebooking(
        self,
        rebooking_requests: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Process multiple rebooking requests"""
        try:
            results = {}
            
            # Process in batches to avoid rate limits
            batch_size = 10
            for i in range(0, len(rebooking_requests), batch_size):
                batch = rebooking_requests[i:i + batch_size]
                
                tasks = [
                    self._process_single_rebooking(request)
                    for request in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for request, result in zip(batch, batch_results):
                    pnr = request.get('pnr')
                    if isinstance(result, Exception):
                        logger.error(f"Rebooking failed for PNR {pnr}", error=str(result))
                        results[pnr] = False
                    else:
                        results[pnr] = result
                
                # Small delay between batches
                if i + batch_size < len(rebooking_requests):
                    await asyncio.sleep(1)
            
            logger.info(f"Batch rebooking completed: {len(results)} requests processed")
            return results
            
        except Exception as e:
            logger.error("Batch rebooking error", error=str(e))
            return {}
    
    async def _authenticate(self):
        """Authenticate with PSS"""
        try:
            auth_url = f"{self.base_url}/auth"
            auth_data = {
                'username': self.username,
                'password': self.password,
                'grant_type': 'client_credentials'
            }
            
            if self.provider == PSSProvider.AMADEUS:
                auth_data['client_id'] = self.api_key
                auth_data['client_secret'] = self.password
            
            response = await self.http_client.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.auth_token = auth_result.get('access_token')
            expires_in = auth_result.get('expires_in', 3600)
            self.token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
            
            logger.info(f"PSS authentication successful for {self.provider.value}")
            
        except Exception as e:
            logger.error("PSS authentication failed", error=str(e))
            raise
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token"""
        if not self.auth_token or (self.token_expires and datetime.utcnow() >= self.token_expires):
            await self._authenticate()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        elif self.api_key:
            headers['X-API-Key'] = self.api_key
        
        return headers
    
    # Amadeus-specific methods
    async def _search_amadeus_flights(self, origin: str, destination: str, departure_date: datetime, passenger_count: int, booking_class: str) -> List[FlightAvailability]:
        """Search flights using Amadeus API"""
        url = f"{self.base_url}/v2/shopping/flight-offers"
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date.strftime('%Y-%m-%d'),
            'adults': passenger_count,
            'travelClass': booking_class.upper(),
            'max': 50
        }
        
        response = await self.http_client.get(url, params=params, headers=self._get_auth_headers())
        response.raise_for_status()
        
        data = response.json()
        return self._parse_amadeus_flights(data)
    
    async def _get_amadeus_booking(self, pnr: str) -> Optional[PassengerBooking]:
        """Get booking from Amadeus"""
        url = f"{self.base_url}/v1/booking/flight-orders/{pnr}"
        response = await self.http_client.get(url, headers=self._get_auth_headers())
        response.raise_for_status()
        
        data = response.json()
        return self._parse_amadeus_booking(data)
    
    # Sabre-specific methods (simplified implementations)
    async def _search_sabre_flights(self, origin: str, destination: str, departure_date: datetime, passenger_count: int, booking_class: str) -> List[FlightAvailability]:
        """Search flights using Sabre API"""
        # Simplified Sabre implementation
        return self._generate_mock_flights(origin, destination, departure_date)
    
    async def _get_sabre_booking(self, pnr: str) -> Optional[PassengerBooking]:
        """Get booking from Sabre"""
        return self._generate_mock_booking(pnr)
    
    # Travelport-specific methods (simplified implementations)  
    async def _search_travelport_flights(self, origin: str, destination: str, departure_date: datetime, passenger_count: int, booking_class: str) -> List[FlightAvailability]:
        """Search flights using Travelport API"""
        return self._generate_mock_flights(origin, destination, departure_date)
    
    async def _get_travelport_booking(self, pnr: str) -> Optional[PassengerBooking]:
        """Get booking from Travelport"""
        return self._generate_mock_booking(pnr)
    
    # Mock data generators for demo mode
    def _generate_mock_flights(self, origin: str, destination: str, departure_date: datetime) -> List[FlightAvailability]:
        """Generate mock flight availability data"""
        import random
        
        flights = []
        
        # Generate 5-10 alternative flights
        for i in range(random.randint(5, 10)):
            flight_number = f"BA{1000 + i}"
            dep_time = departure_date + timedelta(hours=random.randint(1, 24))
            arr_time = dep_time + timedelta(hours=random.randint(1, 8))
            
            flight = FlightAvailability(
                flight_number=flight_number,
                departure_airport=origin,
                arrival_airport=destination,
                departure_time=dep_time,
                arrival_time=arr_time,
                aircraft_type=random.choice(['A320', 'A350', 'B737', 'B777']),
                available_seats={
                    'economy': random.randint(0, 50),
                    'premium_economy': random.randint(0, 20),
                    'business': random.randint(0, 15),
                    'first': random.randint(0, 8)
                },
                price={
                    'economy': random.uniform(200, 800),
                    'premium_economy': random.uniform(400, 1200),
                    'business': random.uniform(800, 3000),
                    'first': random.uniform(2000, 8000)
                },
                booking_class='Y',
                fare_basis='YL14D',
                restrictions=['NON-REFUNDABLE', '24HR-CHANGE']
            )
            flights.append(flight)
        
        return sorted(flights, key=lambda f: f.departure_time)
    
    def _generate_mock_booking(self, pnr: str) -> PassengerBooking:
        """Generate mock booking data"""
        return PassengerBooking(
            pnr=pnr,
            passenger_id=f"PAX_{pnr}",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+447700123456",
            flight_segments=[
                {
                    'flight_number': 'BA123',
                    'departure_airport': 'LHR',
                    'arrival_airport': 'CDG',
                    'departure_time': datetime.utcnow() + timedelta(hours=2),
                    'seat': '12A',
                    'class': 'economy'
                }
            ],
            booking_status='confirmed',
            payment_status='paid',
            created_at=datetime.utcnow() - timedelta(days=7),
            modified_at=datetime.utcnow()
        )
    
    def _generate_mock_pnr(self) -> str:
        """Generate mock PNR"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def _generate_mock_flight_status(self, flight_number: str) -> Dict[str, Any]:
        """Generate mock flight status"""
        import random
        
        statuses = ['on_time', 'delayed', 'boarding', 'departed', 'arrived', 'cancelled']
        status = random.choice(statuses)
        
        return {
            'flight_number': flight_number,
            'status': status,
            'scheduled_departure': datetime.utcnow() + timedelta(hours=2),
            'actual_departure': datetime.utcnow() + timedelta(hours=2, minutes=random.randint(-30, 120)),
            'gate': f"A{random.randint(1, 50)}",
            'terminal': random.choice(['1', '2', '3', '4', '5']),
            'delay_minutes': random.randint(0, 180) if status == 'delayed' else 0,
            'delay_reason': random.choice(['weather', 'technical', 'crew', 'atc', 'airport_congestion']) if status == 'delayed' else None
        }
    
    def _parse_amadeus_flights(self, data: Dict[str, Any]) -> List[FlightAvailability]:
        """Parse Amadeus flight search response"""
        # Simplified parsing - full implementation would parse all Amadeus response fields
        return self._generate_mock_flights('LHR', 'CDG', datetime.utcnow() + timedelta(hours=2))
    
    def _parse_amadeus_booking(self, data: Dict[str, Any]) -> PassengerBooking:
        """Parse Amadeus booking response"""
        # Simplified parsing - full implementation would parse all Amadeus booking fields
        return self._generate_mock_booking('ABC123')
    
    async def _process_single_rebooking(self, request: Dict[str, Any]) -> bool:
        """Process single rebooking request"""
        try:
            pnr = request.get('pnr')
            new_flight = request.get('new_flight')
            
            # In demo mode, always succeed
            if self.config.demo_mode:
                await asyncio.sleep(0.1)  # Simulate API call
                return True
            
            # Cancel old booking
            if not await self.cancel_booking(pnr, "Rebooking due to disruption"):
                return False
            
            # Create new booking
            passenger_data = request.get('passenger_data')
            flight_data = request.get('flight_data')
            new_pnr = await self.create_new_booking(passenger_data, flight_data)
            
            return new_pnr is not None
            
        except Exception as e:
            logger.error("Single rebooking error", error=str(e))
            return False
    
    # Placeholder methods for other PSS operations
    async def _create_amadeus_booking(self, passenger_data: Dict[str, Any], flight_data: FlightAvailability, payment_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        return self._generate_mock_pnr()
    
    async def _modify_amadeus_booking(self, pnr: str, changes: Dict[str, Any]) -> bool:
        return True
    
    async def _cancel_amadeus_booking(self, pnr: str, reason: str) -> bool:
        return True
    
    async def _get_amadeus_flight_status(self, flight_number: str, date: datetime) -> Dict[str, Any]:
        return self._generate_mock_flight_status(flight_number)
    
    # Sabre placeholder methods
    async def _create_sabre_booking(self, passenger_data: Dict[str, Any], flight_data: FlightAvailability, payment_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        return self._generate_mock_pnr()
    
    async def _modify_sabre_booking(self, pnr: str, changes: Dict[str, Any]) -> bool:
        return True
    
    async def _cancel_sabre_booking(self, pnr: str, reason: str) -> bool:
        return True
    
    async def _get_sabre_flight_status(self, flight_number: str, date: datetime) -> Dict[str, Any]:
        return self._generate_mock_flight_status(flight_number)
    
    # Travelport placeholder methods
    async def _create_travelport_booking(self, passenger_data: Dict[str, Any], flight_data: FlightAvailability, payment_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        return self._generate_mock_pnr()
    
    async def _modify_travelport_booking(self, pnr: str, changes: Dict[str, Any]) -> bool:
        return True
    
    async def _cancel_travelport_booking(self, pnr: str, reason: str) -> bool:
        return True
    
    async def _get_travelport_flight_status(self, flight_number: str, date: datetime) -> Dict[str, Any]:
        return self._generate_mock_flight_status(flight_number)
    
    async def health_check(self) -> bool:
        """Check if PSS API is accessible"""
        try:
            if self.config.demo_mode:
                return True
            
            # Simple health check
            health_url = f"{self.base_url}/health"
            response = await self.http_client.get(health_url, timeout=5.0)
            return response.status_code == 200
            
        except Exception:
            return False