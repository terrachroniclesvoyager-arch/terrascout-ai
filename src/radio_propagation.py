"""
Radio Propagation & RF Analysis -- TerraScout AI module.

Estimates radio signal propagation based on terrain, elevation, and obstacles
across six scored dimensions:
  1. Elevation Advantage    -- higher ground = better line-of-sight (Open Topo Data)
  2. Terrain Obstruction    -- Fresnel zone clearance along radial profiles (Open Topo Data)
  3. Urban Clutter          -- buildings / towers blocking signals within 3 km (Overpass)
  4. Vegetation Attenuation -- forest / woodland density reducing signal (Overpass)
  5. Weather Impact         -- rain, humidity affecting high-freq propagation (Open-Meteo)
  6. Infrastructure         -- existing towers, antennas, repeaters nearby (Overpass)

RF model: FSPL = 20*log10(d) + 20*log10(f) + 32.44  (d in km, f in MHz).
Uses: Open Topo Data, Overpass API, Open-Meteo.  Part of TerraScout AI.
"""
import logging
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)
# ── Constants ─────────────────────────────────────────────────────────────────
OPEN_TOPO_API  = "https://api.opentopodata.org/v1/srtm30m"
OVERPASS_URL   = "https://overpass-api.de/api/interpreter"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FREQ_BANDS: Dict[str, float] = {
    "VHF (150 MHz)": 150.0, "UHF (450 MHz)": 450.0,
    "Cellular (900 MHz)": 900.0, "WiFi (2400 MHz)": 2400.0,
}

DIMENSION_CONFIG: Dict[str, Dict[str, Any]] = {
    "elevation_advantage":    {"name": "Elevation Advantage",    "color": "#f97316", "weight": 0.20},
    "terrain_obstruction":    {"name": "Terrain Obstruction",    "color": "#ef4444", "weight": 0.25},
    "urban_clutter":          {"name": "Urban Clutter",          "color": "#6366f1", "weight": 0.15},
    "vegetation_attenuation": {"name": "Vegetation Attenuation", "color": "#22c55e", "weight": 0.10},
    "weather_impact":         {"name": "Weather Impact",         "color": "#3b82f6", "weight": 0.10},
    "infrastructure":         {"name": "Infrastructure",         "color": "#8b5cf6", "weight": 0.20},
}

SIGNAL_LEVELS = [
    (9, 10, "EXCELLENT", "#10b981"), (7, 8, "GOOD", "#22c55e"),
    (5, 6, "FAIR", "#f59e0b"), (3, 4, "POOR", "#f97316"),
    (0, 2, "DEAD ZONE", "#ef4444"),
]

URBAN_THRESHOLDS = [0, 5, 15, 35, 70, 120, 200, 350, 550, 800, 1200]
VEG_THRESHOLDS   = [0, 2, 5, 10, 18, 30, 50, 80, 120, 180, 250]
INFRA_THRESHOLDS = [0, 1, 2, 4, 7, 11, 16, 22, 30, 40, 55]

PROFILE_SAMPLES = 30
NUM_RADIALS     = 8
MAX_PROFILE_KM  = 10.0
# ── Helpers ───────────────────────────────────────────────────────────────────

def _classify_signal(score: float) -> Tuple[str, str]:
    """Return (label, hex-colour) for a score 0-10."""
    s = int(round(score))
    for lo, hi, label, colour in SIGNAL_LEVELS:
        if lo <= s <= hi:
            return label, colour
    return "UNKNOWN", "#6b7280"

def _score_from_count(count: int, thresholds: List[int]) -> int:
    for idx, t in enumerate(thresholds):
        if count <= t:
            return idx
    return 10

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _deg_per_km_lat() -> float:
    return 1.0 / 111.0

def _deg_per_km_lon(lat: float) -> float:
    return 1.0 / (111.0 * max(math.cos(math.radians(lat)), 0.01))

def _fspl_db(distance_km: float, freq_mhz: float) -> float:
    """Free-Space Path Loss: FSPL = 20*log10(d) + 20*log10(f) + 32.44."""
    if distance_km <= 0 or freq_mhz <= 0:
        return 0.0
    return 20 * math.log10(distance_km) + 20 * math.log10(freq_mhz) + 32.44

