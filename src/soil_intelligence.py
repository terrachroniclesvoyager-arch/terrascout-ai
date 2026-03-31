"""
Soil Intelligence AI module for TerraScout AI.
Provides deep soil analysis using SoilGrids data with agricultural
interpretation: texture classification (USDA triangle), fertility index,
drainage, compaction risk, erosion vulnerability, carbon sequestration
potential, nutrient retention, and water holding capacity.
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_elevation_grid,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SOIL_COLORS = {
    "primary": "#92400e",
    "secondary": "#b45309",
    "accent": "#d97706",
    "bg": "#1a1a2e",
    "card": "rgba(26,26,46,0.85)",
    "border": "#3d2e1a",
    "text": "#e8ecf4",
    "muted": "#8b97b0",
}

_SCORE_META = {
    "Fertility Index": {"icon": "leaf", "color": "#10b981"},
    "Drainage Class": {"icon": "droplet", "color": "#3b82f6"},
    "Compaction Risk": {"icon": "compress", "color": "#ef4444"},
    "Erosion Vulnerability": {"icon": "wind", "color": "#f59e0b"},
    "Carbon Sequestration": {"icon": "tree", "color": "#059669"},
    "Nutrient Retention": {"icon": "flask", "color": "#8b5cf6"},
    "Water Holding Cap.": {"icon": "tint", "color": "#06b6d4"},
    "pH Balance": {"icon": "balance-scale", "color": "#ec4899"},
}


# ---------------------------------------------------------------------------
# Helpers to extract SoilGrids values
# ---------------------------------------------------------------------------

def _soil_value(props: dict, name: str, div: float = 10.0):
    """Return the top-layer mean for a given soil property, or None."""
    layers = props.get("layers", [])
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            depths = layer.get("depths", [])
            if depths:
                raw = depths[0].get("values", {}).get("mean")
                if raw is not None:
                    return raw / div
    return None


def _soil_depth_profile(props: dict, name: str, div: float = 10.0) -> list:
    """Return list of {'depth': label, 'value': v} dicts for every layer."""
    layers = props.get("layers", [])
    target = None
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            target = layer
            break
    if target is None:
        return []
    result = []
    for d in target.get("depths", []):
        label = d.get("label", "?")
        raw = d.get("values", {}).get("mean")
        val = raw / div if raw is not None else None
        result.append({"depth": label, "value": val})
    return result


# ---------------------------------------------------------------------------
# USDA Soil Texture Classification
# ---------------------------------------------------------------------------

def _classify_texture(clay: float, sand: float, silt: float) -> str:
    """USDA soil texture triangle classification."""
    if clay is None or sand is None or silt is None:
        return "Unknown"
    # normalise percentages
    total = clay + sand + silt
    if total <= 0:
        return "Unknown"
    c = clay / total * 100
    sa = sand / total * 100
    si = silt / total * 100

    if c >= 40 and sa <= 45 and si <= 40:
        return "Clay"
    if c >= 27 and sa <= 20 and si >= 40:
        return "Silty Clay"
    if c >= 35 and sa >= 45:
        return "Sandy Clay"
    if 27 <= c < 40 and 20 < sa <= 45:
        return "Clay Loam"
    if 27 <= c < 40 and si >= 40:
        return "Silty Clay Loam"
    if 20 <= c < 35 and sa >= 45 and si < 28:
        return "Sandy Clay Loam"
    if si >= 80 and c < 12:
        return "Silt"
    if 50 <= si < 80 and c < 27:
        return "Silt Loam"
    if 7 <= c < 27 and 28 <= si < 50 and sa <= 52:
        return "Loam"
    if sa >= 85:
        return "Sandy"
    if 70 <= sa < 85 and c < 15:
        return "Loamy Sand"
    if c < 20 and si < 50 and sa >= 43:
        return "Sandy Loam"
    return "Loam"


# ---------------------------------------------------------------------------
# Compute scores
# ---------------------------------------------------------------------------

def _ph_score(ph):
    """Score pH on 0-100 scale (optimal 6.0-7.5)."""
    if ph is None:
        return 50
    if 6.0 <= ph <= 7.5:
        return 100
    dist = min(abs(ph - 6.0), abs(ph - 7.5))
    return max(0, 100 - dist * 25)


def _fertility_index(soc, nitrogen, cec, ph):
    """Composite fertility index 0-100."""
    soc_s = min((soc or 0) / 50.0 * 100, 100)
    n_s = min((nitrogen or 0) / 5.0 * 100, 100)
    cec_s = min((cec or 0) / 40.0 * 100, 100)
    ph_s = _ph_score(ph)
    return min(100, round(soc_s * 0.3 + n_s * 0.25 + cec_s * 0.25 + ph_s * 0.2))


def _drainage_score(clay, sand, texture_class):
    """0-100: 100 = very well drained."""
    if texture_class in ("Sandy", "Loamy Sand"):
        return 95
    if texture_class in ("Sandy Loam",):
        return 80
    if texture_class in ("Loam", "Silt Loam"):
        return 60
    if texture_class in ("Clay Loam", "Silty Clay Loam", "Sandy Clay Loam"):
        return 40
    if texture_class in ("Clay", "Silty Clay", "Sandy Clay", "Silt"):
        return 20
    # fallback using clay %
    c = clay or 20
    return max(0, min(100, 100 - c * 2))


def _drainage_label(score):
    if score >= 70:
        return "Well Drained"
    if score >= 40:
        return "Moderately Well"
    return "Poorly Drained"


def _compaction_risk(bdod):
    """0-100 risk based on bulk density (kg/dm3)."""
    if bdod is None:
        return 40
    # typical range 0.8-1.8 kg/dm3; higher = more compacted
    return max(0, min(100, round((bdod - 0.8) / 1.0 * 100)))


def _erosion_vulnerability(silt, slope_pct):
    """0-100: high silt + steep slope = high erosion risk."""
    si = silt if silt is not None else 30
    sl = slope_pct if slope_pct is not None else 2
    silt_factor = min(si / 60.0 * 60, 60)
    slope_factor = min(sl / 15.0 * 40, 40)
    return max(0, min(100, round(silt_factor + slope_factor)))


def _carbon_sequestration(soc, precip_mm, organic_density):
    """0-100 potential: high SOC + moderate precip = good."""
    s = min((soc or 0) / 60.0 * 40, 40)
    p = min((precip_mm or 500) / 1200.0 * 30, 30)
    o = min((organic_density or 0) / 80.0 * 30, 30)
    return max(0, min(100, round(s + p + o)))


def _nutrient_retention(cec, clay, soc):
    """0-100: high CEC + clay + organic matter = high retention."""
    c = min((cec or 0) / 40.0 * 40, 40)
    cl = min((clay or 0) / 50.0 * 30, 30)
    o = min((soc or 0) / 50.0 * 30, 30)
    return max(0, min(100, round(c + cl + o)))


def _water_holding_capacity(clay, silt, soc):
    """0-100 estimate from texture."""
    cl = clay if clay is not None else 20
    si = silt if silt is not None else 30
    oc = soc if soc is not None else 10
    # clay and silt hold more water; organic matter helps
    return max(0, min(100, round(cl * 1.0 + si * 0.5 + oc * 0.3)))


# ---------------------------------------------------------------------------
# Recommendations engine
# ---------------------------------------------------------------------------

def _build_recommendations(scores, texture_class, soil_props):
    recs = []
    fi = scores.get("Fertility Index", 50)
    dr = scores.get("Drainage Class", 50)
    comp = scores.get("Compaction Risk", 50)
    eros = scores.get("Erosion Vulnerability", 50)
    carb = scores.get("Carbon Sequestration", 50)
    nutr = scores.get("Nutrient Retention", 50)
    whc = scores.get("Water Holding Cap.", 50)
    ph_s = scores.get("pH Balance", 50)

    if fi < 40:
        recs.append({
            "title": "Low Fertility Alert",
            "text": "Consider adding organic amendments (compost, manure) and cover crops to boost soil organic matter and nitrogen levels.",
            "priority": "high",
        })
    elif fi >= 75:
        recs.append({
            "title": "Excellent Fertility",
            "text": "This soil has strong natural fertility. Maintain with crop rotation and minimal tillage to preserve organic carbon.",
            "priority": "info",
        })

    if dr < 40:
        recs.append({
            "title": "Drainage Improvement Needed",
            "text": f"The {texture_class} texture indicates poor natural drainage. Consider raised beds, tile drainage, or selecting water-tolerant crops.",
            "priority": "high",
        })

    if comp > 65:
        recs.append({
            "title": "Compaction Risk",
            "text": "High bulk density suggests compaction. Reduce heavy equipment passes, use cover crops with deep taproots (daikon radish), and consider subsoiling.",
            "priority": "medium",
        })

    if eros > 60:
        recs.append({
            "title": "Erosion Mitigation",
            "text": "High silt content and/or slope create erosion risk. Implement contour farming, terracing, cover crops, and buffer strips.",
            "priority": "high",
        })

    if carb > 60:
        recs.append({
            "title": "Carbon Sequestration Opportunity",
            "text": "Conditions favor carbon storage. No-till or reduced-till practices, perennial crops, and biochar application can maximize sequestration.",
            "priority": "info",
        })

    if nutr < 40:
        recs.append({
            "title": "Low Nutrient Retention",
            "text": "Low CEC means applied fertilizers leach quickly. Use slow-release fertilizers, increase organic matter, and consider split applications.",
            "priority": "medium",
        })

    if whc < 35:
        recs.append({
            "title": "Low Water Holding Capacity",
            "text": "Sandy soils dry out fast. Add organic matter, mulch heavily, and consider drip irrigation for efficiency.",
            "priority": "medium",
        })
    elif whc > 75:
        recs.append({
            "title": "High Water Retention",
            "text": "Clay-heavy soils retain water well but risk waterlogging. Ensure adequate drainage and avoid working soil when wet.",
            "priority": "info",
        })

    if ph_s < 50:
        ph_val = soil_props.get("phh2o")
        if ph_val is not None and ph_val < 5.5:
            recs.append({
                "title": "Acidic Soil - Lime Recommended",
                "text": f"pH {ph_val:.1f} is quite acidic. Agricultural lime (CaCO3) can raise pH. Target 6.0-7.0 for most crops.",
                "priority": "medium",
            })
        elif ph_val is not None and ph_val > 8.0:
            recs.append({
                "title": "Alkaline Soil - Amendment Needed",
                "text": f"pH {ph_val:.1f} is alkaline. Sulfur or gypsum amendments can lower pH. Some micronutrients become unavailable above pH 8.",
                "priority": "medium",
            })

    if not recs:
        recs.append({
            "title": "Soil Health is Good",
            "text": "No major concerns detected. Continue monitoring and maintain organic matter levels through good agricultural practices.",
            "priority": "info",
        })

    return recs


# ---------------------------------------------------------------------------
# Cached compute function
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_soil_intelligence(lat: float, lon: float) -> dict:
    """
    Fetch soil, weather and elevation data, then compute comprehensive
    soil intelligence scores and classification.
    """
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    elevation = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)

    # --- extract soil properties ---
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    clay = _soil_value(props, "clay", 10)
    sand = _soil_value(props, "sand", 10)
    silt = _soil_value(props, "silt", 10)
    soc = _soil_value(props, "soc", 10)
    phh2o = _soil_value(props, "phh2o", 10)
    nitrogen = _soil_value(props, "nitrogen", 100)
    bdod = _soil_value(props, "bdod", 100)
    cec = _soil_value(props, "cec", 10)
    cfvo = _soil_value(props, "cfvo", 10)
    ocd = _soil_value(props, "ocd", 10)

    soil_props = {
        "clay": clay, "sand": sand, "silt": silt, "soc": soc,
        "phh2o": phh2o, "nitrogen": nitrogen, "bdod": bdod,
        "cec": cec, "cfvo": cfvo, "ocd": ocd,
    }

    # --- texture classification ---
    texture_class = _classify_texture(clay, sand, silt)

    # --- slope estimate ---
    ns_prof = elevation.get("ns_profile", [])
    if len(ns_prof) >= 2:
        elev_diff = abs(ns_prof[-1].get("elevation", 0) - ns_prof[0].get("elevation", 0))
        from src.deep_zone_analysis import haversine_distance
        dist_km = haversine_distance(
            ns_prof[0].get("lat", lat), ns_prof[0].get("lon", lon),
            ns_prof[-1].get("lat", lat), ns_prof[-1].get("lon", lon),
        )
        slope_pct = (elev_diff / (dist_km * 1000) * 100) if dist_km > 0 else 0
    else:
        slope_pct = 0

    # --- weather summaries ---
    daily = weather.get("daily", {})
    precip_list = daily.get("precipitation_sum", [])
    annual_precip = (
        float(sum(precip_list)) * (365 / max(len(precip_list), 1))
        if precip_list else 500
    )

    # --- scores ---
    fertility = _fertility_index(soc, nitrogen, cec, phh2o)
    drain_score = _drainage_score(clay, sand, texture_class)
    drain_label = _drainage_label(drain_score)
    comp_risk = _compaction_risk(bdod)
    erosion = _erosion_vulnerability(silt, slope_pct)
    carbon = _carbon_sequestration(soc, annual_precip, ocd)
    retention = _nutrient_retention(cec, clay, soc)
    whc = _water_holding_capacity(clay, silt, soc)
    ph_bal = _ph_score(phh2o)

    scores = {
        "Fertility Index": fertility,
        "Drainage Class": drain_score,
        "Compaction Risk": comp_risk,
        "Erosion Vulnerability": erosion,
        "Carbon Sequestration": carbon,
        "Nutrient Retention": retention,
        "Water Holding Cap.": whc,
        "pH Balance": ph_bal,
    }

    # --- depth profiles ---
    depth_profile = []
    for prop_name, div in [("clay", 10), ("sand", 10), ("silt", 10),
                            ("soc", 10), ("phh2o", 10), ("nitrogen", 100),
                            ("bdod", 100), ("cec", 10)]:
        entries = _soil_depth_profile(props, prop_name, div)
        for entry in entries:
            entry["property"] = prop_name
        depth_profile.extend(entries)

    # --- recommendations ---
    recommendations = _build_recommendations(scores, texture_class, soil_props)

    return {
        "texture_class": texture_class,
        "fertility_index": fertility,
        "drainage_label": drain_label,
        "scores": scores,
        "soil_properties": soil_props,
        "recommendations": recommendations,
        "depth_profile": depth_profile,
        "slope_pct": slope_pct,
        "annual_precip": annual_precip,
        "elevation": elevation.get("center_elevation", 0),
    }


# ---------------------------------------------------------------------------
# Render function
# ---------------------------------------------------------------------------

def render_soil_intelligence_tab():
    """Render the Soil Intelligence AI tab in Streamlit."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#92400e 0%,#1a1a2e 100%);'
        'border-radius:14px;padding:18px 24px;margin-bottom:18px;'
        'border:1px solid #b45309;">'
        '<h4 style="color:#fbbf24;margin:0;">Soil Intelligence AI</h4>'
        '<p style="color:#d4c5a9;margin:4px 0 0 0;font-size:14px;">'
        'Deep soil analysis with USDA texture classification, fertility scoring, '
        'and agricultural recommendations powered by SoilGrids data.</p></div>',
        unsafe_allow_html=True,
    )

    # --- Location selector ---
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="soili_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    with c2:
        lat = st.number_input(
            "Latitude", min_value=-90.0, max_value=90.0,
            value=p.get("lat", 41.90) if p else 41.90,
            format="%.5f", key="soili_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0,
            value=p.get("lon", 12.50) if p else 12.50,
            format="%.5f", key="soili_lon",
        )

    run = st.button(
        "Analyze Soil", type="primary",
        key="si_run", use_container_width=True,
    )

    if not run:
        st.info("Select a location and click **Analyze Soil** to begin deep soil intelligence analysis.")
        return

    # --- Compute ---
    with st.spinner("Fetching soil, weather and elevation data..."):
        data = compute_soil_intelligence(lat, lon)

    tex = data["texture_class"]
    fi = data["fertility_index"]
    scores = data["scores"]
    soil_props = data["soil_properties"]
    recs = data["recommendations"]
    depth_prof = data["depth_profile"]

    # ================================================================
    # Texture header
    # ================================================================
    st.markdown(
        f'<div style="background:{_SOIL_COLORS["card"]};border:1px solid '
        f'{_SOIL_COLORS["border"]};border-radius:12px;padding:16px 22px;'
        f'margin:12px 0;text-align:center;">'
        f'<span style="color:{_SOIL_COLORS["accent"]};font-size:14px;">'
        f'USDA Soil Texture Classification</span><br/>'
        f'<span style="color:{_SOIL_COLORS["text"]};font-size:28px;'
        f'font-weight:bold;">{tex}</span><br/>'
        f'<span style="color:{_SOIL_COLORS["muted"]};font-size:12px;">'
        f'Clay {soil_props.get("clay") or 0:.1f}% &bull; '
        f'Sand {soil_props.get("sand") or 0:.1f}% &bull; '
        f'Silt {soil_props.get("silt") or 0:.1f}%</span></div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # Fertility Index gauge (Plotly)
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:18px;">'
        f'Fertility Index</h5>',
        unsafe_allow_html=True,
    )
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fi,
        title={"text": "Fertility Index", "font": {"color": "#e8ecf4", "size": 16}},
        number={"font": {"color": "#fbbf24", "size": 38}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8b97b0",
                     "tickfont": {"color": "#8b97b0"}},
            "bar": {"color": "#d97706"},
            "bgcolor": "#1a1a2e",
            "steps": [
                {"range": [0, 30], "color": "#7f1d1d"},
                {"range": [30, 60], "color": "#92400e"},
                {"range": [60, 80], "color": "#3f6212"},
                {"range": [80, 100], "color": "#166534"},
            ],
            "threshold": {
                "line": {"color": "#fbbf24", "width": 3},
                "thickness": 0.8,
                "value": fi,
            },
        },
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font={"color": "#e8ecf4"},
        height=260,
        margin=dict(t=40, b=10, l=30, r=30),
    )
    st.plotly_chart(fig_gauge, use_container_width=True, key="soiint_pchart1")

    # ================================================================
    # Soil Texture Triangle (ternary plot)
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:12px;">'
        f'Soil Texture Triangle</h5>',
        unsafe_allow_html=True,
    )
    clay_v = soil_props.get("clay") or 0
    sand_v = soil_props.get("sand") or 0
    silt_v = soil_props.get("silt") or 0

    fig_ternary = go.Figure(go.Scatterternary(
        a=[clay_v], b=[sand_v], c=[silt_v],
        mode="markers+text",
        marker=dict(size=16, color="#d97706", line=dict(width=2, color="#fbbf24")),
        text=[tex],
        textposition="top center",
        textfont=dict(color="#fbbf24", size=13),
        name="Sample",
    ))
    fig_ternary.update_layout(
        ternary=dict(
            aaxis=dict(title="Clay %", color="#f59e0b", tickcolor="#8b97b0",
                       tickfont=dict(color="#8b97b0"), title_font=dict(color="#f59e0b")),
            baxis=dict(title="Sand %", color="#ef4444", tickcolor="#8b97b0",
                       tickfont=dict(color="#8b97b0"), title_font=dict(color="#ef4444")),
            caxis=dict(title="Silt %", color="#8b5cf6", tickcolor="#8b97b0",
                       tickfont=dict(color="#8b97b0"), title_font=dict(color="#8b5cf6")),
            bgcolor="#1a1a2e",
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        height=400,
        margin=dict(t=30, b=30, l=50, r=50),
        showlegend=False,
    )
    st.plotly_chart(fig_ternary, use_container_width=True, key="soiint_pchart2")

    # ================================================================
    # 8 Score cards (4 columns x 2 rows)
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:12px;">'
        f'Soil Health Scores</h5>',
        unsafe_allow_html=True,
    )
    score_keys = list(scores.keys())
    for row_start in range(0, 8, 4):
        cols = st.columns(4)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(score_keys):
                break
            key = score_keys[idx]
            val = scores[key]
            meta = _SCORE_META.get(key, {"color": "#06b6d4"})
            color = meta["color"]
            # label for drainage
            extra = ""
            if key == "Drainage Class":
                extra = f"<br/><span style='font-size:11px;'>{data['drainage_label']}</span>"
            level = "Low" if val < 35 else ("Moderate" if val < 65 else "High")
            bar_pct = min(val, 100)
            col.markdown(
                f'<div style="background:{_SOIL_COLORS["card"]};border:1px solid '
                f'{_SOIL_COLORS["border"]};border-radius:10px;padding:12px;'
                f'text-align:center;min-height:120px;">'
                f'<span style="color:{_SOIL_COLORS["muted"]};font-size:11px;">'
                f'{key}</span><br/>'
                f'<span style="color:{color};font-size:26px;font-weight:bold;">'
                f'{val}</span>'
                f'<span style="color:{_SOIL_COLORS["muted"]};font-size:12px;">'
                f'/100</span>{extra}<br/>'
                f'<div style="background:#2a2a3e;border-radius:4px;height:8px;'
                f'margin-top:6px;overflow:hidden;">'
                f'<div style="width:{bar_pct}%;background:{color};height:100%;'
                f'border-radius:4px;"></div></div>'
                f'<span style="color:{_SOIL_COLORS["muted"]};font-size:10px;">'
                f'{level}</span></div>',
                unsafe_allow_html=True,
            )

    # ================================================================
    # Radar chart of all 8 scores
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:18px;">'
        f'Soil Health Radar</h5>',
        unsafe_allow_html=True,
    )
    radar_cats = list(scores.keys())
    radar_vals = [scores[k] for k in radar_cats]
    # close the polygon
    radar_cats_closed = radar_cats + [radar_cats[0]]
    radar_vals_closed = radar_vals + [radar_vals[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_vals_closed,
        theta=radar_cats_closed,
        fill="toself",
        fillcolor="rgba(217,119,6,0.25)",
        line=dict(color="#d97706", width=2),
        marker=dict(size=6, color="#fbbf24"),
        name="Scores",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#3d2e1a", tickcolor="#8b97b0",
                tickfont=dict(color="#8b97b0", size=10),
            ),
            angularaxis=dict(
                gridcolor="#3d2e1a",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        showlegend=False,
        height=420,
        margin=dict(t=30, b=30, l=60, r=60),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="soiint_pchart3")

    # ================================================================
    # Depth profile bar chart
    # ================================================================
    if depth_prof:
        st.markdown(
            f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:18px;">'
            f'Depth Profile</h5>',
            unsafe_allow_html=True,
        )
        depth_order = ["0-5cm", "5-15cm", "15-30cm", "30-60cm",
                       "60-100cm", "100-200cm"]
        prop_colors = {
            "clay": "#f59e0b", "sand": "#ef4444", "silt": "#8b5cf6",
            "soc": "#10b981", "phh2o": "#06b6d4", "nitrogen": "#14b8a6",
            "bdod": "#ec4899", "cec": "#f97316",
        }
        unique_props = list({e["property"] for e in depth_prof})
        fig_depth = go.Figure()
        for prop_name in sorted(unique_props):
            entries = [e for e in depth_prof if e["property"] == prop_name]
            d_map = {e["depth"]: e["value"] for e in entries}
            x_vals = [d for d in depth_order if d in d_map]
            y_vals = [d_map[d] if d_map[d] is not None else 0 for d in x_vals]
            fig_depth.add_trace(go.Bar(
                x=x_vals, y=y_vals, name=prop_name,
                marker_color=prop_colors.get(prop_name, "#8b97b0"),
            ))
        fig_depth.update_layout(
            barmode="group",
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#e8ecf4"),
            xaxis=dict(title="Depth Layer", gridcolor="#3d2e1a",
                       tickfont=dict(color="#8b97b0")),
            yaxis=dict(title="Value", gridcolor="#3d2e1a",
                       tickfont=dict(color="#8b97b0")),
            legend=dict(font=dict(color="#e8ecf4", size=11)),
            height=360,
            margin=dict(t=20, b=40, l=50, r=20),
        )
        st.plotly_chart(fig_depth, use_container_width=True, key="soiint_pchart4")

    # ================================================================
    # Recommendations
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:18px;">'
        f'Agricultural Recommendations</h5>',
        unsafe_allow_html=True,
    )
    priority_colors = {
        "high": "#dc2626",
        "medium": "#f59e0b",
        "info": "#10b981",
    }
    for rec in recs:
        pcolor = priority_colors.get(rec["priority"], "#8b97b0")
        st.markdown(
            f'<div style="background:{_SOIL_COLORS["card"]};'
            f'border-left:4px solid {pcolor};border-radius:0 10px 10px 0;'
            f'padding:12px 16px;margin:8px 0;">'
            f'<span style="color:{pcolor};font-weight:bold;font-size:13px;">'
            f'{rec["title"]}</span><br/>'
            f'<span style="color:{_SOIL_COLORS["text"]};font-size:13px;">'
            f'{rec["text"]}</span></div>',
            unsafe_allow_html=True,
        )

    # ================================================================
    # Raw soil properties metrics row
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SOIL_COLORS["accent"]};margin-top:18px;">'
        f'Raw Soil Properties</h5>',
        unsafe_allow_html=True,
    )
    prop_labels = {
        "clay": ("Clay", "%"),
        "sand": ("Sand", "%"),
        "silt": ("Silt", "%"),
        "soc": ("Organic Carbon", "g/kg"),
        "phh2o": ("pH (H2O)", ""),
        "nitrogen": ("Nitrogen", "g/kg"),
        "bdod": ("Bulk Density", "kg/dm3"),
        "cec": ("CEC", "cmol/kg"),
        "cfvo": ("Coarse Frag.", "%"),
        "ocd": ("OC Density", "kg/m3"),
    }
    mc = st.columns(5)
    for i, (pkey, (plabel, punit)) in enumerate(prop_labels.items()):
        col = mc[i % 5]
        val = soil_props.get(pkey)
        display = f"{val:.2f}" if val is not None else "N/A"
        suffix = f" {punit}" if punit and val is not None else ""
        col.metric(plabel, f"{display}{suffix}")
