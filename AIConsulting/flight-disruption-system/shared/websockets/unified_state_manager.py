"""
Unified State Management System

This module provides centralized state management across all interfaces,
ensuring consistent data flow and real-time synchronization of agent decisions,
passenger data, and system metrics.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
import structlog
from collections import defaultdict
import threading
from contextlib import asynccontextmanager

from .decision_broadcaster import decision_broadcaster, BroadcastChannel, ClientType
from ..models.decision_models import AgentDecision, AgentCollaboration, DecisionStream

logger = structlog.get_logger()


class StateScope(Enum):
    """Different scopes of application state"""
    GLOBAL = "global"              # System-wide state
    SCENARIO = "scenario"          # Scenario-specific state
    PASSENGER = "passenger"        # Passenger-specific state
    AGENT = "agent"               # Agent-specific state
    SESSION = "session"           # Session-specific state


class StateChangeType(Enum):
    """Types of state changes"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"
    RESET = "reset"


@dataclass
class StateChange:
    """Represents a state change event"""
    change_id: str
    scope: StateScope
    change_type: StateChangeType
    path: str  # Dot notation path like "passengers.123.status"
    old_value: Any
    new_value: Any
    timestamp: datetime
    source_client: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "scope": self.scope.value,
            "change_type": self.change_type.value,
            "path": self.path,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "source_client": self.source_client,
            "metadata": self.metadata
        }


class StateValidator:
    """Validates state changes before applying them"""
    
    @staticmethod
    def validate_passenger_update(path: str, new_value: Any) -> tuple[bool, Optional[str]]:
        """Validate passenger-related state changes"""
        
        if "passenger" not in path:
            return True, None
        
        # Validate passenger status changes
        if path.endswith(".status"):
            valid_statuses = ["active", "rebooked", "accommodated", "cancelled", "completed"]
            if new_value not in valid_statuses:
                return False, f"Invalid passenger status: {new_value}"
        
        # Validate passenger satisfaction scores
        if path.endswith(".satisfaction_score"):
            if not isinstance(new_value, (int, float)) or not 0 <= new_value <= 5:
                return False, "Satisfaction score must be between 0 and 5"
        
        return True, None
    
    @staticmethod
    def validate_decision_update(path: str, new_value: Any) -> tuple[bool, Optional[str]]:
        """Validate decision-related state changes"""
        
        if "decision" not in path:
            return True, None
        
        # Validate confidence scores
        if path.endswith(".confidence_score"):
            if not isinstance(new_value, (int, float)) or not 0 <= new_value <= 1:
                return False, "Confidence score must be between 0 and 1"
        
        # Validate execution status
        if path.endswith(".execution_status"):
            valid_statuses = ["pending", "executing", "completed", "failed", "cancelled"]
            if new_value not in valid_statuses:
                return False, f"Invalid execution status: {new_value}"
        
        return True, None
    
    @staticmethod
    def validate_system_metrics(path: str, new_value: Any) -> tuple[bool, Optional[str]]:
        """Validate system metrics changes"""
        
        if "metrics" not in path:
            return True, None
        
        # Validate numeric metrics
        numeric_paths = ["cost_savings", "passenger_count", "success_rate", "response_time"]
        if any(metric in path for metric in numeric_paths):
            if not isinstance(new_value, (int, float)):
                return False, f"Metric value must be numeric: {path}"
        
        return True, None


