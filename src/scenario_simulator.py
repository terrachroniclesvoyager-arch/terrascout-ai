# -*- coding: utf-8 -*-
"""
Scenario Simulator module for TerraScout AI.
Simulates disaster/environmental scenarios at a given location and projects
impacts using elevation, weather, soil, seismic, and infrastructure data.

Scenarios: Flood, Earthquake, Wildfire, Industrial Spill, Sea Level Rise.
"""

import html as html_module
import math
import json
import streamlit as st
import requests

try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
    from streamlit_folium import st_folium

    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OVERPASS_API = "https://overpass-api.de/api/interpreter"
USGS_EQ_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

SCENARIO_TYPES = [
    "Flood Scenario",
    "Earthquake Scenario",
    "Wildfire Scenario",
    "Industrial Spill Scenario",
    "Sea Level Rise Scenario",
]

SEVERITY_COLORS = [
    "#22c55e", "#4ade80", "#a3e635", "#facc15", "#fbbf24",
    "#f59e0b", "#f97316", "#ef4444", "#dc2626", "#b91c1c", "#7f1d1d",
]

SPILL_TYPES = ["Chemical", "Oil", "Radioactive"]

# ---------------------------------------------------------------------------
# Data-fetching helpers (all cached, all with timeout + try/except)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_elevation_point(lat: float, lon: float):
    """Fetch single-point elevation from Open Topo Data."""
    try:
        url = f"{OPEN_TOPO_API}?locations={lat},{lon}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if results:
            return results[0].get("elevation")
        return None
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat: float, lon: float, radius_km: float = 2.0,
                          grid_size: int = 7):
    """Fetch an NxN elevation grid centred on (lat, lon)."""
    try:
        half = radius_km / 111.0  # approximate degrees
        step = (2 * half) / (grid_size - 1)
        points = []
        coords = []
        for r in range(grid_size):
            for c in range(grid_size):
                plat = lat - half + r * step
                plon = lon - half + c * step
                points.append(f"{plat:.5f},{plon:.5f}")
                coords.append((plat, plon))
        # Open Topo Data accepts pipe-separated locations (max ~100)
        url = f"{OPEN_TOPO_API}?locations={'|'.join(points)}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        elevations = []
        for res in results:
            elevations.append(res.get("elevation") if res else None)
        return {
            "elevations": elevations,
            "coords": coords,
            "grid_size": grid_size,
            "center_elevation": elevations[len(elevations) // 2]
            if elevations else None,
        }
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float):
    """Fetch current weather from Open-Meteo."""
    try:
        url = (
            f"{OPEN_METEO_API}?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,"
            "wind_speed_10m,wind_direction_10m&timezone=auto"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data.get("current", {})
        return {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
        }
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_soil(lat: float, lon: float):
    """Fetch SoilGrids data with CORRECT layer parsing."""
    try:
        url = (
            f"{SOILGRIDS_API}?lon={lon}&lat={lat}"
            "&property=clay&property=sand&property=silt&property=soc"
            "&depth=0-5cm&value=mean"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soil = r.json()
        # --- MANDATORY SoilGrids v2.0 parsing ---
        raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
        layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
        _layer_map = {
            l.get("name", ""): l
            for l in layers
            if isinstance(l, dict) and l.get("name")
        }

        def _sv(name, div=10):
            p = _layer_map.get(name, {})
            depths = p.get("depths", []) if isinstance(p, dict) else []
            return (
                (depths[0].get("values", {}).get("mean") or 0) / div
                if depths
                else None
            )

        return {
            "clay": _sv("clay"),
            "sand": _sv("sand"),
            "silt": _sv("silt"),
            "soc": _sv("soc"),
        }
    except Exception:
        return None


@st.cache_data(ttl=900)
def _fetch_infrastructure(lat: float, lon: float, radius_m: int = 3000):
    """Fetch nearby infrastructure via Overpass API."""
    try:
        query = f"""
[out:json][timeout:15];
(
  node["building"](around:{radius_m},{lat},{lon});
  way["building"](around:{radius_m},{lat},{lon});
  node["amenity"](around:{radius_m},{lat},{lon});
  way["highway"](around:{radius_m},{lat},{lon});
  node["natural"="water"](around:{radius_m},{lat},{lon});
  way["natural"="water"](around:{radius_m},{lat},{lon});
  way["waterway"](around:{radius_m},{lat},{lon});
);
out center qt 200;
"""
        r = requests.get(OVERPASS_API, params={"data": query}, timeout=10)
        r.raise_for_status()
        data = r.json()
        elements = data.get("elements", [])
        buildings = []
        amenities = []
        highways = []
        water_features = []
        for el in elements:
            tags = el.get("tags", {})
            if tags.get("building"):
                buildings.append(el)
            elif tags.get("amenity"):
                amenities.append(el)
            elif tags.get("highway"):
                highways.append(el)
            elif tags.get("natural") == "water" or tags.get("waterway"):
                water_features.append(el)
        return {
            "buildings": buildings,
            "amenities": amenities,
            "highways": highways,
            "water_features": water_features,
            "total": len(elements),
        }
    except Exception:
        return {"buildings": [], "amenities": [], "highways": [],
                "water_features": [], "total": 0}


@st.cache_data(ttl=900)
def _fetch_earthquakes(lat: float, lon: float):
    """Fetch recent earthquakes from USGS within 100 km."""
    try:
        url = (
            f"{USGS_EQ_API}?format=geojson&latitude={lat}&longitude={lon}"
            "&maxradiuskm=100&minmagnitude=2&limit=20"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        features = data.get("features", [])
        quakes = []
        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])
            quakes.append({
                "mag": props.get("mag"),
                "place": props.get("place"),
                "time": props.get("time"),
                "lon": coords[0],
                "lat": coords[1],
                "depth": coords[2],
            })
        return quakes
    except Exception:
        return []


@st.cache_data(ttl=900)
def _fetch_coastline_distance(lat: float, lon: float):
    """Estimate distance to nearest coastline via Overpass."""
    try:
        query = f"""
[out:json][timeout:15];
way["natural"="coastline"](around:50000,{lat},{lon});
out geom qt 1;
"""
        r = requests.get(OVERPASS_API, params={"data": query}, timeout=10)
        r.raise_for_status()
        data = r.json()
        elements = data.get("elements", [])
        if not elements:
            return None
        min_dist = float("inf")
        for el in elements:
            geom = el.get("geometry", [])
            for pt in geom:
                d = _haversine(lat, lon, pt.get("lat", 0), pt.get("lon", 0))
                if d < min_dist:
                    min_dist = d
        return round(min_dist, 2) if min_dist < float("inf") else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _severity_color(score: float) -> str:
    """Return hex colour for severity 0-10."""
    idx = max(0, min(10, int(score)))
    return SEVERITY_COLORS[idx]


def _render_severity_gauge(score: float, label: str, chart_key: str):
    """Render a plotly gauge for impact severity."""
    if not HAS_PLOTLY:
        st.metric(label, f"{score:.1f} / 10")
        return
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": label},
        gauge={
            "axis": {"range": [0, 10]},
            "bar": {"color": _severity_color(score)},
            "steps": [
                {"range": [0, 3], "color": "#dcfce7"},
                {"range": [3, 6], "color": "#fef9c3"},
                {"range": [6, 8], "color": "#fed7aa"},
                {"range": [8, 10], "color": "#fecaca"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True, key=chart_key)


def _render_impact_metrics(metrics: dict):
    """Display a row of metric cards."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)


def _render_response_actions(actions: list):
    """Show recommended response actions as bullet list."""
    st.subheader("Recommended Response Actions")
    for a in actions:
        st.markdown(f"- {a}")


def _render_timeline(phases: list):
    """Render a simple timeline of event phases."""
    st.subheader("Estimated Timeline")
    for i, (phase, time_est) in enumerate(phases, 1):
        st.markdown(f"**Phase {i} -- {phase}:** {time_est}")


def _wind_dir_label(deg):
    """Convert wind direction degrees to compass label."""
    if deg is None:
        return "N"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int(((deg + 22.5) % 360) / 45)
    return dirs[idx]


def _wind_dx_dy(deg):
    """Return (dlat, dlon) unit offset in the wind direction."""
    if deg is None:
        deg = 0
    rad = math.radians(deg)
    return (math.cos(rad), math.sin(rad))


# ---------------------------------------------------------------------------
# Scenario 1 -- Flood
# ---------------------------------------------------------------------------

def _run_flood_scenario(lat, lon, flood_level_m):
    """Simulate a flood at the given location with a specified water level rise."""
    st.subheader(f"Flood Scenario -- {flood_level_m}m Water Rise")

    grid_data = _fetch_elevation_grid(lat, lon, radius_km=3.0, grid_size=7)
    infra = _fetch_infrastructure(lat, lon, radius_m=3000)
    soil = _fetch_soil(lat, lon)

    if grid_data is None or grid_data.get("center_elevation") is None:
        st.error("Could not retrieve elevation data for this location.")
        return

    center_elev = grid_data["center_elevation"]
    elevations = grid_data["elevations"]
    coords = grid_data["coords"]
    gs = grid_data["grid_size"]
    flood_line = center_elev + flood_level_m

    # Determine submerged cells
    submerged = []
    dry = []
    for i, elev in enumerate(elevations):
        if elev is not None and elev <= flood_line:
            submerged.append(i)
        else:
            dry.append(i)

    pct_submerged = (len(submerged) / len(elevations) * 100) if elevations else 0

    # Soil absorption factor
    clay_pct = (soil or {}).get("clay")
    soil_factor = 1.0
    soil_label = "Unknown"
    if clay_pct is not None:
        if clay_pct > 40:
            soil_factor = 1.3
            soil_label = "Clay-heavy (poor drainage)"
        elif clay_pct < 15:
            soil_factor = 0.7
            soil_label = "Sandy (good drainage)"
        else:
            soil_label = "Loamy (moderate drainage)"

    severity = min(10, (pct_submerged / 10) * soil_factor + flood_level_m * 0.5)

    infra_at_risk = int(infra.get("total", 0) * pct_submerged / 100)

    # Severity gauge
    _render_severity_gauge(severity, "Flood Impact Severity", "scn_flood_gauge")

    # Metrics
    _render_impact_metrics({
        "Submerged Area": f"{pct_submerged:.0f}%",
        "Flood Level": f"{flood_level_m}m",
        "Center Elevation": f"{center_elev:.0f}m",
        "Infrastructure at Risk": str(infra_at_risk),
        "Soil Type": soil_label,
    })

    # Elevation bar chart
    if HAS_PLOTLY and elevations:
        valid_elevs = [e for e in elevations if e is not None]
        if valid_elevs:
            fig = go.Figure()
            colors = [
                "#3b82f6" if (e is not None and e <= flood_line) else "#22c55e"
                for e in elevations
            ]
            fig.add_trace(go.Bar(
                x=list(range(len(elevations))),
                y=[e if e is not None else 0 for e in elevations],
                marker_color=colors,
                name="Elevation",
            ))
            fig.add_hline(y=flood_line, line_dash="dash", line_color="red",
                          annotation_text=f"Flood line ({flood_line:.0f}m)")
            fig.update_layout(
                title="Elevation Grid vs Flood Line",
                xaxis_title="Grid Cell",
                yaxis_title="Elevation (m)",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True, key="scn_flood_elev_chart")

    # Folium map
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=13)
        for i, (clat, clon) in enumerate(coords):
            elev = elevations[i] if i < len(elevations) else None
            if elev is not None and elev <= flood_line:
                folium.CircleMarker(
                    location=[clat, clon],
                    radius=14,
                    color="#2563eb",
                    fill=True,
                    fill_color="#3b82f6",
                    fill_opacity=0.55,
                    popup=f"Submerged: {elev:.0f}m (flood line {flood_line:.0f}m)",
                ).add_to(m)
            elif elev is not None:
                folium.CircleMarker(
                    location=[clat, clon],
                    radius=8,
                    color="#16a34a",
                    fill=True,
                    fill_color="#22c55e",
                    fill_opacity=0.4,
                    popup=f"Dry: {elev:.0f}m",
                ).add_to(m)
        folium.Marker([lat, lon], popup="Analysis Center",
                      icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=700, height=450, key="scn_flood_map")
    else:
        st.info("Install folium and streamlit-folium for interactive maps.")

    # Response actions
    _render_response_actions([
        "Issue evacuation orders for low-lying areas within the flood zone.",
        "Deploy sandbag barriers along the flood perimeter.",
        "Activate emergency shelters on higher ground.",
        "Coordinate with utility companies to shut off power in submerged areas.",
        f"Prioritize rescue operations -- estimated {infra_at_risk} structures affected.",
        "Establish clean water distribution points (contamination risk).",
    ])

    _render_timeline([
        ("Initial Warning", "0 - 2 hours"),
        ("Evacuation", "2 - 8 hours"),
        ("Peak Flooding", f"8 - 24 hours at {flood_level_m}m rise"),
        ("Water Recession", "1 - 5 days depending on drainage"),
        ("Recovery & Assessment", "1 - 4 weeks"),
    ])


# ---------------------------------------------------------------------------
# Scenario 2 -- Earthquake
# ---------------------------------------------------------------------------

def _pga_attenuation(magnitude, distance_km):
    """Simplified PGA estimate (fraction of g) using Joyner-Boore style."""
    if distance_km < 1:
        distance_km = 1
    log_pga = (0.49 * magnitude
               - 1.64 * math.log10(distance_km)
               - 0.0028 * distance_km
               - 1.27)
    return 10 ** log_pga


def _run_earthquake_scenario(lat, lon, magnitude):
    """Simulate an earthquake centred at (lat, lon)."""
    st.subheader(f"Earthquake Scenario -- M{magnitude}")

    soil = _fetch_soil(lat, lon)
    infra = _fetch_infrastructure(lat, lon, radius_m=5000)
    hist_quakes = _fetch_earthquakes(lat, lon)
    elev_data = _fetch_elevation_grid(lat, lon, radius_km=5.0, grid_size=5)

    # PGA at epicentre
    pga_center = _pga_attenuation(magnitude, 1)

    # Soil amplification
    clay_pct = (soil or {}).get("clay")
    soil_amp = 1.0
    soil_desc = "Unknown"
    if clay_pct is not None:
        if clay_pct > 45:
            soil_amp = 1.6
            soil_desc = "Soft clay (high amplification)"
        elif clay_pct > 25:
            soil_amp = 1.3
            soil_desc = "Medium soil (moderate amplification)"
        elif clay_pct < 15:
            soil_amp = 0.9
            soil_desc = "Rock/sand (low amplification)"
        else:
            soil_amp = 1.1
            soil_desc = "Mixed soil"

    adjusted_pga = pga_center * soil_amp
    severity = min(10, adjusted_pga * 12 + (magnitude - 4) * 1.2)

    # Intensity zones (distances in km)
    zones = [
        ("Extreme (IX+)", 5, "#b91c1c"),
        ("Severe (VII-VIII)", 15, "#ef4444"),
        ("Strong (V-VI)", 40, "#f97316"),
        ("Moderate (III-IV)", 80, "#facc15"),
        ("Light (I-II)", 150, "#22c55e"),
    ]

    # Damage estimate
    bld_count = len(infra.get("buildings", []))
    damage_pct = min(95, adjusted_pga * 100 * 1.5)
    damaged_est = int(bld_count * damage_pct / 100)

    _render_severity_gauge(severity, "Earthquake Impact Severity",
                           "scn_eq_gauge")

    _render_impact_metrics({
        "Magnitude": f"M{magnitude}",
        "PGA (center)": f"{adjusted_pga:.2f}g",
        "Soil Type": soil_desc,
        "Buildings Nearby": str(bld_count),
        "Est. Damaged": str(damaged_est),
    })

    # Intensity zones map
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=9)
        for label, radius_km, color in reversed(zones):
            pga_at_r = _pga_attenuation(magnitude, radius_km) * soil_amp
            folium.Circle(
                location=[lat, lon],
                radius=radius_km * 1000,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.15,
                popup=f"{label} -- PGA {pga_at_r:.3f}g",
            ).add_to(m)
        folium.Marker([lat, lon], popup=f"Epicentre M{magnitude}",
                      icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)
        # Historical quakes
        for q in hist_quakes[:10]:
            if q.get("lat") and q.get("lon"):
                folium.CircleMarker(
                    location=[q["lat"], q["lon"]],
                    radius=max(3, (q.get("mag") or 2) * 2),
                    color="#8b5cf6",
                    fill=True,
                    fill_opacity=0.5,
                    popup=f"M{q.get('mag')} -- {html_module.escape(q.get('place', 'Unknown'))}",
                ).add_to(m)
        st_folium(m, width=700, height=450, key="scn_eq_map")
    else:
        st.info("Install folium and streamlit-folium for interactive maps.")

    # PGA attenuation chart
    if HAS_PLOTLY:
        distances = list(range(1, 151))
        pga_vals = [_pga_attenuation(magnitude, d) * soil_amp for d in distances]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=distances, y=pga_vals,
            mode="lines", fill="tozeroy",
            line=dict(color="#ef4444"),
            name="PGA",
        ))
        fig.add_hline(y=0.2, line_dash="dash", line_color="orange",
                      annotation_text="Structural damage threshold (0.2g)")
        fig.update_layout(
            title=f"PGA Attenuation -- M{magnitude} (soil factor {soil_amp:.1f}x)",
            xaxis_title="Distance from Epicentre (km)",
            yaxis_title="PGA (g)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True, key="scn_eq_pga_chart")

    # Historical seismicity context
    if hist_quakes:
        st.subheader("Historical Seismicity (within 100 km)")
        for q in hist_quakes[:8]:
            st.markdown(
                f"- **M{q.get('mag', '?')}** -- {html_module.escape(q.get('place', 'Unknown'))} "
                f"(depth {q.get('depth', '?')} km)"
            )
    else:
        st.info("No recent earthquakes recorded within 100 km.")

    _render_response_actions([
        "Activate seismic emergency protocols immediately.",
        "Deploy search-and-rescue teams to highest PGA zones.",
        "Inspect bridges, hospitals, and schools for structural integrity.",
        f"Estimated {damaged_est} buildings may sustain damage -- prioritise triage.",
        "Issue tsunami advisory if near coastline.",
        "Establish field hospitals outside the severe zone (> 15 km from epicentre).",
        "Monitor aftershock sequence -- expect M" + f"{magnitude - 1.2:.1f}+ aftershocks.",
    ])

    _render_timeline([
        ("Main Shock", "T+0 seconds"),
        ("Initial Aftershocks", "T+0 to 1 hour"),
        ("Emergency Response", "T+1 to 6 hours"),
        ("Search & Rescue", "T+6 to 72 hours"),
        ("Aftershock Sequence", "Days to weeks"),
        ("Reconstruction", "Months to years"),
    ])


# ---------------------------------------------------------------------------
# Scenario 3 -- Wildfire
# ---------------------------------------------------------------------------

def _run_wildfire_scenario(lat, lon):
    """Simulate wildfire spread risk based on weather, terrain, and vegetation."""
    st.subheader("Wildfire Scenario -- Spread Risk Analysis")

    weather = _fetch_weather(lat, lon)
    grid_data = _fetch_elevation_grid(lat, lon, radius_km=3.0, grid_size=7)
    soil = _fetch_soil(lat, lon)
    infra = _fetch_infrastructure(lat, lon, radius_m=3000)

    # Extract weather parameters
    temp = (weather or {}).get("temperature", 25)
    humidity = (weather or {}).get("humidity", 50)
    wind_spd = (weather or {}).get("wind_speed", 10)
    wind_dir = (weather or {}).get("wind_direction", 0)

    # Compute fire weather index components
    temp_factor = max(0, (temp - 15) / 25)  # 0 at 15C, 1 at 40C
    humidity_factor = max(0, (60 - humidity) / 60)  # drier = higher
    wind_factor = min(1, wind_spd / 50)
    fire_weather_idx = (temp_factor * 0.3 + humidity_factor * 0.35
                        + wind_factor * 0.35)

    # Slope factor from elevation grid
    slope_factor = 0.5
    center_elev = None
    if grid_data and grid_data.get("elevations"):
        elevs = grid_data["elevations"]
        center_elev = grid_data.get("center_elevation")
        valid = [e for e in elevs if e is not None]
        if valid and len(valid) > 1:
            elev_range = max(valid) - min(valid)
            slope_factor = min(1, elev_range / 200)

    # Vegetation proxy from SOC
    soc = (soil or {}).get("soc")
    veg_factor = 0.5
    veg_label = "Moderate"
    if soc is not None:
        if soc > 30:
            veg_factor = 0.9
            veg_label = "Dense (high fuel load)"
        elif soc > 15:
            veg_factor = 0.6
            veg_label = "Moderate"
        else:
            veg_factor = 0.3
            veg_label = "Sparse (low fuel)"

    overall_risk = (fire_weather_idx * 0.45 + slope_factor * 0.25
                    + veg_factor * 0.30)
    severity = min(10, overall_risk * 10)

    # Directional spread: fire moves fastest downwind and uphill
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    dir_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    spread_rates = []
    for angle in dir_angles:
        # Wind alignment: how much this direction aligns with wind
        diff = abs(angle - (wind_dir or 0))
        if diff > 180:
            diff = 360 - diff
        wind_align = max(0, 1 - diff / 180)
        rate = (0.4 + wind_align * 0.6) * (0.5 + fire_weather_idx * 0.5)
        spread_rates.append(round(rate, 2))

    evac_urgency = min(10, severity * 1.1 + wind_factor * 2)
    wind_label = _wind_dir_label(wind_dir)

    _render_severity_gauge(severity, "Wildfire Risk Severity", "scn_fire_gauge")

    _render_impact_metrics({
        "Temperature": f"{temp:.0f} C",
        "Humidity": f"{humidity:.0f}%",
        "Wind": f"{wind_spd:.0f} km/h {wind_label}",
        "Vegetation": veg_label,
        "Evacuation Urgency": f"{evac_urgency:.1f}/10",
    })

    # Directional spread radar chart
    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=spread_rates + [spread_rates[0]],
            theta=directions + [directions[0]],
            fill="toself",
            fillcolor="rgba(239, 68, 68, 0.25)",
            line=dict(color="#ef4444"),
            name="Fire Spread Rate",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(range=[0, 1.2])),
            title=f"Directional Fire Spread Risk (wind from {wind_label})",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True, key="scn_fire_radar")

    # Map with directional spread
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], popup="Fire Origin",
                      icon=folium.Icon(color="red", icon="fire")).add_to(m)
        # Show spread arrows
        for i, direction in enumerate(directions):
            angle_rad = math.radians(dir_angles[i])
            rate = spread_rates[i]
            offset_km = rate * 2  # scale for visual
            dlat = offset_km / 111.0 * math.cos(angle_rad)
            dlon = offset_km / (111.0 * math.cos(math.radians(lat))) * math.sin(angle_rad)
            end_lat = lat + dlat
            end_lon = lon + dlon
            color = "#b91c1c" if rate > 0.7 else ("#f97316" if rate > 0.4 else "#22c55e")
            folium.PolyLine(
                locations=[[lat, lon], [end_lat, end_lon]],
                color=color,
                weight=max(2, int(rate * 6)),
                popup=f"{direction}: spread rate {rate:.2f}",
            ).add_to(m)
            folium.CircleMarker(
                location=[end_lat, end_lon],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.7,
            ).add_to(m)
        st_folium(m, width=700, height=450, key="scn_fire_map")
    else:
        st.info("Install folium and streamlit-folium for interactive maps.")

    # Fire weather breakdown chart
    if HAS_PLOTLY:
        fig = go.Figure(go.Bar(
            x=["Temperature", "Humidity", "Wind", "Slope", "Vegetation"],
            y=[temp_factor, humidity_factor, wind_factor, slope_factor, veg_factor],
            marker_color=["#ef4444", "#3b82f6", "#8b5cf6", "#f59e0b", "#22c55e"],
        ))
        fig.update_layout(
            title="Fire Risk Component Breakdown",
            yaxis_title="Risk Factor (0-1)",
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True, key="scn_fire_breakdown")

    _render_response_actions([
        f"Highest spread risk toward {directions[spread_rates.index(max(spread_rates))]} "
        f"-- prioritise evacuation in that direction.",
        "Establish firebreaks perpendicular to dominant wind direction.",
        "Pre-position aerial firefighting assets.",
        "Evacuate residents within 3 km of the fire origin.",
        "Activate air quality monitoring for PM2.5 and PM10.",
        "Set up triage/medical stations upwind of the fire.",
        "Coordinate road closures on highways in the spread path.",
    ])

    _render_timeline([
        ("Ignition & Initial Spread", "0 - 30 minutes"),
        ("Rapid Expansion", "30 min - 2 hours"),
        ("Peak Intensity", "2 - 8 hours"),
        ("Containment Efforts", "8 - 48 hours"),
        ("Full Containment", f"2 - 7 days (wind {wind_spd:.0f} km/h)"),
        ("Mop-up & Rehabilitation", "1 - 6 months"),
    ])


# ---------------------------------------------------------------------------
# Scenario 4 -- Industrial Spill
# ---------------------------------------------------------------------------

def _run_spill_scenario(lat, lon, spill_type):
    """Simulate contamination spread from an industrial spill."""
    st.subheader(f"Industrial Spill Scenario -- {spill_type}")

    weather = _fetch_weather(lat, lon)
    grid_data = _fetch_elevation_grid(lat, lon, radius_km=2.0, grid_size=7)
    soil = _fetch_soil(lat, lon)
    infra = _fetch_infrastructure(lat, lon, radius_m=5000)

    wind_spd = (weather or {}).get("wind_speed", 10)
    wind_dir = (weather or {}).get("wind_direction", 0)
    temp = (weather or {}).get("temperature", 20)

    # Spill characteristics
    spill_cfg = {
        "Chemical": {
            "base_radius_km": 2.0, "volatility": 0.7, "persistence": 0.5,
            "color": "#facc15", "water_factor": 1.5,
            "health_risk": "Acute respiratory irritation, skin burns, eye damage",
        },
        "Oil": {
            "base_radius_km": 1.5, "volatility": 0.3, "persistence": 0.9,
            "color": "#1e293b", "water_factor": 2.5,
            "health_risk": "Groundwater contamination, long-term carcinogenic risk",
        },
        "Radioactive": {
            "base_radius_km": 5.0, "volatility": 0.5, "persistence": 0.95,
            "color": "#a855f7", "water_factor": 1.2,
            "health_risk": "Radiation sickness, long-term cancer risk, genetic damage",
        },
    }
    cfg = spill_cfg.get(spill_type, spill_cfg["Chemical"])

    # Wind-driven plume
    wind_extend = cfg["base_radius_km"] * (1 + cfg["volatility"] * wind_spd / 30)

    # Terrain slope effect
    slope_extend = 1.0
    if grid_data and grid_data.get("elevations"):
        elevs = [e for e in grid_data["elevations"] if e is not None]
        if elevs:
            slope_extend = 1 + (max(elevs) - min(elevs)) / 300

    affected_radius = wind_extend * slope_extend

    # Water contamination risk
    water_count = len(infra.get("water_features", []))
    water_risk = min(10, water_count * cfg["water_factor"])

    # Soil absorption
    sand_pct = (soil or {}).get("sand")
    soil_absorption = "Moderate"
    if sand_pct is not None:
        if sand_pct > 50:
            soil_absorption = "High (sandy -- rapid groundwater contamination)"
        elif sand_pct < 20:
            soil_absorption = "Low (clay -- surface pooling)"

    # Population impact (rough estimate from building count)
    bld_count = len(infra.get("buildings", []))
    est_pop = bld_count * 3  # rough occupancy
    amenity_count = len(infra.get("amenities", []))

    severity = min(10, (affected_radius / 3) * 2
                   + water_risk * 0.3
                   + cfg["persistence"] * 3)

    _render_severity_gauge(severity, f"{spill_type} Spill Severity",
                           "scn_spill_gauge")

    _render_impact_metrics({
        "Spill Type": spill_type,
        "Affected Radius": f"{affected_radius:.1f} km",
        "Water Features at Risk": str(water_count),
        "Est. Population": str(est_pop),
        "Soil Absorption": soil_absorption,
    })

    # Contamination plume on map
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=12)
        # General affected zone
        folium.Circle(
            location=[lat, lon],
            radius=int(affected_radius * 1000),
            color=cfg["color"],
            fill=True,
            fill_color=cfg["color"],
            fill_opacity=0.2,
            popup=f"Contamination Zone ({affected_radius:.1f} km)",
        ).add_to(m)
        # Wind-driven plume (elongated in wind direction)
        wind_rad = math.radians(wind_dir or 0)
        plume_len = affected_radius * 1.5
        dlat = plume_len / 111.0 * math.cos(wind_rad)
        dlon = plume_len / (111.0 * math.cos(math.radians(lat))) * math.sin(wind_rad)
        plume_end = [lat + dlat, lon + dlon]
        folium.PolyLine(
            locations=[[lat, lon], plume_end],
            color=cfg["color"],
            weight=4,
            dash_array="10",
            popup=f"Wind-driven plume ({_wind_dir_label(wind_dir)})",
        ).add_to(m)
        # Plume spread cone
        for offset_deg in [-25, 25]:
            cone_rad = math.radians((wind_dir or 0) + offset_deg)
            cdlat = plume_len / 111.0 * math.cos(cone_rad)
            cdlon = plume_len / (111.0 * math.cos(math.radians(lat))) * math.sin(cone_rad)
            folium.PolyLine(
                locations=[[lat, lon], [lat + cdlat, lon + cdlon]],
                color=cfg["color"],
                weight=2,
                opacity=0.5,
            ).add_to(m)
        # Exclusion zones
        folium.Circle(
            location=[lat, lon],
            radius=500,
            color="#dc2626",
            fill=True,
            fill_color="#dc2626",
            fill_opacity=0.35,
            popup="Immediate Danger Zone (500m)",
        ).add_to(m)
        folium.Marker([lat, lon], popup="Spill Origin",
                      icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=700, height=450, key="scn_spill_map")
    else:
        st.info("Install folium and streamlit-folium for interactive maps.")

    # Contamination decay chart
    if HAS_PLOTLY:
        hours = list(range(0, 169))
        decay_rate = 1 - cfg["persistence"]
        concentrations = [100 * math.exp(-decay_rate * h / 24) for h in hours]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours, y=concentrations,
            mode="lines", fill="tozeroy",
            line=dict(color=cfg["color"]),
            name="Concentration",
        ))
        fig.add_hline(y=10, line_dash="dash", line_color="green",
                      annotation_text="Safe threshold")
        fig.update_layout(
            title="Estimated Contamination Decay Over Time",
            xaxis_title="Hours After Spill",
            yaxis_title="Concentration (%)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True, key="scn_spill_decay_chart")

    # Health risk info
    st.subheader("Health Risk Assessment")
    st.warning(f"**Primary health risk:** {cfg['health_risk']}")
    st.markdown(
        f"- **Immediate zone (< 500m):** Evacuate immediately, full HAZMAT gear required.\n"
        f"- **Inner zone (< {affected_radius / 2:.1f} km):** Shelter-in-place, close windows.\n"
        f"- **Outer zone (< {affected_radius:.1f} km):** Monitor air quality, be ready to evacuate."
    )

    _render_response_actions([
        "Establish 500m immediate exclusion perimeter.",
        f"Evacuate population within {affected_radius:.1f} km downwind.",
        "Deploy HAZMAT teams with appropriate PPE.",
        f"Protect {water_count} water features from contamination runoff.",
        f"Notify {amenity_count} public amenities (schools, hospitals, etc.).",
        "Set up air quality monitoring stations downwind.",
        "Activate emergency medical services for exposure treatment.",
        f"Soil remediation required -- {soil_absorption.lower()} absorption rate.",
    ])

    _render_timeline([
        ("Immediate Response", "0 - 1 hour"),
        ("Evacuation", "1 - 4 hours"),
        ("Containment", "4 - 24 hours"),
        ("Active Remediation", "1 - 14 days"),
        ("Monitoring Phase", "2 weeks - 6 months"),
        ("Full Decontamination", f"{'6-24 months' if cfg['persistence'] > 0.8 else '1-6 months'}"),
    ])


# ---------------------------------------------------------------------------
# Scenario 5 -- Sea Level Rise
# ---------------------------------------------------------------------------

def _run_sea_level_scenario(lat, lon, rise_m):
    """Simulate sea level rise impacts."""
    st.subheader(f"Sea Level Rise Scenario -- +{rise_m}m")

    grid_data = _fetch_elevation_grid(lat, lon, radius_km=5.0, grid_size=9)
    coast_dist = _fetch_coastline_distance(lat, lon)
    infra = _fetch_infrastructure(lat, lon, radius_m=5000)
    center_elev = _fetch_elevation_point(lat, lon)

    if grid_data is None:
        st.error("Could not retrieve elevation data for this location.")
        return

    elevations = grid_data.get("elevations", [])
    coords = grid_data.get("coords", [])
    gs = grid_data.get("grid_size", 9)

    # Determine which cells would be below new sea level
    # Sea level = 0 + rise_m  (cells below this are submerged)
    new_sea = rise_m
    submerged_indices = []
    above_indices = []
    for i, elev in enumerate(elevations):
        if elev is not None and elev <= new_sea:
            submerged_indices.append(i)
        else:
            above_indices.append(i)

    total_valid = sum(1 for e in elevations if e is not None)
    pct_submerged = (len(submerged_indices) / total_valid * 100) if total_valid else 0

    # Infrastructure impact
    infra_total = infra.get("total", 0)
    infra_at_risk = int(infra_total * pct_submerged / 100)

    # Severity calculation
    coast_factor = 1.0
    coast_label = "Unknown"
    if coast_dist is not None:
        if coast_dist < 5:
            coast_factor = 2.0
            coast_label = f"{coast_dist:.1f} km (very close)"
        elif coast_dist < 20:
            coast_factor = 1.3
            coast_label = f"{coast_dist:.1f} km (moderate)"
        else:
            coast_factor = 0.5
            coast_label = f"{coast_dist:.1f} km (inland)"
    else:
        coast_label = "Could not determine"

    severity = min(10, (pct_submerged / 15) * coast_factor + rise_m * 0.8)

    _render_severity_gauge(severity, "Sea Level Rise Impact", "scn_slr_gauge")

    _render_impact_metrics({
        "Sea Level Rise": f"+{rise_m}m",
        "Center Elevation": f"{center_elev:.0f}m" if center_elev is not None else "N/A",
        "Coast Distance": coast_label,
        "Area Submerged": f"{pct_submerged:.0f}%",
        "Infrastructure at Risk": str(infra_at_risk),
    })

    # Elevation profile vs new sea level
    if HAS_PLOTLY and elevations:
        valid_elevs = [e for e in elevations if e is not None]
        if valid_elevs:
            fig = go.Figure()
            colors = [
                "#2563eb" if (e is not None and e <= new_sea) else "#22c55e"
                for e in elevations
            ]
            fig.add_trace(go.Bar(
                x=list(range(len(elevations))),
                y=[e if e is not None else 0 for e in elevations],
                marker_color=colors,
                name="Elevation",
            ))
            fig.add_hline(y=0, line_dash="solid", line_color="blue",
                          annotation_text="Current sea level")
            fig.add_hline(y=new_sea, line_dash="dash", line_color="red",
                          annotation_text=f"New sea level (+{rise_m}m)")
            fig.update_layout(
                title="Elevation Grid vs New Sea Level",
                xaxis_title="Grid Cell",
                yaxis_title="Elevation (m)",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True, key="scn_slr_elev_chart")

    # Folium map
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        for i, (clat, clon) in enumerate(coords):
            elev = elevations[i] if i < len(elevations) else None
            if elev is not None and elev <= new_sea:
                folium.CircleMarker(
                    location=[clat, clon],
                    radius=12,
                    color="#1d4ed8",
                    fill=True,
                    fill_color="#3b82f6",
                    fill_opacity=0.6,
                    popup=f"Submerged: {elev:.1f}m (sea +{rise_m}m)",
                ).add_to(m)
            elif elev is not None:
                folium.CircleMarker(
                    location=[clat, clon],
                    radius=6,
                    color="#16a34a",
                    fill=True,
                    fill_color="#22c55e",
                    fill_opacity=0.3,
                    popup=f"Above sea level: {elev:.1f}m",
                ).add_to(m)
        folium.Marker([lat, lon], popup="Analysis Center",
                      icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, width=700, height=450, key="scn_slr_map")
    else:
        st.info("Install folium and streamlit-folium for interactive maps.")

    # Sea level rise progression chart
    if HAS_PLOTLY:
        levels = [0.25, 0.5, 1, 2, 3, 5, 7, 10]
        submerged_pcts = []
        for lvl in levels:
            cnt = sum(1 for e in elevations if e is not None and e <= lvl)
            submerged_pcts.append(cnt / total_valid * 100 if total_valid else 0)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=levels, y=submerged_pcts,
            mode="lines+markers",
            line=dict(color="#2563eb"),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.15)",
            name="% Submerged",
        ))
        fig.add_vline(x=rise_m, line_dash="dash", line_color="red",
                      annotation_text=f"Selected: +{rise_m}m")
        fig.update_layout(
            title="Area Submerged vs Sea Level Rise",
            xaxis_title="Sea Level Rise (m)",
            yaxis_title="Area Submerged (%)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True, key="scn_slr_prog_chart")

    _render_response_actions([
        "Develop long-term coastal retreat and relocation plans.",
        f"Protect or relocate {infra_at_risk} at-risk structures.",
        "Construct sea walls and tidal barriers in critical areas.",
        "Upgrade stormwater drainage systems for higher water tables.",
        "Establish saltwater intrusion monitoring for freshwater sources.",
        "Plan managed retreat corridors to higher ground.",
        "Update building codes for flood-resilient construction.",
        "Create ecosystem-based adaptation (mangrove restoration, dune rebuilding).",
    ])

    _render_timeline([
        ("+0.5m rise", "2050-2070 (current trajectory)"),
        ("+1.0m rise", "2070-2100"),
        ("+2.0m rise", "2100-2150 (high-emission scenario)"),
        ("+5.0m rise", "2150+ (worst-case ice sheet collapse)"),
        ("Adaptation planning", "Must begin immediately"),
        ("Infrastructure relocation", "10-30 year planning horizon"),
    ])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_scenario_simulator_tab():
    """Main entry point for the Scenario Simulator module."""
    st.title("Scenario Simulator")
    st.markdown(
        "Simulate disaster and environmental scenarios at any location. "
        "Select a scenario type, configure parameters, and analyse projected impacts."
    )

    # --- Location input ---
    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        lat = st.number_input("Latitude", value=41.9028, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="scn_lat")
    with col_loc2:
        lon = st.number_input("Longitude", value=12.4964, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="scn_lon")

    # --- Scenario selector ---
    scenario = st.selectbox("Select Scenario", SCENARIO_TYPES, key="scn_type")

    # --- Scenario-specific parameters ---
    if scenario == "Flood Scenario":
        flood_level = st.selectbox(
            "Flood Water Level Rise",
            [1, 3, 5, 10],
            format_func=lambda x: f"{x} metres",
            key="scn_flood_level",
        )
    elif scenario == "Earthquake Scenario":
        magnitude = st.selectbox(
            "Earthquake Magnitude",
            [5.0, 6.0, 7.0, 8.0],
            format_func=lambda x: f"M{x}",
            key="scn_eq_mag",
        )
    elif scenario == "Industrial Spill Scenario":
        spill_type = st.selectbox(
            "Spill Type",
            SPILL_TYPES,
            key="scn_spill_type",
        )
    elif scenario == "Sea Level Rise Scenario":
        slr_level = st.selectbox(
            "Sea Level Rise",
            [0.5, 1.0, 2.0, 5.0],
            format_func=lambda x: f"+{x}m",
            key="scn_slr_level",
        )

    # --- Run button ---
    if st.button("Run Simulation", type="primary", key="scn_run"):
        if lat is None or lon is None:
            st.error("Please enter valid coordinates.")
            return

        with st.spinner("Fetching data and running simulation..."):
            st.divider()
            if scenario == "Flood Scenario":
                _run_flood_scenario(lat, lon, flood_level)
            elif scenario == "Earthquake Scenario":
                _run_earthquake_scenario(lat, lon, magnitude)
            elif scenario == "Wildfire Scenario":
                _run_wildfire_scenario(lat, lon)
            elif scenario == "Industrial Spill Scenario":
                _run_spill_scenario(lat, lon, spill_type)
            elif scenario == "Sea Level Rise Scenario":
                _run_sea_level_scenario(lat, lon, slr_level)
