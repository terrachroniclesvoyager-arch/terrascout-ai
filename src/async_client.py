"""
Async API Client for TerraScout AI
Parallel API calls without blocking UI using ThreadPoolExecutor and aiohttp
"""

import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
import time
from functools import partial


class AsyncAPIClient:
    """
    Client for making parallel API requests without blocking the UI.

    Uses ThreadPoolExecutor for concurrent requests while remaining
    compatible with Streamlit's execution model.
    """

    def __init__(self, max_workers: int = 5, timeout: int = 30):
        """
        Initialize the async API client.

        Args:
            max_workers: Maximum number of concurrent requests
            timeout: Default timeout for requests (seconds)
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_single(
        self,
        url: str,
        method: str = "GET",
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch a single URL.

        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            timeout: Request timeout (uses default if None)
            **kwargs: Additional arguments for requests

        Returns:
            Dict with 'url', 'data', 'error', 'status_code'
        """
        result = {
            "url": url,
            "data": None,
            "error": None,
            "status_code": None,
            "elapsed": None
        }

        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=timeout or self.timeout,
                **kwargs
            )

            result["status_code"] = response.status_code
            result["elapsed"] = time.time() - start_time

            response.raise_for_status()
            result["data"] = response.json()

        except requests.exceptions.Timeout:
            result["error"] = f"Timeout after {timeout or self.timeout}s"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection failed"
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP {response.status_code}: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        return result

    def fetch_parallel(
        self,
        urls: List[str],
        method: str = "GET",
        show_progress: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs in parallel.

        Args:
            urls: List of API endpoint URLs
            method: HTTP method
            show_progress: Show progress bar in Streamlit
            **kwargs: Additional arguments for requests

        Returns:
            List of result dicts

        Usage:
            client = AsyncAPIClient(max_workers=10)
            urls = [f"https://api.example.com/item/{i}" for i in range(100)]
            results = client.fetch_parallel(urls)

            for result in results:
                if result['error']:
                    print(f"Failed: {result['url']} - {result['error']}")
                else:
                    print(f"Success: {result['data']}")
        """
        results = []
        total = len(urls)

        # Create progress tracking
        if show_progress:
            progress_bar = st.progress(0.0, text=f"Fetching 0/{total} URLs...")
            status_text = st.empty()

        # Create a partial function with fixed parameters
        fetch_func = partial(
            self.fetch_single,
            method=method,
            **kwargs
        )

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(fetch_func, url): url for url in urls}

            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
                completed += 1

                if show_progress:
                    progress = completed / total
                    progress_bar.progress(
                        progress,
                        text=f"Fetching {completed}/{total} URLs..."
                    )

                    # Show status
                    success_count = sum(1 for r in results if r['error'] is None)
                    error_count = completed - success_count
                    status_text.text(
                        f"✅ {success_count} successful | ❌ {error_count} failed"
                    )

        # Cleanup progress indicators
        if show_progress:
            progress_bar.empty()
            status_text.empty()

        return results

    def fetch_with_fallback(
        self,
        primary_url: str,
        fallback_urls: List[str],
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch from primary URL, falling back to alternatives if it fails.

        Args:
            primary_url: Primary API endpoint
            fallback_urls: List of fallback endpoints (tried in order)
            method: HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            Result dict from first successful fetch

        Usage:
            client = AsyncAPIClient()
            result = client.fetch_with_fallback(
                primary_url="https://api1.example.com/data",
                fallback_urls=[
                    "https://api2.example.com/data",
                    "https://cache.example.com/data"
                ]
            )
        """
        # Try primary
        result = self.fetch_single(primary_url, method=method, **kwargs)

        if result['error'] is None:
            result['source'] = 'primary'
            return result

        # Try fallbacks
        for i, fallback_url in enumerate(fallback_urls):
            st.warning(f"⚠️ Primary failed, trying fallback {i+1}/{len(fallback_urls)}...")

            result = self.fetch_single(fallback_url, method=method, **kwargs)

            if result['error'] is None:
                result['source'] = f'fallback_{i+1}'
                return result

        # All failed
        result['source'] = 'none'
        st.error(f"❌ All {len(fallback_urls) + 1} endpoints failed")
        return result

    def fetch_batch(
        self,
        url_template: str,
        params_list: List[Dict[str, Any]],
        method: str = "GET",
        show_progress: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch a batch of requests with different parameters.

        Args:
            url_template: URL template (e.g., "https://api.example.com/item/{id}")
            params_list: List of parameter dicts to format URL and add as query params
            method: HTTP method
            show_progress: Show progress bar
            **kwargs: Additional arguments for requests

        Returns:
            List of result dicts

        Usage:
            client = AsyncAPIClient()
            results = client.fetch_batch(
                url_template="https://api.example.com/geocode",
                params_list=[
                    {"q": "London", "limit": 1},
                    {"q": "Paris", "limit": 1},
                    {"q": "Tokyo", "limit": 1}
                ]
            )
        """
        results = []
        total = len(params_list)

        if show_progress:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

        fetch_func = partial(self.fetch_single, method=method, **kwargs)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            # Submit all tasks
            for params in params_list:
                # Format URL if it contains placeholders
                try:
                    url = url_template.format(**params)
                except KeyError:
                    url = url_template

                # Add remaining params as query parameters
                future = executor.submit(fetch_func, url, params=params)
                futures.append(future)

            # Collect results
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1

                if show_progress:
                    progress = completed / total
                    progress_bar.progress(progress)

                    success_count = sum(1 for r in results if r['error'] is None)
                    error_count = completed - success_count
                    status_text.text(
                        f"Batch: {completed}/{total} | ✅ {success_count} | ❌ {error_count}"
                    )

        if show_progress:
            progress_bar.empty()
            status_text.empty()

        return results

    def fetch_with_retry_pool(
        self,
        urls: List[str],
        max_retries: int = 2,
        retry_delay: float = 1.0,
        show_progress: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch URLs with automatic retry for failed requests.

        Args:
            urls: List of URLs to fetch
            max_retries: Maximum retry attempts per URL
            retry_delay: Delay between retries (seconds)
            show_progress: Show progress bar
            **kwargs: Additional arguments for requests

        Returns:
            List of result dicts
        """
        results = []
        retry_queue = list(urls)
        attempt = 0

        while retry_queue and attempt <= max_retries:
            attempt += 1

            if show_progress and attempt > 1:
                st.info(f"🔄 Retry attempt {attempt}/{max_retries + 1} for {len(retry_queue)} failed URLs...")

            # Fetch current batch
            batch_results = self.fetch_parallel(
                retry_queue,
                show_progress=show_progress,
                **kwargs
            )

            # Separate successes and failures
            new_retry_queue = []
            for result in batch_results:
                if result['error'] is None:
                    results.append(result)
                else:
                    if attempt <= max_retries:
                        new_retry_queue.append(result['url'])
                    else:
                        # Max retries exceeded, add failed result
                        results.append(result)

            retry_queue = new_retry_queue

            # Delay before retry
            if retry_queue and attempt <= max_retries:
                time.sleep(retry_delay)

        return results

    def close(self):
        """Close the requests session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()


# Convenience function for quick parallel fetches
def fetch_urls_parallel(
    urls: List[str],
    max_workers: int = 5,
    timeout: int = 30,
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Quick helper to fetch multiple URLs in parallel.

    Args:
        urls: List of URLs to fetch
        max_workers: Maximum concurrent requests
        timeout: Request timeout (seconds)
        show_progress: Show progress bar

    Returns:
        List of result dicts

    Usage:
        urls = ["https://api.example.com/1", "https://api.example.com/2"]
        results = fetch_urls_parallel(urls, max_workers=10)
    """
    with AsyncAPIClient(max_workers=max_workers, timeout=timeout) as client:
        return client.fetch_parallel(urls, show_progress=show_progress)
