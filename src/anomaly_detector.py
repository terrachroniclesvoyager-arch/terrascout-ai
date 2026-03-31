"""
Environmental Anomaly Detector for TerraScout AI.
Identifies statistical anomalies and unusual patterns in environmental data
by comparing local values against regional baselines and global norms.
Detects: climate outliers, biodiversity hotspots/coldspots, geological anomalies,
seismic clusters, soil extremes, and land use incongruities.
"""

import logging
import math
import pandas as pd
import numpy as np
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_biodiversity,
    fetch_earthquakes,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_geology,
    compute_species_breakdown,
    fetch_gbif_occurrences,
    haversine_distance,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False

# ═══════════════════════════════════════════════════════════════
# GLOBAL BASELINES — expected ranges for environmental parameters
# Values represent (min_normal, max_normal) for temperate/tropical zones
# ═══════════════════════════════════════════════════════════════

GLOBAL_BASELINES = {
    "elevation_m": {"mean": 370, "std": 500, "unit": "m"},
    "temperature_c": {"mean": 17.0, "std": 10.0, "unit": "C"},
    "humidity_pct": {"mean": 60.0, "std": 20.0, "unit": "%"},
    "wind_kmh": {"mean": 15.0, "std": 10.0, "unit": "km/h"},
    "precip_mm": {"mean": 2.0, "std": 5.0, "unit": "mm"},
    "soil_ph": {"mean": 6.5, "std": 1.5, "unit": "pH"},
    "soil_clay_pct": {"mean": 25.0, "std": 15.0, "unit": "%"},
    "soil_sand_pct": {"mean": 40.0, "std": 20.0, "unit": "%"},
    "soil_organic_c": {"mean": 20.0, "std": 15.0, "unit": "g/kg"},
    "species_count": {"mean": 80, "std": 60, "unit": "species"},
    "observation_density": {"mean": 200, "std": 300, "unit": "obs"},
    "seismic_count": {"mean": 5, "std": 8, "unit": "events/yr"},
    "water_feature_count": {"mean": 5, "std": 5, "unit": "features"},
}


def _compute_z_score(value, key):
    """Compute z-score against global baseline."""
    baseline = GLOBAL_BASELINES.get(key)
    if baseline is None or baseline["std"] == 0:
        return 0.0
    return (value - baseline["mean"]) / baseline["std"]


def _severity_label(z_score):
    """Convert z-score to human-readable severity."""
    az = abs(z_score)
    if az < 1.0:
        return "Normal"
    elif az < 2.0:
        return "Unusual"
    elif az < 3.0:
        return "Anomalous"
    else:
        return "Extreme"


def _severity_color(z_score):
    """Color for severity level."""
    az = abs(z_score)
    if az < 1.0:
        return "#10b981"  # green
    elif az < 2.0:
        return "#f59e0b"  # amber
    elif az < 3.0:
        return "#f97316"  # orange
    else:
        return "#ef4444"  # red


def _severity_icon(z_score):
    """Icon for severity."""
    az = abs(z_score)
    if az < 1.0:
        return "OK"
    elif az < 2.0:
        return "!"
    elif az < 3.0:
        return "!!"
    else:
        return "!!!"


