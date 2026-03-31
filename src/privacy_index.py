"""
Privacy & Isolation Index AI -- Location privacy assessment through
physical isolation, visual concealment, acoustic privacy & digital exposure.
Uses: Overpass, Open Topo Data.
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
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

PRIVACY_COMPONENTS = {
    "physical": {"name": "Physical Isolation", "color": "#22c55e", "weight": 0.20},
    "visual": {"name": "Visual Privacy", "color": "#3b82f6", "weight": 0.20},
    "acoustic": {"name": "Acoustic Privacy", "color": "#8b5cf6", "weight": 0.15},
    "digital": {"name": "Digital Privacy", "color": "#ef4444", "weight": 0.15},
    "access": {"name": "Access Difficulty", "color": "#f59e0b", "weight": 0.15},
    "light": {"name": "Light Pollution", "color": "#ec4899", "weight": 0.15},
}

PRIVACY_CLASSIFICATIONS = [
    (80, 100, "Ultra-Private", "#22c55e"),
    (60, 79, "Very Private", "#3b82f6"),
    (40, 59, "Private", "#8b5cf6"),
    (20, 39, "Semi-Private", "#f59e0b"),
    (0, 19, "Exposed", "#ef4444"),
]


# ==============================================================================
# HELPERS
# ==============================================================================

def _clamp(val, lo=0, hi=100):
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, val))


def _classify_privacy(score):
    """Return (label, color) for a privacy score."""
    for lo, hi, label, color in PRIVACY_CLASSIFICATIONS:
        if lo <= score <= hi:
            return label, color
    return "Exposed", "#ef4444"


# ==============================================================================
# DATA FETCHING
# ==============================================================================

@st.cache_data(ttl=1800)
def fetch_privacy_data(lat, lon, radius=3000):
    """Fetch infrastructure data for privacy assessment from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      way["building"](around:{radius},{lat},{lon});
      way["highway"](around:{radius},{lat},{lon});
      node["man_made"="surveillance"](around:{radius},{lat},{lon});
      node["man_made"="tower"]["tower:type"="communication"](around:{radius},{lat},{lon});
      way["aeroway"](around:{radius},{lat},{lon});
      way["railway"](around:{radius},{lat},{lon});
      way["landuse"="industrial"](around:{radius},{lat},{lon});
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      node["place"~"city|town|village"](around:10000,{lat},{lon});
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
        logger.warning("Privacy data error: %s", e)
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_privacy(lat, lon):
    """Fetch elevation grid for terrain concealment analysis."""
    locations = "|".join(
        f"{lat + dy * 0.005},{lon + dx * 0.005}"
        for dy in range(-3, 4)
        for dx in range(-3, 4)
    )
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm90m",
            params={"locations": locations},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Elevation error: %s", e)
        return {"results": []}


# ==============================================================================
# ELEMENT COUNTING
# ==============================================================================

