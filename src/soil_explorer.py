"""
Soil Data Explorer module for TerraScout AI.
Uses the ISRIC SoilGrids REST API (free, no API key) to query
soil properties at any point on Earth: pH, organic carbon, clay/sand/silt
content, bulk density, nitrogen, and more.
"""

import io
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"

# Soil properties available in SoilGrids
SOIL_PROPERTIES = {
    "phh2o": {"name": "pH (H₂O)", "unit": "pH×10", "desc": "Soil acidity/alkalinity", "color": "#06b6d4", "divisor": 10},
    "soc": {"name": "Organic Carbon", "unit": "g/kg", "desc": "Soil organic carbon content", "color": "#10b981", "divisor": 10},
    "clay": {"name": "Clay Content", "unit": "%", "desc": "Clay fraction (< 2μm)", "color": "#f59e0b", "divisor": 10},
    "sand": {"name": "Sand Content", "unit": "%", "desc": "Sand fraction (50-2000μm)", "color": "#ef4444", "divisor": 10},
    "silt": {"name": "Silt Content", "unit": "%", "desc": "Silt fraction (2-50μm)", "color": "#8b5cf6", "divisor": 10},
    "bdod": {"name": "Bulk Density", "unit": "kg/dm³", "desc": "Soil bulk density", "color": "#ec4899", "divisor": 100},
    "cec": {"name": "CEC", "unit": "cmol(c)/kg", "desc": "Cation exchange capacity", "color": "#f97316", "divisor": 10},
    "nitrogen": {"name": "Nitrogen", "unit": "g/kg", "desc": "Total nitrogen content", "color": "#14b8a6", "divisor": 100},
    "cfvo": {"name": "Coarse Fragments", "unit": "%", "desc": "Volumetric coarse fragments", "color": "#64748b", "divisor": 10},
    "ocd": {"name": "Organic C Density", "unit": "kg/m³", "desc": "Organic carbon density", "color": "#22c55e", "divisor": 10},
}

# Depth layers in SoilGrids
DEPTH_LABELS = {
    "0-5cm": "0-5",
    "5-15cm": "5-15",
    "15-30cm": "15-30",
    "30-60cm": "30-60",
    "60-100cm": "60-100",
    "100-200cm": "100-200",
}

# Interesting soil locations for presets
SOIL_PRESETS = {
    "Custom": None,
    "Fertile Plains - Iowa, USA": {"lat": 42.0, "lon": -93.5},
    "Amazon Rainforest, Brazil": {"lat": -3.0, "lon": -60.0},
    "Sahara Desert, Algeria": {"lat": 27.0, "lon": 2.0},
    "Ukraine Black Earth (Chernozem)": {"lat": 49.0, "lon": 32.0},
    "Tuscany, Italy": {"lat": 43.3, "lon": 11.3},
    "Nile Delta, Egypt": {"lat": 30.9, "lon": 31.2},
    "Dutch Polders, Netherlands": {"lat": 52.5, "lon": 5.0},
    "Volcanic Soil - Java, Indonesia": {"lat": -7.5, "lon": 110.4},
    "Permafrost - Siberia, Russia": {"lat": 64.0, "lon": 100.0},
    "Australian Outback": {"lat": -25.0, "lon": 134.0},
}


