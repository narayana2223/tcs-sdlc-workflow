"""
Passenger Agent for Flight Disruption Management System

This agent specializes in handling individual passenger rebooking,
managing passenger preferences, processing EU261 compliance,
and coordinating personalized passenger care.
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


class PassengerAgent(BaseAgent):
    """Agent specialized in passenger management and rebooking"""
    
    def __init__(self, 
                 agent_id: str,
                 llm: ChatOpenAI,
                 shared_memory,
                 performance_monitor,
                 **kwargs):
        
        # Get tools specific to passenger management
        tools = tool_registry.get_tools_for_agent("passenger")
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PASSENGER,
            llm=llm,
            shared_memory=shared_memory,
            performance_monitor=performance_monitor,
            tools=tools,
            **kwargs
        )
        
        # Passenger-specific configuration
        self.max_rebooking_attempts = 3
        self.priority_processing_time_minutes = 15
        self.batch_processing_size = 100
        
        # Passenger tier priorities
        self.tier_priorities = {
            "platinum": 1,
            "gold": 2, 
            "silver": 3,
            "bronze": 4,
            "regular": 5
        }
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type="passenger"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the passenger agent"""
        return """You are a Passenger Management Agent specialized in:

1. PASSENGER REBOOKING & ACCOMMODATION
   - Intelligent rebooking optimization based on passenger preferences
   - Alternative flight analysis and seat assignment optimization
   - Multi-passenger group handling and family considerations
   - Connection protection and through-check services

2. PASSENGER PRIORITIZATION
   - Tier status and frequent flyer program management
   - Special needs passenger identification and care
   - Time-sensitive travel requirements (business, medical, etc.)
   - Group booking and VIP passenger handling

3. EU261 COMPLIANCE & COMPENSATION
   - Automatic compensation calculation and processing
   - Passenger rights assessment and communication
   - Care and assistance provision (meals, accommodation, transport)
   - Regulatory requirement compliance and documentation

4. PERSONALIZED CUSTOMER SERVICE
   - Individual passenger preference learning and application
   - Historical behavior analysis and service customization
   - Proactive communication and expectation management
   - Complaint resolution and service recovery

5. OPERATIONAL COORDINATION
   - PSS (Passenger Service System) integration and data management
   - Real-time inventory management and seat optimization
   - Ground services coordination and special service requests
   - Revenue management and fare difference handling

KEY CAPABILITIES:
- Process 1000+ passenger rebookings per hour during disruptions
- Maintain 95%+ passenger satisfaction during irregular operations
- Ensure 100% EU261 regulatory compliance
- Optimize rebooking decisions considering cost and passenger preference
- Coordinate with ground services and airport operations

DECISION MAKING APPROACH:
1. Assess passenger priority level and specific needs
2. Analyze available alternatives and constraints
3. Calculate costs (monetary, operational, customer satisfaction)
4. Apply regulatory requirements and compliance checks
5. Optimize for best passenger experience within budget
6. Coordinate execution with relevant systems and teams
7. Monitor outcomes and adjust strategies based on feedback

Always prioritize passenger safety, regulatory compliance, and service quality.
Balance operational efficiency with personalized customer care."""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process passenger-related tasks"""
        task_type = task.get("type", "")
        
        if task_type == "passenger_analysis":
            return await self._analyze_passengers(task)
        elif task_type == "find_alternatives":
            return await self._find_rebooking_alternatives(task)
        elif task_type == "optimize_assignments":
            return await self._optimize_passenger_assignments(task)
        elif task_type == "process_rebookings":
            return await self._process_rebookings(task)
        elif task_type == "handle_compensation":
            return await self._handle_compensation(task)
        elif task_type == "coordinate_services":
            return await self._coordinate_passenger_services(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _analyze_passengers(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze passengers affected by disruption"""
        context = task.get("context", {})
        
        self.logger.info("Analyzing affected passengers")
        
        try:
            # Get passenger data using retrieval tool
            passenger_retriever = tool_registry.get_tool("passenger_data_retriever")
            
            # Retrieve passengers based on disrupted flights
            disrupted_flights = context.get("disrupted_flights", [])
            all_passengers = []
            
            for flight in disrupted_flights[:10]:  # Limit to prevent overload
                try:
                    passenger_data = await passenger_retriever.arun(
                        flight_number=flight.get("flight_number", "")
                    )
                    if passenger_data.get("passengers"):
                        all_passengers.extend(passenger_data["passengers"])
                except Exception as e:
                    self.logger.warning("Failed to retrieve passenger data",
                                      flight=flight, error=str(e))
            
            # Analyze passenger profiles and needs
            analysis_prompt = f"""
            Analyze the affected passengers and categorize them for optimal rebooking:

            AFFECTED PASSENGERS:
            {json.dumps(all_passengers, indent=2)}

            DISRUPTION CONTEXT:
            {json.dumps(context, indent=2)}

            Please provide detailed analysis including:
            1. Passenger segmentation by priority tier and special needs
            2. Travel pattern analysis (business, leisure, connecting flights)
            3. Special service requirements (wheelchair, unaccompanied minors, pets)
            4. Time sensitivity analysis (same-day travel requirements)
            5. Group and family travel identification
            6. Revenue impact assessment by passenger segment

            Include specific recommendations for:
            - Priority processing order
            - Special handling requirements  
            - Service recovery strategies
            - Resource allocation needs
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=analysis_prompt)
            ])
            
            analysis = self._parse_passenger_analysis(response.content)
            
            # Enhance with priority scoring
            analysis["passengers"] = self._calculate_passenger_priorities(all_passengers)
            
            # Store analysis for coordination with other agents
            await self.shared_memory.store(
                f"passenger_analysis_{context.get('incident_id', 'current')}",
                analysis,
                ttl=3600
            )
            
            return {
                "status": "completed",
                "analysis": analysis,
                "total_passengers": len(all_passengers),
                "priority_passengers": len([p for p in all_passengers if p.get("tier_status") in ["Gold", "Platinum"]]),
                "special_needs_passengers": len([p for p in all_passengers if p.get("special_requests")]),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Passenger analysis failed", error=str(e))
            raise
    
    async def _find_rebooking_alternatives(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Find rebooking alternatives for affected passengers"""
        context = task.get("context", {})
        passenger_analysis = task.get("passenger_analysis", {})
        
        self.logger.info("Finding rebooking alternatives")
        
        try:
            # Get alternative flight finder tool
            flight_finder = tool_registry.get_tool("alternative_flight_finder")
            
            # Process each affected route
            all_alternatives = {}
            affected_routes = context.get("affected_routes", [])
            
            if not affected_routes and passenger_analysis:
                # Extract routes from passenger analysis
                affected_routes = self._extract_routes_from_analysis(passenger_analysis)
            
            for route in affected_routes[:5]:  # Limit to prevent API overload
                try:
                    alternatives = await flight_finder.arun(
                        origin=route.get("origin", "LHR"),
                        destination=route.get("destination", "CDG"),
                        preferred_date=route.get("date", datetime.now().strftime("%Y-%m-%d")),
                        passenger_count=route.get("passenger_count", 50),
                        class_of_service="economy"
                    )
                    
                    all_alternatives[f"{route['origin']}-{route['destination']}"] = alternatives
                    
                except Exception as e:
                    self.logger.warning("Failed to find alternatives for route",
                                      route=route, error=str(e))
            
            # Analyze alternatives and make recommendations
            alternatives_prompt = f"""
            Analyze flight alternatives and provide rebooking recommendations:

            AVAILABLE ALTERNATIVES:
            {json.dumps(all_alternatives, indent=2)}

            PASSENGER ANALYSIS:
            {json.dumps(passenger_analysis, indent=2)}

            Please provide:
            1. Optimal rebooking strategies by passenger segment
            2. Alternative flight ranking with pros/cons
            3. Capacity analysis and seat allocation recommendations
            4. Cost impact assessment for each alternative
            5. Timeline recommendations for rebooking execution
            6. Risk mitigation for each rebooking option

            Consider:
            - Passenger tier status and preferences
            - Connection protection requirements
            - Group and family travel needs
            - Special service requirements
            - Revenue optimization opportunities
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=alternatives_prompt)
            ])
            
            recommendations = self._parse_alternatives_response(response.content)
            
            return {
                "status": "completed",
                "alternatives": all_alternatives,
                "recommendations": recommendations,
                "route_count": len(affected_routes),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Alternative finding failed", error=str(e))
            raise
    
    async def _optimize_passenger_assignments(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize passenger assignments to alternative flights"""
        context = task.get("context", {})
        alternatives = task.get("alternatives", {})
        
        self.logger.info("Optimizing passenger assignments")
        
        try:
            optimization_prompt = f"""
            Optimize passenger assignments to alternative flights:

            ALTERNATIVES DATA:
            {json.dumps(alternatives, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Create an optimal assignment plan that:
            1. Maximizes passenger satisfaction scores
            2. Minimizes total rebooking costs
            3. Respects passenger preferences and tier status
            4. Maintains regulatory compliance (EU261)
            5. Optimizes aircraft capacity utilization
            6. Minimizes connection risks

            Provide detailed assignment matrix including:
            - Passenger-to-flight assignments with rationale
            - Cost-benefit analysis for each assignment
            - Risk assessment and mitigation plans
            - Timeline for execution
            - Required approvals and coordination points
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=optimization_prompt)
            ])
            
            optimization = self._parse_optimization_response(response.content)
            
            # Store optimization plan for execution
            await self.shared_memory.store(
                "passenger_optimization_plan",
                optimization,
                ttl=1800  # 30 minutes
            )
            
            return {
                "status": "completed",
                "optimization": optimization,
                "estimated_satisfaction_score": optimization.get("satisfaction_score", 85),
                "estimated_cost": optimization.get("total_cost", 0),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Passenger assignment optimization failed", error=str(e))
            raise
    
    async def _process_rebookings(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process actual passenger rebookings"""
        context = task.get("context", {})
        optimization = task.get("optimization", {})
        
        self.logger.info("Processing passenger rebookings")
        
        try:
            # Get rebooking processor tool
            rebooking_processor = tool_registry.get_tool("rebooking_processor")
            
            # Process rebookings from optimization plan
            assignment_plan = optimization.get("assignment_plan", [])
            rebooking_results = []
            
            # Process in batches to avoid overloading systems
            batch_size = min(self.batch_processing_size, len(assignment_plan))
            
            for i in range(0, len(assignment_plan), batch_size):
                batch = assignment_plan[i:i + batch_size]
                
                for assignment in batch:
                    try:
                        result = await rebooking_processor.arun(
                            passenger_id=assignment.get("passenger_id", ""),
                            original_flight=assignment.get("original_flight", ""),
                            new_flight=assignment.get("new_flight", ""),
                            new_date=assignment.get("new_date", ""),
                            seat_preference=assignment.get("seat_preference"),
                            reason="Operational disruption - proactive rebooking"
                        )
                        
                        rebooking_results.append(result)
                        
                    except Exception as e:
                        self.logger.error("Individual rebooking failed",
                                        passenger_id=assignment.get("passenger_id"),
                                        error=str(e))
                        
                        rebooking_results.append({
                            "status": "failed",
                            "passenger_id": assignment.get("passenger_id"),
                            "error": str(e)
                        })
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            # Analyze rebooking results
            successful_rebookings = [r for r in rebooking_results if r.get("status") == "confirmed"]
            failed_rebookings = [r for r in rebooking_results if r.get("status") == "failed"]
            
            # Generate summary and next actions
            summary_prompt = f"""
            Analyze rebooking execution results and provide summary:

            SUCCESSFUL REBOOKINGS: {len(successful_rebookings)}
            FAILED REBOOKINGS: {len(failed_rebookings)}

            RESULTS DETAILS:
            {json.dumps(rebooking_results[:10], indent=2)}  # Show first 10 for analysis

            Please provide:
            1. Execution success analysis and key metrics
            2. Failed rebooking analysis and reasons
            3. Passenger impact assessment
            4. Required follow-up actions and communications
            5. Service recovery recommendations for failed cases
            6. Lessons learned for future optimization
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=summary_prompt)
            ])
            
            execution_summary = self._parse_execution_summary(response.content)
            
            return {
                "status": "completed",
                "rebooking_results": rebooking_results,
                "execution_summary": execution_summary,
                "success_rate": len(successful_rebookings) / len(rebooking_results) if rebooking_results else 0,
                "passengers_processed": len(rebooking_results),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Rebooking processing failed", error=str(e))
            raise
    
    async def _handle_compensation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle EU261 compensation processing"""
        context = task.get("context", {})
        passengers = task.get("passengers", [])
        
        self.logger.info("Processing compensation claims")
        
        try:
            # Get compliance checker tool
            compliance_checker = tool_registry.get_tool("compliance_checker")
            
            compensation_cases = []
            
            # Check each passenger for compensation eligibility
            for passenger in passengers[:50]:  # Limit processing
                try:
                    # Extract flight information for compliance check
                    flight_info = {
                        "flight_number": passenger.get("flight_number", ""),
                        "distance_km": passenger.get("route_distance", 1500),
                        "origin": passenger.get("origin", "LHR"),
                        "destination": passenger.get("destination", "CDG")
                    }
                    
                    disruption_details = {
                        "delay_minutes": context.get("delay_minutes", 0),
                        "cancellation": context.get("cancellation", False),
                        "reason": context.get("disruption_reason", "operational")
                    }
                    
                    compliance_result = await compliance_checker.arun(
                        regulation="EU261",
                        flight_info=flight_info,
                        disruption_details=disruption_details
                    )
                    
                    if compliance_result.get("compensation_required"):
                        compensation_cases.append({
                            "passenger_id": passenger.get("passenger_id"),
                            "compensation_amount": compliance_result.get("compensation_amount"),
                            "currency": compliance_result.get("currency"),
                            "eligibility": compliance_result
                        })
                        
                except Exception as e:
                    self.logger.warning("Compensation check failed for passenger",
                                      passenger_id=passenger.get("passenger_id"),
                                      error=str(e))
            
            # Generate compensation processing plan
            total_compensation = sum(case.get("compensation_amount", 0) for case in compensation_cases)
            
            return {
                "status": "completed",
                "compensation_cases": compensation_cases,
                "total_eligible_passengers": len(compensation_cases),
                "total_compensation_amount": total_compensation,
                "estimated_processing_time": len(compensation_cases) * 2,  # 2 minutes per case
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Compensation processing failed", error=str(e))
            raise
    
    async def _coordinate_passenger_services(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate additional passenger services"""
        context = task.get("context", {})
        
        self.logger.info("Coordinating passenger services")
        
        try:
            # This would coordinate with ground services, catering, etc.
            # For now, we'll provide a coordinated service plan
            
            coordination_prompt = f"""
            Coordinate comprehensive passenger services for disruption response:

            CONTEXT:
            {json.dumps(context, indent=2)}

            Plan and coordinate:
            1. Ground service requirements (check-in, baggage, gates)
            2. Catering and meal service arrangements
            3. Special assistance coordination (wheelchair, medical, etc.)
            4. Lounge access and passenger comfort measures
            5. Transportation arrangements (airport shuttles, etc.)
            6. Communication and information management

            Provide detailed coordination plan with:
            - Service requirements by passenger category
            - Resource allocation and staffing needs
            - Timeline and execution sequence
            - Quality control and monitoring points
            - Escalation procedures for issues
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=coordination_prompt)
            ])
            
            coordination_plan = self._parse_coordination_response(response.content)
            
            return {
                "status": "completed",
                "coordination_plan": coordination_plan,
                "service_categories": coordination_plan.get("categories", []),
                "estimated_setup_time": coordination_plan.get("setup_time", 60),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Service coordination failed", error=str(e))
            raise
    
    # Helper methods
    
    def _calculate_passenger_priorities(self, passengers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate priority scores for passengers"""
        for passenger in passengers:
            score = 100  # Base score
            
            # Tier status bonus
            tier = passenger.get("tier_status", "regular").lower()
            tier_bonus = {
                "platinum": 50,
                "gold": 30,
                "silver": 15,
                "bronze": 5,
                "regular": 0
            }.get(tier, 0)
            
            score += tier_bonus
            
            # Special needs penalty (higher priority)
            if passenger.get("special_requests"):
                score -= 20
            
            # Connection penalty (higher priority)
            if passenger.get("connection_flight"):
                score -= 15
            
            passenger["priority_score"] = score
            passenger["priority_category"] = self._get_priority_category(score)
        
        # Sort by priority score (lower score = higher priority)
        return sorted(passengers, key=lambda x: x.get("priority_score", 100))
    
    def _get_priority_category(self, score: int) -> str:
        """Get priority category based on score"""
        if score <= 80:
            return "critical"
        elif score <= 100:
            return "high"
        elif score <= 130:
            return "medium"
        else:
            return "low"
    
    def _extract_routes_from_analysis(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract affected routes from passenger analysis"""
        # Mock route extraction - in real implementation would parse analysis
        return [
            {"origin": "LHR", "destination": "CDG", "date": datetime.now().strftime("%Y-%m-%d"), "passenger_count": 150},
            {"origin": "LHR", "destination": "FRA", "date": datetime.now().strftime("%Y-%m-%d"), "passenger_count": 200}
        ]
    
    # Response parsing methods
    
    def _parse_passenger_analysis(self, response: str) -> Dict[str, Any]:
        """Parse passenger analysis response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "segments": [],
            "special_needs_count": 0,
            "priority_processing": [],
            "summary": response
        }
    
    def _parse_alternatives_response(self, response: str) -> Dict[str, Any]:
        """Parse alternatives analysis response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "strategies": [],
            "rankings": [],
            "cost_analysis": {},
            "summary": response
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
            "assignment_plan": [],
            "satisfaction_score": 85,
            "total_cost": 0,
            "summary": response
        }
    
    def _parse_execution_summary(self, response: str) -> Dict[str, Any]:
        """Parse execution summary response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "success_analysis": {},
            "failure_analysis": {},
            "next_actions": [],
            "summary": response
        }
    
    def _parse_coordination_response(self, response: str) -> Dict[str, Any]:
        """Parse service coordination response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "categories": [],
            "setup_time": 60,
            "resource_requirements": {},
            "summary": response
        }