@st.cache_data(ttl=1800)
def _parse_privacy_elements(data):
    """Parse Overpass elements into categorised counts and details."""
    elements = data.get("elements", []) if isinstance(data, dict) else []

    counts = {
        "buildings": 0,
        "highways_major": 0,
        "highways_minor": 0,
        "cameras": 0,
        "telecom_towers": 0,
        "airports": 0,
        "railways": 0,
        "industrial": 0,
        "forests": 0,
        "cities": 0,
        "towns": 0,
        "villages": 0,
    }

    city_details = []
    threat_details = []

    major_highway_types = {
        "motorway", "trunk", "primary", "secondary",
        "motorway_link", "trunk_link", "primary_link",
    }
    minor_highway_types = {
        "tertiary", "residential", "unclassified", "service",
        "living_street", "track", "path", "footway",
    }

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        # Buildings
        if tags.get("building"):
            counts["buildings"] += 1
            continue

        # Highways
        hw = tags.get("highway", "")
        if hw in major_highway_types:
            counts["highways_major"] += 1
            threat_details.append(
                {"type": "Road", "detail": f"Major road ({hw})", "impact": "High"}
            )
            continue
        if hw in minor_highway_types:
            counts["highways_minor"] += 1
            continue

        # Surveillance
        if tags.get("man_made") == "surveillance":
            counts["cameras"] += 1
            threat_details.append(
                {"type": "Camera", "detail": "Surveillance camera", "impact": "High"}
            )
            continue

        # Telecom towers
        if (tags.get("man_made") == "tower"
                and tags.get("tower:type") == "communication"):
            counts["telecom_towers"] += 1
            threat_details.append(
                {"type": "Telecom", "detail": "Communication tower", "impact": "Medium"}
            )
            continue

        # Airports
        if tags.get("aeroway"):
            counts["airports"] += 1
            threat_details.append(
                {"type": "Airport", "detail": f"Aeroway ({tags.get('aeroway', '')})",
                 "impact": "High"}
            )
            continue

        # Railways
        if tags.get("railway"):
            counts["railways"] += 1
            threat_details.append(
                {"type": "Railway", "detail": f"Railway ({tags.get('railway', '')})",
                 "impact": "Medium"}
            )
            continue

        # Industrial
        if tags.get("landuse") == "industrial":
            counts["industrial"] += 1
            threat_details.append(
                {"type": "Industrial", "detail": "Industrial zone", "impact": "Medium"}
            )
            continue

        # Forests / Woods
        if tags.get("natural") == "wood" or tags.get("landuse") == "forest":
            counts["forests"] += 1
            continue

        # Settlements
        place = tags.get("place", "")
        if place == "city":
            counts["cities"] += 1
            name = tags.get("name", "Unknown city")
            city_details.append({"name": name, "type": "city"})
            threat_details.append(
                {"type": "Settlement", "detail": f"City: {name}", "impact": "High"}
            )
        elif place == "town":
            counts["towns"] += 1
            name = tags.get("name", "Unknown town")
            city_details.append({"name": name, "type": "town"})
            threat_details.append(
                {"type": "Settlement", "detail": f"Town: {name}", "impact": "Medium"}
            )
        elif place == "village":
            counts["villages"] += 1
            name = tags.get("name", "Unknown village")
            city_details.append({"name": name, "type": "village"})

    return counts, city_details, threat_details


# ==============================================================================
# TERRAIN ANALYSIS
# ==============================================================================

@st.cache_data(ttl=1800)
def _compute_terrain_variation(elevation_data):
    """Compute terrain variation (standard deviation of elevations)."""
    results = elevation_data.get("results", []) if isinstance(elevation_data, dict) else []
    elevations = [
        r.get("elevation") for r in results
        if r.get("elevation") is not None
    ]
    if len(elevations) < 2:
        return 0.0
    mean_elev = sum(elevations) / len(elevations)
    variance = sum((e - mean_elev) ** 2 for e in elevations) / len(elevations)
    return math.sqrt(variance)


# ==============================================================================
# SCORING FUNCTIONS  (INVERTED: more isolation = higher score)
# ==============================================================================

@st.cache_data(ttl=1800)
def score_physical_isolation(counts):
    """
    Fewer buildings and roads in 3 km = higher score.
    buildings: 0->100, 10->80, 50->50, 200->20, 500+->0
    roads (major+minor) scaled similarly.
    """
    buildings = counts.get("buildings", 0)
    roads = counts.get("highways_major", 0) + counts.get("highways_minor", 0)

    # Building penalty
    if buildings == 0:
        b_score = 100
    elif buildings <= 10:
        b_score = 100 - (buildings * 2)
    elif buildings <= 50:
        b_score = 80 - ((buildings - 10) * 0.75)
    elif buildings <= 200:
        b_score = 50 - ((buildings - 50) * 0.2)
    elif buildings <= 500:
        b_score = 20 - ((buildings - 200) * (20 / 300))
    else:
        b_score = 0

    # Road penalty
    if roads == 0:
        r_score = 100
    elif roads <= 5:
        r_score = 90 - (roads * 2)
    elif roads <= 20:
        r_score = 80 - ((roads - 5) * 2)
    elif roads <= 50:
        r_score = 50 - ((roads - 20) * 1.0)
    else:
        r_score = max(0, 20 - (roads - 50) * 0.4)

    return round(_clamp(b_score * 0.6 + r_score * 0.4))


@st.cache_data(ttl=1800)
def score_visual_privacy(counts, terrain_variation):
    """
    Forest cover + terrain variation = higher concealment.
    forests * 10 + terrain_variation * 5
    """
    forests = counts.get("forests", 0)
    forest_contrib = min(50, forests * 10)
    terrain_contrib = min(50, terrain_variation * 0.5)
    return round(_clamp(forest_contrib + terrain_contrib))


