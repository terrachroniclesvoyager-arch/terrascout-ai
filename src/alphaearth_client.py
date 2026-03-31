"""
AlphaEarth + Google Earth Engine Client for TerraScout AI
Geospatial foundation model for similarity search and analysis

AlphaEarth provides:
- 64-dimensional embeddings at 10m resolution
- Cosine similarity search to find similar locations worldwide
- Integration with Google Earth Engine datasets

Dataset: GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
"""

import streamlit as st
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import geopandas as gpd


class AlphaEarthClient:
    """
    Client for AlphaEarth foundation model + Google Earth Engine.

    Use Case: Given a location with specific characteristics (e.g., forest with huts),
    find other similar locations worldwide using embedding similarity.
    """

    # GEE dataset
    EMBEDDING_DATASET = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"

    def __init__(self):
        """Initialize the AlphaEarth client."""
        self._ee_available = None
        self._ee_initialized = False

    def check_ee_available(self) -> bool:
        """Check if Earth Engine is available."""
        if self._ee_available is not None:
            return self._ee_available

        try:
            import ee
            self._ee_available = True
            return True
        except ImportError:
            st.warning(
                "⚠️ Google Earth Engine not installed.\n"
                "Install with: `pip install earthengine-api`"
            )
            self._ee_available = False
            return False

    def initialize_ee(self):
        """Initialize Earth Engine authentication."""
        if self._ee_initialized:
            return True

        if not self.check_ee_available():
            return False

        try:
            import ee

            # Try to initialize (may require authentication)
            try:
                ee.Initialize()
                self._ee_initialized = True
                st.success("✅ Google Earth Engine initialized")
                return True
            except Exception:
                # Try authentication
                st.info("🔐 Earth Engine requires authentication...")
                ee.Authenticate()
                ee.Initialize()
                self._ee_initialized = True
                st.success("✅ Authenticated and initialized")
                return True

        except Exception as e:
            st.error(f"❌ Earth Engine initialization failed: {e}")
            return False

    def get_embedding(
        self,
        lat: float,
        lon: float,
        year: int = 2021
    ) -> Optional[np.ndarray]:
        """
        Get AlphaEarth embedding for a location.

        Args:
            lat: Latitude
            lon: Longitude
            year: Year (2016-2023)

        Returns:
            64-dimensional embedding vector, or None if failed
        """
        if not self.initialize_ee():
            return None

        try:
            import ee

            # Load embedding dataset
            embeddings = ee.ImageCollection(self.EMBEDDING_DATASET).filterDate(
                f'{year}-01-01', f'{year}-12-31'
            ).first()

            # Sample at point
            point = ee.Geometry.Point([lon, lat])
            sample = embeddings.sample(
                region=point,
                scale=10,
                numPixels=1
            ).first()

            # Extract embedding bands
            embedding = []
            for i in range(64):
                value = sample.get(f'embedding_{i}').getInfo()
                embedding.append(value)

            return np.array(embedding)

        except Exception as e:
            st.warning(f"⚠️ Failed to get embedding: {e}")
            return None

    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_similar_locations(
        self,
        reference_lat: float,
        reference_lon: float,
        candidate_locations: List[Tuple[float, float]],
        top_k: int = 20,
        year: int = 2021
    ) -> List[Dict[str, Any]]:
        """
        Find locations similar to a reference location.

        Args:
            reference_lat: Reference latitude
            reference_lon: Reference longitude
            candidate_locations: List of (lat, lon) tuples to compare
            top_k: Number of top results to return
            year: Year for embeddings

        Returns:
            List of dicts with 'lat', 'lon', 'similarity' sorted by similarity

        Usage:
            client = AlphaEarthClient()

            # Reference: Amazon forest with huts
            ref_lat, ref_lon = -3.1, -60.0

            # Candidates: Other forest regions worldwide
            candidates = [
                (-4.5, -71.5),  # Amazon Peru
                (1.5, 21.0),    # Congo Basin
                (0.5, 115.0),   # Borneo
                # ... more locations
            ]

            similar = client.find_similar_locations(
                ref_lat, ref_lon, candidates, top_k=10
            )

            for loc in similar:
                print(f"Lat: {loc['lat']}, Lon: {loc['lon']}, "
                      f"Similarity: {loc['similarity']:.3f}")
        """
        st.info(f"🔍 Finding locations similar to ({reference_lat:.4f}, {reference_lon:.4f})...")

        # Get reference embedding
        ref_embedding = self.get_embedding(reference_lat, reference_lon, year)

        if ref_embedding is None:
            st.error("❌ Failed to get reference embedding")
            return []

        # Calculate similarity for all candidates
        results = []

        with st.spinner(f"Calculating similarity for {len(candidate_locations)} locations..."):
            for i, (lat, lon) in enumerate(candidate_locations):
                if i % 10 == 0:
                    st.text(f"Progress: {i}/{len(candidate_locations)}")

                candidate_embedding = self.get_embedding(lat, lon, year)

                if candidate_embedding is not None:
                    similarity = self.cosine_similarity(ref_embedding, candidate_embedding)

                    results.append({
                        'lat': lat,
                        'lon': lon,
                        'similarity': similarity
                    })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top K
        return results[:top_k]

    def visualize_similar_locations(
        self,
        results: List[Dict[str, Any]],
        reference_location: Optional[Tuple[float, float]] = None
    ):
        """
        Visualize similar locations on a map.

        Args:
            results: Results from find_similar_locations()
            reference_location: Optional (lat, lon) of reference point
        """
        import folium
        from streamlit_folium import st_folium

        if not results:
            st.warning("⚠️ No results to visualize")
            return

        # Create map centered on first result
        m = folium.Map(
            location=[results[0]['lat'], results[0]['lon']],
            zoom_start=2
        )

        # Add reference location (red marker)
        if reference_location:
            folium.Marker(
                location=list(reference_location),
                popup="Reference Location",
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)

        # Add similar locations (green markers with similarity score)
        for i, result in enumerate(results):
            similarity = result['similarity']

            # Color based on similarity
            if similarity > 0.8:
                color = 'darkgreen'
            elif similarity > 0.6:
                color = 'green'
            elif similarity > 0.4:
                color = 'lightgreen'
            else:
                color = 'gray'

            folium.Marker(
                location=[result['lat'], result['lon']],
                popup=f"Rank {i+1}<br>Similarity: {similarity:.3f}",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        st_folium(m, width=None, height=600, key="alphaearth_folium_map")


# Convenience function
@st.cache_data(ttl=86400, show_spinner=False)
def find_similar_areas(
    reference_lat: float,
    reference_lon: float,
    search_grid: List[Tuple[float, float]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Cached function to find similar areas.

    Args:
        reference_lat: Reference latitude
        reference_lon: Reference longitude
        search_grid: Grid of locations to search
        top_k: Number of results

    Returns:
        List of similar locations
    """
    client = AlphaEarthClient()
    return client.find_similar_locations(
        reference_lat, reference_lon, search_grid, top_k
    )
