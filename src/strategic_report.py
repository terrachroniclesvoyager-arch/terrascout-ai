"""
Strategic Assessment Report AI — Generates comprehensive intelligence-grade
strategic assessments combining ALL data domains into a unified briefing.
Outputs a structured multi-section report with risk matrix, opportunity
analysis, and strategic recommendations.
Uses: All available data sources from deep_zone_analysis.
"""

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
    fetch_protected_areas,
    fetch_earthquakes,
    fetch_geology,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_risk_assessment,
    compute_species_breakdown,
    compute_landuse_breakdown,
    parse_geology_data,
)

logger = logging.getLogger(__name__)


@st.cache_data(ttl=1800)
def _generate_assessment(lat: float, lon: float) -> dict:
    """Generate comprehensive strategic assessment."""
    # Fetch ALL data sources
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=7) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    protected = fetch_protected_areas(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=150, days=365) or {}
    geology_raw = fetch_geology(lat, lon) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}

    # Compute derived data
    risk = compute_risk_assessment(earthquakes, water, weather, elev)
    species = compute_species_breakdown(inat, gbif)
    landuse = compute_landuse_breakdown(infra)
    geology = parse_geology_data(geology_raw)

    # ── Extract metrics ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    valid_tmax = [t for t in temp_max if t is not None]
    valid_tmin = [t for t in temp_min if t is not None]
    avg_high = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20
    avg_low = sum(valid_tmin) / len(valid_tmin) if valid_tmin else 10
    current_temp = current.get("temperature_2m", avg_high)
    humidity = current.get("relative_humidity_2m", 50) or 50

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    peak_wind = max(valid_wind) if valid_wind else 0
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 0

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 0
    min_elev = min(valid_elevs) if valid_elevs else 0
    max_elev = max(valid_elevs) if valid_elevs else 0

    # Soil
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, divisor=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / divisor
        return None

    clay = _sv("clay") or 20
    sand = _sv("sand") or 40
    silt = _sv("silt") or 40
    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0
    nitrogen = _sv("nitrogen", 100) or 1.0

    # Water
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    springs = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "spring")
    wells = sum(1 for e in w_elements if e.get("tags", {}).get("man_made") == "water_well")
    rivers = sum(1 for e in w_elements if e.get("tags", {}).get("waterway") in ("river", "canal"))
    streams = sum(1 for e in w_elements if e.get("tags", {}).get("waterway") in ("stream", "ditch"))

    # Infrastructure
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))

    # Protected areas
    p_elements = protected.get("elements", []) if isinstance(protected, dict) else []
    protected_count = len(p_elements)

    # Risk (flat dict)
    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0
    flood_risk = risk.get("Flood", 0) if isinstance(risk, dict) else 0
    fire_risk = risk.get("Fire", 0) if isinstance(risk, dict) else 0
    landslide_risk = risk.get("Landslide", 0) if isinstance(risk, dict) else 0

    # Biodiversity
    total_species = species.get("gbif_unique_species", 0) + len(species.get("top_species", []))
    total_obs = species.get("inat_total", 0) + species.get("gbif_total", 0)
    kingdoms = species.get("kingdom_counts", {})

    # ── Build report sections ──
    sections = {}

    # SECTION 1: Location Profile
    sections["profile"] = {
        "coordinates": f"{lat:.4f}N, {lon:.4f}E",
        "elevation": f"{avg_elev:.0f}m (range: {min_elev:.0f}-{max_elev:.0f}m)",
        "terrain_type": _classify_terrain(avg_elev, max_elev - min_elev),
        "climate_zone": _classify_climate(avg_high, avg_low, total_precip),
        "urbanization": _classify_urban(buildings, roads),
    }

    # SECTION 2: Environmental Conditions
    sections["environment"] = {
        "temperature": {
            "current": round(current_temp, 1),
            "avg_high": round(avg_high, 1),
            "avg_low": round(avg_low, 1),
            "humidity": round(humidity),
        },
        "precipitation": {
            "forecast_total": round(total_precip, 1),
            "wind_peak": round(peak_wind, 1),
            "wind_avg": round(avg_wind, 1),
        },
        "soil": {
            "clay": round(clay, 1),
            "sand": round(sand, 1),
            "silt": round(silt, 1),
            "soc": round(soc, 1),
            "ph": round(ph, 1),
            "nitrogen": round(nitrogen, 2),
            "classification": _classify_soil(clay, sand, silt),
        },
        "water": {
            "springs": springs,
            "wells": wells,
            "rivers": rivers,
            "streams": streams,
            "total": len(w_elements),
        },
    }

    # SECTION 3: Risk Matrix
    risk_scores = {
        "Seismic": round(seismic_risk, 1),
        "Flood": round(flood_risk, 1),
        "Wildfire": round(fire_risk, 1),
        "Landslide": round(landslide_risk, 1),
    }
    overall_risk = sum(risk_scores.values()) / max(len(risk_scores), 1)
    sections["risk"] = {
        "scores": risk_scores,
        "overall": round(overall_risk, 1),
        "earthquakes_1yr": len(earthquakes.get("features", [])),
        "classification": _classify_risk(overall_risk),
    }

    # SECTION 4: Biodiversity & Ecology
    sections["ecology"] = {
        "total_species": total_species,
        "total_observations": total_obs,
        "kingdoms": kingdoms,
        "protected_areas": protected_count,
        "biodiversity_class": _classify_biodiversity(total_species, total_obs),
    }

    # SECTION 5: Geology
    sections["geology"] = geology[:5] if geology else []

    # SECTION 6: Land Use
    sections["landuse"] = landuse

    # SECTION 7: Opportunities
    opportunities = []
    if total_precip < 3 and avg_high > 25 and avg_wind < 15:
        opportunities.append({
            "type": "Solar Energy",
            "score": 8,
            "detail": "High solar potential: clear skies, warm temps, low wind.",
        })
    if 5.5 <= ph <= 7.5 and soc > 10 and clay <= 40:
        opportunities.append({
            "type": "Agriculture",
            "score": 7 + min(2, soc / 15),
            "detail": f"Good soil conditions: pH {ph:.1f}, SOC {soc:.1f}g/kg, {_classify_soil(clay, sand, silt)}.",
        })
    if total_species > 20 and protected_count > 0:
        opportunities.append({
            "type": "Ecotourism",
            "score": 7,
            "detail": f"Rich biodiversity ({total_species} species) with {protected_count} protected areas.",
        })
    if springs > 0 or wells > 0:
        opportunities.append({
            "type": "Water Resource",
            "score": 6 + springs + wells,
            "detail": f"{springs} springs, {wells} wells. Active groundwater resources.",
        })
    if buildings < 5 and roads < 3 and max_elev - min_elev > 100:
        opportunities.append({
            "type": "Wilderness Research",
            "score": 8,
            "detail": "Remote, undeveloped terrain ideal for scientific field research.",
        })
    if avg_wind > 20:
        opportunities.append({
            "type": "Wind Energy",
            "score": min(9, 5 + avg_wind / 8),
            "detail": f"Average peak wind {avg_wind:.1f} km/h. Viable wind energy site.",
        })

    for opp in opportunities:
        opp["score"] = round(min(10, opp["score"]), 1)
    opportunities.sort(key=lambda o: o["score"], reverse=True)
    sections["opportunities"] = opportunities

    # SECTION 8: Strategic Recommendations
    recommendations = []
    if overall_risk > 5:
        recommendations.append({
            "priority": "HIGH",
            "area": "Risk Mitigation",
            "action": f"Overall risk {overall_risk:.1f}/10. Implement monitoring for "
                      f"{max(risk_scores, key=risk_scores.get)} (highest: {max(risk_scores.values())}/10).",
        })
    if flood_risk > 5 and buildings > 20:
        recommendations.append({
            "priority": "HIGH",
            "area": "Flood Protection",
            "action": "Dense urbanization in flood zone. Assess drainage infrastructure and emergency plans.",
        })
    if soc < 5:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Soil Restoration",
            "action": f"Low organic carbon ({soc:.1f} g/kg). Consider organic amendments or reforestation.",
        })
    if total_species < 5 and protected_count == 0:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Conservation",
            "action": "Low biodiversity detected. Assess habitat degradation causes.",
        })
    if len(w_elements) < 3 and total_precip < 5:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Water Security",
            "action": "Limited water resources in dry conditions. Plan water storage/conservation.",
        })

    sections["recommendations"] = recommendations

    return sections


