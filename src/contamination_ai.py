"""
Contamination Risk AI module for TerraScout AI.
Estimates soil and water contamination risk based on land use,
industrial proximity, and environmental factors.
Uses Overpass API, ISRIC SoilGrids, Open-Meteo, and Open-Elevation
(all free, no API key required).
"""

import math
import logging
from html import escape

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
)

logger = logging.getLogger(__name__)

# ==============================================================================
# THEME CONSTANTS
# ==============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"
CLR_ACCENT = "#84cc16"       # toxic green

CLR_SAFE = "#22c55e"         # green  (< 3)
CLR_WARNING = "#f59e0b"      # amber  (3 - 6)
CLR_DANGER = "#ef4444"       # red    (> 6)
CLR_CRITICAL = "#991b1b"     # dark red (> 8)

# ==============================================================================
# CONTAMINANT TYPES
# ==============================================================================

CONTAMINANT_TYPES = {
    "heavy_metals": {"name": "Heavy Metals", "color": "#a855f7", "icon": "flask"},
    "hydrocarbons": {"name": "Hydrocarbons", "color": "#f97316", "icon": "fire"},
    "pesticides": {"name": "Pesticides", "color": "#84cc16", "icon": "leaf"},
    "industrial_waste": {"name": "Industrial Waste", "color": "#ef4444", "icon": "industry"},
    "sewage": {"name": "Sewage", "color": "#78716c", "icon": "tint"},
    "radioactive": {"name": "Radioactive", "color": "#eab308", "icon": "bolt"},
}

INDEX_LABELS = {
    "Industrial Contamination": {
        "icon": "industry",
        "desc": "Proximity to industrial and commercial sites",
    },
    "Agricultural Runoff": {
        "icon": "leaf",
        "desc": "Farmland extent and fertiliser indicators",
    },
    "Traffic Pollution": {
        "icon": "road",
        "desc": "Road density and traffic-related pollutants",
    },
    "Waste/Landfill": {
        "icon": "trash",
        "desc": "Proximity to landfill and dump sites",
    },
    "Water Contamination": {
        "icon": "tint",
        "desc": "Contamination sources near water features",
    },
    "Soil Contamination": {
        "icon": "globe",
        "desc": "Accumulation potential from all sources",
    },
}

# ==============================================================================
# HELPERS
# ==============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def _risk_color(score: float) -> str:
    if score > 8:
        return CLR_CRITICAL
    if score > 6:
        return CLR_DANGER
    if score >= 3:
        return CLR_WARNING
    return CLR_SAFE


def _risk_class(score: float) -> str:
    if score > 8:
        return "Critical"
    if score > 6:
        return "High"
    if score >= 3:
        return "Moderate"
    if score >= 1:
        return "Low"
    return "Minimal"


def _safe_values(lst):
    """Return list with None values filtered out."""
    return [v for v in (lst or []) if v is not None]


