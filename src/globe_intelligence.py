"""
globe_intelligence.py — 10th page: Global Situational Awareness.

3D Interactive Intelligence Globe with real-time global events from 7 APIs.
Provides filtering, event details, AI analysis, threat dashboard, live ticker,
regional analysis, source reliability, cascading risk network, temporal heatmap,
enhanced intelligence summaries, and data quality panels.
"""

import html as html_module
import logging
import math
from datetime import datetime, timezone, timedelta
from collections import Counter

import streamlit as st

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

try:
    from src.global_events_api import fetch_all_global_events
    HAS_EVENTS_API = True
except ImportError:
    HAS_EVENTS_API = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

_GREEN = "#00ff88"
_CYAN = "#00f0ff"
_AMBER = "#ffaa00"
_RED = "#ff3344"
_VIOLET = "#aa55ff"
_PINK = "#ff66aa"
_DIM = "#8b97b0"
_TEXT = "#e0e6ed"
_BG = "#0a0e14"
_CARD_BG = "#0d1117"
_CRIMSON = "#dc143c"

CATEGORY_COLORS = {
    "DISASTER": "#ff3344",
    "EARTHQUAKE": "#ffaa00",
    "FIRE": "#ff8800",
    "CONFLICT": "#aa55ff",
    "HEALTH": "#00f0ff",
    "WEATHER": "#4488ff",
    "HUMANITARIAN": "#ff66aa",
    "NEWS": "#8b97b0",
}

CATEGORY_SYMBOLS = {
    "DISASTER": "triangle-up",
    "EARTHQUAKE": "diamond",
    "FIRE": "star-triangle-up",
    "CONFLICT": "x",
    "HEALTH": "cross",
    "WEATHER": "circle",
    "HUMANITARIAN": "square",
    "NEWS": "circle-open",
}

CATEGORY_ICONS = {
    "DISASTER": "&#x1F30A;",
    "EARTHQUAKE": "&#x1F30B;",
    "FIRE": "&#x1F525;",
    "CONFLICT": "&#x2694;&#xFE0F;",
    "HEALTH": "&#x1F3E5;",
    "WEATHER": "&#x26C8;&#xFE0F;",
    "HUMANITARIAN": "&#x1F6D1;",
    "NEWS": "&#x1F4F0;",
}

REGION_BOUNDS = {
    "Global": (-90, 90, -180, 180),
    "Americas": (-60, 80, -170, -25),
    "Europe": (34, 75, -25, 60),
    "Africa": (-35, 37, -20, 52),
    "Asia": (-10, 70, 55, 180),
    "Oceania": (-50, 10, 100, 180),
    "Middle East": (12, 42, 25, 63),
}

SEVERITY_COLORS = {
    "CRITICAL": "#ff0033",
    "HIGH": "#ff3344",
    "ELEVATED": "#ffaa00",
    "MODERATE": "#00f0ff",
    "LOW": "#00ff88",
}

# Cascading risk scenarios for cross-category event proximity
_CASCADE_SCENARIOS = {
    ("EARTHQUAKE", "HUMANITARIAN"): "Infrastructure collapse amplifies aid disruption; supply routes compromised",
    ("EARTHQUAKE", "HEALTH"): "Structural damage to medical facilities; potential disease outbreak from displacement",
    ("EARTHQUAKE", "FIRE"): "Seismic rupture of gas lines triggers secondary fires; overwhelmed response",
    ("DISASTER", "HUMANITARIAN"): "Natural disaster compounds humanitarian crisis; resource diversion imminent",
    ("DISASTER", "HEALTH"): "Disaster-driven contamination creates public health emergency cascade",
    ("DISASTER", "CONFLICT"): "Resource scarcity from disaster accelerates civil unrest",
    ("FIRE", "HUMANITARIAN"): "Wildfire displacement merges with existing refugee corridors",
    ("FIRE", "HEALTH"): "Toxic smoke inhalation creates respiratory emergency in population centers",
    ("FIRE", "WEATHER"): "Weather pattern shifts fan fire spread; feedback loop established",
    ("CONFLICT", "HUMANITARIAN"): "Armed conflict blocks humanitarian corridors; aid delivery paralysis",
    ("CONFLICT", "HEALTH"): "Conflict zone prevents medical evacuation; epidemic risk escalates",
    ("CONFLICT", "DISASTER"): "Conflict impedes disaster response; cascading civilian casualties",
    ("HEALTH", "HUMANITARIAN"): "Disease outbreak in displaced population; containment capacity overwhelmed",
    ("WEATHER", "DISASTER"): "Severe weather triggers secondary disaster events; compound hazard chain",
    ("WEATHER", "FIRE"): "High winds and drought conditions accelerate fire propagation vectors",
    ("WEATHER", "HUMANITARIAN"): "Extreme weather displaces vulnerable populations; shelter crisis",
}

# Globe projection options
_GLOBE_PROJECTIONS = {
    "Orthographic": "orthographic",
    "Natural Earth": "natural earth",
    "Equirectangular": "equirectangular",
    "Mollweide": "mollweide",
}