@st.cache_data(ttl=1800)
def get_soil_data(lat: float, lon: float, properties: list = None) -> dict:
    """Query SoilGrids for soil properties at a point."""
    if properties is None:
        properties = list(SOIL_PROPERTIES.keys())

    params = {
        "lon": lon,
        "lat": lat,
        "property": properties,
        "depth": ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"],
        "value": "mean",
    }

    try:
        resp = requests.get(SOILGRIDS_API, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def _parse_soil_response(data: dict) -> dict:
    """Parse SoilGrids response into a structured dict."""
    result = {}
    properties = data.get("properties", {})
    layers = properties.get("layers", [])

    for layer in layers:
        prop_name = layer.get("name", "")
        depths_data = layer.get("depths", [])

        result[prop_name] = {}
        for depth_entry in depths_data:
            depth_label = depth_entry.get("label", "")
            values = depth_entry.get("values", {})
            mean_val = values.get("mean")
            result[prop_name][depth_label] = mean_val

    return result


def _soil_classification(parsed: dict) -> str:
    """Simple soil texture classification based on clay/sand/silt percentages."""
    clay = parsed.get("clay", {}).get("0-5cm")
    sand = parsed.get("sand", {}).get("0-5cm")
    silt = parsed.get("silt", {}).get("0-5cm")

    if clay is None or sand is None or silt is None:
        return "Unknown"

    # Convert from g/kg to percentage
    clay_pct = clay / 10
    sand_pct = sand / 10
    silt_pct = silt / 10

    if clay_pct > 40:
        return "Clay"
    elif sand_pct > 70:
        return "Sandy"
    elif silt_pct > 60:
        return "Silty"
    elif clay_pct > 25 and sand_pct > 25:
        return "Clay Loam"
    elif sand_pct > 50:
        return "Sandy Loam"
    elif silt_pct > 40:
        return "Silt Loam"
    else:
        return "Loam"


def render_soil_explorer_tab():
    """Main render function for the Soil Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header emerald">
        <h4>Soil Data Explorer</h4>
        <p>Query global soil properties from ISRIC SoilGrids at 250m resolution &mdash; pH, organic carbon, clay/sand/silt content, bulk density, nitrogen. Free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Location Input
    # ══════════════════════════════════════════
    st.markdown("#### Location")

    col1, col2 = st.columns(2)
    with col1:
        soil_lat = st.number_input("Latitude", value=43.3000, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="soil_lat",
                                   help="Latitude in decimal degrees")
    with col2:
        soil_lon = st.number_input("Longitude", value=11.3000, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="soil_lon",
                                   help="Longitude in decimal degrees")

    preset_name = st.selectbox("Interesting Soil Locations", list(SOIL_PRESETS.keys()),
                               key="soil_preset")
    if preset_name != "Custom" and SOIL_PRESETS.get(preset_name):
        p = SOIL_PRESETS[preset_name]
        soil_lat = p["lat"]
        soil_lon = p["lon"]

    # Property selection
    st.markdown("#### Properties to Query")
    selected_props = st.multiselect(
        "Select soil properties",
        list(SOIL_PROPERTIES.keys()),
        default=["phh2o", "soc", "clay", "sand", "silt", "nitrogen"],
        format_func=lambda x: f"{SOIL_PROPERTIES[x]['name']} ({SOIL_PROPERTIES[x]['desc']})",
        key="soil_props",
    )

    if st.button("Query Soil Data", key="soil_search", width="stretch"):
        st.session_state.soil_params = {
            "lat": soil_lat, "lon": soil_lon, "props": selected_props,
        }

    if "soil_params" not in st.session_state:
        st.info("Select a location and soil properties, then click Query to explore soil data.")
        return

    sp = st.session_state.soil_params

    # ══════════════════════════════════════════
    # SECTION 2: Results Overview
    # ══════════════════════════════════════════
    with st.spinner("Querying ISRIC SoilGrids (250m resolution)..."):
        data = get_soil_data(sp["lat"], sp["lon"], sp["props"])

    if data.get("error"):
        st.error(f"API Error: {data['error']}")
        return

    parsed = _parse_soil_response(data)

    if not parsed:
        st.warning("No soil data available at this location. SoilGrids may not cover this area (e.g., oceans, ice caps).")
        return

    st.markdown("---")
    st.markdown("#### Soil Profile Overview")

    # Soil texture classification
    texture = _soil_classification(parsed)

    # Top-level metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Soil Texture", texture)
    with c2:
        ph_val = parsed.get("phh2o", {}).get("0-5cm")
        if ph_val is not None:
            st.metric("Surface pH", f"{ph_val / 10:.1f}")
        else:
            st.metric("Surface pH", "—")
    with c3:
        soc_val = parsed.get("soc", {}).get("0-5cm")
        if soc_val is not None:
            st.metric("Organic C (0-5cm)", f"{soc_val / 10:.1f} g/kg")
        else:
            st.metric("Organic C", "—")
    with c4:
        n_val = parsed.get("nitrogen", {}).get("0-5cm")
        if n_val is not None:
            st.metric("Nitrogen (0-5cm)", f"{n_val / 100:.2f} g/kg")
        else:
            st.metric("Properties", f"{len(parsed)}")

    # ══════════════════════════════════════════
    # SECTION 3: Location Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Sample Location")

    m = folium.Map(location=[sp["lat"], sp["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    folium.CircleMarker(
        location=[sp["lat"], sp["lon"]],
        radius=10,
        color="#10b981",
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.8,
        popup=f"Soil Query: {sp['lat']:.4f}, {sp['lon']:.4f}<br/>Texture: {texture}",
    ).add_to(m)
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=350)

    # ══════════════════════════════════════════
    # SECTION 4: Property Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Soil Properties by Depth")

    # Property cards (surface layer 0-5cm)
    pcols = st.columns(3)
    for i, (prop_key, depths) in enumerate(parsed.items()):
        if prop_key not in SOIL_PROPERTIES:
            continue
        info = SOIL_PROPERTIES[prop_key]
        surface_val = depths.get("0-5cm")
        col = pcols[i % 3]
        with col:
            display_val = f"{surface_val / info['divisor']:.1f}" if surface_val is not None else "—"
            st.markdown(f"""
            <div class="bio-card" style="margin-bottom:0.5rem; padding:0.75rem 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#e8ecf4; font-weight:700; font-size:0.95rem;">{info['name']}</div>
                        <div style="color:#5a6580; font-size:0.75rem;">{info['desc']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{info['color']}; font-weight:800; font-size:1.3rem;">{display_val}</div>
                        <div style="color:#8b97b0; font-size:0.7rem;">{info['unit']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 5: Depth Profile Charts
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Depth Profile Charts")

    depth_order = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    depth_midpoints = [2.5, 10, 22.5, 45, 80, 150]  # cm

    # Create depth profile charts
    num_props = len(parsed)
    if num_props > 0:
        ncols = min(3, num_props)
        nrows = (num_props + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows))
        fig.patch.set_facecolor("#0a0e1a")

        if num_props == 1:
            axes = [axes]
        elif nrows == 1:
            axes = list(axes)
        else:
            axes = [ax for row in axes for ax in row]

        for idx, (prop_key, depths) in enumerate(parsed.items()):
            if prop_key not in SOIL_PROPERTIES:
                continue
            info = SOIL_PROPERTIES[prop_key]
            ax = axes[idx]
            ax.set_facecolor("#0a0e1a")

            values = []
            valid_depths = []
            for d, mid in zip(depth_order, depth_midpoints):
                v = depths.get(d)
                if v is not None:
                    values.append(v / info["divisor"])
                    valid_depths.append(mid)

            if values:
                ax.barh(range(len(valid_depths)), values, color=info["color"], alpha=0.7, height=0.6)
                ax.set_yticks(range(len(valid_depths)))
                ax.set_yticklabels([f"{d} cm" for d in valid_depths], color="#8b97b0", fontsize=8)
                ax.invert_yaxis()
                ax.set_xlabel(f"{info['name']} ({info['unit']})", color="#8b97b0", fontsize=8)
                ax.set_title(info["name"], color="#e8ecf4", fontsize=10, fontweight="bold")

            ax.tick_params(axis="both", colors="#8b97b0", labelsize=8)
            ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")

        # Hide empty subplots
        for idx in range(len(parsed), len(axes)):
            axes[idx].set_visible(False)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ══════════════════════════════════════════
    # SECTION 6: Texture Triangle Info
    # ══════════════════════════════════════════
    clay_data = parsed.get("clay", {})
    sand_data = parsed.get("sand", {})
    silt_data = parsed.get("silt", {})

    if clay_data and sand_data and silt_data:
        st.markdown("---")
        st.markdown("#### Texture Composition by Depth")

        rows = []
        for depth in depth_order:
            c = clay_data.get(depth)
            s = sand_data.get(depth)
            si = silt_data.get(depth)
            if c is not None and s is not None and si is not None:
                rows.append({
                    "Depth": depth,
                    "Clay (%)": f"{c / 10:.1f}",
                    "Sand (%)": f"{s / 10:.1f}",
                    "Silt (%)": f"{si / 10:.1f}",
                })

        if rows:
            df_tex = pd.DataFrame(rows)
            st.dataframe(df_tex, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 7: Download
    # ══════════════════════════════════════════
    st.markdown("---")

    # Build export DataFrame
    export_rows = []
    for prop_key, depths in parsed.items():
        if prop_key not in SOIL_PROPERTIES:
            continue
        info = SOIL_PROPERTIES[prop_key]
        for depth, value in depths.items():
            export_rows.append({
                "property": info["name"],
                "property_code": prop_key,
                "depth": depth,
                "value_raw": value,
                "value": value / info["divisor"] if value is not None else None,
                "unit": info["unit"],
                "latitude": sp["lat"],
                "longitude": sp["lon"],
            })

    df_export = pd.DataFrame(export_rows)

    with st.expander(f"Full Data Table ({len(df_export)} values)", expanded=False):
        st.dataframe(df_export, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df_export.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Soil Data (CSV)",
        data=csv_buf.getvalue(),
        file_name="soil_data.csv",
        mime="text/csv",
        key="soil_download",
    )
