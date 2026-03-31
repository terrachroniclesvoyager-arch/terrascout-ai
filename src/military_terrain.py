"""
Military Terrain Analysis AI -- KOCOA-style terrain assessment for
observation, cover, obstacles, key terrain, and approach avenues.
Uses: Open Topo Data, Overpass, Open-Meteo, SoilGrids.
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
    fetch_soil_data,
    fetch_elevation_grid,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# KOCOA component definitions
# ---------------------------------------------------------------------------

KOCOA_COMPONENTS = {
    "observation": {"name": "Observation & Fire", "color": "#ef4444", "weight": 0.20},
    "cover": {"name": "Cover & Concealment", "color": "#22c55e", "weight": 0.20},
    "obstacles": {"name": "Obstacles", "color": "#f59e0b", "weight": 0.15},
    "key_terrain": {"name": "Key Terrain", "color": "#3b82f6", "weight": 0.20},
    "avenues": {"name": "Avenues of Approach", "color": "#8b5cf6", "weight": 0.15},
    "trafficability": {"name": "Trafficability", "color": "#ec4899", "weight": 0.10},
}


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_elevation_grid_military(lat, lon, size=0.02, steps=5):
    """Fetch a grid of elevation points for terrain analysis."""
    points = []
    for i in range(steps):
        for j in range(steps):
            plat = lat - size / 2 + (size * i / (steps - 1))
            plon = lon - size / 2 + (size * j / (steps - 1))
            points.append(f"{plat},{plon}")

    locations = "|".join(points)
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm90m",
            params={"locations": locations},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Elevation grid error: %s", e)
        return {"results": []}


@st.cache_data(ttl=1800)
def fetch_military_overpass(lat, lon, radius=3000):
    """Fetch military-relevant features (roads, bridges, forests, water)."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:25];
