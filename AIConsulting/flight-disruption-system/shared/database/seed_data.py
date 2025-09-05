"""
Seed Data for Flight Disruption Management System

Reference data for airports, aircraft types, and initial system configuration
to support realistic airline operations testing and development.
"""

from datetime import datetime, date
from typing import List, Dict, Any
import uuid


def get_reference_airports() -> List[Dict[str, Any]]:
    """Get reference airport data for major UK and European airports"""
    
    airports = [
        # Major UK Airports
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'LHR',
            'icao_code': 'EGLL',
            'airport_name': 'London Heathrow Airport',
            'city': 'London',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'latitude': 51.4700,
            'longitude': -0.4543,
            'elevation_ft': 83,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 5,
                'runways': 2,
                'gates': 178,
                'max_hourly_movements': 90,
                'passenger_capacity_millions': 80
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'LGW',
            'icao_code': 'EGKK',
            'airport_name': 'London Gatwick Airport',
            'city': 'London',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'latitude': 51.1537,
            'longitude': -0.1821,
            'elevation_ft': 202,
            'hub_priority': 2,
            'operational_capacity': {
                'terminals': 2,
                'runways': 1,
                'gates': 120,
                'max_hourly_movements': 55,
                'passenger_capacity_millions': 46
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'MAN',
            'icao_code': 'EGCC',
            'airport_name': 'Manchester Airport',
            'city': 'Manchester',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'latitude': 53.3537,
            'longitude': -2.2750,
            'elevation_ft': 256,
            'hub_priority': 2,
            'operational_capacity': {
                'terminals': 3,
                'runways': 2,
                'gates': 90,
                'max_hourly_movements': 65,
                'passenger_capacity_millions': 28
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'EDI',
            'icao_code': 'EGPH',
            'airport_name': 'Edinburgh Airport',
            'city': 'Edinburgh',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'latitude': 55.9500,
            'longitude': -3.3725,
            'elevation_ft': 135,
            'hub_priority': 3,
            'operational_capacity': {
                'terminals': 1,
                'runways': 1,
                'gates': 28,
                'max_hourly_movements': 40,
                'passenger_capacity_millions': 14
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'BHX',
            'icao_code': 'EGBB',
            'airport_name': 'Birmingham Airport',
            'city': 'Birmingham',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'latitude': 52.4539,
            'longitude': -1.7480,
            'elevation_ft': 327,
            'hub_priority': 3,
            'operational_capacity': {
                'terminals': 2,
                'runways': 1,
                'gates': 40,
                'max_hourly_movements': 35,
                'passenger_capacity_millions': 13
            }
        },
        
        # Major European Destinations
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'CDG',
            'icao_code': 'LFPG',
            'airport_name': 'Charles de Gaulle Airport',
            'city': 'Paris',
            'country': 'France',
            'timezone': 'Europe/Paris',
            'latitude': 49.0097,
            'longitude': 2.5479,
            'elevation_ft': 392,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 3,
                'runways': 4,
                'gates': 200,
                'max_hourly_movements': 120,
                'passenger_capacity_millions': 76
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'AMS',
            'icao_code': 'EHAM',
            'airport_name': 'Amsterdam Airport Schiphol',
            'city': 'Amsterdam',
            'country': 'Netherlands',
            'timezone': 'Europe/Amsterdam',
            'latitude': 52.3086,
            'longitude': 4.7639,
            'elevation_ft': -11,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 1,
                'runways': 6,
                'gates': 160,
                'max_hourly_movements': 140,
                'passenger_capacity_millions': 71
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'FRA',
            'icao_code': 'EDDF',
            'airport_name': 'Frankfurt Airport',
            'city': 'Frankfurt',
            'country': 'Germany',
            'timezone': 'Europe/Berlin',
            'latitude': 50.0264,
            'longitude': 8.5431,
            'elevation_ft': 364,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 2,
                'runways': 4,
                'gates': 180,
                'max_hourly_movements': 126,
                'passenger_capacity_millions': 70
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'MAD',
            'icao_code': 'LEMD',
            'airport_name': 'Madrid-Barajas Airport',
            'city': 'Madrid',
            'country': 'Spain',
            'timezone': 'Europe/Madrid',
            'latitude': 40.4719,
            'longitude': -3.5626,
            'elevation_ft': 2001,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 4,
                'runways': 4,
                'gates': 140,
                'max_hourly_movements': 120,
                'passenger_capacity_millions': 57
            }
        },
        
        # Major International Destinations
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'JFK',
            'icao_code': 'KJFK',
            'airport_name': 'John F. Kennedy International Airport',
            'city': 'New York',
            'country': 'United States',
            'timezone': 'America/New_York',
            'latitude': 40.6413,
            'longitude': -73.7781,
            'elevation_ft': 13,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 6,
                'runways': 4,
                'gates': 130,
                'max_hourly_movements': 80,
                'passenger_capacity_millions': 62
            }
        },
        {
            'airport_id': str(uuid.uuid4()),
            'iata_code': 'DXB',
            'icao_code': 'OMDB',
            'airport_name': 'Dubai International Airport',
            'city': 'Dubai',
            'country': 'United Arab Emirates',
            'timezone': 'Asia/Dubai',
            'latitude': 25.2532,
            'longitude': 55.3657,
            'elevation_ft': 62,
            'hub_priority': 1,
            'operational_capacity': {
                'terminals': 3,
                'runways': 2,
                'gates': 170,
                'max_hourly_movements': 100,
                'passenger_capacity_millions': 90
            }
        }
    ]
    
    return airports


