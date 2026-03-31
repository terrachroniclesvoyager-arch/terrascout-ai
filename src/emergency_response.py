"""
Emergency Response Intelligence AI module for TerraScout AI.
Evaluates emergency response readiness and disaster preparedness for any
geographic location using infrastructure, seismic, weather, and terrain data
from free APIs via deep_zone_analysis helpers.
No API keys required.
"""

import math
import logging

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
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

CLR_BG = "#1a1a2e"
CLR_CARD = "#16213e"
CLR_BORDER = "#2a3550"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

CLR_RED = "#dc2626"
CLR_BLUE = "#2563eb"
CLR_GREEN = "#16a34a"
CLR_ORANGE = "#f97316"
CLR_YELLOW = "#fbbf24"

READINESS_LEVELS = {
    "Critical": {"range": (0, 20), "color": CLR_RED},
    "Poor": {"range": (20, 40), "color": CLR_ORANGE},
    "Moderate": {"range": (40, 60), "color": CLR_YELLOW},
    "Good": {"range": (60, 80), "color": CLR_BLUE},
    "Excellent": {"range": (80, 101), "color": CLR_GREEN},
}

PRIORITY_COLORS = {
    "Critical": CLR_RED,
    "High": CLR_ORANGE,
    "Medium": CLR_YELLOW,
    "Low": CLR_GREEN,
}


def _classify_readiness(score):
    """Return the readiness classification and colour for a 0-100 score."""
    for name, info in READINESS_LEVELS.items():
        lo, hi = info["range"]
        if lo <= score < hi:
            return name, info["color"]
    return "Critical", CLR_RED


def _clamp(val, lo=0.0, hi=100.0):
    return max(lo, min(hi, val))


