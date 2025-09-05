import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog

logger = structlog.get_logger()

class Database:
    """Database interface for cost optimizer service"""
    
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
    
    async def store_optimization_result(self, optimization_data: Dict[str, Any]) -> str:
        """Store cost optimization result"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        optimization_id = optimization_data.get('optimization_id', str(uuid4()))
        
        query = """
        INSERT INTO cost_optimizations (
            id, disruption_id, total_cost, cost_breakdown, 
            passenger_count, estimated_savings, confidence_score,
            optimization_data, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            total_cost = EXCLUDED.total_cost,
            cost_breakdown = EXCLUDED.cost_breakdown,
            estimated_savings = EXCLUDED.estimated_savings,
            confidence_score = EXCLUDED.confidence_score,
            optimization_data = EXCLUDED.optimization_data
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    optimization_id,
                    optimization_data.get('disruption_id'),
                    optimization_data.get('total_cost', 0.0),
                    json.dumps(optimization_data.get('cost_breakdown', {})),
                    len(optimization_data.get('passenger_allocations', [])),
                    optimization_data.get('estimated_savings', 0.0),
                    optimization_data.get('confidence_score', 0.5),
                    json.dumps(optimization_data),
                    datetime.utcnow()
                )
                
                logger.info("Optimization result stored", optimization_id=optimization_id)
                return optimization_id
                
            except Exception as e:
                logger.error("Failed to store optimization result", error=str(e))
                raise
    
    async def get_optimization_result(self, optimization_id: str) -> Optional[Dict[str, Any]]:
        """Get optimization result by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT optimization_data, created_at
        FROM cost_optimizations
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, optimization_id)
                if row:
                    data = json.loads(row['optimization_data'])
                    data['created_at'] = row['created_at'].isoformat()
                    return data
                return None
                
            except Exception as e:
                logger.error("Failed to get optimization result", error=str(e))
                return None
    
    async def store_hotel_booking(self, passenger_id: str, booking_data: Dict[str, Any]):
        """Store hotel booking details"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO hotel_bookings (
            passenger_id, booking_reference, hotel_name, check_in_date,
            check_out_date, total_cost, booking_data, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    passenger_id,
                    booking_data.get('booking_reference'),
                    booking_data.get('hotel_name'),
                    booking_data.get('check_in_date'),
                    booking_data.get('check_out_date'),
                    booking_data.get('total_cost', 0.0),
                    json.dumps(booking_data),
                    'confirmed'
                )
                
                logger.info("Hotel booking stored", passenger_id=passenger_id)
                
            except Exception as e:
                logger.error("Failed to store hotel booking", error=str(e))
                raise
    
    async def store_transport_booking(self, passenger_id: str, booking_data: Dict[str, Any]):
        """Store transport booking details"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO transport_bookings (
            passenger_id, booking_reference, transport_type, pickup_location,
            destination, pickup_time, total_cost, booking_data, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    passenger_id,
                    booking_data.get('booking_reference'),
                    booking_data.get('transport_type'),
                    booking_data.get('pickup_location'),
                    booking_data.get('destination'),
                    booking_data.get('pickup_time'),
                    booking_data.get('total_cost', 0.0),
                    json.dumps(booking_data),
                    'confirmed'
                )
                
                logger.info("Transport booking stored", passenger_id=passenger_id)
                
            except Exception as e:
                logger.error("Failed to store transport booking", error=str(e))
                raise
    
    async def store_compensation_calculation(self, passenger_id: str, compensation_data: Dict[str, Any]):
        """Store compensation calculation"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO passenger_compensations (
            passenger_id, eu261_amount, additional_amount, meal_vouchers,
            total_amount, calculation_details, calculated_at, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    passenger_id,
                    compensation_data.get('eu261_compensation', 0.0),
                    compensation_data.get('additional_compensation', 0.0),
                    compensation_data.get('meal_vouchers', {}).get('total_value', 0.0),
                    compensation_data.get('total_compensation', 0.0),
                    json.dumps(compensation_data.get('calculation_details', {})),
                    datetime.utcnow(),
                    'calculated'
                )
                
                logger.info("Compensation calculation stored", passenger_id=passenger_id)
                
            except Exception as e:
                logger.error("Failed to store compensation calculation", error=str(e))
                raise
    
    async def get_disruption_passengers(self, disruption_id: str) -> List[Dict[str, Any]]:
        """Get passengers affected by a disruption"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT p.id, p.first_name, p.last_name, p.email, p.phone,
               p.mobility_assistance, p.dietary_requirements, p.loyalty_tier,
               p.passenger_preferences
        FROM passengers p
        JOIN bookings b ON p.id = b.passenger_id
        JOIN flights f ON b.flight_id = f.id
        JOIN disruptions d ON f.id = d.flight_id
        WHERE d.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, disruption_id)
                passengers = []
                
                for row in rows:
                    passenger = dict(row)
                    # Parse JSON preferences
                    if passenger.get('passenger_preferences'):
                        passenger['preferences'] = json.loads(passenger['passenger_preferences'])
                    else:
                        passenger['preferences'] = {}
                    passengers.append(passenger)
                
                return passengers
                
            except Exception as e:
                logger.error("Failed to get disruption passengers", error=str(e))
                return []
    
    async def get_disruption_cost_summary(self, disruption_id: str) -> Optional[Dict[str, Any]]:
        """Get cost summary for a disruption"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT 
            co.total_cost,
            co.cost_breakdown,
            co.estimated_savings,
            co.passenger_count,
            co.created_at,
            (SELECT COUNT(*) FROM hotel_bookings hb 
             JOIN passengers p ON hb.passenger_id = p.id::text
             JOIN bookings b ON p.id = b.passenger_id
             JOIN flights f ON b.flight_id = f.id
             JOIN disruptions d ON f.id = d.flight_id
             WHERE d.id = $1) as hotel_bookings_count,
            (SELECT COUNT(*) FROM transport_bookings tb 
             JOIN passengers p ON tb.passenger_id = p.id::text
             JOIN bookings b ON p.id = b.passenger_id
             JOIN flights f ON b.flight_id = f.id
             JOIN disruptions d ON f.id = d.flight_id
             WHERE d.id = $1) as transport_bookings_count,
            (SELECT SUM(total_amount) FROM passenger_compensations pc
             JOIN passengers p ON pc.passenger_id = p.id::text
             JOIN bookings b ON p.id = b.passenger_id
             JOIN flights f ON b.flight_id = f.id
             JOIN disruptions d ON f.id = d.flight_id
             WHERE d.id = $1) as total_compensation
        FROM cost_optimizations co
        WHERE co.disruption_id = $1
        ORDER BY co.created_at DESC
        LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, disruption_id)
                if row:
                    summary = dict(row)
                    summary['cost_breakdown'] = json.loads(summary['cost_breakdown'])
                    summary['created_at'] = summary['created_at'].isoformat()
                    return summary
                return None
                
            except Exception as e:
                logger.error("Failed to get cost summary", error=str(e))
                return None
    
    async def get_cost_savings_analytics(self) -> Dict[str, Any]:
        """Get cost savings analytics"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        queries = {
            "total_savings": """
                SELECT SUM(estimated_savings) as total_savings,
                       COUNT(*) as optimization_count
                FROM cost_optimizations
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """,
            "savings_by_disruption_type": """
                SELECT d.type, SUM(co.estimated_savings) as total_savings,
                       COUNT(*) as count
                FROM cost_optimizations co
                JOIN disruptions d ON co.disruption_id = d.id::text
                WHERE co.created_at >= NOW() - INTERVAL '30 days'
                GROUP BY d.type
            """,
            "cost_breakdown": """
                SELECT 
                    AVG((cost_breakdown->>'hotels')::float) as avg_hotel_cost,
                    AVG((cost_breakdown->>'transport')::float) as avg_transport_cost,
                    AVG((cost_breakdown->>'compensation')::float) as avg_compensation_cost,
                    AVG((cost_breakdown->>'meals')::float) as avg_meal_cost
                FROM cost_optimizations
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
        }
        
        analytics = {}
        
        async with self.pool.acquire() as conn:
            try:
                for key, query in queries.items():
                    if key == "savings_by_disruption_type":
                        rows = await conn.fetch(query)
                        analytics[key] = [dict(row) for row in rows]
                    else:
                        row = await conn.fetchrow(query)
                        analytics[key] = dict(row) if row else {}
                
                return analytics
                
            except Exception as e:
                logger.error("Failed to get analytics", error=str(e))
                return {}
    
    async def store_rebooking_costs(self, passenger_id: str, cost_data: Dict[str, Any]):
        """Store rebooking-related costs"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO rebooking_costs (
            passenger_id, fare_difference, change_fees, hotel_costs,
            transport_costs, meal_costs, total_cost, cost_details
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    passenger_id,
                    cost_data.get('fare_difference', 0.0),
                    cost_data.get('change_fees', 0.0),
                    cost_data.get('hotel_costs', 0.0),
                    cost_data.get('transport_costs', 0.0),
                    cost_data.get('meal_costs', 0.0),
                    cost_data.get('total_cost', 0.0),
                    json.dumps(cost_data)
                )
                
                logger.info("Rebooking costs stored", passenger_id=passenger_id)
                
            except Exception as e:
                logger.error("Failed to store rebooking costs", error=str(e))
                raise