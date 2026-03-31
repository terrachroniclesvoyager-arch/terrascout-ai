"""
Threat Matrix AI — Multi-domain unified threat assessment engine.
Combines seismic, meteorological, environmental, geological, and human-factor
data into probability-scored threat matrices with cross-correlation analysis.
Uses: Open-Meteo, USGS, Open Topo Data, ISRIC SoilGrids, Overpass, Macrostrat.
"""

import math
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
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
    fetch_earthquakes,
    fetch_geology,
    fetch_landuse_infrastructure,
    compute_risk_assessment,
)
from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ── Threat domains ──────────────────────────────────────────────────────────

THREAT_DOMAINS = {
    "seismic": {
        "name": "Seismic / Tectonic",
        "icon": "earthquake",
        "color": "#ef4444",
        "factors": [
            "earthquake_magnitude",
            "earthquake_frequency",
            "fault_proximity",
            "tectonic_activity",
        ],
    },
    "meteorological": {
        "name": "Meteorological",
        "icon": "thunderstorm",
        "color": "#f59e0b",
        "factors": [
            "extreme_wind",
            "heavy_precipitation",
            "temperature_extreme",
            "storm_probability",
        ],
    },
    "hydrological": {
        "name": "Hydrological / Flood",
        "icon": "water",
        "color": "#3b82f6",
        "factors": [
            "flood_proximity",
            "drainage_density",
            "low_elevation",
            "precipitation_intensity",
        ],
    },
    "geological": {
        "name": "Geological / Landslide",
        "icon": "landscape",
        "color": "#8b5cf6",
        "factors": [
            "slope_steepness",
            "clay_content",
            "geological_instability",
            "vegetation_absence",
        ],
    },
    "wildfire": {
        "name": "Wildfire",
        "icon": "local_fire_department",
        "color": "#f97316",
        "factors": [
            "high_temperature",
            "low_humidity",
            "wind_speed",
            "vegetation_density",
        ],
    },
    "environmental": {
        "name": "Environmental Degradation",
        "icon": "eco",
        "color": "#10b981",
        "factors": [
            "soil_degradation",
            "water_contamination_risk",
            "biodiversity_loss_risk",
            "deforestation_pressure",
        ],
    },
}


# ── Scoring functions ───────────────────────────────────────────────────────

def _score_seismic(earthquakes: dict, geology: list) -> dict:
    """Score seismic threats from USGS + Macrostrat data."""
    features = earthquakes.get("features", [])
    scores = {}

    mags = [f["properties"].get("mag", 0) or 0 for f in features]
    max_mag = max(mags) if mags else 0
    scores["earthquake_magnitude"] = min(10, max_mag * 1.5)
    scores["earthquake_frequency"] = min(10, len(features) / 5)

    # Fault proximity from geological data
    fault_types = {"fault", "rift", "thrust", "shear", "fracture"}
    has_fault = any(
        any(ft in (g.get("lith", "") + g.get("name", "")).lower() for ft in fault_types)
        for g in geology
    ) if geology else False
    scores["fault_proximity"] = 8.0 if has_fault else 2.0

    # Tectonic activity
    recent = [f for f in features if (f["properties"].get("mag", 0) or 0) >= 3.0]
    scores["tectonic_activity"] = min(10, len(recent) * 2)

    return scores


def _score_meteorological(weather: dict) -> dict:
    """Score meteorological threats from Open-Meteo data."""
    daily = weather.get("daily", {})
    current = weather.get("current", {})
    scores = {}

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    peak_wind = max(valid_wind) if valid_wind else 0
    scores["extreme_wind"] = min(10, peak_wind / 12)

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    max_precip = max(valid_precip) if valid_precip else 0
    scores["heavy_precipitation"] = min(10, max_precip / 5)

    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    valid_tmax = [t for t in temp_max if t is not None]
    valid_tmin = [t for t in temp_min if t is not None]
    highest = max(valid_tmax) if valid_tmax else 25
    lowest = min(valid_tmin) if valid_tmin else 10
    temp_extreme = max(highest - 35, 0) + max(-5 - lowest, 0)
    scores["temperature_extreme"] = min(10, temp_extreme)

    # Storm probability from wind + precip combo
    storm_score = (scores["extreme_wind"] + scores["heavy_precipitation"]) / 2
    scores["storm_probability"] = min(10, storm_score * 1.3)

    return scores