# DEFCON-style threat levels
_DEFCON_LEVELS = {
    1: {"label": "DEFCON 1 — MAXIMUM READINESS", "color": _CRIMSON, "bg": "rgba(220,20,60,0.08)"},
    2: {"label": "DEFCON 2 — HIGH ALERT", "color": _RED, "bg": "rgba(255,51,68,0.08)"},
    3: {"label": "DEFCON 3 — ELEVATED THREAT", "color": "#ff8800", "bg": "rgba(255,136,0,0.08)"},
    4: {"label": "DEFCON 4 — ABOVE NORMAL", "color": _AMBER, "bg": "rgba(255,170,0,0.08)"},
    5: {"label": "DEFCON 5 — NORMAL OPERATIONS", "color": _GREEN, "bg": "rgba(0,255,136,0.08)"},
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371.0
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geodesic_points(lat1, lon1, lat2, lon2, n=20):
    """Generate n intermediate points along a great-circle (slerp) between two lat/lon points.
    Phase 2D: real geodesic interpolation instead of linear."""
    lat1r, lon1r = math.radians(lat1), math.radians(lon1)
    lat2r, lon2r = math.radians(lat2), math.radians(lon2)
    # Convert to Cartesian
    x1 = math.cos(lat1r) * math.cos(lon1r)
    y1 = math.cos(lat1r) * math.sin(lon1r)
    z1 = math.sin(lat1r)
    x2 = math.cos(lat2r) * math.cos(lon2r)
    y2 = math.cos(lat2r) * math.sin(lon2r)
    z2 = math.sin(lat2r)
    # Angular distance
    dot = max(-1.0, min(1.0, x1 * x2 + y1 * y2 + z1 * z2))
    omega = math.acos(dot)
    if omega < 1e-10:
        return [lat1] * (n + 1), [lon1] * (n + 1)
    sin_omega = math.sin(omega)
    lats, lons = [], []
    for i in range(n + 1):
        t = i / n
        a = math.sin((1 - t) * omega) / sin_omega
        b = math.sin(t * omega) / sin_omega
        x = a * x1 + b * x2
        y = a * y1 + b * y2
        z = a * z1 + b * z2
        lat_i = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
        lon_i = math.degrees(math.atan2(y, x))
        lats.append(lat_i)
        lons.append(lon_i)
    return lats, lons


def _get_nearby_events(target, events, radius_km=500):
    """Filter events within radius_km of target event."""
    nearby = []
    for ev in events:
        if ev["id"] == target["id"]:
            continue
        dist = _haversine(target["lat"], target["lon"], ev["lat"], ev["lon"])
        if dist <= radius_km:
            nearby.append((ev, dist))
    nearby.sort(key=lambda x: x[1])
    return nearby[:10]


def _estimate_region(lat, lon):
    """Map lat/lon to a human-readable region."""
    for region, (lat_min, lat_max, lon_min, lon_max) in REGION_BOUNDS.items():
        if region == "Global":
            continue
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return region
    return "Other"


def _severity_label(severity):
    """Map 0-1 severity to label."""
    if severity >= 0.8:
        return "CRITICAL", SEVERITY_COLORS["CRITICAL"]
    if severity >= 0.6:
        return "HIGH", SEVERITY_COLORS["HIGH"]
    if severity >= 0.4:
        return "ELEVATED", SEVERITY_COLORS["ELEVATED"]
    if severity >= 0.2:
        return "MODERATE", SEVERITY_COLORS["MODERATE"]
    return "LOW", SEVERITY_COLORS["LOW"]


def _filter_events(events, categories, severity_min, region):
    """Filter events by category, severity, and region."""
    filtered = []
    for ev in events:
        if ev["category"] not in categories:
            continue
        if ev["severity"] < severity_min:
            continue
        if region != "Global":
            bounds = REGION_BOUNDS.get(region)
            if bounds:
                lat_min, lat_max, lon_min, lon_max = bounds
                if not (lat_min <= ev["lat"] <= lat_max and lon_min <= ev["lon"] <= lon_max):
                    continue
        filtered.append(ev)
    return filtered


def _compute_defcon_level(events):
    """Compute DEFCON-style threat level (1-5) from event data."""
    if not events:
        return 5, 0.0, "STABLE"

    total = len(events)
    critical_count = sum(1 for ev in events if ev["severity"] >= 0.8)
    high_count = sum(1 for ev in events if 0.6 <= ev["severity"] < 0.8)
    categories_active = len(set(ev["category"] for ev in events))
    regions_active = len(set(_estimate_region(ev["lat"], ev["lon"]) for ev in events) - {"Other"})

    # Global risk score: 0-100
    risk_score = min(100.0, (
        (critical_count * 12.0) +
        (high_count * 5.0) +
        (total * 0.3) +
        (categories_active * 4.0) +
        (regions_active * 6.0)
    ))

    # DEFCON level from risk score
    if risk_score >= 80:
        defcon = 1
    elif risk_score >= 60:
        defcon = 2
    elif risk_score >= 40:
        defcon = 3
    elif risk_score >= 20:
        defcon = 4
    else:
        defcon = 5

    # Threat trend: use dedicated function with chronological sorting
    trend, _ = _compute_threat_trend(events)

    return defcon, risk_score, trend


def _compute_threat_trend(events):
    """Compute whether threat level is escalating, stable, or de-escalating."""
    if len(events) < 4:
        return "STABLE", 0.0
    # Sort by date for temporal analysis
    dated = []
    for ev in events:
        try:
            dt = datetime.fromisoformat(ev.get("date", "").replace("Z", "+00:00"))
            # Normalize to UTC-aware to avoid naive vs aware comparison
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dated.append((dt, ev["severity"]))
        except (ValueError, AttributeError, TypeError):
            continue
    if len(dated) < 4:
        return "STABLE", 0.0
    dated.sort(key=lambda x: x[0])
    mid = len(dated) // 2
    first_half_avg = sum(s for _, s in dated[:mid]) / mid
    second_half_avg = sum(s for _, s in dated[mid:]) / max(1, len(dated) - mid)
    delta = second_half_avg - first_half_avg
    if delta > 0.08:
        return "ESCALATING", delta
    elif delta < -0.08:
        return "DE-ESCALATING", delta
    return "STABLE", delta


def _parse_event_datetime(ev):
    """Try to parse event date string into a UTC-aware datetime. Return None on failure."""
    date_str = ev.get("date", "")
    if not date_str:
        return None
    dt = None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass
    if dt is None:
        # Try other common formats
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z"):
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except (ValueError, AttributeError):
                continue
    # Normalize to UTC-aware
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _time_ago(dt):
    """Return a human-readable 'time ago' string from a datetime."""
    if dt is None:
        return "unknown"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _dbscan_events(events, eps_km=100, min_samples=3, max_events=200):
    """Pure-Python DBSCAN clustering on events using haversine distance.
    Phase 2E: eps=100km, min_samples=3, cap at 200 events for O(n²) safety.
    Returns list of cluster dicts: {lat, lon, count, avg_severity, category, event_ids}."""
    evts = events[:max_events]
    n = len(evts)
    if n < min_samples:
        return []

    # Pre-compute labels: -1 = noise, 0+ = cluster id
    labels = [-1] * n
    cluster_id = 0

    visited = [False] * n

    def _region_query(idx):
        """Find all points within eps_km of idx."""
        neighbors = []
        for j in range(n):
            if j == idx:
                continue
            d = _haversine(evts[idx]["lat"], evts[idx]["lon"],
                           evts[j]["lat"], evts[j]["lon"])
            if d <= eps_km:
                neighbors.append(j)
        return neighbors

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = _region_query(i)
        if len(neighbors) < min_samples - 1:
            continue  # noise point

        # Expand cluster
        labels[i] = cluster_id
        seed_set = list(neighbors)
        si = 0
        while si < len(seed_set):
            q = seed_set[si]
            if not visited[q]:
                visited[q] = True
                q_neighbors = _region_query(q)
                if len(q_neighbors) >= min_samples - 1:
                    seed_set.extend(q_neighbors)
            if labels[q] == -1:
                labels[q] = cluster_id
            si += 1
        cluster_id += 1

    # Aggregate clusters
    clusters_map = {}
    for idx, lbl in enumerate(labels):
        if lbl < 0:
            continue
        if lbl not in clusters_map:
            clusters_map[lbl] = []
        clusters_map[lbl].append(evts[idx])

    clusters = []
    for cid, members in clusters_map.items():
        avg_lat = sum(e["lat"] for e in members) / len(members)
        avg_lon = sum(e["lon"] for e in members) / len(members)
        avg_sev = sum(e["severity"] for e in members) / len(members)
        cat_counts = Counter(e["category"] for e in members)
        dominant_cat = cat_counts.most_common(1)[0][0] if cat_counts else "NEWS"
        clusters.append({
            "id": cid,
            "lat": avg_lat,
            "lon": avg_lon,
            "count": len(members),
            "avg_severity": avg_sev,
            "category": dominant_cat,
            "event_ids": [e["id"] for e in members],
        })

    # Sort by count descending
    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters


def _render_cluster_summary(clusters):
    """Render top-5 cluster summary panel. Phase 2E."""
    if not clusters:
        st.markdown(
            f'<div style="color:{_DIM};font-size:0.75rem;padding:8px;">'
            f'No spatial clusters detected (minimum 3 events within 100km).</div>',
            unsafe_allow_html=True,
        )
        return

    rows_html = ""
    for ci, cl in enumerate(clusters[:5], 1):
        cat_color = CATEGORY_COLORS.get(cl["category"], _DIM)
        _, sev_color = _severity_label(cl["avg_severity"])
        rows_html += (
            f'<tr style="border-bottom:1px solid #1a1f2e;">'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_AMBER};text-align:center;'
            f'font-weight:700;">#{ci}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_TEXT};text-align:center;">'
            f'{cl["count"]}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{sev_color};text-align:center;'
            f'font-weight:700;">{cl["avg_severity"]:.2f}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{cat_color};text-align:center;'
            f'font-weight:600;">{html_module.escape(str(cl["category"]))}</td>'
            f'<td style="padding:5px 8px;font-size:0.68rem;color:{_DIM};text-align:center;">'
            f'{cl["lat"]:.1f}, {cl["lon"]:.1f}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;font-family:JetBrains Mono,monospace;">'
        f'<thead><tr style="border-bottom:2px solid {_CYAN}44;">'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};letter-spacing:0.5px;">#</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">EVENTS</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">AVG SEV</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">DOMINANT</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">CENTROID</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def _section_header(title, color=None):
    """Generate a styled section header HTML string."""
    c = color or _GREEN
    return (
        f'<div style="border-left:3px solid {c};padding:6px 14px;margin:1.2rem 0 0.5rem 0;'
        f'background:{c}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.85rem;'
        f'font-weight:700;color:{c};letter-spacing:1.5px;">{title}</span></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# VISUALIZATION BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def _build_globe_figure(events, center_lat=0, center_lon=0,
                        projection="orthographic", show_arcs=True,
                        show_impact_radius=True, auto_rotate=False,
                        clusters=None):
    """Build 3D globe with event markers, optional arcs, impact radii,
    auto-rotation animation, and cluster overlay."""
    if not HAS_PLOTLY:
        return None

    fig = go.Figure()

    # --- Impact radius circles for high-severity events ---
    if show_impact_radius:
        for ev in events:
            if ev["severity"] > 0.6:
                radius_deg = ev["severity"] * 3.0  # 0-3 degrees proportional
                n_pts = 36
                circle_lats = []
                circle_lons = []
                cos_lat = math.cos(math.radians(ev["lat"])) or 0.01  # avoid div by zero at poles
                for k in range(n_pts + 1):
                    angle = 2 * math.pi * k / n_pts
                    clat = ev["lat"] + radius_deg * math.sin(angle)
                    clon = ev["lon"] + (radius_deg * math.cos(angle)) / cos_lat
                    circle_lats.append(clat)
                    circle_lons.append(clon)
                cat_color = CATEGORY_COLORS.get(ev.get("category", "NEWS"), _DIM)
                fig.add_trace(go.Scattergeo(
                    lat=circle_lats,
                    lon=circle_lons,
                    mode="lines",
                    line=dict(width=1, color=cat_color),
                    opacity=0.2,
                    showlegend=False,
                    hoverinfo="skip",
                ))

    # --- Arc connections between same-category events within 2000km ---
    # Phase 2D: uses geodesic interpolation + thickness proportional to proximity
    if show_arcs:
        cat_events = {}
        for ev in events:
            cat = ev.get("category", "NEWS")
            if cat not in cat_events:
                cat_events[cat] = []
            cat_events[cat].append(ev)

        for cat, evs in cat_events.items():
            if len(evs) < 2:
                continue
            color = CATEGORY_COLORS.get(cat, _DIM)
            arc_count = 0
            for i in range(len(evs)):
                if arc_count >= 30:
                    break
                for j in range(i + 1, len(evs)):
                    if arc_count >= 30:
                        break
                    dist = _haversine(evs[i]["lat"], evs[i]["lon"],
                                      evs[j]["lat"], evs[j]["lon"])
                    if dist <= 2000:
                        # Phase 2D: geodesic arc + thickness proportional to proximity
                        arc_lats, arc_lons = _geodesic_points(
                            evs[i]["lat"], evs[i]["lon"],
                            evs[j]["lat"], evs[j]["lon"], n=20,
                        )
                        width = max(0.3, 2.0 * (1 - dist / 2000))
                        fig.add_trace(go.Scattergeo(
                            lat=arc_lats,
                            lon=arc_lons,
                            mode="lines",
                            line=dict(width=width, color=color),
                            opacity=0.15,
                            showlegend=False,
                            hoverinfo="skip",
                        ))
                        arc_count += 1

        # Phase 2D: Cross-category arcs (max 20)
        _cross_pairs = [
            ("EARTHQUAKE", "DISASTER"), ("FIRE", "DISASTER"),
            ("CONFLICT", "HUMANITARIAN"),
        ]
        cross_arc_count = 0
        check_evts = events[:80]  # limit for performance
        for i, ev1 in enumerate(check_evts):
            if cross_arc_count >= 20:
                break
            for j in range(i + 1, len(check_evts)):
                if cross_arc_count >= 20:
                    break
                ev2 = check_evts[j]
                pair = (ev1["category"], ev2["category"])
                rpair = (ev2["category"], ev1["category"])
                if pair not in _cross_pairs and rpair not in _cross_pairs:
                    continue
                dist = _haversine(ev1["lat"], ev1["lon"], ev2["lat"], ev2["lon"])
                if dist > 1500:
                    continue
                arc_lats, arc_lons = _geodesic_points(
                    ev1["lat"], ev1["lon"], ev2["lat"], ev2["lon"], n=15,
                )
                width = max(0.3, 1.5 * (1 - dist / 1500))
                fig.add_trace(go.Scattergeo(
                    lat=arc_lats, lon=arc_lons,
                    mode="lines",
                    line=dict(width=width, color=_AMBER, dash="dot"),
                    opacity=0.2,
                    showlegend=False,
                    hoverinfo="skip",
                ))
                cross_arc_count += 1

    # --- Event markers grouped by category ---
    cat_events_grouped = {}
    for ev in events:
        cat = ev.get("category", "NEWS")
        if cat not in cat_events_grouped:
            cat_events_grouped[cat] = []
        cat_events_grouped[cat].append(ev)

    for cat, evs in cat_events_grouped.items():
        color = CATEGORY_COLORS.get(cat, "#8b97b0")
        symbol = CATEGORY_SYMBOLS.get(cat, "circle")
        lats = [ev["lat"] for ev in evs]
        lons = [ev["lon"] for ev in evs]
        # Dramatic size range: min 4, max 30
        sizes = [max(4, min(30, ev["severity"] * 28 + 4)) for ev in evs]
        texts = [ev["title"][:60] for ev in evs]
        customdata = [
            [ev["title"], ev["description"], ev["date"],
             ev["category"], ev["severity"], ev["source"],
             ev["url"], ev["lat"], ev["lon"]]
            for ev in evs
        ]

        fig.add_trace(go.Scattergeo(
            lat=lats, lon=lons,
            text=texts,
            customdata=customdata,
            mode="markers",
            marker=dict(
                size=sizes,
                color=color,
                opacity=0.85,
                symbol=symbol,
                line=dict(width=1, color=color),
            ),
            name=cat,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Category: %{customdata[3]}<br>"
                "Date: %{customdata[2]}<br>"
                "Severity: %{customdata[4]:.2f}<br>"
                "Source: %{customdata[5]}"
                "<extra></extra>"
            ),
        ))

    fig.update_geos(
        projection_type=projection,
        projection_rotation=dict(lat=center_lat, lon=center_lon),
        showland=True, landcolor="#0a1a0a",
        showocean=True, oceancolor="#050520",
        showcoastlines=True, coastlinecolor="#00ff88", coastlinewidth=0.5,
        showlakes=False,
        showcountries=True, countrycolor="rgba(0,255,136,0.2)",
        bgcolor="#0a0e14",
    )

    # --- Phase 2A: Recent event indicator (<1h) — brighter + star overlay ---
    now_utc = datetime.now(timezone.utc)
    recent_lats, recent_lons, recent_texts = [], [], []
    for ev in events:
        ev_dt = _parse_event_datetime(ev)
        if ev_dt and (now_utc - ev_dt).total_seconds() < 3600:
            recent_lats.append(ev["lat"])
            recent_lons.append(ev["lon"])
            recent_texts.append(html_module.escape(str(ev["title"]))[:40])
    if recent_lats:
        fig.add_trace(go.Scattergeo(
            lat=recent_lats, lon=recent_lons,
            text=recent_texts,
            mode="markers",
            marker=dict(size=14, color="#ffffff", symbol="star",
                        opacity=0.9, line=dict(width=1, color="#ffff00")),
            name="Recent (<1h)",
            hovertemplate="<b>%{text}</b><br>RECENT EVENT<extra></extra>",
        ))

    # --- Phase 2E: Cluster overlay (golden markers with count) ---
    if clusters:
        cl_lats = [c["lat"] for c in clusters]
        cl_lons = [c["lon"] for c in clusters]
        cl_sizes = [max(16, min(40, c["count"] * 4)) for c in clusters]
        cl_texts = [f"Cluster: {c['count']} events" for c in clusters]
        fig.add_trace(go.Scattergeo(
            lat=cl_lats, lon=cl_lons,
            text=cl_texts,
            mode="markers+text",
            marker=dict(size=cl_sizes, color="#ffd700", symbol="diamond",
                        opacity=0.8, line=dict(width=1, color="#fff")),
            textfont=dict(size=8, color="#ffd700"),
            name="Clusters",
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))

    fig.update_layout(
        height=720,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="#0a0e14",
        plot_bgcolor="#0a0e14",
        legend=dict(
            font=dict(color="#e0e6ed", size=10, family="JetBrains Mono, monospace"),
            bgcolor="rgba(10,14,20,0.8)",
            bordercolor="rgba(0,255,136,0.2)",
            borderwidth=1,
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="center", x=0.5,
        ),
        title=dict(
            text="GLOBAL INTELLIGENCE GLOBE",
            font=dict(color="#00ff88", size=14, family="JetBrains Mono, monospace"),
            x=0.5,
        ),
    )

    # --- Phase 2A: Auto-rotate animation frames ---
    if auto_rotate and projection == "orthographic":
        frames = []
        for lon_step in range(0, 360, 5):
            frames.append(go.Frame(
                layout=dict(geo=dict(
                    projection_rotation=dict(lat=center_lat, lon=lon_step),
                )),
                name=str(lon_step),
            ))
        fig.frames = frames
        fig.update_layout(
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                y=0.0, x=0.05,
                xanchor="left", yanchor="bottom",
                buttons=[
                    dict(label="&#9654; Play",
                         method="animate",
                         args=[None, dict(
                             frame=dict(duration=200, redraw=True),
                             fromcurrent=True,
                             transition=dict(duration=100),
                         )]),
                    dict(label="&#9724; Stop",
                         method="animate",
                         args=[[None], dict(
                             frame=dict(duration=0, redraw=False),
                             mode="immediate",
                         )]),
                ],
                font=dict(size=10, color=_TEXT),
                bgcolor="rgba(10,14,20,0.7)",
                bordercolor="rgba(0,255,136,0.3)",
            )],
        )

    return fig


