import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from kafka import KafkaProducer
from kafka.errors import KafkaError
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from .real_time_monitor import DisruptionAlert, AlertSeverity, FlightEvent
from .pattern_detector import DisruptionPattern, EarlyWarning, PatternType


class AlertChannel(Enum):
    EMAIL = "email"
    SMS = "sms" 
    WEBHOOK = "webhook"
    KAFKA = "kafka"
    SLACK = "slack"
    TEAMS = "teams"


class AlertPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class AlertRule:
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, any]
    severity_threshold: float
    confidence_threshold: float
    pattern_types: List[PatternType]
    affected_flights_threshold: int
    financial_impact_threshold: float
    passenger_impact_threshold: int
    channels: List[AlertChannel]
    priority: AlertPriority
    cooldown_minutes: int
    enabled: bool


@dataclass
class AlertTemplate:
    template_id: str
    name: str
    subject_template: str
    body_template: str
    channels: List[AlertChannel]
    severity_levels: List[AlertSeverity]
    variables: List[str]


@dataclass
class AlertRecipient:
    recipient_id: str
    name: str
    role: str
    email: str
    phone: str
    slack_user_id: Optional[str]
    teams_user_id: Optional[str]
    alert_types: List[PatternType]
    severity_levels: List[AlertSeverity]
    active_hours: Dict[str, Tuple[int, int]]  # day -> (start_hour, end_hour)
    timezone: str


@dataclass
class GeneratedAlert:
    alert_id: str
    rule_id: str
    template_id: str
    priority: AlertPriority
    severity: AlertSeverity
    title: str
    message: str
    recipients: List[str]
    channels: List[AlertChannel]
    metadata: Dict[str, any]
    created_at: datetime
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    status: str  # pending, sent, acknowledged, resolved, failed


class SeverityScorer:
    def __init__(self):
        self.severity_weights = {
            'delay_minutes': 0.25,
            'affected_passengers': 0.20,
            'financial_impact': 0.20,
            'cancellation_probability': 0.15,
            'cascade_risk': 0.10,
            'weather_severity': 0.05,
            'maintenance_severity': 0.05
        }
        
    def calculate_severity_score(self, 
                                disruption_alert: DisruptionAlert = None,
                                pattern: DisruptionPattern = None,
                                early_warning: EarlyWarning = None) -> float:
        """Calculate normalized severity score (0-1)."""
        score = 0.0
        
        if disruption_alert:
            score += self._score_disruption_alert(disruption_alert)
        
        if pattern:
            score += self._score_pattern(pattern)
            
        if early_warning:
            score += self._score_early_warning(early_warning)
            
        return min(score, 1.0)
        
    def _score_disruption_alert(self, alert: DisruptionAlert) -> float:
        """Score individual disruption alert."""
        factors = {
            'delay_minutes': min(alert.predicted_delay / 180, 1.0),
            'affected_passengers': min(alert.affected_passengers / 500, 1.0),
            'financial_impact': min(alert.financial_impact / 100000, 1.0),
            'confidence_score': alert.confidence_score,
            'impact_score': alert.impact_score
        }
        
        weighted_score = sum(
            factors.get(factor, 0) * weight 
            for factor, weight in self.severity_weights.items()
            if factor in factors
        )
        
        return weighted_score
        
    def _score_pattern(self, pattern: DisruptionPattern) -> float:
        """Score disruption pattern."""
        factors = {
            'affected_passengers': min(pattern.passenger_impact / 1000, 1.0),
            'financial_impact': min(pattern.financial_impact / 500000, 1.0),
            'propagation_risk': pattern.propagation_risk,
            'severity_score': pattern.severity_score,
            'confidence_score': pattern.confidence_score
        }
        
        base_score = sum(factors.values()) / len(factors)
        
        multipliers = {
            PatternType.CASCADE_EFFECT: 1.3,
            PatternType.WEATHER_PATTERN: 1.1,
            PatternType.MAINTENANCE_PATTERN: 1.2,
            PatternType.ANOMALY_CLUSTER: 1.4
        }
        
        multiplier = multipliers.get(pattern.pattern_type, 1.0)
        return min(base_score * multiplier, 1.0)
        
    def _score_early_warning(self, warning: EarlyWarning) -> float:
        """Score early warning."""
        severity_scores = {
            AlertSeverity.LOW: 0.2,
            AlertSeverity.MEDIUM: 0.4,
            AlertSeverity.HIGH: 0.7,
            AlertSeverity.CRITICAL: 1.0
        }
        
        base_score = severity_scores.get(warning.severity, 0.2)
        confidence_factor = warning.confidence
        
        return base_score * confidence_factor
        
    def determine_alert_severity(self, score: float) -> AlertSeverity:
        """Map severity score to AlertSeverity enum."""
        if score >= 0.8:
            return AlertSeverity.CRITICAL
        elif score >= 0.6:
            return AlertSeverity.HIGH
        elif score >= 0.4:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW


