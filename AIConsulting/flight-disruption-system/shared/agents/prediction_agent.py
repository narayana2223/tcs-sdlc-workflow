"""
Prediction Agent for Flight Disruption Management System

This agent specializes in forecasting flight disruptions using ML models,
data analysis, and external data sources. It provides 2-4 hour advance
predictions with confidence levels and impact assessments.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .base_agent import BaseAgent, AgentType, DecisionConfidence
from .tools import tool_registry, ToolCategory


class PredictionAgent(BaseAgent):
    """Agent specialized in disruption prediction and impact analysis"""
    
    def __init__(self, 
                 agent_id: str,
                 llm: ChatOpenAI,
                 shared_memory,
                 performance_monitor,
                 **kwargs):
        
        # Get tools specific to prediction tasks
        tools = tool_registry.get_tools_for_agent("prediction")
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PREDICTION,
            llm=llm,
            shared_memory=shared_memory,
            performance_monitor=performance_monitor,
            tools=tools,
            **kwargs
        )
        
        # Prediction-specific configuration
        self.prediction_window_hours = 4
        self.confidence_threshold = 0.7
        self.max_predictions_per_request = 50
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type="prediction"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the prediction agent"""
        return """You are a Flight Disruption Prediction Agent with expertise in:
        
1. FLIGHT OPERATIONS ANALYSIS
   - Analyze flight schedules, aircraft utilization, and crew availability
   - Identify potential bottlenecks and operational constraints
   - Assess airline network effects and cascading delays
   
2. WEATHER IMPACT ASSESSMENT
   - Process meteorological data and aviation weather reports
   - Evaluate weather impact on flight operations
   - Predict weather-related delays and cancellations
   
3. TECHNICAL DISRUPTION PREDICTION
   - Analyze aircraft maintenance patterns and technical issues
   - Assess risk of technical delays based on fleet data
   - Predict maintenance-related disruptions
   
4. PREDICTIVE MODELING
   - Use historical data to identify disruption patterns
   - Apply machine learning models for disruption forecasting
   - Provide confidence levels and risk assessments
   
5. IMPACT ANALYSIS
   - Calculate passenger impact and affected routes
   - Estimate operational and financial consequences
   - Recommend proactive mitigation strategies

KEY CAPABILITIES:
- Provide 2-4 hour advance predictions with 85%+ accuracy
- Analyze multiple data sources simultaneously
- Generate actionable insights for operations teams
- Assess disruption probability and impact severity
- Recommend preventive actions and resource allocation

DECISION MAKING APPROACH:
1. Collect and analyze relevant data from multiple sources
2. Apply predictive models and pattern recognition
3. Calculate disruption probability and confidence levels
4. Assess potential impact on passengers and operations
5. Generate recommendations with cost-benefit analysis
6. Provide clear reasoning for all predictions and recommendations

Always provide detailed reasoning for your predictions and include confidence levels.
Consider both immediate impacts and cascading effects on the airline network."""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process prediction-related tasks"""
        task_type = task.get("type", "")
        
        if task_type == "situation_assessment":
            return await self._assess_situation(task)
        elif task_type == "impact_prediction":
            return await self._predict_impact(task)
        elif task_type == "disruption_forecast":
            return await self._forecast_disruptions(task)
        elif task_type == "pattern_analysis":
            return await self._analyze_patterns(task)
        elif task_type == "risk_assessment":
            return await self._assess_risks(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _assess_situation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current disruption situation"""
        context = task.get("context", {})
        urgency = task.get("urgency", 2)
        
        self.logger.info("Assessing disruption situation", urgency=urgency)
        
        try:
            # Analyze flight data
            flight_analysis = await self._analyze_flight_data(context)
            
            # Check weather conditions
            weather_analysis = await self._analyze_weather_data(context)
            
            # Assess operational factors
            operational_analysis = await self._analyze_operational_factors(context)
            
            # Generate overall situation assessment
            situation_prompt = f"""
            Analyze the current flight disruption situation based on the following data:

            FLIGHT DATA:
            {json.dumps(flight_analysis, indent=2)}

            WEATHER DATA:
            {json.dumps(weather_analysis, indent=2)}

            OPERATIONAL FACTORS:
            {json.dumps(operational_analysis, indent=2)}

            URGENCY LEVEL: {urgency}/5

            Please provide a comprehensive situation assessment including:
            1. Current disruption status and severity
            2. Root causes and contributing factors
            3. Immediate risks and concerns
            4. Recommended immediate actions
            5. Confidence level in assessment

            Format your response as JSON with clear categories and actionable insights.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=situation_prompt)
            ])
            
            # Parse and structure the response
            assessment = self._parse_assessment_response(response.content)
            
            # Store assessment in shared memory for other agents
            await self.shared_memory.store(
                f"situation_assessment_{context.get('incident_id', 'current')}",
                assessment,
                ttl=3600  # 1 hour TTL
            )
            
            return {
                "status": "completed",
                "assessment": assessment,
                "confidence": assessment.get("confidence", "medium"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Situation assessment failed", error=str(e))
            raise
    
    async def _predict_impact(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Predict the impact of disruption"""
        context = task.get("context", {})
        assessment = task.get("assessment", {})
        
        self.logger.info("Predicting disruption impact")
        
        try:
            # Use disruption analyzer tool
            disruption_analyzer = tool_registry.get_tool("disruption_analyzer")
            
            disruption_data = {
                "disruption_type": context.get("disruption_type", "unknown"),
                "airport_code": context.get("airport_code", "LHR"),
                "start_time": context.get("start_time", datetime.now().isoformat()),
                "severity": assessment.get("severity", "medium")
            }
            
            analysis_result = await disruption_analyzer.arun(**disruption_data)
            
            # Generate detailed impact prediction
            impact_prompt = f"""
            Based on the disruption analysis, predict the comprehensive impact:

            DISRUPTION ANALYSIS:
            {json.dumps(analysis_result, indent=2)}

            SITUATION ASSESSMENT:
            {json.dumps(assessment, indent=2)}

            Please provide a detailed impact prediction including:
            1. Passenger impact (numbers, categories, special needs)
            2. Flight operations impact (delays, cancellations, diversions)
            3. Financial impact (direct costs, compensation, revenue loss)
            4. Network effects (cascading delays, connecting flights)
            5. Timeline of expected impacts
            6. Mitigation opportunities and recommendations

            Include confidence levels and ranges for all numerical estimates.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=impact_prompt)
            ])
            
            impact_prediction = self._parse_impact_response(response.content)
            
            # Enhance with quantitative analysis
            impact_prediction["quantitative_analysis"] = analysis_result
            
            return {
                "status": "completed",
                "impact_prediction": impact_prediction,
                "confidence": impact_prediction.get("confidence", "medium"),
                "prediction_horizon": "4_hours",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Impact prediction failed", error=str(e))
            raise
    
    async def _forecast_disruptions(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate disruption forecasts for the next 4 hours"""
        context = task.get("context", {})
        forecast_window = task.get("forecast_window_hours", self.prediction_window_hours)
        
        self.logger.info("Generating disruption forecasts", window_hours=forecast_window)
        
        try:
            # Get flight status for relevant flights
            flight_checker = tool_registry.get_tool("flight_status_checker")
            
            # Check multiple flights based on context
            flights_to_check = context.get("flights", [])
            if not flights_to_check:
                # Default to checking common routes if no specific flights provided
                flights_to_check = ["BA123", "BA456", "BA789"]
            
            flight_statuses = []
            for flight in flights_to_check[:10]:  # Limit to avoid overload
                try:
                    status = await flight_checker.arun(
                        flight_number=flight,
                        date=datetime.now().strftime("%Y-%m-%d")
                    )
                    flight_statuses.append(status)
                except Exception as e:
                    self.logger.warning("Failed to check flight status", 
                                      flight=flight, error=str(e))
            
            # Generate forecast based on current data and patterns
            forecast_prompt = f"""
            Generate a 4-hour disruption forecast based on current flight data and patterns:

            CURRENT FLIGHT STATUSES:
            {json.dumps(flight_statuses, indent=2)}

            CONTEXT DATA:
            {json.dumps(context, indent=2)}

            Please provide forecasts for:
            1. Probability of new disruptions by hour
            2. Expected delay patterns and duration
            3. Risk of cancellations by route/time
            4. Weather-related impacts
            5. Network effect predictions
            6. Passenger impact estimates

            Include:
            - Confidence intervals for all predictions
            - Key risk factors and triggers
            - Recommended monitoring points
            - Early warning indicators
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=forecast_prompt)
            ])
            
            forecast = self._parse_forecast_response(response.content)
            
            # Add current flight status data
            forecast["current_flight_data"] = flight_statuses
            
            # Store forecast for other agents
            await self.shared_memory.store(
                "disruption_forecast_current",
                forecast,
                ttl=1800  # 30 minutes TTL
            )
            
            return {
                "status": "completed",
                "forecast": forecast,
                "forecast_window_hours": forecast_window,
                "generated_at": datetime.now().isoformat(),
                "valid_until": (datetime.now() + timedelta(hours=forecast_window)).isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Disruption forecasting failed", error=str(e))
            raise
    
    async def _analyze_patterns(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze disruption patterns from historical data"""
        context = task.get("context", {})
        
        self.logger.info("Analyzing disruption patterns")
        
        try:
            # Get recent decisions and patterns from shared memory
            recent_context = await self.get_relevant_context("pattern_analysis")
            
            pattern_prompt = f"""
            Analyze disruption patterns based on available data:

            RECENT CONTEXT:
            {json.dumps(recent_context, indent=2)}

            CURRENT CONTEXT:
            {json.dumps(context, indent=2)}

            Please identify:
            1. Recurring disruption patterns
            2. Seasonal/temporal trends
            3. Weather correlation patterns
            4. Airport-specific patterns
            5. Aircraft type vulnerabilities
            6. Network vulnerability points

            Provide actionable insights for:
            - Proactive disruption prevention
            - Resource pre-positioning
            - Schedule optimization
            - Risk mitigation strategies
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=pattern_prompt)
            ])
            
            patterns = self._parse_pattern_response(response.content)
            
            return {
                "status": "completed",
                "patterns": patterns,
                "analysis_period": "24_hours",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Pattern analysis failed", error=str(e))
            raise
    
    async def _assess_risks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assess various risks related to flight operations"""
        context = task.get("context", {})
        
        self.logger.info("Assessing operational risks")
        
        try:
            risk_prompt = f"""
            Assess operational risks based on current context:

            CONTEXT:
            {json.dumps(context, indent=2)}

            Evaluate risks in the following categories:
            1. Weather risks (probability, impact, timing)
            2. Technical risks (aircraft, systems, maintenance)
            3. Operational risks (crew, airport, ATC)
            4. Network risks (cascading effects, bottlenecks)
            5. External risks (strikes, security, etc.)

            For each risk, provide:
            - Probability (0-1 scale)
            - Impact severity (low/medium/high/critical)
            - Time horizon (immediate/short-term/medium-term)
            - Mitigation strategies
            - Monitoring indicators
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=risk_prompt)
            ])
            
            risk_assessment = self._parse_risk_response(response.content)
            
            return {
                "status": "completed",
                "risk_assessment": risk_assessment,
                "assessment_time": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Risk assessment failed", error=str(e))
            raise
    
    # Helper methods for data analysis
    
    async def _analyze_flight_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current flight data"""
        # In a real implementation, this would connect to flight data APIs
        return {
            "active_flights": context.get("flight_count", 250),
            "average_delay": context.get("average_delay_minutes", 15),
            "delay_trend": "increasing",
            "critical_routes": ["LHR-CDG", "LHR-FRA", "LHR-AMS"],
            "aircraft_utilization": 0.85
        }
    
    async def _analyze_weather_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze weather conditions"""
        # Mock weather analysis
        return {
            "current_conditions": context.get("weather", "cloudy"),
            "forecast_confidence": 0.8,
            "wind_speed": 25,
            "visibility": 8000,
            "precipitation_probability": 0.3,
            "severe_weather_risk": "low"
        }
    
    async def _analyze_operational_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze operational factors"""
        return {
            "crew_availability": 0.95,
            "ground_handling_capacity": 0.8,
            "atc_capacity": context.get("atc_capacity", 0.9),
            "airport_congestion": context.get("congestion_level", "moderate"),
            "maintenance_backlog": 3
        }
    
    # Response parsing methods
    
    def _parse_assessment_response(self, response: str) -> Dict[str, Any]:
        """Parse situation assessment response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing
        return {
            "severity": "medium",
            "confidence": "medium",
            "summary": response,
            "immediate_actions": [],
            "risk_factors": []
        }
    
    def _parse_impact_response(self, response: str) -> Dict[str, Any]:
        """Parse impact prediction response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "passenger_impact": {"affected_count": 0},
            "financial_impact": {"estimated_cost": 0},
            "operational_impact": {"delayed_flights": 0},
            "confidence": "medium",
            "summary": response
        }
    
    def _parse_forecast_response(self, response: str) -> Dict[str, Any]:
        """Parse disruption forecast response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "hourly_predictions": [],
            "key_risks": [],
            "confidence": "medium",
            "summary": response
        }
    
    def _parse_pattern_response(self, response: str) -> Dict[str, Any]:
        """Parse pattern analysis response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "identified_patterns": [],
            "trends": [],
            "recommendations": [],
            "confidence": "medium",
            "summary": response
        }
    
    def _parse_risk_response(self, response: str) -> Dict[str, Any]:
        """Parse risk assessment response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "risk_categories": {},
            "overall_risk_level": "medium",
            "mitigation_strategies": [],
            "confidence": "medium",
            "summary": response
        }