"""
Lazy Data Loader - Load data only when needed to avoid memory issues
Smart caching and progressive loading for optimal performance
"""

import streamlit as st
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import functools


class LazyDataLoader:
    """
    Intelligent lazy loading system for data sources.

    Features:
    - Load data only when requested
    - Smart caching with TTL
    - Progressive loading with timeout
    - Automatic error handling
    - Memory-efficient batching
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Initialize lazy loader.

        Args:
            cache_ttl_seconds: Time-to-live for cached data (default 5 minutes)
        """
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _is_cache_valid(self, source_name: str) -> bool:
        """Check if cached data is still valid."""
        if source_name not in self._cache:
            return False

        cached_time = self._cache[source_name].get("timestamp")
        if not cached_time:
            return False

        age = (datetime.now() - cached_time).total_seconds()
        return age < self.cache_ttl

    def get_cached_or_fetch(
        self,
        source_name: str,
        fetch_function: Callable,
        timeout: int = 10,
        use_cache: bool = True
    ) -> Dict:
        """
        Get data from cache or fetch if needed.

        Args:
            source_name: Unique name for this data source
            fetch_function: Function to call to fetch data
            timeout: Max seconds to wait for fetch
            use_cache: Whether to use cached data

        Returns:
            Dict with data or error info
        """
        # Check cache first
        if use_cache and self._is_cache_valid(source_name):
            return self._cache[source_name]["data"]

        # Fetch with timeout
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(fetch_function)
                data = future.result(timeout=timeout)

                # Cache the result
                self._cache[source_name] = {
                    "data": data,
                    "timestamp": datetime.now()
                }

                return data

        except TimeoutError:
            return {
                "success": False,
                "error": f"Timeout after {timeout}s",
                "cached": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cached": False
            }

    def clear_cache(self, source_name: Optional[str] = None):
        """
        Clear cache for specific source or all sources.

        Args:
            source_name: Source to clear, or None to clear all
        """
        if source_name:
            self._cache.pop(source_name, None)
        else:
            self._cache.clear()

    def get_cache_status(self) -> Dict[str, Dict]:
        """Get status of all cached items."""
        status = {}
        for source, cache_data in self._cache.items():
            timestamp = cache_data.get("timestamp")
            if timestamp:
                age = (datetime.now() - timestamp).total_seconds()
                status[source] = {
                    "age_seconds": age,
                    "valid": age < self.cache_ttl,
                    "cached_at": timestamp.isoformat()
                }
        return status


