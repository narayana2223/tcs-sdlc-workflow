import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from dataclasses import dataclass
from enum import Enum
from config import ExternalAPIConfig

logger = structlog.get_logger()

class TransportProvider(Enum):
    UBER = "uber"
    LYFT = "lyft"
    LOCAL_TAXI = "local_taxi"
    RENTAL_CAR = "rental_car"

class TransportType(Enum):
    TAXI = "taxi"
    RIDE_SHARE = "ride_share"
    SHUTTLE = "shuttle"
    RENTAL_CAR = "rental_car"
    PUBLIC_TRANSPORT = "public_transport"

@dataclass
class TransportOption:
    """Transport option data structure"""
    option_id: str
    provider: str
    transport_type: TransportType
    vehicle_type: str
    estimated_arrival_time: datetime
    estimated_journey_time: int  # minutes
    price_estimate: Dict[str, float]  # currency -> amount
    capacity: int
    description: str
    pickup_location: str
    dropoff_location: str
    booking_required: bool
    cancellation_policy: str
    driver_info: Optional[Dict[str, str]] = None

@dataclass
class TransportBooking:
    """Transport booking data structure"""
    booking_id: str
    provider: str
    transport_type: TransportType
    passenger_name: str
    passenger_phone: str
    pickup_location: str
    dropoff_location: str
    pickup_time: datetime
    estimated_arrival_time: datetime
    vehicle_info: Dict[str, str]
    driver_info: Dict[str, str]
    total_price: float
    currency: str
    booking_status: str
    confirmation_code: str
    created_at: datetime
    special_instructions: Optional[str] = None

