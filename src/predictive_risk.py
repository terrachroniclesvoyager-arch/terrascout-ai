"""
Predictive Risk Model for TerraScout AI.
Fire, flood & landslide risk prediction with heatmap visualization.
Uses weather forecasts, elevation, soil data, and seismic history.
"""

import logging
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

from src.map_factory import MapFactory
from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_earthquakes,
    fetch_water_features,
    ANALYSIS_PRESETS,
)


RISK_COLORS = {
    "Fire": "#f97316",
    "Flood": "#3b82f6",
    "Landslide": "#a855f7",
}

@st.cache_data(ttl=1800)
def _fetch_forecast_7d(lat, lon):
    """Fetch 7-day weather forecast from Open-Meteo."""
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_min",
            "timezone": "auto",
            "forecast_days": 7,
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("daily", {})
    except Exception:
        pass
    return {}


@st.cache_data(ttl=3600)
def _fetch_archive_30d(lat, lon):
    """Fetch past 30 days weather from Open-Meteo Archive."""
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=30)
    try:
        resp = requests.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat, "longitude": lon,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto",
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("daily", {})
    except Exception:
        pass
    return {}


def _compute_fire_risk(forecast, archive, elevation_data, soil_data):
    """Compute fire risk score (0-10)."""
    score = 0

    # Temperature factor (high temp = higher risk)
    temps = forecast.get("temperature_2m_max", [])
    if temps:
        max_temp = max(t for t in temps if t is not None) if any(t is not None for t in temps) else 20
        if max_temp > 40: score += 3
        elif max_temp > 35: score += 2.5
        elif max_temp > 30: score += 2
        elif max_temp > 25: score += 1
    
    # Low humidity factor
    humidity = forecast.get("relative_humidity_2m_min", [])
    if humidity:
        min_hum = min(h for h in humidity if h is not None) if any(h is not None for h in humidity) else 50
        if min_hum < 15: score += 2.5
        elif min_hum < 25: score += 2
        elif min_hum < 35: score += 1.5
        elif min_hum < 50: score += 0.5

    # Wind factor
    winds = forecast.get("wind_speed_10m_max", [])
    if winds:
        max_wind = max(w for w in winds if w is not None) if any(w is not None for w in winds) else 10
        if max_wind > 50: score += 2
        elif max_wind > 30: score += 1.5
        elif max_wind > 20: score += 1

    # Drought factor (low recent precipitation)
    archive_precip = archive.get("precipitation_sum", [])
    if archive_precip:
        total_precip = sum(p for p in archive_precip if p is not None)
        if total_precip < 5: score += 2
        elif total_precip < 20: score += 1.5
        elif total_precip < 50: score += 1

    # Elevation/slope factor
    if isinstance(elevation_data, dict):
        elev_min = elevation_data.get("min_elevation", 0)
        elev_max = elevation_data.get("max_elevation", 0)
        if isinstance(elev_min, (int, float)) and isinstance(elev_max, (int, float)):
            slope = elev_max - elev_min
            if slope > 500: score += 0.5

    return min(10, round(score, 1))


def _compute_flood_risk(forecast, archive, elevation_data, water_data):
    """Compute flood risk score (0-10)."""
    score = 0

    # Precipitation forecast
    precip = forecast.get("precipitation_sum", [])
    if precip:
        max_precip = max(p for p in precip if p is not None) if any(p is not None for p in precip) else 0
        total_precip = sum(p for p in precip if p is not None)
        if max_precip > 50: score += 3
        elif max_precip > 30: score += 2
        elif max_precip > 15: score += 1
        if total_precip > 100: score += 1.5
        elif total_precip > 50: score += 1

    # Recent rain saturation
    archive_precip = archive.get("precipitation_sum", [])
    if archive_precip:
        total_30d = sum(p for p in archive_precip if p is not None)
        if total_30d > 200: score += 2
        elif total_30d > 100: score += 1.5
        elif total_30d > 50: score += 1

    # Low elevation
    if isinstance(elevation_data, dict):
        center_elev = elevation_data.get("center_elevation", 100)
        if isinstance(center_elev, (int, float)):
            if center_elev < 10: score += 2
            elif center_elev < 50: score += 1.5
            elif center_elev < 100: score += 1

    # Water proximity
    if isinstance(water_data, dict):
        waterways = water_data.get("waterways", [])
        water_bodies = water_data.get("water_bodies", [])
        if len(waterways) > 5: score += 1
        if len(water_bodies) > 2: score += 0.5

    return min(10, round(score, 1))