def _build_timeline_chart(events):
    """Scatter plot: events over time colored by category."""
    if not HAS_PLOTLY or not events:
        return None

    fig = go.Figure()

    cat_events = {}
    for ev in events:
        cat = ev.get("category", "NEWS")
        if cat not in cat_events:
            cat_events[cat] = []
        cat_events[cat].append(ev)

    for cat, evs in cat_events.items():
        color = CATEGORY_COLORS.get(cat, "#8b97b0")
        x_vals = []
        for i, ev in enumerate(evs):
            parsed = _parse_event_datetime(ev)
            if parsed is not None:
                x_vals.append(parsed)
            else:
                x_vals.append(i)

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=[ev["severity"] for ev in evs],
            mode="markers",
            marker=dict(
                size=[max(4, ev["severity"] * 18 + 4) for ev in evs],
                color=color, opacity=0.7,
                line=dict(width=1, color=color),
            ),
            text=[ev["title"][:40] for ev in evs],
            name=cat,
            hovertemplate="<b>%{text}</b><br>Severity: %{y:.2f}<extra></extra>",
        ))

    fig.update_layout(
        height=350,
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        margin=dict(l=40, r=10, t=40, b=40),
        title=dict(
            text="EVENT TIMELINE",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
        legend=dict(
            font=dict(color=_TEXT, size=9), bgcolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.02,
        ),
        xaxis=dict(gridcolor="#1a1f2e", color=_DIM),
        yaxis=dict(
            title="Severity", gridcolor="#1a1f2e", color=_DIM,
            range=[0, 1.05],
        ),
    )
    fig.update_xaxes(gridcolor="#1a1f2e")
    fig.update_yaxes(gridcolor="#1a1f2e")

    return fig


def _build_category_donut(events):
    """Donut chart showing event distribution by category."""
    if not HAS_PLOTLY or not events:
        return None

    counts = Counter(ev["category"] for ev in events)
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [CATEGORY_COLORS.get(c, "#8b97b0") for c in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0a0e14", width=2)),
        textinfo="label+percent",
        textfont=dict(size=10, color=_TEXT),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        height=350,
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(
            text="CATEGORY BREAKDOWN",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
        legend=dict(font=dict(color=_TEXT, size=9), bgcolor="rgba(0,0,0,0)"),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{len(events)}</b><br>Events",
            showarrow=False, font=dict(size=14, color=_GREEN),
        )],
    )

    return fig


