"""
Air Quality Monitor module for TerraScout AI.
Uses the Open-Meteo Air Quality API (free, no API key) to display
current and forecast air quality data with pollutant breakdowns.
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

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


OPEN_METEO_AQ = "https://air-quality-api.open-meteo.com/v1/air-quality"

# AQI color mapping (US EPA standard)
AQI_LEVELS = [
    (0, 50, "Good", "#10b981"),
    (51, 100, "Moderate", "#f59e0b"),
    (101, 150, "Unhealthy for Sensitive", "#f97316"),
    (151, 200, "Unhealthy", "#ef4444"),
    (201, 300, "Very Unhealthy", "#8b5cf6"),
    (301, 500, "Hazardous", "#991b1b"),
]

POLLUTANT_INFO = {
    "pm2_5": {"name": "PM2.5", "unit": "μg/m³", "desc": "Fine particulate matter", "color": "#06b6d4"},
    "pm10": {"name": "PM10", "unit": "μg/m³", "desc": "Coarse particulate matter", "color": "#38bdf8"},
    "ozone": {"name": "O₃", "unit": "μg/m³", "desc": "Ground-level ozone", "color": "#8b5cf6"},
    "nitrogen_dioxide": {"name": "NO₂", "unit": "μg/m³", "desc": "Nitrogen dioxide", "color": "#f59e0b"},
    "sulphur_dioxide": {"name": "SO₂", "unit": "μg/m³", "desc": "Sulphur dioxide", "color": "#ef4444"},
    "carbon_monoxide": {"name": "CO", "unit": "μg/m³", "desc": "Carbon monoxide", "color": "#10b981"},
}


def _aqi_info(aqi_val: float) -> tuple:
    """Return (label, color) for an AQI value."""
    for low, high, label, color in AQI_LEVELS:
        if low <= aqi_val <= high:
            return label, color
    return "Unknown", "#8b97b0"


@st.cache_data(ttl=600)
def get_air_quality(lat: float, lon: float) -> dict:
    """Fetch current + forecast air quality from Open-Meteo."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("openaq")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
        "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,european_aqi,us_aqi",
        "timezone": "auto",
        "forecast_days": 5,
    }
    try:
        resp = requests.get(OPEN_METEO_AQ, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=600)
def get_multi_point_aqi(points: list) -> list:
    """Fetch AQI for multiple points (for map grid)."""
    results = []
    for lat, lon, name in points:
        data = get_air_quality(lat, lon)
        current = data.get("current", {})
        results.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "us_aqi": current.get("us_aqi", 0),
            "pm2_5": current.get("pm2_5", 0),
            "pm10": current.get("pm10", 0),
            "ozone": current.get("ozone", 0),
        })
    return results


# Major cities for overview map
OVERVIEW_CITIES = [
    (41.8902, 12.4922, "Rome"),
    (45.4642, 9.1900, "Milan"),
    (48.8566, 2.3522, "Paris"),
    (51.5074, -0.1278, "London"),
    (52.5200, 13.4050, "Berlin"),
    (40.4168, -3.7038, "Madrid"),
    (38.7223, -9.1393, "Lisbon"),
    (59.3293, 18.0686, "Stockholm"),
    (47.3769, 8.5417, "Zurich"),
    (50.0755, 14.4378, "Prague"),
    (37.9838, 23.7275, "Athens"),
    (55.7558, 37.6173, "Moscow"),
    (40.7128, -74.0060, "New York"),
    (34.0522, -118.2437, "Los Angeles"),
    (35.6762, 139.6503, "Tokyo"),
    (39.9042, 116.4074, "Beijing"),
    (28.6139, 77.2090, "New Delhi"),
    (-33.8688, 151.2093, "Sydney"),
]