class TransportAPIClient:
    """Ground transport API client for passenger transfers"""
    
    def __init__(self, config: ExternalAPIConfig):
        self.config = config
        self.provider = TransportProvider(config.transport_provider)
        self.api_key = config.transport_api_key
        self.base_url = config.transport_api_url
        self.http_client: Optional[httpx.AsyncClient] = None
        self.rate_limits = {
            'requests_per_minute': config.transport_rate_limit,
            'current_requests': 0,
            'window_start': datetime.utcnow()
        }
        
    async def start(self):
        """Initialize transport API client"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.transport_timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info(f"Transport API client started with provider: {self.provider.value}")
    
    async def stop(self):
        """Close transport API client"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Transport API client stopped")
    
    async def get_transport_options(
        self,
        pickup_location: str,
        dropoff_location: str,
        pickup_time: Optional[datetime] = None,
        passenger_count: int = 1,
        special_needs: Optional[List[str]] = None
    ) -> List[TransportOption]:
        """Get available transport options"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock options
            if self.config.demo_mode:
                return self._generate_mock_transport_options(
                    pickup_location, dropoff_location, pickup_time, passenger_count
                )
            
            if self.provider == TransportProvider.UBER:
                return await self._get_uber_options(
                    pickup_location, dropoff_location, pickup_time, passenger_count, special_needs
                )
            elif self.provider == TransportProvider.LYFT:
                return await self._get_lyft_options(
                    pickup_location, dropoff_location, pickup_time, passenger_count, special_needs
                )
            elif self.provider == TransportProvider.LOCAL_TAXI:
                return await self._get_local_taxi_options(
                    pickup_location, dropoff_location, pickup_time, passenger_count, special_needs
                )
            elif self.provider == TransportProvider.RENTAL_CAR:
                return await self._get_rental_car_options(
                    pickup_location, dropoff_location, pickup_time, passenger_count, special_needs
                )
            else:
                raise ValueError(f"Unsupported transport provider: {self.provider}")
                
        except Exception as e:
            logger.error("Transport options error", error=str(e))
            return []
    
    async def book_transport(
        self,
        option_id: str,
        passenger_data: Dict[str, Any],
        pickup_location: str,
        dropoff_location: str,
        pickup_time: datetime,
        special_instructions: Optional[str] = None
    ) -> Optional[TransportBooking]:
        """Book transport option"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock booking
            if self.config.demo_mode:
                return self._generate_mock_booking(
                    option_id, passenger_data, pickup_location, dropoff_location, pickup_time
                )
            
            if self.provider == TransportProvider.UBER:
                return await self._book_uber(
                    option_id, passenger_data, pickup_location, dropoff_location, pickup_time, special_instructions
                )
            elif self.provider == TransportProvider.LYFT:
                return await self._book_lyft(
                    option_id, passenger_data, pickup_location, dropoff_location, pickup_time, special_instructions
                )
            elif self.provider == TransportProvider.LOCAL_TAXI:
                return await self._book_local_taxi(
                    option_id, passenger_data, pickup_location, dropoff_location, pickup_time, special_instructions
                )
            elif self.provider == TransportProvider.RENTAL_CAR:
                return await self._book_rental_car(
                    option_id, passenger_data, pickup_location, dropoff_location, pickup_time, special_instructions
                )
            else:
                raise ValueError(f"Unsupported transport provider: {self.provider}")
                
        except Exception as e:
            logger.error("Transport booking error", error=str(e))
            return None
    
    async def cancel_transport_booking(self, booking_id: str, reason: str = "") -> bool:
        """Cancel transport booking"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - always succeed
            if self.config.demo_mode:
                logger.info(f"Mock transport booking cancellation: {booking_id}")
                return True
            
            if self.provider == TransportProvider.UBER:
                return await self._cancel_uber_booking(booking_id, reason)
            elif self.provider == TransportProvider.LYFT:
                return await self._cancel_lyft_booking(booking_id, reason)
            elif self.provider == TransportProvider.LOCAL_TAXI:
                return await self._cancel_local_taxi_booking(booking_id, reason)
            elif self.provider == TransportProvider.RENTAL_CAR:
                return await self._cancel_rental_car_booking(booking_id, reason)
            else:
                raise ValueError(f"Unsupported transport provider: {self.provider}")
                
        except Exception as e:
            logger.error("Transport cancellation error", booking_id=booking_id, error=str(e))
            return False
    
    async def get_booking_status(self, booking_id: str) -> Optional[TransportBooking]:
        """Get transport booking status"""
        try:
            await self._check_rate_limit()
            
            # Demo mode - return mock status
            if self.config.demo_mode:
                return self._generate_mock_booking_status(booking_id)
            
            if self.provider == TransportProvider.UBER:
                return await self._get_uber_booking_status(booking_id)
            elif self.provider == TransportProvider.LYFT:
                return await self._get_lyft_booking_status(booking_id)
            elif self.provider == TransportProvider.LOCAL_TAXI:
                return await self._get_local_taxi_booking_status(booking_id)
            elif self.provider == TransportProvider.RENTAL_CAR:
                return await self._get_rental_car_booking_status(booking_id)
            else:
                raise ValueError(f"Unsupported transport provider: {self.provider}")
                
        except Exception as e:
            logger.error("Transport status error", booking_id=booking_id, error=str(e))
            return None
    
    async def batch_transport_bookings(
        self,
        booking_requests: List[Dict[str, Any]]
    ) -> Dict[str, Optional[TransportBooking]]:
        """Process multiple transport booking requests"""
        try:
            results = {}
            
            # Process in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(booking_requests), batch_size):
                batch = booking_requests[i:i + batch_size]
                
                tasks = [
                    self._process_single_transport_booking(request)
                    for request in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for request, result in zip(batch, batch_results):
                    passenger_name = request.get('passenger_data', {}).get('name', 'Unknown')
                    if isinstance(result, Exception):
                        logger.error(f"Transport booking failed for {passenger_name}", error=str(result))
                        results[passenger_name] = None
                    else:
                        results[passenger_name] = result
                
                # Delay between batches
                if i + batch_size < len(booking_requests):
                    await asyncio.sleep(2)
            
            logger.info(f"Batch transport booking completed: {len(results)} requests processed")
            return results
            
        except Exception as e:
            logger.error("Batch transport booking error", error=str(e))
            return {}
    
    async def get_emergency_transport(
        self,
        pickup_location: str,
        dropoff_location: str,
        passenger_count: int,
        urgency_level: str = "high"
    ) -> List[TransportOption]:
        """Get emergency transport options for disrupted passengers"""
        try:
            # Get immediate transport options
            options = await self.get_transport_options(
                pickup_location=pickup_location,
                dropoff_location=dropoff_location,
                pickup_time=datetime.now(),
                passenger_count=passenger_count
            )
            
            # Filter for immediate availability and sort by arrival time
            emergency_options = [
                option for option in options 
                if (option.estimated_arrival_time - datetime.now()).total_seconds() <= 1800  # Within 30 minutes
            ]
            
            emergency_options.sort(key=lambda o: o.estimated_arrival_time)
            
            logger.info(
                f"Found {len(emergency_options)} emergency transport options",
                pickup=pickup_location,
                dropoff=dropoff_location,
                passenger_count=passenger_count
            )
            
            return emergency_options[:5]  # Return top 5 fastest options
            
        except Exception as e:
            logger.error("Emergency transport search error", error=str(e))
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
            if self.provider == TransportProvider.UBER:
                headers['Authorization'] = f'Bearer {self.api_key}'
            elif self.provider == TransportProvider.LYFT:
                headers['Authorization'] = f'Bearer {self.api_key}'
            else:
                headers['X-API-Key'] = self.api_key
        
        return headers
    
    # Mock data generators for demo mode
    def _generate_mock_transport_options(
        self,
        pickup_location: str,
        dropoff_location: str,
        pickup_time: Optional[datetime],
        passenger_count: int
    ) -> List[TransportOption]:
        """Generate mock transport options"""
        import random
        
        if not pickup_time:
            pickup_time = datetime.now()
        
        options = []
        
        # Generate different transport types
        transport_types = [
            {
                'type': TransportType.TAXI,
                'providers': ['Local Taxi', 'City Cabs', 'Airport Taxi'],
                'vehicles': ['Sedan', 'Estate Car', 'MPV'],
                'base_price': 25
            },
            {
                'type': TransportType.RIDE_SHARE,
                'providers': ['Uber', 'Lyft', 'Ola'],
                'vehicles': ['UberX', 'Lyft Standard', 'Comfort'],
                'base_price': 20
            },
            {
                'type': TransportType.SHUTTLE,
                'providers': ['Airport Shuttle', 'Hotel Shuttle'],
                'vehicles': ['Minibus', 'Coach'],
                'base_price': 15
            },
            {
                'type': TransportType.RENTAL_CAR,
                'providers': ['Hertz', 'Avis', 'Enterprise'],
                'vehicles': ['Economy Car', 'Compact Car', 'Mid-size Car'],
                'base_price': 45
            }
        ]
        
        for transport_type in transport_types:
            for i, provider in enumerate(transport_type['providers']):
                if random.random() > 0.3:  # Some options may not be available
                    arrival_delay = random.randint(5, 45)  # 5-45 minutes
                    journey_time = random.randint(20, 90)  # 20-90 minutes
                    
                    price_multiplier = 1.0
                    if passenger_count > 4:
                        price_multiplier = 1.5  # Larger vehicle needed
                    
                    option = TransportOption(
                        option_id=f"TRANS_{transport_type['type'].value}_{i}",
                        provider=provider,
                        transport_type=transport_type['type'],
                        vehicle_type=random.choice(transport_type['vehicles']),
                        estimated_arrival_time=pickup_time + timedelta(minutes=arrival_delay),
                        estimated_journey_time=journey_time,
                        price_estimate={
                            'GBP': transport_type['base_price'] * price_multiplier * random.uniform(0.8, 1.3),
                            'EUR': transport_type['base_price'] * price_multiplier * random.uniform(0.9, 1.4)
                        },
                        capacity=random.randint(4, 8) if transport_type['type'] == TransportType.SHUTTLE else min(4, passenger_count + 1),
                        description=f"{provider} {transport_type['vehicles'][i % len(transport_type['vehicles'])]}",
                        pickup_location=pickup_location,
                        dropoff_location=dropoff_location,
                        booking_required=transport_type['type'] in [TransportType.RENTAL_CAR, TransportType.SHUTTLE],
                        cancellation_policy='Free cancellation up to 1 hour before pickup'
                    )
                    options.append(option)
        
        return sorted(options, key=lambda o: o.estimated_arrival_time)
    
    def _generate_mock_booking(
        self,
        option_id: str,
        passenger_data: Dict[str, Any],
        pickup_location: str,
        dropoff_location: str,
        pickup_time: datetime
    ) -> TransportBooking:
        """Generate mock transport booking"""
        import random
        
        return TransportBooking(
            booking_id=f"TB_{random.randint(100000, 999999)}",
            provider="Mock Transport",
            transport_type=TransportType.TAXI,
            passenger_name=passenger_data.get('name', 'John Doe'),
            passenger_phone=passenger_data.get('phone', '+447700123456'),
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            pickup_time=pickup_time,
            estimated_arrival_time=pickup_time + timedelta(minutes=random.randint(15, 45)),
            vehicle_info={
                'make': random.choice(['Toyota', 'Mercedes', 'BMW', 'Ford']),
                'model': random.choice(['Prius', 'E-Class', '3 Series', 'Mondeo']),
                'color': random.choice(['Black', 'White', 'Silver', 'Blue']),
                'license_plate': f"L{random.randint(100, 999)} ABC"
            },
            driver_info={
                'name': random.choice(['David Smith', 'Sarah Jones', 'Michael Brown', 'Emma Wilson']),
                'phone': f"+4477{random.randint(10000000, 99999999)}",
                'rating': round(random.uniform(4.0, 5.0), 1)
            },
            total_price=random.uniform(20, 80),
            currency='GBP',
            booking_status='confirmed',
            confirmation_code=f"CONF_{random.randint(1000, 9999)}",
            created_at=datetime.utcnow()
        )
    
    def _generate_mock_booking_status(self, booking_id: str) -> TransportBooking:
        """Generate mock booking status"""
        return self._generate_mock_booking(
            'OPTION_123',
            {'name': 'John Doe', 'phone': '+447700123456'},
            'LHR Terminal 2',
            'Premier Inn London',
            datetime.now() + timedelta(minutes=30)
        )
    
    async def _process_single_transport_booking(self, request: Dict[str, Any]) -> Optional[TransportBooking]:
        """Process single transport booking request"""
        try:
            return await self.book_transport(
                option_id=request.get('option_id'),
                passenger_data=request.get('passenger_data'),
                pickup_location=request.get('pickup_location'),
                dropoff_location=request.get('dropoff_location'),
                pickup_time=request.get('pickup_time'),
                special_instructions=request.get('special_instructions')
            )
        except Exception as e:
            logger.error("Single transport booking error", error=str(e))
            return None
    
    # Provider-specific implementations (simplified)
    async def _get_uber_options(self, pickup_location: str, dropoff_location: str, pickup_time: Optional[datetime], passenger_count: int, special_needs: Optional[List[str]]) -> List[TransportOption]:
        return self._generate_mock_transport_options(pickup_location, dropoff_location, pickup_time, passenger_count)
    
    async def _get_lyft_options(self, pickup_location: str, dropoff_location: str, pickup_time: Optional[datetime], passenger_count: int, special_needs: Optional[List[str]]) -> List[TransportOption]:
        return self._generate_mock_transport_options(pickup_location, dropoff_location, pickup_time, passenger_count)
    
    async def _get_local_taxi_options(self, pickup_location: str, dropoff_location: str, pickup_time: Optional[datetime], passenger_count: int, special_needs: Optional[List[str]]) -> List[TransportOption]:
        return self._generate_mock_transport_options(pickup_location, dropoff_location, pickup_time, passenger_count)
    
    async def _get_rental_car_options(self, pickup_location: str, dropoff_location: str, pickup_time: Optional[datetime], passenger_count: int, special_needs: Optional[List[str]]) -> List[TransportOption]:
        return self._generate_mock_transport_options(pickup_location, dropoff_location, pickup_time, passenger_count)
    
    # Booking method stubs
    async def _book_uber(self, option_id: str, passenger_data: Dict[str, Any], pickup_location: str, dropoff_location: str, pickup_time: datetime, special_instructions: Optional[str]) -> Optional[TransportBooking]:
        return self._generate_mock_booking(option_id, passenger_data, pickup_location, dropoff_location, pickup_time)
    
    async def _book_lyft(self, option_id: str, passenger_data: Dict[str, Any], pickup_location: str, dropoff_location: str, pickup_time: datetime, special_instructions: Optional[str]) -> Optional[TransportBooking]:
        return self._generate_mock_booking(option_id, passenger_data, pickup_location, dropoff_location, pickup_time)
    
    async def _book_local_taxi(self, option_id: str, passenger_data: Dict[str, Any], pickup_location: str, dropoff_location: str, pickup_time: datetime, special_instructions: Optional[str]) -> Optional[TransportBooking]:
        return self._generate_mock_booking(option_id, passenger_data, pickup_location, dropoff_location, pickup_time)
    
    async def _book_rental_car(self, option_id: str, passenger_data: Dict[str, Any], pickup_location: str, dropoff_location: str, pickup_time: datetime, special_instructions: Optional[str]) -> Optional[TransportBooking]:
        return self._generate_mock_booking(option_id, passenger_data, pickup_location, dropoff_location, pickup_time)
    
    # Cancellation method stubs
    async def _cancel_uber_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _cancel_lyft_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _cancel_local_taxi_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    async def _cancel_rental_car_booking(self, booking_id: str, reason: str) -> bool:
        return True
    
    # Status method stubs
    async def _get_uber_booking_status(self, booking_id: str) -> Optional[TransportBooking]:
        return self._generate_mock_booking_status(booking_id)
    
    async def _get_lyft_booking_status(self, booking_id: str) -> Optional[TransportBooking]:
        return self._generate_mock_booking_status(booking_id)
    
    async def _get_local_taxi_booking_status(self, booking_id: str) -> Optional[TransportBooking]:
        return self._generate_mock_booking_status(booking_id)
    
    async def _get_rental_car_booking_status(self, booking_id: str) -> Optional[TransportBooking]:
        return self._generate_mock_booking_status(booking_id)
    
    async def health_check(self) -> bool:
        """Check if transport API is accessible"""
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