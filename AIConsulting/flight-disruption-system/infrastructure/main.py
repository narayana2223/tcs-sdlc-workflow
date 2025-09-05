"""
Flight Disruption Management System - Main Integration Module
Orchestrates all components of the real-time data infrastructure
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from kafka.kafka_config import setup_kafka_infrastructure, get_kafka_config_from_env
from streaming.stream_processor import create_default_stream_processors, StreamProcessorManager
from streaming.event_correlator import EventCorrelationEngine
from reliability.error_handler import ComprehensiveErrorHandler, create_default_retry_config
from external_apis.base_client import create_api_config_from_env
from external_apis.flight_data_client import FlightDataClient, AirlineSystemClient
from external_apis.weather_client import WeatherClient
from demo.mock_data_generator import MockDataStreamer, ScenarioType, run_demo_scenario


class SystemHealthMonitor:
    """Monitors overall system health and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.health_checks = {}
        self.last_health_check = None
    
    async def check_system_health(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check Kafka infrastructure
            if 'kafka_config' in components:
                kafka_health = await self._check_kafka_health(components['kafka_config'])
                health_status['components']['kafka'] = kafka_health
                if not kafka_health['healthy']:
                    health_status['overall_status'] = 'degraded'
            
            # Check stream processors
            if 'stream_manager' in components:
                processor_health = await self._check_stream_processors(components['stream_manager'])
                health_status['components']['stream_processors'] = processor_health
                if processor_health['unhealthy_count'] > 0:
                    health_status['overall_status'] = 'degraded'
            
            # Check external API clients
            if 'api_clients' in components:
                api_health = await self._check_api_clients(components['api_clients'])
                health_status['components']['external_apis'] = api_health
                if api_health['unhealthy_count'] > 0:
                    health_status['warnings'].append('Some external APIs are unhealthy')
            
            # Check error handler
            if 'error_handler' in components:
                error_stats = components['error_handler'].get_error_statistics()
                health_status['components']['error_handler'] = {
                    'healthy': error_stats['error_rate_per_hour'] < 100,
                    'error_rate_per_hour': error_stats['error_rate_per_hour'],
                    'circuit_breakers_open': sum(
                        1 for cb in error_stats['circuit_breaker_states'].values() 
                        if cb['state'] == 'open'
                    )
                }
        
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status['overall_status'] = 'error'
            health_status['errors'].append(f"Health check error: {str(e)}")
        
        self.last_health_check = health_status
        return health_status
    
    async def _check_kafka_health(self, kafka_config) -> Dict[str, Any]:
        """Check Kafka cluster health"""
        try:
            from confluent_kafka.admin import AdminClient
            
            admin_client = AdminClient({
                'bootstrap.servers': kafka_config.bootstrap_servers
            })
            
            # Try to list topics
            metadata = admin_client.list_topics(timeout=5)
            topic_count = len(metadata.topics)
            
            return {
                'healthy': True,
                'topic_count': topic_count,
                'brokers': len(metadata.brokers)
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    async def _check_stream_processors(self, stream_manager: StreamProcessorManager) -> Dict[str, Any]:
        """Check stream processor health"""
        try:
            metrics = stream_manager.get_all_metrics()
            
            unhealthy_count = 0
            processor_statuses = {}
            
            for name, processor_metrics in metrics.items():
                is_healthy = (
                    processor_metrics['state'] in ['running', 'paused'] and
                    processor_metrics['metrics']['events_failed'] < processor_metrics['metrics']['events_processed'] * 0.1
                )
                
                processor_statuses[name] = {
                    'healthy': is_healthy,
                    'state': processor_metrics['state'],
                    'events_processed': processor_metrics['metrics']['events_processed'],
                    'events_failed': processor_metrics['metrics']['events_failed']
                }
                
                if not is_healthy:
                    unhealthy_count += 1
            
            return {
                'healthy': unhealthy_count == 0,
                'total_processors': len(metrics),
                'unhealthy_count': unhealthy_count,
                'processor_status': processor_statuses
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    async def _check_api_clients(self, api_clients: Dict[str, Any]) -> Dict[str, Any]:
        """Check external API client health"""
        unhealthy_count = 0
        client_statuses = {}
        
        for name, client in api_clients.items():
            try:
                if hasattr(client, 'health_check'):
                    is_healthy = await client.health_check()
                    metrics = client.get_metrics()
                    
                    client_statuses[name] = {
                        'healthy': is_healthy,
                        'status': metrics.get('status', 'unknown'),
                        'last_request': metrics.get('last_request_time'),
                        'error_count': metrics.get('failed_requests', 0)
                    }
                    
                    if not is_healthy:
                        unhealthy_count += 1
                else:
                    client_statuses[name] = {'healthy': True, 'status': 'no_health_check'}
                    
            except Exception as e:
                client_statuses[name] = {'healthy': False, 'error': str(e)}
                unhealthy_count += 1
        
        return {
            'healthy': unhealthy_count == 0,
            'total_clients': len(api_clients),
            'unhealthy_count': unhealthy_count,
            'client_status': client_statuses
        }


class FlightDisruptionSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.components = {}
        self.health_monitor = SystemHealthMonitor()
        self.is_running = False
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize all system components"""
        self.logger.info("Initializing Flight Disruption Management System")
        
        try:
            # Setup Kafka infrastructure
            kafka_setup = setup_kafka_infrastructure()
            self.components['kafka_config'] = kafka_setup['config']
            self.components['topic_manager'] = kafka_setup['topic_manager']
            self.components['schema_manager'] = kafka_setup['schema_manager']
            
            # Initialize error handling
            from confluent_kafka import Producer
            producer = Producer(kafka_setup['config'].producer_config)
            error_handler = ComprehensiveErrorHandler(producer)
            self.components['error_handler'] = error_handler
            
            # Initialize stream processors
            stream_manager = await create_default_stream_processors(kafka_setup['config'])
            
            # Add event correlation engine
            correlation_engine = EventCorrelationEngine(kafka_setup['config'])
            stream_manager.register_processor(correlation_engine)
            
            self.components['stream_manager'] = stream_manager
            
            # Initialize external API clients
            api_clients = {}
            
            # Flight data client
            flight_config = create_api_config_from_env('FLIGHT_DATA')
            flight_config.mock_mode = True  # Enable mock mode for demo
            api_clients['flight_data'] = FlightDataClient(flight_config)
            
            # Weather client
            weather_config = create_api_config_from_env('WEATHER')
            weather_config.mock_mode = True  # Enable mock mode for demo
            api_clients['weather'] = WeatherClient(weather_config)
            
            # Airline system client
            airline_config = create_api_config_from_env('AIRLINE_SYSTEM')
            airline_config.mock_mode = True  # Enable mock mode for demo
            api_clients['airline_system'] = AirlineSystemClient(airline_config, 'BA')
            
            self.components['api_clients'] = api_clients
            
            # Initialize mock data streamer for demo
            mock_streamer = MockDataStreamer(kafka_setup['config'])
            self.components['mock_streamer'] = mock_streamer
            
            self.logger.info("System initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            raise
    
    async def start(self):
        """Start all system components"""
        if self.is_running:
            self.logger.warning("System is already running")
            return
        
        self.logger.info("Starting Flight Disruption Management System")
        
        try:
            # Start stream processors
            if 'stream_manager' in self.components:
                stream_manager = self.components['stream_manager']
                # Start processors in background
                asyncio.create_task(stream_manager.start_all())
            
            # Connect API clients
            if 'api_clients' in self.components:
                for name, client in self.components['api_clients'].items():
                    try:
                        await client.connect()
                        await client.authenticate()
                        self.logger.info(f"Connected to {name} API")
                    except Exception as e:
                        self.logger.warning(f"Failed to connect to {name} API: {e}")
            
            self.is_running = True
            self.logger.info("System started successfully")
            
            # Start health monitoring
            asyncio.create_task(self._health_monitoring_loop())
            
        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop all system components gracefully"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping Flight Disruption Management System")
        self.is_running = False
        self._shutdown_event.set()
        
        try:
            # Stop mock data streamer
            if 'mock_streamer' in self.components:
                self.components['mock_streamer'].stop_streaming()
                self.components['mock_streamer'].close()
            
            # Stop stream processors
            if 'stream_manager' in self.components:
                await self.components['stream_manager'].stop_all()
            
            # Close API clients
            if 'api_clients' in self.components:
                for name, client in self.components['api_clients'].items():
                    try:
                        await client.close()
                        self.logger.info(f"Closed {name} API connection")
                    except Exception as e:
                        self.logger.warning(f"Error closing {name} API: {e}")
            
            self.logger.info("System stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
    
    async def run_demo_scenario(
        self,
        scenario: ScenarioType = ScenarioType.WEATHER_DISRUPTION,
        duration_hours: int = 4,
        speed_multiplier: float = 10.0
    ):
        """Run a demo scenario"""
        if not self.is_running:
            await self.start()
        
        self.logger.info(f"Starting demo scenario: {scenario.value}")
        
        try:
            mock_streamer = self.components.get('mock_streamer')
            if mock_streamer:
                await mock_streamer.stream_scenario(scenario, duration_hours, speed_multiplier)
            else:
                # Fallback to standalone demo
                await run_demo_scenario(
                    self.components['kafka_config'],
                    scenario,
                    duration_hours,
                    speed_multiplier
                )
        except Exception as e:
            self.logger.error(f"Demo scenario failed: {e}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health_status = await self.health_monitor.check_system_health(self.components)
        
        # Add component-specific metrics
        status = {
            'system_running': self.is_running,
            'health': health_status,
            'components': {}
        }
        
        # Stream processor metrics
        if 'stream_manager' in self.components:
            status['components']['stream_processors'] = self.components['stream_manager'].get_all_metrics()
        
        # Error handler metrics
        if 'error_handler' in self.components:
            status['components']['error_handler'] = self.components['error_handler'].get_error_statistics()
        
        return status
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                health_status = await self.health_monitor.check_system_health(self.components)
                
                if health_status['overall_status'] == 'error':
                    self.logger.error("System health check failed")
                elif health_status['overall_status'] == 'degraded':
                    self.logger.warning("System health is degraded")
                else:
                    self.logger.debug("System health is good")
                
                # Wait before next check
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=30)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Continue monitoring
                    
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)


# Global system instance
system_instance = None


async def create_system() -> FlightDisruptionSystem:
    """Create and initialize the flight disruption system"""
    global system_instance
    
    if system_instance is None:
        system_instance = FlightDisruptionSystem()
        await system_instance.initialize()
    
    return system_instance


async def start_system():
    """Start the flight disruption system"""
    system = await create_system()
    await system.start()
    return system


async def stop_system():
    """Stop the flight disruption system"""
    global system_instance
    
    if system_instance:
        await system_instance.stop()


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/flight-disruption-system.log', mode='a')
        ]
    )


async def main():
    """Main entry point for the system"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(stop_system())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start system
        system = await start_system()
        logger.info("Flight Disruption Management System is running")
        
        # Run demo scenario if requested
        import os
        demo_scenario = os.getenv('DEMO_SCENARIO')
        if demo_scenario:
            scenario_type = ScenarioType(demo_scenario)
            duration = int(os.getenv('DEMO_DURATION_HOURS', '4'))
            speed = float(os.getenv('DEMO_SPEED_MULTIPLIER', '10.0'))
            
            logger.info(f"Running demo scenario: {scenario_type.value}")
            await system.run_demo_scenario(scenario_type, duration, speed)
        else:
            # Keep system running
            while system.is_running:
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        await stop_system()
        logger.info("System shutdown complete")


@asynccontextmanager
async def flight_disruption_system():
    """Context manager for the flight disruption system"""
    system = await create_system()
    await system.start()
    try:
        yield system
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())