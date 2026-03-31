"""
Multi-Hazard Scenario AI — Combined multi-hazard scenario modeling.
Simulates compound disaster scenarios (earthquake+landslide, storm+flood,
drought+fire) with cascading effect analysis and impact assessment.
Uses: Open-Meteo, USGS, Open Topo Data, ISRIC SoilGrids, Overpass.
"""

import math
import logging

import numpy as np
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_earthquakes,
    compute_risk_assessment,
)

logger = logging.getLogger(__name__)

# ── Hazard scenarios ────────────────────────────────────────────────────────

SCENARIOS = {
    "earthquake_landslide": {
        "name": "Earthquake + Landslide",
        "icon": "warning",
        "color": "#ef4444",
        "primary": "seismic",
        "secondary": "landslide",
        "triggers": "Strong earthquake destabilizes steep terrain, triggering landslides.",
        "factors": ["earthquake_mag", "slope", "clay_content", "precipitation", "vegetation"],
    },
    "storm_flood": {
        "name": "Storm + Flood",
        "icon": "thunderstorm",
        "color": "#3b82f6",
        "primary": "meteorological",
        "secondary": "flood",
        "triggers": "Intense storm system produces heavy rainfall causing flash floods.",
        "factors": ["precipitation", "wind_speed", "elevation", "water_proximity", "drainage"],
    },
    "drought_fire": {
        "name": "Drought + Wildfire",
        "icon": "local_fire_department",
        "color": "#f97316",
        "primary": "drought",
        "secondary": "wildfire",
        "triggers": "Extended drought dries vegetation, creating wildfire conditions.",
        "factors": ["temperature", "humidity", "wind_speed", "vegetation", "precipitation_deficit"],
    },
    "flood_contamination": {
        "name": "Flood + Water Contamination",
        "icon": "water_damage",
        "color": "#8b5cf6",
        "primary": "flood",
        "secondary": "contamination",
        "triggers": "Flooding overwhelms sanitation, contaminating water supply.",
        "factors": ["flood_risk", "infrastructure_density", "water_proximity", "soil_permeability"],
    },
    "seismic_infrastructure": {
        "name": "Earthquake + Infrastructure Collapse",
        "icon": "domain_disabled",
        "color": "#dc2626",
        "primary": "seismic",
        "secondary": "structural",
        "triggers": "Earthquake damages buildings and roads in densely built area.",
        "factors": ["earthquake_mag", "building_density", "road_network", "soil_type"],
    },
}


