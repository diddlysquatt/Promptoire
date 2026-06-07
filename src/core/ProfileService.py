"""
ProfileService - Core profile management functionality

Handles multiple user profiles, profile switching, import/export,
and profile-specific settings management.
"""

import json
import copy
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Profile:
    """Profile configuration data structure"""
    name: str
    description: str = ""
    created_at: str = ""
    modified_at: str = ""
    is_active: bool = False
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "is_active": self.is_active,
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Create profile from dictionary"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            is_active=data.get("is_active", False),
            settings=data.get("settings", {})
        )


class ProfileService:
    """Core service for managing user profiles"""

    def __init__(self, profiles_dir: Union[str, Path] = "profiles"):
        """
        Initialize the profile service.

        Args:
            profiles_dir: Directory to store profile files
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.profiles_file = self.profiles_dir / "profiles.json"
        self.current_profile_file = self.profiles_dir / "current_profile.txt"

        # Ensure profiles structure exists
        self._ensure_profiles_structure()

    def create_profile(self, name: str, description: str = "",
                      base_settings: Optional[Dict[str, Any]] = None) -> Optional[Profile]:
        """
        Create a new profile.

        Args:
            name: Profile name
            description: Profile description
            base_settings: Base settings to copy from

        Returns:
            Created profile or None if failed
        """
        try:
            # Validate profile name
            if not name or not name.strip():
                print("Profile name cannot be empty")
                return None

            name = name.strip()

            # Check if profile already exists
            if self.profile_exists(name):
                print(f"Profile '{name}' already exists")
                return None

            # Create new profile
            profile = Profile(
                name=name,
                description=description,
                settings=copy.deepcopy(base_settings) if base_settings else {}
            )

            # Save profile
            if self._save_profile(profile):
                print(f"Profile '{name}' created successfully")
                return profile
            else:
                print(f"Failed to create profile '{name}'")
                return None

        except Exception as e:
            print(f"Error creating profile: {e}")
            traceback.print_exc()
            return None

    def get_profile(self, name: str) -> Optional[Profile]:
        """
        Get a profile by name.

        Args:
            name: Profile name

        Returns:
            Profile or None if not found
        """
        try:
            profiles = self.load_all_profiles()
            return profiles.get(name)
        except Exception as e:
            print(f"Error getting profile '{name}': {e}")
            return None

    def load_all_profiles(self) -> Dict[str, Profile]:
        """
        Load all profiles from storage.

        Returns:
            Dictionary of profiles keyed by name
        """
        try:
            profiles = {}

            if self.profiles_file.exists():
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)

                for name, data in profiles_data.items():
                    profiles[name] = Profile.from_dict(data)

            return profiles

        except Exception as e:
            print(f"Error loading profiles: {e}")
            return {}

    def get_current_profile(self) -> Optional[Profile]:
        """
        Get the currently active profile.

        Returns:
            Current profile or None
        """
        try:
            if self.current_profile_file.exists():
                with open(self.current_profile_file, 'r', encoding='utf-8') as f:
                    profile_name = f.read().strip()

                if profile_name:
                    return self.get_profile(profile_name)

            return None

        except Exception as e:
            print(f"Error getting current profile: {e}")
            return None

    def switch_profile(self, name: str) -> bool:
        """
        Switch to a different profile.

        Args:
            name: Profile name to switch to

        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.get_profile(name)
            if not profile:
                print(f"Profile '{name}' not found")
                return False

            # Deactivate all profiles
            profiles = self.load_all_profiles()
            for p in profiles.values():
                p.is_active = False

            # Activate target profile
            profile.is_active = True
            profile.modified_at = datetime.now().isoformat()

            # Save changes
            profiles[name] = profile
            if self._save_all_profiles(profiles):
                # Update current profile file
                with open(self.current_profile_file, 'w', encoding='utf-8') as f:
                    f.write(name)

                print(f"Switched to profile '{name}'")
                return True
            else:
                print(f"Failed to switch to profile '{name}'")
                return False

        except Exception as e:
            print(f"Error switching profile: {e}")
            return False

    def update_profile(self, name: str, settings: Dict[str, Any]) -> bool:
        """
        Update profile settings.

        Args:
            name: Profile name
            settings: New settings to merge

        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.get_profile(name)
            if not profile:
                print(f"Profile '{name}' not found")
                return False

            # Update settings
            profile.settings.update(settings)
            profile.modified_at = datetime.now().isoformat()

            # Save profile
            if self._save_profile(profile):
                print(f"Profile '{name}' updated successfully")
                return True
            else:
                print(f"Failed to update profile '{name}'")
                return False

        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.

        Args:
            name: Profile name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if name == "Default":
                print("Cannot delete the default profile")
                return False

            profiles = self.load_all_profiles()
            if name not in profiles:
                print(f"Profile '{name}' not found")
                return False

            # Check if it's the current profile
            current = self.get_current_profile()
            if current and current.name == name:
                print("Cannot delete the currently active profile")
                return False

            # Delete profile
            del profiles[name]

            if self._save_all_profiles(profiles):
                print(f"Profile '{name}' deleted successfully")
                return True
            else:
                print(f"Failed to delete profile '{name}'")
                return False

        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False

    def export_profile(self, name: str, export_path: Union[str, Path]) -> bool:
        """
        Export a profile to a file.

        Args:
            name: Profile name to export
            export_path: Path to export file

        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.get_profile(name)
            if not profile:
                print(f"Profile '{name}' not found")
                return False

            export_path = Path(export_path)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"Profile '{name}' exported to {export_path}")
            return True

        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False

    def import_profile(self, import_path: Union[str, Path],
                      overwrite: bool = False) -> Optional[Profile]:
        """
        Import a profile from a file.

        Args:
            import_path: Path to import file
            overwrite: Whether to overwrite existing profile

        Returns:
            Imported profile or None if failed
        """
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                print(f"Import file not found: {import_path}")
                return None

            with open(import_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            profile = Profile.from_dict(profile_data)

            # Check if profile already exists
            if self.profile_exists(profile.name) and not overwrite:
                print(f"Profile '{profile.name}' already exists. Use overwrite=True to replace.")
                return None

            # Save imported profile
            if self._save_profile(profile):
                print(f"Profile '{profile.name}' imported successfully")
                return profile
            else:
                print(f"Failed to import profile '{profile.name}'")
                return None

        except Exception as e:
            print(f"Error importing profile: {e}")
            return None

    def profile_exists(self, name: str) -> bool:
        """
        Check if a profile exists.

        Args:
            name: Profile name

        Returns:
            True if profile exists, False otherwise
        """
        try:
            profiles = self.load_all_profiles()
            return name in profiles
        except Exception:
            return False

    def get_profile_list(self) -> List[str]:
        """
        Get list of all profile names.

        Returns:
            List of profile names
        """
        try:
            profiles = self.load_all_profiles()
            return list(profiles.keys())
        except Exception:
            return []

    def _save_profile(self, profile: Profile) -> bool:
        """Save a single profile to storage"""
        try:
            profiles = self.load_all_profiles()
            profiles[profile.name] = profile
            return self._save_all_profiles(profiles)
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    def _save_all_profiles(self, profiles: Dict[str, Profile]) -> bool:
        """Save all profiles to storage"""
        try:
            profiles_data = {}
            for name, profile in profiles.items():
                profiles_data[name] = profile.to_dict()

            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving all profiles: {e}")
            return False

    def _ensure_profiles_structure(self) -> None:
        """Ensure the profiles directory structure exists"""
        try:
            # Create profiles.json if it doesn't exist
            if not self.profiles_file.exists():
                # Create default profile
                default_profile = Profile(
                    name="Default",
                    description="Default profile with standard settings"
                )
                default_profile.is_active = True

                profiles = {"Default": default_profile}
                self._save_all_profiles(profiles)

                # Set as current profile
                with open(self.current_profile_file, 'w', encoding='utf-8') as f:
                    f.write("Default")

        except Exception as e:
            print(f"Error ensuring profiles structure: {e}")