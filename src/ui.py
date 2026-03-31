import streamlit as st
import geopandas as gpd
import pandas as pd
import os
from src.project_manager import ProjectManager
from datetime import datetime

# ─── SAMPLE LOCATIONS ───
SAMPLE_LOCATIONS = {
    "Roma - Colosseo": {"lat": 41.8902, "lon": 12.4922, "zoom": 18},
    "Milano - Duomo": {"lat": 45.4642, "lon": 9.1900, "zoom": 18},
    "Firenze - Centro": {"lat": 43.7696, "lon": 11.2558, "zoom": 17},
    "Venezia - San Marco": {"lat": 45.4343, "lon": 12.3388, "zoom": 17},
    "Napoli - Porto": {"lat": 40.8359, "lon": 14.2488, "zoom": 17},
    "Torino - Centro": {"lat": 45.0703, "lon": 7.6869, "zoom": 17},
    "Palermo - Centro": {"lat": 38.1157, "lon": 13.3615, "zoom": 17},
    "Bologna - Piazza Maggiore": {"lat": 44.4949, "lon": 11.3426, "zoom": 18},
}


def render_history_gallery(pm):
    """Renders the history gallery with project cards."""
    projects = pm.list_projects()

    if not projects:
        st.info("Nessuna analisi salvata. Esegui un'analisi e verra' salvata automaticamente qui!")
        return None

    st.markdown(f"### {len(projects)} Analisi Salvate")

    cols = st.columns(3)
    selected_project = None

    for i, project in enumerate(projects):
        col = cols[i % 3]

        with col:
            with st.container():
                thumb_path = project.get("thumbnail")
                if thumb_path and os.path.exists(thumb_path):
                    st.image(thumb_path, width="stretch")
                else:
                    st.markdown("""
                    <div class="glass-card" style="height:150px; display:flex;
                                align-items:center; justify-content:center; color:#8b97b0; font-size:0.9rem;">
                        No Preview
                    </div>
                    """, unsafe_allow_html=True)

                created = project.get("created_at", "")[:10]
                prompt_text = project.get("prompt", project.get("settings", {}).get("prompt", "—"))
                obj_count = project.get("object_count", 0)

                st.markdown(f"""
                <div class="glass-card" style="padding:0.75rem 1rem; margin-top:0.5rem;">
                    <strong style="color:#e8ecf4;">{prompt_text}</strong><br/>
                    <span style="color:#8b97b0; font-size:0.85rem;">{created} | {obj_count} objects</span>
                </div>
                """, unsafe_allow_html=True)

                col_load, col_del = st.columns(2)
                with col_load:
                    if st.button("Load", key=f"load_{project['id']}"):
                        selected_project = project['id']
                with col_del:
                    if st.button("Del", key=f"del_{project['id']}"):
                        pm.delete_project(project['id'])
                        st.rerun()

                st.markdown("---")

    return selected_project


