"""
Flight Disruption Management System - Database Package

Database schemas, connections, and utilities for production-ready
airline operations data management.
"""

from .schemas import (
    Base,
    Airport, Aircraft, CrewMember, Flight, Passenger,
    Disruption, Rebooking, Compensation,
    AgentDecision, SystemEvent, SystemMetrics, Configuration,
    FlightStatus, DisruptionType, DisruptionSeverity,
    PassengerStatus, RebookingStatus, CompensationStatus
)

from .connection import (
    DatabaseConfig, DatabaseManager, db_manager,
    get_db_session, get_async_db_session,
    init_database, get_database_health, MigrationManager
)

from .seed_data import (
    get_reference_airports, get_reference_aircraft,
    get_sample_crew_members, get_system_configurations,
    get_sample_disruption_scenarios
)

__version__ = "1.0.0"

__all__ = [
    # Schema models
    'Base', 'Airport', 'Aircraft', 'CrewMember', 'Flight', 'Passenger',
    'Disruption', 'Rebooking', 'Compensation', 'AgentDecision',
    'SystemEvent', 'SystemMetrics', 'Configuration',
    
    # Enums
    'FlightStatus', 'DisruptionType', 'DisruptionSeverity',
    'PassengerStatus', 'RebookingStatus', 'CompensationStatus',
    
    # Database connection
    'DatabaseConfig', 'DatabaseManager', 'db_manager',
    'get_db_session', 'get_async_db_session',
    'init_database', 'get_database_health', 'MigrationManager',
    
    # Seed data
    'get_reference_airports', 'get_reference_aircraft',
    'get_sample_crew_members', 'get_system_configurations',
    'get_sample_disruption_scenarios'
]