"""
Real Estate Intelligence AI — Site assessment combining location
desirability, connectivity, amenities & buildability.
Uses: Overpass, Open-Meteo, Open Topo Data, SoilGrids.
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
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

RE_COMPONENTS = {
    "desirability": {"name": "Location Desirability", "color": "#ef4444", "weight": 0.15},
    "transport": {"name": "Transport Connectivity", "color": "#3b82f6", "weight": 0.15},
    "education": {"name": "Education Quality", "color": "#f59e0b", "weight": 0.10},
    "healthcare": {"name": "Healthcare Access", "color": "#ec4899", "weight": 0.10},
    "commercial": {"name": "Commercial Vitality", "color": "#8b5cf6", "weight": 0.15},
    "green_spaces": {"name": "Green Spaces", "color": "#22c55e", "weight": 0.10},
    "construction": {"name": "Construction Feasibility", "color": "#6366f1", "weight": 0.15},
    "climate": {"name": "Climate Comfort", "color": "#10b981", "weight": 0.10},
}

CLASSIFICATION_THRESHOLDS = [
    (80, "Prime Location", "#10b981"),
    (60, "Desirable", "#22c55e"),
    (40, "Developing", "#f59e0b"),
    (20, "Emerging", "#f97316"),
    (0, "Remote/Rural", "#6b7280"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING (ALL CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_real_estate_data(lat, lon, radius=2000):
    """Fetch amenities and infrastructure for real estate."""
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"~"school|university|college|kindergarten|library"](around:{radius},{lat},{lon});
      node["amenity"~"hospital|clinic|pharmacy|doctors"](around:{radius},{lat},{lon});
      node["amenity"~"restaurant|cafe|bar|fast_food"](around:{radius},{lat},{lon});
      node["amenity"~"bank|atm|post_office"](around:{radius},{lat},{lon});
      node["shop"](around:{radius},{lat},{lon});
      node["public_transport"="stop_position"](around:{radius},{lat},{lon});
      node["railway"="station"](around:{radius},{lat},{lon});
      node["highway"="bus_stop"](around:{radius},{lat},{lon});
      way["leisure"~"park|garden|playground|sports_centre"](around:{radius},{lat},{lon});
      node["office"](around:{radius},{lat},{lon});
      way["highway"~"motorway|trunk|primary"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Real estate data error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_re(lat, lon):
    """Fetch elevation grid for slope analysis."""
    points = []
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            points.append(f"{lat + dy * 0.002},{lon + dx * 0.002}")
    try:
        resp = requests.get("https://api.opentopodata.org/v1/srtm90m",
                            params={"locations": "|".join(points)}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Elevation error: {e}")
        return {"results": []}


# ═══════════════════════════════════════════════════════════════════════════════
# AMENITY CLASSIFICATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def _classify_amenities(elements):
    """Classify Overpass elements into real-estate-relevant categories."""
    cats = {
        "schools": 0,
        "universities": 0,
        "libraries": 0,
        "hospitals": 0,
        "clinics": 0,
        "pharmacies": 0,
        "doctors": 0,
        "restaurants": 0,
        "cafes": 0,
        "shops": 0,
        "offices": 0,
        "banks": 0,
        "bus_stops": 0,
        "rail_stations": 0,
        "public_transport": 0,
        "major_roads": 0,
        "parks": 0,
        "gardens": 0,
        "playgrounds": 0,
        "sports_centres": 0,
        "kindergartens": 0,
    }
    amenity_types = set()

    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        shop = tags.get("shop", "")
        leisure = tags.get("leisure", "")
        highway = tags.get("highway", "")
        railway = tags.get("railway", "")
        pub_transport = tags.get("public_transport", "")
        office = tags.get("office", "")

        if amenity:
            amenity_types.add(amenity)

        # Education
        if amenity in ("school", "kindergarten"):
            cats["schools"] += 1
            if amenity == "kindergarten":
                cats["kindergartens"] += 1
        elif amenity == "university" or amenity == "college":
            cats["universities"] += 1
        elif amenity == "library":
            cats["libraries"] += 1

        # Healthcare
        elif amenity == "hospital":
            cats["hospitals"] += 1
        elif amenity == "clinic":
            cats["clinics"] += 1
        elif amenity == "pharmacy":
            cats["pharmacies"] += 1
        elif amenity == "doctors":
            cats["doctors"] += 1

        # Commercial — food/drink
        elif amenity in ("restaurant", "fast_food"):
            cats["restaurants"] += 1
        elif amenity in ("cafe", "bar"):
            cats["cafes"] += 1

        # Financial
        elif amenity in ("bank", "atm", "post_office"):
            cats["banks"] += 1

        # Shops
        if shop:
            cats["shops"] += 1

        # Offices
        if office:
            cats["offices"] += 1

        # Transport
        if highway == "bus_stop":
            cats["bus_stops"] += 1
        if railway == "station":
            cats["rail_stations"] += 1
        if pub_transport == "stop_position":
            cats["public_transport"] += 1

        # Major roads
        if tags.get("highway", "") in ("motorway", "trunk", "primary"):
            cats["major_roads"] += 1

        # Green/leisure
        if leisure == "park":
            cats["parks"] += 1
        elif leisure == "garden":
            cats["gardens"] += 1
        elif leisure == "playground":
            cats["playgrounds"] += 1
        elif leisure == "sports_centre":
            cats["sports_centres"] += 1

    return cats, amenity_types


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS (ALL 8 DIMENSIONS)
# ═══════════════════════════════════════════════════════════════════════════════

def _score_desirability(cats, amenity_types):
    """Location Desirability: amenity density, walkability estimate."""
    total_amenities = sum(cats.values())
    shops = cats.get("shops", 0)
    restaurants = cats.get("restaurants", 0) + cats.get("cafes", 0)
    unique_types = len(amenity_types)
    raw = total_amenities * 1.5 + shops * 2 + restaurants * 3 + unique_types * 5
    return min(100, max(0, raw))


def _score_transport(cats):
    """Transport Connectivity: bus stops, rail, major roads."""
    bus_stops = cats.get("bus_stops", 0) + cats.get("public_transport", 0)
    rail_stations = cats.get("rail_stations", 0)
    major_roads = cats.get("major_roads", 0)
    raw = bus_stops * 5 + rail_stations * 20 + major_roads * 3
    return min(100, max(0, raw))


def _score_education(cats):
    """Education Quality: schools, universities, libraries."""
    schools = cats.get("schools", 0)
    universities = cats.get("universities", 0)
    libraries = cats.get("libraries", 0)
    raw = schools * 10 + universities * 25 + libraries * 8
    return min(100, max(0, raw))


def _score_healthcare(cats):
    """Healthcare Access: hospitals, clinics, pharmacies, doctors."""
    hospitals = cats.get("hospitals", 0)
    clinics = cats.get("clinics", 0)
    pharmacies = cats.get("pharmacies", 0)
    doctors = cats.get("doctors", 0)
    raw = hospitals * 25 + clinics * 15 + pharmacies * 8 + doctors * 10
    return min(100, max(0, raw))


def _score_commercial(cats):
    """Commercial Vitality: shops, restaurants, offices, banks."""
    shops = cats.get("shops", 0)
    restaurants = cats.get("restaurants", 0) + cats.get("cafes", 0)
    offices = cats.get("offices", 0)
    banks = cats.get("banks", 0)
    raw = shops * 3 + restaurants * 3 + offices * 5 + banks * 8
    return min(100, max(0, raw))


def _score_green_spaces(cats):
    """Green Spaces: parks, gardens, playgrounds, nature/sports."""
    parks = cats.get("parks", 0)
    gardens = cats.get("gardens", 0)
    playgrounds = cats.get("playgrounds", 0)
    nature = cats.get("sports_centres", 0)
    raw = parks * 10 + gardens * 8 + playgrounds * 12 + nature * 15
    return min(100, max(0, raw))


def _score_construction(elevation_data, soil_data, water_data):
    """Construction Feasibility: slope, soil stability, flood risk."""
    # --- Slope penalty from elevation grid ---
    results = elevation_data.get("results", [])
    elevations = [r.get("elevation", 0) for r in results if r.get("elevation") is not None]
    slope_penalty = 0.0
    if len(elevations) >= 2:
        elev_range = max(elevations) - min(elevations)
        # Approximate slope: range over a ~900m grid
        slope_degrees = math.degrees(math.atan2(elev_range, 900))
        slope_penalty = min(40, slope_degrees * 3)

    # --- Clay penalty from SoilGrids ---
    clay_penalty = 0.0
    layers = soil_data.get("properties", {}).get("layers", [])
    clay_values = []
    for layer in layers:
        if layer.get("name") == "clay":
            for depth_entry in layer.get("depths", []):
                val = depth_entry.get("values", {}).get("mean")
                if val is not None:
                    clay_values.append(val / 10.0)  # g/kg -> %
    if clay_values:
        avg_clay = sum(clay_values) / len(clay_values)
        # High clay (>40%) is problematic for foundations
        if avg_clay > 40:
            clay_penalty = min(30, (avg_clay - 40) * 1.5)
        elif avg_clay > 25:
            clay_penalty = min(15, (avg_clay - 25) * 0.5)

    # --- Flood risk proxy from water features ---
    water_elements = water_data.get("elements", [])
    flood_risk = 0.0
    waterway_count = 0
    for el in water_elements:
        tags = el.get("tags", {})
        if "waterway" in tags or tags.get("natural") == "water":
            waterway_count += 1
    flood_risk = min(30, waterway_count * 3)

    raw = 100 - slope_penalty - clay_penalty - flood_risk
    return max(0, min(100, raw))


def _score_climate(weather_data):
    """Climate Comfort: temperature range, precipitation, humidity."""
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    # Average temperature
    daily_max_list = daily.get("temperature_2m_max", [])
    daily_min_list = daily.get("temperature_2m_min", [])
    daily_precip_list = daily.get("precipitation_sum", [])

    temps = [v for v in daily_max_list + daily_min_list if v is not None]
    avg_temp = sum(temps) / len(temps) if temps else current.get("temperature_2m", 15.0)
    if avg_temp is None:
        avg_temp = 15.0

    # Precipitation penalty
    precip_values = [v for v in daily_precip_list if v is not None]
    daily_avg_precip = sum(precip_values) / len(precip_values) if precip_values else 0.0
    excess_rain_penalty = max(0, (daily_avg_precip - 3) * 4)

    # Humidity penalty
    humidity = current.get("relative_humidity_2m", 50)
    if humidity is None:
        humidity = 50
    humidity_penalty = max(0, (humidity - 65) * 0.5)

    raw = 100 - abs(avg_temp - 20) * 3 - excess_rain_penalty - humidity_penalty
    return max(0, min(100, raw))


# ═══════════════════════════════════════════════════════════════════════════════
# OVERALL SCORE & CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_overall_score(scores):
    """Weighted average of all 8 dimensions."""
    total = 0.0
    for key, meta in RE_COMPONENTS.items():
        total += scores.get(key, 0) * meta["weight"]
    return round(total, 1)


def _classify_score(score):
    """Return (label, color) for the overall score."""
    for threshold, label, color in CLASSIFICATION_THRESHOLDS:
        if score >= threshold:
            return label, color
    return "Remote/Rural", "#6b7280"


# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_radar_chart(scores):
    """Build a Plotly radar chart of the 8 dimensions."""
    categories = []
    values = []
    colors = []
    for key, meta in RE_COMPONENTS.items():
        categories.append(meta["name"])
        values.append(scores.get(key, 0))
        colors.append(meta["color"])

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(99,102,241,0.2)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6, color="#6366f1"),
        name="Score",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15,23,42,0.65)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#8b97b0"),
                gridcolor="#2a3550",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#e8ecf4"),
                gridcolor="#2a3550",
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    return fig


def _build_amenity_bar_chart(cats):
    """Build a Plotly horizontal bar chart of amenity categories."""
    display_cats = {
        "Schools": cats.get("schools", 0),
        "Universities": cats.get("universities", 0),
        "Libraries": cats.get("libraries", 0),
        "Hospitals": cats.get("hospitals", 0),
        "Clinics": cats.get("clinics", 0),
        "Pharmacies": cats.get("pharmacies", 0),
        "Restaurants": cats.get("restaurants", 0) + cats.get("cafes", 0),
        "Shops": cats.get("shops", 0),
        "Offices": cats.get("offices", 0),
        "Banks/ATMs": cats.get("banks", 0),
        "Bus Stops": cats.get("bus_stops", 0) + cats.get("public_transport", 0),
        "Rail Stations": cats.get("rail_stations", 0),
        "Parks": cats.get("parks", 0),
        "Playgrounds": cats.get("playgrounds", 0),
    }
    # Sort by value descending
    sorted_cats = sorted(display_cats.items(), key=lambda x: x[1], reverse=False)
    labels = [item[0] for item in sorted_cats]
    values = [item[1] for item in sorted_cats]

    bar_colors = [
        "#3b82f6", "#6366f1", "#f59e0b", "#ef4444", "#ec4899",
        "#8b5cf6", "#f97316", "#10b981", "#22c55e", "#06b6d4",
        "#14b8a6", "#84cc16", "#a855f7", "#dc2626",
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(
            color=bar_colors[:len(labels)],
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        text=values,
        textposition="auto",
        textfont=dict(color="#e8ecf4", size=11),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.65)",
        xaxis=dict(
            title="Count",
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(
            tickfont=dict(color="#e8ecf4", size=11),
        ),
        margin=dict(l=120, r=20, t=10, b=40),
        height=400,
    )
    return fig


def _build_walkability_gauge(walkability_score):
    """Build a Plotly Indicator gauge for walkability."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=walkability_score,
        title=dict(text="Walkability Score", font=dict(color="#e8ecf4", size=16)),
        number=dict(font=dict(color="#e8ecf4", size=32)),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color="#8b97b0")),
            bar=dict(color="#6366f1"),
            bgcolor="rgba(15,23,42,0.65)",
            bordercolor="#2a3550",
            steps=[
                dict(range=[0, 25], color="#6b7280"),
                dict(range=[25, 50], color="#f97316"),
                dict(range=[50, 75], color="#f59e0b"),
                dict(range=[75, 100], color="#22c55e"),
            ],
            threshold=dict(
                line=dict(color="#ef4444", width=3),
                thickness=0.8,
                value=walkability_score,
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=60, b=20),
        height=280,
    )
    return fig


