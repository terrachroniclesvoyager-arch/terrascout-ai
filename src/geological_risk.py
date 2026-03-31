"""
Geological Risk & Ground Stability module for TerraScout AI.
Deep geological analysis of ground conditions and geohazards across
seven dimensions: seismic activity, slope stability, soil composition,
bedrock geology, karst/sinkhole risk, volcanic proximity, and ground
moisture.  All data fetched from free APIs (no keys required).
"""

import math
import logging
from datetime import datetime

import html as html_module
import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_C = {
    "bg": "#1a1a2e", "card": "rgba(26,26,46,0.85)", "border": "#3d2e1a",
    "text": "#e8ecf4", "muted": "#8b97b0",
    "stable": "#22c55e", "moderate": "#f59e0b",
    "unstable": "#f97316", "hazardous": "#ef4444",
}

_DIM_META = {
    "Seismic Activity":   "#ef4444", "Slope Stability":    "#f97316",
    "Soil Composition":   "#92400e", "Bedrock Geology":    "#6366f1",
    "Karst & Sinkhole":   "#8b5cf6", "Volcanic Proximity": "#dc2626",
    "Ground Moisture":    "#3b82f6",
}

_VERDICT_MAP = [
    (8.0, "STABLE", "#22c55e"), (5.0, "MODERATE", "#f59e0b"),
    (3.0, "UNSTABLE", "#f97316"), (0.0, "HAZARDOUS", "#ef4444"),
]

# Well-known active volcanoes (lat, lon, name)
_VOLCANO_DB = [
    (37.751, 14.993, "Mount Etna"), (40.821, 14.426, "Mount Vesuvius"),
    (40.827, 14.139, "Campi Flegrei"), (38.789, 15.213, "Stromboli"),
    (38.404, 14.962, "Vulcano"), (36.404, 25.396, "Santorini"),
    (63.630, -19.613, "Eyjafjallajokull"), (64.416, -17.316, "Bardarbunga"),
    (65.030, -16.650, "Askja"), (64.640, -17.530, "Grimsvotn"),
    (46.206, -122.188, "Mount St. Helens"), (46.853, -121.760, "Mount Rainier"),
    (44.428, -110.588, "Yellowstone"), (19.421, -155.287, "Kilauea"),
    (19.475, -155.608, "Mauna Loa"), (-8.343, 115.508, "Mount Agung"),
    (-7.541, 110.446, "Mount Merapi"), (-6.102, 105.423, "Krakatoa"),
    (35.363, 138.731, "Mount Fuji"), (31.593, 130.657, "Sakurajima"),
    (-1.467, 29.225, "Nyiragongo"), (-15.379, -71.857, "Ubinas"),
    (0.340, -78.436, "Cotopaxi"), (14.473, -90.880, "Fuego"),
    (19.023, -97.268, "Popocatepetl"), (-38.692, -71.730, "Villarrica"),
    (56.056, 160.644, "Klyuchevskoy"), (-41.281, 175.564, "Ruapehu"),
    (15.130, 120.350, "Mount Pinatubo"), (-2.580, 29.450, "Nyamuragira"),
]

# ---------------------------------------------------------------------------
# Haversine
# ---------------------------------------------------------------------------
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ---------------------------------------------------------------------------
# Cached API fetchers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_earthquakes(lat: float, lon: float):
    """Fetch recent earthquakes within 200 km from USGS."""
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        f"?format=geojson&latitude={lat}&longitude={lon}"
        "&maxradiuskm=200&limit=50"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quakes = []
        for f in data.get("features", []):
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [0, 0, 0])
            qlat = coords[1] if len(coords) > 1 else lat
            qlon = coords[0] if len(coords) > 0 else lon
            quakes.append({
                "mag": props.get("mag") or 0,
                "place": props.get("place", "Unknown"),
                "time": props.get("time", 0),
                "lon": qlon, "lat": qlat,
                "depth": coords[2] if len(coords) > 2 else 0,
                "dist_km": _haversine(lat, lon, qlat, qlon),
            })
        return quakes
    except Exception as exc:
        logger.warning("USGS earthquake fetch failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat: float, lon: float, step: float = 0.005, size: int = 5):
    """Fetch elevation grid from Open Topo Data. Returns center_elevation + grid_elevations."""
    points, coords = [], []
    for i in range(-size, size + 1):
        for j in range(-size, size + 1):
            plat, plon = round(lat + i * step, 6), round(lon + j * step, 6)
            points.append(f"{plat},{plon}")
            coords.append((plat, plon))

    url = f"https://api.opentopodata.org/v1/srtm30m?locations={'|'.join(points[:100])}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevations = [float(r.get("elevation")) if r.get("elevation") is not None else None
                      for r in results]
        center_idx = len(elevations) // 2
        center_elevation = elevations[center_idx] if center_idx < len(elevations) else None
        grid_elevations = [e for e in elevations if e is not None]
        return {"center_elevation": center_elevation, "grid_elevations": grid_elevations,
                "coords": coords[:len(results)]}
    except Exception as exc:
        logger.warning("Open Topo Data fetch failed: %s", exc)
        return {"center_elevation": None, "grid_elevations": [], "coords": []}


