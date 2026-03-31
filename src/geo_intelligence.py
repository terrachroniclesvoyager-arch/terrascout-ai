"""
Geospatial Intelligence Summary AI module for TerraScout AI.
Provides a comprehensive one-page intelligence briefing combining all available
data sources into an actionable summary with scoring, risk assessment,
opportunity analysis, and an overall intelligence grade.
"""

import math
import logging
import datetime

import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Styling constants
# ---------------------------------------------------------------------------
_BG_DARK = "#1a1a2e"
_BG_CARD = "rgba(6,78,59,0.18)"
_BORDER = "#064e3b"
_TEXT_PRIMARY = "#e8ecf4"
_TEXT_SECONDARY = "#8b97b0"
_ACCENT = "#10b981"
_ALERT_RED = "#ef4444"
_SLATE = "#334155"

_GRADE_COLORS = {
    "A+": "#10b981", "A": "#10b981", "A-": "#10b981",
    "B+": "#06b6d4", "B": "#06b6d4", "B-": "#06b6d4",
    "C+": "#f59e0b", "C": "#f59e0b", "C-": "#f59e0b",
    "D+": "#f97316", "D": "#f97316", "D-": "#f97316",
    "F": "#ef4444",
}


# ---------------------------------------------------------------------------
# Helper: safe soil value extraction
# ---------------------------------------------------------------------------
def _soil_value(props, name, div=10):
    """Extract the first-depth mean for a soil property, scaled by *div*."""
    layers = props.get("layers", [])
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            depths = layer.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
    return None


def _safe_list(vals):
    """Return *vals* with None entries removed."""
    return [v for v in vals if v is not None]


