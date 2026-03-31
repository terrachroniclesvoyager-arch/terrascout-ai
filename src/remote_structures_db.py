"""
Remote Structures Database for TerraScout AI
Unified aggregator for finding ALL remote structures from multiple data sources

Data Sources (in priority order):
1. SAM2 Live Detection - Real-time AI analysis of satellite imagery
2. Google Open Buildings - 1.8B AI-detected buildings (Africa, Asia, LatAm)
3. Microsoft Building Footprints - 1B+ ML-detected buildings (Global)
4. OpenStreetMap - Community-mapped structures (Global, incomplete)

Strategy: Multi-source fusion with spatial deduplication
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, box
from shapely import wkt
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN
from ..ui_components import ProgressiveStatus
from ..error_handler import ErrorAggregator


class RemoteStructuresDB:
    """
    Unified database for remote structure detection.

    Combines multiple data sources with intelligent deduplication.
    """

    def __init__(self):
        """Initialize the remote structures database."""
        self.sources_available = self._check_available_sources()

    def _check_available_sources(self) -> Dict[str, bool]:
        """Check which data sources are available."""
        sources = {
            "osm": True,  # Always available (uses requests)
            "google": False,
            "microsoft": False,
            "sam2": False
        }

        # Check Google Open Buildings
        try:
            from .datasources.open_buildings import OpenBuildingsClient
            sources["google"] = True
        except ImportError:
            pass

        # Check Microsoft Buildings
        try:
            from .datasources.ms_buildings import MSBuildingsClient
            sources["microsoft"] = True
        except ImportError:
            pass

        # Check SAM2
        try:
            from .datasources.ai_structure_detector import AIStructureDetector
            if hasattr(st.session_state, 'analyzer'):
                sources["sam2"] = True
        except Exception:
            pass

        return sources

    def search_sam2(
        self,
        bbox: Tuple[float, float, float, float],
        prompt_types: List[str] = ["building", "hut", "shelter"],
        zoom: int = 19
    ) -> gpd.GeoDataFrame:
        """
        Search for structures using SAM2 AI detection (real-time).

        Args:
            bbox: Bounding box
            prompt_types: Detection prompts
            zoom: Satellite imagery zoom level

        Returns:
            GeoDataFrame with AI-detected structures
        """
        if not self.sources_available.get("sam2"):
            return gpd.GeoDataFrame()

        try:
            from .datasources.ai_structure_detector import AIStructureDetector

            detector = AIStructureDetector()
            gdf = detector.detect_in_bbox(
                bbox=bbox,
                prompt_types=prompt_types,
                zoom=zoom
            )

            if not gdf.empty:
                gdf['source'] = 'sam2'

            return gdf

        except Exception as e:
            st.warning(f"⚠️ SAM2 AI detection failed: {e}")
            return gpd.GeoDataFrame()

    def search_osm(
        self,
        bbox: Tuple[float, float, float, float],
        timeout: int = 60
    ) -> gpd.GeoDataFrame:
        """
        Search OSM for structures using Overpass API.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            timeout: API timeout (seconds)

        Returns:
            GeoDataFrame with OSM structures
        """
        try:
            from .overpass_client import OverpassClient

            client = OverpassClient()

            # Query for buildings, ruins, shelters, huts
            query = f"""
            [out:json][timeout:{timeout}][bbox:{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}];
            (
              way["building"];
              way["ruins"="yes"];
              way["amenity"="shelter"];
              node["building"];
              node["ruins"="yes"];
            );
            out geom;
            """

            results = client.query(query)

            if not results:
                return gpd.GeoDataFrame()

            # Convert to GeoDataFrame
            features = []
            for elem in results.get('elements', []):
                geom_type = elem.get('type')

                # Extract geometry
                if geom_type == 'node':
                    lat, lon = elem.get('lat'), elem.get('lon')
                    geom = Point(lon, lat)
                elif geom_type == 'way':
                    coords = [(nd['lon'], nd['lat']) for nd in elem.get('geometry', [])]
                    if len(coords) >= 3:
                        from shapely.geometry import Polygon
                        geom = Polygon(coords)
                    else:
                        continue
                else:
                    continue

                features.append({
                    'geometry': geom,
                    'source': 'osm',
                    'osm_id': elem.get('id'),
                    'building': elem.get('tags', {}).get('building', 'yes'),
                    'name': elem.get('tags', {}).get('name'),
                    **elem.get('tags', {})
                })

            if not features:
                return gpd.GeoDataFrame()

            gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
            return gdf

        except Exception as e:
            st.warning(f"⚠️ OSM search failed: {e}")
            return gpd.GeoDataFrame()

    def search_google(
        self,
        bbox: Tuple[float, float, float, float],
        min_area_sqm: float = 5.0,
        max_area_sqm: float = 10000.0,
        confidence: float = 0.5
    ) -> gpd.GeoDataFrame:
        """
        Search Google Open Buildings.

        Args:
            bbox: Bounding box
            min_area_sqm: Minimum area (sq meters)
            max_area_sqm: Maximum area (sq meters)
            confidence: Minimum ML confidence

        Returns:
            GeoDataFrame with Google buildings
        """
        if not self.sources_available.get("google"):
            return gpd.GeoDataFrame()

        try:
            from .datasources.open_buildings import OpenBuildingsClient

            with OpenBuildingsClient() as client:
                gdf = client.search_buildings(
                    bbox=bbox,
                    min_area_sqm=min_area_sqm,
                    max_area_sqm=max_area_sqm,
                    confidence_threshold=confidence
                )

                if not gdf.empty:
                    gdf['source'] = 'google'

                return gdf

        except Exception as e:
            st.warning(f"⚠️ Google Open Buildings search failed: {e}")
            return gpd.GeoDataFrame()

    def search_microsoft(
        self,
        bbox: Tuple[float, float, float, float],
        region: Optional[str] = None
    ) -> gpd.GeoDataFrame:
        """
        Search Microsoft Building Footprints.

        Args:
            bbox: Bounding box
            region: Region hint (e.g., "Asia")

        Returns:
            GeoDataFrame with Microsoft buildings
        """
        if not self.sources_available.get("microsoft"):
            return gpd.GeoDataFrame()

        try:
            from .datasources.ms_buildings import MSBuildingsClient

            with MSBuildingsClient() as client:
                gdf = client.search_buildings(bbox=bbox, region=region)

                if not gdf.empty:
                    gdf['source'] = 'microsoft'

                return gdf

        except Exception as e:
            st.warning(f"⚠️ Microsoft Buildings search failed: {e}")
            return gpd.GeoDataFrame()

    def deduplicate_spatial(
        self,
        gdf: gpd.GeoDataFrame,
        distance_threshold: float = 0.0001  # ~11 meters at equator
    ) -> gpd.GeoDataFrame:
        """
        Remove spatial duplicates using DBSCAN clustering.

        Args:
            gdf: GeoDataFrame with 'source' and 'geometry' columns
            distance_threshold: Distance threshold in degrees (~11m = 0.0001°)

        Returns:
            Deduplicated GeoDataFrame (keeps highest priority source)
        """
        if gdf.empty or len(gdf) < 2:
            return gdf

        # Source priority (lower = higher priority)
        priority_map = {
            'sam2': 1,
            'google': 2,
            'microsoft': 3,
            'osm': 4
        }

        gdf['priority'] = gdf['source'].map(priority_map).fillna(999)

        # Extract centroids for clustering
        centroids = np.array([
            [geom.centroid.x, geom.centroid.y]
            for geom in gdf.geometry
        ])

        # DBSCAN clustering
        clustering = DBSCAN(eps=distance_threshold, min_samples=1).fit(centroids)
        gdf['cluster'] = clustering.labels_

        # Keep highest priority building in each cluster
        dedup_gdf = gdf.sort_values('priority').groupby('cluster').first().reset_index(drop=True)

        # Remove temporary columns
        dedup_gdf = dedup_gdf.drop(columns=['priority', 'cluster'])

        return dedup_gdf

    def search_all_sources(
        self,
        bbox: Tuple[float, float, float, float],
        mode: str = "fast",
        min_area_sqm: float = 5.0,
        max_area_sqm: float = 10000.0,
        region_hint: Optional[str] = None,
        deduplicate: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Search all available sources and merge results.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            mode: Search mode
                - "fast": OSM + Google (if available)
                - "comprehensive": OSM + Google + Microsoft
                - "ai_only": Google + Microsoft only
                - "ai_live": Real-time SAM2 detection (slow, most accurate)
                - "osm_only": OSM only (legacy mode)
            min_area_sqm: Minimum building area (for AI sources)
            max_area_sqm: Maximum building area (for AI sources)
            region_hint: Region hint for faster tile lookup (e.g., "Asia")
            deduplicate: Apply spatial deduplication

        Returns:
            Unified GeoDataFrame with all detected structures

        Usage:
            db = RemoteStructuresDB()
            gdf = db.search_all_sources(
                bbox=(-74.1, 40.6, -73.9, 40.8),
                mode="comprehensive",
                max_area_sqm=50  # Small structures only
            )
        """
        status = ProgressiveStatus("Remote Structure Search")
        errors = ErrorAggregator()
        gdfs = []

        # OSM search (except ai_only mode)
        if mode != "ai_only":
            status.start_stage("Searching OpenStreetMap", total_items=1)
            try:
                osm_gdf = self.search_osm(bbox)
                if not osm_gdf.empty:
                    gdfs.append(osm_gdf)
                    status.update_progress(1, f"Found {len(osm_gdf):,} OSM structures")
            except Exception as e:
                errors.add("OSM search", e)
            status.complete_stage()

        # Google Open Buildings (except osm_only mode)
        if mode in ["fast", "comprehensive", "ai_only"] and self.sources_available.get("google"):
            status.start_stage("Searching Google Open Buildings", total_items=1)
            try:
                google_gdf = self.search_google(
                    bbox=bbox,
                    min_area_sqm=min_area_sqm,
                    max_area_sqm=max_area_sqm
                )
                if not google_gdf.empty:
                    gdfs.append(google_gdf)
                    status.update_progress(1, f"Found {len(google_gdf):,} Google buildings")
            except Exception as e:
                errors.add("Google Open Buildings search", e)
            status.complete_stage()

        # Microsoft Buildings (comprehensive or ai_only mode)
        if mode in ["comprehensive", "ai_only"] and self.sources_available.get("microsoft"):
            status.start_stage("Searching Microsoft Building Footprints", total_items=1)
            try:
                ms_gdf = self.search_microsoft(bbox=bbox, region=region_hint)
                if not ms_gdf.empty:
                    gdfs.append(ms_gdf)
                    status.update_progress(1, f"Found {len(ms_gdf):,} Microsoft buildings")
            except Exception as e:
                errors.add("Microsoft Buildings search", e)
            status.complete_stage()

        # SAM2 Live Detection (ai_live mode only)
        if mode == "ai_live" and self.sources_available.get("sam2"):
            status.start_stage("SAM2 Real-Time AI Detection", total_items=1)

            # Determine prompts based on size filter
            if max_area_sqm <= 50:
                prompt_types = ["hut", "shelter"]  # Focus on small structures
            elif max_area_sqm <= 200:
                prompt_types = ["building", "hut", "shelter"]
            else:
                prompt_types = ["building", "dwelling"]

            st.info(f"🤖 Running SAM2 live detection with prompts: {', '.join(prompt_types)}")

            try:
                sam2_gdf = self.search_sam2(
                    bbox=bbox,
                    prompt_types=prompt_types,
                    zoom=19
                )
                if not sam2_gdf.empty:
                    gdfs.append(sam2_gdf)
                    status.update_progress(1, f"SAM2 detected {len(sam2_gdf):,} structures")
            except Exception as e:
                errors.add("SAM2 AI detection", e)
            status.complete_stage()

        # Merge all results
        if not gdfs:
            status.finalize(success=False)
            if errors.has_errors():
                errors.display_summary()
            st.warning("⚠️ No structures found from any source")
            return gpd.GeoDataFrame()

        status.start_stage("Merging results", total_items=len(gdfs))
        merged_gdf = pd.concat(gdfs, ignore_index=True)
        status.update_progress(len(gdfs), f"Merged {len(merged_gdf):,} total structures")
        status.complete_stage()

        # Deduplication
        if deduplicate and len(merged_gdf) > 1:
            status.start_stage("Removing duplicates", total_items=1)
            original_count = len(merged_gdf)
            merged_gdf = self.deduplicate_spatial(merged_gdf)
            duplicates_removed = original_count - len(merged_gdf)
            status.update_progress(
                1,
                f"Removed {duplicates_removed:,} duplicates ({len(merged_gdf):,} unique)"
            )
            status.complete_stage()

        status.finalize(success=True)

        # Display errors if any
        if errors.has_errors():
            with st.expander("⚠️ Some sources had errors"):
                errors.display_summary()

        return merged_gdf

    def get_summary_stats(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Get summary statistics from search results.

        Args:
            gdf: GeoDataFrame with search results

        Returns:
            Dict with statistics
        """
        if gdf.empty:
            return {"total": 0}

        stats = {
            "total": len(gdf),
            "by_source": gdf['source'].value_counts().to_dict() if 'source' in gdf.columns else {}
        }

        # Area statistics (if available)
        if 'area_in_meters' in gdf.columns:
            stats["avg_area"] = gdf['area_in_meters'].mean()
            stats["small_structures"] = len(gdf[gdf['area_in_meters'] < 30])
        elif 'area_sqm' in gdf.columns:
            stats["avg_area"] = gdf['area_sqm'].mean()
            stats["small_structures"] = len(gdf[gdf['area_sqm'] < 30])

        return stats