def render_air_quality_tab():
    """Main render function for the Air Quality tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header emerald">
        <h4>Air Quality Monitor</h4>
        <p>Real-time air quality data and 5-day forecast from Open-Meteo &mdash; PM2.5, PM10, O₃, NO₂, SO₂, CO levels with AQI index.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Location Input
    # ══════════════════════════════════════════
    st.markdown("#### Location")
    col1, col2 = st.columns(2)
    with col1:
        aq_lat = st.number_input("Latitude", value=41.8902, format="%.4f",
                                 min_value=-90.0, max_value=90.0, key="aq_lat",
                                 help="Enter latitude for air quality data")
    with col2:
        aq_lon = st.number_input("Longitude", value=12.4922, format="%.4f",
                                 min_value=-180.0, max_value=180.0, key="aq_lon",
                                 help="Enter longitude for air quality data")

    # Quick city selection
    city_name = st.selectbox("Quick City", [
        "Custom",
        "Rome", "Milan", "Paris", "London", "Berlin", "Madrid",
        "New York", "Los Angeles", "Tokyo", "Beijing", "New Delhi", "Sydney",
    ], key="aq_city")

    city_coords = {
        "Rome": (41.8902, 12.4922), "Milan": (45.4642, 9.1900),
        "Paris": (48.8566, 2.3522), "London": (51.5074, -0.1278),
        "Berlin": (52.5200, 13.4050), "Madrid": (40.4168, -3.7038),
        "New York": (40.7128, -74.0060), "Los Angeles": (34.0522, -118.2437),
        "Tokyo": (35.6762, 139.6503), "Beijing": (39.9042, 116.4074),
        "New Delhi": (28.6139, 77.2090), "Sydney": (-33.8688, 151.2093),
    }
    if city_name != "Custom" and city_name in city_coords:
        aq_lat, aq_lon = city_coords[city_name]

    if st.button("Get Air Quality", key="aq_search", width="stretch"):
        st.session_state.aq_params = {"lat": aq_lat, "lon": aq_lon}

    if "aq_params" not in st.session_state:
        st.info("Select a location and click 'Get Air Quality' to view pollution data.")
        return

    p = st.session_state.aq_params

    # ══════════════════════════════════════════
    # SECTION 2: Current Conditions
    # ══════════════════════════════════════════
    with st.spinner("Fetching air quality data..."):
        data = get_air_quality(p["lat"], p["lon"])

    if data.get("error"):
        st.error(f"API Error: {data['error']}")
        return

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    us_aqi = current.get("us_aqi", 0) or 0
    eu_aqi = current.get("european_aqi", 0) or 0
    aqi_label, aqi_color = _aqi_info(us_aqi)

    st.markdown("---")
    st.markdown("#### Current Air Quality")

    # AQI card
    st.markdown(f"""
    <div class="glass-card" style="padding:1.5rem 2rem; margin-bottom:1rem;">
        <div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
            <div style="width:80px; height:80px; border-radius:50%; background:{aqi_color}20;
                        border:3px solid {aqi_color}; display:flex; align-items:center;
                        justify-content:center; flex-shrink:0;">
                <span style="color:{aqi_color}; font-weight:800; font-size:1.8rem;">{us_aqi}</span>
            </div>
            <div>
                <h3 style="margin:0; color:#e8ecf4;">US AQI: {us_aqi}</h3>
                <p style="margin:0.2rem 0 0; color:{aqi_color}; font-weight:600; font-size:1.1rem;">{aqi_label}</p>
                <p style="margin:0.2rem 0 0; color:#8b97b0; font-size:0.85rem;">EU AQI: {eu_aqi}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pollutant cards
    st.markdown("#### Pollutant Levels")
    pcols = st.columns(3)
    for i, (key, info) in enumerate(POLLUTANT_INFO.items()):
        val = current.get(key, 0) or 0
        col = pcols[i % 3]
        with col:
            st.markdown(f"""
            <div class="bio-card" style="margin-bottom:0.5rem; padding:0.75rem 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#e8ecf4; font-weight:700; font-size:1rem;">{info['name']}</div>
                        <div style="color:#5a6580; font-size:0.75rem;">{info['desc']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{info['color']}; font-weight:800; font-size:1.2rem;">{val:.1f}</div>
                        <div style="color:#8b97b0; font-size:0.7rem;">{info['unit']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 3: Hourly Charts
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### 5-Day Forecast Charts")

    if hourly:
        times = hourly.get("time", [])

        # PM2.5 and PM10 chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        fig.patch.set_facecolor("#0a0e1a")

        for ax in (ax1, ax2):
            ax.set_facecolor("#0a0e1a")
            ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)
            ax.tick_params(axis="both", colors="#8b97b0", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")

        pm25 = hourly.get("pm2_5", [])
        pm10 = hourly.get("pm10", [])

        if pm25:
            ax1.plot(range(len(pm25)), pm25, color="#06b6d4", linewidth=1.5, label="PM2.5")
            ax1.fill_between(range(len(pm25)), pm25, alpha=0.15, color="#06b6d4")
        if pm10:
            ax1.plot(range(len(pm10)), pm10, color="#38bdf8", linewidth=1.5, label="PM10")
        ax1.set_ylabel("μg/m³", color="#8b97b0", fontsize=9)
        ax1.set_title("Particulate Matter (PM2.5 & PM10)", color="#e8ecf4", fontsize=11, fontweight="bold")
        ax1.legend(fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550", labelcolor="#8b97b0")

        # AQI forecast
        aqi_vals = hourly.get("us_aqi", [])
        if aqi_vals:
            colors = [_aqi_info(v or 0)[1] for v in aqi_vals]
            ax2.bar(range(len(aqi_vals)), aqi_vals, color="#8b5cf6", alpha=0.6, width=1.0)
        ax2.set_ylabel("US AQI", color="#8b97b0", fontsize=9)
        ax2.set_title("AQI Forecast", color="#e8ecf4", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Hours from now", color="#8b97b0", fontsize=9)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Ozone and NO2 chart
        ozone = hourly.get("ozone", [])
        no2 = hourly.get("nitrogen_dioxide", [])
        so2 = hourly.get("sulphur_dioxide", [])

        if ozone or no2:
            fig2, ax3 = plt.subplots(figsize=(10, 3))
            fig2.patch.set_facecolor("#0a0e1a")
            ax3.set_facecolor("#0a0e1a")
            ax3.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
            ax3.set_axisbelow(True)
            ax3.tick_params(axis="both", colors="#8b97b0", labelsize=8)
            for spine in ax3.spines.values():
                spine.set_color("#2a3550")

            if ozone:
                ax3.plot(range(len(ozone)), ozone, color="#8b5cf6", linewidth=1.5, label="O₃")
            if no2:
                ax3.plot(range(len(no2)), no2, color="#f59e0b", linewidth=1.5, label="NO₂")
            if so2:
                ax3.plot(range(len(so2)), so2, color="#ef4444", linewidth=1.5, label="SO₂")

            ax3.set_ylabel("μg/m³", color="#8b97b0", fontsize=9)
            ax3.set_xlabel("Hours from now", color="#8b97b0", fontsize=9)
            ax3.set_title("Gas Pollutants (O₃, NO₂, SO₂)", color="#e8ecf4", fontsize=11, fontweight="bold")
            ax3.legend(fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550", labelcolor="#8b97b0")
            fig2.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

    # ══════════════════════════════════════════
    # SECTION 4: City Comparison Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Global Air Quality Map")
    st.caption("Shows AQI for major cities worldwide. Click markers for details.")

    with st.spinner("Loading global AQI data..."):
        city_data = get_multi_point_aqi(OVERVIEW_CITIES)

    m = folium.Map(location=[30, 10], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    for city in city_data:
        aqi = city.get("us_aqi", 0) or 0
        label, color = _aqi_info(aqi)
        popup_html = f"""
        <div style="max-width:180px;">
            <strong>{city['name']}</strong><br/>
            AQI: <strong style="color:{color};">{aqi}</strong> ({label})<br/>
            <span style="font-size:0.8rem;">PM2.5: {city.get('pm2_5', 0):.1f} μg/m³</span>
        </div>
        """
        folium.CircleMarker(
            location=[city["lat"], city["lon"]],
            radius=max(6, aqi / 15),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(m)

    components.html(m._repr_html_(), height=450)

    # ══════════════════════════════════════════
    # SECTION 5: Download
    # ══════════════════════════════════════════
    if hourly:
        st.markdown("---")
        times_h = hourly.get("time", [])
        export_data = {"time": times_h}
        for key in ["pm2_5", "pm10", "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide", "us_aqi", "european_aqi"]:
            if key in hourly:
                export_data[key] = hourly[key]

        df_export = pd.DataFrame(export_data)
        csv_buf = io.StringIO()
        df_export.to_csv(csv_buf, index=False)

        with st.expander(f"Hourly Data Table ({len(times_h)} hours)", expanded=False):
            st.dataframe(df_export, width="stretch", hide_index=True)

        st.download_button(
            f"Download Air Quality Data (CSV)",
            data=csv_buf.getvalue(),
            file_name="air_quality.csv",
            mime="text/csv",
            key="aq_download",
        )
