"""
Mineral Prospecting AI -- Geological mineral prospecting assessment
combining lithology, tectonics, soil chemistry, and terrain analysis.
Uses: Macrostrat, SoilGrids, Open Topo Data, USGS.
"""

import logging
import math
from datetime import datetime

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_elevation_grid as fetch_elevation_data,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

MINERAL_COMPONENTS = {
    "geological": {"name": "Geological Favorability", "color": "#f59e0b", "weight": 0.25},
    "tectonic": {"name": "Tectonic Activity", "color": "#ef4444", "weight": 0.15},
    "geochemistry": {"name": "Soil Geochemistry", "color": "#22c55e", "weight": 0.20},
    "terrain": {"name": "Terrain Indicators", "color": "#3b82f6", "weight": 0.15},
    "formation_age": {"name": "Formation Age", "color": "#8b5cf6", "weight": 0.15},
    "deposit_prob": {"name": "Deposit Probability", "color": "#ec4899", "weight": 0.10},
}

# Mineral-favorable rock types
FAVORABLE_LITHOLOGIES = {
    "granite": {"minerals": ["gold", "tin", "tungsten", "uranium"], "score": 75},
    "basalt": {"minerals": ["copper", "nickel", "platinum"], "score": 65},
    "gneiss": {"minerals": ["gold", "iron", "garnet"], "score": 70},
    "schist": {"minerals": ["gold", "silver", "copper"], "score": 65},
    "quartzite": {"minerals": ["gold", "uranium"], "score": 60},
    "limestone": {"minerals": ["lead", "zinc", "copper"], "score": 55},
    "sandstone": {"minerals": ["uranium", "copper", "gold"], "score": 50},
    "serpentinite": {"minerals": ["chromium", "nickel", "platinum", "diamonds"], "score": 80},
    "pegmatite": {"minerals": ["lithium", "rare_earths", "beryllium", "tantalum"], "score": 90},
    "kimberlite": {"minerals": ["diamonds"], "score": 95},
    "dolomite": {"minerals": ["lead", "zinc", "magnesium"], "score": 55},
    "volcanic": {"minerals": ["gold", "silver", "copper", "sulfur"], "score": 70},
    "metamorphic": {"minerals": ["gold", "iron", "copper"], "score": 65},
    "igneous": {"minerals": ["copper", "nickel", "iron", "platinum"], "score": 70},
    "sedimentary": {"minerals": ["coal", "oil", "gas", "iron"], "score": 45},
}

# Target mineral types for probability estimation
TARGET_MINERALS = [
    "gold", "copper", "iron", "rare_earths", "lithium", "coal", "uranium", "diamonds",
]

MINERAL_DISPLAY_NAMES = {
    "gold": "Gold (Au)",
    "copper": "Copper (Cu)",
    "iron": "Iron (Fe)",
    "rare_earths": "Rare Earth Elements",
    "lithium": "Lithium (Li)",
    "coal": "Coal",
    "uranium": "Uranium (U)",
    "diamonds": "Diamonds",
}

MINERAL_COLORS = {
    "gold": "#FFD700",
    "copper": "#B87333",
    "iron": "#A0522D",
    "rare_earths": "#9370DB",
    "lithium": "#87CEEB",
    "coal": "#36454F",
    "uranium": "#7FFF00",
    "diamonds": "#B9F2FF",
}

# Geological era ranges (Ma = millions of years ago)
GEO_ERAS = [
    {"name": "Archean", "start": 4000, "end": 2500, "color": "#e6194b",
     "mineral_boost": 1.4},
    {"name": "Proterozoic", "start": 2500, "end": 541, "color": "#f58231",
     "mineral_boost": 1.3},
    {"name": "Paleozoic", "start": 541, "end": 252, "color": "#3cb44b",
     "mineral_boost": 1.1},
    {"name": "Mesozoic", "start": 252, "end": 66, "color": "#4363d8",
     "mineral_boost": 0.9},
    {"name": "Cenozoic", "start": 66, "end": 0, "color": "#ffe119",
     "mineral_boost": 0.7},
]


# ---------------------------------------------------------------------------
# DATA FETCHING
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_macrostrat_geology(lat, lon):
    """Fetch geological data from Macrostrat API."""
    try:
        resp = requests.get(
            "https://macrostrat.org/api/geologic_units/map",
            params={"lat": lat, "lng": lon, "format": "json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Macrostrat error: %s", e)
        return {}


# ---------------------------------------------------------------------------
# SCORING HELPERS
# ---------------------------------------------------------------------------

def _score_geological(geo_data):
    """Score geological favorability from Macrostrat units."""
    rock_types = []
    lithologies = []
    ages = []
    formation_names = []

    success = geo_data.get("success", {})
    units = success.get("data", []) if isinstance(success, dict) else []
    if not units and isinstance(geo_data, dict):
        raw = geo_data.get("success")
        if isinstance(raw, dict):
            units = raw.get("data", [])

    for unit in units[:10]:
        lith = unit.get("lith", "") or unit.get("lithology", "") or ""
        rock_types.append(lith.lower())
        lithologies.append(lith)
        age = unit.get("t_age") or unit.get("b_age") or 0
        if age:
            ages.append(float(age))
        name = unit.get("strat_name") or unit.get("unit_name") or unit.get("name", "")
        if name:
            formation_names.append(name)

    geo_score = 20
    found_minerals = set()
    for rock in rock_types:
        for key, info in FAVORABLE_LITHOLOGIES.items():
            if key in rock:
                geo_score = max(geo_score, info["score"])
                found_minerals.update(info["minerals"])

    return {
        "score": min(100, round(geo_score)),
        "rock_types": lithologies[:5] if lithologies else ["Unknown"],
        "formations_found": len(units),
        "favorable_indicators": len(found_minerals),
        "found_minerals": found_minerals,
        "ages": ages,
        "formation_names": formation_names[:8],
        "raw_rock_types": rock_types,
    }


def _score_tectonic(eq_data):
    """Score tectonic activity from USGS earthquake data."""
    features = eq_data.get("features", []) if isinstance(eq_data, dict) else []
    count = len(features)

    magnitudes = []
    for feat in features:
        props = feat.get("properties", {}) if isinstance(feat, dict) else {}
        mag = props.get("mag")
        if mag is not None:
            try:
                magnitudes.append(float(mag))
            except (ValueError, TypeError):
                pass

    if count == 0:
        score = 10
    elif count < 5:
        score = 25
    elif count < 20:
        score = 45
    elif count < 50:
        score = 60
    elif count < 100:
        score = 75
    else:
        score = 90

    max_mag = max(magnitudes) if magnitudes else 0.0
    avg_mag = sum(magnitudes) / len(magnitudes) if magnitudes else 0.0

    # Larger earthquakes boost the score
    if max_mag >= 5.0:
        score = min(100, score + 15)
    elif max_mag >= 4.0:
        score = min(100, score + 10)
    elif max_mag >= 3.0:
        score = min(100, score + 5)

    return {
        "score": min(100, round(score)),
        "earthquake_count": count,
        "max_magnitude": round(max_mag, 1),
        "avg_magnitude": round(avg_mag, 2),
        "significant_events": sum(1 for m in magnitudes if m >= 4.0),
    }


def _score_geochemistry(soil_data):
    """Score soil geochemistry from SoilGrids response."""
    layers = []
    props = {}
    if isinstance(soil_data, dict):
        raw_layers = soil_data.get("properties", {}).get("layers", [])
        if isinstance(raw_layers, list):
            layers = raw_layers

    for layer in layers:
        prop_name = layer.get("name", "")
        depths = layer.get("depths", [])
        values = []
        for d in depths if isinstance(depths, list) else []:
            vals = d.get("values", {})
            if isinstance(vals, dict):
                mean_val = vals.get("mean")
                if mean_val is not None:
                    try:
                        values.append(float(mean_val))
                    except (ValueError, TypeError):
                        pass
        if values:
            props[prop_name] = round(sum(values) / len(values), 2)

    # Base score from soil composition interpretation
    score = 30
    clay = props.get("clay", 0)
    soc = props.get("soc", 0)
    ph = props.get("phh2o", 0)
    cec = props.get("cec", 0)
    sand = props.get("sand", 0)
    silt = props.get("silt", 0)

    # High clay content may indicate weathered mineral deposits
    if clay > 0:
        clay_pct = clay / 10.0  # SoilGrids returns g/kg
        if clay_pct > 40:
            score += 20
        elif clay_pct > 25:
            score += 12
        elif clay_pct > 10:
            score += 5

    # Low organic carbon in mineral-rich soils
    if soc > 0:
        soc_val = soc / 10.0
        if soc_val < 10:
            score += 10  # Low organic = more mineralized

    # Acidic soils can indicate sulfide weathering (mineral indicator)
    if ph > 0:
        ph_val = ph / 10.0
        if ph_val < 5.5:
            score += 15
        elif ph_val < 6.5:
            score += 8

    # High CEC may indicate presence of mineral clays
    if cec > 0:
        cec_val = cec / 10.0
        if cec_val > 30:
            score += 10
        elif cec_val > 15:
            score += 5

    return {
        "score": min(100, round(score)),
        "clay": round(clay / 10.0, 1) if clay else 0,
        "sand": round(sand / 10.0, 1) if sand else 0,
        "silt": round(silt / 10.0, 1) if silt else 0,
        "organic_carbon": round(soc / 10.0, 1) if soc else 0,
        "ph": round(ph / 10.0, 1) if ph else 0,
        "cec": round(cec / 10.0, 1) if cec else 0,
        "properties_found": len(props),
    }


def _score_terrain(elev_data):
    """Score terrain indicators from elevation data."""
    center = elev_data.get("center_elevation", 0) if isinstance(elev_data, dict) else 0
    min_elev = elev_data.get("min_elevation", 0) if isinstance(elev_data, dict) else 0
    max_elev = elev_data.get("max_elevation", 0) if isinstance(elev_data, dict) else 0
    avg_elev = elev_data.get("avg_elevation", 0) if isinstance(elev_data, dict) else 0
    elevations = elev_data.get("grid_elevations", []) if isinstance(elev_data, dict) else []

    relief = max_elev - min_elev if max_elev and min_elev else 0

    # Compute slope proxy from elevation variation
    if len(elevations) > 1:
        valid = [e for e in elevations if e is not None]
        if valid:
            std_dev = (sum((x - sum(valid) / len(valid)) ** 2
                          for x in valid) / len(valid)) ** 0.5
        else:
            std_dev = 0
    else:
        std_dev = 0

    score = 25
    # Mountainous terrain favors mineral deposits
    if center > 2000:
        score += 25
    elif center > 1000:
        score += 18
    elif center > 500:
        score += 10
    elif center > 200:
        score += 5

    # High relief indicates tectonic uplift / exposed geology
    if relief > 500:
        score += 20
    elif relief > 200:
        score += 12
    elif relief > 50:
        score += 5

    # Terrain roughness
    if std_dev > 100:
        score += 15
    elif std_dev > 50:
        score += 8
    elif std_dev > 20:
        score += 4

    return {
        "score": min(100, round(score)),
        "center_elevation": round(center, 1),
        "min_elevation": round(min_elev, 1),
        "max_elevation": round(max_elev, 1),
        "relief": round(relief, 1),
        "avg_elevation": round(avg_elev, 1),
        "roughness": round(std_dev, 1),
    }


def _score_formation_age(ages):
    """Score based on geological formation ages (older = more mineral potential)."""
    if not ages:
        return {"score": 30, "oldest_age_ma": 0, "youngest_age_ma": 0,
                "era": "Unknown", "age_range_ma": 0}

    oldest = max(ages)
    youngest = min(ages)

    # Older formations tend to have more concentrated mineral deposits
    if oldest > 2500:
        score = 95  # Archean -- prime mineral territory
    elif oldest > 1000:
        score = 85  # Proterozoic
    elif oldest > 541:
        score = 70  # Late Proterozoic
    elif oldest > 252:
        score = 55  # Paleozoic
    elif oldest > 66:
        score = 40  # Mesozoic
    else:
        score = 25  # Cenozoic

    # Determine era
    era = "Unknown"
    for e in GEO_ERAS:
        if e["start"] >= oldest > e["end"]:
            era = e["name"]
            break

    return {
        "score": min(100, round(score)),
        "oldest_age_ma": round(oldest, 1),
        "youngest_age_ma": round(youngest, 1),
        "era": era,
        "age_range_ma": round(oldest - youngest, 1),
    }


def _estimate_deposit_probabilities(found_minerals, geo_score, tectonic_score,
                                     geo_chemistry_score, terrain_score,
                                     formation_age_score, rock_types):
    """Estimate probability for each target mineral type."""
    probabilities = {}

    # Base probability from combined scores
    base = (geo_score * 0.3 + tectonic_score * 0.15 +
            geo_chemistry_score * 0.2 + terrain_score * 0.15 +
            formation_age_score * 0.2)
    base_prob = min(85, base * 0.6)

    for mineral in TARGET_MINERALS:
        prob = base_prob * 0.3  # Start with a fraction of base

        # Boost if mineral was found in lithology match
        if mineral in found_minerals:
            prob += 30

        # Rock-type specific boosts
        for rock in rock_types:
            for key, info in FAVORABLE_LITHOLOGIES.items():
                if key in rock and mineral in info["minerals"]:
                    prob += 15

        # Mineral-specific adjustments
        if mineral == "gold":
            prob += tectonic_score * 0.15
            prob += formation_age_score * 0.10
        elif mineral == "copper":
            prob += tectonic_score * 0.20
            prob += geo_chemistry_score * 0.10
        elif mineral == "iron":
            prob += formation_age_score * 0.15
        elif mineral == "rare_earths":
            prob += formation_age_score * 0.20
            prob += terrain_score * 0.05
        elif mineral == "lithium":
            prob += geo_chemistry_score * 0.15
            prob += terrain_score * 0.10
        elif mineral == "coal":
            # Coal prefers sedimentary basins, lower terrain
            has_sedimentary = any("sediment" in r for r in rock_types)
            if has_sedimentary:
                prob += 20
        elif mineral == "uranium":
            prob += formation_age_score * 0.15
            prob += geo_chemistry_score * 0.10
        elif mineral == "diamonds":
            # Diamonds need kimberlite or very old cratons
            has_kimberlite = any("kimberlit" in r for r in rock_types)
            has_craton = formation_age_score > 80
            if has_kimberlite:
                prob += 40
            elif has_craton:
                prob += 15

        probabilities[mineral] = min(95, max(2, round(prob)))

    # Score is average of top-3 probabilities
    sorted_probs = sorted(probabilities.values(), reverse=True)
    deposit_score = round(sum(sorted_probs[:3]) / 3) if sorted_probs else 20

    return {
        "score": min(100, deposit_score),
        "probabilities": probabilities,
        "top_mineral": max(probabilities, key=probabilities.get) if probabilities else "Unknown",
        "top_probability": max(probabilities.values()) if probabilities else 0,
    }


# ---------------------------------------------------------------------------
# MAIN COMPUTATION
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_mineral_prospecting(lat, lon):
    """Compute full mineral prospecting assessment for a location."""
    geology = fetch_macrostrat_geology(lat, lon)
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_data(lat, lon) or {}
    quakes = fetch_earthquakes(lat, lon) or {}

    scores = {}
    details = {}

    # 1. Geological Favorability
    geo_result = _score_geological(geology)
    scores["geological"] = geo_result["score"]
    details["geological"] = geo_result

    # 2. Tectonic Activity
    tec_result = _score_tectonic(quakes)
    scores["tectonic"] = tec_result["score"]
    details["tectonic"] = tec_result

    # 3. Soil Geochemistry
    chem_result = _score_geochemistry(soil)
    scores["geochemistry"] = chem_result["score"]
    details["geochemistry"] = chem_result

    # 4. Terrain Indicators
    terr_result = _score_terrain(elev)
    scores["terrain"] = terr_result["score"]
    details["terrain"] = terr_result

    # 5. Formation Age
    age_result = _score_formation_age(geo_result.get("ages", []))
    scores["formation_age"] = age_result["score"]
    details["formation_age"] = age_result

    # 6. Deposit Type Probability
    dep_result = _estimate_deposit_probabilities(
        found_minerals=geo_result.get("found_minerals", set()),
        geo_score=scores["geological"],
        tectonic_score=scores["tectonic"],
        geo_chemistry_score=scores["geochemistry"],
        terrain_score=scores["terrain"],
        formation_age_score=scores["formation_age"],
        rock_types=geo_result.get("raw_rock_types", []),
    )
    scores["deposit_prob"] = dep_result["score"]
    details["deposit_prob"] = dep_result

    # Overall weighted score
    overall = sum(
        scores.get(k, 0) * MINERAL_COMPONENTS[k]["weight"]
        for k in MINERAL_COMPONENTS
    )

    return {
        "overall": round(overall),
        "scores": scores,
        "details": details,
        "minerals": list(geo_result.get("found_minerals", set())),
    }


# ---------------------------------------------------------------------------
# CHART BUILDERS
# ---------------------------------------------------------------------------

def _build_radar_chart(scores):
    """Build a Plotly radar chart of the 6 prospecting dimensions."""
    categories = [MINERAL_COMPONENTS[k]["name"] for k in MINERAL_COMPONENTS]
    values = [scores.get(k, 0) for k in MINERAL_COMPONENTS]
    colors = [MINERAL_COMPONENTS[k]["color"] for k in MINERAL_COMPONENTS]

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(245, 158, 11, 0.15)",
        line=dict(color="#f59e0b", width=2),
        marker=dict(size=8, color=colors + [colors[0]]),
        name="Prospecting Score",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(color="#a0a0a0", size=10),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(color="#e0e0e0", size=11),
            ),
        ),
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
        height=420,
    )

    return fig


def _build_mineral_probability_chart(probabilities):
    """Build horizontal bar chart of mineral deposit probabilities."""
    minerals = []
    probs = []
    colors = []

    # Sort by probability descending
    sorted_minerals = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    for mineral, prob in sorted_minerals:
        minerals.append(MINERAL_DISPLAY_NAMES.get(mineral, mineral))
        probs.append(prob)
        colors.append(MINERAL_COLORS.get(mineral, "#888888"))

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=minerals,
        x=probs,
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(color="rgba(255,255,255,0.2)", width=1),
        ),
        text=[f"{p}%" for p in probs],
        textposition="outside",
        textfont=dict(color="#e0e0e0", size=12),
    ))

    fig.update_layout(
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(
            title="Probability (%)", range=[0, 105],
            gridcolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#a0a0a0"),
        ),
        yaxis=dict(
            tickfont=dict(color="#e0e0e0", size=12),
            autorange="reversed",
        ),
        margin=dict(l=160, r=60, t=30, b=50),
        height=360,
        showlegend=False,
    )

    return fig


def _build_geological_timeline(ages, formation_names):
    """Build a geological timeline chart showing formation ages."""
    if not ages:
        return None

    fig = go.Figure()

    # Add era backgrounds
    for era in GEO_ERAS:
        fig.add_shape(
            type="rect",
            x0=era["end"], x1=era["start"],
            y0=-0.5, y1=len(ages) - 0.5 if ages else 0.5,
            fillcolor=era["color"],
            opacity=0.08,
            line_width=0,
            layer="below",
        )
        fig.add_annotation(
            x=(era["start"] + era["end"]) / 2,
            y=-0.7,
            text=era["name"],
            showarrow=False,
            font=dict(size=9, color=era["color"]),
            yanchor="top",
        )

    # Add formation age markers
    labels = formation_names[:len(ages)] if formation_names else [
        f"Formation {i + 1}" for i in range(len(ages))
    ]
    # Pad labels if fewer than ages
    while len(labels) < len(ages):
        labels.append(f"Unit {len(labels) + 1}")

    for i, (age, label) in enumerate(zip(ages, labels)):
        fig.add_trace(go.Scatter(
            x=[age],
            y=[i],
            mode="markers+text",
            marker=dict(size=14, color="#f59e0b", symbol="diamond",
                        line=dict(color="white", width=1)),
            text=[label[:25]],
            textposition="middle right",
            textfont=dict(size=10, color="#e0e0e0"),
            showlegend=False,
            hovertemplate=f"{label}<br>Age: {age:.0f} Ma<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(
            title="Millions of Years Ago (Ma)",
            gridcolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#a0a0a0"),
            autorange="reversed",
        ),
        yaxis=dict(visible=False),
        margin=dict(l=30, r=30, t=30, b=60),
        height=max(200, 60 * len(ages) + 80),
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------

def _overall_color(score):
    """Return a color based on the overall prospecting score."""
    if score >= 75:
        return "#22c55e"
    if score >= 55:
        return "#f59e0b"
    if score >= 35:
        return "#f97316"
    return "#ef4444"


def _overall_label(score):
    """Return a human-readable label for the overall score."""
    if score >= 80:
        return "Excellent Mineral Potential"
    if score >= 65:
        return "High Mineral Potential"
    if score >= 50:
        return "Moderate Mineral Potential"
    if score >= 35:
        return "Low-Moderate Potential"
    if score >= 20:
        return "Low Potential"
    return "Very Low Potential"


def _render_header_card(overall, lat, lon):
    """Render the header card with overall prospecting potential."""
    color = _overall_color(overall)
    label = _overall_label(overall)
    pct = min(100, max(0, overall))

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid {color}33; border-radius: 12px;
                padding: 24px 28px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;
                    flex-wrap: wrap; gap: 12px;">
            <div>
                <h3 style="color: {color}; margin: 0 0 4px 0; font-size: 1.5rem;">
                    Mineral Prospecting Score: {overall}/100
                </h3>
                <p style="color: #a0a0c0; margin: 0; font-size: 0.95rem;">
                    {label} &mdash; {lat:.4f}, {lon:.4f}
                </p>
            </div>
            <div style="width: 100px; height: 100px; border-radius: 50%;
                        border: 4px solid {color};
                        display: flex; align-items: center; justify-content: center;
                        background: {color}15;">
                <span style="color: {color}; font-size: 1.8rem; font-weight: 700;">
                    {overall}
                </span>
            </div>
        </div>
        <div style="margin-top: 14px; background: #0d0d1a; border-radius: 8px;
                    height: 10px; overflow: hidden;">
            <div style="width: {pct}%; height: 100%;
                        background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e);
                        border-radius: 8px;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_metric_card(key, score, details):
    """Render a single metric card for one of the 6 dimensions."""
    comp = MINERAL_COMPONENTS.get(key, {})
    name = comp.get("name", key)
    color = comp.get("color", "#888")

    # Build detail lines based on component
    detail_lines = ""
    if key == "geological":
        rocks = ", ".join(details.get("rock_types", ["Unknown"])[:3])
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Formations: {details.get('formations_found', 0)}<br>"
            f"Rock types: {rocks}<br>"
            f"Favorable indicators: {details.get('favorable_indicators', 0)}"
            f"</div>"
        )
    elif key == "tectonic":
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Earthquakes (1yr): {details.get('earthquake_count', 0)}<br>"
            f"Max magnitude: {details.get('max_magnitude', 0)}<br>"
            f"Significant (M4+): {details.get('significant_events', 0)}"
            f"</div>"
        )
    elif key == "geochemistry":
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Clay: {details.get('clay', 0)}% &bull; Sand: {details.get('sand', 0)}%<br>"
            f"pH: {details.get('ph', 0)} &bull; OC: {details.get('organic_carbon', 0)} g/kg<br>"
            f"CEC: {details.get('cec', 0)} cmol/kg"
            f"</div>"
        )
    elif key == "terrain":
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Elevation: {details.get('center_elevation', 0)} m<br>"
            f"Relief: {details.get('relief', 0)} m<br>"
            f"Roughness: {details.get('roughness', 0)}"
            f"</div>"
        )
    elif key == "formation_age":
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Oldest: {details.get('oldest_age_ma', 0)} Ma<br>"
            f"Era: {details.get('era', 'Unknown')}<br>"
            f"Range: {details.get('age_range_ma', 0)} Ma"
            f"</div>"
        )
    elif key == "deposit_prob":
        top = details.get("top_mineral", "Unknown")
        top_name = MINERAL_DISPLAY_NAMES.get(top, top)
        detail_lines = (
            f"<div style='color:#a0a0c0;font-size:0.82rem;margin-top:6px;'>"
            f"Top mineral: {top_name}<br>"
            f"Probability: {details.get('top_probability', 0)}%"
            f"</div>"
        )

    pct = min(100, max(0, score))
    st.markdown(f"""
    <div style="background: #1a1a2e; border: 1px solid {color}33;
                border-radius: 10px; padding: 16px; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: {color}; font-weight: 600; font-size: 0.95rem;">
                {name}
            </span>
            <span style="color: {color}; font-size: 1.4rem; font-weight: 700;">
                {score}
            </span>
        </div>
        <div style="margin-top: 8px; background: #0d0d1a; border-radius: 6px;
                    height: 6px; overflow: hidden;">
            <div style="width: {pct}%; height: 100%; background: {color};
                        border-radius: 6px;"></div>
        </div>
        {detail_lines}
    </div>
    """, unsafe_allow_html=True)


def _render_rock_type_table(details):
    """Render table of favorable rock types found at the location."""
    geo = details.get("geological", {})
    raw_rocks = geo.get("raw_rock_types", [])

    matched = []
    seen = set()
    for rock in raw_rocks:
        for key, info in FAVORABLE_LITHOLOGIES.items():
            if key in rock and key not in seen:
                seen.add(key)
                matched.append({
                    "Rock Type": key.capitalize(),
                    "Favorable Score": info["score"],
                    "Associated Minerals": ", ".join(
                        MINERAL_DISPLAY_NAMES.get(m, m) for m in info["minerals"]
                    ),
                })

    if not matched:
        st.info("No specifically favorable rock types identified at this location.")
        return

    # Build HTML table
    rows_html = ""
    for row in sorted(matched, key=lambda x: x["Favorable Score"], reverse=True):
        rows_html += (
            f"<tr style='border-bottom:1px solid #2a2a3e;'>"
            f"<td style='padding:8px 12px;color:#f59e0b;font-weight:600;'>"
            f"{row['Rock Type']}</td>"
            f"<td style='padding:8px 12px;color:#e0e0e0;text-align:center;'>"
            f"{row['Favorable Score']}</td>"
            f"<td style='padding:8px 12px;color:#a0a0c0;'>"
            f"{row['Associated Minerals']}</td></tr>"
        )

    st.markdown(f"""
    <div style="background: #1a1a2e; border-radius: 10px; overflow: hidden;
                border: 1px solid #2a2a3e;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #0d0d1a;">
                    <th style="padding: 10px 12px; text-align: left; color: #a0a0c0;
                              font-size: 0.85rem;">Rock Type</th>
                    <th style="padding: 10px 12px; text-align: center; color: #a0a0c0;
                              font-size: 0.85rem;">Score</th>
                    <th style="padding: 10px 12px; text-align: left; color: #a0a0c0;
                              font-size: 0.85rem;">Associated Minerals</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def render_mineral_prospecting_tab():
    """Render the Mineral Prospecting AI tab."""

    # -- Tab header --
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Mineral Prospecting AI</h4>"
        "<p>Geological mineral prospecting assessment combining lithology, "
        "tectonics, soil chemistry &amp; terrain analysis</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Location selector --
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="mp_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="mp_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="mp_lon",
        )

    run_btn = st.button(
        "Run Mineral Prospecting Analysis",
        type="primary",
        key="mp_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and click **Run Mineral Prospecting Analysis** "
            "to start the geological assessment."
        )
        return

    # -- Progress --
    progress = st.progress(0, text="Initializing mineral prospecting scan...")
    progress.progress(10, text="Fetching geological formations (Macrostrat)...")
    progress.progress(30, text="Fetching soil geochemistry (SoilGrids)...")
    progress.progress(50, text="Fetching elevation data (Open Topo)...")
    progress.progress(70, text="Fetching seismic activity (USGS)...")
    progress.progress(85, text="Computing prospecting assessment...")

    results = compute_mineral_prospecting(lat, lon)

    progress.progress(100, text="Analysis complete.")

    overall = results.get("overall", 0)
    scores = results.get("scores", {})
    details = results.get("details", {})

    # -- Header card --
    _render_header_card(overall, lat, lon)

    # -- Radar chart --
    st.subheader("Prospecting Dimensions")
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="mp_radar")

    # -- 6 metric cards in 3x2 grid --
    st.subheader("Detailed Scores")
    keys = list(MINERAL_COMPONENTS.keys())
    row1 = st.columns(3)
    for i, col in enumerate(row1):
        with col:
            k = keys[i]
            _render_metric_card(k, scores.get(k, 0), details.get(k, {}))

    row2 = st.columns(3)
    for i, col in enumerate(row2):
        with col:
            k = keys[i + 3]
            _render_metric_card(k, scores.get(k, 0), details.get(k, {}))

    # -- Mineral probability bar chart --
    st.subheader("Mineral Deposit Probabilities")
    dep_details = details.get("deposit_prob", {})
    probabilities = dep_details.get("probabilities", {})
    if probabilities:
        prob_fig = _build_mineral_probability_chart(probabilities)
        st.plotly_chart(prob_fig, use_container_width=True, key="mp_prob_chart")
    else:
        st.info("No mineral probability data available.")

    # -- Geological timeline --
    st.subheader("Geological Timeline")
    geo_details = details.get("geological", {})
    age_details = details.get("formation_age", {})
    ages = geo_details.get("ages", [])
    formation_names = geo_details.get("formation_names", [])

    if ages:
        timeline_fig = _build_geological_timeline(ages, formation_names)
        if timeline_fig is not None:
            st.plotly_chart(timeline_fig, use_container_width=True, key="mp_timeline")
        else:
            st.info("No geological age data available for timeline.")

        st.markdown(
            f"<div style='background:#1a1a2e;border-radius:8px;padding:12px 16px;"
            f"border:1px solid #2a2a3e;margin-bottom:16px;'>"
            f"<span style='color:#8b5cf6;font-weight:600;'>Era:</span> "
            f"<span style='color:#e0e0e0;'>{age_details.get('era', 'Unknown')}</span>"
            f" &bull; "
            f"<span style='color:#8b5cf6;font-weight:600;'>Oldest Formation:</span> "
            f"<span style='color:#e0e0e0;'>{age_details.get('oldest_age_ma', 0)} Ma</span>"
            f" &bull; "
            f"<span style='color:#8b5cf6;font-weight:600;'>Age Range:</span> "
            f"<span style='color:#e0e0e0;'>{age_details.get('age_range_ma', 0)} Ma</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No formation age data available for this location.")

    # -- Favorable rock types table --
    st.subheader("Favorable Rock Types Found")
    _render_rock_type_table(details)

    # -- Minerals summary --
    found_minerals = results.get("minerals", [])
    if found_minerals:
        mineral_tags = " ".join(
            f"<span style='display:inline-block;background:{MINERAL_COLORS.get(m, '#555')}22;"
            f"color:{MINERAL_COLORS.get(m, '#ccc')};border:1px solid "
            f"{MINERAL_COLORS.get(m, '#555')}44;border-radius:16px;"
            f"padding:4px 14px;margin:3px;font-size:0.85rem;'>"
            f"{MINERAL_DISPLAY_NAMES.get(m, m)}</span>"
            for m in found_minerals
        )
        st.markdown(
            f"<div style='background:#1a1a2e;border-radius:10px;padding:16px;"
            f"border:1px solid #2a2a3e;margin-top:12px;'>"
            f"<div style='color:#f59e0b;font-weight:600;margin-bottom:8px;'>"
            f"Minerals Indicated by Geology</div>"
            f"<div>{mineral_tags}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
