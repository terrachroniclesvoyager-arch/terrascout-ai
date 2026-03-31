import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

def render_open_buildings_explorer_tab():
    st.markdown("""
    <div class="tab-header cyan">
        <h4>🛖 AI Building Footprints Explorer</h4>
        <p>Instantly find every single structure, hut, or mining camp anywhere on Earth (including the deep Amazon and Congo) using AI-generated building footprints from Google and Microsoft.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        lat = st.number_input("Latitude", value=-3.1190, format="%.4f")
    with col2:
        lon = st.number_input("Longitude", value=-60.0217, format="%.4f")
    with col3:
        layer_choice = st.selectbox(
            "AI Building Database",
            ["Google Open Buildings V3", "Microsoft Building Footprints", "Both (Overlay)"]
        )

    st.markdown("---")

    # Build the map
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles=None)

    # Base Satellite Layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite Base",
        overlay=False,
        max_zoom=20,
        max_native_zoom=17
    ).add_to(m)

    # Add AI Building Layers
    if layer_choice in ["Google Open Buildings V3", "Both (Overlay)"]:
        folium.TileLayer(
            tiles="https://storage.googleapis.com/open-buildings-data/v3/tiles/{z}/{x}/{y}.png",
            attr="Google Open Buildings",
            name="Google Open Buildings (Cyan)",
            overlay=True,
            opacity=0.8,
            max_zoom=20,
            max_native_zoom=15
        ).add_to(m)
        
    if layer_choice in ["Microsoft Building Footprints", "Both (Overlay)"]:
        folium.TileLayer(
            tiles="https://tiles.arcgis.com/tiles/IkktFdUAcY3WrH25/arcgis/rest/services/Microsoft_Building_Footprints/MapServer/tile/{z}/{y}/{x}",
            attr="Microsoft",
            name="Microsoft Building Footprints (Magenta)",
            overlay=True,
            opacity=0.8,
            max_zoom=20,
            max_native_zoom=16
        ).add_to(m)

    # Add a marker for the selected precise point
    folium.Marker(
        [lat, lon],
        popup="Target Center",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Render map
    st_html(m._repr_html_(), height=650)
    
    st.info("💡 **Tip:** Google Open Buildings uses light cyan/blue outlines. Microsoft Building Footprints uses magenta/pink. If you select 'Both', you can compare their AI detections side by side! Zoom in to see the individual structures.")