@st.cache_data(ttl=900)
def _fetch_soil_data(lat: float, lon: float):
    """Fetch soil composition from ISRIC SoilGrids v2.0."""
    url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lon={lon}&lat={lat}"
        "&property=clay&property=sand&property=soc&property=bdod"
        "&depth=0-5cm&value=mean"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("SoilGrids fetch failed: %s", exc)
        return {}


@st.cache_data(ttl=900)
def _fetch_bedrock(lat: float, lon: float):
    """Fetch bedrock geology from Macrostrat API."""
    url = f"https://macrostrat.org/api/geologic_units/map?lat={lat}&lng={lon}&format=geojson"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("success", {}).get("data", {}).get("features", [])
        if not features:
            features = data.get("features", [])
        units = []
        for f in (features if isinstance(features, list) else []):
            p = f.get("properties", {}) if isinstance(f, dict) else {}
            units.append({
                "name": p.get("unit_name") or p.get("name", "Unknown"),
                "lith": p.get("lith", p.get("lithology", "Unknown")),
                "age": p.get("t_age", p.get("age", "Unknown")),
                "period": p.get("t_int_name", p.get("period", "")),
            })
        return units
    except Exception as exc:
        logger.warning("Macrostrat fetch failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_precipitation(lat: float, lon: float):
    """Fetch 30-day precipitation history from Open-Meteo."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=precipitation_sum&past_days=30&timezone=auto"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        return {
            "dates": daily.get("time", []),
            "precip": [p if p is not None else 0.0 for p in daily.get("precipitation_sum", [])],
        }
    except Exception as exc:
        logger.warning("Open-Meteo precipitation fetch failed: %s", exc)
        return {"dates": [], "precip": []}


@st.cache_data(ttl=900)
def _fetch_osm_volcanoes(lat: float, lon: float, radius_km: int = 300):
    """Fetch volcano nodes from Overpass API within radius."""
    r_deg = radius_km / 111.0
    bbox = f"{lat - r_deg},{lon - r_deg},{lat + r_deg},{lon + r_deg}"
    query = f'[out:json][timeout:10];node["natural"="volcano"]({bbox});out body;'
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        volcanoes = []
        for elem in resp.json().get("elements", []):
            vlat, vlon = elem.get("lat", 0), elem.get("lon", 0)
            volcanoes.append({
                "name": elem.get("tags", {}).get("name", "Unnamed volcano"),
                "lat": vlat, "lon": vlon,
                "dist_km": _haversine(lat, lon, vlat, vlon),
            })
        return volcanoes
    except Exception as exc:
        logger.warning("Overpass volcano fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# SoilGrids v2.0 correct parsing
# ---------------------------------------------------------------------------

def _parse_soil(soil: dict):
    """Parse SoilGrids v2.0 response using mandated layer-map pattern."""
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

    return {"clay": _sv("clay"), "sand": _sv("sand"),
            "soc": _sv("soc"), "bdod": _sv("bdod", 100)}


# ---------------------------------------------------------------------------
# Scoring (0-10, inverted: high risk = low score)
# ---------------------------------------------------------------------------

def _score_seismic(quakes):
    if not quakes:
        return 10.0, "No recent seismic activity within 200 km"
    count = len(quakes)
    max_mag = max(q["mag"] for q in quakes)
    avg_mag = sum(q["mag"] for q in quakes) / count
    min_dist = min(q["dist_km"] for q in quakes)
    score = max(0, 10.0
                - min(count / 50, 1.0) * 3.0
                - min(max_mag / 7.0, 1.0) * 4.0
                - max(0, (1 - min_dist / 200)) * 3.0)
    detail = (f"{count} quakes, max M{max_mag:.1f}, "
              f"nearest {min_dist:.0f} km, avg M{avg_mag:.1f}")
    return round(score, 1), detail


def _score_slope(elev_data):
    elevs = elev_data.get("grid_elevations", [])
    if len(elevs) < 4:
        return 7.0, "Insufficient elevation data"
    step_m = 555.0
    slopes = [math.degrees(math.atan2(abs(elevs[i] - elevs[i - 1]), step_m))
              for i in range(1, len(elevs))]
    max_slope = max(slopes) if slopes else 0
    avg_slope = sum(slopes) / len(slopes) if slopes else 0
    elev_range = max(elevs) - min(elevs)
    if max_slope > 35:   score = 2.0
    elif max_slope > 25: score = 4.0
    elif max_slope > 15: score = 6.0
    elif max_slope > 8:  score = 7.5
    else:                score = 9.5
    if elev_range > 300:   score = max(score - 1.5, 0)
    elif elev_range > 100: score = max(score - 0.5, 0)
    detail = (f"Max slope {max_slope:.1f} deg, avg {avg_slope:.1f} deg, "
              f"elev range {elev_range:.0f} m")
    return round(score, 1), detail


def _score_soil(parsed):
    clay, sand, bdod = parsed.get("clay"), parsed.get("sand"), parsed.get("bdod")
    if clay is None and sand is None:
        return 6.0, "No soil data available"
    score, details = 8.0, []
    if clay is not None:
        details.append(f"Clay {clay:.0f}%")
        score -= 3.0 if clay > 60 else 1.5 if clay > 40 else 0.5 if clay > 25 else 0
    if sand is not None:
        details.append(f"Sand {sand:.0f}%")
        score -= 2.0 if sand > 80 else 1.0 if sand > 60 else 0
    if bdod is not None:
        details.append(f"Bulk density {bdod:.2f} g/cm3")
        score -= 1.5 if bdod < 1.0 else 0.5 if bdod < 1.2 else 0
    return round(max(0, min(10, score)), 1), ", ".join(details) or "Parsed with defaults"


def _score_bedrock(units):
    if not units:
        return 6.0, "No bedrock data available"
    risky = ["volcanic", "basalt", "tuff", "pumice", "ash", "clay", "shale", "mudstone"]
    moderate = ["sandstone", "siltstone", "conglomerate", "limestone", "dolomite", "chalk"]
    stable = ["granite", "gneiss", "quartzite", "schist", "marble", "slate"]
    best_score, desc = 5.0, []
    for u in units[:3]:
        lith = str(u.get("lith", "")).lower()
        desc.append(f"{u['name']} ({lith}, {u.get('period', '')})")
        if any(s in lith for s in stable):     best_score = max(best_score, 9.0)
        elif any(s in lith for s in moderate): best_score = max(best_score, 7.0)
        elif any(s in lith for s in risky):    best_score = min(best_score, 4.0)
    return round(best_score, 1), "; ".join(desc) or "Unknown formation"


def _score_karst(units, parsed_soil):
    karst = ["limestone", "dolomite", "chalk", "gypsum", "evaporite", "karst", "carbonate"]
    has_karst = any(any(k in str(u.get("lith", "")).lower() for k in karst)
                    for u in (units if isinstance(units, list) else []))
    score, reasons = 9.0, []
    if has_karst:
        score -= 4.0; reasons.append("Carbonate/karst-prone bedrock detected")
    clay = parsed_soil.get("clay")
    if clay is not None and clay < 15:
        score -= 1.0; reasons.append("Low clay = poor sealing above voids")
    sand = parsed_soil.get("sand")
    if sand is not None and sand > 70:
        score -= 0.5; reasons.append("High sand = possible piping")
    return round(max(0, min(10, score)), 1), "; ".join(reasons) or "No karst indicators"


def _score_volcanic(lat, lon, osm_volcs):
    all_v = [{"name": n, "dist_km": _haversine(lat, lon, vla, vlo)}
             for vla, vlo, n in _VOLCANO_DB]
    all_v += [{"name": v["name"], "dist_km": v["dist_km"]} for v in osm_volcs]
    if not all_v:
        return 9.5, "No known volcanoes in database"
    all_v.sort(key=lambda x: x["dist_km"])
    d = all_v[0]["dist_km"]
    if d < 30:     score = 1.0
    elif d < 80:   score = 3.0
    elif d < 150:  score = 5.0
    elif d < 300:  score = 7.0
    elif d < 600:  score = 8.5
    else:          score = 10.0
    n300 = sum(1 for v in all_v if v["dist_km"] < 300)
    return round(score, 1), f"Nearest: {all_v[0]['name']} ({d:.0f} km), {n300} within 300 km"


def _score_moisture(precip_data):
    vals = precip_data.get("precip", [])
    if not vals:
        return 7.0, "No precipitation data"
    total = sum(vals)
    avg_d = total / len(vals)
    max_d = max(vals)
    rainy = sum(1 for p in vals if p > 1.0)
    if total > 300:   score = 2.0
    elif total > 200: score = 4.0
    elif total > 100: score = 6.0
    elif total > 50:  score = 7.5
    else:             score = 9.5
    if max_d > 80:    score = max(score - 2.0, 0)
    elif max_d > 40:  score = max(score - 1.0, 0)
    detail = f"30-day total {total:.0f} mm, avg {avg_d:.1f} mm/d, max {max_d:.1f} mm, {rainy} rainy days"
    return round(min(10, score), 1), detail


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verdict(score):
    for thr, lbl, clr in _VERDICT_MAP:
        if score >= thr:
            return lbl, clr
    return "HAZARDOUS", _C["hazardous"]


def _scol(score):
    if score >= 8: return _C["stable"]
    if score >= 5: return _C["moderate"]
    if score >= 3: return _C["unstable"]
    return _C["hazardous"]


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def _radar_chart(dim_scores):
    names = list(dim_scores.keys())
    vals = [dim_scores[n][0] for n in names]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=names + [names[0]],
        fill="toself", fillcolor="rgba(99,102,241,0.25)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=8, color=[_scol(v) for v in vals + [vals[0]]]),
    ))
    fig.update_layout(
        polar=dict(bgcolor="rgba(26,26,46,0.5)",
                   radialaxis=dict(visible=True, range=[0, 10]),
                   angularaxis=dict(tickfont=dict(size=11, color=_C["text"]))),
        showlegend=False, margin=dict(l=60, r=60, t=40, b=40), height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Ground Stability Radar", font=dict(color=_C["text"], size=14)),
    )
    return fig


def _seismic_scatter(quakes):
    fig = go.Figure()
    if not quakes:
        fig.add_annotation(text="No earthquake data", showarrow=False,
                           font=dict(size=16, color=_C["muted"]))
        fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
        return fig
    dists = [q["dist_km"] for q in quakes]
    mags = [q["mag"] for q in quakes]
    colors = ["#ef4444" if m >= 5 else "#f97316" if m >= 4 else "#f59e0b" if m >= 3
              else "#84cc16" if m >= 2 else "#22c55e" for m in mags]
    fig.add_trace(go.Scatter(
        x=dists, y=mags, mode="markers",
        marker=dict(size=[max(6, m * 4) for m in mags], color=colors, opacity=0.8,
                    line=dict(width=1, color="white")),
        text=[f"{q['place']}<br>Depth: {q['depth']:.1f} km" for q in quakes],
        hovertemplate="Dist: %{x:.0f} km<br>Mag: %{y:.1f}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Distance (km)", yaxis_title="Magnitude", height=350,
        margin=dict(l=50, r=30, t=40, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.5)",
        title=dict(text="Earthquake Magnitude vs Distance", font=dict(size=13, color=_C["text"])),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)", color=_C["text"]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)", color=_C["text"]),
    )
    return fig


def _precip_chart(precip_data):
    dates, vals = precip_data.get("dates", []), precip_data.get("precip", [])
    fig = go.Figure()
    if dates and vals:
        colors = ["#3b82f6" if v < 20 else "#f59e0b" if v < 50 else "#ef4444" for v in vals]
        fig.add_trace(go.Bar(x=dates, y=vals, marker_color=colors,
                             hovertemplate="Date: %{x}<br>Precip: %{y:.1f} mm<extra></extra>"))
    fig.update_layout(
        xaxis_title="Date", yaxis_title="Precipitation (mm)", height=300,
        margin=dict(l=50, r=30, t=40, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.5)",
        title=dict(text="30-Day Precipitation History", font=dict(size=13, color=_C["text"])),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)", color=_C["text"]),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)", color=_C["text"]),
    )
    return fig


# ---------------------------------------------------------------------------
# Folium map
# ---------------------------------------------------------------------------

def _build_map(lat, lon, quakes, osm_volcanoes):
    try:
        import folium
    except ImportError:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup=f"Analysis Site<br>{lat:.4f}, {lon:.4f}",
                  icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa")).add_to(m)

    # Earthquake markers
    if quakes:
        eq_grp = folium.FeatureGroup(name="Earthquakes")
        for q in quakes:
            mag = q["mag"]
            color = "red" if mag >= 5 else "orange" if mag >= 4 else "yellow" if mag >= 3 else "green"
            folium.CircleMarker(
                [q["lat"], q["lon"]], radius=max(3, mag * 3), color=color,
                fill=True, fill_opacity=0.6,
                popup=f"M{mag:.1f} - {html_module.escape(str(q['place']))}<br>Depth: {q['depth']:.1f} km",
            ).add_to(eq_grp)
        eq_grp.add_to(m)

    # Volcano markers (DB + OSM)
    vol_grp = folium.FeatureGroup(name="Volcanoes")
    added = False
    for vlat, vlon, vname in _VOLCANO_DB:
        d = _haversine(lat, lon, vlat, vlon)
        if d < 500:
            folium.Marker([vlat, vlon], popup=f"{vname}<br>{d:.0f} km",
                          icon=folium.Icon(color="red", icon="fire", prefix="fa")).add_to(vol_grp)
            added = True
    for v in osm_volcanoes:
        if v["dist_km"] < 500:
            folium.Marker([v["lat"], v["lon"]], popup=f"{v['name']}<br>{v['dist_km']:.0f} km",
                          icon=folium.Icon(color="red", icon="fire", prefix="fa")).add_to(vol_grp)
            added = True
    if added:
        vol_grp.add_to(m)

    # 200 km radius
    folium.Circle([lat, lon], radius=200000, color="#6366f1", fill=False,
                  dash_array="5", weight=1, popup="200 km seismic radius").add_to(m)
    folium.LayerControl().add_to(m)
    return m


# ---------------------------------------------------------------------------
# Metric card
# ---------------------------------------------------------------------------

def _card(label, score, detail, color):
    sc = _scol(score)
    st.markdown(f"""
    <div style="background:{_C['card']};border-left:4px solid {color};
                border-radius:8px;padding:12px 14px;margin-bottom:8px;">
        <div style="font-size:0.82em;color:{_C['muted']};margin-bottom:4px;">{label}</div>
        <div style="font-size:1.7em;font-weight:700;color:{sc};">{score:.1f}
            <span style="font-size:0.5em;color:{_C['muted']};"> /10</span></div>
        <div style="font-size:0.75em;color:{_C['text']};margin-top:4px;
             line-height:1.35;">{detail}</div>
    </div>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_geological_risk_tab():
    """Render the Geological Risk & Ground Stability analysis tab."""

    st.markdown("## Geological Risk & Ground Stability")
    st.caption("Deep geological analysis: seismic, slope, soil, bedrock & geohazards")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f",
                          key="georisk_lat", min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.5, format="%.4f",
                          key="georisk_lon", min_value=-180.0, max_value=180.0)

    presets = {
        "Custom": None,
        "Rome, Italy": (41.9028, 12.4964),
        "Mount Vesuvius": (40.821, 14.426),
        "San Francisco, CA": (37.7749, -122.4194),
        "Tokyo, Japan": (35.6762, 139.6503),
        "Reykjavik, Iceland": (64.1466, -21.9426),
        "Mexico City": (19.4326, -99.1332),
        "Istanbul, Turkey": (41.0082, 28.9784),
        "Kathmandu, Nepal": (27.7172, 85.324),
        "Lima, Peru": (-12.0464, -77.0428),
        "Wellington, NZ": (-41.2865, 174.7762),
        "Athens, Greece": (37.9838, 23.7275),
    }
    preset = st.selectbox("Preset locations", list(presets.keys()), key="georisk_preset")
    if preset != "Custom" and presets[preset]:
        lat, lon = presets[preset]

    if not st.button("Analyze Geology", key="georisk_btn"):
        st.info("Enter coordinates and click **Analyze Geology** to begin.")
        return

    # ---- Fetch all data ----
    with st.spinner("Fetching geological data from 6 APIs..."):
        quakes = _fetch_earthquakes(lat, lon)
        elev_data = _fetch_elevation_grid(lat, lon)
        soil_raw = _fetch_soil_data(lat, lon)
        bedrock_units = _fetch_bedrock(lat, lon)
        precip_data = _fetch_precipitation(lat, lon)
        osm_volcanoes = _fetch_osm_volcanoes(lat, lon)

    parsed_soil = _parse_soil(soil_raw)

    # ---- Compute 7 scores ----
    dim_scores = {
        "Seismic Activity":   _score_seismic(quakes),
        "Slope Stability":    _score_slope(elev_data),
        "Soil Composition":   _score_soil(parsed_soil),
        "Bedrock Geology":    _score_bedrock(bedrock_units),
        "Karst & Sinkhole":   _score_karst(bedrock_units, parsed_soil),
        "Volcanic Proximity": _score_volcanic(lat, lon, osm_volcanoes),
        "Ground Moisture":    _score_moisture(precip_data),
    }

    all_sc = [v[0] for v in dim_scores.values()]
    overall = round(sum(all_sc) / len(all_sc), 1)
    vlabel, vcolor = _verdict(overall)

    # ---- Overall banner ----
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{_C['card']},rgba(26,26,46,0.95));
                border:2px solid {vcolor};border-radius:12px;padding:20px;
                text-align:center;margin:16px 0;">
        <div style="font-size:0.9em;color:{_C['muted']};letter-spacing:2px;">
            GROUND STABILITY INDEX</div>
        <div style="font-size:3em;font-weight:800;color:{vcolor};margin:8px 0;">
            {overall}</div>
        <div style="font-size:1.3em;font-weight:700;color:{vcolor};
                    letter-spacing:3px;">{vlabel}</div>
        <div style="font-size:0.85em;color:{_C['text']};margin-top:8px;">
            {lat:.4f}N, {lon:.4f}E &mdash; 7 geological dimensions analysed</div>
    </div>""", unsafe_allow_html=True)

    # ---- 7 metric cards ----
    dim_names = list(dim_scores.keys())
    row1 = st.columns(4)
    for i, col in enumerate(row1):
        if i < len(dim_names):
            nm = dim_names[i]
            with col:
                _card(nm, *dim_scores[nm], _DIM_META.get(nm, "#6366f1"))
    row2 = st.columns(3)
    for i, col in enumerate(row2):
        idx = i + 4
        if idx < len(dim_names):
            nm = dim_names[idx]
            with col:
                _card(nm, *dim_scores[nm], _DIM_META.get(nm, "#6366f1"))

    st.markdown("---")

    # ---- Charts ----
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(_radar_chart(dim_scores, key="georis_pchart1"), use_container_width=True, key="georisk_radar")
    with ch2:
        st.plotly_chart(_seismic_scatter(quakes, key="georis_pchart2"), use_container_width=True, key="georisk_scatter")

    st.plotly_chart(_precip_chart(precip_data, key="georis_pchart3"), use_container_width=True, key="georisk_precip")
    st.markdown("---")

    # ---- Folium map ----
    st.subheader("Geological Hazard Map")
    fol_map = _build_map(lat, lon, quakes, osm_volcanoes)
    if fol_map is not None:
        import streamlit.components.v1 as components
        components.html(fol_map._repr_html_(), height=520, scrolling=True)
    else:
        st.warning("Install `folium` for interactive hazard map: `pip install folium`")

    st.markdown("---")

    # ---- Expander: Seismic Details ----
    with st.expander("Seismic Activity Details", expanded=False):
        if quakes:
            st.markdown(f"**{len(quakes)} earthquakes** within 200 km")
            mag_ranges = [("< 2", 0, 2), ("2-3", 2, 3), ("3-4", 3, 4),
                          ("4-5", 4, 5), ("5-6", 5, 6), ("6+", 6, 99)]
            cols = st.columns(len(mag_ranges))
            for i, (lb, lo, hi) in enumerate(mag_ranges):
                cols[i].metric(lb, sum(1 for q in quakes if lo <= q["mag"] < hi),
                               key=f"georisk_mag_{i}")
            st.markdown("**Nearest 5:**")
            for q in sorted(quakes, key=lambda x: x["dist_km"])[:5]:
                ts = datetime.fromtimestamp(q["time"] / 1000).strftime("%Y-%m-%d") if q["time"] else "N/A"
                st.markdown(f"- **M{q['mag']:.1f}** {q['dist_km']:.0f} km "
                            f"(depth {q['depth']:.1f} km) - {html_module.escape(str(q['place']))} [{ts}]")
            shallow = sum(1 for q in quakes if q["depth"] < 30)
            mid = sum(1 for q in quakes if 30 <= q["depth"] < 70)
            deep = sum(1 for q in quakes if q["depth"] >= 70)
            d1, d2, d3 = st.columns(3)
            d1.metric("Shallow (<30 km)", shallow, key="georisk_depth_s")
            d2.metric("Intermediate", mid, key="georisk_depth_m")
            d3.metric("Deep (>70 km)", deep, key="georisk_depth_d")
        else:
            st.success("No recent seismic activity within 200 km.")

    # ---- Expander: Slope ----
    with st.expander("Slope & Elevation Details", expanded=False):
        ce = elev_data.get("center_elevation")
        ge = elev_data.get("grid_elevations", [])
        if ce is not None:
            st.metric("Centre Elevation", f"{ce:.0f} m", key="georisk_center_elev")
        if ge:
            e1, e2, e3 = st.columns(3)
            e1.metric("Min", f"{min(ge):.0f} m", key="georisk_min_elev")
            e2.metric("Max", f"{max(ge):.0f} m", key="georisk_max_elev")
            e3.metric("Range", f"{max(ge) - min(ge):.0f} m", key="georisk_elev_range")
            efig = go.Figure()
            efig.add_trace(go.Scatter(y=ge, mode="lines+markers",
                                      line=dict(color="#6366f1", width=2),
                                      marker=dict(size=3)))
            efig.update_layout(
                title="Elevation Profile", height=260,
                margin=dict(l=50, r=30, t=40, b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.5)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)", title="Grid Point"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)", title="Elevation (m)"),
            )
            st.plotly_chart(efig, use_container_width=True, key="georisk_elev_chart")
        else:
            st.warning("Elevation data unavailable.")

    # ---- Expander: Soil ----
    with st.expander("Soil Composition Details", expanded=False):
        clay_v, sand_v = parsed_soil.get("clay"), parsed_soil.get("sand")
        soc_v, bdod_v = parsed_soil.get("soc"), parsed_soil.get("bdod")
        if clay_v is not None or sand_v is not None:
            s1, s2, s3, s4 = st.columns(4)
            if clay_v is not None: s1.metric("Clay", f"{clay_v:.1f}%", key="georisk_clay")
            if sand_v is not None: s2.metric("Sand", f"{sand_v:.1f}%", key="georisk_sand")
            if soc_v is not None:  s3.metric("SOC", f"{soc_v:.1f} g/kg", key="georisk_soc")
            if bdod_v is not None: s4.metric("Bulk D.", f"{bdod_v:.2f}", key="georisk_bdod")
            if clay_v is not None and sand_v is not None:
                silt = max(0, 100 - clay_v - sand_v)
                pie = go.Figure(data=[go.Pie(
                    labels=["Clay", "Sand", "Silt (est.)"],
                    values=[clay_v, sand_v, silt],
                    marker=dict(colors=["#a0522d", "#f59e0b", "#8b97b0"]),
                    textinfo="label+percent", hole=0.35,
                )])
                pie.update_layout(title="Soil Texture", height=300,
                                  margin=dict(l=30, r=30, t=50, b=30),
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  legend=dict(font=dict(color=_C["text"])))
                st.plotly_chart(pie, use_container_width=True, key="georisk_soil_pie")
                if clay_v > 40:
                    st.warning("High clay: significant shrink-swell risk.")
                if sand_v > 75:
                    st.warning("High sand: liquefaction risk during earthquakes.")
        else:
            st.warning("No soil data available from SoilGrids.")

    # ---- Expander: Bedrock ----
    with st.expander("Bedrock Geology Details", expanded=False):
        if bedrock_units:
            for u in bedrock_units[:5]:
                st.markdown(f"**{u['name']}** -- {u['lith']} | {u['period']} | Age: {u['age']}")
        else:
            st.info("No bedrock data from Macrostrat for this location.")

    # ---- Expander: Karst ----
    with st.expander("Karst & Sinkhole Assessment", expanded=False):
        ks, kd = dim_scores["Karst & Sinkhole"]
        st.markdown(f"**Score:** {ks}/10 -- {kd}")
        if ks < 5:
            st.error("Carbonate bedrock: high sinkhole risk. GPR survey recommended.")
        elif ks < 7:
            st.warning("Moderate karst indicators. Geotechnical investigation advised.")
        else:
            st.success("Low karst/sinkhole risk.")

    # ---- Expander: Volcanic ----
    with st.expander("Volcanic Proximity Details", expanded=False):
        vs, vd = dim_scores["Volcanic Proximity"]
        st.markdown(f"**Score:** {vs}/10 -- {vd}")
        nearby = sorted(
            [{"name": n, "dist_km": _haversine(lat, lon, vla, vlo)}
             for vla, vlo, n in _VOLCANO_DB if _haversine(lat, lon, vla, vlo) < 500] +
            [v for v in osm_volcanoes if v["dist_km"] < 500],
            key=lambda x: x["dist_km"],
        )
        if nearby:
            st.markdown("**Nearby volcanoes (<500 km):**")
            for v in nearby[:8]:
                tag = "HIGH" if v["dist_km"] < 50 else "MODERATE" if v["dist_km"] < 150 else "LOW"
                st.markdown(f"- **{v['name']}** -- {v['dist_km']:.0f} km ({tag})")
        else:
            st.success("No known volcanoes within 500 km.")

    # ---- Expander: Moisture ----
    with st.expander("Ground Moisture Analysis", expanded=False):
        pv = precip_data.get("precip", [])
        if pv:
            t = sum(pv)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("30-Day Total", f"{t:.0f} mm", key="georisk_tot_prec")
            m2.metric("Daily Avg", f"{t / len(pv):.1f} mm", key="georisk_avg_prec")
            m3.metric("Max Daily", f"{max(pv):.1f} mm", key="georisk_max_prec")
            m4.metric("Rainy Days", sum(1 for p in pv if p > 1), key="georisk_rain_d")
            if t > 200:
                st.error("Very high precipitation: ground saturation, landslide risk.")
            elif t > 100:
                st.warning("Above-average precipitation. Monitor drainage.")
            else:
                st.success("Precipitation within normal range.")
        else:
            st.info("No precipitation data available.")

    # ---- Summary table ----
    st.markdown("---")
    st.subheader("Risk Summary")
    rows = ""
    for nm, (sc, dt) in dim_scores.items():
        clr = _scol(sc)
        rows += (f'<tr><td style="padding:8px;color:{_C["text"]};font-weight:600;">{nm}</td>'
                 f'<td style="padding:8px;text-align:center;">'
                 f'<span style="color:{clr};font-weight:700;font-size:1.1em;">{sc}</span></td>'
                 f'<td style="padding:8px;width:35%;"><div style="background:rgba(255,255,255,0.1);'
                 f'border-radius:4px;height:18px;overflow:hidden;">'
                 f'<div style="background:{clr};width:{sc * 10}%;height:100%;'
                 f'border-radius:4px;"></div></div></td>'
                 f'<td style="padding:8px;color:{_C["muted"]};font-size:0.82em;">'
                 f'{dt[:80]}</td></tr>')
    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;background:{_C['card']};
                  border-radius:8px;overflow:hidden;">
        <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.15);">
            <th style="padding:10px;text-align:left;color:{_C['muted']};">Dimension</th>
            <th style="padding:10px;text-align:center;color:{_C['muted']};">Score</th>
            <th style="padding:10px;text-align:left;color:{_C['muted']};">Level</th>
            <th style="padding:10px;text-align:left;color:{_C['muted']};">Details</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr style="border-top:2px solid {vcolor};">
            <td style="padding:10px;color:{vcolor};font-weight:700;font-size:1.1em;">OVERALL</td>
            <td style="padding:10px;text-align:center;color:{vcolor};
                font-weight:800;font-size:1.3em;">{overall}</td>
            <td colspan="2" style="padding:10px;color:{vcolor};font-weight:700;
                font-size:1.1em;letter-spacing:2px;">{vlabel}</td>
        </tr></tfoot>
    </table>""", unsafe_allow_html=True)

    # ---- Recommendations ----
    st.markdown("---")
    st.subheader("Recommendations")
    sm = {nm: sc for nm, (sc, _) in dim_scores.items()}
    _rec_map = {
        "Seismic Activity": "Seismic hazard assessment needed. Consider seismic-resistant foundations.",
        "Slope Stability": "Steep terrain. Slope stability analysis critical; consider retaining walls.",
        "Soil Composition": "Problematic soil. Geotechnical boring recommended; ground improvement needed.",
        "Bedrock Geology": "Weak bedrock. Account for variable bearing capacity; rock anchoring may help.",
        "Karst & Sinkhole": "High karst risk. GPR survey recommended; avoid concentrated point loads.",
        "Volcanic Proximity": "Volcanic hazard zone. Review risk maps; plan for ashfall and evacuation.",
        "Ground Moisture": "High ground moisture. Delay excavation if possible; implement dewatering.",
    }
    recs = [msg for dim, msg in _rec_map.items() if sm.get(dim, 10) < 5]
    if overall >= 8:
        recs.append("Overall stable. Standard practices appropriate with site-specific investigation.")
    if recs:
        for i, r in enumerate(recs):
            st.markdown(f"{i + 1}. {r}")
    else:
        st.info("Ground conditions broadly acceptable. Standard geotechnical "
                "investigation still recommended.")

    st.markdown("---")
    st.caption(
        "Data: USGS Earthquake Hazards, Open Topo Data (SRTM 30m), "
        "ISRIC SoilGrids v2.0, Macrostrat, OpenStreetMap/Overpass, "
        "Open-Meteo. All free, no API keys required."
    )
