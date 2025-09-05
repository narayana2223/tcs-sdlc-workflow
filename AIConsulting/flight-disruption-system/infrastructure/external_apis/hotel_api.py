import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from dataclasses import dataclass
from enum import Enum
from config import ExternalAPIConfig

logger = structlog.get_logger()

class HotelProvider(Enum):
    BOOKING_COM = "booking.com"
    EXPEDIA = "expedia"
    AMADEUS_HOTEL = "amadeus_hotel"

@dataclass
class HotelRoom:
    """Hotel room data structure"""
    room_id: str
    room_type: str
    description: str
    max_occupancy: int
    price_per_night: float
    total_price: float
    currency: str
    amenities: List[str]
    cancellation_policy: str
    availability: int

@dataclass
class Hotel:
    """Hotel data structure"""
    hotel_id: str
    name: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    star_rating: int
    guest_rating: float
    distance_to_airport: float  # in km
    amenities: List[str]
    available_rooms: List[HotelRoom]
    contact_info: Dict[str, str]

@dataclass
class HotelBooking:
    """Hotel booking data structure"""
    booking_id: str
    hotel_id: str
    hotel_name: str
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in_date: datetime
    check_out_date: datetime
    room_type: str
    number_of_rooms: int
    number_of_guests: int
    total_price: float
    currency: str
    booking_status: str
    confirmation_number: str
    cancellation_policy: str
    created_at: datetime