@st.cache_data(ttl=1800)
def model_scenarios(lat: float, lon: float) -> dict:
    """Model multi-hazard scenarios for a location."""
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=150, days=365) or {}
    risk = compute_risk_assessment(earthquakes, water, weather, elev)

    # ── Extract data ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 25
    max_temp = max(valid_tmax) if valid_tmax else 30

    humidity = current.get("relative_humidity_2m", 50) or 50

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    max_precip = max(valid_precip) if valid_precip else 0
    total_precip = sum(valid_precip) if valid_precip else 0

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    peak_wind = max(valid_wind) if valid_wind else 0
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0
    min_elev = min(valid_elevs) if valid_elevs else 100

    # Soil
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay = _sv("clay") or 20
    sand = _sv("sand") or 40

    # Water & infra
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(w_elements)

    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))

    # Earthquake data
    features = earthquakes.get("features", [])
    max_mag = max((f["properties"].get("mag", 0) or 0 for f in features), default=0)
    eq_count = len(features)

    # Risk (flat dict)
    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0
    flood_risk = risk.get("Flood", 0) if isinstance(risk, dict) else 0

    # ── Model each scenario ──
    scenario_results = {}

    # 1. Earthquake + Landslide
    eq_ls_primary = min(10, seismic_risk + max_mag * 0.5)
    slope_factor = min(10, elev_range / 40)
    clay_factor = min(10, clay / 6)
    precip_factor = min(10, total_precip / 5)
    eq_ls_cascade = (slope_factor * 0.4 + clay_factor * 0.3 + precip_factor * 0.2 + eq_ls_primary * 0.1)
    eq_ls_combined = min(10, eq_ls_primary * 0.5 + eq_ls_cascade * 0.5)

    scenario_results["earthquake_landslide"] = {
        "primary_score": round(eq_ls_primary, 1),
        "cascade_score": round(eq_ls_cascade, 1),
        "combined_score": round(eq_ls_combined, 1),
        "factors": {
            "Seismic Activity": round(seismic_risk, 1),
            "Max Magnitude": round(max_mag, 1),
            "Slope Steepness": round(slope_factor, 1),
            "Clay Content": round(clay_factor, 1),
            "Precipitation": round(precip_factor, 1),
        },
        "impact": _impact_assessment(eq_ls_combined, buildings),
    }

    # 2. Storm + Flood
    storm_primary = min(10, peak_wind / 10 + max_precip / 4)
    low_elev = max(0, min(10, (50 - min_elev) / 5)) if min_elev < 50 else 0
    water_prox = min(10, water_count / 3)
    drainage = max(0, 10 - clay / 5)
    sf_cascade = (low_elev * 0.3 + water_prox * 0.3 + drainage * 0.2 + storm_primary * 0.2)
    sf_combined = min(10, storm_primary * 0.4 + sf_cascade * 0.6)

    scenario_results["storm_flood"] = {
        "primary_score": round(storm_primary, 1),
        "cascade_score": round(sf_cascade, 1),
        "combined_score": round(sf_combined, 1),
        "factors": {
            "Peak Wind": round(min(10, peak_wind / 10), 1),
            "Max Precipitation": round(min(10, max_precip / 4), 1),
            "Low Elevation": round(low_elev, 1),
            "Water Proximity": round(water_prox, 1),
            "Drainage": round(drainage, 1),
        },
        "impact": _impact_assessment(sf_combined, buildings),
    }

    # 3. Drought + Fire
    temp_factor = min(10, max(0, (max_temp - 25) / 2))
    humid_factor = max(0, min(10, (60 - humidity) / 6))
    wind_factor = min(10, avg_wind / 8)
    precip_deficit = max(0, min(10, (10 - total_precip) / 2))
    df_primary = (temp_factor * 0.3 + humid_factor * 0.3 + precip_deficit * 0.4)
    df_cascade = (wind_factor * 0.4 + temp_factor * 0.3 + humid_factor * 0.3)
    df_combined = min(10, df_primary * 0.5 + df_cascade * 0.5)

    scenario_results["drought_fire"] = {
        "primary_score": round(df_primary, 1),
        "cascade_score": round(df_cascade, 1),
        "combined_score": round(df_combined, 1),
        "factors": {
            "Temperature": round(temp_factor, 1),
            "Low Humidity": round(humid_factor, 1),
            "Wind Speed": round(wind_factor, 1),
            "Precip Deficit": round(precip_deficit, 1),
        },
        "impact": _impact_assessment(df_combined, buildings),
    }

    # 4. Flood + Contamination
    fc_primary = min(10, flood_risk + water_count / 3)
    infra_factor = min(10, buildings / 10)
    soil_perm = min(10, sand / 8)
    fc_cascade = (infra_factor * 0.4 + water_prox * 0.3 + soil_perm * 0.3)
    fc_combined = min(10, fc_primary * 0.5 + fc_cascade * 0.5)

    scenario_results["flood_contamination"] = {
        "primary_score": round(fc_primary, 1),
        "cascade_score": round(fc_cascade, 1),
        "combined_score": round(fc_combined, 1),
        "factors": {
            "Flood Risk": round(flood_risk, 1),
            "Infrastructure": round(infra_factor, 1),
            "Water Features": round(water_prox, 1),
            "Soil Permeability": round(soil_perm, 1),
        },
        "impact": _impact_assessment(fc_combined, buildings),
    }

    # 5. Earthquake + Infrastructure
    si_primary = min(10, seismic_risk + max_mag * 0.5)
    building_vuln = min(10, buildings / 8)
    road_vuln = min(10, roads / 5)
    soil_factor = min(10, clay / 5)  # soft soil amplifies shaking
    si_cascade = (building_vuln * 0.4 + road_vuln * 0.3 + soil_factor * 0.3)
    si_combined = min(10, si_primary * 0.5 + si_cascade * 0.5)

    scenario_results["seismic_infrastructure"] = {
        "primary_score": round(si_primary, 1),
        "cascade_score": round(si_cascade, 1),
        "combined_score": round(si_combined, 1),
        "factors": {
            "Seismic Risk": round(seismic_risk, 1),
            "Building Density": round(building_vuln, 1),
            "Road Network": round(road_vuln, 1),
            "Soil Amplification": round(soil_factor, 1),
        },
        "impact": _impact_assessment(si_combined, buildings),
    }

    # Worst-case scenario
    worst = max(scenario_results, key=lambda k: scenario_results[k]["combined_score"])

    return {
        "scenarios": scenario_results,
        "worst_case": worst,
        "worst_score": scenario_results[worst]["combined_score"],
    }