# ═══════════════════════════════════════════════════════════════
# DATA COLLECTION — gather all environmental parameters
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _collect_environmental_data(lat, lon):
    """Collect all environmental parameters for anomaly detection."""
    data = {"lat": lat, "lon": lon}

    # Elevation
    try:
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)
        center_elev = elev.get("center_elevation", 0)
        min_elev = elev.get("min_elevation", 0)
        max_elev = elev.get("max_elevation", 0)
        avg_elev = elev.get("avg_elevation", 0)
        data["elevation_m"] = center_elev if isinstance(center_elev, (int, float)) else 0
        data["elev_min"] = min_elev if isinstance(min_elev, (int, float)) else 0
        data["elev_max"] = max_elev if isinstance(max_elev, (int, float)) else 0
        data["elev_avg"] = avg_elev if isinstance(avg_elev, (int, float)) else 0
        data["terrain_roughness"] = data["elev_max"] - data["elev_min"]
    except Exception:
        logger.warning("Anomaly detector: elevation fetch failed")
        data["elevation_m"] = 0
        data["terrain_roughness"] = 0

    # Weather
    try:
        wx = fetch_weather_data(lat, lon)
        current = wx.get("current", {})
        data["temperature_c"] = current.get("temperature_2m", 0) or 0
        data["humidity_pct"] = current.get("relative_humidity_2m", 0) or 0
        data["wind_kmh"] = current.get("wind_speed_10m", 0) or 0
        data["precip_mm"] = current.get("precipitation", 0) or 0

        # 7-day forecast for trend detection
        daily = wx.get("daily", {})
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precip_sum = daily.get("precipitation_sum", [])
        if temps_max and temps_min:
            avg_temps = [(mx + mn) / 2 for mx, mn in zip(temps_max, temps_min)]
            data["temp_7d_avg"] = round(sum(avg_temps) / len(avg_temps), 1)
            data["temp_7d_range"] = round(max(avg_temps) - min(avg_temps), 1)
        if precip_sum:
            data["precip_7d_total"] = round(sum(p for p in precip_sum if p), 1)
    except Exception:
        logger.warning("Anomaly detector: weather fetch failed")
        data["temperature_c"] = 0
        data["humidity_pct"] = 0
        data["wind_kmh"] = 0
        data["precip_mm"] = 0

    # Soil
    try:
        soil = fetch_soil_data(lat, lon)
        props = soil.get("properties", {}).get("layers", [])
        for layer in props:
            prop_name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    if prop_name == "clay":
                        data["soil_clay_pct"] = round(val / 10, 1)
                    elif prop_name == "sand":
                        data["soil_sand_pct"] = round(val / 10, 1)
                    elif prop_name == "phh2o":
                        data["soil_ph"] = round(val / 10, 1)
                    elif prop_name == "soc":
                        data["soil_organic_c"] = round(val / 10, 1)
                    elif prop_name == "nitrogen":
                        data["soil_nitrogen"] = round(val / 10, 1)
    except Exception:
        logger.warning("Anomaly detector: soil fetch failed")

    # Biodiversity
    try:
        inat = fetch_biodiversity(lat, lon, radius_km=10)
        gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
        breakdown = compute_species_breakdown(inat, gbif)
        data["species_count"] = breakdown.get("gbif_unique_species", 0) + len(breakdown.get("top_species", []))
        data["observation_density"] = breakdown.get("inat_total", 0) + breakdown.get("gbif_total", 0)
    except Exception:
        logger.warning("Anomaly detector: biodiversity fetch failed")
        data["species_count"] = 0
        data["observation_density"] = 0

    # Seismic
    try:
        eq = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        features = eq.get("features", [])
        data["seismic_count"] = len(features)
        if features:
            mags = [f.get("properties", {}).get("mag", 0) for f in features]
            data["seismic_max_mag"] = max(m for m in mags if m is not None) if mags else 0
            data["seismic_avg_mag"] = round(sum(m for m in mags if m) / max(len(mags), 1), 2)
        else:
            data["seismic_max_mag"] = 0
            data["seismic_avg_mag"] = 0
    except Exception:
        logger.warning("Anomaly detector: seismic fetch failed")
        data["seismic_count"] = 0
        data["seismic_max_mag"] = 0

    # Water features
    try:
        water = fetch_water_features(lat, lon, radius=5000)
        elements = water.get("elements", [])
        data["water_feature_count"] = len(elements)
    except Exception:
        logger.warning("Anomaly detector: water fetch failed")
        data["water_feature_count"] = 0

    # Geology
    try:
        geo = fetch_geology(lat, lon)
        if geo and geo.get("success"):
            data["rock_type"] = geo.get("rocktype", "Unknown")
            data["geological_age"] = geo.get("age", "Unknown")
        else:
            data["rock_type"] = "Unknown"
            data["geological_age"] = "Unknown"
    except Exception:
        data["rock_type"] = "Unknown"
        data["geological_age"] = "Unknown"

    return data


# ═══════════════════════════════════════════════════════════════
# ANOMALY DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════

