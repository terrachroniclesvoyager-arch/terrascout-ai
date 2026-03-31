"""
Viewshed & Panorama AI module for TerraScout AI.
Performs visibility and scenic assessment of any geographic point using free APIs:
  - Open Topo Data (elevation grid for viewshed computation)
  - Overpass API (landmarks, peaks, scenic points, viewpoints)
  - Open-Meteo (visibility conditions: cloud, humidity, precipitation)

Five scored dimensions (0-100):
  1. Elevation Advantage — height above surroundings, commanding position
  2. Visible Area — estimated viewshed coverage (how much land is visible)
  3. Scenic Value — nearby peaks, water, landmarks, scenic viewpoints
  4. Atmospheric Clarity — humidity, precipitation, cloud cover affecting visibility
  5. Obstruction Level — buildings/forests blocking views (inverted: fewer = higher)
"""

import logging
import math
from statistics import mean

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.overpass_client import query_overpass
from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

OPEN_TOPO_VIEWSHED_API = "https://api.opentopodata.org/v1/srtm90m"
OVERPASS_TIMEOUT = 25
VIEWSHED_GRID_SIZE = 15
VIEWSHED_RADIUS_DEG = 0.05  # ~5.5 km at mid-latitudes

DIMENSION_LABELS = [
    "Elevation Advantage",
    "Visible Area",
    "Scenic Value",
    "Atmospheric Clarity",
    "Obstruction Level",
]

DIMENSION_ICONS = {
    "Elevation Advantage": "mountain",
    "Visible Area": "eye",
    "Scenic Value": "gem",
    "Atmospheric Clarity": "cloud-sun",
    "Obstruction Level": "tree",
}