def _impact_assessment(score: float, buildings: int) -> dict:
    """Generate impact assessment based on combined score."""
    if score >= 8:
        level = "CATASTROPHIC"
        color = "#dc2626"
        desc = "Severe cascading effects expected. Major infrastructure damage likely."
    elif score >= 6:
        level = "SEVERE"
        color = "#ef4444"
        desc = "Significant cascading damage expected. Emergency response needed."
    elif score >= 4:
        level = "MODERATE"
        color = "#f59e0b"
        desc = "Moderate cascading effects possible. Preparedness recommended."
    elif score >= 2:
        level = "LOW"
        color = "#3b82f6"
        desc = "Minor cascading effects. Low risk scenario."
    else:
        level = "MINIMAL"
        color = "#10b981"
        desc = "Negligible cascading risk."

    pop_exposure = "HIGH" if buildings > 50 else "MODERATE" if buildings > 10 else "LOW"

    return {
        "level": level,
        "color": color,
        "description": desc,
        "population_exposure": pop_exposure,
        "buildings_at_risk": buildings,
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_multi_hazard_tab():
    """Render the Multi-Hazard Scenario AI tab."""
    st.markdown("## Multi-Hazard Scenario AI")
    st.caption("Compound disaster scenario modeling with cascading effect analysis")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="mh_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="mh_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="mh_lon", format="%.4f")

    if st.button("Model Scenarios", type="primary", use_container_width=True):
        with st.spinner("Modeling 5 compound disaster scenarios..."):
            result = model_scenarios(lat, lon)

        if not result:
            st.error("Failed to model scenarios.")
            return

        scenarios = result["scenarios"]
        worst = result["worst_case"]
        worst_score = result["worst_score"]

        # ── Worst case header ──
        worst_info = SCENARIOS[worst]
        worst_impact = scenarios[worst]["impact"]
        wc = worst_impact["color"]

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {wc}22, {wc}44);
                    border-left:5px solid {wc}; border-radius:10px;
                    padding:20px; margin:10px 0;">
            <div style="color:#888; font-size:12px;">HIGHEST RISK SCENARIO</div>
            <div style="color:{wc}; font-size:24px; font-weight:bold; margin:4px 0;">
                {worst_info['name']}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="color:#aaa; font-size:13px;">{worst_info['triggers']}</div>
                <div style="color:{wc}; font-size:36px; font-weight:bold;">
                    {worst_score}<span style="font-size:14px; color:#888;">/10</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Scenario comparison radar ──
        st.markdown("### Scenario Risk Comparison")
        scenario_names = [SCENARIOS[k]["name"] for k in scenarios]
        combined_scores = [scenarios[k]["combined_score"] for k in scenarios]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=combined_scores + [combined_scores[0]],
            theta=scenario_names + [scenario_names[0]],
            fill="toself",
            fillcolor="rgba(239,68,68,0.15)",
            line=dict(color="#ef4444", width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=400,
            margin=dict(t=30, b=30, l=80, r=80),
        )
        st.plotly_chart(fig, use_container_width=True, key="mulhaz_pchart1")

        # ── Scenario cards ──
        st.markdown("### Scenario Details")
        for sc_id, sc_data in scenarios.items():
            sc_info = SCENARIOS[sc_id]
            impact = sc_data["impact"]
            combined = sc_data["combined_score"]

            st.markdown(f"""
            <div style="background:#1a1a2e; border-left:4px solid {sc_info['color']};
                        border-radius:10px; padding:16px; margin:10px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:{sc_info['color']}; font-weight:bold; font-size:16px;">
                            {sc_info['name']}
                        </span>
                        <span style="background:{impact['color']}22; color:{impact['color']};
                                    padding:2px 8px; border-radius:4px; font-size:11px; margin-left:8px;">
                            {impact['level']}
                        </span>
                    </div>
                    <span style="color:{impact['color']}; font-size:28px; font-weight:bold;">
                        {combined}<span style="font-size:12px; color:#888;">/10</span>
                    </span>
                </div>
                <div style="color:#888; font-size:12px; margin:6px 0;">
                    Primary: {sc_data['primary_score']} | Cascade: {sc_data['cascade_score']} |
                    Pop Exposure: {impact['population_exposure']}
                </div>
                <div style="color:#aaa; font-size:13px;">{impact['description']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Factor breakdown
            with st.expander(f"Factor Details — {sc_info['name']}"):
                factors = sc_data["factors"]
                f_names = list(factors.keys())
                f_vals = list(factors.values())
                f_colors = ["#10b981" if v < 3 else "#f59e0b" if v < 6 else "#ef4444" for v in f_vals]

                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=f_vals,
                    y=f_names,
                    orientation="h",
                    marker_color=f_colors,
                    text=[f"{v}" for v in f_vals],
                    textposition="auto",
                ))
                fig2.update_layout(
                    height=max(200, len(f_names) * 35),
                    margin=dict(t=10, b=20, l=150),
                    xaxis=dict(range=[0, 10]),
                )
                st.plotly_chart(fig2, use_container_width=True, key="mulhaz_pchart2")
