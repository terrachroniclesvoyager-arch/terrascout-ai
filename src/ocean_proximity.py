"""
Ocean Proximity Analysis module for TerraScout AI.
Analyzes proximity to ocean/sea, coastal features, and maritime influence
on a given location using free APIs (Open Topo Data, Overpass, Open-Meteo).
"""

import streamlit as st
import requests
import json
import math

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ELEVATION_API = "https://api.opentopodata.org/v1/srtm30m"
OVERPASS_API = "https://overpass-api.de/api/interpreter"
MARINE_API = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

COASTAL_SEARCH_RADII = [1, 5, 10, 25, 50, 100]  # km

CLIMATE_ZONE_THRESHOLDS = {
    "tropical": (0, 23.5),
    "subtropical": (23.5, 35),
    "temperate": (35, 55),
    "subpolar": (55, 66.5),
    "polar": (66.5, 90),
}

BIODIVERSITY_BASE = {
    "tropical": 95,
    "subtropical": 80,
    "temperate": 65,
    "subpolar": 45,
    "polar": 30,
}

COMPASS_DIRS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _deg_to_compass(deg):
    """Convert degrees (0-360) to compass bearing string."""
    if deg is None:
        return "N/A"
    ix = round(deg / 22.5) % 16
    return COMPASS_DIRS[ix]


def _haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _climate_zone(lat):
    """Return climate zone name based on absolute latitude."""
    abs_lat = abs(lat)
    for zone, (lo, hi) in CLIMATE_ZONE_THRESHOLDS.items():
        if lo <= abs_lat < hi:
            return zone
    return "polar"


