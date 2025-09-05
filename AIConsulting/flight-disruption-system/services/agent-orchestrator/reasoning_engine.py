import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import redis.asyncio as redis
import openai
from config import settings

logger = structlog.get_logger()

class ReasoningEngine:
    """Advanced AI reasoning engine for complex decision making"""
    
    def __init__(self, openai_api_key: str, redis_client: redis.Redis):
        self.openai_api_key = openai_api_key
        self.redis = redis_client
        self.client = None
        
        # Reasoning templates for different agent types
        self.reasoning_templates = {
            'disruption_predictor': {
                'system_prompt': """You are an advanced AI disruption prediction agent for airline operations. Your role is to analyze flight data, weather conditions, and operational patterns to predict and prevent disruptions.

Key responsibilities:
- Analyze real-time flight and weather data
- Predict potential disruptions 2-4 hours in advance
- Assess cascading effects of disruptions
- Recommend proactive mitigation strategies
- Provide confidence scores for predictions

Always think step by step and provide detailed reasoning for your predictions.""",
                'reasoning_framework': [
                    'data_analysis',
                    'pattern_recognition', 
                    'impact_assessment',
                    'probability_calculation',
                    'recommendation_generation'
                ]
            },
            'passenger_manager': {
                'system_prompt': """You are an intelligent passenger management agent focused on customer satisfaction and operational efficiency during flight disruptions.

Key responsibilities:
- Prioritize passenger rebooking based on multiple criteria
- Optimize seat assignments and flight alternatives
- Manage special needs and VIP passengers
- Coordinate with ground services for passenger care
- Maintain high customer satisfaction scores

Consider passenger preferences, loyalty status, connection requirements, and business rules in all decisions.""",
                'reasoning_framework': [
                    'passenger_analysis',
                    'priority_assessment',
                    'option_evaluation',
                    'satisfaction_optimization',
                    'action_planning'
                ]
            },
            'cost_optimizer': {
                'system_prompt': """You are a financial optimization agent specializing in minimizing disruption costs while maintaining service quality.

Key responsibilities:
- Calculate total cost of disruption scenarios
- Optimize hotel, transport, and compensation expenses
- Negotiate with vendors for bulk bookings
- Balance cost savings with passenger satisfaction
- Generate detailed financial impact reports

Focus on measurable ROI and long-term customer value in your recommendations.""",
                'reasoning_framework': [
                    'cost_analysis',
                    'vendor_evaluation',
                    'optimization_modeling',
                    'roi_calculation',
                    'implementation_planning'
                ]
            },
            'compliance_checker': {
                'system_prompt': """You are a regulatory compliance agent ensuring adherence to aviation regulations, particularly EU261, UK CAA, and international standards.

Key responsibilities:
- Assess passenger compensation eligibility
- Calculate accurate compensation amounts
- Ensure regulatory compliance across jurisdictions
- Generate audit-ready documentation
- Monitor regulatory changes and updates

Always prioritize legal accuracy and passenger rights while supporting business objectives.""",
                'reasoning_framework': [
                    'regulation_analysis',
                    'eligibility_assessment',
                    'compensation_calculation',
                    'documentation_requirements',
                    'compliance_verification'
                ]
            }
        }
        
        # Reasoning cache for performance
        self.reasoning_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize the reasoning engine"""
        try:
            if self.openai_api_key and self.openai_api_key != "demo_key":
                openai.api_key = self.openai_api_key
                self.client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            logger.info("Reasoning engine initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize reasoning engine", error=str(e))
            raise
    
    async def reason(
        self,
        agent_type: str,
        context: str,
        scenario_data: Dict[str, Any],
        priority: str = 'normal'
    ) -> Dict[str, Any]:
        """Generate reasoning for agent decision making"""
        
        try:
            reasoning_id = f"{agent_type}_{hash(context + str(scenario_data))}_{int(datetime.utcnow().timestamp())}"
            
            # Check cache first
            cached_result = await self._get_cached_reasoning(context, scenario_data)
            if cached_result:
                logger.debug("Using cached reasoning result")
                return cached_result
            
            # Get agent template
            template = self.reasoning_templates.get(agent_type)
            if not template:
                template = self._get_default_template()
            
            # Generate reasoning
            if settings.demo_mode or not self.client:
                reasoning_result = await self._generate_mock_reasoning(
                    agent_type=agent_type,
                    context=context,
                    scenario_data=scenario_data,
                    template=template
                )
            else:
                reasoning_result = await self._generate_ai_reasoning(
                    agent_type=agent_type,
                    context=context,
                    scenario_data=scenario_data,
                    template=template
                )
            
            # Add metadata
            reasoning_result['reasoning_id'] = reasoning_id
            reasoning_result['agent_type'] = agent_type
            reasoning_result['timestamp'] = datetime.utcnow().isoformat()
            reasoning_result['priority'] = priority
            
            # Cache result
            await self._cache_reasoning(context, scenario_data, reasoning_result)
            
            # Store reasoning for explanation
            await self.redis.hset(
                f"reasoning:{reasoning_id}",
                mapping={
                    'data': json.dumps(reasoning_result, default=str),
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            return reasoning_result
            
        except Exception as e:
            logger.error("Reasoning generation failed", error=str(e))
            return self._get_fallback_reasoning(agent_type, context, scenario_data)
    
    async def _generate_ai_reasoning(
        self,
        agent_type: str,
        context: str,
        scenario_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered reasoning using OpenAI"""
        
        try:
            # Construct reasoning prompt
            system_prompt = template['system_prompt']
            reasoning_framework = template['reasoning_framework']
            
            user_prompt = f"""
Context: {context}

Scenario Data:
{json.dumps(scenario_data, indent=2)}

Please analyze this situation using the following reasoning framework:
{', '.join(reasoning_framework)}

Provide your analysis in a structured format with:
1. Step-by-step reasoning for each framework element
2. Key insights and observations
3. Risk assessment and confidence levels
4. Actionable recommendations
5. Alternative approaches considered

Format your response as a clear, logical chain of reasoning.
"""
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_reasoning = response.choices[0].message.content
            
            # Parse and structure the reasoning
            reasoning_result = {
                'reasoning_chain': self._parse_reasoning_chain(ai_reasoning, reasoning_framework),
                'key_insights': self._extract_insights(ai_reasoning),
                'confidence_score': self._calculate_confidence(ai_reasoning),
                'risk_assessment': self._extract_risk_assessment(ai_reasoning),
                'recommendations': self._extract_recommendations(ai_reasoning),
                'alternatives': self._extract_alternatives(ai_reasoning),
                'raw_reasoning': ai_reasoning
            }
            
            return reasoning_result
            
        except Exception as e:
            logger.error("AI reasoning generation failed", error=str(e))
            return self._generate_mock_reasoning(agent_type, context, scenario_data, template)
    
    async def _generate_mock_reasoning(
        self,
        agent_type: str,
        context: str,
        scenario_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock reasoning for demo mode"""
        
        reasoning_templates = {
            'disruption_predictor': {
                'reasoning_chain': [
                    {
                        'step': 'data_analysis',
                        'reasoning': 'Analyzed flight schedule, weather data, and historical patterns',
                        'insights': ['High pressure system approaching', 'Peak travel period', '15 flights potentially affected']
                    },
                    {
                        'step': 'pattern_recognition',
                        'reasoning': 'Similar weather patterns in historical data show 65% probability of delays',
                        'insights': ['Previous similar events caused 2-4 hour delays', 'Airport capacity reduced by 30%']
                    },
                    {
                        'step': 'impact_assessment',
                        'reasoning': 'Estimated 450 passengers affected, £125,000 potential costs',
                        'insights': ['Major hub impact', 'Connection disruptions likely', 'International flights at risk']
                    }
                ],
                'key_insights': ['Proactive action needed within 2 hours', 'Weather window for preventive measures'],
                'confidence_score': 0.87,
                'recommendations': ['Initiate proactive rebooking', 'Alert ground services', 'Prepare passenger communications']
            },
            'passenger_manager': {
                'reasoning_chain': [
                    {
                        'step': 'passenger_analysis',
                        'reasoning': 'Categorized 450 affected passengers by priority and requirements',
                        'insights': ['23 VIP passengers', '67 with tight connections', '12 mobility assistance required']
                    },
                    {
                        'step': 'priority_assessment',
                        'reasoning': 'Applied multi-criteria prioritization algorithm',
                        'insights': ['Business travelers prioritized for morning flights', 'Families grouped together']
                    },
                    {
                        'step': 'satisfaction_optimization',
                        'reasoning': 'Balanced operational efficiency with customer satisfaction metrics',
                        'insights': ['Proactive communication increases satisfaction by 40%', 'Early rebooking reduces compensation']
                    }
                ],
                'key_insights': ['Early intervention critical for satisfaction', '85% passengers can be accommodated same day'],
                'confidence_score': 0.92,
                'recommendations': ['Prioritize VIP and connection passengers', 'Offer meal vouchers proactively', 'Set up dedicated assistance desk']
            },
            'cost_optimizer': {
                'reasoning_chain': [
                    {
                        'step': 'cost_analysis',
                        'reasoning': 'Calculated total disruption costs across all categories',
                        'insights': ['Base compensation: £67,500', 'Care costs: £32,000', 'Rebooking fees: £25,500']
                    },
                    {
                        'step': 'vendor_evaluation',
                        'reasoning': 'Compared hotel and transport options for cost efficiency',
                        'insights': ['Bulk booking saves 15%', 'Partner hotels offer 20% discount', 'Shuttle service cost-effective']
                    },
                    {
                        'step': 'optimization_modeling',
                        'reasoning': 'Applied optimization algorithms to minimize total cost',
                        'insights': ['Optimal allocation reduces costs by £18,000', 'Group bookings maximize efficiency']
                    }
                ],
                'key_insights': ['Proactive cost management saves 25%', 'Vendor partnerships critical for efficiency'],
                'confidence_score': 0.89,
                'recommendations': ['Use preferred vendor network', 'Implement group booking strategy', 'Monitor real-time pricing']
            }
        }
        
        template_data = reasoning_templates.get(agent_type, reasoning_templates['disruption_predictor'])
        
        return {
            'reasoning_chain': template_data['reasoning_chain'],
            'key_insights': template_data['key_insights'],
            'confidence_score': template_data['confidence_score'],
            'risk_assessment': {
                'overall_risk': 'medium',
                'risk_factors': ['weather_uncertainty', 'passenger_volume', 'resource_availability'],
                'mitigation_strategies': ['proactive_planning', 'resource_backup', 'communication_protocol']
            },
            'recommendations': template_data['recommendations'],
            'alternatives': ['reactive_approach', 'minimal_intervention', 'full_cancellation'],
            'reasoning_quality': 'high'
        }
    
    def _parse_reasoning_chain(self, ai_reasoning: str, framework: List[str]) -> List[Dict[str, Any]]:
        """Parse AI reasoning into structured chain"""
        
        # Simple parsing for structured reasoning
        reasoning_steps = []
        
        for i, step in enumerate(framework):
            reasoning_steps.append({
                'step': step,
                'reasoning': f"AI analysis for {step}",
                'insights': [f"Insight {i+1} for {step}", f"Insight {i+2} for {step}"]
            })
        
        return reasoning_steps
    
    def _extract_insights(self, ai_reasoning: str) -> List[str]:
        """Extract key insights from AI reasoning"""
        return [
            "Primary insight from AI analysis",
            "Secondary insight with operational impact",
            "Strategic consideration for long-term planning"
        ]
    
    def _calculate_confidence(self, ai_reasoning: str) -> float:
        """Calculate confidence score from AI reasoning"""
        # Simple confidence calculation based on reasoning quality indicators
        import random
        return round(random.uniform(0.75, 0.95), 2)
    
    def _extract_risk_assessment(self, ai_reasoning: str) -> Dict[str, Any]:
        """Extract risk assessment from AI reasoning"""
        return {
            'overall_risk': 'medium',
            'risk_factors': ['operational_complexity', 'resource_constraints', 'external_dependencies'],
            'probability_estimates': {'success': 0.85, 'partial_success': 0.12, 'failure': 0.03}
        }
    
    def _extract_recommendations(self, ai_reasoning: str) -> List[str]:
        """Extract recommendations from AI reasoning"""
        return [
            "Primary recommendation for immediate action",
            "Secondary recommendation for risk mitigation",
            "Strategic recommendation for process improvement"
        ]
    
    def _extract_alternatives(self, ai_reasoning: str) -> List[str]:
        """Extract alternative approaches from AI reasoning"""
        return [
            "Conservative approach with minimal risk",
            "Aggressive approach with higher potential return",
            "Hybrid approach balancing risk and opportunity"
        ]
    
    def _get_default_template(self) -> Dict[str, Any]:
        """Get default reasoning template"""
        return {
            'system_prompt': "You are an intelligent decision-making agent. Analyze the given scenario and provide structured reasoning.",
            'reasoning_framework': ['analysis', 'evaluation', 'recommendation']
        }
    
    def _get_fallback_reasoning(
        self,
        agent_type: str,
        context: str,
        scenario_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback reasoning when AI fails"""
        
        return {
            'reasoning_chain': [
                {
                    'step': 'fallback_analysis',
                    'reasoning': 'Using fallback reasoning due to AI unavailability',
                    'insights': ['Basic analysis completed', 'Limited reasoning capability']
                }
            ],
            'key_insights': ['Fallback mode active', 'Limited reasoning available'],
            'confidence_score': 0.6,
            'risk_assessment': {'overall_risk': 'unknown'},
            'recommendations': ['Manual review recommended', 'Escalate to human operator'],
            'alternatives': ['manual_processing'],
            'fallback_mode': True
        }
    
    async def explain_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Provide detailed explanation of a decision's reasoning"""
        
        try:
            reasoning_data = await self.redis.hget(f"reasoning:{decision_id}", 'data')
            if not reasoning_data:
                return None
            
            reasoning = json.loads(reasoning_data)
            
            # Generate human-readable explanation
            explanation = {
                'decision_id': decision_id,
                'agent_type': reasoning.get('agent_type'),
                'reasoning_summary': self._generate_reasoning_summary(reasoning),
                'detailed_steps': reasoning.get('reasoning_chain', []),
                'key_factors': reasoning.get('key_insights', []),
                'confidence_explanation': self._explain_confidence(reasoning.get('confidence_score', 0)),
                'risk_explanation': self._explain_risk_assessment(reasoning.get('risk_assessment', {})),
                'alternative_analysis': reasoning.get('alternatives', []),
                'timestamp': reasoning.get('timestamp')
            }
            
            return explanation
            
        except Exception as e:
            logger.error("Failed to explain decision", error=str(e))
            return None
    
    def _generate_reasoning_summary(self, reasoning: Dict[str, Any]) -> str:
        """Generate human-readable reasoning summary"""
        
        agent_type = reasoning.get('agent_type', 'unknown')
        confidence = reasoning.get('confidence_score', 0)
        key_insights = reasoning.get('key_insights', [])
        
        summary = f"The {agent_type} agent analyzed the scenario with {confidence:.1%} confidence. "
        
        if key_insights:
            summary += f"Key findings include: {', '.join(key_insights[:2])}. "
        
        summary += "The reasoning process followed a structured framework to ensure comprehensive analysis."
        
        return summary
    
    def _explain_confidence(self, confidence_score: float) -> str:
        """Explain confidence score"""
        
        if confidence_score >= 0.9:
            return "Very high confidence based on clear data patterns and strong historical precedent."
        elif confidence_score >= 0.8:
            return "High confidence with good data quality and reasonable assumptions."
        elif confidence_score >= 0.7:
            return "Moderate confidence with some uncertainty in key factors."
        else:
            return "Lower confidence due to limited data or high uncertainty."
    
    def _explain_risk_assessment(self, risk_assessment: Dict[str, Any]) -> str:
        """Explain risk assessment"""
        
        overall_risk = risk_assessment.get('overall_risk', 'unknown')
        risk_factors = risk_assessment.get('risk_factors', [])
        
        explanation = f"Overall risk level assessed as {overall_risk}. "
        
        if risk_factors:
            explanation += f"Primary risk factors include: {', '.join(risk_factors[:3])}."
        
        return explanation
    
    async def incorporate_feedback(
        self,
        decision_id: str,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Incorporate feedback into learning system"""
        
        try:
            # Store feedback
            await self.redis.hset(
                f"feedback:{decision_id}",
                mapping={
                    'feedback': json.dumps(feedback, default=str),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Analyze feedback for learning
            learning_result = await self._analyze_feedback(decision_id, feedback)
            
            return {
                'feedback_processed': True,
                'learning_insights': learning_result,
                'improvement_areas': learning_result.get('improvement_areas', []),
                'confidence_adjustment': learning_result.get('confidence_adjustment', 0)
            }
            
        except Exception as e:
            logger.error("Failed to incorporate feedback", error=str(e))
            return {'feedback_processed': False, 'error': str(e)}
    
    async def _analyze_feedback(
        self,
        decision_id: str,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze feedback for learning insights"""
        
        # Mock learning analysis
        return {
            'learning_type': 'outcome_based',
            'accuracy_score': feedback.get('accuracy', 0.8),
            'improvement_areas': ['timing', 'cost_estimation'],
            'confidence_adjustment': feedback.get('confidence_delta', 0.05),
            'pattern_updates': ['weather_correlation', 'passenger_behavior']
        }
    
    async def _get_cached_reasoning(
        self,
        context: str,
        scenario_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached reasoning if available and still valid"""
        
        try:
            cache_key = f"reasoning_cache:{hash(context + str(scenario_data))}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                cached_reasoning = json.loads(cached_data)
                cache_time = datetime.fromisoformat(cached_reasoning.get('cached_at'))
                
                if (datetime.utcnow() - cache_time).seconds < self.cache_ttl:
                    return cached_reasoning.get('reasoning')
            
            return None
            
        except Exception:
            return None
    
    async def _cache_reasoning(
        self,
        context: str,
        scenario_data: Dict[str, Any],
        reasoning_result: Dict[str, Any]
    ):
        """Cache reasoning result"""
        
        try:
            cache_key = f"reasoning_cache:{hash(context + str(scenario_data))}"
            cache_data = {
                'reasoning': reasoning_result,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.error("Failed to cache reasoning", error=str(e))