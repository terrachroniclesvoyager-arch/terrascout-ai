"""
Water Quality Intelligence AI module for TerraScout AI.
Estimates water quality indicators using soil composition, weather patterns,
land use, terrain data, and hydrological features from free APIs.
No API key required.
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

CLR_WATER_DARK = "#1e3a5f"
CLR_WATER_MID = "#2563eb"
CLR_WATER_LIGHT = "#60a5fa"
CLR_WATER_ACCENT = "#38bdf8"

CLR_EXCELLENT = "#22c55e"
CLR_GOOD = "#60a5fa"
CLR_FAIR = "#f59e0b"
CLR_POOR = "#ef4444"
CLR_HAZARDOUS = "#991b1b"

# ==============================================================================
# WATER QUALITY PARAMETERS
# ==============================================================================

WATER_QUALITY_PARAMS = {
    "pH": {
        "name": "pH Level",
        "unit": "pH",
        "color": "#06b6d4",
        "ideal_range": (6.5, 8.5),
        "description": "Acidity/alkalinity balance; ideal range 6.5-8.5 for aquatic life",
    },
    "Turbidity": {
        "name": "Turbidity",
        "unit": "NTU",
        "color": "#a78bfa",
        "ideal_range": (0, 5),
        "description": "Water clarity indicator; lower is better for drinking water",
    },
    "Dissolved Oxygen": {
        "name": "Dissolved Oxygen",
        "unit": "mg/L",
        "color": "#34d399",
        "ideal_range": (6, 14),
        "description": "Oxygen available for aquatic organisms; higher is healthier",
    },
    "Nitrate": {
        "name": "Nitrate",
        "unit": "mg/L",
        "color": "#fbbf24",
        "ideal_range": (0, 10),
        "description": "Nutrient from agriculture runoff; excess causes algal blooms",
    },
    "Phosphate": {
        "name": "Phosphate",
        "unit": "mg/L",
        "color": "#f472b6",
        "ideal_range": (0, 0.1),
        "description": "Urbanization and fertilizer indicator; excess causes eutrophication",
    },
    "Heavy Metals": {
        "name": "Heavy Metal Risk",
        "unit": "index",
        "color": "#94a3b8",
        "ideal_range": (0, 0.05),
        "description": "Industrial contamination proxy from land use and geology",
    },
    "Bacterial": {
        "name": "Bacterial Safety",
        "unit": "index",
        "color": "#fb923c",
        "ideal_range": (0, 200),
        "description": "Microbial contamination risk from population density",
    },
    "Salinity": {
        "name": "Salinity",
        "unit": "ppt",
        "color": "#818cf8",
        "ideal_range": (0, 0.5),
        "description": "Dissolved salt concentration; affected by coastal proximity and climate",
    },
}


# ==============================================================================
# HELPERS
# ==============================================================================

def _clamp(value, lo=0.0, hi=100.0):
    return max(lo, min(hi, value))


def _safe_mean(values):
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _quality_color(score):
    """Return hex color for a 0-100 quality score."""
    if score > 80:
        return CLR_EXCELLENT
    if score > 60:
        return CLR_GOOD
    if score > 40:
        return CLR_FAIR
    if score > 20:
        return CLR_POOR
    return CLR_HAZARDOUS


def _classify_wqi(score):
    """Return (label, color) for a 0-100 WQI score."""
    if score > 80:
        return "Excellent", CLR_EXCELLENT
    if score > 60:
        return "Good", CLR_GOOD
    if score > 40:
        return "Fair", CLR_FAIR
    if score > 20:
        return "Poor", CLR_POOR
    return "Hazardous", CLR_HAZARDOUS


# ==============================================================================
# COMPUTE WATER QUALITY
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_water_quality(lat, lon):
    """
    Compute water quality estimates for a geographic location.

    Returns a dict with:
        wqi             - overall Water Quality Index (0-100)
        classification  - Excellent / Good / Fair / Poor / Hazardous
        class_color     - hex color for the classification
        parameter_scores - dict of 8 individual quality scores (0-100)
        risk_factors    - list of identified risk factor strings
        water_sources   - dict with springs, rivers, wetlands counts
        recommendations - list of recommendation strings
    """
    # -- Fetch all data sources ------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)

    # -- Parse soil properties -------------------------------------------------
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soil_ph = _sv("phh2o", 10)          # pH * 10 -> actual pH
    soil_nitrogen = _sv("nitrogen", 100)  # cg/kg -> g/kg
    soil_clay = _sv("clay", 10)          # g/kg -> %
    soil_sand = _sv("sand", 10)
    soil_soc = _sv("soc", 10)           # dg/kg -> g/kg

    # -- Parse weather ---------------------------------------------------------
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    temp_c = current.get("temperature_2m", 15.0) or 15.0
    precip_mm = current.get("precipitation", 0.0) or 0.0
    humidity = current.get("relative_humidity_2m", 50.0) or 50.0

    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    precip_sums = daily.get("precipitation_sum", [])
    avg_precip = _safe_mean(precip_sums)

    # -- Parse elevation -------------------------------------------------------
    elev_data = elevation if isinstance(elevation, dict) else {}
    center_elev = elev_data.get("center_elevation", 0.0) or 0.0
    min_elev = elev_data.get("min_elevation", 0.0) or 0.0
    max_elev = elev_data.get("max_elevation", 0.0) or 0.0
    slope_range = max_elev - min_elev

    # -- Parse water features --------------------------------------------------
    elements = (water if isinstance(water, dict) else {}).get("elements", [])
    springs, rivers, wetlands = 0, 0, 0
    for el in (elements if isinstance(elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if tags.get("natural") == "spring":
            springs += 1
        elif tags.get("waterway") in ("river", "stream", "canal"):
            rivers += 1
        elif tags.get("natural") == "water" or tags.get("waterway") == "riverbank":
            wetlands += 1

    total_water = springs + rivers + wetlands

    # -- Parse infrastructure / land use ---------------------------------------
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    buildings, farmland_count, industrial_count, residential_count = 0, 0, 0, 0
    for el in (infra_elements if isinstance(infra_elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if tags.get("building"):
            buildings += 1
        lu = tags.get("landuse", "")
        if lu in ("farmland", "farm", "meadow", "orchard", "vineyard"):
            farmland_count += 1
        if lu in ("industrial", "quarry", "landfill"):
            industrial_count += 1
        if lu in ("residential", "commercial", "retail"):
            residential_count += 1

    # =========================================================================
    # Estimate 8 water quality parameters (0-100 quality score each)
    # =========================================================================
    risk_factors = []

    # 1. pH Quality: from soil pH proxy, adjusted by precipitation acidity
    if soil_ph is not None:
        ph_dev = abs(soil_ph - 7.0)
        ph_quality = _clamp(100 - ph_dev * 25)
        if avg_precip > 10:
            ph_quality = _clamp(ph_quality - 8)  # acid rain proxy
    else:
        ph_quality = 65.0  # neutral assumption
    if ph_quality < 50:
        risk_factors.append("Soil pH indicates potential water acidity/alkalinity issues")

    # 2. Turbidity Quality: inverse of erosion risk (slope + rainfall + exposed soil)
    erosion_slope = min(40.0, slope_range / 5.0)
    erosion_rain = min(30.0, avg_precip * 3.0)
    exposed_soil = 0.0
    if soil_sand is not None and soil_sand > 50:
        exposed_soil = min(20.0, (soil_sand - 50) * 1.0)
    if soil_clay is not None and soil_clay < 10:
        exposed_soil += 10.0
    turbidity_quality = _clamp(100 - erosion_slope - erosion_rain - exposed_soil)
    if turbidity_quality < 50:
        risk_factors.append("High erosion risk contributes to water turbidity")

    # 3. Dissolved Oxygen: higher in cold, flowing water, elevation, water features
    do_temp = _clamp(30 - (temp_c - 5) * 1.2, 0, 30)
    do_flow = min(30.0, total_water * 10.0)
    do_elev = min(20.0, center_elev / 100.0 * 5.0)
    do_base = 20.0
    do_quality = _clamp(do_base + do_temp + do_flow + do_elev)
    if do_quality < 50:
        risk_factors.append("Warm temperatures and low water flow reduce dissolved oxygen")

    # 4. Nitrate Quality: inverse of agricultural intensity
    farm_intensity = min(50.0, farmland_count * 5.0)
    nitrogen_factor = 0.0
    if soil_nitrogen is not None:
        nitrogen_factor = min(30.0, soil_nitrogen * 10.0)
    precip_runoff = min(20.0, avg_precip * 2.0)
    nitrate_quality = _clamp(100 - farm_intensity - nitrogen_factor - precip_runoff)
    if nitrate_quality < 50:
        risk_factors.append("Agricultural land use elevates nitrate contamination risk")

    # 5. Phosphate Quality: inverse of urbanization + soil phosphorus proxy
    urban_factor = min(40.0, residential_count * 2.0)
    building_factor = min(30.0, buildings / 10.0)
    soc_factor = 0.0
    if soil_soc is not None:
        soc_factor = min(20.0, soil_soc * 2.0)
    phosphate_quality = _clamp(100 - urban_factor - building_factor - soc_factor)
    if phosphate_quality < 50:
        risk_factors.append("Urban density increases phosphate runoff into water sources")

    # 6. Heavy Metal Risk: industrial proximity + geological factors
    ind_factor = min(60.0, industrial_count * 15.0)
    clay_geology = 0.0
    if soil_clay is not None and soil_clay > 30:
        clay_geology = min(20.0, (soil_clay - 30) * 2.0)
    heavy_metal_quality = _clamp(100 - ind_factor - clay_geology)
    if heavy_metal_quality < 50:
        risk_factors.append("Industrial land use nearby increases heavy metal contamination risk")

    # 7. Bacterial Quality: population density proxy + water treatment indicator
    pop_proxy = min(50.0, (buildings + residential_count * 3) * 1.5)
    stagnant_penalty = 0.0
    if total_water == 0:
        stagnant_penalty = 15.0
    elif rivers == 0 and springs == 0:
        stagnant_penalty = 10.0
    temp_penalty = max(0.0, (temp_c - 20) * 1.5)
    bacterial_quality = _clamp(100 - pop_proxy - stagnant_penalty - min(20.0, temp_penalty))
    if bacterial_quality < 50:
        risk_factors.append("Population density and warm temperatures increase bacterial risk")

    # 8. Salinity: coastal proximity estimate + climate (evaporation)
    coastal_proxy = 0.0
    if center_elev < 10:
        coastal_proxy = 40.0
    elif center_elev < 50:
        coastal_proxy = 25.0
    elif center_elev < 100:
        coastal_proxy = 10.0
    evap_factor = 0.0
    if temp_c > 25 and humidity < 40:
        evap_factor = min(30.0, (temp_c - 25) * 3.0)
    salinity_quality = _clamp(100 - coastal_proxy - evap_factor)
    if salinity_quality < 50:
        risk_factors.append("Low elevation and high evaporation suggest elevated salinity")

    # =========================================================================
    # Overall Water Quality Index (weighted average)
    # =========================================================================
    parameter_scores = {
        "pH": round(ph_quality, 1),
        "Turbidity": round(turbidity_quality, 1),
        "Dissolved Oxygen": round(do_quality, 1),
        "Nitrate": round(nitrate_quality, 1),
        "Phosphate": round(phosphate_quality, 1),
        "Heavy Metals": round(heavy_metal_quality, 1),
        "Bacterial": round(bacterial_quality, 1),
        "Salinity": round(salinity_quality, 1),
    }

    weights = {
        "pH": 1.2,
        "Turbidity": 1.0,
        "Dissolved Oxygen": 1.5,
        "Nitrate": 1.3,
        "Phosphate": 1.1,
        "Heavy Metals": 1.4,
        "Bacterial": 1.5,
        "Salinity": 1.0,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(parameter_scores[k] * weights[k] for k in parameter_scores)
    wqi = round(weighted_sum / total_weight, 1)

    classification, class_color = _classify_wqi(wqi)

    # =========================================================================
    # Recommendations
    # =========================================================================
    recommendations = []

    if wqi > 80:
        recommendations.append(
            "Water quality conditions appear excellent. Continue routine monitoring "
            "and maintain current land management practices."
        )
    elif wqi > 60:
        recommendations.append(
            "Water quality is generally good. Monitor nutrient levels periodically "
            "and address any emerging contamination sources."
        )
    elif wqi > 40:
        recommendations.append(
            "Water quality is fair. Consider implementing buffer zones around water "
            "bodies and reducing agricultural chemical inputs nearby."
        )
    elif wqi > 20:
        recommendations.append(
            "WATER QUALITY WARNING: Poor conditions detected. Investigate contamination "
            "sources, implement water treatment measures, and restrict untreated use."
        )
    else:
        recommendations.append(
            "WATER QUALITY ALERT: Hazardous conditions estimated. Water is likely unsafe "
            "without extensive treatment. Identify and remediate pollution sources urgently."
        )

    if nitrate_quality < 50:
        recommendations.append(
            "Reduce nitrate loading by establishing riparian buffer strips and "
            "optimizing fertilizer application schedules on surrounding farmland."
        )
    if bacterial_quality < 50:
        recommendations.append(
            "Address bacterial contamination risk by improving wastewater management "
            "and ensuring livestock are excluded from waterways."
        )
    if heavy_metal_quality < 50:
        recommendations.append(
            "Monitor heavy metal concentrations with laboratory testing. Consider "
            "remediation of industrial discharge points upstream."
        )
    if turbidity_quality < 50:
        recommendations.append(
            "Reduce erosion-driven turbidity by planting ground cover on slopes "
            "and implementing sediment traps near water courses."
        )

    water_sources = {
        "springs": springs,
        "rivers": rivers,
        "wetlands": wetlands,
        "total": total_water,
    }

    return {
        "wqi": wqi,
        "classification": classification,
        "class_color": class_color,
        "parameter_scores": parameter_scores,
        "risk_factors": risk_factors,
        "water_sources": water_sources,
        "recommendations": recommendations,
    }


# ==============================================================================
# CHART BUILDERS
# ==============================================================================

def _build_radar_chart(scores):
    """Build a radar (spider) chart of 8 water quality parameters."""
    params = list(scores.keys())
    values = list(scores.values())
    colors = [WATER_QUALITY_PARAMS[p]["color"] for p in params]

    # Close the polygon
    params_closed = params + [params[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=params_closed,
        fill="toself",
        fillcolor="rgba(96,165,250,0.15)",
        line={"color": CLR_WATER_LIGHT, "width": 2.5},
        marker={"color": colors + [colors[0]], "size": 8},
        name="Quality Score",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))

    fig.update_layout(
        polar={
            "bgcolor": CLR_SURFACE,
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
                "gridcolor": "#2a3550",
            },
            "angularaxis": {
                "tickfont": {"color": CLR_TEXT, "size": 11},
                "gridcolor": "#2a3550",
            },
        },
        showlegend=False,
        height=420,
        margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
    )
    return fig


# ==============================================================================
# RENDER
# ==============================================================================

def render_water_quality_tab():
    """Render the Water Quality Intelligence tab in the Streamlit UI."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_WATER_DARK});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Water Quality Intelligence AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Estimates water quality from soil composition, weather patterns,
                land use, terrain, and hydrological features.
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
            key="wqi_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="wqi_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="wqi_lon",
        )

    run_btn = st.button(
        "Assess Water Quality",
        type="primary",
        key="wqi_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Assess Water Quality** to begin.")
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching environmental data and estimating water quality..."):
        result = compute_water_quality(lat, lon)

    wqi = result["wqi"]
    classification = result["classification"]
    class_color = result["class_color"]
    scores = result["parameter_scores"]
    risk_factors = result["risk_factors"]
    water_sources = result["water_sources"]
    recommendations = result["recommendations"]

    # -- WQI header ------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{class_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {class_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};text-transform:uppercase;
                                 letter-spacing:1px;">Water Quality Index</span>
                    <h1 style="margin:4px 0;color:{class_color};font-size:48px;">
                        {wqi}/100
                    </h1>
                    <span style="font-size:18px;color:{class_color};font-weight:600;">
                        {escape(classification)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Water Sources: {water_sources['total']} detected<br>
                        Parameters: 8 assessed
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Parameter gauge cards (4 columns x 2 rows) ----------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Parameter Quality Scores
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    param_keys = list(scores.keys())
    row1_keys = param_keys[:4]
    row2_keys = param_keys[4:]

    for row_keys in (row1_keys, row2_keys):
        cols = st.columns(4)
        for col, key in zip(cols, row_keys):
            score_val = scores[key]
            s_color = _quality_color(score_val)
            meta = WATER_QUALITY_PARAMS.get(key, {})
            param_color = meta.get("color", CLR_WATER_LIGHT)
            bar_width = max(5, score_val)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {param_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:190px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:4px;">
                            {escape(meta.get('name', key))}
                        </div>
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            ({escape(meta.get('unit', ''))})
                        </div>
                        <div style="font-size:34px;font-weight:700;color:{s_color};">
                            {score_val}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:10px 0 6px;">
                            <div style="background:{s_color};width:{bar_width}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};line-height:1.3;">
                            {escape(meta.get('description', ''))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar chart -----------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Quality Profile Radar
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="wqi_radar")

    # -- Water sources section -------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Detected Water Sources
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ws_cols = st.columns(3)
    ws_items = [
        ("Springs", water_sources["springs"], "#38bdf8"),
        ("Rivers / Streams", water_sources["rivers"], "#2563eb"),
        ("Wetlands / Water Bodies", water_sources["wetlands"], "#06b6d4"),
    ]
    for col, (label, count, color) in zip(ws_cols, ws_items):
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {color}44;
                            border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:13px;color:{CLR_TEXT_SEC};">{escape(label)}</div>
                    <div style="font-size:36px;font-weight:700;color:{color};margin:6px 0;">
                        {count}
                    </div>
                    <div style="font-size:11px;color:{CLR_TEXT_SEC};">
                        within 5 km radius
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Risk factors section --------------------------------------------------
    if risk_factors:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:20px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    Identified Risk Factors
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for rf in risk_factors:
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {CLR_POOR}44;
                            border-left:4px solid {CLR_POOR};
                            border-radius:8px;padding:12px 16px;margin:6px 0;">
                    <span style="color:{CLR_POOR};font-weight:600;font-size:13px;">
                        WARNING:
                    </span>
                    <span style="color:{CLR_TEXT};font-size:13px;">
                        {escape(rf)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Recommendations section -----------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Recommendations
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for rec in recommendations:
        is_alert = "ALERT" in rec or "WARNING" in rec
        card_border = CLR_POOR if is_alert else CLR_BORDER
        icon_color = CLR_POOR if is_alert else CLR_WATER_ACCENT

        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {card_border};
                        border-left:4px solid {card_border};
                        border-radius:8px;padding:12px 16px;margin:6px 0;">
                <span style="color:{icon_color};font-size:13px;">
                    {escape(rec)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
