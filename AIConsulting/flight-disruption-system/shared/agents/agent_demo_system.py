"""
Agent Demonstration System

This module provides a comprehensive demonstration of the autonomous agentic intelligence
with live reasoning display, agent conversations, and executive-friendly visualizations.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
import structlog

from .autonomous_orchestrator import AutonomousAgentOrchestrator
from .agentic_intelligence import format_agent_conversation, generate_executive_summary

logger = structlog.get_logger()


class LiveAgentDemonstration:
    """
    Live demonstration system showing autonomous agents in action
    with visible reasoning, collaboration, and conflict resolution.
    """
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.orchestrator = AutonomousAgentOrchestrator(openai_api_key=openai_api_key)
        self.demo_scenarios = self._create_demo_scenarios()
        
    def _create_demo_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create realistic demonstration scenarios"""
        
        return {
            "weather_disruption_lhr": {
                "name": "Weather Disruption at London Heathrow",
                "description": "Heavy fog at LHR causing significant delays and cancellations",
                "context": {
                    "disruption_type": "weather_delay",
                    "airport_code": "LHR",
                    "affected_flights": [
                        {"flight_number": "BA123", "passengers": 180, "route": "LHR-JFK"},
                        {"flight_number": "BA456", "passengers": 200, "route": "LHR-CDG"},
                        {"flight_number": "VS789", "passengers": 250, "route": "LHR-LAX"}
                    ],
                    "severity": "high",
                    "expected_delay_hours": 4,
                    "weather_conditions": {
                        "visibility": "50m",
                        "fog_density": "dense",
                        "forecast": "clearing_in_3_hours"
                    },
                    "total_affected_passengers": 630,
                    "estimated_compensation": "£157,500",
                    "business_impact": "high"
                },
                "expected_agents": ["prediction", "passenger", "resource", "finance", "communication", "coordinator"],
                "demo_highlights": [
                    "AI predicts 78% probability of fog clearance by 14:30",
                    "Finance agent negotiates hotel rates 28% below market",
                    "Passenger agent prioritizes 89 business passengers with tight connections",
                    "Communication agent sends personalized updates in 6 languages",
                    "Resource agent coordinates 340 hotel rooms and transport"
                ]
            },
            
            "technical_aircraft_issue": {
                "name": "Technical Aircraft Issue - Manchester",
                "description": "Engine warning light on A320 requires maintenance inspection",
                "context": {
                    "disruption_type": "technical_delay", 
                    "airport_code": "MAN",
                    "aircraft_type": "Airbus A320",
                    "affected_flights": [
                        {"flight_number": "EZY892", "passengers": 174, "route": "MAN-AMS"},
                        {"flight_number": "EZY893", "passengers": 168, "route": "AMS-MAN"}
                    ],
                    "severity": "medium",
                    "expected_delay_hours": 2.5,
                    "maintenance_requirements": {
                        "inspection_time": "90_minutes",
                        "parts_available": True,
                        "crew_impact": "minimal"
                    },
                    "total_affected_passengers": 342,
                    "estimated_compensation": "£42,750",
                    "business_impact": "medium"
                },
                "expected_agents": ["prediction", "passenger", "resource", "finance", "communication"],
                "demo_highlights": [
                    "Prediction agent forecasts 2.5hr delay with 92% confidence",
                    "Resource agent identifies alternative aircraft in 45 minutes",
                    "Passenger agent manages complex connection rebookings",
                    "Finance agent calculates cost-optimal solution saving £18,400",
                    "Communication agent provides real-time maintenance updates"
                ]
            },
            
            "crew_shortage_disruption": {
                "name": "Crew Shortage Emergency - Edinburgh",
                "description": "Cabin crew illness causes cascading flight disruptions",
                "context": {
                    "disruption_type": "crew_shortage",
                    "airport_code": "EDI", 
                    "affected_flights": [
                        {"flight_number": "FR456", "passengers": 189, "route": "EDI-BCN"},
                        {"flight_number": "FR789", "passengers": 142, "route": "EDI-DUB"},
                        {"flight_number": "FR012", "passengers": 156, "route": "EDI-ALC"}
                    ],
                    "severity": "high",
                    "expected_delay_hours": 6,
                    "crew_situation": {
                        "sick_crew_members": 4,
                        "available_standby": 2,
                        "minimum_crew_required": 6,
                        "regulatory_limits": "duty_time_exceeded"
                    },
                    "total_affected_passengers": 487,
                    "estimated_compensation": "£121,750", 
                    "business_impact": "very_high"
                },
                "expected_agents": ["prediction", "passenger", "resource", "finance", "communication", "coordinator"],
                "demo_highlights": [
                    "Coordinator agent orchestrates complex crew reallocation",
                    "Finance agent weighs compensation vs alternative crew costs",
                    "Passenger agent manages high-priority rebookings",
                    "Resource agent sources accommodation for 487 passengers",
                    "Communication agent handles escalated customer complaints"
                ]
            }
        }
    
    async def run_live_demonstration(
        self, 
        scenario_name: str = "weather_disruption_lhr",
        real_time_display: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run live demonstration with streaming updates
        """
        
        if scenario_name not in self.demo_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.demo_scenarios[scenario_name]
        
        print(f"\n🚀 STARTING LIVE AUTONOMOUS AGENT DEMONSTRATION")
        print(f"=" * 60)
        print(f"Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Expected Agents: {len(scenario['expected_agents'])}")
        print(f"Affected Passengers: {scenario['context']['total_affected_passengers']}")
        print(f"=" * 60)
        
        try:
            # Initialize agent system
            print(f"\n🔧 Initializing Autonomous Agent System...")
            init_result = await self.orchestrator.initialize_agent_system()
            
            yield {
                "phase": "initialization",
                "status": "completed",
                "result": init_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if real_time_display:
                await asyncio.sleep(2)  # Pause for dramatic effect
            
            print(f"\n✅ Agent System Initialized:")
            print(f"   - Total Agents: {init_result['total_agents']}")
            print(f"   - Healthy Agents: {sum(1 for status in init_result['agent_health'].values() if status.get('healthy', False))}")
            print(f"   - Intelligence Engine: {init_result['intelligence_engine']}")
            
            # Start autonomous disruption handling
            print(f"\n🤖 BEGINNING AUTONOMOUS DISRUPTION RESPONSE")
            print(f"-" * 50)
            
            # Create real-time monitoring task
            monitor_task = asyncio.create_task(
                self._stream_live_reasoning(real_time_display)
            )
            
            # Run the autonomous scenario
            scenario_result = await self.orchestrator.demonstrate_autonomous_disruption_handling(
                scenario['context']
            )
            
            # Stop monitoring
            monitor_task.cancel()
            
            yield {
                "phase": "autonomous_execution",
                "status": "completed",
                "result": scenario_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Display final results
            await self._display_final_results(scenario_result)
            
            yield {
                "phase": "demonstration_complete",
                "status": "success",
                "scenario_name": scenario_name,
                "execution_time": scenario_result["execution_time"],
                "agents_involved": scenario_result["agents_involved"],
                "autonomous_success": scenario_result["autonomous_success"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in live demonstration: {e}")
            yield {
                "phase": "error",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _stream_live_reasoning(self, display: bool = True):
        """Stream live agent reasoning in real-time"""
        
        displayed_entries = set()
        
        try:
            while True:
                # Get current reasoning feed
                reasoning_feed = self.orchestrator.intelligence_engine.get_live_reasoning_feed()
                
                # Display new entries
                for entry in reasoning_feed:
                    if entry not in displayed_entries and display:
                        print(f"💭 {entry}")
                        displayed_entries.add(entry)
                
                await asyncio.sleep(0.5)  # Update every 500ms
                
        except asyncio.CancelledError:
            pass
    
    async def _display_final_results(self, scenario_result: Dict[str, Any]):
        """Display final demonstration results"""
        
        print(f"\n🎯 AUTONOMOUS DEMONSTRATION COMPLETE")
        print(f"=" * 60)
        
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"   Scenario ID: {scenario_result['scenario_id']}")
        print(f"   Execution Time: {scenario_result['execution_time']:.2f} seconds")
        print(f"   Phases Completed: {scenario_result['phases_completed']}/4")
        print(f"   Agents Involved: {scenario_result['agents_involved']}")
        print(f"   Collaborations: {scenario_result['collaborations_created']}")
        print(f"   Conflicts Resolved: {scenario_result['conflicts_resolved']}")
        print(f"   Learning Events: {scenario_result['learning_events']}")
        print(f"   Autonomous Success: {'✅ YES' if scenario_result['autonomous_success'] else '❌ NO'}")
        
        if "cost_impact" in scenario_result:
            cost_impact = scenario_result["cost_impact"]
            print(f"\n💰 FINANCIAL IMPACT:")
            print(f"   Resolution Savings: £{cost_impact.get('resolution_savings', 0):,.2f}")
            print(f"   Efficiency Gained: {cost_impact.get('efficiency_gained', 0):.1%}")
            print(f"   Cost Avoidance: £{cost_impact.get('cost_avoidance', 0):,.2f}")
        
        print(f"\n👥 PASSENGER IMPACT:")
        print(f"   Satisfaction Score: {scenario_result.get('passenger_satisfaction', 0):.1%}")
        
        # Display live reasoning log summary
        print(f"\n🧠 KEY AGENT DECISIONS:")
        reasoning_log = scenario_result.get("live_reasoning_log", [])[-10:]  # Last 10
        for i, entry in enumerate(reasoning_log, 1):
            print(f"   {i}. {entry[:100]}..." if len(entry) > 100 else f"   {i}. {entry}")
        
        print(f"\n" + "=" * 60)
    
    async def demonstrate_agent_collaboration(self) -> Dict[str, Any]:
        """Demonstrate specific agent-to-agent collaboration"""
        
        print(f"\n🤝 DEMONSTRATING AGENT-TO-AGENT COLLABORATION")
        print(f"=" * 50)
        
        # Initialize if needed
        if not self.orchestrator.agents:
            await self.orchestrator.initialize_agent_system()
        
        # Create collaboration scenario
        collaboration_context = {
            "scenario": "high_cost_disruption",
            "affected_passengers": 450,
            "estimated_cost": 125000,
            "priority": "critical",
            "time_constraint": "2_hours"
        }
        
        print(f"💡 Collaboration Scenario:")
        print(f"   Affected Passengers: {collaboration_context['affected_passengers']}")
        print(f"   Estimated Cost: £{collaboration_context['estimated_cost']:,}")
        print(f"   Priority: {collaboration_context['priority']}")
        print(f"   Time Constraint: {collaboration_context['time_constraint']}")
        
        # Initiate collaboration
        collaboration = await self.orchestrator.intelligence_engine.initiate_agent_collaboration(
            initiating_agent="finance_agent_01",
            target_agents=["passenger_agent_01", "resource_agent_01", "coordinator_agent_01"],
            collaboration_context=collaboration_context,
            collaboration_type="cost_crisis_management"
        )
        
        print(f"\n🔄 Agent Collaboration in Progress...")
        
        # Wait for agents to process
        await asyncio.sleep(3)
        
        # Format and display collaboration
        collaboration_display = await format_agent_conversation(collaboration)
        print(f"\n{collaboration_display}")
        
        return {
            "collaboration_id": collaboration.collaboration_id,
            "participating_agents": collaboration.participating_agents,
            "messages_exchanged": len(collaboration.messages),
            "collaboration_type": collaboration.collaboration_type,
            "success": True
        }
    
    async def demonstrate_conflict_resolution(self) -> Dict[str, Any]:
        """Demonstrate autonomous conflict resolution"""
        
        print(f"\n⚖️ DEMONSTRATING AUTONOMOUS CONFLICT RESOLUTION")
        print(f"=" * 50)
        
        # Initialize if needed  
        if not self.orchestrator.agents:
            await self.orchestrator.initialize_agent_system()
        
        # Create conflict scenario
        conflict_context = {
            "scenario": "resource_priority_conflict",
            "description": "Passenger comfort vs cost optimization conflict",
            "passenger_expectations": "premium_accommodation",
            "financial_constraints": "budget_limits_exceeded",
            "regulatory_requirements": "eu261_compliance"
        }
        
        print(f"🚨 Conflict Scenario:")
        print(f"   Type: Resource Priority Disagreement")
        print(f"   Description: {conflict_context['description']}")
        print(f"   Stakeholders: Passenger satisfaction vs Financial optimization")
        
        # Initiate conflict resolution
        from .agentic_intelligence import ConflictType
        resolution = await self.orchestrator.intelligence_engine.resolve_agent_conflict(
            conflicting_agents=["passenger_agent_01", "finance_agent_01"],
            conflict_context=conflict_context,
            conflict_type=ConflictType.RESOURCE_ALLOCATION
        )
        
        print(f"\n🔧 Autonomous Resolution Process:")
        for i, step in enumerate(resolution.resolution_steps, 1):
            print(f"   Step {i}: {step}")
        
        print(f"\n✅ Resolution Outcome:")
        print(f"   Status: {resolution.consensus_status.value.upper()}")
        print(f"   Final Resolution: {resolution.final_resolution}")
        print(f"   Compromise Points: {len(resolution.compromise_points)}")
        
        return {
            "resolution_id": resolution.conflict_id,
            "conflict_type": resolution.conflict_type.value,
            "involved_agents": resolution.involved_agents,
            "status": resolution.consensus_status.value,
            "resolution": resolution.final_resolution,
            "steps_taken": len(resolution.resolution_steps)
        }
    
    async def demonstrate_learning_system(self) -> Dict[str, Any]:
        """Demonstrate real-time learning and adaptation"""
        
        print(f"\n🧠 DEMONSTRATING REAL-TIME LEARNING SYSTEM")
        print(f"=" * 50)
        
        # Initialize if needed
        if not self.orchestrator.agents:
            await self.orchestrator.initialize_agent_system()
        
        # Simulate multiple decision outcomes for learning
        learning_scenarios = [
            {
                "agent_id": "finance_agent_01",
                "decision_context": {"cost_optimization": "hotel_booking"},
                "predicted_outcome": {"cost": 15000, "satisfaction": 0.8},
                "actual_outcome": {"cost": 13500, "satisfaction": 0.85},
                "feedback_score": 0.9  # Good performance
            },
            {
                "agent_id": "passenger_agent_01", 
                "decision_context": {"rebooking_strategy": "priority_based"},
                "predicted_outcome": {"success_rate": 0.85, "time": 120},
                "actual_outcome": {"success_rate": 0.82, "time": 95},
                "feedback_score": 0.7  # Moderate performance
            },
            {
                "agent_id": "resource_agent_01",
                "decision_context": {"resource_allocation": "transport_coordination"},
                "predicted_outcome": {"efficiency": 0.9, "cost": 8000},
                "actual_outcome": {"efficiency": 0.95, "cost": 7200},
                "feedback_score": 0.95  # Excellent performance
            }
        ]
        
        learning_results = []
        
        for scenario in learning_scenarios:
            print(f"\n📊 Learning Scenario: {scenario['decision_context']}")
            
            learning_event = await self.orchestrator.intelligence_engine.learn_from_outcome(
                agent_id=scenario["agent_id"],
                decision_context=scenario["decision_context"],
                predicted_outcome=scenario["predicted_outcome"],
                actual_outcome=scenario["actual_outcome"],
                feedback_score=scenario["feedback_score"]
            )
            
            learning_results.append(learning_event)
            
            print(f"   Agent: {scenario['agent_id']}")
            print(f"   Feedback Score: {scenario['feedback_score']:.2f}")
            print(f"   Key Lesson: {learning_event.lessons_learned[0] if learning_event.lessons_learned else 'Model updated'}")
        
        # Display system-wide learning improvements
        print(f"\n🚀 SYSTEM LEARNING IMPROVEMENTS:")
        print(f"   Total Learning Events: {len(learning_results)}")
        print(f"   Average Feedback Score: {sum(s['feedback_score'] for s in learning_scenarios) / len(learning_scenarios):.2f}")
        print(f"   Model Adaptations Made: {sum(1 for lr in learning_results if lr.model_adjustments)}")
        
        return {
            "learning_events": len(learning_results),
            "average_feedback": sum(s['feedback_score'] for s in learning_scenarios) / len(learning_scenarios),
            "improvements_detected": len([s for s in learning_scenarios if s['feedback_score'] > 0.8]),
            "lessons_learned": [lr.lessons_learned for lr in learning_results],
            "system_adaptation": "active"
        }
    
    async def generate_executive_demo_report(self) -> str:
        """Generate comprehensive executive demonstration report"""
        
        return await self.orchestrator.generate_executive_demo_report()


# Convenience function for easy demonstration
async def run_quick_demo(openai_api_key: str, scenario: str = "weather_disruption_lhr"):
    """Run a quick demonstration of the agentic system"""
    
    demo = LiveAgentDemonstration(openai_api_key)
    
    print(f"🎬 QUICK AUTONOMOUS AGENT DEMO")
    print(f"Scenario: {scenario}")
    print(f"=" * 40)
    
    async for update in demo.run_live_demonstration(scenario, real_time_display=True):
        if update["phase"] == "demonstration_complete":
            print(f"\n✅ Demo Complete!")
            print(f"Execution Time: {update['execution_time']:.2f}s")
            print(f"Agents Involved: {update['agents_involved']}")
            print(f"Autonomous Success: {update['autonomous_success']}")
            break


# Main demonstration runner
async def main_demonstration(openai_api_key: str):
    """Run comprehensive demonstration of all agentic capabilities"""
    
    demo = LiveAgentDemonstration(openai_api_key)
    
    print(f"\n🚀 COMPREHENSIVE AUTONOMOUS AGENT DEMONSTRATION")
    print(f"=" * 60)
    print(f"This demonstration will showcase:")
    print(f"✅ Autonomous agent reasoning with visible decision chains")
    print(f"✅ Multi-agent collaboration and communication")
    print(f"✅ Autonomous conflict resolution without human intervention") 
    print(f"✅ Real-time learning and adaptation")
    print(f"✅ Executive-friendly transparency and reporting")
    print(f"=" * 60)
    
    # 1. Full scenario demonstration
    print(f"\n1️⃣ FULL SCENARIO DEMONSTRATION")
    async for update in demo.run_live_demonstration("weather_disruption_lhr"):
        if update["phase"] == "demonstration_complete":
            break
    
    # 2. Agent collaboration demo
    print(f"\n2️⃣ AGENT COLLABORATION DEMONSTRATION")
    collab_result = await demo.demonstrate_agent_collaboration()
    
    # 3. Conflict resolution demo
    print(f"\n3️⃣ CONFLICT RESOLUTION DEMONSTRATION") 
    conflict_result = await demo.demonstrate_conflict_resolution()
    
    # 4. Learning system demo
    print(f"\n4️⃣ LEARNING SYSTEM DEMONSTRATION")
    learning_result = await demo.demonstrate_learning_system()
    
    # 5. Executive report
    print(f"\n5️⃣ EXECUTIVE SUMMARY REPORT")
    executive_report = await demo.generate_executive_demo_report()
    print(executive_report)
    
    print(f"\n🎯 DEMONSTRATION COMPLETE")
    print(f"All autonomous agent capabilities successfully demonstrated!")


if __name__ == "__main__":
    # Example usage
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        asyncio.run(main_demonstration(api_key))
    else:
        print("Please set OPENAI_API_KEY environment variable")