def _clamp(value, lo=0, hi=100):
    """Clamp a numeric value between lo and hi."""
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# API-calling functions (all cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_elevation(lat, lon):
    """Fetch elevation in metres from Open Topo Data."""
    try:
        url = f"{ELEVATION_API}?locations={lat},{lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("elevation")
        return None
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_coastline_distance(lat, lon, radius_km):
    """
    Query Overpass for coastline/water ways within a radius.
    Returns list of dicts with lat, lon, distance_km, feature_type.
    """
    radius_m = radius_km * 1000
    query = f"""
    [out:json][timeout:25];
    (
      way["natural"="coastline"](around:{radius_m},{lat},{lon});
      way["natural"="water"](around:{radius_m},{lat},{lon});
      way["natural"="bay"](around:{radius_m},{lat},{lon});
      way["natural"="strait"](around:{radius_m},{lat},{lon});
      node["natural"="coastline"](around:{radius_m},{lat},{lon});
      way["waterway"="river"](around:{radius_m},{lat},{lon});
      relation["natural"="water"]["water"="sea"](around:{radius_m},{lat},{lon});
      relation["natural"="water"]["water"="ocean"](around:{radius_m},{lat},{lon});
    );
    out center 50;
    """
    try:
        resp = requests.get(OVERPASS_API, params={"data": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        features = []
        for el in elements:
            elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
            elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
            if elat is None or elon is None:
                continue
            tags = el.get("tags", {})
            ftype = tags.get("natural") or tags.get("waterway") or tags.get("water") or "water"
            dist = _haversine(lat, lon, elat, elon)
            features.append({
                "lat": elat,
                "lon": elon,
                "distance_km": round(dist, 2),
                "feature_type": ftype,
                "name": tags.get("name", ""),
            })
        features.sort(key=lambda x: x["distance_km"])
        return features
    except Exception:
        return []


@st.cache_data(ttl=900)
def _fetch_coastal_infrastructure(lat, lon, radius_km):
    """
    Query Overpass for harbors, marinas, piers, lighthouses, beaches.
    Returns dict of category -> list of feature dicts.
    """
    radius_m = radius_km * 1000
    query = f"""
    [out:json][timeout:25];
    (
      node["leisure"="marina"](around:{radius_m},{lat},{lon});
      way["leisure"="marina"](around:{radius_m},{lat},{lon});
      node["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
      way["man_made"="lighthouse"](around:{radius_m},{lat},{lon});
      node["man_made"="pier"](around:{radius_m},{lat},{lon});
      way["man_made"="pier"](around:{radius_m},{lat},{lon});
      node["harbour"="yes"](around:{radius_m},{lat},{lon});
      way["harbour"="yes"](around:{radius_m},{lat},{lon});
      node["natural"="beach"](around:{radius_m},{lat},{lon});
      way["natural"="beach"](around:{radius_m},{lat},{lon});
      node["seamark:type"="harbour"](around:{radius_m},{lat},{lon});
      node["amenity"="ferry_terminal"](around:{radius_m},{lat},{lon});
    );
    out center 100;
    """
    categories = {
        "harbors": [],
        "marinas": [],
        "piers": [],
        "lighthouses": [],
        "beaches": [],
        "ferry_terminals": [],
    }
    try:
        resp = requests.get(OVERPASS_API, params={"data": query}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        for el in elements:
            elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
            elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
            if elat is None or elon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name", "Unnamed")
            dist = _haversine(lat, lon, elat, elon)
            item = {"lat": elat, "lon": elon, "name": name, "distance_km": round(dist, 2)}

            if tags.get("leisure") == "marina":
                categories["marinas"].append(item)
            elif tags.get("man_made") == "lighthouse":
                categories["lighthouses"].append(item)
            elif tags.get("man_made") == "pier":
                categories["piers"].append(item)
            elif tags.get("harbour") == "yes" or tags.get("seamark:type") == "harbour":
                categories["harbors"].append(item)
            elif tags.get("natural") == "beach":
                categories["beaches"].append(item)
            elif tags.get("amenity") == "ferry_terminal":
                categories["ferry_terminals"].append(item)

        # Sort each category by distance
        for cat in categories:
            categories[cat].sort(key=lambda x: x["distance_km"])
        return categories
    except Exception:
        return categories


@st.cache_data(ttl=900)
def _fetch_marine_weather(lat, lon):
    """Fetch current marine conditions from Open-Meteo Marine API."""
    try:
        url = (
            f"{MARINE_API}?latitude={lat}&longitude={lon}"
            f"&current=wave_height,wave_direction,wave_period,wind_wave_height"
            f"&daily=wave_height_max,wave_period_max"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    """Fetch current weather from Open-Meteo Weather API."""
    try:
        url = (
            f"{WEATHER_API}?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------
def _estimate_coastal_distance(lat, lon):
    """
    Try progressively larger radii to find nearest coastal feature.
    Returns (distance_km, nearest_feature) or (None, None).
    """
    for r in COASTAL_SEARCH_RADII:
        features = _fetch_coastline_distance(lat, lon, r)
        if features:
            nearest = features[0]
            return nearest["distance_km"], nearest
    return None, None


def _compute_flood_risk(elevation, coast_dist):
    """
    Compute flood/tsunami risk score 0-100 based on elevation & coast distance.
    Lower elevation + closer to coast = higher risk.
    """
    if elevation is None or coast_dist is None:
        return None, "Insufficient data"

    # Elevation factor: below 10m is high risk, above 100m is low
    if elevation <= 0:
        elev_score = 100
    elif elevation < 5:
        elev_score = 90
    elif elevation < 10:
        elev_score = 70
    elif elevation < 25:
        elev_score = 50
    elif elevation < 50:
        elev_score = 30
    elif elevation < 100:
        elev_score = 15
    else:
        elev_score = 5

    # Distance factor: within 1km is high risk, beyond 50km is low
    if coast_dist < 0.5:
        dist_score = 100
    elif coast_dist < 1:
        dist_score = 85
    elif coast_dist < 5:
        dist_score = 65
    elif coast_dist < 10:
        dist_score = 45
    elif coast_dist < 25:
        dist_score = 25
    elif coast_dist < 50:
        dist_score = 10
    else:
        dist_score = 5

    risk_score = int(0.5 * elev_score + 0.5 * dist_score)

    if risk_score >= 80:
        label = "Very High"
    elif risk_score >= 60:
        label = "High"
    elif risk_score >= 40:
        label = "Moderate"
    elif risk_score >= 20:
        label = "Low"
    else:
        label = "Very Low"

    return risk_score, label


def _compute_biodiversity_score(lat, coast_dist, water_features_count):
    """
    Estimate marine biodiversity potential score 0-100.
    Based on climate zone, coast proximity, and water feature density.
    """
    zone = _climate_zone(lat)
    base = BIODIVERSITY_BASE.get(zone, 50)

    # Proximity bonus: closer = higher biodiversity potential
    if coast_dist is not None:
        if coast_dist < 1:
            prox_bonus = 20
        elif coast_dist < 5:
            prox_bonus = 15
        elif coast_dist < 10:
            prox_bonus = 10
        elif coast_dist < 25:
            prox_bonus = 5
        else:
            prox_bonus = 0
    else:
        prox_bonus = 0

    # Water features bonus
    feat_bonus = min(15, water_features_count * 2)

    score = _clamp(base + prox_bonus + feat_bonus)
    return score, zone


def _compute_ocean_influence(coast_dist, elevation, marine_data, weather_data,
                             infra_count, biodiversity_score):
    """
    Compute composite Ocean Influence Score 0-100 across 6 dimensions.
    Returns (total_score, dimension_dict).
    """
    dims = {}

    # 1. Proximity (0-100) - inverse of distance
    if coast_dist is not None:
        if coast_dist < 0.5:
            dims["Proximity"] = 100
        elif coast_dist < 1:
            dims["Proximity"] = 90
        elif coast_dist < 5:
            dims["Proximity"] = 75
        elif coast_dist < 10:
            dims["Proximity"] = 60
        elif coast_dist < 25:
            dims["Proximity"] = 40
        elif coast_dist < 50:
            dims["Proximity"] = 25
        elif coast_dist < 100:
            dims["Proximity"] = 15
        else:
            dims["Proximity"] = 5
    else:
        dims["Proximity"] = 0

    # 2. Marine Weather Intensity
    wave_h = None
    if marine_data:
        current = marine_data.get("current", {})
        wave_h = current.get("wave_height")
    if wave_h is not None:
        dims["Marine Weather"] = _clamp(int(wave_h * 20), 0, 100)
    else:
        dims["Marine Weather"] = 0

    # 3. Humidity / Maritime Climate
    humidity = None
    if weather_data:
        current = weather_data.get("current", {})
        humidity = current.get("relative_humidity_2m")
    if humidity is not None:
        dims["Maritime Climate"] = _clamp(int(humidity), 0, 100)
    else:
        dims["Maritime Climate"] = 50

    # 4. Coastal Infrastructure
    dims["Infrastructure"] = _clamp(min(100, infra_count * 8))

    # 5. Elevation Risk (inverted - lower = more ocean influence)
    if elevation is not None:
        if elevation <= 0:
            dims["Sea-Level Exposure"] = 100
        elif elevation < 10:
            dims["Sea-Level Exposure"] = 80
        elif elevation < 50:
            dims["Sea-Level Exposure"] = 50
        elif elevation < 200:
            dims["Sea-Level Exposure"] = 25
        else:
            dims["Sea-Level Exposure"] = 10
    else:
        dims["Sea-Level Exposure"] = 30

    # 6. Biodiversity
    dims["Biodiversity"] = biodiversity_score

    total = int(sum(dims.values()) / len(dims)) if dims else 0
    return total, dims


# ---------------------------------------------------------------------------
# Plotly chart builders
# ---------------------------------------------------------------------------
def _gauge_chart(value, title, max_val=100, color_ranges=None):
    """Build a plotly gauge indicator."""
    if color_ranges is None:
        color_ranges = [
            {"range": [0, 30], "color": "#10b981"},
            {"range": [30, 60], "color": "#f59e0b"},
            {"range": [60, 100], "color": "#ef4444"},
        ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value if value is not None else 0,
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, max_val], "tickwidth": 1},
            "bar": {"color": "#3b82f6"},
            "steps": color_ranges,
        },
    ))
    fig.update_layout(height=250, margin=dict(t=60, b=20, l=30, r=30))
    return fig


def _radar_chart(dimensions):
    """Build a plotly radar chart from dimension dict."""
    cats = list(dimensions.keys())
    vals = list(dimensions.values())
    # Close the polygon
    cats_closed = cats + [cats[0]]
    vals_closed = vals + [vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor="rgba(59,130,246,0.25)",
        line=dict(color="#3b82f6", width=2),
        name="Ocean Influence",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
        ),
        showlegend=False,
        height=400,
        margin=dict(t=40, b=40, l=60, r=60),
        title=dict(text="Ocean Influence Dimensions", font=dict(size=14)),
    )
    return fig


