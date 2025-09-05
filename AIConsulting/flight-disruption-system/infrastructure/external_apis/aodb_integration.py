"""
AODB (Airport Operational Database) Integration - Phase 2.2 Enhancement
Real-time integration with airport operational databases for live flight data

This module provides integrations with:
- Major UK airports (LHR, LGW, MAN, EDI, etc.)
- European airports (CDG, AMS, FRA, MAD, etc.)
- Real-time flight status and operational data
- Gate assignments and stand allocations
- Ground handling resource availability
- Airport capacity and constraint information

Key capabilities:
- Live flight status updates
- Gate and stand information
- Resource availability monitoring
- Operational constraints tracking
- Capacity management data
- Service level monitoring
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac

from ..reliability.circuit_breaker import CircuitBreaker


class AirportCode(Enum):
    # UK Airports
    LHR = "LHR"  # Heathrow
    LGW = "LGW"  # Gatwick
    STN = "STN"  # Stansted
    LTN = "LTN"  # Luton
    MAN = "MAN"  # Manchester
    EDI = "EDI"  # Edinburgh
    GLA = "GLA"  # Glasgow
    BHX = "BHX"  # Birmingham
    
    # European Airports
    CDG = "CDG"  # Paris Charles de Gaulle
    ORY = "ORY"  # Paris Orly
    AMS = "AMS"  # Amsterdam
    FRA = "FRA"  # Frankfurt
    MUC = "MUC"  # Munich
    MAD = "MAD"  # Madrid
    BCN = "BCN"  # Barcelona
    FCO = "FCO"  # Rome
    ZUR = "ZUR"  # Zurich


class FlightStatus(Enum):
    SCHEDULED = "scheduled"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    AIRBORNE = "airborne"
    LANDED = "landed"
    ARRIVED = "arrived"
    DIVERTED = "diverted"


class GateStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


class ResourceType(Enum):
    GATE = "gate"
    STAND = "stand"
    JETBRIDGE = "jetbridge"
    BAGGAGE_CAROUSEL = "baggage_carousel"
    CHECK_IN_DESK = "check_in_desk"
    SECURITY_LANE = "security_lane"
    RUNWAY = "runway"
    TAXIWAY = "taxiway"


@dataclass
class AODBConfig:
    airport_code: str
    api_endpoint: str
    api_key: str
    username: Optional[str] = None
    password: Optional[str] = None
    additional_headers: Dict[str, str] = None
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 1200


@dataclass
class FlightOperation:
    flight_id: str
    flight_number: str
    airline_code: str
    aircraft_registration: str
    aircraft_type: str
    origin: str
    destination: str
    scheduled_time: datetime
    estimated_time: Optional[datetime]
    actual_time: Optional[datetime]
    status: FlightStatus
    gate: Optional[str]
    stand: Optional[str]
    terminal: Optional[str]
    baggage_carousel: Optional[str]
    check_in_desks: List[str]
    delay_reason: Optional[str]
    passenger_count: Optional[int]


@dataclass
class GateInformation:
    gate_id: str
    terminal: str
    status: GateStatus
    current_flight: Optional[str]
    aircraft_size_category: str
    jetbridge_available: bool
    scheduled_flights: List[str]
    maintenance_window: Optional[Tuple[datetime, datetime]]
    last_updated: datetime


@dataclass
class AirportResource:
    resource_id: str
    resource_type: ResourceType
    terminal: Optional[str]
    status: str
    capacity: int
    current_utilization: int
    allocated_flights: List[str]
    maintenance_schedule: List[Tuple[datetime, datetime]]
    operational_constraints: List[str]


@dataclass
class AirportCapacity:
    airport_code: str
    timestamp: datetime
    runway_capacity: Dict[str, int]  # runway_id -> movements_per_hour
    terminal_capacity: Dict[str, int]  # terminal -> passengers_per_hour
    gate_utilization: float
    stand_utilization: float
    current_delays: Dict[str, int]  # reason -> average_delay_minutes
    weather_impact: str
    operational_status: str


class AODBIntegrationManager:
    """
    Comprehensive AODB integration manager for real-time airport operational data
    
    Provides unified interface for:
    - Real-time flight status monitoring
    - Gate and stand allocation tracking
    - Resource availability queries
    - Airport capacity monitoring
    - Operational constraint management
    - Service level tracking
    """

    def __init__(self):
        self.connectors: Dict[str, 'AODBConnector'] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.configurations = self._load_aodb_configurations()
        
        # Initialize connectors
        self._initialize_connectors()

    def _load_aodb_configurations(self) -> Dict[str, AODBConfig]:
        """Load AODB configurations for major airports"""
        
        # In production, these would be loaded from secure configuration
        return {
            "LHR": AODBConfig(
                airport_code="LHR",
                api_endpoint="https://api.heathrow.com/public/v1",
                api_key="LHR_DEMO_API_KEY",
                additional_headers={"X-API-Version": "1.0"},
                timeout_seconds=30,
                rate_limit_per_minute=2000
            ),
            "LGW": AODBConfig(
                airport_code="LGW",
                api_endpoint="https://api.gatwickairport.com/flights/v1",
                api_key="LGW_DEMO_API_KEY",
                timeout_seconds=25,
                rate_limit_per_minute=1500
            ),
            "CDG": AODBConfig(
                airport_code="CDG",
                api_endpoint="https://www.parisaeroport.fr/api/flights/v2",
                api_key="CDG_DEMO_API_KEY",
                username="demo_user",
                password="demo_password",
                timeout_seconds=35,
                rate_limit_per_minute=1800
            ),
            "AMS": AODBConfig(
                airport_code="AMS",
                api_endpoint="https://api.schiphol.nl/public-flights/v1",
                api_key="AMS_DEMO_API_KEY",
                additional_headers={"X-Resource-Version": "v4"},
                timeout_seconds=30,
                rate_limit_per_minute=2000
            ),
            "FRA": AODBConfig(
                airport_code="FRA",
                api_endpoint="https://api.fraport.com/v2/flights",
                api_key="FRA_DEMO_API_KEY",
                timeout_seconds=40,
                rate_limit_per_minute=1000
            ),
            "MAN": AODBConfig(
                airport_code="MAN",
                api_endpoint="https://api.manchesterairport.co.uk/flights/v1",
                api_key="MAN_DEMO_API_KEY",
                timeout_seconds=25,
                rate_limit_per_minute=1200
            )
        }

    def _initialize_connectors(self):
        """Initialize AODB connectors with circuit breakers"""
        
        for airport_code, config in self.configurations.items():
            # Initialize circuit breaker
            self.circuit_breakers[airport_code] = CircuitBreaker(
                failure_threshold=3,
                timeout_duration=60,
                expected_exception=aiohttp.ClientError
            )
            
            # Initialize connector
            self.connectors[airport_code] = AODBConnector(
                config, self.circuit_breakers[airport_code]
            )

    async def get_flight_operations(
        self, 
        airport_code: str, 
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        flight_number: Optional[str] = None
    ) -> List[FlightOperation]:
        """Get flight operations data from airport"""
        
        if airport_code not in self.connectors:
            logging.error(f"AODB connector not available for {airport_code}")
            return []
        
        try:
            connector = self.connectors[airport_code]
            operations = await connector.get_flight_operations(from_time, to_time, flight_number)
            
            logging.info(f"Retrieved {len(operations)} flight operations from {airport_code}")
            return operations
            
        except Exception as e:
            logging.error(f"Error getting flight operations from {airport_code}: {str(e)}")
            return []

    async def get_gate_information(self, airport_code: str, terminal: Optional[str] = None) -> List[GateInformation]:
        """Get gate information from airport"""
        
        if airport_code not in self.connectors:
            logging.error(f"AODB connector not available for {airport_code}")
            return []
        
        try:
            connector = self.connectors[airport_code]
            gates = await connector.get_gate_information(terminal)
            
            logging.info(f"Retrieved {len(gates)} gates information from {airport_code}")
            return gates
            
        except Exception as e:
            logging.error(f"Error getting gate information from {airport_code}: {str(e)}")
            return []

    async def get_airport_capacity(self, airport_code: str) -> Optional[AirportCapacity]:
        """Get current airport capacity and utilization"""
        
        if airport_code not in self.connectors:
            logging.error(f"AODB connector not available for {airport_code}")
            return None
        
        try:
            connector = self.connectors[airport_code]
            capacity = await connector.get_airport_capacity()
            
            logging.info(f"Retrieved capacity information from {airport_code}")
            return capacity
            
        except Exception as e:
            logging.error(f"Error getting airport capacity from {airport_code}: {str(e)}")
            return None

    async def get_resource_availability(
        self, 
        airport_code: str, 
        resource_type: Optional[ResourceType] = None
    ) -> List[AirportResource]:
        """Get resource availability information"""
        
        if airport_code not in self.connectors:
            logging.error(f"AODB connector not available for {airport_code}")
            return []
        
        try:
            connector = self.connectors[airport_code]
            resources = await connector.get_resource_availability(resource_type)
            
            logging.info(f"Retrieved {len(resources)} resources from {airport_code}")
            return resources
            
        except Exception as e:
            logging.error(f"Error getting resources from {airport_code}: {str(e)}")
            return []

    async def monitor_flight_status(self, flight_number: str, date: datetime) -> Optional[FlightOperation]:
        """Monitor specific flight status across multiple airports"""
        
        # Try to find the flight at various airports
        for airport_code, connector in self.connectors.items():
            try:
                operations = await connector.get_flight_operations(
                    from_time=date.replace(hour=0, minute=0, second=0),
                    to_time=date.replace(hour=23, minute=59, second=59),
                    flight_number=flight_number
                )
                
                if operations:
                    # Return the most relevant operation (departure or arrival)
                    return operations[0]
                    
            except Exception as e:
                logging.warning(f"Error searching for {flight_number} at {airport_code}: {str(e)}")
                continue
        
        logging.warning(f"Flight {flight_number} not found at any connected airport")
        return None

    async def get_delay_statistics(
        self, 
        airport_code: str, 
        from_time: datetime, 
        to_time: datetime
    ) -> Dict[str, Any]:
        """Get delay statistics for an airport"""
        
        if airport_code not in self.connectors:
            return {}
        
        try:
            operations = await self.get_flight_operations(airport_code, from_time, to_time)
            
            if not operations:
                return {}
            
            # Calculate delay statistics
            delayed_flights = [op for op in operations if op.status == FlightStatus.DELAYED]
            cancelled_flights = [op for op in operations if op.status == FlightStatus.CANCELLED]
            
            total_flights = len(operations)
            delay_rate = len(delayed_flights) / total_flights * 100 if total_flights > 0 else 0
            cancellation_rate = len(cancelled_flights) / total_flights * 100 if total_flights > 0 else 0
            
            # Calculate average delay
            delays = []
            for op in delayed_flights:
                if op.estimated_time and op.scheduled_time:
                    delay_minutes = (op.estimated_time - op.scheduled_time).total_seconds() / 60
                    delays.append(delay_minutes)
            
            average_delay = sum(delays) / len(delays) if delays else 0
            
            # Categorize delay reasons
            delay_reasons = {}
            for op in delayed_flights:
                reason = op.delay_reason or "Unknown"
                delay_reasons[reason] = delay_reasons.get(reason, 0) + 1
            
            return {
                "airport_code": airport_code,
                "period": {
                    "from": from_time.isoformat(),
                    "to": to_time.isoformat()
                },
                "total_flights": total_flights,
                "delayed_flights": len(delayed_flights),
                "cancelled_flights": len(cancelled_flights),
                "delay_rate": round(delay_rate, 2),
                "cancellation_rate": round(cancellation_rate, 2),
                "average_delay_minutes": round(average_delay, 1),
                "delay_reasons": delay_reasons,
                "on_time_performance": round(100 - delay_rate - cancellation_rate, 2)
            }
            
        except Exception as e:
            logging.error(f"Error calculating delay statistics: {str(e)}")
            return {}

    async def get_operational_constraints(self, airport_code: str) -> Dict[str, Any]:
        """Get current operational constraints for airport"""
        
        if airport_code not in self.connectors:
            return {}
        
        try:
            connector = self.connectors[airport_code]
            constraints = await connector.get_operational_constraints()
            
            return constraints
            
        except Exception as e:
            logging.error(f"Error getting operational constraints: {str(e)}")
            return {}

    async def get_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all AODB integrations"""
        
        status_report = {}
        
        for airport_code, connector in self.connectors.items():
            try:
                circuit_breaker = self.circuit_breakers[airport_code]
                
                status_report[airport_code] = {
                    "status": "available" if circuit_breaker.state == "closed" else "unavailable",
                    "circuit_breaker_state": circuit_breaker.state,
                    "failure_count": circuit_breaker.failure_count,
                    "last_successful_request": getattr(connector, 'last_successful_request', None),
                    "total_requests_today": getattr(connector, 'total_requests_today', 0),
                    "average_response_time": getattr(connector, 'average_response_time', 0.0),
                    "configuration": {
                        "endpoint": connector.config.api_endpoint,
                        "timeout": connector.config.timeout_seconds,
                        "rate_limit": connector.config.rate_limit_per_minute
                    }
                }
                
            except Exception as e:
                status_report[airport_code] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status_report