def _clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Intelligence computation (cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def compute_geo_intelligence(lat, lon):
    """
    Fetch ALL data sources for *lat*/*lon* and compute a unified
    intelligence report with 10 scored sections plus an overall grade.

    Returns a dict with keys:
        grade, grade_color, sections, key_findings, critical_alerts,
        quick_metrics
    """

    # -- 1. Fetch data sources sequentially --------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    inat = fetch_biodiversity(lat, lon)
    gbif = fetch_gbif_occurrences(lat, lon)
    quakes = fetch_earthquakes(lat, lon)

    # -- 2. Parse raw responses safely -------------------------------------
    props_raw = (soil if isinstance(soil, dict) else {}).get("properties", {})
    layers = props_raw.get("layers", [])
    props = {}
    for layer in layers:
        lname = layer.get("name", "")
        props[lname] = layer

    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])
    daily_precip = daily.get("precipitation_sum", [])

    temp_now = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    pressure = current.get("surface_pressure")

    elements_water = (water if isinstance(water, dict) else {}).get("elements", [])
    elements_infra = (infra if isinstance(infra, dict) else {}).get("elements", [])
    elements_prot = (protected if isinstance(protected, dict) else {}).get("elements", [])
    features_eq = (quakes if isinstance(quakes, dict) else {}).get("features", [])

    center_elev = elevation.get("center_elevation", 0) if isinstance(elevation, dict) else 0
    min_elev = elevation.get("min_elevation", 0) if isinstance(elevation, dict) else 0
    max_elev = elevation.get("max_elevation", 0) if isinstance(elevation, dict) else 0
    avg_elev = elevation.get("avg_elevation", 0) if isinstance(elevation, dict) else 0
    elev_range = max_elev - min_elev

    species = compute_species_breakdown(
        inat if isinstance(inat, dict) else {},
        gbif if isinstance(gbif, dict) else {},
    )
    kingdom_counts = species.get("kingdom_counts") or {}
    top_species = species.get("top_species") or []
    inat_total = species.get("inat_total") or 0
    gbif_total = species.get("gbif_total") or 0
    gbif_unique = species.get("gbif_unique_species") or 0

    # -- 3. Derived metrics ------------------------------------------------
    # Soil
    clay = _soil_value(props, "clay", 10)
    sand = _soil_value(props, "sand", 10)
    silt = _soil_value(props, "silt", 10)
    ph = _soil_value(props, "phh2o", 10)
    soc = _soil_value(props, "soc", 10)
    nitrogen = _soil_value(props, "nitrogen", 100)
    cec = _soil_value(props, "cec", 10)

    if clay is not None and sand is not None:
        if clay > 40:
            texture = "Clay"
        elif sand > 60:
            texture = "Sandy"
        elif silt is not None and silt > 50:
            texture = "Silty"
        else:
            texture = "Loam"
    else:
        texture = "Unknown"

    fertility = 0
    fert_parts = _safe_list([soc, nitrogen, cec])
    if fert_parts:
        # rough normalised average
        fertility = _clamp(
            ((soc or 0) / 5 * 30 + (nitrogen or 0) / 2 * 30 +
             (cec or 0) / 40 * 40),
            0, 100,
        )

    # Temperature
    safe_max = _safe_list(daily_max)
    safe_min = _safe_list(daily_min)
    safe_precip = _safe_list(daily_precip)
    temp_max = max(safe_max) if safe_max else (temp_now + 5 if temp_now is not None else None)
    temp_min = min(safe_min) if safe_min else (temp_now - 5 if temp_now is not None else None)
    precip_total = sum(safe_precip) if safe_precip else 0
    annual_precip_est = precip_total * (365 / max(len(safe_precip), 1)) if safe_precip else None

    # Climate zone estimate
    if temp_now is not None and annual_precip_est is not None:
        if (temp_min or 0) >= 18 and annual_precip_est > 1500:
            climate_zone = "Tropical"
        elif annual_precip_est < 250:
            climate_zone = "Arid / Desert"
        elif annual_precip_est < 500:
            climate_zone = "Semi-Arid"
        elif (temp_min or 0) >= -3:
            climate_zone = "Temperate"
        elif (temp_min or -20) < -3:
            climate_zone = "Continental"
        else:
            climate_zone = "Unclassified"
    else:
        climate_zone = "Insufficient Data"

    # Water
    water_types = {}
    for el in elements_water:
        tags = el.get("tags", {})
        wt = tags.get("natural", tags.get("waterway", tags.get("man_made", "other")))
        water_types[wt] = water_types.get(wt, 0) + 1
    total_water = len(elements_water)
    water_score = _clamp(total_water * 5, 0, 100)

    # Terrain type
    if elev_range > 500:
        terrain_type = "Mountainous"
    elif elev_range > 200:
        terrain_type = "Hilly"
    elif elev_range > 50:
        terrain_type = "Rolling"
    elif center_elev < 5:
        terrain_type = "Coastal / Low-Lying"
    else:
        terrain_type = "Flat / Plain"

    # Infrastructure
    road_count = 0
    building_count = 0
    service_count = 0
    for el in elements_infra:
        tags = el.get("tags", {})
        if "highway" in tags:
            road_count += 1
        elif "building" in tags:
            building_count += 1
        elif "amenity" in tags or "shop" in tags:
            service_count += 1

    # Seismic
    mags = _safe_list([f.get("properties", {}).get("mag") for f in features_eq])
    eq_count = len(features_eq)
    max_mag = max(mags) if mags else 0
    eq_distances = []
    for f in features_eq:
        coords = f.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            dlat = math.radians(coords[1] - lat)
            dlon = math.radians(coords[0] - lon)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(coords[1])) *
                 math.sin(dlon / 2) ** 2)
            dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            eq_distances.append(dist_km)
    min_eq_dist = min(eq_distances) if eq_distances else None

    # Protected areas
    prot_count = len(elements_prot)

    # -- 4. Section scores -------------------------------------------------
    # Each score is 0-100

    # 4a. Location Profile
    loc_score = _clamp(60 + (20 if terrain_type not in ("Flat / Plain",) else 0)
                       + min(center_elev / 50, 20), 0, 100)

    # 4b. Climate Assessment
    if temp_now is not None:
        climate_score = _clamp(
            50 + (25 if 10 <= (temp_now or 15) <= 28 else 0)
            + (25 if (annual_precip_est or 500) > 300 else 0),
            0, 100,
        )
    else:
        climate_score = 30

    # 4c. Soil Profile
    soil_score = _clamp(fertility, 0, 100) if fertility else 20

    # 4d. Water Resources
    water_res_score = water_score

    # 4e. Biodiversity
    total_species = inat_total + gbif_total
    bio_score = _clamp(min(total_species, 500) / 5, 0, 100)

    # 4f. Seismic Activity (lower is better for safety; invert for scoring)
    if eq_count == 0:
        seismic_score = 95
    else:
        seismic_score = _clamp(100 - (max_mag / 9 * 60) - min(eq_count / 50, 1) * 40,
                               0, 100)

    # 4g. Infrastructure
    infra_score = _clamp(
        min(road_count, 100) / 100 * 40 +
        min(building_count, 200) / 200 * 40 +
        min(service_count, 20) / 20 * 20,
        0, 100,
    )

    # 4h. Protection Status
    prot_score = _clamp(prot_count * 20, 0, 100)

    # 4i. Risk Summary (aggregate; lower risk = higher score)
    seismic_risk = _clamp((max_mag / 9 * 60 + min(eq_count / 50, 1) * 40), 0, 100)
    flood_risk = _clamp(total_water / 30 * 50 + max(0, (50 - center_elev) / 50) * 30
                        + max(0, (10 - elev_range) / 10) * 20, 0, 100)
    wildfire_risk = _clamp(
        (kingdom_counts.get("Plantae", 0) + kingdom_counts.get("forest", 0)) / 20 * 50
        + max(0, elev_range - 50) / 200 * 50,
        0, 100,
    )
    top_risks = sorted([
        ("Seismic", round(seismic_risk, 1)),
        ("Flood", round(flood_risk, 1)),
        ("Wildfire", round(wildfire_risk, 1)),
    ], key=lambda x: x[1], reverse=True)[:3]
    risk_avg = sum(r[1] for r in top_risks) / max(len(top_risks), 1)
    risk_section_score = _clamp(100 - risk_avg, 0, 100)

    # 4j. Opportunities
    agri_opp = _clamp(fertility * 0.6
                      + (25 if (annual_precip_est or 0) > 400 else 0)
                      + (15 if 5 < (temp_now or 15) < 35 else 0),
                      0, 100)
    energy_opp = _clamp(
        (30 if (wind or 0) > 15 else (wind or 0) / 15 * 30)
        + (35 if center_elev > 200 else center_elev / 200 * 35)
        + (35 if total_water > 5 else total_water / 5 * 35),
        0, 100,
    )
    tourism_opp = _clamp(
        min(prot_count * 15, 30)
        + (20 if terrain_type in ("Mountainous", "Hilly") else 10)
        + min(total_species / 10, 30)
        + (20 if 15 <= (temp_now or 15) <= 30 else 10),
        0, 100,
    )
    top_opps = sorted([
        ("Agriculture", round(agri_opp, 1)),
        ("Energy", round(energy_opp, 1)),
        ("Tourism", round(tourism_opp, 1)),
    ], key=lambda x: x[1], reverse=True)[:3]
    opp_avg = sum(o[1] for o in top_opps) / max(len(top_opps), 1)
    opp_section_score = _clamp(opp_avg, 0, 100)

    # -- 5. Sections dict --------------------------------------------------
    sections = {
        "Location Profile": {
            "score": round(loc_score),
            "metrics": {
                "Coordinates": f"{lat:.4f}, {lon:.4f}",
                "Elevation": f"{center_elev:.0f} m",
                "Terrain": terrain_type,
            },
            "analysis": (
                f"Target located at {lat:.4f}N, {lon:.4f}E at an elevation of "
                f"{center_elev:.0f} m. Terrain classified as {terrain_type} with "
                f"an elevation range of {elev_range:.0f} m across the survey grid."
            ),
        },
        "Climate Assessment": {
            "score": round(climate_score),
            "metrics": {
                "Temperature": f"{temp_now:.1f} C" if temp_now is not None else "N/A",
                "Temp Range": (f"{temp_min:.1f} - {temp_max:.1f} C"
                               if temp_min is not None and temp_max is not None
                               else "N/A"),
                "Climate Zone": climate_zone,
            },
            "analysis": (
                f"Current temperature {temp_now:.1f} C. " if temp_now is not None else "Temperature data unavailable. "
            ) + (
                f"Estimated annual precipitation {annual_precip_est:.0f} mm. "
                if annual_precip_est is not None else ""
            ) + f"Climate zone estimate: {climate_zone}.",
        },
        "Soil Profile": {
            "score": round(soil_score),
            "metrics": {
                "Texture": texture,
                "pH": f"{ph:.1f}" if ph is not None else "N/A",
                "Organic Matter": f"{soc:.1f} g/kg" if soc is not None else "N/A",
            },
            "analysis": (
                f"Surface soil classified as {texture}. "
                + (f"pH {ph:.1f} " if ph is not None else "pH unknown ")
                + (f"with organic carbon {soc:.1f} g/kg. " if soc is not None else ". ")
                + f"Estimated fertility score: {fertility:.0f}/100."
            ),
        },
        "Water Resources": {
            "score": round(water_res_score),
            "metrics": {
                "Total Features": str(total_water),
                "Feature Types": ", ".join(f"{k}: {v}" for k, v in
                                           sorted(water_types.items(),
                                                  key=lambda x: x[1],
                                                  reverse=True)[:4]) or "None",
                "Availability Score": f"{water_score}/100",
            },
            "analysis": (
                f"{total_water} water features detected within survey radius. "
                + (f"Types include {', '.join(water_types.keys())}. " if water_types else "")
                + f"Water availability score: {water_score}/100."
            ),
        },
        "Biodiversity": {
            "score": round(bio_score),
            "metrics": {
                "Total Observations": str(inat_total + gbif_total),
                "Kingdoms": str(len(kingdom_counts)),
                "Species Richness": str(gbif_unique),
            },
            "analysis": (
                f"{inat_total} iNaturalist observations and {gbif_total} GBIF records. "
                f"{gbif_unique} unique species identified across "
                f"{len(kingdom_counts)} kingdoms. "
                + (f"Dominant group: {max(kingdom_counts, key=kingdom_counts.get)}."
                   if kingdom_counts else "No dominant group identified.")
            ),
        },
        "Seismic Activity": {
            "score": round(seismic_score),
            "metrics": {
                "Earthquakes (1yr)": str(eq_count),
                "Max Magnitude": f"{max_mag:.1f}" if mags else "None",
                "Nearest Event": f"{min_eq_dist:.1f} km" if min_eq_dist is not None else "N/A",
            },
            "analysis": (
                f"{eq_count} seismic events recorded in past year"
                + (f" with maximum magnitude {max_mag:.1f}." if mags else ".")
                + (f" Nearest event at {min_eq_dist:.1f} km." if min_eq_dist is not None else "")
                + (" Seismic risk is low." if seismic_score > 70 else
                   " Elevated seismic activity detected." if seismic_score < 40 else
                   " Moderate seismic activity.")
            ),
        },
        "Infrastructure": {
            "score": round(infra_score),
            "metrics": {
                "Roads": str(road_count),
                "Buildings": str(building_count),
                "Services": str(service_count),
            },
            "analysis": (
                f"Infrastructure survey: {road_count} road segments, "
                f"{building_count} buildings, {service_count} service points. "
                + ("Highly developed area." if infra_score > 70 else
                   "Moderately developed." if infra_score > 35 else
                   "Limited infrastructure present.")
            ),
        },
        "Protection Status": {
            "score": round(prot_score),
            "metrics": {
                "Protected Areas": str(prot_count),
                "Coverage": "High" if prot_count > 3 else ("Moderate" if prot_count > 0 else "None"),
            },
            "analysis": (
                f"{prot_count} protected or nature reserve areas identified. "
                + ("Significant environmental protection in place." if prot_count > 3 else
                   "Some protected areas present." if prot_count > 0 else
                   "No designated protected areas found in survey radius.")
            ),
        },
        "Risk Summary": {
            "score": round(risk_section_score),
            "metrics": {k: f"{v}/100" for k, v in top_risks},
            "analysis": (
                "Top risks: "
                + ", ".join(f"{r[0]} ({r[1]}/100)" for r in top_risks)
                + ". "
                + ("Overall risk profile is low." if risk_avg < 25 else
                   "Moderate risk factors present." if risk_avg < 50 else
                   "Elevated risk profile -- caution advised.")
            ),
            "risks": top_risks,
        },
        "Opportunities": {
            "score": round(opp_section_score),
            "metrics": {k: f"{v}/100" for k, v in top_opps},
            "analysis": (
                "Top opportunities: "
                + ", ".join(f"{o[0]} ({o[1]}/100)" for o in top_opps)
                + ". "
                + ("Strong multi-sector potential." if opp_avg > 60 else
                   "Selective opportunities available." if opp_avg > 30 else
                   "Limited opportunity indicators.")
            ),
            "opportunities": top_opps,
        },
    }

    # -- 6. Overall grade --------------------------------------------------
    all_scores = [s["score"] for s in sections.values()]
    overall = sum(all_scores) / max(len(all_scores), 1)

    if overall >= 90:
        grade = "A+"
    elif overall >= 83:
        grade = "A"
    elif overall >= 78:
        grade = "A-"
    elif overall >= 73:
        grade = "B+"
    elif overall >= 68:
        grade = "B"
    elif overall >= 63:
        grade = "B-"
    elif overall >= 58:
        grade = "C+"
    elif overall >= 53:
        grade = "C"
    elif overall >= 48:
        grade = "C-"
    elif overall >= 43:
        grade = "D+"
    elif overall >= 38:
        grade = "D"
    elif overall >= 33:
        grade = "D-"
    else:
        grade = "F"

    grade_color = _GRADE_COLORS.get(grade, "#8b97b0")

    # -- 7. Key findings (top 5 by impact) ---------------------------------
    key_findings = []
    if eq_count > 20 or max_mag > 5:
        key_findings.append(
            f"High seismic activity: {eq_count} events, max M{max_mag:.1f}"
        )
    if prot_count > 0:
        key_findings.append(
            f"{prot_count} protected area(s) in proximity"
        )
    if total_species > 100:
        key_findings.append(
            f"Rich biodiversity: {total_species} total records, {gbif_unique} unique species"
        )
    if total_water > 10:
        key_findings.append(
            f"Abundant water resources: {total_water} features detected"
        )
    if terrain_type == "Mountainous":
        key_findings.append(
            f"Mountainous terrain with {elev_range:.0f} m elevation range"
        )
    if infra_score > 60:
        key_findings.append(
            f"Well-developed infrastructure: {building_count} buildings, {road_count} roads"
        )
    if climate_zone not in ("Insufficient Data", "Unclassified"):
        key_findings.append(f"Climate classification: {climate_zone}")
    if fertility > 60:
        key_findings.append(f"High soil fertility score: {fertility:.0f}/100")
    elif fertility < 20 and clay is not None:
        key_findings.append(f"Low soil fertility: {fertility:.0f}/100")
    if total_water == 0:
        key_findings.append("No water features detected -- potential water scarcity")
    key_findings = key_findings[:5]

    # -- 8. Critical alerts ------------------------------------------------
    critical_alerts = []
    if max_mag >= 6:
        critical_alerts.append(
            f"SEISMIC ALERT: Magnitude {max_mag:.1f} event recorded within survey area"
        )
    if seismic_risk > 70:
        critical_alerts.append("HIGH SEISMIC RISK: Significant earthquake activity detected")
    if flood_risk > 70:
        critical_alerts.append("FLOOD RISK: Low elevation combined with high water feature density")
    if center_elev < 2:
        critical_alerts.append("ELEVATION WARNING: Location at near-sea-level elevation")

    # -- 9. Quick metrics --------------------------------------------------
    quick_metrics = {
        "Elevation": f"{center_elev:.0f}m",
        "Temperature": f"{temp_now:.1f}C" if temp_now is not None else "N/A",
        "Humidity": f"{humidity}%" if humidity is not None else "N/A",
        "Species": str(inat_total + gbif_total),
        "Water Feat.": str(total_water),
        "Earthquakes": str(eq_count),
        "Buildings": str(building_count),
        "Protected": str(prot_count),
    }

    return {
        "grade": grade,
        "grade_color": grade_color,
        "sections": sections,
        "key_findings": key_findings,
        "critical_alerts": critical_alerts,
        "quick_metrics": quick_metrics,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _score_badge_html(score):
    """Return a small coloured badge for a section score."""
    if score >= 75:
        bg = "#064e3b"
        fg = "#10b981"
    elif score >= 50:
        bg = "#422006"
        fg = "#f59e0b"
    elif score >= 25:
        bg = "#431407"
        fg = "#f97316"
    else:
        bg = "#450a0a"
        fg = "#ef4444"
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:10px;font-weight:700;font-size:13px;">'
        f'{score}/100</span>'
    )


