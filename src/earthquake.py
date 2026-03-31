"""
Earthquake Explorer module for TerraScout AI.
Uses the USGS Earthquake API (free, no API key) to display seismic events
on an interactive map with filtering by magnitude, time range, and region.
"""

import io
import html as html_module
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Magnitude color scale
MAG_COLORS = {
    "minor": "#10b981",     # < 3.0 green
    "light": "#f59e0b",     # 3.0-4.9 amber
    "moderate": "#f97316",  # 5.0-5.9 orange
    "strong": "#ef4444",    # 6.0-6.9 red
    "major": "#dc2626",     # 7.0+ dark red
    "great": "#991b1b",     # 8.0+ very dark red
}


def _mag_color(mag: float) -> str:
    if mag < 3.0:
        return MAG_COLORS["minor"]
    elif mag < 5.0:
        return MAG_COLORS["light"]
    elif mag < 6.0:
        return MAG_COLORS["moderate"]
    elif mag < 7.0:
        return MAG_COLORS["strong"]
    elif mag < 8.0:
        return MAG_COLORS["major"]
    return MAG_COLORS["great"]


def _mag_radius(mag: float) -> float:
    if mag < 2.0:
        return 3
    elif mag < 4.0:
        return 5
    elif mag < 6.0:
        return 8
    elif mag < 7.0:
        return 12
    return 16