class HotelAPIClient:
    """Hotel booking API client for passenger accommodation"""
    
    def __init__(self, config: ExternalAPIConfig):
        self.config = config
        self.provider = HotelProvider(config.hotel_provider)
        self.api_key = config.hotel_api_key
        self.base_url = config.hotel_api_url
        self.http_client: Optional[httpx.AsyncClient] = None
        self.rate_limits = {
            'requests_per_minute': 100,
            'current_requests': 0,
            'window_start': datetime.utcnow()
        }
        
    async def start(self):
        """Initialize hotel API client"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info(f"Hotel API client started with provider: {self.provider.value}")
    
    async def stop(self):
        """Close hotel API client"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Hotel API client stopped")
    
    async def search_hotels_near_airport(
        self,
        airport_code: str,
        check_in_date: datetime,
        check_out_date: datetime,
        guests: int = 1,
        rooms: int = 1,
        max_distance_km: float = 20.0,
        min_star_rating: int = 3
    ) -> List[Hotel]:
        """Search for hotels near airport"""
        try:
            # Rate limiting
            await self._check_rate_limit()
            
            # Demo mode - return mock hotels
            if self.config.demo_mode:
                return self._generate_mock_hotels(airport_code, check_in_date, check_out_date)
            
            if self.provider == HotelProvider.BOOKING_COM:
                return await self._search_booking_com_hotels(
                    airport_code, check_in_date, check_out_date, guests, rooms, max_distance_km, min_star_rating
                )
            elif self.provider == HotelProvider.EXPEDIA:
                return await self._search_expedia_hotels(
                    airport_code, check_in_date, check_out_date, guests, rooms, max_distance_km, min_star_rating
                )
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                return await self._search_amadeus_hotels(
                    airport_code, check_in_date, check_out_date, guests, rooms, max_distance_km, min_star_rating
                )
            else:
                raise ValueError(f"Unsupported hotel provider: {self.provider}")
                
        except Exception as e:
            logger.error("Hotel search error", airport_code=airport_code, error=str(e))
            return []
    
    async def get_hotel_details(self, hotel_id: str) -> Optional[Hotel]:
        """Get detailed hotel information"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock hotel details
            if self.config.demo_mode:
                return self._generate_mock_hotel_details(hotel_id)
            
            if self.provider == HotelProvider.BOOKING_COM:
                return await self._get_booking_com_details(hotel_id)
            elif self.provider == HotelProvider.EXPEDIA:
                return await self._get_expedia_details(hotel_id)
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                return await self._get_amadeus_hotel_details(hotel_id)
            else:
                raise ValueError(f"Unsupported hotel provider: {self.provider}")
                
        except Exception as e:
            logger.error("Hotel details error", hotel_id=hotel_id, error=str(e))
            return None
    
    async def create_hotel_booking(
        self,
        hotel_id: str,
        room_id: str,
        guest_data: Dict[str, Any],
        check_in_date: datetime,
        check_out_date: datetime,
        number_of_rooms: int = 1,
        special_requests: Optional[str] = None
    ) -> Optional[HotelBooking]:
        """Create hotel booking"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock booking
            if self.config.demo_mode:
                return self._generate_mock_booking(hotel_id, guest_data, check_in_date, check_out_date)
            
            if self.provider == HotelProvider.BOOKING_COM:
                return await self._create_booking_com_booking(
                    hotel_id, room_id, guest_data, check_in_date, check_out_date, number_of_rooms, special_requests
                )
            elif self.provider == HotelProvider.EXPEDIA:
                return await self._create_expedia_booking(
                    hotel_id, room_id, guest_data, check_in_date, check_out_date, number_of_rooms, special_requests
                )
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                return await self._create_amadeus_hotel_booking(
                    hotel_id, room_id, guest_data, check_in_date, check_out_date, number_of_rooms, special_requests
                )
            else:
                raise ValueError(f"Unsupported hotel provider: {self.provider}")
                
        except Exception as e:
            logger.error("Hotel booking error", hotel_id=hotel_id, error=str(e))
            return None
    
    async def cancel_hotel_booking(self, booking_id: str, reason: str = "") -> bool:
        """Cancel hotel booking"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - always succeed
            if self.config.demo_mode:
                logger.info(f"Mock hotel booking cancellation: {booking_id}")
                return True
            
            if self.provider == HotelProvider.BOOKING_COM:
                return await self._cancel_booking_com_booking(booking_id, reason)
            elif self.provider == HotelProvider.EXPEDIA:
                return await self._cancel_expedia_booking(booking_id, reason)
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                return await self._cancel_amadeus_hotel_booking(booking_id, reason)
            else:
                raise ValueError(f"Unsupported hotel provider: {self.provider}")
                
        except Exception as e:
            logger.error("Hotel cancellation error", booking_id=booking_id, error=str(e))
            return False
    
    async def get_booking_details(self, booking_id: str) -> Optional[HotelBooking]:
        """Get hotel booking details"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock booking details
            if self.config.demo_mode:
                return self._generate_mock_booking_details(booking_id)
            
            if self.provider == HotelProvider.BOOKING_COM:
                return await self._get_booking_com_booking(booking_id)
            elif self.provider == HotelProvider.EXPEDIA:
                return await self._get_expedia_booking(booking_id)
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                return await self._get_amadeus_hotel_booking(booking_id)
            else:
                raise ValueError(f"Unsupported hotel provider: {self.provider}")
                
        except Exception as e:
            logger.error("Booking details error", booking_id=booking_id, error=str(e))
            return None
    
    async def batch_hotel_bookings(
        self,
        booking_requests: List[Dict[str, Any]]
    ) -> Dict[str, Optional[HotelBooking]]:
        """Process multiple hotel booking requests"""
        try:
            results = {}
            
            # Process in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(booking_requests), batch_size):
                batch = booking_requests[i:i + batch_size]
                
                tasks = [
                    self._process_single_hotel_booking(request)
                    for request in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for request, result in zip(batch, batch_results):
                    guest_name = request.get('guest_data', {}).get('name', 'Unknown')
                    if isinstance(result, Exception):
                        logger.error(f"Hotel booking failed for guest {guest_name}", error=str(result))
                        results[guest_name] = None
                    else:
                        results[guest_name] = result
                
                # Delay between batches
                if i + batch_size < len(booking_requests):
                    await asyncio.sleep(2)
            
            logger.info(f"Batch hotel booking completed: {len(results)} requests processed")
            return results
            
        except Exception as e:
            logger.error("Batch hotel booking error", error=str(e))
            return {}
    
    async def find_emergency_accommodation(
        self,
        airport_code: str,
        passenger_count: int,
        tonight: bool = True
    ) -> List[Hotel]:
        """Find emergency accommodation for disrupted passengers"""
        try:
            check_in = datetime.now()
            if not tonight:
                check_in += timedelta(days=1)
            
            check_out = check_in + timedelta(days=1)
            
            # Search for available hotels with relaxed criteria for emergency
            hotels = await self.search_hotels_near_airport(
                airport_code=airport_code,
                check_in_date=check_in,
                check_out_date=check_out,
                guests=passenger_count,
                rooms=max(1, passenger_count // 2),  # Assuming 2 guests per room max
                max_distance_km=30.0,  # Extended distance for emergency
                min_star_rating=2  # Lower minimum rating for emergency
            )
            
            # Sort by availability and distance
            emergency_hotels = [
                hotel for hotel in hotels 
                if any(room.availability > 0 for room in hotel.available_rooms)
            ]
            
            emergency_hotels.sort(key=lambda h: (h.distance_to_airport, -h.guest_rating))
            
            logger.info(
                f"Found {len(emergency_hotels)} emergency accommodation options",
                airport=airport_code,
                passenger_count=passenger_count
            )
            
            return emergency_hotels[:10]  # Return top 10 options
            
        except Exception as e:
            logger.error("Emergency accommodation search error", error=str(e))
            return []
    
    async def _check_rate_limit(self):
        """Check and enforce rate limits"""
        current_time = datetime.utcnow()
        
        # Reset window if needed
        if (current_time - self.rate_limits['window_start']).seconds >= 60:
            self.rate_limits['current_requests'] = 0
            self.rate_limits['window_start'] = current_time
        
        # Check limit
        if self.rate_limits['current_requests'] >= self.rate_limits['requests_per_minute']:
            sleep_time = 60 - (current_time - self.rate_limits['window_start']).seconds
            await asyncio.sleep(sleep_time)
            self.rate_limits['current_requests'] = 0
            self.rate_limits['window_start'] = datetime.utcnow()
        
        self.rate_limits['current_requests'] += 1
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            if self.provider == HotelProvider.BOOKING_COM:
                headers['X-Booking-API-Key'] = self.api_key
            elif self.provider == HotelProvider.EXPEDIA:
                headers['Authorization'] = f'Bearer {self.api_key}'
            elif self.provider == HotelProvider.AMADEUS_HOTEL:
                headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    # Mock data generators for demo mode
    def _generate_mock_hotels(
        self, 
        airport_code: str, 
        check_in_date: datetime, 
        check_out_date: datetime
    ) -> List[Hotel]:
        """Generate mock hotel data"""
        import random
        
        airport_locations = {
            'LHR': {'lat': 51.4700, 'lon': -0.4543, 'city': 'London'},
            'CDG': {'lat': 49.0097, 'lon': 2.5479, 'city': 'Paris'},
            'FRA': {'lat': 50.0264, 'lon': 8.5431, 'city': 'Frankfurt'},
            'AMS': {'lat': 52.3105, 'lon': 4.7683, 'city': 'Amsterdam'},
            'MAD': {'lat': 40.4719, 'lon': -3.5626, 'city': 'Madrid'}
        }
        
        location = airport_locations.get(airport_code, {'lat': 51.0, 'lon': 0.0, 'city': 'Unknown'})
        
        hotels = []
        hotel_names = [
            f"{location['city']} Airport Hotel",
            f"Premier Inn {location['city']}",
            f"Holiday Inn {location['city']} Airport",
            f"Travelodge {location['city']}",
            f"Hilton {location['city']} Airport",
            f"Marriott {location['city']}",
            f"Ibis {location['city']} Airport",
            f"Novotel {location['city']}"
        ]
        
        for i, name in enumerate(hotel_names):
            # Generate rooms
            rooms = []
            room_types = ['Standard Double', 'Twin Room', 'Superior Room', 'Executive Room']
            
            for j, room_type in enumerate(room_types):
                if random.random() > 0.3:  # Some rooms may not be available
                    room = HotelRoom(
                        room_id=f"ROOM_{i}_{j}",
                        room_type=room_type,
                        description=f"{room_type} with modern amenities",
                        max_occupancy=2 if 'Twin' not in room_type else 2,
                        price_per_night=random.uniform(80, 300),
                        total_price=random.uniform(80, 300) * ((check_out_date - check_in_date).days),
                        currency='GBP' if airport_code == 'LHR' else 'EUR',
                        amenities=['WiFi', 'TV', 'Air Conditioning', 'Private Bathroom'],
                        cancellation_policy='Free cancellation until 6 PM',
                        availability=random.randint(0, 10)
                    )
                    rooms.append(room)
            
            hotel = Hotel(
                hotel_id=f"HOTEL_{airport_code}_{i}",
                name=name,
                address=f"{i+1} Airport Road, {location['city']}",
                city=location['city'],
                country='UK' if airport_code == 'LHR' else 'Europe',
                latitude=location['lat'] + random.uniform(-0.1, 0.1),
                longitude=location['lon'] + random.uniform(-0.1, 0.1),
                star_rating=random.randint(2, 5),
                guest_rating=random.uniform(6.0, 9.5),
                distance_to_airport=random.uniform(1.0, 15.0),
                amenities=['Free WiFi', '24-hour Reception', 'Restaurant', 'Bar', 'Airport Shuttle'],
                available_rooms=rooms,
                contact_info={
                    'phone': '+44123456789' if airport_code == 'LHR' else '+33123456789',
                    'email': f'reservations@{name.lower().replace(" ", "")}.com'
                }
            )
            hotels.append(hotel)
        
        return sorted(hotels, key=lambda h: h.distance_to_airport)
    
    def _generate_mock_hotel_details(self, hotel_id: str) -> Hotel:
        """Generate mock hotel details"""
        return self._generate_mock_hotels('LHR', datetime.now(), datetime.now() + timedelta(days=1))[0]
    
    def _generate_mock_booking(
        self,
        hotel_id: str,
        guest_data: Dict[str, Any],
        check_in_date: datetime,
        check_out_date: datetime
    ) -> HotelBooking:
        """Generate mock hotel booking"""
        import random
        
        return HotelBooking(
            booking_id=f"HB_{random.randint(100000, 999999)}",
            hotel_id=hotel_id,
            hotel_name="Airport Hotel London",
            guest_name=guest_data.get('name', 'John Doe'),
            guest_email=guest_data.get('email', 'john.doe@example.com'),
            guest_phone=guest_data.get('phone', '+447700123456'),
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            room_type="Standard Double",
            number_of_rooms=1,
            number_of_guests=guest_data.get('guests', 1),
            total_price=random.uniform(100, 300),
            currency='GBP',
            booking_status='confirmed',
            confirmation_number=f"CONF_{random.randint(1000, 9999)}",
            cancellation_policy='Free cancellation until 6 PM',
            created_at=datetime.utcnow()
        )
    
    def _generate_mock_booking_details(self, booking_id: str) -> HotelBooking:
        """Generate mock booking details"""
        return self._generate_mock_booking(
            'HOTEL_123',
            {'name': 'John Doe', 'email': 'john@example.com'},
            datetime.now(),
            datetime.now() + timedelta(days=1)
        )
    
    async def _process_single_hotel_booking(self, request: Dict[str, Any]) -> Optional[HotelBooking]:
        """Process single hotel booking request"""
        try:
            return await self.create_hotel_booking(
                hotel_id=request.get('hotel_id'),
                room_id=request.get('room_id'),
                guest_data=request.get('guest_data'),
                check_in_date=request.get('check_in_date'),
                check_out_date=request.get('check_out_date'),
                number_of_rooms=request.get('number_of_rooms', 1),
                special_requests=request.get('special_requests')
            )
        except Exception as e:
            logger.error("Single hotel booking error", error=str(e))
            return None
    
    # Provider-specific implementations (simplified)
    async def _search_booking_com_hotels(self, airport_code: str, check_in_date: datetime, check_out_date: datetime, guests: int, rooms: int, max_distance_km: float, min_star_rating: int) -> List[Hotel]:
        return self._generate_mock_hotels(airport_code, check_in_date, check_out_date)
    
    async def _search_expedia_hotels(self, airport_code: str, check_in_date: datetime, check_out_date: datetime, guests: int, rooms: int, max_distance_km: float, min_star_rating: int) -> List[Hotel]:
        return self._generate_mock_hotels(airport_code, check_in_date, check_out_date)
    
    async def _search_amadeus_hotels(self, airport_code: str, check_in_date: datetime, check_out_date: datetime, guests: int, rooms: int, max_distance_km: float, min_star_rating: int) -> List[Hotel]:
        return self._generate_mock_hotels(airport_code, check_in_date, check_out_date)
    
    # Additional provider-specific method stubs
    async def _get_booking_com_details(self, hotel_id: str) -> Optional[Hotel]:
        return self._generate_mock_hotel_details(hotel_id)
    
    async def _get_expedia_details(self, hotel_id: str) -> Optional[Hotel]:
        return self._generate_mock_hotel_details(hotel_id)
    
    async def _get_amadeus_hotel_details(self, hotel_id: str) -> Optional[Hotel]:
        return self._generate_mock_hotel_details(hotel_id)
    
    async def _create_booking_com_booking(self, hotel_id: str, room_id: str, guest_data: Dict[str, Any], check_in_date: datetime, check_out_date: datetime, number_of_rooms: int, special_requests: Optional[str]) -> Optional[HotelBooking]:
        return self._generate_mock_booking(hotel_id, guest_data, check_in_date, check_out_date)
    
    async def _create_expedia_booking(self, hotel_id: str, room_id: str, guest_data: Dict[str, Any], check_in_date: datetime, check_out_date: datetime, number_of_rooms: int, special_requests: Optional[str]) -> Optional[HotelBooking]:
        return self._generate_mock_booking(hotel_id, guest_data, check_in_date, check_out_date)
    
    async def _create_amadeus_hotel_booking(self, hotel_id: str, room_id: str, guest_data: Dict[str, Any], check_in_date: datetime, check_out_date: datetime, number_of_rooms: int, special_requests: Optional[str]) -> Optional[HotelBooking]:
        return self._generate_mock_booking(hotel_id, guest_data, check_in_date, check_out_date)
    
    async def _cancel_booking_com_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _cancel_expedia_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _cancel_amadeus_hotel_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _get_booking_com_booking(self, booking_id: str) -> Optional[HotelBooking]:
        return self._generate_mock_booking_details(booking_id)
    
    async def _get_expedia_booking(self, booking_id: str) -> Optional[HotelBooking]:
        return self._generate_mock_booking_details(booking_id)
    
    async def _get_amadeus_hotel_booking(self, booking_id: str) -> Optional[HotelBooking]:
        return self._generate_mock_booking_details(booking_id)
    
    async def health_check(self) -> bool:
        """Check if hotel API is accessible"""
        try:
            if self.config.demo_mode:
                return True
            
            # Simple health check
            response = await self.http_client.get(
                f"{self.base_url}/health",
                headers=self._get_headers(),
                timeout=5.0
            )
            return response.status_code == 200
            
        except Exception:
            return False