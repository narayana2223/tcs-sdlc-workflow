import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog

logger = structlog.get_logger()

class Database:
    """Database interface for passenger management service"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Connect to database"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")
    
    # Passenger operations
    async def create_passenger(self, passenger_data: Dict[str, Any]) -> UUID:
        """Create a new passenger"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO passengers (pnr, first_name, last_name, email, phone, nationality, 
                               passport_number, mobility_assistance, dietary_requirements)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                passenger_id = await conn.fetchval(
                    query,
                    passenger_data['pnr'],
                    passenger_data['first_name'],
                    passenger_data['last_name'],
                    passenger_data.get('email'),
                    passenger_data.get('phone'),
                    passenger_data.get('nationality'),
                    passenger_data.get('passport_number'),
                    passenger_data.get('mobility_assistance', False),
                    passenger_data.get('dietary_requirements')
                )
                
                logger.info("Passenger created", passenger_id=str(passenger_id), pnr=passenger_data['pnr'])
                return passenger_id
                
            except Exception as e:
                logger.error("Failed to create passenger", error=str(e))
                raise
    
    async def get_passenger(self, passenger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get passenger by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT * FROM passengers WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, passenger_id)
                return dict(row) if row else None
            except Exception as e:
                logger.error("Failed to get passenger", error=str(e))
                return None
    
    async def get_passenger_by_pnr(self, pnr: str) -> Optional[Dict[str, Any]]:
        """Get passenger by PNR"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT * FROM passengers WHERE pnr = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, pnr)
                return dict(row) if row else None
            except Exception as e:
                logger.error("Failed to get passenger by PNR", error=str(e))
                return None
    
    async def get_passenger_with_bookings(self, passenger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get passenger with all their bookings"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        passenger_query = """
        SELECT * FROM passengers WHERE id = $1
        """
        
        bookings_query = """
        SELECT b.*, f.flight_number, f.scheduled_departure, f.scheduled_arrival,
               f.status as flight_status, da.iata_code as departure_airport,
               aa.iata_code as arrival_airport
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        WHERE b.passenger_id = $1
        ORDER BY f.scheduled_departure DESC
        """
        
        async with self.pool.acquire() as conn:
            try:
                passenger_row = await conn.fetchrow(passenger_query, passenger_id)
                if not passenger_row:
                    return None
                
                booking_rows = await conn.fetch(bookings_query, passenger_id)
                
                passenger_data = dict(passenger_row)
                passenger_data['current_bookings'] = [dict(row) for row in booking_rows]
                
                return passenger_data
                
            except Exception as e:
                logger.error("Failed to get passenger with bookings", error=str(e))
                return None
    
    # Booking operations
    async def create_booking(self, booking_data: Dict[str, Any]) -> UUID:
        """Create a new booking"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO bookings (passenger_id, flight_id, seat_number, class, 
                             booking_reference, original_price)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                booking_id = await conn.fetchval(
                    query,
                    booking_data['passenger_id'],
                    booking_data['flight_id'],
                    booking_data.get('seat_number'),
                    booking_data['class_'],
                    booking_data['booking_reference'],
                    booking_data['original_price']
                )
                
                logger.info("Booking created", booking_id=str(booking_id))
                return booking_id
                
            except Exception as e:
                logger.error("Failed to create booking", error=str(e))
                raise
    
    async def get_booking_with_flight(self, booking_id: UUID) -> Optional[Dict[str, Any]]:
        """Get booking with flight details"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT b.*, f.flight_number, f.scheduled_departure, f.scheduled_arrival,
               f.status as flight_status, da.iata_code as departure_airport,
               aa.iata_code as arrival_airport, al.name as airline_name,
               ac.aircraft_type
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN airlines al ON f.airline_id = al.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        WHERE b.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, booking_id)
                if not row:
                    return None
                
                booking_data = dict(row)
                # Rename 'class' field for Pydantic compatibility
                booking_data['class_'] = booking_data.pop('class')
                
                # Add flight details as nested object
                booking_data['flight_details'] = {
                    'flight_number': booking_data['flight_number'],
                    'scheduled_departure': booking_data['scheduled_departure'],
                    'scheduled_arrival': booking_data['scheduled_arrival'],
                    'status': booking_data['flight_status'],
                    'departure_airport': booking_data['departure_airport'],
                    'arrival_airport': booking_data['arrival_airport'],
                    'airline_name': booking_data['airline_name'],
                    'aircraft_type': booking_data['aircraft_type']
                }
                
                return booking_data
                
            except Exception as e:
                logger.error("Failed to get booking with flight", error=str(e))
                return None
    
    async def update_booking_status(self, booking_id: UUID, status: str):
        """Update booking status"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        UPDATE bookings SET status = $2, updated_at = NOW()
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, booking_id, status)
                logger.info("Booking status updated", booking_id=str(booking_id), status=status)
            except Exception as e:
                logger.error("Failed to update booking status", error=str(e))
                raise
    
    async def get_active_booking_for_flight(
        self, 
        passenger_id: UUID, 
        flight_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get passenger's active booking for a specific flight"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT b.*, f.flight_number, f.scheduled_departure, f.scheduled_arrival
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        WHERE b.passenger_id = $1 AND b.flight_id = $2 AND b.status = 'active'
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, passenger_id, flight_id)
                if row:
                    booking_data = dict(row)
                    booking_data['class_'] = booking_data.pop('class')
                    return booking_data
                return None
            except Exception as e:
                logger.error("Failed to get active booking", error=str(e))
                return None
    
    # Flight operations
    async def get_flight(self, flight_id: UUID) -> Optional[Dict[str, Any]]:
        """Get flight by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT f.*, da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               al.name as airline_name, ac.aircraft_type
        FROM flights f
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN airlines al ON f.airline_id = al.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        WHERE f.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id)
                return dict(row) if row else None
            except Exception as e:
                logger.error("Failed to get flight", error=str(e))
                return None
    
    async def get_flight_passengers(self, flight_id: UUID) -> List[Dict[str, Any]]:
        """Get all passengers on a flight"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT p.*, b.booking_reference, b.seat_number, b.class, b.status as booking_status
        FROM passengers p
        JOIN bookings b ON p.id = b.passenger_id
        WHERE b.flight_id = $1 AND b.status = 'active'
        ORDER BY p.last_name, p.first_name
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, flight_id)
                passengers = []
                for row in rows:
                    passenger_data = dict(row)
                    passenger_data['current_bookings'] = [{
                        'booking_reference': passenger_data.pop('booking_reference'),
                        'seat_number': passenger_data.pop('seat_number'),
                        'class': passenger_data.pop('class'),
                        'status': passenger_data.pop('booking_status')
                    }]
                    passengers.append(passenger_data)
                return passengers
            except Exception as e:
                logger.error("Failed to get flight passengers", error=str(e))
                return []
    
    async def find_alternative_flights(
        self,
        departure_airport: str,
        arrival_airport: str,
        departure_time: datetime,
        class_preference: str = None,
        hours_window: int = 12
    ) -> List[Dict[str, Any]]:
        """Find alternative flights"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        # Search for flights within time window
        start_time = departure_time
        end_time = departure_time + timedelta(hours=hours_window)
        
        query = """
        SELECT f.*, da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               al.name as airline_name, ac.aircraft_type, ac.seat_capacity,
               COUNT(b.id) as booked_seats
        FROM flights f
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN airlines al ON f.airline_id = al.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        LEFT JOIN bookings b ON f.id = b.flight_id AND b.status = 'active'
        WHERE da.iata_code = $1 
          AND aa.iata_code = $2
          AND f.scheduled_departure BETWEEN $3 AND $4
          AND f.status IN ('scheduled', 'delayed')
        GROUP BY f.id, da.iata_code, aa.iata_code, al.name, ac.aircraft_type, ac.seat_capacity
        HAVING COUNT(b.id) < ac.seat_capacity
        ORDER BY f.scheduled_departure ASC
        LIMIT 10
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    query, 
                    departure_airport, 
                    arrival_airport, 
                    start_time, 
                    end_time
                )
                
                alternatives = []
                for row in rows:
                    flight_data = dict(row)
                    available_seats = flight_data['seat_capacity'] - flight_data['booked_seats']
                    
                    if available_seats > 0:
                        flight_data['available_seats'] = available_seats
                        alternatives.append(flight_data)
                
                return alternatives
                
            except Exception as e:
                logger.error("Failed to find alternative flights", error=str(e))
                return []
    
    # Rebooking operations
    async def create_rebooking(self, rebooking_data: Dict[str, Any]) -> UUID:
        """Create a new rebooking record"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO rebookings (original_booking_id, new_flight_id, passenger_id,
                              disruption_id, rebooking_reason, cost_difference, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                rebooking_id = await conn.fetchval(
                    query,
                    rebooking_data['original_booking_id'],
                    rebooking_data.get('new_flight_id'),
                    rebooking_data['passenger_id'],
                    rebooking_data['disruption_id'],
                    rebooking_data.get('rebooking_reason', ''),
                    rebooking_data.get('cost_difference', 0.0),
                    rebooking_data.get('created_by', 'system')
                )
                
                logger.info("Rebooking created", rebooking_id=str(rebooking_id))
                return rebooking_id
                
            except Exception as e:
                logger.error("Failed to create rebooking", error=str(e))
                raise
    
    async def get_rebooking(self, rebooking_id: UUID) -> Optional[Dict[str, Any]]:
        """Get rebooking by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT r.*, 
               ob.booking_reference as original_booking_reference,
               of.flight_number as original_flight_number,
               nf.flight_number as new_flight_number,
               p.first_name, p.last_name, p.email
        FROM rebookings r
        JOIN bookings ob ON r.original_booking_id = ob.id
        JOIN flights of ON ob.flight_id = of.id
        LEFT JOIN flights nf ON r.new_flight_id = nf.id
        JOIN passengers p ON r.passenger_id = p.id
        WHERE r.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, rebooking_id)
                if row:
                    rebooking_data = dict(row)
                    rebooking_data['rebooking_status'] = 'confirmed' if rebooking_data['new_flight_id'] else 'pending'
                    return rebooking_data
                return None
            except Exception as e:
                logger.error("Failed to get rebooking", error=str(e))
                return None
    
    # Disruption operations
    async def get_disruption(self, disruption_id: UUID) -> Optional[Dict[str, Any]]:
        """Get disruption by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT * FROM disruptions WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, disruption_id)
                return dict(row) if row else None
            except Exception as e:
                logger.error("Failed to get disruption", error=str(e))
                return None
    
    async def get_disruption_with_passengers(self, disruption_id: UUID) -> Optional[Dict[str, Any]]:
        """Get disruption with affected passengers"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        disruption_query = """
        SELECT d.*, f.flight_number, f.scheduled_departure
        FROM disruptions d
        JOIN flights f ON d.flight_id = f.id
        WHERE d.id = $1
        """
        
        passengers_query = """
        SELECT DISTINCT p.id, p.first_name, p.last_name, p.email, p.phone
        FROM passengers p
        JOIN bookings b ON p.id = b.passenger_id
        JOIN disruptions d ON b.flight_id = d.flight_id
        WHERE d.id = $1 AND b.status = 'active'
        """
        
        async with self.pool.acquire() as conn:
            try:
                disruption_row = await conn.fetchrow(disruption_query, disruption_id)
                if not disruption_row:
                    return None
                
                passenger_rows = await conn.fetch(passengers_query, disruption_id)
                
                disruption_data = dict(disruption_row)
                disruption_data['affected_passengers'] = [dict(row) for row in passenger_rows]
                
                return disruption_data
                
            except Exception as e:
                logger.error("Failed to get disruption with passengers", error=str(e))
                return None
    
    async def get_passenger_disruptions(self, passenger_id: UUID) -> List[Dict[str, Any]]:
        """Get all disruptions affecting a passenger"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT DISTINCT d.*, f.flight_number, f.scheduled_departure,
               b.booking_reference
        FROM disruptions d
        JOIN flights f ON d.flight_id = f.id
        JOIN bookings b ON f.id = b.flight_id
        WHERE b.passenger_id = $1 AND b.status IN ('active', 'rebooked')
        ORDER BY d.confirmed_at DESC
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, passenger_id)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error("Failed to get passenger disruptions", error=str(e))
                return []