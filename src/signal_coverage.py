"""
Signal & Communications Coverage -- TerraScout AI module.

Analyses radio, cell, and communications infrastructure around a point
across six dimensions: cell tower density, radio infrastructure, internet
infrastructure, emergency communications, terrain impact on signal, and
satellite visibility.

Uses: Overpass API, Open Topo Data.  Part of TerraScout AI.
"""

import logging
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

SIGNAL_LEVELS = [
    (9, 10, "EXCELLENT", "#10b981"),
    (7, 8, "GOOD", "#22c55e"),
    (5, 6, "FAIR", "#f59e0b"),
    (3, 4, "POOR", "#f97316"),
    (0, 2, "DEAD ZONE", "#ef4444"),
]

DIMENSION_CONFIG: Dict[str, Dict[str, Any]] = {
    "cell_towers":          {"name": "Cell Tower Density",       "color": "#3b82f6", "weight": 0.25},
    "radio_infra":          {"name": "Radio Infrastructure",     "color": "#8b5cf6", "weight": 0.20},
    "internet_infra":       {"name": "Internet Infrastructure",  "color": "#06b6d4", "weight": 0.15},
    "emergency_comms":      {"name": "Emergency Communications", "color": "#ef4444", "weight": 0.15},
    "terrain_impact":       {"name": "Terrain Impact on Signal", "color": "#f59e0b", "weight": 0.15},
    "satellite_visibility": {"name": "Satellite Visibility",     "color": "#6366f1", "weight": 0.10},
}

CELL_TOWER_THRESHOLDS   = [0, 1, 3, 6, 10, 16, 24, 35, 50, 70, 100]
RADIO_THRESHOLDS        = [0, 1, 2, 4, 7, 11, 16, 22, 30, 40, 55]
INTERNET_THRESHOLDS     = [0, 1, 2, 3, 5, 8, 12, 18, 25, 35, 50]
EMERGENCY_THRESHOLDS    = [0, 1, 2, 3, 5, 7, 10, 14, 19, 25, 35]
# Lower std-dev => flatter => better signal propagation
TERRAIN_ROUGHNESS_THRESHOLDS = [200, 160, 130, 100, 75, 55, 40, 28, 18, 10, 0]

# ── Helpers ────────────────────────────────────────────────────────────────

def _classify_signal(score: float) -> Tuple[str, str]:
    """Return (label, hex-colour) for a score 0-10."""
    s = int(round(score))
    for lo, hi, label, colour in SIGNAL_LEVELS:
        if lo <= s <= hi:
            return label, colour
    return "UNKNOWN", "#6b7280"


def _score_from_count(count: int, thresholds: List[int]) -> int:
    """Map a raw count to 0-10 using threshold list."""
    for idx, t in enumerate(thresholds):
        if count <= t:
            return idx
    return 10


def _score_terrain_roughness(std_dev: float) -> int:
    """Map terrain roughness (std-dev m) to 0-10.  Flat = 10, rugged = 0."""
    for idx, t in enumerate(TERRAIN_ROUGHNESS_THRESHOLDS):
        if std_dev >= t:
            return idx
    return 10

# ── Overpass query runner ──────────────────────────────────────────────────

