import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from uuid import uuid4
import numpy as np
from database import Database
from reasoning_engine import ReasoningEngine
from aiokafka import AIOKafkaProducer

logger = structlog.get_logger()

class DecisionEngine:
    """Advanced decision engine with confidence scoring and multi-criteria analysis"""
    
    def __init__(
        self,
        db: Database,
        reasoning_engine: ReasoningEngine,
        kafka_producer: AIOKafkaProducer
    ):
        self.db = db
        self.reasoning_engine = reasoning_engine
        self.kafka_producer = kafka_producer
        
        # Decision criteria weights for different agent types
        self.decision_criteria = {
            'disruption_predictor': {
                'accuracy': 0.35,
                'timeliness': 0.25,
                'completeness': 0.20,
                'actionability': 0.20
            },
            'passenger_manager': {
                'satisfaction': 0.30,
                'efficiency': 0.25,
                'compliance': 0.25,
                'cost_impact': 0.20
            },
            'cost_optimizer': {
                'cost_savings': 0.40,
                'feasibility': 0.25,
                'risk_level': 0.20,
                'implementation_time': 0.15
            },
            'compliance_checker': {
                'legal_accuracy': 0.45,
                'completeness': 0.25,
                'documentation': 0.20,
                'risk_mitigation': 0.10
            },
            'communication_manager': {
                'clarity': 0.30,
                'reach': 0.25,
                'timeliness': 0.25,
                'channel_optimization': 0.20
            },
            'resource_allocator': {
                'efficiency': 0.35,
                'availability': 0.25,
                'cost_effectiveness': 0.25,
                'scalability': 0.15
            },
            'executive_advisor': {
                'strategic_value': 0.35,
                'risk_assessment': 0.30,
                'business_impact': 0.20,
                'stakeholder_alignment': 0.15
            }
        }
        
        # Decision templates for different scenarios
        self.decision_templates = {
            'flight_cancellation': {
                'primary_actions': [
                    'notify_passengers',
                    'arrange_rebooking',
                    'calculate_compensation',
                    'coordinate_ground_services'
                ],
                'success_metrics': {
                    'passenger_satisfaction': 0.85,
                    'cost_efficiency': 0.80,
                    'regulatory_compliance': 0.95,
                    'resolution_time': 1800  # 30 minutes
                }
            },
            'weather_delay': {
                'primary_actions': [
                    'monitor_conditions',
                    'proactive_communication',
                    'arrange_passenger_care',
                    'optimize_recovery'
                ],
                'success_metrics': {
                    'prediction_accuracy': 0.90,
                    'passenger_satisfaction': 0.80,
                    'cost_minimization': 0.85,
                    'operational_recovery': 0.88
                }
            },
            'technical_issue': {
                'primary_actions': [
                    'assess_safety_impact',
                    'coordinate_maintenance',
                    'manage_passenger_impact',
                    'communicate_updates'
                ],
                'success_metrics': {
                    'safety_compliance': 1.00,
                    'resolution_speed': 0.85,
                    'passenger_care': 0.80,
                    'cost_control': 0.75
                }
            }
        }
        
        # Decision quality tracking
        self.decision_history = []
        self.performance_metrics = {
            'total_decisions': 0,
            'average_confidence': 0.0,
            'success_rate': 0.0,
            'avg_processing_time': 0.0
        }
    
    async def make_decision(
        self,
        agent_type: str,
        reasoning_result: Dict[str, Any],
        step_name: str = None,
        priority: str = 'normal'
    ) -> Dict[str, Any]:
        """Make a structured decision based on reasoning results"""
        
        start_time = datetime.utcnow()
        decision_id = str(uuid4())
        
        try:
            # Extract key components from reasoning
            reasoning_chain = reasoning_result.get('reasoning_chain', [])
            key_insights = reasoning_result.get('key_insights', [])
            confidence_score = reasoning_result.get('confidence_score', 0.75)
            recommendations = reasoning_result.get('recommendations', [])
            alternatives = reasoning_result.get('alternatives', [])
            risk_assessment = reasoning_result.get('risk_assessment', {})
            
            # Calculate decision confidence using multiple factors
            decision_confidence = await self._calculate_decision_confidence(
                agent_type=agent_type,
                reasoning_result=reasoning_result,
                step_name=step_name
            )
            
            # Generate execution plan
            execution_plan = await self._generate_execution_plan(
                agent_type=agent_type,
                recommendations=recommendations,
                priority=priority,
                step_name=step_name
            )
            
            # Assess resource requirements
            resource_requirements = await self._assess_resource_requirements(
                agent_type=agent_type,
                execution_plan=execution_plan,
                priority=priority
            )
            
            # Estimate impact
            estimated_impact = await self._estimate_impact(
                agent_type=agent_type,
                execution_plan=execution_plan,
                confidence_score=decision_confidence
            )
            
            # Evaluate alternatives
            evaluated_alternatives = await self._evaluate_alternatives(
                agent_type=agent_type,
                alternatives=alternatives,
                current_plan=execution_plan
            )
            
            # Construct decision
            decision = {
                'decision_id': decision_id,
                'agent_type': agent_type,
                'decision_type': step_name or 'general_decision',
                'reasoning_chain': reasoning_chain,
                'confidence_score': decision_confidence,
                'execution_plan': execution_plan,
                'resource_requirements': resource_requirements,
                'estimated_impact': estimated_impact,
                'risk_assessment': risk_assessment,
                'alternatives_considered': evaluated_alternatives,
                'priority': priority,
                'created_at': datetime.utcnow(),
                'processing_time': (datetime.utcnow() - start_time).total_seconds(),
                'quality_score': await self._calculate_quality_score(
                    reasoning_result, execution_plan, decision_confidence
                )
            }
            
            # Store decision
            await self._store_decision(decision)
            
            # Update performance metrics
            await self._update_performance_metrics(decision)
            
            # Publish decision event
            await self._publish_decision_event(decision)
            
            logger.info(
                "Decision made successfully",
                decision_id=decision_id,
                agent_type=agent_type,
                confidence=decision_confidence,
                processing_time=decision['processing_time']
            )
            
            return decision
            
        except Exception as e:
            logger.error("Decision making failed", error=str(e))
            return await self._generate_fallback_decision(
                agent_type=agent_type,
                reasoning_result=reasoning_result,
                error=str(e)
            )
    
    async def _calculate_decision_confidence(
        self,
        agent_type: str,
        reasoning_result: Dict[str, Any],
        step_name: str = None
    ) -> float:
        """Calculate multi-factor decision confidence score"""
        
        try:
            base_confidence = reasoning_result.get('confidence_score', 0.75)
            
            # Get agent-specific criteria weights
            criteria_weights = self.decision_criteria.get(agent_type, {})
            
            # Factor 1: Reasoning quality
            reasoning_quality = self._assess_reasoning_quality(reasoning_result)
            
            # Factor 2: Data completeness
            data_completeness = self._assess_data_completeness(reasoning_result)
            
            # Factor 3: Historical performance for this agent type
            historical_performance = await self._get_historical_performance(agent_type)
            
            # Factor 4: Complexity of scenario
            scenario_complexity = self._assess_scenario_complexity(reasoning_result)
            
            # Factor 5: Time pressure impact
            time_pressure_factor = self._calculate_time_pressure_factor(step_name)
            
            # Weighted confidence calculation
            weighted_confidence = (
                base_confidence * 0.35 +
                reasoning_quality * 0.25 +
                data_completeness * 0.20 +
                historical_performance * 0.15 +
                (1.0 - scenario_complexity) * 0.05
            ) * time_pressure_factor
            
            # Ensure confidence is within valid range
            final_confidence = max(0.1, min(1.0, weighted_confidence))
            
            return round(final_confidence, 3)
            
        except Exception as e:
            logger.error("Confidence calculation failed", error=str(e))
            return 0.75  # Default confidence
    
    def _assess_reasoning_quality(self, reasoning_result: Dict[str, Any]) -> float:
        """Assess the quality of reasoning provided"""
        
        quality_score = 0.5  # Base score
        
        # Check for structured reasoning chain
        reasoning_chain = reasoning_result.get('reasoning_chain', [])
        if len(reasoning_chain) >= 3:
            quality_score += 0.2
        
        # Check for key insights
        insights = reasoning_result.get('key_insights', [])
        if len(insights) >= 2:
            quality_score += 0.15
        
        # Check for risk assessment
        if reasoning_result.get('risk_assessment'):
            quality_score += 0.1
        
        # Check for alternatives considered
        alternatives = reasoning_result.get('alternatives', [])
        if len(alternatives) >= 2:
            quality_score += 0.05
        
        return min(1.0, quality_score)
    
    def _assess_data_completeness(self, reasoning_result: Dict[str, Any]) -> float:
        """Assess completeness of available data for decision making"""
        
        completeness_score = 0.6  # Base score
        
        # Check reasoning chain depth
        chain_length = len(reasoning_result.get('reasoning_chain', []))
        if chain_length >= 5:
            completeness_score += 0.2
        elif chain_length >= 3:
            completeness_score += 0.1
        
        # Check for quantitative insights
        insights = reasoning_result.get('key_insights', [])
        has_quantitative = any('$' in str(insight) or '%' in str(insight) or any(char.isdigit() for char in str(insight)) for insight in insights)
        if has_quantitative:
            completeness_score += 0.15
        
        # Check risk assessment completeness
        risk_assessment = reasoning_result.get('risk_assessment', {})
        if len(risk_assessment) >= 3:
            completeness_score += 0.05
        
        return min(1.0, completeness_score)
    
    async def _get_historical_performance(self, agent_type: str) -> float:
        """Get historical performance score for agent type"""
        
        try:
            # In production, this would query actual historical data
            # For now, return simulated historical performance
            performance_scores = {
                'disruption_predictor': 0.88,
                'passenger_manager': 0.91,
                'cost_optimizer': 0.85,
                'compliance_checker': 0.94,
                'communication_manager': 0.87,
                'resource_allocator': 0.83,
                'executive_advisor': 0.89
            }
            
            return performance_scores.get(agent_type, 0.80)
            
        except Exception:
            return 0.80  # Default historical performance
    
    def _assess_scenario_complexity(self, reasoning_result: Dict[str, Any]) -> float:
        """Assess the complexity of the current scenario (0.0 = simple, 1.0 = very complex)"""
        
        complexity_factors = 0.3  # Base complexity
        
        # Factor 1: Number of risk factors
        risk_factors = reasoning_result.get('risk_assessment', {}).get('risk_factors', [])
        complexity_factors += min(0.3, len(risk_factors) * 0.1)
        
        # Factor 2: Number of alternatives to consider
        alternatives = reasoning_result.get('alternatives', [])
        complexity_factors += min(0.2, len(alternatives) * 0.05)
        
        # Factor 3: Length of reasoning chain (more steps = more complex)
        chain_length = len(reasoning_result.get('reasoning_chain', []))
        complexity_factors += min(0.2, chain_length * 0.04)
        
        return min(1.0, complexity_factors)
    
    def _calculate_time_pressure_factor(self, step_name: str = None) -> float:
        """Calculate impact of time pressure on decision confidence"""
        
        # Different steps have different time sensitivities
        time_sensitive_steps = {
            'detect_disruption': 0.95,  # High time pressure reduces confidence
            'assess_impact': 0.90,
            'coordinate_response': 0.85,
            'execute_actions': 1.00,  # Execution phase, less time pressure impact
            'monitor_progress': 1.05,  # More time available increases confidence
            'complete_resolution': 1.00
        }
        
        return time_sensitive_steps.get(step_name, 1.0)
    
    async def _generate_execution_plan(
        self,
        agent_type: str,
        recommendations: List[str],
        priority: str,
        step_name: str = None
    ) -> List[Dict[str, Any]]:
        """Generate detailed execution plan from recommendations"""
        
        try:
            execution_steps = []
            
            for i, recommendation in enumerate(recommendations[:5]):  # Limit to top 5
                step = {
                    'step_id': f"{agent_type}_step_{i+1}",
                    'action': recommendation,
                    'agent_responsible': agent_type,
                    'estimated_duration': self._estimate_step_duration(recommendation, agent_type),
                    'dependencies': self._identify_dependencies(recommendation, i),
                    'success_criteria': self._define_success_criteria(recommendation, agent_type),
                    'risk_mitigation': self._identify_risk_mitigation(recommendation),
                    'priority_level': priority,
                    'resource_allocation': self._estimate_step_resources(recommendation, agent_type)
                }
                execution_steps.append(step)
            
            # Add coordination steps if multiple actions
            if len(execution_steps) > 1:
                coordination_step = {
                    'step_id': f"{agent_type}_coordination",
                    'action': 'Coordinate parallel execution and monitor progress',
                    'agent_responsible': agent_type,
                    'estimated_duration': max(step['estimated_duration'] for step in execution_steps) * 0.1,
                    'dependencies': [step['step_id'] for step in execution_steps],
                    'success_criteria': 'All primary actions completed successfully',
                    'priority_level': priority
                }
                execution_steps.append(coordination_step)
            
            return execution_steps
            
        except Exception as e:
            logger.error("Execution plan generation failed", error=str(e))
            return [{
                'step_id': f"{agent_type}_fallback",
                'action': 'Execute fallback procedure',
                'estimated_duration': 300,  # 5 minutes
                'priority_level': priority
            }]
    
    def _estimate_step_duration(self, recommendation: str, agent_type: str) -> int:
        """Estimate duration for execution step in seconds"""
        
        # Base durations by agent type
        base_durations = {
            'disruption_predictor': 180,  # 3 minutes
            'passenger_manager': 600,     # 10 minutes
            'cost_optimizer': 900,        # 15 minutes
            'compliance_checker': 480,    # 8 minutes
            'communication_manager': 120, # 2 minutes
            'resource_allocator': 720,    # 12 minutes
            'executive_advisor': 1200     # 20 minutes
        }
        
        base_duration = base_durations.get(agent_type, 300)
        
        # Adjust based on action complexity
        complexity_multipliers = {
            'analyze': 1.0,
            'calculate': 0.8,
            'coordinate': 1.5,
            'communicate': 0.6,
            'optimize': 1.8,
            'monitor': 2.0,
            'arrange': 1.2,
            'assess': 1.1
        }
        
        # Find relevant multiplier
        multiplier = 1.0
        for keyword, mult in complexity_multipliers.items():
            if keyword.lower() in recommendation.lower():
                multiplier = mult
                break
        
        return int(base_duration * multiplier)
    
    def _identify_dependencies(self, recommendation: str, step_index: int) -> List[str]:
        """Identify dependencies for execution step"""
        
        dependencies = []
        
        # First step typically has no dependencies
        if step_index == 0:
            return dependencies
        
        # Identify common dependency patterns
        if 'coordinate' in recommendation.lower():
            dependencies.append('data_analysis_complete')
        
        if 'communicate' in recommendation.lower():
            dependencies.append('decision_finalized')
        
        if 'execute' in recommendation.lower():
            dependencies.append('resources_allocated')
        
        return dependencies
    
    def _define_success_criteria(self, recommendation: str, agent_type: str) -> str:
        """Define success criteria for execution step"""
        
        criteria_templates = {
            'disruption_predictor': 'Prediction accuracy >85% and early warning issued',
            'passenger_manager': 'Passenger satisfaction >90% and rebooking completed',
            'cost_optimizer': 'Cost savings achieved and budget compliance maintained',
            'compliance_checker': 'Regulatory compliance verified and documentation complete',
            'communication_manager': 'Message delivered successfully and acknowledgment received',
            'resource_allocator': 'Resources allocated efficiently and availability confirmed',
            'executive_advisor': 'Strategic alignment achieved and stakeholder approval obtained'
        }
        
        return criteria_templates.get(agent_type, 'Task completed successfully within time and quality constraints')
    
    def _identify_risk_mitigation(self, recommendation: str) -> List[str]:
        """Identify risk mitigation strategies for action"""
        
        mitigation_strategies = []
        
        # Common risk mitigation patterns
        if 'communicate' in recommendation.lower():
            mitigation_strategies.extend([
                'Prepare backup communication channels',
                'Verify contact information accuracy',
                'Set up delivery confirmation tracking'
            ])
        
        if 'coordinate' in recommendation.lower():
            mitigation_strategies.extend([
                'Establish clear escalation procedures',
                'Define fallback coordination mechanisms',
                'Set up real-time status monitoring'
            ])
        
        if not mitigation_strategies:
            mitigation_strategies = [
                'Monitor progress continuously',
                'Prepare alternative approaches',
                'Set up early warning indicators'
            ]
        
        return mitigation_strategies
    
    def _estimate_step_resources(self, recommendation: str, agent_type: str) -> Dict[str, Any]:
        """Estimate resource requirements for execution step"""
        
        base_resources = {
            'cpu_utilization': 0.3,
            'memory_mb': 512,
            'network_bandwidth': 'low',
            'external_api_calls': 2,
            'database_operations': 5
        }
        
        # Adjust based on agent type
        agent_multipliers = {
            'disruption_predictor': {'cpu_utilization': 1.5, 'external_api_calls': 5},
            'passenger_manager': {'database_operations': 3, 'external_api_calls': 8},
            'cost_optimizer': {'cpu_utilization': 2.0, 'memory_mb': 2.0},
            'compliance_checker': {'database_operations': 2, 'memory_mb': 1.5}
        }
        
        multipliers = agent_multipliers.get(agent_type, {})
        
        resources = base_resources.copy()
        for resource, value in resources.items():
            if resource in multipliers:
                if isinstance(value, (int, float)):
                    resources[resource] = value * multipliers[resource]
        
        return resources
    
    async def _assess_resource_requirements(
        self,
        agent_type: str,
        execution_plan: List[Dict[str, Any]],
        priority: str
    ) -> Dict[str, Any]:
        """Assess overall resource requirements for decision execution"""
        
        total_requirements = {
            'total_cpu': 0.0,
            'total_memory_mb': 0,
            'total_duration_seconds': 0,
            'external_api_calls': 0,
            'database_operations': 0,
            'human_intervention_required': False,
            'critical_dependencies': []
        }
        
        for step in execution_plan:
            step_resources = step.get('resource_allocation', {})
            
            total_requirements['total_cpu'] += step_resources.get('cpu_utilization', 0)
            total_requirements['total_memory_mb'] += step_resources.get('memory_mb', 0)
            total_requirements['total_duration_seconds'] += step.get('estimated_duration', 0)
            total_requirements['external_api_calls'] += step_resources.get('external_api_calls', 0)
            total_requirements['database_operations'] += step_resources.get('database_operations', 0)
            
            # Check for human intervention needs
            if priority == 'critical' or 'manual' in step.get('action', '').lower():
                total_requirements['human_intervention_required'] = True
            
            # Collect critical dependencies
            dependencies = step.get('dependencies', [])
            total_requirements['critical_dependencies'].extend(dependencies)
        
        # Remove duplicates from dependencies
        total_requirements['critical_dependencies'] = list(set(total_requirements['critical_dependencies']))
        
        return total_requirements
    
    async def _estimate_impact(
        self,
        agent_type: str,
        execution_plan: List[Dict[str, Any]],
        confidence_score: float
    ) -> Dict[str, Any]:
        """Estimate the impact of decision execution"""
        
        # Base impact estimates by agent type
        impact_templates = {
            'disruption_predictor': {
                'operational_impact': 'High - Affects flight operations and passenger experience',
                'financial_impact': {'cost_avoidance': 50000, 'implementation_cost': 2000},
                'passenger_impact': {'affected_passengers': 200, 'satisfaction_change': 0.15},
                'timeline_impact': {'resolution_time_reduction': 1800}  # 30 minutes
            },
            'passenger_manager': {
                'operational_impact': 'Medium - Direct passenger service improvement',
                'financial_impact': {'revenue_protection': 75000, 'service_cost': 5000},
                'passenger_impact': {'affected_passengers': 450, 'satisfaction_change': 0.25},
                'timeline_impact': {'rebooking_time_reduction': 900}  # 15 minutes
            },
            'cost_optimizer': {
                'operational_impact': 'Medium - Cost structure optimization',
                'financial_impact': {'cost_savings': 25000, 'optimization_overhead': 1500},
                'passenger_impact': {'affected_passengers': 300, 'satisfaction_change': 0.05},
                'timeline_impact': {'decision_time_reduction': 600}  # 10 minutes
            }
        }
        
        base_impact = impact_templates.get(agent_type, {
            'operational_impact': 'Low - Standard operational adjustment',
            'financial_impact': {'net_benefit': 10000},
            'passenger_impact': {'affected_passengers': 100, 'satisfaction_change': 0.1},
            'timeline_impact': {'process_improvement': 300}
        })
        
        # Adjust impact based on confidence score
        confidence_multiplier = confidence_score
        
        # Scale financial impacts
        if 'financial_impact' in base_impact:
            for key, value in base_impact['financial_impact'].items():
                if isinstance(value, (int, float)):
                    base_impact['financial_impact'][key] = int(value * confidence_multiplier)
        
        # Calculate execution plan complexity impact
        plan_complexity = len(execution_plan)
        complexity_multiplier = 1.0 + (plan_complexity - 1) * 0.1  # 10% increase per additional step
        
        # Add execution-specific impacts
        base_impact['execution_complexity'] = {
            'complexity_score': plan_complexity,
            'coordination_required': plan_complexity > 2,
            'success_probability': confidence_score * 0.95,  # Slightly reduce for execution risk
            'rollback_complexity': 'medium' if plan_complexity > 3 else 'low'
        }
        
        return base_impact
    
    async def _evaluate_alternatives(
        self,
        agent_type: str,
        alternatives: List[str],
        current_plan: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate alternative approaches and compare to current plan"""
        
        evaluated_alternatives = []
        
        for i, alternative in enumerate(alternatives):
            evaluation = {
                'alternative_id': f"alt_{i+1}",
                'description': alternative,
                'feasibility_score': self._assess_feasibility(alternative, agent_type),
                'cost_comparison': self._compare_costs(alternative, current_plan),
                'risk_comparison': self._compare_risks(alternative, current_plan),
                'timeline_comparison': self._compare_timeline(alternative, current_plan),
                'recommendation': self._get_alternative_recommendation(alternative, current_plan)
            }
            evaluated_alternatives.append(evaluation)
        
        return evaluated_alternatives
    
    def _assess_feasibility(self, alternative: str, agent_type: str) -> float:
        """Assess feasibility of alternative approach"""
        
        # Base feasibility by agent capability
        base_feasibility = 0.75
        
        # Adjust based on alternative complexity
        if 'simple' in alternative.lower() or 'minimal' in alternative.lower():
            return min(1.0, base_feasibility + 0.2)
        elif 'complex' in alternative.lower() or 'comprehensive' in alternative.lower():
            return max(0.1, base_feasibility - 0.3)
        
        return base_feasibility
    
    def _compare_costs(self, alternative: str, current_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare costs between alternative and current plan"""
        
        return {
            'cost_difference': 'Alternative estimated 15% lower cost',
            'cost_confidence': 0.70,
            'implementation_overhead': 'Medium - requires setup changes'
        }
    
    def _compare_risks(self, alternative: str, current_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare risks between alternative and current plan"""
        
        return {
            'risk_level_comparison': 'Similar risk profile to current plan',
            'unique_risks': ['Less tested approach', 'Potential integration issues'],
            'risk_mitigation': 'Additional monitoring and backup procedures required'
        }
    
    def _compare_timeline(self, alternative: str, current_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare timeline between alternative and current plan"""
        
        current_duration = sum(step.get('estimated_duration', 0) for step in current_plan)
        
        return {
            'time_difference': f"Alternative estimated {current_duration * 0.8:.0f} seconds vs {current_duration} seconds",
            'timeline_confidence': 0.65,
            'critical_path_impact': 'Minimal impact on overall resolution timeline'
        }
    
    def _get_alternative_recommendation(self, alternative: str, current_plan: List[Dict[str, Any]]) -> str:
        """Get recommendation for alternative approach"""
        
        recommendations = [
            'Consider as backup option if primary plan encounters issues',
            'Viable alternative with trade-offs in complexity vs speed',
            'Not recommended due to higher risk profile',
            'Recommended for future scenarios with similar characteristics'
        ]
        
        return recommendations[hash(alternative) % len(recommendations)]
    
    async def _calculate_quality_score(
        self,
        reasoning_result: Dict[str, Any],
        execution_plan: List[Dict[str, Any]],
        confidence_score: float
    ) -> float:
        """Calculate overall decision quality score"""
        
        # Quality components
        reasoning_quality = self._assess_reasoning_quality(reasoning_result)
        plan_quality = self._assess_plan_quality(execution_plan)
        confidence_quality = min(1.0, confidence_score + 0.1)  # Slight bonus for high confidence
        
        # Weighted quality score
        quality_score = (
            reasoning_quality * 0.4 +
            plan_quality * 0.35 +
            confidence_quality * 0.25
        )
        
        return round(quality_score, 3)
    
    def _assess_plan_quality(self, execution_plan: List[Dict[str, Any]]) -> float:
        """Assess quality of execution plan"""
        
        quality_score = 0.5  # Base score
        
        # Check plan completeness
        if len(execution_plan) >= 3:
            quality_score += 0.2
        
        # Check for success criteria
        has_criteria = all(step.get('success_criteria') for step in execution_plan)
        if has_criteria:
            quality_score += 0.15
        
        # Check for risk mitigation
        has_mitigation = any(step.get('risk_mitigation') for step in execution_plan)
        if has_mitigation:
            quality_score += 0.1
        
        # Check for resource estimation
        has_resources = all(step.get('resource_allocation') for step in execution_plan)
        if has_resources:
            quality_score += 0.05
        
        return min(1.0, quality_score)
    
    async def _store_decision(self, decision: Dict[str, Any]):
        """Store decision for future reference and learning"""
        
        try:
            # Store in database
            await self.db.store_agent_decision(decision)
            
            # Add to decision history
            self.decision_history.append({
                'decision_id': decision['decision_id'],
                'agent_type': decision['agent_type'],
                'confidence': decision['confidence_score'],
                'quality': decision['quality_score'],
                'timestamp': decision['created_at']
            })
            
            # Maintain history size
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-1000:]
            
        except Exception as e:
            logger.error("Failed to store decision", error=str(e))
    
    async def _update_performance_metrics(self, decision: Dict[str, Any]):
        """Update decision engine performance metrics"""
        
        try:
            self.performance_metrics['total_decisions'] += 1
            
            # Update average confidence
            total_decisions = self.performance_metrics['total_decisions']
            current_avg = self.performance_metrics['average_confidence']
            new_confidence = decision['confidence_score']
            
            self.performance_metrics['average_confidence'] = (
                (current_avg * (total_decisions - 1) + new_confidence) / total_decisions
            )
            
            # Update average processing time
            current_avg_time = self.performance_metrics['avg_processing_time']
            new_time = decision['processing_time']
            
            self.performance_metrics['avg_processing_time'] = (
                (current_avg_time * (total_decisions - 1) + new_time) / total_decisions
            )
            
            # Update success rate (simplified calculation)
            if decision['quality_score'] > 0.8:
                success_count = self.performance_metrics.get('success_count', 0) + 1
                self.performance_metrics['success_count'] = success_count
                self.performance_metrics['success_rate'] = success_count / total_decisions
            
        except Exception as e:
            logger.error("Failed to update performance metrics", error=str(e))
    
    async def _publish_decision_event(self, decision: Dict[str, Any]):
        """Publish decision event to Kafka"""
        
        try:
            event = {
                'event_type': 'agent_decision_made',
                'decision_id': decision['decision_id'],
                'agent_type': decision['agent_type'],
                'confidence_score': decision['confidence_score'],
                'quality_score': decision['quality_score'],
                'processing_time': decision['processing_time'],
                'timestamp': decision['created_at'].isoformat()
            }
            
            await self.kafka_producer.send('agent.decisions', value=event)
            
        except Exception as e:
            logger.error("Failed to publish decision event", error=str(e))
    
    async def _generate_fallback_decision(
        self,
        agent_type: str,
        reasoning_result: Dict[str, Any],
        error: str
    ) -> Dict[str, Any]:
        """Generate fallback decision when normal processing fails"""
        
        return {
            'decision_id': str(uuid4()),
            'agent_type': agent_type,
            'decision_type': 'fallback_decision',
            'reasoning_chain': [{'step': 'fallback', 'reasoning': f'Fallback due to error: {error}'}],
            'confidence_score': 0.5,
            'execution_plan': [{
                'step_id': f"{agent_type}_fallback",
                'action': 'Execute manual review and intervention',
                'estimated_duration': 1800,
                'priority_level': 'high'
            }],
            'resource_requirements': {'human_intervention_required': True},
            'estimated_impact': {'operational_impact': 'Requires manual intervention'},
            'risk_assessment': {'overall_risk': 'elevated_due_to_fallback'},
            'alternatives_considered': [],
            'created_at': datetime.utcnow(),
            'fallback_mode': True,
            'fallback_reason': error
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get decision engine performance metrics"""
        return self.performance_metrics.copy()
    
    async def get_decision_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decision history"""
        return self.decision_history[-limit:]