"""
Map Factory for TerraScout AI
Standardized Folium map creation to eliminate code duplication across 30+ modules
"""

try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from typing import Optional, List, Tuple, Dict, Any
import branca.colormap as cm


class MapFactory:
    """
    Factory class for creating standardized Folium maps.

    Reduces code duplication and ensures consistent styling across all modules.
    """

    # Default TerraScout theme colors
    THEME = {
        "primary": "#06b6d4",  # Cyan
        "secondary": "#8b5cf6",  # Violet
        "success": "#10b981",  # Emerald
        "warning": "#f59e0b",  # Amber
        "danger": "#ef4444",  # Red
        "dark": "#0f172a",  # Slate-900
        "light": "#e2e8f0",  # Slate-200
    }

    # Common base tile layers
    TILE_LAYERS = {
        "satellite": {
            "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attr": "Esri WorldImagery",
            "name": "Satellite"
        },
        "osm": {
            "tiles": "OpenStreetMap",
            "attr": "OpenStreetMap",
            "name": "OpenStreetMap"
        },
        "cartodb_dark": {
            "tiles": "CartoDB dark_matter",
            "attr": "CartoDB",
            "name": "Dark"
        },
        "cartodb_positron": {
            "tiles": "CartoDB positron",
            "attr": "CartoDB",
            "name": "Light"
        },
        "terrain": {
            "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
            "attr": "Esri World Terrain",
            "name": "Terrain"
        },
        "topo": {
            "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            "attr": "Esri World Topo",
            "name": "Topographic"
        },
    }

    @classmethod
    def create_base_map(
        cls,
        center: Tuple[float, float] = (0, 0),
        zoom: int = 2,
        tile_layer: str = "osm",
        prefer_canvas: bool = True,
        **kwargs
    ) -> folium.Map:
        """
        Create a base Folium map with TerraScout styling.

        Args:
            center: (lat, lon) tuple for map center
            zoom: Initial zoom level (1-18)
            tile_layer: Base tile layer ("satellite", "osm", "cartodb_dark", etc.)
            prefer_canvas: Use Canvas renderer for better performance with many markers
            **kwargs: Additional arguments passed to folium.Map()

        Returns:
            Configured folium.Map object

        Usage:
            m = MapFactory.create_base_map(
                center=(51.5074, -0.1278),
                zoom=10,
                tile_layer="satellite"
            )
        """
        # Get tile configuration
        tile_config = cls.TILE_LAYERS.get(tile_layer, cls.TILE_LAYERS["osm"])

        # Create map
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=tile_config["tiles"],
            attr=tile_config["attr"],
            prefer_canvas=prefer_canvas,
            **kwargs
        )

        return m

    @classmethod
    def add_layer_control(
        cls,
        m: folium.Map,
        additional_layers: Optional[List[str]] = None
    ) -> folium.Map:
        """
        Add layer control with common base layers.

        Args:
            m: Folium map object
            additional_layers: List of additional tile layer names to include

        Returns:
            Map with layer control added
        """
        # Add common alternative base layers
        base_layers = ["satellite", "osm", "cartodb_dark", "terrain"]
        if additional_layers:
            base_layers.extend(additional_layers)

        for layer_name in base_layers:
            if layer_name in cls.TILE_LAYERS:
                tile_config = cls.TILE_LAYERS[layer_name]
                folium.TileLayer(
                    tiles=tile_config["tiles"],
                    attr=tile_config["attr"],
                    name=tile_config["name"],
                    overlay=False,
                    control=True
                ).add_to(m)

        # Add layer control
        folium.LayerControl(position='topright', collapsed=False).add_to(m)

        return m

    @classmethod
    def add_search(cls, m: folium.Map) -> folium.Map:
        """Add geocoding search box to map."""
        plugins.Geocoder(
            collapsed=False,
            position='topleft',
            placeholder='Search location...'
        ).add_to(m)
        return m

    @classmethod
    def add_fullscreen(cls, m: folium.Map) -> folium.Map:
        """Add fullscreen button to map."""
        plugins.Fullscreen(
            position='topleft',
            title='Enter fullscreen',
            title_cancel='Exit fullscreen',
            force_separate_button=True
        ).add_to(m)
        return m

    @classmethod
    def add_measure_control(cls, m: folium.Map) -> folium.Map:
        """Add measurement tool to map."""
        plugins.MeasureControl(
            position='bottomleft',
            primary_length_unit='kilometers',
            secondary_length_unit='miles',
            primary_area_unit='sqkilometers',
            secondary_area_unit='acres'
        ).add_to(m)
        return m

    @classmethod
    def add_draw_control(cls, m: folium.Map) -> folium.Map:
        """Add drawing tools to map."""
        plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': True,
                'polygon': True,
                'rectangle': True,
                'circle': True,
                'marker': True,
                'circlemarker': False
            }
        ).add_to(m)
        return m

    @classmethod
    def add_minimap(cls, m: folium.Map) -> folium.Map:
        """Add minimap overview."""
        plugins.MiniMap(
            tile_layer=cls.TILE_LAYERS["osm"]["tiles"],
            position='bottomright',
            width=150,
            height=150,
            collapsed_width=25,
            collapsed_height=25,
            zoom_level_offset=-5
        ).add_to(m)
        return m

    @classmethod
    def add_marker(
        cls,
        m: folium.Map,
        location: Tuple[float, float],
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        icon: Optional[str] = None,
        icon_color: str = "blue",
        prefix: str = "fa",
        **kwargs
    ) -> folium.Map:
        """
        Add a marker to the map with custom styling.

        Args:
            m: Folium map object
            location: (lat, lon) tuple
            popup: Popup HTML content
            tooltip: Tooltip text
            icon: Font Awesome icon name (e.g., "star", "flag")
            icon_color: Icon color
            prefix: Icon prefix ("fa", "glyphicon")
            **kwargs: Additional arguments for folium.Marker()

        Returns:
            Map with marker added
        """
        marker_kwargs = {"location": location}

        if popup:
            marker_kwargs["popup"] = folium.Popup(popup, max_width=300)

        if tooltip:
            marker_kwargs["tooltip"] = tooltip

        if icon:
            marker_kwargs["icon"] = folium.Icon(
                icon=icon,
                prefix=prefix,
                color=icon_color
            )

        marker_kwargs.update(kwargs)
        folium.Marker(**marker_kwargs).add_to(m)

        return m

    @classmethod
    def add_circle_marker(
        cls,
        m: folium.Map,
        location: Tuple[float, float],
        radius: float = 10,
        color: str = "#06b6d4",
        fill: bool = True,
        fill_opacity: float = 0.6,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        **kwargs
    ) -> folium.Map:
        """
        Add a circle marker to the map.

        Args:
            m: Folium map object
            location: (lat, lon) tuple
            radius: Radius in pixels
            color: Border color
            fill: Whether to fill the circle
            fill_opacity: Fill opacity (0-1)
            popup: Popup HTML content
            tooltip: Tooltip text
            **kwargs: Additional arguments for folium.CircleMarker()

        Returns:
            Map with circle marker added
        """
        marker_kwargs = {
            "location": location,
            "radius": radius,
            "color": color,
            "fill": fill,
            "fill_color": color,
            "fill_opacity": fill_opacity
        }

        if popup:
            marker_kwargs["popup"] = folium.Popup(popup, max_width=300)

        if tooltip:
            marker_kwargs["tooltip"] = tooltip

        marker_kwargs.update(kwargs)
        folium.CircleMarker(**marker_kwargs).add_to(m)

        return m

    @classmethod
    def add_heatmap(
        cls,
        m: folium.Map,
        data: List[Tuple[float, float]],
        radius: int = 15,
        blur: int = 15,
        max_zoom: int = 13,
        gradient: Optional[Dict[float, str]] = None,
        name: str = "Heat Map"
    ) -> folium.Map:
        """
        Add a heatmap layer to the map.

        Args:
            m: Folium map object
            data: List of (lat, lon) tuples or (lat, lon, weight) tuples
            radius: Heatmap radius
            blur: Heatmap blur
            max_zoom: Maximum zoom level for heatmap
            gradient: Custom color gradient {0.0: 'color1', 1.0: 'color2'}
            name: Layer name

        Returns:
            Map with heatmap added
        """
        if not gradient:
            gradient = {
                0.0: 'blue',
                0.5: 'lime',
                0.7: 'yellow',
                1.0: 'red'
            }

        plugins.HeatMap(
            data=data,
            radius=radius,
            blur=blur,
            max_zoom=max_zoom,
            gradient=gradient,
            name=name
        ).add_to(m)

        return m

    @classmethod
    def add_marker_cluster(
        cls,
        m: folium.Map,
        name: str = "Markers",
        overlay: bool = True,
        control: bool = True
    ) -> plugins.MarkerCluster:
        """
        Add a marker cluster group for efficient rendering of many markers.

        Args:
            m: Folium map object
            name: Cluster layer name
            overlay: Whether this is an overlay layer
            control: Show in layer control

        Returns:
            MarkerCluster object (add markers to this)

        Usage:
            cluster = MapFactory.add_marker_cluster(m, name="Cities")
            for lat, lon in locations:
                folium.Marker([lat, lon]).add_to(cluster)
        """
        marker_cluster = plugins.MarkerCluster(
            name=name,
            overlay=overlay,
            control=control
        )
        marker_cluster.add_to(m)
        return marker_cluster

    @classmethod
    def create_colormap(
        cls,
        values: List[float],
        colormap_name: str = "viridis",
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        caption: str = "Legend"
    ) -> cm.LinearColormap:
        """
        Create a colormap for value-based coloring.

        Args:
            values: List of values to map
            colormap_name: Matplotlib colormap name
            vmin: Minimum value (auto if None)
            vmax: Maximum value (auto if None)
            caption: Legend caption

        Returns:
            LinearColormap object

        Usage:
            colormap = MapFactory.create_colormap(
                values=[1, 2, 3, 4, 5],
                colormap_name="RdYlGn",
                caption="Temperature (°C)"
            )
            color = colormap(value)
        """
        if not values:
            vmin, vmax = 0, 1
        else:
            if vmin is None:
                vmin = min(values)
            if vmax is None:
                vmax = max(values)

        colormap = cm.LinearColormap(
            colors=colormap_name,
            vmin=vmin,
            vmax=vmax,
            caption=caption
        )

        return colormap

    @classmethod
    def create_full_featured_map(
        cls,
        center: Tuple[float, float] = (0, 0),
        zoom: int = 2,
        tile_layer: str = "osm",
        enable_search: bool = True,
        enable_fullscreen: bool = True,
        enable_measure: bool = True,
        enable_draw: bool = False,
        enable_minimap: bool = False,
        enable_layer_control: bool = True
    ) -> folium.Map:
        """
        Create a fully-featured map with all common plugins.

        Args:
            center: (lat, lon) tuple for map center
            zoom: Initial zoom level
            tile_layer: Base tile layer
            enable_search: Add geocoding search
            enable_fullscreen: Add fullscreen button
            enable_measure: Add measurement tool
            enable_draw: Add drawing tools
            enable_minimap: Add minimap overview
            enable_layer_control: Add layer control

        Returns:
            Fully configured Folium map

        Usage:
            m = MapFactory.create_full_featured_map(
                center=(40.7128, -74.0060),
                zoom=10,
                tile_layer="satellite",
                enable_draw=True
            )
        """
        # Create base map
        m = cls.create_base_map(center=center, zoom=zoom, tile_layer=tile_layer)

        # Add plugins
        if enable_search:
            cls.add_search(m)

        if enable_fullscreen:
            cls.add_fullscreen(m)

        if enable_measure:
            cls.add_measure_control(m)

        if enable_draw:
            cls.add_draw_control(m)

        if enable_minimap:
            cls.add_minimap(m)

        if enable_layer_control:
            cls.add_layer_control(m)

        return m