def _classify_terrain(elev, elev_range):
    if elev > 2500:
        return "Alpine"
    if elev > 1000:
        return "Highland" if elev_range > 200 else "Plateau"
    if elev_range > 300:
        return "Mountainous"
    if elev_range > 100:
        return "Hilly"
    if elev < 10:
        return "Coastal/Low-lying"
    return "Lowland"


def _classify_climate(avg_high, avg_low, precip):
    if avg_high > 35:
        return "Hot Arid" if precip < 5 else "Hot Humid"
    if avg_high > 25:
        return "Subtropical" if precip > 10 else "Mediterranean"
    if avg_high > 15:
        return "Temperate"
    if avg_high > 5:
        return "Cool Temperate"
    return "Cold/Polar"


def _classify_urban(buildings, roads):
    if buildings > 100:
        return "Dense Urban"
    if buildings > 30:
        return "Suburban"
    if buildings > 5:
        return "Rural Settlement"
    return "Undeveloped"


def _classify_soil(clay, sand, silt):
    if clay > 40:
        return "Clay"
    if sand > 60:
        return "Sandy"
    if silt > 50:
        return "Silty"
    if 20 <= clay <= 35 and 30 <= sand <= 50:
        return "Loam"
    return "Mixed"


def _classify_risk(score):
    if score >= 7:
        return "CRITICAL"
    if score >= 5:
        return "HIGH"
    if score >= 3:
        return "MODERATE"
    return "LOW"