DIMENSION_COLORS = {
    "Elevation Advantage": "#f97316",
    "Visible Area": "#3b82f6",
    "Scenic Value": "#10b981",
    "Atmospheric Clarity": "#a78bfa",
    "Obstruction Level": "#ef4444",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING — ELEVATION GRID
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_viewshed_elevation(lat, lon, radius_deg=0.05, grid_size=15):
    """Fetch elevation grid for viewshed analysis from Open Topo Data."""
    points = []
    for i in range(grid_size):
        for j in range(grid_size):
            plat = lat - radius_deg + (2 * radius_deg * i / (grid_size - 1))
            plon = lon - radius_deg + (2 * radius_deg * j / (grid_size - 1))
            points.append(f"{plat:.5f},{plon:.5f}")
    # Split into batches of 100 for API limit
    all_results = []
    for batch_start in range(0, len(points), 100):
        batch = points[batch_start:batch_start + 100]
        try:
            resp = requests.get(
                OPEN_TOPO_VIEWSHED_API,
                params={"locations": "|".join(batch)},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            all_results.extend(results)
        except Exception as e:
            logger.warning(f"Viewshed elevation error: {e}")
    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING — SCENIC / VIEWPOINTS (Overpass)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_scenic_features(lat, lon, radius=5000):
    """Fetch peaks, viewpoints, scenic features, water bodies via Overpass."""
    query = f"""[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  node["natural"="peak"](around:{radius},{lat},{lon});
  node["tourism"="viewpoint"](around:{radius},{lat},{lon});
  node["natural"="saddle"](around:{radius},{lat},{lon});
  node["information"="guidepost"](around:{radius},{lat},{lon});
  way["natural"="water"](around:{radius},{lat},{lon});
  way["waterway"="river"](around:{radius},{lat},{lon});
  way["waterway"="stream"](around:{radius},{lat},{lon});
  node["historic"](around:{radius},{lat},{lon});
  node["tourism"="attraction"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=1800)
def fetch_obstructions(lat, lon, radius=3000):
    """Fetch buildings and forests that could obstruct views via Overpass."""
    query = f"""[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  way["building"](around:{radius},{lat},{lon});
  way["landuse"="forest"](around:{radius},{lat},{lon});
  way["natural"="wood"](around:{radius},{lat},{lon});
  way["landuse"="commercial"](around:{radius},{lat},{lon});
  way["landuse"="industrial"](around:{radius},{lat},{lon});
);
out count;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# VIEWSHED ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

def compute_viewshed(elevation_results, grid_size=15):
    """
    Simple line-of-sight viewshed from center of the grid.

    For each surrounding point, check if any intermediate grid cell blocks
    the line of sight from the center to that point (i.e., its elevation
    exceeds the interpolated elevation along the straight line from center
    to target). Returns (visible_count, total_count, center_elev, elev_grid).
    """
    if not elevation_results:
        return 0, 1, 0.0, []

    # Build 2D elevation grid
    elev_grid = []
    idx = 0
    for i in range(grid_size):
        row = []
        for j in range(grid_size):
            if idx < len(elevation_results):
                entry = elevation_results[idx]
                elev = entry.get("elevation", None) if isinstance(entry, dict) else None
                row.append(elev)
            else:
                row.append(None)
            idx += 1
        elev_grid.append(row)

    # Center point
    ci = grid_size // 2
    cj = grid_size // 2
    center_elev = elev_grid[ci][cj]
    if center_elev is None:
        # Try to find any valid center-ish elevation
        for di in range(-1, 2):
            for dj in range(-1, 2):
                ni, nj = ci + di, cj + dj
                if 0 <= ni < grid_size and 0 <= nj < grid_size:
                    if elev_grid[ni][nj] is not None:
                        center_elev = elev_grid[ni][nj]
                        break
            if center_elev is not None:
                break
    if center_elev is None:
        center_elev = 0.0

    # Observer height above ground (assume 2m)
    observer_elev = center_elev + 2.0

    visible_count = 0
    total_count = 0

    for ti in range(grid_size):
        for tj in range(grid_size):
            if ti == ci and tj == cj:
                continue
            target_elev = elev_grid[ti][tj]
            if target_elev is None:
                continue

            total_count += 1

            # Check line of sight from center to target
            # Sample intermediate points along the line
            dist = max(abs(ti - ci), abs(tj - cj))
            is_visible = True

            for step in range(1, dist):
                frac = step / dist
                mi = ci + frac * (ti - ci)
                mj = cj + frac * (tj - cj)

                # Bilinear index (nearest)
                mi_int = int(round(mi))
                mj_int = int(round(mj))
                mi_int = max(0, min(grid_size - 1, mi_int))
                mj_int = max(0, min(grid_size - 1, mj_int))

                mid_elev = elev_grid[mi_int][mj_int]
                if mid_elev is None:
                    continue

                # Line-of-sight elevation at this fraction
                los_elev = observer_elev + frac * (target_elev - observer_elev)

                if mid_elev > los_elev:
                    is_visible = False
                    break

            if is_visible:
                visible_count += 1

    return visible_count, max(total_count, 1), center_elev, elev_grid


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING — 5 DIMENSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def score_elevation_advantage(center_elev, elev_grid, grid_size=15):
    """
    Score 0-100: how much higher the center is relative to surroundings.
    A point 100m+ above average surroundings scores ~100.
    """
    all_elevs = []
    for row in elev_grid:
        for e in row:
            if e is not None:
                all_elevs.append(e)

    if not all_elevs:
        return 0.0, {}

    avg_surr = mean(all_elevs)
    min_surr = min(all_elevs)
    max_surr = max(all_elevs)
    advantage_m = center_elev - avg_surr

    # Normalize: 0m advantage = 20 (flat is ok), 100m+ = 100
    score = max(0.0, min(100.0, 20 + advantage_m * 0.8))
    # If below average, penalize harder
    if advantage_m < 0:
        score = max(0.0, 20 + advantage_m * 1.2)

    details = {
        "center_elevation_m": round(center_elev, 1),
        "avg_surrounding_m": round(avg_surr, 1),
        "min_surrounding_m": round(min_surr, 1),
        "max_surrounding_m": round(max_surr, 1),
        "advantage_m": round(advantage_m, 1),
    }
    return round(max(0.0, min(100.0, score)), 1), details


def score_visible_area(visible_count, total_count):
    """
    Score 0-100 based on viewshed ratio.
    100% visible = 100, 0% = 0, with slight non-linearity.
    """
    if total_count == 0:
        return 0.0, {}

    ratio = visible_count / total_count
    # Slightly generous curve: even 60% visibility is quite good
    score = min(100.0, ratio * 110.0)

    details = {
        "visible_points": visible_count,
        "total_points": total_count,
        "visibility_ratio": round(ratio * 100, 1),
    }
    return round(max(0.0, min(100.0, score)), 1), details


def score_scenic_value(scenic_data):
    """
    Score 0-100 based on nearby scenic features: peaks, viewpoints,
    water bodies, historic sites, attractions.
    """
    elements = scenic_data.get("elements", [])
    if not elements:
        return 15.0, {"features_found": 0, "categories": {}}

    categories = {
        "peaks": 0,
        "viewpoints": 0,
        "water_features": 0,
        "historic_sites": 0,
        "attractions": 0,
        "other": 0,
    }

    for el in elements:
        tags = el.get("tags", {})
        if tags.get("natural") == "peak" or tags.get("natural") == "saddle":
            categories["peaks"] += 1
        elif tags.get("tourism") == "viewpoint":
            categories["viewpoints"] += 1
        elif (tags.get("natural") == "water" or
              tags.get("waterway") in ("river", "stream")):
            categories["water_features"] += 1
        elif tags.get("historic"):
            categories["historic_sites"] += 1
        elif tags.get("tourism") == "attraction":
            categories["attractions"] += 1
        else:
            categories["other"] += 1

    # Weighted scoring
    score = 15.0  # baseline
    score += min(25.0, categories["peaks"] * 5.0)
    score += min(20.0, categories["viewpoints"] * 8.0)
    score += min(20.0, categories["water_features"] * 4.0)
    score += min(10.0, categories["historic_sites"] * 3.0)
    score += min(10.0, categories["attractions"] * 5.0)

    details = {
        "features_found": len(elements),
        "categories": {k: v for k, v in categories.items() if v > 0},
    }
    return round(max(0.0, min(100.0, score)), 1), details


def score_atmospheric_clarity(weather_data):
    """
    Score 0-100 based on current atmospheric conditions.
    Low humidity, no precipitation, low cloud cover = high score.
    """
    current = weather_data.get("current", {})
    if not current:
        return 50.0, {"status": "no weather data"}

    humidity = current.get("relative_humidity_2m", 50.0)
    if humidity is None:
        humidity = 50.0
    precipitation = current.get("precipitation", 0.0)
    if precipitation is None:
        precipitation = 0.0
    cloud_cover = current.get("cloud_cover", 50.0)
    if cloud_cover is None:
        cloud_cover = 50.0

    # Humidity: 20% = perfect, 100% = very poor
    humidity_score = max(0.0, 100.0 - (humidity - 20.0) * 1.25)

    # Precipitation: 0 = perfect, >5mm = terrible
    precip_score = max(0.0, 100.0 - precipitation * 20.0)

    # Cloud cover: 0% = perfect, 100% = poor
    cloud_score = max(0.0, 100.0 - cloud_cover)

    # Weighted average
    score = humidity_score * 0.3 + precip_score * 0.3 + cloud_score * 0.4

    details = {
        "humidity_pct": round(humidity, 1),
        "precipitation_mm": round(precipitation, 1),
        "cloud_cover_pct": round(cloud_cover, 1),
        "humidity_sub": round(humidity_score, 1),
        "precip_sub": round(precip_score, 1),
        "cloud_sub": round(cloud_score, 1),
    }
    return round(max(0.0, min(100.0, score)), 1), details


def score_obstruction_level(landuse_data, obstruction_data):
    """
    Score 0-100: fewer obstructions = higher score (inverted).
    Counts buildings and forest areas that could block views.
    """
    # Count from landuse data
    lu_elements = landuse_data.get("elements", [])
    buildings = 0
    forests = 0
    industrial = 0

    for el in lu_elements:
        tags = el.get("tags", {})
        if tags.get("building"):
            buildings += 1
        elif tags.get("landuse") in ("forest",):
            forests += 1
        elif tags.get("landuse") in ("commercial", "industrial"):
            industrial += 1

    # Count from obstruction-specific query (may have count tags)
    obs_elements = obstruction_data.get("elements", [])
    obs_count = 0
    for el in obs_elements:
        tags = el.get("tags", {})
        # Overpass "out count" returns total in tags
        total_str = tags.get("total", "0")
        try:
            obs_count = int(total_str)
        except (ValueError, TypeError):
            obs_count += 1

    # Combine counts
    total_obstructions = buildings + forests + industrial + obs_count

    # Scoring: 0 obstructions = 100, 500+ = 0
    # Inverted: fewer obstructions = higher viewshed quality
    raw = max(0.0, 100.0 - total_obstructions * 0.2)

    details = {
        "buildings_nearby": buildings,
        "forests_nearby": forests,
        "industrial_nearby": industrial,
        "obstruction_count_alt": obs_count,
        "total_obstructions": total_obstructions,
    }
    return round(max(0.0, min(100.0, raw)), 1), details


def compute_composite_score(scores):
    """Weighted composite of all 5 dimensions."""
    weights = {
        "Elevation Advantage": 0.20,
        "Visible Area": 0.30,
        "Scenic Value": 0.20,
        "Atmospheric Clarity": 0.15,
        "Obstruction Level": 0.15,
    }
    total_w = 0.0
    total_s = 0.0
    for dim, w in weights.items():
        s = scores.get(dim, 0.0)
        if s is not None:
            total_s += s * w
            total_w += w
    if total_w == 0:
        return 0.0
    return round(total_s / total_w, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_radar_chart(scores, composite):
    """Build a Plotly radar chart with 5 dimensions."""
    labels = list(DIMENSION_LABELS)
    values = [scores.get(lbl, 0.0) for lbl in labels]
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.25)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=8, color="#6366f1"),
        name="Viewshed Score",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                tickfont=dict(size=10, color="#9ca3af"),
                gridcolor="rgba(255,255,255,0.1)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#d1d5db"),
                gridcolor="rgba(255,255,255,0.15)",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=60, r=60, t=40, b=40),
        height=420,
        title=dict(
            text=f"Viewshed & Panorama Score: {composite}/100",
            font=dict(size=16, color="#e5e7eb"),
            x=0.5,
        ),
        showlegend=False,
    )
    return fig