def _fresnel_radius(distance_m: float, total_m: float, freq_mhz: float) -> float:
    """First Fresnel zone radius at a point along the path (metres)."""
    if total_m <= 0 or freq_mhz <= 0:
        return 0.0
    wavelength = 300.0 / freq_mhz
    d2 = total_m - distance_m
    if distance_m <= 0 or d2 <= 0:
        return 0.0
    return math.sqrt(wavelength * distance_m * d2 / total_m)
# ── Overpass runner ───────────────────────────────────────────────────────────

@st.cache_data(ttl=900)
def _run_overpass(query_body: str) -> Optional[dict]:
    full = f"[out:json][timeout:25];({query_body});out body;>;out skel qt;"
    try:
        resp = requests.post(OVERPASS_URL, data={"data": full}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return None

def _count_elements(data: Optional[dict]) -> int:
    if not data:
        return 0
    return len({el.get("id", id(el)) for el in data.get("elements", [])})

def _extract_nodes(data: Optional[dict]) -> List[dict]:
    if not data:
        return []
    out: List[dict] = []
    for el in data.get("elements", []):
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is not None and lon is not None:
            out.append({"lat": lat, "lon": lon, "tags": el.get("tags", {})})
    return out
# ── Dimension 1: Elevation Advantage ─────────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_elevation_grid(lat: float, lon: float, grid_n: int = 7,
                         spacing_km: float = 1.5) -> Dict[str, Any]:
    """Fetch NxN elevation grid and score height advantage."""
    half = grid_n // 2
    dlat, dlon = spacing_km * _deg_per_km_lat(), spacing_km * _deg_per_km_lon(lat)
    points = [f"{lat + i * dlat:.5f},{lon + j * dlon:.5f}"
              for i in range(-half, half + 1) for j in range(-half, half + 1)]
    default: Dict[str, Any] = {"center": 0.0, "elevations": [], "score": 5,
                                "mean": 0.0, "min": 0.0, "max": 0.0, "advantage_m": 0.0}
    all_results: List[dict] = []
    for bs in range(0, len(points), 100):
        try:
            resp = requests.get(OPEN_TOPO_API,
                                params={"locations": "|".join(points[bs:bs+100])}, timeout=10)
            resp.raise_for_status()
            all_results.extend(resp.json().get("results", []))
        except Exception as exc:
            logger.warning("Elevation grid error: %s", exc)
    elevs = [float(r["elevation"]) for r in all_results if r.get("elevation") is not None]
    if len(elevs) < 3:
        return default
    center_elev = elevs[len(elevs) // 2]
    avg = statistics.mean(elevs)
    advantage = center_elev - avg
    score = max(0, min(10, int(round(5.0 + advantage * 0.05))))
    return {"center": round(center_elev, 1), "elevations": elevs, "score": score,
            "mean": round(avg, 1), "min": round(min(elevs), 1),
            "max": round(max(elevs), 1), "advantage_m": round(advantage, 1)}
# ── Dimension 2: Terrain Obstruction (Fresnel clearance) ─────────────────────

@st.cache_data(ttl=900)
def fetch_radial_profiles(lat: float, lon: float, max_dist_km: float = 10.0,
                          n_radials: int = 8, n_samples: int = 30) -> Dict[str, Any]:
    """Elevation profiles along radial directions with Fresnel clearance."""
    dlat_km, dlon_km = _deg_per_km_lat(), _deg_per_km_lon(lat)
    angles = [i * 360.0 / n_radials for i in range(n_radials)]
    profiles: Dict[str, List[Tuple[float, float]]] = {}
    clearance_scores: List[float] = []

    for bearing in angles:
        rad = math.radians(bearing)
        pts = [f"{lat + max_dist_km * s / n_samples * math.cos(rad) * dlat_km:.5f},"
               f"{lon + max_dist_km * s / n_samples * math.sin(rad) * dlon_km:.5f}"
               for s in range(n_samples + 1)]
        elevs: List[Optional[float]] = [None] * len(pts)
        for bs in range(0, len(pts), 100):
            try:
                resp = requests.get(OPEN_TOPO_API,
                                    params={"locations": "|".join(pts[bs:bs+100])}, timeout=10)
                resp.raise_for_status()
                for k, r in enumerate(resp.json().get("results", [])):
                    if r.get("elevation") is not None:
                        elevs[bs + k] = float(r["elevation"])
            except Exception as exc:
                logger.warning("Radial profile %.0f deg error: %s", bearing, exc)

        profile = [(max_dist_km * s / n_samples, elevs[s] if elevs[s] is not None else 0.0)
                    for s in range(n_samples + 1)]
        profiles[f"{int(bearing)}"] = profile

        # Fresnel clearance check
        tx_elev, rx_elev = profile[0][1], profile[-1][1]
        total_d_m = max_dist_km * 1000.0
        blocked = 0
        for s in range(1, n_samples):
            d_m = (max_dist_km * s / n_samples) * 1000.0
            los_elev = tx_elev + (rx_elev - tx_elev) * (s / n_samples)
            f1 = _fresnel_radius(d_m, total_d_m, 450.0)
            if profile[s][1] > los_elev - f1:
                blocked += 1
        clearance_scores.append(100.0 * (1.0 - blocked / max(n_samples - 1, 1)))

    avg_cl = statistics.mean(clearance_scores) if clearance_scores else 50.0
    return {"profiles": profiles, "clearance_scores": clearance_scores,
            "avg_clearance_pct": round(avg_cl, 1),
            "score": max(0, min(10, int(round(avg_cl / 10.0))))}
# ── Dimension 3: Urban Clutter ───────────────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_urban_clutter(lat: float, lon: float, radius: int = 3000) -> Dict[str, Any]:
    """Buildings and tall structures blocking RF."""
    query = (f'way["building"](around:{radius},{lat},{lon});'
             f'node["man_made"="tower"](around:{radius},{lat},{lon});'
             f'way["building:levels"](around:{radius},{lat},{lon});')
    data = _run_overpass(query)
    count = _count_elements(data)
    return {"count": count, "score": 10 - _score_from_count(count, URBAN_THRESHOLDS),
            "elements": _extract_nodes(data)}
# ── Dimension 4: Vegetation Attenuation ──────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_vegetation(lat: float, lon: float, radius: int = 3000) -> Dict[str, Any]:
    """Forest / woodland areas attenuating RF signals."""
    query = (f'way["landuse"="forest"](around:{radius},{lat},{lon});'
             f'way["natural"="wood"](around:{radius},{lat},{lon});'
             f'way["landuse"="orchard"](around:{radius},{lat},{lon});')
    data = _run_overpass(query)
    count = _count_elements(data)
    return {"count": count, "score": 10 - _score_from_count(count, VEG_THRESHOLDS)}
# ── Dimension 5: Weather Impact ──────────────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_weather_impact(lat: float, lon: float) -> Dict[str, Any]:
    """Current weather conditions affecting RF propagation."""
    default: Dict[str, Any] = {"score": 7, "rain_mm": 0.0, "humidity_pct": 50.0,
                                "cloud_pct": 50, "temp_c": 20.0, "detail": "No data"}
    try:
        resp = requests.get(OPEN_METEO_URL, params={
            "latitude": lat, "longitude": lon, "current_weather": "true",
            "hourly": "relativehumidity_2m,precipitation,cloudcover",
            "forecast_days": 1}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo request failed: %s", exc)
        return default
    hourly = data.get("hourly", {})
    hum_l = hourly.get("relativehumidity_2m", [])
    prec_l = hourly.get("precipitation", [])
    cld_l = hourly.get("cloudcover", [])
    humidity = statistics.mean(hum_l) if hum_l else 50.0
    rain = max(prec_l) if prec_l else 0.0
    cloud = statistics.mean(cld_l) if cld_l else 50.0
    temp = data.get("current_weather", {}).get("temperature", 20.0)
    penalty = 0.0
    if rain > 10:       penalty += 4.0
    elif rain > 3:      penalty += 2.5
    elif rain > 0.5:    penalty += 1.0
    if humidity > 90:   penalty += 2.0
    elif humidity > 75: penalty += 1.0
    if cloud > 90:      penalty += 1.0
    score = max(0, min(10, int(round(10 - penalty))))
    detail = f"Rain {rain:.1f}mm, Humidity {humidity:.0f}%, Cloud {cloud:.0f}%"
    return {"score": score, "rain_mm": round(rain, 1), "humidity_pct": round(humidity, 1),
            "cloud_pct": round(cloud, 0), "temp_c": round(temp, 1), "detail": detail}
# ── Dimension 6: Infrastructure ──────────────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_rf_infrastructure(lat: float, lon: float, radius: int = 10000) -> Dict[str, Any]:
    """Communication towers, antennas, and repeaters within radius."""
    query = (
        f'node["tower:type"~"communication|telecommunication"](around:{radius},{lat},{lon});'
        f'node["man_made"="mast"](around:{radius},{lat},{lon});'
        f'node["man_made"="antenna"](around:{radius},{lat},{lon});'
        f'node["man_made"="tower"]["tower:type"="communication"](around:{radius},{lat},{lon});'
        f'node["tower:type"="broadcast"](around:{radius},{lat},{lon});')
    data = _run_overpass(query)
    count = _count_elements(data)
    return {"count": count, "score": _score_from_count(count, INFRA_THRESHOLDS),
            "elements": _extract_nodes(data)}
# ── Aggregate / RF models ────────────────────────────────────────────────────

def _compute_overall(dim_scores: Dict[str, int]) -> float:
    ws = sum(dim_scores.get(k, 0) * c["weight"] for k, c in DIMENSION_CONFIG.items())
    tw = sum(c["weight"] for c in DIMENSION_CONFIG.values())
    return round(ws / tw, 1) if tw else 0.0

def _estimate_coverage_radius(freq_mhz: float, overall_score: float,
                              tx_dbm: float = 36.0, rx_dbm: float = -100.0) -> float:
    """Max coverage radius (km) from FSPL solved for d with env penalty."""
    env_penalty = (10 - overall_score) * 3.0
    budget = tx_dbm - rx_dbm - env_penalty
    exp = (budget - 20 * math.log10(freq_mhz) - 32.44) / 20.0
    return round(max(0.01, 10 ** exp), 2)
# ── UI rendering helpers ─────────────────────────────────────────────────────

def _render_overall_gauge(overall: float) -> None:
    label, colour = _classify_signal(overall)
    pct = overall * 10
    st.markdown(
        f"<div style='text-align:center;margin-bottom:6px;'>"
        f"<span style='font-size:2.5rem;font-weight:800;color:{colour};'>"
        f"{overall:.1f}</span>"
        f"<span style='font-size:1.1rem;color:#6b7280;'> / 10</span></div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div style='background:#e5e7eb;border-radius:8px;height:18px;"
        f"overflow:hidden;margin:0 auto;max-width:500px;'>"
        f"<div style='width:{pct}%;height:100%;background:{colour};"
        f"border-radius:8px;transition:width 0.6s;'></div></div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;font-weight:700;color:{colour};"
        f"margin-top:4px;font-size:1.05rem;'>{label}</p>", unsafe_allow_html=True)

def _render_signal_bars(score: int, label: str, colour: str) -> None:
    bars = "".join(
        f'<div style="width:12px;height:{8 + i * 7}px;'
        f'background:{colour if score >= i * 2 else "#e5e7eb"};'
        f'border-radius:2px;margin-right:3px;display:inline-block;'
        f'vertical-align:bottom;"></div>' for i in range(1, 6))
    st.markdown(
        f'<div style="display:flex;align-items:flex-end;margin-bottom:4px;">{bars}'
        f'<span style="margin-left:8px;font-weight:700;color:{colour};">'
        f'{score}/10 -- {label}</span></div>', unsafe_allow_html=True)

def _render_dimension_card(title: str, score: int, details: Dict[str, Any],
                           colour: str) -> None:
    label, lbl_c = _classify_signal(score)
    st.markdown(
        f"<div style='border-left:4px solid {colour};padding:8px 12px;"
        f"margin-bottom:10px;border-radius:4px;background:rgba(0,0,0,0.02);'>"
        f"<strong>{title}</strong></div>", unsafe_allow_html=True)
    _render_signal_bars(score, label, lbl_c)
    items = [f"**{k}:** {v}" for k, v in details.items()]
    if items:
        st.caption(" | ".join(items))

def _render_radar_chart(dim_scores: Dict[str, int]) -> None:
    cats = [c["name"] for c in DIMENSION_CONFIG.values()]
    vals = [dim_scores.get(k, 0) for k in DIMENSION_CONFIG]
    cats.append(cats[0]); vals.append(vals[0])
    fig = go.Figure(data=[go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color="#6366f1", width=2), marker=dict(size=6))])
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=10))),
        showlegend=False, margin=dict(l=60, r=60, t=30, b=30),
        height=370, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, key="rfprop_radar")

