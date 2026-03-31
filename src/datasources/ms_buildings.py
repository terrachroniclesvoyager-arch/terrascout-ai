"""
Microsoft Building Footprints Client for TerraScout AI
Access to 1 billion+ AI-detected building footprints worldwide

Data Source: Microsoft Global ML Building Footprints
Coverage: Global (999M+ buildings across 100+ countries)
Resolution: ~1m from Bing Maps satellite imagery + ML
License: Open Data (ODbL)
URL: https://github.com/microsoft/GlobalMLBuildingFootprints
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, box
from typing import Optional, Tuple, List, Dict, Any
import requests
import json
from ..error_handler import with_retry
from ..async_client import AsyncAPIClient


class MSBuildingsClient:
    """
    Client for Microsoft Global ML Building Footprints dataset.

    Access method: Azure Blob Storage (public, no auth)
    Format: GeoJSON tiles organized by quadkey
    """

    # Azure Blob Storage URLs
    BASE_URL = "https://minedbuildings.blob.core.windows.net/global-buildings"
    DATASET_LINKS_URL = "https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv"

    # Regions available
    REGIONS = [
        "Africa", "Asia", "Australia", "Europe", "LatinAmerica",
        "MiddleEast", "NorthAmerica", "Oceania"
    ]

    def __init__(self):
        """Initialize the MS Buildings client."""
        self.session = requests.Session()
        self._region_tiles = {}  # Cache for region tile URLs

    @st.cache_data(ttl=86400, show_spinner=False)
    @staticmethod
    def _fetch_dataset_links() -> pd.DataFrame:
        """
        Fetch the dataset links CSV (contains all tile URLs).

        Returns:
            DataFrame with columns: Location, QuadKey, Url, Size
        """
        try:
            df = pd.read_csv(MSBuildingsClient.DATASET_LINKS_URL)
            return df
        except Exception as e:
            st.error(f"❌ Failed to fetch MS Buildings dataset links: {e}")
            return pd.DataFrame()

    def get_tiles_for_region(self, region: str) -> pd.DataFrame:
        """
        Get all tile URLs for a specific region.

        Args:
            region: Region name (e.g., "Asia", "Africa")

        Returns:
            DataFrame with tile info
        """
        if region in self._region_tiles:
            return self._region_tiles[region]

        # Fetch full dataset links
        links_df = self._fetch_dataset_links()

        if links_df.empty:
            return pd.DataFrame()

        # Filter by region
        region_tiles = links_df[
            links_df['Location'].str.contains(region, case=False, na=False)
        ].copy()

        # Cache
        self._region_tiles[region] = region_tiles

        return region_tiles

    def latlon_to_quadkey(self, lat: float, lon: float, level: int = 9) -> str:
        """
        Convert lat/lon to Bing Maps quadkey.

        Args:
            lat: Latitude
            lon: Longitude
            level: Zoom level (1-23, default 9)

        Returns:
            Quadkey string

        Reference: https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
        """
        import math

        # Clip lat to valid range
        lat = max(min(lat, 85.05112878), -85.05112878)

        # Convert to pixel coordinates
        sin_lat = math.sin(lat * math.pi / 180)
        x = (lon + 180) / 360
        y = 0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)

        # Convert to tile coordinates
        map_size = 1 << level  # 2^level
        tile_x = int(x * map_size)
        tile_y = int(y * map_size)

        # Clip to valid range
        tile_x = max(min(tile_x, map_size - 1), 0)
        tile_y = max(min(tile_y, map_size - 1), 0)

        # Convert tile coordinates to quadkey
        quadkey = ""
        for i in range(level, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if (tile_x & mask) != 0:
                digit += 1
            if (tile_y & mask) != 0:
                digit += 2
            quadkey += str(digit)

        return quadkey

    def bbox_to_quadkeys(
        self,
        bbox: Tuple[float, float, float, float],
        level: int = 9
    ) -> List[str]:
        """
        Get all quadkeys covering a bounding box.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            level: Quadkey zoom level (higher = more tiles, finer resolution)

        Returns:
            List of quadkeys
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Get corner quadkeys
        nw_quadkey = self.latlon_to_quadkey(max_lat, min_lon, level)
        ne_quadkey = self.latlon_to_quadkey(max_lat, max_lon, level)
        sw_quadkey = self.latlon_to_quadkey(min_lat, min_lon, level)
        se_quadkey = self.latlon_to_quadkey(min_lat, max_lon, level)

        # For simplicity, return unique quadkeys
        # TODO: Implement full quadkey covering algorithm
        quadkeys = list(set([nw_quadkey, ne_quadkey, sw_quadkey, se_quadkey]))

        return quadkeys

    @with_retry(max_retries=3, initial_delay=2.0)
    def fetch_tile_geojson(
        self,
        tile_url: str,
        timeout: int = 30
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch a single GeoJSON tile.

        Args:
            tile_url: Full URL to GeoJSON.gz tile
            timeout: Request timeout (seconds)

        Returns:
            GeoDataFrame with building footprints
        """
        try:
            # Download compressed GeoJSON
            response = self.session.get(tile_url, timeout=timeout)
            response.raise_for_status()

            # Parse GeoJSON
            geojson_data = response.json()

            # Convert to GeoDataFrame
            features = geojson_data.get('features', [])
            if not features:
                return gpd.GeoDataFrame()

            # Extract geometries
            geometries = [shape(f['geometry']) for f in features]
            properties = [f.get('properties', {}) for f in features]

            gdf = gpd.GeoDataFrame(
                properties,
                geometry=geometries,
                crs="EPSG:4326"
            )

            return gdf

        except Exception as e:
            st.warning(f"⚠️ Failed to fetch tile {tile_url}: {e}")
            return None

    def search_buildings(
        self,
        bbox: Tuple[float, float, float, float],
        region: Optional[str] = None,
        quadkey_level: int = 9,
        max_tiles: int = 50
    ) -> gpd.GeoDataFrame:
        """
        Search for buildings in a bounding box.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            region: Region hint (e.g., "Asia") - speeds up tile selection
            quadkey_level: Quadkey zoom level (7-12 recommended)
            max_tiles: Maximum tiles to fetch (prevents excessive downloads)

        Returns:
            GeoDataFrame with building footprints

        Usage:
            client = MSBuildingsClient()
            gdf = client.search_buildings(
                bbox=(100.5, 13.7, 100.6, 13.8),  # Bangkok
                region="Asia",
                quadkey_level=10
            )
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Get quadkeys covering bbox
        quadkeys = self.bbox_to_quadkeys(bbox, level=quadkey_level)

        if len(quadkeys) > max_tiles:
            st.warning(
                f"⚠️ Bbox covers {len(quadkeys)} tiles (limit: {max_tiles}). "
                f"Reduce area or lower quadkey_level."
            )
            quadkeys = quadkeys[:max_tiles]

        # Get dataset links
        if region:
            tiles_df = self.get_tiles_for_region(region)
        else:
            tiles_df = self._fetch_dataset_links()

        if tiles_df.empty:
            st.error("❌ No tile data available")
            return gpd.GeoDataFrame()

        # Find matching tiles
        matching_tiles = tiles_df[
            tiles_df['QuadKey'].isin(quadkeys)
        ]['Url'].tolist()

        if not matching_tiles:
            st.info(f"ℹ️ No MS Buildings tiles found for quadkeys: {quadkeys}")
            return gpd.GeoDataFrame()

        st.info(f"📦 Fetching {len(matching_tiles)} MS Buildings tiles...")

        # Fetch tiles in parallel
        gdfs = []
        with AsyncAPIClient(max_workers=5, timeout=30) as client:
            for tile_url in matching_tiles:
                gdf = self.fetch_tile_geojson(tile_url)
                if gdf is not None and not gdf.empty:
                    gdfs.append(gdf)

        # Merge all tiles
        if not gdfs:
            return gpd.GeoDataFrame()

        merged_gdf = pd.concat(gdfs, ignore_index=True)

        # Filter to exact bbox
        bbox_poly = box(min_lon, min_lat, max_lon, max_lat)
        merged_gdf = merged_gdf[
            merged_gdf.geometry.intersects(bbox_poly)
        ].copy()

        return merged_gdf

    def filter_small_structures(
        self,
        gdf: gpd.GeoDataFrame,
        max_area_sqm: float = 50.0
    ) -> gpd.GeoDataFrame:
        """
        Filter for small structures.

        Args:
            gdf: GeoDataFrame with buildings
            max_area_sqm: Maximum area threshold (sq meters)

        Returns:
            Filtered GeoDataFrame
        """
        if gdf.empty:
            return gdf

        # Calculate area in square meters (approximate for small polygons)
        gdf['area_sqm'] = gdf.geometry.area * 111320 * 111320  # Rough conversion

        return gdf[gdf['area_sqm'] <= max_area_sqm].copy()

    def get_statistics(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Get statistics about detected buildings."""
        if gdf.empty:
            return {
                "total_count": 0,
                "avg_area": 0,
                "min_area": 0,
                "max_area": 0
            }

        # Calculate areas if not present
        if 'area_sqm' not in gdf.columns:
            gdf['area_sqm'] = gdf.geometry.area * 111320 * 111320

        return {
            "total_count": len(gdf),
            "avg_area": gdf['area_sqm'].mean(),
            "min_area": gdf['area_sqm'].min(),
            "max_area": gdf['area_sqm'].max(),
            "small_structures": len(gdf[gdf['area_sqm'] < 30]),
            "medium_structures": len(gdf[(gdf['area_sqm'] >= 30) & (gdf['area_sqm'] < 100)]),
            "large_structures": len(gdf[gdf['area_sqm'] >= 100])
        }

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function
@st.cache_data(ttl=3600, show_spinner=False)
def get_ms_buildings(
    bbox: Tuple[float, float, float, float],
    region: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Cached function to get Microsoft buildings.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        region: Region hint for faster tile lookup

    Returns:
        GeoDataFrame with building footprints
    """
    with MSBuildingsClient() as client:
        return client.search_buildings(bbox=bbox, region=region)
