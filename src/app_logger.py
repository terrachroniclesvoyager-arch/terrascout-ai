"""
Professional Logging System for TerraScout AI
Replaces generic exception handling with structured logging
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback


class TerraScoutLogger:
    """
    Centralized logger for TerraScout AI.

    Features:
    - Structured logging
    - File + console output
    - Error categorization
    - Performance tracking
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("TerraScout")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # File handler (all logs)
        log_file = self.log_dir / f"terrascout_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Error file handler (errors only)
        error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)

        # Console handler (warnings and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def log_api_call(
        self,
        api_name: str,
        endpoint: str,
        status: str,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log API call with structured data."""
        msg = f"API Call | {api_name} | {endpoint} | Status: {status}"

        if duration_ms:
            msg += f" | Duration: {duration_ms:.0f}ms"

        if error:
            msg += f" | Error: {error}"

        if status == "success":
            self.logger.info(msg)
        elif status == "error":
            self.logger.error(msg)
        else:
            self.logger.warning(msg)

    def log_module_load(self, module_id: str, success: bool, error: Optional[str] = None):
        """Log module loading attempt."""
        if success:
            self.logger.info(f"Module Loaded | {module_id}")
        else:
            self.logger.error(f"Module Load Failed | {module_id} | Error: {error}")

    def log_exception(
        self,
        exception: Exception,
        context: str = "",
        severity: str = "ERROR"
    ):
        """
        Log exception with full traceback.

        Args:
            exception: The exception object
            context: Additional context (e.g., "Fetching weather data for NYC")
            severity: ERROR, WARNING, or CRITICAL
        """
        exc_type = type(exception).__name__
        exc_msg = str(exception)
        exc_traceback = ''.join(traceback.format_tb(exception.__traceback__))

        msg = f"Exception | {exc_type}: {exc_msg}"
        if context:
            msg += f" | Context: {context}"

        # Log full traceback to file only
        full_msg = f"{msg}\n{exc_traceback}"

        if severity == "CRITICAL":
            self.logger.critical(full_msg)
        elif severity == "WARNING":
            self.logger.warning(msg)  # No traceback for warnings
        else:
            self.logger.error(full_msg)

    def log_performance(self, operation: str, duration_ms: float, threshold_ms: float = 1000):
        """Log performance metrics and warn on slow operations."""
        msg = f"Performance | {operation} | {duration_ms:.0f}ms"

        if duration_ms > threshold_ms:
            self.logger.warning(f"{msg} | SLOW (threshold: {threshold_ms}ms)")
        else:
            self.logger.debug(msg)

    def log_data_export(self, module: str, format: str, rows: int, success: bool):
        """Log data export attempts."""
        if success:
            self.logger.info(f"Export | {module} | Format: {format} | Rows: {rows}")
        else:
            self.logger.error(f"Export Failed | {module} | Format: {format}")

    def log_user_action(self, action: str, details: str = ""):
        """Log user interactions (for analytics)."""
        msg = f"User Action | {action}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)


# Global logger instance
app_logger = TerraScoutLogger()


# Convenience functions for easy import
def log_api_call(api_name: str, endpoint: str, status: str, **kwargs):
    """Shortcut for logging API calls."""
    app_logger.log_api_call(api_name, endpoint, status, **kwargs)


def log_exception(exception: Exception, context: str = "", severity: str = "ERROR"):
    """Shortcut for logging exceptions."""
    app_logger.log_exception(exception, context, severity)


def log_performance(operation: str, duration_ms: float, threshold_ms: float = 1000):
    """Shortcut for logging performance."""
    app_logger.log_performance(operation, duration_ms, threshold_ms)


# Decorator for automatic exception logging
def log_exceptions(context: str = ""):
    """
    Decorator to automatically log exceptions.

    Usage:
        @log_exceptions("Fetching weather data")
        def get_weather():
            # ... code ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_exception(e, context or f"Function: {func.__name__}")
                raise  # Re-raise after logging
        return wrapper
    return decorator


import functools  # Import at module level


# Usage examples
"""
USAGE EXAMPLES:

1. Basic API call logging:
```python
from src.app_logger import log_api_call
import time

start = time.time()
try:
    response = requests.get("https://api.example.com/data")
    duration = (time.time() - start) * 1000
    log_api_call("example_api", "/data", "success", duration_ms=duration)
except requests.RequestException as e:
    log_api_call("example_api", "/data", "error", error=str(e))
```

2. Exception logging:
```python
from src.app_logger import log_exception

try:
    result = some_risky_operation()
except ValueError as e:
    log_exception(e, "Processing user input", severity="WARNING")
except Exception as e:
    log_exception(e, "Critical operation failed", severity="CRITICAL")
    raise
```

3. Using decorator:
```python
from src.app_logger import log_exceptions

@log_exceptions("Fetching NASA data")
def fetch_nasa_neo():
    return requests.get("https://api.nasa.gov/...")
```

4. Performance logging:
```python
from src.app_logger import log_performance
import time

start = time.time()
process_large_dataset()
duration = (time.time() - start) * 1000
log_performance("Dataset processing", duration, threshold_ms=5000)
```
"""