def build_viewshed_heatmap(elev_grid, grid_size, center_elev):
    """Build a Plotly heatmap showing the elevation grid."""
    # Flatten grid, replace None with center_elev for display
    z = []
    for row in elev_grid:
        z_row = []
        for v in row:
            z_row.append(v if v is not None else center_elev)
        z.append(z_row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        colorscale="Earth",
        colorbar=dict(
            title=dict(text="Elev (m)", font=dict(color="#d1d5db")),
            tickfont=dict(color="#9ca3af"),
        ),
        hovertemplate="Row %{y}, Col %{x}<br>Elevation: %{z:.1f}m<extra></extra>",
    ))

    # Mark center
    ci = grid_size // 2
    fig.add_trace(go.Scatter(
        x=[ci], y=[ci],
        mode="markers",
        marker=dict(size=14, color="#ef4444", symbol="x", line=dict(width=2, color="white")),
        name="Observer",
        hovertemplate=f"Observer<br>Elevation: {center_elev:.1f}m<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=40, r=40, t=40, b=40),
        height=380,
        title=dict(
            text="Elevation Grid (Observer = X)",
            font=dict(size=14, color="#e5e7eb"),
            x=0.5,
        ),
        xaxis=dict(title="Grid Column", showgrid=False),
        yaxis=dict(title="Grid Row", showgrid=False),
        showlegend=True,
        legend=dict(font=dict(color="#d1d5db")),
    )
    return fig


def classify_viewshed(composite):
    """Return a text classification based on composite score."""
    if composite >= 85:
        return "Exceptional Panorama", "#10b981"
    elif composite >= 70:
        return "Very Good Visibility", "#22d3ee"
    elif composite >= 55:
        return "Good Vista", "#3b82f6"
    elif composite >= 40:
        return "Moderate View", "#f59e0b"
    elif composite >= 25:
        return "Limited Visibility", "#f97316"
    else:
        return "Obstructed / Poor View", "#ef4444"


def _scenic_feature_list(scenic_data):
    """Extract named scenic features for display."""
    elements = scenic_data.get("elements", [])
    features = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        ftype = ""
        if tags.get("natural") == "peak":
            ftype = "Peak"
            ele = tags.get("ele", "")
            if ele:
                name = f"{name} ({ele}m)" if name else f"Unnamed peak ({ele}m)"
        elif tags.get("tourism") == "viewpoint":
            ftype = "Viewpoint"
        elif tags.get("natural") == "water":
            ftype = "Water body"
        elif tags.get("waterway"):
            ftype = "Waterway"
        elif tags.get("historic"):
            ftype = f"Historic: {tags.get('historic', '')}"
        elif tags.get("tourism") == "attraction":
            ftype = "Attraction"
        elif tags.get("natural") == "saddle":
            ftype = "Saddle"
        elif tags.get("information") == "guidepost":
            ftype = "Guidepost"
        else:
            continue

        if name:
            features.append({"name": name, "type": ftype})
        elif ftype:
            features.append({"name": f"Unnamed {ftype.lower()}", "type": ftype})

    return features[:30]  # Limit display


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def render_viewshed_ai_tab():
    """Render the Viewshed & Panorama AI tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Viewshed &amp; Panorama AI</h4>"
        "<p>Assess visibility, scenic value and panoramic quality of any point &mdash; "
        "line-of-sight viewshed, atmospheric clarity, elevation advantage &amp; obstruction analysis</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Controls ──
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="vs_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="vs_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="vs_lon",
        )

    rc1, rc2 = st.columns([1, 1])
    with rc1:
        grid_size = st.select_slider(
            "Grid Resolution",
            options=[9, 11, 13, 15, 17, 19],
            value=VIEWSHED_GRID_SIZE,
            key="vs_grid",
            help="Higher = more accurate viewshed but slower API calls",
        )
    with rc2:
        search_radius_km = st.slider(
            "Scenic Search Radius (km)", 1, 15, 5, key="vs_radius",
        )

    run_btn = st.button(
        "Analyze Viewshed & Panorama",
        type="primary",
        key="vs_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Analyze Viewshed & Panorama** to begin.")
        return

    # ── Data Fetching ──
    radius_m = search_radius_km * 1000
    radius_deg = search_radius_km / 111.0  # rough conversion

    with st.spinner("Fetching elevation grid for viewshed..."):
        elev_results = fetch_viewshed_elevation(lat, lon, radius_deg=radius_deg, grid_size=grid_size)

    with st.spinner("Fetching scenic features & weather..."):
        scenic_data = fetch_scenic_features(lat, lon, radius=radius_m)
        weather_data = fetch_weather_data(lat, lon)
        landuse_data = fetch_landuse_infrastructure(lat, lon, radius=min(radius_m, 3000))
        obstruction_data = fetch_obstructions(lat, lon, radius=min(radius_m, 3000))

    # ── Viewshed Computation ──
    with st.spinner("Computing line-of-sight viewshed..."):
        visible_count, total_count, center_elev, elev_grid = compute_viewshed(
            elev_results, grid_size=grid_size,
        )

    # ── Scoring ──
    s1, d1 = score_elevation_advantage(center_elev, elev_grid, grid_size=grid_size)
    s2, d2 = score_visible_area(visible_count, total_count)
    s3, d3 = score_scenic_value(scenic_data)
    s4, d4 = score_atmospheric_clarity(weather_data)
    s5, d5 = score_obstruction_level(landuse_data, obstruction_data)

    scores = {
        "Elevation Advantage": s1,
        "Visible Area": s2,
        "Scenic Value": s3,
        "Atmospheric Clarity": s4,
        "Obstruction Level": s5,
    }
    details = {
        "Elevation Advantage": d1,
        "Visible Area": d2,
        "Scenic Value": d3,
        "Atmospheric Clarity": d4,
        "Obstruction Level": d5,
    }

    composite = compute_composite_score(scores)
    classification, class_color = classify_viewshed(composite)

    # ══════════════════════════════════════════════════════════════════════════
    # UI OUTPUT
    # ══════════════════════════════════════════════════════════════════════════

    # ── Composite Score Banner ──
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{class_color}22,{class_color}11);'
        f'border:1px solid {class_color}44;border-radius:12px;padding:18px 24px;'
        f'margin:10px 0 18px 0;text-align:center;">'
        f'<h2 style="margin:0;color:{class_color};">{composite}/100</h2>'
        f'<p style="margin:4px 0 0 0;font-size:1.1rem;color:#d1d5db;">'
        f'{classification}</p>'
        f'<p style="margin:2px 0 0 0;font-size:0.85rem;color:#9ca3af;">'
        f'{lat:.5f}, {lon:.5f} &mdash; Elevation: {center_elev:.0f}m</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Radar Chart + Elevation Heatmap ──
    col_radar, col_heat = st.columns([1, 1])
    with col_radar:
        radar_fig = build_radar_chart(scores, composite)
        st.plotly_chart(radar_fig, use_container_width=True, key="vs_radar")
    with col_heat:
        if elev_grid:
            heat_fig = build_viewshed_heatmap(elev_grid, grid_size, center_elev)
            st.plotly_chart(heat_fig, use_container_width=True, key="vs_heatmap")
        else:
            st.warning("No elevation data available for heatmap.")

    # ── Viewshed Coverage Metric ──
    vis_ratio = d2.get("visibility_ratio", 0.0)
    st.markdown(
        f'<div style="background:#1e293b;border-radius:10px;padding:14px 20px;'
        f'margin:8px 0 14px 0;border-left:4px solid #3b82f6;">'
        f'<span style="font-size:1.3rem;font-weight:700;color:#60a5fa;">'
        f'{vis_ratio:.1f}%</span>'
        f'<span style="color:#9ca3af;margin-left:10px;">Viewshed Coverage</span>'
        f'<span style="color:#6b7280;margin-left:6px;font-size:0.85rem;">'
        f'({visible_count} of {total_count} grid points visible from observer)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Dimension Detail Cards ──
    st.markdown("### Dimension Breakdown")

    dim_cols = st.columns(5)
    for idx, dim in enumerate(DIMENSION_LABELS):
        with dim_cols[idx]:
            sc = scores.get(dim, 0.0)
            col = DIMENSION_COLORS.get(dim, "#6366f1")
            icon = DIMENSION_ICONS.get(dim, "circle")
            bar_w = max(5, int(sc))
            st.markdown(
                f'<div style="background:#1e293b;border-radius:8px;padding:12px;'
                f'text-align:center;border-top:3px solid {col};min-height:110px;">'
                f'<div style="font-size:0.75rem;color:#9ca3af;margin-bottom:4px;">'
                f'<i class="fa fa-{icon}" style="margin-right:4px;"></i>{dim}</div>'
                f'<div style="font-size:1.4rem;font-weight:700;color:{col};">'
                f'{sc:.0f}</div>'
                f'<div style="background:#374151;border-radius:4px;height:6px;'
                f'margin-top:6px;">'
                f'<div style="background:{col};width:{bar_w}%;height:6px;'
                f'border-radius:4px;"></div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Detailed Metrics Expanders ──
    st.markdown("### Detailed Metrics")

    # Elevation Advantage details
    with st.expander(f"Elevation Advantage  ({s1:.0f}/100)", expanded=False):
        ea = details["Elevation Advantage"]
        if ea:
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Center Elevation", f"{ea.get('center_elevation_m', 0):.1f} m")
            mc2.metric("Avg Surrounding", f"{ea.get('avg_surrounding_m', 0):.1f} m")
            mc3.metric("Advantage", f"{ea.get('advantage_m', 0):+.1f} m")
            st.caption(
                f"Range: {ea.get('min_surrounding_m', 0):.0f}m "
                f"to {ea.get('max_surrounding_m', 0):.0f}m"
            )
        else:
            st.info("No elevation data.")

    # Visible Area details
    with st.expander(f"Visible Area  ({s2:.0f}/100)", expanded=False):
        va = details["Visible Area"]
        if va:
            vc1, vc2 = st.columns(2)
            vc1.metric("Visible Points", f"{va.get('visible_points', 0)}")
            vc2.metric("Total Grid Points", f"{va.get('total_points', 0)}")
            st.progress(min(1.0, va.get("visibility_ratio", 0) / 100.0))
            st.caption(
                f"Visibility ratio: {va.get('visibility_ratio', 0):.1f}% "
                f"(grid {grid_size}x{grid_size}, radius ~{search_radius_km}km)"
            )
        else:
            st.info("No viewshed data.")

    # Scenic Value details
    with st.expander(f"Scenic Value  ({s3:.0f}/100)", expanded=False):
        sv = details["Scenic Value"]
        if sv:
            st.write(f"**Features found:** {sv.get('features_found', 0)}")
            cats = sv.get("categories", {})
            if cats:
                cat_cols = st.columns(min(len(cats), 4))
                for ci_idx, (cat, cnt) in enumerate(cats.items()):
                    cat_cols[ci_idx % len(cat_cols)].metric(
                        cat.replace("_", " ").title(), cnt,
                    )
            # Named features table
            named = _scenic_feature_list(scenic_data)
            if named:
                st.markdown("**Notable features:**")
                for f in named[:15]:
                    st.markdown(
                        f'<span style="color:#9ca3af;font-size:0.85rem;">'
                        f'[{f["type"]}]</span> {f["name"]}',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No scenic features found nearby.")

    # Atmospheric Clarity details
    with st.expander(f"Atmospheric Clarity  ({s4:.0f}/100)", expanded=False):
        ac = details["Atmospheric Clarity"]
        if ac and ac.get("status") != "no weather data":
            wc1, wc2, wc3 = st.columns(3)
            wc1.metric("Humidity", f"{ac.get('humidity_pct', 0):.0f}%")
            wc2.metric("Precipitation", f"{ac.get('precipitation_mm', 0):.1f} mm")
            wc3.metric("Cloud Cover", f"{ac.get('cloud_cover_pct', 0):.0f}%")

            st.markdown("**Sub-scores:**")
            sub1, sub2, sub3 = st.columns(3)
            sub1.metric("Humidity Score", f"{ac.get('humidity_sub', 0):.0f}")
            sub2.metric("Precip Score", f"{ac.get('precip_sub', 0):.0f}")
            sub3.metric("Cloud Score", f"{ac.get('cloud_sub', 0):.0f}")
        else:
            st.info("No weather data available.")

    # Obstruction Level details
    with st.expander(f"Obstruction Level  ({s5:.0f}/100)", expanded=False):
        ol = details["Obstruction Level"]
        if ol:
            oc1, oc2, oc3 = st.columns(3)
            oc1.metric("Buildings", ol.get("buildings_nearby", 0))
            oc2.metric("Forests", ol.get("forests_nearby", 0))
            oc3.metric("Industrial", ol.get("industrial_nearby", 0))
            st.caption(
                f"Total obstruction features: {ol.get('total_obstructions', 0)} "
                f"(fewer = better view)"
            )
        else:
            st.info("No obstruction data.")

    # ── Visibility Summary ──
    st.markdown("### Visibility Summary")

    summary_lines = []
    if s1 >= 70:
        summary_lines.append(
            "Elevated position with commanding height advantage over surroundings."
        )
    elif s1 >= 40:
        summary_lines.append(
            "Moderate elevation relative to surroundings."
        )
    else:
        summary_lines.append(
            "Low-lying position with limited elevation advantage."
        )

    if vis_ratio >= 70:
        summary_lines.append(
            f"Excellent viewshed coverage ({vis_ratio:.0f}%) with wide unobstructed sightlines."
        )
    elif vis_ratio >= 40:
        summary_lines.append(
            f"Moderate viewshed ({vis_ratio:.0f}%), some terrain obstructions."
        )
    else:
        summary_lines.append(
            f"Limited viewshed ({vis_ratio:.0f}%), significant terrain blocking."
        )

    if s3 >= 60:
        n_feat = details["Scenic Value"].get("features_found", 0)
        summary_lines.append(
            f"Rich scenic surroundings with {n_feat} notable features nearby."
        )
    elif s3 >= 30:
        summary_lines.append("Some scenic features present in the area.")
    else:
        summary_lines.append("Limited scenic features in the immediate vicinity.")

    if s4 >= 70:
        summary_lines.append("Current atmospheric conditions are favorable for visibility.")
    elif s4 >= 40:
        summary_lines.append("Partial atmospheric interference (clouds or humidity).")
    else:
        summary_lines.append("Poor atmospheric clarity reducing effective visible range.")

    if s5 >= 70:
        summary_lines.append("Minimal built/vegetative obstructions in the immediate area.")
    elif s5 >= 40:
        summary_lines.append("Moderate obstructions from buildings or forest cover.")
    else:
        summary_lines.append("Dense obstructions (urban or forest) limiting panoramic views.")

    summary_html = "".join(
        f'<div style="padding:4px 0;color:#d1d5db;font-size:0.92rem;">'
        f'<span style="color:{DIMENSION_COLORS[DIMENSION_LABELS[i]]};'
        f'margin-right:6px;">&#9679;</span>{line}</div>'
        for i, line in enumerate(summary_lines)
    )
    st.markdown(
        f'<div style="background:#1e293b;border-radius:10px;padding:16px 20px;'
        f'margin:4px 0 10px 0;">{summary_html}</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Data sources: Open Topo Data (SRTM 90m), Overpass API (OSM), "
        "Open-Meteo (weather). All free, no API key required."
    )