@st.cache_data(ttl=1800)
def score_acoustic_privacy(counts):
    """
    100 - (highways_major*5 + airports*30 + railways*10 + industrial*8).
    Fewer noise sources = higher score.
    """
    highways = counts.get("highways_major", 0)
    airports = counts.get("airports", 0)
    railways = counts.get("railways", 0)
    industrial = counts.get("industrial", 0)

    penalty = highways * 5 + airports * 30 + railways * 10 + industrial * 8
    return round(_clamp(100 - penalty))


@st.cache_data(ttl=1800)
def score_digital_privacy(counts):
    """
    100 - (cameras*15 + telecom_towers*10).
    No surveillance = 100.
    """
    cameras = counts.get("cameras", 0)
    towers = counts.get("telecom_towers", 0)
    penalty = cameras * 15 + towers * 10
    return round(_clamp(100 - penalty))


@st.cache_data(ttl=1800)
def score_access_difficulty(counts, terrain_variation):
    """
    100 - (major_roads*10 + minor_roads*3).
    Fewer roads = harder access = more private.
    Terrain roughness adds bonus.
    """
    major = counts.get("highways_major", 0)
    minor = counts.get("highways_minor", 0)
    road_penalty = major * 10 + minor * 3
    terrain_bonus = min(20, terrain_variation * 0.2)
    return round(_clamp(100 - road_penalty + terrain_bonus))


@st.cache_data(ttl=1800)
def score_light_pollution(counts):
    """
    Estimate from city/town/village proximity.
    Cities within 10 km reduce score heavily. No cities = Bortle 1-2 = 100.
    """
    cities = counts.get("cities", 0)
    towns = counts.get("towns", 0)
    villages = counts.get("villages", 0)

    penalty = cities * 35 + towns * 15 + villages * 5
    return round(_clamp(100 - penalty))


# ==============================================================================
# MASTER SCORING
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_privacy_scores(lat, lon):
    """Compute all 6 privacy dimension scores for a location."""
    privacy_data = fetch_privacy_data(lat, lon, radius=3000)
    elevation_data = fetch_elevation_privacy(lat, lon)

    counts, city_details, threat_details = _parse_privacy_elements(privacy_data)
    terrain_var = _compute_terrain_variation(elevation_data)

    scores = {
        "physical": score_physical_isolation(counts),
        "visual": score_visual_privacy(counts, terrain_var),
        "acoustic": score_acoustic_privacy(counts),
        "digital": score_digital_privacy(counts),
        "access": score_access_difficulty(counts, terrain_var),
        "light": score_light_pollution(counts),
    }

    # Weighted overall
    overall = sum(
        scores[k] * PRIVACY_COMPONENTS[k]["weight"]
        for k in scores
    )
    overall = round(_clamp(overall))

    # Bortle estimate
    light_score = scores["light"]
    if light_score >= 90:
        bortle = "1-2 (Excellent dark sky)"
    elif light_score >= 70:
        bortle = "3 (Rural sky)"
    elif light_score >= 50:
        bortle = "4-5 (Rural/Suburban transition)"
    elif light_score >= 30:
        bortle = "6-7 (Suburban sky)"
    else:
        bortle = "8-9 (City sky)"

    return {
        "scores": scores,
        "overall": overall,
        "counts": counts,
        "city_details": city_details,
        "threat_details": threat_details,
        "terrain_variation": terrain_var,
        "bortle": bortle,
    }


# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def _render_header(overall, lat, lon):
    """Render the large header with overall score and classification."""
    label, color = _classify_privacy(overall)
    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem;
                background:linear-gradient(135deg, #1e293b, #0f172a);
                border-radius:16px; border:2px solid {color};
                margin-bottom:1.5rem;">
        <div style="font-size:3.5rem; font-weight:900; color:{color};">
            {overall}
        </div>
        <div style="font-size:1.3rem; color:{color}; font-weight:600;">
            {label}
        </div>
        <div style="color:#94a3b8; margin-top:0.5rem;">
            Privacy &amp; Isolation Index
        </div>
        <div style="color:#64748b; font-size:0.85rem;">
            ({lat:.4f}, {lon:.4f})
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_radar_chart(scores):
    """Render a radar chart of the 6 privacy dimensions."""
    keys = list(PRIVACY_COMPONENTS.keys())
    labels = [PRIVACY_COMPONENTS[k]["name"] for k in keys]
    values = [scores.get(k, 0) for k in keys]
    # Close the polygon
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        line_color="#06b6d4",
        fillcolor="rgba(6, 182, 212, 0.15)",
        name="Privacy Profile",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin=dict(t=40, b=40, l=80, r=80),
        showlegend=False,
        font=dict(color="#e2e8f0"),
    )
    st.plotly_chart(fig, use_container_width=True, key="priind_pchart1")


