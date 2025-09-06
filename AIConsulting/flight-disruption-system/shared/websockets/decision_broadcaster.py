"""
Decision Broadcasting System

This module provides centralized WebSocket broadcasting for agent decisions
across all interfaces with unified state management and real-time synchronization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
import structlog
from collections import defaultdict, deque
import weakref

# Import decision models
from ..models.decision_models import (
    AgentDecision, DecisionStream, AgentCollaboration,
    DecisionType, ReasoningStep, DataSourceType
)

logger = structlog.get_logger()


class BroadcastChannel(Enum):
    """Different broadcast channels for targeted messaging"""
    DECISIONS = "decisions"
    COLLABORATIONS = "collaborations"
    ANALYTICS = "analytics"
    SYSTEM_STATUS = "system_status"
    DEMO_CONTROLS = "demo_controls"
    PASSENGER_UPDATES = "passenger_updates"
    EXECUTIVE_METRICS = "executive_metrics"
    ALL = "all"


class ClientType(Enum):
    """Types of client interfaces"""
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    OPERATIONS_CENTER = "operations_center"
    PASSENGER_PORTAL = "passenger_portal"
    EXTERNAL_API = "external_api"


class BroadcastMessage:
    """Structured broadcast message"""
    
    def __init__(self, 
                 message_type: str,
                 channel: BroadcastChannel,
                 data: Dict[str, Any],
                 priority: int = 5,
                 target_clients: List[ClientType] = None,
                 expires_at: datetime = None):
        
        self.message_id = f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
        self.message_type = message_type
        self.channel = channel
        self.data = data
        self.priority = priority
        self.target_clients = target_clients or []
        self.created_at = datetime.utcnow()
        self.expires_at = expires_at or (self.created_at + timedelta(minutes=30))
        self.delivery_count = 0
        self.failed_deliveries = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "message_id": self.message_id,
            "type": self.message_type,
            "channel": self.channel.value,
            "data": self.data,
            "priority": self.priority,
            "timestamp": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_targeted_to(self, client_type: ClientType) -> bool:
        """Check if message is targeted to specific client type"""
        return not self.target_clients or client_type in self.target_clients


class ClientConnection:
    """Represents a client connection with metadata"""
    
    def __init__(self, 
                 connection_id: str,
                 client_type: ClientType,
                 subscribed_channels: List[BroadcastChannel] = None,
                 metadata: Dict[str, Any] = None):
        
        self.connection_id = connection_id
        self.client_type = client_type
        self.subscribed_channels = subscribed_channels or [BroadcastChannel.ALL]
        self.metadata = metadata or {}
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.message_queue = deque(maxlen=100)  # Buffer for failed messages
        self.total_messages_sent = 0
        self.failed_messages = 0
        self.is_active = True
        
        # Weak reference to actual WebSocket connection
        self._websocket_ref = None
    
    def set_websocket(self, websocket):
        """Set WebSocket reference"""
        self._websocket_ref = weakref.ref(websocket)
    
    def get_websocket(self):
        """Get WebSocket connection if still alive"""
        if self._websocket_ref:
            return self._websocket_ref()
        return None
    
    def is_subscribed_to(self, channel: BroadcastChannel) -> bool:
        """Check if client is subscribed to channel"""
        return BroadcastChannel.ALL in self.subscribed_channels or channel in self.subscribed_channels
    
    def update_subscription(self, channels: List[BroadcastChannel]):
        """Update channel subscriptions"""
        self.subscribed_channels = channels
        logger.info("Client subscription updated",
                   connection_id=self.connection_id,
                   channels=[c.value for c in channels])
    
    def queue_message(self, message: BroadcastMessage):
        """Queue message for delivery"""
        self.message_queue.append(message)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "connection_id": self.connection_id,
            "client_type": self.client_type.value,
            "subscribed_channels": [c.value for c in self.subscribed_channels],
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "connection_duration": (datetime.utcnow() - self.connected_at).total_seconds(),
            "messages_sent": self.total_messages_sent,
            "failed_messages": self.failed_messages,
            "success_rate": (self.total_messages_sent - self.failed_messages) / max(1, self.total_messages_sent),
            "is_active": self.is_active,
            "queued_messages": len(self.message_queue),
            "metadata": self.metadata
        }


class DecisionBroadcaster:
    """
    Centralized decision broadcasting system that manages WebSocket connections
    across all interfaces with unified state management and intelligent routing
    """
    
    def __init__(self):
        self.connections: Dict[str, ClientConnection] = {}
        self.message_history: deque = deque(maxlen=1000)  # Keep last 1000 messages
        self.channel_subscribers: Dict[BroadcastChannel, Set[str]] = defaultdict(set)
        self.broadcast_stats = {
            "total_messages": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "active_connections": 0,
            "messages_per_minute": 0
        }
        
        # Message handlers for different channels
        self.message_handlers: Dict[BroadcastChannel, List[Callable]] = defaultdict(list)
        
        # Background tasks
        self._cleanup_task = None
        self._stats_task = None
        self._heartbeat_task = None
        
        # Rate limiting
        self.rate_limits = {
            BroadcastChannel.DECISIONS: 100,  # messages per minute
            BroadcastChannel.ANALYTICS: 10,
            BroadcastChannel.SYSTEM_STATUS: 60,
            BroadcastChannel.ALL: 200
        }
        self.rate_counters = defaultdict(int)
        self.last_rate_reset = datetime.utcnow()
        
        logger.info("DecisionBroadcaster initialized")
    
    async def start(self):
        """Start background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        self._stats_task = asyncio.create_task(self._update_stats())
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
        
        logger.info("DecisionBroadcaster started with background tasks")
    
    async def stop(self):
        """Stop background tasks"""
        tasks = [self._cleanup_task, self._stats_task, self._heartbeat_task]
        
        for task in tasks:
            if task:
                task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("DecisionBroadcaster stopped")
    
    async def register_connection(self, 
                                connection_id: str,
                                client_type: ClientType,
                                websocket,
                                subscribed_channels: List[BroadcastChannel] = None,
                                metadata: Dict[str, Any] = None) -> ClientConnection:
        """Register a new client connection"""
        
        client = ClientConnection(
            connection_id=connection_id,
            client_type=client_type,
            subscribed_channels=subscribed_channels,
            metadata=metadata
        )
        client.set_websocket(websocket)
        
        self.connections[connection_id] = client
        
        # Update channel subscribers
        for channel in client.subscribed_channels:
            self.channel_subscribers[channel].add(connection_id)
        
        # Send welcome message
        welcome_message = BroadcastMessage(
            message_type="connection_established",
            channel=BroadcastChannel.SYSTEM_STATUS,
            data={
                "connection_id": connection_id,
                "client_type": client_type.value,
                "subscribed_channels": [c.value for c in client.subscribed_channels],
                "server_info": {
                    "active_connections": len(self.connections),
                    "available_channels": [c.value for c in BroadcastChannel],
                    "server_time": datetime.utcnow().isoformat()
                }
            }
        )
        
        await self._send_to_client(client, welcome_message)
        
        self.broadcast_stats["active_connections"] = len(self.connections)
        
        logger.info("Client connection registered",
                   connection_id=connection_id,
                   client_type=client_type.value,
                   total_connections=len(self.connections))
        
        return client
    
    async def unregister_connection(self, connection_id: str):
        """Unregister a client connection"""
        
        if connection_id not in self.connections:
            return
        
        client = self.connections[connection_id]
        
        # Remove from channel subscribers
        for channel in client.subscribed_channels:
            self.channel_subscribers[channel].discard(connection_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        self.broadcast_stats["active_connections"] = len(self.connections)
        
        logger.info("Client connection unregistered",
                   connection_id=connection_id,
                   client_type=client.client_type.value,
                   total_connections=len(self.connections))
    
    async def broadcast_message(self,
                              message_type: str,
                              channel: BroadcastChannel,
                              data: Dict[str, Any],
                              priority: int = 5,
                              target_clients: List[ClientType] = None,
                              expires_in_minutes: int = 30):
        """Broadcast message to subscribed clients"""
        
        # Check rate limits
        if not self._check_rate_limit(channel):
            logger.warning("Rate limit exceeded for channel", channel=channel.value)
            return
        
        message = BroadcastMessage(
            message_type=message_type,
            channel=channel,
            data=data,
            priority=priority,
            target_clients=target_clients,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        )
        
        # Add to history
        self.message_history.append(message)
        
        # Get target connections
        target_connections = self._get_target_connections(channel, target_clients)
        
        # Send to all target connections
        successful_deliveries = 0
        failed_deliveries = 0
        
        send_tasks = []
        for connection_id in target_connections:
            if connection_id in self.connections:
                client = self.connections[connection_id]
                send_tasks.append(self._send_to_client(client, message))
        
        # Execute sends concurrently
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, Exception):
                failed_deliveries += 1
            else:
                successful_deliveries += 1
        
        # Update stats
        self.broadcast_stats["total_messages"] += 1
        self.broadcast_stats["successful_deliveries"] += successful_deliveries
        self.broadcast_stats["failed_deliveries"] += failed_deliveries
        
        # Execute channel handlers
        await self._execute_handlers(channel, message)
        
        logger.debug("Message broadcast completed",
                    message_id=message.message_id,
                    channel=channel.value,
                    successful_deliveries=successful_deliveries,
                    failed_deliveries=failed_deliveries)
    
    async def broadcast_decision_event(self, event_type: str, decision: AgentDecision):
        """Broadcast agent decision event"""
        
        data = decision.to_display_format()
        data["event_type"] = event_type
        
        # Determine target clients based on decision type
        target_clients = [ClientType.EXECUTIVE_DASHBOARD, ClientType.OPERATIONS_CENTER]
        
        if decision.decision_type in [DecisionType.PASSENGER_REBOOKING, DecisionType.COMMUNICATION]:
            target_clients.append(ClientType.PASSENGER_PORTAL)
        
        await self.broadcast_message(
            message_type="decision_event",
            channel=BroadcastChannel.DECISIONS,
            data=data,
            priority=7,  # High priority for decisions
            target_clients=target_clients
        )
    
    async def broadcast_collaboration_event(self, event_type: str, collaboration: AgentCollaboration):
        """Broadcast agent collaboration event"""
        
        data = collaboration.to_display_format()
        data["event_type"] = event_type
        
        await self.broadcast_message(
            message_type="collaboration_event",
            channel=BroadcastChannel.COLLABORATIONS,
            data=data,
            priority=6,
            target_clients=[ClientType.EXECUTIVE_DASHBOARD, ClientType.OPERATIONS_CENTER]
        )
    
    async def broadcast_passenger_update(self, passenger_id: str, update_data: Dict[str, Any]):
        """Broadcast passenger-specific updates"""
        
        data = {
            "passenger_id": passenger_id,
            "update": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_message(
            message_type="passenger_update",
            channel=BroadcastChannel.PASSENGER_UPDATES,
            data=data,
            target_clients=[ClientType.PASSENGER_PORTAL, ClientType.OPERATIONS_CENTER]
        )
    
    async def broadcast_system_analytics(self, analytics: Dict[str, Any]):
        """Broadcast system analytics"""
        
        await self.broadcast_message(
            message_type="system_analytics",
            channel=BroadcastChannel.ANALYTICS,
            data=analytics,
            priority=3
        )
    
    async def broadcast_demo_control(self, control_type: str, control_data: Dict[str, Any]):
        """Broadcast demo control commands"""
        
        data = {
            "control_type": control_type,
            "control_data": control_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_message(
            message_type="demo_control",
            channel=BroadcastChannel.DEMO_CONTROLS,
            data=data,
            priority=8  # Highest priority for demo controls
        )
    
    def register_channel_handler(self, channel: BroadcastChannel, handler: Callable):
        """Register a handler for specific channel messages"""
        self.message_handlers[channel].append(handler)
        logger.info("Channel handler registered", channel=channel.value)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        
        # Connection stats by type
        connections_by_type = defaultdict(int)
        for client in self.connections.values():
            connections_by_type[client.client_type.value] += 1
        
        # Channel subscription stats
        channel_stats = {}
        for channel, subscribers in self.channel_subscribers.items():
            channel_stats[channel.value] = len(subscribers)
        
        return {
            "total_connections": len(self.connections),
            "active_connections": sum(1 for c in self.connections.values() if c.is_active),
            "connections_by_type": dict(connections_by_type),
            "channel_subscriptions": channel_stats,
            "broadcast_stats": self.broadcast_stats.copy(),
            "message_history_size": len(self.message_history),
            "rate_limits": {k.value: v for k, v in self.rate_limits.items()},
            "recent_activity": self._get_recent_activity()
        }
    
    def get_client_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about specific client"""
        
        if connection_id not in self.connections:
            return None
        
        return self.connections[connection_id].get_connection_info()
    
    async def update_client_subscription(self, connection_id: str, channels: List[BroadcastChannel]):
        """Update client channel subscriptions"""
        
        if connection_id not in self.connections:
            logger.warning("Attempt to update subscription for unknown client", 
                          connection_id=connection_id)
            return
        
        client = self.connections[connection_id]
        
        # Remove from old channels
        for channel in client.subscribed_channels:
            self.channel_subscribers[channel].discard(connection_id)
        
        # Update subscription
        client.update_subscription(channels)
        
        # Add to new channels
        for channel in channels:
            self.channel_subscribers[channel].add(connection_id)
    
    # Private methods
    
    def _get_target_connections(self, channel: BroadcastChannel, target_clients: List[ClientType] = None) -> Set[str]:
        """Get connections that should receive the message"""
        
        # Start with channel subscribers
        target_connections = self.channel_subscribers[channel].copy()
        target_connections.update(self.channel_subscribers[BroadcastChannel.ALL])
        
        # Filter by client type if specified
        if target_clients:
            filtered_connections = set()
            for conn_id in target_connections:
                if conn_id in self.connections:
                    client = self.connections[conn_id]
                    if client.client_type in target_clients:
                        filtered_connections.add(conn_id)
            target_connections = filtered_connections
        
        return target_connections
    
    async def _send_to_client(self, client: ClientConnection, message: BroadcastMessage) -> bool:
        """Send message to specific client"""
        
        try:
            # Check if client should receive this message
            if not client.is_subscribed_to(message.channel):
                return True
            
            if not message.is_targeted_to(client.client_type):
                return True
            
            # Get WebSocket connection
            websocket = client.get_websocket()
            if not websocket:
                client.is_active = False
                return False
            
            # Send message
            message_json = json.dumps(message.to_dict())
            await websocket.send_text(message_json)
            
            # Update client stats
            client.total_messages_sent += 1
            client.last_ping = datetime.utcnow()
            message.delivery_count += 1
            
            return True
            
        except Exception as e:
            logger.error("Failed to send message to client",
                        connection_id=client.connection_id,
                        error=str(e))
            
            client.failed_messages += 1
            message.failed_deliveries += 1
            
            # Queue message for retry if connection is still considered active
            if client.is_active:
                client.queue_message(message)
            
            return False
    
    def _check_rate_limit(self, channel: BroadcastChannel) -> bool:
        """Check if channel is within rate limits"""
        
        now = datetime.utcnow()
        
        # Reset counters if needed (every minute)
        if (now - self.last_rate_reset).total_seconds() >= 60:
            self.rate_counters.clear()
            self.last_rate_reset = now
        
        # Check specific channel limit
        limit = self.rate_limits.get(channel, 50)
        current_count = self.rate_counters[channel]
        
        if current_count >= limit:
            return False
        
        self.rate_counters[channel] += 1
        return True
    
    async def _execute_handlers(self, channel: BroadcastChannel, message: BroadcastMessage):
        """Execute registered handlers for channel"""
        
        handlers = self.message_handlers.get(channel, [])
        
        if not handlers:
            return
        
        handler_tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    handler_tasks.append(handler(message))
                else:
                    # Run sync handlers in thread pool
                    handler_tasks.append(asyncio.get_event_loop().run_in_executor(None, handler, message))
            except Exception as e:
                logger.error("Error preparing handler execution", handler=str(handler), error=str(e))
        
        if handler_tasks:
            await asyncio.gather(*handler_tasks, return_exceptions=True)
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent message activity"""
        
        recent_messages = list(self.message_history)[-10:]  # Last 10 messages
        
        return [
            {
                "message_id": msg.message_id,
                "type": msg.message_type,
                "channel": msg.channel.value,
                "timestamp": msg.created_at.isoformat(),
                "delivery_count": msg.delivery_count,
                "failed_deliveries": msg.failed_deliveries
            }
            for msg in recent_messages
        ]
    
    # Background tasks
    
    async def _cleanup_expired_messages(self):
        """Clean up expired messages and inactive connections"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                now = datetime.utcnow()
                
                # Clean expired messages from history
                self.message_history = deque(
                    (msg for msg in self.message_history if not msg.is_expired()),
                    maxlen=1000
                )
                
                # Clean inactive connections
                inactive_connections = []
                for conn_id, client in self.connections.items():
                    # Mark as inactive if no ping for 5 minutes
                    if (now - client.last_ping).total_seconds() > 300:
                        client.is_active = False
                        inactive_connections.append(conn_id)
                
                # Remove inactive connections
                for conn_id in inactive_connections:
                    await self.unregister_connection(conn_id)
                
                logger.debug("Cleanup completed",
                           expired_messages_removed=len(self.message_history),
                           inactive_connections_removed=len(inactive_connections))
                
            except Exception as e:
                logger.error("Error in cleanup task", error=str(e))
    
    async def _update_stats(self):
        """Update broadcast statistics"""
        
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Calculate messages per minute
                recent_messages = [
                    msg for msg in self.message_history 
                    if (datetime.utcnow() - msg.created_at).total_seconds() <= 60
                ]
                
                self.broadcast_stats["messages_per_minute"] = len(recent_messages)
                self.broadcast_stats["active_connections"] = len([
                    c for c in self.connections.values() if c.is_active
                ])
                
            except Exception as e:
                logger.error("Error in stats update task", error=str(e))
    
    async def _send_heartbeats(self):
        """Send periodic heartbeat messages"""
        
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                heartbeat_data = {
                    "server_time": datetime.utcnow().isoformat(),
                    "active_connections": len([c for c in self.connections.values() if c.is_active]),
                    "server_status": "healthy"
                }
                
                await self.broadcast_message(
                    message_type="heartbeat",
                    channel=BroadcastChannel.SYSTEM_STATUS,
                    data=heartbeat_data,
                    priority=1  # Low priority
                )
                
            except Exception as e:
                logger.error("Error in heartbeat task", error=str(e))


# Global broadcaster instance
decision_broadcaster = DecisionBroadcaster()

# Convenience functions
async def broadcast_decision(event_type: str, decision: AgentDecision):
    """Convenience function to broadcast decision"""
    await decision_broadcaster.broadcast_decision_event(event_type, decision)

async def broadcast_collaboration(event_type: str, collaboration: AgentCollaboration):
    """Convenience function to broadcast collaboration"""
    await decision_broadcaster.broadcast_collaboration_event(event_type, collaboration)

async def broadcast_analytics(analytics: Dict[str, Any]):
    """Convenience function to broadcast analytics"""
    await decision_broadcaster.broadcast_system_analytics(analytics)