class ProgressiveDataFetcher:
    """
    Fetch data progressively with user feedback.
    Shows progress, handles errors gracefully.
    """

    @staticmethod
    def fetch_with_progress(
        sources: List[Dict[str, Any]],
        max_workers: int = 10,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch multiple sources with progress indicator.

        Args:
            sources: List of dicts with keys: name, function, timeout
            max_workers: Max parallel workers
            show_progress: Show Streamlit progress bar

        Returns:
            Dict mapping source names to results
        """
        results = {}
        total = len(sources)

        if show_progress:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {}
            for source in sources:
                future = executor.submit(source["function"])
                futures[future] = source["name"]

            # Collect results as they complete
            completed = 0
            for future in futures:
                source_name = futures[future]

                try:
                    timeout = next(
                        (s["timeout"] for s in sources if s["name"] == source_name),
                        10
                    )
                    result = future.result(timeout=timeout)
                    results[source_name] = result

                except TimeoutError:
                    results[source_name] = {
                        "success": False,
                        "error": "Timeout"
                    }
                except Exception as e:
                    results[source_name] = {
                        "success": False,
                        "error": str(e)
                    }

                # Update progress
                completed += 1
                if show_progress:
                    progress = completed / total
                    progress_bar.progress(progress)
                    status_text.text(f"Loading data sources... {completed}/{total}")

            if show_progress:
                progress_bar.empty()
                status_text.empty()

        return results


class MapDataPaginator:
    """
    Paginate large datasets for map display.
    Prevents memory issues with thousands of markers.
    """

    @staticmethod
    def paginate_markers(
        markers: List[Dict],
        page_size: int = 100,
        current_page: int = 0
    ) -> Dict:
        """
        Paginate markers for display.

        Args:
            markers: List of marker data
            page_size: Markers per page
            current_page: Current page number (0-indexed)

        Returns:
            Dict with paginated data and metadata
        """
        total = len(markers)
        total_pages = (total + page_size - 1) // page_size

        start = current_page * page_size
        end = min(start + page_size, total)

        return {
            "markers": markers[start:end],
            "page": current_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_markers": total,
            "showing_start": start + 1,
            "showing_end": end
        }

    @staticmethod
    def create_pagination_controls(pagination_data: Dict, key_prefix: str = ""):
        """
        Create Streamlit pagination controls.

        Args:
            pagination_data: Output from paginate_markers()
            key_prefix: Prefix for widget keys

        Returns:
            Selected page number
        """
        total_pages = pagination_data["total_pages"]
        current_page = pagination_data["page"]

        if total_pages <= 1:
            return 0

        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            if st.button("◀ Previous", key=f"{key_prefix}_prev", disabled=(current_page == 0)):
                return max(0, current_page - 1)

        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                Page {current_page + 1} of {total_pages}
                ({pagination_data['showing_start']}-{pagination_data['showing_end']}
                of {pagination_data['total_markers']} items)
            </div>
            """, unsafe_allow_html=True)

        with col3:
            if st.button("Next ▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
                return min(total_pages - 1, current_page + 1)

        return current_page


# Global lazy loader instance
_lazy_loader = LazyDataLoader(cache_ttl_seconds=300)


def get_lazy_loader() -> LazyDataLoader:
    """Get global lazy loader instance."""
    return _lazy_loader


# Decorator for lazy loading functions
def lazy_load(source_name: str, timeout: int = 10, use_cache: bool = True):
    """
    Decorator to make any function lazy-loaded with caching.

    Usage:
        @lazy_load("weather_data", timeout=15)
        def fetch_weather():
            return requests.get(...).json()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            loader = get_lazy_loader()
            return loader.get_cached_or_fetch(
                source_name=source_name,
                fetch_function=lambda: func(*args, **kwargs),
                timeout=timeout,
                use_cache=use_cache
            )
        return wrapper
    return decorator


# Example usage in docstring
"""
USAGE EXAMPLES:

1. Basic lazy loading with caching:
```python
from src.lazy_data_loader import get_lazy_loader

loader = get_lazy_loader()

# First call: fetches data
data = loader.get_cached_or_fetch(
    "earthquakes",
    fetch_earthquakes,
    timeout=15
)

# Second call within 5 minutes: uses cache
data = loader.get_cached_or_fetch(
    "earthquakes",
    fetch_earthquakes
)
```

2. Progressive fetching with progress bar:
```python
from src.lazy_data_loader import ProgressiveDataFetcher

sources = [
    {"name": "weather", "function": fetch_weather, "timeout": 10},
    {"name": "earthquakes", "function": fetch_earthquakes, "timeout": 15},
    {"name": "fires", "function": fetch_fires, "timeout": 10}
]

results = ProgressiveDataFetcher.fetch_with_progress(sources, max_workers=5)
```

3. Map pagination:
```python
from src.lazy_data_loader import MapDataPaginator

# Paginate 10,000 markers
paginated = MapDataPaginator.paginate_markers(
    markers=all_markers,
    page_size=100,
    current_page=0
)

# Display only current page
for marker in paginated["markers"]:
    folium.Marker(...).add_to(map)

# Add pagination controls
new_page = MapDataPaginator.create_pagination_controls(paginated)
```

4. Decorator usage:
```python
from src.lazy_data_loader import lazy_load

@lazy_load("crypto_prices", timeout=10, use_cache=True)
def fetch_crypto_prices():
    return requests.get("https://api.coingecko.com/...").json()

# Automatically cached for 5 minutes
data = fetch_crypto_prices()
```
"""
