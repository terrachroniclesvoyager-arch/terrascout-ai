# -*- coding: utf-8 -*-
"""
Infrastructure Age & Condition AI -- Estimates infrastructure maturity,
building stock age, road quality, utility coverage, maintenance levels and
modernization score for any location.
Uses: Overpass API, Open Topo Data.
Part of TerraScout AI (264+ modules).
"""

import logging
import math
import re
from datetime import datetime

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests
import streamlit as st

from src.deep_zone_analysis import ANALYSIS_PRESETS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CURRENT_YEAR = datetime.now().year

INFRA_AGE_COMPONENTS = {
    "building_stock_age": {
        "name": "Building Stock Age",
        "color": "#f59e0b",
        "weight": 0.25,
    },
    "road_quality": {
        "name": "Road Quality",
        "color": "#3b82f6",
        "weight": 0.20,
    },
    "utility_coverage": {
        "name": "Utility Coverage",
        "color": "#22c55e",
        "weight": 0.20,
    },
    "maintenance_level": {
        "name": "Maintenance Level",
        "color": "#ef4444",
        "weight": 0.15,
    },
    "modernization_score": {
        "name": "Modernization Score",
        "color": "#8b5cf6",
        "weight": 0.20,
    },
}

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

# Surface quality scores (higher = better)
SURFACE_QUALITY = {
    "asphalt": 95,
    "concrete": 90,
    "paving_stones": 80,
    "sett": 70,
    "cobblestone": 60,
    "compacted": 50,
    "fine_gravel": 45,
    "gravel": 35,
    "pebblestone": 30,
    "ground": 20,
    "dirt": 15,
    "mud": 10,
    "sand": 10,
    "grass": 5,
    "unpaved": 20,
    "paved": 85,
}

# Road class weights for quality assessment
ROAD_CLASS_IMPORTANCE = {
    "motorway": 5,
    "trunk": 4,
    "primary": 4,
    "secondary": 3,
    "tertiary": 2,
    "residential": 1,
    "service": 1,
    "unclassified": 1,
    "living_street": 1,
    "pedestrian": 1,
    "track": 0.5,
    "path": 0.3,
    "footway": 0.3,
    "cycleway": 0.5,
}


# ---------------------------------------------------------------------------
# Date parsing utilities
# ---------------------------------------------------------------------------