def _compute_walkability(cats):
    """Estimate walkability from amenity diversity and density."""
    total_pois = sum(cats.values())
    unique_cats = sum(1 for v in cats.values() if v > 0)
    raw = min(100, total_pois * 1.2 + unique_cats * 6)
    return round(raw, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# METRIC CARD HTML HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _render_score_card(name, score, color, detail_text=""):
    """Render a single dimension score card as styled HTML."""
    bar_width = min(score, 100)
    return (
        f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;'
        f'border-radius:12px;padding:14px 16px;backdrop-filter:blur(16px);'
        f'border-left:4px solid {color};">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="color:#e8ecf4;font-size:13px;font-weight:600;">{name}</span>'
        f'<span style="color:{color};font-size:20px;font-weight:bold;">'
        f'{score:.0f}</span></div>'
        f'<div style="background:#1a2235;border-radius:6px;height:8px;margin:8px 0 6px 0;">'
        f'<div style="width:{bar_width:.0f}%;background:{color};height:100%;'
        f'border-radius:6px;transition:width 0.6s;"></div></div>'
        f'<span style="color:#8b97b0;font-size:11px;">{detail_text}</span></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def render_real_estate_ai_tab():
    """Render the Real Estate Intelligence AI tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Real Estate Intelligence AI</h4>"
        "<p>AI-powered site assessment &mdash; combining location desirability, "
        "transport connectivity, amenities, construction feasibility &amp; climate comfort</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════════════════════
    # 1. LOCATION SELECTOR
    # ═══════════════════════════════════════════════════════════════════

    c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="re_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="re_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="re_lon",
        )

    r1, r2 = st.columns(2)
    with r1:
        radius_m = st.slider(
            "Search Radius (m)", 500, 5000, 2000, step=100, key="re_radius",
        )
    with r2:
        st.markdown(
            f"<p style='color:#8b97b0;margin-top:28px;'>Area: "
            f"~{math.pi * (radius_m / 1000) ** 2:.2f} km&sup2;</p>",
            unsafe_allow_html=True,
        )

    run = st.button(
        "Run Real Estate Analysis", type="primary",
        key="re_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Run Real Estate Analysis** to "
            "generate a comprehensive site assessment."
        )
        return

    # ═══════════════════════════════════════════════════════════════════
    # 2. FETCH ALL DATA
    # ═══════════════════════════════════════════════════════════════════

    progress = st.progress(0, text="Starting real estate analysis...")

    progress.progress(5, text="Fetching amenities & infrastructure (Overpass)...")
    re_data = fetch_real_estate_data(lat, lon, radius=radius_m)

    progress.progress(25, text="Fetching elevation grid (Open Topo Data)...")
    elevation_data = fetch_elevation_re(lat, lon)

    progress.progress(40, text="Fetching soil composition (SoilGrids)...")
    soil_data = fetch_soil_data(lat, lon)

    progress.progress(55, text="Fetching weather & climate (Open-Meteo)...")
    weather_data = fetch_weather_data(lat, lon)

    progress.progress(70, text="Fetching water features (Overpass)...")
    water_data = fetch_water_features(lat, lon, radius=radius_m)

    progress.progress(80, text="Fetching land use (Overpass)...")
    landuse_data = fetch_landuse_infrastructure(lat, lon, radius=radius_m)

    progress.progress(90, text="Computing scores...")

    # ═══════════════════════════════════════════════════════════════════
    # 3. CLASSIFY & SCORE
    # ═══════════════════════════════════════════════════════════════════

    elements = re_data.get("elements", [])
    cats, amenity_types = _classify_amenities(tuple())  # can't hash list directly
    # Re-classify without caching issue — pass raw
    cats, amenity_types = {}, set()
    cat_counts = {
        "schools": 0, "universities": 0, "libraries": 0,
        "hospitals": 0, "clinics": 0, "pharmacies": 0, "doctors": 0,
        "restaurants": 0, "cafes": 0, "shops": 0, "offices": 0, "banks": 0,
        "bus_stops": 0, "rail_stations": 0, "public_transport": 0,
        "major_roads": 0, "parks": 0, "gardens": 0, "playgrounds": 0,
        "sports_centres": 0, "kindergartens": 0,
    }
    all_amenity_types = set()

    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        shop = tags.get("shop", "")
        leisure = tags.get("leisure", "")
        highway = tags.get("highway", "")
        railway = tags.get("railway", "")
        pub_transport = tags.get("public_transport", "")
        office = tags.get("office", "")

        if amenity:
            all_amenity_types.add(amenity)

        # Education
        if amenity in ("school", "kindergarten"):
            cat_counts["schools"] += 1
            if amenity == "kindergarten":
                cat_counts["kindergartens"] += 1
        elif amenity in ("university", "college"):
            cat_counts["universities"] += 1
        elif amenity == "library":
            cat_counts["libraries"] += 1
        # Healthcare
        elif amenity == "hospital":
            cat_counts["hospitals"] += 1
        elif amenity == "clinic":
            cat_counts["clinics"] += 1
        elif amenity == "pharmacy":
            cat_counts["pharmacies"] += 1
        elif amenity == "doctors":
            cat_counts["doctors"] += 1
        # Food/drink
        elif amenity in ("restaurant", "fast_food"):
            cat_counts["restaurants"] += 1
        elif amenity in ("cafe", "bar"):
            cat_counts["cafes"] += 1
        # Financial
        elif amenity in ("bank", "atm", "post_office"):
            cat_counts["banks"] += 1

        if shop:
            cat_counts["shops"] += 1
        if office:
            cat_counts["offices"] += 1

        # Transport
        if highway == "bus_stop":
            cat_counts["bus_stops"] += 1
        if railway == "station":
            cat_counts["rail_stations"] += 1
        if pub_transport == "stop_position":
            cat_counts["public_transport"] += 1
        if tags.get("highway", "") in ("motorway", "trunk", "primary"):
            cat_counts["major_roads"] += 1

        # Green/leisure
        if leisure == "park":
            cat_counts["parks"] += 1
        elif leisure == "garden":
            cat_counts["gardens"] += 1
        elif leisure == "playground":
            cat_counts["playgrounds"] += 1
        elif leisure == "sports_centre":
            cat_counts["sports_centres"] += 1

    # Compute all 8 dimension scores
    scores = {
        "desirability": round(_score_desirability(cat_counts, all_amenity_types), 1),
        "transport": round(_score_transport(cat_counts), 1),
        "education": round(_score_education(cat_counts), 1),
        "healthcare": round(_score_healthcare(cat_counts), 1),
        "commercial": round(_score_commercial(cat_counts), 1),
        "green_spaces": round(_score_green_spaces(cat_counts), 1),
        "construction": round(_score_construction(elevation_data, soil_data, water_data), 1),
        "climate": round(_score_climate(weather_data), 1),
    }

    overall_score = _compute_overall_score(scores)
    classification, class_color = _classify_score(overall_score)
    walkability = _compute_walkability(cat_counts)

    progress.progress(100, text="Analysis complete!")

    # ═══════════════════════════════════════════════════════════════════
    # 4. DISPLAY — HEADER WITH CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("---")

    st.markdown(
        f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;'
        f'border-radius:16px;padding:24px 28px;text-align:center;'
        f'backdrop-filter:blur(16px);margin-bottom:16px;">'
        f'<h2 style="color:#e8ecf4;margin:0 0 6px 0;">Real Estate Intelligence Score</h2>'
        f'<span style="color:{class_color};font-size:56px;font-weight:bold;'
        f'line-height:1.1;">{overall_score:.0f}</span>'
        f'<span style="color:#8b97b0;font-size:18px;"> / 100</span><br/>'
        f'<span style="background:{class_color};color:#0a0e1a;padding:4px 16px;'
        f'border-radius:20px;font-size:14px;font-weight:700;'
        f'display:inline-block;margin-top:8px;">{classification}</span><br/>'
        f'<span style="color:#8b97b0;font-size:12px;margin-top:8px;'
        f'display:inline-block;">'
        f'{lat:.5f}, {lon:.5f} &mdash; radius {radius_m}m</span></div>',
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════════════════════
    # 5. RADAR CHART
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("### Dimension Analysis")
    radar_col, gauge_col = st.columns([1.3, 0.7])
    with radar_col:
        fig_radar = _build_radar_chart(scores)
        st.plotly_chart(fig_radar, use_container_width=True, key="rea_pchart1")
    with gauge_col:
        fig_gauge = _build_walkability_gauge(walkability)
        st.plotly_chart(fig_gauge, use_container_width=True, key="rea_pchart2")
        st.markdown(
            f'<p style="color:#8b97b0;font-size:12px;text-align:center;">'
            f'Walkability estimates how well daily needs can be met on foot '
            f'based on amenity diversity &amp; density.</p>',
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════════════════════════════════════════
    # 6. METRIC CARDS (4x2 grid)
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("### Score Breakdown")

    # Build detail text per component
    detail_texts = {
        "desirability": (
            f"{len(elements)} amenities, {len(all_amenity_types)} unique types, "
            f"{cat_counts.get('shops', 0)} shops"
        ),
        "transport": (
            f"{cat_counts.get('bus_stops', 0) + cat_counts.get('public_transport', 0)} bus/transit stops, "
            f"{cat_counts.get('rail_stations', 0)} rail stations, "
            f"{cat_counts.get('major_roads', 0)} major roads"
        ),
        "education": (
            f"{cat_counts.get('schools', 0)} schools, "
            f"{cat_counts.get('universities', 0)} universities, "
            f"{cat_counts.get('libraries', 0)} libraries"
        ),
        "healthcare": (
            f"{cat_counts.get('hospitals', 0)} hospitals, "
            f"{cat_counts.get('clinics', 0)} clinics, "
            f"{cat_counts.get('pharmacies', 0)} pharmacies, "
            f"{cat_counts.get('doctors', 0)} doctors"
        ),
        "commercial": (
            f"{cat_counts.get('shops', 0)} shops, "
            f"{cat_counts.get('restaurants', 0) + cat_counts.get('cafes', 0)} restaurants/cafes, "
            f"{cat_counts.get('offices', 0)} offices, "
            f"{cat_counts.get('banks', 0)} banks"
        ),
        "green_spaces": (
            f"{cat_counts.get('parks', 0)} parks, "
            f"{cat_counts.get('gardens', 0)} gardens, "
            f"{cat_counts.get('playgrounds', 0)} playgrounds"
        ),
        "construction": _get_construction_detail(elevation_data, soil_data, water_data),
        "climate": _get_climate_detail(weather_data),
    }

    keys = list(RE_COMPONENTS.keys())
    # Row 1: first 4
    row1 = st.columns(4)
    for idx in range(4):
        key = keys[idx]
        meta = RE_COMPONENTS[key]
        with row1[idx]:
            st.markdown(
                _render_score_card(
                    meta["name"], scores[key], meta["color"],
                    detail_texts.get(key, ""),
                ),
                unsafe_allow_html=True,
            )

    # Row 2: next 4
    row2 = st.columns(4)
    for idx in range(4, 8):
        key = keys[idx]
        meta = RE_COMPONENTS[key]
        with row2[idx - 4]:
            st.markdown(
                _render_score_card(
                    meta["name"], scores[key], meta["color"],
                    detail_texts.get(key, ""),
                ),
                unsafe_allow_html=True,
            )

    # ═══════════════════════════════════════════════════════════════════
    # 7. AMENITY DENSITY BAR CHART
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("### Amenity Density by Category")
    fig_bar = _build_amenity_bar_chart(cat_counts)
    st.plotly_chart(fig_bar, use_container_width=True, key="rea_pchart3")

    # ═══════════════════════════════════════════════════════════════════
    # 8. CONSTRUCTION FEASIBILITY SUMMARY
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("### Construction Feasibility Summary")
    con_c1, con_c2, con_c3 = st.columns(3)

    # Slope info
    results = elevation_data.get("results", [])
    elevations = [r.get("elevation", 0) for r in results if r.get("elevation") is not None]
    with con_c1:
        if len(elevations) >= 2:
            elev_min = min(elevations)
            elev_max = max(elevations)
            elev_range = elev_max - elev_min
            slope_deg = math.degrees(math.atan2(elev_range, 900))
            st.metric("Elevation Range", f"{elev_range:.1f} m")
            st.metric("Approx. Slope", f"{slope_deg:.1f} deg")
            if slope_deg < 5:
                slope_verdict = "Flat terrain - ideal for construction"
            elif slope_deg < 15:
                slope_verdict = "Moderate slope - buildable with grading"
            else:
                slope_verdict = "Steep terrain - significant earthworks needed"
            st.markdown(
                f'<p style="color:#8b97b0;font-size:12px;">{slope_verdict}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.metric("Elevation Range", "N/A")
            st.markdown(
                '<p style="color:#8b97b0;font-size:12px;">Elevation data unavailable</p>',
                unsafe_allow_html=True,
            )

    # Soil info
    with con_c2:
        layers = soil_data.get("properties", {}).get("layers", [])
        clay_values = []
        sand_values = []
        for layer in layers:
            if layer.get("name") == "clay":
                for d in layer.get("depths", []):
                    v = d.get("values", {}).get("mean")
                    if v is not None:
                        clay_values.append(v / 10.0)
            if layer.get("name") == "sand":
                for d in layer.get("depths", []):
                    v = d.get("values", {}).get("mean")
                    if v is not None:
                        sand_values.append(v / 10.0)

        avg_clay = sum(clay_values) / len(clay_values) if clay_values else 0
        avg_sand = sum(sand_values) / len(sand_values) if sand_values else 0
        st.metric("Avg. Clay Content", f"{avg_clay:.1f}%")
        st.metric("Avg. Sand Content", f"{avg_sand:.1f}%")
        if avg_clay > 40:
            soil_verdict = "High clay - poor drainage, foundation risk"
        elif avg_clay > 25:
            soil_verdict = "Moderate clay - standard foundations adequate"
        else:
            soil_verdict = "Low clay - good foundation conditions"
        st.markdown(
            f'<p style="color:#8b97b0;font-size:12px;">{soil_verdict}</p>',
            unsafe_allow_html=True,
        )

    # Flood risk info
    with con_c3:
        water_elements = water_data.get("elements", [])
        waterway_count = 0
        for el in water_elements:
            tags = el.get("tags", {})
            if "waterway" in tags or tags.get("natural") == "water":
                waterway_count += 1
        st.metric("Nearby Water Features", f"{waterway_count}")
        if waterway_count == 0:
            flood_verdict = "No nearby waterways - low flood risk"
        elif waterway_count <= 3:
            flood_verdict = "Some water features - moderate flood awareness"
        else:
            flood_verdict = "Multiple water features - flood assessment recommended"
        st.markdown(
            f'<p style="color:#8b97b0;font-size:12px;">{flood_verdict}</p>',
            unsafe_allow_html=True,
        )

        cons_score = scores.get("construction", 0)
        if cons_score >= 80:
            cons_label = "Excellent"
            cons_color = "#10b981"
        elif cons_score >= 60:
            cons_label = "Good"
            cons_color = "#22c55e"
        elif cons_score >= 40:
            cons_label = "Moderate"
            cons_color = "#f59e0b"
        else:
            cons_label = "Challenging"
            cons_color = "#ef4444"
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;'
            f'border-radius:10px;padding:10px;text-align:center;margin-top:10px;">'
            f'<span style="color:{cons_color};font-size:18px;font-weight:bold;">'
            f'{cons_label}</span><br/>'
            f'<span style="color:#8b97b0;font-size:11px;">Overall buildability</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DETAIL TEXT HELPERS (used by score cards)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_construction_detail(elevation_data, soil_data, water_data):
    """Build detail text for the construction card."""
    results = elevation_data.get("results", [])
    elevations = [r.get("elevation", 0) for r in results if r.get("elevation") is not None]
    parts = []
    if len(elevations) >= 2:
        elev_range = max(elevations) - min(elevations)
        slope_deg = math.degrees(math.atan2(elev_range, 900))
        parts.append(f"slope ~{slope_deg:.1f} deg")
    layers = soil_data.get("properties", {}).get("layers", [])
    clay_values = []
    for layer in layers:
        if layer.get("name") == "clay":
            for d in layer.get("depths", []):
                v = d.get("values", {}).get("mean")
                if v is not None:
                    clay_values.append(v / 10.0)
    if clay_values:
        avg_clay = sum(clay_values) / len(clay_values)
        parts.append(f"clay {avg_clay:.0f}%")
    water_elements = water_data.get("elements", [])
    wc = sum(1 for el in water_elements
             if "waterway" in el.get("tags", {}) or
             el.get("tags", {}).get("natural") == "water")
    parts.append(f"{wc} water features")
    return ", ".join(parts) if parts else "No detail available"


def _get_climate_detail(weather_data):
    """Build detail text for the climate card."""
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    temp = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    daily_max_list = daily.get("temperature_2m_max", [])
    daily_min_list = daily.get("temperature_2m_min", [])

    temps = [v for v in daily_max_list + daily_min_list if v is not None]
    avg_temp = sum(temps) / len(temps) if temps else (temp if temp is not None else 15)

    parts = []
    if temp is not None:
        parts.append(f"current {temp:.1f} C")
    parts.append(f"avg {avg_temp:.1f} C")
    if humidity is not None:
        parts.append(f"humidity {humidity}%")
    return ", ".join(parts) if parts else "No weather data"