@st.cache_data(ttl=900)
def _run_overpass_query(query_body: str) -> Optional[dict]:
    """Execute an Overpass QL query and return JSON."""
    full = f"[out:json][timeout:25];({query_body});out body;>;out skel qt;"
    try:
        resp = requests.post(OVERPASS_URL, data={"data": full}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return None

def _dedup_nodes(data: Optional[dict], nodes_only: bool = True) -> Dict[int, dict]:
    """Deduplicate Overpass elements by id."""
    if not data:
        return {}
    elements = data.get("elements", [])
    if nodes_only:
        return {e["id"]: e for e in elements if e.get("type") == "node"}
    return {e["id"]: e for e in elements}

# ── Dimension 1: Cell Tower Density ───────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_cell_towers(lat: float, lon: float) -> Dict[str, Any]:
    """Count cell / telecom towers within 10 km."""
    query = (
        f'node["tower:type"~"communication|telecommunication"](around:10000,{lat},{lon});'
        f'node["man_made"="mast"](around:10000,{lat},{lon});'
        f'node["man_made"="tower"]["tower:type"="communication"](around:10000,{lat},{lon});'
    )
    unique = _dedup_nodes(_run_overpass_query(query))
    return {"count": len(unique), "score": _score_from_count(len(unique), CELL_TOWER_THRESHOLDS),
            "elements": list(unique.values())}

# ── Dimension 2: Radio Infrastructure ─────────────────────────────────────

@st.cache_data(ttl=900)
def fetch_radio_infrastructure(lat: float, lon: float) -> Dict[str, Any]:
    """Count radio / broadcast antennas within 10 km."""
    query = (
        f'node["man_made"="antenna"](around:10000,{lat},{lon});'
        f'node["tower:type"="broadcast"](around:10000,{lat},{lon});'
    )
    unique = _dedup_nodes(_run_overpass_query(query))
    return {"count": len(unique), "score": _score_from_count(len(unique), RADIO_THRESHOLDS),
            "elements": list(unique.values())}

# ── Dimension 3: Internet Infrastructure ──────────────────────────────────

@st.cache_data(ttl=900)
def fetch_internet_infrastructure(lat: float, lon: float) -> Dict[str, Any]:
    """Count telecom / internet facilities within 20 km."""
    query = (
        f'node["telecom"](around:20000,{lat},{lon});'
        f'way["building"="data_centre"](around:20000,{lat},{lon});'
        f'node["man_made"="telephone_exchange"](around:20000,{lat},{lon});'
    )
    unique = _dedup_nodes(_run_overpass_query(query), nodes_only=False)
    return {"count": len(unique), "score": _score_from_count(len(unique), INTERNET_THRESHOLDS),
            "elements": list(unique.values())}

# ── Dimension 4: Emergency Communications ─────────────────────────────────

@st.cache_data(ttl=900)
def fetch_emergency_comms(lat: float, lon: float) -> Dict[str, Any]:
    """Count police, fire stations and sirens."""
    query = (
        f'node["amenity"~"police|fire_station"](around:10000,{lat},{lon});'
        f'node["emergency"="siren"](around:5000,{lat},{lon});'
    )
    unique = _dedup_nodes(_run_overpass_query(query), nodes_only=False)
    return {"count": len(unique), "score": _score_from_count(len(unique), EMERGENCY_THRESHOLDS),
            "elements": list(unique.values())}

# ── Dimension 5: Terrain Impact on Signal ─────────────────────────────────

def _build_elevation_grid(lat: float, lon: float, n: int = 5,
                          spacing_km: float = 2.0) -> List[Tuple[float, float]]:
    """Create an NxN grid of lat/lon points centred on (lat, lon)."""
    pts: List[Tuple[float, float]] = []
    d_lat = spacing_km / 111.0
    d_lon = spacing_km / (111.0 * math.cos(math.radians(lat)))
    half = n // 2
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            pts.append((round(lat + i * d_lat, 6), round(lon + j * d_lon, 6)))
    return pts

@st.cache_data(ttl=900)
def fetch_terrain_roughness(lat: float, lon: float) -> Dict[str, Any]:
    """Compute terrain roughness from a grid of elevation samples."""
    grid = _build_elevation_grid(lat, lon, n=5, spacing_km=2.0)
    loc_str = "|".join(f"{p[0]},{p[1]}" for p in grid)
    default = {"elevations": [], "std_dev": 0.0, "mean_elev": 0.0,
               "min_elev": 0.0, "max_elev": 0.0, "score": 5}
    try:
        resp = requests.get(OPEN_TOPO_API, params={"locations": loc_str}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open Topo Data request failed: %s", exc)
        return default

    elevations = [float(r["elevation"]) for r in data.get("results", [])
                  if r.get("elevation") is not None]
    if len(elevations) < 3:
        return default

    sd = statistics.stdev(elevations)
    mn = statistics.mean(elevations)
    return {"elevations": elevations, "std_dev": round(sd, 1),
            "mean_elev": round(mn, 1), "min_elev": round(min(elevations), 1),
            "max_elev": round(max(elevations), 1),
            "score": _score_terrain_roughness(sd)}

# ── Dimension 6: Satellite Visibility ─────────────────────────────────────

@st.cache_data(ttl=900)
def compute_satellite_visibility(lat: float, lon: float,
                                 terrain_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Estimate satellite visibility from elevation and terrain roughness."""
    if terrain_data is None:
        terrain_data = fetch_terrain_roughness(lat, lon)

    mean_elev = terrain_data.get("mean_elev", 0.0)
    std_dev = terrain_data.get("std_dev", 0.0)
    max_elev = terrain_data.get("max_elev", 0.0)
    min_elev = terrain_data.get("min_elev", 0.0)

    # Elevation bonus
    if mean_elev > 3000:     elev_f = 1.0
    elif mean_elev > 1500:   elev_f = 0.85
    elif mean_elev > 500:    elev_f = 0.7
    elif mean_elev > 100:    elev_f = 0.55
    else:                    elev_f = 0.4

    # Terrain penalty
    if std_dev < 10:         terr_f = 1.0
    elif std_dev < 30:       terr_f = 0.85
    elif std_dev < 60:       terr_f = 0.65
    elif std_dev < 120:      terr_f = 0.45
    else:                    terr_f = 0.25

    # Open-sky estimation
    relief = max_elev - min_elev
    if relief < 20:          mask_deg = 2
    elif relief < 100:       mask_deg = 8
    elif relief < 300:       mask_deg = 18
    else:                    mask_deg = 30

    open_sky = max(0.0, min(100.0, 100.0 * (1.0 - mask_deg / 90.0)))
    score = max(0, min(10, int(round((0.45 * elev_f + 0.55 * terr_f) * 10))))

    return {"score": score, "open_sky_pct": round(open_sky, 1),
            "horizon_mask_deg": mask_deg, "mean_elevation_m": mean_elev,
            "elev_factor": round(elev_f, 2), "terrain_factor": round(terr_f, 2)}

# ── Aggregate scoring ─────────────────────────────────────────────────────

def compute_overall_score(dim_scores: Dict[str, int]) -> float:
    """Weighted average across all six dimensions."""
    ws = sum(dim_scores.get(k, 0) * c["weight"] for k, c in DIMENSION_CONFIG.items())
    tw = sum(c["weight"] for c in DIMENSION_CONFIG.values())
    return round(ws / tw, 1) if tw else 0.0

# ── UI: signal bars ───────────────────────────────────────────────────────

def _render_signal_bars(score: int, label: str, colour: str) -> None:
    """Draw a phone-signal-style bar visualisation."""
    bars = ""
    for i in range(1, 6):
        h = 8 + i * 7
        c = colour if score >= i * 2 else "#e5e7eb"
        bars += (f'<div style="width:12px;height:{h}px;background:{c};'
                 f'border-radius:2px;margin-right:3px;display:inline-block;'
                 f'vertical-align:bottom;"></div>')
    st.markdown(
        f'<div style="display:flex;align-items:flex-end;margin-bottom:4px;">{bars}'
        f'<span style="margin-left:8px;font-weight:700;color:{colour};">'
        f'{score}/10 &ndash; {label}</span></div>',
        unsafe_allow_html=True)


def _render_dimension_card(title: str, score: int, details: Dict[str, Any],
                           colour: str) -> None:
    """Render a compact card for one dimension."""
    label, lbl_c = _classify_signal(score)
    st.markdown(
        f"<div style='border-left:4px solid {colour};padding:8px 12px;"
        f"margin-bottom:10px;border-radius:4px;background:rgba(0,0,0,0.02);'>"
        f"<strong>{title}</strong></div>", unsafe_allow_html=True)
    _render_signal_bars(score, label, lbl_c)
    items = [f"**{k.replace('_',' ').title()}:** {v}" for k, v in details.items()]
    if items:
        st.caption(" | ".join(items))

# ── UI: radar chart ───────────────────────────────────────────────────────

def _render_radar_chart(dim_scores: Dict[str, int]) -> None:
    """Plotly radar chart of the six dimensions."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("Install plotly for radar chart visualisation.")
        return

    cats = [c["name"] for c in DIMENSION_CONFIG.values()]
    vals = [dim_scores.get(k, 0) for k in DIMENSION_CONFIG]
    cats.append(cats[0]); vals.append(vals[0])  # noqa: E702

    fig = go.Figure(data=[go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=6), name="Signal Coverage")])
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0, 10],
                                   tickfont=dict(size=10))),
        showlegend=False, margin=dict(l=60, r=60, t=30, b=30),
        height=370, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, key="sigcov_radar")