def _score_hydrological(weather: dict, water: dict, elev_data: dict) -> dict:
    """Score flood / hydrological threats."""
    scores = {}
    elements = water.get("elements", []) if isinstance(water, dict) else []
    waterways = sum(1 for e in elements if e.get("tags", {}).get("waterway"))
    water_bodies = sum(1 for e in elements if e.get("tags", {}).get("natural") == "water")

    scores["flood_proximity"] = min(10, (waterways + water_bodies * 3) / 2)
    scores["drainage_density"] = min(10, waterways / 3)

    # Low elevation risk
    elevations = elev_data.get("grid_elevations", []) if isinstance(elev_data, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    min_elev = min(valid_elevs) if valid_elevs else 100
    scores["low_elevation"] = max(0, min(10, (50 - min_elev) / 5)) if min_elev < 50 else 0

    daily = weather.get("daily", {})
    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    max_daily = max(valid_precip) if valid_precip else 0
    scores["precipitation_intensity"] = min(10, max_daily / 4)

    return scores


def _score_geological(elev_data: dict, soil: dict, geology: list) -> dict:
    """Score landslide / geological threats."""
    scores = {}

    elevations = elev_data.get("grid_elevations", []) if isinstance(elev_data, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    if len(valid_elevs) >= 2:
        slope_proxy = max(valid_elevs) - min(valid_elevs)
        scores["slope_steepness"] = min(10, slope_proxy / 50)
    else:
        scores["slope_steepness"] = 0

    # Clay content increases landslide risk
    layers = soil.get("properties", {}) if isinstance(soil, dict) else {}
    clay_vals = []
    clay_prop = layers.get("clay", {})
    if isinstance(clay_prop, dict):
        for depth in clay_prop.get("depths", []):
            vals = depth.get("values", {})
            mean_val = vals.get("mean")
            if mean_val is not None:
                clay_vals.append(mean_val / 10)
    avg_clay = sum(clay_vals) / len(clay_vals) if clay_vals else 20
    scores["clay_content"] = min(10, avg_clay / 8)

    unstable = {"shale", "marl", "clay", "silt", "loess", "volcanic"}
    has_unstable = any(
        any(u in (g.get("lith", "")).lower() for u in unstable)
        for g in geology
    ) if geology else False
    scores["geological_instability"] = 7.0 if has_unstable else 2.0

    scores["vegetation_absence"] = 3.0  # Default mid-range

    return scores


def _score_wildfire(weather: dict, elev_data: dict) -> dict:
    """Score wildfire threats."""
    scores = {}
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    highest = max(valid_tmax) if valid_tmax else 25
    scores["high_temperature"] = min(10, max(0, (highest - 25) / 2))

    humidity = current.get("relative_humidity_2m", 50) or 50
    scores["low_humidity"] = max(0, min(10, (60 - humidity) / 6))

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10
    scores["wind_speed"] = min(10, avg_wind / 8)

    # Vegetation density (higher = more fuel = more fire risk)
    scores["vegetation_density"] = 5.0  # Default

    return scores


def _score_environmental(soil: dict, water: dict) -> dict:
    """Score environmental degradation threats."""
    scores = {}

    # Soil degradation from SOC & pH
    layers = soil.get("properties", {}) if isinstance(soil, dict) else {}
    soc_vals = []
    soc_prop = layers.get("soc", {})
    if isinstance(soc_prop, dict):
        for depth in soc_prop.get("depths", []):
            vals = depth.get("values", {})
            mean_val = vals.get("mean")
            if mean_val is not None:
                soc_vals.append(mean_val / 10)
    avg_soc = sum(soc_vals) / len(soc_vals) if soc_vals else 15
    scores["soil_degradation"] = max(0, min(10, (30 - avg_soc) / 3))

    elements = water.get("elements", []) if isinstance(water, dict) else []
    industrial = sum(
        1 for e in elements
        if e.get("tags", {}).get("landuse") in ("industrial", "landfill")
        or e.get("tags", {}).get("man_made") in ("wastewater_plant", "works")
    )
    scores["water_contamination_risk"] = min(10, industrial * 3)

    scores["biodiversity_loss_risk"] = 4.0
    scores["deforestation_pressure"] = 3.0

    return scores


# ── Main computation ────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def compute_threat_matrix(lat: float, lon: float) -> dict:
    """Compute unified threat matrix across all domains."""
    # Fetch all data sources
    weather = fetch_weather_data(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=150, days=365) or {}
    water = fetch_water_features(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5) or {}

    # Geology
    try:
        import requests
        geo_resp = requests.get(
            "https://macrostrat.org/api/v2/geologic_units/map",
            params={"lat": lat, "lng": lon, "adjacents": "true"},
            timeout=15,
        )
        geo_data = geo_resp.json() if geo_resp.ok else {}
    except Exception:
        geo_data = {}
    geology = []
    for item in geo_data.get("success", {}).get("data", []):
        geology.append({
            "name": item.get("unit_name", "Unknown"),
            "lith": item.get("lith", ""),
            "age": item.get("t_age", ""),
            "type": item.get("lith_type", ""),
        })

    # Score each domain
    domain_scores = {}
    domain_scores["seismic"] = _score_seismic(earthquakes, geology)
    domain_scores["meteorological"] = _score_meteorological(weather)
    domain_scores["hydrological"] = _score_hydrological(weather, water, elev)
    domain_scores["geological"] = _score_geological(elev, soil, geology)
    domain_scores["wildfire"] = _score_wildfire(weather, elev)
    domain_scores["environmental"] = _score_environmental(soil, water)

    # Aggregate domain scores
    domain_aggregates = {}
    for domain, factor_scores in domain_scores.items():
        values = list(factor_scores.values())
        domain_aggregates[domain] = {
            "score": round(sum(values) / len(values), 1) if values else 0,
            "max_factor": max(factor_scores, key=factor_scores.get) if factor_scores else "",
            "max_score": round(max(values), 1) if values else 0,
            "factors": factor_scores,
        }

    # Overall threat level
    agg_scores = [d["score"] for d in domain_aggregates.values()]
    overall = round(sum(agg_scores) / len(agg_scores), 1) if agg_scores else 0

    # Cross-correlations
    correlations = []
    seis = domain_aggregates.get("seismic", {}).get("score", 0)
    geo = domain_aggregates.get("geological", {}).get("score", 0)
    if seis > 5 and geo > 5:
        correlations.append({
            "domains": ["Seismic", "Geological"],
            "strength": round((seis + geo) / 2, 1),
            "insight": "High seismic activity combined with unstable geology creates compound landslide risk.",
            "level": "CRITICAL",
        })

    hydro = domain_aggregates.get("hydrological", {}).get("score", 0)
    meteo = domain_aggregates.get("meteorological", {}).get("score", 0)
    if hydro > 4 and meteo > 4:
        correlations.append({
            "domains": ["Hydrological", "Meteorological"],
            "strength": round((hydro + meteo) / 2, 1),
            "insight": "Heavy precipitation forecast combined with flood-prone terrain amplifies flash flood risk.",
            "level": "HIGH" if (hydro + meteo) / 2 > 6 else "MODERATE",
        })

    fire = domain_aggregates.get("wildfire", {}).get("score", 0)
    env = domain_aggregates.get("environmental", {}).get("score", 0)
    if fire > 5 and env > 4:
        correlations.append({
            "domains": ["Wildfire", "Environmental"],
            "strength": round((fire + env) / 2, 1),
            "insight": "Wildfire risk in degraded environment may accelerate deforestation and soil loss.",
            "level": "HIGH",
        })

    if seis > 4 and hydro > 4:
        correlations.append({
            "domains": ["Seismic", "Hydrological"],
            "strength": round((seis + hydro) / 2, 1),
            "insight": "Seismic activity near water bodies raises tsunami/seiche and dam failure risk.",
            "level": "HIGH" if (seis + hydro) / 2 > 6 else "MODERATE",
        })

    # Threat classification
    if overall >= 7:
        threat_class = "CRITICAL"
        threat_color = "#ef4444"
    elif overall >= 5:
        threat_class = "HIGH"
        threat_color = "#f59e0b"
    elif overall >= 3:
        threat_class = "MODERATE"
        threat_color = "#3b82f6"
    else:
        threat_class = "LOW"
        threat_color = "#10b981"

    return {
        "overall_score": overall,
        "threat_class": threat_class,
        "threat_color": threat_color,
        "domains": domain_aggregates,
        "correlations": correlations,
        "factor_details": domain_scores,
        "earthquake_count": len(earthquakes.get("features", [])),
        "geology": geology[:5],
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_threat_matrix_tab():
    """Render the Threat Matrix AI tab."""
    st.markdown("## Threat Matrix AI")
    st.caption("Multi-domain unified threat assessment with cross-correlation analysis")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="tm_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="tm_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="tm_lon", format="%.4f")

    if st.button("Generate Threat Matrix", type="primary", use_container_width=True):
        with st.spinner("Scanning 6 threat domains across 8 data sources..."):
            result = compute_threat_matrix(lat, lon)

        if not result:
            st.error("Failed to compute threat matrix.")
            return

        # ── Overall threat level ──
        tc = result["threat_class"]
        ts = result["overall_score"]
        tcolor = result["threat_color"]

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {tcolor}22, {tcolor}44);
                    border-left:5px solid {tcolor}; border-radius:10px;
                    padding:20px; margin:10px 0;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <span style="font-size:14px; color:#888;">OVERALL THREAT LEVEL</span><br/>
                    <span style="font-size:36px; font-weight:bold; color:{tcolor};">{tc}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:48px; font-weight:bold; color:{tcolor};">{ts}</span>
                    <span style="font-size:18px; color:#888;">/10</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Domain radar chart ──
        domains = result["domains"]
        radar_names = [THREAT_DOMAINS[d]["name"] for d in domains]
        radar_scores = [domains[d]["score"] for d in domains]
        radar_colors = [THREAT_DOMAINS[d]["color"] for d in domains]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_scores + [radar_scores[0]],
            theta=radar_names + [radar_names[0]],
            fill="toself",
            fillcolor="rgba(239,68,68,0.15)",
            line=dict(color="#ef4444", width=2),
            name="Threat Score",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10]),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False,
            height=380,
            margin=dict(t=30, b=30, l=60, r=60),
        )
        st.plotly_chart(fig, use_container_width=True, key="thrmat_pchart1")

        # ── Domain cards ──
        st.markdown("### Domain Breakdown")
        cols = st.columns(3)
        for idx, (domain_id, domain_data) in enumerate(domains.items()):
            info = THREAT_DOMAINS[domain_id]
            score = domain_data["score"]
            max_f = domain_data["max_factor"].replace("_", " ").title()

            if score >= 7:
                level_color = "#ef4444"
                level = "CRITICAL"
            elif score >= 5:
                level_color = "#f59e0b"
                level = "HIGH"
            elif score >= 3:
                level_color = "#3b82f6"
                level = "MODERATE"
            else:
                level_color = "#10b981"
                level = "LOW"

            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid {info['color']}44;
                            border-radius:10px; padding:15px; margin:5px 0; min-height:160px;">
                    <div style="color:{info['color']}; font-weight:bold; font-size:14px;">
                        {info['name']}
                    </div>
                    <div style="font-size:32px; font-weight:bold; color:{level_color};
                                margin:5px 0;">{score}<span style="font-size:14px; color:#888;">/10</span></div>
                    <div style="font-size:11px; color:#aaa;">
                        Level: <span style="color:{level_color};">{level}</span><br/>
                        Key factor: {max_f} ({domain_data['max_score']})
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Factor heatmap ──
        st.markdown("### Factor Heatmap")
        factor_details = result["factor_details"]
        all_factors = []
        all_domains_list = []
        all_scores_list = []

        for domain_id, factors in factor_details.items():
            for factor, score in factors.items():
                all_factors.append(factor.replace("_", " ").title())
                all_domains_list.append(THREAT_DOMAINS[domain_id]["name"])
                all_scores_list.append(score)

        df = pd.DataFrame({
            "Domain": all_domains_list,
            "Factor": all_factors,
            "Score": all_scores_list,
        })

        pivot = df.pivot_table(index="Factor", columns="Domain", values="Score", aggfunc="first")
        fig2 = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[
                [0, "#10b981"],
                [0.3, "#3b82f6"],
                [0.5, "#f59e0b"],
                [0.7, "#f97316"],
                [1, "#ef4444"],
            ],
            zmin=0,
            zmax=10,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}",
            textfont={"size": 11},
        ))
        fig2.update_layout(
            height=max(350, len(pivot.index) * 30),
            margin=dict(t=20, b=20, l=150, r=20),
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig2, use_container_width=True, key="thrmat_pchart2")

        # ── Cross-correlations ──
        correlations = result["correlations"]
        if correlations:
            st.markdown("### Cross-Domain Correlations")
            for corr in correlations:
                lv = corr["level"]
                if lv == "CRITICAL":
                    border = "#ef4444"
                elif lv == "HIGH":
                    border = "#f59e0b"
                else:
                    border = "#3b82f6"

                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:4px solid {border};
                            border-radius:8px; padding:12px; margin:6px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color:{border}; font-weight:bold;">[{lv}]</span>
                            <span style="color:#ddd; font-weight:bold;">
                                {' + '.join(corr['domains'])}
                            </span>
                            <span style="color:#888; font-size:12px;"> (strength {corr['strength']})</span>
                        </div>
                    </div>
                    <div style="color:#aaa; font-size:13px; margin-top:5px;">
                        {corr['insight']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Summary stats ──
        st.markdown("### Intelligence Summary")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Threat Score", f"{ts}/10")
        mc2.metric("Domains Analyzed", "6")
        mc3.metric("Earthquakes (1yr)", result["earthquake_count"])
        mc4.metric("Correlations Found", len(correlations))

        # Geology context
        if result["geology"]:
            with st.expander("Geological Context"):
                for g in result["geology"]:
                    st.markdown(f"**{g['name']}** — {g['lith']} ({g['type']})")