def _detect_anomalies(data):
    """Analyze environmental data and detect anomalies. Returns list of anomaly dicts."""
    anomalies = []

    # Check each parameter against global baselines
    for key, baseline in GLOBAL_BASELINES.items():
        val = data.get(key)
        if val is None or not isinstance(val, (int, float)):
            continue
        z = _compute_z_score(val, key)
        severity = _severity_label(z)
        if severity != "Normal":
            direction = "above" if z > 0 else "below"
            anomalies.append({
                "parameter": key.replace("_", " ").title(),
                "value": val,
                "unit": baseline["unit"],
                "expected": f"{baseline['mean']} +/- {baseline['std']}",
                "z_score": round(z, 2),
                "severity": severity,
                "direction": direction,
                "color": _severity_color(z),
                "description": _describe_anomaly(key, val, z, direction),
            })

    # Cross-parameter anomalies
    cross = _detect_cross_anomalies(data)
    anomalies.extend(cross)

    # Sort by absolute z-score (most extreme first)
    anomalies.sort(key=lambda a: abs(a.get("z_score", 0)), reverse=True)
    return anomalies


def _describe_anomaly(key, value, z_score, direction):
    """Generate human-readable description for an anomaly."""
    az = abs(z_score)
    intensity = "slightly" if az < 2 else "significantly" if az < 3 else "extremely"

    descriptions = {
        "elevation_m": f"Elevation is {intensity} {direction} average ({value}m). {'High altitude environment.' if direction == 'above' else 'Very low-lying area.'}",
        "temperature_c": f"Temperature is {intensity} {direction} global average ({value}C). {'Possible heat stress conditions.' if direction == 'above' else 'Cold environment detected.'}",
        "humidity_pct": f"Humidity {intensity} {direction} normal ({value}%). {'Very dry conditions — drought risk.' if direction == 'below' else 'Very humid — mold/disease risk.'}",
        "wind_kmh": f"Wind speed {intensity} {direction} average ({value} km/h). {'High wind energy potential.' if direction == 'above' else ''}",
        "precip_mm": f"Precipitation {intensity} {direction} normal ({value}mm). {'Heavy rainfall — flood risk.' if direction == 'above' else 'Drought conditions possible.'}",
        "soil_ph": f"Soil pH {intensity} {direction} neutral ({value}). {'Alkaline soil.' if direction == 'above' else 'Acidic soil — limited crop range.'}",
        "soil_clay_pct": f"Clay content {intensity} {direction} average ({value}%). {'Heavy clay — drainage issues.' if direction == 'above' else 'Sandy soil — low water retention.'}",
        "soil_sand_pct": f"Sand content {intensity} {direction} average ({value}%). {'Sandy soil — rapid drainage.' if direction == 'above' else ''}",
        "soil_organic_c": f"Organic carbon {intensity} {direction} average ({value} g/kg). {'Extremely fertile soil!' if direction == 'above' else 'Low fertility — amendment needed.'}",
        "species_count": f"Biodiversity {intensity} {direction} average ({value} species). {'Biodiversity hotspot!' if direction == 'above' else 'Low diversity — ecological concern.'}",
        "observation_density": f"Observation density {intensity} {direction} average ({value}). {'Well-studied area.' if direction == 'above' else 'Data-sparse region.'}",
        "seismic_count": f"Seismic activity {intensity} {direction} average ({value} events/yr). {'Seismically active zone!' if direction == 'above' else ''}",
        "water_feature_count": f"Water features {intensity} {direction} average ({value}). {'Water-rich area.' if direction == 'above' else 'Arid zone — limited water.'}",
    }
    return descriptions.get(key, f"{key} is {intensity} {direction} average.")