@st.cache_data(ttl=300)
def search_earthquakes(start_date: str, end_date: str,
                       min_mag: float = 2.5, max_mag: float = 10.0,
                       lat: float = None, lon: float = None,
                       radius_km: int = None,
                       limit: int = 500) -> dict:
    """Search USGS earthquake catalog."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("usgs")
    params = {
        "format": "geojson",
        "starttime": start_date,
        "endtime": end_date,
        "minmagnitude": min_mag,
        "maxmagnitude": max_mag,
        "limit": min(limit, 2000),
        "orderby": "time",
    }
    if lat is not None and lon is not None and radius_km is not None:
        params["latitude"] = lat
        params["longitude"] = lon
        params["maxradiuskm"] = radius_km

    try:
        resp = requests.get(USGS_API, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"type": "FeatureCollection", "features": [], "error": str(e)}


def render_earthquake_tab():
    """Main render function for the Earthquake Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header red">
        <h4>Earthquake Explorer</h4>
        <p>Search and visualize seismic events worldwide from the USGS Earthquake Catalog &mdash; real-time data, free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")

    # Time range
    col_start, col_end, col_mag_min, col_mag_max = st.columns(4)
    default_end = datetime.now().date()
    default_start = default_end - timedelta(days=30)

    with col_start:
        start_date = st.date_input("Start Date", value=default_start, key="eq_start")
    with col_end:
        end_date = st.date_input("End Date", value=default_end, key="eq_end")
    with col_mag_min:
        min_mag = st.number_input("Min Magnitude", value=3.0, min_value=0.0,
                                  max_value=10.0, step=0.5, key="eq_min_mag",
                                  help="Minimum earthquake magnitude (Richter)")
    with col_mag_max:
        max_mag = st.number_input("Max Magnitude", value=10.0, min_value=0.0,
                                  max_value=10.0, step=0.5, key="eq_max_mag")

    # Location filter
    with st.expander("Location Filter (optional)", expanded=False):
        lcol1, lcol2, lcol3 = st.columns(3)
        with lcol1:
            eq_lat = st.number_input("Center Lat", value=0.0, format="%.4f",
                                     min_value=-90.0, max_value=90.0, key="eq_lat")
        with lcol2:
            eq_lon = st.number_input("Center Lon", value=0.0, format="%.4f",
                                     min_value=-180.0, max_value=180.0, key="eq_lon")
        with lcol3:
            eq_radius = st.slider("Radius (km)", 50, 5000, 1000, key="eq_radius",
                                  help="Search radius around center point")
        use_location = st.checkbox("Enable location filter", key="eq_use_loc")

    # Quick presets
    preset = st.selectbox("Quick Presets", [
        "Custom",
        "Last 24 Hours - Significant (M5+)",
        "Last 7 Days - M4+",
        "Last 30 Days - M3+",
        "Pacific Ring of Fire - Last Month",
        "Mediterranean - Last Month",
        "Japan Region - Last Month",
    ], key="eq_preset")

    if preset == "Last 24 Hours - Significant (M5+)":
        start_date = default_end - timedelta(days=1)
        end_date = default_end
        min_mag = 5.0
    elif preset == "Last 7 Days - M4+":
        start_date = default_end - timedelta(days=7)
        min_mag = 4.0
    elif preset == "Last 30 Days - M3+":
        start_date = default_end - timedelta(days=30)
        min_mag = 3.0

    if st.button("Search Earthquakes", key="eq_search", width="stretch"):
        lat_param = eq_lat if use_location else None
        lon_param = eq_lon if use_location else None
        radius_param = eq_radius if use_location else None

        st.session_state.eq_search_params = {
            "start": str(start_date),
            "end": str(end_date),
            "min_mag": min_mag,
            "max_mag": max_mag,
            "lat": lat_param,
            "lon": lon_param,
            "radius": radius_param,
        }

    if "eq_search_params" not in st.session_state:
        st.info("Configure search parameters and click Search to explore earthquake data.")
        return

    params = st.session_state.eq_search_params

    # ══════════════════════════════════════════
    # SECTION 2: Results Overview
    # ══════════════════════════════════════════
    with st.spinner("Fetching earthquake data from USGS..."):
        data = search_earthquakes(
            params["start"], params["end"],
            params["min_mag"], params["max_mag"],
            params.get("lat"), params.get("lon"), params.get("radius")
        )

    if data.get("error"):
        st.error(f"API Error: {data['error']}")
        return

    features = data.get("features", [])
    total = len(features)

    if total == 0:
        st.warning("No earthquakes found matching your criteria. Try adjusting the filters.")
        return

    st.markdown("---")
    st.markdown("#### Results Overview")

    # Stats
    magnitudes = [f["properties"]["mag"] for f in features if f["properties"].get("mag")]
    depths = [f["geometry"]["coordinates"][2] for f in features if len(f["geometry"]["coordinates"]) > 2]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Events", f"{total:,}")
    with c2:
        st.metric("Strongest", f"M{max(magnitudes):.1f}" if magnitudes else "—")
    with c3:
        st.metric("Avg Magnitude", f"M{sum(magnitudes)/len(magnitudes):.1f}" if magnitudes else "—")
    with c4:
        st.metric("Max Depth", f"{max(depths):.0f} km" if depths else "—")

    # ══════════════════════════════════════════
    # SECTION 3: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Seismic Activity Map")

    # Color legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#10b981; font-size:0.8rem;">● M&lt;3 Minor</span>
        <span style="color:#f59e0b; font-size:0.8rem;">● M3-5 Light</span>
        <span style="color:#f97316; font-size:0.8rem;">● M5-6 Moderate</span>
        <span style="color:#ef4444; font-size:0.8rem;">● M6-7 Strong</span>
        <span style="color:#dc2626; font-size:0.8rem;">● M7+ Major</span>
    </div>
    """, unsafe_allow_html=True)

    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    for feat in features[:500]:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        mag = props.get("mag", 0) or 0
        place = props.get("place", "Unknown")
        time_ms = props.get("time", 0)
        depth = coords[2] if len(coords) > 2 else 0

        eq_time = datetime.utcfromtimestamp(time_ms / 1000).strftime("%Y-%m-%d %H:%M UTC") if time_ms else "—"

        safe_place = html_module.escape(str(place))

        popup_html = f"""
        <div style="max-width:220px;">
            <strong>M{mag:.1f}</strong> - {safe_place}<br/>
            <span style="font-size:0.8rem;">Depth: {depth:.1f} km</span><br/>
            <span style="font-size:0.8rem;">{eq_time}</span>
        </div>
        """

        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=_mag_radius(mag),
            color=_mag_color(mag),
            fill=True,
            fill_color=_mag_color(mag),
            fill_opacity=0.6,
            weight=1,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 4: Event List & Data
    # ══════════════════════════════════════════
    st.markdown("---")

    col_list, col_chart = st.columns([1, 1])

    with col_list:
        st.markdown("#### Recent Events")
        for feat in features[:15]:
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            mag = props.get("mag", 0) or 0
            place = props.get("place", "Unknown")
            time_ms = props.get("time", 0)
            depth = coords[2] if len(coords) > 2 else 0
            eq_time = datetime.utcfromtimestamp(time_ms / 1000).strftime("%Y-%m-%d %H:%M") if time_ms else "—"
            color = _mag_color(mag)

            safe_place = html_module.escape(str(place))
            st.markdown(f"""
            <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <div style="width:50px; height:50px; border-radius:50%; background:{color}20;
                            display:flex; align-items:center; justify-content:center;
                            margin-right:0.75rem; flex-shrink:0;">
                    <span style="color:{color}; font-weight:800; font-size:0.9rem;">M{mag:.1f}</span>
                </div>
                <div>
                    <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe_place}</div>
                    <div style="color:#8b97b0; font-size:0.75rem;">Depth: {depth:.1f} km</div>
                    <div style="color:#5a6580; font-size:0.7rem;">{eq_time}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_chart:
        st.markdown("#### Magnitude Distribution")
        if magnitudes:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")

            bins = [0, 2, 3, 4, 5, 6, 7, 8, 10]
            colors = ["#10b981", "#10b981", "#f59e0b", "#f59e0b", "#f97316", "#ef4444", "#dc2626", "#991b1b"]
            ax.hist(magnitudes, bins=bins, color="#06b6d4", edgecolor="#0a0e1a", alpha=0.8)

            ax.set_xlabel("Magnitude", color="#8b97b0", fontsize=10)
            ax.set_ylabel("Count", color="#8b97b0", fontsize=10)
            ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
            ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        st.markdown("#### Depth Distribution")
        if depths:
            fig2, ax2 = plt.subplots(figsize=(6, 3))
            fig2.patch.set_facecolor("#0a0e1a")
            ax2.set_facecolor("#0a0e1a")
            ax2.hist(depths, bins=20, color="#8b5cf6", edgecolor="#0a0e1a", alpha=0.8)
            ax2.set_xlabel("Depth (km)", color="#8b97b0", fontsize=10)
            ax2.set_ylabel("Count", color="#8b97b0", fontsize=10)
            ax2.tick_params(axis="both", colors="#8b97b0", labelsize=9)
            ax2.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
            ax2.set_axisbelow(True)
            for spine in ax2.spines.values():
                spine.set_color("#2a3550")
            fig2.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

    # ══════════════════════════════════════════
    # SECTION 5: Download
    # ══════════════════════════════════════════
    st.markdown("---")
    rows = []
    for feat in features:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        time_ms = props.get("time", 0)
        rows.append({
            "magnitude": props.get("mag"),
            "place": props.get("place", ""),
            "latitude": coords[1],
            "longitude": coords[0],
            "depth_km": coords[2] if len(coords) > 2 else None,
            "time": datetime.utcfromtimestamp(time_ms / 1000).strftime("%Y-%m-%d %H:%M:%S") if time_ms else "",
            "type": props.get("type", ""),
            "status": props.get("status", ""),
            "url": props.get("url", ""),
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} events)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(rows)} Earthquakes (CSV)",
        data=csv_buf.getvalue(),
        file_name="earthquakes.csv",
        mime="text/csv",
        key="eq_download",
    )