# ==============================================================================
# COMPUTE
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_emergency_readiness(lat, lon):
    """Compute comprehensive emergency response readiness for a location."""

    # -- Fetch all data sources -------------------------------------------------
    infra = fetch_landuse_infrastructure(lat, lon, radius=8000)
    water = fetch_water_features(lat, lon)
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6)
    weather = fetch_weather_data(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    quakes = fetch_earthquakes(lat, lon, radius_km=150, days=365)

    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])

    # -- Helper: count elements by tag value ------------------------------------
    def _count(tag_key, tag_value, source=None):
        src = source if source is not None else elements
        return sum(
            1 for e in src
            if isinstance(e, dict) and e.get("tags", {}).get(tag_key) == tag_value
        )

    def _count_any(tag_key, source=None):
        src = source if source is not None else elements
        return sum(
            1 for e in src
            if isinstance(e, dict) and e.get("tags", {}).get(tag_key)
        )

    # -- Emergency services ----------------------------------------------------
    hospitals = _count("amenity", "hospital")
    fire_stations = _count("amenity", "fire_station")
    police_stations = _count("amenity", "police")
    ambulance_stations = _count("amenity", "ambulance_station") + sum(
        1 for e in elements
        if isinstance(e, dict) and e.get("tags", {}).get("emergency") == "ambulance_station"
    )
    helipads = _count("aeroway", "helipad")
    pharmacies = _count("amenity", "pharmacy")

    # -- Access infrastructure -------------------------------------------------
    primary_roads = sum(
        1 for e in elements
        if isinstance(e, dict)
        and e.get("tags", {}).get("highway") in ("primary", "primary_link")
    )
    secondary_roads = sum(
        1 for e in elements
        if isinstance(e, dict)
        and e.get("tags", {}).get("highway") in ("secondary", "secondary_link")
    )
    bridges = _count("man_made", "bridge")
    tunnels = sum(
        1 for e in elements
        if isinstance(e, dict) and e.get("tags", {}).get("tunnel") == "yes"
    )

    # -- Shelter capacity ------------------------------------------------------
    schools = _count("amenity", "school")
    community_centres = _count("amenity", "community_centre")
    places_of_worship = _count("amenity", "place_of_worship")
    sports_facilities = _count("leisure", "sports_centre")

    # -- Communication & power -------------------------------------------------
    comm_towers = sum(
        1 for e in elements
        if isinstance(e, dict)
        and e.get("tags", {}).get("man_made") == "tower"
        and "communication" in str(e.get("tags", {}).get("tower:type", "")).lower()
    )
    power_infra = _count_any("power")

    # -- Service counts dict ---------------------------------------------------
    service_counts = {
        "Hospitals": hospitals,
        "Fire Stations": fire_stations,
        "Police Stations": police_stations,
        "Ambulance Stations": ambulance_stations,
        "Helipads": helipads,
        "Pharmacies": pharmacies,
        "Primary Roads": primary_roads,
        "Secondary Roads": secondary_roads,
        "Bridges": bridges,
        "Tunnels": tunnels,
        "Schools (potential shelters)": schools,
        "Community Centres": community_centres,
        "Places of Worship": places_of_worship,
        "Sports Facilities": sports_facilities,
        "Communication Towers": comm_towers,
        "Power Infrastructure": power_infra,
    }

    # ==========================================================================
    # Readiness indices (0 - 100)
    # ==========================================================================

    # 1. Emergency Services
    es_score = _clamp(
        min(hospitals * 20, 30)
        + min(fire_stations * 15, 25)
        + min(police_stations * 12, 25)
        + min(ambulance_stations * 15, 20)
    )

    # 2. Evacuation Routes
    evac_score = _clamp(
        min((primary_roads + secondary_roads) * 4, 70)
        + min(bridges * 10, 30)
    )

    # 3. Shelter Capacity
    shelter_score = _clamp(
        min(schools * 8, 30)
        + min(community_centres * 12, 25)
        + min(sports_facilities * 10, 20)
        + min(places_of_worship * 5, 25)
    )

    # 4. Communication Infrastructure
    comm_score = _clamp(
        min(comm_towers * 15, 50)
        + min(power_infra * 3, 50)
    )

    # 5. Medical Access
    med_score = _clamp(
        min(hospitals * 25, 40)
        + min(pharmacies * 10, 30)
        + min(ambulance_stations * 15, 30)
    )

    # 6. Response Time Estimate (inverse of distance/density)
    total_services = hospitals + fire_stations + police_stations + ambulance_stations
    road_density = primary_roads + secondary_roads
    if total_services > 0 and road_density > 0:
        density_factor = min(total_services / 3.0, 1.0)
        access_factor = min(road_density / 10.0, 1.0)
        response_score = _clamp((density_factor * 0.6 + access_factor * 0.4) * 100)
    elif total_services > 0:
        response_score = _clamp(total_services / 5.0 * 60)
    else:
        response_score = 10.0

    indices = {
        "Emergency Services": round(es_score, 1),
        "Evacuation Routes": round(evac_score, 1),
        "Shelter Capacity": round(shelter_score, 1),
        "Communication Infrastructure": round(comm_score, 1),
        "Medical Access": round(med_score, 1),
        "Response Time Estimate": round(response_score, 1),
    }

    # -- Overall weighted average -----------------------------------------------
    weights = {
        "Emergency Services": 0.25,
        "Evacuation Routes": 0.15,
        "Shelter Capacity": 0.15,
        "Communication Infrastructure": 0.10,
        "Medical Access": 0.20,
        "Response Time Estimate": 0.15,
    }
    readiness_index = round(
        sum(indices[k] * weights[k] for k in indices), 1
    )
    classification, _ = _classify_readiness(readiness_index)

    # ==========================================================================
    # Threat level assessment
    # ==========================================================================
    threats = []

    # Seismic risk
    significant_quakes = [
        f for f in features
        if isinstance(f, dict)
        and (f.get("properties") or {}).get("mag", 0) is not None
        and (f.get("properties") or {}).get("mag", 0) >= 3.0
    ]
    eq_count = len(features)
    sig_count = len(significant_quakes)

    mags = [
        (f.get("properties") or {}).get("mag", 0)
        for f in features
        if isinstance(f, dict)
        and (f.get("properties") or {}).get("mag") is not None
    ]
    max_mag = max(mags) if mags else 0

    if sig_count >= 5 or max_mag >= 5.0:
        threats.append({"type": "Seismic", "level": "High",
                        "detail": f"{eq_count} quakes in past year, {sig_count} M3+, max M{max_mag:.1f}"})
    elif eq_count >= 3 or max_mag >= 3.0:
        threats.append({"type": "Seismic", "level": "Medium",
                        "detail": f"{eq_count} quakes recorded, max magnitude M{max_mag:.1f}"})
    else:
        threats.append({"type": "Seismic", "level": "Low",
                        "detail": f"{eq_count} minor quake(s) in the past year"})

    # Weather risk
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    wind_speed = current.get("wind_speed_10m") or 0
    precip = current.get("precipitation") or 0
    temp = current.get("temperature_2m") or 20

    if wind_speed > 60 or precip > 30:
        threats.append({"type": "Weather", "level": "High",
                        "detail": f"Wind {wind_speed} km/h, precip {precip} mm"})
    elif wind_speed > 30 or precip > 10 or temp > 40:
        threats.append({"type": "Weather", "level": "Medium",
                        "detail": f"Wind {wind_speed} km/h, temp {temp}C, precip {precip} mm"})
    else:
        threats.append({"type": "Weather", "level": "Low",
                        "detail": f"Stable: {temp}C, wind {wind_speed} km/h"})

    # Elevation / flood risk
    center_elev = (elev_data.get("center_elevation", 0)
                   if isinstance(elev_data, dict) else 0)
    grid_elevs = (elev_data.get("grid_elevations", [])
                  if isinstance(elev_data, dict) else [])
    valid_elevs = [e for e in grid_elevs if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0

    water_count = len([
        e for e in water_elements
        if isinstance(e, dict)
        and e.get("tags", {}).get("waterway")
    ])

    if center_elev < 10 and water_count > 3:
        threats.append({"type": "Flood", "level": "High",
                        "detail": f"Low elevation ({center_elev:.0f}m) with {water_count} waterways nearby"})
    elif center_elev < 50 or water_count > 2:
        threats.append({"type": "Flood", "level": "Medium",
                        "detail": f"Elevation {center_elev:.0f}m, {water_count} waterway(s)"})
    else:
        threats.append({"type": "Flood", "level": "Low",
                        "detail": f"Elevation {center_elev:.0f}m, limited flood exposure"})

    # Landslide risk (steep terrain)
    if elev_range > 200:
        threats.append({"type": "Landslide", "level": "High",
                        "detail": f"Steep terrain, {elev_range:.0f}m elevation range"})
    elif elev_range > 80:
        threats.append({"type": "Landslide", "level": "Medium",
                        "detail": f"Moderate terrain, {elev_range:.0f}m elevation range"})
    else:
        threats.append({"type": "Landslide", "level": "Low",
                        "detail": f"Relatively flat terrain ({elev_range:.0f}m range)"})

    threat_assessment = {
        "threats": threats,
        "overall_threat": "High" if any(t["level"] == "High" for t in threats)
                          else ("Medium" if any(t["level"] == "Medium" for t in threats)
                                else "Low"),
    }

    # ==========================================================================
    # Gap analysis
    # ==========================================================================
    gap_analysis = []

    if hospitals == 0:
        gap_analysis.append({
            "gap": "No hospitals within 8 km radius",
            "priority": "Critical",
            "recommendation": "Establish medical evacuation protocols to nearest hospital."
        })
    if fire_stations == 0:
        gap_analysis.append({
            "gap": "No fire stations detected",
            "priority": "Critical",
            "recommendation": "Area lacks fire response capability; volunteer brigade recommended."
        })
    if police_stations == 0:
        gap_analysis.append({
            "gap": "No police stations in area",
            "priority": "High",
            "recommendation": "Coordinate with nearest law enforcement for emergency coverage."
        })
    if ambulance_stations == 0 and hospitals == 0:
        gap_analysis.append({
            "gap": "No ambulance or hospital services nearby",
            "priority": "Critical",
            "recommendation": "Deploy mobile medical units or air ambulance staging."
        })
    if primary_roads + secondary_roads < 3:
        gap_analysis.append({
            "gap": "Limited evacuation routes (fewer than 3 major roads)",
            "priority": "High",
            "recommendation": "Identify and mark alternative evacuation paths."
        })
    if schools + community_centres + sports_facilities < 2:
        gap_analysis.append({
            "gap": "Insufficient shelter capacity",
            "priority": "High",
            "recommendation": "Pre-designate additional buildings as emergency shelters."
        })
    if comm_towers == 0:
        gap_analysis.append({
            "gap": "No communication towers detected",
            "priority": "Medium",
            "recommendation": "Deploy portable communication equipment for emergencies."
        })
    if helipads == 0:
        gap_analysis.append({
            "gap": "No helipads for aerial evacuation",
            "priority": "Medium",
            "recommendation": "Identify flat, open areas suitable for helicopter landing zones."
        })
    if pharmacies == 0:
        gap_analysis.append({
            "gap": "No pharmacies in the area",
            "priority": "Medium",
            "recommendation": "Pre-position essential medical supplies at shelters."
        })

    if not gap_analysis:
        gap_analysis.append({
            "gap": "No critical gaps identified",
            "priority": "Low",
            "recommendation": "Maintain current emergency infrastructure and conduct regular drills."
        })

    # ==========================================================================
    # Recommendations
    # ==========================================================================
    recommendations = []

    if readiness_index < 30:
        recommendations.append({
            "priority": "Critical",
            "text": "Emergency readiness is critically low. Establish mutual-aid agreements with neighbouring jurisdictions immediately."
        })
    if readiness_index < 50:
        recommendations.append({
            "priority": "High",
            "text": "Readiness below acceptable threshold. Invest in emergency service infrastructure."
        })

    if threat_assessment["overall_threat"] == "High":
        recommendations.append({
            "priority": "Critical",
            "text": "Active high-level threats detected. Activate emergency operations centre."
        })

    if es_score < 40:
        recommendations.append({
            "priority": "High",
            "text": "Emergency services are insufficient. Increase staffing or establish satellite stations."
        })
    if evac_score < 40:
        recommendations.append({
            "priority": "High",
            "text": "Evacuation route network is weak. Conduct route planning and public awareness campaigns."
        })
    if shelter_score < 30:
        recommendations.append({
            "priority": "Medium",
            "text": "Shelter capacity is limited. Designate and equip additional shelter facilities."
        })
    if med_score < 40:
        recommendations.append({
            "priority": "High",
            "text": "Medical access is poor. Pre-position first-aid kits and train community responders."
        })
    if comm_score < 30:
        recommendations.append({
            "priority": "Medium",
            "text": "Communication infrastructure is sparse. Deploy backup radio and satellite systems."
        })

    if readiness_index >= 70 and threat_assessment["overall_threat"] == "Low":
        recommendations.append({
            "priority": "Low",
            "text": "Good readiness with low threat levels. Continue regular drills and equipment maintenance."
        })

    if not recommendations:
        recommendations.append({
            "priority": "Low",
            "text": "Moderate readiness achieved. Focus on continuous improvement and community training."
        })

    return {
        "readiness_index": readiness_index,
        "classification": classification,
        "indices": indices,
        "threat_assessment": threat_assessment,
        "service_counts": service_counts,
        "gap_analysis": gap_analysis,
        "recommendations": recommendations,
    }


# ==============================================================================
# RENDER
# ==============================================================================

def _readiness_bar(score, height=16):
    """Return an HTML progress bar for a 0-100 readiness score."""
    pct = min(score / 100.0 * 100, 100)
    _, bar_color = _classify_readiness(score)
    return (
        f'<div style="background:#2a2a3e;border-radius:8px;height:{height}px;width:100%;overflow:hidden;">'
        f'<div style="width:{pct}%;height:100%;border-radius:8px;'
        f'background:linear-gradient(90deg,{CLR_BLUE},{bar_color});"></div></div>'
    )


def render_emergency_response_tab():
    """Render the Emergency Response Intelligence tab."""

    st.markdown(
        f"""<div style="background:{CLR_BG};padding:18px 20px 10px;border-radius:12px;
        border:1px solid {CLR_BORDER};margin-bottom:18px;">
        <h2 style="color:{CLR_RED};margin:0;">Emergency Response Intelligence AI</h2>
        <p style="color:{CLR_TEXT_SEC};margin:4px 0 0;">Evaluate emergency response readiness
        and disaster preparedness for any location.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # -- Location selector ------------------------------------------------------
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="er_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="er_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="er_lon",
        )

    run = st.button(
        "Assess Emergency Readiness", type="primary",
        key="er_run", use_container_width=True,
    )

    if not run:
        st.info("Select a location and press **Assess Emergency Readiness** to begin.")
        return

    with st.spinner("Fetching data and computing emergency readiness..."):
        result = compute_emergency_readiness(lat, lon)

    ri = result["readiness_index"]
    classification = result["classification"]
    indices = result["indices"]
    threat_assessment = result["threat_assessment"]
    service_counts = result["service_counts"]
    gap_analysis = result["gap_analysis"]
    recommendations = result["recommendations"]

    _, ri_color = _classify_readiness(ri)

    # ==========================================================================
    # Readiness Index header
    # ==========================================================================
    st.markdown(
        f"""<div style="background:{CLR_CARD};padding:20px 24px;border-radius:12px;
        border:1px solid {ri_color};margin-bottom:14px;text-align:center;">
        <span style="font-size:2.8rem;font-weight:800;color:{ri_color};">{ri}</span>
        <span style="font-size:1.1rem;color:{CLR_TEXT_SEC};">&nbsp;/ 100</span>
        <div style="margin-top:8px;">
        <span style="background:{ri_color};color:#fff;padding:4px 18px;border-radius:20px;
        font-weight:700;font-size:0.95rem;">{classification}</span>
        </div>
        <p style="color:{CLR_TEXT_SEC};margin:10px 0 0;font-size:0.88rem;">
        Overall Emergency Readiness Index</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # 6 readiness cards (3 x 2 grid)
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:16px 0 8px;">Readiness Component Scores</h4>',
        unsafe_allow_html=True,
    )

    card_icons = {
        "Emergency Services": "hospital",
        "Evacuation Routes": "route",
        "Shelter Capacity": "house-chimney",
        "Communication Infrastructure": "tower-broadcast",
        "Medical Access": "kit-medical",
        "Response Time Estimate": "clock",
    }

    comp_list = list(indices.items())
    for row_start in range(0, len(comp_list), 3):
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            ci = row_start + idx
            if ci >= len(comp_list):
                break
            name, score = comp_list[ci]
            _, sc = _classify_readiness(score)
            bar_html = _readiness_bar(score)
            col.markdown(
                f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
                border-radius:10px;padding:14px 16px;margin-bottom:10px;">
                <p style="color:{CLR_TEXT_SEC};margin:0 0 4px;font-size:0.82rem;">{name}</p>
                <span style="font-size:1.6rem;font-weight:700;color:{sc};">{score}</span>
                <span style="color:{CLR_TEXT_SEC};font-size:0.85rem;">/100</span>
                <div style="margin-top:6px;">{bar_html}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ==========================================================================
    # Radar chart of readiness indices
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Readiness Radar</h4>',
        unsafe_allow_html=True,
    )

    categories = list(indices.keys())
    values = list(indices.values())
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(37,99,235,0.22)",
        line=dict(color=CLR_BLUE, width=2),
        marker=dict(size=6, color=CLR_BLUE),
        name="Readiness",
    ))
    radar.update_layout(
        polar=dict(
            bgcolor=CLR_BG,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor=CLR_BORDER,
                tickfont=dict(color=CLR_TEXT_SEC, size=10),
            ),
            angularaxis=dict(
                gridcolor=CLR_BORDER,
                tickfont=dict(color=CLR_TEXT, size=11),
            ),
        ),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        showlegend=False,
        height=400,
        margin=dict(t=40, b=40, l=80, r=80),
    )
    st.plotly_chart(radar, use_container_width=True, key="emeres_pchart1")

    # ==========================================================================
    # Emergency services inventory table
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Emergency Services Inventory</h4>',
        unsafe_allow_html=True,
    )

    table_rows = ""
    for svc_name, svc_count in service_counts.items():
        count_color = CLR_GREEN if svc_count > 0 else CLR_RED
        status = "Available" if svc_count > 0 else "Not Found"
        status_color = CLR_GREEN if svc_count > 0 else CLR_RED
        table_rows += (
            f'<tr style="border-bottom:1px solid {CLR_BORDER};">'
            f'<td style="padding:8px 12px;color:{CLR_TEXT};font-size:0.9rem;">{svc_name}</td>'
            f'<td style="padding:8px 12px;color:{count_color};font-weight:700;'
            f'font-size:0.95rem;text-align:center;">{svc_count}</td>'
            f'<td style="padding:8px 12px;text-align:center;">'
            f'<span style="color:{status_color};font-size:0.82rem;font-weight:600;">'
            f'{status}</span></td></tr>'
        )

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
        border-radius:10px;overflow:hidden;margin-bottom:14px;">
        <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="background:{CLR_BG};border-bottom:2px solid {CLR_BORDER};">
        <th style="padding:10px 12px;color:{CLR_TEXT_SEC};text-align:left;font-size:0.82rem;">
        Service / Infrastructure</th>
        <th style="padding:10px 12px;color:{CLR_TEXT_SEC};text-align:center;font-size:0.82rem;">
        Count</th>
        <th style="padding:10px 12px;color:{CLR_TEXT_SEC};text-align:center;font-size:0.82rem;">
        Status</th>
        </tr></thead><tbody>{table_rows}</tbody></table></div>""",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # Threat assessment section
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Current Threat Assessment</h4>',
        unsafe_allow_html=True,
    )

    overall_threat = threat_assessment["overall_threat"]
    ot_color = (CLR_RED if overall_threat == "High"
                else CLR_ORANGE if overall_threat == "Medium"
                else CLR_GREEN)

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {ot_color};
        border-radius:10px;padding:14px 18px;margin-bottom:10px;">
        <span style="color:{CLR_TEXT_SEC};font-size:0.85rem;">Overall Threat Level:&nbsp;</span>
        <span style="color:{ot_color};font-weight:700;font-size:1.15rem;">{overall_threat}</span>
        </div>""",
        unsafe_allow_html=True,
    )

    threat_items_html = ""
    for t in threat_assessment["threats"]:
        t_color = (CLR_RED if t["level"] == "High"
                   else CLR_ORANGE if t["level"] == "Medium"
                   else CLR_GREEN)
        threat_items_html += (
            f'<div style="display:flex;align-items:center;padding:8px 0;'
            f'border-bottom:1px solid {CLR_BORDER};">'
            f'<span style="min-width:120px;color:{CLR_TEXT};font-weight:600;'
            f'font-size:0.9rem;">{t["type"]}</span>'
            f'<span style="min-width:80px;color:{t_color};font-weight:700;'
            f'font-size:0.85rem;">{t["level"]}</span>'
            f'<span style="color:{CLR_TEXT_SEC};font-size:0.84rem;">{t["detail"]}</span>'
            f'</div>'
        )

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
        border-radius:10px;padding:12px 18px;margin-bottom:14px;">
        {threat_items_html}
        </div>""",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # Gap analysis
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Gap Analysis</h4>',
        unsafe_allow_html=True,
    )

    gap_html = ""
    for g in gap_analysis:
        g_color = PRIORITY_COLORS.get(g["priority"], CLR_YELLOW)
        gap_html += (
            f'<div style="background:rgba(0,0,0,0.2);border-left:4px solid {g_color};'
            f'border-radius:0 8px 8px 0;padding:10px 16px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="color:{CLR_TEXT};font-weight:600;font-size:0.9rem;">'
            f'{g["gap"]}</span>'
            f'<span style="background:{g_color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:0.75rem;font-weight:700;">'
            f'{g["priority"]}</span></div>'
            f'<p style="color:{CLR_TEXT_SEC};margin:4px 0 0;font-size:0.84rem;">'
            f'{g["recommendation"]}</p></div>'
        )

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
        border-radius:10px;padding:14px 16px;margin-bottom:14px;">
        {gap_html}
        </div>""",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # Recommendations
    # ==========================================================================
    st.markdown(
        f'<h4 style="color:{CLR_TEXT};margin:18px 0 8px;">Recommendations</h4>',
        unsafe_allow_html=True,
    )

    recs_html = ""
    for rec in recommendations:
        r_color = PRIORITY_COLORS.get(rec["priority"], CLR_YELLOW)
        recs_html += (
            f'<div style="display:flex;align-items:flex-start;padding:8px 0;'
            f'border-bottom:1px solid {CLR_BORDER};">'
            f'<span style="background:{r_color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:0.72rem;font-weight:700;margin-right:12px;'
            f'white-space:nowrap;margin-top:2px;">{rec["priority"]}</span>'
            f'<span style="color:{CLR_TEXT};font-size:0.9rem;">{rec["text"]}</span>'
            f'</div>'
        )

    st.markdown(
        f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
        border-radius:12px;padding:16px 20px;margin-bottom:14px;">
        {recs_html}
        </div>""",
        unsafe_allow_html=True,
    )
