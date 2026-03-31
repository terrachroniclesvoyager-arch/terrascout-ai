"""
Global Rate Limiter for All API Calls
Prevents IP bans and ensures compliance with API rate limits
"""

import time
import functools
from collections import defaultdict
from threading import Lock
from typing import Callable, Dict
import streamlit as st


class RateLimiter:
    """
    Global rate limiter with per-API tracking.

    Features:
    - Prevents API abuse
    - Per-API rate limits
    - Automatic throttling
    - Thread-safe
    """

    def __init__(self):
        self._locks: Dict[str, Lock] = defaultdict(Lock)
        self._last_call: Dict[str, float] = {}
        self._call_counts: Dict[str, int] = defaultdict(int)

    def throttle(
        self,
        api_name: str,
        min_interval: float = 1.0,
        max_calls_per_minute: int = 60
    ) -> Callable:
        """
        Decorator to rate limit API calls.

        Args:
            api_name: Unique identifier for the API
            min_interval: Minimum seconds between calls
            max_calls_per_minute: Maximum calls per minute

        Usage:
            @rate_limiter.throttle("nasa_api", min_interval=2.0)
            def fetch_nasa_data():
                return requests.get(...)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self._locks[api_name]:
                    # Check minimum interval
                    if api_name in self._last_call:
                        elapsed = time.time() - self._last_call[api_name]
                        if elapsed < min_interval:
                            sleep_time = min_interval - elapsed
                            if sleep_time > 0:
                                time.sleep(sleep_time)

                    # Update tracking
                    self._last_call[api_name] = time.time()
                    self._call_counts[api_name] += 1

                    # Execute function
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        # Re-raise but track failure
                        self._call_counts[f"{api_name}_errors"] += 1
                        raise

            return wrapper
        return decorator

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "total_calls": sum(
                count for api, count in self._call_counts.items()
                if not api.endswith("_errors")
            ),
            "total_errors": sum(
                count for api, count in self._call_counts.items()
                if api.endswith("_errors")
            ),
            "api_breakdown": dict(self._call_counts),
            "last_calls": dict(self._last_call)
        }

    def reset_stats(self):
        """Reset all statistics."""
        self._call_counts.clear()
        self._last_call.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


# Predefined rate limit configurations for known APIs
API_RATE_LIMITS = {
    # NASA APIs (with DEMO_KEY: 30/hour = 1 every 120 seconds)
    "nasa_neo": {"min_interval": 120.0, "max_calls_per_minute": 1},
    "nasa_apod": {"min_interval": 120.0, "max_calls_per_minute": 1},
    "nasa_firms": {"min_interval": 60.0, "max_calls_per_minute": 1},

    # iNaturalist (be respectful)
    "inaturalist": {"min_interval": 2.0, "max_calls_per_minute": 30},

    # GBIF (no strict limit but be respectful)
    "gbif": {"min_interval": 1.0, "max_calls_per_minute": 60},

    # USGS (be respectful)
    "usgs_earthquake": {"min_interval": 1.0, "max_calls_per_minute": 60},

    # Open-Meteo (generous but let's be nice)
    "openmeteo": {"min_interval": 0.5, "max_calls_per_minute": 120},

    # OpenAQ (1000/day documented limit)
    "openaq": {"min_interval": 2.0, "max_calls_per_minute": 30},

    # Nominatim OSM (STRICT: 1 request/second)
    "nominatim": {"min_interval": 1.0, "max_calls_per_minute": 60},

    # Overpass API (be very respectful)
    "overpass": {"min_interval": 3.0, "max_calls_per_minute": 20},

    # Default for unknown APIs (conservative)
    "default": {"min_interval": 2.0, "max_calls_per_minute": 30}
}


def get_rate_limit_config(api_name: str) -> Dict:
    """Get rate limit configuration for an API."""
    return API_RATE_LIMITS.get(api_name, API_RATE_LIMITS["default"])


@st.cache_data(ttl=300)
def get_rate_limiter_dashboard_data():
    """Get dashboard data for rate limiter (cached for 5 minutes)."""
    return rate_limiter.get_stats()


def display_rate_limit_dashboard():
    """Display rate limiter statistics in Streamlit."""
    st.markdown("### 🚦 API Rate Limiter Status")

    stats = get_rate_limiter_dashboard_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total API Calls",
            f"{stats['total_calls']:,}",
            help="Total number of API calls made this session"
        )

    with col2:
        st.metric(
            "Total Errors",
            f"{stats['total_errors']:,}",
            delta="-" + str(stats['total_errors']) if stats['total_errors'] > 0 else "0",
            delta_color="inverse"
        )

    with col3:
        success_rate = (
            (stats['total_calls'] - stats['total_errors']) / stats['total_calls'] * 100
            if stats['total_calls'] > 0 else 100
        )
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%"
        )

    # API breakdown
    if stats['api_breakdown']:
        st.markdown("#### API Call Breakdown")

        api_data = {
            api: count for api, count in stats['api_breakdown'].items()
            if not api.endswith("_errors") and count > 0
        }

        if api_data:
            import pandas as pd
            df = pd.DataFrame([
                {"API": api, "Calls": count}
                for api, count in sorted(api_data.items(), key=lambda x: x[1], reverse=True)
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)


# Usage examples for documentation
"""
USAGE EXAMPLES:

1. Basic throttling:
```python
from src.rate_limiter import rate_limiter

@rate_limiter.throttle("my_api", min_interval=2.0)
def fetch_data():
    return requests.get("https://api.example.com/data")
```

2. Using predefined config:
```python
from src.rate_limiter import rate_limiter, get_rate_limit_config

config = get_rate_limit_config("nasa_neo")

@rate_limiter.throttle("nasa_neo", **config)
def fetch_nasa_neo():
    return requests.get("https://api.nasa.gov/neo/...")
```

3. Display dashboard:
```python
from src.rate_limiter import display_rate_limit_dashboard

display_rate_limit_dashboard()
```
"""
