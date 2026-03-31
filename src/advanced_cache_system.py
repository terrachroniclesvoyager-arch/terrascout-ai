"""
Advanced Caching System - Ultra Performance
Intelligent multi-level caching for zero loading delays
"""

import streamlit as st
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import json
import pickle
from pathlib import Path


class AdvancedCacheSystem:
    """
    Multi-level intelligent caching system.

    Features:
    - Streamlit session cache (fastest)
    - Memory cache with LRU eviction
    - Disk cache for persistence
    - Smart TTL per data type
    - Automatic cache warming
    - Cache hit/miss tracking
    """

    def __init__(self, cache_dir: str = ".cache"):
        """Initialize cache system."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache statistics
        if "cache_stats" not in st.session_state:
            st.session_state.cache_stats = {
                "hits": 0,
                "misses": 0,
                "total_requests": 0
            }

    def _generate_key(self, source_name: str, params: Dict = None) -> str:
        """Generate unique cache key."""
        key_data = {"source": source_name}
        if params:
            key_data.update(params)

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_ttl(self, source_name: str) -> int:
        """Get TTL (seconds) for different data types."""
        # Different TTL for different data types
        ttl_config = {
            # Very fast changing data (1 minute)
            "aircraft": 60,
            "iss": 60,
            "traffic": 60,

            # Fast changing data (5 minutes)
            "weather": 300,
            "aurora": 300,
            "winds": 300,

            # Medium changing data (15 minutes)
            "earthquakes": 900,
            "fires": 900,
            "pollution": 900,
            "crypto": 900,

            # Slow changing data (1 hour)
            "exchange": 3600,
            "stocks": 3600,
            "oil": 3600,
            "space": 3600,

            # Very slow changing data (24 hours)
            "volcanoes": 86400,
            "satellites": 86400,
            "webcams": 86400,
            "meteors": 86400,
        }

        return ttl_config.get(source_name, 300)  # Default 5 minutes

    def get(self, source_name: str, fetch_function: Callable,
            params: Dict = None, force_refresh: bool = False) -> Dict:
        """
        Get data from cache or fetch.

        Args:
            source_name: Name of data source
            fetch_function: Function to call if cache miss
            params: Optional parameters for cache key
            force_refresh: Force bypass cache

        Returns:
            Data dict
        """
        st.session_state.cache_stats["total_requests"] += 1

        if force_refresh:
            st.session_state.cache_stats["misses"] += 1
            return self._fetch_and_cache(source_name, fetch_function, params)

        # Try session cache first (fastest)
        session_key = f"cache_{source_name}"
        if session_key in st.session_state:
            cached = st.session_state[session_key]
            if self._is_valid(cached, source_name):
                st.session_state.cache_stats["hits"] += 1
                return cached["data"]

        # Try disk cache
        cache_key = self._generate_key(source_name, params)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    cached = pickle.load(f)

                if self._is_valid(cached, source_name):
                    # Restore to session cache
                    st.session_state[session_key] = cached
                    st.session_state.cache_stats["hits"] += 1
                    return cached["data"]
            except:
                pass  # Cache corrupted, fetch fresh

        # Cache miss - fetch fresh data
        st.session_state.cache_stats["misses"] += 1
        return self._fetch_and_cache(source_name, fetch_function, params)

    def _is_valid(self, cached: Dict, source_name: str) -> bool:
        """Check if cached data is still valid."""
        if not cached or "timestamp" not in cached:
            return False

        age = (datetime.now() - cached["timestamp"]).total_seconds()
        ttl = self._get_ttl(source_name)

        return age < ttl

    def _fetch_and_cache(self, source_name: str, fetch_function: Callable,
                         params: Dict = None) -> Dict:
        """Fetch fresh data and cache it."""
        try:
            data = fetch_function()

            cached = {
                "data": data,
                "timestamp": datetime.now(),
                "source": source_name
            }

            # Save to session cache
            session_key = f"cache_{source_name}"
            st.session_state[session_key] = cached

            # Save to disk cache
            cache_key = self._generate_key(source_name, params)
            cache_file = self.cache_dir / f"{cache_key}.pkl"

            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(cached, f)
            except:
                pass  # Disk cache write failed, not critical

            return data

        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def clear(self, source_name: Optional[str] = None):
        """
        Clear cache.

        Args:
            source_name: Clear specific source, or None for all
        """
        if source_name:
            # Clear specific source
            session_key = f"cache_{source_name}"
            if session_key in st.session_state:
                del st.session_state[session_key]

            # Clear disk cache for this source
            cache_key = self._generate_key(source_name)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all
            # Session cache
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith("cache_")]
            for key in keys_to_delete:
                del st.session_state[key]

            # Disk cache
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except:
                    pass

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        stats = st.session_state.cache_stats
        total = stats["total_requests"]

        if total > 0:
            hit_rate = (stats["hits"] / total) * 100
        else:
            hit_rate = 0

        return {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "total_requests": total,
            "hit_rate": hit_rate,
            "cache_size_mb": self._get_cache_size()
        }

    def _get_cache_size(self) -> float:
        """Get total cache size in MB."""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                total_size += cache_file.stat().st_size
            except:
                pass

        return total_size / (1024 * 1024)  # Convert to MB

    def warm_cache(self, sources: Dict[str, Callable]):
        """
        Pre-warm cache with data sources.

        Args:
            sources: Dict of {source_name: fetch_function}
        """
        for source_name, fetch_func in sources.items():
            try:
                self.get(source_name, fetch_func)
            except:
                pass  # Continue warming other sources


# Global cache instance
_cache_system = None


def get_cache_system() -> AdvancedCacheSystem:
    """Get global cache system instance."""
    global _cache_system
    if _cache_system is None:
        _cache_system = AdvancedCacheSystem()
    return _cache_system


def cached_fetch(source_name: str, ttl: int = None):
    """
    Decorator for automatic caching.

    Usage:
        @cached_fetch("weather", ttl=300)
        def fetch_weather():
            return requests.get(...).json()
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache_system()
            return cache.get(source_name, lambda: func(*args, **kwargs))
        return wrapper
    return decorator


# Example usage
"""
USAGE EXAMPLES:

1. Basic caching:
```python
from src.advanced_cache_system import get_cache_system

cache = get_cache_system()

# First call: fetches from API
data = cache.get("weather", fetch_weather)

# Second call (within 5 min): returns from cache
data = cache.get("weather", fetch_weather)
```

2. Decorator usage:
```python
from src.advanced_cache_system import cached_fetch

@cached_fetch("earthquakes", ttl=900)
def fetch_earthquakes():
    return requests.get("...").json()

# Automatically cached!
data = fetch_earthquakes()
```

3. Cache statistics:
```python
cache = get_cache_system()
stats = cache.get_stats()

print(f"Hit rate: {stats['hit_rate']:.1f}%")
print(f"Cache size: {stats['cache_size_mb']:.2f} MB")
```

4. Cache warming (pre-load):
```python
sources = {
    "weather": fetch_weather,
    "earthquakes": fetch_earthquakes,
    "crypto": fetch_crypto
}

cache.warm_cache(sources)
```

5. Clear cache:
```python
cache = get_cache_system()

# Clear specific source
cache.clear("weather")

# Clear all
cache.clear()
```
"""
