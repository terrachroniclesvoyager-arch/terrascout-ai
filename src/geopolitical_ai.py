"""
Geopolitical Analysis AI module for TerraScout AI.
Analyses border proximity, strategic infrastructure, resource control,
terrain advantage, connectivity and stability indicators for any
geographic point.

Data sources (all FREE, no API key):
  - Overpass API   -- borders, military areas, embassies, customs, gov buildings
  - Open-Meteo     -- climate context (via deep_zone_analysis)
  - Open Topo Data -- terrain / elevation grid for border-defense analysis
  - USGS Earthquakes -- tectonic-border correlation & seismic stability
"""

import logging
import math

import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_landuse_infrastructure,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

GEOPOLITICAL_COMPONENTS = {
    "border": {
        "name": "Border Proximity",
        "color": "#ef4444",
        "weight": 0.20,
    },
    "strategic": {
        "name": "Strategic Infrastructure",
        "color": "#6366f1",
        "weight": 0.20,
    },
    "resources": {
        "name": "Resource Control",
        "color": "#f59e0b",
        "weight": 0.15,
    },
    "terrain": {
        "name": "Terrain Advantage",
        "color": "#22c55e",
        "weight": 0.15,
    },
    "connectivity": {
        "name": "Connectivity",
        "color": "#3b82f6",
        "weight": 0.15,
    },
    "stability": {
        "name": "Stability Indicators",
        "color": "#8b5cf6",
        "weight": 0.15,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to [lo, hi]."""
    return max(lo, min(hi, value))


def _safe_avg(values: list) -> float:
    """Average of non-None values; 0 if empty."""
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else 0.0


def _count_by_tag(data: dict, tag_key: str, tag_value: str | None = None) -> int:
    """Count Overpass elements whose *tag_key* matches *tag_value*.

    If *tag_value* is ``None`` count elements that simply have the key.
    """
    elements = data.get("elements", []) if isinstance(data, dict) else []
    count = 0
    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        val = tags.get(tag_key)
        if val is None:
            continue
        if tag_value is None or val == tag_value:
            count += 1
    return count


def _count_by_tag_prefix(data: dict, tag_key: str,
                         prefix: str) -> int:
    """Count Overpass elements whose *tag_key* starts with *prefix*."""
    elements = data.get("elements", []) if isinstance(data, dict) else []
    count = 0
    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        val = tags.get(tag_key, "")
        if isinstance(val, str) and val.startswith(prefix):
            count += 1
    return count


def _count_all(data: dict) -> int:
    """Total element count in an Overpass result dict."""
    elements = data.get("elements", []) if isinstance(data, dict) else []
    return len(elements)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHERS  (cached, free APIs only)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_geopolitical_data(lat: float, lon: float,
                            radius: int = 10000) -> dict:
    """Fetch borders, military, embassies, customs, government, transport,
    mining and energy infrastructure from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      way["boundary"="administrative"]["admin_level"="2"](around:{radius},{lat},{lon});
      node["barrier"="border_control"](around:{radius},{lat},{lon});
      node["amenity"="customs"](around:{radius},{lat},{lon});
      node["amenity"="embassy"](around:{radius},{lat},{lon});
      way["landuse"="military"](around:{radius},{lat},{lon});
      node["office"="government"](around:{radius},{lat},{lon});
      way["aeroway"="aerodrome"](around:{radius},{lat},{lon});
      node["railway"="station"]["international"](around:{radius},{lat},{lon});
      way["highway"="motorway"](around:{radius},{lat},{lon});
      way["landuse"~"quarry|mine"](around:{radius},{lat},{lon});
      node["man_made"="mineshaft"](around:{radius},{lat},{lon});
      way["power"="plant"](around:{radius},{lat},{lon});
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
        logger.warning(f"Geopolitical data error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_geopolitical(lat: float, lon: float) -> dict:
    """Fetch a 7x7 elevation grid for terrain-advantage analysis.

    Returns ``{"results": [{"elevation": float, ...}, ...]}``
    """
    points = "|".join(
        f"{lat + dy * 0.01},{lon + dx * 0.01}"
        for dy in range(-3, 4)
        for dx in range(-3, 4)
    )
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm90m",
            params={"locations": points},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Elevation error: {e}")
        return {"results": []}


# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSION SCORERS  (each returns 0-100)
# ═══════════════════════════════════════════════════════════════════════════════

def _score_border_proximity(geo_data: dict) -> dict:
    """Score how close the point is to international borders / crossings.

    admin_level=2 boundaries within radius  -> high significance
    border controls & customs               -> proximity indicator
    """
    borders = _count_by_tag(geo_data, "admin_level", "2")
    border_controls = _count_by_tag(geo_data, "barrier", "border_control")
    customs = _count_by_tag(geo_data, "amenity", "customs")

    border_score = _clamp(borders * 25, 0, 100)
    control_score = _clamp(border_controls * 30, 0, 100)
    customs_score = _clamp(customs * 30, 0, 100)

    overall = _clamp(
        border_score * 0.50 + control_score * 0.25 + customs_score * 0.25,
        0, 100,
    )

    return {
        "overall": round(overall, 1),
        "details": {
            "international_boundaries": borders,
            "border_controls": border_controls,
            "customs_facilities": customs,
            "border_presence_score": round(border_score, 1),
            "crossing_score": round(control_score, 1),
            "customs_score": round(customs_score, 1),
        },
    }


def _score_strategic_infrastructure(geo_data: dict) -> dict:
    """Score military, embassy, government & airport assets.

    military*20 + embassies*15 + government*10 + airports*15
    """
    military = _count_by_tag(geo_data, "landuse", "military")
    embassies = _count_by_tag(geo_data, "amenity", "embassy")
    government = _count_by_tag(geo_data, "office", "government")
    airports = _count_by_tag(geo_data, "aeroway", "aerodrome")

    raw = military * 20 + embassies * 15 + government * 10 + airports * 15
    overall = _clamp(raw, 0, 100)

    return {
        "overall": round(overall, 1),
        "details": {
            "military_installations": military,
            "embassies": embassies,
            "government_offices": government,
            "airports": airports,
        },
    }


def _score_resource_control(geo_data: dict) -> dict:
    """Score mining, quarry and power-plant presence.

    mines*15 + quarries*10 + power_plants*20
    """
    mines = _count_by_tag(geo_data, "man_made", "mineshaft")
    quarries = _count_by_tag(geo_data, "landuse", "quarry")
    mines_landuse = _count_by_tag(geo_data, "landuse", "mine")
    power_plants = _count_by_tag(geo_data, "power", "plant")

    total_mines = mines + mines_landuse
    raw = total_mines * 15 + quarries * 10 + power_plants * 20
    overall = _clamp(raw, 0, 100)

    return {
        "overall": round(overall, 1),
        "details": {
            "mines": total_mines,
            "quarries": quarries,
            "power_plants": power_plants,
            "resource_density_raw": raw,
        },
    }


def _score_terrain_advantage(elev_data: dict) -> dict:
    """Score natural barriers (elevation variation) for border defense.

    High elevation variation = mountains = defensive advantage.
    """
    results = elev_data.get("results", []) if isinstance(elev_data, dict) else []
    elevations = [
        r.get("elevation", 0.0)
        for r in results
        if isinstance(r, dict) and r.get("elevation") is not None
    ]

    if not elevations:
        return {
            "overall": 0.0,
            "details": {
                "min_elevation": 0,
                "max_elevation": 0,
                "elevation_range": 0,
                "mean_elevation": 0,
                "variation_score": 0,
            },
        }

    min_e = min(elevations)
    max_e = max(elevations)
    elev_range = max_e - min_e
    mean_e = sum(elevations) / len(elevations)

    # Standard deviation as proxy for terrain roughness
    variance = sum((e - mean_e) ** 2 for e in elevations) / len(elevations)
    std_dev = math.sqrt(variance)

    # Range-based score: 500 m range = 100
    range_score = _clamp(elev_range / 5.0, 0, 100)
    # Std-dev-based score: 150 m std = 100
    roughness_score = _clamp(std_dev / 1.5, 0, 100)

    overall = _clamp(range_score * 0.60 + roughness_score * 0.40, 0, 100)

    return {
        "overall": round(overall, 1),
        "details": {
            "min_elevation": round(min_e, 1),
            "max_elevation": round(max_e, 1),
            "elevation_range": round(elev_range, 1),
            "mean_elevation": round(mean_e, 1),
            "std_deviation": round(std_dev, 1),
            "variation_score": round(range_score, 1),
            "roughness_score": round(roughness_score, 1),
        },
    }


def _score_connectivity(geo_data: dict) -> dict:
    """Score international connectivity via roads, airports, rail.

    motorways*5 + airports*20 + international_railways*15
    """
    motorways = _count_by_tag(geo_data, "highway", "motorway")
    airports = _count_by_tag(geo_data, "aeroway", "aerodrome")
    intl_rail = _count_by_tag(geo_data, "railway", "station")

    raw = motorways * 5 + airports * 20 + intl_rail * 15
    overall = _clamp(raw, 0, 100)

    return {
        "overall": round(overall, 1),
        "details": {
            "motorways": motorways,
            "airports": airports,
            "international_railways": intl_rail,
            "connectivity_raw": raw,
        },
    }


def _score_stability(quakes: dict, landuse: dict,
                     weather: dict) -> dict:
    """Score stability: 100 - (earthquake_risk + infrastructure_gaps).

    More infrastructure + low seismicity = stable.
    """
    # -- earthquake risk --
    features = quakes.get("features", []) if isinstance(quakes, dict) else []
    magnitudes = []
    for f in features:
        if not isinstance(f, dict):
            continue
        props = f.get("properties", {})
        if isinstance(props, dict):
            mag = props.get("mag")
            if mag is not None:
                magnitudes.append(float(mag))

    eq_count = len(magnitudes)
    max_mag = max(magnitudes) if magnitudes else 0.0
    avg_mag = (sum(magnitudes) / len(magnitudes)) if magnitudes else 0.0

    # Penalty grows with both count and magnitude
    eq_penalty = _clamp(eq_count * 1.5 + max_mag * 5.0, 0, 50)

    # -- infrastructure density bonus --
    elements = landuse.get("elements", []) if isinstance(landuse, dict) else []
    infra_count = len(elements)
    infra_bonus = _clamp(infra_count * 0.3, 0, 30)

    # -- weather stability bonus --
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    wind = current.get("wind_speed_10m", 0) if isinstance(current, dict) else 0
    wind = wind if wind is not None else 0
    wind_penalty = _clamp(max(0, (wind - 50) * 0.5), 0, 15)

    overall = _clamp(100 - eq_penalty + infra_bonus - wind_penalty, 0, 100)

    return {
        "overall": round(overall, 1),
        "details": {
            "earthquake_count": eq_count,
            "max_magnitude": round(max_mag, 1),
            "avg_magnitude": round(avg_mag, 2),
            "seismic_penalty": round(eq_penalty, 1),
            "infrastructure_elements": infra_count,
            "infrastructure_bonus": round(infra_bonus, 1),
            "wind_speed_kmh": round(wind, 1),
            "wind_penalty": round(wind_penalty, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE COMPUTATION  (cached)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_geopolitical_analysis(lat: float, lon: float) -> dict:
    """Run full 6-dimension geopolitical analysis for *(lat, lon)*.

    Returns
    -------
    dict with keys:
        component_scores  -- per-dimension breakdown (0-100)
        weighted_total    -- single composite score (0-100)
        findings          -- list of human-readable insight strings
        raw_counts        -- element counts for the UI
    """
    # -- fetch data --------------------------------------------------------
    geo_data = fetch_geopolitical_data(lat, lon)
    elev_data = fetch_elevation_geopolitical(lat, lon)
    quakes = fetch_earthquakes(lat, lon)
    weather = fetch_weather_data(lat, lon)
    landuse = fetch_landuse_infrastructure(lat, lon)

    # -- score each dimension ----------------------------------------------
    border = _score_border_proximity(geo_data)
    strategic = _score_strategic_infrastructure(geo_data)
    resources = _score_resource_control(geo_data)
    terrain = _score_terrain_advantage(elev_data)
    connectivity = _score_connectivity(geo_data)
    stability = _score_stability(quakes, landuse, weather)

    component_scores = {
        "border": border,
        "strategic": strategic,
        "resources": resources,
        "terrain": terrain,
        "connectivity": connectivity,
        "stability": stability,
    }

    # -- weighted composite ------------------------------------------------
    weighted_total = 0.0
    for key, score_dict in component_scores.items():
        weight = GEOPOLITICAL_COMPONENTS[key]["weight"]
        weighted_total += score_dict["overall"] * weight
    weighted_total = round(_clamp(weighted_total, 0, 100), 1)

    # -- raw element counts for the UI ------------------------------------
    raw_counts = {
        "total_geopolitical_elements": _count_all(geo_data),
        "elevation_points": len(
            elev_data.get("results", [])
            if isinstance(elev_data, dict) else []
        ),
        "earthquake_events": len(
            quakes.get("features", [])
            if isinstance(quakes, dict) else []
        ),
        "infrastructure_elements": len(
            landuse.get("elements", [])
            if isinstance(landuse, dict) else []
        ),
    }

    # -- findings ----------------------------------------------------------
    findings = _generate_findings(component_scores, weighted_total, raw_counts)

    return {
        "component_scores": component_scores,
        "weighted_total": weighted_total,
        "findings": findings,
        "raw_counts": raw_counts,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FINDINGS GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_findings(components: dict, total: float,
                       raw: dict) -> list:
    """Produce a list of human-readable insight strings."""
    findings: list[str] = []

    # Highest-scoring dimension
    top_key = max(components, key=lambda k: components[k]["overall"])
    top_name = GEOPOLITICAL_COMPONENTS[top_key]["name"]
    top_val = components[top_key]["overall"]
    findings.append(
        f"Dominant geopolitical dimension: {top_name} "
        f"(score {top_val:.0f}/100)."
    )

    # Border proximity commentary
    bdr = components["border"]
    if bdr["overall"] >= 50:
        findings.append(
            f"Significant border proximity detected "
            f"({bdr['details']['international_boundaries']} boundary segment(s), "
            f"{bdr['details']['border_controls']} crossing(s)). "
            f"Area is within an active border zone."
        )
    elif bdr["overall"] >= 20:
        findings.append(
            "Moderate border presence; some administrative boundaries "
            "or crossing infrastructure nearby."
        )
    else:
        findings.append(
            "Low border proximity; location is inland with no significant "
            "boundary infrastructure within the search radius."
        )

    # Strategic infrastructure
    strat = components["strategic"]
    sd = strat["details"]
    if strat["overall"] >= 40:
        assets_list = []
        if sd["military_installations"] > 0:
            assets_list.append(
                f"{sd['military_installations']} military installation(s)"
            )
        if sd["embassies"] > 0:
            assets_list.append(f"{sd['embassies']} embassy/embassies")
        if sd["government_offices"] > 0:
            assets_list.append(f"{sd['government_offices']} government office(s)")
        if sd["airports"] > 0:
            assets_list.append(f"{sd['airports']} airport(s)")
        asset_str = ", ".join(assets_list) if assets_list else "multiple assets"
        findings.append(
            f"Notable strategic infrastructure: {asset_str}."
        )

    # Resource control
    res = components["resources"]
    if res["overall"] >= 30:
        findings.append(
            f"Resource-control value is elevated "
            f"({res['details']['mines']} mine(s), "
            f"{res['details']['quarries']} quarry/quarries, "
            f"{res['details']['power_plants']} power plant(s))."
        )

    # Terrain advantage
    terr = components["terrain"]
    td = terr["details"]
    if terr["overall"] >= 50:
        findings.append(
            f"Terrain provides strong natural barriers -- "
            f"elevation range {td['elevation_range']:.0f} m "
            f"(min {td['min_elevation']:.0f} m, "
            f"max {td['max_elevation']:.0f} m)."
        )
    elif terr["overall"] >= 20:
        findings.append(
            f"Moderate terrain variation ({td['elevation_range']:.0f} m range). "
            f"Partial natural barriers present."
        )

    # Connectivity
    conn = components["connectivity"]
    cd = conn["details"]
    if conn["overall"] >= 40:
        findings.append(
            f"Good international connectivity: "
            f"{cd['motorways']} motorway(s), {cd['airports']} airport(s), "
            f"{cd['international_railways']} railway station(s)."
        )
    else:
        findings.append(
            "Limited international connectivity infrastructure detected."
        )

    # Stability
    stab = components["stability"]
    sbd = stab["details"]
    if stab["overall"] >= 70:
        findings.append(
            f"High stability index ({stab['overall']:.0f}/100). "
            f"Low seismic risk, adequate infrastructure coverage."
        )
    elif stab["overall"] >= 40:
        findings.append(
            f"Moderate stability ({stab['overall']:.0f}/100). "
            f"{sbd['earthquake_count']} earthquake event(s) recorded "
            f"(max magnitude {sbd['max_magnitude']:.1f})."
        )
    else:
        findings.append(
            f"Low stability ({stab['overall']:.0f}/100). "
            f"Seismic activity and/or infrastructure gaps present significant "
            f"risk factors."
        )

    # Overall assessment
    if total >= 70:
        findings.append(
            f"Overall geopolitical significance is HIGH ({total:.0f}/100). "
            f"This location warrants close monitoring and strategic planning."
        )
    elif total >= 40:
        findings.append(
            f"Overall geopolitical significance is MODERATE ({total:.0f}/100)."
        )
    else:
        findings.append(
            f"Overall geopolitical significance is LOW ({total:.0f}/100). "
            f"The area currently shows limited strategic interest."
        )

    return findings


# ═══════════════════════════════════════════════════════════════════════════════
# PLOTLY VISUALISATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_radar_chart(components: dict) -> go.Figure:
    """Build a Plotly radar chart for the six geopolitical dimensions."""
    labels = []
    values = []
    colors = []

    for key in GEOPOLITICAL_COMPONENTS:
        comp_meta = GEOPOLITICAL_COMPONENTS[key]
        labels.append(comp_meta["name"])
        values.append(components.get(key, {}).get("overall", 0))
        colors.append(comp_meta["color"])

    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        name="Geopolitical Score",
        line=dict(color="#6366f1", width=2),
        fillcolor="rgba(99,102,241,0.25)",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#1e293b",
                linecolor="#334155",
                tickfont=dict(color="#94a3b8", size=9),
            ),
            angularaxis=dict(
                gridcolor="#1e293b",
                linecolor="#334155",
                tickfont=dict(color="#cbd5e1", size=10),
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        margin=dict(t=50, b=40, l=70, r=70),
        height=440,
        title=dict(
            text="Geopolitical Dimension Radar",
            font=dict(color="#e2e8f0", size=14),
        ),
        showlegend=False,
    )
    return fig


def _build_bar_chart(components: dict) -> go.Figure:
    """Build a horizontal bar chart for each dimension score."""
    keys = list(GEOPOLITICAL_COMPONENTS.keys())
    names = [GEOPOLITICAL_COMPONENTS[k]["name"] for k in keys]
    scores = [components.get(k, {}).get("overall", 0) for k in keys]
    bar_colors = [GEOPOLITICAL_COMPONENTS[k]["color"] for k in keys]

    fig = go.Figure(go.Bar(
        y=names,
        x=scores,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{s:.0f}" for s in scores],
        textposition="auto",
        textfont=dict(color="#e2e8f0", size=12),
    ))

    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        xaxis=dict(
            range=[0, 105],
            gridcolor="#1e293b",
            linecolor="#334155",
            tickfont=dict(color="#94a3b8"),
            title="Score (0-100)",
        ),
        yaxis=dict(
            tickfont=dict(color="#cbd5e1"),
            autorange="reversed",
        ),
        margin=dict(t=40, b=40, l=160, r=30),
        height=340,
        title=dict(
            text="Component Scores",
            font=dict(color="#e2e8f0", size=14),
        ),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# UI RENDER HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_score_banner(total: float, lat: float, lon: float):
    """Render the overall geopolitical significance banner."""
    if total >= 70:
        color = "#ef4444"
        label = "HIGH SIGNIFICANCE"
    elif total >= 40:
        color = "#f59e0b"
        label = "MODERATE SIGNIFICANCE"
    else:
        color = "#22c55e"
        label = "LOW SIGNIFICANCE"

    bar_w = max(1, int(total))

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);
                    border:1px solid {color};border-radius:10px;
                    padding:22px 26px;text-align:center;margin:10px 0 18px 0;">
            <div style="color:#94a3b8;font-size:0.82rem;
                        text-transform:uppercase;letter-spacing:1.6px;">
                Geopolitical Significance Index</div>
            <div style="color:{color};font-size:2.6rem;
                        font-weight:800;margin:6px 0;">
                {total:.0f}<span style="font-size:1.1rem;
                color:#64748b;">/100</span></div>
            <div style="background:#0f172a;border-radius:5px;height:10px;
                        margin:8px auto;max-width:400px;">
                <div style="background:{color};width:{bar_w}%;
                            height:100%;border-radius:5px;"></div>
            </div>
            <div style="display:inline-block;background:{color};
                        color:#0f172a;padding:3px 16px;border-radius:12px;
                        font-size:0.82rem;font-weight:700;">
                {label}</div>
            <div style="color:#64748b;font-size:0.8rem;margin-top:8px;">
                {lat:.5f}N, {lon:.5f}E</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_component_card(key: str, score_data: dict):
    """Render a single component score card with detail breakdown."""
    meta = GEOPOLITICAL_COMPONENTS.get(key, {})
    color = meta.get("color", "#64748b")
    name = meta.get("name", key)
    weight = meta.get("weight", 0)
    overall = score_data.get("overall", 0)
    details = score_data.get("details", {})
    bar_w = max(1, int(overall))

    detail_pills = "".join(
        f'<span style="background:#0f172a;color:#cbd5e1;'
        f'padding:2px 8px;border-radius:10px;font-size:0.76rem;">'
        f'{dk.replace("_", " ").title()}: {dv}</span>'
        for dk, dv in details.items()
    )

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                    border-left:4px solid {color};border-radius:8px;
                    padding:14px 18px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:6px;">
                <span style="color:{color};font-weight:700;font-size:1.05rem;">
                    {name}
                    <span style="color:#64748b;font-size:0.75rem;
                                 font-weight:400;margin-left:6px;">
                        (weight {weight:.0%})</span>
                </span>
                <span style="color:#e2e8f0;font-weight:700;font-size:1.15rem;">
                    {overall:.0f}<small style="color:#94a3b8;">/100</small></span>
            </div>
            <div style="background:#0f172a;border-radius:4px;height:8px;
                        margin-bottom:8px;">
                <div style="background:{color};width:{bar_w}%;
                            height:100%;border-radius:4px;"></div>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
                {detail_pills}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_findings(findings: list):
    """Render the list of analytical findings."""
    for i, finding in enumerate(findings, 1):
        if "HIGH" in finding:
            left_color = "#ef4444"
        elif "MODERATE" in finding:
            left_color = "#f59e0b"
        elif "LOW" in finding:
            left_color = "#22c55e"
        else:
            left_color = "#64748b"

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                        border-radius:6px;padding:10px 14px;margin-bottom:6px;
                        border-left:3px solid {left_color};">
                <span style="color:#64748b;font-weight:600;
                             margin-right:8px;">{i}.</span>
                <span style="color:#cbd5e1;font-size:0.9rem;">{finding}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_raw_counts(raw: dict):
    """Render a summary of raw data element counts."""
    items = [
        ("Geopolitical Elements", raw.get("total_geopolitical_elements", 0),
         "#6366f1"),
        ("Elevation Points", raw.get("elevation_points", 0), "#22c55e"),
        ("Earthquake Events", raw.get("earthquake_events", 0), "#ef4444"),
        ("Infrastructure Elements", raw.get("infrastructure_elements", 0),
         "#3b82f6"),
    ]

    cols = st.columns(len(items))
    for col, (label, count, color) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div style="background:#0f172a;border-radius:8px;
                            padding:12px 14px;text-align:center;
                            border:1px solid #1e293b;">
                    <div style="color:{color};font-size:1.6rem;
                                font-weight:800;">{count}</div>
                    <div style="color:#94a3b8;font-size:0.78rem;
                                margin-top:2px;">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def render_geopolitical_ai_tab():
    """Render the Geopolitical Analysis AI tab in the Streamlit app."""

    # -- header ------------------------------------------------------------
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
        'border-radius:10px;padding:18px 22px;margin-bottom:14px;'
        'border-left:4px solid #ef4444;">'
        '<h4 style="color:#e2e8f0;margin:0 0 4px 0;">'
        'Geopolitical Analysis AI</h4>'
        '<p style="color:#94a3b8;margin:0;font-size:0.92rem;">'
        'Border proximity, strategic infrastructure, resource control, '
        'terrain advantage, connectivity &amp; stability assessment'
        '</p></div>',
        unsafe_allow_html=True,
    )

    # -- location selector -------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="geopol_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with c2:
        lat = st.number_input(
            "Latitude",
            value=default_lat,
            format="%.5f",
            min_value=-90.0,
            max_value=90.0,
            key="geopol_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="geopol_lon",
        )

    # -- analysis radius ---------------------------------------------------
    radius_km = st.slider(
        "Analysis Radius (km)",
        min_value=1,
        max_value=50,
        value=10,
        key="geopol_radius",
    )

    run_btn = st.button(
        "Run Geopolitical Analysis",
        type="primary",
        key="geopol_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and click **Run Geopolitical Analysis** "
            "to compute the 6-dimension geopolitical assessment."
        )
        return

    # -- progress ----------------------------------------------------------
    progress = st.progress(0, text="Initializing geopolitical analysis...")
    progress.progress(10, text="Fetching border & strategic data...")
    result = compute_geopolitical_analysis(lat, lon)
    progress.progress(100, text="Analysis complete.")

    components = result.get("component_scores", {})
    total = result.get("weighted_total", 0)
    findings = result.get("findings", [])
    raw = result.get("raw_counts", {})

    # -- overall score banner ----------------------------------------------
    _render_score_banner(total, lat, lon)

    # -- raw data counts ---------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:10px 0 8px 0;">'
        'Data Sources Summary</h5>',
        unsafe_allow_html=True,
    )
    _render_raw_counts(raw)

    # -- component cards ---------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:18px 0 8px 0;">'
        'Dimension Scores</h5>',
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns(2)
    comp_keys = list(GEOPOLITICAL_COMPONENTS.keys())
    for idx, key in enumerate(comp_keys):
        target_col = left_col if idx % 2 == 0 else right_col
        with target_col:
            _render_component_card(key, components.get(key, {}))

    # -- radar chart -------------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:18px 0 8px 0;">'
        'Geopolitical Radar</h5>',
        unsafe_allow_html=True,
    )
    radar_fig = _build_radar_chart(components)
    st.plotly_chart(radar_fig, use_container_width=True, key="geoai_pchart1")

    # -- bar chart ---------------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:18px 0 8px 0;">'
        'Component Breakdown</h5>',
        unsafe_allow_html=True,
    )
    bar_fig = _build_bar_chart(components)
    st.plotly_chart(bar_fig, use_container_width=True, key="geoai_pchart2")

    # -- analytical findings -----------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:18px 0 8px 0;">'
        'Analytical Findings</h5>',
        unsafe_allow_html=True,
    )
    _render_findings(findings)

    # -- weight legend -----------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:18px 0 8px 0;">'
        'Scoring Weights</h5>',
        unsafe_allow_html=True,
    )
    weight_pills = "".join(
        f'<span style="background:{meta["color"]}22;color:{meta["color"]};'
        f'border:1px solid {meta["color"]}44;padding:4px 12px;'
        f'border-radius:12px;font-size:0.82rem;font-weight:600;">'
        f'{meta["name"]}: {meta["weight"]:.0%}</span>'
        for meta in GEOPOLITICAL_COMPONENTS.values()
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;'
        f'margin-bottom:16px;">{weight_pills}</div>',
        unsafe_allow_html=True,
    )