def _render_path_loss_chart(freq_mhz: float, freq_label: str) -> None:
    dists = [20.0 * i / 50 for i in range(1, 51)]
    losses = [round(_fspl_db(d, freq_mhz), 1) for d in dists]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dists, y=losses, mode="lines", name=freq_label,
                             line=dict(color="#6366f1", width=2),
                             fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"))
    fig.update_layout(title=f"Free-Space Path Loss -- {freq_label}",
                      xaxis_title="Distance (km)", yaxis_title="Path Loss (dB)",
                      height=350, margin=dict(l=50, r=20, t=40, b=40),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor="rgba(200,200,200,0.3)"),
                      yaxis=dict(gridcolor="rgba(200,200,200,0.3)"))
    st.plotly_chart(fig, use_container_width=True, key="rfprop_fspl_chart")

def _render_signal_heatmap(lat: float, lon: float, freq_mhz: float,
                           overall_score: float) -> None:
    """Plotly heatmap of estimated signal strength around the point."""
    gn, radius_km = 20, 15.0
    dlat, dlon = _deg_per_km_lat(), _deg_per_km_lon(lat)
    env_pen = (10 - overall_score) * 3.0
    z: List[List[float]] = []
    for i in range(gn):
        row: List[float] = []
        for j in range(gn):
            glat = lat + (i - gn / 2) * radius_km * 2 / gn * dlat
            glon = lon + (j - gn / 2) * radius_km * 2 / gn * dlon
            d = max(0.05, _haversine_km(lat, lon, glat, glon))
            row.append(round(36.0 - _fspl_db(d, freq_mhz) - env_pen, 1))
        z.append(row)
    x_lbl = [f"{(j - gn / 2) * radius_km * 2 / gn:.1f}" for j in range(gn)]
    y_lbl = [f"{(i - gn / 2) * radius_km * 2 / gn:.1f}" for i in range(gn)]
    fig = go.Figure(data=go.Heatmap(
        z=z, x=x_lbl, y=y_lbl,
        colorscale=[[0, "#ef4444"], [0.3, "#f97316"], [0.5, "#f59e0b"],
                     [0.7, "#22c55e"], [1.0, "#10b981"]],
        colorbar=dict(title="dBm"), hoverongaps=False))
    fig.update_layout(title="Estimated Signal Strength (dBm)",
                      xaxis_title="East-West offset (km)",
                      yaxis_title="North-South offset (km)",
                      height=450, margin=dict(l=50, r=20, t=40, b=40),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, key="rfprop_heatmap")

