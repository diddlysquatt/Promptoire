"""
File Service - Handles all file operations for the Promptoire application
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union
import tkinter as tk
from tkinter import filedialog, messagebox
import logging

try:
    from src.utils.security import safe_open_file_location, validate_input, sanitize_filename, secure_file_operation
except ImportError:
    # Fallback implementations if security module is not available
    import platform
    import subprocess

    def safe_open_file_location(file_path):
        """Fallback implementation"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            parent_dir = path.parent
            if platform.system() == "Windows":
                os.startfile(parent_dir)
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(parent_dir)], check=True, timeout=10)
            else:
                subprocess.run(["xdg-open", str(parent_dir)], check=True, timeout=10)
            return True
        except:
            return False

    def validate_input(input_str, max_length=1000, allowed_chars=None):
        """Fallback implementation"""
        if not isinstance(input_str, str):
            return False
        if len(input_str) > max_length or len(input_str) == 0:
            return False
        return True

    def sanitize_filename(filename):
        """Fallback implementation"""
        if not isinstance(filename, str):
            return "invalid"
        import re
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        sanitized = sanitized.strip(' .')
        if not sanitized:
            sanitized = "unnamed"
        return sanitized

    def secure_file_operation(file_path, operation, **kwargs):
        """Fallback implementation"""
        try:
            path = Path(file_path)
            if operation == 'exists':
                return path.exists()
            elif operation == 'mkdir':
                path.mkdir(parents=True, exist_ok=True)
                return True
            return False
        except:
            return False


class FileService:
    """Service class for handling file operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def read_json_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Safely read a JSON file"""
        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, Exception) as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            return None

    def write_json_file(self, file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """Safely write data to a JSON file using atomic write pattern"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=os.path.dirname(file_path),
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_path = tmp_file.name

            # Atomic rename
            shutil.move(tmp_path, file_path)
            return True

        except (IOError, OSError, Exception) as e:
            self.logger.error(f"Error writing JSON file {file_path}: {e}")
            # Clean up temporary file if it exists
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return False

    def open_file_dialog(self, title: str = "Open File", filetypes: list = None) -> Optional[str]:
        """Open a file dialog and return the selected file path"""
        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes or [("All files", "*.*")]
            )
            return file_path if file_path else None
        except Exception as e:
            self.logger.error(f"Error in open file dialog: {e}")
            return None

    def save_file_dialog(self, title: str = "Save File", defaultextension: str = "",
                        filetypes: list = None, initialfile: str = "") -> Optional[str]:
        """Open a save file dialog and return the selected file path"""
        try:
            file_path = filedialog.asksaveasfilename(
                title=title,
                defaultextension=defaultextension,
                filetypes=filetypes or [("All files", "*.*")],
                initialfile=initialfile
            )
            return file_path if file_path else None
        except Exception as e:
            self.logger.error(f"Error in save file dialog: {e}")
            return None

    def read_text_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text content from a file"""
        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, UnicodeDecodeError, Exception) as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")
            return None

    def write_text_file(self, file_path: Union[str, Path], content: str) -> bool:
        """Write text content to a file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            return True

        except (IOError, OSError, Exception) as e:
            self.logger.error(f"Error writing text file {file_path}: {e}")
            return False

    def backup_file(self, file_path: Union[str, Path], backup_dir: Union[str, Path] = None) -> bool:
        """Create a backup of a file"""
        try:
            if not os.path.exists(file_path):
                return True  # Nothing to backup

            source_path = Path(file_path)

            if backup_dir is None:
                backup_dir = source_path.parent / "backups"
            else:
                backup_dir = Path(backup_dir)

            # Create backup directory if it doesn't exist
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_filename

            # Copy file to backup location
            shutil.copy2(source_path, backup_path)
            return True

        except (IOError, OSError, Exception) as e:
            self.logger.error(f"Error creating backup of {file_path}: {e}")
            return False

    def open_file_location(self, file_path: Union[str, Path]) -> bool:
        """Open the file location in the system file manager"""
        return safe_open_file_location(file_path)

    def ensure_directory_exists(self, directory_path: Union[str, Path]) -> bool:
        """Ensure a directory exists, creating it if necessary"""
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, Exception) as e:
            self.logger.error(f"Error creating directory {directory_path}: {e}")
            return False

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists"""
        try:
            return os.path.exists(file_path)
        except Exception as e:
            self.logger.error(f"Error checking if file exists {file_path}: {e}")
            return False

    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get the size of a file in bytes"""
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
        except Exception as e:
            self.logger.error(f"Error getting file size {file_path}: {e}")
            return 0

    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete a file safely"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            return True
        except (OSError, Exception) as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False