class AlertGenerator:
    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 2)
        )
        
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=config.get('kafka_servers', ['localhost:9092']),
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        self.severity_scorer = SeverityScorer()
        self.alert_rules = self._load_alert_rules()
        self.alert_templates = self._load_alert_templates()
        self.recipients = self._load_recipients()
        
        self.alert_history = {}
        self.cooldown_tracker = {}
        
    def _load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from configuration."""
        return [
            AlertRule(
                rule_id="critical_delay",
                name="Critical Flight Delays",
                description="Alerts for flights with severe delays",
                conditions={
                    "min_delay_minutes": 120,
                    "min_confidence": 0.8
                },
                severity_threshold=0.7,
                confidence_threshold=0.8,
                pattern_types=[PatternType.WEATHER_PATTERN, PatternType.MAINTENANCE_PATTERN],
                affected_flights_threshold=5,
                financial_impact_threshold=50000,
                passenger_impact_threshold=200,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.KAFKA],
                priority=AlertPriority.HIGH,
                cooldown_minutes=30,
                enabled=True
            ),
            AlertRule(
                rule_id="cascade_effect",
                name="Cascade Effect Detection",
                description="Alerts for cascade disruption effects",
                conditions={
                    "min_cascade_depth": 3,
                    "min_connected_flights": 10
                },
                severity_threshold=0.6,
                confidence_threshold=0.7,
                pattern_types=[PatternType.CASCADE_EFFECT],
                affected_flights_threshold=10,
                financial_impact_threshold=100000,
                passenger_impact_threshold=500,
                channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK, AlertChannel.KAFKA],
                priority=AlertPriority.CRITICAL,
                cooldown_minutes=45,
                enabled=True
            ),
            AlertRule(
                rule_id="weather_disruption",
                name="Severe Weather Disruptions", 
                description="Alerts for weather-related disruptions",
                conditions={
                    "min_weather_severity": 0.6,
                    "min_affected_airports": 2
                },
                severity_threshold=0.5,
                confidence_threshold=0.75,
                pattern_types=[PatternType.WEATHER_PATTERN],
                affected_flights_threshold=8,
                financial_impact_threshold=75000,
                passenger_impact_threshold=300,
                channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.KAFKA],
                priority=AlertPriority.HIGH,
                cooldown_minutes=20,
                enabled=True
            ),
            AlertRule(
                rule_id="anomaly_cluster",
                name="Operational Anomalies",
                description="Alerts for clusters of anomalous events",
                conditions={
                    "min_anomaly_score": 0.8,
                    "min_cluster_size": 5
                },
                severity_threshold=0.75,
                confidence_threshold=0.8,
                pattern_types=[PatternType.ANOMALY_CLUSTER],
                affected_flights_threshold=5,
                financial_impact_threshold=25000,
                passenger_impact_threshold=150,
                channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK, AlertChannel.KAFKA],
                priority=AlertPriority.CRITICAL,
                cooldown_minutes=60,
                enabled=True
            )
        ]
        
    def _load_alert_templates(self) -> List[AlertTemplate]:
        """Load alert message templates."""
        return [
            AlertTemplate(
                template_id="critical_delay_template",
                name="Critical Delay Alert",
                subject_template="CRITICAL: Flight Delays Detected - {affected_flights} flights affected",
                body_template="""
