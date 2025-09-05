import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from dataclasses import dataclass
from config import ExternalAPIConfig

logger = structlog.get_logger()

@dataclass
class WeatherCondition:
    """Weather condition data structure"""
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: int
    visibility: float
    precipitation: float
    cloud_cover: int
    condition: str
    severity: str
    timestamp: datetime

@dataclass
class WeatherForecast:
    """Weather forecast data structure"""
    location: str
    airport_code: str
    current_conditions: WeatherCondition
    hourly_forecast: List[WeatherCondition]
    alerts: List[Dict[str, Any]]
    last_updated: datetime

class WeatherAPIClient:
    """Weather API client for flight disruption prediction"""
    
    def __init__(self, config: ExternalAPIConfig):
        self.config = config
        self.api_key = config.weather_api_key
        self.base_url = config.weather_api_url
        self.http_client: Optional[httpx.AsyncClient] = None
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def start(self):
        """Initialize HTTP client"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info("Weather API client started")
    
    async def stop(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("Weather API client stopped")
    
    async def get_current_weather(self, airport_code: str) -> Optional[WeatherForecast]:
        """Get current weather conditions for airport"""
        try:
            # Check cache first
            cached = self._get_cached_weather(airport_code)
            if cached:
                return cached
            
            # Demo mode - return mock data
            if self.config.demo_mode:
                return self._generate_mock_weather(airport_code)
            
            # Make API request
            url = f"{self.base_url}/current"
            params = {
                'key': self.api_key,
                'q': airport_code,
                'aqi': 'yes'
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            weather_forecast = self._parse_weather_response(airport_code, data)
            
            # Cache the result
            self._cache_weather(airport_code, weather_forecast)
            
            logger.info(
                "Weather data retrieved",
                airport=airport_code,
                condition=weather_forecast.current_conditions.condition
            )
            
            return weather_forecast
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "Weather API HTTP error",
                airport=airport_code,
                status_code=e.response.status_code,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error("Weather API error", airport=airport_code, error=str(e))
            return None
    
    async def get_weather_forecast(
        self, 
        airport_code: str, 
        hours: int = 24
    ) -> Optional[WeatherForecast]:
        """Get weather forecast for airport"""
        try:
            # Demo mode - return mock data
            if self.config.demo_mode:
                return self._generate_mock_forecast(airport_code, hours)
            
            url = f"{self.base_url}/forecast"
            params = {
                'key': self.api_key,
                'q': airport_code,
                'days': max(1, hours // 24 + 1),
                'aqi': 'yes',
                'alerts': 'yes'
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            weather_forecast = self._parse_forecast_response(airport_code, data, hours)
            
            logger.info(
                "Weather forecast retrieved",
                airport=airport_code,
                hours=hours,
                alerts=len(weather_forecast.alerts)
            )
            
            return weather_forecast
            
        except Exception as e:
            logger.error("Weather forecast error", airport=airport_code, error=str(e))
            return None
    
    async def get_weather_alerts(self, airport_code: str) -> List[Dict[str, Any]]:
        """Get weather alerts for airport"""
        try:
            weather_forecast = await self.get_weather_forecast(airport_code)
            if weather_forecast:
                return weather_forecast.alerts
            return []
            
        except Exception as e:
            logger.error("Weather alerts error", airport=airport_code, error=str(e))
            return []
    
    async def get_disruption_risk_assessment(
        self, 
        airport_code: str, 
        flight_time: datetime
    ) -> Dict[str, Any]:
        """Assess weather-related disruption risk for specific flight time"""
        try:
            weather_forecast = await self.get_weather_forecast(airport_code, hours=6)
            if not weather_forecast:
                return {'risk_level': 'unknown', 'confidence': 0.0}
            
            # Find weather condition closest to flight time
            target_condition = self._find_closest_condition(
                weather_forecast.hourly_forecast, 
                flight_time
            )
            
            if not target_condition:
                target_condition = weather_forecast.current_conditions
            
            # Calculate risk factors
            risk_assessment = self._calculate_weather_risk(target_condition, weather_forecast.alerts)
            
            logger.info(
                "Weather risk assessment completed",
                airport=airport_code,
                flight_time=flight_time,
                risk_level=risk_assessment['risk_level']
            )
            
            return risk_assessment
            
        except Exception as e:
            logger.error("Weather risk assessment error", airport=airport_code, error=str(e))
            return {'risk_level': 'unknown', 'confidence': 0.0}
    
    async def get_multiple_airports_weather(
        self, 
        airport_codes: List[str]
    ) -> Dict[str, Optional[WeatherForecast]]:
        """Get weather for multiple airports concurrently"""
        try:
            tasks = [
                self.get_current_weather(airport_code) 
                for airport_code in airport_codes
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            weather_data = {}
            for airport_code, result in zip(airport_codes, results):
                if isinstance(result, Exception):
                    logger.error(
                        "Weather fetch failed for airport",
                        airport=airport_code,
                        error=str(result)
                    )
                    weather_data[airport_code] = None
                else:
                    weather_data[airport_code] = result
            
            return weather_data
            
        except Exception as e:
            logger.error("Multiple airports weather error", error=str(e))
            return {airport: None for airport in airport_codes}
    
    def _get_cached_weather(self, airport_code: str) -> Optional[WeatherForecast]:
        """Get weather from cache if still valid"""
        if airport_code in self.cache:
            cached_data = self.cache[airport_code]
            cache_time = cached_data.get('cached_at')
            if cache_time and (datetime.utcnow() - cache_time).seconds < self.cache_ttl:
                return cached_data.get('forecast')
        return None
    
    def _cache_weather(self, airport_code: str, forecast: WeatherForecast):
        """Cache weather data"""
        self.cache[airport_code] = {
            'forecast': forecast,
            'cached_at': datetime.utcnow()
        }
    
    def _parse_weather_response(self, airport_code: str, data: Dict[str, Any]) -> WeatherForecast:
        """Parse weather API response"""
        current = data.get('current', {})
        location = data.get('location', {})
        
        condition = WeatherCondition(
            temperature=current.get('temp_c', 15.0),
            humidity=current.get('humidity', 50),
            wind_speed=current.get('wind_kph', 0.0),
            wind_direction=current.get('wind_degree', 0),
            visibility=current.get('vis_km', 10.0),
            precipitation=current.get('precip_mm', 0.0),
            cloud_cover=current.get('cloud', 0),
            condition=current.get('condition', {}).get('text', 'Clear'),
            severity=self._assess_condition_severity(current),
            timestamp=datetime.utcnow()
        )
        
        return WeatherForecast(
            location=location.get('name', airport_code),
            airport_code=airport_code,
            current_conditions=condition,
            hourly_forecast=[condition],  # Would parse hourly data in full implementation
            alerts=[],
            last_updated=datetime.utcnow()
        )
    
    def _parse_forecast_response(
        self, 
        airport_code: str, 
        data: Dict[str, Any], 
        hours: int
    ) -> WeatherForecast:
        """Parse forecast API response"""
        # Simplified parsing - full implementation would parse all forecast data
        return self._parse_weather_response(airport_code, data)
    
    def _generate_mock_weather(self, airport_code: str) -> WeatherForecast:
        """Generate mock weather data for demo mode"""
        import random
        
        # Simulate different weather conditions for different airports
        weather_scenarios = {
            'LHR': {'temp': 12, 'condition': 'Cloudy', 'wind': 15, 'visibility': 8},
            'CDG': {'temp': 14, 'condition': 'Light Rain', 'wind': 12, 'visibility': 6},
            'FRA': {'temp': 8, 'condition': 'Fog', 'wind': 5, 'visibility': 2},
            'AMS': {'temp': 10, 'condition': 'Overcast', 'wind': 20, 'visibility': 7},
            'MAD': {'temp': 18, 'condition': 'Sunny', 'wind': 8, 'visibility': 10}
        }
        
        scenario = weather_scenarios.get(airport_code, {
            'temp': random.randint(5, 25),
            'condition': 'Clear',
            'wind': random.randint(0, 30),
            'visibility': random.randint(1, 10)
        })
        
        condition = WeatherCondition(
            temperature=scenario['temp'],
            humidity=random.randint(30, 90),
            wind_speed=scenario['wind'],
            wind_direction=random.randint(0, 360),
            visibility=scenario['visibility'],
            precipitation=random.uniform(0, 5) if 'Rain' in scenario['condition'] else 0,
            cloud_cover=random.randint(10, 90),
            condition=scenario['condition'],
            severity=self._assess_condition_severity({'vis_km': scenario['visibility'], 'wind_kph': scenario['wind']}),
            timestamp=datetime.utcnow()
        )
        
        # Generate alerts for severe conditions
        alerts = []
        if scenario['visibility'] < 3:
            alerts.append({
                'type': 'fog_warning',
                'severity': 'high',
                'message': f'Dense fog at {airport_code}. Visibility {scenario["visibility"]}km.',
                'issued_at': datetime.utcnow()
            })
        
        if scenario['wind'] > 25:
            alerts.append({
                'type': 'wind_warning',
                'severity': 'medium',
                'message': f'Strong winds at {airport_code}. Wind speed {scenario["wind"]}kph.',
                'issued_at': datetime.utcnow()
            })
        
        return WeatherForecast(
            location=f"{airport_code} Airport",
            airport_code=airport_code,
            current_conditions=condition,
            hourly_forecast=[condition],
            alerts=alerts,
            last_updated=datetime.utcnow()
        )
    
    def _generate_mock_forecast(self, airport_code: str, hours: int) -> WeatherForecast:
        """Generate mock forecast data"""
        base_forecast = self._generate_mock_weather(airport_code)
        
        # Generate hourly forecast by slightly varying base conditions
        hourly_forecast = []
        for i in range(hours):
            condition = WeatherCondition(
                temperature=base_forecast.current_conditions.temperature + (i * 0.5),
                humidity=min(100, base_forecast.current_conditions.humidity + (i * 2)),
                wind_speed=max(0, base_forecast.current_conditions.wind_speed + (i * 0.5)),
                wind_direction=base_forecast.current_conditions.wind_direction,
                visibility=base_forecast.current_conditions.visibility,
                precipitation=base_forecast.current_conditions.precipitation,
                cloud_cover=base_forecast.current_conditions.cloud_cover,
                condition=base_forecast.current_conditions.condition,
                severity=base_forecast.current_conditions.severity,
                timestamp=datetime.utcnow() + timedelta(hours=i)
            )
            hourly_forecast.append(condition)
        
        base_forecast.hourly_forecast = hourly_forecast
        return base_forecast
    
    def _find_closest_condition(
        self, 
        hourly_forecast: List[WeatherCondition], 
        target_time: datetime
    ) -> Optional[WeatherCondition]:
        """Find weather condition closest to target time"""
        if not hourly_forecast:
            return None
        
        closest_condition = None
        min_time_diff = float('inf')
        
        for condition in hourly_forecast:
            time_diff = abs((condition.timestamp - target_time).total_seconds())
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_condition = condition
        
        return closest_condition
    
    def _assess_condition_severity(self, condition_data: Dict[str, Any]) -> str:
        """Assess weather condition severity"""
        visibility = condition_data.get('vis_km', 10.0)
        wind_speed = condition_data.get('wind_kph', 0.0)
        precipitation = condition_data.get('precip_mm', 0.0)
        
        # High severity conditions
        if visibility < 1.0 or wind_speed > 50 or precipitation > 10:
            return 'high'
        
        # Medium severity conditions
        if visibility < 3.0 or wind_speed > 25 or precipitation > 2:
            return 'medium'
        
        return 'low'
    
    def _calculate_weather_risk(
        self, 
        condition: WeatherCondition, 
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate weather-related disruption risk"""
        risk_score = 0.0
        risk_factors = []
        
        # Visibility risk
        if condition.visibility < 1.0:
            risk_score += 0.4
            risk_factors.append('low_visibility')
        elif condition.visibility < 3.0:
            risk_score += 0.2
            risk_factors.append('reduced_visibility')
        
        # Wind risk
        if condition.wind_speed > 50:
            risk_score += 0.3
            risk_factors.append('severe_wind')
        elif condition.wind_speed > 25:
            risk_score += 0.15
            risk_factors.append('strong_wind')
        
        # Precipitation risk
        if condition.precipitation > 10:
            risk_score += 0.2
            risk_factors.append('heavy_precipitation')
        elif condition.precipitation > 2:
            risk_score += 0.1
            risk_factors.append('moderate_precipitation')
        
        # Alert-based risk
        for alert in alerts:
            if alert.get('severity') == 'high':
                risk_score += 0.3
                risk_factors.append(f'alert_{alert.get("type")}')
            elif alert.get('severity') == 'medium':
                risk_score += 0.15
                risk_factors.append(f'alert_{alert.get("type")}')
        
        # Determine risk level
        risk_score = min(risk_score, 1.0)
        
        if risk_score > 0.7:
            risk_level = 'high'
        elif risk_score > 0.4:
            risk_level = 'medium'
        elif risk_score > 0.1:
            risk_level = 'low'
        else:
            risk_level = 'minimal'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'confidence': 0.85 if not self.config.demo_mode else 0.95,
            'weather_condition': condition.condition,
            'visibility_km': condition.visibility,
            'wind_speed_kph': condition.wind_speed,
            'alerts_count': len(alerts)
        }
    
    async def health_check(self) -> bool:
        """Check if weather API is accessible"""
        try:
            if self.config.demo_mode:
                return True
            
            # Simple health check endpoint
            response = await self.http_client.get(
                f"{self.base_url}/current",
                params={'key': self.api_key, 'q': 'London'},
                timeout=5.0
            )
            return response.status_code == 200
            
        except Exception:
            return False