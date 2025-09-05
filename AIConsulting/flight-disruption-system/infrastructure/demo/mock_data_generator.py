"""
Mock Data Generator for Flight Disruption System Demo
Generates realistic flight data, weather conditions, and disruption scenarios
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..kafka.producers import ProducerFactory, FlightEventProducer, DisruptionEventProducer, ExternalDataProducer
from ..kafka.kafka_config import KafkaConfig


class ScenarioType(str, Enum):
    """Types of demo scenarios"""
    NORMAL_OPERATIONS = "normal_operations"
    WEATHER_DISRUPTION = "weather_disruption"
    TECHNICAL_DELAYS = "technical_delays"
    AIRPORT_CONGESTION = "airport_congestion"
    CASCADING_DELAYS = "cascading_delays"
    AIRLINE_DISRUPTION = "airline_disruption"
    NETWORK_WIDE_CHAOS = "network_wide_chaos"


@dataclass
class AirportInfo:
    """Airport information for realistic data generation"""
    code: str
    name: str
    city: str
    country: str
    timezone: str
    latitude: float
    longitude: float
    hub_airlines: List[str]
    daily_flights: int
    weather_patterns: List[str]


@dataclass
class AirlineInfo:
    """Airline information"""
    code: str
    name: str
    country: str
    fleet_size: int
    hub_airports: List[str]
    route_network: List[Tuple[str, str]]  # (origin, destination) pairs


class MockAirportDatabase:
    """Mock database of airports"""
    
    def __init__(self):
        self.airports = {
            "LHR": AirportInfo("LHR", "London Heathrow", "London", "GB", "Europe/London", 51.4700, -0.4543, ["BA", "VS"], 1300, ["fog", "rain"]),
            "CDG": AirportInfo("CDG", "Paris Charles de Gaulle", "Paris", "FR", "Europe/Paris", 49.0097, 2.5479, ["AF", "KL"], 1400, ["rain", "snow"]),
            "FRA": AirportInfo("FRA", "Frankfurt am Main", "Frankfurt", "DE", "Europe/Berlin", 50.0264, 8.5431, ["LH", "LX"], 1200, ["fog", "snow"]),
            "AMS": AirportInfo("AMS", "Amsterdam Schiphol", "Amsterdam", "NL", "Europe/Amsterdam", 52.3105, 4.7683, ["KL", "AF"], 1100, ["rain", "fog"]),
            "MAD": AirportInfo("MAD", "Madrid Barajas", "Madrid", "ES", "Europe/Madrid", 40.4719, -3.5626, ["IB", "UX"], 900, ["clear", "rain"]),
            "FCO": AirportInfo("FCO", "Rome Fiumicino", "Rome", "IT", "Europe/Rome", 41.7999, 12.2462, ["AZ", "FR"], 800, ["clear", "thunderstorm"]),
            "MUC": AirportInfo("MUC", "Munich", "Munich", "DE", "Europe/Berlin", 48.3537, 11.7750, ["LH", "LX"], 700, ["snow", "fog"]),
            "ZUR": AirportInfo("ZUR", "Zurich", "Zurich", "CH", "Europe/Zurich", 47.4647, 8.5492, ["LX", "LH"], 600, ["snow", "fog"]),
            "VIE": AirportInfo("VIE", "Vienna", "Vienna", "AT", "Europe/Vienna", 48.1103, 16.5697, ["OS", "LH"], 500, ["snow", "rain"]),
            "BRU": AirportInfo("BRU", "Brussels", "Brussels", "BE", "Europe/Brussels", 50.9009, 4.4844, ["SN", "AF"], 600, ["rain", "fog"]),
            "CPH": AirportInfo("CPH", "Copenhagen", "Copenhagen", "DK", "Europe/Copenhagen", 55.6180, 12.6506, ["SK", "SAS"], 650, ["snow", "rain"])
        }
        
        self.airlines = {
            "BA": AirlineInfo("BA", "British Airways", "GB", 280, ["LHR"], [("LHR", "CDG"), ("LHR", "FRA"), ("LHR", "AMS")]),
            "AF": AirlineInfo("AF", "Air France", "FR", 220, ["CDG"], [("CDG", "LHR"), ("CDG", "FRA"), ("CDG", "AMS")]),
            "LH": AirlineInfo("LH", "Lufthansa", "DE", 300, ["FRA", "MUC"], [("FRA", "LHR"), ("MUC", "CDG"), ("FRA", "AMS")]),
            "KL": AirlineInfo("KL", "KLM", "NL", 120, ["AMS"], [("AMS", "LHR"), ("AMS", "CDG"), ("AMS", "FRA")]),
            "IB": AirlineInfo("IB", "Iberia", "ES", 80, ["MAD"], [("MAD", "LHR"), ("MAD", "CDG"), ("MAD", "FRA")]),
            "AZ": AirlineInfo("AZ", "Alitalia", "IT", 100, ["FCO"], [("FCO", "LHR"), ("FCO", "CDG"), ("FCO", "FRA")]),
            "LX": AirlineInfo("LX", "Swiss", "CH", 90, ["ZUR"], [("ZUR", "LHR"), ("ZUR", "CDG"), ("ZUR", "FRA")]),
            "OS": AirlineInfo("OS", "Austrian Airlines", "AT", 80, ["VIE"], [("VIE", "LHR"), ("VIE", "CDG"), ("VIE", "FRA")]),
            "SN": AirlineInfo("SN", "Brussels Airlines", "BE", 60, ["BRU"], [("BRU", "LHR"), ("BRU", "CDG"), ("BRU", "FRA")]),
            "SK": AirlineInfo("SK", "SAS", "DK", 150, ["CPH"], [("CPH", "LHR"), ("CPH", "CDG"), ("CPH", "FRA")])
        }
    
    def get_random_route(self) -> Tuple[AirportInfo, AirportInfo, AirlineInfo]:
        """Get a random realistic route with appropriate airline"""
        airline = random.choice(list(self.airlines.values()))
        route = random.choice(airline.route_network)
        
        origin = self.airports[route[0]]
        destination = self.airports[route[1]]
        
        return origin, destination, airline


class FlightScheduleGenerator:
    """Generates realistic flight schedules"""
    
    def __init__(self, airport_db: MockAirportDatabase):
        self.airport_db = airport_db
        self.aircraft_types = [
            "Boeing 737-800", "Boeing 777-300", "Airbus A320", "Airbus A330", 
            "Airbus A350", "Boeing 787-9", "Embraer E190", "Bombardier CRJ900"
        ]
    
    def generate_flight_schedule(
        self,
        start_time: datetime,
        duration_hours: int = 24,
        flights_per_hour: int = 50
    ) -> List[Dict[str, Any]]:
        """Generate flight schedule for demo period"""
        flights = []
        
        current_time = start_time
        end_time = start_time + timedelta(hours=duration_hours)
        
        while current_time < end_time:
            # Generate flights for current hour
            hour_flights = random.randint(
                int(flights_per_hour * 0.8), 
                int(flights_per_hour * 1.2)
            )
            
            for _ in range(hour_flights):
                flight = self._generate_single_flight(current_time)
                flights.append(flight)
            
            current_time += timedelta(hours=1)
        
        return sorted(flights, key=lambda f: f['scheduled_departure'])
    
    def _generate_single_flight(self, base_time: datetime) -> Dict[str, Any]:
        """Generate a single flight"""
        origin, destination, airline = self.airport_db.get_random_route()
        
        # Random departure time within the hour
        departure_offset = random.randint(0, 3599)  # 0-59:59 minutes
        scheduled_departure = base_time + timedelta(seconds=departure_offset)
        
        # Flight duration based on route (simplified)
        base_duration = self._estimate_flight_duration(origin.code, destination.code)
        actual_duration = base_duration + timedelta(minutes=random.randint(-15, 30))
        scheduled_arrival = scheduled_departure + actual_duration
        
        # Generate flight number
        flight_number = f"{airline.code}{random.randint(100, 9999)}"
        
        flight = {
            'flight_id': str(uuid.uuid4()),
            'flight_number': flight_number,
            'airline_code': airline.code,
            'departure_airport': origin.code,
            'arrival_airport': destination.code,
            'scheduled_departure': scheduled_departure.isoformat(),
            'scheduled_arrival': scheduled_arrival.isoformat(),
            'aircraft_type': random.choice(self.aircraft_types),
            'total_seats': self._get_aircraft_capacity(random.choice(self.aircraft_types)),
            'seats_sold': None,  # Will be set later
            'status': 'scheduled',
            'gate': self._generate_gate(),
            'terminal': str(random.randint(1, 3))
        }
        
        # Set passenger load
        capacity = flight['total_seats']
        load_factor = random.uniform(0.6, 0.95)  # 60-95% load factor
        flight['seats_sold'] = int(capacity * load_factor)
        
        return flight
    
    def _estimate_flight_duration(self, origin: str, destination: str) -> timedelta:
        """Estimate flight duration between airports"""
        # Simplified duration estimation based on airport pairs
        durations = {
            ('LHR', 'CDG'): 1.5, ('CDG', 'LHR'): 1.5,
            ('LHR', 'FRA'): 1.75, ('FRA', 'LHR'): 1.75,
            ('LHR', 'AMS'): 1.25, ('AMS', 'LHR'): 1.25,
            ('CDG', 'FRA'): 1.5, ('FRA', 'CDG'): 1.5,
            ('CDG', 'AMS'): 1.25, ('AMS', 'CDG'): 1.25,
            ('FRA', 'AMS'): 1.0, ('AMS', 'FRA'): 1.0,
        }
        
        key = (origin, destination)
        base_hours = durations.get(key, 2.0)  # Default 2 hours
        
        return timedelta(hours=base_hours)
    
    def _get_aircraft_capacity(self, aircraft_type: str) -> int:
        """Get aircraft seating capacity"""
        capacities = {
            "Boeing 737-800": 189,
            "Boeing 777-300": 396,
            "Airbus A320": 180,
            "Airbus A330": 277,
            "Airbus A350": 325,
            "Boeing 787-9": 290,
            "Embraer E190": 114,
            "Bombardier CRJ900": 90
        }
        
        return capacities.get(aircraft_type, 180)
    
    def _generate_gate(self) -> str:
        """Generate realistic gate number"""
        terminal = random.choice(['A', 'B', 'C', 'D'])
        gate_number = random.randint(1, 30)
        return f"{terminal}{gate_number}"


class WeatherGenerator:
    """Generates realistic weather conditions"""
    
    def __init__(self, airport_db: MockAirportDatabase):
        self.airport_db = airport_db
    
    def generate_weather_data(
        self,
        airport_code: str,
        timestamp: datetime,
        severity_bias: float = 0.0
    ) -> Dict[str, Any]:
        """Generate weather data for an airport"""
        airport = self.airport_db.airports.get(airport_code)
        if not airport:
            airport_code = "LHR"  # Default fallback
            airport = self.airport_db.airports[airport_code]
        
        # Base weather conditions influenced by airport patterns
        possible_conditions = airport.weather_patterns + ["clear", "partly_cloudy", "cloudy"]
        
        # Apply severity bias
        if severity_bias > 0.5:
            # Bias towards more severe weather
            severe_conditions = ["thunderstorm", "heavy_rain", "heavy_snow", "fog"]
            possible_conditions.extend(severe_conditions * 2)  # Double the weight
        
        condition = random.choice(possible_conditions)
        
        # Generate weather parameters based on condition
        weather_data = self._generate_weather_parameters(condition, severity_bias)
        weather_data.update({
            'location': airport_code,
            'condition': condition,
            'timestamp': timestamp.isoformat(),
            'source': 'weather_service_mock'
        })
        
        return weather_data
    
    def _generate_weather_parameters(self, condition: str, severity_bias: float) -> Dict[str, Any]:
        """Generate detailed weather parameters"""
        base_params = {
            'temperature_c': random.uniform(-5, 25),
            'humidity_percent': random.uniform(30, 90),
            'pressure_mb': random.uniform(990, 1030),
            'cloud_coverage_percent': random.uniform(0, 100),
            'wind_direction_degrees': random.randint(0, 359)
        }
        
        # Condition-specific parameters
        if condition == "clear":
            base_params.update({
                'visibility_km': random.uniform(15, 25),
                'precipitation_mm': 0,
                'wind_speed_kmh': random.uniform(5, 20),
                'severity': 'light',
                'flight_impact_score': random.uniform(0.0, 0.2)
            })
        
        elif condition == "fog":
            base_params.update({
                'visibility_km': random.uniform(0.2, 2),
                'precipitation_mm': 0,
                'wind_speed_kmh': random.uniform(0, 10),
                'severity': random.choice(['moderate', 'heavy']),
                'flight_impact_score': random.uniform(0.6, 0.9)
            })
        
        elif condition in ["rain", "heavy_rain"]:
            intensity = 'heavy' if condition == 'heavy_rain' else 'moderate'
            precip_range = (10, 30) if intensity == 'heavy' else (2, 10)
            
            base_params.update({
                'visibility_km': random.uniform(3, 8),
                'precipitation_mm': random.uniform(*precip_range),
                'wind_speed_kmh': random.uniform(10, 40),
                'severity': intensity,
                'flight_impact_score': random.uniform(0.3, 0.7) if intensity == 'moderate' else random.uniform(0.6, 0.9)
            })
        
        elif condition == "thunderstorm":
            base_params.update({
                'visibility_km': random.uniform(1, 5),
                'precipitation_mm': random.uniform(15, 40),
                'wind_speed_kmh': random.uniform(40, 80),
                'severity': 'severe',
                'flight_impact_score': random.uniform(0.8, 1.0),
                'wind_gust_kmh': random.uniform(60, 120)
            })
        
        elif condition in ["snow", "heavy_snow"]:
            intensity = 'heavy' if condition == 'heavy_snow' else 'moderate'
            base_params.update({
                'temperature_c': random.uniform(-10, 2),
                'visibility_km': random.uniform(1, 5) if intensity == 'heavy' else random.uniform(3, 8),
                'precipitation_mm': random.uniform(5, 15) if intensity == 'heavy' else random.uniform(1, 5),
                'wind_speed_kmh': random.uniform(15, 35),
                'severity': intensity,
                'flight_impact_score': random.uniform(0.5, 0.8) if intensity == 'moderate' else random.uniform(0.7, 1.0)
            })
        
        else:  # Default for other conditions
            base_params.update({
                'visibility_km': random.uniform(8, 15),
                'precipitation_mm': random.uniform(0, 2),
                'wind_speed_kmh': random.uniform(10, 30),
                'severity': 'light',
                'flight_impact_score': random.uniform(0.1, 0.4)
            })
        
        # Apply severity bias
        if severity_bias > 0:
            base_params['flight_impact_score'] = min(1.0, base_params['flight_impact_score'] + severity_bias * 0.3)
            base_params['wind_speed_kmh'] *= (1 + severity_bias * 0.5)
            base_params['precipitation_mm'] *= (1 + severity_bias * 0.5)
        
        return base_params


class DisruptionScenarioGenerator:
    """Generates various disruption scenarios for demo"""
    
    def __init__(self, airport_db: MockAirportDatabase):
        self.airport_db = airport_db
        self.weather_generator = WeatherGenerator(airport_db)
    
    def generate_scenario_events(
        self,
        scenario_type: ScenarioType,
        start_time: datetime,
        flights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate events for a specific scenario"""
        if scenario_type == ScenarioType.NORMAL_OPERATIONS:
            return self._generate_normal_operations(start_time, flights)
        elif scenario_type == ScenarioType.WEATHER_DISRUPTION:
            return self._generate_weather_disruption(start_time, flights)
        elif scenario_type == ScenarioType.TECHNICAL_DELAYS:
            return self._generate_technical_delays(start_time, flights)
        elif scenario_type == ScenarioType.AIRPORT_CONGESTION:
            return self._generate_airport_congestion(start_time, flights)
        elif scenario_type == ScenarioType.CASCADING_DELAYS:
            return self._generate_cascading_delays(start_time, flights)
        elif scenario_type == ScenarioType.AIRLINE_DISRUPTION:
            return self._generate_airline_disruption(start_time, flights)
        elif scenario_type == ScenarioType.NETWORK_WIDE_CHAOS:
            return self._generate_network_chaos(start_time, flights)
        else:
            return []
    
    def _generate_normal_operations(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate normal operations with minimal disruptions"""
        events = []
        
        # Add normal weather for all airports
        for airport_code in self.airport_db.airports.keys():
            weather_event = {
                'event_type': 'weather_update',
                'timestamp': start_time.isoformat(),
                'data': self.weather_generator.generate_weather_data(airport_code, start_time, severity_bias=0.0)
            }
            events.append(weather_event)
        
        # Apply minimal delays to some flights (normal operational variance)
        for flight in flights:
            if random.random() < 0.15:  # 15% of flights have minor delays
                delay_minutes = random.randint(5, 30)
                updated_flight = flight.copy()
                
                original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                new_departure = original_departure + timedelta(minutes=delay_minutes)
                
                original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                
                updated_flight.update({
                    'actual_departure': new_departure.isoformat(),
                    'actual_arrival': new_arrival.isoformat(),
                    'delay_minutes': delay_minutes,
                    'status': 'delayed',
                    'event_type': 'DELAYED'
                })
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + timedelta(minutes=random.randint(0, 120))).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events
    
    def _generate_weather_disruption(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate weather-based disruption scenario"""
        events = []
        
        # Choose affected airport
        affected_airport = random.choice(list(self.airport_db.airports.keys()))
        
        # Generate severe weather
        severe_weather = self.weather_generator.generate_weather_data(
            affected_airport, start_time, severity_bias=0.8
        )
        
        weather_event = {
            'event_type': 'weather_update',
            'timestamp': start_time.isoformat(),
            'data': severe_weather
        }
        events.append(weather_event)
        
        # Create disruption event
        disruption_event = {
            'event_type': 'disruption_detected',
            'timestamp': (start_time + timedelta(minutes=15)).isoformat(),
            'data': {
                'disruption_id': str(uuid.uuid4()),
                'disruption_type': 'WEATHER',
                'severity': 'HIGH',
                'cause': severe_weather['condition'],
                'affected_airports': [affected_airport],
                'start_time': start_time.isoformat(),
                'description': f"Severe weather disruption at {affected_airport}",
                'estimated_duration_hours': random.uniform(2, 6)
            }
        }
        events.append(disruption_event)
        
        # Apply weather impacts to flights
        for flight in flights:
            is_affected = (
                flight['departure_airport'] == affected_airport or
                flight['arrival_airport'] == affected_airport
            )
            
            if is_affected:
                impact_probability = 0.8  # 80% of flights affected
                if random.random() < impact_probability:
                    # Determine impact type
                    if random.random() < 0.2:  # 20% cancelled
                        updated_flight = flight.copy()
                        updated_flight.update({
                            'status': 'cancelled',
                            'event_type': 'CANCELLED',
                            'cancellation_reason': f"Weather conditions at {affected_airport}"
                        })
                    else:  # Delayed
                        delay_minutes = random.randint(60, 240)  # 1-4 hour delays
                        updated_flight = flight.copy()
                        
                        original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                        new_departure = original_departure + timedelta(minutes=delay_minutes)
                        
                        original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                        new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                        
                        updated_flight.update({
                            'actual_departure': new_departure.isoformat(),
                            'actual_arrival': new_arrival.isoformat(),
                            'delay_minutes': delay_minutes,
                            'status': 'delayed',
                            'event_type': 'DELAYED',
                            'delay_reason': f"Weather at {affected_airport}"
                        })
                    
                    flight_event = {
                        'event_type': 'flight_update',
                        'timestamp': (start_time + timedelta(minutes=random.randint(30, 120))).isoformat(),
                        'data': updated_flight
                    }
                    events.append(flight_event)
        
        return events
    
    def _generate_technical_delays(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate technical delay scenario"""
        events = []
        
        # Select affected airline
        affected_airline = random.choice(list(self.airport_db.airlines.keys()))
        
        technical_reasons = [
            "Aircraft maintenance issue",
            "Engine inspection required",
            "Avionics system fault",
            "Landing gear inspection",
            "Cabin system malfunction"
        ]
        
        for flight in flights:
            if flight['airline_code'] == affected_airline and random.random() < 0.4:  # 40% of airline's flights affected
                delay_minutes = random.randint(30, 180)
                updated_flight = flight.copy()
                
                original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                new_departure = original_departure + timedelta(minutes=delay_minutes)
                
                original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                
                updated_flight.update({
                    'actual_departure': new_departure.isoformat(),
                    'actual_arrival': new_arrival.isoformat(),
                    'delay_minutes': delay_minutes,
                    'status': 'delayed',
                    'event_type': 'DELAYED',
                    'delay_reason': random.choice(technical_reasons)
                })
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + timedelta(minutes=random.randint(0, 90))).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events
    
    def _generate_airport_congestion(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate airport congestion scenario"""
        events = []
        
        # Choose congested airport
        congested_airport = random.choice(["LHR", "CDG", "FRA", "AMS"])  # Major hubs
        
        # Create disruption event
        disruption_event = {
            'event_type': 'disruption_detected',
            'timestamp': start_time.isoformat(),
            'data': {
                'disruption_id': str(uuid.uuid4()),
                'disruption_type': 'OPERATIONAL',
                'severity': 'MEDIUM',
                'cause': 'Air traffic control congestion',
                'affected_airports': [congested_airport],
                'start_time': start_time.isoformat(),
                'description': f"Air traffic congestion at {congested_airport}",
                'estimated_duration_hours': random.uniform(3, 8)
            }
        }
        events.append(disruption_event)
        
        # Apply congestion delays
        for flight in flights:
            is_affected = (
                flight['departure_airport'] == congested_airport or
                flight['arrival_airport'] == congested_airport
            )
            
            if is_affected and random.random() < 0.6:  # 60% affected
                delay_minutes = random.randint(20, 90)  # Moderate delays
                updated_flight = flight.copy()
                
                original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                new_departure = original_departure + timedelta(minutes=delay_minutes)
                
                original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                
                updated_flight.update({
                    'actual_departure': new_departure.isoformat(),
                    'actual_arrival': new_arrival.isoformat(),
                    'delay_minutes': delay_minutes,
                    'status': 'delayed',
                    'event_type': 'DELAYED',
                    'delay_reason': f"Air traffic congestion at {congested_airport}"
                })
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + timedelta(minutes=random.randint(0, 60))).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events
    
    def _generate_cascading_delays(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cascading delay scenario"""
        events = []
        
        # Start with initial delay at a major hub
        primary_airport = "LHR"  # London Heathrow
        
        # Sort flights by time to simulate cascade effect
        sorted_flights = sorted(flights, key=lambda f: f['scheduled_departure'])
        
        # Initial delays
        initial_delay_base = 30
        
        for i, flight in enumerate(sorted_flights):
            is_affected = (
                flight['departure_airport'] == primary_airport or
                flight['arrival_airport'] == primary_airport
            )
            
            if is_affected:
                # Increasing delays as day progresses
                cascade_factor = min(3.0, 1.0 + (i / len(sorted_flights)) * 2)
                delay_minutes = int(initial_delay_base * cascade_factor) + random.randint(0, 30)
                
                updated_flight = flight.copy()
                
                original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                new_departure = original_departure + timedelta(minutes=delay_minutes)
                
                original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                
                updated_flight.update({
                    'actual_departure': new_departure.isoformat(),
                    'actual_arrival': new_arrival.isoformat(),
                    'delay_minutes': delay_minutes,
                    'status': 'delayed',
                    'event_type': 'DELAYED',
                    'delay_reason': f"Cascading delays from {primary_airport}"
                })
                
                # Events spread over time to show cascade
                event_delay = timedelta(minutes=int(i * 2))  # Spread events
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + event_delay).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events
    
    def _generate_airline_disruption(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate airline-wide disruption"""
        events = []
        
        # Select airline for disruption
        affected_airline = random.choice(list(self.airport_db.airlines.keys()))
        
        disruption_causes = [
            "Crew shortage due to strike action",
            "Fleet-wide technical inspection",
            "IT system outage",
            "Ground handling disruption",
            "Fuel supply issues"
        ]
        
        cause = random.choice(disruption_causes)
        
        # Create airline disruption event
        disruption_event = {
            'event_type': 'disruption_detected',
            'timestamp': start_time.isoformat(),
            'data': {
                'disruption_id': str(uuid.uuid4()),
                'disruption_type': 'OPERATIONAL',
                'severity': 'HIGH',
                'cause': cause,
                'affected_airlines': [affected_airline],
                'start_time': start_time.isoformat(),
                'description': f"{affected_airline} operational disruption: {cause}",
                'estimated_duration_hours': random.uniform(4, 12)
            }
        }
        events.append(disruption_event)
        
        # Impact flights
        for flight in flights:
            if flight['airline_code'] == affected_airline:
                impact_type = random.choices(
                    ['cancelled', 'major_delay', 'minor_delay', 'normal'],
                    weights=[0.3, 0.4, 0.2, 0.1]
                )[0]
                
                if impact_type == 'cancelled':
                    updated_flight = flight.copy()
                    updated_flight.update({
                        'status': 'cancelled',
                        'event_type': 'CANCELLED',
                        'cancellation_reason': cause
                    })
                elif impact_type == 'major_delay':
                    delay_minutes = random.randint(120, 360)  # 2-6 hours
                    updated_flight = flight.copy()
                    
                    original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                    new_departure = original_departure + timedelta(minutes=delay_minutes)
                    
                    original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                    new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                    
                    updated_flight.update({
                        'actual_departure': new_departure.isoformat(),
                        'actual_arrival': new_arrival.isoformat(),
                        'delay_minutes': delay_minutes,
                        'status': 'delayed',
                        'event_type': 'DELAYED',
                        'delay_reason': cause
                    })
                elif impact_type == 'minor_delay':
                    delay_minutes = random.randint(30, 90)
                    updated_flight = flight.copy()
                    
                    original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                    new_departure = original_departure + timedelta(minutes=delay_minutes)
                    
                    original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                    new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                    
                    updated_flight.update({
                        'actual_departure': new_departure.isoformat(),
                        'actual_arrival': new_arrival.isoformat(),
                        'delay_minutes': delay_minutes,
                        'status': 'delayed',
                        'event_type': 'DELAYED',
                        'delay_reason': cause
                    })
                else:
                    continue  # No impact
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + timedelta(minutes=random.randint(15, 120))).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events
    
    def _generate_network_chaos(self, start_time: datetime, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate network-wide chaos scenario"""
        events = []
        
        # Multiple simultaneous disruptions
        chaos_events = [
            ("LHR", "WEATHER", "Severe thunderstorms"),
            ("CDG", "OPERATIONAL", "Air traffic control strike"),
            ("FRA", "TECHNICAL", "Runway closure for emergency"),
            ("AMS", "OPERATIONAL", "Ground handling shortage")
        ]
        
        # Create multiple disruption events
        for i, (airport, disruption_type, cause) in enumerate(chaos_events):
            disruption_event = {
                'event_type': 'disruption_detected',
                'timestamp': (start_time + timedelta(minutes=i * 30)).isoformat(),
                'data': {
                    'disruption_id': str(uuid.uuid4()),
                    'disruption_type': disruption_type,
                    'severity': 'HIGH' if i < 2 else 'MEDIUM',
                    'cause': cause,
                    'affected_airports': [airport],
                    'start_time': (start_time + timedelta(minutes=i * 30)).isoformat(),
                    'description': f"{cause} at {airport}",
                    'estimated_duration_hours': random.uniform(2, 8)
                }
            }
            events.append(disruption_event)
        
        # Massive flight impacts
        affected_airports = {event[0] for event in chaos_events}
        
        for flight in flights:
            is_affected = (
                flight['departure_airport'] in affected_airports or
                flight['arrival_airport'] in affected_airports
            )
            
            if is_affected:
                impact_severity = random.choices(
                    ['cancelled', 'major_delay', 'moderate_delay'],
                    weights=[0.4, 0.4, 0.2]
                )[0]
                
                if impact_severity == 'cancelled':
                    updated_flight = flight.copy()
                    updated_flight.update({
                        'status': 'cancelled',
                        'event_type': 'CANCELLED',
                        'cancellation_reason': "Network-wide disruptions"
                    })
                else:
                    delay_range = (180, 480) if impact_severity == 'major_delay' else (60, 180)
                    delay_minutes = random.randint(*delay_range)
                    
                    updated_flight = flight.copy()
                    
                    original_departure = datetime.fromisoformat(flight['scheduled_departure'])
                    new_departure = original_departure + timedelta(minutes=delay_minutes)
                    
                    original_arrival = datetime.fromisoformat(flight['scheduled_arrival'])
                    new_arrival = original_arrival + timedelta(minutes=delay_minutes)
                    
                    updated_flight.update({
                        'actual_departure': new_departure.isoformat(),
                        'actual_arrival': new_arrival.isoformat(),
                        'delay_minutes': delay_minutes,
                        'status': 'delayed',
                        'event_type': 'DELAYED',
                        'delay_reason': "Network disruptions"
                    })
                
                flight_event = {
                    'event_type': 'flight_update',
                    'timestamp': (start_time + timedelta(minutes=random.randint(0, 180))).isoformat(),
                    'data': updated_flight
                }
                events.append(flight_event)
        
        return events


class MockDataStreamer:
    """Streams mock data to Kafka topics"""
    
    def __init__(self, kafka_config: KafkaConfig):
        self.kafka_config = kafka_config
        self.producer_factory = ProducerFactory(kafka_config)
        self.logger = logging.getLogger(__name__)
        
        # Create specialized producers
        self.flight_producer = self.producer_factory.create_flight_producer()
        self.disruption_producer = self.producer_factory.create_disruption_producer()
        self.external_data_producer = self.producer_factory.create_external_data_producer()
        
        self.is_streaming = False
    
    async def stream_scenario(
        self,
        scenario_type: ScenarioType,
        duration_hours: int = 8,
        speed_multiplier: float = 1.0
    ):
        """Stream a complete scenario"""
        self.logger.info(f"Starting scenario stream: {scenario_type.value}")
        
        # Initialize components
        airport_db = MockAirportDatabase()
        flight_generator = FlightScheduleGenerator(airport_db)
        scenario_generator = DisruptionScenarioGenerator(airport_db)
        
        # Generate scenario data
        start_time = datetime.now()
        flights = flight_generator.generate_flight_schedule(start_time, duration_hours, flights_per_hour=30)
        events = scenario_generator.generate_scenario_events(scenario_type, start_time, flights)
        
        # Sort all events by timestamp
        all_events = []
        
        # Add flight events
        for flight in flights:
            all_events.append({
                'event_type': 'flight_scheduled',
                'timestamp': flight['scheduled_departure'],
                'data': flight
            })
        
        # Add scenario events
        all_events.extend(events)
        
        # Sort by timestamp
        all_events.sort(key=lambda e: datetime.fromisoformat(e['timestamp']))
        
        self.is_streaming = True
        self.logger.info(f"Generated {len(all_events)} events for streaming")
        
        # Stream events
        stream_start_time = time.time()
        scenario_start_time = datetime.fromisoformat(all_events[0]['timestamp'])
        
        for event in all_events:
            if not self.is_streaming:
                break
            
            # Calculate delay based on event timestamp and speed multiplier
            event_time = datetime.fromisoformat(event['timestamp'])
            scenario_elapsed = (event_time - scenario_start_time).total_seconds()
            real_elapsed = time.time() - stream_start_time
            
            target_time = scenario_elapsed / speed_multiplier
            sleep_time = target_time - real_elapsed
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
            # Send event
            try:
                await self._send_event(event)
            except Exception as e:
                self.logger.error(f"Failed to send event: {e}")
        
        self.logger.info("Scenario streaming completed")
    
    async def _send_event(self, event: Dict[str, Any]):
        """Send individual event to appropriate Kafka topic"""
        event_type = event['event_type']
        data = event['data']
        
        try:
            if event_type in ['flight_scheduled', 'flight_update']:
                if event_type == 'flight_scheduled':
                    success = self.flight_producer.send_flight_scheduled(
                        flight_id=data['flight_id'],
                        flight_number=data['flight_number'],
                        airline_code=data['airline_code'],
                        departure_airport=data['departure_airport'],
                        arrival_airport=data['arrival_airport'],
                        scheduled_departure=datetime.fromisoformat(data['scheduled_departure']),
                        scheduled_arrival=datetime.fromisoformat(data['scheduled_arrival']),
                        **{k: v for k, v in data.items() if k not in ['scheduled_departure', 'scheduled_arrival']}
                    )
                elif data.get('event_type') == 'DELAYED':
                    success = self.flight_producer.send_flight_delayed(
                        flight_id=data['flight_id'],
                        delay_minutes=data.get('delay_minutes', 0),
                        reason=data.get('delay_reason', 'Unknown'),
                        new_departure_time=datetime.fromisoformat(data['actual_departure']),
                        new_arrival_time=datetime.fromisoformat(data['actual_arrival']),
                        **{k: v for k, v in data.items() if k not in ['actual_departure', 'actual_arrival']}
                    )
                elif data.get('event_type') == 'CANCELLED':
                    success = self.flight_producer.send_flight_cancelled(
                        flight_id=data['flight_id'],
                        reason=data.get('cancellation_reason', 'Unknown'),
                        **{k: v for k, v in data.items() if k != 'cancellation_reason'}
                    )
                
                if success:
                    self.logger.debug(f"Sent flight event: {data.get('flight_number', 'Unknown')}")
            
            elif event_type == 'disruption_detected':
                success = self.disruption_producer.send_disruption_started(
                    disruption_id=data['disruption_id'],
                    disruption_type=data['disruption_type'],
                    severity=data['severity'],
                    cause=data['cause'],
                    affected_airports=data.get('affected_airports', []),
                    affected_flights=data.get('affected_flights', []),
                    start_time=datetime.fromisoformat(data['start_time']),
                    description=data['description'],
                    **{k: v for k, v in data.items() if k not in ['start_time']}
                )
                
                if success:
                    self.logger.debug(f"Sent disruption event: {data.get('disruption_type', 'Unknown')}")
            
            elif event_type == 'weather_update':
                success = self.external_data_producer.send_weather_data(
                    location=data['location'],
                    weather_data=data,
                    quality_score=0.95
                )
                
                if success:
                    self.logger.debug(f"Sent weather event: {data.get('location', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error sending event {event_type}: {e}")
    
    def stop_streaming(self):
        """Stop the streaming process"""
        self.is_streaming = False
        self.logger.info("Stopping event streaming")
    
    def close(self):
        """Close all producers"""
        self.producer_factory.close_all()


# Convenience functions for demo setup
async def run_demo_scenario(
    kafka_config: KafkaConfig,
    scenario: ScenarioType = ScenarioType.WEATHER_DISRUPTION,
    duration_hours: int = 4,
    speed_multiplier: float = 10.0
):
    """Run a complete demo scenario"""
    streamer = MockDataStreamer(kafka_config)
    
    try:
        await streamer.stream_scenario(scenario, duration_hours, speed_multiplier)
    finally:
        streamer.close()


def get_available_scenarios() -> List[Dict[str, str]]:
    """Get list of available demo scenarios"""
    return [
        {
            'type': ScenarioType.NORMAL_OPERATIONS.value,
            'name': 'Normal Operations',
            'description': 'Typical day with minimal disruptions and normal delays'
        },
        {
            'type': ScenarioType.WEATHER_DISRUPTION.value,
            'name': 'Weather Disruption',
            'description': 'Severe weather at major hub causing widespread delays and cancellations'
        },
        {
            'type': ScenarioType.TECHNICAL_DELAYS.value,
            'name': 'Technical Delays',
            'description': 'Airline-wide technical issues causing systematic delays'
        },
        {
            'type': ScenarioType.AIRPORT_CONGESTION.value,
            'name': 'Airport Congestion',
            'description': 'Air traffic control congestion at major hub airport'
        },
        {
            'type': ScenarioType.CASCADING_DELAYS.value,
            'name': 'Cascading Delays',
            'description': 'Initial delays that cascade throughout the day and network'
        },
        {
            'type': ScenarioType.AIRLINE_DISRUPTION.value,
            'name': 'Airline Disruption',
            'description': 'Major airline operational disruption affecting entire fleet'
        },
        {
            'type': ScenarioType.NETWORK_WIDE_CHAOS.value,
            'name': 'Network-Wide Chaos',
            'description': 'Multiple simultaneous disruptions across major airports'
        }
    ]