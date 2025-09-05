"""
Custom Tools for Airline Operations

This module provides specialized tools that AI agents can use to interact
with external systems, perform calculations, and execute airline-specific operations.
"""

import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid
import structlog

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class ToolCategory(Enum):
    """Categories of tools available to agents"""
    FLIGHT_OPERATIONS = "flight_operations"
    PASSENGER_SERVICES = "passenger_services"
    COST_MANAGEMENT = "cost_management"
    COMMUNICATION = "communication"
    DATA_ANALYSIS = "data_analysis"
    COMPLIANCE = "compliance"


# Base tool classes

class AirlineOperationTool(BaseTool):
    """Base class for airline operation tools"""
    
    category: ToolCategory
    requires_approval: bool = False
    max_retries: int = 3
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = structlog.get_logger().bind(
            tool_name=self.name,
            category=self.category.value
        )
    
    async def _arun_with_retry(self, *args, **kwargs):
        """Run tool with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return await self._arun(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    self.logger.error("Tool execution failed after retries",
                                    attempt=attempt + 1,
                                    error=str(e))
                    raise
                else:
                    self.logger.warning("Tool execution failed, retrying",
                                      attempt=attempt + 1,
                                      error=str(e))
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff


# Flight Operations Tools

class FlightStatusChecker(AirlineOperationTool):
    name = "flight_status_checker"
    description = "Check real-time flight status including delays, cancellations, and gate information"
    category = ToolCategory.FLIGHT_OPERATIONS
    
    class FlightStatusInput(BaseModel):
        flight_number: str = Field(description="Flight number (e.g., 'BA123')")
        date: str = Field(description="Flight date in YYYY-MM-DD format")
        airport_code: Optional[str] = Field(None, description="Airport code to filter results")
    
    args_schema = FlightStatusInput
    
    async def _arun(self, flight_number: str, date: str, airport_code: Optional[str] = None):
        """Check flight status from airline systems"""
        try:
            # In a real implementation, this would connect to airline APIs
            # For now, we'll simulate the response
            
            self.logger.info("Checking flight status",
                           flight_number=flight_number,
                           date=date,
                           airport_code=airport_code)
            
            # Simulate API delay
            await asyncio.sleep(0.5)
            
            # Mock response based on flight number patterns
            status = "on_time"
            delay_minutes = 0
            
            if "delay" in flight_number.lower():
                status = "delayed"
                delay_minutes = 45
            elif "cancel" in flight_number.lower():
                status = "cancelled"
            
            return {
                "flight_number": flight_number,
                "date": date,
                "status": status,
                "delay_minutes": delay_minutes,
                "departure_gate": "A12",
                "arrival_gate": "B8",
                "aircraft_type": "Boeing 737-800",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to check flight status", error=str(e))
            raise


class AlternativeFlightFinder(AirlineOperationTool):
    name = "alternative_flight_finder"
    description = "Find alternative flights for rebooking passengers"
    category = ToolCategory.FLIGHT_OPERATIONS
    
    class AlternativeFlightInput(BaseModel):
        origin: str = Field(description="Origin airport code")
        destination: str = Field(description="Destination airport code")
        preferred_date: str = Field(description="Preferred travel date in YYYY-MM-DD format")
        passenger_count: int = Field(description="Number of passengers")
        class_of_service: str = Field(default="economy", description="Class of service (economy, premium, business, first)")
        max_alternatives: int = Field(default=10, description="Maximum number of alternatives to return")
    
    args_schema = AlternativeFlightInput
    
    async def _arun(self, origin: str, destination: str, preferred_date: str, 
                   passenger_count: int, class_of_service: str = "economy", 
                   max_alternatives: int = 10):
        """Find alternative flight options"""
        try:
            self.logger.info("Finding alternative flights",
                           origin=origin,
                           destination=destination,
                           preferred_date=preferred_date,
                           passengers=passenger_count)
            
            # Simulate API delay
            await asyncio.sleep(1.0)
            
            # Generate mock alternative flights
            alternatives = []
            base_date = datetime.fromisoformat(preferred_date)
            
            for i in range(min(max_alternatives, 5)):
                flight_date = base_date + timedelta(hours=i * 4)
                alternatives.append({
                    "flight_number": f"BA{100 + i}",
                    "departure_time": flight_date.isoformat(),
                    "arrival_time": (flight_date + timedelta(hours=2)).isoformat(),
                    "available_seats": 50 - (i * 5),
                    "price": 250 + (i * 25),
                    "aircraft_type": "Boeing 737-800",
                    "stops": 0 if i < 3 else 1
                })
            
            return {
                "origin": origin,
                "destination": destination,
                "alternatives": alternatives,
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to find alternative flights", error=str(e))
            raise


# Passenger Services Tools

class PassengerDataRetriever(AirlineOperationTool):
    name = "passenger_data_retriever"
    description = "Retrieve passenger information from airline systems"
    category = ToolCategory.PASSENGER_SERVICES
    
    class PassengerDataInput(BaseModel):
        pnr: Optional[str] = Field(None, description="Passenger Name Record (booking reference)")
        passenger_id: Optional[str] = Field(None, description="Unique passenger ID")
        flight_number: Optional[str] = Field(None, description="Flight number")
        last_name: Optional[str] = Field(None, description="Passenger last name")
    
    args_schema = PassengerDataInput
    
    async def _arun(self, pnr: Optional[str] = None, passenger_id: Optional[str] = None,
                   flight_number: Optional[str] = None, last_name: Optional[str] = None):
        """Retrieve passenger data"""
        try:
            if not any([pnr, passenger_id, flight_number, last_name]):
                raise ValueError("At least one search parameter must be provided")
            
            self.logger.info("Retrieving passenger data",
                           pnr=pnr,
                           passenger_id=passenger_id,
                           flight_number=flight_number)
            
            # Simulate API delay
            await asyncio.sleep(0.7)
            
            # Mock passenger data
            return {
                "passengers": [
                    {
                        "passenger_id": "PAX123456",
                        "pnr": pnr or "ABC123",
                        "first_name": "John",
                        "last_name": last_name or "Doe",
                        "email": "john.doe@email.com",
                        "phone": "+44 20 7946 0958",
                        "frequent_flyer_number": "FF123456789",
                        "tier_status": "Gold",
                        "special_requests": ["WHEELCHAIR", "MEAL_VEGAN"],
                        "booking_date": "2024-01-15",
                        "flights": [
                            {
                                "flight_number": flight_number or "BA123",
                                "date": "2024-02-15",
                                "origin": "LHR",
                                "destination": "CDG",
                                "seat": "12A",
                                "class": "economy"
                            }
                        ]
                    }
                ],
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to retrieve passenger data", error=str(e))
            raise


class RebookingProcessor(AirlineOperationTool):
    name = "rebooking_processor"
    description = "Process passenger rebooking to alternative flights"
    category = ToolCategory.PASSENGER_SERVICES
    requires_approval = True
    
    class RebookingInput(BaseModel):
        passenger_id: str = Field(description="Unique passenger ID")
        original_flight: str = Field(description="Original flight number")
        new_flight: str = Field(description="New flight number")
        new_date: str = Field(description="New flight date")
        seat_preference: Optional[str] = Field(None, description="Seat preference")
        reason: str = Field(description="Reason for rebooking")
    
    args_schema = RebookingInput
    
    async def _arun(self, passenger_id: str, original_flight: str, new_flight: str,
                   new_date: str, seat_preference: Optional[str] = None, reason: str = ""):
        """Process passenger rebooking"""
        try:
            self.logger.info("Processing rebooking",
                           passenger_id=passenger_id,
                           original_flight=original_flight,
                           new_flight=new_flight)
            
            # Simulate processing time
            await asyncio.sleep(1.5)
            
            # Generate rebooking confirmation
            confirmation_code = f"RBK{str(uuid.uuid4())[:8].upper()}"
            
            return {
                "status": "confirmed",
                "confirmation_code": confirmation_code,
                "passenger_id": passenger_id,
                "original_flight": original_flight,
                "new_flight": new_flight,
                "new_date": new_date,
                "assigned_seat": seat_preference or "15C",
                "processing_time": datetime.now().isoformat(),
                "additional_charges": 0.0,
                "refund_amount": 0.0
            }
            
        except Exception as e:
            self.logger.error("Failed to process rebooking", error=str(e))
            raise


# Cost Management Tools

class CostCalculator(AirlineOperationTool):
    name = "cost_calculator"
    description = "Calculate costs for various airline operations"
    category = ToolCategory.COST_MANAGEMENT
    
    class CostCalculationInput(BaseModel):
        operation_type: str = Field(description="Type of operation (rebooking, hotel, meal, transport)")
        parameters: Dict[str, Any] = Field(description="Operation-specific parameters")
    
    args_schema = CostCalculationInput
    
    async def _arun(self, operation_type: str, parameters: Dict[str, Any]):
        """Calculate operation costs"""
        try:
            self.logger.info("Calculating costs",
                           operation_type=operation_type,
                           parameters=parameters)
            
            # Simulate calculation time
            await asyncio.sleep(0.3)
            
            base_costs = {
                "rebooking": 50.0,
                "hotel": 120.0,
                "meal": 25.0,
                "transport": 40.0,
                "compensation": 250.0
            }
            
            base_cost = base_costs.get(operation_type, 0.0)
            multiplier = parameters.get("passenger_count", 1)
            duration = parameters.get("duration_hours", 1)
            
            total_cost = base_cost * multiplier * (duration / 24 if operation_type == "hotel" else 1)
            
            return {
                "operation_type": operation_type,
                "base_cost": base_cost,
                "passenger_count": multiplier,
                "duration_hours": duration,
                "total_cost": total_cost,
                "currency": "GBP",
                "calculated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to calculate costs", error=str(e))
            raise


class HotelBookingTool(AirlineOperationTool):
    name = "hotel_booking_tool"
    description = "Book hotel accommodations for stranded passengers"
    category = ToolCategory.COST_MANAGEMENT
    requires_approval = True
    
    class HotelBookingInput(BaseModel):
        airport_code: str = Field(description="Airport code for hotel location")
        check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
        check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
        room_count: int = Field(description="Number of rooms needed")
        passenger_count: int = Field(description="Total number of passengers")
        room_type: str = Field(default="standard", description="Room type preference")
    
    args_schema = HotelBookingInput
    
    async def _arun(self, airport_code: str, check_in_date: str, check_out_date: str,
                   room_count: int, passenger_count: int, room_type: str = "standard"):
        """Book hotel rooms for passengers"""
        try:
            self.logger.info("Booking hotel accommodation",
                           airport_code=airport_code,
                           room_count=room_count,
                           passengers=passenger_count)
            
            # Simulate booking process
            await asyncio.sleep(2.0)
            
            # Generate booking confirmation
            booking_reference = f"HTL{str(uuid.uuid4())[:8].upper()}"
            
            return {
                "status": "confirmed",
                "booking_reference": booking_reference,
                "hotel_name": f"Airport Hotel {airport_code}",
                "address": f"Terminal 2, {airport_code} Airport",
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "rooms_booked": room_count,
                "room_type": room_type,
                "total_cost": room_count * 120.0,  # Base rate per room
                "currency": "GBP",
                "amenities": ["WiFi", "Breakfast", "Airport Shuttle"],
                "contact_phone": "+44 20 7946 0958",
                "booking_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to book hotel", error=str(e))
            raise


# Communication Tools

class NotificationSender(AirlineOperationTool):
    name = "notification_sender"
    description = "Send notifications to passengers via multiple channels"
    category = ToolCategory.COMMUNICATION
    
    class NotificationInput(BaseModel):
        passenger_ids: List[str] = Field(description="List of passenger IDs")
        message: str = Field(description="Message content")
        channels: List[str] = Field(description="Communication channels (email, sms, push)")
        priority: str = Field(default="normal", description="Message priority (low, normal, high, urgent)")
        template_id: Optional[str] = Field(None, description="Message template ID")
    
    args_schema = NotificationInput
    
    async def _arun(self, passenger_ids: List[str], message: str, 
                   channels: List[str], priority: str = "normal",
                   template_id: Optional[str] = None):
        """Send notifications to passengers"""
        try:
            self.logger.info("Sending notifications",
                           passenger_count=len(passenger_ids),
                           channels=channels,
                           priority=priority)
            
            # Simulate sending delay
            await asyncio.sleep(len(passenger_ids) * 0.1)
            
            # Generate delivery reports
            delivery_reports = []
            for passenger_id in passenger_ids:
                for channel in channels:
                    delivery_reports.append({
                        "passenger_id": passenger_id,
                        "channel": channel,
                        "status": "delivered",
                        "timestamp": datetime.now().isoformat(),
                        "message_id": str(uuid.uuid4())
                    })
            
            return {
                "batch_id": str(uuid.uuid4()),
                "total_sent": len(passenger_ids) * len(channels),
                "successful_deliveries": len(delivery_reports),
                "failed_deliveries": 0,
                "delivery_reports": delivery_reports,
                "sent_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to send notifications", error=str(e))
            raise


# Data Analysis Tools

class DisruptionAnalyzer(AirlineOperationTool):
    name = "disruption_analyzer"
    description = "Analyze disruption patterns and predict impacts"
    category = ToolCategory.DATA_ANALYSIS
    
    class DisruptionAnalysisInput(BaseModel):
        disruption_type: str = Field(description="Type of disruption (weather, technical, atc)")
        airport_code: str = Field(description="Affected airport code")
        start_time: str = Field(description="Disruption start time")
        severity: str = Field(description="Disruption severity (low, medium, high)")
        additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    
    args_schema = DisruptionAnalysisInput
    
    async def _arun(self, disruption_type: str, airport_code: str, start_time: str,
                   severity: str, additional_data: Optional[Dict[str, Any]] = None):
        """Analyze disruption impact"""
        try:
            self.logger.info("Analyzing disruption",
                           type=disruption_type,
                           airport=airport_code,
                           severity=severity)
            
            # Simulate analysis time
            await asyncio.sleep(1.0)
            
            # Generate analysis results
            impact_scores = {
                "low": {"flights": 5, "passengers": 150, "delay_minutes": 30},
                "medium": {"flights": 25, "passengers": 750, "delay_minutes": 90},
                "high": {"flights": 100, "passengers": 3000, "delay_minutes": 240}
            }
            
            impact = impact_scores.get(severity, impact_scores["medium"])
            
            return {
                "disruption_id": str(uuid.uuid4()),
                "type": disruption_type,
                "airport": airport_code,
                "severity": severity,
                "estimated_impact": {
                    "affected_flights": impact["flights"],
                    "affected_passengers": impact["passengers"],
                    "average_delay_minutes": impact["delay_minutes"],
                    "estimated_cost": impact["passengers"] * 150.0
                },
                "recommendations": [
                    "Implement proactive rebooking for high-tier passengers",
                    "Arrange ground transportation for connecting flights",
                    "Set up passenger care stations at affected gates"
                ],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to analyze disruption", error=str(e))
            raise


# Compliance Tools

class ComplianceChecker(AirlineOperationTool):
    name = "compliance_checker"
    description = "Check regulatory compliance for passenger rights and compensation"
    category = ToolCategory.COMPLIANCE
    
    class ComplianceInput(BaseModel):
        regulation: str = Field(description="Regulation to check (EU261, DOT)")
        flight_info: Dict[str, Any] = Field(description="Flight information")
        disruption_details: Dict[str, Any] = Field(description="Disruption details")
    
    args_schema = ComplianceInput
    
    async def _arun(self, regulation: str, flight_info: Dict[str, Any],
                   disruption_details: Dict[str, Any]):
        """Check regulatory compliance"""
        try:
            self.logger.info("Checking compliance",
                           regulation=regulation,
                           flight=flight_info.get("flight_number"))
            
            # Simulate compliance check
            await asyncio.sleep(0.5)
            
            # Mock EU261 compliance check
            delay_minutes = disruption_details.get("delay_minutes", 0)
            flight_distance = flight_info.get("distance_km", 1000)
            
            compensation_required = False
            compensation_amount = 0
            
            if regulation == "EU261" and delay_minutes >= 180:
                compensation_required = True
                if flight_distance <= 1500:
                    compensation_amount = 250
                elif flight_distance <= 3500:
                    compensation_amount = 400
                else:
                    compensation_amount = 600
            
            return {
                "regulation": regulation,
                "compliance_status": "compliant" if not compensation_required else "action_required",
                "compensation_required": compensation_required,
                "compensation_amount": compensation_amount,
                "currency": "EUR",
                "requirements": [
                    "Provide meal vouchers for delays over 2 hours",
                    "Arrange accommodation for overnight delays",
                    "Offer compensation for delays over 3 hours"
                ] if compensation_required else [],
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to check compliance", error=str(e))
            raise


# Tool factory and registry

class ToolRegistry:
    """Registry for managing agent tools"""
    
    def __init__(self):
        self._tools: Dict[str, AirlineOperationTool] = {}
        self._tools_by_category: Dict[ToolCategory, List[AirlineOperationTool]] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        default_tools = [
            FlightStatusChecker(),
            AlternativeFlightFinder(),
            PassengerDataRetriever(),
            RebookingProcessor(),
            CostCalculator(),
            HotelBookingTool(),
            NotificationSender(),
            DisruptionAnalyzer(),
            ComplianceChecker()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: AirlineOperationTool):
        """Register a new tool"""
        self._tools[tool.name] = tool
        
        if tool.category not in self._tools_by_category:
            self._tools_by_category[tool.category] = []
        
        self._tools_by_category[tool.category].append(tool)
    
    def get_tool(self, name: str) -> Optional[AirlineOperationTool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_tools_by_category(self, category: ToolCategory) -> List[AirlineOperationTool]:
        """Get all tools in a category"""
        return self._tools_by_category.get(category, [])
    
    def get_all_tools(self) -> List[AirlineOperationTool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def get_tools_for_agent(self, agent_type: str) -> List[AirlineOperationTool]:
        """Get recommended tools for a specific agent type"""
        tool_mappings = {
            "prediction": [ToolCategory.DATA_ANALYSIS, ToolCategory.FLIGHT_OPERATIONS],
            "passenger": [ToolCategory.PASSENGER_SERVICES, ToolCategory.COMPLIANCE],
            "resource": [ToolCategory.COST_MANAGEMENT, ToolCategory.FLIGHT_OPERATIONS],
            "communication": [ToolCategory.COMMUNICATION],
            "coordinator": [ToolCategory.FLIGHT_OPERATIONS, ToolCategory.DATA_ANALYSIS]
        }
        
        categories = tool_mappings.get(agent_type, [])
        tools = []
        
        for category in categories:
            tools.extend(self.get_tools_by_category(category))
        
        return tools


# Global tool registry instance
tool_registry = ToolRegistry()