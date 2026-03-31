"""
Weather Radar module for TerraScout AI.
Real-time precipitation radar and satellite infrared imagery from RainViewer — free, no API key.
"""

import logging
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

logger = logging.getLogger(__name__)

RAINVIEWER_API = "https://api.rainviewer.com/public/weather-maps.json"

# ── Location presets ──
PRESETS = {
    "World": {"lat": 30, "lon": 0, "zoom": 3},
    "Europe": {"lat": 48, "lon": 10, "zoom": 5},
    "North America": {"lat": 40, "lon": -95, "zoom": 4},
    "South America": {"lat": -15, "lon": -55, "zoom": 4},
    "East Asia": {"lat": 35, "lon": 120, "zoom": 5},
    "SE Asia": {"lat": 5, "lon": 110, "zoom": 5},
    "Australia": {"lat": -25, "lon": 135, "zoom": 5},
    "Africa": {"lat": 5, "lon": 20, "zoom": 4},
    "Middle East": {"lat": 30, "lon": 45, "zoom": 5},
    "Italy": {"lat": 42, "lon": 12.5, "zoom": 6},
}

# ── Color schemes for radar tiles ──
COLOR_SCHEMES = {
    "Original": 1,
    "Universal Blue": 2,
    "TITAN": 3,
    "TWC": 4,
    "Meteored": 5,
    "NEXRAD L3": 6,
    "Rainbow": 7,
    "Dark Sky": 8,
}

# ── Radar intensity legend colors (approximate dBZ ranges) ──
RADAR_LEGEND = [
    ("Light Rain", "#88ddff"),
    ("Moderate Rain", "#00bb00"),
    ("Heavy Rain", "#ffff00"),
    ("Very Heavy", "#ff8800"),
    ("Extreme", "#ff0000"),
    ("Hail/Intense", "#cc00cc"),
]


@st.cache_data(ttl=120)
def fetch_radar_data() -> dict:
    """Fetch the RainViewer maps index (radar + satellite frame metadata)."""
    try:
        resp = requests.get(RAINVIEWER_API, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"RainViewer API error: {e}")
        return {"error": str(e)}


def _ts_label(ts: int) -> str:
    """Convert a Unix timestamp to a readable label."""
    try:
        return datetime.utcfromtimestamp(ts).strftime("%H:%M %d %b UTC")
    except Exception:
        return str(ts)