def _render_terrain_profile(profiles: Dict[str, List[Tuple[float, float]]],
                            freq_mhz: float, bearing_key: str) -> None:
    """Terrain cross-section with line-of-sight and Fresnel zone overlay."""
    if bearing_key not in profiles:
        st.info("No profile data available for this bearing.")
        return
    profile = profiles[bearing_key]
    distances = [p[0] for p in profile]
    elevations = [p[1] for p in profile]
    tx_elev, rx_elev = elevations[0], elevations[-1]
    total_d_m = distances[-1] * 1000.0 if distances[-1] > 0 else 1.0
    los_line, f_upper, f_lower = [], [], []
    for d_km, _ in profile:
        frac = d_km / distances[-1] if distances[-1] > 0 else 0
        los_e = tx_elev + frac * (rx_elev - tx_elev)
        los_line.append(round(los_e, 1))
        f1 = _fresnel_radius(d_km * 1000.0, total_d_m, freq_mhz)
        f_upper.append(round(los_e + f1, 1))
        f_lower.append(round(los_e - f1, 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=elevations, mode="lines", name="Terrain",
                             fill="tozeroy", fillcolor="rgba(139,92,246,0.12)",
                             line=dict(color="#8b5cf6", width=2)))
    fig.add_trace(go.Scatter(x=distances, y=los_line, mode="lines", name="Line of Sight",
                             line=dict(color="#ef4444", width=1, dash="dash")))
    fig.add_trace(go.Scatter(x=distances, y=f_upper, mode="lines", name="Fresnel upper",
                             line=dict(color="#f59e0b", width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=distances, y=f_lower, mode="lines", name="Fresnel lower",
                             line=dict(color="#f59e0b", width=1, dash="dot"),
                             fill="tonexty", fillcolor="rgba(245,158,11,0.07)"))
    fig.update_layout(title=f"Terrain Profile -- Bearing {bearing_key} deg",
                      xaxis_title="Distance (km)", yaxis_title="Elevation (m)",
                      height=370, margin=dict(l=50, r=20, t=40, b=40),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="right", x=1),
                      xaxis=dict(gridcolor="rgba(200,200,200,0.3)"),
                      yaxis=dict(gridcolor="rgba(200,200,200,0.3)"))
    st.plotly_chart(fig, use_container_width=True, key="rfprop_terrain_profile")

