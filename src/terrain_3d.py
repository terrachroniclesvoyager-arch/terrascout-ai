"""
3D Terrain Viewer for TerraScout AI.
Interactive 3D terrain visualization using Open Topo Data and PyDeck.
"""

import json
import logging
import math
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

logger = logging.getLogger(__name__)


OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

ANALYSIS_PRESETS = {
    "Custom": None,
    "Rome, Italy": {"lat": 41.90, "lon": 12.50},
    "Grand Canyon, USA": {"lat": 36.11, "lon": -112.11},
    "Swiss Alps - Jungfrau": {"lat": 46.56, "lon": 7.97},
    "Mount Etna, Sicily": {"lat": 37.75, "lon": 14.99},
    "Mount Kilimanjaro": {"lat": -3.07, "lon": 37.35},
    "Yellowstone, Wyoming": {"lat": 44.43, "lon": -110.59},
    "Fjords of Norway": {"lat": 61.20, "lon": 6.75},
    "Dead Sea, Israel": {"lat": 31.50, "lon": 35.50},
}


@st.cache_data(ttl=3600, show_spinner="Fetching elevation grid...")
def fetch_terrain_grid(lat, lon, radius_deg=0.05, grid_size=20):
    """Fetch dense elevation grid from Open Topo Data. Returns list of point dicts."""
    points = []
    lats = np.linspace(lat - radius_deg, lat + radius_deg, grid_size)
    lons = np.linspace(lon - radius_deg, lon + radius_deg, grid_size)
    
    for la in lats:
        for lo in lons:
            points.append({"lat": round(la, 6), "lon": round(lo, 6)})
    
    results = []
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        locations = "|".join(f"{p['lat']},{p['lon']}" for p in batch)
        try:
            resp = requests.get(OPEN_TOPO_API, params={"locations": locations}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for r in data.get("results", []):
                    elev = r.get("elevation")
                    loc = r.get("location", {})
                    if elev is not None and loc:
                        results.append({
                            "lat": loc.get("lat", 0),
                            "lon": loc.get("lng", 0),
                            "elevation": elev,
                        })
        except Exception as e:
            logger.warning(f"Elevation batch fetch error: {e}")
            continue
    
    return results


def _elevation_color(elev, min_e, max_e):
    """Map elevation to RGB color (green -> yellow -> red)."""
    if max_e == min_e:
        return [100, 200, 100]
    t = (elev - min_e) / (max_e - min_e)
    if t < 0.5:
        r = int(255 * (t * 2))
        g = 200
        b = 50
    else:
        r = 255
        g = int(200 * (1 - (t - 0.5) * 2))
        b = 50
    return [r, g, b, 200]


def render_terrain_3d_tab():
    st.markdown("""
    <div class="tab-header violet">
        <h4>🏔️ 3D Terrain Viewer</h4>
        <p>Interactive 3D terrain visualization powered by Open Topo Data elevation grid</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="t3d_preset")
    
    preset_data = ANALYSIS_PRESETS.get(preset)
    default_lat = preset_data["lat"] if preset_data else 41.90
    default_lon = preset_data["lon"] if preset_data else 12.50
    
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude", -90.0, 90.0, default_lat, step=0.01, key="t3d_lat", format="%.4f")
        with c2:
            lon = st.number_input("Longitude", -180.0, 180.0, default_lon, step=0.01, key="t3d_lon", format="%.4f")
    
    # Advanced settings
    with st.expander("⚙️ 3D Settings"):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            grid_size = st.slider("Grid Resolution", 10, 30, 20, key="t3d_grid")
        with sc2:
            exaggeration = st.slider("Vertical Exaggeration", 1, 50, 10, key="t3d_exag")
        with sc3:
            radius = st.slider("Radius (degrees)", 0.01, 0.20, 0.05, step=0.01, key="t3d_radius")
    
    if st.button("🏔️ Generate 3D Terrain", type="primary", use_container_width=True):
        with st.spinner("Fetching elevation data..."):
            grid_data = fetch_terrain_grid(lat, lon, radius_deg=radius, grid_size=grid_size)
        
        if not grid_data:
            st.error("Could not fetch elevation data. Try a different location or smaller grid.")
        else:
            st.session_state["t3d_results"] = {
                "grid_data": grid_data, "lat": lat, "lon": lon,
                "radius": radius, "exaggeration": exaggeration,
                "grid_size": grid_size,
            }

    if "t3d_results" in st.session_state:
        r = st.session_state["t3d_results"]
        grid_data = r["grid_data"]
        _lat, _lon = r["lat"], r["lon"]
        _radius = r["radius"]
        _exag = r["exaggeration"]
        _gs = r["grid_size"]
        
        df = pd.DataFrame(grid_data)
        min_elev = df["elevation"].min()
        max_elev = df["elevation"].max()
        avg_elev = df["elevation"].mean()
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Min Elevation", f"{min_elev:.0f} m")
        with m2:
            st.metric("Max Elevation", f"{max_elev:.0f} m")
        with m3:
            st.metric("Avg Elevation", f"{avg_elev:.0f} m")
        with m4:
            st.metric("Grid Points", f"{len(df)}")
        
        # Color mapping
        df["color"] = df["elevation"].apply(lambda e: _elevation_color(e, min_elev, max_elev))
        df["height"] = (df["elevation"] - min_elev) * _exag
        
        # PyDeck 3D visualization
        view_state = pdk.ViewState(
            latitude=_lat,
            longitude=_lon,
            zoom=max(10, 14 - int(_radius * 100)),
            pitch=45,
            bearing=0,
        )
        
        column_layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["lon", "lat"],
            get_elevation="height",
            elevation_scale=1,
            radius=max(30, int(_radius * 111000 / _gs * 0.4)),
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )
        
        deck = pdk.Deck(
            layers=[column_layer],
            initial_view_state=view_state,
            tooltip={"text": "Elevation: {elevation} m\nLat: {lat}\nLon: {lon}"},
            map_style="mapbox://styles/mapbox/dark-v10",
        )
        
        st.pydeck_chart(deck, use_container_width=True, key="t3d_pydeck")
        
        # Relief summary
        st.markdown("#### Elevation Profile Summary")
        relief = max_elev - min_elev
        st.info(f"**Total Relief:** {relief:.0f} m | **Area:** ~{_radius*2*111:.1f} x {_radius*2*111*math.cos(math.radians(_lat)):.1f} km")
        
        # Download
        csv_data = df[["lat", "lon", "elevation"]].to_csv(index=False)
        st.download_button("📥 Download Elevation Grid (CSV)", data=csv_data, file_name=f"terrain_3d_{_lat:.2f}_{_lon:.2f}.csv", mime="text/csv")