def _build_radar_map(
    host: str,
    frame_path: str,
    frame_ts: int,
    lat: float,
    lon: float,
    zoom: int,
    color_scheme: int,
    opacity: float,
    mode: str,
    prev_frame_path: str = None,
    show_comparison: bool = False,
    prev_opacity: float = 0.3,
):
    """Build a Folium map with radar or satellite IR overlay tiles."""
    import folium

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
    )

    # Dark base layer
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # Construct tile URL based on mode
    if mode == "Satellite Infrared":
        tile_url = f"{host}{frame_path}/256/{{z}}/{{x}}/{{y}}/0/0_0.png"
        layer_name = f"Satellite IR — {_ts_label(frame_ts)}"
    else:
        tile_url = f"{host}{frame_path}/256/{{z}}/{{x}}/{{y}}/{color_scheme}/1_1.png"
        layer_name = f"Precipitation Radar — {_ts_label(frame_ts)}"

    # Optional comparison layer (previous frame, lower opacity)
    if show_comparison and prev_frame_path:
        if mode == "Satellite Infrared":
            prev_url = f"{host}{prev_frame_path}/256/{{z}}/{{x}}/{{y}}/0/0_0.png"
        else:
            prev_url = f"{host}{prev_frame_path}/256/{{z}}/{{x}}/{{y}}/{color_scheme}/1_1.png"

        folium.TileLayer(
            tiles=prev_url,
            attr="RainViewer (previous)",
            name="Previous Frame",
            overlay=True,
            opacity=prev_opacity,
        ).add_to(m)

    # Main radar/satellite overlay
    folium.TileLayer(
        tiles=tile_url,
        attr="RainViewer",
        name=layer_name,
        overlay=True,
        opacity=opacity,
    ).add_to(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def render_weather_radar_tab():
    """Main render function for the Weather Radar tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Weather Radar</h4>
        <p>Real-time precipitation radar and satellite infrared imagery from RainViewer &mdash; free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Controls
    # ══════════════════════════════════════════
    st.markdown("#### Radar Settings")

    col_mode, col_preset = st.columns(2)

    with col_mode:
        mode = st.radio(
            "Mode",
            ["Precipitation Radar", "Satellite Infrared"],
            horizontal=True,
            key="wr_mode",
        )

    with col_preset:
        preset_name = st.selectbox(
            "Location Preset",
            list(PRESETS.keys()),
            index=0,
            key="wr_preset",
        )

    preset = PRESETS[preset_name]

    # Custom coordinates
    with st.expander("Custom Coordinates", expanded=False):
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            custom_lat = st.number_input(
                "Latitude", value=float(preset["lat"]),
                min_value=-90.0, max_value=90.0, format="%.4f",
                key="wr_lat",
            )
        with ccol2:
            custom_lon = st.number_input(
                "Longitude", value=float(preset["lon"]),
                min_value=-180.0, max_value=180.0, format="%.4f",
                key="wr_lon",
            )
        use_custom = st.checkbox("Use custom coordinates", key="wr_use_custom")

    # Visual settings
    col_color, col_opacity = st.columns(2)

    with col_color:
        if mode == "Precipitation Radar":
            color_name = st.selectbox(
                "Color Scheme",
                list(COLOR_SCHEMES.keys()),
                index=0,
                key="wr_color",
            )
            color_scheme = COLOR_SCHEMES[color_name]
        else:
            st.info("Satellite IR uses a fixed color palette.")
            color_scheme = 0  # unused for satellite

    with col_opacity:
        opacity = st.slider(
            "Overlay Opacity", min_value=0.3, max_value=1.0,
            value=0.7, step=0.05, key="wr_opacity",
        )

    # Comparison toggle
    show_comparison = st.checkbox(
        "Show previous frame as comparison layer",
        value=False,
        key="wr_compare",
    )

    # ── Load button ──
    if st.button("Load Radar", key="wr_load", width="stretch"):
        st.session_state.wr_loaded = True

    if not st.session_state.get("wr_loaded"):
        st.info("Configure settings and click **Load Radar** to view precipitation data.")
        return

    # ══════════════════════════════════════════
    # SECTION 2: Fetch data
    # ══════════════════════════════════════════
    with st.spinner("Fetching radar data from RainViewer..."):
        data = fetch_radar_data()

    if data.get("error"):
        st.error(f"RainViewer API error: {data['error']}")
        return

    host = data.get("host", "https://tilecache.rainviewer.com")
    radar_data = data.get("radar", {})
    satellite_data = data.get("satellite", {})

    past_frames = radar_data.get("past", [])
    nowcast_frames = radar_data.get("nowcast", [])
    ir_frames = satellite_data.get("infrared", [])

    # Validate frames
    if mode == "Precipitation Radar" and not past_frames:
        st.warning("No radar frames available at this time. Try again later.")
        return
    if mode == "Satellite Infrared" and not ir_frames:
        st.warning("No satellite infrared frames available at this time. Try again later.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Stats overview
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Data Overview")

    latest_radar_ts = past_frames[-1]["time"] if past_frames else None
    latest_ir_ts = ir_frames[-1]["time"] if ir_frames else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Radar Frames", f"{len(past_frames)}")
    with c2:
        st.metric("Nowcast Frames", f"{len(nowcast_frames)}")
    with c3:
        st.metric("Satellite IR Frames", f"{len(ir_frames)}")
    with c4:
        if mode == "Precipitation Radar" and latest_radar_ts:
            st.metric("Latest Radar", _ts_label(latest_radar_ts))
        elif mode == "Satellite Infrared" and latest_ir_ts:
            st.metric("Latest Satellite", _ts_label(latest_ir_ts))
        else:
            st.metric("Latest", "N/A")

    # ══════════════════════════════════════════
    # SECTION 4: Frame selector
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Frame Selection")

    if mode == "Precipitation Radar":
        all_frames = past_frames + nowcast_frames
        frame_labels = []
        for i, f in enumerate(all_frames):
            ts = f["time"]
            label = _ts_label(ts)
            if i < len(past_frames):
                frame_labels.append(f"Past: {label}")
            else:
                frame_labels.append(f"Nowcast: {label}")

        if len(all_frames) == 0:
            st.warning("No radar frames available.")
            return

        # Default to latest past frame
        default_idx = len(past_frames) - 1

        selected_idx = st.select_slider(
            "Select Frame",
            options=list(range(len(all_frames))),
            value=default_idx,
            format_func=lambda i: frame_labels[i],
            key="wr_frame_slider",
        )

        selected_frame = all_frames[selected_idx]
        prev_frame = all_frames[selected_idx - 1] if selected_idx > 0 else None

    else:  # Satellite Infrared
        frame_labels = [_ts_label(f["time"]) for f in ir_frames]

        if len(ir_frames) == 0:
            st.warning("No satellite IR frames available.")
            return

        default_idx = len(ir_frames) - 1

        selected_idx = st.select_slider(
            "Select Frame",
            options=list(range(len(ir_frames))),
            value=default_idx,
            format_func=lambda i: frame_labels[i],
            key="wr_ir_slider",
        )

        selected_frame = ir_frames[selected_idx]
        prev_frame = ir_frames[selected_idx - 1] if selected_idx > 0 else None

    # Display selected timestamp
    selected_ts = selected_frame["time"]
    st.markdown(
        f'<div style="text-align:center; padding:0.5rem; margin-bottom:0.5rem;">'
        f'<span style="color:#06b6d4; font-size:1.1rem; font-weight:600;">'
        f'Showing: {_ts_label(selected_ts)}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 5: Radar map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Radar Map")

    # Determine location
    if use_custom:
        map_lat = custom_lat
        map_lon = custom_lon
        map_zoom = preset["zoom"]
    else:
        map_lat = preset["lat"]
        map_lon = preset["lon"]
        map_zoom = preset["zoom"]

    prev_path = prev_frame["path"] if prev_frame else None

    m = _build_radar_map(
        host=host,
        frame_path=selected_frame["path"],
        frame_ts=selected_ts,
        lat=map_lat,
        lon=map_lon,
        zoom=map_zoom,
        color_scheme=color_scheme,
        opacity=opacity,
        mode=mode,
        prev_frame_path=prev_path,
        show_comparison=show_comparison,
        prev_opacity=0.3,
    )

    # Render map
    try:
        from streamlit_folium import st_folium
        st_folium(m, height=550, width=None, returned_objects=[], key="wxrad_folium_map")
    except ImportError:
        components.html(m._repr_html_(), height=550)
    except Exception as e:
        logger.warning(f"st_folium error, falling back to components.html: {e}")
        components.html(m._repr_html_(), height=550)

    # ══════════════════════════════════════════
    # SECTION 6: Legend
    # ══════════════════════════════════════════
    if mode == "Precipitation Radar":
        legend_items = "".join(
            f'<span style="color:{color}; font-size:0.8rem; margin-right:1rem;">'
            f'&#9632; {label}</span>'
            for label, color in RADAR_LEGEND
        )
        st.markdown(
            f'<div style="display:flex; flex-wrap:wrap; gap:0.25rem; '
            f'margin-top:0.5rem; padding:0.5rem; '
            f'background:rgba(15,23,42,0.5); border-radius:8px; '
            f'border:1px solid #2a3550;">'
            f'<span style="color:#8b97b0; font-size:0.8rem; margin-right:0.75rem; '
            f'font-weight:600;">Intensity:</span>'
            f'{legend_items}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:flex; flex-wrap:wrap; gap:0.5rem; '
            'margin-top:0.5rem; padding:0.5rem; '
            'background:rgba(15,23,42,0.5); border-radius:8px; '
            'border:1px solid #2a3550;">'
            '<span style="color:#8b97b0; font-size:0.8rem; font-weight:600;">'
            'Satellite Infrared:</span>'
            '<span style="color:#e8ecf4; font-size:0.8rem;">'
            'Bright = cold cloud tops (high altitude) &mdash; '
            'Dark = warm surface / low clouds</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════
    # SECTION 7: Frame timeline info
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Available Frames Timeline")

    if mode == "Precipitation Radar":
        with st.expander(f"Past Radar Frames ({len(past_frames)})", expanded=False):
            for i, f in enumerate(past_frames):
                ts = f["time"]
                marker = " **[selected]**" if f["path"] == selected_frame["path"] else ""
                st.markdown(
                    f'<span style="color:#8b97b0; font-size:0.8rem;">'
                    f'{i + 1}. {_ts_label(ts)}{marker}</span>',
                    unsafe_allow_html=True,
                )

        if nowcast_frames:
            with st.expander(f"Nowcast Frames ({len(nowcast_frames)})", expanded=False):
                for i, f in enumerate(nowcast_frames):
                    ts = f["time"]
                    marker = " **[selected]**" if f["path"] == selected_frame["path"] else ""
                    st.markdown(
                        f'<span style="color:#8b5cf6; font-size:0.8rem;">'
                        f'{i + 1}. {_ts_label(ts)} (forecast){marker}</span>',
                        unsafe_allow_html=True,
                    )
    else:
        with st.expander(f"Satellite IR Frames ({len(ir_frames)})", expanded=False):
            for i, f in enumerate(ir_frames):
                ts = f["time"]
                marker = " **[selected]**" if f["path"] == selected_frame["path"] else ""
                st.markdown(
                    f'<span style="color:#8b97b0; font-size:0.8rem;">'
                    f'{i + 1}. {_ts_label(ts)}{marker}</span>',
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════════
    # SECTION 8: API info
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; padding:0.5rem;">'
        '<span style="color:#5a6580; font-size:0.75rem;">'
        'Data provided by <a href="https://www.rainviewer.com/api.html" '
        'style="color:#06b6d4;" target="_blank">RainViewer API</a> '
        '&mdash; radar data updates approximately every 10 minutes. '
        'Nowcast provides precipitation forecasts up to 1 hour ahead.'
        '</span></div>',
        unsafe_allow_html=True,
    )