def _render_folium_map(lat: float, lon: float, infra_elements: List[dict],
                       urban_elements: List[dict], coverage_km: float) -> None:
    """Folium map with infrastructure, clutter, and coverage ring."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Install folium and streamlit-folium for map visualisation.")
        return
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
    folium.CircleMarker(location=[lat, lon], radius=8, color="#ef4444",
                        fill=True, fill_opacity=0.9,
                        popup="TX / Analysis Centre").add_to(m)
    folium.Circle(location=[lat, lon], radius=int(coverage_km * 1000),
                  color="#22c55e", weight=2, dash_array="6 4",
                  fill=True, fill_opacity=0.04,
                  popup=f"Est. coverage: {coverage_km} km").add_to(m)
    for r_km in [5, 10]:
        folium.Circle(location=[lat, lon], radius=r_km * 1000, color="#94a3b8",
                      weight=1, dash_array="5 5", fill=False,
                      popup=f"{r_km} km").add_to(m)
    for el in infra_elements[:300]:
        tags = el.get("tags", {})
        popup = "<br>".join(f"{k}={v}" for k, v in list(tags.items())[:5]) or "tower"
        folium.CircleMarker(location=[el["lat"], el["lon"]], radius=5, color="#8b5cf6",
                            fill=True, fill_opacity=0.7,
                            popup=folium.Popup(popup, max_width=250)).add_to(m)
    for el in urban_elements[:200]:
        folium.CircleMarker(location=[el["lat"], el["lon"]], radius=3, color="#6366f1",
                            fill=True, fill_opacity=0.3, popup="building").add_to(m)
    st_folium(m, width=700, height=460, key="rfprop_map")

def _render_map_legend() -> None:
    items = [("#ef4444", "TX Centre"), ("#8b5cf6", "Tower/Antenna"),
             ("#6366f1", "Building"), ("#22c55e", "Coverage"), ("#94a3b8", "Ref Ring")]
    html = "<div style='display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px;'>"
    for clr, lbl in items:
        html += (f"<span style='display:inline-flex;align-items:center;gap:4px;'>"
                 f"<span style='width:12px;height:12px;border-radius:50%;"
                 f"background:{clr};display:inline-block;'></span>"
                 f"<span style='font-size:0.82rem;'>{lbl}</span></span>")
    st.markdown(html + "</div>", unsafe_allow_html=True)

def _render_score_table(dim_scores: Dict[str, int], details: Dict[str, str],
                        overall: float) -> None:
    hdr = "| Dimension | Detail | Score | Level |\n|---|---|---|---|\n"
    rows: List[str] = []
    for key, cfg in DIMENSION_CONFIG.items():
        s = dim_scores.get(key, 0)
        lbl, _ = _classify_signal(s)
        rows.append(f"| {cfg['name']} | {details.get(key, '--')} | {s}/10 | {lbl} |")
    lbl_o, _ = _classify_signal(overall)
    rows.append(f"| **Overall** | -- | **{overall:.1f}/10** | **{lbl_o}** |")
    st.markdown(hdr + "\n".join(rows))

def _generate_narrative(dim_scores: Dict[str, int], overall: float,
                        freq_label: str, coverage_km: float,
                        elev_data: Dict, weather_data: Dict,
                        infra_count: int, urban_count: int, veg_count: int) -> str:
    label, _ = _classify_signal(overall)
    p: List[str] = [
        f"**Overall RF Propagation Index: {overall:.1f}/10 -- {label}.**",
        f"Frequency band: **{freq_label}**. "
        f"Estimated coverage radius: **{coverage_km} km**.",
        f"Elevation: centre at **{elev_data.get('center', 0)} m**, "
        f"**{elev_data.get('advantage_m', 0)} m** above average surroundings.",
        f"Urban clutter: **{urban_count}** structures (3 km). "
        f"Vegetation: **{veg_count}** forest areas.",
        f"RF infrastructure: **{infra_count}** towers/antennas (10 km).",
        f"Weather: {weather_data.get('detail', 'N/A')}.",
        "", "**Recommendations:**"]
    if overall < 3:
        p += ["- Terrain severely limits propagation; consider satellite or high-gain antennas.",
              "- Deploy portable repeaters on elevated positions."]
    elif overall < 6:
        p += ["- Signal boosters or elevated masts could improve coverage.",
              "- Identify line-of-sight corridors to nearby infrastructure."]
    else:
        p += ["- Propagation conditions are favourable for standard equipment.",
              "- Multiple paths available; consider diversity reception."]
    return "\n\n".join(p)
# ── Main entry point ─────────────────────────────────────────────────────────

def render_radio_propagation_tab() -> None:
    """Render the Radio Propagation & RF Analysis tab."""
    st.markdown("## Radio Propagation & RF Analysis")
    st.caption("Estimate radio signal propagation based on terrain, elevation, "
               "obstacles, weather, and existing infrastructure. "
               "Uses FSPL model with environmental correction.")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f",
                          key="rfprop_lat", min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f",
                          key="rfprop_lon", min_value=-180.0, max_value=180.0)
    c3, c4 = st.columns(2)
    freq_label = c3.selectbox("Frequency Band", list(FREQ_BANDS.keys()),
                              index=1, key="rfprop_freq")
    freq_mhz = FREQ_BANDS[freq_label]
    profile_bearing = c4.selectbox(
        "Terrain Profile Bearing",
        [f"{int(i * 360 / NUM_RADIALS)}" for i in range(NUM_RADIALS)],
        index=0, key="rfprop_bearing",
        help="Compass bearing (degrees) for the terrain profile display.")

    if not st.button("Analyse RF Propagation", key="rfprop_btn"):
        st.info("Enter coordinates, select a frequency band, and press "
                "**Analyse RF Propagation** to begin.")
        return

    # ── Fetch all six dimensions ──────────────────────────────────────
    progress = st.progress(0, text="Fetching elevation grid...")
    elev_data = fetch_elevation_grid(lat, lon)
    progress.progress(15, text="Computing radial terrain profiles...")
    radial_data = fetch_radial_profiles(lat, lon, MAX_PROFILE_KM, NUM_RADIALS, PROFILE_SAMPLES)
    progress.progress(35, text="Scanning urban clutter...")
    urban_data = fetch_urban_clutter(lat, lon)
    progress.progress(50, text="Analysing vegetation attenuation...")
    veg_data = fetch_vegetation(lat, lon)
    progress.progress(65, text="Fetching weather conditions...")
    weather_data = fetch_weather_impact(lat, lon)
    progress.progress(80, text="Scanning RF infrastructure...")
    infra_data = fetch_rf_infrastructure(lat, lon)
    progress.progress(100, text="Analysis complete.")

    # ── Collect scores ────────────────────────────────────────────────
    dim_scores: Dict[str, int] = {
        "elevation_advantage": elev_data["score"],
        "terrain_obstruction": radial_data["score"],
        "urban_clutter":       urban_data["score"],
        "vegetation_attenuation": veg_data["score"],
        "weather_impact":      weather_data["score"],
        "infrastructure":      infra_data["score"],
    }
    overall = _compute_overall(dim_scores)
    coverage_km = _estimate_coverage_radius(freq_mhz, overall)

    # ── Overall gauge ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### RF Propagation Index")
    _render_overall_gauge(overall)

    # ── Coverage metrics ──────────────────────────────────────────────
    st.markdown("---")
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Frequency", freq_label)
    mc2.metric("Est. Coverage Radius", f"{coverage_km} km")
    mc3.metric("FSPL at Edge", f"{_fspl_db(coverage_km, freq_mhz):.1f} dB")

    # ── Dimension cards (2 cols x 3 rows) ─────────────────────────────
    st.markdown("---")
    st.markdown("### Dimension Breakdown")
    detail_maps: Dict[str, Dict[str, Any]] = {
        "elevation_advantage":    {"Centre": f"{elev_data['center']}m",
                                   "Advantage": f"{elev_data['advantage_m']}m",
                                   "Range": f"{elev_data['min']}-{elev_data['max']}m"},
        "terrain_obstruction":    {"Clearance": f"{radial_data['avg_clearance_pct']}%",
                                   "Radials": NUM_RADIALS, "Dist": f"{MAX_PROFILE_KM}km"},
        "urban_clutter":          {"Structures": urban_data["count"], "Radius": "3 km"},
        "vegetation_attenuation": {"Forests": veg_data["count"], "Radius": "3 km"},
        "weather_impact":         {"Rain": f"{weather_data['rain_mm']}mm",
                                   "Humidity": f"{weather_data['humidity_pct']}%",
                                   "Cloud": f"{weather_data['cloud_pct']}%"},
        "infrastructure":         {"Towers": infra_data["count"], "Radius": "10 km"},
    }
    dim_keys = list(DIMENSION_CONFIG.keys())
    for rs in range(0, len(dim_keys), 2):
        ca, cb = st.columns(2)
        for ci, cw in enumerate([ca, cb]):
            ki = rs + ci
            if ki >= len(dim_keys):
                break
            dk = dim_keys[ki]
            cfg = DIMENSION_CONFIG[dk]
            with cw:
                _render_dimension_card(cfg["name"], dim_scores[dk],
                                       detail_maps.get(dk, {}), cfg["color"])

    # ── Score summary table ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Score Summary")
    summary_det: Dict[str, str] = {
        "elevation_advantage":    f"{elev_data['advantage_m']}m advantage",
        "terrain_obstruction":    f"{radial_data['avg_clearance_pct']}% clearance",
        "urban_clutter":          f"{urban_data['count']} structures",
        "vegetation_attenuation": f"{veg_data['count']} forest areas",
        "weather_impact":         weather_data["detail"],
        "infrastructure":         f"{infra_data['count']} towers",
    }
    _render_score_table(dim_scores, summary_det, overall)

    # ── Radar chart ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### RF Propagation Radar")
    _render_radar_chart(dim_scores)

    # ── Signal strength heatmap ───────────────────────────────────────
    st.markdown("---")
    st.markdown("### Signal Strength Heatmap")
    _render_signal_heatmap(lat, lon, freq_mhz, overall)

    # ── Path loss chart ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Free-Space Path Loss vs Distance")
    _render_path_loss_chart(freq_mhz, freq_label)

    # ── Terrain profile with Fresnel zone ─────────────────────────────
    st.markdown("---")
    st.markdown("### Terrain Profile with Fresnel Zone")
    _render_terrain_profile(radial_data.get("profiles", {}), freq_mhz, profile_bearing)

    # ── Folium map ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### RF Infrastructure Map")
    _render_map_legend()
    infra_els = infra_data.get("elements", [])
    urban_els = urban_data.get("elements", [])
    if infra_els or urban_els:
        _render_folium_map(lat, lon, infra_els, urban_els, coverage_km)
    else:
        st.warning("No infrastructure elements found to display on the map.")

    # ── Narrative report ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Analysis Report")
    st.markdown(_generate_narrative(
        dim_scores, overall, freq_label, coverage_km, elev_data, weather_data,
        infra_data["count"], urban_data["count"], veg_data["count"]))

    # ── Raw data expander ─────────────────────────────────────────────
    with st.expander("Raw Data", expanded=False):
        st.json({
            "coordinates": {"lat": lat, "lon": lon},
            "frequency": {"label": freq_label, "mhz": freq_mhz},
            "overall_score": overall, "coverage_radius_km": coverage_km,
            "dimension_scores": dim_scores,
            "elevation": {"center_m": elev_data["center"],
                          "advantage_m": elev_data["advantage_m"],
                          "mean_m": elev_data["mean"],
                          "min_m": elev_data["min"], "max_m": elev_data["max"]},
            "terrain_obstruction": {
                "avg_clearance_pct": radial_data["avg_clearance_pct"],
                "per_radial": radial_data["clearance_scores"]},
            "urban_clutter_count": urban_data["count"],
            "vegetation_count": veg_data["count"],
            "weather": {"rain_mm": weather_data["rain_mm"],
                        "humidity_pct": weather_data["humidity_pct"],
                        "cloud_pct": weather_data["cloud_pct"],
                        "temp_c": weather_data["temp_c"]},
            "infrastructure_count": infra_data["count"],
        })