def _detect_cross_anomalies(data):
    """Detect anomalies from correlations between multiple parameters."""
    cross = []

    temp = data.get("temperature_c", 0)
    humidity = data.get("humidity_pct", 0)
    precip = data.get("precip_mm", 0)
    wind = data.get("wind_kmh", 0)
    elev = data.get("elevation_m", 0)
    species = data.get("species_count", 0)
    seismic = data.get("seismic_count", 0)
    clay = data.get("soil_clay_pct", 0)

    # Heat + Low humidity = fire risk
    if temp > 30 and humidity < 30:
        cross.append({
            "parameter": "Fire Risk Pattern",
            "value": f"{temp}C / {humidity}%",
            "unit": "",
            "expected": "T<30C or H>30%",
            "z_score": round((temp - 30) / 5 + (30 - humidity) / 10, 2),
            "severity": "Anomalous",
            "direction": "above",
            "color": "#ef4444",
            "description": f"Hot ({temp}C) + dry ({humidity}% humidity) — elevated wildfire risk pattern.",
        })

    # High precipitation + clay soil = flood risk
    if precip > 5 and clay > 40:
        cross.append({
            "parameter": "Flood Risk Pattern",
            "value": f"{precip}mm / {clay}% clay",
            "unit": "",
            "expected": "P<5mm or Clay<40%",
            "z_score": round((precip - 5) / 3 + (clay - 40) / 10, 2),
            "severity": "Anomalous",
            "direction": "above",
            "color": "#3b82f6",
            "description": f"Heavy precip ({precip}mm) on clay soil ({clay}%) — poor drainage and flood risk.",
        })

    # High elevation + high seismic = landslide risk
    if elev > 1000 and seismic > 10:
        cross.append({
            "parameter": "Landslide Risk Pattern",
            "value": f"{elev}m / {seismic} quakes",
            "unit": "",
            "expected": "E<1000m or S<10",
            "z_score": round((elev - 1000) / 500 + (seismic - 10) / 5, 2),
            "severity": "Anomalous",
            "direction": "above",
            "color": "#f97316",
            "description": f"High terrain ({elev}m) in seismically active zone ({seismic} events) — landslide risk.",
        })

    # High species + low observations = understudied biodiversity hotspot
    if species > 150 and data.get("observation_density", 0) < 50:
        cross.append({
            "parameter": "Understudied Biodiversity Hotspot",
            "value": f"{species} spp / {data.get('observation_density', 0)} obs",
            "unit": "",
            "expected": "Normal correlation",
            "z_score": 2.5,
            "severity": "Anomalous",
            "direction": "above",
            "color": "#8b5cf6",
            "description": f"High species count ({species}) with few observations — potential understudied biodiversity hotspot.",
        })

    # Very high wind + flat terrain = wind energy anomaly
    if wind > 30 and data.get("terrain_roughness", 0) < 100:
        cross.append({
            "parameter": "Wind Energy Opportunity",
            "value": f"{wind} km/h / flat",
            "unit": "",
            "expected": "W<30 km/h",
            "z_score": round((wind - 30) / 10, 2),
            "severity": "Unusual",
            "direction": "above",
            "color": "#06b6d4",
            "description": f"Consistently high winds ({wind} km/h) on flat terrain — exceptional wind energy potential.",
        })

    return cross


# ═══════════════════════════════════════════════════════════════
# VISUALIZATION
# ═══════════════════════════════════════════════════════════════

def _make_anomaly_gauge(anomaly):
    """Create a small gauge chart for a single anomaly."""
    z = anomaly["z_score"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=abs(z),
        title={"text": anomaly["parameter"], "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 5], "tickvals": [1, 2, 3, 4]},
            "bar": {"color": anomaly["color"]},
            "steps": [
                {"range": [0, 1], "color": "rgba(16, 185, 129, 0.2)"},
                {"range": [1, 2], "color": "rgba(245, 158, 11, 0.2)"},
                {"range": [2, 3], "color": "rgba(249, 115, 22, 0.2)"},
                {"range": [3, 5], "color": "rgba(239, 68, 68, 0.2)"},
            ],
            "threshold": {
                "line": {"color": anomaly["color"], "width": 3},
                "thickness": 0.75,
                "value": abs(z),
            },
        },
    ))
    fig.update_layout(height=200, margin=dict(t=40, b=10, l=30, r=30))
    return fig


