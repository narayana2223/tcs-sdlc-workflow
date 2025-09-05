import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import structlog

logger = structlog.get_logger()

class Database:
    """Database interface for disruption prediction service"""
    
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
    
    async def get_flight_data(self, flight_id: UUID) -> Optional[Dict[str, Any]]:
        """Get flight data by ID"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT f.id, f.flight_number, f.scheduled_departure, f.scheduled_arrival,
               f.status, da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               ac.aircraft_type, ac.registration, al.name as airline_name
        FROM flights f
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        JOIN airlines al ON f.airline_id = al.id
        WHERE f.id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id)
                if row:
                    return dict(row)
                return None
            except Exception as e:
                logger.error("Failed to get flight data", flight_id=str(flight_id), error=str(e))
                raise
    
    async def get_historical_disruptions(
        self, 
        departure_airport: str, 
        arrival_airport: str, 
        aircraft_type: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical disruption data for similar flights"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT d.type, d.severity, d.delay_minutes, d.cause_details, 
               f.scheduled_departure, f.flight_number
        FROM disruptions d
        JOIN flights f ON d.flight_id = f.id
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        WHERE da.iata_code = $1 
          AND aa.iata_code = $2
          AND ac.aircraft_type = $3
          AND f.scheduled_departure >= $4
        ORDER BY f.scheduled_departure DESC
        LIMIT 50
        """
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    query, 
                    departure_airport, 
                    arrival_airport, 
                    aircraft_type,
                    cutoff_date
                )
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error("Failed to get historical disruptions", error=str(e))
                return []
    
    async def store_prediction(self, flight_id: UUID, prediction: Dict[str, Any]):
        """Store prediction in database"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        # First, get or create a prediction model record
        model_query = """
        SELECT id FROM prediction_models 
        WHERE model_name = 'DisruptionAgent' AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        insert_prediction = """
        INSERT INTO disruption_predictions 
        (flight_id, model_id, predicted_disruption_type, confidence_score, 
         predicted_delay_minutes, prediction_horizon_hours, input_features)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        async with self.pool.acquire() as conn:
            try:
                # Get model ID
                model_row = await conn.fetchrow(model_query)
                if not model_row:
                    # Create a default model record
                    model_id = await conn.fetchval("""
                    INSERT INTO prediction_models 
                    (model_name, model_version, model_type, is_active, training_date)
                    VALUES ('DisruptionAgent', '1.0.0', 'operational', true, NOW())
                    RETURNING id
                    """)
                else:
                    model_id = model_row['id']
                
                # Insert prediction
                await conn.execute(
                    insert_prediction,
                    flight_id,
                    model_id,
                    prediction.get('predicted_disruption_type', 'none'),
                    prediction.get('confidence_score', 0.5),
                    prediction.get('predicted_delay_minutes', 0),
                    prediction.get('prediction_horizon_hours', 4),
                    json.dumps({
                        'reasoning': prediction.get('reasoning', ''),
                        'risk_factors': prediction.get('risk_factors', []),
                        'recommended_actions': prediction.get('recommended_actions', [])
                    })
                )
                
                logger.info("Prediction stored", flight_id=str(flight_id))
                
            except Exception as e:
                logger.error("Failed to store prediction", flight_id=str(flight_id), error=str(e))
                raise
    
    async def get_latest_prediction(self, flight_id: UUID) -> Optional[Dict[str, Any]]:
        """Get latest prediction for a flight"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT dp.*, pm.model_name, pm.model_version
        FROM disruption_predictions dp
        JOIN prediction_models pm ON dp.model_id = pm.id
        WHERE dp.flight_id = $1
        ORDER BY dp.predicted_at DESC
        LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, flight_id)
                if row:
                    result = dict(row)
                    # Parse JSON fields
                    if result.get('input_features'):
                        features = json.loads(result['input_features'])
                        result.update(features)
                    return result
                return None
            except Exception as e:
                logger.error("Failed to get prediction", flight_id=str(flight_id), error=str(e))
                return None
    
    async def get_high_risk_predictions(
        self, 
        hours_ahead: int = 4, 
        confidence_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get flights with high disruption risk"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT dp.*, f.flight_number, f.scheduled_departure,
               da.iata_code as departure_airport, aa.iata_code as arrival_airport
        FROM disruption_predictions dp
        JOIN flights f ON dp.flight_id = f.id
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        WHERE dp.confidence_score >= $1
          AND f.scheduled_departure BETWEEN NOW() AND NOW() + INTERVAL '%s hours'
          AND dp.predicted_disruption_type != 'none'
        ORDER BY dp.confidence_score DESC, f.scheduled_departure ASC
        """ % hours_ahead
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, confidence_threshold)
                results = []
                for row in rows:
                    result = dict(row)
                    if result.get('input_features'):
                        features = json.loads(result['input_features'])
                        result.update(features)
                    results.append(result)
                return results
            except Exception as e:
                logger.error("Failed to get high risk predictions", error=str(e))
                return []
    
    async def get_upcoming_flights(self, hours: int = 4) -> List[Dict[str, Any]]:
        """Get flights departing in the next N hours"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT f.id, f.flight_number, f.scheduled_departure, f.scheduled_arrival,
               da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               ac.aircraft_type
        FROM flights f
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        WHERE f.scheduled_departure BETWEEN NOW() AND NOW() + INTERVAL '%s hours'
          AND f.status IN ('scheduled', 'delayed')
        ORDER BY f.scheduled_departure ASC
        """ % hours
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error("Failed to get upcoming flights", error=str(e))
                return []
    
    async def get_training_data(self, days_back: int = 90) -> List[Dict[str, Any]]:
        """Get data for model training"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT f.*, d.type as disruption_type, d.severity, d.delay_minutes,
               d.weather_data, d.cause_details,
               da.iata_code as departure_airport, aa.iata_code as arrival_airport,
               ac.aircraft_type
        FROM flights f
        LEFT JOIN disruptions d ON f.id = d.flight_id
        JOIN airports da ON f.departure_airport_id = da.id
        JOIN airports aa ON f.arrival_airport_id = aa.id
        JOIN aircraft ac ON f.aircraft_id = ac.id
        WHERE f.scheduled_departure >= $1
        ORDER BY f.scheduled_departure DESC
        """
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, cutoff_date)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error("Failed to get training data", error=str(e))
                return []
    
    async def store_trained_model(self, model_data: Dict[str, Any]):
        """Store a trained ML model"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        INSERT INTO prediction_models 
        (model_name, model_version, model_type, accuracy_score, precision_score,
         recall_score, f1_score, training_date, model_config, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9)
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    query,
                    model_data.get('model_name'),
                    model_data.get('model_version'),
                    model_data.get('model_type'),
                    model_data.get('accuracy_score'),
                    model_data.get('precision_score'),
                    model_data.get('recall_score'),
                    model_data.get('f1_score'),
                    json.dumps(model_data.get('config', {})),
                    model_data.get('is_active', True)
                )
                
                logger.info("Model stored", model_name=model_data.get('model_name'))
                
            except Exception as e:
                logger.error("Failed to store model", error=str(e))
                raise
    
    async def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all active models"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        SELECT model_name, model_version, model_type, accuracy_score,
               precision_score, recall_score, f1_score, training_date
        FROM prediction_models
        WHERE is_active = true
        ORDER BY training_date DESC
        """
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query)
                models = [dict(row) for row in rows]
                
                # Get prediction accuracy over last 30 days
                accuracy_query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN was_accurate = true THEN 1 END) as accurate_predictions,
                    AVG(confidence_score) as avg_confidence
                FROM disruption_predictions 
                WHERE predicted_at >= NOW() - INTERVAL '30 days'
                  AND was_accurate IS NOT NULL
                """
                
                accuracy_row = await conn.fetchrow(accuracy_query)
                
                return {
                    "models": models,
                    "recent_performance": dict(accuracy_row) if accuracy_row else {},
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error("Failed to get model performance", error=str(e))
                return {"models": [], "recent_performance": {}}
    
    async def update_prediction_accuracy(self, prediction_id: UUID, was_accurate: bool):
        """Update whether a prediction was accurate after the fact"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        query = """
        UPDATE disruption_predictions 
        SET was_accurate = $2
        WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, prediction_id, was_accurate)
                logger.info(
                    "Prediction accuracy updated", 
                    prediction_id=str(prediction_id),
                    was_accurate=was_accurate
                )
            except Exception as e:
                logger.error("Failed to update prediction accuracy", error=str(e))