# ==============================================================================
# CORE COMPUTATION
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_contamination_risk(lat: float, lon: float) -> dict:
    """
    Compute contamination risk assessment for a location.

    Returns dict with: overall_risk, risk_class, indices,
    source_inventory, pathway_assessment, vulnerable_receptors,
    remediation_recommendations.
    """

    # -- Fetch all data sources ------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)

    # -- Parse infrastructure --------------------------------------------------
    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])

    industrial_sites = []
    fuel_stations = []
    landfills = []
    quarries = []
    farmlands = []
    roads = []
    residential_areas = []

    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        landuse = tags.get("landuse", "")
        amenity = tags.get("amenity", "")
        highway = tags.get("highway", "")

        if landuse in ("industrial", "commercial"):
            industrial_sites.append(el)
        if amenity == "fuel":
            fuel_stations.append(el)
        if landuse == "landfill":
            landfills.append(el)
        if landuse == "quarry":
            quarries.append(el)
        if landuse == "farmland":
            farmlands.append(el)
        if highway and highway not in ("footway", "path", "cycleway", "steps"):
            roads.append(el)
        if landuse == "residential":
            residential_areas.append(el)

    # -- Parse soil data -------------------------------------------------------
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers_list = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _layer in (_layers_list if isinstance(_layers_list, list) else []):
        _lname = _layer.get("name", "") if isinstance(_layer, dict) else ""
        if _lname:
            _layer_map[_lname] = _layer

    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay")
    sand_pct = _sv("sand")
    soc_val = _sv("soc")
    ph_val = _sv("phh2o")

    # -- Parse water features --------------------------------------------------
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    rivers = [w for w in water_elements
              if (w.get("tags", {}) if isinstance(w, dict) else {}).get("waterway") in ("river", "stream")]
    springs_wells = [w for w in water_elements
                     if (w.get("tags", {}) if isinstance(w, dict) else {}).get("natural") == "spring"
                     or (w.get("tags", {}) if isinstance(w, dict) else {}).get("man_made") == "water_well"]

    # -- Parse elevation -------------------------------------------------------
    center_elev = 0.0
    slope_factor = 0.0
    if elevation and isinstance(elevation, dict):
        center_elev = elevation.get("center_elevation", 0.0) or 0.0
        ns_profile = elevation.get("ns_profile", [])
        ew_profile = elevation.get("ew_profile", [])
        ns_elevs = [p.get("elevation") for p in (ns_profile if isinstance(ns_profile, list) else []) if isinstance(p, dict)]
        ew_elevs = [p.get("elevation") for p in (ew_profile if isinstance(ew_profile, list) else []) if isinstance(p, dict)]
        all_elevs = _safe_values(ns_elevs + ew_elevs)
        if len(all_elevs) >= 2:
            elev_range = max(all_elevs) - min(all_elevs)
            slope_factor = min(10.0, elev_range / 50.0 * 10.0)

    # -- Parse weather (rainfall) ----------------------------------------------
    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    precip_sums = _safe_values(daily.get("precipitation_sum", []))
    avg_precip = sum(precip_sums) / len(precip_sums) if precip_sums else 0.0
    rainfall_factor = min(10.0, avg_precip / 8.0 * 10.0)

    # ======================================================================
    # SOURCE IDENTIFICATION
    # ======================================================================
    source_inventory = []

    if industrial_sites:
        source_inventory.append({
            "type": "Industrial/Commercial",
            "count": len(industrial_sites),
            "contaminants": ["heavy_metals", "hydrocarbons", "industrial_waste"],
            "severity": min(10, len(industrial_sites) * 2),
        })
    if fuel_stations:
        source_inventory.append({
            "type": "Fuel Stations",
            "count": len(fuel_stations),
            "contaminants": ["hydrocarbons"],
            "severity": min(8, len(fuel_stations) * 3),
        })
    if landfills:
        source_inventory.append({
            "type": "Landfills / Dumps",
            "count": len(landfills),
            "contaminants": ["industrial_waste", "heavy_metals", "sewage"],
            "severity": min(10, len(landfills) * 4),
        })
    if quarries:
        source_inventory.append({
            "type": "Mining / Quarries",
            "count": len(quarries),
            "contaminants": ["heavy_metals", "radioactive"],
            "severity": min(9, len(quarries) * 3),
        })
    if farmlands:
        source_inventory.append({
            "type": "Agricultural Runoff",
            "count": len(farmlands),
            "contaminants": ["pesticides"],
            "severity": min(7, len(farmlands) * 1.5),
        })
    if roads:
        road_severity = min(6, len(roads) * 0.3)
        major = [r for r in roads
                 if (r.get("tags", {}) if isinstance(r, dict) else {}).get("highway")
                 in ("motorway", "trunk", "primary")]
        if major:
            road_severity = min(8, road_severity + len(major) * 1.5)
        source_inventory.append({
            "type": "Traffic / Roads",
            "count": len(roads),
            "contaminants": ["hydrocarbons", "heavy_metals"],
            "severity": round(road_severity, 1),
        })

    # ======================================================================
    # PATHWAY ANALYSIS
    # ======================================================================
    pathway_assessment = []

    # Water pathways
    if rivers:
        pathway_assessment.append({
            "pathway": "Surface Water Transport",
            "description": f"{len(rivers)} rivers/streams detected that can carry contaminants downstream.",
            "risk_modifier": min(3.0, len(rivers) * 0.8),
        })

    # Soil permeability
    if sand_pct is not None and clay_pct is not None:
        if sand_pct > 5:
            pathway_assessment.append({
                "pathway": "High Soil Permeability",
                "description": f"Sandy soil ({sand_pct:.0f}%) allows fast contaminant migration to groundwater.",
                "risk_modifier": min(3.0, sand_pct / 20.0),
            })
        if clay_pct > 3:
            pathway_assessment.append({
                "pathway": "Clay Accumulation",
                "description": f"Clay content ({clay_pct:.0f}%) retains contaminants near the surface.",
                "risk_modifier": min(2.0, clay_pct / 20.0),
            })

    # Slope
    if slope_factor > 2:
        pathway_assessment.append({
            "pathway": "Slope Runoff",
            "description": f"Terrain slope (factor {slope_factor:.1f}) facilitates contaminant flow downhill.",
            "risk_modifier": min(2.5, slope_factor / 4.0),
        })

    # Rainfall
    if avg_precip > 2:
        pathway_assessment.append({
            "pathway": "Rainfall Washout",
            "description": f"Average precipitation ({avg_precip:.1f} mm/day) washes contaminants into water bodies.",
            "risk_modifier": min(2.0, avg_precip / 5.0),
        })

    # ======================================================================
    # RECEPTOR VULNERABILITY
    # ======================================================================
    vulnerable_receptors = []

    if springs_wells:
        vulnerable_receptors.append({
            "receptor": "Water Sources",
            "detail": f"{len(springs_wells)} springs/wells at risk of contamination.",
            "severity": "High" if source_inventory else "Moderate",
        })

    if residential_areas and source_inventory:
        vulnerable_receptors.append({
            "receptor": "Residential Areas",
            "detail": f"{len(residential_areas)} residential zones near contamination sources.",
            "severity": "High",
        })

    if rivers and source_inventory:
        vulnerable_receptors.append({
            "receptor": "River Ecosystems",
            "detail": f"{len(rivers)} watercourses exposed to upstream contamination.",
            "severity": "Moderate",
        })

    # ======================================================================
    # COMPUTE 6 RISK INDICES (0 - 10)
    # ======================================================================

    # 1. Industrial Contamination
    ind_score = min(10.0, len(industrial_sites) * 2.5 + len(fuel_stations) * 1.5)
    ind_score = _clamp(ind_score)

    # 2. Agricultural Runoff
    agr_score = min(10.0, len(farmlands) * 1.8)
    if soc_val is not None and soc_val > 3:
        agr_score = min(10.0, agr_score + 1.5)
    if ph_val is not None and ph_val < 5.5:
        agr_score = min(10.0, agr_score + 1.0)
    agr_score = _clamp(agr_score)

    # 3. Traffic Pollution
    major_roads = [r for r in roads
                   if (r.get("tags", {}) if isinstance(r, dict) else {}).get("highway")
                   in ("motorway", "trunk", "primary", "secondary")]
    trf_score = min(10.0, len(roads) * 0.3 + len(major_roads) * 1.5)
    trf_score = _clamp(trf_score)

    # 4. Waste / Landfill
    wst_score = min(10.0, len(landfills) * 5.0 + len(quarries) * 2.0)
    wst_score = _clamp(wst_score)

    # 5. Water Contamination
    source_count = len(industrial_sites) + len(landfills) + len(fuel_stations)
    water_nearby = len(rivers) + len(springs_wells)
    wat_score = 0.0
    if source_count > 0 and water_nearby > 0:
        wat_score = min(10.0, source_count * 1.5 + water_nearby * 1.0 + rainfall_factor * 0.3)
    elif water_nearby > 0:
        wat_score = min(4.0, rainfall_factor * 0.4)
    wat_score = _clamp(wat_score)

    # 6. Soil Contamination
    pathway_mod = sum(p.get("risk_modifier", 0) for p in pathway_assessment)
    all_source_severity = _safe_values([s.get("severity") for s in source_inventory])
    max_sev = max(all_source_severity) if all_source_severity else 0
    soil_score = min(10.0, max_sev * 0.5 + pathway_mod * 0.6)
    if clay_pct is not None and clay_pct > 4:
        soil_score = min(10.0, soil_score + 1.5)
    soil_score = _clamp(soil_score)

    indices = {
        "Industrial Contamination": round(ind_score, 1),
        "Agricultural Runoff": round(agr_score, 1),
        "Traffic Pollution": round(trf_score, 1),
        "Waste/Landfill": round(wst_score, 1),
        "Water Contamination": round(wat_score, 1),
        "Soil Contamination": round(soil_score, 1),
    }

    # -- Overall risk (weighted) -----------------------------------------------
    weights = {
        "Industrial Contamination": 2.0,
        "Agricultural Runoff": 1.3,
        "Traffic Pollution": 1.0,
        "Waste/Landfill": 2.0,
        "Water Contamination": 1.8,
        "Soil Contamination": 1.5,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(indices[k] * weights[k] for k in indices)
    overall = round(weighted_sum / total_weight, 1)
    overall = _clamp(overall)

    # -- Remediation recommendations -------------------------------------------
    remediation = []
    if ind_score >= 6:
        remediation.append(
            "INDUSTRIAL ZONE: Conduct soil and groundwater sampling near industrial sites. "
            "Install monitoring wells and consider phytoremediation buffers."
        )
    elif ind_score >= 3:
        remediation.append(
            "Industrial Advisory: Monitor runoff from commercial/industrial areas. "
            "Establish vegetated buffer strips to intercept contaminants."
        )

    if agr_score >= 6:
        remediation.append(
            "AGRICULTURAL ALERT: High fertiliser/pesticide runoff risk. "
            "Implement riparian buffer zones and controlled drainage systems."
        )
    elif agr_score >= 3:
        remediation.append(
            "Agricultural Advisory: Consider integrated pest management and "
            "precision fertiliser application to reduce runoff."
        )

    if wst_score >= 6:
        remediation.append(
            "WASTE HAZARD: Proximity to landfill or dump sites detected. "
            "Monitor leachate migration and install groundwater barriers."
        )
    elif wst_score >= 3:
        remediation.append(
            "Waste Advisory: Monitor surface drainage near waste sites. "
            "Ensure landfill liner integrity assessments are current."
        )

    if wat_score >= 6:
        remediation.append(
            "WATER CONTAMINATION: Sources detected near water features. "
            "Implement source control and consider activated carbon filtration."
        )
    elif wat_score >= 3:
        remediation.append(
            "Water Advisory: Periodic water quality testing recommended "
            "for nearby springs, wells, and watercourses."
        )

    if soil_score >= 6:
        remediation.append(
            "SOIL REMEDIATION NEEDED: Elevated accumulation potential. "
            "Consider soil excavation, bioremediation, or capping strategies."
        )
    elif soil_score >= 3:
        remediation.append(
            "Soil Advisory: Monitor heavy metal and organic compound levels. "
            "Maintain vegetative cover to reduce erosion and contaminant spread."
        )

    if not remediation:
        remediation.append(
            "Overall contamination risk appears low. Continue routine "
            "environmental monitoring and maintain best management practices."
        )

    return {
        "overall_risk": overall,
        "risk_class": _risk_class(overall),
        "indices": indices,
        "source_inventory": source_inventory,
        "pathway_assessment": pathway_assessment,
        "vulnerable_receptors": vulnerable_receptors,
        "remediation_recommendations": remediation,
    }


# ==============================================================================
# CHART BUILDERS
# ==============================================================================

def _build_radar_chart(indices: dict) -> go.Figure:
    """Create a plotly radar chart for the six contamination indices."""
    categories = list(indices.keys())
    values = list(indices.values())
    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(132,204,22,0.15)",
        line={"color": CLR_ACCENT, "width": 2.5},
        marker={"size": 6, "color": CLR_ACCENT},
        name="Risk Index",
        hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>",
    ))

    fig.update_layout(
        polar={
            "bgcolor": CLR_SURFACE,
            "radialaxis": {
                "visible": True,
                "range": [0, 10],
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
            },
            "angularaxis": {
                "gridcolor": "#2a3550",
                "tickfont": {"color": CLR_TEXT, "size": 11},
            },
        },
        title={
            "text": "Contamination Risk Profile",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=420,
        margin=dict(l=60, r=60, t=60, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
        showlegend=False,
    )
    return fig


# ==============================================================================
# RENDER TAB
# ==============================================================================

def render_contamination_tab():
    """Render the Contamination Risk AI tab in the Streamlit UI."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_ACCENT};font-size:26px;">
                Contamination Risk AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Estimates soil and water contamination risk from land use,
                industrial proximity, and environmental pathways.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="contam_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="contam_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="contam_lon",
        )

    run_btn = st.button(
        "Assess Contamination Risk",
        type="primary",
        key="contam_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Assess Contamination Risk** to begin.")
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching environmental data and computing contamination risk..."):
        result = compute_contamination_risk(lat, lon)

    overall = result["overall_risk"]
    rc = result["risk_class"]
    r_color = _risk_color(overall)
    indices = result["indices"]
    sources = result["source_inventory"]
    pathways = result["pathway_assessment"]
    receptors = result["vulnerable_receptors"]
    remediation = result["remediation_recommendations"]

    # -- Overall risk header ---------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{r_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {r_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};
                                 text-transform:uppercase;letter-spacing:1px;">
                        Overall Contamination Risk
                    </span>
                    <h1 style="margin:4px 0;color:{r_color};font-size:42px;">
                        {overall}/10
                    </h1>
                    <span style="font-size:18px;color:{r_color};font-weight:600;">
                        {escape(rc)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Sources found: {len(sources)}<br>
                        Pathways identified: {len(pathways)}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- 6 index cards ---------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Contamination Indices
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    idx_keys = list(indices.keys())
    row1_keys = idx_keys[:3]
    row2_keys = idx_keys[3:]

    for row_keys in (row1_keys, row2_keys):
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            score_val = indices[key]
            s_color = _risk_color(score_val)
            s_class = _risk_class(score_val)
            meta = INDEX_LABELS.get(key, {"icon": "info", "desc": ""})
            bar_width = max(5, score_val / 10 * 100)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:180px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            {escape(key)}
                        </div>
                        <div style="font-size:32px;font-weight:700;color:{s_color};">
                            {score_val}
                        </div>
                        <div style="font-size:12px;color:{s_color};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_class)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color};width:{bar_width}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:6px;">
                            {escape(meta['desc'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar chart -----------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    radar_fig = _build_radar_chart(indices)
    st.plotly_chart(radar_fig, use_container_width=True, key="contam_radar")

    # -- Source inventory ------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Source Inventory
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if sources:
        for src in sources:
            sev = src.get("severity", 0)
            sev_color = _risk_color(sev)
            contam_names = ", ".join(
                CONTAMINANT_TYPES.get(c, {}).get("name", c)
                for c in src.get("contaminants", [])
            )
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {sev_color}44;
                            border-left:4px solid {sev_color};
                            border-radius:8px;padding:14px 18px;margin:8px 0;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;flex-wrap:wrap;">
                        <div>
                            <span style="color:{CLR_TEXT};font-size:15px;font-weight:600;">
                                {escape(str(src.get('type', 'Unknown')))}
                            </span>
                            <span style="color:{CLR_TEXT_SEC};font-size:13px;margin-left:12px;">
                                Count: {src.get('count', 0)}
                            </span>
                        </div>
                        <span style="color:{sev_color};font-weight:700;font-size:16px;">
                            {sev}/10
                        </span>
                    </div>
                    <div style="color:{CLR_TEXT_SEC};font-size:12px;margin-top:6px;">
                        Contaminants: {escape(contam_names)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {CLR_BORDER};
                        border-radius:8px;padding:14px 18px;margin:8px 0;
                        color:{CLR_TEXT_SEC};font-size:14px;">
                No significant contamination sources detected in this area.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Pathway assessment ----------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Pathway Assessment
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if pathways:
        for pw in pathways:
            mod = pw.get("risk_modifier", 0)
            mod_color = CLR_WARNING if mod >= 1.5 else CLR_TEXT_SEC
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {CLR_BORDER};
                            border-radius:8px;padding:14px 18px;margin:8px 0;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;flex-wrap:wrap;">
                        <span style="color:{CLR_ACCENT};font-size:14px;font-weight:600;">
                            {escape(str(pw.get('pathway', '')))}
                        </span>
                        <span style="color:{mod_color};font-size:13px;">
                            Risk modifier: +{mod:.1f}
                        </span>
                    </div>
                    <div style="color:{CLR_TEXT_SEC};font-size:13px;margin-top:6px;">
                        {escape(str(pw.get('description', '')))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {CLR_BORDER};
                        border-radius:8px;padding:14px 18px;margin:8px 0;
                        color:{CLR_TEXT_SEC};font-size:14px;">
                No significant contamination pathways identified.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Vulnerable receptors --------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Vulnerable Receptors
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if receptors:
        for rec in receptors:
            sev_text = rec.get("severity", "Low")
            alert_color = CLR_DANGER if sev_text == "High" else CLR_WARNING
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {alert_color}44;
                            border-left:4px solid {alert_color};
                            border-radius:8px;padding:14px 18px;margin:8px 0;">
                    <div style="display:flex;align-items:flex-start;gap:12px;">
                        <span style="color:{alert_color};font-size:18px;margin-top:2px;">
                            &#9888;
                        </span>
                        <div>
                            <span style="color:{CLR_TEXT};font-size:14px;font-weight:600;">
                                {escape(str(rec.get('receptor', '')))}
                            </span>
                            <span style="color:{alert_color};font-size:12px;margin-left:10px;">
                                [{escape(sev_text)}]
                            </span>
                            <div style="color:{CLR_TEXT_SEC};font-size:13px;margin-top:4px;">
                                {escape(str(rec.get('detail', '')))}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {CLR_SAFE}44;
                        border-radius:8px;padding:14px 18px;margin:8px 0;
                        color:{CLR_TEXT_SEC};font-size:14px;">
                No vulnerable receptors identified in the immediate area.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Remediation recommendations -------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Remediation Recommendations
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for rem in remediation:
        is_alert = any(rem.startswith(kw) for kw in (
            "INDUSTRIAL ZONE", "AGRICULTURAL ALERT", "WASTE HAZARD",
            "WATER CONTAMINATION", "SOIL REMEDIATION",
        ))
        card_border = CLR_DANGER if is_alert else CLR_BORDER
        icon_color = CLR_DANGER if is_alert else CLR_ACCENT
        icon_char = "&#9888;" if is_alert else "&#9432;"
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {card_border};
                        border-left:4px solid {card_border};
                        border-radius:8px;padding:14px 18px;margin:8px 0;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="color:{icon_color};font-size:18px;margin-top:2px;">
                        {icon_char}
                    </span>
                    <span style="color:{CLR_TEXT};font-size:14px;line-height:1.5;">
                        {escape(rem)}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Footer ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="text-align:center;padding:16px;margin-top:20px;
                    color:{CLR_TEXT_SEC};font-size:12px;">
            Contamination Risk AI powered by ISRIC SoilGrids, Open-Meteo,
            Open-Elevation, and OpenStreetMap Overpass API.
            Risk scores are indicative and should supplement professional site assessments.
        </div>
        """,
        unsafe_allow_html=True,
    )
