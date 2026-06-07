"""
EventTypes - Type definitions for event-related data structures
"""

from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class EventType(Enum):
    """Types of events supported by the application"""
    PROMPT_USED = "prompt_used"
    PROMPT_CREATED = "prompt_created"
    PROMPT_UPDATED = "prompt_updated"
    PROMPT_DELETED = "prompt_deleted"
    CATEGORY_CREATED = "category_created"
    CATEGORY_UPDATED = "category_updated"
    CATEGORY_DELETED = "category_deleted"
    SETTINGS_CHANGED = "settings_changed"
    THEME_CHANGED = "theme_changed"
    WINDOW_MOVED = "window_moved"
    WINDOW_RESIZED = "window_resized"
    APPLICATION_STARTED = "application_started"
    APPLICATION_EXITED = "application_exited"
    IMPORT_COMPLETED = "import_completed"
    EXPORT_COMPLETED = "export_completed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    SYNC_COMPLETED = "sync_completed"
    ERROR_OCCURRED = "error_occurred"
    USER_ACTION = "user_action"


class EventSeverity(Enum):
    """Severity levels for events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class EventData:
    """Data associated with an event"""
    prompt_id: Optional[str] = None
    category_id: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "prompt_id": self.prompt_id,
            "category_id": self.category_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventData":
        """Create from dictionary representation"""
        return cls(
            prompt_id=data.get("prompt_id"),
            category_id=data.get("category_id"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            metadata=data.get("metadata")
        )


@dataclass
class Event:
    """Represents an application event"""
    id: str
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime
    message: str
    data: Optional[EventData] = None
    source: Optional[str] = None
    user_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "data": self.data.to_dict() if self.data else None,
            "source": self.source,
            "user_action": self.user_action
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dictionary representation"""
        return cls(
            id=data.get("id", ""),
            event_type=EventType(data.get("event_type", "info")),
            severity=EventSeverity(data.get("severity", "info")),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            message=data.get("message", ""),
            data=EventData.from_dict(data.get("data")) if data.get("data") else None,
            source=data.get("source"),
            user_action=data.get("user_action")
        )


@dataclass
class UserAction:
    """Represents a user action event"""
    action_type: str
    target: str
    parameters: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAction":
        """Create from dictionary representation"""
        return cls(
            action_type=data.get("action_type", ""),
            target=data.get("target", ""),
            parameters=data.get("parameters", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            user_id=data.get("user_id"),
            session_id=data.get("session_id")
        )


# Event handler function type
EventHandler = Callable[[Event], None]
ActionHandler = Callable[[UserAction], None]

# Type aliases for better readability
EventID = str
EventDict = Dict[str, Any]
ActionDict = Dict[str, Any]
EventHandlerDict = Dict[EventType, List[EventHandler]]


@dataclass
class EventLog:
    """Container for event log entries"""
    events: List[Event]
    max_entries: int = 1000
    auto_purge: bool = True

    def add_event(self, event: Event) -> None:
        """Add an event to the log"""
        self.events.append(event)
        if self.auto_purge and len(self.events) > self.max_entries:
            self.events = self.events[-self.max_entries:]

    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.event_type == event_type]

    def get_events_by_severity(self, severity: EventSeverity) -> List[Event]:
        """Get all events of a specific severity"""
        return [event for event in self.events if event.severity == severity]

    def get_events_since(self, timestamp: datetime) -> List[Event]:
        """Get all events since a specific timestamp"""
        return [event for event in self.events if event.timestamp >= timestamp]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "events": [event.to_dict() for event in self.events],
            "max_entries": self.max_entries,
            "auto_purge": self.auto_purge
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventLog":
        """Create from dictionary representation"""
        events = [Event.from_dict(event_data) for event_data in data.get("events", [])]
        return cls(
            events=events,
            max_entries=data.get("max_entries", 1000),
            auto_purge=data.get("auto_purge", True)
        )