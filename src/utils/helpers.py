"""
Helper Utilities for Promptoire
General utility functions and helper classes
"""

import json
import os
import shutil
import time
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from ..constants import (
    BASE_DIR,
    DEFAULT_ENCODING,
    BACKUP_PREFIX,
    BACKUP_DATE_FORMAT,
    TEMPLATE_PLACEHOLDER_START,
    TEMPLATE_PLACEHOLDER_END,
    LOG_FORMAT,
    AGENT_STATUS_COMPLETED
)
from ..validators import (
    ValidationResult,
    validate_file_path,
    validate_json_data,
    validate_template_variables,
    ValidationError
)


class FileManager:
    """File management utilities"""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """Ensure directory exists"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def safe_read_json(file_path: Union[str, Path]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Safely read JSON file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, None, f"File not found: {path}"

            with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
                data = json.load(f)
            return True, data, "Success"
        except json.JSONDecodeError as e:
            return False, None, f"JSON decode error: {str(e)}"
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"

    @staticmethod
    def safe_write_json(file_path: Union[str, Path], data: Dict[str, Any]) -> Tuple[bool, str]:
        """Safely write JSON file"""
        try:
            path = Path(file_path)
            FileManager.ensure_directory(path.parent)

            validation_result = validate_json_data(data)
            if not validation_result.is_valid:
                return False, f"Invalid JSON data: {validation_result.message}"

            with open(path, 'w', encoding=DEFAULT_ENCODING) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True, "Success"
        except Exception as e:
            return False, f"Error writing file: {str(e)}"

    @staticmethod
    def create_backup(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Tuple[bool, Optional[Path], str]:
        """Create backup of a file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False, None, f"Source file not found: {source_path}"

            if backup_dir:
                backup_path = Path(backup_dir)
                FileManager.ensure_directory(backup_path)
            else:
                backup_path = source_path.parent

            timestamp = datetime.now().strftime(BACKUP_DATE_FORMAT)
            backup_name = f"{BACKUP_PREFIX}{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_name

            shutil.copy2(source_path, backup_file_path)
            return True, backup_file_path, "Backup created successfully"
        except Exception as e:
            return False, None, f"Error creating backup: {str(e)}"

    @staticmethod
    def get_file_hash(file_path: Union[str, Path]) -> Tuple[bool, Optional[str], str]:
        """Get file hash for integrity checking"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, None, f"File not found: {path}"

            hash_sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return True, hash_sha256.hexdigest(), "Success"
        except Exception as e:
            return False, None, f"Error calculating hash: {str(e)}"


class TemplateProcessor:
    """Template processing utilities"""

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """Extract variable names from template"""
        import re
        pattern = rf'\{re.escape(TEMPLATE_PLACEHOLDER_START)}(\w+)\{re.escape(TEMPLATE_PLACEHOLDER_END)}'
        return re.findall(pattern, template)

    @staticmethod
    def process_template(template: str, variables: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Process template with variables"""
        try:
            validation_result = validate_template_variables(template, variables)
            if not validation_result.is_valid:
                return False, "", validation_result.message

            result = template
            for var_name, var_value in variables.items():
                placeholder = f"{TEMPLATE_PLACEHOLDER_START}{var_name}{TEMPLATE_PLACEHOLDER_END}"
                result = result.replace(placeholder, str(var_value))

            return True, result, "Template processed successfully"
        except Exception as e:
            return False, "", f"Error processing template: {str(e)}"

    @staticmethod
    def create_template_variables(variable_names: List[str], values: List[Any]) -> Dict[str, Any]:
        """Create variable dictionary from names and values"""
        if len(variable_names) != len(values):
            raise ValueError("Number of variable names must match number of values")

        return dict(zip(variable_names, values))


class Logger:
    """Simple logging utility"""

    def __init__(self, name: str, log_file: Optional[Union[str, Path]] = None):
        self.name = name
        self.log_file = log_file

    def _format_message(self, level: str, message: str) -> str:
        """Format log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} - {self.name} - {level.upper()} - {message}"

    def _write_log(self, level: str, message: str):
        """Write log message"""
        formatted_message = self._format_message(level, message)
        print(formatted_message)

        if self.log_file:
            try:
                log_path = Path(self.log_file)
                FileManager.ensure_directory(log_path.parent)
                with open(log_path, 'a', encoding=DEFAULT_ENCODING) as f:
                    f.write(formatted_message + '\n')
            except Exception:
                pass  # Fail silently if log writing fails

    def info(self, message: str):
        """Log info message"""
        self._write_log("info", message)

    def warning(self, message: str):
        """Log warning message"""
        self._write_log("warning", message)

    def error(self, message: str):
        """Log error message"""
        self._write_log("error", message)

    def debug(self, message: str):
        """Log debug message"""
        self._write_log("debug", message)


class ConfigManager:
    """Configuration management utilities"""

    @staticmethod
    def load_config(config_file: Union[str, Path], default_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Load configuration with fallback to defaults"""
        success, data, message = FileManager.safe_read_json(config_file)
        if success:
            return True, data, "Configuration loaded"
        else:
            return True, default_config, f"Using default config: {message}"

    @staticmethod
    def save_config(config_file: Union[str, Path], config: Dict[str, Any]) -> Tuple[bool, str]:
        """Save configuration"""
        return FileManager.safe_write_json(config_file, config)

    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries"""
        result = base_config.copy()
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager.merge_configs(result[key], value)
            else:
                result[key] = value
        return result


class DataProcessor:
    """Data processing utilities"""

    @staticmethod
    def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(text, str):
            return ""

        sanitized = text.strip()
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        return sanitized

    @staticmethod
    def generate_unique_id() -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())

    @staticmethod
    def format_timestamp(timestamp: Optional[datetime] = None) -> str:
        """Format timestamp"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        return timestamp.isoformat()

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return None

    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataProcessor.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class SystemInfo:
    """System information utilities"""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        import platform
        import sys

        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable
        }

    @staticmethod
    def get_disk_usage(path: Union[str, Path]) -> Dict[str, int]:
        """Get disk usage information"""
        try:
            usage = shutil.disk_usage(path)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free
            }
        except Exception:
            return {"total": 0, "used": 0, "free": 0}

    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {}

            stat = path.stat()
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "extension": path.suffix,
                "name": path.name
            }
        except Exception:
            return {}


class PerformanceTimer:
    """Performance timing utility"""

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def get_elapsed_string(self) -> str:
        """Get elapsed time as formatted string"""
        return f"{self.description}: {self.elapsed_time:.4f} seconds"


class RetryHandler:
    """Retry operation utility"""

    @staticmethod
    def retry_operation(operation, max_attempts: int = 3, delay: float = 1.0,
                       exceptions: Tuple = (Exception,)) -> Tuple[bool, Any, str]:
        """Retry operation with specified attempts"""
        last_exception = None

        for attempt in range(max_attempts):
            try:
                result = operation()
                return True, result, "Success"
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

        return False, None, f"All {max_attempts} attempts failed. Last error: {str(last_exception)}"


class CacheManager:
    """Simple cache manager"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set value in cache"""
        if key in self.cache:
            # Update existing
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]

            self.cache[key] = value
            self.access_order.append(key)

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_order.clear()

    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)