def render_project_sidebar(pm):
    """Renders the project management section in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Projects")

    projects = pm.list_projects()
    project_names = [f"{p['id']} ({p['created_at'][:10]})" for p in projects]

    new_project_name = st.sidebar.text_input("New Project Name")
    if st.sidebar.button("Save Current Session"):
        if new_project_name and 'results' in st.session_state:
            pid, _ = pm.create_project(new_project_name)
            pm.save_project(pid, {
                "settings": {"prompt": st.session_state.get("last_prompt", "")},
                "image_path": st.session_state.results["image"],
                "mask_path": st.session_state.results["mask"],
                "vector_path": st.session_state.results["vector"],
                "csv_path": st.session_state.results["csv"]
            })
            st.sidebar.success(f"Saved: {pid}")
            st.rerun()

    selected_project = st.sidebar.selectbox("Load Project", ["Select..."] + project_names)
    if selected_project != "Select...":
        pid = selected_project.split(" ")[0]
        if st.sidebar.button("Load"):
            with st.spinner("Loading..."):
                data = pm.load_project(pid)
                if data:
                    files = data.get("files", {})
                    st.session_state.results = {
                        "image": files.get("image.tif"),
                        "mask": files.get("mask.tif"),
                        "csv": files.get("data.csv"),
                        "vector": files.get("vectors.geojson")
                    }
                    st.sidebar.success("Loaded!")
                    st.rerun()


def render_image_uploader():
    """Renders the image upload interface."""
    st.subheader("Upload Aerial/Drone Image")
    uploaded_file = st.file_uploader("Choose a TIFF or JPG file", type=['tif', 'tiff', 'jpg', 'jpeg', 'png'])

    if uploaded_file is not None:
        save_dir = "output/uploads"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.image(file_path, caption="Uploaded Image", width=500)
        return file_path
    return None


def render_sidebar():
    """Renders the sidebar configuration."""
    st.sidebar.title("TerraScout AI")

    st.sidebar.header("Analysis Parameters")
    prompt = st.sidebar.text_input("Text Prompt", value="tree", help="What do you want to detect?")

    box_threshold = st.sidebar.slider("Box Threshold", 0.0, 1.0, 0.24, 0.01, help="Confidence threshold for object detection.")
    text_threshold = st.sidebar.slider("Text Threshold", 0.0, 1.0, 0.24, 0.01, help="Confidence threshold for text association.")

    st.sidebar.header("Map Settings")
    zoom_level = st.sidebar.number_input("Download Zoom Level", 17, 22, 19, help="Higher = better quality (19-20 recommended)")

    # Quick-navigate to sample locations
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Navigate")
    location_name = st.sidebar.selectbox("Go to location", ["-- Select --"] + list(SAMPLE_LOCATIONS.keys()))
    if location_name != "-- Select --":
        loc = SAMPLE_LOCATIONS[location_name]
        st.session_state["map_center"] = [loc["lat"], loc["lon"]]
        st.session_state["map_zoom"] = loc["zoom"]

    st.sidebar.header("Segmentation Settings")
    tile_size = st.sidebar.slider(
        "Tile Size (pixels)",
        min_value=256, max_value=2048, value=1000, step=64,
        help="Size of each tile for segmentation. Larger = fewer tiles but more memory. Recommended: 512-1024"
    )

    overlap = st.sidebar.slider(
        "Tile Overlap (pixels)",
        min_value=0, max_value=256, value=96, step=16,
        help="Overlap between tiles to avoid boundary artifacts. Recommended: 96-128 pixels"
    )

    st.sidebar.info(f"With current settings: ~{(2048//tile_size)**2} tiles for typical area")

    # Model Selector
    model_options = ["MobileSAM - Fast (CPU)", "SAM 1 (LangSAM) - Standard", "SAM 2 - Balanced"]
    model_choice = st.sidebar.radio("AI Model", model_options, index=0)

    if "MobileSAM" in model_choice:
        model_type = "mobile_sam"
    elif "SAM 1" in model_choice:
        model_type = "sam1"
    else:
        model_type = "sam2"

    st.sidebar.caption({
        "mobile_sam": "~0.5s/tile on CPU - lightweight and fast",
        "sam1": "~2s/tile on CPU - good quality",
        "sam2": "~3s/tile on CPU - best quality"
    }.get(model_type, ""))

    st.sidebar.markdown("---")
    st.sidebar.subheader("API Keys (Optional)")
    hf_token = st.sidebar.text_input("Hugging Face Token", type="password", help="For gated models on HuggingFace", key="hf_token_input")

    return prompt, box_threshold, text_threshold, zoom_level, model_type, hf_token, tile_size, overlap


def render_map():
    """Renders the interactive map for ROI selection."""
    import folium
    from folium.plugins import Draw

    # Get center from session state (set by Quick Navigate) or default
    center = st.session_state.get("map_center", [41.9028, 12.4964])
    zoom = st.session_state.get("map_zoom", 6)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None
    )

    # ═══ BASE LAYERS (organized by type) ═══
    base_layers = [
        # Dark & Minimal
        ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "CartoDB Dark", "CartoDB"),
        ("https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png", "Stadia Dark", "Stadia"),
        ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", "Esri Dark Gray", "Esri"),
        # Satellite
        ("https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", "Google Satellite", "Google"),
        ("https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", "Google Hybrid", "Google"),
        ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Esri Satellite", "Esri"),
        # Street
        ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap", "OSM"),
        ("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "CartoDB Light", "CartoDB"),
        ("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", "CartoDB Voyager", "CartoDB"),
        ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", "Esri Street", "Esri"),
        # Terrain & Topo
        ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", "Esri Topographic", "Esri"),
        ("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", "OpenTopoMap", "OpenTopoMap"),
        ("https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png", "Stamen Terrain", "Stadia"),
        ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}", "Esri Physical", "Esri"),
        ("https://services.arcgisonline.com/arcgis/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}", "Esri Hillshade", "Esri"),
        # Special
        ("https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}", "NatGeo World", "Esri/NatGeo"),
        ("https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}", "Esri Ocean", "Esri"),
        ("https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg", "Stamen Watercolor", "Stadia"),
        ("https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}{r}.png", "Stamen Toner", "Stadia"),
        ("https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png", "Humanitarian OSM", "HOT"),
    ]

    for url, name, attr in base_layers:
        folium.TileLayer(tiles=url, attr=attr, name=name, overlay=False).add_to(m)

    # ═══ OVERLAYS ═══
    overlays = [
        ("https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png", "Railways", "OpenRailwayMap"),
        ("https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png", "Sea Marks", "OpenSeaMap"),
        ("https://tile.waymarkedtrails.org/hiking/{z}/{x}/{y}.png", "Hiking Trails", "Waymarked Trails"),
    ]
    for url, name, attr in overlays:
        folium.TileLayer(tiles=url, attr=attr, name=name, overlay=True, show=False).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    draw = Draw(
        export=True,
        draw_options={
            'polyline': False,
            'polygon': False,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'rectangle': True,
        },
        edit_options={'edit': False}
    )

    draw.add_to(m)
    folium.LatLngPopup().add_to(m)

    return m


def display_results(image_path, mask_path, vector_path, bbox=None):
    """Displays the analysis results with styled cards and map."""
    import folium
    import json
    import streamlit.components.v1 as components

    center_lat, center_lon = 41.9028, 12.4964
    zoom_level = 17

    if bbox is not None and len(bbox) == 4:
        center_lon = (bbox[0] + bbox[2]) / 2
        center_lat = (bbox[1] + bbox[3]) / 2
        zoom_level = 18

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite"
    ).add_to(m)

    feature_count = 0
    if vector_path and os.path.exists(vector_path):
        try:
            with open(vector_path, 'r') as f:
                geojson_data = json.load(f)

            feature_count = len(geojson_data.get("features", []))
            folium.GeoJson(
                geojson_data,
                name="Detections",
                style_function=lambda x: {
                    'fillColor': '#06b6d4',
                    'color': '#06b6d4',
                    'weight': 2,
                    'fillOpacity': 0.3
                }
            ).add_to(m)
        except Exception as e:
            st.warning(f"Could not load vectors: {e}")

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=450)

    # Output files as compact cards
    files_html = ""
    if image_path and os.path.exists(image_path):
        files_html += f'<div class="result-card"><span class="file-label">Image</span><br/><span class="file-path">{image_path}</span></div>'
    if mask_path and os.path.exists(mask_path):
        files_html += f'<div class="result-card"><span class="file-label">Mask</span><br/><span class="file-path">{mask_path}</span></div>'
    if vector_path and os.path.exists(vector_path):
        files_html += f'<div class="result-card"><span class="file-label">Vectors &mdash; {feature_count} features</span><br/><span class="file-path">{vector_path}</span></div>'

    if files_html:
        st.markdown(files_html, unsafe_allow_html=True)


def display_dataframe(csv_path):
    """Displays the coordinates dataframe with styling."""
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        with st.expander(f"Detected Coordinates ({len(df)} rows)", expanded=False):
            st.dataframe(df, width="stretch", hide_index=True)
            with open(csv_path, "rb") as f:
                st.download_button(
                    label="Download CSV",
                    data=f,
                    file_name="coordinates.csv",
                    mime="text/csv",
                    key="results_csv_dl",
                )