def render_geo_intelligence_tab():
    """Render the Geospatial Intelligence Summary tab."""

    # -- Header ------------------------------------------------------------
    st.markdown(
        f'<div style="background:{_BG_DARK};border:1px solid {_BORDER};'
        f'border-radius:12px;padding:18px 24px;margin-bottom:16px;">'
        f'<h4 style="color:{_TEXT_PRIMARY};margin:0;">Geospatial Intelligence Summary</h4>'
        f'<p style="color:{_TEXT_SECONDARY};margin:4px 0 0 0;font-size:13px;">'
        f'Comprehensive one-page intelligence briefing combining all available '
        f'data sources into an actionable summary.</p></div>',
        unsafe_allow_html=True,
    )

    # -- Location selector -------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.5, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="geoint_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with col_lat:
        lat = st.number_input("Latitude", value=default_lat, format="%.5f",
                              min_value=-90.0, max_value=90.0,
                              key="geoint_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=default_lon, format="%.5f",
                              min_value=-180.0, max_value=180.0,
                              key="geoint_lon")

    run = st.button("Generate Intelligence Briefing", type="primary",
                    key="geoint_run", use_container_width=True)

    if not run:
        st.info("Select a location and click **Generate Intelligence Briefing** "
                "to produce a full geospatial intelligence report.")
        return

    # -- Compute -----------------------------------------------------------
    with st.spinner("Collecting multi-source intelligence data ..."):
        report = compute_geo_intelligence(lat, lon)

    grade = report["grade"]
    grade_color = report["grade_color"]
    sections = report["sections"]
    key_findings = report["key_findings"]
    critical_alerts = report["critical_alerts"]
    quick_metrics = report["quick_metrics"]

    # -- Intelligence Grade header -----------------------------------------
    st.markdown(
        f'<div style="background:{_BG_DARK};border:2px solid {grade_color};'
        f'border-radius:16px;padding:28px;text-align:center;margin:12px 0 20px 0;">'
        f'<div style="font-size:14px;color:{_TEXT_SECONDARY};letter-spacing:2px;'
        f'text-transform:uppercase;margin-bottom:6px;">Intelligence Grade</div>'
        f'<div style="font-size:72px;font-weight:900;color:{grade_color};'
        f'line-height:1;">{grade}</div>'
        f'<div style="font-size:13px;color:{_TEXT_SECONDARY};margin-top:8px;">'
        f'{lat:.4f}N, {lon:.4f}E &mdash; '
        f'{datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # -- Key findings ------------------------------------------------------
    if key_findings:
        st.markdown(
            f'<div style="color:{_TEXT_PRIMARY};font-weight:700;font-size:15px;'
            f'margin-bottom:6px;">KEY FINDINGS</div>',
            unsafe_allow_html=True,
        )
        for idx, finding in enumerate(key_findings, 1):
            st.markdown(
                f'<div style="background:{_BG_CARD};border-left:3px solid {_ACCENT};'
                f'padding:10px 14px;margin:4px 0;border-radius:0 8px 8px 0;'
                f'color:{_TEXT_PRIMARY};font-size:13px;">'
                f'<strong style="color:{_ACCENT};">#{idx}</strong> &nbsp; {finding}</div>',
                unsafe_allow_html=True,
            )

    # -- Critical alerts ---------------------------------------------------
    if critical_alerts:
        st.markdown(
            f'<div style="color:{_ALERT_RED};font-weight:700;font-size:15px;'
            f'margin:14px 0 6px 0;">CRITICAL ALERTS</div>',
            unsafe_allow_html=True,
        )
        for alert in critical_alerts:
            st.markdown(
                f'<div style="background:rgba(239,68,68,0.12);'
                f'border-left:3px solid {_ALERT_RED};padding:10px 14px;'
                f'margin:4px 0;border-radius:0 8px 8px 0;color:{_ALERT_RED};'
                f'font-size:13px;font-weight:600;">{alert}</div>',
                unsafe_allow_html=True,
            )

    # -- 10 Section expanders ----------------------------------------------
    st.markdown("---")
    st.markdown(
        f'<div style="color:{_TEXT_PRIMARY};font-weight:700;font-size:15px;'
        f'margin-bottom:8px;">SECTION ANALYSIS</div>',
        unsafe_allow_html=True,
    )

    for section_name, data in sections.items():
        score = data["score"]
        badge = _score_badge_html(score)
        with st.expander(f"{section_name}  --  Score: {score}/100", expanded=False):
            st.markdown(badge, unsafe_allow_html=True)

            metrics = data.get("metrics", {})
            metric_keys = list(metrics.keys())
            if metric_keys:
                cols = st.columns(min(len(metric_keys), 3))
                for i, key in enumerate(metric_keys):
                    with cols[i % len(cols)]:
                        st.metric(key, metrics[key])

            analysis_text = data.get("analysis", "")
            if analysis_text:
                st.markdown(
                    f'<div style="color:{_TEXT_SECONDARY};font-size:13px;'
                    f'margin-top:8px;line-height:1.6;">{analysis_text}</div>',
                    unsafe_allow_html=True,
                )

            # Show risk / opportunity bars when present
            if "risks" in data:
                for rname, rval in data["risks"]:
                    pct = min(rval, 100)
                    bar_color = "#ef4444" if rval > 50 else ("#f59e0b" if rval > 25 else "#10b981")
                    st.markdown(
                        f'<div style="margin:4px 0;">'
                        f'<span style="color:{_TEXT_SECONDARY};font-size:12px;">'
                        f'{rname}</span>'
                        f'<div style="background:#1a2235;border-radius:6px;'
                        f'height:12px;margin-top:2px;">'
                        f'<div style="width:{pct:.0f}%;background:{bar_color};'
                        f'height:100%;border-radius:6px;"></div></div></div>',
                        unsafe_allow_html=True,
                    )

            if "opportunities" in data:
                for oname, oval in data["opportunities"]:
                    pct = min(oval, 100)
                    bar_color = "#10b981" if oval > 60 else ("#06b6d4" if oval > 30 else "#64748b")
                    st.markdown(
                        f'<div style="margin:4px 0;">'
                        f'<span style="color:{_TEXT_SECONDARY};font-size:12px;">'
                        f'{oname}</span>'
                        f'<div style="background:#1a2235;border-radius:6px;'
                        f'height:12px;margin-top:2px;">'
                        f'<div style="width:{pct:.0f}%;background:{bar_color};'
                        f'height:100%;border-radius:6px;"></div></div></div>',
                        unsafe_allow_html=True,
                    )

    # -- Quick metrics row -------------------------------------------------
    st.markdown("---")
    st.markdown(
        f'<div style="color:{_TEXT_PRIMARY};font-weight:700;font-size:15px;'
        f'margin-bottom:8px;">QUICK METRICS</div>',
        unsafe_allow_html=True,
    )
    qm_keys = list(quick_metrics.keys())
    qm_cols = st.columns(len(qm_keys))
    for i, key in enumerate(qm_keys):
        with qm_cols[i]:
            st.metric(key, quick_metrics[key])

    # -- Radar chart of section scores -------------------------------------
    st.markdown("---")
    st.markdown(
        f'<div style="color:{_TEXT_PRIMARY};font-weight:700;font-size:15px;'
        f'margin-bottom:8px;">OVERALL ASSESSMENT RADAR</div>',
        unsafe_allow_html=True,
    )

    radar_names = list(sections.keys())
    radar_scores = [sections[n]["score"] for n in radar_names]
    # Close the polygon
    radar_names_closed = radar_names + [radar_names[0]]
    radar_scores_closed = radar_scores + [radar_scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_scores_closed,
        theta=radar_names_closed,
        fill="toself",
        fillcolor="rgba(16,185,129,0.18)",
        line=dict(color="#10b981", width=2),
        marker=dict(size=6, color="#10b981"),
        name="Section Scores",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=_BG_DARK,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color=_TEXT_SECONDARY, size=9),
                gridcolor=_SLATE,
            ),
            angularaxis=dict(
                tickfont=dict(color=_TEXT_PRIMARY, size=10),
                gridcolor=_SLATE,
            ),
        ),
        paper_bgcolor=_BG_DARK,
        plot_bgcolor=_BG_DARK,
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True, key="geoint_pchart1")

    # -- Summary recommendation --------------------------------------------
    st.markdown("---")
    all_scores = [sections[n]["score"] for n in sections]
    avg_score = sum(all_scores) / max(len(all_scores), 1)
    strongest = max(sections, key=lambda n: sections[n]["score"])
    weakest = min(sections, key=lambda n: sections[n]["score"])

    if avg_score >= 70:
        verdict = (
            "This location exhibits a strong overall profile with favorable "
            "conditions across most assessment categories."
        )
    elif avg_score >= 45:
        verdict = (
            "This location presents a mixed profile with notable strengths "
            "and areas requiring further investigation."
        )
    else:
        verdict = (
            "This location shows significant limitations across multiple "
            "assessment categories. Targeted field verification recommended."
        )

    recommendation = (
        f"{verdict} "
        f"Strongest dimension: **{strongest}** (score {sections[strongest]['score']}/100). "
        f"Weakest dimension: **{weakest}** (score {sections[weakest]['score']}/100). "
        f"Overall average score: **{avg_score:.0f}/100** (Grade **{grade}**)."
    )

    st.markdown(
        f'<div style="background:{_BG_DARK};border:1px solid {_BORDER};'
        f'border-radius:12px;padding:18px 24px;margin-top:4px;">'
        f'<div style="color:{_ACCENT};font-weight:700;font-size:14px;'
        f'margin-bottom:8px;letter-spacing:1px;">RECOMMENDATION</div>'
        f'<div style="color:{_TEXT_PRIMARY};font-size:13px;line-height:1.7;">'
        f'{recommendation}</div></div>',
        unsafe_allow_html=True,
    )