def _wave_gauge(wave_height, title="Wave Height"):
    """Gauge chart for wave height with sea-state color coding."""
    color_ranges = [
        {"range": [0, 0.5], "color": "#10b981"},
        {"range": [0.5, 1.25], "color": "#38bdf8"},
        {"range": [1.25, 2.5], "color": "#f59e0b"},
        {"range": [2.5, 4.0], "color": "#f97316"},
        {"range": [4.0, 8.0], "color": "#ef4444"},
    ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=wave_height if wave_height is not None else 0,
        number={"suffix": " m"},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 8], "tickwidth": 1},
            "bar": {"color": "#1e40af"},
            "steps": color_ranges,
        },
    ))
    fig.update_layout(height=250, margin=dict(t=60, b=20, l=30, r=30))
    return fig


# ---------------------------------------------------------------------------
# Folium map builders
# ---------------------------------------------------------------------------
def _build_infrastructure_map(lat, lon, categories):
    """Build a folium map showing coastal infrastructure."""
    if not HAS_FOLIUM:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB positron")
    folium.Marker(
        [lat, lon],
        popup="Analysis Location",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)

    icon_map = {
        "harbors": ("anchor", "blue"),
        "marinas": ("ship", "darkblue"),
        "piers": ("road", "gray"),
        "lighthouses": ("lightbulb", "orange"),
        "beaches": ("umbrella-beach", "beige"),
        "ferry_terminals": ("ferry", "green"),
    }

    for cat, items in categories.items():
        icon_name, color = icon_map.get(cat, ("info-sign", "gray"))
        for item in items:
            folium.Marker(
                [item["lat"], item["lon"]],
                popup=f"{cat.title()}: {item['name']} ({item['distance_km']} km)",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
            ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_ocean_proximity_tab():
    """Entry point for Ocean Proximity Analysis module."""
    st.markdown("## Ocean Proximity Analysis")
    st.markdown(
        "Analyze proximity to ocean and sea, coastal features, maritime weather, "
        "and the overall influence of the ocean on a given location."
    )

    # ── Coordinate inputs ─────────────────────────────────────────────
    col_in1, col_in2, col_in3 = st.columns([2, 2, 1])
    with col_in1:
        lat = st.number_input(
            "Latitude", value=40.85, min_value=-90.0, max_value=90.0,
            step=0.01, format="%.4f", key="ocp_lat",
        )
    with col_in2:
        lon = st.number_input(
            "Longitude", value=14.27, min_value=-180.0, max_value=180.0,
            step=0.01, format="%.4f", key="ocp_lon",
        )
    with col_in3:
        search_radius = st.selectbox(
            "Search radius (km)", options=[10, 25, 50, 100],
            index=1, key="ocp_radius",
        )

    analyze = st.button("Analyze Ocean Proximity", key="ocp_analyze", type="primary")

    if not analyze:
        st.info("Enter coordinates and click **Analyze Ocean Proximity** to begin.")
        return

    # ── Fetch all data ────────────────────────────────────────────────
    with st.spinner("Fetching elevation data..."):
        elevation = _fetch_elevation(lat, lon)

    with st.spinner("Searching for coastline features..."):
        coast_dist, nearest_coast = _estimate_coastal_distance(lat, lon)

    with st.spinner("Scanning coastal infrastructure..."):
        infra = _fetch_coastal_infrastructure(lat, lon, search_radius)

    with st.spinner("Fetching marine weather..."):
        marine_data = _fetch_marine_weather(lat, lon)

    with st.spinner("Fetching local weather..."):
        weather_data = _fetch_weather(lat, lon)

    # Count total water features found in initial scan
    water_count = len(_fetch_coastline_distance(lat, lon, search_radius))

    # Total infrastructure count
    infra_total = sum(len(v) for v in infra.values())

    # ──────────────────────────────────────────────────────────────────
    # SECTION 1: Coastal Distance Estimate
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 1. Coastal Distance Estimate")

    if coast_dist is not None and nearest_coast is not None:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Nearest Coast/Water", f"{coast_dist:.1f} km")
        with c2:
            st.metric("Feature Type", nearest_coast["feature_type"].replace("_", " ").title())
        with c3:
            feature_name = nearest_coast.get("name") or "Unnamed"
            st.metric("Feature Name", feature_name[:20])
        with c4:
            st.metric("Water Bodies Found", str(water_count))

        with st.expander("Distance interpretation", expanded=False):
            if coast_dist < 1:
                st.success("This location is **very close to the coast** (< 1 km). "
                           "Strong maritime influence expected.")
            elif coast_dist < 5:
                st.info("This location is **near the coast** (1-5 km). "
                        "Moderate maritime influence expected.")
            elif coast_dist < 25:
                st.warning("This location is **moderately inland** (5-25 km). "
                           "Some maritime influence may be present.")
            else:
                st.warning("This location is **far from the coast** (> 25 km). "
                           "Limited direct maritime influence.")
    else:
        st.warning(
            "No coastline or water body found within 100 km. "
            "This location appears to be deep inland."
        )
        coast_dist = None

    # ──────────────────────────────────────────────────────────────────
    # SECTION 2: Maritime Weather
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 2. Maritime Weather Conditions")

    marine_current = {}
    if marine_data:
        marine_current = marine_data.get("current", {})

    weather_current = {}
    if weather_data:
        weather_current = weather_data.get("current", {})

    wave_height = marine_current.get("wave_height")
    wave_dir = marine_current.get("wave_direction")
    wave_period = marine_current.get("wave_period")
    wind_wave_h = marine_current.get("wind_wave_height")

    temp = weather_current.get("temperature_2m")
    humidity = weather_current.get("relative_humidity_2m")
    wind_speed = weather_current.get("wind_speed_10m")
    wind_dir = weather_current.get("wind_direction_10m")

    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown("**Marine Conditions**")
        if wave_height is not None:
            fig_wave = _wave_gauge(wave_height, "Current Wave Height")
            st.plotly_chart(fig_wave, use_container_width=True, key="ocp_wave_gauge")
        else:
            st.info("Marine wave data not available for this location. "
                    "The point may be too far inland.")

        wm1, wm2 = st.columns(2)
        with wm1:
            st.metric("Wave Period", f"{wave_period:.1f} s" if wave_period is not None else "N/A")
            st.metric("Wave Direction", _deg_to_compass(wave_dir) if wave_dir is not None else "N/A")
        with wm2:
            st.metric("Wind Wave Height", f"{wind_wave_h:.2f} m" if wind_wave_h is not None else "N/A")
            # Daily max from marine API
            daily = marine_data.get("daily", {}) if marine_data else {}
            daily_max_waves = daily.get("wave_height_max", [])
            if daily_max_waves:
                max_wave = max(w for w in daily_max_waves if w is not None) if any(w is not None for w in daily_max_waves) else None
                st.metric("7-Day Max Wave", f"{max_wave:.2f} m" if max_wave is not None else "N/A")
            else:
                st.metric("7-Day Max Wave", "N/A")

    with mc2:
        st.markdown("**Local Weather**")
        wc1, wc2 = st.columns(2)
        with wc1:
            st.metric("Temperature", f"{temp:.1f} C" if temp is not None else "N/A")
            st.metric("Humidity", f"{humidity:.0f}%" if humidity is not None else "N/A")
        with wc2:
            st.metric("Wind Speed", f"{wind_speed:.1f} km/h" if wind_speed is not None else "N/A")
            st.metric("Wind Direction", _deg_to_compass(wind_dir) if wind_dir is not None else "N/A")

        if humidity is not None:
            humidity_gauge = _gauge_chart(
                humidity, "Relative Humidity (%)",
                max_val=100,
                color_ranges=[
                    {"range": [0, 40], "color": "#f59e0b"},
                    {"range": [40, 70], "color": "#10b981"},
                    {"range": [70, 100], "color": "#3b82f6"},
                ],
            )
            st.plotly_chart(humidity_gauge, use_container_width=True, key="ocp_humidity_gauge")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 3: Coastal Infrastructure
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 3. Coastal Infrastructure")

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.metric("Harbors", len(infra.get("harbors", [])))
        st.metric("Marinas", len(infra.get("marinas", [])))
    with ic2:
        st.metric("Piers", len(infra.get("piers", [])))
        st.metric("Lighthouses", len(infra.get("lighthouses", [])))
    with ic3:
        st.metric("Beaches", len(infra.get("beaches", [])))
        st.metric("Ferry Terminals", len(infra.get("ferry_terminals", [])))

    if infra_total > 0:
        # Infrastructure breakdown bar chart
        cat_names = []
        cat_counts = []
        cat_colors = []
        color_map = {
            "harbors": "#3b82f6",
            "marinas": "#1e40af",
            "piers": "#6b7280",
            "lighthouses": "#f59e0b",
            "beaches": "#f97316",
            "ferry_terminals": "#10b981",
        }
        for cat, items in infra.items():
            if items:
                cat_names.append(cat.replace("_", " ").title())
                cat_counts.append(len(items))
                cat_colors.append(color_map.get(cat, "#6b7280"))

        if cat_names:
            fig_bar = go.Figure(go.Bar(
                x=cat_names, y=cat_counts,
                marker_color=cat_colors,
                text=cat_counts, textposition="auto",
            ))
            fig_bar.update_layout(
                title="Coastal Infrastructure Breakdown",
                xaxis_title="Category", yaxis_title="Count",
                height=300, margin=dict(t=40, b=40, l=40, r=20),
            )
            st.plotly_chart(fig_bar, use_container_width=True, key="ocp_infra_bar")

        # Folium map
        if HAS_FOLIUM:
            infra_map = _build_infrastructure_map(lat, lon, infra)
            if infra_map is not None:
                st_folium(infra_map, width=700, height=450, key="ocp_infra_map")
        else:
            st.info("Install `folium` and `streamlit-folium` for an interactive infrastructure map.")

        # Details expander
        with st.expander("Infrastructure details", expanded=False):
            for cat, items in infra.items():
                if items:
                    st.markdown(f"**{cat.replace('_', ' ').title()}** ({len(items)})")
                    for item in items[:10]:
                        st.markdown(
                            f"- {item['name']} -- {item['distance_km']} km away"
                        )
    else:
        st.info(f"No coastal infrastructure found within {search_radius} km.")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 4: Elevation & Coastal Risk
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 4. Elevation & Coastal Risk Assessment")

    ec1, ec2 = st.columns(2)
    with ec1:
        if elevation is not None:
            st.metric("Elevation Above Sea Level", f"{elevation:.1f} m")
            elev_gauge = _gauge_chart(
                min(elevation, 500), "Elevation (m)",
                max_val=500,
                color_ranges=[
                    {"range": [0, 10], "color": "#ef4444"},
                    {"range": [10, 50], "color": "#f59e0b"},
                    {"range": [50, 200], "color": "#10b981"},
                    {"range": [200, 500], "color": "#3b82f6"},
                ],
            )
            st.plotly_chart(elev_gauge, use_container_width=True, key="ocp_elev_gauge")
        else:
            st.warning("Elevation data not available.")

    with ec2:
        risk_score, risk_label = _compute_flood_risk(elevation, coast_dist)
        if risk_score is not None:
            st.metric("Flood / Tsunami Risk", f"{risk_score}/100 ({risk_label})")
            risk_gauge = _gauge_chart(
                risk_score, "Coastal Flood Risk",
                max_val=100,
                color_ranges=[
                    {"range": [0, 20], "color": "#10b981"},
                    {"range": [20, 40], "color": "#84cc16"},
                    {"range": [40, 60], "color": "#f59e0b"},
                    {"range": [60, 80], "color": "#f97316"},
                    {"range": [80, 100], "color": "#ef4444"},
                ],
            )
            st.plotly_chart(risk_gauge, use_container_width=True, key="ocp_risk_gauge")
        else:
            st.info("Insufficient data to compute coastal risk.")

    with st.expander("Risk assessment details", expanded=False):
        st.markdown("**Methodology:**")
        st.markdown(
            "The flood/tsunami risk score combines two equally-weighted factors:\n"
            "- **Elevation factor** -- locations below 10 m are at high risk; above 100 m, risk is minimal.\n"
            "- **Distance factor** -- locations within 1 km of the coast face significant risk; "
            "beyond 50 km, coastal flooding is unlikely."
        )
        if elevation is not None and coast_dist is not None:
            st.markdown(f"- Elevation: **{elevation:.1f} m** above sea level")
            st.markdown(f"- Distance to coast: **{coast_dist:.1f} km**")
            if elevation <= 5 and coast_dist is not None and coast_dist < 5:
                st.error("This location is at significant risk from storm surges and tsunamis.")
            elif elevation <= 10:
                st.warning("Low-lying area. Consider flood mitigation measures.")
            else:
                st.success("Elevation provides reasonable protection from coastal flooding.")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 5: Marine Biodiversity Potential
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 5. Marine Biodiversity Potential")

    bio_score, zone = _compute_biodiversity_score(lat, coast_dist, water_count)

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        st.metric("Biodiversity Score", f"{bio_score}/100")
    with bc2:
        st.metric("Climate Zone", zone.title())
    with bc3:
        abs_lat = abs(lat)
        if abs_lat < 23.5:
            hemisphere_note = "Tropical belt"
        elif abs_lat < 35:
            hemisphere_note = "Subtropical zone"
        elif abs_lat < 55:
            hemisphere_note = "Temperate zone"
        elif abs_lat < 66.5:
            hemisphere_note = "Subpolar zone"
        else:
            hemisphere_note = "Polar zone"
        st.metric("Latitude Zone", hemisphere_note)

    bio_gauge = _gauge_chart(
        bio_score, "Marine Biodiversity Potential",
        max_val=100,
        color_ranges=[
            {"range": [0, 30], "color": "#ef4444"},
            {"range": [30, 50], "color": "#f59e0b"},
            {"range": [50, 70], "color": "#84cc16"},
            {"range": [70, 100], "color": "#10b981"},
        ],
    )
    st.plotly_chart(bio_gauge, use_container_width=True, key="ocp_bio_gauge")

    with st.expander("Biodiversity scoring details", expanded=False):
        st.markdown(
            "The biodiversity potential score is estimated from:\n"
            "- **Climate zone base score** -- tropical waters support the highest biodiversity; "
            "polar waters the least.\n"
            "- **Proximity bonus** -- closer to the coast means greater access to diverse "
            "coastal habitats (reefs, estuaries, tidal zones).\n"
            "- **Water features density** -- more nearby water features suggest a richer "
            "hydrological environment."
        )
        st.markdown(f"- Base score for {zone}: **{BIODIVERSITY_BASE.get(zone, 50)}**")
        st.markdown(f"- Nearby water features found: **{water_count}**")
        if coast_dist is not None:
            st.markdown(f"- Distance to nearest coast: **{coast_dist:.1f} km**")

        if zone == "tropical" and coast_dist is not None and coast_dist < 5:
            st.success("Tropical coastal zone -- high potential for coral reefs and diverse marine life.")
        elif zone in ("tropical", "subtropical"):
            st.info("Warm-water region with good biodiversity potential.")
        elif zone == "temperate":
            st.info("Temperate waters support moderate but resilient marine ecosystems.")
        else:
            st.info("Cold-water ecosystems with specialized but less diverse marine life.")

    # ──────────────────────────────────────────────────────────────────
    # SECTION 6: Ocean Influence Score
    # ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 6. Ocean Influence Score")

    total_score, dimensions = _compute_ocean_influence(
        coast_dist, elevation, marine_data, weather_data,
        infra_total, bio_score,
    )

    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.metric("Overall Ocean Influence", f"{total_score}/100")
        st.markdown("---")
        for dim_name, dim_val in dimensions.items():
            st.metric(dim_name, f"{dim_val}/100")

    with sc2:
        radar = _radar_chart(dimensions)
        st.plotly_chart(radar, use_container_width=True, key="ocp_radar_chart")

    # Interpretation
    with st.expander("Score interpretation", expanded=True):
        if total_score >= 75:
            st.success(
                f"**Strong ocean influence** (score: {total_score}/100). "
                "This location is heavily shaped by maritime conditions -- expect "
                "oceanic climate, salt air, and significant coastal dynamics."
            )
        elif total_score >= 50:
            st.info(
                f"**Moderate ocean influence** (score: {total_score}/100). "
                "The ocean plays a noticeable role in local climate and geography, "
                "but inland factors are also significant."
            )
        elif total_score >= 25:
            st.warning(
                f"**Low ocean influence** (score: {total_score}/100). "
                "This location experiences limited maritime effects. "
                "Continental climate patterns likely dominate."
            )
        else:
            st.warning(
                f"**Minimal ocean influence** (score: {total_score}/100). "
                "This location is essentially landlocked with negligible "
                "oceanic impact on local conditions."
            )

        st.markdown("**Dimension breakdown:**")
        st.markdown(
            "| Dimension | Score | Description |\n"
            "|-----------|-------|-------------|\n"
            f"| Proximity | {dimensions.get('Proximity', 0)} | How close to the coastline |\n"
            f"| Marine Weather | {dimensions.get('Marine Weather', 0)} | Wave/sea activity intensity |\n"
            f"| Maritime Climate | {dimensions.get('Maritime Climate', 0)} | Humidity and atmospheric moisture |\n"
            f"| Infrastructure | {dimensions.get('Infrastructure', 0)} | Density of coastal infrastructure |\n"
            f"| Sea-Level Exposure | {dimensions.get('Sea-Level Exposure', 0)} | Elevation-based exposure |\n"
            f"| Biodiversity | {dimensions.get('Biodiversity', 0)} | Marine life potential |"
        )

    # ── Summary footer ────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Data sources: Open Topo Data (elevation), OpenStreetMap via Overpass (coastal features), "
        "Open-Meteo (marine weather & forecasts). All APIs are free and require no API key."
    )