CRITICAL FLIGHT DISRUPTION ALERT

Alert Details:
- Severity: {severity}
- Affected Flights: {affected_flights}
- Predicted Delay: {predicted_delay} minutes
- Affected Passengers: {affected_passengers}
- Financial Impact: ${financial_impact:,.2f}
- Confidence: {confidence:.1%}

Root Cause: {root_cause}

Recommended Actions:
{recommended_actions}

Alert Generated: {timestamp}
Alert ID: {alert_id}
                """,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                severity_levels=[AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                variables=['severity', 'affected_flights', 'predicted_delay', 'affected_passengers', 
                          'financial_impact', 'confidence', 'root_cause', 'recommended_actions', 
                          'timestamp', 'alert_id']
            ),
            AlertTemplate(
                template_id="cascade_effect_template", 
                name="Cascade Effect Alert",
                subject_template="CASCADE EFFECT: Disruption propagation detected across {affected_airports} airports",
                body_template="""
CASCADE EFFECT DISRUPTION ALERT

Pattern Details:
- Pattern Type: {pattern_type}
- Affected Airports: {affected_airports}
- Duration: {duration_hours} hours
- Propagation Risk: {propagation_risk:.1%}
- Passenger Impact: {passenger_impact}
- Financial Impact: ${financial_impact:,.2f}

Similar Historical Patterns: {similar_patterns}

Immediate Actions Required:
{recommended_actions}

Pattern ID: {pattern_id}
Generated: {timestamp}
                """,
                channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK],
                severity_levels=[AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                variables=['pattern_type', 'affected_airports', 'duration_hours', 'propagation_risk',
                          'passenger_impact', 'financial_impact', 'similar_patterns', 
                          'recommended_actions', 'pattern_id', 'timestamp']
            ),
            AlertTemplate(
                template_id="early_warning_template",
                name="Early Warning Alert", 
                subject_template="EARLY WARNING: Potential disruption predicted - {pattern_type}",
                body_template="""
EARLY WARNING SYSTEM ALERT

Warning Details:
- Pattern Type: {pattern_type}  
- Predicted Start: {predicted_start}
- Predicted Duration: {predicted_duration} hours
- Confidence: {confidence:.1%}
- Affected Airports: {affected_airports}
- Estimated Flight Impact: {affected_flights_estimate}

Proactive Measures:
{recommended_actions}

