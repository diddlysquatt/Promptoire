"""
Security utilities for Promptoire
Provides secure alternatives to os.system() and input validation functions
"""

import os
import subprocess
import platform
import re
from pathlib import Path
from typing import Optional, Union


def validate_path(path: Union[str, Path]) -> bool:
    """
    Validate that a path is safe and doesn't contain dangerous characters

    Args:
        path: Path to validate

    Returns:
        bool: True if path is safe
    """
    if not path:
        return False

    path_str = str(path)

    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'\.\.\\',  # Directory traversal (Windows)
        r'[;&|`$]',  # Shell command injection
        r'\x00',  # Null byte injection
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, path_str):
            return False

    # Resolve absolute path and check it stays within expected bounds
    try:
        resolved_path = Path(path_str).resolve()
        # Additional checks can be added here based on application needs
        return True
    except (OSError, ValueError):
        return False


def safe_open_file_location(file_path: Union[str, Path]) -> bool:
    """
    Safely open the parent directory of a file in the system file manager

    Args:
        file_path: Path to the file whose parent directory should be opened

    Returns:
        bool: True if operation succeeded
    """
    if not validate_path(file_path):
        return False

    try:
        path = Path(file_path)
        if not path.exists():
            return False

        parent_dir = path.parent

        if platform.system() == "Windows":
            # Use os.startfile on Windows (safer than os.system)
            os.startfile(parent_dir)
        elif platform.system() == "Darwin":  # macOS
            # Use subprocess.run instead of os.system for security
            subprocess.run(
                ["open", str(parent_dir)],
                check=True,
                timeout=10,
                capture_output=True
            )
        else:  # Linux and other Unix-like systems
            # Use subprocess.run instead of os.system for security
            subprocess.run(
                ["xdg-open", str(parent_dir)],
                check=True,
                timeout=10,
                capture_output=True
            )

        return True
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def safe_execute_command(command: list, timeout: int = 30) -> Optional[subprocess.CompletedProcess]:
    """
    Safely execute a command using subprocess.run with proper validation

    Args:
        command: List of command and arguments
        timeout: Maximum execution time in seconds

    Returns:
        subprocess.CompletedProcess if successful, None otherwise
    """
    if not command or not isinstance(command, list):
        return None

    # Validate command components
    for arg in command:
        if not isinstance(arg, str):
            return False
        if not validate_path(arg) and not arg.isalnum() and not re.match(r'^[\w\-\.]+$', arg):
            return None

    try:
        result = subprocess.run(
            command,
            check=True,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        return result
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return None


def validate_input(input_str: str, max_length: int = 1000,
                  allowed_chars: Optional[str] = None) -> bool:
    """
    Validate user input to prevent injection attacks

    Args:
        input_str: Input string to validate
        max_length: Maximum allowed length
        allowed_chars: Regex pattern of allowed characters (None for default)

    Returns:
        bool: True if input is safe
    """
    if not isinstance(input_str, str):
        return False

    # Length check
    if len(input_str) > max_length or len(input_str) == 0:
        return False

    # Default allowed characters: alphanumeric, spaces, and basic punctuation
    if allowed_chars is None:
        allowed_chars = r'^[a-zA-Z0-9\s\-_.,!?@#%&()=+\[\]{}:;\'"]*$'

    # Pattern matching
    if not re.match(allowed_chars, input_str):
        return False

    # Check for dangerous substrings
    dangerous_substrings = [
        '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
        'eval(', 'exec(', 'system(', 'subprocess.', 'os.system',
        '__import__', 'open(', 'file(', 'input(', 'raw_input('
    ]

    input_lower = input_str.lower()
    for dangerous in dangerous_substrings:
        if dangerous in input_lower:
            return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and invalid characters

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    if not isinstance(filename, str):
        return "invalid"

    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')

    # Ensure it's not empty after sanitization
    if not sanitized:
        sanitized = "unnamed"

    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext

    return sanitized


def secure_file_operation(file_path: Union[str, Path], operation: str, **kwargs) -> bool:
    """
    Perform secure file operations with validation

    Args:
        file_path: Path to the file
        operation: Operation type ('read', 'write', 'exists', 'mkdir')
        **kwargs: Additional arguments for the operation

    Returns:
        bool: True if operation succeeded
    """
    if not validate_path(file_path):
        return False

    path = Path(file_path)

    try:
        if operation == 'exists':
            return path.exists()
        elif operation == 'mkdir':
            path.mkdir(parents=True, exist_ok=True)
            return True
        elif operation == 'read':
            encoding = kwargs.get('encoding', 'utf-8')
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        elif operation == 'write':
            encoding = kwargs.get('encoding', 'utf-8')
            content = kwargs.get('content', '')
            # Validate content if provided
            if isinstance(content, str) and not validate_input(content, max_length=1000000):
                return False
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        else:
            return False
    except (OSError, ValueError, UnicodeError):
        return False