def _classify_biodiversity(species, observations):
    if species > 50:
        return "Very High"
    if species > 20:
        return "High"
    if species > 5:
        return "Moderate"
    return "Low"


# ── Rendering ───────────────────────────────────────────────────────────────

def render_strategic_report_tab():
    """Render the Strategic Assessment Report AI tab."""
    st.markdown("## Strategic Assessment Report AI")
    st.caption("Intelligence-grade comprehensive location assessment")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="sr_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="sr_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="sr_lon", format="%.4f")

    if st.button("Generate Strategic Assessment", type="primary", use_container_width=True):
        with st.spinner("Compiling intelligence from 10+ data sources..."):
            report = _generate_assessment(lat, lon)

        if not report:
            st.error("Failed to generate assessment.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        # ── Report Header ──
        profile = report["profile"]
        risk_data = report["risk"]
        risk_class = risk_data["classification"]
        risk_colors = {"CRITICAL": "#ef4444", "HIGH": "#f59e0b", "MODERATE": "#3b82f6", "LOW": "#10b981"}
        rc = risk_colors.get(risk_class, "#888")

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #1a1a2e, #16213e);
                    border:1px solid #333; border-radius:12px; padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="color:#888; font-size:11px;">STRATEGIC ASSESSMENT</div>
                    <div style="color:#eee; font-size:22px; font-weight:bold; margin:4px 0;">
                        {profile['coordinates']}
                    </div>
                    <div style="color:#aaa; font-size:13px;">
                        {profile['terrain_type']} | {profile['climate_zone']} | {profile['urbanization']}
                    </div>
                    <div style="color:#666; font-size:11px; margin-top:4px;">
                        Generated: {timestamp}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:11px;">RISK LEVEL</div>
                    <div style="color:{rc}; font-size:28px; font-weight:bold;">{risk_class}</div>
                    <div style="color:#888; font-size:13px;">{risk_data['overall']}/10</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Section 1: Location Profile ──
        st.markdown("### 1. Location Profile")
        pc = st.columns(4)
        pc[0].metric("Elevation", profile["elevation"].split("(")[0])
        pc[1].metric("Terrain", profile["terrain_type"])
        pc[2].metric("Climate", profile["climate_zone"])
        pc[3].metric("Urbanization", profile["urbanization"])

        # ── Section 2: Environmental Conditions ──
        st.markdown("### 2. Environmental Conditions")
        env = report["environment"]

        tab_w, tab_s, tab_h = st.tabs(["Weather", "Soil", "Water"])

        with tab_w:
            wc = st.columns(4)
            wc[0].metric("Current Temp", f"{env['temperature']['current']}C")
            wc[1].metric("Avg High", f"{env['temperature']['avg_high']}C")
            wc[2].metric("Humidity", f"{env['temperature']['humidity']}%")
            wc[3].metric("Peak Wind", f"{env['precipitation']['wind_peak']} km/h")

        with tab_s:
            soil = env["soil"]
            sc = st.columns(4)
            sc[0].metric("Classification", soil["classification"])
            sc[1].metric("Clay/Sand/Silt", f"{soil['clay']}/{soil['sand']}/{soil['silt']}%")
            sc[2].metric("pH", soil["ph"])
            sc[3].metric("SOC", f"{soil['soc']} g/kg")

        with tab_h:
            w = env["water"]
            hc = st.columns(5)
            hc[0].metric("Total Features", w["total"])
            hc[1].metric("Rivers", w["rivers"])
            hc[2].metric("Streams", w["streams"])
            hc[3].metric("Springs", w["springs"])
            hc[4].metric("Wells", w["wells"])

        # ── Section 3: Risk Matrix ──
        st.markdown("### 3. Risk Matrix")
        risk_scores = risk_data["scores"]

        fig = go.Figure()
        r_names = list(risk_scores.keys())
        r_values = list(risk_scores.values())
        r_colors = ["#10b981" if v < 3 else "#f59e0b" if v < 6 else "#ef4444" for v in r_values]

        fig.add_trace(go.Bar(
            x=r_values,
            y=r_names,
            orientation="h",
            marker_color=r_colors,
            text=[f"{v}/10" for v in r_values],
            textposition="auto",
        ))
        fig.update_layout(
            height=200,
            margin=dict(t=10, b=20, l=100),
            xaxis=dict(range=[0, 10], title="Risk Score"),
        )
        st.plotly_chart(fig, use_container_width=True, key="strrep_pchart1")

        rc2 = st.columns(3)
        rc2[0].metric("Overall Risk", f"{risk_data['overall']}/10")
        rc2[1].metric("Earthquakes (1yr)", risk_data["earthquakes_1yr"])
        rc2[2].metric("Risk Class", risk_data["classification"])

        # ── Section 4: Ecology ──
        st.markdown("### 4. Biodiversity & Ecology")
        eco = report["ecology"]
        ec = st.columns(4)
        ec[0].metric("Species Detected", eco["total_species"])
        ec[1].metric("Observations", eco["total_observations"])
        ec[2].metric("Protected Areas", eco["protected_areas"])
        ec[3].metric("Bio Class", eco["biodiversity_class"])

        if eco["kingdoms"]:
            fig2 = go.Figure(data=[go.Pie(
                labels=list(eco["kingdoms"].keys()),
                values=list(eco["kingdoms"].values()),
                hole=0.4,
            )])
            fig2.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True, key="strrep_pchart2")

        # ── Section 5: Geology ──
        if report["geology"]:
            st.markdown("### 5. Geological Context")
            for g in report["geology"]:
                name = g.get("name", "Unknown") if isinstance(g, dict) else str(g)
                lith = g.get("lith", "") if isinstance(g, dict) else ""
                age = g.get("age", "") if isinstance(g, dict) else ""
                st.markdown(f"- **{name}** — {lith} ({age})")

        # ── Section 6: Opportunities ──
        opps = report.get("opportunities", [])
        if opps:
            st.markdown("### 6. Opportunities")
            for opp in opps:
                score = opp["score"]
                if score >= 7:
                    oc = "#10b981"
                elif score >= 5:
                    oc = "#f59e0b"
                else:
                    oc = "#888"

                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:4px solid {oc};
                            border-radius:8px; padding:10px 14px; margin:6px 0;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#eee; font-weight:bold;">{opp['type']}</span>
                        <span style="color:{oc}; font-weight:bold;">{score}/10</span>
                    </div>
                    <div style="color:#aaa; font-size:13px; margin-top:4px;">{opp['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Section 7: Strategic Recommendations ──
        recs = report.get("recommendations", [])
        if recs:
            st.markdown("### 7. Strategic Recommendations")
            for rec in recs:
                pri = rec["priority"]
                if pri == "HIGH":
                    pc_color = "#ef4444"
                elif pri == "MEDIUM":
                    pc_color = "#f59e0b"
                else:
                    pc_color = "#3b82f6"

                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:4px solid {pc_color};
                            border-radius:8px; padding:10px 14px; margin:6px 0;">
                    <span style="color:{pc_color}; font-weight:bold;">[{pri}]</span>
                    <span style="color:#ddd; font-weight:bold; margin-left:6px;">{rec['area']}</span>
                    <div style="color:#aaa; font-size:13px; margin-top:4px;">{rec['action']}</div>
                </div>
                """, unsafe_allow_html=True)
