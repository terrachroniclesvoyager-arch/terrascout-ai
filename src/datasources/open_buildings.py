"""
Google Open Buildings Client for TerraScout AI
Access to 1.8 billion AI-detected building footprints worldwide

Data Source: Google Open Buildings v3
Coverage: Africa, Asia, Latin America, Caribbean
Resolution: ~1m accuracy from satellite imagery + ML
License: Open Data (CC-BY 4.0)
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Polygon
from typing import Optional, Tuple, List, Dict, Any
import requests
import time
from ..error_handler import with_retry, safe_api_call


class OpenBuildingsClient:
    """
    Client for Google Open Buildings dataset.

    Two access methods:
    1. BigQuery Public Dataset (no auth, SQL queries)
    2. CSV/GeoParquet tiles from Google Cloud Storage (fallback)
    """

    # Dataset info
    DATASET_ID = "google_open_buildings.open_buildings_v3"
    TILES_BASE_URL = "https://sites.research.google/open-buildings/tiles"

    # Coverage regions (simplified)
    REGIONS = {
        "africa": ["016", "017", "018", "019"],  # UN M49 codes
        "asia": ["030", "034", "035", "143", "145"],
        "latin_america": ["013", "029", "005"],
        "caribbean": ["029"]
    }

    def __init__(self):
        """Initialize the Open Buildings client."""
        self.session = requests.Session()
        self._bigquery_available = None

    def check_bigquery_available(self) -> bool:
        """Check if BigQuery API is available (optional dependency)."""
        if self._bigquery_available is not None:
            return self._bigquery_available

        try:
            from google.cloud import bigquery
            # Try to create client (works with Application Default Credentials or public datasets)
            client = bigquery.Client()
            self._bigquery_available = True
        except ImportError:
            st.warning(
                "⚠️ BigQuery client not installed. Install with: `pip install google-cloud-bigquery`\n"
                "Falling back to tile-based access (slower)."
            )
            self._bigquery_available = False
        except Exception as e:
            st.info(f"ℹ️ BigQuery client not configured: {e}. Using tile-based access.")
            self._bigquery_available = False

        return self._bigquery_available

    @with_retry(max_retries=2, initial_delay=1.0)
    def query_buildings_bigquery(
        self,
        bbox: Tuple[float, float, float, float],
        min_area_sqm: float = 5.0,
        max_area_sqm: float = 10000.0,
        confidence_threshold: float = 0.5,
        limit: int = 10000
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Query buildings using BigQuery SQL (fast, scalable).

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            min_area_sqm: Minimum building area (sq meters)
            max_area_sqm: Maximum building area (sq meters)
            confidence_threshold: Minimum ML confidence (0-1)
            limit: Maximum results

        Returns:
            GeoDataFrame with building footprints, or None if query fails
        """
        if not self.check_bigquery_available():
            return None

        try:
            from google.cloud import bigquery
            client = bigquery.Client()

            min_lon, min_lat, max_lon, max_lat = bbox

            # SQL query
            query = f"""
            SELECT
                latitude,
                longitude,
                area_in_meters,
                confidence,
                geometry,
                full_plus_code
            FROM
                `{self.DATASET_ID}`
            WHERE
                longitude >= {min_lon}
                AND longitude <= {max_lon}
                AND latitude >= {min_lat}
                AND latitude <= {max_lat}
                AND area_in_meters >= {min_area_sqm}
                AND area_in_meters <= {max_area_sqm}
                AND confidence >= {confidence_threshold}
            LIMIT {limit}
            """

            # Execute query
            df = client.query(query).to_dataframe()

            if df.empty:
                return gpd.GeoDataFrame()

            # Convert WKT geometry to Shapely
            from shapely import wkt
            df['geometry'] = df['geometry'].apply(wkt.loads)

            # Create GeoDataFrame
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

            return gdf

        except Exception as e:
            st.error(f"❌ BigQuery query failed: {e}")
            return None

    def get_tile_url(self, s2_token: str) -> str:
        """
        Get CSV tile URL for a given S2 cell token.

        Args:
            s2_token: S2 geometry cell token (e.g., "0000_AAAA")

        Returns:
            URL to CSV tile
        """
        # Format: https://sites.research.google/open-buildings/tiles/s2_token.csv.gz
        return f"{self.TILES_BASE_URL}/{s2_token}.csv.gz"

    @with_retry(max_retries=3, initial_delay=2.0)
    def fetch_tile_csv(
        self,
        s2_token: str,
        timeout: int = 30
    ) -> Optional[pd.DataFrame]:
        """
        Fetch a single CSV tile from Google Cloud Storage.

        Args:
            s2_token: S2 cell token
            timeout: Request timeout (seconds)

        Returns:
            DataFrame with building data, or None if failed
        """
        url = self.get_tile_url(s2_token)

        try:
            df = pd.read_csv(url, compression='gzip', timeout=timeout)
            return df
        except Exception as e:
            st.warning(f"⚠️ Failed to fetch tile {s2_token}: {e}")
            return None

    def bbox_to_s2_tokens(
        self,
        bbox: Tuple[float, float, float, float],
        level: int = 4
    ) -> List[str]:
        """
        Convert bounding box to S2 cell tokens (approximate).

        Note: This is a simplified implementation. For production,
        use the s2sphere library for accurate S2 cell covering.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            level: S2 cell level (4-10, lower = larger cells)

        Returns:
            List of S2 cell tokens covering the bbox
        """
        # Placeholder: return common tokens
        # TODO: Implement proper S2 geometry library integration
        st.warning(
            "⚠️ S2 cell token generation not fully implemented. "
            "Install s2sphere for accurate tile selection."
        )

        # Return empty for now (fallback to BigQuery)
        return []

    def search_buildings(
        self,
        bbox: Tuple[float, float, float, float],
        min_area_sqm: float = 5.0,
        max_area_sqm: float = 10000.0,
        confidence_threshold: float = 0.5,
        max_results: int = 10000,
        method: str = "auto"
    ) -> gpd.GeoDataFrame:
        """
        Search for buildings in a bounding box.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            min_area_sqm: Minimum building area
            max_area_sqm: Maximum building area
            confidence_threshold: Minimum confidence (0-1)
            max_results: Maximum results
            method: "bigquery", "tiles", or "auto"

        Returns:
            GeoDataFrame with building footprints

        Usage:
            client = OpenBuildingsClient()
            gdf = client.search_buildings(
                bbox=(-74.1, 40.6, -73.9, 40.8),  # NYC area
                min_area_sqm=10,
                max_area_sqm=100,  # Small structures only
                confidence_threshold=0.7
            )
        """
        # Auto-select method
        if method == "auto":
            method = "bigquery" if self.check_bigquery_available() else "tiles"

        # Try BigQuery first
        if method == "bigquery":
            gdf = self.query_buildings_bigquery(
                bbox=bbox,
                min_area_sqm=min_area_sqm,
                max_area_sqm=max_area_sqm,
                confidence_threshold=confidence_threshold,
                limit=max_results
            )

            if gdf is not None and not gdf.empty:
                return gdf

            # Fallback to tiles if BigQuery failed
            st.info("ℹ️ BigQuery failed, trying tile-based access...")
            method = "tiles"

        # Tile-based fallback
        if method == "tiles":
            st.warning(
                "⚠️ Tile-based access not fully implemented yet. "
                "Install google-cloud-bigquery for optimal performance."
            )
            # TODO: Implement tile fetching with S2 geometry
            return gpd.GeoDataFrame()

        return gpd.GeoDataFrame()

    def filter_small_structures(
        self,
        gdf: gpd.GeoDataFrame,
        max_area_sqm: float = 50.0
    ) -> gpd.GeoDataFrame:
        """
        Filter for small structures (huts, cabins, shelters).

        Args:
            gdf: GeoDataFrame with 'area_in_meters' column
            max_area_sqm: Maximum area threshold (sq meters)

        Returns:
            Filtered GeoDataFrame
        """
        if gdf.empty or 'area_in_meters' not in gdf.columns:
            return gdf

        return gdf[gdf['area_in_meters'] <= max_area_sqm].copy()

    def get_statistics(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Get statistics about detected buildings.

        Args:
            gdf: GeoDataFrame with buildings

        Returns:
            Dict with statistics
        """
        if gdf.empty:
            return {
                "total_count": 0,
                "avg_area": 0,
                "min_area": 0,
                "max_area": 0,
                "avg_confidence": 0
            }

        stats = {
            "total_count": len(gdf),
            "avg_area": gdf['area_in_meters'].mean() if 'area_in_meters' in gdf.columns else 0,
            "min_area": gdf['area_in_meters'].min() if 'area_in_meters' in gdf.columns else 0,
            "max_area": gdf['area_in_meters'].max() if 'area_in_meters' in gdf.columns else 0,
            "avg_confidence": gdf['confidence'].mean() if 'confidence' in gdf.columns else 0,
        }

        # Area distribution
        if 'area_in_meters' in gdf.columns:
            stats["small_structures"] = len(gdf[gdf['area_in_meters'] < 30])  # < 30 sqm
            stats["medium_structures"] = len(gdf[
                (gdf['area_in_meters'] >= 30) & (gdf['area_in_meters'] < 100)
            ])
            stats["large_structures"] = len(gdf[gdf['area_in_meters'] >= 100])

        return stats

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
def get_google_buildings(
    bbox: Tuple[float, float, float, float],
    min_area: float = 5.0,
    max_area: float = 10000.0,
    confidence: float = 0.5
) -> gpd.GeoDataFrame:
    """
    Cached function to get Google Open Buildings.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        min_area: Minimum area (sq meters)
        max_area: Maximum area (sq meters)
        confidence: Minimum confidence (0-1)

    Returns:
        GeoDataFrame with building footprints
    """
    with OpenBuildingsClient() as client:
        return client.search_buildings(
            bbox=bbox,
            min_area_sqm=min_area,
            max_area_sqm=max_area,
            confidence_threshold=confidence
        )
