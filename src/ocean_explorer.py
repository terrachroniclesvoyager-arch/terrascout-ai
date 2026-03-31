"""
Ocean & Marine Explorer for TerraScout AI.
Wave height, sea conditions, swell data, and tidal information.
Uses Open-Meteo Marine API — free, no API key.
"""

import io
import logging
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

MARINE_API = "https://marine-api.open-meteo.com/v1/marine"

# ── Ocean location presets ──────────────────────────────────────────
OCEAN_PRESETS = {
    "Mediterranean (Italy)": {"lat": 40.5, "lon": 14.0},
    "North Atlantic": {"lat": 45.0, "lon": -30.0},
    "Caribbean": {"lat": 18.0, "lon": -70.0},
    "North Sea": {"lat": 56.0, "lon": 3.0},
    "Pacific (Hawaii)": {"lat": 21.3, "lon": -157.8},
    "Indian Ocean": {"lat": -10.0, "lon": 75.0},
    "South Pacific": {"lat": -30.0, "lon": -170.0},
    "Bay of Biscay": {"lat": 44.5, "lon": -4.0},
    "Sea of Japan": {"lat": 38.0, "lon": 135.0},
    "Southern Ocean": {"lat": -55.0, "lon": 0.0},
    "Gulf of Mexico": {"lat": 25.0, "lon": -90.0},
    "Coral Sea (Australia)": {"lat": -18.0, "lon": 150.0},
}

# ── Beaufort sea-state scale (wave height based) ───────────────────
BEAUFORT_SCALE = [
    (0.0, 0.1, 0, "Calm", "#10b981"),
    (0.1, 0.5, 2, "Smooth", "#38bdf8"),
    (0.5, 1.25, 3, "Slight", "#06b6d4"),
    (1.25, 2.5, 4, "Moderate", "#f59e0b"),
    (2.5, 4.0, 5, "Rough", "#f97316"),
    (4.0, 6.0, 6, "Very Rough", "#ef4444"),
    (6.0, 9.0, 7, "High", "#dc2626"),
    (9.0, 14.0, 8, "Very High", "#991b1b"),
    (14.0, 999.0, 9, "Phenomenal", "#7f1d1d"),
]


# ── Helpers ─────────────────────────────────────────────────────────

def _deg_to_compass(deg):
    """Convert degrees (0-360) to 16-point compass bearing."""
    if deg is None:
        return "—"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(deg / 22.5) % 16
    return dirs[ix]


def _beaufort_info(wave_height):
    """Return (scale_number, label, color) for a wave height in metres."""
    if wave_height is None:
        return (0, "Unknown", "#8b97b0")
    for low, high, scale, label, color in BEAUFORT_SCALE:
        if low <= wave_height < high:
            return (scale, label, color)
    return (9, "Phenomenal", "#7f1d1d")


def _direction_arrow(deg):
    """Return an HTML arrow character rotated to match wave direction."""
    if deg is None:
        return ""
    # CSS rotate: 0 = up (N), clockwise
    return (
        f'<span style="display:inline-block; transform:rotate({deg}deg); '
        f'font-size:1.4rem; line-height:1;">&#x2191;</span>'
    )


# ── API fetch functions ─────────────────────────────────────────────

@st.cache_data(ttl=600)
def fetch_marine_current(lat: float, lon: float) -> dict:
    """Fetch current marine conditions from Open-Meteo Marine API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "wave_height,wave_direction,wave_period,"
            "wind_wave_height,wind_wave_direction,"
            "swell_wave_height,swell_wave_direction,swell_wave_period,"
            "ocean_current_velocity,ocean_current_direction"
        ),
    }
    try:
        resp = requests.get(MARINE_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Marine current API error: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=600)
def fetch_marine_forecast(lat: float, lon: float) -> dict:
    """Fetch 7-day hourly marine forecast from Open-Meteo Marine API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "wave_height,wave_direction,wave_period,"
            "swell_wave_height,wind_wave_height"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }
    try:
        resp = requests.get(MARINE_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Marine forecast API error: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=600)
