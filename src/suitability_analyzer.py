"""
Land Suitability Analyzer for TerraScout AI.
Purpose-specific analysis: evaluate land for farming, solar energy, wind energy,
housing development, conservation, or tourism development.
Uses multi-criteria decision analysis with weighted scoring.
"""

import logging
import math
import pandas as pd
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
    fetch_protected_areas,
    compute_risk_assessment,
    compute_species_breakdown,
    compute_landuse_breakdown,
    fetch_gbif_occurrences,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SUITABILITY PROFILES
# ═══════════════════════════════════════════════════════════════

SUITABILITY_PROFILES = {
    "agriculture": {
        "name": "Agriculture / Farming",
        "icon": "🌾",
        "color": "#10b981",
        "criteria": {
            "Soil Quality": {"weight": 0.30, "desc": "Organic carbon, pH, nitrogen content"},
            "Water Access": {"weight": 0.20, "desc": "Springs, wells, waterways nearby"},
            "Climate": {"weight": 0.20, "desc": "Temperature, rainfall for crops"},
            "Terrain": {"weight": 0.15, "desc": "Flat land preferred, low slope"},
            "Risk": {"weight": 0.15, "desc": "Low flood, fire, landslide risk"},
        },
    },
    "solar": {
        "name": "Solar Energy",
        "icon": "☀️",
        "color": "#f59e0b",
        "criteria": {
            "Solar Exposure": {"weight": 0.35, "desc": "Low cloud cover, high temperature"},
            "Terrain": {"weight": 0.20, "desc": "Flat land, south-facing preferred"},
            "Infrastructure": {"weight": 0.20, "desc": "Road access, grid proximity"},
            "Land Availability": {"weight": 0.15, "desc": "Open land, low building density"},
            "Risk": {"weight": 0.10, "desc": "Low extreme weather risk"},
        },
    },
    "wind": {
        "name": "Wind Energy",
        "icon": "💨",
        "color": "#06b6d4",
        "criteria": {
            "Wind Resource": {"weight": 0.40, "desc": "Average wind speed, consistency"},
            "Terrain": {"weight": 0.20, "desc": "Elevated, exposed positions ideal"},
            "Infrastructure": {"weight": 0.15, "desc": "Road access for construction"},
            "Environmental": {"weight": 0.15, "desc": "Low biodiversity impact"},
            "Risk": {"weight": 0.10, "desc": "Low seismic, extreme weather risk"},
        },
    },
    "housing": {
        "name": "Housing Development",
        "icon": "🏘️",
        "color": "#8b5cf6",
        "criteria": {
            "Terrain": {"weight": 0.20, "desc": "Flat, stable ground"},
            "Infrastructure": {"weight": 0.25, "desc": "Existing roads, utilities"},
            "Climate": {"weight": 0.15, "desc": "Comfortable temperatures"},
            "Water": {"weight": 0.15, "desc": "Water supply access"},
            "Soil Stability": {"weight": 0.10, "desc": "Low clay, stable foundation"},
            "Risk": {"weight": 0.15, "desc": "Low natural hazard risk"},
        },
    },
    "conservation": {
        "name": "Conservation / Nature Reserve",
        "icon": "🌿",
        "color": "#059669",
        "criteria": {
            "Biodiversity": {"weight": 0.35, "desc": "Species richness, rare species"},
            "Habitat Quality": {"weight": 0.20, "desc": "Water features, terrain variety"},
            "Low Development": {"weight": 0.20, "desc": "Minimal existing infrastructure"},
            "Protection Status": {"weight": 0.15, "desc": "Existing protected areas nearby"},
            "Connectivity": {"weight": 0.10, "desc": "Ecological corridor potential"},
        },
    },
    "tourism": {
        "name": "Tourism Development",
        "icon": "📸",
        "color": "#ec4899",
        "criteria": {
            "Scenic Value": {"weight": 0.25, "desc": "Dramatic terrain, water features"},
            "Biodiversity": {"weight": 0.20, "desc": "Wildlife viewing potential"},
            "Climate": {"weight": 0.20, "desc": "Pleasant weather for visitors"},
            "Infrastructure": {"weight": 0.20, "desc": "Road access, existing facilities"},
            "Uniqueness": {"weight": 0.15, "desc": "Geological features, protected areas"},
        },
    },
}