def _build_density_map(events):
    """Density scatter showing event concentration hotspots."""
    if not HAS_PLOTLY or not events:
        return None

    lats = [ev["lat"] for ev in events]
    lons = [ev["lon"] for ev in events]
    severities = [ev["severity"] for ev in events]
    texts = [ev["title"][:40] for ev in events]

    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons,
        text=texts,
        mode="markers",
        marker=dict(
            size=[s * 12 + 3 for s in severities],
            color=severities,
            colorscale=[[0, "#050520"], [0.3, "#00f0ff"], [0.6, "#ffaa00"], [1.0, "#ff3344"]],
            opacity=0.5,
            colorbar=dict(
                title=dict(text="Severity", font=dict(color=_DIM, size=10)),
                tickfont=dict(color=_DIM, size=9),
            ),
        ),
        hovertemplate="<b>%{text}</b><br>Severity: %{marker.color:.2f}<extra></extra>",
    ))

    fig.update_geos(
        projection_type="natural earth",
        showland=True, landcolor="#0a1a0a",
        showocean=True, oceancolor="#050520",
        showcoastlines=True, coastlinecolor="rgba(0,255,136,0.27)",
        showcountries=True, countrycolor="rgba(0,255,136,0.13)",
        bgcolor="#0a0e14",
    )

    fig.update_layout(
        height=400,
        paper_bgcolor="#0a0e14", plot_bgcolor="#0a0e14",
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(
            text="GLOBAL EVENT DENSITY",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
    )

    return fig


def _build_regional_bar_chart(events):
    """Horizontal bar chart of events per region, colored by average severity."""
    if not HAS_PLOTLY or not events:
        return None

    region_data = {}
    for ev in events:
        region = _estimate_region(ev["lat"], ev["lon"])
        if region not in region_data:
            region_data[region] = {"count": 0, "severity_sum": 0.0}
        region_data[region]["count"] += 1
        region_data[region]["severity_sum"] += ev["severity"]

    # Sort by count descending
    sorted_regions = sorted(region_data.items(), key=lambda x: x[1]["count"], reverse=True)
    regions = [r[0] for r in sorted_regions]
    counts = [r[1]["count"] for r in sorted_regions]
    avg_sevs = [r[1]["severity_sum"] / max(1, r[1]["count"]) for r in sorted_regions]

    # Map average severity to color
    bar_colors = []
    for s in avg_sevs:
        if s >= 0.7:
            bar_colors.append(_RED)
        elif s >= 0.5:
            bar_colors.append(_AMBER)
        elif s >= 0.3:
            bar_colors.append(_CYAN)
        else:
            bar_colors.append(_GREEN)

    fig = go.Figure(go.Bar(
        x=counts,
        y=regions,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=1, color=[c + "88" for c in bar_colors])),
        text=[f"{c} events (avg sev: {s:.2f})" for c, s in zip(counts, avg_sevs)],
        textposition="auto",
        textfont=dict(color=_TEXT, size=10, family="JetBrains Mono, monospace"),
        hovertemplate="<b>%{y}</b><br>Events: %{x}<extra></extra>",
    ))

    fig.update_layout(
        height=350,
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(l=100, r=20, t=40, b=30),
        title=dict(
            text="EVENTS BY REGION",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
    )
    fig.update_xaxes(gridcolor="#1a1f2e", color=_DIM, title="Event Count")
    fig.update_yaxes(gridcolor="#1a1f2e", color=_TEXT)

    return fig


def _build_source_reliability_chart(events):
    """Bar chart showing events per API source with severity-based color intensity."""
    if not HAS_PLOTLY or not events:
        return None

    source_data = {}
    for ev in events:
        src = ev.get("source", "Unknown")
        if src not in source_data:
            source_data[src] = {"count": 0, "severity_sum": 0.0, "latest_dt": None}
        source_data[src]["count"] += 1
        source_data[src]["severity_sum"] += ev["severity"]
        dt = _parse_event_datetime(ev)
        if dt is not None:
            if source_data[src]["latest_dt"] is None or dt > source_data[src]["latest_dt"]:
                source_data[src]["latest_dt"] = dt

    sorted_sources = sorted(source_data.items(), key=lambda x: x[1]["count"], reverse=True)
    sources = [s[0] for s in sorted_sources]
    counts = [s[1]["count"] for s in sorted_sources]
    avg_sevs = [s[1]["severity_sum"] / max(1, s[1]["count"]) for s in sorted_sources]

    # Color intensity based on severity
    bar_colors = []
    for s in avg_sevs:
        opacity_hex = format(int(min(255, max(80, s * 255))), "02x")
        if s >= 0.6:
            bar_colors.append(f"#ff3344{opacity_hex}")
        elif s >= 0.4:
            bar_colors.append(f"#ffaa00{opacity_hex}")
        else:
            bar_colors.append(f"#00f0ff{opacity_hex}")

    fig = go.Figure(go.Bar(
        x=sources,
        y=counts,
        marker=dict(color=bar_colors, line=dict(width=1, color=_DIM)),
        text=[f"{c}" for c in counts],
        textposition="outside",
        textfont=dict(color=_TEXT, size=10, family="JetBrains Mono, monospace"),
        hovertemplate="<b>%{x}</b><br>Events: %{y}<br>Avg Severity: %{customdata:.2f}<extra></extra>",
        customdata=avg_sevs,
    ))

    fig.update_layout(
        height=320,
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(l=40, r=20, t=40, b=60),
        title=dict(
            text="SOURCE RELIABILITY & CONTRIBUTION",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
    )
    fig.update_xaxes(gridcolor="#1a1f2e", color=_TEXT, tickangle=-30)
    fig.update_yaxes(gridcolor="#1a1f2e", color=_DIM, title="Event Count")

    return fig


def _build_temporal_heatmap(events):
    """Heatmap: X=hour of day (0-23), Y=day of week, Z=event count."""
    if not HAS_PLOTLY or not events:
        return None

    # Build 7x24 grid (Mon=0...Sun=6 x Hour 0..23)
    grid = [[0] * 24 for _ in range(7)]
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for ev in events:
        dt = _parse_event_datetime(ev)
        if dt is None:
            continue
        dow = dt.weekday()  # 0=Mon
        hour = dt.hour
        grid[dow][hour] += 1

    fig = go.Figure(go.Heatmap(
        z=grid,
        x=list(range(24)),
        y=day_names,
        colorscale=[
            [0.0, "#050520"],
            [0.25, "#003366"],
            [0.5, "#00f0ff"],
            [0.75, "#ffaa00"],
            [1.0, "#ff3344"],
        ],
        hovertemplate="Hour: %{x}<br>%{y}<br>Events: %{z}<extra></extra>",
        colorbar=dict(
            title=dict(text="Count", font=dict(color=_DIM, size=10)),
            tickfont=dict(color=_DIM, size=9),
        ),
    ))

    fig.update_layout(
        height=300,
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        margin=dict(l=90, r=20, t=40, b=40),
        title=dict(
            text="TEMPORAL HEATMAP — EVENT CLUSTERING",
            font=dict(color=_CYAN, size=12, family="JetBrains Mono, monospace"),
        ),
    )
    fig.update_xaxes(
        title="Hour of Day (UTC)", color=_DIM, gridcolor="#1a1f2e",
        dtick=1, tickvals=list(range(24)),
        ticktext=[f"{h:02d}" for h in range(24)],
    )
    fig.update_yaxes(color=_TEXT, gridcolor="#1a1f2e")

    return fig


def _render_event_card(event):
    """Build HTML card for a single event."""
    sev_label, sev_color = _severity_label(event["severity"])
    title = html_module.escape(str(event.get("title", "Unknown")))
    desc = html_module.escape(str(event.get("description", "")))
    source = html_module.escape(str(event.get("source", "")))
    date = html_module.escape(str(event.get("date", "")))
    cat = html_module.escape(str(event.get("category", "")))
    cat_color = CATEGORY_COLORS.get(event.get("category", ""), _DIM)
    url = event.get("url", "")

    link_html = ""
    if url:
        escaped_url = html_module.escape(str(url))
        link_html = (
            f'<a href="{escaped_url}" target="_blank" rel="noopener noreferrer" '
            f'style="color:{_CYAN};font-size:0.7rem;">View Source</a>'
        )

    return (
        f'<div style="border:1px solid {sev_color}33;border-radius:8px;padding:12px;'
        f'background:{sev_color}08;margin:0.5rem 0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:1rem;font-weight:700;color:{_TEXT};">{title}</span>'
        f'<span style="background:{sev_color}22;border:1px solid {sev_color};'
        f'border-radius:4px;padding:2px 8px;font-size:0.65rem;color:{sev_color};'
        f'font-weight:700;">{sev_label}</span>'
        f'</div>'
        f'<div style="margin-top:6px;font-size:0.72rem;color:{_DIM};">'
        f'<span style="color:{cat_color};font-weight:600;">{cat}</span>'
        f' &bull; {source} &bull; {date}'
        f'</div>'
        f'<div style="margin-top:6px;font-size:0.75rem;color:{_TEXT};">{desc}</div>'
        f'<div style="margin-top:4px;font-size:0.68rem;color:{_DIM};">'
        f'Location: {event["lat"]:.3f}, {event["lon"]:.3f} {link_html}'
        f'</div>'
        f'</div>'
    )


def _generate_ai_analysis(event, nearby_events):
    """Generate AI-driven impact assessment for an event."""
    sev_label, sev_color = _severity_label(event["severity"])
    region = _estimate_region(event["lat"], event["lon"])
    cat = event.get("category", "NEWS")

    # Cascading effects by category
    cascade_map = {
        "EARTHQUAKE": "structural damage, landslides, tsunami risk, infrastructure disruption, population displacement",
        "DISASTER": "infrastructure damage, supply chain disruption, humanitarian crisis, economic losses",
        "FIRE": "air quality degradation, ecosystem destruction, evacuation needs, agricultural losses",
        "CONFLICT": "population displacement, humanitarian crisis, economic disruption, regional instability",
        "HEALTH": "healthcare system strain, economic impact, travel restrictions, social disruption",
        "WEATHER": "infrastructure damage, agricultural impact, transportation disruption, energy grid stress",
        "HUMANITARIAN": "food insecurity, health risks, population displacement, resource strain",
        "NEWS": "public awareness shift, policy implications, market effects",
    }
    cascading = cascade_map.get(cat, "further assessment needed")

    # Historical context
    same_cat_nearby = sum(1 for ev, _ in nearby_events if ev["category"] == cat)
    if same_cat_nearby >= 3:
        hist = f"HIGH CLUSTER: {same_cat_nearby} similar events within 500km indicate a regional pattern."
    elif same_cat_nearby >= 1:
        hist = f"Related activity: {same_cat_nearby} similar event(s) detected nearby."
    else:
        hist = "No similar events in immediate vicinity. Isolated occurrence."

    return (
        f'<div style="border:1px solid {_CYAN}33;border-radius:8px;padding:12px;'
        f'background:{_CYAN}05;margin:0.5rem 0;">'
        f'<div style="font-size:0.7rem;color:{_CYAN};font-weight:700;letter-spacing:1px;'
        f'margin-bottom:8px;">AI IMPACT ASSESSMENT</div>'
        # Severity classification
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:0.68rem;color:{_DIM};">Severity Classification:</span> '
        f'<span style="color:{sev_color};font-weight:700;font-size:0.75rem;">{sev_label}</span> '
        f'<span style="color:{_DIM};font-size:0.68rem;">({event["severity"]:.2f})</span>'
        f'</div>'
        # Region
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:0.68rem;color:{_DIM};">Geographic Context:</span> '
        f'<span style="color:{_TEXT};font-size:0.72rem;">{region} region '
        f'({event["lat"]:.2f}N, {event["lon"]:.2f}E)</span>'
        f'</div>'
        # Cascading effects
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:0.68rem;color:{_DIM};">Potential Cascading Effects:</span> '
        f'<span style="color:{_AMBER};font-size:0.72rem;">{cascading}</span>'
        f'</div>'
        # Historical pattern
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:0.68rem;color:{_DIM};">Historical Pattern:</span> '
        f'<span style="color:{_TEXT};font-size:0.72rem;">{hist}</span>'
        f'</div>'
        # Nearby events
        f'<div>'
        f'<span style="font-size:0.68rem;color:{_DIM};">Nearby Events (500km):</span> '
        f'<span style="color:{_GREEN};font-size:0.72rem;">{len(nearby_events)} detected</span>'
        f'</div>'
        f'</div>'
    )


def _generate_intelligence_summary(events, timespan="24h"):
    """Generate NLG intelligence summary -- 4-paragraph analytical report."""
    if not events:
        return "No events detected in the selected timeframe and filters."

    total = len(events)
    cat_counts = Counter(ev["category"] for ev in events)
    dominant_cat = cat_counts.most_common(1)[0] if cat_counts else ("NEWS", 0)
    dominant_pct = (dominant_cat[1] / total * 100) if total else 0
    top_event = events[0] if events else None

    # Severity distribution
    critical_n = sum(1 for ev in events if ev["severity"] >= 0.8)
    high_n = sum(1 for ev in events if 0.6 <= ev["severity"] < 0.8)
    elevated_n = sum(1 for ev in events if 0.4 <= ev["severity"] < 0.6)
    moderate_n = sum(1 for ev in events if 0.2 <= ev["severity"] < 0.4)
    low_n = total - critical_n - high_n - elevated_n - moderate_n
    avg_severity = sum(ev["severity"] for ev in events) / total if total else 0
    sev_label, _ = _severity_label(avg_severity)

    top_title = html_module.escape(str(top_event["title"])) if top_event else "N/A"
    top_loc = f"{top_event['lat']:.1f}N, {top_event['lon']:.1f}E" if top_event else "N/A"

    # Region analysis
    region_counts = Counter(_estimate_region(ev["lat"], ev["lon"]) for ev in events)
    hotspots = [r for r, _ in region_counts.most_common(6) if r != "Other"]
    top_region = hotspots[0] if hotspots else "undetermined"
    top_region_count = region_counts.get(top_region, 0)
    top_region_pct = (top_region_count / total * 100) if total else 0
    multi_region = len(hotspots) >= 3

    # Trend analysis
    defcon, risk_score, trend = _compute_defcon_level(events)

    # Date range
    date_objs = [_parse_event_datetime(ev) for ev in events]
    date_objs = [d for d in date_objs if d is not None]
    if date_objs:
        oldest = min(date_objs)
        newest = max(date_objs)
        span_hours = max(1, (newest - oldest).total_seconds() / 3600)
        span_str = f"{span_hours:.0f} hours" if span_hours < 48 else f"{span_hours / 24:.1f} days"
    else:
        span_str = html_module.escape(str(timespan))

    ts_esc = html_module.escape(str(timespan))

    # --- Paragraph 1: Overview ---
    p1 = (
        f"In the past {ts_esc}, <b>{total}</b> verified events were recorded across the global monitoring network, "
        f"spanning a temporal window of approximately {span_str}. "
        f"The highest-priority incident is <span style='color:{_RED};font-weight:700;'>{top_title}</span> "
        f"near coordinates {top_loc}. "
        f"<span style='color:{CATEGORY_COLORS.get(dominant_cat[0], _DIM)};font-weight:600;'>"
        f"{html_module.escape(str(dominant_cat[0]))}</span> events dominate the activity landscape at "
        f"<b>{dominant_pct:.0f}%</b> of total volume. "
        f"Severity distribution: {critical_n} CRITICAL, {high_n} HIGH, {elevated_n} ELEVATED, "
        f"{moderate_n} MODERATE, {low_n} LOW. Mean severity index stands at "
        f"<b>{sev_label}</b> ({avg_severity:.2f}/1.00)."
    )

    # --- Paragraph 2: Regional analysis ---
    if multi_region:
        region_detail = (
            f"Multi-regional activity detected across <b>{len(hotspots)}</b> distinct zones. "
            f"The <b>{html_module.escape(str(top_region))}</b> region leads with "
            f"{top_region_count} events ({top_region_pct:.0f}% of total). "
        )
        if len(hotspots) >= 2:
            region_detail += (
                f"Secondary concentrations observed in <b>{html_module.escape(str(hotspots[1]))}</b> "
                f"({region_counts.get(hotspots[1], 0)} events)"
            )
            if len(hotspots) >= 3:
                region_detail += (
                    f" and <b>{html_module.escape(str(hotspots[2]))}</b> "
                    f"({region_counts.get(hotspots[2], 0)} events)"
                )
            region_detail += ". "
        region_detail += (
            "Cross-regional correlation analysis suggests interconnected event chains may be "
            "developing along established geopolitical and meteorological corridors."
        )
    else:
        region_detail = (
            f"Activity is concentrated primarily in <b>{html_module.escape(str(top_region))}</b> "
            f"({top_region_count} events). "
            "Limited multi-regional spread reduces cascading risk but warrants continued monitoring "
            "for potential secondary effects in adjacent zones."
        )
    p2 = region_detail

    # --- Paragraph 3: Threat trajectory ---
    if trend == "ESCALATING":
        trend_text = (
            f"<span style='color:{_RED};font-weight:700;'>THREAT TRAJECTORY: ESCALATING.</span> "
            f"Recent events show increasing severity compared to earlier activity in this window. "
            f"Global risk score has reached <b>{risk_score:.0f}/100</b> (DEFCON {defcon}). "
            f"Situation requires heightened monitoring and potential activation of contingency protocols. "
            f"The upward severity trend across {len(set(ev['category'] for ev in events))} active categories "
            f"indicates compounding risk factors."
        )
    elif trend == "DE-ESCALATING":
        trend_text = (
            f"<span style='color:{_GREEN};font-weight:700;'>THREAT TRAJECTORY: DE-ESCALATING.</span> "
            f"Severity metrics show a downward trend from peak levels. "
            f"Global risk score stands at <b>{risk_score:.0f}/100</b> (DEFCON {defcon}). "
            f"While the immediate threat profile is improving, continued surveillance is recommended "
            f"to confirm stabilization and detect any secondary escalation vectors."
        )
    else:
        trend_text = (
            f"<span style='color:{_AMBER};font-weight:700;'>THREAT TRAJECTORY: STABLE.</span> "
            f"No significant change in severity patterns detected within the analysis window. "
            f"Global risk score holds at <b>{risk_score:.0f}/100</b> (DEFCON {defcon}). "
            f"The stable trajectory does not preclude rapid escalation; "
            f"maintain current monitoring posture with attention to high-severity outliers."
        )
    p3 = trend_text

    # --- Paragraph 4: Recommendations ---
    recs = []
    if critical_n > 0:
        recs.append(
            f"Immediate attention required on {critical_n} CRITICAL-severity event(s); "
            f"recommend real-time tracking and situation room activation"
        )
    if multi_region:
        recs.append(
            "Multi-regional activity pattern detected; activate cross-border coordination protocols"
        )
    most_active_cat = dominant_cat[0]
    if most_active_cat in ("EARTHQUAKE", "DISASTER"):
        recs.append(
            "Prioritize structural damage assessment and population displacement monitoring"
        )
    elif most_active_cat == "FIRE":
        recs.append(
            "Monitor air quality indices and evacuation corridor availability in affected zones"
        )
    elif most_active_cat == "CONFLICT":
        recs.append(
            "Escalate diplomatic intelligence gathering; track population movement patterns"
        )
    elif most_active_cat == "HEALTH":
        recs.append(
            "Activate epidemiological surveillance networks; monitor healthcare capacity metrics"
        )
    if not recs:
        recs.append("Maintain standard monitoring posture with periodic re-assessment")
    recs.append("Schedule next comprehensive threat assessment in 6 hours")

    p4 = "<b>RECOMMENDATIONS:</b> " + "; ".join(recs) + "."

    # Combine all paragraphs
    return (
        f"<div style='margin-bottom:10px;'>{p1}</div>"
        f"<div style='margin-bottom:10px;'>{p2}</div>"
        f"<div style='margin-bottom:10px;'>{p3}</div>"
        f"<div>{p4}</div>"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ═══════════════════════════════════════════════════════════════════════════

def _render_threat_dashboard(events):
    """Render the DEFCON-style threat level dashboard."""
    defcon, risk_score, trend = _compute_defcon_level(events)
    level_info = _DEFCON_LEVELS.get(defcon, _DEFCON_LEVELS[5])
    level_color = level_info["color"]
    level_label = level_info["label"]
    level_bg = level_info["bg"]

    # Pulse animation for high threat levels (DEFCON 1-2)
    pulse_css = ""
    if defcon <= 2:
        pulse_css = (
            f'animation: globe-pulse 1.5s ease-in-out infinite;'
        )
    elif defcon == 3:
        pulse_css = (
            f'animation: globe-pulse 2.5s ease-in-out infinite;'
        )

    # Trend arrow and color
    if trend == "ESCALATING":
        trend_arrow = "&#x25B2;"  # up triangle
        trend_color = _RED
    elif trend == "DE-ESCALATING":
        trend_arrow = "&#x25BC;"  # down triangle
        trend_color = _GREEN
    else:
        trend_arrow = "&#x25C6;"  # diamond
        trend_color = _AMBER

    # Inject CSS keyframes for pulse
    st.markdown(
        """<style>
        @keyframes globe-pulse {
            0% { box-shadow: 0 0 5px rgba(255,51,68,0.2); }
            50% { box-shadow: 0 0 25px rgba(255,51,68,0.6); }
            100% { box-shadow: 0 0 5px rgba(255,51,68,0.2); }
        }
        </style>""",
        unsafe_allow_html=True,
    )

    col_defcon, col_risk, col_trend = st.columns([2, 1, 1])

    with col_defcon:
        st.markdown(
            f'<div style="text-align:center;padding:20px;border:2px solid {level_color};'
            f'border-radius:12px;background:{level_bg};{pulse_css}'
            f'font-family:JetBrains Mono,monospace;">'
            f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:2px;'
            f'margin-bottom:8px;">GLOBAL THREAT LEVEL</div>'
            f'<div style="font-size:1.6rem;font-weight:900;color:{level_color};'
            f'letter-spacing:3px;">{level_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_risk:
        # Risk score gauge
        if risk_score >= 70:
            score_color = _RED
        elif risk_score >= 40:
            score_color = _AMBER
        else:
            score_color = _GREEN

        st.markdown(
            f'<div style="text-align:center;padding:20px;border:1px solid {score_color}33;'
            f'border-radius:12px;background:{score_color}08;'
            f'font-family:JetBrains Mono,monospace;">'
            f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:2px;'
            f'margin-bottom:8px;">GLOBAL RISK SCORE</div>'
            f'<div style="font-size:2.4rem;font-weight:900;color:{score_color};">'
            f'{risk_score:.0f}</div>'
            f'<div style="font-size:0.6rem;color:{_DIM};">/ 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_trend:
        # Phase 2C: risk score variation indicator (session state)
        prev_risk = st.session_state.get("globe_prev_risk_score")
        delta_html = ""
        if prev_risk is not None:
            delta = risk_score - prev_risk
            if abs(delta) > 0.5:
                d_arrow = "&#x25B2;" if delta > 0 else "&#x25BC;"
                d_color = _RED if delta > 0 else _GREEN
                delta_html = (
                    f'<div style="font-size:0.65rem;color:{d_color};margin-top:4px;">'
                    f'{d_arrow} {delta:+.1f}</div>'
                )
        st.session_state["globe_prev_risk_score"] = risk_score

        st.markdown(
            f'<div style="text-align:center;padding:20px;border:1px solid {trend_color}33;'
            f'border-radius:12px;background:{trend_color}08;'
            f'font-family:JetBrains Mono,monospace;">'
            f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:2px;'
            f'margin-bottom:8px;">THREAT TREND</div>'
            f'<div style="font-size:1.8rem;color:{trend_color};">{trend_arrow}</div>'
            f'<div style="font-size:0.85rem;font-weight:700;color:{trend_color};'
            f'letter-spacing:1px;">{trend}</div>'
            f'{delta_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Phase 2C: Mini horizontal bars per category
    cat_counts = Counter(ev["category"] for ev in events)
    if cat_counts:
        bars_html = ""
        max_count = max(cat_counts.values()) if cat_counts else 1
        for cat, cnt in cat_counts.most_common():
            cc = CATEGORY_COLORS.get(cat, _DIM)
            pct = cnt / max_count * 100
            bars_html += (
                f'<div style="display:flex;align-items:center;margin:2px 0;">'
                f'<span style="font-size:0.6rem;color:{cc};width:90px;font-weight:600;'
                f'font-family:JetBrains Mono,monospace;">{cat}</span>'
                f'<div style="flex:1;height:8px;background:{_BG};border-radius:4px;overflow:hidden;">'
                f'<div style="width:{pct:.0f}%;height:100%;background:{cc};border-radius:4px;">'
                f'</div></div>'
                f'<span style="font-size:0.6rem;color:{_DIM};width:30px;text-align:right;'
                f'margin-left:6px;">{cnt}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div style="margin-top:8px;padding:8px;border:1px solid {_DIM}22;'
            f'border-radius:6px;background:{_CARD_BG};">{bars_html}</div>',
            unsafe_allow_html=True,
        )

    # Phase 2C: Quick top-3 critical events
    critical_events = [ev for ev in events if ev["severity"] >= 0.7][:3]
    if critical_events:
        crit_html = ""
        for cev in critical_events:
            sl, sc = _severity_label(cev["severity"])
            ct = html_module.escape(str(cev["title"]))[:50]
            ccat = CATEGORY_COLORS.get(cev.get("category", "NEWS"), _DIM)
            crit_html += (
                f'<div style="padding:4px 8px;margin:2px 0;border-left:2px solid {sc};'
                f'font-size:0.68rem;background:{sc}08;">'
                f'<span style="color:{ccat};font-weight:700;">'
                f'{html_module.escape(str(cev.get("category","")))}</span> '
                f'<span style="color:{_TEXT};">{ct}</span> '
                f'<span style="color:{sc};font-weight:700;margin-left:6px;">{sl}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div style="margin-top:6px;font-size:0.6rem;color:{_RED};'
            f'font-weight:700;letter-spacing:1px;margin-bottom:2px;">'
            f'TOP CRITICAL EVENTS</div>{crit_html}',
            unsafe_allow_html=True,
        )


def _render_live_ticker(events):
    """Render a CSS-animated horizontal scrolling event ticker.
    Phase 2B: hover pause, severity colors, blink for CRITICAL, event count badge."""
    if not events:
        return

    # Build ticker items from the top 20 events
    ticker_items = []
    for ev in events[:20]:
        cat = html_module.escape(str(ev.get("category", "NEWS")))
        title = html_module.escape(str(ev.get("title", "Unknown")))[:60]
        source = html_module.escape(str(ev.get("source", "")))
        dt = _parse_event_datetime(ev)
        ago = _time_ago(dt)
        cat_color = CATEGORY_COLORS.get(ev.get("category", "NEWS"), _DIM)
        sev = ev.get("severity", 0)
        # Phase 2B: severity-based border for items with sev >= 0.6
        border_style = ""
        if sev >= 0.6:
            _, sev_color = _severity_label(sev)
            border_style = f"border-left:2px solid {sev_color};padding-left:6px;"
        # Phase 2B: blink class for CRITICAL events
        blink_class = ' class="globe-ticker-blink"' if sev >= 0.8 else ""
        ticker_items.append(
            f'<span style="white-space:nowrap;margin-right:40px;{border_style}"{blink_class}>'
            f'<span style="color:{cat_color};font-weight:700;">[{cat}]</span> '
            f'<span style="color:{_TEXT};">{title}</span> '
            f'<span style="color:{_DIM};">&mdash; {source} &mdash; {ago}</span>'
            f'</span>'
        )

    ticker_content = " ".join(ticker_items)
    # Double the content for seamless loop
    ticker_double = ticker_content + " " + ticker_content

    # Calculate animation duration based on content length
    duration = max(30, len(ticker_items) * 4)

    # Phase 2B: inject marquee CSS with hover pause + blink
    st.markdown(
        "<style>"
        "@keyframes globe-marquee {"
        "  0% { transform: translateX(0%); }"
        "  100% { transform: translateX(-50%); }"
        "}"
        "@keyframes globe-ticker-blink-anim {"
        "  0%, 100% { opacity: 1; }"
        "  50% { opacity: 0.4; }"
        "}"
        ".globe-ticker-blink { animation: globe-ticker-blink-anim 1.5s ease-in-out infinite; }"
        ".globe-ticker-track:hover { animation-play-state: paused !important; }"
        "</style>",
        unsafe_allow_html=True,
    )

    # Phase 2B: event count badge
    event_count_badge = (
        f'<span style="background:{_AMBER};color:#000;padding:2px 6px;font-size:0.55rem;'
        f'font-weight:700;border-radius:8px;margin-left:6px;">{len(events)}</span>'
    )

    # Render ticker content separately
    st.markdown(
        f'<div style="border:1px solid rgba(0,255,136,0.13);border-radius:8px;padding:10px 0;'
        f'background:{_CARD_BG};overflow:hidden;margin:0.5rem 0;">'
        f'<div style="display:flex;align-items:center;">'
        f'<div style="background:{_RED};color:#fff;padding:4px 12px;font-size:0.65rem;'
        f'font-weight:700;letter-spacing:1px;font-family:JetBrains Mono,monospace;'
        f'white-space:nowrap;border-radius:4px;margin:0 12px;flex-shrink:0;">'
        f'LIVE FEED{event_count_badge}</div>'
        f'<div style="overflow:hidden;flex:1;">'
        f'<div class="globe-ticker-track" style="display:inline-block;white-space:nowrap;'
        f'animation:globe-marquee {duration}s linear infinite;'
        f'font-family:JetBrains Mono,monospace;font-size:0.72rem;">'
        f'{ticker_double}'
        f'</div></div></div></div>',
        unsafe_allow_html=True,
    )


def _render_cascading_risk_network(events):
    """Render cascading risk analysis for cross-category event pairs within 300km."""
    if not events or len(events) < 2:
        st.markdown(
            f'<div style="color:{_DIM};font-size:0.75rem;padding:8px;">'
            f'Insufficient event data for cascading risk analysis.</div>',
            unsafe_allow_html=True,
        )
        return

    risk_pairs = []
    seen_pairs = set()
    # Limit comparisons for performance
    check_events = events[:60]
    for i, ev1 in enumerate(check_events):
        for j, ev2 in enumerate(check_events):
            if i >= j:
                continue
            if ev1["category"] == ev2["category"]:
                continue
            pair_key = (min(ev1["id"], ev2["id"]), max(ev1["id"], ev2["id"]))
            if pair_key in seen_pairs:
                continue
            dist = _haversine(ev1["lat"], ev1["lon"], ev2["lat"], ev2["lon"])
            if dist <= 300:
                seen_pairs.add(pair_key)
                # Look up cascade scenario
                key1 = (ev1["category"], ev2["category"])
                key2 = (ev2["category"], ev1["category"])
                scenario = _CASCADE_SCENARIOS.get(key1) or _CASCADE_SCENARIOS.get(key2)
                if scenario is None:
                    scenario = "Cross-category proximity risk; monitor for compound effects"
                risk_pairs.append({
                    "ev1": ev1,
                    "ev2": ev2,
                    "distance": dist,
                    "scenario": scenario,
                    "combined_severity": (ev1["severity"] + ev2["severity"]) / 2,
                })
            if len(risk_pairs) >= 15:
                break
        if len(risk_pairs) >= 15:
            break

    if not risk_pairs:
        st.markdown(
            f'<div style="color:{_GREEN};font-size:0.75rem;padding:8px;'
            f'border:1px solid {_GREEN}22;border-radius:6px;background:{_GREEN}05;">'
            f'No cross-category cascading risk pairs detected within 300km threshold. '
            f'Low compound-threat environment.</div>',
            unsafe_allow_html=True,
        )
        return

    # Sort by combined severity descending
    risk_pairs.sort(key=lambda x: x["combined_severity"], reverse=True)

    # Build HTML table
    rows_html = ""
    for rp in risk_pairs[:12]:
        ev1 = rp["ev1"]
        ev2 = rp["ev2"]
        c1 = CATEGORY_COLORS.get(ev1["category"], _DIM)
        c2 = CATEGORY_COLORS.get(ev2["category"], _DIM)
        sev_avg = rp["combined_severity"]
        _, sev_color = _severity_label(sev_avg)
        t1 = html_module.escape(str(ev1["title"]))[:35]
        t2 = html_module.escape(str(ev2["title"]))[:35]
        cat1 = html_module.escape(str(ev1["category"]))
        cat2 = html_module.escape(str(ev2["category"]))
        scenario_esc = html_module.escape(str(rp["scenario"]))

        rows_html += (
            f'<tr style="border-bottom:1px solid #1a1f2e;">'
            f'<td style="padding:6px 8px;font-size:0.68rem;">'
            f'<span style="color:{c1};font-weight:600;">{cat1}</span><br>'
            f'<span style="color:{_TEXT};">{t1}</span></td>'
            f'<td style="padding:6px 8px;font-size:0.68rem;">'
            f'<span style="color:{c2};font-weight:600;">{cat2}</span><br>'
            f'<span style="color:{_TEXT};">{t2}</span></td>'
            f'<td style="padding:6px 8px;font-size:0.68rem;color:{_AMBER};text-align:center;">'
            f'{rp["distance"]:.0f} km</td>'
            f'<td style="padding:6px 8px;font-size:0.68rem;text-align:center;">'
            f'<span style="color:{sev_color};font-weight:700;">{sev_avg:.2f}</span></td>'
            f'<td style="padding:6px 8px;font-size:0.65rem;color:{_AMBER};max-width:300px;">'
            f'{scenario_esc}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;font-family:JetBrains Mono,monospace;">'
        f'<thead><tr style="border-bottom:2px solid {_CYAN}44;">'
        f'<th style="padding:8px;font-size:0.62rem;color:{_CYAN};text-align:left;'
        f'letter-spacing:1px;">EVENT A</th>'
        f'<th style="padding:8px;font-size:0.62rem;color:{_CYAN};text-align:left;'
        f'letter-spacing:1px;">EVENT B</th>'
        f'<th style="padding:8px;font-size:0.62rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:1px;">DISTANCE</th>'
        f'<th style="padding:8px;font-size:0.62rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:1px;">RISK</th>'
        f'<th style="padding:8px;font-size:0.62rem;color:{_CYAN};text-align:left;'
        f'letter-spacing:1px;">CASCADE SCENARIO</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )


def _render_regional_ranking_table(events):
    """Render a regional threat ranking table below the bar chart."""
    if not events:
        return

    region_data = {}
    for ev in events:
        region = _estimate_region(ev["lat"], ev["lon"])
        if region not in region_data:
            region_data[region] = {"count": 0, "severity_sum": 0.0, "critical": 0, "categories": set()}
        region_data[region]["count"] += 1
        region_data[region]["severity_sum"] += ev["severity"]
        region_data[region]["categories"].add(ev["category"])
        if ev["severity"] >= 0.8:
            region_data[region]["critical"] += 1

    # Sort by threat score: count * avg_severity
    sorted_regions = sorted(
        region_data.items(),
        key=lambda x: x[1]["count"] * (x[1]["severity_sum"] / max(1, x[1]["count"])),
        reverse=True,
    )

    rows_html = ""
    for rank, (region, data) in enumerate(sorted_regions, 1):
        avg_sev = data["severity_sum"] / max(1, data["count"])
        _, sev_color = _severity_label(avg_sev)
        region_esc = html_module.escape(str(region))
        n_cats = len(data["categories"])
        threat_score = data["count"] * avg_sev

        rows_html += (
            f'<tr style="border-bottom:1px solid #1a1f2e;">'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_AMBER};text-align:center;'
            f'font-weight:700;">#{rank}</td>'
            f'<td style="padding:5px 8px;font-size:0.72rem;color:{_TEXT};font-weight:600;">'
            f'{region_esc}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_TEXT};text-align:center;">'
            f'{data["count"]}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{sev_color};text-align:center;'
            f'font-weight:700;">{avg_sev:.2f}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_RED};text-align:center;">'
            f'{data["critical"]}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_DIM};text-align:center;">'
            f'{n_cats}</td>'
            f'<td style="padding:5px 8px;font-size:0.7rem;color:{_AMBER};text-align:center;'
            f'font-weight:700;">{threat_score:.1f}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="margin-top:8px;font-size:0.7rem;color:{_CYAN};font-weight:700;'
        f'letter-spacing:1px;margin-bottom:4px;">REGIONAL THREAT RANKING</div>'
        f'<table style="width:100%;border-collapse:collapse;font-family:JetBrains Mono,monospace;">'
        f'<thead><tr style="border-bottom:2px solid {_CYAN}44;">'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};letter-spacing:0.5px;">#</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:left;'
        f'letter-spacing:0.5px;">REGION</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">EVENTS</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">AVG SEV</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">CRITICAL</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">CATS</th>'
        f'<th style="padding:5px 8px;font-size:0.6rem;color:{_CYAN};text-align:center;'
        f'letter-spacing:0.5px;">THREAT</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True,
    )


def _render_source_freshness(events):
    """Render source freshness indicators below the source reliability chart."""
    if not events:
        return

    source_latest = {}
    for ev in events:
        src = ev.get("source", "Unknown")
        dt = _parse_event_datetime(ev)
        if dt is not None:
            if src not in source_latest or dt > source_latest[src]:
                source_latest[src] = dt

    if not source_latest:
        return

    items_html = ""
    for src, dt in sorted(source_latest.items(), key=lambda x: x[1], reverse=True):
        ago = _time_ago(dt)
        src_esc = html_module.escape(str(src))
        # Color code: recent=green, stale=amber, very stale=red
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours_ago = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        if hours_ago < 6:
            freshness_color = _GREEN
            freshness_label = "FRESH"
        elif hours_ago < 24:
            freshness_color = _AMBER
            freshness_label = "AGING"
        else:
            freshness_color = _RED
            freshness_label = "STALE"

        items_html += (
            f'<div style="display:inline-block;margin:3px 6px;padding:4px 10px;'
            f'border:1px solid {freshness_color}33;border-radius:4px;background:{freshness_color}08;">'
            f'<span style="font-size:0.68rem;color:{_TEXT};font-weight:600;">{src_esc}</span>'
            f'<span style="font-size:0.6rem;color:{_DIM};margin-left:6px;">{ago}</span>'
            f'<span style="font-size:0.55rem;color:{freshness_color};margin-left:6px;'
            f'font-weight:700;">{freshness_label}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div style="margin-top:8px;font-size:0.65rem;color:{_DIM};margin-bottom:4px;'
        f'letter-spacing:0.5px;">SOURCE FRESHNESS:</div>'
        f'<div>{items_html}</div>',
        unsafe_allow_html=True,
    )


def _render_data_quality_panel(events, raw_count):
    """Render data quality metrics panel."""
    if not events:
        return

    total = len(events)
    dedup_pct = ((raw_count - total) / max(1, raw_count) * 100) if raw_count > total else 0

    # Source breakdown
    source_counts = Counter(ev.get("source", "Unknown") for ev in events)
    source_parts = []
    for src, cnt in source_counts.most_common():
        pct = cnt / max(1, total) * 100
        src_esc = html_module.escape(str(src))
        source_parts.append(f"{src_esc}: {cnt} ({pct:.0f}%)")
    source_str = " | ".join(source_parts)

    # Date range
    date_objs = [_parse_event_datetime(ev) for ev in events]
    date_objs = [d for d in date_objs if d is not None]
    if date_objs:
        oldest = min(date_objs).strftime("%Y-%m-%d %H:%M UTC")
        newest = max(date_objs).strftime("%Y-%m-%d %H:%M UTC")
    else:
        oldest = "N/A"
        newest = "N/A"

    # Category coverage
    active_cats = set(ev["category"] for ev in events)
    total_cats = len(CATEGORY_COLORS)
    coverage = len(active_cats)
    coverage_pct = coverage / total_cats * 100

    st.markdown(
        f'<div style="border:1px solid {_DIM}22;border-radius:8px;padding:12px;'
        f'background:{_CARD_BG};font-family:JetBrains Mono,monospace;">'
        f'<div style="display:flex;flex-wrap:wrap;gap:16px;">'
        # Raw vs deduped
        f'<div style="flex:1;min-width:140px;">'
        f'<div style="font-size:0.58rem;color:{_DIM};letter-spacing:1px;">EVENTS (RAW / DEDUPED)</div>'
        f'<div style="font-size:1rem;color:{_TEXT};font-weight:700;">'
        f'{raw_count} &rarr; {total} '
        f'<span style="font-size:0.65rem;color:{_AMBER};">(-{dedup_pct:.0f}%)</span></div>'
        f'</div>'
        # Date range
        f'<div style="flex:1;min-width:200px;">'
        f'<div style="font-size:0.58rem;color:{_DIM};letter-spacing:1px;">DATA WINDOW</div>'
        f'<div style="font-size:0.72rem;color:{_TEXT};">{oldest}</div>'
        f'<div style="font-size:0.72rem;color:{_TEXT};">&rarr; {newest}</div>'
        f'</div>'
        # Coverage
        f'<div style="flex:1;min-width:140px;">'
        f'<div style="font-size:0.58rem;color:{_DIM};letter-spacing:1px;">CATEGORY COVERAGE</div>'
        f'<div style="font-size:1rem;color:{_GREEN if coverage_pct >= 75 else _AMBER};'
        f'font-weight:700;">{coverage}/{total_cats} '
        f'<span style="font-size:0.65rem;">({coverage_pct:.0f}%)</span></div>'
        f'</div>'
        f'</div>'
        # Source breakdown
        f'<div style="margin-top:8px;font-size:0.6rem;color:{_DIM};letter-spacing:0.5px;">'
        f'SOURCE BREAKDOWN: {source_str}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PAGE RENDER
# ═══════════════════════════════════════════════════════════════════════════

def render_globe_intelligence():
    """Render the Global Situational Awareness page."""

    # ─── HERO HEADER ───
    st.markdown(
        '<div style="text-align:center;padding:1.2rem 0 0.8rem 0;">'
        '<h1 style="font-family:JetBrains Mono,monospace;font-size:1.6rem;'
        f'color:{_GREEN};letter-spacing:3px;margin:0;">GLOBAL SITUATIONAL AWARENESS</h1>'
        '<p style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_DIM};letter-spacing:1.5px;margin:4px 0 0 0;">'
        '3D INTELLIGENCE GLOBE &bull; 7 DATA SOURCES &bull; REAL-TIME MONITORING '
        '&bull; THREAT ANALYSIS &bull; CASCADING RISK</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not HAS_EVENTS_API:
        st.error("Global events API module not available. Cannot load intelligence data.")
        return
    if not HAS_PLOTLY:
        st.error("Plotly is required for the Intelligence Globe. Install with: pip install plotly")
        return

    # ─── SECTION 1: CONTROLS BAR ───
    c1, c2, c3, c4, c5 = st.columns([1.2, 2, 1, 1.2, 0.8])

    with c1:
        timespan_map = {"1 hour": "1h", "6 hours": "6h", "24 hours": "24h", "3 days": "3d", "7 days": "7d"}
        timespan_label = st.selectbox(
            "Timespan", list(timespan_map.keys()), index=2, key="globe_timespan",
        )
        timespan = timespan_map[timespan_label]

    with c2:
        all_cats = list(CATEGORY_COLORS.keys())
        selected_cats = st.multiselect(
            "Event Categories", all_cats, default=all_cats, key="globe_categories",
        )

    with c3:
        severity_min = st.slider(
            "Min Severity", 0.0, 1.0, 0.0, 0.05, key="globe_severity",
        )

    with c4:
        region = st.selectbox(
            "Region", list(REGION_BOUNDS.keys()), index=0, key="globe_region",
        )

    with c5:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        refresh = st.button("Refresh", key="globe_refresh", use_container_width=True)

    # ─── FETCH DATA ───
    with st.spinner("Fetching global intelligence data from 7 sources..."):
        try:
            raw_events = fetch_all_global_events(timespan=timespan)
        except Exception as exc:
            logger.warning("Failed to fetch global events: %s", exc)
            raw_events = []

    raw_count = len(raw_events)

    if not raw_events:
        st.info("No events retrieved. APIs may be temporarily unavailable. Try refreshing.")

    # Apply filters
    if selected_cats and raw_events:
        events = _filter_events(raw_events, selected_cats, severity_min, region)
    else:
        events = raw_events

    # ─── SECTION 2: KPI STATISTICS STRIP ───
    cat_counts = Counter(ev["category"] for ev in events)
    kpi_data = [
        ("TOTAL EVENTS", len(events), _GREEN),
        ("DISASTERS", cat_counts.get("DISASTER", 0), _RED),
        ("FIRES", cat_counts.get("FIRE", 0), "#ff8800"),
        ("EARTHQUAKES", cat_counts.get("EARTHQUAKE", 0), _AMBER),
        ("CONFLICTS", cat_counts.get("CONFLICT", 0), _VIOLET),
        ("HEALTH", cat_counts.get("HEALTH", 0), _CYAN),
        ("WEATHER", cat_counts.get("WEATHER", 0), "#4488ff"),
        ("HUMANITARIAN", cat_counts.get("HUMANITARIAN", 0), _PINK),
        ("NEWS", cat_counts.get("NEWS", 0), _DIM),
    ]

    kpi_cols = st.columns(len(kpi_data))
    for col, (label, value, color) in zip(kpi_cols, kpi_data):
        col.markdown(
            f'<div style="text-align:center;padding:6px 2px;border:1px solid {color}22;'
            f'border-radius:6px;background:{color}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.52rem;'
            f'color:{_DIM};letter-spacing:0.5px;">{label}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1.2rem;'
            f'font-weight:700;color:{color};">{value}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ─── SECTION 3: THREAT LEVEL DASHBOARD ───
    st.markdown(_section_header("THREAT ASSESSMENT DASHBOARD", _RED), unsafe_allow_html=True)
    _render_threat_dashboard(events)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ─── SECTION 4: LIVE EVENT TICKER ───
    if events:
        _render_live_ticker(events)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Initialize globe variables at broader scope
    globe_fig = None
    globe_clusters = None

    # ─── SECTION 5: 3D INTERACTIVE GLOBE WITH ENHANCED CONTROLS ───
    if events:
        st.markdown(_section_header("INTELLIGENCE GLOBE", _GREEN), unsafe_allow_html=True)

        # Globe controls row
        gc1, gc2, gc3, gc4, gc5 = st.columns([1.2, 1, 1, 1, 1])

        with gc1:
            projection_label = st.selectbox(
                "Globe Projection",
                list(_GLOBE_PROJECTIONS.keys()),
                index=0,
                key="globe_projection",
            )
            projection = _GLOBE_PROJECTIONS[projection_label]

        with gc2:
            show_arcs = st.checkbox("Show Category Arcs", value=True, key="globe_show_arcs")

        with gc3:
            show_impact = st.checkbox("Show Impact Radii", value=True, key="globe_show_impact")

        # Phase 2A: Auto-rotate checkbox
        auto_rotate = st.checkbox("Auto-Rotate", value=False, key="globe_auto_rotate")

        # Center globe on region as default, allow manual override
        bounds = REGION_BOUNDS.get(region, (0, 0, 0, 0))
        default_lat = (bounds[0] + bounds[1]) / 2
        default_lon = (bounds[2] + bounds[3]) / 2

        with gc4:
            globe_lat = st.slider(
                "Rotation Lat", -90.0, 90.0, float(default_lat), 5.0,
                key="globe_rot_lat",
            )

        with gc5:
            globe_lon = st.slider(
                "Rotation Lon", -180.0, 180.0, float(default_lon), 5.0,
                key="globe_rot_lon",
            )

        # Phase 2E: compute clusters for globe overlay
        globe_clusters = None
        if len(events) >= 3:
            globe_clusters = _dbscan_events(events, eps_km=100, min_samples=3, max_events=200)

        globe_fig = _build_globe_figure(
            events, globe_lat, globe_lon,
            projection=projection,
            show_arcs=show_arcs,
            show_impact_radius=show_impact,
            auto_rotate=auto_rotate,
            clusters=globe_clusters,
        )
        if globe_fig:
            st.plotly_chart(globe_fig, use_container_width=True, key="globe_main")
    else:
        st.markdown(
            f'<div style="text-align:center;padding:3rem;color:{_DIM};'
            f'border:1px dashed {_DIM}33;border-radius:8px;">'
            f'No events match current filters.</div>',
            unsafe_allow_html=True,
        )

    # ─── SECTION 6: TIMELINE + CATEGORY DONUT ───
    if events:
        col_tl, col_dn = st.columns([2, 1])

        with col_tl:
            timeline_fig = _build_timeline_chart(events)
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True, key="globe_timeline")

        with col_dn:
            donut_fig = _build_category_donut(events)
            if donut_fig:
                st.plotly_chart(donut_fig, use_container_width=True, key="globe_donut")

    # ─── SECTION 7: TEMPORAL HEATMAP ───
    if events:
        st.markdown(_section_header("TEMPORAL ANALYSIS", _CYAN), unsafe_allow_html=True)
        heatmap_fig = _build_temporal_heatmap(events)
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True, key="globe_temporal_heatmap")

    # ─── SECTION 8: REGIONAL ANALYSIS PANEL ───
    if events:
        st.markdown(_section_header("REGIONAL THREAT ANALYSIS", _AMBER), unsafe_allow_html=True)

        col_reg_chart, col_reg_table = st.columns([1, 1])

        with col_reg_chart:
            regional_fig = _build_regional_bar_chart(events)
            if regional_fig:
                st.plotly_chart(regional_fig, use_container_width=True, key="globe_regional_bar")

        with col_reg_table:
            _render_regional_ranking_table(events)

    # ─── SECTION 9: SOURCE RELIABILITY PANEL ───
    if events:
        st.markdown(_section_header("SOURCE INTELLIGENCE", _CYAN), unsafe_allow_html=True)

        source_fig = _build_source_reliability_chart(events)
        if source_fig:
            st.plotly_chart(source_fig, use_container_width=True, key="globe_source_reliability")
        _render_source_freshness(events)

    # ─── SECTION 10: CASCADING RISK NETWORK ───
    if events and len(events) >= 2:
        st.markdown(_section_header("CASCADING RISK NETWORK", _RED), unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.68rem;color:{_DIM};margin-bottom:8px;">'
            f'Cross-category event pairs within 300km threshold. Compound risk scenarios '
            f'identified through proximity and category interaction analysis.</div>',
            unsafe_allow_html=True,
        )
        _render_cascading_risk_network(events)

    # ─── SECTION 11: EVENT INVESTIGATION PANEL ───
    if events:
        st.markdown(_section_header("EVENT INVESTIGATION", _GREEN), unsafe_allow_html=True)

        # Event selector
        event_options = {
            f"[{i+1}] {ev['title'][:45]} [{ev['category']}] (sev: {ev['severity']:.2f})": i
            for i, ev in enumerate(events[:50])
        }
        selected_label = st.selectbox(
            "Select event to investigate",
            list(event_options.keys()),
            key="globe_event_select",
        )
        selected_idx = event_options.get(selected_label, 0)
        selected_event = events[selected_idx]

        col_detail, col_map = st.columns([2, 1])

        with col_detail:
            # Event card
            st.markdown(_render_event_card(selected_event), unsafe_allow_html=True)

            # Nearby events
            nearby = _get_nearby_events(selected_event, events, 500)
            if nearby:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:{_CYAN};font-weight:600;'
                    f'margin:8px 0 4px 0;">NEARBY EVENTS (within 500km):</div>',
                    unsafe_allow_html=True,
                )
                for nev, dist in nearby[:5]:
                    nev_title = html_module.escape(str(nev["title"]))[:40]
                    nev_cat_color = CATEGORY_COLORS.get(nev["category"], _DIM)
                    st.markdown(
                        f'<div style="font-size:0.7rem;color:{_TEXT};padding:2px 0;">'
                        f'<span style="color:{nev_cat_color};">{html_module.escape(str(nev["category"]))}</span> '
                        f'{nev_title} — <span style="color:{_DIM};">{dist:.0f} km</span></div>',
                        unsafe_allow_html=True,
                    )

            # AI Analysis
            st.markdown(
                _generate_ai_analysis(selected_event, nearby),
                unsafe_allow_html=True,
            )

        with col_map:
            # Mini folium map
            if HAS_FOLIUM:
                try:
                    m = folium.Map(
                        location=[selected_event["lat"], selected_event["lon"]],
                        zoom_start=6,
                        tiles="CartoDB dark_matter",
                    )
                    sev_label_str, sev_c = _severity_label(selected_event["severity"])
                    folium.CircleMarker(
                        [selected_event["lat"], selected_event["lon"]],
                        radius=12,
                        color=sev_c,
                        fill=True, fill_opacity=0.5,
                        popup=html_module.escape(str(selected_event["title"])),
                    ).add_to(m)
                    # Add nearby markers
                    for nev, dist in nearby[:5]:
                        nc = CATEGORY_COLORS.get(nev["category"], _DIM)
                        folium.CircleMarker(
                            [nev["lat"], nev["lon"]],
                            radius=6, color=nc, fill=True, fill_opacity=0.4,
                            popup=html_module.escape(str(nev["title"])),
                        ).add_to(m)
                    st_folium(m, height=350, key="globe_minimap")
                except Exception as exc:
                    logger.warning("Folium mini map failed: %s", exc)
                    st.info("Map unavailable.")
            else:
                st.info("Install folium + streamlit-folium for mini map.")

    # ─── SECTION 12: DENSITY MAP ───
    if events and len(events) > 5:
        st.markdown(_section_header("GLOBAL EVENT DENSITY", _CYAN), unsafe_allow_html=True)
        density_fig = _build_density_map(events)
        if density_fig:
            st.plotly_chart(density_fig, use_container_width=True, key="globe_density")

    # ─── SECTION 12B: SPATIAL CLUSTER ANALYSIS (Phase 2E) ───
    if events and len(events) >= 3:
        st.markdown(_section_header("SPATIAL CLUSTER ANALYSIS", _AMBER), unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.68rem;color:{_DIM};margin-bottom:8px;">'
            f'DBSCAN clustering with haversine distance. eps=100km, min_samples=3. '
            f'Identifies geographic hotspots of correlated events.</div>',
            unsafe_allow_html=True,
        )
        # Use pre-computed clusters if available, else compute
        event_clusters = (globe_clusters if globe_clusters is not None
                          else _dbscan_events(events, eps_km=100, min_samples=3, max_events=200))
        _render_cluster_summary(event_clusters)

    # ─── SECTION 13: CLASSIFIED INTELLIGENCE SUMMARY ───
    st.markdown(_section_header("INTELLIGENCE SUMMARY", _GREEN), unsafe_allow_html=True)

    # Classified header
    st.markdown(
        f'<div style="text-align:center;margin-bottom:6px;">'
        f'<span style="background:{_RED};color:#fff;padding:3px 18px;font-size:0.6rem;'
        f'font-weight:900;letter-spacing:3px;font-family:JetBrains Mono,monospace;'
        f'border-radius:2px;">CLASSIFIED — SITUATIONAL ANALYSIS</span></div>',
        unsafe_allow_html=True,
    )

    summary = _generate_intelligence_summary(events, timespan)
    st.markdown(
        f'<div style="border:1px solid {_GREEN}22;border-radius:8px;padding:18px;'
        f'background:{_GREEN}05;font-family:JetBrains Mono,monospace;'
        f'font-size:0.76rem;color:{_TEXT};line-height:1.7;">{summary}</div>',
        unsafe_allow_html=True,
    )

    # ─── SECTION 14: DATA QUALITY PANEL ───
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.7rem;color:{_DIM};font-weight:600;'
        f'letter-spacing:1px;margin-bottom:4px;">DATA QUALITY METRICS</div>',
        unsafe_allow_html=True,
    )
    _render_data_quality_panel(events, raw_count)

    # ─── FOOTER ───
    st.markdown(
        f'<div style="text-align:center;padding:1.2rem 0 0.5rem 0;'
        f'font-family:JetBrains Mono,monospace;font-size:0.55rem;color:{_DIM};'
        f'letter-spacing:1px;border-top:1px solid {_DIM}15;margin-top:1rem;">'
        f'TERRASCOUT AI &bull; GLOBAL SITUATIONAL AWARENESS &bull; '
        f'7 API SOURCES &bull; CLASSIFICATION: OPERATIONAL INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )
