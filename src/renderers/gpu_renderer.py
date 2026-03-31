"""
GPU Map Renderer for TerraScout AI
High-performance rendering for 50k+ features using Lonboard (GPU-accelerated)

Lonboard uses deck.gl under the hood for WebGL rendering, supporting:
- Millions of points/polygons
- Interactive panning/zooming without lag
- Hardware-accelerated rendering
"""

import streamlit as st
import geopandas as gpd
import pandas as pd
from typing import Optional, Tuple, Dict, Any, List
import numpy as np


class GPUMapRenderer:
    """
    GPU-accelerated map renderer using Lonboard.

    Auto-switches from Folium to Lonboard when feature count > threshold.
    """

    # Threshold for auto-switching to GPU rendering
    GPU_THRESHOLD = 50000

    def __init__(self):
        """Initialize the GPU renderer."""
        self._lonboard_available = None

    def check_lonboard_available(self) -> bool:
        """Check if Lonboard is installed."""
        if self._lonboard_available is not None:
            return self._lonboard_available

        try:
            import lonboard
            self._lonboard_available = True
            return True
        except ImportError:
            st.warning(
                "⚠️ Lonboard not installed. GPU rendering unavailable.\n"
                "Install with: `pip install lonboard`\n"
                "Falling back to Folium (may be slow for >50k features)."
            )
            self._lonboard_available = False
            return False

    def should_use_gpu(self, feature_count: int) -> bool:
        """
        Determine if GPU rendering should be used.

        Args:
            feature_count: Number of features to render

        Returns:
            True if GPU rendering is recommended
        """
        return feature_count >= self.GPU_THRESHOLD and self.check_lonboard_available()

    def render_points(
        self,
        gdf: gpd.GeoDataFrame,
        radius_scale: float = 1.0,
        fill_color: str = "#06b6d4",
        opacity: float = 0.7,
        title: str = "Point Data"
    ):
        """
        Render point data using Lonboard.

        Args:
            gdf: GeoDataFrame with Point geometries
            radius_scale: Point radius scaling factor
            fill_color: Fill color (hex)
            opacity: Opacity (0-1)
            title: Map title

        Usage:
            renderer = GPUMapRenderer()
            renderer.render_points(gdf, radius_scale=5, fill_color="#ff0000")
        """
        if not self.check_lonboard_available():
            st.error("❌ Lonboard not available. Cannot render with GPU.")
            return

        try:
            from lonboard import Map, ScatterplotLayer
            from lonboard.colormap import apply_continuous_cmap

            st.markdown(f"### {title}")
            st.info(f"🎮 GPU Rendering ({len(gdf):,} points)")

            # Extract coordinates
            coords = np.array([
                [geom.x, geom.y] for geom in gdf.geometry
            ])

            # Create layer
            layer = ScatterplotLayer.from_geopandas(
                gdf,
                get_fill_color=self._hex_to_rgb(fill_color, opacity),
                get_radius=radius_scale * 10,
                radius_min_pixels=2,
                radius_max_pixels=50,
                pickable=True
            )

            # Create map
            m = Map(layers=[layer])

            # Auto-zoom to data bounds
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2

            m.set_view_state(
                longitude=center_lon,
                latitude=center_lat,
                zoom=10
            )

            # Render
            st.pydeck_chart(m)

        except Exception as e:
            st.error(f"❌ GPU rendering failed: {e}")
            st.info("💡 Try reducing feature count or use Folium fallback")

    def render_polygons(
        self,
        gdf: gpd.GeoDataFrame,
        fill_color: str = "#06b6d4",
        opacity: float = 0.5,
        line_width: int = 1,
        title: str = "Polygon Data"
    ):
        """
        Render polygon data using Lonboard.

        Args:
            gdf: GeoDataFrame with Polygon geometries
            fill_color: Fill color (hex)
            opacity: Fill opacity (0-1)
            line_width: Line width (pixels)
            title: Map title
        """
        if not self.check_lonboard_available():
            st.error("❌ Lonboard not available. Cannot render with GPU.")
            return

        try:
            from lonboard import Map, SolidPolygonLayer

            st.markdown(f"### {title}")
            st.info(f"🎮 GPU Rendering ({len(gdf):,} polygons)")

            # Create layer
            layer = SolidPolygonLayer.from_geopandas(
                gdf,
                get_fill_color=self._hex_to_rgb(fill_color, opacity),
                get_line_color=[255, 255, 255, 200],
                get_line_width=line_width,
                pickable=True
            )

            # Create map
            m = Map(layers=[layer])

            # Auto-zoom
            bounds = gdf.total_bounds
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2

            m.set_view_state(
                longitude=center_lon,
                latitude=center_lat,
                zoom=10
            )

            # Render
            st.pydeck_chart(m)

        except Exception as e:
            st.error(f"❌ GPU rendering failed: {e}")

    def render_mixed(
        self,
        gdf: gpd.GeoDataFrame,
        color_column: Optional[str] = None,
        size_column: Optional[str] = None,
        title: str = "Mixed Geometry Data"
    ):
        """
        Render mixed geometry types (auto-detect points/polygons).

        Args:
            gdf: GeoDataFrame with mixed geometries
            color_column: Column to use for coloring (optional)
            size_column: Column to use for sizing (optional)
            title: Map title
        """
        if gdf.empty:
            st.warning("⚠️ No data to render")
            return

        # Split by geometry type
        points_gdf = gdf[gdf.geometry.type == 'Point']
        polygons_gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]

        if not points_gdf.empty:
            self.render_points(points_gdf, title=f"{title} (Points)")

        if not polygons_gdf.empty:
            self.render_polygons(polygons_gdf, title=f"{title} (Polygons)")

    def render_heatmap(
        self,
        gdf: gpd.GeoDataFrame,
        weight_column: Optional[str] = None,
        radius: int = 30,
        intensity: float = 1.0,
        threshold: float = 0.05,
        title: str = "Heatmap"
    ):
        """
        Render heatmap using GPU-accelerated HeatmapLayer.

        Args:
            gdf: GeoDataFrame with Point geometries
            weight_column: Column to use for weighting (optional)
            radius: Radius in pixels
            intensity: Heatmap intensity
            threshold: Minimum threshold for display
            title: Map title
        """
        if not self.check_lonboard_available():
            st.error("❌ Lonboard not available")
            return

        try:
            from lonboard import Map
            import pydeck as pdk

            st.markdown(f"### {title}")
            st.info(f"🎮 GPU Heatmap ({len(gdf):,} points)")

            # Extract coordinates
            coords = [[geom.x, geom.y] for geom in gdf.geometry]

            # Weights
            if weight_column and weight_column in gdf.columns:
                weights = gdf[weight_column].tolist()
                data = [{"coordinates": c, "weight": w} for c, w in zip(coords, weights)]
            else:
                data = [{"coordinates": c} for c in coords]

            # Create heatmap layer
            layer = pdk.Layer(
                "HeatmapLayer",
                data=data,
                get_position="coordinates",
                get_weight="weight" if weight_column else 1,
                radius_pixels=radius,
                intensity=intensity,
                threshold=threshold,
                pickable=False
            )

            # Auto-zoom
            bounds = gdf.total_bounds
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2

            view_state = pdk.ViewState(
                longitude=center_lon,
                latitude=center_lat,
                zoom=10,
                pitch=0,
                bearing=0
            )

            # Render
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style="mapbox://styles/mapbox/dark-v10"
            )

            st.pydeck_chart(deck)

        except Exception as e:
            st.error(f"❌ Heatmap rendering failed: {e}")

    def _hex_to_rgb(self, hex_color: str, opacity: float = 1.0) -> List[int]:
        """
        Convert hex color to RGBA list.

        Args:
            hex_color: Hex color string (e.g., "#06b6d4")
            opacity: Opacity (0-1)

        Returns:
            [R, G, B, A] where A is 0-255
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(opacity * 255)
        return [r, g, b, a]

    @staticmethod
    def render_with_fallback(
        gdf: gpd.GeoDataFrame,
        folium_renderer: callable,
        gpu_threshold: int = 50000,
        **kwargs
    ):
        """
        Render with automatic fallback from GPU to Folium.

        Args:
            gdf: GeoDataFrame to render
            folium_renderer: Function to render with Folium
            gpu_threshold: Feature count threshold for GPU
            **kwargs: Additional arguments for renderers

        Usage:
            def render_folium(gdf):
                m = folium.Map()
                for _, row in gdf.iterrows():
                    folium.Marker([row.geometry.y, row.geometry.x]).add_to(m)
                return m

            GPUMapRenderer.render_with_fallback(
                gdf,
                render_folium,
                gpu_threshold=50000
            )
        """
        feature_count = len(gdf)

        if feature_count >= gpu_threshold:
            st.info(
                f"📊 Large dataset ({feature_count:,} features). "
                f"Switching to GPU-accelerated rendering..."
            )

            renderer = GPUMapRenderer()
            if renderer.check_lonboard_available():
                # Use GPU rendering
                geom_type = gdf.geometry.type.iloc[0] if not gdf.empty else None

                if geom_type == 'Point':
                    renderer.render_points(gdf, **kwargs)
                elif geom_type in ['Polygon', 'MultiPolygon']:
                    renderer.render_polygons(gdf, **kwargs)
                else:
                    renderer.render_mixed(gdf, **kwargs)

                return

        # Fallback to Folium
        st.info(f"🗺️ Rendering with Folium ({feature_count:,} features)")
        folium_map = folium_renderer(gdf, **kwargs)

        try:
            from streamlit_folium import st_folium
            st_folium(folium_map, width=None, height=600, key="gpurend_folium_map1")
        except ImportError:
            st.warning("⚠️ streamlit-folium not installed. Displaying static map.")
            import streamlit.components.v1 as components
            components.html(folium_map._repr_html_(), height=600)


# Convenience function
def auto_render_map(
    gdf: gpd.GeoDataFrame,
    title: str = "Map",
    color: str = "#06b6d4",
    gpu_threshold: int = 50000
):
    """
    Automatically render map with best renderer (GPU or Folium).

    Args:
        gdf: GeoDataFrame to render
        title: Map title
        color: Feature color
        gpu_threshold: Threshold for GPU rendering

    Usage:
        from src.renderers.gpu_renderer import auto_render_map
        auto_render_map(buildings_gdf, title="Buildings", color="#ff0000")
    """
    renderer = GPUMapRenderer()

    if renderer.should_use_gpu(len(gdf)):
        st.success(f"🎮 Using GPU rendering for {len(gdf):,} features")
        renderer.render_mixed(gdf, title=title)
    else:
        st.info(f"🗺️ Using Folium for {len(gdf):,} features")
        # Fallback to standard Folium rendering
        import folium
        from streamlit_folium import st_folium

        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        # Add features
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom.geom_type == 'Point':
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)
            elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                folium.GeoJson(geom, style_function=lambda x: {
                    'fillColor': color,
                    'color': color,
                    'weight': 1,
                    'fillOpacity': 0.5
                }).add_to(m)

        st_folium(m, width=None, height=600, key="gpurend_folium_map2")