def get_reference_aircraft() -> List[Dict[str, Any]]:
    """Get reference aircraft fleet data for major aircraft types"""
    
    aircraft_fleet = [
        # Airbus A320 Family
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-EUYA',
            'aircraft_type': 'A320',
            'manufacturer': 'Airbus',
            'model': 'A320-232',
            'seat_capacity': 180,
            'seat_configuration': {
                'economy': 174,
                'premium_economy': 6,
                'business': 0,
                'first': 0,
                'total': 180
            },
            'range_km': 6150,
            'max_speed_kmh': 828,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 12, 15),
            'next_maintenance_date': date(2025, 3, 15),
            'operational_status': 'available',
            'current_location': 'LHR'
        },
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-EUYB',
            'aircraft_type': 'A320',
            'manufacturer': 'Airbus',
            'model': 'A320-232',
            'seat_capacity': 180,
            'seat_configuration': {
                'economy': 174,
                'premium_economy': 6,
                'business': 0,
                'first': 0,
                'total': 180
            },
            'range_km': 6150,
            'max_speed_kmh': 828,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 11, 20),
            'next_maintenance_date': date(2025, 2, 20),
            'operational_status': 'available',
            'current_location': 'LGW'
        },
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-EUYC',
            'aircraft_type': 'A321',
            'manufacturer': 'Airbus',
            'model': 'A321-232',
            'seat_capacity': 220,
            'seat_configuration': {
                'economy': 208,
                'premium_economy': 12,
                'business': 0,
                'first': 0,
                'total': 220
            },
            'range_km': 7400,
            'max_speed_kmh': 828,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 10, 10),
            'next_maintenance_date': date(2025, 1, 10),
            'operational_status': 'available',
            'current_location': 'MAN'
        },
        
        # Boeing 737 Family
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-BZHA',
            'aircraft_type': 'B737',
            'manufacturer': 'Boeing',
            'model': '737-800',
            'seat_capacity': 189,
            'seat_configuration': {
                'economy': 177,
                'premium_economy': 12,
                'business': 0,
                'first': 0,
                'total': 189
            },
            'range_km': 5765,
            'max_speed_kmh': 842,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 12, 5),
            'next_maintenance_date': date(2025, 3, 5),
            'operational_status': 'available',
            'current_location': 'EDI'
        },
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-BZHB',
            'aircraft_type': 'B737',
            'manufacturer': 'Boeing',
            'model': '737-800',
            'seat_capacity': 189,
            'seat_configuration': {
                'economy': 177,
                'premium_economy': 12,
                'business': 0,
                'first': 0,
                'total': 189
            },
            'range_km': 5765,
            'max_speed_kmh': 842,
            'maintenance_status': 'maintenance',
            'last_maintenance_date': date(2024, 12, 20),
            'next_maintenance_date': date(2025, 3, 20),
            'operational_status': 'unavailable',
            'current_location': 'LHR'
        },
        
        # Wide-body Aircraft
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-BOAA',
            'aircraft_type': 'B777',
            'manufacturer': 'Boeing',
            'model': '777-200ER',
            'seat_capacity': 336,
            'seat_configuration': {
                'economy': 252,
                'premium_economy': 40,
                'business': 40,
                'first': 4,
                'total': 336
            },
            'range_km': 14305,
            'max_speed_kmh': 905,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 11, 1),
            'next_maintenance_date': date(2025, 2, 1),
            'operational_status': 'available',
            'current_location': 'LHR'
        },
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-XLAA',
            'aircraft_type': 'A350',
            'manufacturer': 'Airbus',
            'model': 'A350-1000',
            'seat_capacity': 331,
            'seat_configuration': {
                'economy': 235,
                'premium_economy': 56,
                'business': 32,
                'first': 8,
                'total': 331
            },
            'range_km': 16100,
            'max_speed_kmh': 903,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 12, 1),
            'next_maintenance_date': date(2025, 3, 1),
            'operational_status': 'available',
            'current_location': 'LHR'
        },
        
        # Regional Aircraft
        {
            'aircraft_id': str(uuid.uuid4()),
            'registration': 'G-EMBA',
            'aircraft_type': 'EMB190',
            'manufacturer': 'Embraer',
            'model': 'E190',
            'seat_capacity': 100,
            'seat_configuration': {
                'economy': 96,
                'premium_economy': 4,
                'business': 0,
                'first': 0,
                'total': 100
            },
            'range_km': 4537,
            'max_speed_kmh': 829,
            'maintenance_status': 'operational',
            'last_maintenance_date': date(2024, 11, 15),
            'next_maintenance_date': date(2025, 2, 15),
            'operational_status': 'available',
            'current_location': 'BHX'
        }
    ]
    
    return aircraft_fleet


