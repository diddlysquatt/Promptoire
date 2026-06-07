"""
Logging infrastructure for Promptoire
Provides consistent logging configuration and utilities
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any
import traceback


class PromptoireLogger:
    """Centralized logging manager for Promptoire"""

    def __init__(self, name: str = "Promptoire", log_dir: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Set up log directory
        if log_dir is None:
            log_dir = Path.home() / "AppData" / "Local" / "Promptoire" / "logs"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up console and file handlers"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

        # File handler for general logs
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)

        # Error-only file handler
        error_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = RotatingFileHandler(
            error_file, maxBytes=2*1024*1024, backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details"""
        if exception:
            error_msg = f"{message}\nException: {str(exception)}\nTraceback: {traceback.format_exc()}"
            self._log_with_context(logging.ERROR, error_msg, **kwargs)
        else:
            self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception details"""
        if exception:
            error_msg = f"{message}\nException: {str(exception)}\nTraceback: {traceback.format_exc()}"
            self._log_with_context(logging.CRITICAL, error_msg, **kwargs)
        else:
            self._log_with_context(logging.CRITICAL, message, **kwargs)

    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context"""
        if kwargs:
            context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context_str}"

        self.logger.log(level, message)

    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """Log function call for debugging"""
        kwargs = kwargs or {}
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])

        params = []
        if args_str:
            params.append(args_str)
        if kwargs_str:
            params.append(kwargs_str)

        param_str = ", ".join(params)
        self.debug(f"Calling {func_name}({param_str})")

    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """Log user action for analytics"""
        details = details or {}
        details_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        message = f"User Action: {action}"
        if details_str:
            message += f" | {details_str}"
        self.info(message)

    def log_system_event(self, event: str, details: Dict[str, Any] = None):
        """Log system event"""
        details = details or {}
        details_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        message = f"System Event: {event}"
        if details_str:
            message += f" | {details_str}"
        self.info(message)

    def set_level(self, level):
        """Set logging level"""
        self.logger.setLevel(level)

    def get_log_files(self) -> Dict[str, Path]:
        """Get paths to log files"""
        return {
            "main": self.log_dir / f"{self.name}.log",
            "errors": self.log_dir / f"{self.name}_errors.log"
        }


# Global logger instance
_global_logger = None


def get_logger(name: str = "Promptoire") -> PromptoireLogger:
    """Get or create logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = PromptoireLogger(name)
    return _global_logger


def setup_logging(name: str = "Promptoire", log_dir: Optional[Path] = None) -> PromptoireLogger:
    """Setup logging configuration"""
    global _global_logger
    _global_logger = PromptoireLogger(name, log_dir)
    return _global_logger


# Decorator for automatic function call logging
def log_function_calls(logger: Optional[PromptoireLogger] = None):
    """Decorator to automatically log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            log.log_function_call(func.__name__, args, kwargs)
            try:
                result = func(*args, **kwargs)
                log.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                log.error(f"{func.__name__} failed", exception=e)
                raise
        return wrapper
    return decorator


# Context manager for logging operations
class LogOperation:
    """Context manager for logging operations"""

    def __init__(self, operation_name: str, logger: Optional[PromptoireLogger] = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger()
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed operation: {self.operation_name} | duration={duration.total_seconds():.2f}s")
        else:
            self.logger.error(f"Failed operation: {self.operation_name} | duration={duration.total_seconds():.2f}s | error={exc_val}")
        return False  # Don't suppress exceptions