class UnifiedStateManager:
    """
    Centralized state management system that maintains consistency across
    all interfaces with real-time synchronization and change tracking
    """
    
    def __init__(self):
        self.state: Dict[str, Any] = {
            "global": {
                "system_status": "operational",
                "active_scenarios": {},
                "total_passengers": 0,
                "total_decisions": 0,
                "cost_savings": 0.0,
                "success_rate": 0.0,
                "last_updated": datetime.utcnow().isoformat()
            },
            "scenarios": {},
            "passengers": {},
            "agents": {},
            "sessions": {},
            "decisions": {},
            "collaborations": {},
            "analytics": {
                "real_time_metrics": {},
                "performance_trends": [],
                "agent_performance": {},
                "passenger_satisfaction": {}
            }
        }
        
        # Change tracking
        self.change_history: List[StateChange] = []
        self.change_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.validation_enabled = True
        
        # Concurrency control
        self._lock = threading.RLock()
        self._change_counter = 0
        
        # Snapshot management
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.max_snapshots = 10
        
        # Performance tracking
        self.performance_stats = {
            "total_changes": 0,
            "changes_per_minute": 0,
            "validation_failures": 0,
            "broadcast_failures": 0,
            "average_change_time": 0.0
        }
        
        logger.info("UnifiedStateManager initialized")
    
    async def initialize(self):
        """Initialize state manager with default data"""
        
        # Initialize with demo data
        await self.initialize_demo_data()
        
        # Create initial snapshot
        await self.create_snapshot("initial_state")
        
        logger.info("UnifiedStateManager initialized with demo data")
    
    async def get_state(self, 
                       scope: Union[StateScope, str] = None, 
                       path: str = None,
                       client_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get current state or specific state portion"""
        
        with self._lock:
            if scope is None:
                # Return full state
                return self._deep_copy(self.state)
            
            scope_key = scope.value if isinstance(scope, StateScope) else scope
            
            if scope_key not in self.state:
                return {}
            
            state_portion = self.state[scope_key]
            
            if path:
                # Navigate to specific path
                state_portion = self._get_nested_value(state_portion, path)
            
            # Apply client filters if specified
            if client_filter:
                state_portion = self._apply_client_filter(state_portion, client_filter)
            
            return self._deep_copy(state_portion)
    
    async def update_state(self,
                          scope: StateScope,
                          path: str,
                          new_value: Any,
                          source_client: str = None,
                          metadata: Dict[str, Any] = None,
                          broadcast: bool = True) -> bool:
        """Update state and broadcast changes"""
        
        start_time = datetime.utcnow()
        
        try:
            with self._lock:
                # Get current value
                current_state = self.state.get(scope.value, {})
                old_value = self._get_nested_value(current_state, path)
                
                # Validate change if validation is enabled
                if self.validation_enabled:
                    is_valid, error_msg = self._validate_change(path, new_value)
                    if not is_valid:
                        logger.warning("State validation failed", 
                                     path=path, error=error_msg)
                        self.performance_stats["validation_failures"] += 1
                        return False
                
                # Apply change
                self._set_nested_value(self.state[scope.value], path, new_value)
                
                # Create change record
                change_id = f"change_{self._change_counter}"
                self._change_counter += 1
                
                change = StateChange(
                    change_id=change_id,
                    scope=scope,
                    change_type=StateChangeType.UPDATE,
                    path=path,
                    old_value=old_value,
                    new_value=new_value,
                    timestamp=datetime.utcnow(),
                    source_client=source_client,
                    metadata=metadata or {}
                )
                
                # Add to history
                self.change_history.append(change)
                
                # Update global last_updated timestamp
                self.state["global"]["last_updated"] = datetime.utcnow().isoformat()
                
                # Update performance stats
                self.performance_stats["total_changes"] += 1
                change_time = (datetime.utcnow() - start_time).total_seconds()
                self.performance_stats["average_change_time"] = (
                    (self.performance_stats["average_change_time"] * (self.performance_stats["total_changes"] - 1) + change_time) /
                    self.performance_stats["total_changes"]
                )
            
            # Broadcast change if requested
            if broadcast:
                await self._broadcast_state_change(change)
            
            # Notify subscribers
            await self._notify_subscribers(change)
            
            logger.debug("State updated successfully",
                        scope=scope.value,
                        path=path,
                        change_id=change_id)
            
            return True
            
        except Exception as e:
            logger.error("Error updating state",
                        scope=scope.value if scope else "unknown",
                        path=path,
                        error=str(e))
            return False
    
    async def merge_state(self,
                         scope: StateScope,
                         state_data: Dict[str, Any],
                         source_client: str = None,
                         broadcast: bool = True) -> bool:
        """Merge state data into existing state"""
        
        try:
            with self._lock:
                old_state = self._deep_copy(self.state.get(scope.value, {}))
                
                # Merge state data
                self._deep_merge(self.state.setdefault(scope.value, {}), state_data)
                
                # Create change record
                change = StateChange(
                    change_id=f"merge_{self._change_counter}",
                    scope=scope,
                    change_type=StateChangeType.MERGE,
                    path="",
                    old_value=old_state,
                    new_value=state_data,
                    timestamp=datetime.utcnow(),
                    source_client=source_client
                )
                
                self._change_counter += 1
                self.change_history.append(change)
                self.performance_stats["total_changes"] += 1
            
            # Broadcast and notify
            if broadcast:
                await self._broadcast_state_change(change)
            await self._notify_subscribers(change)
            
            logger.info("State merged successfully",
                       scope=scope.value,
                       keys_merged=list(state_data.keys()))
            
            return True
            
        except Exception as e:
            logger.error("Error merging state", error=str(e))
            return False
    
    async def delete_state(self,
                          scope: StateScope,
                          path: str,
                          source_client: str = None,
                          broadcast: bool = True) -> bool:
        """Delete state at specific path"""
        
        try:
            with self._lock:
                current_state = self.state.get(scope.value, {})
                old_value = self._get_nested_value(current_state, path)
                
                if old_value is None:
                    return True  # Already doesn't exist
                
                # Delete the value
                self._delete_nested_value(self.state[scope.value], path)
                
                # Create change record
                change = StateChange(
                    change_id=f"delete_{self._change_counter}",
                    scope=scope,
                    change_type=StateChangeType.DELETE,
                    path=path,
                    old_value=old_value,
                    new_value=None,
                    timestamp=datetime.utcnow(),
                    source_client=source_client
                )
                
                self._change_counter += 1
                self.change_history.append(change)
                self.performance_stats["total_changes"] += 1
            
            # Broadcast and notify
            if broadcast:
                await self._broadcast_state_change(change)
            await self._notify_subscribers(change)
            
            logger.info("State deleted successfully", scope=scope.value, path=path)
            return True
            
        except Exception as e:
            logger.error("Error deleting state", error=str(e))
            return False
    
    async def create_snapshot(self, snapshot_name: str) -> bool:
        """Create a snapshot of current state"""
        
        try:
            with self._lock:
                # Remove oldest snapshot if at limit
                if len(self.snapshots) >= self.max_snapshots:
                    oldest_snapshot = min(self.snapshots.keys())
                    del self.snapshots[oldest_snapshot]
                
                # Create snapshot
                self.snapshots[snapshot_name] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "state": self._deep_copy(self.state)
                }
            
            logger.info("Snapshot created", name=snapshot_name)
            return True
            
        except Exception as e:
            logger.error("Error creating snapshot", error=str(e))
            return False
    
    async def restore_snapshot(self, snapshot_name: str, broadcast: bool = True) -> bool:
        """Restore state from snapshot"""
        
        try:
            if snapshot_name not in self.snapshots:
                logger.warning("Snapshot not found", name=snapshot_name)
                return False
            
            with self._lock:
                old_state = self._deep_copy(self.state)
                self.state = self._deep_copy(self.snapshots[snapshot_name]["state"])
                
                # Create change record
                change = StateChange(
                    change_id=f"restore_{self._change_counter}",
                    scope=StateScope.GLOBAL,
                    change_type=StateChangeType.RESET,
                    path="",
                    old_value=old_state,
                    new_value=self.state,
                    timestamp=datetime.utcnow(),
                    metadata={"snapshot_name": snapshot_name}
                )
                
                self._change_counter += 1
                self.change_history.append(change)
            
            # Broadcast full state reset
            if broadcast:
                await self._broadcast_state_change(change)
            await self._notify_subscribers(change)
            
            logger.info("Snapshot restored", name=snapshot_name)
            return True
            
        except Exception as e:
            logger.error("Error restoring snapshot", error=str(e))
            return False
    
    def subscribe_to_changes(self, 
                           pattern: str, 
                           callback: Callable[[StateChange], None]) -> str:
        """Subscribe to state changes matching pattern"""
        
        subscription_id = f"sub_{len(self.change_subscribers)}_{int(datetime.utcnow().timestamp())}"
        self.change_subscribers[pattern].append((subscription_id, callback))
        
        logger.info("Change subscription created", 
                   pattern=pattern, 
                   subscription_id=subscription_id)
        
        return subscription_id
    
    def unsubscribe_from_changes(self, subscription_id: str):
        """Unsubscribe from state changes"""
        
        for pattern, subscribers in self.change_subscribers.items():
            self.change_subscribers[pattern] = [
                (sub_id, callback) for sub_id, callback in subscribers 
                if sub_id != subscription_id
            ]
        
        logger.info("Change subscription removed", subscription_id=subscription_id)
    
    async def get_change_history(self, 
                               since: datetime = None,
                               scope: StateScope = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get change history with optional filters"""
        
        with self._lock:
            changes = self.change_history.copy()
        
        # Apply filters
        if since:
            changes = [c for c in changes if c.timestamp >= since]
        
        if scope:
            changes = [c for c in changes if c.scope == scope]
        
        # Sort by timestamp (newest first) and limit
        changes.sort(key=lambda c: c.timestamp, reverse=True)
        changes = changes[:limit]
        
        return [change.to_dict() for change in changes]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get state manager performance statistics"""
        
        # Calculate changes per minute
        now = datetime.utcnow()
        recent_changes = [
            c for c in self.change_history 
            if (now - c.timestamp).total_seconds() <= 60
        ]
        
        self.performance_stats["changes_per_minute"] = len(recent_changes)
        
        return {
            **self.performance_stats,
            "total_state_size": self._calculate_state_size(),
            "change_history_size": len(self.change_history),
            "active_subscriptions": sum(len(subs) for subs in self.change_subscribers.values()),
            "snapshots_count": len(self.snapshots)
        }
    
    # State-specific methods for common operations
    
    async def update_passenger_status(self, 
                                    passenger_id: str, 
                                    status: str,
                                    details: Dict[str, Any] = None):
        """Update passenger status with automatic state propagation"""
        
        # Update passenger state
        await self.update_state(
            StateScope.PASSENGER,
            f"{passenger_id}.status",
            status,
            metadata={"details": details or {}}
        )
        
        # Update global passenger count
        passengers = await self.get_state(StateScope.PASSENGER)
        active_count = len([p for p in passengers.values() if p.get("status") == "active"])
        
        await self.update_state(
            StateScope.GLOBAL,
            "total_passengers",
            active_count,
            broadcast=False  # Avoid double broadcast
        )
    
    async def add_decision(self, decision: AgentDecision):
        """Add new decision to state"""
        
        decision_data = decision.to_display_format()
        
        await self.update_state(
            StateScope.GLOBAL,
            f"decisions.{decision.decision_id}",
            decision_data
        )
        
        # Update decision count
        decisions = await self.get_state(StateScope.GLOBAL, "decisions")
        await self.update_state(
            StateScope.GLOBAL,
            "total_decisions",
            len(decisions),
            broadcast=False
        )
    
    async def add_collaboration(self, collaboration: AgentCollaboration):
        """Add collaboration to state"""
        
        collab_data = collaboration.to_display_format()
        
        await self.update_state(
            StateScope.GLOBAL,
            f"collaborations.{collaboration.collaboration_id}",
            collab_data
        )
    
    async def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system-wide metrics"""
        
        for key, value in metrics.items():
            await self.update_state(
                StateScope.GLOBAL,
                f"analytics.real_time_metrics.{key}",
                value,
                broadcast=False
            )
        
        # Single broadcast for all metrics
        await decision_broadcaster.broadcast_message(
            "system_metrics_updated",
            BroadcastChannel.ANALYTICS,
            {
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    # Private helper methods
    
    async def initialize_demo_data(self):
        """Initialize with demo data for demonstration purposes"""
        
        # Demo passengers
        demo_passengers = {
            "passenger_1": {
                "id": "passenger_1",
                "name": "Sarah Chen",
                "status": "active",
                "flight": "BA123",
                "satisfaction_score": 4.2,
                "rebooking_status": "in_progress"
            },
            "passenger_2": {
                "id": "passenger_2", 
                "name": "Johnson Family",
                "status": "accommodated",
                "flight": "EZY892",
                "satisfaction_score": 3.8,
                "rebooking_status": "completed"
            },
            "passenger_3": {
                "id": "passenger_3",
                "name": "Alex Rivera", 
                "status": "rebooked",
                "flight": "FR456",
                "satisfaction_score": 4.5,
                "rebooking_status": "completed"
            }
        }
        
        # Demo system metrics
        demo_metrics = {
            "cost_savings": 156300.0,
            "total_passengers": 3,
            "success_rate": 0.917,
            "average_resolution_time": 24.5,
            "passenger_satisfaction": 4.17
        }
        
        # Initialize state
        self.state["passengers"] = demo_passengers
        self.state["global"].update(demo_metrics)
        
        logger.info("Demo data initialized")
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        
        if not path:
            return data
        
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _delete_nested_value(self, data: Dict[str, Any], path: str):
        """Delete value from nested dictionary using dot notation"""
        
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                return  # Path doesn't exist
            current = current[key]
        
        if keys[-1] in current:
            del current[keys[-1]]
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy an object"""
        import copy
        return copy.deepcopy(obj)
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source into target"""
        
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _validate_change(self, path: str, new_value: Any) -> tuple[bool, Optional[str]]:
        """Validate a state change"""
        
        validators = [
            StateValidator.validate_passenger_update,
            StateValidator.validate_decision_update,
            StateValidator.validate_system_metrics
        ]
        
        for validator in validators:
            is_valid, error_msg = validator(path, new_value)
            if not is_valid:
                return False, error_msg
        
        return True, None
    
    def _apply_client_filter(self, data: Any, filter_spec: Dict[str, Any]) -> Any:
        """Apply client-specific filters to data"""
        
        # This would implement client-specific data filtering
        # For now, return data as-is
        return data
    
    async def _broadcast_state_change(self, change: StateChange):
        """Broadcast state change to connected clients"""
        
        try:
            # Determine appropriate broadcast channel based on scope
            channel_map = {
                StateScope.GLOBAL: BroadcastChannel.SYSTEM_STATUS,
                StateScope.PASSENGER: BroadcastChannel.PASSENGER_UPDATES,
                StateScope.AGENT: BroadcastChannel.DECISIONS,
                StateScope.SCENARIO: BroadcastChannel.DEMO_CONTROLS
            }
            
            channel = channel_map.get(change.scope, BroadcastChannel.ALL)
            
            await decision_broadcaster.broadcast_message(
                "state_change",
                channel,
                change.to_dict(),
                priority=6
            )
            
        except Exception as e:
            logger.error("Error broadcasting state change", error=str(e))
            self.performance_stats["broadcast_failures"] += 1
    
    async def _notify_subscribers(self, change: StateChange):
        """Notify change subscribers"""
        
        for pattern, subscribers in self.change_subscribers.items():
            if self._matches_pattern(change.path, pattern):
                for sub_id, callback in subscribers:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(change)
                        else:
                            callback(change)
                    except Exception as e:
                        logger.error("Error notifying subscriber",
                                   subscription_id=sub_id,
                                   error=str(e))
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches subscription pattern"""
        
        if pattern == "*":
            return True
        
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return path.startswith(prefix)
        
        return path == pattern
    
    def _calculate_state_size(self) -> int:
        """Calculate approximate state size in bytes"""
        import sys
        return sys.getsizeof(json.dumps(self.state, default=str))


# Global state manager instance
unified_state_manager = UnifiedStateManager()

# Convenience functions
async def get_global_state(path: str = None) -> Dict[str, Any]:
    """Get global state"""
    return await unified_state_manager.get_state(StateScope.GLOBAL, path)

async def update_global_state(path: str, value: Any, source: str = None) -> bool:
    """Update global state"""
    return await unified_state_manager.update_state(StateScope.GLOBAL, path, value, source)

async def get_passenger_state(passenger_id: str = None) -> Dict[str, Any]:
    """Get passenger state"""
    path = passenger_id if passenger_id else None
    return await unified_state_manager.get_state(StateScope.PASSENGER, path)

async def update_passenger_state(passenger_id: str, field: str, value: Any, source: str = None) -> bool:
    """Update passenger state"""
    path = f"{passenger_id}.{field}" if field else passenger_id
    return await unified_state_manager.update_state(StateScope.PASSENGER, path, value, source)