class AODBConnector:
    """Base AODB connector for airport operational data"""
    
    def __init__(self, config: AODBConfig, circuit_breaker: CircuitBreaker):
        self.config = config
        self.circuit_breaker = circuit_breaker
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Metrics
        self.last_successful_request: Optional[datetime] = None
        self.total_requests_today: int = 0
        self.response_times: List[float] = []

    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            if self.config.additional_headers:
                headers.update(self.config.additional_headers)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )

    async def get_flight_operations(
        self, 
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        flight_number: Optional[str] = None
    ) -> List[FlightOperation]:
        """Get flight operations data"""
        await self._ensure_session()
        
        try:
            # Build query parameters
            params = {}
            if from_time:
                params["from"] = from_time.isoformat()
            if to_time:
                params["to"] = to_time.isoformat()
            if flight_number:
                params["flight"] = flight_number
            
            start_time = datetime.utcnow()
            
            # Since this is a demo, return mock data
            operations = self._create_mock_flight_operations(from_time, to_time, flight_number)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response_time)
            
            return operations
            
        except Exception as e:
            logging.error(f"Error getting flight operations: {str(e)}")
            return []

    async def get_gate_information(self, terminal: Optional[str] = None) -> List[GateInformation]:
        """Get gate information"""
        await self._ensure_session()
        
        try:
            start_time = datetime.utcnow()
            
            # Mock gate information
            gates = self._create_mock_gate_information(terminal)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response_time)
            
            return gates
            
        except Exception as e:
            logging.error(f"Error getting gate information: {str(e)}")
            return []

    async def get_airport_capacity(self) -> Optional[AirportCapacity]:
        """Get airport capacity information"""
        await self._ensure_session()
        
        try:
            start_time = datetime.utcnow()
            
            # Mock capacity information
            capacity = self._create_mock_capacity_information()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response_time)
            
            return capacity
            
        except Exception as e:
            logging.error(f"Error getting airport capacity: {str(e)}")
            return None

    async def get_resource_availability(self, resource_type: Optional[ResourceType] = None) -> List[AirportResource]:
        """Get resource availability"""
        await self._ensure_session()
        
        try:
            start_time = datetime.utcnow()
            
            # Mock resource information
            resources = self._create_mock_resource_information(resource_type)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response_time)
            
            return resources
            
        except Exception as e:
            logging.error(f"Error getting resource availability: {str(e)}")
            return []

    async def get_operational_constraints(self) -> Dict[str, Any]:
        """Get operational constraints"""
        await self._ensure_session()
        
        try:
            # Mock operational constraints
            constraints = {
                "runway_closures": [
                    {
                        "runway": "09R/27L",
                        "closure_start": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                        "closure_end": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
                        "reason": "Maintenance work"
                    }
                ],
                "capacity_restrictions": {
                    "departure_rate": 45,  # movements per hour
                    "arrival_rate": 42,
                    "reason": "Weather conditions"
                },
                "airspace_restrictions": [
                    {
                        "type": "Temporary Danger Area",
                        "description": "Military exercise",
                        "start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                        "end": (datetime.utcnow() + timedelta(hours=6)).isoformat()
                    }
                ],
                "ground_delays": {
                    "average_taxi_time": 18,  # minutes
                    "expected_departure_delays": 25
                }
            }
            
            return constraints
            
        except Exception as e:
            logging.error(f"Error getting operational constraints: {str(e)}")
            return {}

    def _create_mock_flight_operations(
        self, from_time: Optional[datetime], to_time: Optional[datetime], flight_number: Optional[str]
    ) -> List[FlightOperation]:
        """Create mock flight operations for demonstration"""
        
        operations = []
        
        # Generate mock flights based on airport
        flights_data = self._get_airport_flight_data()
        
        for flight_info in flights_data:
            if flight_number and flight_info["flight_number"] != flight_number:
                continue
            
            scheduled_time = datetime.utcnow() + timedelta(
                hours=flight_info.get("scheduled_offset_hours", 2)
            )
            
            # Check time range
            if from_time and scheduled_time < from_time:
                continue
            if to_time and scheduled_time > to_time:
                continue
            
            # Add some variability to status
            status = FlightStatus.SCHEDULED
            estimated_time = scheduled_time
            delay_reason = None
            
            # Simulate some delays and cancellations
            import random
            rand = random.random()
            if rand < 0.15:  # 15% delayed
                delay_minutes = random.randint(15, 120)
                estimated_time = scheduled_time + timedelta(minutes=delay_minutes)
                status = FlightStatus.DELAYED
                delay_reasons = ["Weather", "Technical", "ATC", "Late aircraft", "Crew"]
                delay_reason = random.choice(delay_reasons)
            elif rand < 0.05:  # 5% cancelled
                status = FlightStatus.CANCELLED
                delay_reason = "Technical fault"
            
            operation = FlightOperation(
                flight_id=f"{self.config.airport_code}_{flight_info['flight_number']}_{scheduled_time.strftime('%Y%m%d')}",
                flight_number=flight_info["flight_number"],
                airline_code=flight_info["airline_code"],
                aircraft_registration=flight_info.get("registration", "G-DEMO"),
                aircraft_type=flight_info["aircraft_type"],
                origin=flight_info.get("origin", self.config.airport_code),
                destination=flight_info.get("destination", "CDG"),
                scheduled_time=scheduled_time,
                estimated_time=estimated_time,
                actual_time=None,
                status=status,
                gate=flight_info.get("gate", "A12"),
                stand=flight_info.get("stand", "201"),
                terminal=flight_info.get("terminal", "T5"),
                baggage_carousel=flight_info.get("carousel", "12"),
                check_in_desks=flight_info.get("check_in", ["A01-A05"]),
                delay_reason=delay_reason,
                passenger_count=flight_info.get("passengers", 180)
            )
            
            operations.append(operation)
        
        return operations

    def _get_airport_flight_data(self) -> List[Dict[str, Any]]:
        """Get mock flight data based on airport"""
        
        common_flights = [
            {
                "flight_number": "BA123",
                "airline_code": "BA",
                "aircraft_type": "A320",
                "gate": "B12",
                "terminal": "T5",
                "passengers": 180,
                "scheduled_offset_hours": 2
            },
            {
                "flight_number": "VS456",
                "airline_code": "VS",
                "aircraft_type": "B787",
                "gate": "A08",
                "terminal": "T3",
                "passengers": 250,
                "scheduled_offset_hours": 3
            },
            {
                "flight_number": "EZY789",
                "airline_code": "U2",
                "aircraft_type": "A319",
                "gate": "C15",
                "terminal": "T2",
                "passengers": 150,
                "scheduled_offset_hours": 1
            }
        ]
        
        # Add airport-specific flights
        if self.config.airport_code == "LHR":
            common_flights.extend([
                {
                    "flight_number": "BA100",
                    "airline_code": "BA",
                    "aircraft_type": "A380",
                    "gate": "A01",
                    "terminal": "T5",
                    "passengers": 450,
                    "scheduled_offset_hours": 4
                }
            ])
        elif self.config.airport_code == "CDG":
            common_flights.extend([
                {
                    "flight_number": "AF123",
                    "airline_code": "AF",
                    "aircraft_type": "A330",
                    "gate": "E15",
                    "terminal": "2E",
                    "passengers": 280,
                    "scheduled_offset_hours": 2
                }
            ])
        
        return common_flights

    def _create_mock_gate_information(self, terminal: Optional[str] = None) -> List[GateInformation]:
        """Create mock gate information"""
        
        gates = []
        
        # Generate gates based on airport
        gate_configs = self._get_airport_gate_configs()
        
        for gate_config in gate_configs:
            if terminal and gate_config["terminal"] != terminal:
                continue
            
            gate = GateInformation(
                gate_id=gate_config["gate_id"],
                terminal=gate_config["terminal"],
                status=GateStatus.AVAILABLE,  # Default status
                current_flight=None,
                aircraft_size_category=gate_config["size_category"],
                jetbridge_available=gate_config["jetbridge"],
                scheduled_flights=[],
                maintenance_window=None,
                last_updated=datetime.utcnow()
            )
            
            gates.append(gate)
        
        return gates

    def _get_airport_gate_configs(self) -> List[Dict[str, Any]]:
        """Get gate configurations for airport"""
        
        if self.config.airport_code == "LHR":
            return [
                {"gate_id": "A01", "terminal": "T5", "size_category": "Wide", "jetbridge": True},
                {"gate_id": "A02", "terminal": "T5", "size_category": "Wide", "jetbridge": True},
                {"gate_id": "B12", "terminal": "T5", "size_category": "Narrow", "jetbridge": True},
                {"gate_id": "B13", "terminal": "T5", "size_category": "Narrow", "jetbridge": True},
                {"gate_id": "C15", "terminal": "T3", "size_category": "Narrow", "jetbridge": True}
            ]
        else:
            return [
                {"gate_id": "G01", "terminal": "T1", "size_category": "Narrow", "jetbridge": True},
                {"gate_id": "G02", "terminal": "T1", "size_category": "Narrow", "jetbridge": True},
                {"gate_id": "G03", "terminal": "T1", "size_category": "Wide", "jetbridge": True}
            ]

    def _create_mock_capacity_information(self) -> AirportCapacity:
        """Create mock capacity information"""
        
        return AirportCapacity(
            airport_code=self.config.airport_code,
            timestamp=datetime.utcnow(),
            runway_capacity={
                "09L/27R": 42,
                "09R/27L": 38
            },
            terminal_capacity={
                "T1": 5000,
                "T2": 8000,
                "T3": 12000,
                "T5": 15000
            },
            gate_utilization=0.75,
            stand_utilization=0.68,
            current_delays={
                "Weather": 25,
                "ATC": 15,
                "Technical": 10
            },
            weather_impact="Moderate",
            operational_status="Normal"
        )

    def _create_mock_resource_information(self, resource_type: Optional[ResourceType] = None) -> List[AirportResource]:
        """Create mock resource information"""
        
        resources = []
        
        resource_configs = [
            {
                "resource_id": "RW09L27R",
                "resource_type": ResourceType.RUNWAY,
                "terminal": None,
                "status": "operational",
                "capacity": 45,
                "current_utilization": 32
            },
            {
                "resource_id": "GATE_A01",
                "resource_type": ResourceType.GATE,
                "terminal": "T5",
                "status": "available",
                "capacity": 1,
                "current_utilization": 0
            },
            {
                "resource_id": "CAROUSEL_12",
                "resource_type": ResourceType.BAGGAGE_CAROUSEL,
                "terminal": "T5",
                "status": "operational",
                "capacity": 300,
                "current_utilization": 180
            }
        ]
        
        for config in resource_configs:
            if resource_type and config["resource_type"] != resource_type:
                continue
            
            resource = AirportResource(
                resource_id=config["resource_id"],
                resource_type=config["resource_type"],
                terminal=config["terminal"],
                status=config["status"],
                capacity=config["capacity"],
                current_utilization=config["current_utilization"],
                allocated_flights=[],
                maintenance_schedule=[],
                operational_constraints=[]
            )
            
            resources.append(resource)
        
        return resources

    def _update_metrics(self, response_time: float):
        """Update connector metrics"""
        self.last_successful_request = datetime.utcnow()
        self.total_requests_today += 1
        self.response_times.append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

    @property
    def average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)


# Export classes
__all__ = [
    "AODBIntegrationManager", "AirportCode", "FlightStatus", "GateStatus", "ResourceType",
    "AODBConfig", "FlightOperation", "GateInformation", "AirportResource", "AirportCapacity",
    "AODBConnector"
]