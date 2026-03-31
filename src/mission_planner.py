"""
Mission Planner AI — Given an objective (agriculture, construction, expedition,
energy, conservation), generates optimized plans with logistics, timing,
risk mitigation, and resource analysis.
Uses: Open-Meteo, Open Topo Data, ISRIC SoilGrids, Overpass, USGS, Macrostrat.
"""

import math
import logging
from datetime import datetime

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
from src.overpass_client import query_overpass

def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ── Mission types ───────────────────────────────────────────────────────────

MISSION_TYPES = {
    "agriculture": {
        "name": "Agricultural Development",
        "icon": "agriculture",
        "color": "#10b981",
        "desc": "Crop farming, livestock, irrigation planning",
        "factors": ["soil_quality", "water_access", "climate_suitability", "terrain_flatness",
                     "infrastructure", "risk_exposure"],
    },
    "construction": {
        "name": "Construction / Building",
        "icon": "construction",
        "color": "#f59e0b",
        "desc": "Residential, commercial, or industrial construction",
        "factors": ["terrain_stability", "soil_bearing", "flood_risk", "seismic_risk",
                     "infrastructure", "accessibility"],
    },
    "expedition": {
        "name": "Research Expedition",
        "icon": "explore",
        "color": "#3b82f6",
        "desc": "Scientific exploration, field research",
        "factors": ["terrain_difficulty", "weather_conditions", "water_access",
                     "accessibility", "wildlife_density", "risk_exposure"],
    },
    "solar_energy": {
        "name": "Solar Energy Project",
        "icon": "solar_power",
        "color": "#f97316",
        "desc": "Solar farm or off-grid energy installation",
        "factors": ["solar_radiation", "terrain_flatness", "grid_proximity",
                     "land_availability", "climate_suitability", "risk_exposure"],
    },
    "conservation": {
        "name": "Conservation Project",
        "icon": "park",
        "color": "#22c55e",
        "desc": "Habitat restoration, wildlife protection, reforestation",
        "factors": ["biodiversity_potential", "water_system_health", "soil_health",
                     "human_pressure", "protected_status", "climate_suitability"],
    },
    "water_resource": {
        "name": "Water Resource Development",
        "icon": "water",
        "color": "#06b6d4",
        "desc": "Well drilling, water supply, irrigation systems",
        "factors": ["water_access", "groundwater_potential", "terrain_slope",
                     "soil_permeability", "precipitation", "infrastructure"],
    },
}


