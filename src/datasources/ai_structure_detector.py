"""
AI Structure Detector for TerraScout AI
Real-time detection of unmapped structures using SAM2 (Segment Anything Model 2)

Strategy: Multi-prompt detection with spatial deduplication
Use Case: Find huts, cabins, shelters not in OSM/Google/Microsoft databases
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, box
from typing import Tuple, List, Dict, Any, Optional
import os
import tempfile
from sklearn.cluster import DBSCAN
from ..ui_components import ProgressiveStatus
from ..error_handler import with_retry


class AIStructureDetector:
    """
    Real-time AI detection of structures using SAM2.

    Uses multiple prompts to detect different structure types
    and applies spatial deduplication to remove overlaps.
    """

    # Detection prompts for different structure types
    STRUCTURE_PROMPTS = {
        "building": {
            "prompt": "building",
            "threshold_box": 0.20,
            "threshold_text": 0.20,
            "min_area_sqm": 10
        },
        "hut": {
            "prompt": "hut, cabin, shack, shed",
            "threshold_box": 0.15,  # Lower threshold for small structures
            "threshold_text": 0.15,
            "min_area_sqm": 5
        },
        "shelter": {
            "prompt": "shelter, refuge, camp",
            "threshold_box": 0.18,
            "threshold_text": 0.18,
            "min_area_sqm": 8
        },
        "dwelling": {
            "prompt": "house, dwelling, residence",
            "threshold_box": 0.22,
            "threshold_text": 0.22,
            "min_area_sqm": 15
        }
    }

    def __init__(self, analyzer=None):
        """
        Initialize the AI Structure Detector.

        Args:
            analyzer: GeoAnalyzer instance (uses st.session_state.analyzer if None)
        """
        self.analyzer = analyzer
        if self.analyzer is None and hasattr(st.session_state, 'analyzer'):
            self.analyzer = st.session_state.analyzer

    def check_analyzer_available(self) -> bool:
        """Check if analyzer with SAM2 is available."""
        if self.analyzer is None:
            st.warning("⚠️ GeoAnalyzer not initialized. SAM2 detection unavailable.")
            return False

        try:
            from src.analyzer import SAMGEO_AVAILABLE
            if not SAMGEO_AVAILABLE:
                st.warning("⚠️ SAM GEO not installed. Install with: `pip install segment-geospatial`")
                return False
        except ImportError:
            return False

        return True

    @with_retry(max_retries=1, initial_delay=2.0, show_progress=False)
    def download_satellite_image(
        self,
        bbox: Tuple[float, float, float, float],
        zoom: int = 19,
        source: str = "Esri.WorldImagery"
    ) -> str:
        """
        Download satellite imagery for the bbox.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            zoom: Zoom level (higher = more detail, but larger download)
            source: Tile source

        Returns:
            Path to downloaded GeoTIFF
        """
        if not self.check_analyzer_available():
            raise RuntimeError("Analyzer not available")

        min_lon, min_lat, max_lon, max_lat = bbox

        # Download image
        self.analyzer.download_image(
            bbox=[min_lon, min_lat, max_lon, max_lat],
            zoom=zoom
        )

        return self.analyzer.image_path

    def detect_structures_single_prompt(
        self,
        image_path: str,
        prompt_config: Dict[str, Any],
        model_type: str = "sam2"
    ) -> gpd.GeoDataFrame:
        """
        Detect structures using a single prompt.

        Args:
            image_path: Path to GeoTIFF
            prompt_config: Prompt configuration dict
            model_type: SAM model type

        Returns:
            GeoDataFrame with detected structures
        """
        try:
            # Split image into tiles
            self.analyzer.split_image(tile_size=1000, overlap=100)

            # Run SAM2 prediction
            mask_path = self.analyzer.analyze(
                text_prompt=prompt_config["prompt"],
                box_threshold=prompt_config["threshold_box"],
                text_threshold=prompt_config["threshold_text"],
                model_type=model_type,
                merge_output=True
            )

            # Process results to GeoDataFrame
            gdf, csv_path = self.analyzer.process_results()

            if gdf is None or gdf.empty:
                return gpd.GeoDataFrame()

            # Filter by minimum area
            if 'area_sqm' not in gdf.columns and 'geometry' in gdf.columns:
                # Calculate area in square meters (approximate)
                gdf['area_sqm'] = gdf.geometry.area * 111320 * 111320

            min_area = prompt_config.get("min_area_sqm", 5)
            gdf = gdf[gdf['area_sqm'] >= min_area].copy()

            # Add metadata
            gdf['detection_prompt'] = prompt_config["prompt"]
            gdf['source'] = 'sam2'

            return gdf

        except Exception as e:
            st.warning(f"⚠️ Detection failed for prompt '{prompt_config['prompt']}': {e}")
            return gpd.GeoDataFrame()

    def detect_structures_multi_prompt(
        self,
        image_path: str,
        prompt_types: List[str] = ["building", "hut"],
        model_type: str = "sam2"
    ) -> gpd.GeoDataFrame:
        """
        Detect structures using multiple prompts.

        Args:
            image_path: Path to GeoTIFF
            prompt_types: List of prompt type keys
            model_type: SAM model type

        Returns:
            Deduplicated GeoDataFrame with all detections
        """
        status = ProgressiveStatus("AI Structure Detection")
        gdfs = []

        status.start_stage("Multi-prompt detection", total_items=len(prompt_types))

        for i, prompt_type in enumerate(prompt_types):
            if prompt_type not in self.STRUCTURE_PROMPTS:
                st.warning(f"⚠️ Unknown prompt type: {prompt_type}")
                continue

            prompt_config = self.STRUCTURE_PROMPTS[prompt_type]

            status.update_progress(
                i + 1,
                f"Detecting with prompt: {prompt_config['prompt']}"
            )

            gdf = self.detect_structures_single_prompt(
                image_path=image_path,
                prompt_config=prompt_config,
                model_type=model_type
            )

            if not gdf.empty:
                gdfs.append(gdf)

        status.complete_stage()

        # Merge all results
        if not gdfs:
            status.finalize(success=False)
            return gpd.GeoDataFrame()

        status.start_stage("Merging detections", total_items=1)
        merged_gdf = pd.concat(gdfs, ignore_index=True)
        status.update_progress(1, f"Merged {len(merged_gdf):,} detections")
        status.complete_stage()

        # Spatial deduplication
        if len(merged_gdf) > 1:
            status.start_stage("Deduplicating overlaps", total_items=1)
            original_count = len(merged_gdf)
            merged_gdf = self.deduplicate_spatial(merged_gdf)
            duplicates = original_count - len(merged_gdf)
            status.update_progress(
                1,
                f"Removed {duplicates:,} overlaps ({len(merged_gdf):,} unique)"
            )
            status.complete_stage()

        status.finalize(success=True)

        return merged_gdf

    def deduplicate_spatial(
        self,
        gdf: gpd.GeoDataFrame,
        distance_threshold: float = 0.00005  # ~5.5 meters at equator
    ) -> gpd.GeoDataFrame:
        """
        Remove spatial duplicates using DBSCAN clustering.

        Args:
            gdf: GeoDataFrame with detections
            distance_threshold: Distance threshold in degrees

        Returns:
            Deduplicated GeoDataFrame
        """
        if gdf.empty or len(gdf) < 2:
            return gdf

        # Extract centroids
        centroids = np.array([
            [geom.centroid.x, geom.centroid.y]
            for geom in gdf.geometry
        ])

        # DBSCAN clustering
        clustering = DBSCAN(eps=distance_threshold, min_samples=1).fit(centroids)
        gdf['cluster'] = clustering.labels_

        # Keep largest detection in each cluster
        if 'area_sqm' in gdf.columns:
            dedup_gdf = gdf.sort_values('area_sqm', ascending=False).groupby('cluster').first()
        else:
            dedup_gdf = gdf.groupby('cluster').first()

        dedup_gdf = dedup_gdf.reset_index(drop=True)

        # Remove temporary column
        if 'cluster' in dedup_gdf.columns:
            dedup_gdf = dedup_gdf.drop(columns=['cluster'])

        return dedup_gdf

    def detect_in_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        zoom: int = 19,
        prompt_types: List[str] = ["building", "hut", "shelter"],
        model_type: str = "sam2",
        max_area_km2: float = 5.0
    ) -> gpd.GeoDataFrame:
        """
        Detect structures in a bounding box using real-time SAM2 analysis.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            zoom: Satellite imagery zoom level
            prompt_types: List of prompt types to use
            model_type: SAM model type
            max_area_km2: Maximum area to analyze (safety limit)

        Returns:
            GeoDataFrame with detected structures

        Usage:
            detector = AIStructureDetector()
            gdf = detector.detect_in_bbox(
                bbox=(-74.1, 40.6, -73.9, 40.8),
                prompt_types=["hut", "shelter"],
                zoom=19
            )
        """
        if not self.check_analyzer_available():
            st.error("❌ AI detection not available. Check dependencies.")
            return gpd.GeoDataFrame()

        min_lon, min_lat, max_lon, max_lat = bbox

        # Calculate area
        lat_dist = (max_lat - min_lat) * 111.32
        lon_dist = (max_lon - min_lon) * 111.32 * np.cos(np.radians((min_lat + max_lat) / 2))
        area_km2 = lat_dist * lon_dist

        if area_km2 > max_area_km2:
            st.warning(
                f"⚠️ Area too large ({area_km2:.1f} km²). Maximum: {max_area_km2} km².\n"
                f"Reduce bbox size or increase max_area_km2 parameter."
            )
            return gpd.GeoDataFrame()

        try:
            # Download satellite imagery
            with st.spinner(f"📡 Downloading satellite imagery ({area_km2:.2f} km²)..."):
                image_path = self.download_satellite_image(bbox, zoom=zoom)

            st.info(f"🤖 Running AI detection with {len(prompt_types)} prompts...")

            # Multi-prompt detection
            gdf = self.detect_structures_multi_prompt(
                image_path=image_path,
                prompt_types=prompt_types,
                model_type=model_type
            )

            if not gdf.empty:
                st.success(f"✅ AI detected {len(gdf):,} structures")

            return gdf

        except Exception as e:
            st.error(f"❌ AI detection failed: {e}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
            return gpd.GeoDataFrame()

    def get_statistics(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Get statistics about AI detections."""
        if gdf.empty:
            return {"total": 0}

        stats = {
            "total": len(gdf),
            "avg_area": gdf['area_sqm'].mean() if 'area_sqm' in gdf.columns else 0,
            "min_area": gdf['area_sqm'].min() if 'area_sqm' in gdf.columns else 0,
            "max_area": gdf['area_sqm'].max() if 'area_sqm' in gdf.columns else 0,
        }

        # By prompt breakdown
        if 'detection_prompt' in gdf.columns:
            stats['by_prompt'] = gdf['detection_prompt'].value_counts().to_dict()

        # Size categories
        if 'area_sqm' in gdf.columns:
            stats['tiny'] = len(gdf[gdf['area_sqm'] < 10])  # < 10 m²
            stats['small'] = len(gdf[(gdf['area_sqm'] >= 10) & (gdf['area_sqm'] < 30)])
            stats['medium'] = len(gdf[(gdf['area_sqm'] >= 30) & (gdf['area_sqm'] < 100)])
            stats['large'] = len(gdf[gdf['area_sqm'] >= 100])

        return stats


# Convenience function
def detect_structures_ai(
    bbox: Tuple[float, float, float, float],
    prompt_types: List[str] = ["building", "hut"],
    zoom: int = 19
) -> gpd.GeoDataFrame:
    """
    Quick helper to detect structures using AI.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        prompt_types: Detection prompts to use
        zoom: Satellite imagery zoom

    Returns:
        GeoDataFrame with AI-detected structures
    """
    detector = AIStructureDetector()
    return detector.detect_in_bbox(bbox=bbox, prompt_types=prompt_types, zoom=zoom)
