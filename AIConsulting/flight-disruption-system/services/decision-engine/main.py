"""
Real-time Decision Engine - Phase 3
Advanced intelligent decision-making system for complex airline operations

Features:
- Real-time decision making with sub-second response times
- Multi-criteria decision analysis (MCDA) algorithms
- Dynamic scenario adaptation and learning
- Complex event processing and pattern recognition
- Intelligent rule engine with fuzzy logic
- Risk assessment and uncertainty quantification
- Decision explainability and audit trails
- Adaptive thresholds and dynamic policies
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
import redis
import json
import uuid
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import httpx
import os
from collections import defaultdict, deque
import heapq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter('decision_requests_total', 'Total decision requests', ['method', 'decision_type'])
DECISION_TIME = Histogram('decision_processing_time_seconds', 'Decision processing time')
DECISION_QUALITY = Gauge('decision_quality_score', 'Quality of decisions made', ['decision_type'])
ACTIVE_SCENARIOS = Gauge('active_scenarios_count', 'Number of active scenarios')

# Enums
class DecisionType(str, Enum):
    DISRUPTION_RESPONSE = "disruption_response"
    RESOURCE_ALLOCATION = "resource_allocation"
    PASSENGER_REBOOKING = "passenger_rebooking"
    CREW_ASSIGNMENT = "crew_assignment"
    PRICING_ADJUSTMENT = "pricing_adjustment"
    MAINTENANCE_SCHEDULING = "maintenance_scheduling"
    STRATEGIC_PLANNING = "strategic_planning"

class Priority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class DecisionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

# Data Models
@dataclass
class DecisionContext:
    scenario_id: str
    timestamp: datetime
    decision_type: DecisionType
    priority: Priority
    urgency_factor: float  # 0-1 scale
    stakeholders: List[str]
    constraints: Dict[str, Any]
    objectives: Dict[str, float]
    available_data: Dict[str, Any]
    external_factors: Dict[str, Any]

@dataclass
class DecisionOption:
    option_id: str
    description: str
    estimated_cost: float
    estimated_benefit: float
    risk_level: RiskLevel
    implementation_time: float  # hours
    resource_requirements: Dict[str, Any]
    success_probability: float
    side_effects: List[str]
    regulatory_compliance: bool

@dataclass
class DecisionResult:
    decision_id: str
    selected_option: DecisionOption
    confidence_score: float
    reasoning: List[str]
    risk_assessment: Dict[str, Any]
    implementation_plan: List[Dict[str, Any]]
    monitoring_points: List[str]
    rollback_plan: Optional[Dict[str, Any]]
    quality_metrics: Dict[str, float]

class DecisionRequest(BaseModel):
    context: Dict[str, Any]
    decision_type: DecisionType
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)

class RealTimeScenario(BaseModel):
    scenario_id: str
    scenario_type: str
    description: str
    active_events: List[Dict[str, Any]]
    key_metrics: Dict[str, Any]
    decision_points: List[Dict[str, Any]]
    auto_decisions_enabled: bool = True

class DecisionEngineResponse(BaseModel):
    decision_id: str
    decision_type: DecisionType
    status: DecisionStatus
    selected_option: Optional[Dict[str, Any]] = None
    confidence: float
    reasoning: List[str]
    risk_level: RiskLevel
    estimated_impact: Dict[str, Any]
    implementation_steps: List[str]
    monitoring_required: bool
    decision_time: float

# Real-time Decision Engine
class RealTimeDecisionEngine:
    def __init__(self):
        self.active_scenarios = {}
        self.decision_history = deque(maxlen=10000)  # Keep last 10k decisions
        self.rule_engine = IntelligentRuleEngine()
        self.risk_assessor = RiskAssessmentEngine()
        self.mcda_analyzer = MCDAAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        
        # Initialize Redis for real-time data
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # WebSocket connections for real-time updates
        self.websocket_connections = set()
        
        # Database connection
        self.db_pool = None
        
        # Decision queues by priority
        self.decision_queues = {
            Priority.CRITICAL: asyncio.PriorityQueue(),
            Priority.HIGH: asyncio.PriorityQueue(),
            Priority.MEDIUM: asyncio.PriorityQueue(),
            Priority.LOW: asyncio.PriorityQueue()
        }
        
        # Start background processors
        self.processors_running = False
    
    async def initialize_db_pool(self):
        """Initialize database connection pool"""
        try:
            database_url = os.getenv('DATABASE_URL')
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def start_background_processors(self):
        """Start background decision processors"""
        if not self.processors_running:
            self.processors_running = True
            
            # Start decision processors for each priority level
            for priority in Priority:
                asyncio.create_task(self._process_decision_queue(priority))
            
            # Start scenario monitoring
            asyncio.create_task(self._monitor_active_scenarios())
            
            # Start pattern recognition
            asyncio.create_task(self._continuous_pattern_analysis())
            
            logger.info("Background processors started")
    
    async def _process_decision_queue(self, priority: Priority):
        """Process decisions for a specific priority level"""
        queue = self.decision_queues[priority]
        
        while self.processors_running:
            try:
                # Wait for decisions with timeout
                try:
                    _, decision_item = await asyncio.wait_for(queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process the decision
                await self._process_single_decision(decision_item)
                
                # Mark task as done
                queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing {priority.name} priority decisions: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_decision(self, decision_item: Dict[str, Any]):
        """Process a single decision request"""
        try:
            start_time = datetime.now()
            decision_id = decision_item['decision_id']
            context = DecisionContext(**decision_item['context'])
            
            # Generate decision options
            options = await self._generate_decision_options(context)
            
            # Analyze options using MCDA
            analysis_result = await self.mcda_analyzer.analyze_options(options, context)
            
            # Assess risks
            risk_assessment = await self.risk_assessor.assess_decision_risks(
                analysis_result['best_option'], context
            )
            
            # Create decision result
            decision_result = DecisionResult(
                decision_id=decision_id,
                selected_option=analysis_result['best_option'],
                confidence_score=analysis_result['confidence'],
                reasoning=analysis_result['reasoning'],
                risk_assessment=risk_assessment,
                implementation_plan=analysis_result['implementation_plan'],
                monitoring_points=analysis_result['monitoring_points'],
                rollback_plan=analysis_result.get('rollback_plan'),
                quality_metrics=analysis_result['quality_metrics']
            )
            
            # Store decision
            await self._store_decision(decision_result)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            DECISION_TIME.observe(processing_time)
            DECISION_QUALITY.labels(decision_type=context.decision_type.value).set(
                decision_result.confidence_score
            )
            
            # Notify WebSocket clients
            await self._broadcast_decision_update(decision_result)
            
            logger.info(f"Decision {decision_id} processed in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Error processing decision: {e}")
    
    async def _generate_decision_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate possible decision options based on context"""
        try:
            options = []
            
            if context.decision_type == DecisionType.DISRUPTION_RESPONSE:
                options = await self._generate_disruption_options(context)
            elif context.decision_type == DecisionType.PASSENGER_REBOOKING:
                options = await self._generate_rebooking_options(context)
            elif context.decision_type == DecisionType.CREW_ASSIGNMENT:
                options = await self._generate_crew_options(context)
            elif context.decision_type == DecisionType.PRICING_ADJUSTMENT:
                options = await self._generate_pricing_options(context)
            else:
                # Generate generic options
                options = await self._generate_generic_options(context)
            
            return options
            
        except Exception as e:
            logger.error(f"Error generating decision options: {e}")
            return []
    
    async def _generate_disruption_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate disruption response options"""
        options = []
        disruption_data = context.available_data.get('disruption', {})
        
        severity = disruption_data.get('severity', 'medium')
        affected_passengers = disruption_data.get('passenger_count', 150)
        
        # Option 1: Delay and wait
        if severity in ['low', 'medium']:
            options.append(DecisionOption(
                option_id="delay_wait",
                description="Delay flight and wait for conditions to improve",
                estimated_cost=2000 + (affected_passengers * 10),
                estimated_benefit=affected_passengers * 50,  # Passenger preference for same flight
                risk_level=RiskLevel.LOW if severity == 'low' else RiskLevel.MEDIUM,
                implementation_time=2.0,
                resource_requirements={'gates': 1, 'crew_overtime': 2},
                success_probability=0.8 if severity == 'low' else 0.6,
                side_effects=['passenger_inconvenience', 'slot_disruption'],
                regulatory_compliance=True
            ))
        
        # Option 2: Cancel and rebook
        options.append(DecisionOption(
            option_id="cancel_rebook",
            description="Cancel flight and rebook passengers on alternative flights",
            estimated_cost=10000 + (affected_passengers * 250),
            estimated_benefit=affected_passengers * 30,  # Passenger accommodation
            risk_level=RiskLevel.MEDIUM,
            implementation_time=1.0,
            resource_requirements={'rebooking_agents': 5, 'alternative_flights': affected_passengers // 50},
            success_probability=0.9,
            side_effects=['customer_satisfaction_impact', 'revenue_loss'],
            regulatory_compliance=True
        ))
        
        # Option 3: Aircraft substitution
        if context.available_data.get('alternative_aircraft'):
            options.append(DecisionOption(
                option_id="aircraft_substitution",
                description="Replace aircraft with available alternative",
                estimated_cost=15000,
                estimated_benefit=affected_passengers * 80,  # Maintain schedule
                risk_level=RiskLevel.MEDIUM,
                implementation_time=3.0,
                resource_requirements={'alternative_aircraft': 1, 'crew': 4},
                success_probability=0.75,
                side_effects=['crew_schedule_impact', 'maintenance_schedule_change'],
                regulatory_compliance=True
            ))
        
        return options
    
    async def _generate_rebooking_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate passenger rebooking options"""
        options = []
        passenger_data = context.available_data.get('passengers', {})
        
        passenger_count = passenger_data.get('count', 1)
        passenger_tier = passenger_data.get('tier', 'economy')
        
        # Option 1: Same-day rebooking
        options.append(DecisionOption(
            option_id="same_day_rebook",
            description="Rebook on same-day alternative flights",
            estimated_cost=passenger_count * 50,
            estimated_benefit=passenger_count * 100,
            risk_level=RiskLevel.LOW,
            implementation_time=0.5,
            resource_requirements={'available_seats': passenger_count},
            success_probability=0.85,
            side_effects=['minor_schedule_disruption'],
            regulatory_compliance=True
        ))
        
        # Option 2: Next-day rebooking with accommodation
        options.append(DecisionOption(
            option_id="next_day_rebook",
            description="Rebook for next day with hotel accommodation",
            estimated_cost=passenger_count * 200,
            estimated_benefit=passenger_count * 75,
            risk_level=RiskLevel.MEDIUM,
            implementation_time=2.0,
            resource_requirements={'hotel_rooms': passenger_count, 'meal_vouchers': passenger_count * 3},
            success_probability=0.95,
            side_effects=['extended_travel_time', 'accommodation_costs'],
            regulatory_compliance=True
        ))
        
        # Option 3: Route via hub
        options.append(DecisionOption(
            option_id="hub_routing",
            description="Route passengers via connecting hub airport",
            estimated_cost=passenger_count * 150,
            estimated_benefit=passenger_count * 80,
            risk_level=RiskLevel.MEDIUM,
            implementation_time=1.5,
            resource_requirements={'connecting_flights': 2},
            success_probability=0.8,
            side_effects=['extended_journey_time', 'connection_risk'],
            regulatory_compliance=True
        ))
        
        return options
    
    async def _generate_crew_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate crew assignment options"""
        options = []
        crew_data = context.available_data.get('crew_requirements', {})
        
        required_crew = crew_data.get('required_positions', [])
        available_crew = crew_data.get('available_crew', [])
        
        # Option 1: Use standby crew
        if available_crew:
            options.append(DecisionOption(
                option_id="standby_crew",
                description="Assign standby crew to cover requirements",
                estimated_cost=len(required_crew) * 500,
                estimated_benefit=10000,  # Flight operation value
                risk_level=RiskLevel.LOW,
                implementation_time=1.0,
                resource_requirements={'standby_crew': len(required_crew)},
                success_probability=0.9,
                side_effects=['crew_overtime_costs'],
                regulatory_compliance=True
            ))
        
        # Option 2: Crew repositioning
        options.append(DecisionOption(
            option_id="crew_reposition",
            description="Reposition crew from other bases",
            estimated_cost=len(required_crew) * 800,
            estimated_benefit=10000,
            risk_level=RiskLevel.MEDIUM,
            implementation_time=4.0,
            resource_requirements={'crew_transport': len(required_crew)},
            success_probability=0.8,
            side_effects=['crew_fatigue', 'schedule_disruption'],
            regulatory_compliance=True
        ))
        
        return options
    
    async def _generate_pricing_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate dynamic pricing options"""
        options = []
        pricing_data = context.available_data.get('pricing', {})
        
        current_demand = pricing_data.get('demand', 0.7)
        competitor_prices = pricing_data.get('competitor_average', 200)
        
        # Option 1: Competitive pricing
        options.append(DecisionOption(
            option_id="competitive_price",
            description="Match competitor pricing for market share",
            estimated_cost=0,  # No immediate cost
            estimated_benefit=current_demand * competitor_prices * 0.9,
            risk_level=RiskLevel.LOW,
            implementation_time=0.1,
            resource_requirements={},
            success_probability=0.85,
            side_effects=['lower_margins'],
            regulatory_compliance=True
        ))
        
        # Option 2: Premium pricing
        if current_demand > 0.8:
            options.append(DecisionOption(
                option_id="premium_price",
                description="Set premium pricing for high demand",
                estimated_cost=0,
                estimated_benefit=current_demand * competitor_prices * 1.3,
                risk_level=RiskLevel.MEDIUM,
                implementation_time=0.1,
                resource_requirements={},
                success_probability=0.7,
                side_effects=['demand_reduction_risk'],
                regulatory_compliance=True
            ))
        
        return options
    
    async def _generate_generic_options(self, context: DecisionContext) -> List[DecisionOption]:
        """Generate generic decision options"""
        return [
            DecisionOption(
                option_id="default_action",
                description="Apply standard operating procedure",
                estimated_cost=1000,
                estimated_benefit=5000,
                risk_level=RiskLevel.LOW,
                implementation_time=1.0,
                resource_requirements={},
                success_probability=0.8,
                side_effects=[],
                regulatory_compliance=True
            )
        ]
    
    async def _store_decision(self, decision: DecisionResult):
        """Store decision in database and cache"""
        try:
            # Store in database
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO decisions (
                            id, decision_type, selected_option, confidence_score,
                            risk_level, processing_time, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, 
                    decision.decision_id,
                    decision.selected_option.description,
                    json.dumps(asdict(decision.selected_option)),
                    decision.confidence_score,
                    decision.selected_option.risk_level.value,
                    0.1,  # placeholder
                    datetime.now()
                    )
            
            # Store in Redis for fast access
            decision_data = asdict(decision)
            await self.redis_client.setex(
                f"decision:{decision.decision_id}",
                3600,  # 1 hour TTL
                json.dumps(decision_data, default=str)
            )
            
            # Add to history
            self.decision_history.append(decision)
            
        except Exception as e:
            logger.error(f"Error storing decision: {e}")
    
    async def _broadcast_decision_update(self, decision: DecisionResult):
        """Broadcast decision updates to WebSocket clients"""
        if self.websocket_connections:
            message = {
                'type': 'decision_update',
                'decision_id': decision.decision_id,
                'status': 'completed',
                'confidence': decision.confidence_score,
                'risk_level': decision.selected_option.risk_level.value,
                'selected_option': decision.selected_option.description,
                'timestamp': datetime.now().isoformat()
            }
            
            disconnected = set()
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            self.websocket_connections -= disconnected
    
    async def _monitor_active_scenarios(self):
        """Monitor active scenarios and trigger decisions"""
        while self.processors_running:
            try:
                # Update active scenarios count
                ACTIVE_SCENARIOS.set(len(self.active_scenarios))
                
                # Check for scenarios needing decisions
                for scenario_id, scenario in self.active_scenarios.items():
                    if scenario.get('auto_decisions_enabled', True):
                        await self._check_scenario_decision_points(scenario_id, scenario)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring scenarios: {e}")
                await asyncio.sleep(30)
    
    async def _check_scenario_decision_points(self, scenario_id: str, scenario: Dict[str, Any]):
        """Check if scenario has reached decision points"""
        try:
            decision_points = scenario.get('decision_points', [])
            
            for point in decision_points:
                if not point.get('processed', False):
                    trigger_condition = point.get('trigger_condition')
                    
                    # Simple condition checking (can be expanded)
                    if self._evaluate_trigger_condition(trigger_condition, scenario):
                        # Create decision request
                        decision_request = {
                            'decision_id': str(uuid.uuid4()),
                            'context': {
                                'scenario_id': scenario_id,
                                'timestamp': datetime.now(),
                                'decision_type': point.get('decision_type', 'disruption_response'),
                                'priority': Priority.HIGH,
                                'urgency_factor': 0.8,
                                'stakeholders': ['operations', 'customer_service'],
                                'constraints': point.get('constraints', {}),
                                'objectives': point.get('objectives', {}),
                                'available_data': scenario.get('key_metrics', {}),
                                'external_factors': {}
                            }
                        }
                        
                        # Queue decision
                        priority = Priority(point.get('priority', Priority.HIGH))
                        await self.decision_queues[priority].put((0, decision_request))
                        
                        # Mark as processed
                        point['processed'] = True
                        
                        logger.info(f"Auto-generated decision for scenario {scenario_id}")
        
        except Exception as e:
            logger.error(f"Error checking decision points for scenario {scenario_id}: {e}")
    
    def _evaluate_trigger_condition(self, condition: str, scenario: Dict[str, Any]) -> bool:
        """Evaluate trigger condition for auto-decisions"""
        try:
            if not condition:
                return False
            
            # Simple condition evaluation (expand as needed)
            metrics = scenario.get('key_metrics', {})
            
            # Example conditions
            if 'delay > 60' in condition:
                return metrics.get('delay_minutes', 0) > 60
            elif 'passenger_count > 100' in condition:
                return metrics.get('affected_passengers', 0) > 100
            elif 'cost_impact > 50000' in condition:
                return metrics.get('estimated_cost', 0) > 50000
            
            return False
            
        except Exception:
            return False
    
    async def _continuous_pattern_analysis(self):
        """Continuously analyze patterns in decisions"""
        while self.processors_running:
            try:
                if len(self.decision_history) >= 10:
                    patterns = await self.pattern_recognizer.analyze_decision_patterns(
                        list(self.decision_history)[-50:]  # Last 50 decisions
                    )
                    
                    # Store patterns for future use
                    if patterns:
                        await self.redis_client.setex(
                            "decision_patterns",
                            1800,  # 30 minutes
                            json.dumps(patterns, default=str)
                        )
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in pattern analysis: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def make_decision(self, request: DecisionRequest) -> str:
        """Make a decision and return decision ID"""
        decision_id = str(uuid.uuid4())
        
        decision_item = {
            'decision_id': decision_id,
            'context': {
                'scenario_id': f"manual_{decision_id}",
                'timestamp': datetime.now(),
                'decision_type': request.decision_type,
                'priority': request.priority,
                'urgency_factor': 0.7,
                'stakeholders': ['operations'],
                'constraints': request.constraints,
                'objectives': {'primary': 1.0},
                'available_data': request.context,
                'external_factors': {}
            }
        }
        
        # Queue decision based on priority
        await self.decision_queues[request.priority].put((0, decision_item))
        
        REQUEST_COUNT.labels(method="POST", decision_type=request.decision_type.value).inc()
        
        return decision_id
    
    async def get_decision_status(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get decision status and result"""
        try:
            # Check Redis cache first
            cached_decision = await self.redis_client.get(f"decision:{decision_id}")
            if cached_decision:
                return json.loads(cached_decision)
            
            # Check database if not in cache
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM decisions WHERE id = $1", decision_id
                    )
                    if row:
                        return dict(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting decision status: {e}")
            return None

# Supporting Classes
class IntelligentRuleEngine:
    """Intelligent rule engine with fuzzy logic"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize decision rules"""
        return {
            'disruption_severity': {
                'low': {'delay_threshold': 30, 'cost_threshold': 5000},
                'medium': {'delay_threshold': 120, 'cost_threshold': 25000},
                'high': {'delay_threshold': 300, 'cost_threshold': 100000}
            },
            'passenger_priority': {
                'vip': {'weight': 3.0, 'compensation_multiplier': 2.0},
                'frequent_flyer': {'weight': 2.0, 'compensation_multiplier': 1.5},
                'regular': {'weight': 1.0, 'compensation_multiplier': 1.0}
            }
        }

class RiskAssessmentEngine:
    """Risk assessment and uncertainty quantification"""
    
    async def assess_decision_risks(self, option: DecisionOption, context: DecisionContext) -> Dict[str, Any]:
        """Assess risks for a decision option"""
        try:
            base_risk = self._calculate_base_risk(option)
            contextual_risk = self._calculate_contextual_risk(context)
            
            overall_risk = min(1.0, (base_risk + contextual_risk) / 2)
            
            return {
                'overall_risk_score': overall_risk,
                'base_risk': base_risk,
                'contextual_risk': contextual_risk,
                'risk_factors': self._identify_risk_factors(option, context),
                'mitigation_strategies': self._suggest_mitigation_strategies(option),
                'uncertainty_level': self._calculate_uncertainty(option, context)
            }
            
        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
            return {'overall_risk_score': 0.5, 'error': str(e)}
    
    def _calculate_base_risk(self, option: DecisionOption) -> float:
        """Calculate base risk from option properties"""
        risk_mapping = {
            RiskLevel.VERY_LOW: 0.1,
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.VERY_HIGH: 0.9
        }
        return risk_mapping.get(option.risk_level, 0.5)
    
    def _calculate_contextual_risk(self, context: DecisionContext) -> float:
        """Calculate risk based on context"""
        urgency_risk = context.urgency_factor * 0.3
        complexity_risk = len(context.constraints) / 10.0 * 0.2
        stakeholder_risk = len(context.stakeholders) / 5.0 * 0.1
        
        return min(1.0, urgency_risk + complexity_risk + stakeholder_risk)
    
    def _identify_risk_factors(self, option: DecisionOption, context: DecisionContext) -> List[str]:
        """Identify key risk factors"""
        factors = []
        
        if option.success_probability < 0.7:
            factors.append("Low success probability")
        
        if option.estimated_cost > 50000:
            factors.append("High financial impact")
        
        if context.urgency_factor > 0.8:
            factors.append("High urgency pressure")
        
        if len(option.side_effects) > 2:
            factors.append("Multiple side effects")
        
        return factors
    
    def _suggest_mitigation_strategies(self, option: DecisionOption) -> List[str]:
        """Suggest risk mitigation strategies"""
        strategies = []
        
        if option.success_probability < 0.8:
            strategies.append("Develop contingency plans")
        
        if option.estimated_cost > 25000:
            strategies.append("Implement cost monitoring")
        
        if option.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            strategies.append("Require senior approval")
        
        return strategies
    
    def _calculate_uncertainty(self, option: DecisionOption, context: DecisionContext) -> float:
        """Calculate decision uncertainty level"""
        data_completeness = len(context.available_data) / 10.0  # Assume 10 ideal data points
        return max(0.1, min(0.9, 1.0 - data_completeness))

class MCDAAnalyzer:
    """Multi-Criteria Decision Analysis"""
    
    async def analyze_options(self, options: List[DecisionOption], context: DecisionContext) -> Dict[str, Any]:
        """Analyze options using MCDA techniques"""
        if not options:
            return {'best_option': None, 'confidence': 0.0, 'reasoning': ['No options available']}
        
        # Score options using multiple criteria
        scored_options = []
        
        for option in options:
            score = self._calculate_option_score(option, context)
            scored_options.append((score, option))
        
        # Sort by score
        scored_options.sort(reverse=True, key=lambda x: x[0])
        
        best_option = scored_options[0][1]
        best_score = scored_options[0][0]
        
        # Calculate confidence based on score separation
        if len(scored_options) > 1:
            score_gap = best_score - scored_options[1][0]
            confidence = min(0.95, 0.5 + (score_gap / 2))
        else:
            confidence = 0.8
        
        reasoning = self._generate_reasoning(best_option, scored_options, context)
        
        return {
            'best_option': best_option,
            'confidence': confidence,
            'reasoning': reasoning,
            'all_scores': [(score, opt.option_id) for score, opt in scored_options],
            'implementation_plan': self._create_implementation_plan(best_option),
            'monitoring_points': self._create_monitoring_points(best_option),
            'quality_metrics': {'mcda_score': best_score, 'option_count': len(options)}
        }
    
    def _calculate_option_score(self, option: DecisionOption, context: DecisionContext) -> float:
        """Calculate weighted score for an option"""
        # Define weights (can be made configurable)
        weights = {
            'cost_efficiency': 0.25,
            'success_probability': 0.25,
            'implementation_speed': 0.15,
            'risk_level': 0.20,
            'benefit': 0.15
        }
        
        # Normalize scores (0-1 scale)
        cost_score = max(0, min(1, 1 - (option.estimated_cost / 100000)))  # Lower cost is better
        success_score = option.success_probability
        speed_score = max(0, min(1, 1 - (option.implementation_time / 24)))  # Faster is better
        
        # Risk score (inverse of risk level)
        risk_mapping = {
            RiskLevel.VERY_LOW: 1.0,
            RiskLevel.LOW: 0.8,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.HIGH: 0.4,
            RiskLevel.VERY_HIGH: 0.2
        }
        risk_score = risk_mapping.get(option.risk_level, 0.5)
        
        benefit_score = max(0, min(1, option.estimated_benefit / 50000))
        
        # Calculate weighted sum
        total_score = (
            weights['cost_efficiency'] * cost_score +
            weights['success_probability'] * success_score +
            weights['implementation_speed'] * speed_score +
            weights['risk_level'] * risk_score +
            weights['benefit'] * benefit_score
        )
        
        return total_score
    
    def _generate_reasoning(self, best_option: DecisionOption, all_options: List[Tuple[float, DecisionOption]], 
                          context: DecisionContext) -> List[str]:
        """Generate reasoning for the decision"""
        reasoning = [
            f"Selected '{best_option.description}' with score {all_options[0][0]:.3f}",
            f"Success probability: {best_option.success_probability:.1%}",
            f"Risk level: {best_option.risk_level.value}",
            f"Estimated cost: £{best_option.estimated_cost:,.0f}",
            f"Implementation time: {best_option.implementation_time:.1f} hours"
        ]
        
        if len(all_options) > 1:
            second_best = all_options[1][1]
            reasoning.append(f"Next best option was '{second_best.description}' with score {all_options[1][0]:.3f}")
        
        return reasoning
    
    def _create_implementation_plan(self, option: DecisionOption) -> List[Dict[str, Any]]:
        """Create implementation plan for selected option"""
        plan = [
            {
                'step': 1,
                'description': 'Prepare resources and approvals',
                'estimated_time': 0.5,
                'dependencies': []
            },
            {
                'step': 2,
                'description': f'Execute: {option.description}',
                'estimated_time': option.implementation_time,
                'dependencies': [1]
            },
            {
                'step': 3,
                'description': 'Monitor implementation and measure success',
                'estimated_time': 1.0,
                'dependencies': [2]
            }
        ]
        
        return plan
    
    def _create_monitoring_points(self, option: DecisionOption) -> List[str]:
        """Create monitoring points for decision"""
        points = [
            'Implementation progress tracking',
            'Cost monitoring against estimates',
            'Success probability validation'
        ]
        
        if option.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            points.append('Risk indicator monitoring')
        
        if option.side_effects:
            points.append('Side effect monitoring')
        
        return points

class PatternRecognizer:
    """Pattern recognition for decision optimization"""
    
    async def analyze_decision_patterns(self, decisions: List[DecisionResult]) -> Dict[str, Any]:
        """Analyze patterns in historical decisions"""
        patterns = {
            'success_patterns': [],
            'failure_patterns': [],
            'cost_trends': {},
            'timing_patterns': {},
            'recommendations': []
        }
        
        if len(decisions) < 5:
            return patterns
        
        # Analyze success/failure patterns
        successful_decisions = [d for d in decisions if d.confidence_score > 0.8]
        
        if successful_decisions:
            patterns['success_patterns'] = [
                'High confidence decisions have better outcomes',
                f'{len(successful_decisions)}/{len(decisions)} decisions had high confidence'
            ]
        
        # Analyze cost patterns
        costs = [d.selected_option.estimated_cost for d in decisions]
        avg_cost = sum(costs) / len(costs)
        patterns['cost_trends']['average_cost'] = avg_cost
        patterns['cost_trends']['cost_range'] = [min(costs), max(costs)]
        
        return patterns

# Initialize Decision Engine
decision_engine = RealTimeDecisionEngine()

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await decision_engine.initialize_db_pool()
    await decision_engine.start_background_processors()
    logger.info("Real-time Decision Engine started")
    yield
    # Shutdown
    decision_engine.processors_running = False
    await decision_engine.close_db_pool()
    logger.info("Real-time Decision Engine stopped")

# Create FastAPI app
app = FastAPI(
    title="Real-time Decision Engine",
    description="Advanced intelligent decision-making system for complex airline operations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "decision-engine",
        "active_scenarios": len(decision_engine.active_scenarios),
        "decision_history_size": len(decision_engine.decision_history),
        "processors_running": decision_engine.processors_running,
        "database_connected": decision_engine.db_pool is not None
    }

@app.post("/decision/request")
async def request_decision(request: DecisionRequest) -> Dict[str, Any]:
    """Request a new decision"""
    decision_id = await decision_engine.make_decision(request)
    
    return {
        "decision_id": decision_id,
        "status": "queued",
        "estimated_processing_time": "5-30 seconds",
        "priority": request.priority.name
    }

@app.get("/decision/{decision_id}")
async def get_decision_result(decision_id: str) -> Dict[str, Any]:
    """Get decision result"""
    result = await decision_engine.get_decision_status(decision_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return result

@app.post("/scenario/register")
async def register_scenario(scenario: RealTimeScenario) -> Dict[str, str]:
    """Register a real-time scenario"""
    decision_engine.active_scenarios[scenario.scenario_id] = scenario.dict()
    
    return {
        "status": "registered",
        "scenario_id": scenario.scenario_id,
        "auto_decisions": scenario.auto_decisions_enabled
    }

@app.delete("/scenario/{scenario_id}")
async def unregister_scenario(scenario_id: str) -> Dict[str, str]:
    """Unregister a scenario"""
    if scenario_id in decision_engine.active_scenarios:
        del decision_engine.active_scenarios[scenario_id]
        return {"status": "unregistered", "scenario_id": scenario_id}
    else:
        raise HTTPException(status_code=404, detail="Scenario not found")

@app.get("/scenarios/active")
async def get_active_scenarios() -> Dict[str, Any]:
    """Get all active scenarios"""
    return {
        "active_scenarios": decision_engine.active_scenarios,
        "count": len(decision_engine.active_scenarios)
    }

@app.websocket("/ws/decisions")
async def websocket_decisions(websocket: WebSocket):
    """WebSocket endpoint for real-time decision updates"""
    await websocket.accept()
    decision_engine.websocket_connections.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        decision_engine.websocket_connections.discard(websocket)

@app.get("/analytics/patterns")
async def get_decision_patterns() -> Dict[str, Any]:
    """Get decision patterns and analytics"""
    if len(decision_engine.decision_history) < 5:
        return {"message": "Insufficient data for pattern analysis"}
    
    patterns = await decision_engine.pattern_recognizer.analyze_decision_patterns(
        list(decision_engine.decision_history)
    )
    
    return patterns

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/decision/queue-status")
async def get_queue_status() -> Dict[str, Any]:
    """Get decision queue status"""
    queue_status = {}
    
    for priority in Priority:
        queue = decision_engine.decision_queues[priority]
        queue_status[priority.name] = {
            'size': queue.qsize(),
            'priority_level': priority.value
        }
    
    return {
        "queue_status": queue_status,
        "total_queued": sum(q.qsize() for q in decision_engine.decision_queues.values())
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8012,
        reload=True
    )