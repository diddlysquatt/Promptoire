"""
Error handling patterns and utilities for Promptoire
Provides consistent error handling, recovery, and user feedback
"""

import functools
import traceback
from typing import Optional, Callable, Any, Dict, List, Type, Union
from pathlib import Path
import sys

from .logger import get_logger, LogOperation


class PromptoireError(Exception):
    """Base exception class for Promptoire"""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = None


class ConfigurationError(PromptoireError):
    """Raised when there's a configuration issue"""
    pass


class DataValidationError(PromptoireError):
    """Raised when data validation fails"""
    pass


class FileOperationError(PromptoireError):
    """Raised when file operations fail"""
    pass


class UIError(PromptoireError):
    """Raised when UI operations fail"""
    pass


class NetworkError(PromptoireError):
    """Raised when network operations fail"""
    pass


class SecurityError(PromptoireError):
    """Raised when security constraints are violated"""
    pass


class ErrorHandler:
    """Centralized error handler for Promptoire"""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.error_callbacks: Dict[Type[Exception], List[Callable]] = {}
        self.user_message_handlers: Dict[Type[Exception], Callable] = {}

    def register_callback(self, exception_type: Type[Exception], callback: Callable):
        """Register a callback for specific exception types"""
        if exception_type not in self.error_callbacks:
            self.error_callbacks[exception_type] = []
        self.error_callbacks[exception_type].append(callback)

    def register_user_message_handler(self, exception_type: Type[Exception], handler: Callable):
        """Register a handler for displaying user-friendly messages"""
        self.user_message_handlers[exception_type] = handler

    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Handle an exception with logging and callbacks"""
        context = context or {}

        # Log the exception
        self.logger.error(
            f"Exception handled: {type(exception).__name__}: {str(exception)}",
            exception=exception,
            **context
        )

        # Execute registered callbacks
        for exc_type, callbacks in self.error_callbacks.items():
            if isinstance(exception, exc_type):
                for callback in callbacks:
                    try:
                        callback(exception, context)
                    except Exception as callback_error:
                        self.logger.error(f"Error in exception callback: {callback_error}")

        # Show user message if handler is registered
        for exc_type, handler in self.user_message_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    handler(exception, context)
                except Exception as handler_error:
                    self.logger.error(f"Error in user message handler: {handler_error}")
                break


# Global error handler instance
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_exceptions(
    exception_types: Union[Type[Exception], tuple] = Exception,
    return_value: Any = None,
    log_errors: bool = True,
    show_user_message: bool = False,
    context: Optional[Dict[str, Any]] = None
):
    """Decorator for handling exceptions in functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            func_context = context or {}
            func_context.update({
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            })

            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_errors:
                    error_handler.handle_exception(e, func_context)

                if show_user_message:
                    _show_default_user_message(e)

                return return_value
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None,
    default_return: Any = None,
    exception_types: Union[Type[Exception], tuple] = Exception,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """Safely execute a function with error handling"""
    kwargs = kwargs or {}
    error_handler = get_error_handler()

    func_context = context or {}
    func_context.update({
        'function': func.__name__,
        'module': getattr(func, '__module__', 'unknown'),
        'args_count': len(args),
        'kwargs_keys': list(kwargs.keys())
    })

    try:
        return func(*args, **kwargs)
    except exception_types as e:
        error_handler.handle_exception(e, func_context)
        return default_return


def safe_file_operation(
    operation: str,
    file_path: Union[str, Path],
    **kwargs
) -> Any:
    """Safely perform file operations with error handling"""
    logger = get_logger()
    error_handler = get_error_handler()

    context = {
        'operation': operation,
        'file_path': str(file_path),
        **kwargs
    }

    try:
        with LogOperation(f"File operation: {operation}", logger):
            path = Path(file_path)

            if operation == 'exists':
                return path.exists()
            elif operation == 'read':
                if path.exists():
                    return path.read_text(encoding='utf-8')
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
            elif operation == 'write':
                path.parent.mkdir(parents=True, exist_ok=True)
                content = kwargs.get('content', '')
                path.write_text(content, encoding='utf-8')
                return True
            elif operation == 'delete':
                if path.exists():
                    path.unlink()
                    return True
                return False
            elif operation == 'copy':
                src = Path(kwargs.get('src', file_path))
                dst = Path(kwargs.get('dst', file_path))
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(src, dst)
                    return True
                else:
                    raise FileNotFoundError(f"Source file not found: {src}")
            else:
                raise ValueError(f"Unknown file operation: {operation}")

    except Exception as e:
        file_error = FileOperationError(
            f"File operation failed: {operation} on {file_path}",
            error_code="FILE_OP_ERROR",
            details=context
        )
        error_handler.handle_exception(file_error, context)
        raise file_error


def validate_and_execute(
    validator: Callable,
    operation: Callable,
    validation_error_message: str = "Validation failed",
    **kwargs
) -> Any:
    """Validate input and execute operation"""
    logger = get_logger()
    error_handler = get_error_handler()

    try:
        # Run validation
        if validator(**kwargs):
            # Validation passed, execute operation
            return operation(**kwargs)
        else:
            # Validation failed
            validation_error = DataValidationError(validation_error_message)
            error_handler.handle_exception(validation_error, {'operation': operation.__name__})
            return None

    except Exception as e:
        error_handler.handle_exception(e, {'operation': operation.__name__})
        raise


def _show_default_user_message(exception: Exception):
    """Show default user-friendly message for exception"""
    # This would typically integrate with the UI layer
    # For now, we'll just log it
    logger = get_logger()

    if isinstance(exception, FileOperationError):
        logger.error("File operation failed. Please check file permissions and try again.")
    elif isinstance(exception, ConfigurationError):
        logger.error("Configuration error. Please check your settings.")
    elif isinstance(exception, DataValidationError):
        logger.error("Invalid data provided. Please check your input.")
    elif isinstance(exception, NetworkError):
        logger.error("Network error. Please check your internet connection.")
    elif isinstance(exception, SecurityError):
        logger.error("Security violation detected. Operation blocked.")
    else:
        logger.error("An unexpected error occurred. Please try again.")


# Context manager for error handling
class ErrorContext:
    """Context manager for error handling with context"""

    def __init__(self, operation_name: str,
                 exception_types: Union[Type[Exception], tuple] = Exception,
                 return_value: Any = None,
                 log_errors: bool = True,
                 context: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.exception_types = exception_types
        self.return_value = return_value
        self.log_errors = log_errors
        self.context = context or {}
        self.error_handler = get_error_handler()
        self.logger = get_logger()

    def __enter__(self):
        self.logger.debug(f"Entering error context: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, self.exception_types):
                if self.log_errors:
                    self.error_handler.handle_exception(exc_val, self.context)
                return True  # Suppress exception
        return False  # Don't suppress exceptions


# Utility functions for common error scenarios
def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exception_types: Union[Type[Exception], tuple] = Exception,
    backoff_factor: float = 2.0
):
    """Decorator to retry function on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time}s: {e}")
                        import time
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")

            raise last_exception
        return wrapper
    return decorator


def fallback_on_exception(
    fallback_func: Callable,
    exception_types: Union[Type[Exception], tuple] = Exception
):
    """Decorator to use fallback function on exception"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger = get_logger()
                logger.warning(f"Primary function {func.__name__} failed, using fallback: {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator