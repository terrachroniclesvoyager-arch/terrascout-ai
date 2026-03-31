"""
Soil Erosion Risk AI module for TerraScout AI.
RUSLE-inspired erosion estimation using five key factors:
  R (Rainfall Erosivity), K (Soil Erodibility), LS (Slope & Length),
  C (Cover Management), P (Conservation Practice).

Data sources (all FREE, no API key):
  - ISRIC SoilGrids  : clay, sand, silt, organic carbon (erodibility)
  - Open-Meteo       : precipitation intensity & frequency (erosivity)
  - Open Topo Data   : slope steepness & flow length (topographic factor)
  - Overpass API      : land cover, vegetation, conservation structures
"""

import math
import logging
from html import escape

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
)
from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# =============================================================================
# THEME CONSTANTS
# =============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

CLR_VERY_LOW = "#22c55e"
CLR_LOW = "#84cc16"
CLR_MODERATE = "#f59e0b"
CLR_HIGH = "#ef4444"
CLR_VERY_HIGH = "#991b1b"

DIMENSION_COLORS = {
    "Rainfall Erosivity (R)": "#3b82f6",
    "Soil Erodibility (K)": "#f59e0b",
    "Slope & Length (LS)": "#a855f7",
    "Cover Management (C)": "#10b981",
    "Conservation Practice (P)": "#06b6d4",
}

DIMENSION_KEYS = list(DIMENSION_COLORS.keys())


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _risk_color(score: float) -> str:
    """Return colour for erosion *score* (100 = low risk, 0 = high risk)."""
    if score >= 80:
        return CLR_VERY_LOW
    if score >= 60:
        return CLR_LOW
    if score >= 40:
        return CLR_MODERATE
    if score >= 20:
        return CLR_HIGH
    return CLR_VERY_HIGH


def _risk_label(score: float) -> str:
    if score >= 80:
        return "Very Low Risk"
    if score >= 60:
        return "Low Risk"
    if score >= 40:
        return "Moderate Risk"
    if score >= 20:
        return "High Risk"
    return "Very High Risk"


# =============================================================================
# OVERPASS: VEGETATION & LAND COVER
# =============================================================================

@st.cache_data(ttl=1800)
def _fetch_vegetation(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch forests, grasslands, cropland, bare soil, and conservation
    structures from the Overpass API."""
    query = f"""[out:json][timeout:30];
(
  way["natural"="wood"](around:{radius},{lat},{lon});
  way["landuse"="forest"](around:{radius},{lat},{lon});
  way["landuse"="grass"](around:{radius},{lat},{lon});
  way["natural"="grassland"](around:{radius},{lat},{lon});
  way["landuse"="meadow"](around:{radius},{lat},{lon});
  way["landuse"="farmland"](around:{radius},{lat},{lon});
  way["natural"="scrub"](around:{radius},{lat},{lon});
  way["natural"="bare_rock"](around:{radius},{lat},{lon});
  way["natural"="sand"](around:{radius},{lat},{lon});
  way["natural"="scree"](around:{radius},{lat},{lon});
  way["man_made"="embankment"](around:{radius},{lat},{lon});
  way["barrier"="retaining_wall"](around:{radius},{lat},{lon});
  way["man_made"="dyke"](around:{radius},{lat},{lon});
  node["natural"="tree_row"](around:{radius},{lat},{lon});
  way["natural"="tree_row"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


# =============================================================================
# CORE ANALYSIS
# =============================================================================

@st.cache_data(ttl=1800)
def compute_erosion_risk(lat: float, lon: float) -> dict:
    """
    Compute RUSLE-inspired erosion risk analysis.

    Returns dict with:
        overall             - weighted composite score 0-100 (100 = low risk)
        risk_label          - Very Low / Low / Moderate / High / Very High Risk
        risk_color          - hex colour for risk label
        dimension_scores    - dict of 5 dimension scores (0-100, 100=low risk)
        dimension_details   - short explanation per dimension
        rusle_factors       - raw RUSLE-like factor values (R, K, LS, C, P)
        recommendations     - list of actionable recommendations
        raw                 - supporting data snippets for display
    """

    # -- Fetch all data sources ------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=7)
    veg_data = _fetch_vegetation(lat, lon, radius=5000)

    # -- Parse soil (CRITICAL SoilGrids pattern) --------------------------------
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l

    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay", 10)
    sand_pct = _sv("sand", 10)
    silt_pct = _sv("silt", 10)
    soc_val = _sv("soc", 10)       # g/kg

    # -- Parse weather ----------------------------------------------------------
    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    precip_sums = daily.get("precipitation_sum", [])
    valid_precip = [p for p in (precip_sums if isinstance(precip_sums, list) else [])
                    if p is not None]
    total_precip_7d = sum(valid_precip) if valid_precip else 0.0
    max_daily_precip = max(valid_precip) if valid_precip else 0.0
    avg_daily_precip = (total_precip_7d / len(valid_precip)) if valid_precip else 0.0
    annual_precip_est = (total_precip_7d * (365 / max(len(valid_precip), 1))
                         if valid_precip else 600.0)
    rainy_days = sum(1 for p in valid_precip if p > 1.0)

    hourly = (weather if isinstance(weather, dict) else {}).get("hourly", {})
    hourly_precip = hourly.get("precipitation", [])
    valid_hourly = [h for h in (hourly_precip if isinstance(hourly_precip, list) else [])
                    if h is not None]
    max_hourly_precip = max(valid_hourly) if valid_hourly else 0.0

    # -- Parse elevation --------------------------------------------------------
    raw_elevations = (elev if isinstance(elev, dict) else {}).get("grid_elevations", [])
    elevations = [e for e in (raw_elevations if isinstance(raw_elevations, list) else [])
                  if e is not None]
    center_elev = (elev if isinstance(elev, dict) else {}).get("center_elevation", 0.0) or 0.0
    elev_min = min(elevations) if elevations else 0.0
    elev_max = max(elevations) if elevations else 0.0
    elev_range = elev_max - elev_min

    # Estimate slope in degrees from elevation grid
    grid_size = 7
    radius_deg = 0.04
    cell_size_m = radius_deg * 111_320 / max(grid_size // 2, 1)  # approx metres
    slopes = []
    for i in range(grid_size):
        for j in range(grid_size):
            idx = i * grid_size + j
            if idx >= len(elevations):
                continue
            neighbours = []
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < grid_size and 0 <= nj < grid_size:
                    nidx = ni * grid_size + nj
                    if nidx < len(elevations):
                        neighbours.append(elevations[nidx])
            if neighbours:
                dz = max(abs(elevations[idx] - n) for n in neighbours)
                angle = math.degrees(math.atan2(dz, cell_size_m)) if cell_size_m > 0 else 0
                slopes.append(angle)
    avg_slope_deg = (sum(slopes) / len(slopes)) if slopes else 0.0
    max_slope_deg = max(slopes) if slopes else 0.0

    # -- Parse vegetation / land cover ------------------------------------------
    veg_elements = (veg_data if isinstance(veg_data, dict) else {}).get("elements", [])
    veg_list = veg_elements if isinstance(veg_elements, list) else []

    forests = 0
    grasslands = 0
    croplands = 0
    bare_soil = 0
    scrub = 0
    conservation_structures = 0
    tree_rows = 0

    for elem in veg_list:
        tags = elem.get("tags", {}) if isinstance(elem, dict) else {}
        landuse = tags.get("landuse", "")
        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")
        barrier = tags.get("barrier", "")

        if natural == "wood" or landuse == "forest":
            forests += 1
        elif natural in ("grassland",) or landuse in ("grass", "meadow"):
            grasslands += 1
        elif landuse == "farmland":
            croplands += 1
        elif natural in ("bare_rock", "sand", "scree"):
            bare_soil += 1
        elif natural == "scrub":
            scrub += 1
        elif natural == "tree_row":
            tree_rows += 1
        elif man_made in ("embankment", "dyke") or barrier == "retaining_wall":
            conservation_structures += 1

    total_cover = forests + grasslands + croplands + bare_soil + scrub
    forest_ratio = forests / max(total_cover, 1)
    grass_ratio = grasslands / max(total_cover, 1)
    crop_ratio = croplands / max(total_cover, 1)
    bare_ratio = bare_soil / max(total_cover, 1)

    # =========================================================================
    # DIMENSION 1: Rainfall Erosivity (R)  — 0-100 where 100 = low erosivity
    # =========================================================================
    # Based on precipitation intensity, frequency, annual total
    r_factor_raw = 0.0
    # Annual precipitation contribution
    if annual_precip_est > 2000:
        r_factor_raw += 40
    elif annual_precip_est > 1200:
        r_factor_raw += 30
    elif annual_precip_est > 800:
        r_factor_raw += 20
    elif annual_precip_est > 400:
        r_factor_raw += 10
    else:
        r_factor_raw += 5

    # Max daily intensity
    if max_daily_precip > 50:
        r_factor_raw += 30
    elif max_daily_precip > 30:
        r_factor_raw += 22
    elif max_daily_precip > 15:
        r_factor_raw += 14
    elif max_daily_precip > 5:
        r_factor_raw += 7
    else:
        r_factor_raw += 3

    # Hourly intensity (storm bursts)
    if max_hourly_precip > 20:
        r_factor_raw += 20
    elif max_hourly_precip > 10:
        r_factor_raw += 14
    elif max_hourly_precip > 5:
        r_factor_raw += 8
    else:
        r_factor_raw += 3

    # Frequency of rainy days in 7-day window
    if rainy_days >= 6:
        r_factor_raw += 10
    elif rainy_days >= 4:
        r_factor_raw += 7
    elif rainy_days >= 2:
        r_factor_raw += 4
    else:
        r_factor_raw += 1

    r_factor_raw = min(100, r_factor_raw)
    rainfall_score = round(_clamp(100 - r_factor_raw), 1)

    if rainfall_score >= 70:
        rainfall_detail = (f"Low erosivity: ~{annual_precip_est:.0f} mm/yr est., "
                           f"max {max_daily_precip:.1f} mm/day")
    elif rainfall_score >= 40:
        rainfall_detail = (f"Moderate erosivity: ~{annual_precip_est:.0f} mm/yr est., "
                           f"peak {max_daily_precip:.1f} mm/day")
    else:
        rainfall_detail = (f"High erosivity: ~{annual_precip_est:.0f} mm/yr est., "
                           f"intense bursts up to {max_hourly_precip:.1f} mm/hr")

    # =========================================================================
    # DIMENSION 2: Soil Erodibility (K)  — 0-100 where 100 = low erodibility
    # =========================================================================
    # RUSLE K depends on silt, very fine sand, organic matter, structure, permeability
    k_factor_raw = 50.0  # default mid-range
    k_parts = []

    if silt_pct is not None and clay_pct is not None and sand_pct is not None:
        # High silt = highly erodible
        if silt_pct > 60:
            k_factor_raw = 85
            k_parts.append(f"Very high silt ({silt_pct:.0f}%): extremely erodible")
        elif silt_pct > 40:
            k_factor_raw = 65
            k_parts.append(f"High silt ({silt_pct:.0f}%): moderately erodible")
        elif silt_pct > 20:
            k_factor_raw = 40
            k_parts.append(f"Moderate silt ({silt_pct:.0f}%)")
        else:
            k_factor_raw = 25
            k_parts.append(f"Low silt ({silt_pct:.0f}%): resistant")

        # Clay aggregation benefit
        if clay_pct > 35:
            k_factor_raw = max(10, k_factor_raw - 15)
            k_parts.append(f"High clay ({clay_pct:.0f}%): binds aggregates")
        elif clay_pct > 20:
            k_factor_raw = max(10, k_factor_raw - 8)
            k_parts.append(f"Moderate clay ({clay_pct:.0f}%)")

        # Sandy soil: low cohesion but good drainage
        if sand_pct > 70:
            k_factor_raw = max(10, k_factor_raw - 5)
            k_parts.append(f"Sandy ({sand_pct:.0f}%): quick drainage")
    else:
        k_parts.append("Soil texture data unavailable; using estimate")

    # Organic carbon reduces erodibility
    if soc_val is not None:
        if soc_val > 30:
            k_factor_raw = max(5, k_factor_raw - 20)
            k_parts.append(f"High organic C ({soc_val:.1f} g/kg): strong binding")
        elif soc_val > 15:
            k_factor_raw = max(5, k_factor_raw - 12)
            k_parts.append(f"Moderate organic C ({soc_val:.1f} g/kg)")
        elif soc_val > 5:
            k_factor_raw = max(5, k_factor_raw - 5)
            k_parts.append(f"Low organic C ({soc_val:.1f} g/kg)")
        else:
            k_parts.append(f"Very low organic C ({soc_val:.1f} g/kg): weak binding")

    k_factor_raw = min(100, max(0, k_factor_raw))
    erodibility_score = round(_clamp(100 - k_factor_raw), 1)
    erodibility_detail = "; ".join(k_parts) if k_parts else "Soil erodibility assessment"

    # =========================================================================
    # DIMENSION 3: Slope & Length (LS)  — 0-100 where 100 = low slope risk
    # =========================================================================
    # RUSLE LS: steeper and longer slopes => more erosion
    if avg_slope_deg < 1:
        ls_raw = 5
        slope_detail = f"Nearly flat ({avg_slope_deg:.1f} deg avg): minimal runoff"
    elif avg_slope_deg < 3:
        ls_raw = 15
        slope_detail = f"Gentle slope ({avg_slope_deg:.1f} deg avg): low runoff risk"
    elif avg_slope_deg < 6:
        ls_raw = 30
        slope_detail = f"Moderate slope ({avg_slope_deg:.1f} deg avg): notable erosion potential"
    elif avg_slope_deg < 12:
        ls_raw = 55
        slope_detail = f"Steep slope ({avg_slope_deg:.1f} deg avg): significant erosion risk"
    elif avg_slope_deg < 20:
        ls_raw = 75
        slope_detail = f"Very steep ({avg_slope_deg:.1f} deg avg): severe erosion potential"
    else:
        ls_raw = 90
        slope_detail = f"Extreme slope ({avg_slope_deg:.1f} deg avg): critical erosion zone"

    # Relief amplifies length factor
    if elev_range > 200:
        ls_raw = min(100, ls_raw + 15)
        slope_detail += f"; high relief ({elev_range:.0f} m)"
    elif elev_range > 80:
        ls_raw = min(100, ls_raw + 8)
        slope_detail += f"; moderate relief ({elev_range:.0f} m)"
    else:
        slope_detail += f"; low relief ({elev_range:.0f} m)"

    slope_score = round(_clamp(100 - ls_raw), 1)

    # =========================================================================
    # DIMENSION 4: Cover Management (C)  — 0-100 where 100 = good cover
    # =========================================================================
    # Dense vegetation cover protects against erosion
    cover_score = 30.0  # baseline (no data = assume some exposure)
    cover_parts = []

    if total_cover > 0:
        # Forest is best protection
        cover_score = 20.0
        cover_score += forest_ratio * 50
        cover_score += grass_ratio * 30
        cover_score += (scrub / max(total_cover, 1)) * 25
        cover_score += crop_ratio * 10
        # Bare soil penalty
        cover_score -= bare_ratio * 30

        if forests > 0:
            cover_parts.append(f"{forests} forest area(s)")
        if grasslands > 0:
            cover_parts.append(f"{grasslands} grassland(s)")
        if croplands > 0:
            cover_parts.append(f"{croplands} cropland(s)")
        if bare_soil > 0:
            cover_parts.append(f"{bare_soil} bare/rock area(s)")
        if scrub > 0:
            cover_parts.append(f"{scrub} scrubland(s)")
    else:
        cover_parts.append("No mapped land cover features; using default estimate")

    # Tree rows provide windbreaks and reduce sheet erosion
    if tree_rows > 0:
        cover_score += min(15, tree_rows * 5)
        cover_parts.append(f"{tree_rows} tree row(s)")

    cover_score = round(_clamp(cover_score), 1)
    cover_detail = "; ".join(cover_parts) if cover_parts else "Cover assessment"

    # =========================================================================
    # DIMENSION 5: Conservation Practice (P)  — 0-100 where 100 = good practices
    # =========================================================================
    practice_score = 35.0  # baseline (no known practices)
    practice_parts = []

    # Conservation structures from Overpass
    if conservation_structures > 0:
        practice_score += min(30, conservation_structures * 10)
        practice_parts.append(
            f"{conservation_structures} conservation structure(s) (embankments/dykes/walls)")

    # Tree rows indicate contour planting / windbreaks
    if tree_rows > 0:
        practice_score += min(15, tree_rows * 5)
        practice_parts.append(f"{tree_rows} tree row(s) suggesting contour planting")

    # Terracing indicators from slope + cropland presence
    if croplands > 0 and avg_slope_deg > 5:
        # Cropland on slopes often implies terracing in many regions
        practice_score += 10
        practice_parts.append("Cropland on slopes may indicate terracing")

    # Forest buffers near water or on slopes
    if forests > 0 and avg_slope_deg > 3:
        practice_score += 8
        practice_parts.append("Forest cover on slopes acts as natural buffer")

    if not practice_parts:
        practice_parts.append("No conservation structures detected; practices unknown")

    practice_score = round(_clamp(practice_score), 1)
    practice_detail = "; ".join(practice_parts)

    # =========================================================================
    # RUSLE Factor Values (dimensionless relative indices for display)
    # =========================================================================
    # Normalise raw factor intensities to 0-1 scale for bar chart
    r_value = round(r_factor_raw / 100, 2)
    k_value = round(k_factor_raw / 100, 2)
    ls_value = round(ls_raw / 100, 2)
    c_value = round(1.0 - (cover_score / 100), 2)      # lower cover => higher C
    p_value = round(1.0 - (practice_score / 100), 2)    # fewer practices => higher P

    rusle_product = r_value * k_value * ls_value * max(c_value, 0.01) * max(p_value, 0.01)

    # =========================================================================
    # AGGREGATE SCORE
    # =========================================================================
    dimension_scores = {
        "Rainfall Erosivity (R)": rainfall_score,
        "Soil Erodibility (K)": erodibility_score,
        "Slope & Length (LS)": slope_score,
        "Cover Management (C)": cover_score,
        "Conservation Practice (P)": practice_score,
    }
    dimension_details = {
        "Rainfall Erosivity (R)": rainfall_detail,
        "Soil Erodibility (K)": erodibility_detail,
        "Slope & Length (LS)": slope_detail,
        "Cover Management (C)": cover_detail,
        "Conservation Practice (P)": practice_detail,
    }

    weights = {
        "Rainfall Erosivity (R)": 2.0,
        "Soil Erodibility (K)": 1.8,
        "Slope & Length (LS)": 2.0,
        "Cover Management (C)": 1.5,
        "Conservation Practice (P)": 1.2,
    }
    total_w = sum(weights.values())
    overall = round(
        sum(dimension_scores[k] * weights[k] for k in dimension_scores) / total_w, 1
    )
    risk_label = _risk_label(overall)
    risk_color = _risk_color(overall)

    # -- Recommendations -------------------------------------------------------
    recommendations = []
    if rainfall_score < 40:
        recommendations.append(
            "Install rainwater management systems: contour bunds, diversion channels, "
            "or retention basins to reduce runoff velocity during intense storms."
        )
    if erodibility_score < 40:
        recommendations.append(
            "Improve soil structure: add organic matter (compost, mulch, cover crops) "
            "to bind particles. Consider gypsum amendments for high-silt soils."
        )
    if slope_score < 40:
        recommendations.append(
            "Implement terracing or bench construction on steep slopes. "
            "Use check dams in drainage channels to slow water flow."
        )
    if cover_score < 40:
        recommendations.append(
            "Increase ground cover urgently: plant native grasses, establish cover crops, "
            "or apply mulch. Avoid leaving soil bare between planting seasons."
        )
    if practice_score < 40:
        recommendations.append(
            "Adopt conservation tillage, contour farming, or strip cropping. "
            "Establish vegetative buffer strips along waterways and field boundaries."
        )
    if overall >= 70 and not recommendations:
        recommendations.append(
            "Erosion risk is low. Maintain current land management practices and "
            "monitor for changes in precipitation patterns or land cover."
        )
    if overall < 30:
        recommendations.append(
            "CRITICAL: Multiple erosion factors are severe. Consider an integrated "
            "watershed management plan combining structural and vegetative measures."
        )
    if not recommendations:
        recommendations.append(
            "Monitor erosion indicators seasonally. Consider soil conservation "
            "planning to maintain current conditions."
        )

    return {
        "overall": overall,
        "risk_label": risk_label,
        "risk_color": risk_color,
        "dimension_scores": dimension_scores,
        "dimension_details": dimension_details,
        "rusle_factors": {
            "R": r_value,
            "K": k_value,
            "LS": ls_value,
            "C": c_value,
            "P": p_value,
            "product": round(rusle_product, 4),
        },
        "recommendations": recommendations,
        "raw": {
            "annual_precip_est": round(annual_precip_est, 0),
            "max_daily_precip": round(max_daily_precip, 1),
            "max_hourly_precip": round(max_hourly_precip, 1),
            "clay_pct": round(clay_pct, 1) if clay_pct is not None else None,
            "sand_pct": round(sand_pct, 1) if sand_pct is not None else None,
            "silt_pct": round(silt_pct, 1) if silt_pct is not None else None,
            "soc_gkg": round(soc_val, 1) if soc_val is not None else None,
            "avg_slope_deg": round(avg_slope_deg, 1),
            "max_slope_deg": round(max_slope_deg, 1),
            "elev_range_m": round(elev_range, 0),
            "center_elev_m": round(center_elev, 0),
            "forests": forests,
            "grasslands": grasslands,
            "croplands": croplands,
            "bare_soil": bare_soil,
            "conservation_structures": conservation_structures,
        },
    }


# =============================================================================
# CHART BUILDERS
# =============================================================================

def _build_radar_chart(dimension_scores: dict) -> go.Figure:
    """Build a radar chart of the 5 RUSLE dimensions."""
    labels = list(dimension_scores.keys())
    values = list(dimension_scores.values())
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(168,85,247,0.15)",
        line={"color": "#a855f7", "width": 2.5},
        marker={"size": 7, "color": "#a855f7"},
        name="Erosion Score",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar={
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
            "bgcolor": CLR_BG,
        },
        title={
            "text": "Erosion Risk Profile (100 = Low Risk)",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=430,
        margin=dict(l=70, r=70, t=60, b=40),
        paper_bgcolor=CLR_BG,
        showlegend=False,
    )
    return fig


def _build_rusle_bar_chart(rusle_factors: dict) -> go.Figure:
    """Build a bar chart showing RUSLE factor breakdown."""
    factor_names = ["R (Rainfall)", "K (Soil)", "LS (Slope)", "C (Cover)", "P (Practice)"]
    factor_keys = ["R", "K", "LS", "C", "P"]
    values = [rusle_factors.get(k, 0) for k in factor_keys]
    colors = ["#3b82f6", "#f59e0b", "#a855f7", "#10b981", "#06b6d4"]

    fig = go.Figure(go.Bar(
        x=factor_names,
        y=values,
        marker={"color": colors, "line": {"width": 0}},
        text=[f"{v:.2f}" for v in values],
        textposition="auto",
        textfont={"color": CLR_TEXT, "size": 13},
        hovertemplate="%{x}: %{y:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title={
            "text": "RUSLE Factor Intensity (0 = None, 1 = Maximum)",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=350,
        margin=dict(l=50, r=30, t=60, b=50),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        yaxis={
            "range": [0, 1.05],
            "gridcolor": "#2a3550",
            "tickfont": {"color": CLR_TEXT_SEC},
            "title": {"text": "Factor Intensity", "font": {"color": CLR_TEXT_SEC}},
        },
        xaxis={
            "tickfont": {"color": CLR_TEXT, "size": 12},
        },
    )
    return fig


def _build_erosion_gauge(overall: float, risk_label: str, risk_color: str) -> str:
    """Return HTML for an erosion risk gauge."""
    # Invert for gauge: 0 = low risk (green), 100 = high risk (red)
    risk_value = 100 - overall
    angle = -90 + (risk_value / 100) * 180  # -90 to +90 degrees

    return f"""
    <div style="text-align:center; background:linear-gradient(135deg,{risk_color}15,{CLR_BG});
                border-radius:14px; padding:24px 20px; border:1px solid {risk_color}55;">
        <div style="font-size:13px; color:{CLR_TEXT_SEC}; text-transform:uppercase;
                    letter-spacing:1.5px; margin-bottom:8px;">
            Erosion Risk Assessment
        </div>
        <div style="position:relative; width:200px; height:110px; margin:0 auto;">
            <svg viewBox="0 0 200 110" width="200" height="110">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
                      stroke="#2a3550" stroke-width="12" stroke-linecap="round"/>
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
                      stroke="url(#gaugeGrad)" stroke-width="12" stroke-linecap="round"
                      stroke-dasharray="{risk_value * 2.51} 251"/>
                <defs>
                    <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#22c55e"/>
                        <stop offset="50%" style="stop-color:#f59e0b"/>
                        <stop offset="100%" style="stop-color:#ef4444"/>
                    </linearGradient>
                </defs>
                <line x1="100" y1="100" x2="{100 + 60 * math.cos(math.radians(angle)):.1f}"
                      y2="{100 - 60 * math.sin(math.radians(angle)):.1f}"
                      stroke="{CLR_TEXT}" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="5" fill="{CLR_TEXT}"/>
            </svg>
        </div>
        <div style="font-size:42px; font-weight:bold; color:{risk_color}; margin-top:4px;">
            {overall:.0f}<span style="font-size:16px; color:{CLR_TEXT_SEC};">/100</span>
        </div>
        <div style="font-size:18px; font-weight:600; color:{risk_color}; margin-top:2px;">
            {escape(risk_label)}
        </div>
        <div style="font-size:11px; color:{CLR_TEXT_SEC}; margin-top:6px;">
            Score 100 = Very Low Erosion Risk &nbsp;|&nbsp; Score 0 = Very High Risk
        </div>
    </div>
    """


# =============================================================================
# RENDER
# =============================================================================

def render_soil_erosion_ai_tab():
    """Render the Soil Erosion Risk AI tab in the Streamlit UI."""

    # -- Header card -----------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px; border-radius:12px;
                    border:1px solid {CLR_BORDER}; margin-bottom:20px;">
            <h2 style="margin:0; color:{CLR_TEXT}; font-size:26px;">
                Soil Erosion Risk AI
            </h2>
            <p style="margin:6px 0 0; color:{CLR_TEXT_SEC}; font-size:14px;">
                RUSLE-inspired erosion risk estimation across 5 dimensions: rainfall
                erosivity, soil erodibility, slope, cover management, and conservation
                practices. Powered by SoilGrids, Open-Meteo, Open Topo Data, and
                Overpass API.
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
            key="seai_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="seai_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="seai_lon",
        )

    run_btn = st.button(
        "Analyze Erosion Risk",
        type="primary",
        key="seai_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Analyze Erosion Risk** to begin.")
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching soil, weather, terrain, and land cover data..."):
        result = compute_erosion_risk(lat, lon)

    if not result:
        st.error("Failed to compute erosion risk. Please try again.")
        return

    overall = result["overall"]
    risk_label = result["risk_label"]
    risk_color = result["risk_color"]
    dim_scores = result["dimension_scores"]
    dim_details = result["dimension_details"]
    rusle = result["rusle_factors"]
    recs = result["recommendations"]
    raw = result["raw"]

    # -- Erosion risk gauge ----------------------------------------------------
    st.markdown(
        _build_erosion_gauge(overall, risk_label, risk_color),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # -- Radar chart (5 dimensions) --------------------------------------------
    radar_fig = _build_radar_chart(dim_scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="seai_radar")

    # -- 5 metric cards --------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE}; padding:16px 20px; border-radius:10px;
                    border:1px solid {CLR_BORDER}; margin:16px 0 8px;">
            <h3 style="margin:0; color:{CLR_TEXT}; font-size:18px;">
                Erosion Factor Breakdown
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render 5 cards in a row (3 + 2)
    row1_keys = DIMENSION_KEYS[:3]
    row2_keys = DIMENSION_KEYS[3:]

    for row_keys in [row1_keys, row2_keys]:
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            score_val = dim_scores[key]
            s_color = _risk_color(score_val)
            s_label = _risk_label(score_val)
            f_color = DIMENSION_COLORS.get(key, "#a855f7")
            bar_width = max(5, score_val)
            detail_text = escape(dim_details.get(key, ""))
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE}; border:1px solid {f_color}44;
                                border-radius:10px; padding:16px; text-align:center;
                                min-height:210px;">
                        <div style="font-size:12px; color:{f_color}; margin-bottom:6px;
                                    font-weight:600;">
                            {escape(key)}
                        </div>
                        <div style="font-size:32px; font-weight:700; color:{s_color};">
                            {score_val:.0f}
                        </div>
                        <div style="font-size:11px; color:{s_color}; font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_label)}
                        </div>
                        <div style="background:{CLR_BG}; border-radius:4px; height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color}; width:{bar_width}%;
                                        height:6px; border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px; color:{CLR_TEXT_SEC}; margin-top:6px;
                                    line-height:1.4;">
                            {detail_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- RUSLE factor breakdown bar chart --------------------------------------
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    rusle_fig = _build_rusle_bar_chart(rusle)
    st.plotly_chart(rusle_fig, use_container_width=True, key="seai_rusle")

    # RUSLE product display
    product = rusle.get("product", 0)
    if product < 0.01:
        prod_label = "Very Low"
        prod_color = CLR_VERY_LOW
    elif product < 0.05:
        prod_label = "Low"
        prod_color = CLR_LOW
    elif product < 0.15:
        prod_label = "Moderate"
        prod_color = CLR_MODERATE
    elif product < 0.35:
        prod_label = "High"
        prod_color = CLR_HIGH
    else:
        prod_label = "Very High"
        prod_color = CLR_VERY_HIGH

    st.markdown(
        f"""
        <div style="text-align:center; background:{CLR_BG}; border:1px solid {prod_color}55;
                    border-radius:10px; padding:14px 20px; margin:0 0 16px;">
            <span style="color:{CLR_TEXT_SEC}; font-size:12px; text-transform:uppercase;
                         letter-spacing:1px;">
                RUSLE Composite (R x K x LS x C x P)
            </span>
            <div style="font-size:28px; font-weight:bold; color:{prod_color}; margin-top:4px;">
                {product:.4f}
                <span style="font-size:14px; font-weight:600; margin-left:8px;">
                    {escape(prod_label)}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Key data metrics row --------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE}; padding:16px 20px; border-radius:10px;
                    border:1px solid {CLR_BORDER}; margin:16px 0 8px;">
            <h3 style="margin:0; color:{CLR_TEXT}; font-size:18px;">
                Key Measurements
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mc = st.columns(5)
    mc[0].metric("Annual Precip (est)", f"{raw['annual_precip_est']:.0f} mm")
    mc[1].metric("Avg Slope", f"{raw['avg_slope_deg']:.1f} deg")
    mc[2].metric("Elevation Range", f"{raw['elev_range_m']:.0f} m")
    mc[3].metric("Silt Content",
                 f"{raw['silt_pct']:.0f}%" if raw.get("silt_pct") is not None else "N/A")
    mc[4].metric("Organic Carbon",
                 f"{raw['soc_gkg']:.1f} g/kg" if raw.get("soc_gkg") is not None else "N/A")

    mc2 = st.columns(5)
    mc2[0].metric("Max Daily Rain", f"{raw['max_daily_precip']:.1f} mm")
    mc2[1].metric("Max Slope", f"{raw['max_slope_deg']:.1f} deg")
    mc2[2].metric("Center Elevation", f"{raw['center_elev_m']:.0f} m")
    mc2[3].metric("Clay Content",
                  f"{raw['clay_pct']:.0f}%" if raw.get("clay_pct") is not None else "N/A")
    mc2[4].metric("Conservation Struct.",
                  f"{raw['conservation_structures']}")

    # -- Land cover summary ----------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE}; padding:16px 20px; border-radius:10px;
                    border:1px solid {CLR_BORDER}; margin:16px 0 8px;">
            <h3 style="margin:0; color:{CLR_TEXT}; font-size:18px;">
                Land Cover Inventory
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cover_items = [
        ("Forest", raw.get("forests", 0), "#10b981"),
        ("Grassland", raw.get("grasslands", 0), "#84cc16"),
        ("Cropland", raw.get("croplands", 0), "#f59e0b"),
        ("Bare Soil / Rock", raw.get("bare_soil", 0), "#ef4444"),
    ]

    cover_names = [c[0] for c in cover_items if c[1] > 0]
    cover_counts = [c[1] for c in cover_items if c[1] > 0]
    cover_colors = [c[2] for c in cover_items if c[1] > 0]

    if cover_names:
        cover_fig = go.Figure(go.Bar(
            x=cover_names,
            y=cover_counts,
            marker_color=cover_colors,
            text=cover_counts,
            textposition="auto",
            textfont={"color": CLR_TEXT, "size": 13},
        ))
        cover_fig.update_layout(
            height=280,
            margin=dict(t=20, b=40, l=50, r=30),
            paper_bgcolor=CLR_BG,
            plot_bgcolor=CLR_BG,
            yaxis={"gridcolor": "#2a3550", "tickfont": {"color": CLR_TEXT_SEC}},
            xaxis={"tickfont": {"color": CLR_TEXT, "size": 12}},
        )
        st.plotly_chart(cover_fig, use_container_width=True, key="seai_cover")
    else:
        st.info("No land cover features mapped in the analysis area.")

    # -- Recommendations -------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE}; padding:16px 20px; border-radius:10px;
                    border:1px solid {CLR_BORDER}; margin:20px 0 8px;">
            <h3 style="margin:0; color:{CLR_TEXT}; font-size:18px;">
                Recommendations
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for rec in recs:
        st.markdown(
            f"""
            <div style="background:{CLR_BG}; border:1px solid {CLR_BORDER};
                        border-left:4px solid #a855f7;
                        border-radius:8px; padding:14px 18px; margin:8px 0;">
                <span style="color:{CLR_TEXT}; font-size:14px; line-height:1.5;">
                    {escape(rec)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Footer ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="text-align:center; padding:16px; margin-top:20px;
                    color:{CLR_TEXT_SEC}; font-size:12px;">
            Soil Erosion Risk AI powered by ISRIC SoilGrids, Open-Meteo,
            Open Topo Data &amp; Overpass API | Location: {lat:.4f}, {lon:.4f}
        </div>
        """,
        unsafe_allow_html=True,
    )