def _make_deviation_chart(anomalies):
    """Horizontal bar chart showing all parameter deviations."""
    if not anomalies:
        return None

    params = [a["parameter"] for a in anomalies]
    z_scores = [a["z_score"] for a in anomalies]
    colors = [a["color"] for a in anomalies]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=params,
        x=z_scores,
        orientation="h",
        marker_color=colors,
        text=[f"{z:+.1f}s" for z in z_scores],
        textposition="outside",
    ))

    # Add reference lines
    fig.add_vline(x=-2, line_dash="dash", line_color="rgba(249,115,22,0.5)")
    fig.add_vline(x=2, line_dash="dash", line_color="rgba(249,115,22,0.5)")
    fig.add_vline(x=-3, line_dash="dash", line_color="rgba(239,68,68,0.5)")
    fig.add_vline(x=3, line_dash="dash", line_color="rgba(239,68,68,0.5)")
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)")

    fig.update_layout(
        title="Parameter Deviations from Global Baseline (z-scores)",
        xaxis_title="Standard Deviations from Mean",
        height=max(300, len(anomalies) * 40 + 100),
        margin=dict(t=50, b=40, l=10),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def _make_radar_overview(data):
    """Radar chart showing normalized values of all key parameters."""
    params = {
        "Elevation": data.get("elevation_m", 0) / 5000 * 100,
        "Temperature": (data.get("temperature_c", 0) + 30) / 80 * 100,
        "Humidity": data.get("humidity_pct", 0),
        "Wind": min(data.get("wind_kmh", 0) / 50 * 100, 100),
        "Soil pH": data.get("soil_ph", 7) / 14 * 100,
        "Biodiversity": min(data.get("species_count", 0) / 300 * 100, 100),
        "Seismic": min(data.get("seismic_count", 0) / 30 * 100, 100),
        "Water": min(data.get("water_feature_count", 0) / 20 * 100, 100),
    }

    categories = list(params.keys())
    values = list(params.values())
    values.append(values[0])  # close polygon

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill="toself",
        name="Location Profile",
        line_color="#06b6d4",
        fillcolor="rgba(6, 182, 212, 0.2)",
    ))

    # Add global baseline
    baseline_vals = [50] * len(categories) + [50]
    fig.add_trace(go.Scatterpolar(
        r=baseline_vals,
        theta=categories + [categories[0]],
        name="Global Baseline",
        line=dict(color="rgba(255,255,255,0.3)", dash="dash"),
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Environmental Profile vs Global Baseline",
        height=400,
        margin=dict(t=60, b=30),
    )
    return fig


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════

def render_anomaly_detector_tab():
    """Main render function for Anomaly Detector tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Anomaly Detector</h4>
        <p>Identify environmental anomalies — statistical deviations from global baselines across all parameters</p>
    </div>
    """, unsafe_allow_html=True)

    # Location input
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Preset Location",
                              ["Custom"] + [k for k in ANALYSIS_PRESETS.keys() if k != "Custom"],
                              key="anom_preset")
        p = ANALYSIS_PRESETS.get(preset)
    with col2:
        d_lat = p["lat"] if p else 41.9028
        lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01,
                              key="anom_lat", format="%.4f")
    with col3:
        d_lon = p["lon"] if p else 12.4964
        lon = st.number_input("Longitude", -180.0, 180.0,
                              p["lon"] if p else d_lon, step=0.01,
                              key="anom_lon", format="%.4f")

    # Sensitivity
    sensitivity = st.select_slider(
        "Detection Sensitivity",
        options=["Low (z > 3)", "Medium (z > 2)", "High (z > 1)"],
        value="Medium (z > 2)",
        key="anom_sensitivity",
    )
    z_threshold = {"Low (z > 3)": 3.0, "Medium (z > 2)": 2.0, "High (z > 1)": 1.0}[sensitivity]

    if st.button("Scan for Anomalies", type="primary", use_container_width=True):
        with st.spinner("Collecting environmental data..."):
            env_data = _collect_environmental_data(lat, lon)

        with st.spinner("Running anomaly detection..."):
            all_anomalies = _detect_anomalies(env_data)
            filtered = [a for a in all_anomalies if abs(a["z_score"]) >= z_threshold]

        st.session_state["anom_results"] = {
            "data": env_data,
            "anomalies": filtered,
            "all_anomalies": all_anomalies,
            "threshold": z_threshold,
        }

    # Display results
    if "anom_results" not in st.session_state:
        return

    results = st.session_state["anom_results"]
    env_data = results["data"]
    anomalies = results["anomalies"]
    all_anomalies = results["all_anomalies"]

    st.markdown("---")

    # Summary metrics
    st.markdown("### Scan Summary")
    s1, s2, s3, s4 = st.columns(4)
    extreme = sum(1 for a in anomalies if a["severity"] == "Extreme")
    anomalous = sum(1 for a in anomalies if a["severity"] == "Anomalous")
    unusual = sum(1 for a in anomalies if a["severity"] == "Unusual")
    normal_count = len(GLOBAL_BASELINES) - len(anomalies)

    with s1:
        st.metric("Extreme", extreme)
    with s2:
        st.metric("Anomalous", anomalous)
    with s3:
        st.metric("Unusual", unusual)
    with s4:
        st.metric("Normal", max(normal_count, 0))

    # Overall health score (inverted anomaly intensity)
    if all_anomalies:
        max_possible = len(GLOBAL_BASELINES) * 3
        total_deviation = sum(min(abs(a["z_score"]), 3) for a in all_anomalies)
        health = max(0, round(100 - (total_deviation / max_possible * 100)))
    else:
        health = 100

    health_color = "#10b981" if health >= 70 else "#f59e0b" if health >= 40 else "#ef4444"
    st.markdown(f"""
    <div style="text-align:center; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; border-left: 4px solid {health_color}; margin: 10px 0;">
        <div style="font-size: 2.5em; font-weight: bold; color: {health_color};">{health}/100</div>
        <div style="color: #9ca3af;">Environmental Normality Score</div>
        <div style="color: #6b7280; font-size: 0.85em;">Higher = more typical environment | Lower = more anomalous</div>
    </div>
    """, unsafe_allow_html=True)

    # Charts
    st.markdown("---")
    ch1, ch2 = st.columns(2)
    with ch1:
        radar_fig = _make_radar_overview(env_data)
        st.plotly_chart(radar_fig, use_container_width=True, key="anodet_pchart1")
    with ch2:
        if anomalies:
            dev_fig = _make_deviation_chart(anomalies)
            if dev_fig:
                st.plotly_chart(dev_fig, use_container_width=True, key="anodet_pchart2")
        else:
            st.success("No anomalies detected at this sensitivity level.")

    # Anomaly details
    if anomalies:
        st.markdown("### Detected Anomalies")

        # Top gauges (max 4)
        gauge_anomalies = anomalies[:4]
        gauge_cols = st.columns(len(gauge_anomalies))
        for i, anom in enumerate(gauge_anomalies):
            with gauge_cols[i]:
                fig = _make_anomaly_gauge(anom)
                st.plotly_chart(fig, use_container_width=True, key="anodet_pchart3")

        # Detailed table
        st.markdown("### Anomaly Report")
        rows = []
        for a in anomalies:
            rows.append({
                "Alert": _severity_icon(a["z_score"]),
                "Parameter": a["parameter"],
                "Value": f"{a['value']} {a['unit']}",
                "Expected": a["expected"],
                "Z-Score": f"{a['z_score']:+.2f}",
                "Severity": a["severity"],
                "Direction": a["direction"],
                "Description": a["description"],
            })
        df_report = pd.DataFrame(rows)
        st.dataframe(df_report, use_container_width=True, hide_index=True)

    # Raw data table
    with st.expander("Raw Environmental Data"):
        raw_rows = []
        for key, val in env_data.items():
            if key in ("lat", "lon", "rock_type", "geological_age"):
                continue
            if isinstance(val, (int, float)):
                baseline = GLOBAL_BASELINES.get(key)
                z = _compute_z_score(val, key) if baseline else 0
                raw_rows.append({
                    "Parameter": key.replace("_", " ").title(),
                    "Value": round(val, 2) if isinstance(val, float) else val,
                    "Z-Score": round(z, 2) if baseline else "-",
                    "Status": _severity_label(z) if baseline else "N/A",
                })
        if raw_rows:
            st.dataframe(pd.DataFrame(raw_rows), use_container_width=True, hide_index=True)

    # Export
    st.markdown("---")
    st.markdown("### Export")
    if anomalies:
        export_rows = []
        for a in anomalies:
            export_rows.append({
                "Parameter": a["parameter"],
                "Value": a["value"],
                "Unit": a["unit"],
                "Expected": a["expected"],
                "Z_Score": a["z_score"],
                "Severity": a["severity"],
                "Direction": a["direction"],
                "Description": a["description"],
                "Latitude": env_data["lat"],
                "Longitude": env_data["lon"],
            })
        df_export = pd.DataFrame(export_rows)
        if HAS_EXPORT:
            render_export_buttons(df_export, prefix="anomalies", lat_col="Latitude", lon_col="Longitude")
        else:
            csv = df_export.to_csv(index=False)
            st.download_button("Download Anomaly Report (CSV)", data=csv,
                               file_name="anomaly_report.csv", mime="text/csv")
    else:
        st.info("No anomalies to export at current sensitivity.")