(
  way["highway"](around:{radius},{lat},{lon});
  way["bridge"="yes"](around:{radius},{lat},{lon});
  way["natural"="wood"](around:{radius},{lat},{lon});
  way["landuse"="forest"](around:{radius},{lat},{lon});
  way["natural"="water"](around:{radius},{lat},{lon});
  way["waterway"](around:{radius},{lat},{lon});
  way["natural"="wetland"](around:{radius},{lat},{lon});
  way["building"](around:{radius},{lat},{lon});
  node["natural"="peak"](around:{radius},{lat},{lon});
  node["mountain_pass"](around:{radius},{lat},{lon});
);
out center;"""
    try:
        resp = requests.post(overpass_url, data={"data": query}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Military overpass error: %s", e)
        return {"elements": []}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _safe_mean(values):
    """Return mean of numeric list filtering None, or 0."""
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else 0.0


def _clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


def _extract_soil_property(soil_data, prop_name):
    """Extract mean value from ISRIC SoilGrids response for *prop_name*.

    Structure: properties -> layers[] -> {name, depths[{values: {mean}}]}
    Returns the average across depths, divided by 10 for g/kg props.
    """
    props = soil_data.get("properties", {})
    layers = props.get("layers", [])
    for layer in layers:
        if layer.get("name") != prop_name:
            continue
        depths = layer.get("depths", [])
        means = []
        for d in depths:
            val = d.get("values", {}).get("mean")
            if val is not None:
                means.append(val)
        if means:
            raw = sum(means) / len(means)
            # SoilGrids stores clay/sand/silt as g/kg (divide by 10 for %)
            if prop_name in ("clay", "sand", "silt"):
                return raw / 10.0
            return raw
    return None


# ---------------------------------------------------------------------------
# Dimension scoring
# ---------------------------------------------------------------------------

def _score_observation(elev_data, mil_data):
    """Score observation & fields of fire (0-100).

    High score = good visibility: elevation advantage, open areas,
    large elevation range (commanding heights).
    """
    elevations = elev_data.get("grid_elevations", [])
    valid = [e for e in elevations if e is not None]
    if not valid:
        return 50

    elev_range = max(valid) - min(valid)
    center_elev = elev_data.get("center_elevation", 0) or 0
    avg = _safe_mean(valid)

    # Elevation advantage of center vs surroundings
    elev_advantage = max(0, center_elev - avg)

    # Count open areas (lack of forest/building = open sightlines)
    elements = mil_data.get("elements", [])
    forest_count = 0
    building_count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("natural") == "wood" or tags.get("landuse") == "forest":
            forest_count += 1
        if tags.get("building"):
            building_count += 1

    obstruction_penalty = min(40, (forest_count + building_count) * 2)

    # Components
    range_score = min(40, elev_range / 5)  # 200m range -> 40 pts
    advantage_score = min(30, elev_advantage / 3)  # 90m advantage -> 30 pts
    openness_score = max(0, 30 - obstruction_penalty)

    return _clamp(round(range_score + advantage_score + openness_score))


def _score_cover(mil_data, landuse_data):
    """Score cover & concealment (0-100).

    High score = good cover: forests, buildings, rough terrain features.
    """
    elements_mil = mil_data.get("elements", [])
    elements_lu = landuse_data.get("elements", [])

    forest_count = 0
    building_count = 0
    for el in elements_mil + elements_lu:
        tags = el.get("tags", {})
        if tags.get("natural") == "wood" or tags.get("landuse") == "forest":
            forest_count += 1
        if tags.get("building"):
            building_count += 1

    # Forests provide excellent concealment
    forest_score = min(50, forest_count * 5)
    # Buildings provide cover from fire
    building_score = min(30, building_count * 1.5)
    # Base score (some terrain always offers micro-cover)
    base = 10

    return _clamp(round(base + forest_score + building_score))


def _score_obstacles(mil_data, water_data, elev_data):
    """Score obstacles (0-100).

    High score = many obstacles present: rivers, steep slopes, marshes,
    dense urban. This is *presence* of obstacles, not ease-of-movement.
    """
    elevations = elev_data.get("grid_elevations", [])
    valid = [e for e in elevations if e is not None]

    # Steep slope assessment
    slope_score = 0
    if len(valid) >= 4:
        diffs = [abs(valid[i] - valid[i + 1]) for i in range(len(valid) - 1)]
        avg_diff = _safe_mean(diffs)
        slope_score = min(30, avg_diff * 2)

    # Water obstacles
    water_elements = water_data.get("elements", [])
    water_count = len(water_elements)
    water_score = min(30, water_count * 3)

    # Wetlands, marshes
    mil_elements = mil_data.get("elements", [])
    wetland_count = 0
    for el in mil_elements:
        tags = el.get("tags", {})
        if tags.get("natural") == "wetland":
            wetland_count += 1
    wetland_score = min(20, wetland_count * 5)

    # Dense urban (many buildings = obstacle to maneuver)
    building_count = sum(
        1 for el in mil_elements if el.get("tags", {}).get("building")
    )
    urban_score = min(20, building_count * 0.5)

    return _clamp(round(slope_score + water_score + wetland_score + urban_score))


def _score_key_terrain(elev_data, mil_data):
    """Score key terrain (0-100).

    High score = many key terrain features: high ground, chokepoints,
    bridges, crossroads, peaks.
    """
    elements = mil_data.get("elements", [])

    # Peaks and passes
    peak_count = 0
    bridge_count = 0
    crossroad_count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("natural") == "peak":
            peak_count += 1
        if tags.get("mountain_pass"):
            peak_count += 1
        if tags.get("bridge") == "yes":
            bridge_count += 1
        hw = tags.get("highway", "")
        if hw in ("trunk", "primary", "secondary", "motorway"):
            crossroad_count += 1

    peak_score = min(30, peak_count * 10)
    bridge_score = min(25, bridge_count * 8)
    crossroad_score = min(25, crossroad_count * 2)

    # Elevation dominance (high ground value)
    elevations = elev_data.get("grid_elevations", [])
    valid = [e for e in elevations if e is not None]
    if valid:
        elev_range = max(valid) - min(valid)
        dominance_score = min(20, elev_range / 10)
    else:
        dominance_score = 5

    return _clamp(round(peak_score + bridge_score + crossroad_score + dominance_score))


def _score_avenues(mil_data, landuse_data):
    """Score avenues of approach (0-100).

    High score = good mobility corridors: road network, passable terrain.
    """
    elements = mil_data.get("elements", []) + landuse_data.get("elements", [])

    road_count = 0
    major_road_count = 0
    for el in elements:
        tags = el.get("tags", {})
        hw = tags.get("highway", "")
        if hw:
            road_count += 1
            if hw in ("motorway", "trunk", "primary", "secondary"):
                major_road_count += 1

    road_score = min(40, road_count * 1.5)
    major_score = min(30, major_road_count * 5)

    # Passable terrain (inverse of wetlands/water)
    wetland_count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("natural") in ("wetland", "water") or tags.get("waterway"):
            wetland_count += 1
    passable_score = max(0, 30 - wetland_count * 3)

    return _clamp(round(road_score + major_score + passable_score))


def _score_trafficability(soil_data, elev_data, weather_data):
    """Score trafficability (0-100).

    High score = good bearing capacity: low clay, moderate slopes,
    dry weather.
    """
    # Soil bearing capacity (clay reduces trafficability)
    clay_pct = _extract_soil_property(soil_data, "clay")
    if clay_pct is not None:
        # High clay = poor trafficability when wet
        soil_score = max(0, 35 - clay_pct * 0.7)
    else:
        soil_score = 20  # neutral default

    # Slope grades
    elevations = elev_data.get("grid_elevations", [])
    valid = [e for e in elevations if e is not None]
    if len(valid) >= 4:
        diffs = [abs(valid[i] - valid[i + 1]) for i in range(len(valid) - 1)]
        avg_diff = _safe_mean(diffs)
        slope_component = max(0, 35 - avg_diff * 3)
    else:
        slope_component = 20

    # Weather impact
    current = weather_data.get("current", {})
    precip = current.get("precipitation", 0) or 0
    humidity = current.get("relative_humidity_2m", 50) or 50

    if precip > 5:
        weather_score = 5
    elif precip > 1:
        weather_score = 15
    elif humidity > 85:
        weather_score = 20
    else:
        weather_score = 30

    return _clamp(round(soil_score + slope_component + weather_score))


# ---------------------------------------------------------------------------
# Master analysis
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def run_kocoa_analysis(lat, lon):
    """Execute full KOCOA analysis, return dict with scores & metadata."""
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=7) or {}
    mil_data = fetch_military_overpass(lat, lon, radius=3000)
    soil_data = fetch_soil_data(lat, lon) or {}
    weather_data = fetch_weather_data(lat, lon) or {}
    water_data = fetch_water_features(lat, lon, radius=3000)
    landuse_data = fetch_landuse_infrastructure(lat, lon, radius=3000)

    scores = {
        "observation": _score_observation(elev_data, mil_data),
        "cover": _score_cover(mil_data, landuse_data),
        "obstacles": _score_obstacles(mil_data, water_data, elev_data),
        "key_terrain": _score_key_terrain(elev_data, mil_data),
        "avenues": _score_avenues(mil_data, landuse_data),
        "trafficability": _score_trafficability(soil_data, elev_data, weather_data),
    }

    # Weighted overall tactical value
    overall = sum(
        scores[k] * KOCOA_COMPONENTS[k]["weight"] for k in scores
    )

    # Classification
    if overall >= 75:
        classification = "Excellent"
    elif overall >= 55:
        classification = "Good"
    elif overall >= 35:
        classification = "Fair"
    else:
        classification = "Poor"

    # Build tactical findings
    findings = _build_tactical_summary(scores, elev_data, mil_data, water_data)

    return {
        "scores": scores,
        "overall": round(overall, 1),
        "classification": classification,
        "elev_data": elev_data,
        "weather_data": weather_data,
        "soil_data": soil_data,
        "findings": findings,
    }


def _build_tactical_summary(scores, elev_data, mil_data, water_data):
    """Generate key findings text list."""
    findings = []

    # Commanding heights
    elevations = elev_data.get("grid_elevations", [])
    valid = [e for e in elevations if e is not None]
    if valid:
        max_e = max(valid)
        min_e = min(valid)
        rng = max_e - min_e
        center = elev_data.get("center_elevation", 0) or 0
        if rng > 50:
            findings.append(
                f"Significant relief: {rng:.0f}m range "
                f"({min_e:.0f}m - {max_e:.0f}m). "
                "High ground offers tactical advantage."
            )
        if center > _safe_mean(valid) + 20:
            findings.append(
                "Position on elevated ground with commanding observation."
            )

    # Natural obstacles
    water_els = water_data.get("elements", [])
    if len(water_els) > 5:
        findings.append(
            f"{len(water_els)} water features in AO -- "
            "significant obstacle to cross-country movement."
        )

    # Approach routes
    mil_els = mil_data.get("elements", [])
    road_count = sum(
        1 for el in mil_els if el.get("tags", {}).get("highway")
    )
    bridge_count = sum(
        1 for el in mil_els if el.get("tags", {}).get("bridge") == "yes"
    )
    if road_count > 20:
        findings.append(
            f"Dense road network ({road_count} segments) -- "
            "multiple avenues of approach available."
        )
    elif road_count < 5:
        findings.append(
            "Sparse road network -- limited avenues of approach; "
            "off-road capability required."
        )
    if bridge_count > 0:
        findings.append(
            f"{bridge_count} bridge(s) identified -- "
            "key chokepoints for control or denial."
        )

    # Cover assessment
    forest_count = sum(
        1
        for el in mil_els
        if el.get("tags", {}).get("natural") == "wood"
        or el.get("tags", {}).get("landuse") == "forest"
    )
    if forest_count > 10:
        findings.append(
            "Extensive forest cover provides excellent concealment "
            "for dismounted operations."
        )

    if not findings:
        findings.append(
            "Terrain is relatively featureless with moderate tactical value."
        )

    return findings


# ---------------------------------------------------------------------------
# Elevation profile helper
# ---------------------------------------------------------------------------

def _build_elevation_profile(elev_data):
    """Build a mini elevation profile figure from the N-S profile."""
    ns = elev_data.get("ns_profile", [])
    ew = elev_data.get("ew_profile", [])
    profile = ns if ns else ew
    if not profile:
        return None

    dists = []
    elevs = []
    for idx, pt in enumerate(profile):
        elev = pt.get("elevation")
        if elev is None:
            continue
        dists.append(idx)
        elevs.append(elev)

    if len(elevs) < 2:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dists,
        y=elevs,
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=6, color="#60a5fa"),
        fillcolor="rgba(59,130,246,0.15)",
        name="Elevation",
    ))

    max_elev = max(elevs)
    min_elev = min(elevs)
    max_idx = elevs.index(max_elev)
    min_idx = elevs.index(min_elev)

    fig.add_annotation(
        x=dists[max_idx], y=max_elev,
        text=f"HIGH {max_elev:.0f}m",
        showarrow=True, arrowhead=2,
        font=dict(color="#ef4444", size=11),
    )
    fig.add_annotation(
        x=dists[min_idx], y=min_elev,
        text=f"LOW {min_elev:.0f}m",
        showarrow=True, arrowhead=2,
        font=dict(color="#22c55e", size=11),
    )

    fig.update_layout(
        height=250,
        margin=dict(t=30, b=30, l=40, r=20),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        xaxis=dict(
            title="Profile Point",
            color="#888",
            gridcolor="#333",
            showgrid=True,
        ),
        yaxis=dict(
            title="Elevation (m)",
            color="#888",
            gridcolor="#333",
            showgrid=True,
        ),
        font=dict(color="#ccc"),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------

def render_military_terrain_tab():
    """Render the Military Terrain Analysis AI tab (single entry point)."""
    st.markdown("## Military Terrain Analysis AI")
    st.caption(
        "KOCOA-style terrain assessment: Observation, Cover, Obstacles, "
        "Key Terrain, Avenues of Approach, Trafficability"
    )

    # ── Location selector ──────────────────────────────────────────────────
    col_sel, col_coords = st.columns(2)
    with col_sel:
        preset = st.selectbox(
            "Location", list(ANALYSIS_PRESETS.keys()), key="mt_preset"
        )
    p = ANALYSIS_PRESETS.get(preset)
    with col_coords:
        cc1, cc2 = st.columns(2)
        with cc1:
            lat = st.number_input(
                "Lat", -90.0, 90.0,
                p.get("lat", 41.90) if p else 41.90,
                step=0.01, key="mt_lat", format="%.4f",
            )
        with cc2:
            lon = st.number_input(
                "Lon", -180.0, 180.0,
                p.get("lon", 12.50) if p else 12.50,
                step=0.01, key="mt_lon", format="%.4f",
            )

    if not st.button(
        "Run Terrain Assessment", type="primary", use_container_width=True
    ):
        return

    with st.spinner("Conducting KOCOA terrain analysis..."):
        result = run_kocoa_analysis(lat, lon)

    scores = result.get("scores", {})
    overall = result.get("overall", 0)
    classification = result.get("classification", "Fair")
    elev_data = result.get("elev_data", {})
    findings = result.get("findings", [])

    # ── Classification colour ──────────────────────────────────────────────
    cls_color_map = {
        "Excellent": "#10b981",
        "Good": "#22c55e",
        "Fair": "#f59e0b",
        "Poor": "#ef4444",
    }
    cls_color = cls_color_map.get(classification, "#888")

    # ── Header card ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                border:1px solid #333;border-radius:12px;padding:20px;margin:10px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="color:#888;font-size:12px;text-transform:uppercase;">
                    Terrain Assessment</div>
                <div style="color:#eee;font-size:22px;font-weight:bold;">
                    KOCOA Analysis &mdash; {lat:.4f}, {lon:.4f}</div>
                <div style="color:#888;font-size:13px;">
                    6-dimension military terrain evaluation</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#888;font-size:12px;">OVERALL TACTICAL VALUE</div>
                <div style="color:{cls_color};font-size:38px;font-weight:bold;">
                    {overall}<span style="font-size:14px;color:#888;">/100</span>
                </div>
                <div style="color:{cls_color};font-size:14px;font-weight:600;">
                    {classification}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Radar chart ────────────────────────────────────────────────────────
    st.markdown("### KOCOA Radar Profile")
    categories = [KOCOA_COMPONENTS[k]["name"] for k in KOCOA_COMPONENTS]
    values = [scores.get(k, 0) for k in KOCOA_COMPONENTS]
    colors = [KOCOA_COMPONENTS[k]["color"] for k in KOCOA_COMPONENTS]

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(59,130,246,0.18)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=7, color=colors + [colors[0]]),
        name="KOCOA",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#333", color="#888",
            ),
            angularaxis=dict(color="#ccc"),
        ),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#ccc"),
        height=420,
        margin=dict(t=40, b=40, l=60, r=60),
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="milter_pchart1")

    # ── 6 metric cards (3x2) ──────────────────────────────────────────────
    st.markdown("### Dimension Scores")
    keys = list(KOCOA_COMPONENTS.keys())
    for row_start in range(0, 6, 3):
        cols = st.columns(3)
        for idx, col in enumerate(cols):
            k = keys[row_start + idx]
            comp = KOCOA_COMPONENTS[k]
            score = scores.get(k, 0)
            bar_width = score  # percentage

            if score >= 70:
                grade = "HIGH"
            elif score >= 40:
                grade = "MED"
            else:
                grade = "LOW"

            col.markdown(f"""
            <div style="background:#1a1a2e;border:1px solid #333;
                        border-radius:10px;padding:16px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:6px;">
                    <span style="color:{comp['color']};font-size:13px;
                                 font-weight:600;">{comp['name']}</span>
                    <span style="color:{comp['color']};font-size:22px;
                                 font-weight:bold;">{score}</span>
                </div>
                <div style="background:#2a2a3e;border-radius:4px;
                            height:8px;overflow:hidden;">
                    <div style="width:{bar_width}%;height:100%;
                                background:{comp['color']};
                                border-radius:4px;"></div>
                </div>
                <div style="color:#888;font-size:11px;margin-top:4px;
                            text-align:right;">{grade}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Elevation profile ──────────────────────────────────────────────────
    st.markdown("### Elevation Profile")
    profile_fig = _build_elevation_profile(elev_data)
    if profile_fig is not None:
        st.plotly_chart(profile_fig, use_container_width=True, key="milter_pchart2")
    else:
        st.info("Elevation profile data not available for this location.")

    # ── Tactical summary ───────────────────────────────────────────────────
    st.markdown("### Tactical Summary")
    summary_items = "".join(
        f'<li style="color:#ccc;margin-bottom:6px;">{f}</li>' for f in findings
    )
    st.markdown(f"""
    <div style="background:#1a1a2e;border:1px solid #333;border-radius:10px;
                padding:18px;margin:8px 0;">
        <div style="color:#f59e0b;font-size:13px;font-weight:600;
                    margin-bottom:8px;text-transform:uppercase;">
            Key Findings</div>
        <ul style="padding-left:20px;margin:0;">{summary_items}</ul>
    </div>
    """, unsafe_allow_html=True)