def _render_dimension_cards(scores, counts, terrain_var, bortle):
    """Render 6 metric cards in a 3x2 grid with scores and details."""
    details = {
        "physical": (
            f"Buildings: {counts.get('buildings', 0)} | "
            f"Roads: {counts.get('highways_major', 0) + counts.get('highways_minor', 0)}"
        ),
        "visual": (
            f"Forest areas: {counts.get('forests', 0)} | "
            f"Terrain variation: {terrain_var:.1f}m"
        ),
        "acoustic": (
            f"Major roads: {counts.get('highways_major', 0)} | "
            f"Airports: {counts.get('airports', 0)} | "
            f"Railways: {counts.get('railways', 0)}"
        ),
        "digital": (
            f"Cameras: {counts.get('cameras', 0)} | "
            f"Telecom towers: {counts.get('telecom_towers', 0)}"
        ),
        "access": (
            f"Major roads: {counts.get('highways_major', 0)} | "
            f"Minor roads: {counts.get('highways_minor', 0)} | "
            f"Terrain bonus: {min(20, terrain_var * 0.2):.0f}"
        ),
        "light": (
            f"Cities: {counts.get('cities', 0)} | "
            f"Towns: {counts.get('towns', 0)} | "
            f"Bortle: {bortle}"
        ),
    }

    keys = list(PRIVACY_COMPONENTS.keys())

    # Row 1: first 3
    cols_a = st.columns(3)
    for i, key in enumerate(keys[:3]):
        comp = PRIVACY_COMPONENTS[key]
        s = scores.get(key, 0)
        lbl, clr = _classify_privacy(s)
        with cols_a[i]:
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:1rem;
                        text-align:center; border-top:3px solid {comp['color']};
                        min-height:170px; margin-bottom:0.5rem;">
                <div style="font-size:2rem; font-weight:800; color:{comp['color']};">
                    {s}
                </div>
                <div style="font-weight:600; color:#e2e8f0; font-size:0.95rem;">
                    {comp['name']}
                </div>
                <div style="color:{clr}; font-size:0.8rem; font-weight:600;
                            margin-top:0.25rem;">
                    {lbl}
                </div>
                <div style="color:#64748b; font-size:0.72rem; margin-top:0.5rem;">
                    {details.get(key, '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Row 2: last 3
    cols_b = st.columns(3)
    for i, key in enumerate(keys[3:]):
        comp = PRIVACY_COMPONENTS[key]
        s = scores.get(key, 0)
        lbl, clr = _classify_privacy(s)
        with cols_b[i]:
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:1rem;
                        text-align:center; border-top:3px solid {comp['color']};
                        min-height:170px; margin-bottom:0.5rem;">
                <div style="font-size:2rem; font-weight:800; color:{comp['color']};">
                    {s}
                </div>
                <div style="font-weight:600; color:#e2e8f0; font-size:0.95rem;">
                    {comp['name']}
                </div>
                <div style="color:{clr}; font-size:0.8rem; font-weight:600;
                            margin-top:0.25rem;">
                    {lbl}
                </div>
                <div style="color:#64748b; font-size:0.72rem; margin-top:0.5rem;">
                    {details.get(key, '')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_threats_table(threat_details):
    """Render a table of detected privacy threats."""
    if not threat_details:
        st.info("No significant privacy threats detected in this area.")
        return

    impact_colors = {
        "High": "#ef4444",
        "Medium": "#f59e0b",
        "Low": "#22c55e",
    }

    rows_html = ""
    for t in threat_details[:20]:  # cap at 20 rows
        t_type = t.get("type", "Unknown")
        t_detail = t.get("detail", "")
        t_impact = t.get("impact", "Low")
        i_color = impact_colors.get(t_impact, "#94a3b8")
        rows_html += f"""
        <tr>
            <td style="padding:0.5rem; color:#e2e8f0;">{t_type}</td>
            <td style="padding:0.5rem; color:#94a3b8;">{t_detail}</td>
            <td style="padding:0.5rem;">
                <span style="color:{i_color}; font-weight:600;">{t_impact}</span>
            </td>
        </tr>
        """

    st.markdown(f"""
    <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; background:#1e293b;
                      border-radius:8px; overflow:hidden;">
            <thead>
                <tr style="background:#334155;">
                    <th style="padding:0.6rem; text-align:left; color:#e2e8f0;">
                        Threat Type
                    </th>
                    <th style="padding:0.6rem; text-align:left; color:#e2e8f0;">
                        Detail
                    </th>
                    <th style="padding:0.6rem; text-align:left; color:#e2e8f0;">
                        Impact
                    </th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


def _render_bar_chart(scores):
    """Render a horizontal bar chart comparing all 6 dimensions."""
    keys = list(PRIVACY_COMPONENTS.keys())
    labels = [PRIVACY_COMPONENTS[k]["name"] for k in keys]
    values = [scores.get(k, 0) for k in keys]
    colors = [PRIVACY_COMPONENTS[k]["color"] for k in keys]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v}" for v in values],
        textposition="auto",
        textfont=dict(color="#ffffff", size=13),
    ))
    fig.update_layout(
        xaxis=dict(
            range=[0, 100],
            title="Score",
            gridcolor="rgba(148,163,184,0.15)",
            tickfont=dict(color="#94a3b8"),
        ),
        yaxis=dict(
            tickfont=dict(color="#e2e8f0", size=12),
            autorange="reversed",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(t=20, b=40, l=150, r=30),
        font=dict(color="#e2e8f0"),
    )
    st.plotly_chart(fig, use_container_width=True, key="priind_pchart2")


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def render_privacy_index_tab():
    """Main render function for Privacy & Isolation Index AI tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Privacy &amp; Isolation Index</h4>
        <p>Assess how private and isolated a location is across 6 dimensions
           using infrastructure density, terrain, surveillance, and settlement data</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Location selector ---
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="priv_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    d_lat = p.get("lat", 41.90) if p else 41.90
    d_lon = p.get("lon", 12.50) if p else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Latitude", -90.0, 90.0, d_lat,
                step=0.01, key="priv_lat", format="%.4f",
            )
        with c2:
            lon = st.number_input(
                "Longitude", -180.0, 180.0, d_lon,
                step=0.01, key="priv_lon", format="%.4f",
            )

    if st.button("Analyse Privacy Index", type="primary", use_container_width=True):
        progress = st.progress(0, text="Initialising privacy analysis...")

        progress.progress(10, text="Fetching infrastructure & surveillance data...")
        try:
            result = compute_privacy_scores(lat, lon)
        except Exception as e:
            logger.warning("Privacy scoring error: %s", e)
            result = {
                "scores": {k: 0 for k in PRIVACY_COMPONENTS},
                "overall": 0,
                "counts": {},
                "city_details": [],
                "threat_details": [],
                "terrain_variation": 0.0,
                "bortle": "N/A",
            }

        progress.progress(100, text="Privacy analysis complete!")

        st.session_state["priv_results"] = {
            "result": result,
            "lat": lat,
            "lon": lon,
        }

    # --- Display results ---
    if "priv_results" not in st.session_state:
        return

    data = st.session_state["priv_results"]
    result = data["result"]
    lat_r = data["lat"]
    lon_r = data["lon"]

    scores = result.get("scores", {})
    overall = result.get("overall", 0)
    counts = result.get("counts", {})
    threat_details = result.get("threat_details", [])
    terrain_var = result.get("terrain_variation", 0.0)
    bortle = result.get("bortle", "N/A")

    st.markdown("---")

    # 1. Header with overall score + classification
    _render_header(overall, lat_r, lon_r)

    # 2. Radar chart
    st.markdown("### Privacy Profile Radar")
    _render_radar_chart(scores)

    # 3. Six dimension cards (3x2)
    st.markdown("### Dimension Scores")
    _render_dimension_cards(scores, counts, terrain_var, bortle)

    # 4. Privacy threats table
    st.markdown("### Privacy Threats Detected")
    _render_threats_table(threat_details)

    # 5. Comparative bar chart
    st.markdown("### Dimension Comparison")
    _render_bar_chart(scores)
