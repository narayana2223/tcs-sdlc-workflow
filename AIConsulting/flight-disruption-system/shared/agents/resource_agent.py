"""
Resource Agent for Flight Disruption Management System

This agent specializes in managing and optimizing resources including
hotels, ground transportation, vouchers, crew scheduling, and cost
optimization during flight disruptions.
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


class ResourceAgent(BaseAgent):
    """Agent specialized in resource management and cost optimization"""
    
    def __init__(self, 
                 agent_id: str,
                 llm: ChatOpenAI,
                 shared_memory,
                 performance_monitor,
                 **kwargs):
        
        # Get tools specific to resource management
        tools = tool_registry.get_tools_for_agent("resource")
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.RESOURCE,
            llm=llm,
            shared_memory=shared_memory,
            performance_monitor=performance_monitor,
            tools=tools,
            **kwargs
        )
        
        # Resource-specific configuration
        self.max_hotel_booking_batch = 50
        self.cost_optimization_threshold = 10000  # GBP
        self.vendor_response_timeout = 30  # seconds
        self.budget_alert_threshold = 0.8  # 80% of budget
        
        # Resource cost baselines
        self.baseline_costs = {
            "hotel_per_night": 120.0,
            "meal_voucher": 25.0,
            "transport_per_person": 40.0,
            "lounge_access": 50.0,
            "priority_service": 75.0
        }
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type="resource"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the resource agent"""
        return """You are a Resource Management Agent specialized in:

1. ACCOMMODATION MANAGEMENT
   - Hotel booking optimization for stranded passengers
   - Room allocation based on passenger profiles and needs
   - Cost negotiation and vendor relationship management
   - Quality assurance and passenger satisfaction monitoring

2. GROUND TRANSPORTATION
   - Airport shuttle and taxi coordination
   - Group transportation for large passenger volumes
   - Special needs transportation (wheelchair accessible, medical)
   - Cost optimization across multiple transportation providers

3. MEAL AND VOUCHER SERVICES
   - Meal voucher distribution and restaurant coordination
   - Dietary requirement management and special meal arrangements
   - Lounge access coordination and capacity management
   - Service provider negotiation and cost control

4. COST OPTIMIZATION & BUDGET MANAGEMENT
   - Real-time cost tracking and budget monitoring
   - Vendor negotiation and dynamic pricing optimization
   - Resource allocation efficiency analysis
   - ROI calculation and cost-benefit analysis for all resource decisions

5. CREW AND OPERATIONAL RESOURCES
   - Crew accommodation and positioning optimization
   - Equipment and facility resource allocation
   - Vendor coordination and service level agreement management
   - Emergency resource procurement and deployment

KEY CAPABILITIES:
- Optimize resource allocation for 1000+ passengers simultaneously
- Achieve 15-20% cost savings through intelligent vendor selection
- Maintain 95%+ passenger satisfaction with accommodation services
- Process resource requests within 2-minute response time
- Coordinate with 50+ service providers across multiple airports

DECISION MAKING APPROACH:
1. Assess total resource requirements and constraints
2. Analyze vendor options, pricing, and availability
3. Optimize allocation considering cost, quality, and passenger needs
4. Negotiate terms and ensure service level compliance
5. Monitor execution and adjust resources as needed
6. Track costs and report budget impact in real-time
7. Learn from outcomes to improve future resource allocation

Always balance cost efficiency with service quality and passenger satisfaction.
Prioritize safety, regulatory compliance, and operational efficiency."""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource management tasks"""
        task_type = task.get("type", "")
        
        if task_type == "resource_coordination":
            return await self._coordinate_resources(task)
        elif task_type == "optimize_resources":
            return await self._optimize_resource_allocation(task)
        elif task_type == "book_accommodations":
            return await self._book_accommodations(task)
        elif task_type == "arrange_transportation":
            return await self._arrange_transportation(task)
        elif task_type == "manage_vouchers":
            return await self._manage_vouchers(task)
        elif task_type == "track_costs":
            return await self._track_costs(task)
        elif task_type == "vendor_coordination":
            return await self._coordinate_vendors(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _coordinate_resources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate overall resource allocation for disruption response"""
        context = task.get("context", {})
        response_plan = task.get("response_plan", {})
        
        self.logger.info("Coordinating resource allocation")
        
        try:
            # Analyze resource requirements from response plan
            resource_requirements = self._extract_resource_requirements(response_plan, context)
            
            # Get cost calculations for all required resources
            cost_calculator = tool_registry.get_tool("cost_calculator")
            
            total_costs = {}
            cost_breakdown = []
            
            for resource_type, requirements in resource_requirements.items():
                try:
                    cost_result = await cost_calculator.arun(
                        operation_type=resource_type,
                        parameters=requirements
                    )
                    total_costs[resource_type] = cost_result
                    cost_breakdown.append(cost_result)
                except Exception as e:
                    self.logger.warning("Cost calculation failed",
                                      resource_type=resource_type,
                                      error=str(e))
            
            # Create comprehensive resource coordination plan
            coordination_prompt = f"""
            Create a comprehensive resource coordination plan for flight disruption response:

            RESOURCE REQUIREMENTS:
            {json.dumps(resource_requirements, indent=2)}

            COST ANALYSIS:
            {json.dumps(total_costs, indent=2)}

            RESPONSE PLAN CONTEXT:
            {json.dumps(response_plan, indent=2)}

            Please provide detailed coordination plan including:
            1. Resource allocation strategy by priority and timeline
            2. Vendor selection and negotiation approach
            3. Quality control and service level monitoring
            4. Cost optimization opportunities and trade-offs
            5. Risk mitigation for resource shortages or delays
            6. Coordination timeline and critical path analysis

            Consider:
            - Passenger tier status and special needs
            - Regulatory compliance requirements
            - Budget constraints and cost optimization
            - Service provider capacity and reliability
            - Seasonal demand and pricing variations
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=coordination_prompt)
            ])
            
            coordination_plan = self._parse_coordination_response(response.content)
            
            # Store coordination plan for execution
            await self.shared_memory.store(
                f"resource_coordination_plan_{context.get('incident_id', 'current')}",
                coordination_plan,
                ttl=3600
            )
            
            return {
                "status": "completed",
                "coordination_plan": coordination_plan,
                "resource_requirements": resource_requirements,
                "cost_breakdown": cost_breakdown,
                "estimated_total_cost": sum(c.get("total_cost", 0) for c in cost_breakdown),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Resource coordination failed", error=str(e))
            raise
    
    async def _optimize_resource_allocation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resource allocation for cost and efficiency"""
        context = task.get("context", {})
        alternatives = task.get("alternatives", {})
        
        self.logger.info("Optimizing resource allocation")
        
        try:
            optimization_prompt = f"""
            Optimize resource allocation for maximum efficiency and cost-effectiveness:

            CURRENT CONTEXT:
            {json.dumps(context, indent=2)}

            AVAILABLE ALTERNATIVES:
            {json.dumps(alternatives, indent=2)}

            Perform optimization analysis considering:
            1. Cost minimization while maintaining service quality
            2. Resource utilization efficiency and capacity planning
            3. Vendor performance and reliability scoring
            4. Passenger satisfaction impact assessment
            5. Operational risk and contingency planning
            6. Time sensitivity and execution feasibility

            Provide optimization recommendations including:
            - Optimal resource allocation matrix
            - Cost-benefit analysis for each allocation decision
            - Risk assessment and mitigation strategies
            - Implementation timeline and dependencies
            - Performance metrics and success criteria
            - Alternative scenarios for different constraint conditions
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=optimization_prompt)
            ])
            
            optimization = self._parse_optimization_response(response.content)
            
            # Calculate optimization metrics
            baseline_cost = context.get("baseline_cost", 0)
            optimized_cost = optimization.get("optimized_cost", 0)
            savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
            savings_percentage = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
            
            return {
                "status": "completed",
                "optimization": optimization,
                "cost_savings": savings,
                "savings_percentage": savings_percentage,
                "efficiency_score": optimization.get("efficiency_score", 85),
                "risk_level": optimization.get("risk_level", "medium"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Resource optimization failed", error=str(e))
            raise
    
    async def _book_accommodations(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Book hotel accommodations for stranded passengers"""
        context = task.get("context", {})
        passenger_requirements = task.get("passenger_requirements", {})
        
        self.logger.info("Booking passenger accommodations")
        
        try:
            # Get hotel booking tool
            hotel_booking_tool = tool_registry.get_tool("hotel_booking_tool")
            
            # Extract accommodation requirements
            airport_code = context.get("airport_code", "LHR")
            passenger_count = passenger_requirements.get("total_passengers", 100)
            special_needs_count = passenger_requirements.get("special_needs", 0)
            
            # Calculate room requirements
            room_count = self._calculate_room_requirements(passenger_count, special_needs_count)
            
            # Book accommodations
            booking_result = await hotel_booking_tool.arun(
                airport_code=airport_code,
                check_in_date=datetime.now().strftime("%Y-%m-%d"),
                check_out_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                room_count=room_count["total_rooms"],
                passenger_count=passenger_count,
                room_type="standard"
            )
            
            # Analyze booking result and passenger allocation
            allocation_prompt = f"""
            Create passenger accommodation allocation plan:

            BOOKING RESULT:
            {json.dumps(booking_result, indent=2)}

            PASSENGER REQUIREMENTS:
            {json.dumps(passenger_requirements, indent=2)}

            ROOM BREAKDOWN:
            {json.dumps(room_count, indent=2)}

            Please provide:
            1. Room allocation strategy by passenger priority
            2. Special needs accommodation planning
            3. Check-in coordination and passenger communication plan
            4. Quality assurance and monitoring procedures
            5. Contingency plans for additional capacity needs
            6. Cost tracking and budget management
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=allocation_prompt)
            ])
            
            allocation_plan = self._parse_allocation_response(response.content)
            
            return {
                "status": "completed",
                "booking_result": booking_result,
                "allocation_plan": allocation_plan,
                "rooms_booked": room_count["total_rooms"],
                "passengers_accommodated": passenger_count,
                "total_cost": booking_result.get("total_cost", 0),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Accommodation booking failed", error=str(e))
            raise
    
    async def _arrange_transportation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Arrange ground transportation for passengers"""
        context = task.get("context", {})
        transportation_needs = task.get("transportation_needs", {})
        
        self.logger.info("Arranging ground transportation")
        
        try:
            # Calculate transportation requirements
            transport_analysis = self._analyze_transportation_needs(transportation_needs, context)
            
            transportation_prompt = f"""
            Plan and coordinate ground transportation for disrupted passengers:

            TRANSPORTATION ANALYSIS:
            {json.dumps(transport_analysis, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Plan comprehensive transportation including:
            1. Airport-to-hotel shuttle services with schedules
            2. Special needs transportation (wheelchair accessible)
            3. Group transportation coordination and passenger manifests
            4. Cost optimization across multiple transport providers
            5. Real-time tracking and passenger communication
            6. Contingency transportation for delays or capacity issues

            Provide detailed execution plan with:
            - Transportation schedule and passenger assignments
            - Vendor coordination and service level agreements
            - Cost breakdown and budget tracking
            - Quality control and passenger satisfaction monitoring
            - Emergency backup plans and alternative options
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=transportation_prompt)
            ])
            
            transport_plan = self._parse_transport_response(response.content)
            
            # Calculate costs using cost calculator
            cost_calculator = tool_registry.get_tool("cost_calculator")
            transport_cost = await cost_calculator.arun(
                operation_type="transport",
                parameters={
                    "passenger_count": transport_analysis.get("total_passengers", 0),
                    "distance": transport_analysis.get("average_distance", 25),
                    "special_needs": transport_analysis.get("special_needs_count", 0)
                }
            )
            
            return {
                "status": "completed",
                "transport_plan": transport_plan,
                "transport_analysis": transport_analysis,
                "cost_estimate": transport_cost,
                "passengers_to_transport": transport_analysis.get("total_passengers", 0),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Transportation arrangement failed", error=str(e))
            raise
    
    async def _manage_vouchers(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manage meal vouchers and service provisions"""
        context = task.get("context", {})
        voucher_requirements = task.get("voucher_requirements", {})
        
        self.logger.info("Managing voucher distribution")
        
        try:
            voucher_prompt = f"""
            Plan comprehensive voucher and service provision strategy:

            VOUCHER REQUIREMENTS:
            {json.dumps(voucher_requirements, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Plan voucher distribution including:
            1. Meal voucher allocation by passenger tier and dietary needs
            2. Lounge access coordination and capacity management
            3. Service provider negotiation and partnership management
            4. Distribution logistics and passenger communication
            5. Cost tracking and budget optimization
            6. Quality assurance and passenger feedback monitoring

            Consider:
            - EU261 compliance requirements for care and assistance
            - Passenger dietary restrictions and cultural preferences
            - Airport restaurant capacity and operating hours
            - Cost per passenger optimization
            - Service provider performance monitoring
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=voucher_prompt)
            ])
            
            voucher_plan = self._parse_voucher_response(response.content)
            
            # Calculate total voucher costs
            total_passengers = voucher_requirements.get("passenger_count", 0)
            meal_voucher_cost = total_passengers * self.baseline_costs["meal_voucher"]
            lounge_access_cost = voucher_requirements.get("premium_passengers", 0) * self.baseline_costs["lounge_access"]
            
            return {
                "status": "completed",
                "voucher_plan": voucher_plan,
                "meal_voucher_cost": meal_voucher_cost,
                "lounge_access_cost": lounge_access_cost,
                "total_voucher_cost": meal_voucher_cost + lounge_access_cost,
                "passengers_served": total_passengers,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Voucher management failed", error=str(e))
            raise
    
    async def _track_costs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Track and analyze resource costs"""
        context = task.get("context", {})
        
        self.logger.info("Tracking resource costs")
        
        try:
            # Get cost data from shared memory
            recent_decisions = await self.shared_memory.get_decisions(
                agent_type=self.agent_type,
                since=datetime.now() - timedelta(hours=24)
            )
            
            # Analyze cost patterns and budget utilization
            cost_analysis_prompt = f"""
            Analyze resource costs and budget utilization:

            RECENT DECISIONS:
            {json.dumps([d.to_dict() for d in recent_decisions[:10]], indent=2)}

            CURRENT CONTEXT:
            {json.dumps(context, indent=2)}

            Provide cost analysis including:
            1. Budget utilization by resource category
            2. Cost trends and variance analysis
            3. Cost efficiency metrics and benchmarking
            4. Budget forecast and remaining capacity
            5. Cost optimization recommendations
            6. Risk assessment for budget overruns

            Include:
            - Real-time budget status dashboard data
            - Cost per passenger metrics by service type
            - Vendor performance and cost efficiency scoring
            - Predictive cost modeling for remaining disruption period
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=cost_analysis_prompt)
            ])
            
            cost_analysis = self._parse_cost_analysis_response(response.content)
            
            # Calculate total costs from recent decisions
            total_estimated_costs = sum(d.estimated_cost for d in recent_decisions)
            total_actual_costs = sum(d.actual_cost or d.estimated_cost for d in recent_decisions)
            
            return {
                "status": "completed",
                "cost_analysis": cost_analysis,
                "total_estimated_costs": total_estimated_costs,
                "total_actual_costs": total_actual_costs,
                "cost_accuracy": abs(total_estimated_costs - total_actual_costs) / max(total_estimated_costs, 1),
                "decisions_analyzed": len(recent_decisions),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Cost tracking failed", error=str(e))
            raise
    
    async def _coordinate_vendors(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate with multiple service vendors"""
        context = task.get("context", {})
        vendor_requirements = task.get("vendor_requirements", {})
        
        self.logger.info("Coordinating with service vendors")
        
        try:
            vendor_prompt = f"""
            Coordinate with service vendors for resource provisioning:

            VENDOR REQUIREMENTS:
            {json.dumps(vendor_requirements, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Plan vendor coordination including:
            1. Vendor selection and capacity allocation
            2. Service level agreement monitoring and compliance
            3. Performance tracking and quality assurance
            4. Cost negotiation and contract optimization
            5. Backup vendor activation and contingency planning
            6. Vendor relationship management and feedback

            Provide coordination strategy with:
            - Primary and backup vendor assignments
            - Service delivery timelines and milestones
            - Quality control checkpoints and escalation procedures
            - Cost management and payment processing
            - Performance metrics and vendor scorecards
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=vendor_prompt)
            ])
            
            vendor_coordination = self._parse_vendor_response(response.content)
            
            return {
                "status": "completed",
                "vendor_coordination": vendor_coordination,
                "vendors_engaged": vendor_coordination.get("vendor_count", 0),
                "coordination_timeline": vendor_coordination.get("timeline", "2_hours"),
                "risk_level": vendor_coordination.get("risk_level", "medium"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Vendor coordination failed", error=str(e))
            raise
    
    # Helper methods
    
    def _extract_resource_requirements(self, response_plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract resource requirements from response plan"""
        passenger_count = context.get("affected_passengers", 100)
        duration_hours = context.get("expected_duration_hours", 8)
        
        return {
            "hotel": {
                "passenger_count": passenger_count,
                "duration_hours": duration_hours,
                "special_needs_count": int(passenger_count * 0.15)  # Assume 15% special needs
            },
            "transport": {
                "passenger_count": passenger_count,
                "trip_count": 2,  # Airport to hotel, hotel to airport
                "special_needs_count": int(passenger_count * 0.15)
            },
            "meal": {
                "passenger_count": passenger_count,
                "meal_count": max(2, duration_hours // 4),  # Meal every 4 hours
                "dietary_restrictions": int(passenger_count * 0.2)  # 20% dietary restrictions
            }
        }
    
    def _calculate_room_requirements(self, passenger_count: int, special_needs_count: int) -> Dict[str, int]:
        """Calculate hotel room requirements"""
        # Assume average 1.5 passengers per room, adjust for special needs
        base_rooms = int(passenger_count / 1.5)
        special_rooms = special_needs_count  # 1:1 for special needs
        
        return {
            "total_rooms": base_rooms + special_rooms,
            "standard_rooms": base_rooms,
            "accessible_rooms": special_rooms,
            "family_rooms": int(passenger_count * 0.1)  # 10% families
        }
    
    def _analyze_transportation_needs(self, needs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transportation requirements"""
        return {
            "total_passengers": needs.get("passenger_count", 100),
            "special_needs_count": needs.get("special_needs", 15),
            "average_distance": 25,  # km from airport
            "peak_transport_hours": ["18:00", "08:00"],
            "estimated_trips": needs.get("passenger_count", 100) * 2  # Round trip
        }
    
    # Response parsing methods
    
    def _parse_coordination_response(self, response: str) -> Dict[str, Any]:
        """Parse coordination plan response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "strategy": response,
            "timeline": "2_hours",
            "cost_optimization": [],
            "risk_mitigation": []
        }
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """Parse optimization response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "optimized_cost": 0,
            "efficiency_score": 85,
            "risk_level": "medium",
            "recommendations": []
        }
    
    def _parse_allocation_response(self, response: str) -> Dict[str, Any]:
        """Parse allocation plan response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "allocation_strategy": response,
            "check_in_plan": {},
            "quality_assurance": {}
        }
    
    def _parse_transport_response(self, response: str) -> Dict[str, Any]:
        """Parse transportation plan response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "transport_schedule": [],
            "vendor_assignments": {},
            "backup_plans": []
        }
    
    def _parse_voucher_response(self, response: str) -> Dict[str, Any]:
        """Parse voucher plan response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "distribution_plan": response,
            "provider_assignments": {},
            "quality_monitoring": {}
        }
    
    def _parse_cost_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse cost analysis response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "budget_utilization": 0.6,
            "cost_trends": [],
            "efficiency_metrics": {},
            "recommendations": []
        }
    
    def _parse_vendor_response(self, response: str) -> Dict[str, Any]:
        """Parse vendor coordination response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "vendor_count": 5,
            "timeline": "2_hours",
            "risk_level": "medium",
            "coordination_strategy": response
        }