def _parse_start_date(raw_date):
    """
    Parse OSM start_date tags into a year integer.
    Handles formats: '1980', '1980s', 'C19', 'C20', '19th century',
    '1980-05', '1980-05-23', 'early 1900s', 'late 1800s',
    'before 1950', 'after 1960', '~1970', 'circa 1850', etc.
    Returns an integer year or None if unparseable.
    """
    if raw_date is None:
        return None

    s = str(raw_date).strip()
    if not s:
        return None

    try:
        # Exact 4-digit year: "1980"
        match = re.match(r"^(\d{4})$", s)
        if match:
            yr = int(match.group(1))
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # Year with month/day: "1980-05" or "1980-05-23"
        match = re.match(r"^(\d{4})-\d{1,2}", s)
        if match:
            yr = int(match.group(1))
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # Decade: "1980s" or "1980er"
        match = re.match(r"^(\d{4})s", s, re.IGNORECASE)
        if match:
            yr = int(match.group(1)) + 5  # mid-decade
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # Century notation: "C19", "C20", "C18"
        match = re.match(r"^[Cc](\d{1,2})$", s)
        if match:
            century = int(match.group(1))
            yr = (century - 1) * 100 + 50  # mid-century
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # "19th century", "20th century"
        match = re.match(r"^(\d{1,2})(st|nd|rd|th)\s+century", s, re.IGNORECASE)
        if match:
            century = int(match.group(1))
            yr = (century - 1) * 100 + 50
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # "early 1900s" / "late 1800s" / "mid 1900s"
        match = re.match(r"^(early|mid|late)\s+(\d{4})s?", s, re.IGNORECASE)
        if match:
            modifier = match.group(1).lower()
            base = int(match.group(2))
            if modifier == "early":
                yr = base + 15
            elif modifier == "late":
                yr = base + 85
            else:
                yr = base + 50
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # "before 1950" / "after 1960" / "circa 1850" / "~1970" / "ca. 1900"
        match = re.match(
            r"^(?:before|after|circa|ca\.?|~|approx\.?)\s*(\d{4})",
            s,
            re.IGNORECASE,
        )
        if match:
            yr = int(match.group(1))
            if 1000 <= yr <= CURRENT_YEAR:
                return yr

        # Last resort: find any 4-digit number that looks like a year
        match = re.search(r"(\d{4})", s)
        if match:
            yr = int(match.group(1))
            if 1500 <= yr <= CURRENT_YEAR:
                return yr

    except (ValueError, TypeError):
        pass

    return None


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_infrastructure_age(lat, lon, radius=2000):
    """Fetch infrastructure data from Overpass API for age & condition analysis."""
    query = f"""
    [out:json][timeout:30];
    (
      way["building"]["start_date"](around:{radius},{lat},{lon});
      way["building"](around:{radius},{lat},{lon});
      way["highway"]["surface"](around:{radius},{lat},{lon});
      way["highway"](around:{radius},{lat},{lon});
      node["power"](around:{radius},{lat},{lon});
      way["power"](around:{radius},{lat},{lon});
      node["man_made"="water_tower"](around:{radius},{lat},{lon});
      way["man_made"="pipeline"](around:{radius},{lat},{lon});
      way["bridge"](around:{radius},{lat},{lon});
      node["man_made"="tower"]["tower:type"="communication"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Overpass infrastructure age error: %s", e)
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_for_infra(lat, lon):
    """Fetch elevation from Open Topo Data for terrain context."""
    try:
        resp = requests.get(
            OPEN_TOPO_API,
            params={"locations": f"{lat},{lon}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("elevation")
    except Exception as e:
        logger.warning("Elevation fetch error: %s", e)
    return None


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def compute_infrastructure_age(lat, lon):
    """Compute infrastructure age & condition analysis across 5 dimensions."""
    data = fetch_infrastructure_age(lat, lon)
    elements = data.get("elements", [])

    # Categorize elements safely
    buildings = [e for e in elements if e.get("tags", {}).get("building")]
    buildings_with_date = [
        e for e in buildings if e.get("tags", {}).get("start_date")
    ]
    roads_with_surface = [
        e
        for e in elements
        if e.get("tags", {}).get("highway") and e.get("tags", {}).get("surface")
    ]
    all_roads = [e for e in elements if e.get("tags", {}).get("highway")]
    power_nodes = [
        e for e in elements if e.get("type") == "node" and e.get("tags", {}).get("power")
    ]
    power_ways = [
        e for e in elements if e.get("type") == "way" and e.get("tags", {}).get("power")
    ]
    water_towers = [
        e
        for e in elements
        if e.get("tags", {}).get("man_made") == "water_tower"
    ]
    pipelines = [
        e
        for e in elements
        if e.get("tags", {}).get("man_made") == "pipeline"
    ]
    bridges = [e for e in elements if e.get("tags", {}).get("bridge")]
    telecom_towers = [
        e
        for e in elements
        if e.get("tags", {}).get("man_made") == "tower"
        and e.get("tags", {}).get("tower:type") == "communication"
    ]

    scores = {}
    details = {}

    # ======================================================================
    # 1. BUILDING STOCK AGE (0-100, higher = newer/better maintained)
    # ======================================================================
    parsed_years = []
    decade_distribution = {}
    for b in buildings_with_date:
        raw = b.get("tags", {}).get("start_date", "")
        yr = _parse_start_date(raw)
        if yr is not None:
            parsed_years.append(yr)
            decade = (yr // 10) * 10
            decade_distribution[decade] = decade_distribution.get(decade, 0) + 1

    if parsed_years:
        avg_year = sum(parsed_years) / len(parsed_years)
        median_year = sorted(parsed_years)[len(parsed_years) // 2]
        oldest = min(parsed_years)
        newest = max(parsed_years)
        age_span = newest - oldest
        avg_age = CURRENT_YEAR - avg_year

        # Score: newer stock = higher score.  0-10 years => ~95, 50 years => ~60, 100+ => ~30
        age_score = max(0, min(100, 100 - (avg_age * 0.7)))
    else:
        avg_year = None
        median_year = None
        oldest = None
        newest = None
        age_span = 0
        avg_age = None
        # No date data: estimate from building count (more buildings = likely older area)
        bld_count = len(buildings)
        if bld_count > 200:
            age_score = 45  # lots of buildings, likely established area
        elif bld_count > 50:
            age_score = 55
        elif bld_count > 10:
            age_score = 60
        else:
            age_score = 50  # unknown

    scores["building_stock_age"] = round(age_score)
    details["building_stock_age"] = {
        "total_buildings": len(buildings),
        "buildings_with_date": len(buildings_with_date),
        "parsed_dates": len(parsed_years),
        "average_year": round(avg_year) if avg_year is not None else "N/A",
        "median_year": median_year if median_year is not None else "N/A",
        "oldest": oldest if oldest is not None else "N/A",
        "newest": newest if newest is not None else "N/A",
        "age_span_years": age_span,
        "average_age": round(avg_age) if avg_age is not None else "N/A",
    }

    # ======================================================================
    # 2. ROAD QUALITY (0-100)
    # ======================================================================
    surface_counts = {}
    surface_quality_scores = []
    for r in roads_with_surface:
        surf = r.get("tags", {}).get("surface", "").lower().strip()
        if surf:
            surface_counts[surf] = surface_counts.get(surf, 0) + 1
            quality = SURFACE_QUALITY.get(surf, 40)
            highway_type = r.get("tags", {}).get("highway", "unclassified")
            importance = ROAD_CLASS_IMPORTANCE.get(highway_type, 1)
            surface_quality_scores.append(quality * importance)

    paved_count = sum(
        v
        for k, v in surface_counts.items()
        if k in ("asphalt", "concrete", "paving_stones", "paved", "sett")
    )
    unpaved_count = sum(
        v
        for k, v in surface_counts.items()
        if k in ("unpaved", "ground", "dirt", "mud", "sand", "grass", "gravel")
    )
    total_with_surface = len(roads_with_surface)
    total_roads_count = len(all_roads)

    if surface_quality_scores:
        weighted_avg = sum(surface_quality_scores) / sum(
            ROAD_CLASS_IMPORTANCE.get(
                r.get("tags", {}).get("highway", "unclassified"), 1
            )
            for r in roads_with_surface
        )
        # Factor in surface data coverage
        coverage_ratio = total_with_surface / max(1, total_roads_count)
        road_score = weighted_avg * 0.7 + coverage_ratio * 30
        road_score = min(100, max(0, road_score))
    elif total_roads_count > 0:
        # Roads exist but no surface tags: moderate score
        road_score = 50
    else:
        road_score = 0

    paved_ratio = paved_count / max(1, paved_count + unpaved_count)

    scores["road_quality"] = round(road_score)
    details["road_quality"] = {
        "total_roads": total_roads_count,
        "roads_with_surface": total_with_surface,
        "paved_roads": paved_count,
        "unpaved_roads": unpaved_count,
        "paved_ratio": f"{paved_ratio:.0%}",
        "surface_types": dict(
            sorted(surface_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ),
    }

    # ======================================================================
    # 3. UTILITY COVERAGE (0-100)
    # ======================================================================
    power_total = len(power_nodes) + len(power_ways)
    water_total = len(water_towers) + len(pipelines)
    telecom_total = len(telecom_towers)

    # Power sub-types
    power_line_count = sum(
        1
        for e in power_ways
        if e.get("tags", {}).get("power") in ("line", "minor_line", "cable")
    )
    power_pole_count = sum(
        1 for e in power_nodes if e.get("tags", {}).get("power") == "pole"
    )
    power_tower_count = sum(
        1 for e in power_nodes if e.get("tags", {}).get("power") == "tower"
    )
    substation_count = sum(
        1
        for e in (power_nodes + power_ways)
        if e.get("tags", {}).get("power") == "substation"
    )
    transformer_count = sum(
        1
        for e in (power_nodes + power_ways)
        if e.get("tags", {}).get("power") == "transformer"
    )

    # Utility score based on counts
    power_score_raw = min(40, power_total * 2)
    water_score_raw = min(30, water_total * 10)
    telecom_score_raw = min(30, telecom_total * 15)

    utility_score = min(100, power_score_raw + water_score_raw + telecom_score_raw)

    scores["utility_coverage"] = round(utility_score)
    details["utility_coverage"] = {
        "power_elements": power_total,
        "power_lines": power_line_count,
        "power_poles": power_pole_count,
        "power_towers": power_tower_count,
        "substations": substation_count,
        "transformers": transformer_count,
        "water_towers": len(water_towers),
        "pipelines": len(pipelines),
        "telecom_towers": telecom_total,
    }

    # ======================================================================
    # 4. MAINTENANCE LEVEL (0-100)
    # ======================================================================
    # Infer maintenance from: surface quality, bridge conditions, building conditions
    condition_tags_count = 0
    good_condition_count = 0
    bad_condition_count = 0

    for e in elements:
        tags = e.get("tags", {})
        # Check various condition-related tags
        condition = tags.get("condition", tags.get("bridge:condition", ""))
        if condition:
            condition_tags_count += 1
            if condition.lower() in ("good", "excellent", "new"):
                good_condition_count += 1
            elif condition.lower() in ("bad", "poor", "ruined", "collapsed"):
                bad_condition_count += 1

        surface_cond = tags.get("surface:condition", tags.get("smoothness", ""))
        if surface_cond:
            condition_tags_count += 1
            if surface_cond.lower() in ("excellent", "good", "intermediate"):
                good_condition_count += 1
            elif surface_cond.lower() in ("bad", "very_bad", "horrible", "impassable"):
                bad_condition_count += 1

    # Maintenance proxies
    bridge_count = len(bridges)
    bridge_with_material = sum(
        1
        for b in bridges
        if b.get("tags", {}).get("bridge:material")
        or b.get("tags", {}).get("bridge:structure")
    )

    # Lit roads (street lighting = maintenance indicator)
    lit_roads = sum(
        1
        for r in all_roads
        if r.get("tags", {}).get("lit") == "yes"
    )
    sidewalks = sum(
        1
        for r in all_roads
        if r.get("tags", {}).get("sidewalk") in ("both", "left", "right", "yes")
    )

    # Compute maintenance score
    maint_score = 50  # baseline

    # Surface quality influence
    if paved_ratio > 0.8:
        maint_score += 15
    elif paved_ratio > 0.5:
        maint_score += 8
    elif paved_ratio < 0.2 and total_with_surface > 0:
        maint_score -= 10

    # Lit roads bonus
    if total_roads_count > 0:
        lit_ratio = lit_roads / max(1, total_roads_count)
        maint_score += min(15, lit_ratio * 30)

    # Sidewalk bonus
    if total_roads_count > 0:
        sw_ratio = sidewalks / max(1, total_roads_count)
        maint_score += min(10, sw_ratio * 20)

    # Condition tags
    if condition_tags_count > 0:
        good_ratio = good_condition_count / max(1, condition_tags_count)
        bad_ratio = bad_condition_count / max(1, condition_tags_count)
        maint_score += (good_ratio - bad_ratio) * 15

    maint_score = max(0, min(100, maint_score))

    scores["maintenance_level"] = round(maint_score)
    details["maintenance_level"] = {
        "bridges": bridge_count,
        "bridges_with_material_info": bridge_with_material,
        "lit_roads": lit_roads,
        "roads_with_sidewalks": sidewalks,
        "condition_tags_found": condition_tags_count,
        "good_condition": good_condition_count,
        "bad_condition": bad_condition_count,
        "paved_ratio": f"{paved_ratio:.0%}",
    }

    # ======================================================================
    # 5. MODERNIZATION SCORE (0-100)
    # ======================================================================
    # Recent construction ratio (buildings built in last 20 years)
    recent_threshold = CURRENT_YEAR - 20
    recent_buildings = sum(1 for yr in parsed_years if yr >= recent_threshold)
    very_old_buildings = sum(1 for yr in parsed_years if yr < 1950)

    if parsed_years:
        recent_ratio = recent_buildings / len(parsed_years)
        old_ratio = very_old_buildings / len(parsed_years)
    else:
        recent_ratio = 0
        old_ratio = 0

    # Modern infrastructure indicators
    fiber_optic = sum(
        1
        for e in elements
        if "fibre" in str(e.get("tags", {}).get("cable", "")).lower()
        or "fiber" in str(e.get("tags", {}).get("cable", "")).lower()
        or e.get("tags", {}).get("telecom") == "fibre"
    )
    solar = sum(
        1
        for e in elements
        if e.get("tags", {}).get("generator:source") == "solar"
        or e.get("tags", {}).get("power") == "generator"
        and "solar" in str(e.get("tags", {}).get("generator:source", "")).lower()
    )
    ev_charging = sum(
        1
        for e in elements
        if e.get("tags", {}).get("amenity") == "charging_station"
    )

    # Compute modernization score
    modern_score = 30  # baseline

    # Recent construction bonus
    modern_score += recent_ratio * 35

    # Old buildings penalty
    modern_score -= old_ratio * 15

    # Telecom bonus
    modern_score += min(10, telecom_total * 3)

    # Modern amenities bonus
    modern_score += min(10, fiber_optic * 5 + solar * 3 + ev_charging * 3)

    # Power infrastructure maturity
    if substation_count > 0:
        modern_score += min(5, substation_count * 2.5)

    # Road surface quality influence
    if road_score > 70:
        modern_score += 10
    elif road_score > 50:
        modern_score += 5

    modern_score = max(0, min(100, modern_score))

    scores["modernization_score"] = round(modern_score)
    details["modernization_score"] = {
        "recent_buildings_20yr": recent_buildings,
        "recent_ratio": f"{recent_ratio:.0%}",
        "very_old_pre1950": very_old_buildings,
        "old_ratio": f"{old_ratio:.0%}",
        "telecom_towers": telecom_total,
        "fiber_optic_indicators": fiber_optic,
        "solar_installations": solar,
        "ev_charging_stations": ev_charging,
        "substations": substation_count,
    }

    # ======================================================================
    # OVERALL WEIGHTED SCORE
    # ======================================================================
    overall = sum(
        scores.get(k, 0) * INFRA_AGE_COMPONENTS[k]["weight"] for k in scores
    )
    overall = round(overall)

    if overall >= 75:
        ov_class = "Modern Infrastructure"
        ov_color = "#22c55e"
    elif overall >= 55:
        ov_class = "Mature Infrastructure"
        ov_color = "#3b82f6"
    elif overall >= 40:
        ov_class = "Aging Infrastructure"
        ov_color = "#f59e0b"
    elif overall >= 20:
        ov_class = "Legacy Infrastructure"
        ov_color = "#ef4444"
    else:
        ov_class = "Minimal Infrastructure"
        ov_color = "#6b7280"

    return {
        "overall": overall,
        "overall_class": ov_class,
        "overall_color": ov_color,
        "scores": scores,
        "details": details,
        "decade_distribution": decade_distribution,
        "surface_counts": surface_counts,
    }


# ---------------------------------------------------------------------------
# Plotly chart builders (dark-theme compatible)
# ---------------------------------------------------------------------------

_CHART_BG = "#1a1a2e"
_CHART_PAPER = "#1a1a2e"
_CHART_FONT_COLOR = "#e2e8f0"


def _build_radar_chart(scores):
    """Build a radar chart of the 5 infrastructure dimensions."""
    categories = []
    values = []
    colors = []
    for key, meta in INFRA_AGE_COMPONENTS.items():
        categories.append(meta["name"])
        values.append(scores.get(key, 0))
        colors.append(meta["color"])

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(139,92,246,0.25)",
            line=dict(color="#8b5cf6", width=2),
            marker=dict(size=6, color=colors + [colors[0]]),
            name="Score",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor=_CHART_BG,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#94a3b8"),
                gridcolor="rgba(148,163,184,0.15)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=_CHART_FONT_COLOR),
                gridcolor="rgba(148,163,184,0.15)",
            ),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
        height=420,
    )
    return fig


def _build_decade_histogram(decade_distribution):
    """Bar chart showing building construction decade distribution."""
    if not decade_distribution:
        return None

    sorted_decades = sorted(decade_distribution.items(), key=lambda x: x[0])
    labels = [f"{d}s" for d, _ in sorted_decades]
    counts = [c for _, c in sorted_decades]

    # Color gradient from old (amber) to new (green)
    max_decade = max(d for d, _ in sorted_decades) if sorted_decades else 2020
    min_decade = min(d for d, _ in sorted_decades) if sorted_decades else 1900
    span = max(1, max_decade - min_decade)
    colors = []
    for d, _ in sorted_decades:
        ratio = (d - min_decade) / span
        r = int(245 * (1 - ratio) + 34 * ratio)
        g = int(158 * (1 - ratio) + 197 * ratio)
        b = int(11 * (1 - ratio) + 94 * ratio)
        colors.append(f"rgb({r},{g},{b})")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=counts,
            marker=dict(color=colors, line=dict(width=0)),
            text=counts,
            textposition="outside",
            textfont=dict(color=_CHART_FONT_COLOR, size=11),
        )
    )
    fig.update_layout(
        title=dict(
            text="Building Construction by Decade",
            font=dict(size=14, color=_CHART_FONT_COLOR),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        xaxis=dict(
            title="Decade",
            tickfont=dict(color="#94a3b8", size=11),
            gridcolor="rgba(148,163,184,0.15)",
        ),
        yaxis=dict(
            title="Buildings",
            tickfont=dict(color="#94a3b8"),
            gridcolor="rgba(148,163,184,0.15)",
        ),
        margin=dict(l=50, r=30, t=50, b=50),
        height=380,
    )
    return fig


def _build_surface_pie(surface_counts):
    """Pie chart showing road surface type distribution."""
    if not surface_counts:
        return None

    sorted_surfaces = sorted(surface_counts.items(), key=lambda x: x[1], reverse=True)
    top_n = sorted_surfaces[:12]
    labels = [s[0].replace("_", " ").title() for s in top_n]
    values = [s[1] for s in top_n]

    # Color-code by quality
    colors = []
    for s, _ in top_n:
        quality = SURFACE_QUALITY.get(s.lower(), 40)
        if quality >= 80:
            colors.append("#22c55e")
        elif quality >= 50:
            colors.append("#3b82f6")
        elif quality >= 30:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")

    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color=_CHART_BG, width=2)),
            hole=0.45,
            textinfo="label+percent",
            textfont=dict(color=_CHART_FONT_COLOR, size=11),
        )
    )
    fig.update_layout(
        title=dict(
            text="Road Surface Types",
            font=dict(size=14, color=_CHART_FONT_COLOR),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(font=dict(color=_CHART_FONT_COLOR, size=11)),
        height=380,
    )
    return fig


def _build_utility_bar(details):
    """Horizontal bar chart for utility coverage breakdown."""
    util_details = details.get("utility_coverage", {})
    categories = [
        ("Power Lines", util_details.get("power_lines", 0)),
        ("Power Poles", util_details.get("power_poles", 0)),
        ("Power Towers", util_details.get("power_towers", 0)),
        ("Substations", util_details.get("substations", 0)),
        ("Transformers", util_details.get("transformers", 0)),
        ("Water Towers", util_details.get("water_towers", 0)),
        ("Pipelines", util_details.get("pipelines", 0)),
        ("Telecom Towers", util_details.get("telecom_towers", 0)),
    ]
    # Filter out zeros
    categories = [(label, val) for label, val in categories if val and val > 0]
    if not categories:
        return None

    labels = [c[0] for c in categories]
    values = [c[1] for c in categories]

    bar_colors = [
        "#f59e0b", "#f59e0b", "#f59e0b", "#ef4444", "#ef4444",
        "#3b82f6", "#3b82f6", "#8b5cf6",
    ]
    colors_filtered = bar_colors[: len(labels)]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors_filtered, line=dict(width=0)),
            text=values,
            textposition="outside",
            textfont=dict(color=_CHART_FONT_COLOR, size=11),
        )
    )
    fig.update_layout(
        title=dict(
            text="Utility Infrastructure Breakdown",
            font=dict(size=14, color=_CHART_FONT_COLOR),
        ),
        paper_bgcolor=_CHART_PAPER,
        plot_bgcolor=_CHART_BG,
        font=dict(color=_CHART_FONT_COLOR),
        xaxis=dict(
            title="Count",
            gridcolor="rgba(148,163,184,0.15)",
            tickfont=dict(color="#94a3b8"),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color=_CHART_FONT_COLOR, size=11),
        ),
        margin=dict(l=130, r=40, t=50, b=40),
        height=max(280, len(labels) * 36 + 80),
    )
    return fig


# ---------------------------------------------------------------------------
# HTML card helpers
# ---------------------------------------------------------------------------


def _render_overall_card(result):
    """Render the big overall score header card."""
    overall = result.get("overall", 0) or 0
    ov_class = result.get("overall_class", "Unknown")
    ov_color = result.get("overall_color", "#6b7280")
    bsa = result.get("details", {}).get("building_stock_age", {})
    rq = result.get("details", {}).get("road_quality", {})
    uc = result.get("details", {}).get("utility_coverage", {})

    avg_year = bsa.get("average_year", "N/A")
    total_bld = bsa.get("total_buildings", 0) or 0
    total_roads = rq.get("total_roads", 0) or 0
    power_elems = uc.get("power_elements", 0) or 0

    html_str = f"""
    <div style="
        background: linear-gradient(135deg, {ov_color}22, {ov_color}44);
        border: 1px solid {ov_color}88;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 20px;
        text-align: center;
    ">
        <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;
                    letter-spacing: 2px; margin-bottom: 8px;">
            Infrastructure Age &amp; Condition
        </div>
        <div style="font-size: 56px; font-weight: 800; color: {ov_color};
                    line-height: 1.1;">
            {overall}<span style="font-size: 22px; color: #94a3b8;">/100</span>
        </div>
        <div style="font-size: 20px; font-weight: 600; color: {ov_color};
                    margin-top: 4px;">
            {ov_class}
        </div>
        <div style="
            display: flex; justify-content: center; gap: 32px;
            margin-top: 16px; flex-wrap: wrap;
        ">
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Avg. Build Year</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {avg_year}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Buildings</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {total_bld:,}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Roads</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {total_roads:,}
                </span>
            </div>
            <div>
                <span style="color: #94a3b8; font-size: 12px;">Power Elements</span><br>
                <span style="color: #e2e8f0; font-size: 15px; font-weight: 600;">
                    {power_elems:,}
                </span>
            </div>
        </div>
    </div>
    """
    st.markdown(html_str, unsafe_allow_html=True)


def _metric_card_html(title, score, color, detail_lines):
    """Return HTML for a single metric card."""
    bar_width = max(0, min(100, score or 0))
    lines_html = ""
    for label, value in detail_lines:
        lines_html += f"""
        <div style="display:flex; justify-content:space-between;
                    font-size:12px; padding:2px 0;">
            <span style="color:#94a3b8;">{label}</span>
            <span style="color:#e2e8f0; font-weight:600;">{value}</span>
        </div>
        """
    return f"""
    <div style="
        background: #1a1a2e;
        border: 1px solid {color}55;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        min-height: 220px;
    ">
        <div style="display:flex; justify-content:space-between;
                    align-items:center; margin-bottom: 10px;">
            <span style="font-size:14px; font-weight:700; color:{color};">
                {title}
            </span>
            <span style="font-size:22px; font-weight:800; color:{color};">
                {score}
            </span>
        </div>
        <div style="
            background: #0f0f23;
            border-radius: 6px;
            height: 6px;
            margin-bottom: 14px;
            overflow: hidden;
        ">
            <div style="
                width: {bar_width}%;
                height: 100%;
                background: {color};
                border-radius: 6px;
            "></div>
        </div>
        {lines_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_infrastructure_age_tab():
    """Entry point: Infrastructure Age & Condition AI tab."""

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #8b5cf622, #3b82f622);
            border: 1px solid #8b5cf655;
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 20px;
        ">
            <span style="font-size:22px; font-weight:700; color:#8b5cf6;">
                Infrastructure Age &amp; Condition AI
            </span><br>
            <span style="font-size:13px; color:#94a3b8;">
                Estimates infrastructure maturity through building stock age,
                road quality, utility coverage, maintenance levels and
                modernization indicators using OSM data &amp; terrain context.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="ia_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude",
            value=default_lat,
            format="%.5f",
            min_value=-90.0,
            max_value=90.0,
            key="ia_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="ia_lon",
        )

    run_btn = st.button(
        "Analyze Infrastructure Age",
        type="primary",
        key="ia_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and press **Analyze Infrastructure Age** to begin."
        )
        return

    # -- Fetch & compute --------------------------------------------------
    with st.spinner(
        "Querying Overpass API for buildings, roads, utilities & bridges..."
    ):
        result = compute_infrastructure_age(lat, lon)

    if result is None:
        st.error("Analysis failed. Please try again.")
        return

    scores = result.get("scores", {})
    details = result.get("details", {})
    decade_distribution = result.get("decade_distribution", {})
    surface_counts = result.get("surface_counts", {})

    # -- Overall header card ----------------------------------------------
    _render_overall_card(result)

    # -- Elevation context ------------------------------------------------
    elev = fetch_elevation_for_infra(lat, lon)
    if elev is not None:
        st.caption(f"Elevation at location: **{elev:,.0f} m** above sea level")

    # -- Radar chart ------------------------------------------------------
    st.subheader("Infrastructure Profile Radar")
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="infage_pchart1")

    # -- 5 metric cards (3 + 2 layout) ------------------------------------
    st.subheader("Dimension Breakdown")

    # Row 1: 3 cards
    r1c1, r1c2, r1c3 = st.columns(3)

    # Building Stock Age card
    bsa = details.get("building_stock_age", {})
    with r1c1:
        st.markdown(
            _metric_card_html(
                "Building Stock Age",
                scores.get("building_stock_age", 0),
                "#f59e0b",
                [
                    ("Total Buildings", f"{bsa.get('total_buildings', 0):,}"),
                    ("With Dates", f"{bsa.get('buildings_with_date', 0):,}"),
                    ("Avg. Year", f"{bsa.get('average_year', 'N/A')}"),
                    ("Median Year", f"{bsa.get('median_year', 'N/A')}"),
                    ("Oldest", f"{bsa.get('oldest', 'N/A')}"),
                    ("Newest", f"{bsa.get('newest', 'N/A')}"),
                    ("Avg. Age (yrs)", f"{bsa.get('average_age', 'N/A')}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Road Quality card
    rq = details.get("road_quality", {})
    with r1c2:
        st.markdown(
            _metric_card_html(
                "Road Quality",
                scores.get("road_quality", 0),
                "#3b82f6",
                [
                    ("Total Roads", f"{rq.get('total_roads', 0):,}"),
                    ("With Surface Info", f"{rq.get('roads_with_surface', 0):,}"),
                    ("Paved Roads", f"{rq.get('paved_roads', 0):,}"),
                    ("Unpaved Roads", f"{rq.get('unpaved_roads', 0):,}"),
                    ("Paved Ratio", f"{rq.get('paved_ratio', '0%')}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Utility Coverage card
    uc = details.get("utility_coverage", {})
    with r1c3:
        st.markdown(
            _metric_card_html(
                "Utility Coverage",
                scores.get("utility_coverage", 0),
                "#22c55e",
                [
                    ("Power Elements", f"{uc.get('power_elements', 0):,}"),
                    ("Power Lines", f"{uc.get('power_lines', 0):,}"),
                    ("Substations", f"{uc.get('substations', 0)}"),
                    ("Water Towers", f"{uc.get('water_towers', 0)}"),
                    ("Pipelines", f"{uc.get('pipelines', 0)}"),
                    ("Telecom Towers", f"{uc.get('telecom_towers', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Row 2: 2 cards
    r2c1, r2c2 = st.columns(2)

    # Maintenance Level card
    ml = details.get("maintenance_level", {})
    with r2c1:
        st.markdown(
            _metric_card_html(
                "Maintenance Level",
                scores.get("maintenance_level", 0),
                "#ef4444",
                [
                    ("Bridges", f"{ml.get('bridges', 0):,}"),
                    ("Bridge Material Info", f"{ml.get('bridges_with_material_info', 0)}"),
                    ("Lit Roads", f"{ml.get('lit_roads', 0):,}"),
                    ("Sidewalks", f"{ml.get('roads_with_sidewalks', 0):,}"),
                    ("Condition Tags", f"{ml.get('condition_tags_found', 0)}"),
                    ("Good Condition", f"{ml.get('good_condition', 0)}"),
                    ("Bad Condition", f"{ml.get('bad_condition', 0)}"),
                    ("Paved Ratio", f"{ml.get('paved_ratio', '0%')}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # Modernization Score card
    ms = details.get("modernization_score", {})
    with r2c2:
        st.markdown(
            _metric_card_html(
                "Modernization Score",
                scores.get("modernization_score", 0),
                "#8b5cf6",
                [
                    ("Recent (< 20yr)", f"{ms.get('recent_buildings_20yr', 0):,}"),
                    ("Recent Ratio", f"{ms.get('recent_ratio', '0%')}"),
                    ("Pre-1950", f"{ms.get('very_old_pre1950', 0):,}"),
                    ("Old Ratio", f"{ms.get('old_ratio', '0%')}"),
                    ("Telecom Towers", f"{ms.get('telecom_towers', 0)}"),
                    ("Fiber Optic", f"{ms.get('fiber_optic_indicators', 0)}"),
                    ("Solar", f"{ms.get('solar_installations', 0)}"),
                    ("EV Charging", f"{ms.get('ev_charging_stations', 0)}"),
                ],
            ),
            unsafe_allow_html=True,
        )

    # -- Charts -----------------------------------------------------------
    st.subheader("Detailed Charts")
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        decade_fig = _build_decade_histogram(decade_distribution)
        if decade_fig is not None:
            st.plotly_chart(decade_fig, use_container_width=True, key="infage_pchart2")
        else:
            st.info("No building date data available for decade distribution.")

    with chart_c2:
        surface_fig = _build_surface_pie(surface_counts)
        if surface_fig is not None:
            st.plotly_chart(surface_fig, use_container_width=True, key="infage_pchart3")
        else:
            st.info("No road surface data available for this location.")

    # Utility breakdown chart (full width)
    util_fig = _build_utility_bar(details)
    if util_fig is not None:
        st.plotly_chart(util_fig, use_container_width=True, key="infage_pchart4")

    # -- AI Interpretation ------------------------------------------------
    st.subheader("AI Interpretation")
    interpretation_lines = []

    bsa_score = scores.get("building_stock_age", 0)
    if bsa_score >= 70:
        interpretation_lines.append(
            "The building stock is **relatively modern**, with many structures "
            "dating from recent decades. This suggests active development."
        )
    elif bsa_score >= 45:
        interpretation_lines.append(
            "The building stock shows a **mixed age profile**, with a blend of "
            "older and newer construction indicating gradual development."
        )
    else:
        interpretation_lines.append(
            "The building stock is **predominantly older**, suggesting a "
            "historically established area with limited recent construction."
        )

    rq_score = scores.get("road_quality", 0)
    if rq_score >= 70:
        interpretation_lines.append(
            "Road infrastructure is **well-maintained** with predominantly paved "
            "surfaces, indicating good transportation investment."
        )
    elif rq_score >= 40:
        interpretation_lines.append(
            "Road quality is **moderate** with a mix of paved and unpaved "
            "surfaces. Some improvement opportunities exist."
        )
    else:
        interpretation_lines.append(
            "Road conditions are **below average** with significant unpaved "
            "or poorly surfaced routes. Infrastructure investment may be needed."
        )

    uc_score = scores.get("utility_coverage", 0)
    if uc_score >= 70:
        interpretation_lines.append(
            "**Strong utility coverage** detected with power grid, water "
            "infrastructure and telecommunications well-represented."
        )
    elif uc_score >= 35:
        interpretation_lines.append(
            "**Moderate utility coverage** with some infrastructure present "
            "but potential gaps in water or telecom services."
        )
    else:
        interpretation_lines.append(
            "**Limited utility infrastructure** detected. The area may rely "
            "on distributed or informal services."
        )

    ml_score = scores.get("maintenance_level", 0)
    if ml_score >= 65:
        interpretation_lines.append(
            "Infrastructure **maintenance level is good**, with street lighting, "
            "sidewalks and well-documented conditions."
        )
    elif ml_score >= 40:
        interpretation_lines.append(
            "**Maintenance is average** -- some indicators of upkeep are present "
            "but there are areas needing attention."
        )
    else:
        interpretation_lines.append(
            "**Maintenance appears low** based on limited lighting, sidewalks "
            "and condition data. Deferred maintenance is likely."
        )

    ms_score = scores.get("modernization_score", 0)
    if ms_score >= 65:
        interpretation_lines.append(
            "The area shows **strong modernization signals** with recent "
            "construction, advanced telecom and modern energy infrastructure."
        )
    elif ms_score >= 35:
        interpretation_lines.append(
            "**Some modernization** is underway, but legacy infrastructure "
            "still dominates. Upgrading is in progress."
        )
    else:
        interpretation_lines.append(
            "**Limited modernization** detected. The infrastructure largely "
            "reflects older construction patterns."
        )

    for line in interpretation_lines:
        st.markdown(f"- {line}", unsafe_allow_html=True)

    # -- Raw data expander ------------------------------------------------
    with st.expander("Raw Analysis Data"):
        st.json(result)