@st.cache_data(ttl=1800)
def _generate_plan(lat: float, lon: float, mission_type: str) -> dict:
    """Generate mission plan based on location data and mission type."""
    mission = MISSION_TYPES.get(mission_type, MISSION_TYPES["agriculture"])

    # Fetch all relevant data
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365) or {}
    risk = compute_risk_assessment(earthquakes, water, weather, elev)

    # ── Extract metrics ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    valid_tmax = [t for t in temp_max if t is not None]
    valid_tmin = [t for t in temp_min if t is not None]
    avg_high = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 25
    avg_low = sum(valid_tmin) / len(valid_tmin) if valid_tmin else 10

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 0

    # Soil
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _soil_surface(name):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / 10
        return None

    clay = _soil_surface("clay") or 20
    sand = _soil_surface("sand") or 40
    soc = _soil_surface("soc") or 10
    ph = _soil_surface("phh2o") or 7.0

    # Water features
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(w_elements)
    springs = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "spring")
    wells = sum(1 for e in w_elements if e.get("tags", {}).get("man_made") == "water_well")

    # Infrastructure
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))

    # Risk values (flat dict)
    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0
    flood_risk = risk.get("Flood", 0) if isinstance(risk, dict) else 0

    # ── Score factors ──
    factor_scores = {}

    if mission_type == "agriculture":
        factor_scores["soil_quality"] = min(10, (soc / 3) + (7 - abs(ph - 6.5) * 2))
        factor_scores["water_access"] = min(10, water_count / 2 + springs * 2 + wells * 2)
        factor_scores["climate_suitability"] = min(10, 10 - abs(avg_high - 25) / 3)
        factor_scores["terrain_flatness"] = max(0, min(10, 10 - elev_range / 20))
        factor_scores["infrastructure"] = min(10, (roads + buildings) / 5)
        factor_scores["risk_exposure"] = max(0, 10 - (seismic_risk + flood_risk) / 2)

    elif mission_type == "construction":
        factor_scores["terrain_stability"] = max(0, min(10, 10 - elev_range / 30))
        factor_scores["soil_bearing"] = min(10, sand / 8 + (10 - clay / 6))
        factor_scores["flood_risk"] = max(0, 10 - flood_risk)
        factor_scores["seismic_risk"] = max(0, 10 - seismic_risk)
        factor_scores["infrastructure"] = min(10, (roads + buildings) / 3)
        factor_scores["accessibility"] = min(10, roads / 2 + 2)

    elif mission_type == "expedition":
        factor_scores["terrain_difficulty"] = min(10, elev_range / 50 + 2)
        factor_scores["weather_conditions"] = max(0, 10 - abs(avg_high - 22) / 3)
        factor_scores["water_access"] = min(10, water_count / 2 + springs * 3)
        factor_scores["accessibility"] = min(10, roads / 3 + 1)
        factor_scores["wildlife_density"] = 5.0  # Default
        factor_scores["risk_exposure"] = max(0, 10 - (seismic_risk + flood_risk) / 3)

    elif mission_type == "solar_energy":
        factor_scores["solar_radiation"] = min(10, avg_high / 4 + (10 - total_precip / 3))
        factor_scores["terrain_flatness"] = max(0, min(10, 10 - elev_range / 15))
        factor_scores["grid_proximity"] = min(10, buildings / 10 + roads / 5)
        factor_scores["land_availability"] = max(0, 10 - buildings / 10)
        factor_scores["climate_suitability"] = max(0, 10 - total_precip / 5)
        factor_scores["risk_exposure"] = max(0, 10 - (seismic_risk + flood_risk) / 2)

    elif mission_type == "conservation":
        factor_scores["biodiversity_potential"] = min(10, water_count / 2 + 3)
        factor_scores["water_system_health"] = min(10, water_count / 3 + springs * 2)
        factor_scores["soil_health"] = min(10, soc / 2 + 2)
        factor_scores["human_pressure"] = max(0, 10 - buildings / 5)
        factor_scores["protected_status"] = 5.0
        factor_scores["climate_suitability"] = min(10, 10 - abs(avg_high - 22) / 3)

    elif mission_type == "water_resource":
        factor_scores["water_access"] = min(10, water_count / 2 + springs * 3 + wells * 3)
        factor_scores["groundwater_potential"] = min(10, springs * 3 + (clay / 5))
        factor_scores["terrain_slope"] = max(0, min(10, 10 - elev_range / 25))
        factor_scores["soil_permeability"] = min(10, sand / 6)
        factor_scores["precipitation"] = min(10, total_precip / 3)
        factor_scores["infrastructure"] = min(10, roads / 3 + 2)

    # Clamp all scores 0-10
    for k in factor_scores:
        factor_scores[k] = round(max(0, min(10, factor_scores[k])), 1)

    # Overall feasibility
    scores = list(factor_scores.values())
    overall = round(sum(scores) / len(scores), 1) if scores else 0

    # ── Generate recommendations ──
    recommendations = []
    warnings = []
    timeline = []

    if overall >= 7:
        recommendations.append("Location is highly suitable for this mission type.")
    elif overall >= 5:
        recommendations.append("Location is moderately suitable with some challenges to address.")
    else:
        recommendations.append("Location presents significant challenges. Consider alternatives.")

    # Factor-specific recommendations
    for factor, score in factor_scores.items():
        fname = factor.replace("_", " ").title()
        if score < 3:
            warnings.append(f"{fname}: Critical issue (score {score}/10). Requires mitigation.")
        elif score < 5:
            warnings.append(f"{fname}: Below threshold (score {score}/10). Plan accordingly.")
        elif score >= 8:
            recommendations.append(f"{fname}: Excellent conditions (score {score}/10).")

    # Timeline
    if avg_high > 35:
        timeline.append({"phase": "Avoid Peak Summer", "detail": "Temperatures exceed 35C. Plan for spring/autumn."})
    if total_precip > 20:
        timeline.append({"phase": "Rainy Period", "detail": f"Expected {total_precip:.0f}mm precipitation in forecast. Plan indoor/covered activities."})

    timeline.append({"phase": "Site Assessment", "detail": "On-ground survey and data validation. 1-2 weeks."})
    timeline.append({"phase": "Planning & Permits", "detail": "Regulatory compliance and detailed planning. 2-4 weeks."})
    timeline.append({"phase": "Execution", "detail": "Main project execution phase."})
    timeline.append({"phase": "Monitoring", "detail": "Ongoing monitoring and adjustment."})

    return {
        "mission": mission,
        "overall_score": overall,
        "factor_scores": factor_scores,
        "recommendations": recommendations,
        "warnings": warnings,
        "timeline": timeline,
        "metrics": {
            "avg_high": round(avg_high, 1),
            "avg_low": round(avg_low, 1),
            "precipitation": round(total_precip, 1),
            "elevation": round(avg_elev, 0),
            "elev_range": round(elev_range, 0),
            "avg_wind": round(avg_wind, 1),
            "clay": round(clay, 1),
            "sand": round(sand, 1),
            "ph": round(ph, 1),
            "soc": round(soc, 1),
            "water_features": water_count,
            "roads": roads,
            "buildings": buildings,
            "seismic_risk": round(seismic_risk, 1),
            "flood_risk": round(flood_risk, 1),
        },
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_mission_planner_tab():
    """Render the Mission Planner AI tab."""
    st.markdown("## Mission Planner AI")
    st.caption("AI-powered project planning with environmental intelligence")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="mispl_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        lat = st.number_input("Lat", -90.0, 90.0,
                              p.get("lat", 41.90) if p else 41.90,
                              step=0.01, key="mispl_lat", format="%.4f")
    with col3:
        lon = st.number_input("Lon", -180.0, 180.0,
                              p.get("lon", 12.50) if p else 12.50,
                              step=0.01, key="mispl_lon", format="%.4f")

    # Mission type selection
    st.markdown("### Select Mission Type")
    mission_cols = st.columns(3)
    selected_mission = None
    for idx, (m_id, m_info) in enumerate(MISSION_TYPES.items()):
        with mission_cols[idx % 3]:
            if st.button(f"{m_info['name']}", key=f"mp_btn_{m_id}", use_container_width=True):
                st.session_state["mp_selected"] = m_id

    mission_type = st.session_state.get("mp_selected", "agriculture")
    current_mission = MISSION_TYPES[mission_type]
    st.info(f"Selected: **{current_mission['name']}** — {current_mission['desc']}")

    if st.button("Generate Mission Plan", type="primary", use_container_width=True):
        with st.spinner(f"Planning {current_mission['name']} mission..."):
            plan = _generate_plan(lat, lon, mission_type)

        if not plan:
            st.error("Failed to generate plan.")
            return

        # ── Overall feasibility ──
        score = plan["overall_score"]
        if score >= 7:
            color = "#10b981"
            label = "HIGHLY FEASIBLE"
        elif score >= 5:
            color = "#f59e0b"
            label = "MODERATELY FEASIBLE"
        else:
            color = "#ef4444"
            label = "CHALLENGING"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {color}22, {color}44);
                    border-left:5px solid {color}; border-radius:10px;
                    padding:20px; margin:10px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <span style="font-size:14px; color:#888;">MISSION FEASIBILITY</span><br/>
                    <span style="font-size:32px; font-weight:bold; color:{color};">{label}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:48px; font-weight:bold; color:{color};">{score}</span>
                    <span style="font-size:18px; color:#888;">/10</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Factor radar chart ──
        st.markdown("### Factor Analysis")
        factors = plan["factor_scores"]
        f_names = [k.replace("_", " ").title() for k in factors]
        f_values = list(factors.values())

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=f_values + [f_values[0]],
            theta=f_names + [f_names[0]],
            fill="toself",
            fillcolor=_hex_rgba(current_mission['color'], 0.13),
            line=dict(color=current_mission["color"], width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=380,
            margin=dict(t=30, b=30),
        )
        st.plotly_chart(fig, use_container_width=True, key="mispla_pchart1")

        # ── Factor bars ──
        fig2 = go.Figure()
        colors = ["#10b981" if v >= 7 else "#f59e0b" if v >= 4 else "#ef4444" for v in f_values]
        fig2.add_trace(go.Bar(
            x=f_values,
            y=f_names,
            orientation="h",
            marker_color=colors,
            text=[f"{v}" for v in f_values],
            textposition="auto",
        ))
        fig2.update_layout(
            height=max(250, len(f_names) * 40),
            margin=dict(t=10, b=20, l=150),
            xaxis=dict(range=[0, 10], title="Score"),
        )
        st.plotly_chart(fig2, use_container_width=True, key="mispla_pchart2")

        # ── Metrics ──
        st.markdown("### Site Metrics")
        m = plan["metrics"]
        mc = st.columns(5)
        mc[0].metric("Avg High", f"{m['avg_high']}C")
        mc[1].metric("Precipitation", f"{m['precipitation']}mm")
        mc[2].metric("Elevation", f"{m['elevation']:.0f}m")
        mc[3].metric("Elev Range", f"{m['elev_range']:.0f}m")
        mc[4].metric("Avg Wind", f"{m['avg_wind']} km/h")

        mc2 = st.columns(5)
        mc2[0].metric("Clay", f"{m['clay']}%")
        mc2[1].metric("Sand", f"{m['sand']}%")
        mc2[2].metric("pH", f"{m['ph']}")
        mc2[3].metric("Seismic Risk", f"{m['seismic_risk']}/10")
        mc2[4].metric("Flood Risk", f"{m['flood_risk']}/10")

        # ── Recommendations & Warnings ──
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Recommendations")
            for rec in plan["recommendations"]:
                st.markdown(f"""
                <div style="background:#10b98122; border-left:3px solid #10b981;
                            border-radius:6px; padding:8px 12px; margin:4px 0;
                            color:#10b981; font-size:13px;">
                    {rec}
                </div>
                """, unsafe_allow_html=True)

        with col_b:
            st.markdown("### Warnings")
            if plan["warnings"]:
                for warn in plan["warnings"]:
                    st.markdown(f"""
                    <div style="background:#f59e0b22; border-left:3px solid #f59e0b;
                                border-radius:6px; padding:8px 12px; margin:4px 0;
                                color:#f59e0b; font-size:13px;">
                        {warn}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("No significant warnings.")

        # ── Timeline ──
        st.markdown("### Project Timeline")
        for i, phase in enumerate(plan["timeline"]):
            step_color = current_mission["color"]
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; margin:8px 0;">
                <div style="min-width:30px; height:30px; background:{step_color};
                            border-radius:50%; display:flex; align-items:center;
                            justify-content:center; color:white; font-weight:bold;
                            font-size:14px; margin-right:12px;">{i + 1}</div>
                <div>
                    <div style="color:#eee; font-weight:bold;">{phase['phase']}</div>
                    <div style="color:#aaa; font-size:13px;">{phase['detail']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