def _evaluate_criteria(profile_key, weather, elevation, soil, water, landuse,
                       biodiversity, earthquakes, protected, risk, lat=0.0):
    """Evaluate all criteria for a suitability profile. Returns dict of criterion scores (0-100)."""
    scores = {}
    profile = SUITABILITY_PROFILES[profile_key]

    if profile_key == "agriculture":
        # Soil Quality
        soil_score = 50
        try:
            layers = soil.get("properties", {}).get("layers", [])
            for layer in layers:
                name = layer.get("name", "")
                depths = layer.get("depths", [])
                if depths:
                    val = depths[0].get("values", {}).get("mean")
                    if val is not None:
                        if name == "soc" and val / 10 > 15:
                            soil_score += 15
                        if name == "phh2o" and 55 <= val / 10 <= 75:
                            soil_score += 15
                        if name == "nitrogen" and val / 100 > 2:
                            soil_score += 10
        except Exception:
            pass
        scores["Soil Quality"] = min(100, soil_score)

        # Water Access
        w_score = 30
        try:
            elements = water.get("elements", [])
            springs = sum(1 for e in elements if e.get("tags", {}).get("natural") == "spring")
            waterways = sum(1 for e in elements if e.get("tags", {}).get("waterway"))
            wells = sum(1 for e in elements if e.get("tags", {}).get("man_made") == "water_well")
            w_score += min(30, springs * 10)
            w_score += min(20, waterways * 5)
            w_score += min(20, wells * 8)
        except Exception:
            pass
        scores["Water Access"] = min(100, w_score)

        # Climate
        c_score = 40
        try:
            daily = weather.get("daily", {})
            temps = daily.get("temperature_2m_max", [])
            if temps:
                avg_t = sum(t for t in temps if t is not None) / max(1, len([t for t in temps if t is not None]))
                if 15 <= avg_t <= 30:
                    c_score += 30
                elif 5 <= avg_t <= 35:
                    c_score += 15
            precip = daily.get("precipitation_sum", [])
            if precip:
                weekly = sum(p for p in precip if p is not None)
                annual_est = weekly * 52
                if 400 <= annual_est <= 1500:
                    c_score += 30
                elif 200 <= annual_est <= 2500:
                    c_score += 15
        except Exception:
            pass
        scores["Climate"] = min(100, c_score)

        # Terrain
        t_score = 50
        try:
            relief = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
            if isinstance(relief, (int, float)):
                if relief < 30:
                    t_score += 40
                elif relief < 100:
                    t_score += 20
                elif relief > 500:
                    t_score -= 30
        except Exception:
            pass
        scores["Terrain"] = min(100, max(0, t_score))

        # Risk
        r_score = 80
        try:
            for rn, ri in risk.items():
                rs = ri if isinstance(ri, (int, float)) else 0
                r_score -= rs * 3
        except Exception:
            pass
        scores["Risk"] = max(0, r_score)

    elif profile_key == "solar":
        # Solar Exposure
        s_score = 40
        try:
            current = weather.get("current", {})
            cloud = current.get("cloud_cover", 50)
            temp = current.get("temperature_2m", 20)
            if cloud is not None:
                if cloud < 20:
                    s_score += 35
                elif cloud < 40:
                    s_score += 25
                elif cloud < 60:
                    s_score += 10
            if temp is not None and temp > 20:
                s_score += 15
            # Latitude factor (lower = more solar)
            abs_lat = abs(lat)
            if abs_lat < 25:
                s_score += 20
            elif abs_lat < 40:
                s_score += 10
        except Exception:
            pass
        scores["Solar Exposure"] = min(100, s_score)

        # Terrain
        t_score = 50
        try:
            relief = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
            if isinstance(relief, (int, float)):
                if relief < 20:
                    t_score += 40
                elif relief < 50:
                    t_score += 20
        except Exception:
            pass
        scores["Terrain"] = min(100, t_score)

        # Infrastructure
        i_score = 30
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            roads = lu.get("road_segments", 0)
            i_score += min(40, roads * 5)
        except Exception:
            pass
        scores["Infrastructure"] = min(100, i_score)

        # Land Availability
        l_score = 70
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            buildings = lu.get("building_count", 0)
            if buildings > 50:
                l_score -= 40
            elif buildings > 20:
                l_score -= 20
        except Exception:
            pass
        scores["Land Availability"] = max(0, l_score)

        # Risk
        r_score = 80
        try:
            for rn, ri in risk.items():
                rs = ri if isinstance(ri, (int, float)) else 0
                r_score -= rs * 2
        except Exception:
            pass
        scores["Risk"] = max(0, r_score)

    elif profile_key == "wind":
        # Wind Resource
        w_score = 20
        try:
            current = weather.get("current", {})
            wind = current.get("wind_speed_10m", 0) or 0
            if wind > 30:
                w_score += 60
            elif wind > 20:
                w_score += 45
            elif wind > 12:
                w_score += 30
            elif wind > 6:
                w_score += 15
        except Exception:
            pass
        scores["Wind Resource"] = min(100, w_score)

        # Terrain (elevated = better)
        t_score = 40
        try:
            center = elevation.get("center_elevation", 0)
            if isinstance(center, (int, float)):
                if center > 500:
                    t_score += 30
                elif center > 200:
                    t_score += 20
                elif center > 50:
                    t_score += 10
        except Exception:
            pass
        scores["Terrain"] = min(100, t_score)

        # Infrastructure
        i_score = 30
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            roads = lu.get("road_segments", 0)
            i_score += min(40, roads * 5)
        except Exception:
            pass
        scores["Infrastructure"] = min(100, i_score)

        # Environmental
        e_score = 70
        try:
            species = biodiversity.get("gbif_unique_species", 0) + len(biodiversity.get("top_species", []))
            if species > 200:
                e_score -= 30
            elif species > 100:
                e_score -= 15
        except Exception:
            pass
        scores["Environmental"] = max(0, e_score)

        # Risk
        r_score = 80
        try:
            for rn, ri in risk.items():
                rs = ri if isinstance(ri, (int, float)) else 0
                r_score -= rs * 2
        except Exception:
            pass
        scores["Risk"] = max(0, r_score)

    elif profile_key == "housing":
        scores["Terrain"] = 50
        try:
            relief = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
            if isinstance(relief, (int, float)):
                if relief < 20:
                    scores["Terrain"] = 90
                elif relief < 50:
                    scores["Terrain"] = 70
                elif relief > 300:
                    scores["Terrain"] = 20
        except Exception:
            pass

        scores["Infrastructure"] = 30
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            scores["Infrastructure"] = min(100, 30 + lu.get("road_segments", 0) * 5 + lu.get("building_count", 0))
        except Exception:
            pass

        scores["Climate"] = 50
        try:
            current = weather.get("current", {})
            temp = current.get("temperature_2m", 20)
            if temp is not None:
                if 15 <= temp <= 28:
                    scores["Climate"] = 85
                elif 5 <= temp <= 35:
                    scores["Climate"] = 60
        except Exception:
            pass

        scores["Water"] = 30
        try:
            w_elements = water.get("elements", [])
            total_w = len(w_elements)
            scores["Water"] = min(100, 30 + total_w * 10)
        except Exception:
            pass

        scores["Soil Stability"] = 60
        try:
            layers = soil.get("properties", {}).get("layers", [])
            for layer in layers:
                if layer.get("name") == "clay":
                    depths = layer.get("depths", [])
                    if depths:
                        clay = (depths[0].get("values", {}).get("mean", 250) or 250) / 10
                        if clay < 20:
                            scores["Soil Stability"] = 85
                        elif clay > 50:
                            scores["Soil Stability"] = 25
        except Exception:
            pass

        scores["Risk"] = 80
        try:
            for rn, ri in risk.items():
                rs = ri if isinstance(ri, (int, float)) else 0
                scores["Risk"] = max(0, scores["Risk"] - rs * 3)
        except Exception:
            pass

    elif profile_key == "conservation":
        scores["Biodiversity"] = 20
        try:
            total = biodiversity.get("gbif_unique_species", 0) + len(biodiversity.get("top_species", []))
            if total > 300:
                scores["Biodiversity"] = 95
            elif total > 150:
                scores["Biodiversity"] = 80
            elif total > 50:
                scores["Biodiversity"] = 60
            elif total > 10:
                scores["Biodiversity"] = 40
        except Exception:
            pass

        scores["Habitat Quality"] = 30
        try:
            w_elements = water.get("elements", [])
            total_w = len(w_elements)
            relief = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
            scores["Habitat Quality"] = min(100, 30 + total_w * 5 + (10 if isinstance(relief, (int, float)) and relief > 200 else 0))
        except Exception:
            pass

        scores["Low Development"] = 80
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            buildings = lu.get("building_count", 0)
            if buildings > 100:
                scores["Low Development"] = 10
            elif buildings > 20:
                scores["Low Development"] = 40
            elif buildings == 0:
                scores["Low Development"] = 95
        except Exception:
            pass

        scores["Protection Status"] = 20
        try:
            areas = protected.get("elements", []) if protected else []
            if len(areas) > 5:
                scores["Protection Status"] = 90
            elif len(areas) > 0:
                scores["Protection Status"] = 60
        except Exception:
            pass

        scores["Connectivity"] = 50
        try:
            waterways = sum(1 for e in water.get("elements", []) if e.get("tags", {}).get("waterway"))
            scores["Connectivity"] = min(100, 50 + waterways * 10)
        except Exception:
            pass

    elif profile_key == "tourism":
        scores["Scenic Value"] = 30
        try:
            relief = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
            water_bodies = sum(1 for e in water.get("elements", []) if e.get("tags", {}).get("natural") == "water")
            if isinstance(relief, (int, float)):
                if relief > 500:
                    scores["Scenic Value"] += 35
                elif relief > 200:
                    scores["Scenic Value"] += 20
            scores["Scenic Value"] += min(20, water_bodies * 10)
        except Exception:
            pass
        scores["Scenic Value"] = min(100, scores["Scenic Value"])

        scores["Biodiversity"] = 20
        try:
            total = biodiversity.get("gbif_unique_species", 0) + len(biodiversity.get("top_species", []))
            if total > 200:
                scores["Biodiversity"] = 90
            elif total > 50:
                scores["Biodiversity"] = 60
            elif total > 10:
                scores["Biodiversity"] = 40
        except Exception:
            pass

        scores["Climate"] = 50
        try:
            current = weather.get("current", {})
            temp = current.get("temperature_2m", 20)
            if temp is not None:
                if 18 <= temp <= 28:
                    scores["Climate"] = 90
                elif 10 <= temp <= 32:
                    scores["Climate"] = 65
        except Exception:
            pass

        scores["Infrastructure"] = 30
        try:
            lu = compute_landuse_breakdown(landuse) if landuse else {}
            scores["Infrastructure"] = min(100, 30 + lu.get("road_segments", 0) * 4 + lu.get("building_count", 0) // 2)
        except Exception:
            pass

        scores["Uniqueness"] = 30
        try:
            areas = protected.get("elements", []) if protected else []
            if len(areas) > 3:
                scores["Uniqueness"] += 40
            elif len(areas) > 0:
                scores["Uniqueness"] += 20
        except Exception:
            pass
        scores["Uniqueness"] = min(100, scores["Uniqueness"])

    return scores


def render_suitability_analyzer_tab():
    """Main render function for Suitability Analyzer tab."""
    st.markdown("""
    <div class="tab-header emerald">
        <h4>🎯 Land Suitability Analyzer</h4>
        <p>Purpose-specific land evaluation — farming, solar, wind, housing, conservation or tourism</p>
    </div>
    """, unsafe_allow_html=True)

    # Profile selection
    profile_options = {k: f"{v['icon']} {v['name']}" for k, v in SUITABILITY_PROFILES.items()}
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_profile = st.selectbox("Purpose", list(profile_options.keys()),
                                        format_func=lambda x: profile_options[x],
                                        key="sa_profile")
    profile = SUITABILITY_PROFILES[selected_profile]

    with col2:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="sa_preset")
    preset_data = ANALYSIS_PRESETS.get(preset)
    d_lat = preset_data["lat"] if preset_data else 41.90
    d_lon = preset_data["lon"] if preset_data else 12.50

    lc1, lc2 = st.columns(2)
    with lc1:
        lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01, key="sa_lat", format="%.4f")
    with lc2:
        lon = st.number_input("Longitude", -180.0, 180.0, d_lon, step=0.01, key="sa_lon", format="%.4f")

    # Show criteria
    with st.expander(f"Evaluation Criteria for {profile['name']}"):
        for cname, cinfo in profile["criteria"].items():
            st.markdown(f"- **{cname}** (weight: {cinfo['weight']*100:.0f}%) — {cinfo['desc']}")

    if st.button(f"{profile['icon']} Analyze Suitability", type="primary", use_container_width=True):
        progress = st.progress(0, text="Collecting data...")

        # Fetch data
        try:
            elevation = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=7)
        except Exception:
            elevation = {}
        progress.progress(12)

        try:
            weather = fetch_weather_data(lat, lon)
        except Exception:
            weather = {}
        progress.progress(24)

        try:
            soil = fetch_soil_data(lat, lon)
        except Exception:
            soil = {}
        progress.progress(36)

        try:
            inat = fetch_biodiversity(lat, lon, radius_km=10)
            gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
            bio = compute_species_breakdown(inat, gbif)
        except Exception:
            bio = {}
        progress.progress(48)

        try:
            water = fetch_water_features(lat, lon, radius=5000)
        except Exception:
            water = {}
        progress.progress(60)

        try:
            landuse = fetch_landuse_infrastructure(lat, lon, radius=3000)
        except Exception:
            landuse = {}
        progress.progress(70)

        try:
            earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        except Exception:
            earthquakes = {}

        try:
            protected = fetch_protected_areas(lat, lon, radius=10000)
        except Exception:
            protected = {}
        progress.progress(80)

        try:
            risk = compute_risk_assessment(earthquakes, water, landuse, elevation, lat, lon)
        except Exception:
            risk = {}
        progress.progress(90)

        # Evaluate criteria
        criteria_scores = _evaluate_criteria(
            selected_profile, weather, elevation, soil, water, landuse,
            bio, earthquakes, protected, risk, lat=lat
        )

        # Weighted overall
        overall = 0
        for cname, cinfo in profile["criteria"].items():
            overall += criteria_scores.get(cname, 50) * cinfo["weight"]
        overall = round(overall)

        progress.progress(100)

        st.session_state["sa_results"] = {
            "criteria": criteria_scores, "overall": overall, "profile": selected_profile,
            "lat": lat, "lon": lon,
        }

    # Display results
    if "sa_results" not in st.session_state:
        return

    r = st.session_state["sa_results"]
    criteria_scores = r["criteria"]
    overall = r["overall"]
    profile_key = r["profile"]
    profile = SUITABILITY_PROFILES[profile_key]

    st.markdown("---")

    # Overall suitability score
    color = "#10b981" if overall >= 70 else "#06b6d4" if overall >= 50 else "#f59e0b" if overall >= 30 else "#ef4444"
    verdict = "HIGHLY SUITABLE" if overall >= 75 else "SUITABLE" if overall >= 55 else "MARGINAL" if overall >= 35 else "NOT SUITABLE"

    st.markdown(f"""
    <div style="text-align:center; padding:2rem; background:linear-gradient(135deg, #1e293b, #0f172a);
                border-radius:16px; border:2px solid {color}; margin-bottom:1.5rem;">
        <div style="font-size:1rem; color:#94a3b8;">{profile['icon']} {profile['name']}</div>
        <div style="font-size:4rem; font-weight:900; color:{color}; margin:0.5rem 0;">{overall}%</div>
        <div style="font-size:1.3rem; color:{color}; font-weight:600;">{verdict}</div>
        <div style="color:#64748b; font-size:0.85rem; margin-top:0.5rem;">({r['lat']:.4f}, {r['lon']:.4f})</div>
    </div>
    """, unsafe_allow_html=True)

    # Criteria breakdown
    st.markdown("### Criteria Breakdown")
    for cname, cinfo in profile["criteria"].items():
        score = criteria_scores.get(cname, 50)
        c = "#10b981" if score >= 70 else "#06b6d4" if score >= 50 else "#f59e0b" if score >= 30 else "#ef4444"
        weight_pct = int(cinfo["weight"] * 100)

        st.markdown(f"""
        <div style="background:#1e293b; border-radius:8px; padding:0.8rem; margin:0.4rem 0;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#e2e8f0; font-weight:600;">{cname} <span style="color:#64748b; font-size:0.8rem;">({weight_pct}%)</span></span>
                <span style="color:{c}; font-weight:700;">{score}/100</span>
            </div>
            <div style="background:#334155; border-radius:4px; height:8px;">
                <div style="background:{c}; width:{score}%; height:100%; border-radius:4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Radar chart
    st.markdown("### Suitability Profile")
    labels = list(criteria_scores.keys())
    values = list(criteria_scores.values())
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        line_color=profile["color"],
        fillcolor=f"rgba({int(profile['color'][1:3], 16)}, {int(profile['color'][3:5], 16)}, {int(profile['color'][5:7], 16)}, 0.15)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400, margin=dict(t=30, b=30, l=60, r=60),
    )
    st.plotly_chart(fig, use_container_width=True, key="suiana_pchart1")

    # Recommendations
    st.markdown("### Recommendations")
    strengths = [k for k, v in criteria_scores.items() if v >= 70]
    weaknesses = [k for k, v in criteria_scores.items() if v < 40]

    if strengths:
        st.success(f"**Strengths:** {', '.join(strengths)}")
    if weaknesses:
        st.warning(f"**Limiting factors:** {', '.join(weaknesses)}")
    if not weaknesses and overall >= 60:
        st.info("This location shows no significant limiting factors for the selected purpose.")

    # Export
    st.markdown("---")
    export_rows = [{"Criterion": k, "Score": v, "Weight": f"{SUITABILITY_PROFILES[profile_key]['criteria'][k]['weight']*100:.0f}%"}
                   for k, v in criteria_scores.items()]
    export_rows.append({"Criterion": "OVERALL", "Score": overall, "Weight": "100%"})
    df = pd.DataFrame(export_rows)
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Suitability Report (CSV)", data=csv,
                       file_name=f"suitability_{profile_key}_{r['lat']:.2f}_{r['lon']:.2f}.csv", mime="text/csv")