def get_sample_crew_members() -> List[Dict[str, Any]]:
    """Get sample crew member data"""
    
    crew_members = [
        {
            'crew_member_id': str(uuid.uuid4()),
            'employee_id': 'BA001',
            'first_name': 'James',
            'last_name': 'Smith',
            'role': 'pilot',
            'rank': 'captain',
            'base_airport': 'LHR',
            'qualifications': ['A320', 'A321', 'B737'],
            'availability_status': 'available',
            'current_location': 'LHR',
            'max_flight_hours_month': 100,
            'current_flight_hours_month': 45
        },
        {
            'crew_member_id': str(uuid.uuid4()),
            'employee_id': 'BA002',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'pilot',
            'rank': 'first_officer',
            'base_airport': 'LHR',
            'qualifications': ['A320', 'A321'],
            'availability_status': 'available',
            'current_location': 'LHR',
            'max_flight_hours_month': 100,
            'current_flight_hours_month': 38
        },
        {
            'crew_member_id': str(uuid.uuid4()),
            'employee_id': 'BA003',
            'first_name': 'Michael',
            'last_name': 'Brown',
            'role': 'cabin_crew',
            'rank': 'senior_cabin_crew',
            'base_airport': 'LHR',
            'qualifications': ['A320', 'A321', 'B737', 'B777'],
            'availability_status': 'available',
            'current_location': 'LHR',
            'max_flight_hours_month': 120,
            'current_flight_hours_month': 52
        }
    ]
    
    return crew_members


def get_system_configurations() -> List[Dict[str, Any]]:
    """Get initial system configuration parameters"""
    
    configurations = [
        # Agent Configuration
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'agent.prediction.confidence_threshold',
            'config_value': 0.75,
            'config_type': 'agent',
            'description': 'Minimum confidence threshold for prediction agent decisions',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': False,
            'created_by': 'system_init'
        },
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'agent.passenger.max_concurrent_rebookings',
            'config_value': 50,
            'config_type': 'agent',
            'description': 'Maximum number of concurrent passenger rebookings',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': False,
            'created_by': 'system_init'
        },
        
        # Business Rules
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'business.eu261.short_haul_compensation',
            'config_value': 250.00,
            'config_type': 'business_rule',
            'description': 'EU261 compensation amount for short-haul flights (EUR)',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': False,
            'created_by': 'system_init'
        },
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'business.rebooking.auto_approval_threshold',
            'config_value': 500.00,
            'config_type': 'business_rule',
            'description': 'Maximum cost difference for automatic rebooking approval (GBP)',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': False,
            'created_by': 'system_init'
        },
        
        # System Configuration
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'system.notification.max_retries',
            'config_value': 3,
            'config_type': 'system',
            'description': 'Maximum retry attempts for passenger notifications',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': True,
            'created_by': 'system_init'
        },
        {
            'config_id': str(uuid.uuid4()),
            'config_key': 'system.kafka.batch_size',
            'config_value': 100,
            'config_type': 'system',
            'description': 'Kafka consumer batch size for event processing',
            'environment': 'production',
            'is_sensitive': False,
            'requires_restart': True,
            'created_by': 'system_init'
        }
    ]
    
    return configurations


def get_sample_disruption_scenarios() -> List[Dict[str, Any]]:
    """Get sample disruption scenarios for testing"""
    
    scenarios = [
        {
            'disruption_id': str(uuid.uuid4()),
            'disruption_type': 'weather',
            'severity': 'high',
            'status': 'resolved',
            'title': 'Severe Thunderstorms - London Area',
            'description': 'Severe thunderstorms affecting London airports with visibility below minimums',
            'primary_airport': 'LHR',
            'affected_airports': ['LHR', 'LGW', 'STN'],
            'geographical_scope': 'regional',
            'flights_affected_count': 45,
            'passengers_affected_count': 8500,
            'estimated_cost_impact': 1250000.00,
            'actual_cost_impact': 1180000.00,
            'responsible_department': 'Operations Control Center',
            'escalation_level': 2,
            'ai_confidence_score': 0.92
        },
        {
            'disruption_id': str(uuid.uuid4()),
            'disruption_type': 'technical',
            'severity': 'medium',
            'status': 'active',
            'title': 'Aircraft Technical Issue - A320 Fleet',
            'description': 'Recurring technical issue identified in A320 fleet requiring precautionary inspections',
            'primary_airport': 'LHR',
            'affected_airports': ['LHR', 'LGW', 'MAN'],
            'geographical_scope': 'national',
            'flights_affected_count': 12,
            'passengers_affected_count': 2160,
            'estimated_cost_impact': 450000.00,
            'responsible_department': 'Technical Services',
            'escalation_level': 1,
            'ai_confidence_score': 0.87
        }
    ]
    
    return scenarios


# Export functions
__all__ = [
    'get_reference_airports',
    'get_reference_aircraft', 
    'get_sample_crew_members',
    'get_system_configurations',
    'get_sample_disruption_scenarios'
]