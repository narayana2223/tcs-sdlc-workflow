"""
Communication Agent for Flight Disruption Management System

This agent specializes in managing multi-channel passenger communications,
personalized notifications, proactive updates, and maintaining consistent
messaging across all communication channels during disruptions.
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


class CommunicationAgent(BaseAgent):
    """Agent specialized in passenger communication and notifications"""
    
    def __init__(self, 
                 agent_id: str,
                 llm: ChatOpenAI,
                 shared_memory,
                 performance_monitor,
                 **kwargs):
        
        # Get tools specific to communication
        tools = tool_registry.get_tools_for_agent("communication")
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.COMMUNICATION,
            llm=llm,
            shared_memory=shared_memory,
            performance_monitor=performance_monitor,
            tools=tools,
            **kwargs
        )
        
        # Communication-specific configuration
        self.max_batch_size = 500  # Messages per batch
        self.message_priorities = {
            "emergency": 1,
            "urgent": 2,
            "important": 3,
            "informational": 4
        }
        
        # Channel preferences by passenger tier
        self.channel_preferences = {
            "platinum": ["sms", "email", "push"],
            "gold": ["sms", "email", "push"],
            "silver": ["email", "sms"],
            "bronze": ["email"],
            "regular": ["email"]
        }
        
        # Message templates for different scenarios
        self.message_templates = {
            "delay_notification": "Your flight {flight_number} is delayed by {delay_minutes} minutes. New departure time: {new_departure}.",
            "cancellation": "Unfortunately, flight {flight_number} has been cancelled. We are rebooking you automatically.",
            "rebooking_confirmation": "Good news! You've been rebooked on flight {new_flight} departing at {new_time}.",
            "compensation_eligible": "You may be eligible for compensation. We'll process your claim automatically.",
            "hotel_booking": "We've arranged accommodation at {hotel_name}. Confirmation: {booking_ref}",
            "transport_arranged": "Transport to your hotel has been arranged. Please proceed to {pickup_location}."
        }
        
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type="communication"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the communication agent"""
        return """You are a Communication Agent specialized in:

1. MULTI-CHANNEL COMMUNICATION MANAGEMENT
   - SMS, email, push notifications, and WhatsApp integration
   - Channel optimization based on passenger preferences and urgency
   - Real-time delivery tracking and failure recovery
   - Message personalization and localization (multiple languages)

2. PROACTIVE PASSENGER COMMUNICATION
   - Predictive notifications before disruptions occur
   - Automated updates on rebooking, compensation, and services
   - Personalized messaging based on passenger profile and history
   - Expectation management and service recovery communication

3. CRISIS COMMUNICATION & MESSAGING
   - Mass communication during large-scale disruptions
   - Consistent messaging across all channels and touchpoints
   - Regulatory compliance communication (EU261, passenger rights)
   - Media management and brand reputation protection

4. PERSONALIZATION & CUSTOMER EXPERIENCE
   - Individual passenger preference learning and application
   - Dynamic content generation based on passenger context
   - Sentiment analysis and communication tone optimization
   - Cultural sensitivity and language localization

5. COMMUNICATION ANALYTICS & OPTIMIZATION
   - Delivery rate monitoring and channel performance analysis
   - Open/read rate tracking and engagement optimization
   - A/B testing for message effectiveness
   - Customer feedback integration and response management

KEY CAPABILITIES:
- Send 10,000+ personalized messages per minute during peak disruptions
- Achieve 98%+ message delivery rates across all channels
- Maintain consistent brand voice while personalizing content
- Process customer responses and route to appropriate handlers
- Coordinate with ground staff and airport information systems

DECISION MAKING APPROACH:
1. Analyze passenger profiles and communication preferences
2. Assess message urgency and select optimal delivery channels
3. Personalize content based on passenger context and needs
4. Coordinate timing with other operational activities
5. Monitor delivery and engagement metrics
6. Adjust messaging strategy based on passenger feedback
7. Ensure regulatory compliance and brand consistency

Always prioritize clear, empathetic, and actionable communication.
Balance transparency with reassurance, and provide specific next steps."""
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process communication-related tasks"""
        task_type = task.get("type", "")
        
        if task_type == "send_notifications":
            return await self._send_passenger_notifications(task)
        elif task_type == "personalize_messages":
            return await self._personalize_messages(task)
        elif task_type == "coordinate_communications":
            return await self._coordinate_communications(task)
        elif task_type == "emergency_broadcast":
            return await self._emergency_broadcast(task)
        elif task_type == "track_responses":
            return await self._track_communication_responses(task)
        elif task_type == "manage_feedback":
            return await self._manage_customer_feedback(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _send_passenger_notifications(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send notifications to affected passengers"""
        context = task.get("context", {})
        rebooking_results = task.get("rebooking_results", {})
        notification_type = task.get("notification_type", "disruption_update")
        
        self.logger.info("Sending passenger notifications", 
                        type=notification_type)
        
        try:
            # Get notification sender tool
            notification_sender = tool_registry.get_tool("notification_sender")
            
            # Extract passenger information and create personalized messages
            passengers = self._extract_passenger_info(rebooking_results, context)
            
            # Generate personalized messages
            personalized_messages = await self._generate_personalized_messages(
                passengers, notification_type, context
            )
            
            # Group passengers by preferred communication channels
            channel_groups = self._group_by_channels(passengers)
            
            # Send notifications in batches
            all_delivery_reports = []
            
            for channel, passenger_group in channel_groups.items():
                if not passenger_group:
                    continue
                
                # Process in batches to avoid overwhelming the system
                for i in range(0, len(passenger_group), self.max_batch_size):
                    batch = passenger_group[i:i + self.max_batch_size]
                    passenger_ids = [p["passenger_id"] for p in batch]
                    
                    # Get personalized messages for this batch
                    batch_messages = [personalized_messages.get(pid, "Update on your flight.") 
                                    for pid in passenger_ids]
                    
                    try:
                        delivery_result = await notification_sender.arun(
                            passenger_ids=passenger_ids,
                            message=batch_messages[0] if len(set(batch_messages)) == 1 else "Personalized flight update",
                            channels=[channel],
                            priority=self._get_message_priority(notification_type),
                            template_id=f"{notification_type}_template"
                        )
                        
                        all_delivery_reports.extend(delivery_result.get("delivery_reports", []))
                        
                    except Exception as e:
                        self.logger.error("Batch notification failed",
                                        channel=channel,
                                        batch_size=len(batch),
                                        error=str(e))
                
                # Small delay between channel batches
                await asyncio.sleep(0.2)
            
            # Analyze delivery results
            delivery_analysis = self._analyze_delivery_results(all_delivery_reports)
            
            # Generate communication summary
            summary_prompt = f"""
            Analyze passenger notification delivery and provide summary:

            NOTIFICATION TYPE: {notification_type}
            TOTAL PASSENGERS: {len(passengers)}
            DELIVERY REPORTS: {len(all_delivery_reports)}

            DELIVERY ANALYSIS:
            {json.dumps(delivery_analysis, indent=2)}

            PASSENGER CONTEXT:
            {json.dumps(context, indent=2)}

            Please provide:
            1. Communication effectiveness assessment
            2. Channel performance analysis
            3. Passenger response expectations and timeline
            4. Follow-up communication recommendations
            5. Service recovery opportunities
            6. Lessons learned for future communications
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=summary_prompt)
            ])
            
            communication_summary = self._parse_communication_summary(response.content)
            
            return {
                "status": "completed",
                "delivery_reports": all_delivery_reports,
                "delivery_analysis": delivery_analysis,
                "communication_summary": communication_summary,
                "passengers_notified": len(passengers),
                "channels_used": list(channel_groups.keys()),
                "delivery_rate": delivery_analysis.get("overall_delivery_rate", 0),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Passenger notification failed", error=str(e))
            raise
    
    async def _personalize_messages(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized messages for different passenger segments"""
        context = task.get("context", {})
        passenger_segments = task.get("passenger_segments", {})
        message_type = task.get("message_type", "general_update")
        
        self.logger.info("Personalizing messages", 
                        segments=len(passenger_segments),
                        type=message_type)
        
        try:
            personalization_prompt = f"""
            Create personalized message templates for different passenger segments:

            MESSAGE TYPE: {message_type}
            PASSENGER SEGMENTS:
            {json.dumps(passenger_segments, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Create personalized messages considering:
            1. Passenger tier status and loyalty program benefits
            2. Travel purpose (business vs leisure) and urgency
            3. Special needs and service requirements
            4. Historical interaction patterns and preferences
            5. Cultural sensitivity and language preferences
            6. Compensation eligibility and service recovery

            Provide messages that are:
            - Clear and actionable with specific next steps
            - Empathetic and acknowledging inconvenience
            - Consistent with brand voice and regulatory requirements
            - Tailored to individual passenger circumstances
            - Optimized for the communication channel

            Include template variations for:
            - High-value frequent flyers
            - Business travelers with tight schedules
            - Families with children
            - Passengers with special needs
            - International passengers
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=personalization_prompt)
            ])
            
            personalized_templates = self._parse_personalization_response(response.content)
            
            return {
                "status": "completed",
                "personalized_templates": personalized_templates,
                "segments_processed": len(passenger_segments),
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Message personalization failed", error=str(e))
            raise
    
    async def _coordinate_communications(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate communications across multiple channels and teams"""
        context = task.get("context", {})
        communication_plan = task.get("communication_plan", {})
        
        self.logger.info("Coordinating multi-channel communications")
        
        try:
            coordination_prompt = f"""
            Coordinate comprehensive communication strategy across all channels:

            COMMUNICATION PLAN:
            {json.dumps(communication_plan, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Plan coordination including:
            1. Multi-channel message sequencing and timing
            2. Consistent messaging across all touchpoints
            3. Ground staff and airport coordination
            4. Social media and public relations alignment
            5. Customer service team briefing and script updates
            6. Regulatory communication requirements

            Provide coordination strategy with:
            - Communication timeline and critical milestones
            - Channel-specific messaging adaptations
            - Staff briefing materials and talking points
            - Escalation procedures for communication issues
            - Brand consistency guidelines and approval processes
            - Performance monitoring and adjustment protocols
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=coordination_prompt)
            ])
            
            coordination_strategy = self._parse_coordination_response(response.content)
            
            # Store coordination plan for other teams
            await self.shared_memory.store(
                "communication_coordination_plan",
                coordination_strategy,
                ttl=3600
            )
            
            return {
                "status": "completed",
                "coordination_strategy": coordination_strategy,
                "channels_coordinated": coordination_strategy.get("channel_count", 0),
                "timeline_duration": coordination_strategy.get("timeline", "2_hours"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Communication coordination failed", error=str(e))
            raise
    
    async def _emergency_broadcast(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send emergency broadcast messages"""
        context = task.get("context", {})
        emergency_details = task.get("emergency_details", {})
        
        self.logger.info("Sending emergency broadcast",
                        severity=emergency_details.get("severity", "medium"))
        
        try:
            # Get all affected passengers from context
            affected_passengers = context.get("affected_passengers", [])
            
            emergency_prompt = f"""
            Create emergency broadcast message for immediate distribution:

            EMERGENCY DETAILS:
            {json.dumps(emergency_details, indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            AFFECTED PASSENGERS: {len(affected_passengers)}

            Create emergency broadcast that:
            1. Clearly communicates the situation without causing panic
            2. Provides specific actions passengers should take
            3. Includes contact information for immediate assistance
            4. Addresses safety concerns and passenger welfare
            5. Maintains regulatory compliance and brand reputation
            6. Provides estimated timeline for resolution

            Message should be:
            - Concise but comprehensive
            - Calm and reassuring tone
            - Specific and actionable
            - Consistent across all channels
            - Legally compliant and accurate
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=emergency_prompt)
            ])
            
            emergency_message = self._parse_emergency_response(response.content)
            
            # Send emergency broadcast using notification sender
            notification_sender = tool_registry.get_tool("notification_sender")
            
            # Send to all available channels for maximum reach
            all_channels = ["sms", "email", "push"]
            passenger_ids = [p.get("passenger_id", "") for p in affected_passengers[:1000]]  # Limit for system protection
            
            broadcast_result = await notification_sender.arun(
                passenger_ids=passenger_ids,
                message=emergency_message.get("broadcast_text", "Emergency update regarding your flight."),
                channels=all_channels,
                priority="urgent"
            )
            
            return {
                "status": "completed",
                "emergency_message": emergency_message,
                "broadcast_result": broadcast_result,
                "passengers_notified": len(passenger_ids),
                "channels_used": all_channels,
                "severity": emergency_details.get("severity", "medium"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Emergency broadcast failed", error=str(e))
            raise
    
    async def _track_communication_responses(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Track passenger responses to communications"""
        context = task.get("context", {})
        
        self.logger.info("Tracking communication responses")
        
        try:
            # Get recent communication data from shared memory
            recent_communications = await self.shared_memory.get_context_history(
                since=datetime.now() - timedelta(hours=6)
            )
            
            response_tracking_prompt = f"""
            Analyze passenger communication responses and engagement:

            RECENT COMMUNICATIONS:
            {json.dumps(recent_communications[:10], indent=2)}

            CONTEXT:
            {json.dumps(context, indent=2)}

            Analyze and provide:
            1. Response rates by communication channel
            2. Sentiment analysis of passenger feedback
            3. Common questions and concerns raised
            4. Effectiveness of different message types
            5. Channel performance and optimization opportunities
            6. Passenger satisfaction indicators

            Provide actionable insights for:
            - Communication strategy optimization
            - Channel preference adjustments
            - Message content improvements
            - Response handling procedures
            - Service recovery opportunities
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=response_tracking_prompt)
            ])
            
            response_analysis = self._parse_response_analysis(response.content)
            
            return {
                "status": "completed",
                "response_analysis": response_analysis,
                "communications_analyzed": len(recent_communications),
                "analysis_period": "6_hours",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Response tracking failed", error=str(e))
            raise
    
    async def _manage_customer_feedback(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manage and respond to customer feedback"""
        context = task.get("context", {})
        feedback_data = task.get("feedback_data", [])
        
        self.logger.info("Managing customer feedback",
                        feedback_count=len(feedback_data))
        
        try:
            feedback_prompt = f"""
            Analyze customer feedback and create response strategy:

            CUSTOMER FEEDBACK:
            {json.dumps(feedback_data[:20], indent=2)}  # Limit for analysis

            CONTEXT:
            {json.dumps(context, indent=2)}

            Analyze feedback and provide:
            1. Sentiment distribution and key themes
            2. Priority issues requiring immediate attention
            3. Service recovery opportunities
            4. Response templates for common concerns
            5. Escalation criteria for serious complaints
            6. Process improvements based on feedback patterns

            Create response strategy including:
            - Personalized response templates
            - Priority handling procedures
            - Service recovery offers
            - Follow-up communication timeline
            - Quality assurance checkpoints
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=feedback_prompt)
            ])
            
            feedback_strategy = self._parse_feedback_response(response.content)
            
            return {
                "status": "completed",
                "feedback_strategy": feedback_strategy,
                "feedback_analyzed": len(feedback_data),
                "priority_cases": feedback_strategy.get("priority_count", 0),
                "response_templates": len(feedback_strategy.get("templates", [])),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error("Feedback management failed", error=str(e))
            raise
    
    # Helper methods
    
    def _extract_passenger_info(self, rebooking_results: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract passenger information from rebooking results"""
        passengers = []
        
        # Extract from rebooking results if available
        results = rebooking_results.get("rebooking_results", [])
        for result in results:
            passengers.append({
                "passenger_id": result.get("passenger_id", ""),
                "tier_status": "regular",  # Would be retrieved from passenger data
                "preferred_channels": ["email"],
                "language": "en",
                "rebooking_status": result.get("status", "unknown")
            })
        
        # Add passengers from context if not in rebooking results
        context_passengers = context.get("affected_passengers", [])
        existing_ids = {p["passenger_id"] for p in passengers}
        
        for ctx_passenger in context_passengers:
            if ctx_passenger.get("passenger_id") not in existing_ids:
                passengers.append({
                    "passenger_id": ctx_passenger.get("passenger_id", ""),
                    "tier_status": ctx_passenger.get("tier_status", "regular"),
                    "preferred_channels": self.channel_preferences.get(
                        ctx_passenger.get("tier_status", "regular"), ["email"]
                    ),
                    "language": ctx_passenger.get("language", "en"),
                    "rebooking_status": "pending"
                })
        
        return passengers
    
    async def _generate_personalized_messages(self, passengers: List[Dict[str, Any]], 
                                            notification_type: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate personalized messages for each passenger"""
        messages = {}
        
        # Get base template
        base_template = self.message_templates.get(notification_type, "Update on your flight booking.")
        
        for passenger in passengers:
            # Customize based on passenger profile
            tier_status = passenger.get("tier_status", "regular")
            rebooking_status = passenger.get("rebooking_status", "pending")
            
            if tier_status in ["platinum", "gold"]:
                message_prefix = "Dear valued member, "
            else:
                message_prefix = "Dear customer, "
            
            # Add context-specific information
            flight_info = context.get("flight_info", {})
            message = base_template.format(
                flight_number=flight_info.get("flight_number", "your flight"),
                delay_minutes=context.get("delay_minutes", 0),
                new_departure=context.get("new_departure", "TBD"),
                new_flight=context.get("new_flight", "TBD"),
                new_time=context.get("new_time", "TBD"),
                hotel_name=context.get("hotel_name", "TBD"),
                booking_ref=context.get("booking_ref", "TBD"),
                pickup_location=context.get("pickup_location", "TBD")
            )
            
            messages[passenger["passenger_id"]] = message_prefix + message
        
        return messages
    
    def _group_by_channels(self, passengers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group passengers by their preferred communication channels"""
        channel_groups = {}
        
        for passenger in passengers:
            preferred_channels = passenger.get("preferred_channels", ["email"])
            primary_channel = preferred_channels[0] if preferred_channels else "email"
            
            if primary_channel not in channel_groups:
                channel_groups[primary_channel] = []
            
            channel_groups[primary_channel].append(passenger)
        
        return channel_groups
    
    def _get_message_priority(self, notification_type: str) -> str:
        """Get message priority based on notification type"""
        priority_mapping = {
            "emergency_broadcast": "urgent",
            "cancellation": "urgent",
            "delay_notification": "important",
            "rebooking_confirmation": "important",
            "compensation_eligible": "informational",
            "hotel_booking": "important",
            "transport_arranged": "important"
        }
        
        return priority_mapping.get(notification_type, "informational")
    
    def _analyze_delivery_results(self, delivery_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze message delivery results"""
        if not delivery_reports:
            return {"overall_delivery_rate": 0}
        
        successful_deliveries = len([r for r in delivery_reports if r.get("status") == "delivered"])
        total_deliveries = len(delivery_reports)
        
        # Group by channel
        channel_performance = {}
        for report in delivery_reports:
            channel = report.get("channel", "unknown")
            if channel not in channel_performance:
                channel_performance[channel] = {"delivered": 0, "total": 0}
            
            channel_performance[channel]["total"] += 1
            if report.get("status") == "delivered":
                channel_performance[channel]["delivered"] += 1
        
        # Calculate rates
        for channel in channel_performance:
            perf = channel_performance[channel]
            perf["delivery_rate"] = perf["delivered"] / perf["total"] if perf["total"] > 0 else 0
        
        return {
            "overall_delivery_rate": successful_deliveries / total_deliveries,
            "total_messages": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": total_deliveries - successful_deliveries,
            "channel_performance": channel_performance
        }
    
    # Response parsing methods
    
    def _parse_communication_summary(self, response: str) -> Dict[str, Any]:
        """Parse communication summary response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "effectiveness_score": 85,
            "channel_performance": {},
            "follow_up_recommendations": [],
            "summary": response
        }
    
    def _parse_personalization_response(self, response: str) -> Dict[str, Any]:
        """Parse personalization response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "templates": {},
            "segment_mapping": {},
            "personalization_rules": [],
            "summary": response
        }
    
    def _parse_coordination_response(self, response: str) -> Dict[str, Any]:
        """Parse coordination response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "channel_count": 3,
            "timeline": "2_hours",
            "coordination_points": [],
            "summary": response
        }
    
    def _parse_emergency_response(self, response: str) -> Dict[str, Any]:
        """Parse emergency broadcast response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "broadcast_text": response,
            "urgency_level": "high",
            "action_items": []
        }
    
    def _parse_response_analysis(self, response: str) -> Dict[str, Any]:
        """Parse response tracking analysis"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "response_rates": {},
            "sentiment_analysis": {},
            "optimization_opportunities": [],
            "summary": response
        }
    
    def _parse_feedback_response(self, response: str) -> Dict[str, Any]:
        """Parse feedback management response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "priority_count": 0,
            "templates": [],
            "service_recovery": [],
            "summary": response
        }