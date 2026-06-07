"""
State Manager for Promptoire

Manages application runtime state including UI state, user preferences,
and temporary data that needs to be persisted across sessions.
"""

import json
import copy
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
from datetime import datetime
from collections import deque


class StateManager:
    """Manages application runtime state with persistence capabilities."""

    def __init__(self, state_file: str = "state.json"):
        """
        Initialize the state manager.

        Args:
            state_file: Path to the state JSON file
        """
        self.state_file = Path(state_file)
        self.state = {}
        self._dirty = set()  # Track which sections have been modified

    def initialize_state(self) -> None:
        """Initialize state with default values."""
        self.state = {
            "ui_state": {
                "collapsed_categories": set(),
                "expanded_paths": [],
                "selected_category": None,
                "drawer_open": False,
                "window_focused": False
            },
            "user_data": {
                "favorites": [],
                "recent_prompts": deque(maxlen=20),
                "usage_statistics": {
                    "total_uses": 0,
                    "category_counts": {},
                    "last_used": None
                }
            },
            "session_state": {
                "current_prompt": None,
                "search_query": "",
                "search_filters": {},
                "clipboard_history": deque(maxlen=10),
                "last_categories": []
            },
            "temporary_state": {
                "notifications": [],
                "pending_operations": [],
                "cache_data": {},
                "last_backup": None
            }
        }

    def load_state(self) -> bool:
        """
        Load state from file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)

                # Convert lists back to appropriate types
                self._convert_loaded_state(loaded_state)
                self.state = loaded_state
                return True
            else:
                self.initialize_state()
                return True

        except Exception as e:
            print(f"Error loading state: {e}")
            self.initialize_state()
            return False

    def save_state(self) -> bool:
        """
        Save state to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert non-serializable types
            serializable_state = self._prepare_for_serialization()

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)

            self._dirty.clear()
            return True

        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def get_ui_state(self, key: str, default: Any = None) -> Any:
        """Get UI state value."""
        return self.state.get("ui_state", {}).get(key, default)

    def set_ui_state(self, key: str, value: Any) -> None:
        """Set UI state value."""
        if "ui_state" not in self.state:
            self.state["ui_state"] = {}
        self.state["ui_state"][key] = value
        self._dirty.add("ui_state")

    def get_user_data(self, key: str, default: Any = None) -> Any:
        """Get user data value."""
        return self.state.get("user_data", {}).get(key, default)

    def set_user_data(self, key: str, value: Any) -> None:
        """Set user data value."""
        if "user_data" not in self.state:
            self.state["user_data"] = {}
        self.state["user_data"][key] = value
        self._dirty.add("user_data")

    def get_session_state(self, key: str, default: Any = None) -> Any:
        """Get session state value."""
        return self.state.get("session_state", {}).get(key, default)

    def set_session_state(self, key: str, value: Any) -> None:
        """Set session state value."""
        if "session_state" not in self.state:
            self.state["session_state"] = {}
        self.state["session_state"][key] = value
        self._dirty.add("session_state")

    def add_favorite(self, prompt_id: str) -> None:
        """Add a prompt to favorites."""
        favorites = self.get_user_data("favorites", [])
        if prompt_id not in favorites:
            favorites.append(prompt_id)
            self.set_user_data("favorites", favorites)

    def remove_favorite(self, prompt_id: str) -> None:
        """Remove a prompt from favorites."""
        favorites = self.get_user_data("favorites", [])
        if prompt_id in favorites:
            favorites.remove(prompt_id)
            self.set_user_data("favorites", favorites)

    def is_favorite(self, prompt_id: str) -> bool:
        """Check if a prompt is in favorites."""
        favorites = self.get_user_data("favorites", [])
        return prompt_id in favorites

    def add_recent_prompt(self, prompt_id: str) -> None:
        """Add a prompt to recent history."""
        recent_prompts = self.get_user_data("recent_prompts", [])

        # Convert to deque if it's a list
        if isinstance(recent_prompts, list):
            recent_prompts = deque(recent_prompts, maxlen=20)

        # Remove if already present and add to front
        if prompt_id in recent_prompts:
            recent_prompts.remove(prompt_id)
        recent_prompts.appendleft(prompt_id)

        self.set_user_data("recent_prompts", list(recent_prompts))

    def get_recent_prompts(self, limit: int = 10) -> List[str]:
        """Get recent prompts."""
        recent_prompts = self.get_user_data("recent_prompts", [])
        return recent_prompts[:limit]

    def add_collapsed_category(self, category_path: str) -> None:
        """Add a category to collapsed categories."""
        collapsed = self.get_ui_state("collapsed_categories", set())
        if isinstance(collapsed, list):
            collapsed = set(collapsed)
        collapsed.add(category_path)
        self.set_ui_state("collapsed_categories", collapsed)

    def remove_collapsed_category(self, category_path: str) -> None:
        """Remove a category from collapsed categories."""
        collapsed = self.get_ui_state("collapsed_categories", set())
        if isinstance(collapsed, list):
            collapsed = set(collapsed)
        collapsed.discard(category_path)
        self.set_ui_state("collapsed_categories", collapsed)

    def is_category_collapsed(self, category_path: str) -> bool:
        """Check if a category is collapsed."""
        collapsed = self.get_ui_state("collapsed_categories", set())
        if isinstance(collapsed, list):
            collapsed = set(collapsed)
        return category_path in collapsed

    def add_expanded_path(self, path: str) -> None:
        """Add an expanded path for the editor."""
        expanded = self.get_ui_state("expanded_paths", [])
        if path not in expanded:
            expanded.append(path)
            self.set_ui_state("expanded_paths", expanded)

    def remove_expanded_path(self, path: str) -> None:
        """Remove an expanded path from the editor."""
        expanded = self.get_ui_state("expanded_paths", [])
        if path in expanded:
            expanded.remove(path)
            self.set_ui_state("expanded_paths", expanded)

    def record_usage(self, category: str = None, prompt_id: str = None) -> None:
        """Record usage statistics."""
        stats = self.get_user_data("usage_statistics", {
            "total_uses": 0,
            "category_counts": {},
            "last_used": None
        })

        stats["total_uses"] += 1
        stats["last_used"] = datetime.now().isoformat()

        if category:
            stats["category_counts"][category] = stats["category_counts"].get(category, 0) + 1

        self.set_user_data("usage_statistics", stats)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self.get_user_data("usage_statistics", {})

    def add_notification(self, message: str, level: str = "info",
                        timestamp: str = None) -> None:
        """Add a notification to temporary state."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        notifications = self.state.get("temporary_state", {}).get("notifications", [])
        notifications.append({
            "message": message,
            "level": level,
            "timestamp": timestamp
        })

        # Keep only last 50 notifications
        notifications = notifications[-50:]

        if "temporary_state" not in self.state:
            self.state["temporary_state"] = {}
        self.state["temporary_state"]["notifications"] = notifications
        self._dirty.add("temporary_state")

    def get_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent notifications."""
        notifications = self.state.get("temporary_state", {}).get("notifications", [])
        return notifications[-limit:]

    def clear_notifications(self) -> None:
        """Clear all notifications."""
        if "temporary_state" not in self.state:
            self.state["temporary_state"] = {}
        self.state["temporary_state"]["notifications"] = []
        self._dirty.add("temporary_state")

    def set_cache_data(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set cache data with TTL (time to live) in seconds."""
        if "temporary_state" not in self.state:
            self.state["temporary_state"] = {}

        cache = self.state["temporary_state"].get("cache_data", {})
        cache[key] = {
            "value": value,
            "expires": datetime.now().timestamp() + ttl
        }

        self.state["temporary_state"]["cache_data"] = cache
        self._dirty.add("temporary_state")

    def get_cache_data(self, key: str) -> Any:
        """Get cached data if not expired."""
        cache = self.state.get("temporary_state", {}).get("cache_data", {})

        if key in cache:
            entry = cache[key]
            if datetime.now().timestamp() < entry.get("expires", 0):
                return entry["value"]
            else:
                # Remove expired entry
                del cache[key]
                self.state["temporary_state"]["cache_data"] = cache
                self._dirty.add("temporary_state")

        return None

    def clear_cache(self) -> None:
        """Clear all cached data."""
        if "temporary_state" not in self.state:
            self.state["temporary_state"] = {}
        self.state["temporary_state"]["cache_data"] = {}
        self._dirty.add("temporary_state")

    def is_dirty(self) -> bool:
        """Check if state has been modified since last save."""
        return len(self._dirty) > 0

    def clear_dirty_flags(self) -> None:
        """Clear all dirty flags."""
        self._dirty.clear()

    def backup_state(self, backup_path: str = None) -> bool:
        """Create a backup of the current state."""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"state_backup_{timestamp}.json"

            backup_file = Path(backup_path)
            serializable_state = self._prepare_for_serialization()

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error backing up state: {e}")
            return False

    def restore_state(self, backup_path: str) -> bool:
        """Restore state from a backup file."""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"Backup file not found: {backup_path}")
                return False

            with open(backup_file, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)

            self._convert_loaded_state(loaded_state)
            self.state = loaded_state
            self._dirty.clear()

            return True

        except Exception as e:
            print(f"Error restoring state: {e}")
            return False

    def _convert_loaded_state(self, loaded_state: Dict[str, Any]) -> None:
        """Convert loaded state data to appropriate types."""
        # Convert collapsed_categories to set
        if "ui_state" in loaded_state:
            ui_state = loaded_state["ui_state"]
            if "collapsed_categories" in ui_state:
                if isinstance(ui_state["collapsed_categories"], list):
                    ui_state["collapsed_categories"] = set(ui_state["collapsed_categories"])

    def _prepare_for_serialization(self) -> Dict[str, Any]:
        """Prepare state for JSON serialization."""
        serializable = copy.deepcopy(self.state)

        # Convert sets to lists
        if "ui_state" in serializable:
            ui_state = serializable["ui_state"]
            if "collapsed_categories" in ui_state:
                if isinstance(ui_state["collapsed_categories"], set):
                    ui_state["collapsed_categories"] = list(ui_state["collapsed_categories"])

        # Convert deques to lists
        if "user_data" in serializable:
            user_data = serializable["user_data"]
            if "recent_prompts" in user_data:
                if hasattr(user_data["recent_prompts"], 'tolist'):
                    user_data["recent_prompts"] = list(user_data["recent_prompts"])

        if "session_state" in serializable:
            session_state = serializable["session_state"]
            for key in ["clipboard_history"]:
                if key in session_state and hasattr(session_state[key], 'tolist'):
                    session_state[key] = list(session_state[key])

        return serializable