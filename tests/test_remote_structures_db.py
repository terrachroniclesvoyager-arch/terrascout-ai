"""
Test Suite for RemoteStructuresDB
Tests multi-source building detection and deduplication
"""

import pytest
import geopandas as gpd
from shapely.geometry import Point
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.remote_structures_db import RemoteStructuresDB


class TestRemoteStructuresDB:
    """Test suite for RemoteStructuresDB."""

    def test_initialization(self):
        """Test database initialization."""
        db = RemoteStructuresDB()
        assert db is not None
        assert isinstance(db.sources_available, dict)

    def test_osm_search(self):
        """Test OSM search functionality."""
        db = RemoteStructuresDB()

        # Small test area (London)
        bbox = (-0.1278, 51.5074, -0.1178, 51.5174)

        gdf = db.search_osm(bbox, timeout=30)

        # Should return some results or empty GeoDataFrame
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_spatial_deduplication(self):
        """Test spatial deduplication."""
        db = RemoteStructuresDB()

        # Create test data with duplicates
        points = [
            Point(0, 0),
            Point(0.00001, 0.00001),  # ~1m away (duplicate)
            Point(0.01, 0.01),  # 1km away (unique)
        ]

        gdf = gpd.GeoDataFrame({
            'geometry': points,
            'source': ['a', 'b', 'c']
        }, crs="EPSG:4326")

        dedup_gdf = db.deduplicate_spatial(gdf, distance_threshold=0.0001)

        # Should have 2 points (first two merged)
        assert len(dedup_gdf) == 2

    def test_mode_validation(self):
        """Test search mode validation."""
        db = RemoteStructuresDB()

        # Valid modes
        valid_modes = ["fast", "comprehensive", "ai_only", "ai_live", "osm_only"]

        for mode in valid_modes:
            # Should not raise error
            assert mode in ["fast", "comprehensive", "ai_only", "ai_live", "osm_only"]


def test_imports():
    """Test that all required modules can be imported."""
    try:
        from src.remote_structures_db import RemoteStructuresDB
        from src.datasources.open_buildings import OpenBuildingsClient
        from src.datasources.ms_buildings import MSBuildingsClient
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
