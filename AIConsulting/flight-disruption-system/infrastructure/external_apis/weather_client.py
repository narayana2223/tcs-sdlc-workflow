"""
Weather API Client
Integration with weather services for disruption prediction
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .base_client import CachedAPIClient, APIConfig, APIResponse


class WeatherSeverity(str, Enum):
    """Weather severity levels"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"
    EXTREME = "extreme"


class WeatherCondition(str, Enum):
    """Weather condition types"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    MIST = "mist"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    HEAVY_SNOW = "heavy_snow"
    THUNDERSTORM = "thunderstorm"
    HAIL = "hail"
    TORNADO = "tornado"
    HURRICANE = "hurricane"
    DUST_STORM = "dust_storm"
    VOLCANIC_ASH = "volcanic_ash"


@dataclass
class WeatherData:
    """Weather data structure"""
    location: str
    timestamp: datetime
    condition: WeatherCondition
    severity: WeatherSeverity
    temperature_c: float
    humidity_percent: float
    pressure_mb: float
    wind_speed_kmh: float
    wind_direction_degrees: int
    visibility_km: float
    precipitation_mm: float
    cloud_coverage_percent: float
    
    # Aviation-specific data
    ceiling_feet: Optional[int] = None
    runway_visual_range_m: Optional[int] = None
    wind_gust_kmh: Optional[float] = None
    turbulence_level: Optional[str] = None
    icing_conditions: bool = False
    
    # Impact assessment
    flight_impact_score: float = 0.0  # 0-1 scale
    delay_probability: float = 0.0
    cancellation_probability: float = 0.0
    
    @property
    def is_severe_weather(self) -> bool:
        """Check if weather conditions are severe for aviation"""
        return (
            self.severity in [WeatherSeverity.SEVERE, WeatherSeverity.EXTREME] or
            self.condition in [WeatherCondition.THUNDERSTORM, WeatherCondition.TORNADO, WeatherCondition.HURRICANE] or
            self.wind_speed_kmh > 50 or
            self.visibility_km < 1 or
            (self.ceiling_feet and self.ceiling_feet < 500)
        )


@dataclass
class WeatherForecast:
    """Weather forecast data"""
    location: str
    forecast_time: datetime
    valid_from: datetime
    valid_until: datetime
    weather_data: WeatherData
    confidence_percentage: float


@dataclass
class WeatherAlert:
    """Weather alert/warning"""
    alert_id: str
    location: str
    alert_type: str
    severity: WeatherSeverity
    title: str
    description: str
    issued_time: datetime
    valid_from: datetime
    valid_until: datetime
    affected_area_km: float
    aviation_impact: Dict[str, Any]


class WeatherClient(CachedAPIClient):
    """Client for weather data APIs"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config, cache_ttl=300)  # 5 minute cache for weather data
        self.logger = logging.getLogger(__name__)
        
        # Weather impact calculation weights
        self.impact_weights = {
            'visibility': 0.3,
            'wind_speed': 0.25,
            'precipitation': 0.2,
            'ceiling': 0.15,
            'thunderstorm': 0.1
        }
    
    def _get_health_endpoint(self) -> str:
        return "health"
    
    async def authenticate(self) -> bool:
        """Authenticate with weather API"""
        if self.config.mock_mode:
            return True
        
        try:
            response = await self._make_request('POST', 'auth', {
                'api_key': self.config.api_key,
                'service': 'aviation'
            })
            
            if response.success and response.data:
                token = response.data.get('access_token')
                if token:
                    self.config.default_headers['Authorization'] = f'Bearer {token}'
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Weather API authentication failed: {e}")
            return False
    
    async def get_current_weather(self, location: str) -> Optional[WeatherData]:
        """Get current weather for location (airport code or coordinates)"""
        if self.config.mock_mode:
            return self._generate_mock_weather(location)
        
        try:
            response = await self._make_cached_request(
                'GET',
                'current',
                params={
                    'location': location,
                    'include_aviation': True,
                    'units': 'metric'
                }
            )
            
            if response.success and response.data:
                return self._parse_weather_data(response.data, location)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get current weather for {location}: {e}")
            return None
    
    async def get_weather_forecast(
        self,
        location: str,
        hours_ahead: int = 48
    ) -> List[WeatherForecast]:
        """Get weather forecast for location"""
        if self.config.mock_mode:
            return self._generate_mock_forecast(location, hours_ahead)
        
        try:
            response = await self._make_cached_request(
                'GET',
                'forecast',
                params={
                    'location': location,
                    'hours': hours_ahead,
                    'include_aviation': True,
                    'units': 'metric'
                }
            )
            
            if response.success and response.data:
                forecasts = []
                for forecast_data in response.data.get('forecasts', []):
                    forecast = self._parse_weather_forecast(forecast_data, location)
                    if forecast:
                        forecasts.append(forecast)
                return forecasts
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get weather forecast for {location}: {e}")
            return []
    
    async def get_weather_alerts(self, location: str, radius_km: float = 100) -> List[WeatherAlert]:
        """Get weather alerts for location and surrounding area"""
        if self.config.mock_mode:
            return self._generate_mock_alerts(location)
        
        try:
            response = await self._make_cached_request(
                'GET',
                'alerts',
                params={
                    'location': location,
                    'radius': radius_km,
                    'active_only': True
                }
            )
            
            if response.success and response.data:
                alerts = []
                for alert_data in response.data.get('alerts', []):
                    alert = self._parse_weather_alert(alert_data)
                    if alert:
                        alerts.append(alert)
                return alerts
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get weather alerts for {location}: {e}")
            return []
    
    async def get_multiple_locations_weather(
        self,
        locations: List[str]
    ) -> Dict[str, WeatherData]:
        """Get current weather for multiple locations"""
        if self.config.mock_mode:
            return {loc: self._generate_mock_weather(loc) for loc in locations}
        
        try:
            response = await self._make_cached_request(
                'POST',
                'current/bulk',
                data={
                    'locations': locations,
                    'include_aviation': True,
                    'units': 'metric'
                }
            )
            
            if response.success and response.data:
                weather_data = {}
                for location_data in response.data.get('weather_data', []):
                    location = location_data.get('location')
                    if location:
                        weather = self._parse_weather_data(location_data, location)
                        if weather:
                            weather_data[location] = weather
                return weather_data
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get bulk weather data: {e}")
            return {}
    
    async def get_aviation_weather_report(self, airport_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed aviation weather report (METAR/TAF equivalent)"""
        if self.config.mock_mode:
            return self._generate_mock_aviation_report(airport_code)
        
        try:
            response = await self._make_cached_request(
                'GET',
                f'aviation/{airport_code}',
                params={'format': 'detailed'}
            )
            
            if response.success and response.data:
                return response.data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get aviation weather report for {airport_code}: {e}")
            return None
    
    def _parse_weather_data(self, data: Dict[str, Any], location: str) -> Optional[WeatherData]:
        """Parse API response into WeatherData object"""
        try:
            # Parse basic weather data
            weather = WeatherData(
                location=location,
                timestamp=self._parse_datetime(data.get('timestamp')),
                condition=WeatherCondition(data.get('condition', 'clear').lower()),
                severity=WeatherSeverity(data.get('severity', 'light').lower()),
                temperature_c=float(data.get('temperature', 15)),
                humidity_percent=float(data.get('humidity', 50)),
                pressure_mb=float(data.get('pressure', 1013)),
                wind_speed_kmh=float(data.get('wind_speed', 0)),
                wind_direction_degrees=int(data.get('wind_direction', 0)),
                visibility_km=float(data.get('visibility', 10)),
                precipitation_mm=float(data.get('precipitation', 0)),
                cloud_coverage_percent=float(data.get('cloud_coverage', 0))
            )
            
            # Parse aviation-specific data if available
            aviation_data = data.get('aviation', {})
            if aviation_data:
                weather.ceiling_feet = aviation_data.get('ceiling_feet')
                weather.runway_visual_range_m = aviation_data.get('runway_visual_range')
                weather.wind_gust_kmh = aviation_data.get('wind_gust_kmh')
                weather.turbulence_level = aviation_data.get('turbulence_level')
                weather.icing_conditions = aviation_data.get('icing_conditions', False)
            
            # Calculate aviation impact
            weather.flight_impact_score = self._calculate_flight_impact(weather)
            weather.delay_probability = self._calculate_delay_probability(weather)
            weather.cancellation_probability = self._calculate_cancellation_probability(weather)
            
            return weather
            
        except Exception as e:
            self.logger.error(f"Failed to parse weather data: {e}")
            return None
    
    def _parse_weather_forecast(self, data: Dict[str, Any], location: str) -> Optional[WeatherForecast]:
        """Parse forecast data"""
        try:
            weather_data = self._parse_weather_data(data, location)
            if not weather_data:
                return None
            
            return WeatherForecast(
                location=location,
                forecast_time=self._parse_datetime(data.get('forecast_time')),
                valid_from=self._parse_datetime(data.get('valid_from')),
                valid_until=self._parse_datetime(data.get('valid_until')),
                weather_data=weather_data,
                confidence_percentage=float(data.get('confidence', 85))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse weather forecast: {e}")
            return None
    
    def _parse_weather_alert(self, data: Dict[str, Any]) -> Optional[WeatherAlert]:
        """Parse weather alert data"""
        try:
            return WeatherAlert(
                alert_id=data.get('alert_id', ''),
                location=data.get('location', ''),
                alert_type=data.get('alert_type', ''),
                severity=WeatherSeverity(data.get('severity', 'moderate').lower()),
                title=data.get('title', ''),
                description=data.get('description', ''),
                issued_time=self._parse_datetime(data.get('issued_time')),
                valid_from=self._parse_datetime(data.get('valid_from')),
                valid_until=self._parse_datetime(data.get('valid_until')),
                affected_area_km=float(data.get('affected_area_km', 50)),
                aviation_impact=data.get('aviation_impact', {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse weather alert: {e}")
            return None
    
    def _calculate_flight_impact(self, weather: WeatherData) -> float:
        """Calculate flight impact score (0-1)"""
        impact_score = 0.0
        
        # Visibility impact
        if weather.visibility_km < 1:
            impact_score += self.impact_weights['visibility'] * 1.0
        elif weather.visibility_km < 3:
            impact_score += self.impact_weights['visibility'] * 0.7
        elif weather.visibility_km < 8:
            impact_score += self.impact_weights['visibility'] * 0.3
        
        # Wind speed impact
        if weather.wind_speed_kmh > 60:
            impact_score += self.impact_weights['wind_speed'] * 1.0
        elif weather.wind_speed_kmh > 40:
            impact_score += self.impact_weights['wind_speed'] * 0.7
        elif weather.wind_speed_kmh > 25:
            impact_score += self.impact_weights['wind_speed'] * 0.4
        
        # Precipitation impact
        if weather.precipitation_mm > 20:
            impact_score += self.impact_weights['precipitation'] * 0.8
        elif weather.precipitation_mm > 10:
            impact_score += self.impact_weights['precipitation'] * 0.5
        elif weather.precipitation_mm > 2:
            impact_score += self.impact_weights['precipitation'] * 0.2
        
        # Ceiling impact
        if weather.ceiling_feet and weather.ceiling_feet < 200:
            impact_score += self.impact_weights['ceiling'] * 1.0
        elif weather.ceiling_feet and weather.ceiling_feet < 500:
            impact_score += self.impact_weights['ceiling'] * 0.7
        elif weather.ceiling_feet and weather.ceiling_feet < 1000:
            impact_score += self.impact_weights['ceiling'] * 0.4
        
        # Severe weather conditions
        if weather.condition in [WeatherCondition.THUNDERSTORM, WeatherCondition.TORNADO, WeatherCondition.HURRICANE]:
            impact_score += self.impact_weights['thunderstorm'] * 1.0
        elif weather.condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.HEAVY_SNOW, WeatherCondition.HAIL]:
            impact_score += self.impact_weights['thunderstorm'] * 0.6
        
        return min(1.0, impact_score)
    
    def _calculate_delay_probability(self, weather: WeatherData) -> float:
        """Calculate probability of flight delays"""
        base_probability = weather.flight_impact_score * 0.6
        
        # Additional factors
        if weather.condition == WeatherCondition.FOG:
            base_probability += 0.3
        if weather.wind_speed_kmh > 30:
            base_probability += 0.2
        if weather.visibility_km < 5:
            base_probability += 0.2
        
        return min(1.0, base_probability)
    
    def _calculate_cancellation_probability(self, weather: WeatherData) -> float:
        """Calculate probability of flight cancellations"""
        if weather.severity == WeatherSeverity.EXTREME:
            return 0.8
        elif weather.severity == WeatherSeverity.SEVERE:
            return 0.4
        elif weather.is_severe_weather:
            return 0.2
        else:
            return weather.flight_impact_score * 0.1
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_str:
            return datetime.now()
        
        try:
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime.now()
    
    # Mock data generation methods
    def _generate_mock_weather(self, location: str) -> WeatherData:
        """Generate mock weather data"""
        import random
        
        conditions = list(WeatherCondition)
        # Weight towards more common conditions
        condition_weights = [0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.1, 0.02, 0.08, 0.01, 0.02, 0.01, 0.001, 0.001, 0.001, 0.001]
        
        condition = random.choices(conditions, weights=condition_weights)[0]
        
        # Generate weather based on condition
        if condition in [WeatherCondition.THUNDERSTORM, WeatherCondition.TORNADO, WeatherCondition.HURRICANE]:
            severity = random.choice([WeatherSeverity.SEVERE, WeatherSeverity.EXTREME])
            wind_speed = random.uniform(50, 120)
            visibility = random.uniform(0.5, 3)
            precipitation = random.uniform(10, 50)
        elif condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.HEAVY_SNOW]:
            severity = WeatherSeverity.HEAVY
            wind_speed = random.uniform(20, 50)
            visibility = random.uniform(1, 5)
            precipitation = random.uniform(5, 25)
        elif condition == WeatherCondition.FOG:
            severity = random.choice([WeatherSeverity.MODERATE, WeatherSeverity.HEAVY])
            wind_speed = random.uniform(0, 15)
            visibility = random.uniform(0.2, 2)
            precipitation = 0
        else:
            severity = random.choice([WeatherSeverity.LIGHT, WeatherSeverity.MODERATE])
            wind_speed = random.uniform(0, 30)
            visibility = random.uniform(8, 15)
            precipitation = random.uniform(0, 5) if 'rain' in condition.value or 'snow' in condition.value else 0
        
        weather = WeatherData(
            location=location,
            timestamp=datetime.now(),
            condition=condition,
            severity=severity,
            temperature_c=random.uniform(-10, 35),
            humidity_percent=random.uniform(30, 95),
            pressure_mb=random.uniform(980, 1040),
            wind_speed_kmh=wind_speed,
            wind_direction_degrees=random.randint(0, 359),
            visibility_km=visibility,
            precipitation_mm=precipitation,
            cloud_coverage_percent=random.uniform(0, 100),
            ceiling_feet=random.randint(200, 5000) if random.random() > 0.3 else None,
            runway_visual_range_m=random.randint(150, 1200) if visibility < 3 else None,
            wind_gust_kmh=wind_speed * random.uniform(1.2, 1.8) if wind_speed > 20 else None,
            turbulence_level=random.choice(["light", "moderate", "severe"]) if wind_speed > 25 else None,
            icing_conditions=random.random() > 0.8 and condition in [WeatherCondition.SNOW, WeatherCondition.HEAVY_SNOW]
        )
        
        # Calculate impact scores
        weather.flight_impact_score = self._calculate_flight_impact(weather)
        weather.delay_probability = self._calculate_delay_probability(weather)
        weather.cancellation_probability = self._calculate_cancellation_probability(weather)
        
        return weather
    
    def _generate_mock_forecast(self, location: str, hours: int) -> List[WeatherForecast]:
        """Generate mock weather forecast"""
        forecasts = []
        current_time = datetime.now()
        
        for hour in range(0, hours, 3):  # Every 3 hours
            forecast_time = current_time + timedelta(hours=hour)
            weather_data = self._generate_mock_weather(location)
            weather_data.timestamp = forecast_time
            
            forecasts.append(WeatherForecast(
                location=location,
                forecast_time=current_time,
                valid_from=forecast_time,
                valid_until=forecast_time + timedelta(hours=3),
                weather_data=weather_data,
                confidence_percentage=random.uniform(75, 95)
            ))
        
        return forecasts
    
    def _generate_mock_alerts(self, location: str) -> List[WeatherAlert]:
        """Generate mock weather alerts"""
        import random
        from uuid import uuid4
        
        alerts = []
        
        # 30% chance of having alerts
        if random.random() > 0.7:
            num_alerts = random.randint(1, 3)
            alert_types = ["thunderstorm_warning", "high_wind_warning", "visibility_warning", "snow_warning"]
            
            for i in range(num_alerts):
                start_time = datetime.now() + timedelta(hours=random.randint(1, 12))
                
                alerts.append(WeatherAlert(
                    alert_id=str(uuid4()),
                    location=location,
                    alert_type=random.choice(alert_types),
                    severity=random.choice(list(WeatherSeverity)),
                    title=f"Weather Alert {i+1}",
                    description=f"Mock weather alert for {location}",
                    issued_time=datetime.now(),
                    valid_from=start_time,
                    valid_until=start_time + timedelta(hours=random.randint(2, 8)),
                    affected_area_km=random.uniform(25, 150),
                    aviation_impact={
                        'expected_delays': random.uniform(0, 120),
                        'cancellation_risk': random.choice(["low", "medium", "high"]),
                        'affected_operations': random.choice(["departures", "arrivals", "both"])
                    }
                ))
        
        return alerts
    
    def _generate_mock_aviation_report(self, airport_code: str) -> Dict[str, Any]:
        """Generate mock aviation weather report"""
        import random
        
        weather = self._generate_mock_weather(airport_code)
        
        return {
            'airport_code': airport_code,
            'report_time': datetime.now().isoformat(),
            'metar': f"{airport_code} {datetime.now().strftime('%d%H%MZ')} AUTO {random.randint(10, 35):02d}{random.randint(1, 20):02d}KT {random.randint(2, 15):02d}SM CLR {random.randint(15, 30):02d}/{random.randint(10, 25):02d} A{random.randint(2980, 3040)} RMK AO2",
            'taf': f"TAF {airport_code} {datetime.now().strftime('%d%H%MZ')} {(datetime.now() + timedelta(hours=24)).strftime('%d%H%M')} {random.randint(10, 35):02d}{random.randint(5, 15):02d}KT P6SM CLR",
            'current_conditions': {
                'temperature': weather.temperature_c,
                'dewpoint': weather.temperature_c - random.uniform(2, 10),
                'wind_speed_kt': weather.wind_speed_kmh * 0.539957,
                'wind_direction': weather.wind_direction_degrees,
                'visibility_sm': weather.visibility_km * 0.621371,
                'ceiling_ft': weather.ceiling_feet,
                'altimeter_in': weather.pressure_mb * 0.02953
            },
            'impact_assessment': {
                'operational_impact': random.choice(["minimal", "moderate", "significant", "severe"]),
                'delay_factor': weather.delay_probability,
                'recommended_actions': [
                    "Monitor weather conditions closely",
                    "Prepare for potential delays",
                    "Consider alternate airports"
                ]
            }
        }