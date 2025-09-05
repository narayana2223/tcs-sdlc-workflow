import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog

logger = structlog.get_logger()

class Database:
    """Database interface for compliance service"""
    
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
    
    async def store_compliance_result(self, compliance_data: Dict[str, Any]) -> str:
        """Store compliance assessment result"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        compliance_id = compliance_data.get('compliance_id', str(uuid4()))
        
        query = """
        INSERT INTO compliance_assessments (
            id, passenger_id, flight_id, disruption_id, regulations_checked,
            compliance_status, eligible_compensation, total_compensation,
            compliance_reasons, required_actions, claim_deadline,
            assessment_data, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (id) DO UPDATE SET
            compliance_status = EXCLUDED.compliance_status,
            eligible_compensation = EXCLUDED.eligible_compensation,
            total_compensation = EXCLUDED.total_compensation,
            assessment_data = EXCLUDED.assessment_data
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval(
                    query,
                    compliance_id,
                    compliance_data.get('passenger_id'),
                    compliance_data.get('flight_id'),
                    compliance_data.get('disruption_id'),
                    json.dumps(compliance_data.get('regulations_checked', [])),
                    json.dumps(compliance_data.get('compliance_status', {})),
                    json.dumps(compliance_data.get('eligible_compensation', {})),
                    compliance_data.get('total_compensation', 0.0),
                    json.dumps(compliance_data.get('compliance_reasons', [])),
                    json.dumps(compliance_data.get('required_actions', [])),
                    compliance_data.get('claim_deadline'),
                    json.dumps(compliance_data),
                    datetime.utcnow()
                )
                
                logger.info("Compliance result stored", compliance_id=result)
                return result
                
            except Exception as e:
                logger.error("Failed to store compliance result", error=str(e))
                raise
    
    async def get_compliance_result_by_flight_passenger(
        self, 
        flight_id: str, 
        passenger_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get compliance result for specific flight and passenger"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT assessment_data, created_at
        FROM compliance_assessments
        WHERE flight_id = $1 AND passenger_id = $2
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id, passenger_id)
                if row:
                    data = json.loads(row['assessment_data'])
                    data['created_at'] = row['created_at'].isoformat()
                    return data
                return None
                
            except Exception as e:
                logger.error("Failed to get compliance result", error=str(e))
                return None
    
    async def store_compensation_claim(self, claim_data: Dict[str, Any]) -> str:
        """Store compensation claim"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        claim_id = claim_data.get('claim_id', str(uuid4()))
        
        query = """
        INSERT INTO compensation_claims (
            id, passenger_id, flight_id, regulation_type, compensation_amount,
            claim_status, claim_reasons, supporting_documents, claim_deadline,
            submitted_at, processed_at, claim_data
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval(
                    query,
                    claim_id,
                    claim_data.get('passenger_id'),
                    claim_data.get('flight_id'),
                    claim_data.get('regulation_type'),
                    claim_data.get('compensation_amount', 0.0),
                    claim_data.get('claim_status'),
                    json.dumps(claim_data.get('claim_reasons', [])),
                    json.dumps(claim_data.get('supporting_documents', [])),
                    claim_data.get('claim_deadline'),
                    claim_data.get('submitted_at'),
                    claim_data.get('processed_at'),
                    json.dumps(claim_data)
                )
                
                logger.info("Compensation claim stored", claim_id=result)
                return result
                
            except Exception as e:
                logger.error("Failed to store compensation claim", error=str(e))
                raise
    
    async def get_compensation_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get compensation claim by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT claim_data, submitted_at, processed_at
        FROM compensation_claims
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, claim_id)
                if row:
                    data = json.loads(row['claim_data'])
                    data['submitted_at'] = row['submitted_at'].isoformat()
                    if row['processed_at']:
                        data['processed_at'] = row['processed_at'].isoformat()
                    return data
                return None
                
            except Exception as e:
                logger.error("Failed to get compensation claim", error=str(e))
                return None
    
    async def update_claim_status(
        self, 
        claim_id: str, 
        new_status: str, 
        processing_notes: Optional[str] = None
    ):
        """Update claim status"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        UPDATE compensation_claims 
        SET claim_status = $2, processed_at = $3, processing_notes = $4
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    claim_id,
                    new_status,
                    datetime.utcnow(),
                    processing_notes
                )
                
                logger.info("Claim status updated", claim_id=claim_id, status=new_status)
                
            except Exception as e:
                logger.error("Failed to update claim status", error=str(e))
                raise
    
    async def store_claim_dispute(self, dispute_data: Dict[str, Any]) -> str:
        """Store claim dispute"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        dispute_id = dispute_data.get('dispute_id', str(uuid4()))
        
        query = """
        INSERT INTO claim_disputes (
            id, claim_id, passenger_id, dispute_reason, supporting_evidence,
            dispute_status, submitted_at, dispute_data
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchval(
                    query,
                    dispute_id,
                    dispute_data.get('claim_id'),
                    dispute_data.get('passenger_id'),
                    dispute_data.get('dispute_reason'),
                    json.dumps(dispute_data.get('supporting_evidence', [])),
                    dispute_data.get('dispute_status'),
                    dispute_data.get('submitted_at'),
                    json.dumps(dispute_data)
                )
                
                logger.info("Claim dispute stored", dispute_id=result)
                return result
                
            except Exception as e:
                logger.error("Failed to store claim dispute", error=str(e))
                raise
    
    async def get_flight_passengers(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all passengers for a flight"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT p.id, p.pnr, p.first_name, p.last_name, p.email, p.phone,
               p.nationality, p.mobility_assistance, b.booking_class, b.ticket_price
        FROM passengers p
        JOIN bookings b ON p.id = b.passenger_id
        WHERE b.flight_id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, flight_id)
                return [dict(row) for row in rows]
                
            except Exception as e:
                logger.error("Failed to get flight passengers", error=str(e))
                return []
    
    async def get_flight_info(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get flight information"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT f.id, f.flight_number, f.scheduled_departure, f.actual_departure,
               f.scheduled_arrival, f.actual_arrival, f.aircraft_id, f.status,
               da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               ac.aircraft_type, r.distance_km
        FROM flights f
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        LEFT JOIN routes r ON (r.departure_airport_id = da.id AND r.arrival_airport_id = aa.id)
        WHERE f.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id)
                if row:
                    return dict(row)
                return None
                
            except Exception as e:
                logger.error("Failed to get flight info", error=str(e))
                return None
    
    async def get_flight_disruption(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get disruption information for a flight"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT d.id, d.type, d.cause, d.severity, d.delay_minutes,
               d.weather_data, d.is_extraordinary_circumstance,
               d.reported_at, d.resolved_at
        FROM disruptions d
        WHERE d.flight_id = $1
        ORDER BY d.reported_at DESC
        LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id)
                if row:
                    data = dict(row)
                    if data.get('weather_data'):
                        data['weather_data'] = json.loads(data['weather_data'])
                    return data
                return None
                
            except Exception as e:
                logger.error("Failed to get flight disruption", error=str(e))
                return None
    
    async def get_compliance_analytics(self) -> Dict[str, Any]:
        """Get compliance analytics"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        queries = {
            "total_assessments": """
                SELECT COUNT(*) as total_assessments,
                       AVG(total_compensation) as avg_compensation,
                       SUM(total_compensation) as total_compensation_issued
                FROM compliance_assessments
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """,
            "claims_by_status": """
                SELECT claim_status, COUNT(*) as count,
                       SUM(compensation_amount) as total_amount
                FROM compensation_claims
                WHERE submitted_at >= NOW() - INTERVAL '30 days'
                GROUP BY claim_status
            """,
            "regulation_compliance": """
                SELECT 
                    (regulations_checked::text) as regulation,
                    COUNT(*) as assessment_count,
                    AVG(total_compensation) as avg_compensation
                FROM compliance_assessments
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY regulations_checked
            """,
            "processing_times": """
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (processed_at - submitted_at))/86400) as avg_processing_days,
                    MIN(EXTRACT(EPOCH FROM (processed_at - submitted_at))/86400) as min_processing_days,
                    MAX(EXTRACT(EPOCH FROM (processed_at - submitted_at))/86400) as max_processing_days
                FROM compensation_claims
                WHERE processed_at IS NOT NULL
                AND submitted_at >= NOW() - INTERVAL '30 days'
            """
        }
        
        analytics = {}
        
        async with self.pool.acquire() as conn:
            try:
                for key, query in queries.items():
                    if key in ["claims_by_status", "regulation_compliance"]:
                        rows = await conn.fetch(query)
                        analytics[key] = [dict(row) for row in rows]
                    else:
                        row = await conn.fetchrow(query)
                        analytics[key] = dict(row) if row else {}
                
                return analytics
                
            except Exception as e:
                logger.error("Failed to get compliance analytics", error=str(e))
                return {}
    
    async def update_compliance_with_rebooking(
        self, 
        compliance_id: str, 
        rebooking_data: Dict[str, Any]
    ):
        """Update compliance assessment with rebooking information"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        UPDATE compliance_assessments
        SET rebooking_data = $2, updated_at = $3
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    compliance_id,
                    json.dumps(rebooking_data),
                    datetime.utcnow()
                )
                
                logger.info("Compliance updated with rebooking", compliance_id=compliance_id)
                
            except Exception as e:
                logger.error("Failed to update compliance with rebooking", error=str(e))
                raise
    
    async def get_pending_claims(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending compensation claims"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT claim_data, submitted_at
        FROM compensation_claims
        WHERE claim_status = 'pending'
        ORDER BY submitted_at ASC
        LIMIT $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, limit)
                claims = []
                for row in rows:
                    data = json.loads(row['claim_data'])
                    data['submitted_at'] = row['submitted_at'].isoformat()
                    claims.append(data)
                return claims
                
            except Exception as e:
                logger.error("Failed to get pending claims", error=str(e))
                return []
    
    async def get_expired_claims(self) -> List[Dict[str, Any]]:
        """Get claims that have passed their deadline"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT claim_data, claim_deadline
        FROM compensation_claims
        WHERE claim_status = 'pending'
        AND claim_deadline < NOW()
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query)
                claims = []
                for row in rows:
                    data = json.loads(row['claim_data'])
                    data['claim_deadline'] = row['claim_deadline'].isoformat()
                    claims.append(data)
                return claims
                
            except Exception as e:
                logger.error("Failed to get expired claims", error=str(e))
                return []
    
    async def get_high_value_claims(self, threshold: float = 1000.0) -> List[Dict[str, Any]]:
        """Get high-value compensation claims requiring manual review"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT claim_data, compensation_amount
        FROM compensation_claims
        WHERE compensation_amount >= $1
        AND claim_status = 'pending'
        ORDER BY compensation_amount DESC
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, threshold)
                claims = []
                for row in rows:
                    data = json.loads(row['claim_data'])
                    data['compensation_amount'] = float(row['compensation_amount'])
                    claims.append(data)
                return claims
                
            except Exception as e:
                logger.error("Failed to get high value claims", error=str(e))
                return []