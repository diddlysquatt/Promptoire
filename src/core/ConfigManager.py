"""
Configuration Manager for Promptoire

Centralized settings management with atomic file operations,
validation, and error handling.
"""

import json
import copy
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime


class ConfigManager:
    """Manages application configuration with atomic operations and validation."""

    def __init__(self, settings_file: Union[str, Path] = "settings.json"):
        """
        Initialize the configuration manager.

        Args:
            settings_file: Path to the settings JSON file
        """
        self.settings_file = Path(settings_file)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def load_settings(self, default_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load settings from file with fallback to defaults.

        Args:
            default_settings: Default settings configuration

        Returns:
            Merged settings dictionary
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to fill any missing keys
                    settings = self._merge_settings(default_settings, loaded)

                    # Remove deprecated keys
                    settings = self._clean_deprecated_keys(settings)

                    # Validate and fix settings structure
                    settings = self._validate_and_fix_settings(settings, default_settings)

                    return settings
            else:
                # Create new settings file with defaults
                self.save_settings(default_settings)
                return copy.deepcopy(default_settings)

        except Exception as e:
            print(f"Error loading settings: {e}")
            traceback.print_exc()
            return copy.deepcopy(default_settings)

    def save_settings(self, settings: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        Save settings to file atomically.

        Args:
            settings: Settings dictionary to save
            create_backup: Whether to create a backup before saving

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if create_backup and self.settings_file.exists():
                self._create_backup()

            # Atomic write using temporary file
            tmp_file = self.settings_file.with_suffix('.tmp')

            # Validate settings before saving
            validated_settings = self._validate_settings(settings)

            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=2, ensure_ascii=False)

            # Atomic replace
            tmp_file.replace(self.settings_file)
            return True

        except Exception as e:
            print(f"Error saving settings: {e}")
            traceback.print_exc()
            return False

    def get_setting(self, settings: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get a nested setting value using dot notation.

        Args:
            settings: Settings dictionary
            key_path: Dot-separated path to the setting (e.g., 'theme.background')
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        try:
            keys = key_path.split('.')
            value = settings

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception:
            return default

    def set_setting(self, settings: Dict[str, Any], key_path: str, value: Any) -> Dict[str, Any]:
        """
        Set a nested setting value using dot notation.

        Args:
            settings: Settings dictionary to modify
            key_path: Dot-separated path to the setting
            value: New value to set

        Returns:
            Modified settings dictionary
        """
        try:
            keys = key_path.split('.')
            current = settings

            # Navigate to parent of target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the final value
            current[keys[-1]] = value

            return settings

        except Exception as e:
            print(f"Error setting {key_path}: {e}")
            return settings

    def reset_to_defaults(self, default_settings: Dict[str, Any],
                         preserve_keys: Optional[list] = None) -> Dict[str, Any]:
        """
        Reset settings to defaults while preserving specified keys.

        Args:
            default_settings: Default settings configuration
            preserve_keys: List of key paths to preserve (dot notation)

        Returns:
            Reset settings dictionary
        """
        try:
            # Load current settings
            current_settings = self.load_settings(default_settings)

            # Start with fresh defaults
            new_settings = copy.deepcopy(default_settings)

            # Preserve specified keys
            if preserve_keys:
                for key_path in preserve_keys:
                    value = self.get_setting(current_settings, key_path)
                    if value is not None:
                        new_settings = self.set_setting(new_settings, key_path, value)

            # Save the reset settings
            self.save_settings(new_settings)

            return new_settings

        except Exception as e:
            print(f"Error resetting settings: {e}")
            return current_settings

    def _merge_settings(self, defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded settings on top of defaults."""
        try:
            if not isinstance(defaults, dict):
                return copy.deepcopy(loaded) if loaded is not None else copy.deepcopy(defaults)

            result = copy.deepcopy(defaults)

            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if key in defaults and isinstance(defaults.get(key), dict) and isinstance(value, dict):
                        result[key] = self._merge_settings(defaults[key], value)
                    else:
                        result[key] = value

            return result

        except Exception:
            # Fallback to loaded or defaults
            return copy.deepcopy(loaded) if isinstance(loaded, dict) else copy.deepcopy(defaults)

    def _clean_deprecated_keys(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Remove deprecated configuration keys."""
        try:
            # Remove deprecated gradient/pattern keys from theme
            theme = settings.get("theme", {})
            deprecated_keys = [
                "gradient_type", "gradient_start", "gradient_end",
                "pattern_type", "pattern_color", "pattern_opacity"
            ]

            for key in deprecated_keys:
                theme.pop(key, None)

            settings["theme"] = theme
            return settings

        except Exception:
            return settings

    def _validate_and_fix_settings(self, settings: Dict[str, Any],
                                 defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings structure and fix common issues."""
        try:
            # Ensure essential sections exist
            essential_sections = ["position", "theme", "visual", "font"]
            for section in essential_sections:
                if section not in settings:
                    settings[section] = copy.deepcopy(defaults.get(section, {}))

            # Ensure support link is populated
            if not settings.get("coffee_url", "").strip():
                settings["coffee_url"] = defaults.get("coffee_url", "")

            # Fix numeric ranges
            settings["opacity"] = max(0.1, min(1.0, float(settings.get("opacity", 0.95))))
            settings["bar_scale"] = max(0.8, min(2.0, float(settings.get("bar_scale", 1.0))))
            settings["font_scale"] = max(0.5, min(3.0, float(settings.get("font_scale", 1.0))))

            return settings

        except Exception:
            return settings

    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings before saving."""
        # Create a copy to avoid modifying the original
        validated = copy.deepcopy(settings)

        # Ensure all values are JSON serializable
        try:
            json.dumps(validated)
        except (TypeError, ValueError) as e:
            print(f"Settings contain non-serializable values: {e}")
            # Fall back to a minimal valid settings structure
            return self._get_minimal_settings()

        return validated

    def _get_minimal_settings(self) -> Dict[str, Any]:
        """Get a minimal valid settings structure."""
        return {
            "position": {"x": 100, "y": 100},
            "theme": {
                "background": "#0f0f23",
                "foreground": "#ffffff"
            },
            "opacity": 0.95
        }

    def _create_backup(self) -> bool:
        """Create a timestamped backup of the current settings."""
        try:
            if not self.settings_file.exists():
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"settings_{timestamp}.json"

            # Copy current settings to backup
            import shutil
            shutil.copy2(self.settings_file, backup_file)

            # Clean old backups (keep last 10)
            self._cleanup_old_backups()

            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = list(self.backup_dir.glob("settings_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the 10 most recent backups
            for old_backup in backup_files[10:]:
                old_backup.unlink()

        except Exception:
            pass

    def export_settings(self, settings: Dict[str, Any], export_path: Union[str, Path]) -> bool:
        """Export settings to a specified file."""
        try:
            export_path = Path(export_path)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, import_path: Union[str, Path],
                       default_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Import settings from a specified file."""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                print(f"Import file not found: {import_path}")
                return None

            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)

            # Validate and merge with defaults
            merged_settings = self._merge_settings(default_settings, imported_settings)
            validated_settings = self._validate_and_fix_settings(merged_settings, default_settings)

            return validated_settings

        except Exception as e:
            print(f"Error importing settings: {e}")
            return None