def fetch_marine_multi(points: list) -> list:
    """Fetch current conditions for multiple points. Each item: (lat, lon, name)."""
    results = []
    for lat, lon, name in points:
        data = fetch_marine_current(lat, lon)
        current = data.get("current", {})
        results.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "wave_height": current.get("wave_height"),
            "wave_period": current.get("wave_period"),
            "wave_direction": current.get("wave_direction"),
            "swell_wave_height": current.get("swell_wave_height"),
            "wind_wave_height": current.get("wind_wave_height"),
        })
    return results


# ── Main render function ────────────────────────────────────────────

def render_ocean_explorer_tab():
    """Main render function for the Ocean & Marine Explorer tab."""

    import folium
    import streamlit.components.v1 as components

    # ── Header ──
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Ocean &amp; Marine Explorer</h4>
        <p>Wave height, swell data, sea conditions and tidal info from Open-Meteo Marine &mdash; free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode & Location
    # ══════════════════════════════════════════
    mode = st.radio(
        "Mode",
        ["Current Conditions", "Wave Forecast", "Multi-Point Comparison"],
        horizontal=True,
        key="ocean_mode",
    )

    st.markdown("#### Location")

    preset_name = st.selectbox(
        "Ocean Location Preset",
        ["Custom"] + list(OCEAN_PRESETS.keys()),
        key="ocean_preset",
    )

    if preset_name != "Custom" and preset_name in OCEAN_PRESETS:
        default_lat = OCEAN_PRESETS[preset_name]["lat"]
        default_lon = OCEAN_PRESETS[preset_name]["lon"]
    else:
        default_lat = 40.5
        default_lon = 14.0

    col1, col2 = st.columns(2)
    with col1:
        oc_lat = st.number_input(
            "Latitude", value=default_lat, format="%.4f",
            min_value=-90.0, max_value=90.0, key="ocean_lat",
            help="Latitude of the ocean point",
        )
    with col2:
        oc_lon = st.number_input(
            "Longitude", value=default_lon, format="%.4f",
            min_value=-180.0, max_value=180.0, key="ocean_lon",
            help="Longitude of the ocean point",
        )

    # Override with preset coordinates when a preset is selected
    if preset_name != "Custom" and preset_name in OCEAN_PRESETS:
        oc_lat = OCEAN_PRESETS[preset_name]["lat"]
        oc_lon = OCEAN_PRESETS[preset_name]["lon"]

    # ──────────────────────────────────────────
    # CURRENT CONDITIONS
    # ──────────────────────────────────────────
    if mode == "Current Conditions":
        if st.button("Get Ocean Conditions", key="ocean_current_btn", width="stretch"):
            st.session_state.ocean_current_params = {"lat": oc_lat, "lon": oc_lon}

        if "ocean_current_params" not in st.session_state:
            st.info("Select an ocean location and click 'Get Ocean Conditions' to view marine data.")
            return

        p = st.session_state.ocean_current_params

        with st.spinner("Fetching marine conditions..."):
            data = fetch_marine_current(p["lat"], p["lon"])

        if data.get("error"):
            st.error(f"API Error: {data['error']}")
            return

        current = data.get("current", {})

        # Check for land point (API returns null values)
        wh = current.get("wave_height")
        if wh is None:
            st.warning(
                "No marine data available for this location. "
                "The point may be on land — the Marine API only covers ocean areas. "
                "Try moving the coordinates to open water."
            )
            return

        wp = current.get("wave_period")
        wd = current.get("wave_direction")
        wwh = current.get("wind_wave_height")
        wwd = current.get("wind_wave_direction")
        swh = current.get("swell_wave_height")
        swd = current.get("swell_wave_direction")
        swp = current.get("swell_wave_period")
        ocv = current.get("ocean_current_velocity")
        ocd = current.get("ocean_current_direction")

        bft_num, bft_label, bft_color = _beaufort_info(wh)
        wd_compass = _deg_to_compass(wd)

        st.markdown("---")
        st.markdown("#### Current Sea Conditions")

        # Beaufort indicator
        st.markdown(f"""
        <div class="glass-card" style="padding:1.2rem 1.5rem; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
                <div style="width:80px; height:80px; border-radius:50%; background:{bft_color}20;
                            border:3px solid {bft_color}; display:flex; align-items:center;
                            justify-content:center; flex-shrink:0;">
                    <span style="color:{bft_color}; font-weight:800; font-size:1.8rem;">{bft_num}</span>
                </div>
                <div>
                    <h3 style="margin:0; color:#e8ecf4;">Sea State: {escape(bft_label)}</h3>
                    <p style="margin:0.2rem 0 0; color:{bft_color}; font-weight:600; font-size:1.1rem;">
                        Beaufort Scale {bft_num}
                    </p>
                    <p style="margin:0.2rem 0 0; color:#8b97b0; font-size:0.85rem;">
                        {p['lat']:.2f}, {p['lon']:.2f}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metric cards row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Wave Height", f"{wh:.1f} m" if wh is not None else "—")
        with c2:
            st.metric("Wave Period", f"{wp:.1f} s" if wp is not None else "—")
        with c3:
            st.metric("Wave Direction", f"{wd_compass} ({wd:.0f}°)" if wd is not None else "—")
        with c4:
            st.metric("Wind Wave", f"{wwh:.1f} m" if wwh is not None else "—")

        # Detail cards
        st.markdown("#### Wave Breakdown")

        col_swell, col_wind, col_current = st.columns(3)

        with col_swell:
            sw_dir = _deg_to_compass(swd)
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem 1.2rem; margin-bottom:0.5rem;">
                <div style="color:#8b5cf6; font-weight:700; font-size:0.85rem; margin-bottom:0.5rem;">
                    SWELL
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#e8ecf4; font-weight:800; font-size:1.5rem;">
                            {f'{swh:.1f} m' if swh is not None else '—'}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Height</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#e8ecf4; font-size:0.95rem;">
                            {_direction_arrow(swd)} {sw_dir}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Direction</div>
                    </div>
                </div>
                <div style="margin-top:0.5rem; color:#8b97b0; font-size:0.85rem;">
                    Period: <span style="color:#e8ecf4; font-weight:600;">{f'{swp:.1f} s' if swp is not None else '—'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_wind:
            ww_dir = _deg_to_compass(wwd)
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem 1.2rem; margin-bottom:0.5rem;">
                <div style="color:#38bdf8; font-weight:700; font-size:0.85rem; margin-bottom:0.5rem;">
                    WIND WAVES
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#e8ecf4; font-weight:800; font-size:1.5rem;">
                            {f'{wwh:.1f} m' if wwh is not None else '—'}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Height</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#e8ecf4; font-size:0.95rem;">
                            {_direction_arrow(wwd)} {ww_dir}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Direction</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_current:
            oc_dir = _deg_to_compass(ocd)
            st.markdown(f"""
            <div class="glass-card" style="padding:1rem 1.2rem; margin-bottom:0.5rem;">
                <div style="color:#10b981; font-weight:700; font-size:0.85rem; margin-bottom:0.5rem;">
                    OCEAN CURRENT
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#e8ecf4; font-weight:800; font-size:1.5rem;">
                            {f'{ocv:.2f} m/s' if ocv is not None else '—'}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Velocity</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#e8ecf4; font-size:0.95rem;">
                            {_direction_arrow(ocd)} {oc_dir}
                        </div>
                        <div style="color:#8b97b0; font-size:0.8rem;">Direction</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Map ──
        st.markdown("---")
        st.markdown("#### Location Map")

        m = folium.Map(
            location=[p["lat"], p["lon"]],
            zoom_start=6,
            tiles=None,
        )
        # Esri Ocean Basemap
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Esri Ocean Basemap",
            name="Esri Ocean",
            max_zoom=13,
        ).add_to(m)

        period_line = f'<strong>Period:</strong> {wp:.1f} s<br/>' if wp is not None else ''
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>Wave Height:</strong> {wh:.1f} m<br/>'
            f'{period_line}'
            f'<strong>Direction:</strong> {wd_compass}<br/>'
            f'<strong>Sea State:</strong> {escape(bft_label)} (Bft {bft_num})<br/>'
            f'<span style="font-size:0.8rem;">{p["lat"]:.4f}, {p["lon"]:.4f}</span>'
            f'</div>'
        )

        folium.Marker(
            location=[p["lat"], p["lon"]],
            popup=folium.Popup(popup_html, max_width=240),
            icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
        ).add_to(m)

        # Direction arrow as a DivIcon marker offset slightly
        if wd is not None:
            import math
            arrow_lat = p["lat"] + 0.3 * math.cos(math.radians(wd))
            arrow_lon = p["lon"] + 0.3 * math.sin(math.radians(wd))
            folium.Marker(
                location=[arrow_lat, arrow_lon],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:24px; color:{bft_color}; '
                         f'transform:rotate({wd}deg);">&#x2B06;</div>',
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                ),
            ).add_to(m)

        components.html(m._repr_html_(), height=480)

    # ──────────────────────────────────────────
    # WAVE FORECAST
    # ──────────────────────────────────────────
    elif mode == "Wave Forecast":
        if st.button("Get Wave Forecast", key="ocean_forecast_btn", width="stretch"):
            st.session_state.ocean_forecast_params = {"lat": oc_lat, "lon": oc_lon}

        if "ocean_forecast_params" not in st.session_state:
            st.info("Select an ocean location and click 'Get Wave Forecast' to view the 7-day forecast.")
            return

        p = st.session_state.ocean_forecast_params

        with st.spinner("Fetching 7-day marine forecast..."):
            data = fetch_marine_forecast(p["lat"], p["lon"])

        if data.get("error"):
            st.error(f"API Error: {data['error']}")
            return

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        wave_h = hourly.get("wave_height", [])
        swell_h = hourly.get("swell_wave_height", [])
        wind_w_h = hourly.get("wind_wave_height", [])
        wave_dir = hourly.get("wave_direction", [])
        wave_per = hourly.get("wave_period", [])

        if not times or not wave_h:
            st.warning(
                "No forecast data available for this location. "
                "The point may be on land — try an ocean location."
            )
            return

        # Check if all values are None (land point)
        if all(v is None for v in wave_h):
            st.warning(
                "No marine data available for this location. "
                "The point may be on land — the Marine API only covers ocean areas."
            )
            return

        st.markdown("---")
        st.markdown("#### 7-Day Wave Forecast")

        # Stats
        valid_wh = [v for v in wave_h if v is not None]
        valid_sw = [v for v in swell_h if v is not None] if swell_h else []
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Max Wave Height", f"{max(valid_wh):.1f} m" if valid_wh else "—")
        with c2:
            st.metric("Avg Wave Height", f"{sum(valid_wh)/len(valid_wh):.1f} m" if valid_wh else "—")
        with c3:
            st.metric("Max Swell", f"{max(valid_sw):.1f} m" if valid_sw else "—")
        with c4:
            st.metric("Forecast Hours", f"{len(times)}")

        # ── Chart ──
        st.markdown("#### Wave Height Over Time")

        fig, ax = plt.subplots(figsize=(12, 4.5))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#0a0e1a")
        ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", colors="#8b97b0", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

        x = list(range(len(wave_h)))

        # Swell fill
        if swell_h:
            swell_clean = [v if v is not None else 0 for v in swell_h]
            ax.fill_between(x, swell_clean, alpha=0.2, color="#8b5cf6", label="Swell (fill)")
            ax.plot(x, swell_clean, color="#8b5cf6", linewidth=1.0, alpha=0.6)

        # Wind wave line
        if wind_w_h:
            wind_clean = [v if v is not None else 0 for v in wind_w_h]
            ax.plot(x, wind_clean, color="#38bdf8", linewidth=1.2, label="Wind Wave", alpha=0.8)

        # Total wave height (main line)
        wave_clean = [v if v is not None else 0 for v in wave_h]
        ax.plot(x, wave_clean, color="#06b6d4", linewidth=2.0, label="Total Wave Height")
        ax.fill_between(x, wave_clean, alpha=0.08, color="#06b6d4")

        # X-axis labels (show every 24 hours)
        tick_positions = list(range(0, len(times), 24))
        tick_labels = []
        for idx in tick_positions:
            if idx < len(times):
                try:
                    dt = datetime.fromisoformat(times[idx])
                    tick_labels.append(dt.strftime("%b %d"))
                except (ValueError, TypeError):
                    tick_labels.append(str(idx))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, fontsize=8, color="#8b97b0")

        ax.set_ylabel("Height (m)", color="#8b97b0", fontsize=9)
        ax.set_xlabel("Date", color="#8b97b0", fontsize=9)
        ax.set_title(
            f"7-Day Wave Forecast — {p['lat']:.2f}, {p['lon']:.2f}",
            color="#e8ecf4", fontsize=11, fontweight="bold",
        )
        ax.legend(
            fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550",
            labelcolor="#8b97b0", loc="upper right",
        )
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # ── Data table ──
        st.markdown("---")
        df = pd.DataFrame({
            "Time": times,
            "Wave Height (m)": wave_h,
            "Wave Period (s)": wave_per,
            "Wave Dir (°)": wave_dir,
            "Swell Height (m)": swell_h if swell_h else [None] * len(times),
            "Wind Wave (m)": wind_w_h if wind_w_h else [None] * len(times),
        })

        with st.expander(f"Hourly Data Table ({len(times)} hours)", expanded=False):
            st.dataframe(df, width="stretch", hide_index=True)

        # ── Download ──
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)

        st.download_button(
            "Download Wave Forecast (CSV)",
            data=csv_buf.getvalue(),
            file_name="wave_forecast.csv",
            mime="text/csv",
            key="ocean_forecast_dl",
        )

    # ──────────────────────────────────────────
    # MULTI-POINT COMPARISON
    # ──────────────────────────────────────────
    elif mode == "Multi-Point Comparison":
        st.markdown("#### Compare Ocean Locations")
        st.caption("Select up to 4 ocean presets to compare side-by-side.")

        preset_keys = list(OCEAN_PRESETS.keys())
        selected = st.multiselect(
            "Select locations (max 4)",
            preset_keys,
            default=preset_keys[:4],
            max_selections=4,
            key="ocean_compare_sel",
        )

        if st.button("Compare Locations", key="ocean_compare_btn", width="stretch"):
            st.session_state.ocean_compare_sel_confirmed = selected

        if "ocean_compare_sel_confirmed" not in st.session_state:
            st.info("Select up to 4 ocean locations and click 'Compare Locations'.")
            return

        chosen = st.session_state.ocean_compare_sel_confirmed
        if not chosen:
            st.warning("Please select at least one location.")
            return

        points = [
            (OCEAN_PRESETS[name]["lat"], OCEAN_PRESETS[name]["lon"], name)
            for name in chosen if name in OCEAN_PRESETS
        ]

        with st.spinner("Fetching marine data for all locations..."):
            results = fetch_marine_multi(points)

        if not results:
            st.warning("No data returned.")
            return

        st.markdown("---")
        st.markdown("#### Comparison Results")

        # Metric cards for each location
        cols = st.columns(len(results))
        for i, res in enumerate(results):
            with cols[i]:
                wh = res.get("wave_height")
                wp = res.get("wave_period")
                sw = res.get("swell_wave_height")
                ww = res.get("wind_wave_height")

                if wh is None:
                    st.markdown(f"""
                    <div class="glass-card" style="padding:1rem; margin-bottom:0.5rem;">
                        <div style="color:#06b6d4; font-weight:700; font-size:0.85rem; margin-bottom:0.5rem;">
                            {escape(res['name'])}
                        </div>
                        <div style="color:#5a6580; font-size:0.85rem;">No data (land?)</div>
                    </div>
                    """, unsafe_allow_html=True)
                    continue

                bft_num, bft_label, bft_color = _beaufort_info(wh)
                wd_compass = _deg_to_compass(res.get("wave_direction"))

                st.markdown(f"""
                <div class="glass-card" style="padding:1rem; margin-bottom:0.5rem;">
                    <div style="color:#06b6d4; font-weight:700; font-size:0.85rem; margin-bottom:0.5rem;">
                        {escape(res['name'])}
                    </div>
                    <div style="color:#e8ecf4; font-weight:800; font-size:1.6rem;">{wh:.1f} m</div>
                    <div style="color:{bft_color}; font-size:0.8rem; font-weight:600; margin-bottom:0.4rem;">
                        {escape(bft_label)} (Bft {bft_num})
                    </div>
                    <div style="color:#8b97b0; font-size:0.8rem;">
                        Period: {f'{wp:.1f} s' if wp is not None else '—'}<br/>
                        Swell: {f'{sw:.1f} m' if sw is not None else '—'}<br/>
                        Wind Wave: {f'{ww:.1f} m' if ww is not None else '—'}<br/>
                        Direction: {wd_compass}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Bar chart comparison ──
        st.markdown("#### Wave Height Comparison")

        names = []
        wave_vals = []
        swell_vals = []
        wind_vals = []
        for res in results:
            wh = res.get("wave_height")
            if wh is not None:
                names.append(res["name"])
                wave_vals.append(wh)
                swell_vals.append(res.get("swell_wave_height") or 0)
                wind_vals.append(res.get("wind_wave_height") or 0)

        if names:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#0a0e1a")
            ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7, axis="y")
            ax.set_axisbelow(True)
            ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")

            import numpy as np
            x_pos = np.arange(len(names))
            bar_w = 0.25

            ax.bar(x_pos - bar_w, wave_vals, bar_w, color="#06b6d4", label="Total Wave", alpha=0.85)
            ax.bar(x_pos, swell_vals, bar_w, color="#8b5cf6", label="Swell", alpha=0.85)
            ax.bar(x_pos + bar_w, wind_vals, bar_w, color="#38bdf8", label="Wind Wave", alpha=0.85)

            ax.set_xticks(x_pos)
            ax.set_xticklabels(names, fontsize=8, color="#8b97b0", rotation=15, ha="right")
            ax.set_ylabel("Height (m)", color="#8b97b0", fontsize=9)
            ax.set_title("Wave Height Comparison", color="#e8ecf4", fontsize=11, fontweight="bold")
            ax.legend(
                fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550",
                labelcolor="#8b97b0",
            )
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        # ── Comparison map ──
        st.markdown("---")
        st.markdown("#### Locations Map")

        m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Esri Ocean Basemap",
            name="Esri Ocean",
            max_zoom=13,
        ).add_to(m)

        for res in results:
            wh = res.get("wave_height")
            if wh is None:
                continue
            bft_num, bft_label, bft_color = _beaufort_info(wh)
            popup_html = (
                f'<div style="max-width:200px;">'
                f'<strong>{escape(res["name"])}</strong><br/>'
                f'Wave: <strong>{wh:.1f} m</strong><br/>'
                f'State: {escape(bft_label)} (Bft {bft_num})<br/>'
                f'Swell: {res.get("swell_wave_height", 0) or 0:.1f} m'
                f'</div>'
            )
            folium.CircleMarker(
                location=[res["lat"], res["lon"]],
                radius=max(6, wh * 4),
                color=bft_color,
                fill=True,
                fill_color=bft_color,
                fill_opacity=0.6,
                weight=2,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)

        components.html(m._repr_html_(), height=450)
