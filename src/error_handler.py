"""
Robust Error Handling for TerraScout AI
Automatic retry with exponential backoff, fallback strategies, and user-friendly error messages
"""

import streamlit as st
import time
import functools
import traceback
from typing import Callable, Optional, Any, List, Type
import requests
from urllib.error import URLError, HTTPError
import socket


class APIError(Exception):
    """Base exception for API-related errors."""
    pass


class RetryableError(APIError):
    """Error that can be retried (temporary network issues, rate limits, etc.)."""
    pass


class FatalError(APIError):
    """Error that should not be retried (invalid credentials, bad requests, etc.)."""
    pass


# Retryable error types
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    socket.timeout,
    URLError,
    RetryableError,
)

# Fatal error types (don't retry)
FATAL_EXCEPTIONS = (
    ValueError,
    KeyError,
    TypeError,
    FatalError,
)


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    show_progress: bool = True,
    fallback: Optional[Callable] = None,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry (exponential backoff)
        show_progress: Whether to show retry status in UI
        fallback: Optional fallback function to call if all retries fail
        retryable_exceptions: Tuple of exception types that should trigger retry

    Usage:
        @with_retry(max_retries=3, initial_delay=2.0)
        def fetch_data(url):
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        # With fallback
        def fallback_data():
            return {"status": "cached", "data": []}

        @with_retry(fallback=fallback_data)
        def fetch_with_fallback(url):
            return requests.get(url).json()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    return result

                except FATAL_EXCEPTIONS as e:
                    # Don't retry fatal errors
                    if show_progress:
                        st.error(f"❌ Fatal error in {func.__name__}: {str(e)}")
                    raise

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Retry
                        if show_progress:
                            st.warning(
                                f"⚠️ Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}\n"
                                f"Retrying in {delay:.1f}s..."
                            )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        # Max retries exceeded
                        if show_progress:
                            st.error(
                                f"❌ All {max_retries + 1} attempts failed for {func.__name__}\n"
                                f"Last error: {str(e)}"
                            )

                        # Try fallback if available
                        if fallback:
                            if show_progress:
                                st.info("ℹ️ Using fallback data...")
                            try:
                                return fallback(*args, **kwargs)
                            except Exception as fallback_error:
                                st.error(f"❌ Fallback also failed: {fallback_error}")
                                raise last_exception

                        raise last_exception

                except Exception as e:
                    # Unexpected error
                    last_exception = e
                    if show_progress:
                        st.error(f"❌ Unexpected error in {func.__name__}: {str(e)}")
                        with st.expander("🔍 Stack Trace"):
                            st.code(traceback.format_exc())
                    raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def safe_api_call(
    api_func: Callable,
    *args,
    error_message: str = "API call failed",
    default_value: Any = None,
    show_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute an API call with error handling.

    Args:
        api_func: The API function to call
        args: Positional arguments for api_func
        error_message: Custom error message to display
        default_value: Value to return on error
        show_errors: Whether to display errors in UI
        kwargs: Keyword arguments for api_func

    Returns:
        API result or default_value on error

    Usage:
        result = safe_api_call(
            requests.get,
            "https://api.example.com/data",
            timeout=10,
            error_message="Failed to fetch data",
            default_value=[]
        )
    """
    try:
        return api_func(*args, **kwargs)
    except requests.exceptions.Timeout:
        if show_errors:
            st.warning(f"⏱️ {error_message}: Request timed out")
        return default_value
    except requests.exceptions.ConnectionError:
        if show_errors:
            st.warning(f"🌐 {error_message}: Connection failed (check your internet)")
        return default_value
    except requests.exceptions.HTTPError as e:
        if show_errors:
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            if status_code == 429:
                st.warning(f"⏸️ {error_message}: Rate limit exceeded. Try again later.")
            elif status_code >= 500:
                st.warning(f"🔧 {error_message}: Server error ({status_code})")
            else:
                st.error(f"❌ {error_message}: HTTP {status_code}")
        return default_value
    except Exception as e:
        if show_errors:
            st.error(f"❌ {error_message}: {str(e)}")
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())
        return default_value


class ErrorAggregator:
    """
    Aggregate multiple errors during batch operations.

    Usage:
        errors = ErrorAggregator()

        for item in items:
            try:
                process(item)
            except Exception as e:
                errors.add(f"Failed processing {item}", e)

        errors.display_summary()
    """

    def __init__(self):
        self.errors: List[dict] = []

    def add(self, context: str, exception: Exception):
        """Add an error to the aggregator."""
        self.errors.append({
            "context": context,
            "exception": str(exception),
            "type": type(exception).__name__,
            "traceback": traceback.format_exc()
        })

    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.errors) > 0

    def count(self) -> int:
        """Get the number of errors."""
        return len(self.errors)

    def display_summary(self, title: str = "Errors Summary"):
        """Display error summary in Streamlit UI."""
        if not self.has_errors():
            st.success("✅ No errors occurred")
            return

        error_count = self.count()
        st.error(f"❌ {error_count} error(s) occurred during operation")

        with st.expander(f"🔍 View {error_count} Error(s)"):
            for i, error in enumerate(self.errors, 1):
                st.markdown(f"### Error {i}: {error['context']}")
                st.code(f"{error['type']}: {error['exception']}", language="python")

                with st.expander("Stack Trace"):
                    st.code(error['traceback'], language="python")

                st.markdown("---")

    def get_errors(self) -> List[dict]:
        """Get all recorded errors."""
        return self.errors

    def clear(self):
        """Clear all errors."""
        self.errors.clear()


def handle_api_error(error: Exception, api_name: str) -> str:
    """
    Convert API errors to user-friendly messages.

    Args:
        error: The exception that occurred
        api_name: Name of the API (for context)

    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__

    # Timeout errors
    if isinstance(error, (requests.exceptions.Timeout, socket.timeout)):
        return f"⏱️ {api_name} is taking too long to respond. Try again or reduce the query area."

    # Connection errors
    if isinstance(error, (requests.exceptions.ConnectionError, URLError)):
        return f"🌐 Cannot connect to {api_name}. Check your internet connection."

    # HTTP errors
    if isinstance(error, (requests.exceptions.HTTPError, HTTPError)):
        status_code = getattr(error, 'response', None)
        if status_code:
            status_code = status_code.status_code

        if status_code == 400:
            return f"❌ Invalid request to {api_name}. Check your input parameters."
        elif status_code == 401:
            return f"🔐 Authentication failed for {api_name}. Check your API key."
        elif status_code == 403:
            return f"🚫 Access denied to {api_name}. You may not have permission."
        elif status_code == 404:
            return f"🔍 Resource not found in {api_name}. The requested data may not exist."
        elif status_code == 429:
            return f"⏸️ Rate limit exceeded for {api_name}. Wait a few minutes and try again."
        elif status_code >= 500:
            return f"🔧 {api_name} server error. The service may be temporarily down."

    # JSON decode errors
    if isinstance(error, ValueError) and "JSON" in str(error):
        return f"📄 Invalid response from {api_name}. The data format may have changed."

    # Generic fallback
    return f"❌ {api_name} error: {str(error)}"


@st.cache_data(ttl=3600, show_spinner=False)
def cached_api_call(url: str, **kwargs) -> Any:
    """
    Cached API call with 1-hour TTL.

    Args:
        url: API endpoint URL
        kwargs: Additional arguments for requests.get()

    Returns:
        API response JSON

    Usage:
        data = cached_api_call("https://api.example.com/data", timeout=10)
    """
    kwargs.setdefault("timeout", 10)
    try:
        response = requests.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": True, "message": f"Request to {url} timed out"}
    except requests.exceptions.ConnectionError:
        return {"error": True, "message": f"Connection to {url} failed"}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if hasattr(e, "response") and e.response is not None else "unknown"
        return {"error": True, "message": f"HTTP {status} from {url}"}
    except Exception as e:
        return {"error": True, "message": f"API call failed: {str(e)}"}
