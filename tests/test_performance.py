"""
Performance Benchmarks for TerraScout AI
Tests lazy loading speedup and other optimizations
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_lazy_loading_performance():
    """
    Test lazy loading performance improvement.

    Expected: Module loading should be deferred until first use.
    """
    start_time = time.time()

    # Import module loader
    from src.module_loader import load_module_render_function

    load_time = time.time() - start_time

    # Should load very quickly (<0.5s)
    assert load_time < 0.5, f"Module loader took {load_time:.2f}s (expected <0.5s)"

    print(f"✅ Module loader loaded in {load_time:.3f}s")


def test_module_caching():
    """Test that modules are cached after first load."""
    from src.module_loader import load_module_render_function, _render_function_cache

    # Clear cache
    _render_function_cache.clear()

    # First load
    start = time.time()
    func1 = load_module_render_function("geocoder")
    first_load = time.time() - start

    # Second load (should be cached)
    start = time.time()
    func2 = load_module_render_function("geocoder")
    second_load = time.time() - start

    # Second load should be much faster
    assert second_load < first_load / 10, "Module not properly cached"

    # Should be same function object
    assert func1 is func2

    print(f"✅ First load: {first_load:.3f}s, Cached load: {second_load:.6f}s")


def test_error_handler_performance():
    """Test that error handler doesn't add significant overhead."""
    from src.error_handler import with_retry

    @with_retry(max_retries=0, show_progress=False)
    def fast_function():
        return "success"

    # Measure overhead
    iterations = 100
    start = time.time()
    for _ in range(iterations):
        fast_function()
    total_time = time.time() - start

    avg_time = total_time / iterations

    # Should add minimal overhead (<1ms per call)
    assert avg_time < 0.001, f"Error handler overhead too high: {avg_time*1000:.2f}ms"

    print(f"✅ Error handler overhead: {avg_time*1000:.3f}ms per call")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
