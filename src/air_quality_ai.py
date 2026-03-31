"""
Air Quality Intelligence AI module for TerraScout AI.
Estimates air quality based on infrastructure density, weather patterns,
terrain morphology, and land use data using real-time pollutant readings
from the Open-Meteo Air Quality API combined with geospatial analysis.
"""

import math
import logging

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"

AQI_COLORS = {
    "Excellent": "#2ecc71",
    "Good": "#a3d977",
    "Moderate": "#f1c40f",
    "Poor": "#e67e22",
    "Hazardous": "#9b59b6",
}

INDEX_LABELS = [
    "Particulate Matter",
    "Gas Pollutants",
    "Ozone Level",
    "Emission Sources",
    "Natural Filtration",
    "Ventilation",
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_air_quality_data(lat: float, lon: float) -> dict:
    """Fetch current air quality from Open-Meteo Air Quality API."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
                       "sulphur_dioxide,ozone,european_aqi",
        }
        resp = requests.get(AIR_QUALITY_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Air Quality API error: %s", e)
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


@st.cache_data(ttl=1800)
def compute_air_quality_intelligence(lat: float, lon: float) -> dict:
    """
    Compute a comprehensive air quality intelligence report by combining
    real pollutant readings with infrastructure, terrain, and weather data.
    """
    # -- Fetch all data sources ------------------------------------------------
    aq_data = fetch_air_quality_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    elevation = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=9)
    infra = fetch_landuse_infrastructure(lat, lon, radius=3000)

    current_aq = aq_data.get("current", {}) if aq_data else {}
    current_wx = weather.get("current", {}) if weather else {}

    # -- Real pollutant values (with fallback estimates) -----------------------
    pm25 = current_aq.get("pm2_5")
    pm10 = current_aq.get("pm10")
    co = current_aq.get("carbon_monoxide")
    no2 = current_aq.get("nitrogen_dioxide")
    so2 = current_aq.get("sulphur_dioxide")
    ozone = current_aq.get("ozone")
    eu_aqi = current_aq.get("european_aqi")

    api_available = pm25 is not None

    if pm25 is None:
        pm25 = 12.0
    if pm10 is None:
        pm10 = 25.0
    if co is None:
        co = 400.0
    if no2 is None:
        no2 = 20.0
    if so2 is None:
        so2 = 5.0
    if ozone is None:
        ozone = 60.0
    if eu_aqi is None:
        eu_aqi = 45.0

    pollutant_values = {
        "PM2.5": round(float(pm25), 1),
        "PM10": round(float(pm10), 1),
        "CO": round(float(co), 1),
        "NO2": round(float(no2), 1),
        "SO2": round(float(so2), 1),
        "Ozone": round(float(ozone), 1),
        "European AQI": round(float(eu_aqi), 0),
    }

    # -- Infrastructure emission estimates ------------------------------------
    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])

    industrial_count = 0
    major_road_count = 0
    building_count = 0
    forest_park_count = 0

    for el in elements:
        if el is None:
            continue
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        landuse = tags.get("landuse", "")
        highway = tags.get("highway", "")
        leisure = tags.get("leisure", "")

        if landuse == "industrial":
            industrial_count += 1
        if highway in ("motorway", "trunk", "primary", "secondary"):
            major_road_count += 1
        if tags.get("building"):
            building_count += 1
        if landuse in ("forest", "meadow", "orchard") or leisure == "park":
            forest_park_count += 1

    emission_factor = 8.5
    industrial_emissions = industrial_count * emission_factor
    traffic_emissions = major_road_count * 3.2
    population_proxy = building_count * 0.15

    emission_sources = {
        "Industrial": round(industrial_emissions, 1),
        "Traffic": round(traffic_emissions, 1),
        "Population Density": round(population_proxy, 1),
        "industrial_count": industrial_count,
        "major_road_count": major_road_count,
        "building_count": building_count,
    }

    # -- Natural filters -------------------------------------------------------
    center_elev = elevation.get("center_elevation", 0) if elevation else 0
    min_elev = elevation.get("min_elevation", 0) if elevation else 0
    max_elev = elevation.get("max_elevation", 0) if elevation else 0
    grid_elevs = elevation.get("grid_elevations", []) if elevation else []
    valid_elevs = [e for e in grid_elevs if e is not None]
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 0

    wind_speed = current_wx.get("wind_speed_10m", 5.0)
    if wind_speed is None:
        wind_speed = 5.0

    elev_range = (max_elev - min_elev) if max_elev is not None and min_elev is not None else 0
    is_valley = center_elev < avg_elev and elev_range > 50

    natural_filters = {
        "Forest/Park Areas": forest_park_count,
        "Green Coverage Score": round(min(forest_park_count * 4.0, 100), 1),
        "Elevation (m)": round(float(center_elev), 0),
        "Elevation Range (m)": round(float(elev_range), 0),
        "Valley Inversion Risk": is_valley,
        "Wind Speed (km/h)": round(float(wind_speed), 1),
    }

    # -- Compute 6 air quality indices (0-100, higher = cleaner) ---------------
    # 1. Particulate Matter index
    pm_raw = float(pm25) + float(pm10) * 0.5
    particulate_idx = _clamp(100 - pm_raw * 1.2)

    # 2. Gas Pollutants index
    gas_raw = float(no2) * 0.5 + float(so2) * 0.8 + float(co) * 0.005
    gas_idx = _clamp(100 - gas_raw * 0.8)

    # 3. Ozone Level index
    ozone_val = float(ozone)
    if ozone_val <= 60:
        ozone_idx = _clamp(90 - abs(ozone_val - 40) * 0.5)
    else:
        ozone_idx = _clamp(100 - ozone_val * 0.7)

    # 4. Emission Sources index (inverse of industrial + traffic)
    source_raw = industrial_emissions + traffic_emissions + population_proxy
    emission_idx = _clamp(100 - source_raw * 0.4)

    # 5. Natural Filtration index
    green_bonus = min(forest_park_count * 4.0, 60)
    elev_bonus = min(float(center_elev) * 0.01, 15) if center_elev > 0 else 0
    filtration_idx = _clamp(25 + green_bonus + elev_bonus)

    # 6. Ventilation index
    wind_val = float(wind_speed)
    wind_bonus = min(wind_val * 3.5, 60)
    valley_penalty = 20 if is_valley else 0
    ventilation_idx = _clamp(30 + wind_bonus - valley_penalty)

    indices = {
        "Particulate Matter": round(particulate_idx, 1),
        "Gas Pollutants": round(gas_idx, 1),
        "Ozone Level": round(ozone_idx, 1),
        "Emission Sources": round(emission_idx, 1),
        "Natural Filtration": round(filtration_idx, 1),
        "Ventilation": round(ventilation_idx, 1),
    }

    # -- Overall AQI (weighted average) ----------------------------------------
    weights = [0.25, 0.20, 0.10, 0.20, 0.15, 0.10]
    idx_values = [indices[k] for k in INDEX_LABELS]
    overall_aqi = sum(w * v for w, v in zip(weights, idx_values))
    overall_aqi = round(_clamp(overall_aqi), 1)

    if overall_aqi >= 80:
        classification = "Excellent"
    elif overall_aqi >= 60:
        classification = "Good"
    elif overall_aqi >= 40:
        classification = "Moderate"
    elif overall_aqi >= 20:
        classification = "Poor"
    else:
        classification = "Hazardous"

    # -- Health advice ---------------------------------------------------------
    health_map = {
        "Excellent": "Air quality is ideal. No restrictions on outdoor activities.",
        "Good": "Air quality is acceptable. Unusually sensitive people should "
                "consider limiting prolonged outdoor exertion.",
        "Moderate": "Sensitive groups may experience health effects. Consider "
                    "reducing prolonged outdoor exertion.",
        "Poor": "Everyone may begin to experience health effects. Limit outdoor "
                "activities and keep windows closed.",
        "Hazardous": "Health alert: serious health effects possible for entire "
                     "population. Avoid all outdoor physical activity.",
    }
    health_advice = health_map.get(classification, health_map["Moderate"])

    # -- Recommendations -------------------------------------------------------
    recommendations = []
    if particulate_idx < 50:
        recommendations.append(
            "High particulate levels detected. Use air purifiers indoors "
            "and wear N95 masks outside."
        )
    if gas_idx < 50:
        recommendations.append(
            "Elevated gas pollutant concentrations. Limit time near heavy "
            "traffic corridors."
        )
    if emission_idx < 50:
        recommendations.append(
            "Significant emission sources nearby. Support local zoning for "
            "industrial buffer zones."
        )
    if filtration_idx < 40:
        recommendations.append(
            "Low natural filtration capacity. Advocate for urban greening "
            "and tree-planting programs."
        )
    if ventilation_idx < 40:
        recommendations.append(
            "Poor ventilation conditions (valley or low wind). Monitor AQI "
            "closely during thermal inversions."
        )
    if is_valley:
        recommendations.append(
            "Valley location increases inversion risk. Pollutants may "
            "accumulate during calm, cold nights."
        )
    if not recommendations:
        recommendations.append(
            "Overall air quality is favorable. Continue monitoring for "
            "seasonal changes."
        )

    return {
        "overall_aqi": overall_aqi,
        "classification": classification,
        "pollutant_values": pollutant_values,
        "indices": indices,
        "emission_sources": emission_sources,
        "natural_filters": natural_filters,
        "health_advice": health_advice,
        "recommendations": recommendations,
        "api_available": api_available,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_air_quality_ai_tab() -> None:
    """Render the Air Quality Intelligence AI tab in Streamlit."""
    st.markdown(
        "<h2 style='color:#06b6d4;'>Air Quality Intelligence AI</h2>"
        "<p style='color:#8b97b0;'>Real-time pollutant analysis combined with "
        "geospatial infrastructure, terrain, and weather data.</p>",
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="aqi_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="aqi_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="aqi_lon",
        )

    run = st.button(
        "Analyze Air Quality", type="primary",
        key="aqi_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Air Quality** to generate "
            "a comprehensive air quality intelligence report."
        )
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching air quality data and analyzing environment..."):
        result = compute_air_quality_intelligence(lat, lon)

    overall = result["overall_aqi"]
    classification = result["classification"]
    pollutants = result["pollutant_values"]
    indices = result["indices"]
    emissions = result["emission_sources"]
    filters = result["natural_filters"]
    advice = result["health_advice"]
    recs = result["recommendations"]
    api_ok = result["api_available"]

    aqi_color = AQI_COLORS.get(classification, "#f1c40f")

    # -- AQI header ------------------------------------------------------------
    st.markdown(
        f"<div style='background:#1a1a2e;padding:20px;border-radius:12px;"
        f"border-left:5px solid {aqi_color};margin-bottom:16px;'>"
        f"<h1 style='color:{aqi_color};margin:0;'>{overall} / 100</h1>"
        f"<h3 style='color:{aqi_color};margin:4px 0 8px 0;'>"
        f"{classification}</h3>"
        f"<p style='color:#ccc;margin:0;font-size:0.95em;'>{advice}</p>"
        f"{'<p style=\"color:#888;font-size:0.8em;margin-top:6px;\">'
           'Using real-time Open-Meteo Air Quality data</p>'
           if api_ok else
           '<p style=\"color:#f59e0b;font-size:0.8em;margin-top:6px;\">'
           'API unavailable - using estimated fallback values</p>'}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # -- Pollutant values metrics row ------------------------------------------
    st.markdown("### Pollutant Concentrations")
    cols = st.columns(len(pollutants))
    units = {
        "PM2.5": "ug/m3", "PM10": "ug/m3", "CO": "ug/m3",
        "NO2": "ug/m3", "SO2": "ug/m3", "Ozone": "ug/m3",
        "European AQI": "index",
    }
    for col, (name, val) in zip(cols, pollutants.items()):
        with col:
            st.metric(label=f"{name} ({units.get(name, '')})", value=val)

    # -- Six index cards -------------------------------------------------------
    st.markdown("### Air Quality Indices")
    idx_colors = ["#2ecc71", "#3498db", "#9b59b6", "#e74c3c", "#27ae60", "#1abc9c"]
    idx_cols = st.columns(3)
    for i, (label, score) in enumerate(indices.items()):
        with idx_cols[i % 3]:
            bar_color = idx_colors[i % len(idx_colors)]
            if score >= 70:
                level_text = "Good"
            elif score >= 40:
                level_text = "Moderate"
            else:
                level_text = "Concern"
            st.markdown(
                f"<div style='background:#1a1a2e;padding:14px;border-radius:10px;"
                f"margin-bottom:10px;'>"
                f"<p style='color:#8b97b0;margin:0 0 4px 0;font-size:0.85em;'>"
                f"{label}</p>"
                f"<h3 style='color:{bar_color};margin:0;'>{score}</h3>"
                f"<div style='background:#2a2a3e;border-radius:6px;height:8px;"
                f"margin-top:6px;'>"
                f"<div style='background:{bar_color};width:{score}%;"
                f"height:8px;border-radius:6px;'></div></div>"
                f"<p style='color:#8b97b0;margin:4px 0 0 0;font-size:0.75em;'>"
                f"{level_text}</p></div>",
                unsafe_allow_html=True,
            )

    # -- Radar chart -----------------------------------------------------------
    st.markdown("### Quality Profile")
    radar_values = [indices[k] for k in INDEX_LABELS]
    radar_values_closed = radar_values + [radar_values[0]]
    labels_closed = INDEX_LABELS + [INDEX_LABELS[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(6,182,212,0.2)",
        line=dict(color="#06b6d4", width=2),
        name="Air Quality",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a2a3e", tickfont=dict(color="#8b97b0"),
            ),
            angularaxis=dict(
                gridcolor="#2a2a3e", tickfont=dict(color="#ccc", size=11),
            ),
        ),
        paper_bgcolor="#0e0e1a",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#ccc"),
        showlegend=False,
        height=420,
        margin=dict(t=30, b=30, l=60, r=60),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="aqa_pchart1")

    # -- Emission Sources vs Natural Filters comparison ------------------------
    st.markdown("### Emission Sources vs Natural Filters")
    cmp1, cmp2 = st.columns(2)

    with cmp1:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:10px;'>"
            "<h4 style='color:#e74c3c;margin:0 0 10px 0;'>Emission Sources</h4>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color:#ccc;margin:2px 0;'>Industrial sites: "
            f"<b>{emissions['industrial_count']}</b> "
            f"(est. {emissions['Industrial']} units)</p>"
            f"<p style='color:#ccc;margin:2px 0;'>Major roads: "
            f"<b>{emissions['major_road_count']}</b> "
            f"(est. {emissions['Traffic']} units)</p>"
            f"<p style='color:#ccc;margin:2px 0;'>Buildings (density proxy): "
            f"<b>{emissions['building_count']}</b> "
            f"(est. {emissions['Population Density']} units)</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with cmp2:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:10px;'>"
            "<h4 style='color:#2ecc71;margin:0 0 10px 0;'>Natural Filters</h4>",
            unsafe_allow_html=True,
        )
        valley_txt = "Yes" if filters["Valley Inversion Risk"] else "No"
        st.markdown(
            f"<p style='color:#ccc;margin:2px 0;'>Forest/Park areas: "
            f"<b>{filters['Forest/Park Areas']}</b> "
            f"(score {filters['Green Coverage Score']})</p>"
            f"<p style='color:#ccc;margin:2px 0;'>Elevation: "
            f"<b>{filters['Elevation (m)']} m</b> "
            f"(range {filters['Elevation Range (m)']} m)</p>"
            f"<p style='color:#ccc;margin:2px 0;'>Wind speed: "
            f"<b>{filters['Wind Speed (km/h)']} km/h</b></p>"
            f"<p style='color:#ccc;margin:2px 0;'>Valley inversion risk: "
            f"<b>{valley_txt}</b></p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # -- Health advice section -------------------------------------------------
    st.markdown("### Health Guidance")
    st.markdown(
        f"<div style='background:#1a1a2e;padding:16px;border-radius:10px;"
        f"border-left:4px solid {aqi_color};'>"
        f"<p style='color:#ccc;margin:0;font-size:1.05em;'>{advice}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # -- Recommendations -------------------------------------------------------
    st.markdown("### Recommendations")
    for rec in recs:
        st.markdown(
            f"<div style='background:#1a1a2e;padding:12px 16px;"
            f"border-radius:8px;margin-bottom:8px;border-left:3px solid #06b6d4;'>"
            f"<p style='color:#ccc;margin:0;'>{rec}</p></div>",
            unsafe_allow_html=True,
        )
