"""
Validation Functions for Promptoire
Input validation and data integrity checking
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from .constants import (
    VALID_PROMPT_NAME_PATTERN,
    VALID_CATEGORY_NAME_PATTERN,
    MAX_PROMPT_LENGTH,
    MAX_PROMPT_NAME_LENGTH,
    MAX_CATEGORY_NAME_LENGTH,
    MIN_PROMPT_LENGTH,
    MIN_NAME_LENGTH,
    REGEX_EMAIL,
    REGEX_URL,
    REGEX_PHONE,
    JSON_EXT
)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ValidationResult:
    """Validation result container"""
    def __init__(self, is_valid: bool, message: str = "", data: Any = None):
        self.is_valid = is_valid
        self.message = message
        self.data = data

    def __bool__(self):
        return self.is_valid

    def __str__(self):
        return self.message


def validate_prompt_name(name: str) -> ValidationResult:
    """Validate prompt name"""
    if not isinstance(name, str):
        return ValidationResult(False, "Prompt name must be a string")

    if not name.strip():
        return ValidationResult(False, "Prompt name cannot be empty")

    if len(name) < MIN_NAME_LENGTH:
        return ValidationResult(False, f"Prompt name must be at least {MIN_NAME_LENGTH} character long")

    if len(name) > MAX_PROMPT_NAME_LENGTH:
        return ValidationResult(False, f"Prompt name cannot exceed {MAX_PROMPT_NAME_LENGTH} characters")

    if not re.match(VALID_PROMPT_NAME_PATTERN, name):
        return ValidationResult(False, "Prompt name contains invalid characters")

    return ValidationResult(True, "Valid prompt name", name.strip())


def validate_prompt_content(content: str) -> ValidationResult:
    """Validate prompt content"""
    if not isinstance(content, str):
        return ValidationResult(False, "Prompt content must be a string")

    if len(content.strip()) < MIN_PROMPT_LENGTH:
        return ValidationResult(False, f"Prompt content must be at least {MIN_PROMPT_LENGTH} character long")

    if len(content) > MAX_PROMPT_LENGTH:
        return ValidationResult(False, f"Prompt content cannot exceed {MAX_PROMPT_LENGTH} characters")

    return ValidationResult(True, "Valid prompt content", content.strip())


def validate_category_name(name: str) -> ValidationResult:
    """Validate category name"""
    if not isinstance(name, str):
        return ValidationResult(False, "Category name must be a string")

    if not name.strip():
        return ValidationResult(False, "Category name cannot be empty")

    if len(name) < MIN_NAME_LENGTH:
        return ValidationResult(False, f"Category name must be at least {MIN_NAME_LENGTH} character long")

    if len(name) > MAX_CATEGORY_NAME_LENGTH:
        return ValidationResult(False, f"Category name cannot exceed {MAX_CATEGORY_NAME_LENGTH} characters")

    if not re.match(VALID_CATEGORY_NAME_PATTERN, name):
        return ValidationResult(False, "Category name contains invalid characters")

    return ValidationResult(True, "Valid category name", name.strip())


def validate_email(email: str) -> ValidationResult:
    """Validate email address"""
    if not isinstance(email, str):
        return ValidationResult(False, "Email must be a string")

    if not re.match(REGEX_EMAIL, email):
        return ValidationResult(False, "Invalid email format")

    return ValidationResult(True, "Valid email", email.lower().strip())


def validate_url(url: str) -> ValidationResult:
    """Validate URL"""
    if not isinstance(url, str):
        return ValidationResult(False, "URL must be a string")

    if not re.match(REGEX_URL, url):
        return ValidationResult(False, "Invalid URL format")

    return ValidationResult(True, "Valid URL", url.strip())


def validate_phone_number(phone: str) -> ValidationResult:
    """Validate phone number"""
    if not isinstance(phone, str):
        return ValidationResult(False, "Phone number must be a string")

    if not re.match(REGEX_PHONE, phone):
        return ValidationResult(False, "Invalid phone number format")

    return ValidationResult(True, "Valid phone number", phone.strip())


def validate_file_path(file_path: Union[str, Path]) -> ValidationResult:
    """Validate file path"""
    try:
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if not isinstance(path, Path):
            return ValidationResult(False, "Invalid path type")

        if not path.parent.exists():
            return ValidationResult(False, f"Parent directory does not exist: {path.parent}")

        return ValidationResult(True, "Valid file path", path)

    except Exception as e:
        return ValidationResult(False, f"Path validation error: {str(e)}")


def validate_directory_path(dir_path: Union[str, Path]) -> ValidationResult:
    """Validate directory path"""
    try:
        path = Path(dir_path) if isinstance(dir_path, str) else dir_path

        if not isinstance(path, Path):
            return ValidationResult(False, "Invalid path type")

        if not path.exists():
            return ValidationResult(False, f"Directory does not exist: {path}")

        if not path.is_dir():
            return ValidationResult(False, f"Path is not a directory: {path}")

        return ValidationResult(True, "Valid directory path", path)

    except Exception as e:
        return ValidationResult(False, f"Directory validation error: {str(e)}")


def validate_json_file(file_path: Union[str, Path]) -> ValidationResult:
    """Validate JSON file"""
    path_result = validate_file_path(file_path)
    if not path_result.is_valid:
        return path_result

    path = path_result.data

    if not path.suffix.lower() == JSON_EXT:
        return ValidationResult(False, f"File must have {JSON_EXT} extension")

    if not path.exists():
        return ValidationResult(False, f"File does not exist: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        return ValidationResult(True, "Valid JSON file", path)

    except json.JSONDecodeError as e:
        return ValidationResult(False, f"Invalid JSON format: {str(e)}")
    except Exception as e:
        return ValidationResult(False, f"Error reading JSON file: {str(e)}")


def validate_json_data(data: Any) -> ValidationResult:
    """Validate JSON data structure"""
    try:
        json.dumps(data)
        return ValidationResult(True, "Valid JSON data", data)
    except (TypeError, ValueError) as e:
        return ValidationResult(False, f"Invalid JSON data: {str(e)}")


def validate_prompt_data(prompt_data: Dict[str, Any]) -> ValidationResult:
    """Validate complete prompt data structure"""
    if not isinstance(prompt_data, dict):
        return ValidationResult(False, "Prompt data must be a dictionary")

    # Required fields
    required_fields = ['name', 'content']
    for field in required_fields:
        if field not in prompt_data:
            return ValidationResult(False, f"Missing required field: {field}")

    # Validate name
    name_result = validate_prompt_name(prompt_data['name'])
    if not name_result.is_valid:
        return ValidationResult(False, f"Invalid prompt name: {name_result.message}")

    # Validate content
    content_result = validate_prompt_content(prompt_data['content'])
    if not content_result.is_valid:
        return ValidationResult(False, f"Invalid prompt content: {content_result.message}")

    # Optional fields validation
    if 'category' in prompt_data:
        category_result = validate_category_name(prompt_data['category'])
        if not category_result.is_valid:
            return ValidationResult(False, f"Invalid category: {category_result.message}")

    if 'tags' in prompt_data:
        tags = prompt_data['tags']
        if not isinstance(tags, list):
            return ValidationResult(False, "Tags must be a list")

        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                return ValidationResult(False, "All tags must be non-empty strings")

    return ValidationResult(True, "Valid prompt data", prompt_data)


def validate_settings_data(settings_data: Dict[str, Any]) -> ValidationResult:
    """Validate settings data structure"""
    if not isinstance(settings_data, dict):
        return ValidationResult(False, "Settings data must be a dictionary")

    # Validate specific setting fields
    if 'theme' in settings_data:
        theme = settings_data['theme']
        if not isinstance(theme, str) or theme not in ['light', 'dark']:
            return ValidationResult(False, "Theme must be 'light' or 'dark'")

    if 'language' in settings_data:
        language = settings_data['language']
        if not isinstance(language, str) or len(language) != 2:
            return ValidationResult(False, "Language must be a 2-character code")

    if 'auto_save' in settings_data:
        auto_save = settings_data['auto_save']
        if not isinstance(auto_save, bool):
            return ValidationResult(False, "Auto save must be a boolean")

    if 'backup_interval_hours' in settings_data:
        interval = settings_data['backup_interval_hours']
        if not isinstance(interval, int) or interval < 1:
            return ValidationResult(False, "Backup interval must be a positive integer")

    return ValidationResult(True, "Valid settings data", settings_data)


def validate_template_variables(template: str, variables: Dict[str, Any]) -> ValidationResult:
    """Validate template variables against template placeholders"""
    if not isinstance(template, str):
        return ValidationResult(False, "Template must be a string")

    if not isinstance(variables, dict):
        return ValidationResult(False, "Variables must be a dictionary")

    # Find placeholders in template
    placeholder_pattern = r'\{\{(\w+)\}\}'
    template_vars = set(re.findall(placeholder_pattern, template))

    # Check for missing variables
    provided_vars = set(variables.keys())
    missing_vars = template_vars - provided_vars

    if missing_vars:
        return ValidationResult(False, f"Missing template variables: {', '.join(missing_vars)}")

    # Check for extra variables
    extra_vars = provided_vars - template_vars
    if extra_vars:
        return ValidationResult(False, f"Extra variables not used in template: {', '.join(extra_vars)}")

    return ValidationResult(True, "Valid template variables", variables)


def validate_list_size(lst: List[Any], min_size: int = 0, max_size: Optional[int] = None) -> ValidationResult:
    """Validate list size constraints"""
    if not isinstance(lst, list):
        return ValidationResult(False, "Input must be a list")

    if len(lst) < min_size:
        return ValidationResult(False, f"List must have at least {min_size} items")

    if max_size is not None and len(lst) > max_size:
        return ValidationResult(False, f"List cannot have more than {max_size} items")

    return ValidationResult(True, "Valid list size", lst)


def validate_numeric_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> ValidationResult:
    """Validate numeric value is within range"""
    if not isinstance(value, (int, float)):
        return ValidationResult(False, "Value must be numeric")

    if value < min_val or value > max_val:
        return ValidationResult(False, f"Value must be between {min_val} and {max_val}")

    return ValidationResult(True, "Valid numeric range", value)


def validate_string_length(text: str, min_length: int = 0, max_length: Optional[int] = None) -> ValidationResult:
    """Validate string length constraints"""
    if not isinstance(text, str):
        return ValidationResult(False, "Input must be a string")

    if len(text) < min_length:
        return ValidationResult(False, f"String must be at least {min_length} characters long")

    if max_length is not None and len(text) > max_length:
        return ValidationResult(False, f"String cannot exceed {max_length} characters")

    return ValidationResult(True, "Valid string length", text)


def validate_uuid(uuid_string: str) -> ValidationResult:
    """Validate UUID format"""
    if not isinstance(uuid_string, str):
        return ValidationResult(False, "UUID must be a string")

    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, uuid_string.lower()):
        return ValidationResult(False, "Invalid UUID format")

    return ValidationResult(True, "Valid UUID", uuid_string.lower())


def validate_date_format(date_string: str, date_format: str = "%Y-%m-%d") -> ValidationResult:
    """Validate date format"""
    if not isinstance(date_string, str):
        return ValidationResult(False, "Date must be a string")

    try:
        from datetime import datetime
        datetime.strptime(date_string, date_format)
        return ValidationResult(True, "Valid date format", date_string)
    except ValueError:
        return ValidationResult(False, f"Invalid date format. Expected: {date_format}")


def validate_color_hex(color_hex: str) -> ValidationResult:
    """Validate hexadecimal color code"""
    if not isinstance(color_hex, str):
        return ValidationResult(False, "Color must be a string")

    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    if not re.match(hex_pattern, color_hex):
        return ValidationResult(False, "Invalid hexadecimal color format")

    return ValidationResult(True, "Valid hex color", color_hex.upper())