import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import structlog

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.schema import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langgraph import StateGraph, END
from pydantic import BaseModel

logger = structlog.get_logger()

class PredictionState(BaseModel):
    """State for the prediction workflow"""
    flight_data: Dict[str, Any]
    weather_data: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    aircraft_type: str
    route: str
    analysis_results: Dict[str, Any] = {}
    prediction: Dict[str, Any] = {}
    confidence_factors: List[str] = []
    risk_factors: List[str] = []
    recommended_actions: List[str] = []

class PredictionAgent:
    """AI Agent for flight disruption prediction"""
    
    def __init__(self, openai_api_key: str, weather_api_key: str):
        self.openai_api_key = openai_api_key
        self.weather_api_key = weather_api_key
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4-turbo-preview",
            temperature=0.1
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=ConversationBufferWindowMemory(k=5)
        )
        
        # Initialize prediction workflow
        self.workflow = self._create_prediction_workflow()
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools for the agent"""
        return [
            Tool(
                name="weather_analyzer",
                description="Analyze weather conditions and their impact on flight operations",
                func=self._analyze_weather
            ),
            Tool(
                name="historical_analyzer",
                description="Analyze historical disruption patterns for similar flights",
                func=self._analyze_historical_data
            ),
            Tool(
                name="aircraft_analyzer",
                description="Analyze aircraft-specific risk factors",
                func=self._analyze_aircraft_factors
            ),
            Tool(
                name="route_analyzer",
                description="Analyze route-specific factors and congestion patterns",
                func=self._analyze_route_factors
            ),
            Tool(
                name="operational_analyzer",
                description="Analyze operational factors like crew, maintenance, and airport capacity",
                func=self._analyze_operational_factors
            )
        ]
    
    def _create_prediction_workflow(self) -> StateGraph:
        """Create the prediction workflow using LangGraph"""
        workflow = StateGraph(PredictionState)
        
        # Add nodes
        workflow.add_node("weather_analysis", self._weather_analysis_node)
        workflow.add_node("historical_analysis", self._historical_analysis_node)
        workflow.add_node("aircraft_analysis", self._aircraft_analysis_node)
        workflow.add_node("route_analysis", self._route_analysis_node)
        workflow.add_node("risk_synthesis", self._risk_synthesis_node)
        workflow.add_node("prediction_generation", self._prediction_generation_node)
        
        # Set entry point
        workflow.set_entry_point("weather_analysis")
        
        # Add edges
        workflow.add_edge("weather_analysis", "historical_analysis")
        workflow.add_edge("historical_analysis", "aircraft_analysis")
        workflow.add_edge("aircraft_analysis", "route_analysis")
        workflow.add_edge("route_analysis", "risk_synthesis")
        workflow.add_edge("risk_synthesis", "prediction_generation")
        workflow.add_edge("prediction_generation", END)
        
        return workflow.compile()
    
    async def predict_disruption(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main prediction method"""
        try:
            # Initialize state
            state = PredictionState(
                flight_data=input_data["flight_data"],
                weather_data=input_data["weather_data"],
                historical_data=input_data["historical_data"],
                aircraft_type=input_data["aircraft_type"],
                route=input_data["route"]
            )
            
            # Run workflow
            result = await self.workflow.ainvoke(state.dict())
            
            # Extract final prediction
            prediction = result["prediction"]
            
            logger.info(
                "Prediction completed",
                flight_id=input_data["flight_data"].get("id"),
                confidence=prediction.get("confidence_score")
            )
            
            return prediction
            
        except Exception as e:
            logger.error("Prediction failed", error=str(e))
            raise
    
    async def _weather_analysis_node(self, state: PredictionState) -> PredictionState:
        """Analyze weather conditions"""
        weather_prompt = PromptTemplate(
            input_variables=["weather_data", "route", "departure_time"],
            template="""
            Analyze the weather conditions for flight disruption risk:
            
            Weather Data: {weather_data}
            Route: {route}
            Departure Time: {departure_time}
            
            Consider:
            1. Visibility conditions
            2. Wind speed and direction
            3. Precipitation
            4. Temperature extremes
            5. Pressure systems
            6. Seasonal patterns
            
            Provide:
            - Weather risk score (0-1)
            - Key weather concerns
            - Impact on flight operations
            - Recommended monitoring points
            
            Format as JSON.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=weather_prompt)
        
        result = await chain.arun(
            weather_data=json.dumps(state.weather_data),
            route=state.route,
            departure_time=state.flight_data.get("scheduled_departure")
        )
        
        try:
            weather_analysis = json.loads(result)
            state.analysis_results["weather"] = weather_analysis
            
            # Extract risk factors
            if weather_analysis.get("weather_risk_score", 0) > 0.5:
                state.risk_factors.extend(weather_analysis.get("key_concerns", []))
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse weather analysis JSON")
            state.analysis_results["weather"] = {"weather_risk_score": 0.2}
        
        return state
    
    async def _historical_analysis_node(self, state: PredictionState) -> PredictionState:
        """Analyze historical disruption patterns"""
        historical_prompt = PromptTemplate(
            input_variables=["historical_data", "route", "aircraft_type", "season"],
            template="""
            Analyze historical disruption patterns:
            
            Historical Data: {historical_data}
            Route: {route}
            Aircraft Type: {aircraft_type}
            Season: {season}
            
            Analyze:
            1. Frequency of disruptions on this route
            2. Common disruption types
            3. Seasonal patterns
            4. Aircraft-specific issues
            5. Time-of-day patterns
            6. Recovery patterns
            
            Provide:
            - Historical risk score (0-1)
            - Most common disruption types
            - Seasonal risk factors
            - Pattern-based recommendations
            
            Format as JSON.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=historical_prompt)
        
        current_season = self._get_current_season()
        
        result = await chain.arun(
            historical_data=json.dumps(state.historical_data[:10]),  # Limit data size
            route=state.route,
            aircraft_type=state.aircraft_type,
            season=current_season
        )
        
        try:
            historical_analysis = json.loads(result)
            state.analysis_results["historical"] = historical_analysis
            
            # Extract risk factors
            if historical_analysis.get("historical_risk_score", 0) > 0.4:
                state.risk_factors.extend(historical_analysis.get("seasonal_risk_factors", []))
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse historical analysis JSON")
            state.analysis_results["historical"] = {"historical_risk_score": 0.3}
        
        return state
    
    async def _aircraft_analysis_node(self, state: PredictionState) -> PredictionState:
        """Analyze aircraft-specific factors"""
        aircraft_prompt = PromptTemplate(
            input_variables=["aircraft_type", "flight_data"],
            template="""
            Analyze aircraft-specific risk factors:
            
            Aircraft Type: {aircraft_type}
            Flight Data: {flight_data}
            
            Consider:
            1. Aircraft age and maintenance history
            2. Known technical issues for this aircraft type
            3. Performance in current weather conditions
            4. Range and fuel efficiency factors
            5. Ground handling requirements
            6. Crew requirements
            
            Provide:
            - Aircraft risk score (0-1)
            - Technical risk factors
            - Maintenance considerations
            - Operational limitations
            
            Format as JSON.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=aircraft_prompt)
        
        result = await chain.arun(
            aircraft_type=state.aircraft_type,
            flight_data=json.dumps(state.flight_data)
        )
        
        try:
            aircraft_analysis = json.loads(result)
            state.analysis_results["aircraft"] = aircraft_analysis
            
            # Extract risk factors
            if aircraft_analysis.get("aircraft_risk_score", 0) > 0.3:
                state.risk_factors.extend(aircraft_analysis.get("technical_risk_factors", []))
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse aircraft analysis JSON")
            state.analysis_results["aircraft"] = {"aircraft_risk_score": 0.1}
        
        return state
    
    async def _route_analysis_node(self, state: PredictionState) -> PredictionState:
        """Analyze route-specific factors"""
        route_prompt = PromptTemplate(
            input_variables=["route", "departure_time", "flight_data"],
            template="""
            Analyze route-specific operational factors:
            
            Route: {route}
            Departure Time: {departure_time}
            Flight Data: {flight_data}
            
            Consider:
            1. Airport congestion patterns
            2. Air traffic control delays
            3. Slot restrictions
            4. Ground handling capacity
            5. Security queue times
            6. Connecting flight impacts
            7. Peak vs off-peak operations
            
            Provide:
            - Route operational risk score (0-1)
            - Congestion factors
            - Peak time impacts
            - Infrastructure limitations
            
            Format as JSON.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=route_prompt)
        
        result = await chain.arun(
            route=state.route,
            departure_time=state.flight_data.get("scheduled_departure"),
            flight_data=json.dumps(state.flight_data)
        )
        
        try:
            route_analysis = json.loads(result)
            state.analysis_results["route"] = route_analysis
            
            # Extract risk factors
            if route_analysis.get("route_operational_risk_score", 0) > 0.4:
                state.risk_factors.extend(route_analysis.get("congestion_factors", []))
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse route analysis JSON")
            state.analysis_results["route"] = {"route_operational_risk_score": 0.2}
        
        return state
    
    async def _risk_synthesis_node(self, state: PredictionState) -> PredictionState:
        """Synthesize all risk factors"""
        synthesis_prompt = PromptTemplate(
            input_variables=["weather_analysis", "historical_analysis", "aircraft_analysis", "route_analysis"],
            template="""
            Synthesize all risk factors to determine overall disruption risk:
            
            Weather Analysis: {weather_analysis}
            Historical Analysis: {historical_analysis}
            Aircraft Analysis: {aircraft_analysis}
            Route Analysis: {route_analysis}
            
            Calculate:
            1. Overall risk score (weighted combination)
            2. Primary risk factors
            3. Secondary risk factors
            4. Risk mitigation opportunities
            5. Confidence level in assessment
            
            Weighting:
            - Weather: 40%
            - Historical: 25%
            - Aircraft: 20%
            - Route: 15%
            
            Provide:
            - Overall risk score (0-1)
            - Top 3 risk factors
            - Confidence level (0-1)
            - Risk category (low/medium/high)
            
            Format as JSON.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=synthesis_prompt)
        
        result = await chain.arun(
            weather_analysis=json.dumps(state.analysis_results.get("weather", {})),
            historical_analysis=json.dumps(state.analysis_results.get("historical", {})),
            aircraft_analysis=json.dumps(state.analysis_results.get("aircraft", {})),
            route_analysis=json.dumps(state.analysis_results.get("route", {}))
        )
        
        try:
            synthesis = json.loads(result)
            state.analysis_results["synthesis"] = synthesis
        except json.JSONDecodeError:
            logger.warning("Failed to parse synthesis JSON")
            state.analysis_results["synthesis"] = {"overall_risk_score": 0.3, "confidence_level": 0.5}
        
        return state
    
    async def _prediction_generation_node(self, state: PredictionState) -> PredictionState:
        """Generate final prediction"""
        prediction_prompt = PromptTemplate(
            input_variables=["synthesis", "risk_factors", "flight_data"],
            template="""
            Generate final disruption prediction:
            
            Risk Synthesis: {synthesis}
            Risk Factors: {risk_factors}
            Flight Data: {flight_data}
            
            Generate:
            1. Predicted disruption type (weather/technical/operational/crew/atc/none)
            2. Predicted delay in minutes (0 if no disruption)
            3. Confidence score (0-1)
            4. Reasoning explanation
            5. Recommended preventive actions
            6. Monitoring recommendations
            
            Consider:
            - If overall risk < 0.3: predict "none" with low delay
            - If 0.3 <= risk < 0.6: predict most likely type with moderate delay
            - If risk >= 0.6: predict highest risk type with significant delay
            
            Format as JSON with fields:
            - predicted_disruption_type
            - predicted_delay_minutes
            - confidence_score
            - reasoning
            - recommended_actions
            - prediction_horizon_hours: 4
            - risk_factors
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prediction_prompt)
        
        result = await chain.arun(
            synthesis=json.dumps(state.analysis_results.get("synthesis", {})),
            risk_factors=json.dumps(state.risk_factors),
            flight_data=json.dumps(state.flight_data)
        )
        
        try:
            prediction = json.loads(result)
            
            # Ensure required fields
            prediction.setdefault("predicted_disruption_type", "none")
            prediction.setdefault("predicted_delay_minutes", 0)
            prediction.setdefault("confidence_score", 0.5)
            prediction.setdefault("reasoning", "Analysis completed")
            prediction.setdefault("recommended_actions", [])
            prediction.setdefault("prediction_horizon_hours", 4)
            prediction.setdefault("risk_factors", state.risk_factors)
            
            # Add flight ID
            prediction["flight_id"] = state.flight_data.get("id")
            
            state.prediction = prediction
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse prediction JSON, using fallback")
            state.prediction = {
                "flight_id": state.flight_data.get("id"),
                "predicted_disruption_type": "none",
                "predicted_delay_minutes": 0,
                "confidence_score": 0.3,
                "reasoning": "Analysis completed with limited confidence due to parsing issues",
                "recommended_actions": ["Monitor weather conditions", "Check aircraft status"],
                "prediction_horizon_hours": 4,
                "risk_factors": state.risk_factors[:3]  # Top 3 factors
            }
        
        return state
    
    # Tool implementation methods
    def _analyze_weather(self, weather_data: str) -> str:
        """Analyze weather conditions"""
        try:
            data = json.loads(weather_data)
            
            # Simple weather risk assessment
            risk_score = 0.0
            factors = []
            
            # Visibility
            visibility = data.get("visibility", "10000m")
            if "1000m" in visibility or "500m" in visibility:
                risk_score += 0.4
                factors.append("Low visibility")
            
            # Wind
            wind_speed = data.get("wind_speed", "0kt")
            if "30kt" in wind_speed or "40kt" in wind_speed:
                risk_score += 0.3
                factors.append("High winds")
            
            # Precipitation
            precipitation = data.get("precipitation", "none")
            if precipitation in ["heavy_rain", "snow", "ice"]:
                risk_score += 0.3
                factors.append(f"Severe precipitation: {precipitation}")
            
            return json.dumps({
                "weather_risk_score": min(risk_score, 1.0),
                "risk_factors": factors,
                "analysis": "Weather analysis completed"
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "weather_risk_score": 0.2})
    
    def _analyze_historical_data(self, historical_data: str) -> str:
        """Analyze historical disruption patterns"""
        try:
            data = json.loads(historical_data)
            
            if not data:
                return json.dumps({"historical_risk_score": 0.2, "patterns": []})
            
            # Count disruption types
            disruption_counts = {}
            total_flights = len(data)
            
            for record in data:
                disruption_type = record.get("type", "none")
                disruption_counts[disruption_type] = disruption_counts.get(disruption_type, 0) + 1
            
            # Calculate risk based on disruption frequency
            disruption_rate = (total_flights - disruption_counts.get("none", 0)) / max(total_flights, 1)
            
            return json.dumps({
                "historical_risk_score": min(disruption_rate, 1.0),
                "disruption_patterns": disruption_counts,
                "total_flights_analyzed": total_flights
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "historical_risk_score": 0.3})
    
    def _analyze_aircraft_factors(self, aircraft_data: str) -> str:
        """Analyze aircraft-specific risk factors"""
        try:
            data = json.loads(aircraft_data)
            aircraft_type = data.get("aircraft_type", "")
            
            # Simple aircraft risk assessment
            risk_score = 0.1  # Base risk
            factors = []
            
            # Age-based risk (mock logic)
            if "737" in aircraft_type:
                risk_score += 0.1
                factors.append("Boeing 737 series - moderate maintenance requirements")
            elif "A320" in aircraft_type:
                risk_score += 0.05
                factors.append("Airbus A320 series - reliable performance")
            
            return json.dumps({
                "aircraft_risk_score": risk_score,
                "risk_factors": factors,
                "aircraft_type": aircraft_type
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "aircraft_risk_score": 0.1})
    
    def _analyze_route_factors(self, route_data: str) -> str:
        """Analyze route-specific factors"""
        try:
            route = route_data.strip()
            
            # Simple route analysis
            risk_score = 0.2  # Base risk
            factors = []
            
            # High-traffic routes
            high_traffic_routes = ["LHR-JFK", "LGW-CDG", "STN-AMS"]
            if route in high_traffic_routes:
                risk_score += 0.2
                factors.append("High-traffic route with potential congestion")
            
            return json.dumps({
                "route_risk_score": risk_score,
                "risk_factors": factors,
                "route": route
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "route_risk_score": 0.2})
    
    def _analyze_operational_factors(self, operational_data: str) -> str:
        """Analyze operational factors"""
        try:
            # Mock operational analysis
            return json.dumps({
                "operational_risk_score": 0.15,
                "risk_factors": ["Standard operational conditions"],
                "crew_status": "Available",
                "maintenance_status": "Current"
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "operational_risk_score": 0.15})
    
    def _get_current_season(self) -> str:
        """Get current season for analysis"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    async def update_models(self, new_models: Dict[str, Any]):
        """Update ML models used by the agent"""
        # Implementation for updating models
        logger.info("Models updated", models=list(new_models.keys()))