def _compute_landslide_risk(forecast, archive, elevation_data, soil_data, eq_data):
    """Compute landslide risk score (0-10)."""
    score = 0

    # Steep terrain
    if isinstance(elevation_data, dict):
        elev_min = elevation_data.get("min_elevation", 0)
        elev_max = elevation_data.get("max_elevation", 0)
        if isinstance(elev_min, (int, float)) and isinstance(elev_max, (int, float)):
            relief = elev_max - elev_min
            if relief > 1000: score += 3
            elif relief > 500: score += 2.5
            elif relief > 200: score += 2
            elif relief > 100: score += 1

    # Clay content (high clay = unstable)
    if isinstance(soil_data, dict):
        try:
            layers = soil_data.get("properties", {}).get("layers", [])
            for layer in layers:
                if layer.get("name") == "clay":
                    depths = layer.get("depths", [])
                    if depths:
                        val = depths[0].get("values", {}).get("mean", 0)
                        clay_pct = (val or 0) / 10
                        if clay_pct > 50: score += 2
                        elif clay_pct > 35: score += 1.5
                        elif clay_pct > 20: score += 1
        except Exception:
            pass

    # Heavy rain trigger
    precip = forecast.get("precipitation_sum", [])
    if precip:
        max_precip = max(p for p in precip if p is not None) if any(p is not None for p in precip) else 0
        if max_precip > 40: score += 2
        elif max_precip > 20: score += 1.5
        elif max_precip > 10: score += 1

    # Seismic activity
    if isinstance(eq_data, dict):
        quakes = eq_data.get("features", [])
        if len(quakes) > 20: score += 2
        elif len(quakes) > 5: score += 1.5
        elif len(quakes) > 0: score += 1

    return min(10, round(score, 1))


def _risk_gauge(label, score, color):
    """Render a risk gauge card."""
    level = "LOW" if score < 3 else "MODERATE" if score < 6 else "HIGH" if score < 8 else "CRITICAL"
    pct = score * 10
    st.markdown(f"""
    <div style="background:#1e293b; border-radius:12px; padding:1.2rem; border-left:4px solid {color};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:{color}; font-weight:700; font-size:1.1rem;">{label}</span>
            <span style="color:white; font-size:1.5rem; font-weight:bold;">{score}/10</span>
        </div>
        <div style="background:#334155; border-radius:8px; height:12px; margin:8px 0;">
            <div style="background:{color}; width:{pct}%; height:100%; border-radius:8px;"></div>
        </div>
        <span style="color:#94a3b8; font-size:0.85rem;">{level}</span>
    </div>
    """, unsafe_allow_html=True)


