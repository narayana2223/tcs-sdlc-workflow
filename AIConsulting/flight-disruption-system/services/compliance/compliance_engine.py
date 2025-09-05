import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4
import redis.asyncio as redis
import httpx
from database import Database
from config import settings

logger = structlog.get_logger()

class ComplianceEngine:
    """Main compliance engine that orchestrates regulation checks"""
    
    def __init__(
        self, 
        db: Database, 
        redis_client: redis.Redis, 
        http_client: httpx.AsyncClient,
        regulation_engines: Dict[str, Any]
    ):
        self.db = db
        self.redis = redis_client
        self.http_client = http_client
        self.regulation_engines = regulation_engines
    
    async def check_compliance(
        self,
        flight_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        disruption_info: Dict[str, Any],
        regulations: List[str]
    ) -> Dict[str, Any]:
        """Perform comprehensive compliance check"""
        
        try:
            compliance_id = str(uuid4())
            
            logger.info(
                "Starting compliance check",
                compliance_id=compliance_id,
                passenger_id=passenger_info.get('passenger_id'),
                regulations=regulations
            )
            
            # Initialize result structure
            compliance_result = {
                'compliance_id': compliance_id,
                'passenger_id': passenger_info.get('passenger_id'),
                'flight_id': flight_info.get('flight_id'),
                'disruption_id': disruption_info.get('disruption_id'),
                'regulations_checked': regulations,
                'compliance_status': {},
                'eligible_compensation': {},
                'total_compensation': 0.0,
                'compensation_breakdown': {},
                'compliance_reasons': [],
                'required_actions': [],
                'claim_deadline': None,
                'care_obligations': {},
                'processing_time_seconds': 0.0,
                'created_at': datetime.utcnow()
            }
            
            # Calculate delay information
            delay_info = self._calculate_delay_info(flight_info, disruption_info)
            
            # Check each regulation
            for regulation_type in regulations:
                if regulation_type.value in self.regulation_engines:
                    engine = self.regulation_engines[regulation_type.value]
                    
                    # Perform regulation-specific check
                    reg_result = await engine.check_compliance(
                        flight_info, passenger_info, disruption_info, delay_info
                    )
                    
                    compliance_result['compliance_status'][regulation_type.value] = reg_result['status']
                    compliance_result['eligible_compensation'][regulation_type.value] = reg_result['compensation']
                    compliance_result['compensation_breakdown'][regulation_type.value] = reg_result['breakdown']
                    
                    # Accumulate total compensation
                    compliance_result['total_compensation'] += reg_result['compensation']
                    
                    # Add regulation-specific reasons
                    compliance_result['compliance_reasons'].extend(reg_result.get('reasons', []))
                    
                    # Add required actions
                    compliance_result['required_actions'].extend(reg_result.get('actions', []))
                    
                    # Update care obligations
                    if reg_result.get('care_obligations'):
                        compliance_result['care_obligations'].update(reg_result['care_obligations'])
            
            # Set claim deadline (longest among all regulations)
            compliance_result['claim_deadline'] = self._calculate_claim_deadline(regulations)
            
            # Generate summary recommendations
            compliance_result['required_actions'] = list(set(compliance_result['required_actions']))
            compliance_result['compliance_reasons'] = list(set(compliance_result['compliance_reasons']))
            
            logger.info(
                "Compliance check completed",
                compliance_id=compliance_id,
                total_compensation=compliance_result['total_compensation'],
                regulations_processed=len(regulations)
            )
            
            return compliance_result
            
        except Exception as e:
            logger.error("Compliance check failed", error=str(e))
            raise
    
    def _calculate_delay_info(
        self, 
        flight_info: Dict[str, Any], 
        disruption_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate delay information"""
        
        scheduled_departure = flight_info.get('scheduled_departure')
        actual_departure = flight_info.get('actual_departure')
        
        if isinstance(scheduled_departure, str):
            scheduled_departure = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
        
        if actual_departure:
            if isinstance(actual_departure, str):
                actual_departure = datetime.fromisoformat(actual_departure.replace('Z', '+00:00'))
            delay_minutes = int((actual_departure - scheduled_departure).total_seconds() / 60)
        else:
            # Use disruption info if actual departure not available
            delay_minutes = disruption_info.get('delay_minutes', 0)
        
        return {
            'delay_minutes': max(0, delay_minutes),
            'delay_hours': max(0, delay_minutes / 60),
            'scheduled_departure': scheduled_departure,
            'actual_departure': actual_departure,
            'is_significant_delay': delay_minutes >= settings.min_compensation_delay,
            'is_severe_delay': delay_minutes >= settings.severe_delay_threshold
        }
    
    def _calculate_claim_deadline(self, regulations: List[str]) -> datetime:
        """Calculate claim deadline based on regulations"""
        
        # Different regulations have different claim periods
        deadline_days = {
            'eu261': 365 * 6,  # 6 years for EU261
            'uk_caa': 365 * 6,  # 6 years for UK CAA
            'us_dot': 365 * 3,  # 3 years for US DOT
            'iata': 365 * 2,   # 2 years for IATA
            'montreal_convention': 365 * 2  # 2 years
        }
        
        # Use the longest applicable period
        max_days = 0
        for regulation in regulations:
            reg_days = deadline_days.get(regulation.value, settings.claim_deadline_days)
            max_days = max(max_days, reg_days)
        
        return datetime.utcnow() + timedelta(days=max_days)
    
    async def create_compliance_request_from_disruption(
        self,
        flight_id: str,
        passenger: Dict[str, Any],
        disruption_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create compliance request from disruption event"""
        
        try:
            # Get flight information
            flight_info = await self.db.get_flight_info(flight_id)
            if not flight_info:
                raise ValueError(f"Flight {flight_id} not found")
            
            # Format passenger info
            passenger_info = {
                'passenger_id': passenger.get('id'),
                'pnr': passenger.get('pnr'),
                'first_name': passenger.get('first_name'),
                'last_name': passenger.get('last_name'),
                'email': passenger.get('email'),
                'phone': passenger.get('phone'),
                'nationality': passenger.get('nationality', 'GB'),
                'ticket_price': passenger.get('ticket_price', 200.0),
                'booking_class': passenger.get('booking_class', 'economy'),
                'mobility_assistance': passenger.get('mobility_assistance', False)
            }
            
            # Format disruption info
            disruption_info = {
                'disruption_id': disruption_data.get('disruption_id'),
                'disruption_type': disruption_data.get('type', 'unknown'),
                'cause': disruption_data.get('cause', 'Unknown cause'),
                'delay_minutes': disruption_data.get('estimated_delay_minutes', 0),
                'is_extraordinary_circumstance': self._is_extraordinary_circumstance(
                    disruption_data.get('type'),
                    disruption_data.get('cause')
                ),
                'weather_data': disruption_data.get('weather_data'),
                'airline_fault': not self._is_extraordinary_circumstance(
                    disruption_data.get('type'),
                    disruption_data.get('cause')
                )
            }
            
            # Determine applicable regulations
            regulations = self._determine_applicable_regulations(flight_info, passenger_info)
            
            return {
                'flight_info': flight_info,
                'passenger_info': passenger_info,
                'disruption_info': disruption_info,
                'regulations': regulations
            }
            
        except Exception as e:
            logger.error("Failed to create compliance request", error=str(e))
            raise
    
    def _is_extraordinary_circumstance(self, disruption_type: str, cause: str) -> bool:
        """Determine if disruption qualifies as extraordinary circumstance"""
        
        extraordinary_types = settings.extraordinary_circumstances.split(',')
        
        # Check disruption type
        if disruption_type.lower() in [t.strip().lower() for t in extraordinary_types]:
            return True
        
        # Check cause keywords
        extraordinary_keywords = [
            'weather', 'storm', 'fog', 'snow', 'ice', 'volcanic ash',
            'security', 'terrorism', 'political', 'strike', 'atc',
            'air traffic control', 'airport closure', 'pandemic'
        ]
        
        cause_lower = cause.lower()
        for keyword in extraordinary_keywords:
            if keyword in cause_lower:
                return True
        
        return False
    
    def _determine_applicable_regulations(
        self, 
        flight_info: Dict[str, Any], 
        passenger_info: Dict[str, Any]
    ) -> List[str]:
        """Determine which regulations apply to this flight/passenger"""
        
        from main import RegulationType
        
        regulations = []
        
        departure_airport = flight_info.get('departure_airport', '')
        arrival_airport = flight_info.get('arrival_airport', '')
        passenger_nationality = passenger_info.get('nationality', 'GB')
        
        # EU261 applies to:
        # - Flights departing from EU/EEA
        # - Flights arriving in EU/EEA operated by EU carrier
        eu_airports = self._get_eu_airports()
        if (departure_airport in eu_airports or 
            (arrival_airport in eu_airports and self._is_eu_carrier(flight_info))):
            regulations.append(RegulationType.EU261)
        
        # UK CAA applies to flights to/from UK
        uk_airports = {'LHR', 'LGW', 'STN', 'MAN', 'EDI', 'BHX', 'GLA', 'BRS', 'NCL'}
        if departure_airport in uk_airports or arrival_airport in uk_airports:
            regulations.append(RegulationType.UK_CAA)
        
        # US DOT applies to flights to/from US
        us_airports = {'JFK', 'LAX', 'ORD', 'MIA', 'DFW', 'ATL', 'BOS', 'IAD'}
        if departure_airport in us_airports or arrival_airport in us_airports:
            regulations.append(RegulationType.US_DOT)
        
        # IATA recommendations always apply
        regulations.append(RegulationType.IATA)
        
        # Montreal Convention for international flights
        if departure_airport != arrival_airport:  # Simple international check
            regulations.append(RegulationType.MONTREAL_CONVENTION)
        
        return regulations
    
    def _get_eu_airports(self) -> set:
        """Get set of EU/EEA airport codes"""
        return {
            # Major EU airports
            'CDG', 'AMS', 'FRA', 'MAD', 'FCO', 'BCN', 'MUC', 'VIE', 'BRU', 'ZUR',
            'CPH', 'ARN', 'OSL', 'HEL', 'WAW', 'PRG', 'BUD', 'OTP', 'SOF', 'ATH',
            'LIS', 'DUB', 'VNO', 'RIX', 'TLL', 'LUX', 'MLT', 'LCA', 'PDG'
        }
    
    def _is_eu_carrier(self, flight_info: Dict[str, Any]) -> bool:
        """Check if flight is operated by EU carrier"""
        
        flight_number = flight_info.get('flight_number', '')
        
        # Extract airline code from flight number
        airline_code = flight_number[:2] if len(flight_number) >= 2 else ''
        
        # EU airline codes (sample)
        eu_airlines = {
            'AF',  # Air France
            'BA',  # British Airways  
            'LH',  # Lufthansa
            'KL',  # KLM
            'IB',  # Iberia
            'AZ',  # ITA Airways
            'SK',  # SAS
            'AY',  # Finnair
            'LO',  # LOT Polish
            'OS',  # Austrian
            'SN'   # Brussels Airlines
        }
        
        return airline_code in eu_airlines
    
    async def calculate_care_obligations(
        self,
        delay_info: Dict[str, Any],
        passenger_info: Dict[str, Any],
        flight_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate passenger care obligations (meals, accommodation, etc.)"""
        
        care_obligations = {
            'meals': {'required': False, 'allowance': 0.0},
            'accommodation': {'required': False, 'allowance': 0.0},
            'transport': {'required': False, 'allowance': 0.0},
            'communication': {'required': False, 'allowance': 0.0}
        }
        
        delay_hours = delay_info['delay_hours']
        distance_km = flight_info.get('distance_km', 1500)
        
        # Meals
        if delay_hours >= 2:
            care_obligations['meals']['required'] = True
            if delay_hours >= 4:
                care_obligations['meals']['allowance'] = settings.meal_allowance_4h
            else:
                care_obligations['meals']['allowance'] = settings.meal_allowance_2h
        
        # Accommodation (if delay requires overnight stay)
        if delay_hours >= 8 or self._requires_overnight_stay(flight_info, delay_info):
            care_obligations['accommodation']['required'] = True
            care_obligations['accommodation']['allowance'] = settings.hotel_allowance_overnight
            
            # Transport to/from accommodation
            care_obligations['transport']['required'] = True
            care_obligations['transport']['allowance'] = settings.transport_allowance
        
        # Communication
        if delay_hours >= 2:
            care_obligations['communication']['required'] = True
            if delay_hours >= 4:
                care_obligations['communication']['allowance'] = settings.communication_allowance_4h
            else:
                care_obligations['communication']['allowance'] = settings.communication_allowance_2h
        
        return care_obligations
    
    def _requires_overnight_stay(
        self, 
        flight_info: Dict[str, Any], 
        delay_info: Dict[str, Any]
    ) -> bool:
        """Check if delay requires overnight accommodation"""
        
        scheduled_departure = delay_info.get('scheduled_departure')
        delay_minutes = delay_info.get('delay_minutes', 0)
        
        if not scheduled_departure:
            return delay_info.get('delay_hours', 0) >= 8
        
        # Calculate new departure time
        new_departure = scheduled_departure + timedelta(minutes=delay_minutes)
        
        # Check if new departure is in overnight hours (10 PM - 6 AM)
        hour = new_departure.hour
        return hour >= 22 or hour <= 6
    
    async def generate_compliance_report(
        self, 
        compliance_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed compliance report"""
        
        try:
            report = {
                'summary': {
                    'compliance_id': compliance_result['compliance_id'],
                    'passenger_id': compliance_result['passenger_id'],
                    'flight_id': compliance_result['flight_id'],
                    'total_compensation': compliance_result['total_compensation'],
                    'regulations_checked': len(compliance_result['regulations_checked']),
                    'eligible_regulations': len([r for r, c in compliance_result['eligible_compensation'].items() if c > 0])
                },
                'compensation_details': compliance_result['compensation_breakdown'],
                'care_obligations': compliance_result.get('care_obligations', {}),
                'compliance_reasons': compliance_result['compliance_reasons'],
                'required_actions': compliance_result['required_actions'],
                'deadlines': {
                    'claim_deadline': compliance_result.get('claim_deadline'),
                    'days_remaining': (compliance_result.get('claim_deadline') - datetime.utcnow()).days
                    if compliance_result.get('claim_deadline') else None
                },
                'next_steps': self._generate_next_steps(compliance_result),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error("Failed to generate compliance report", error=str(e))
            raise
    
    def _generate_next_steps(self, compliance_result: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps"""
        
        next_steps = []
        total_compensation = compliance_result.get('total_compensation', 0)
        
        if total_compensation > 0:
            next_steps.append("Submit compensation claim through airline customer service")
            next_steps.append("Retain all travel receipts and documentation")
            next_steps.append("Document all additional expenses incurred due to delay")
        
        care_obligations = compliance_result.get('care_obligations', {})
        if care_obligations.get('meals', {}).get('required'):
            next_steps.append("Request meal vouchers from airline staff")
        
        if care_obligations.get('accommodation', {}).get('required'):
            next_steps.append("Request accommodation from airline (if not already provided)")
        
        if total_compensation == 0:
            next_steps.append("No compensation available under applicable regulations")
            next_steps.append("Consider alternative resolution options")
        
        return next_steps