# ── UI: folium map ────────────────────────────────────────────────────────

_COLOUR_MAP = {
    "communication": "#3b82f6", "telecommunication": "#3b82f6",
    "mast": "#3b82f6", "antenna": "#8b5cf6", "broadcast": "#8b5cf6",
    "telecom": "#06b6d4", "data_centre": "#06b6d4",
    "telephone_exchange": "#06b6d4", "police": "#ef4444",
    "fire_station": "#ef4444", "siren": "#f97316",
}

def _render_coverage_map(lat: float, lon: float,
                         all_elements: List[Dict]) -> None:
    """Folium map showing tower/infrastructure locations colour-coded."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Install folium and streamlit-folium for map visualisation.")
        return

    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
    folium.CircleMarker(location=[lat, lon], radius=8, color="#ef4444",
                        fill=True, fill_opacity=0.9,
                        popup="Analysis Centre").add_to(m)

    placed = 0
    for el in all_elements:
        el_lat, el_lon = el.get("lat"), el.get("lon")
        if el_lat is None or el_lon is None:
            continue
        tags = el.get("tags", {})
        clr = "#6b7280"
        for tv in [tags.get("tower:type", ""), tags.get("man_made", ""),
                   tags.get("amenity", ""), tags.get("emergency", ""),
                   tags.get("building", ""), tags.get("telecom", "")]:
            if tv in _COLOUR_MAP:
                clr = _COLOUR_MAP[tv]; break  # noqa: E702
        popup_txt = "<br>".join(f"{k}={v}" for k, v in list(tags.items())[:6]) or "node"
        folium.CircleMarker(
            location=[el_lat, el_lon], radius=5, color=clr,
            fill=True, fill_opacity=0.7,
            popup=folium.Popup(popup_txt, max_width=250)).add_to(m)
        placed += 1
        if placed >= 500:
            break

    for radius, lbl in [(5000, "5 km"), (10000, "10 km")]:
        folium.Circle(location=[lat, lon], radius=radius, color="#94a3b8",
                      weight=1, dash_array="5 5", fill=False, popup=lbl).add_to(m)
    st_folium(m, width=700, height=450, key="sigcov_map")

# ── UI: overall gauge ─────────────────────────────────────────────────────

def _render_overall_gauge(overall: float) -> None:
    """Large visual gauge for the overall Signal Coverage Index."""
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
        f"margin-top:4px;font-size:1.05rem;'>{label}</p>",
        unsafe_allow_html=True)

# ── Narrative report ──────────────────────────────────────────────────────

def _generate_narrative(dim_scores: Dict[str, int], overall: float,
                        terrain_data: Dict, sat_data: Dict,
                        counts: Dict[str, int]) -> str:
    """Return a concise human-readable narrative of findings."""
    label, _ = _classify_signal(overall)
    p: List[str] = [f"**Overall Signal Coverage Index: {overall:.1f}/10 -- {label}.**"]

    p.append(f"Cell infrastructure: **{counts.get('cell_towers', 0)}** "
             f"towers/masts detected within 10 km.")
    p.append(f"Radio/broadcast infrastructure: **{counts.get('radio_infra', 0)}** "
             f"antennas or broadcast towers.")
    p.append(f"Internet infrastructure: **{counts.get('internet_infra', 0)}** "
             f"telecom nodes, exchanges, or data centres within 20 km.")
    p.append(f"Emergency communications: **{counts.get('emergency_comms', 0)}** "
             f"police/fire stations and sirens.")

    std = terrain_data.get("std_dev", 0)
    if std < 15:     topo = "flat terrain favourable for signal propagation"
    elif std < 50:   topo = "moderate terrain variation may partially obstruct signals"
    else:            topo = "rugged terrain likely causes significant signal degradation"
    p.append(f"Terrain roughness: std-dev **{std} m** -- {topo}.")

    sky = sat_data.get("open_sky_pct", 0)
    p.append(f"Estimated open-sky percentage: **{sky}%** "
             f"(horizon mask ~{sat_data.get('horizon_mask_deg', 0)} deg).")

    p.append("")
    p.append("**Recommendations:**")
    if overall < 3:
        p.append("- Consider satellite communication (e.g. Starlink, Iridium) "
                 "as terrestrial coverage is minimal.")
        p.append("- Deploy portable repeaters if operations require connectivity.")
    elif overall < 6:
        p.append("- Signal boosters or directional antennas could improve reception.")
        p.append("- Identify line-of-sight to nearest towers for optimal placement.")
    else:
        p.append("- Standard devices should achieve reliable connectivity.")
        p.append("- Multiple redundant paths available for critical communications.")
    return "\n\n".join(p)

# ── Map legend ─────────────────────────────────────────────────────────────

def _render_map_legend() -> None:
    """Colour legend for the map markers."""
    items = [("#3b82f6", "Cell / Telecom Tower"), ("#8b5cf6", "Radio / Broadcast Antenna"),
             ("#06b6d4", "Internet / Telecom Node"), ("#ef4444", "Emergency Station"),
             ("#f97316", "Emergency Siren"), ("#ef4444", "Analysis Centre")]
    html = "<div style='display:flex;flex-wrap:wrap;gap:12px;'>"
    for clr, lbl in items:
        html += (f"<span style='display:inline-flex;align-items:center;gap:4px;'>"
                 f"<span style='width:12px;height:12px;border-radius:50%;"
                 f"background:{clr};display:inline-block;'></span>"
                 f"<span style='font-size:0.82rem;'>{lbl}</span></span>")
    st.markdown(html + "</div>", unsafe_allow_html=True)

# ── Score summary table ───────────────────────────────────────────────────

def _render_score_table(dim_scores: Dict[str, int], counts: Dict[str, Any],
                        overall: float) -> None:
    """Render a compact score summary table."""
    hdr = "| Dimension | Raw Count | Score | Level |\n|---|---|---|---|\n"
    rows = []
    for key, cfg in DIMENSION_CONFIG.items():
        s = dim_scores.get(key, 0)
        lbl, _ = _classify_signal(s)
        rows.append(f"| {cfg['name']} | {counts.get(key, '--')} | {s}/10 | {lbl} |")
    lbl_o, _ = _classify_signal(overall)
    rows.append(f"| **Overall** | -- | **{overall:.1f}/10** | **{lbl_o}** |")
    st.markdown(hdr + "\n".join(rows))

# ── Main entry point ──────────────────────────────────────────────────────

def render_signal_coverage_tab() -> None:
    """Render the Signal & Communications Coverage analysis tab."""
    st.markdown("## Signal & Communications Coverage")
    st.caption("Cell, radio, internet & emergency communications infrastructure "
               "analysis with terrain and satellite visibility assessment.")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f",
                          key="sigcov_lat", min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f",
                          key="sigcov_lon", min_value=-180.0, max_value=180.0)

    if not st.button("Scan Coverage", key="sigcov_btn"):
        st.info("Enter coordinates and press **Scan Coverage** to analyse "
                "signal and communications infrastructure.")
        return

    # ── Fetch all dimensions ──────────────────────────────────────────
    progress = st.progress(0, text="Scanning cell towers...")
    cell_data = fetch_cell_towers(lat, lon)
    progress.progress(15, text="Scanning radio infrastructure...")
    radio_data = fetch_radio_infrastructure(lat, lon)
    progress.progress(30, text="Scanning internet infrastructure...")
    internet_data = fetch_internet_infrastructure(lat, lon)
    progress.progress(45, text="Scanning emergency communications...")
    emergency_data = fetch_emergency_comms(lat, lon)
    progress.progress(60, text="Analysing terrain impact...")
    terrain_data = fetch_terrain_roughness(lat, lon)
    progress.progress(80, text="Computing satellite visibility...")
    sat_data = compute_satellite_visibility(lat, lon, terrain_data)
    progress.progress(100, text="Analysis complete.")

    # ── Collect scores ────────────────────────────────────────────────
    dim_scores: Dict[str, int] = {
        "cell_towers": cell_data["score"],
        "radio_infra": radio_data["score"],
        "internet_infra": internet_data["score"],
        "emergency_comms": emergency_data["score"],
        "terrain_impact": terrain_data["score"],
        "satellite_visibility": sat_data["score"],
    }
    counts: Dict[str, Any] = {
        "cell_towers": cell_data["count"],
        "radio_infra": radio_data["count"],
        "internet_infra": internet_data["count"],
        "emergency_comms": emergency_data["count"],
        "terrain_impact": f"{terrain_data['std_dev']}m std",
        "satellite_visibility": f"{sat_data['open_sky_pct']}% sky",
    }
    overall = compute_overall_score(dim_scores)

    # ── Overall gauge ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Signal Coverage Index")
    _render_overall_gauge(overall)

    # ── Dimension cards (2 cols x 3 rows) ─────────────────────────────
    st.markdown("---")
    st.markdown("### Dimension Breakdown")
    dim_keys = list(DIMENSION_CONFIG.keys())
    detail_maps: Dict[str, Dict[str, Any]] = {
        "cell_towers":     {"Towers found": cell_data["count"], "Radius": "10 km"},
        "radio_infra":     {"Antennas found": radio_data["count"], "Radius": "10 km"},
        "internet_infra":  {"Facilities found": internet_data["count"], "Radius": "20 km"},
        "emergency_comms": {"Stations/sirens": emergency_data["count"], "Radius": "5-10 km"},
        "terrain_impact":  {"Std-dev": f"{terrain_data['std_dev']} m",
                            "Mean elev": f"{terrain_data['mean_elev']} m",
                            "Relief": (f"{terrain_data['max_elev'] - terrain_data['min_elev']:.0f} m"
                                       if terrain_data.get("max_elev") is not None else "--")},
        "satellite_visibility": {"Open sky": f"{sat_data['open_sky_pct']}%",
                                 "Horizon mask": f"{sat_data['horizon_mask_deg']} deg",
                                 "Elev factor": sat_data["elev_factor"]},
    }
    for row_start in range(0, len(dim_keys), 2):
        col_a, col_b = st.columns(2)
        for ci, cw in enumerate([col_a, col_b]):
            ki = row_start + ci
            if ki >= len(dim_keys):
                break
            dk = dim_keys[ki]
            cfg = DIMENSION_CONFIG[dk]
            with cw:
                _render_dimension_card(cfg["name"], dim_scores[dk],
                                       detail_maps.get(dk, {}), cfg["color"])

    # ── Score table ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Score Summary")
    _render_score_table(dim_scores, counts, overall)

    # ── Radar chart ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Coverage Radar")
    _render_radar_chart(dim_scores)

    # ── Folium map ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Infrastructure Map")
    _render_map_legend()
    all_elements: List[Dict] = []
    for d in [cell_data, radio_data, internet_data, emergency_data]:
        all_elements.extend(d.get("elements", []))
    if all_elements:
        _render_coverage_map(lat, lon, all_elements)
    else:
        st.warning("No infrastructure elements found to display on the map.")

    # ── Narrative report ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Analysis Report")
    st.markdown(_generate_narrative(
        dim_scores, overall, terrain_data, sat_data,
        {"cell_towers": cell_data["count"], "radio_infra": radio_data["count"],
         "internet_infra": internet_data["count"],
         "emergency_comms": emergency_data["count"]}))

    # ── Raw data expander ─────────────────────────────────────────────
    with st.expander("Raw Data", expanded=False):
        st.json({
            "coordinates": {"lat": lat, "lon": lon},
            "overall_score": overall,
            "dimension_scores": dim_scores,
            "counts": counts,
            "terrain": {"std_dev_m": terrain_data["std_dev"],
                        "mean_elevation_m": terrain_data["mean_elev"],
                        "min_elevation_m": terrain_data["min_elev"],
                        "max_elevation_m": terrain_data["max_elev"],
                        "num_samples": len(terrain_data.get("elevations", []))},
            "satellite": {"open_sky_pct": sat_data["open_sky_pct"],
                          "horizon_mask_deg": sat_data["horizon_mask_deg"],
                          "elev_factor": sat_data["elev_factor"],
                          "terrain_factor": sat_data["terrain_factor"]},
            "infrastructure_elements_total": len(all_elements),
        })