def render_predictive_risk_tab():
    """Main render function for Predictive Risk Model tab."""
    st.markdown("""
    <div class="tab-header red">
        <h4>🔥 Predictive Risk Model</h4>
        <p>Fire, flood &amp; landslide risk prediction with 7-day forecast and heatmap visualization</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="pr_preset")
    preset_data = ANALYSIS_PRESETS.get(preset)
    d_lat = preset_data.get("lat", 41.90) if preset_data else 41.90
    d_lon = preset_data.get("lon", 12.50) if preset_data else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01, key="pr_lat", format="%.4f")
        with c2:
            lon = st.number_input("Longitude", -180.0, 180.0, d_lon, step=0.01, key="pr_lon", format="%.4f")

    if st.button("Analyze Risk", type="primary", use_container_width=True):
        progress = st.progress(0)

        with st.spinner("Fetching weather forecast..."):
            forecast = _fetch_forecast_7d(lat, lon)
            archive = _fetch_archive_30d(lat, lon)
        progress.progress(25)

        with st.spinner("Fetching terrain data..."):
            try:
                elevation = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5)
            except Exception as e:
                logger.warning(f"Elevation fetch error: {e}")
                elevation = {}
            try:
                soil = fetch_soil_data(lat, lon)
            except Exception as e:
                logger.warning(f"Soil fetch error: {e}")
                soil = {}
        progress.progress(50)

        with st.spinner("Fetching hazard data..."):
            water = fetch_water_features(lat, lon, radius=5000)
            earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        progress.progress(75)

        # Compute risks
        fire_score = _compute_fire_risk(forecast, archive, elevation, soil)
        flood_score = _compute_flood_risk(forecast, archive, elevation, water)
        slide_score = _compute_landslide_risk(forecast, archive, elevation, soil, earthquakes)
        progress.progress(100)

        st.session_state["pr_results"] = {
            "fire": fire_score, "flood": flood_score, "landslide": slide_score,
            "forecast": forecast, "lat": lat, "lon": lon,
        }

    if "pr_results" in st.session_state:
        r = st.session_state["pr_results"]
        fire_score = r["fire"]
        flood_score = r["flood"]
        slide_score = r["landslide"]
        forecast = r["forecast"]
        lat = r["lat"]
        lon = r["lon"]

        st.markdown("---")
        st.markdown("### Risk Assessment")

        # Gauge cards
        g1, g2, g3 = st.columns(3)
        with g1:
            _risk_gauge("Fire Risk", fire_score, RISK_COLORS["Fire"])
        with g2:
            _risk_gauge("Flood Risk", flood_score, RISK_COLORS["Flood"])
        with g3:
            _risk_gauge("Landslide Risk", slide_score, RISK_COLORS["Landslide"])

        # Overall risk
        overall = round(max(fire_score, flood_score, slide_score), 1)
        level_color = "#10b981" if overall < 3 else "#f59e0b" if overall < 6 else "#ef4444"
        st.markdown(f"""
        <div style="text-align:center; margin:1rem 0;">
            <span style="font-size:1.2rem; color:#94a3b8;">Overall Risk Level: </span>
            <span style="font-size:1.5rem; font-weight:bold; color:{level_color};">{overall}/10</span>
        </div>
        """, unsafe_allow_html=True)

        # Radar chart
        st.markdown("### Risk Profile")
        categories = ["Fire", "Flood", "Landslide"]
        values = [fire_score, flood_score, slide_score] + [fire_score]
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            line_color="#06b6d4",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            height=350,
            margin=dict(t=30, b=30),
        )
        st.plotly_chart(fig, use_container_width=True, key="prr_gauge")

        # 7-day forecast timeline
        if forecast:
            st.markdown("### 7-Day Weather Forecast")
            dates = forecast.get("time", [])
            temp_max = forecast.get("temperature_2m_max", [])
            temp_min = forecast.get("temperature_2m_min", [])
            precip = forecast.get("precipitation_sum", [])
            wind = forecast.get("wind_speed_10m_max", [])

            if dates:
                fig2 = go.Figure()
                if temp_max:
                    fig2.add_trace(go.Scatter(x=dates, y=temp_max, name="Temp Max (C)", line_color="#ef4444"))
                if temp_min:
                    fig2.add_trace(go.Scatter(x=dates, y=temp_min, name="Temp Min (C)", line_color="#3b82f6"))
                if precip:
                    fig2.add_trace(go.Bar(x=dates, y=precip, name="Precip (mm)", marker_color="#06b6d4", opacity=0.5))
                fig2.update_layout(height=350, margin=dict(t=30, b=30), barmode="overlay")
                st.plotly_chart(fig2, use_container_width=True, key="prr_radar")

        # Heatmap
        st.markdown("### Risk Heatmap")
        m = MapFactory.create_base_map(center=(lat, lon), zoom=10, tile_layer="cartodb_dark")
        MapFactory.add_marker(m, (lat, lon), popup="Analysis Point", icon="warning", icon_color="red")

        # Generate heatmap points around location
        heat_data = []
        for dlat in np.linspace(-0.1, 0.1, 10):
            for dlon in np.linspace(-0.1, 0.1, 10):
                weight = max(fire_score, flood_score, slide_score) * (1 - (abs(dlat) + abs(dlon)) * 3)
                if weight > 0:
                    heat_data.append((lat + dlat, lon + dlon, weight))

        if heat_data:
            MapFactory.add_heatmap(m, heat_data, radius=25, blur=20, name="Risk Heatmap")

        folium.LayerControl().add_to(m)
        st_html(m._repr_html_(), height=450)

        # Export risk summary
        st.markdown("---")
        risk_df = pd.DataFrame([{
            "Metric": "Fire Risk", "Score": fire_score, "Level": "LOW" if fire_score < 3 else "MODERATE" if fire_score < 6 else "HIGH",
        }, {
            "Metric": "Flood Risk", "Score": flood_score, "Level": "LOW" if flood_score < 3 else "MODERATE" if flood_score < 6 else "HIGH",
        }, {
            "Metric": "Landslide Risk", "Score": slide_score, "Level": "LOW" if slide_score < 3 else "MODERATE" if slide_score < 6 else "HIGH",
        }])
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
        csv_data = risk_df.to_csv(index=False)
        st.download_button("📥 Download Risk Assessment (CSV)", data=csv_data,
                           file_name=f"risk_assessment_{lat:.2f}_{lon:.2f}.csv", mime="text/csv")

