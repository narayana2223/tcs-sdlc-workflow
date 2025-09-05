"""
Basic Usage Examples for Flight Disruption AI Agent System

This module demonstrates how to use the AI agent framework for
handling flight disruptions with autonomous decision-making.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from shared.agents.agent_factory import AgentManager, AgentConfiguration
from shared.agents.orchestrator import TaskType, TaskPriority


async def basic_disruption_handling_example():
    """
    Example: Handle a basic flight disruption scenario
    """
    print("=== Basic Disruption Handling Example ===")
    
    # Configure the agent system
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        model_name="gpt-4",
        temperature=0.1
    )
    
    # Create agent manager
    manager = AgentManager(config)
    
    try:
        # Initialize the agent system
        init_result = await manager.initialize_system()
        print(f"✅ System initialized: {init_result['agents_created']} agents created")
        
        # Define disruption scenario
        disruption_context = {
            "incident_id": "DISRUPTION_001",
            "type": "weather_delay",
            "airport_code": "LHR",
            "affected_flights": [
                {"flight_number": "BA123", "route": "LHR-CDG", "passengers": 180},
                {"flight_number": "BA456", "route": "LHR-FRA", "passengers": 200}
            ],
            "severity": "medium",
            "expected_delay_hours": 4,
            "weather_conditions": "heavy_rain_and_wind",
            "start_time": datetime.now().isoformat(),
            "affected_passengers": 380
        }
        
        print(f"🌧️  Processing weather disruption affecting {disruption_context['affected_passengers']} passengers")
        
        # Handle the disruption using AI agents
        result = await manager.handle_disruption(
            disruption_context=disruption_context,
            priority=TaskPriority.HIGH
        )
        
        print(f"✅ Disruption handled successfully!")
        print(f"   - Task ID: {result.get('task_id', 'N/A')}")
        print(f"   - Execution time: {result.get('execution_time', 0):.2f} seconds")
        print(f"   - Agents involved: {len(result.get('agents_involved', []))}")
        print(f"   - Status: {result.get('status', 'Unknown')}")
        
        # Show some key results
        step_results = result.get("step_results", {})
        if "situation_assessment" in step_results:
            assessment = step_results["situation_assessment"]
            print(f"   - Situation severity: {assessment.get('assessment', {}).get('severity', 'Unknown')}")
        
        if "execution" in step_results:
            execution = step_results["execution"]
            print(f"   - Passenger rebooking: {execution.get('passenger', {}).get('status', 'Unknown')}")
            print(f"   - Resource coordination: {execution.get('resource', {}).get('status', 'Unknown')}")
            print(f"   - Communications sent: {execution.get('communication', {}).get('status', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def passenger_rebooking_example():
    """
    Example: Handle passenger rebooking workflow
    """
    print("=== Passenger Rebooking Example ===")
    
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    manager = AgentManager(config)
    
    try:
        await manager.initialize_system()
        print("✅ System initialized for passenger rebooking")
        
        # Passenger rebooking context
        passenger_context = {
            "disrupted_flights": ["BA789", "BA012"],
            "affected_passengers": [
                {
                    "passenger_id": "PAX001",
                    "pnr": "ABC123",
                    "tier_status": "Gold",
                    "original_flight": "BA789",
                    "destination": "CDG",
                    "connection_flight": "AF456",
                    "special_requests": ["WHEELCHAIR"]
                },
                {
                    "passenger_id": "PAX002", 
                    "pnr": "DEF456",
                    "tier_status": "Regular",
                    "original_flight": "BA789",
                    "destination": "CDG",
                    "travel_purpose": "leisure"
                }
            ],
            "rebooking_options": {
                "same_day_alternatives": 3,
                "next_day_alternatives": 8,
                "partner_airline_options": 2
            }
        }
        
        print(f"👥 Processing rebooking for {len(passenger_context['affected_passengers'])} passengers")
        
        # Execute passenger rebooking workflow
        result = await manager.process_passenger_rebooking(
            passenger_context=passenger_context,
            priority=TaskPriority.HIGH
        )
        
        print(f"✅ Rebooking completed!")
        print(f"   - Success rate: {result.get('step_results', {}).get('rebooking_results', {}).get('success_rate', 0)*100:.1f}%")
        print(f"   - Passengers processed: {result.get('step_results', {}).get('rebooking_results', {}).get('passengers_processed', 0)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def cost_optimization_example():
    """
    Example: Cost optimization workflow
    """
    print("=== Cost Optimization Example ===")
    
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    manager = AgentManager(config)
    
    try:
        await manager.initialize_system()
        print("✅ System initialized for cost optimization")
        
        # Cost optimization context
        cost_context = {
            "disruption_costs": {
                "hotel_accommodation": 15000,  # GBP
                "meal_vouchers": 8000,
                "ground_transport": 5000,
                "compensation": 25000,
                "rebooking_fees": 3000
            },
            "passenger_segments": {
                "premium": 50,
                "regular": 250,
                "connecting": 80
            },
            "optimization_targets": {
                "cost_reduction_percentage": 15,
                "service_quality_minimum": 85
            },
            "constraints": {
                "regulatory_compliance": "EU261",
                "brand_standards": "maintain_premium_service",
                "timeline": "4_hours"
            }
        }
        
        total_cost = sum(cost_context["disruption_costs"].values())
        print(f"💰 Optimizing costs for disruption (Total: £{total_cost:,})")
        
        # Execute cost optimization
        result = await manager.optimize_costs(
            cost_context=cost_context,
            priority=TaskPriority.NORMAL
        )
        
        print(f"✅ Cost optimization completed!")
        optimization_result = result.get("step_results", {}).get("optimization", {})
        if "cost_savings" in result:
            savings = result["cost_savings"]
            savings_pct = result.get("savings_percentage", 0)
            print(f"   - Cost savings: £{savings:,.2f} ({savings_pct:.1f}%)")
        
        efficiency_score = result.get("efficiency_score", 0)
        print(f"   - Efficiency score: {efficiency_score}/100")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def communication_campaign_example():
    """
    Example: Communication campaign workflow
    """
    print("=== Communication Campaign Example ===")
    
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    manager = AgentManager(config)
    
    try:
        await manager.initialize_system()
        print("✅ System initialized for communication campaign")
        
        # Communication context
        communication_context = {
            "campaign_type": "disruption_update",
            "affected_passengers": 500,
            "passenger_segments": {
                "platinum": {"count": 25, "channels": ["sms", "email", "push"]},
                "gold": {"count": 75, "channels": ["sms", "email"]},
                "regular": {"count": 400, "channels": ["email"]}
            },
            "message_content": {
                "primary": "Flight delay notification and rebooking options",
                "compensation": "EU261 compensation eligibility information",
                "services": "Hotel and transport arrangements"
            },
            "urgency": "high",
            "languages": ["en", "fr", "de"],
            "delivery_timeline": "immediate"
        }
        
        print(f"📱 Sending communications to {communication_context['affected_passengers']} passengers")
        
        # Execute communication campaign
        result = await manager.send_communications(
            communication_context=communication_context,
            priority=TaskPriority.HIGH
        )
        
        print(f"✅ Communication campaign completed!")
        
        # Show delivery results
        step_results = result.get("step_results", {})
        if "notifications" in step_results:
            notifications = step_results["notifications"]
            delivery_rate = notifications.get("delivery_rate", 0)
            print(f"   - Delivery rate: {delivery_rate*100:.1f}%")
            print(f"   - Channels used: {', '.join(notifications.get('channels_used', []))}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def predictive_analysis_example():
    """
    Example: Predictive analysis workflow
    """
    print("=== Predictive Analysis Example ===")
    
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    manager = AgentManager(config)
    
    try:
        await manager.initialize_system()
        print("✅ System initialized for predictive analysis")
        
        # Prediction context
        prediction_context = {
            "analysis_type": "disruption_forecast",
            "forecast_window_hours": 4,
            "airports": ["LHR", "CDG", "FRA"],
            "weather_data": {
                "lhr": {"conditions": "storm_approaching", "severity": "high", "eta": "2_hours"},
                "cdg": {"conditions": "clear", "severity": "none"},
                "fra": {"conditions": "light_rain", "severity": "low"}
            },
            "flight_volume": {
                "peak_hours": ["08:00", "18:00"],
                "daily_flights": 850
            },
            "historical_patterns": {
                "weather_delays_winter": 0.15,
                "cascade_probability": 0.3
            }
        }
        
        print(f"🔮 Generating {prediction_context['forecast_window_hours']}-hour disruption forecast")
        
        # Execute predictive analysis
        result = await manager.get_predictions(
            prediction_context=prediction_context,
            priority=TaskPriority.NORMAL
        )
        
        print(f"✅ Predictive analysis completed!")
        
        # Show prediction results
        if "forecasts" in result.get("step_results", {}):
            forecasts = result["step_results"]["forecasts"]
            print(f"   - Forecast confidence: {forecasts.get('confidence', 'medium')}")
            print(f"   - Validity period: {result.get('forecast_window_hours', 4)} hours")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def system_performance_monitoring_example():
    """
    Example: System performance monitoring
    """
    print("=== System Performance Monitoring Example ===")
    
    config = AgentConfiguration(
        openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    manager = AgentManager(config)
    
    try:
        await manager.initialize_system()
        print("✅ System initialized for performance monitoring")
        
        # Run some sample operations to generate performance data
        sample_contexts = [
            {"type": "minor_delay", "passengers": 50},
            {"type": "weather_disruption", "passengers": 200},
            {"type": "technical_issue", "passengers": 150}
        ]
        
        print("🔄 Running sample operations to generate performance data...")
        
        for i, context in enumerate(sample_contexts):
            try:
                await manager.handle_disruption(context, TaskPriority.NORMAL)
                print(f"   ✅ Operation {i+1} completed")
            except Exception as e:
                print(f"   ⚠️  Operation {i+1} failed: {str(e)}")
        
        # Get system performance metrics
        print("\n📊 Getting system performance metrics...")
        performance = await manager.get_system_performance()
        
        print("✅ Performance analysis completed!")
        
        # Display key metrics
        system_status = performance.get("system_status", {})
        print(f"   - Total agents: {system_status.get('total_agents', 0)}")
        print(f"   - System health: {performance.get('health_check', {}).get('overall_health', 'unknown')}")
        
        agent_performance = performance.get("agent_performance", {})
        for agent_type, metrics in agent_performance.items():
            if metrics:
                success_rate = metrics.get("success_rate", 0) * 100
                avg_duration = metrics.get("avg_duration_ms", 0) / 1000
                print(f"   - {agent_type.title()} agent: {success_rate:.1f}% success, {avg_duration:.2f}s avg response")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        manager.shutdown()
    
    print("\n")


async def main():
    """
    Run all examples
    """
    print("🚀 Flight Disruption AI Agent System Examples")
    print("=" * 50)
    print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set.")
        print("   Set your OpenAI API key to run these examples:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print()
    
    examples = [
        basic_disruption_handling_example,
        passenger_rebooking_example,
        cost_optimization_example,
        communication_campaign_example,
        predictive_analysis_example,
        system_performance_monitoring_example
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            print(f"Running Example {i}/{len(examples)}: {example.__name__}")
            print("-" * 40)
            await example()
            await asyncio.sleep(1)  # Brief pause between examples
        except Exception as e:
            print(f"❌ Example {i} failed: {str(e)}")
            print()
    
    print("🎉 All examples completed!")
    print()
    print("Next Steps:")
    print("- Integrate the agent system into your flight disruption service")
    print("- Configure with your actual API keys and endpoints")
    print("- Customize agent behaviors for your airline's specific needs")
    print("- Set up monitoring and alerting for production use")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())