Warning ID: {warning_id}
Generated: {timestamp}
                """,
                channels=[AlertChannel.EMAIL, AlertChannel.SMS],
                severity_levels=[AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                variables=['pattern_type', 'predicted_start', 'predicted_duration', 'confidence',
                          'affected_airports', 'affected_flights_estimate', 'recommended_actions',
                          'warning_id', 'timestamp']
            )
        ]
        
    def _load_recipients(self) -> List[AlertRecipient]:
        """Load alert recipients configuration."""
        return [
            AlertRecipient(
                recipient_id="ops_manager",
                name="Operations Manager",
                role="operations",
                email="ops.manager@airline.com",
                phone="+44123456789",
                slack_user_id="U1234567890",
                teams_user_id="teams_user_123",
                alert_types=[PatternType.WEATHER_PATTERN, PatternType.MAINTENANCE_PATTERN, 
                           PatternType.AIRPORT_CONGESTION],
                severity_levels=[AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                active_hours={"mon-fri": (6, 22), "sat-sun": (8, 20)},
                timezone="Europe/London"
            ),
            AlertRecipient(
                recipient_id="duty_manager",
                name="Duty Manager", 
                role="duty_management",
                email="duty.manager@airline.com",
                phone="+44987654321",
                slack_user_id="U0987654321",
                teams_user_id=None,
                alert_types=[PatternType.CREW_PATTERN, PatternType.CASCADE_EFFECT, 
                           PatternType.ANOMALY_CLUSTER],
                severity_levels=[AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                active_hours={"all_days": (0, 23)},
                timezone="Europe/London"
            ),
            AlertRecipient(
                recipient_id="maintenance_chief",
                name="Maintenance Chief",
                role="maintenance",
                email="maintenance.chief@airline.com", 
                phone="+44555123456",
                slack_user_id="U5551234567",
                teams_user_id="teams_maint_123",
                alert_types=[PatternType.MAINTENANCE_PATTERN, PatternType.ANOMALY_CLUSTER],
                severity_levels=[AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                active_hours={"all_days": (5, 23)},
                timezone="Europe/London"
            )
        ]
        
    async def process_disruption_alert(self, alert: DisruptionAlert) -> List[GeneratedAlert]:
        """Process disruption alert and generate notifications."""
        severity_score = self.severity_scorer.calculate_severity_score(disruption_alert=alert)
        
        applicable_rules = self._find_applicable_rules(
            alert_type="disruption",
            severity_score=severity_score,
            confidence=alert.confidence_score,
            affected_flights=1,
            financial_impact=alert.financial_impact,
            passenger_impact=alert.affected_passengers
        )
        
        generated_alerts = []
        for rule in applicable_rules:
            if self._check_cooldown(rule.rule_id, alert.flight_id):
                continue
                
            template = self._find_template_for_rule(rule, alert)
            if template:
                generated_alert = await self._create_alert_from_disruption(
                    alert, rule, template, severity_score
                )
                generated_alerts.append(generated_alert)
                self._update_cooldown(rule.rule_id, alert.flight_id)
                
        return generated_alerts
        
    async def process_pattern_alert(self, pattern: DisruptionPattern) -> List[GeneratedAlert]:
        """Process pattern alert and generate notifications.""" 
        severity_score = self.severity_scorer.calculate_severity_score(pattern=pattern)
        
        applicable_rules = self._find_applicable_rules(
            alert_type="pattern",
            severity_score=severity_score,
            confidence=pattern.confidence_score,
            affected_flights=len(pattern.affected_flights),
            financial_impact=pattern.financial_impact,
            passenger_impact=pattern.passenger_impact,
            pattern_types=[pattern.pattern_type]
        )
        
        generated_alerts = []
        for rule in applicable_rules:
            if self._check_cooldown(rule.rule_id, pattern.pattern_id):
                continue
                
            template = self._find_template_for_pattern(rule, pattern)
            if template:
                generated_alert = await self._create_alert_from_pattern(
                    pattern, rule, template, severity_score
                )
                generated_alerts.append(generated_alert)
                self._update_cooldown(rule.rule_id, pattern.pattern_id)
                
        return generated_alerts
        
    async def process_early_warning(self, warning: EarlyWarning) -> List[GeneratedAlert]:
        """Process early warning and generate notifications."""
        severity_score = self.severity_scorer.calculate_severity_score(early_warning=warning)
        
        applicable_rules = self._find_applicable_rules(
            alert_type="early_warning",
            severity_score=severity_score,
            confidence=warning.confidence,
            affected_flights=warning.affected_flights_estimate,
            pattern_types=[warning.pattern_type]
        )
        
        generated_alerts = []
        for rule in applicable_rules:
            if self._check_cooldown(rule.rule_id, warning.warning_id):
                continue
                
            template = self._find_template_for_warning(rule, warning)
            if template:
                generated_alert = await self._create_alert_from_warning(
                    warning, rule, template, severity_score
                )
                generated_alerts.append(generated_alert)
                self._update_cooldown(rule.rule_id, warning.warning_id)
                
        return generated_alerts
        
    def _find_applicable_rules(self, 
                             alert_type: str,
                             severity_score: float,
                             confidence: float,
                             affected_flights: int,
                             financial_impact: float = 0,
                             passenger_impact: int = 0,
                             pattern_types: List[PatternType] = None) -> List[AlertRule]:
        """Find applicable alert rules based on conditions."""
        applicable_rules = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
                
            if severity_score < rule.severity_threshold:
                continue
                
            if confidence < rule.confidence_threshold:
                continue
                
            if affected_flights < rule.affected_flights_threshold:
                continue
                
            if financial_impact < rule.financial_impact_threshold:
                continue
                
            if passenger_impact < rule.passenger_impact_threshold:
                continue
                
            if pattern_types and not any(pt in rule.pattern_types for pt in pattern_types):
                continue
                
            applicable_rules.append(rule)
            
        return applicable_rules
        
    def _find_template_for_rule(self, rule: AlertRule, alert: DisruptionAlert) -> Optional[AlertTemplate]:
        """Find appropriate template for rule and alert."""
        severity = self.severity_scorer.determine_alert_severity(
            self.severity_scorer.calculate_severity_score(disruption_alert=alert)
        )
        
        for template in self.alert_templates:
            if severity in template.severity_levels:
                if any(channel in rule.channels for channel in template.channels):
                    return template
                    
        return self.alert_templates[0] if self.alert_templates else None
        
    def _find_template_for_pattern(self, rule: AlertRule, pattern: DisruptionPattern) -> Optional[AlertTemplate]:
        """Find appropriate template for rule and pattern."""
        for template in self.alert_templates:
            if template.template_id == "cascade_effect_template":
                return template
                
        return self.alert_templates[0] if self.alert_templates else None
        
    def _find_template_for_warning(self, rule: AlertRule, warning: EarlyWarning) -> Optional[AlertTemplate]:
        """Find appropriate template for rule and warning."""
        for template in self.alert_templates:
            if template.template_id == "early_warning_template":
                return template
                
        return self.alert_templates[0] if self.alert_templates else None
        
    async def _create_alert_from_disruption(self, 
                                          alert: DisruptionAlert,
                                          rule: AlertRule,
                                          template: AlertTemplate,
                                          severity_score: float) -> GeneratedAlert:
        """Create generated alert from disruption alert."""
        alert_id = f"gen_{alert.alert_id}_{int(datetime.now().timestamp())}"
        
        severity = self.severity_scorer.determine_alert_severity(severity_score)
        recipients = self._find_recipients_for_alert(rule, severity, alert.alert_type)
        
        variables = {
            'severity': severity.value,
            'affected_flights': 1,
            'predicted_delay': alert.predicted_delay,
            'affected_passengers': alert.affected_passengers,
            'financial_impact': alert.financial_impact,
            'confidence': alert.confidence_score,
            'root_cause': f"{alert.alert_type.value} disruption",
            'recommended_actions': "\n".join(f"• {action}" for action in alert.recommended_actions),
            'timestamp': alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'alert_id': alert.alert_id
        }
        
        title = template.subject_template.format(**variables)
        message = template.body_template.format(**variables)
        
        return GeneratedAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            template_id=template.template_id,
            priority=rule.priority,
            severity=severity,
            title=title,
            message=message,
            recipients=recipients,
            channels=rule.channels,
            metadata={
                'original_alert_id': alert.alert_id,
                'flight_id': alert.flight_id,
                'severity_score': severity_score,
                'alert_type': 'disruption'
            },
            created_at=datetime.now(),
            scheduled_at=None,
            sent_at=None,
            acknowledged_at=None,
            resolved_at=None,
            status='pending'
        )
        
    async def _create_alert_from_pattern(self,
                                       pattern: DisruptionPattern,
                                       rule: AlertRule,
                                       template: AlertTemplate,
                                       severity_score: float) -> GeneratedAlert:
        """Create generated alert from disruption pattern."""
        alert_id = f"gen_pattern_{pattern.pattern_id}_{int(datetime.now().timestamp())}"
        
        severity = self.severity_scorer.determine_alert_severity(severity_score)
        recipients = self._find_recipients_for_pattern(rule, severity, pattern.pattern_type)
        
        variables = {
            'pattern_type': pattern.pattern_type.value.replace('_', ' ').title(),
            'affected_airports': ", ".join(pattern.airports_affected),
            'duration_hours': f"{pattern.duration_hours:.1f}",
            'propagation_risk': pattern.propagation_risk,
            'passenger_impact': pattern.passenger_impact,
            'financial_impact': pattern.financial_impact,
            'similar_patterns': ", ".join(pattern.similar_historical_patterns) or "None found",
            'recommended_actions': "\n".join(f"• Action for {pattern.pattern_type.value}"),
            'pattern_id': pattern.pattern_id,
            'timestamp': pattern.start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        title = template.subject_template.format(**variables)
        message = template.body_template.format(**variables)
        
        return GeneratedAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            template_id=template.template_id,
            priority=rule.priority,
            severity=severity,
            title=title,
            message=message,
            recipients=recipients,
            channels=rule.channels,
            metadata={
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type.value,
                'severity_score': severity_score,
                'alert_type': 'pattern'
            },
            created_at=datetime.now(),
            scheduled_at=None,
            sent_at=None,
            acknowledged_at=None,
            resolved_at=None,
            status='pending'
        )
        
    async def _create_alert_from_warning(self,
                                       warning: EarlyWarning,
                                       rule: AlertRule,
                                       template: AlertTemplate,
                                       severity_score: float) -> GeneratedAlert:
        """Create generated alert from early warning."""
        alert_id = f"gen_warning_{warning.warning_id}_{int(datetime.now().timestamp())}"
        
        severity = self.severity_scorer.determine_alert_severity(severity_score)
        recipients = self._find_recipients_for_warning(rule, severity, warning.pattern_type)
        
        variables = {
            'pattern_type': warning.pattern_type.value.replace('_', ' ').title(),
            'predicted_start': warning.predicted_start.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'predicted_duration': f"{warning.predicted_duration:.1f}",
            'confidence': warning.confidence,
            'affected_airports': ", ".join(warning.affected_airports),
            'affected_flights_estimate': warning.affected_flights_estimate,
            'recommended_actions': "\n".join(f"• {action}" for action in warning.recommended_actions),
            'warning_id': warning.warning_id,
            'timestamp': warning.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        title = template.subject_template.format(**variables)
        message = template.body_template.format(**variables)
        
        return GeneratedAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            template_id=template.template_id,
            priority=rule.priority,
            severity=severity,
            title=title,
            message=message,
            recipients=recipients,
            channels=rule.channels,
            metadata={
                'warning_id': warning.warning_id,
                'pattern_type': warning.pattern_type.value,
                'severity_score': severity_score,
                'alert_type': 'early_warning'
            },
            created_at=datetime.now(),
            scheduled_at=None,
            sent_at=None,
            acknowledged_at=None,
            resolved_at=None,
            status='pending'
        )
        
    def _find_recipients_for_alert(self, rule: AlertRule, severity: AlertSeverity, alert_type) -> List[str]:
        """Find recipients for disruption alert."""
        recipients = []
        
        for recipient in self.recipients:
            if severity in recipient.severity_levels:
                if self._is_recipient_active(recipient):
                    recipients.append(recipient.recipient_id)
                    
        return recipients
        
    def _find_recipients_for_pattern(self, rule: AlertRule, severity: AlertSeverity, pattern_type: PatternType) -> List[str]:
        """Find recipients for pattern alert."""
        recipients = []
        
        for recipient in self.recipients:
            if pattern_type in recipient.alert_types and severity in recipient.severity_levels:
                if self._is_recipient_active(recipient):
                    recipients.append(recipient.recipient_id)
                    
        return recipients
        
    def _find_recipients_for_warning(self, rule: AlertRule, severity: AlertSeverity, pattern_type: PatternType) -> List[str]:
        """Find recipients for early warning."""
        return self._find_recipients_for_pattern(rule, severity, pattern_type)
        
    def _is_recipient_active(self, recipient: AlertRecipient) -> bool:
        """Check if recipient is currently active."""
        now = datetime.now()
        current_day = now.strftime("%a").lower()
        current_hour = now.hour
        
        for day_range, (start_hour, end_hour) in recipient.active_hours.items():
            if day_range == "all_days" or current_day in day_range:
                if start_hour <= current_hour <= end_hour:
                    return True
                    
        return False
        
    def _check_cooldown(self, rule_id: str, entity_id: str) -> bool:
        """Check if rule is in cooldown period for entity."""
        key = f"{rule_id}:{entity_id}"
        
        if key in self.cooldown_tracker:
            last_sent = self.cooldown_tracker[key]
            rule = next(r for r in self.alert_rules if r.rule_id == rule_id)
            
            if datetime.now() - last_sent < timedelta(minutes=rule.cooldown_minutes):
                return True
                
        return False
        
    def _update_cooldown(self, rule_id: str, entity_id: str):
        """Update cooldown tracker."""
        key = f"{rule_id}:{entity_id}"
        self.cooldown_tracker[key] = datetime.now()
        
    async def send_alerts(self, alerts: List[GeneratedAlert]) -> List[GeneratedAlert]:
        """Send generated alerts through configured channels."""
        sent_alerts = []
        
        for alert in alerts:
            try:
                success = await self._send_alert(alert)
                if success:
                    alert.sent_at = datetime.now()
                    alert.status = 'sent'
                else:
                    alert.status = 'failed'
                    
                sent_alerts.append(alert)
                self.alert_history[alert.alert_id] = alert
                
            except Exception as e:
                self.logger.error(f"Failed to send alert {alert.alert_id}: {e}")
                alert.status = 'failed'
                sent_alerts.append(alert)
                
        return sent_alerts
        
    async def _send_alert(self, alert: GeneratedAlert) -> bool:
        """Send individual alert through specified channels."""
        success = True
        
        for channel in alert.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_alert(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert)
                elif channel == AlertChannel.KAFKA:
                    await self._send_kafka_alert(alert)
                    
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel.value}: {e}")
                success = False
                
        return success
        
    async def _send_email_alert(self, alert: GeneratedAlert):
        """Send alert via email."""
        recipients = [
            recipient for recipient in self.recipients 
            if recipient.recipient_id in alert.recipients
        ]
        
        for recipient in recipients:
            msg = MIMEMultipart()
            msg['From'] = self.config.get('email_from', 'alerts@airline.com')
            msg['To'] = recipient.email
            msg['Subject'] = alert.title
            
            msg.attach(MIMEText(alert.message, 'plain'))
            
            # Would implement actual email sending here
            self.logger.info(f"Email alert sent to {recipient.email}")
            
    async def _send_sms_alert(self, alert: GeneratedAlert):
        """Send alert via SMS."""
        # Would implement SMS sending here
        self.logger.info(f"SMS alert sent for {alert.alert_id}")
        
    async def _send_slack_alert(self, alert: GeneratedAlert):
        """Send alert via Slack."""
        # Would implement Slack API integration here
        self.logger.info(f"Slack alert sent for {alert.alert_id}")
        
    async def _send_webhook_alert(self, alert: GeneratedAlert):
        """Send alert via webhook."""
        webhook_url = self.config.get('webhook_url')
        if webhook_url:
            payload = {
                'alert_id': alert.alert_id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'priority': alert.priority.value,
                'created_at': alert.created_at.isoformat(),
                'metadata': alert.metadata
            }
            
            # Would implement webhook POST here
            self.logger.info(f"Webhook alert sent for {alert.alert_id}")
            
    async def _send_kafka_alert(self, alert: GeneratedAlert):
        """Send alert via Kafka."""
        alert_data = asdict(alert)
        alert_data['created_at'] = alert.created_at.isoformat()
        alert_data['severity'] = alert.severity.value
        alert_data['priority'] = alert.priority.value
        alert_data['channels'] = [c.value for c in alert.channels]
        
        self.kafka_producer.send('generated-alerts', alert_data)
        self.kafka_producer.flush()
        
        self.logger.info(f"Kafka alert sent for {alert.alert_id}")
        
    def get_alert_history(self) -> List[GeneratedAlert]:
        """Get alert history."""
        return list(self.alert_history.values())
        
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.alert_history:
            alert = self.alert_history[alert_id]
            alert.acknowledged_at = datetime.now()
            alert.status = 'acknowledged'
            
            self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        return False
        
    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.alert_history:
            alert = self.alert_history[alert_id]
            alert.resolved_at = datetime.now()
            alert.status = 'resolved'
            
            self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True
            
        return False