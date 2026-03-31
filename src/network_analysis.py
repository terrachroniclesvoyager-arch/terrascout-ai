"""
Network & Connectivity Analysis module for TerraScout AI.
Analyzes road networks, transport connectivity, and reachability from any point.
Six dimensions: Road Network Graph, Intersection Density, Bridge & Tunnel Crossings,
Railway Connectivity, Water Crossings, and Settlement Connectivity.
Uses Overpass API exclusively (free, no API key).
"""

import math
import logging
from collections import Counter

import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
except ImportError:
    folium = None

try:
    from streamlit.components.v1 import html as st_html
except ImportError:
    st_html = None

from src.overpass_client import query_overpass
from src.map_factory import MapFactory

logger = logging.getLogger(__name__)

# ── Theme ────────────────────────────────────────────────────────────────────
CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_SEC = "#8b97b0"
CLR_ACCENT = "#06b6d4"
CLR_SAFE = "#22c55e"
CLR_WARN = "#f59e0b"
CLR_DANGER = "#ef4444"

DIMENSIONS = [
    ("Road Network", "#3b82f6", "Road density and type diversity within 5 km"),
    ("Intersection Density", "#8b5cf6", "Junction density indicating grid connectivity"),
    ("Bridge & Tunnel", "#f97316", "Crossings enabling passage over/under obstacles"),
    ("Railway Access", "#ef4444", "Rail lines and stations within 10 km"),
    ("Water Crossings", "#06b6d4", "Rivers and canals that may impede movement"),
    ("Settlement Reach", "#10b981", "Settlements reachable within 20 km"),
]
DIM_NAMES = [d[0] for d in DIMENSIONS]
DIM_COLORS = [d[1] for d in DIMENSIONS]
DIM_KEYS = ["road_network", "intersections", "bridges_tunnels",
            "railway", "water_crossings", "settlements"]

ROAD_COLORS = {
    "motorway": "#ef4444", "trunk": "#f97316", "primary": "#f59e0b",
    "secondary": "#eab308", "tertiary": "#84cc16", "residential": "#a3a3a3",
    "motorway_link": "#ef4444", "trunk_link": "#f97316", "primary_link": "#f59e0b",
    "secondary_link": "#eab308", "tertiary_link": "#84cc16",
}

CONN_CLASSES = [
    (8.5, "EXCELLENT", CLR_SAFE, "Superb multi-modal connectivity with dense road grid"),
    (6.5, "GOOD", "#3b82f6", "Strong network with multiple route options"),
    (4.5, "MODERATE", CLR_WARN, "Adequate connections but some gaps exist"),
    (2.5, "POOR", "#f97316", "Limited connectivity, few alternative routes"),
    (0.0, "ISOLATED", CLR_DANGER, "Very sparse network, remote or disconnected area"),
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hav(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    r = 6371.0
    dl, dn = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dl / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)) * math.sin(dn / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _area(radius_m):
    return math.pi * (radius_m / 1000.0) ** 2


def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, v))


def _elems(data):
    if isinstance(data, dict) and "_error" not in data:
        return data.get("elements", [])
    return []


def _stat(label, value, color=CLR_TEXT):
    return (f'<div style="display:flex;justify-content:space-between;padding:3px 0;'
            f'border-bottom:1px solid {CLR_BORDER}33;">'
            f'<span style="color:{CLR_SEC};font-size:13px;">{label}</span>'
            f'<span style="color:{color};font-weight:600;font-size:13px;">{value}</span></div>')


def _card(value, label, color):
    return (f'<div style="text-align:center;background:{CLR_BG};border-radius:10px;'
            f'padding:12px 8px;border:1px solid {color}55;margin-bottom:4px;">'
            f'<div style="font-size:30px;font-weight:bold;color:{color};">'
            f'{value}<span style="font-size:12px;color:{CLR_SEC};">/10</span></div>'
            f'<div style="color:{CLR_TEXT};font-size:12px;font-weight:600;'
            f'margin-top:3px;">{label}</div></div>')


def _panel(title, color, rows_html):
    return (f'<div style="background:{CLR_SURFACE};border-radius:8px;padding:12px;'
            f'border-left:3px solid {color};">'
            f'<div style="color:{CLR_TEXT};font-weight:bold;margin-bottom:6px;">'
            f'{title}</div>{rows_html}</div>')


# ── Data Fetchers (cached, error-handled) ────────────────────────────────────

@st.cache_data(ttl=900)
def _fetch_roads(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    way["highway"~"motorway|trunk|primary|secondary|tertiary|residential"](around:5000,{lat},{lon});
    out body;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Road fetch failed: %s", e)
        return {}


@st.cache_data(ttl=900)
def _fetch_road_ways_3km(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    way["highway"~"motorway|trunk|primary|secondary|tertiary|residential"](around:3000,{lat},{lon});
    out body;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Road ways 3km fetch failed: %s", e)
        return {}


@st.cache_data(ttl=900)
def _fetch_bridges_tunnels(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    (way["bridge"="yes"](around:10000,{lat},{lon});
     way["tunnel"="yes"](around:10000,{lat},{lon}););
    out center tags;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Bridge/tunnel fetch failed: %s", e)
        return {}


@st.cache_data(ttl=900)
def _fetch_railway(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    (way["railway"~"rail|light_rail|subway"](around:10000,{lat},{lon});
     node["railway"="station"](around:10000,{lat},{lon}););
    out center tags;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Railway fetch failed: %s", e)
        return {}


@st.cache_data(ttl=900)
def _fetch_waterways(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    way["waterway"~"river|canal"](around:5000,{lat},{lon});
    out center tags;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Waterway fetch failed: %s", e)
        return {}


@st.cache_data(ttl=900)
def _fetch_settlements(lat: float, lon: float) -> dict:
    query = f"""[out:json][timeout:30];
    node["place"~"city|town|village|hamlet"](around:20000,{lat},{lon});
    out tags;"""
    try:
        return query_overpass(query, timeout=10) or {}
    except Exception as e:
        logger.warning("Settlement fetch failed: %s", e)
        return {}


# ── Scoring ──────────────────────────────────────────────────────────────────

def _score_roads(data):
    els = _elems(data)
    rc = Counter()
    for e in els:
        hw = e.get("tags", {}).get("highway", "")
        if hw in ROAD_COLORS:
            rc[hw] += 1
    total = sum(rc.values())
    density = total / max(_area(5000), 0.01)
    diversity = len(rc)
    major = any(rc.get(t, 0) > 0 for t in ("motorway", "trunk", "primary"))
    raw = density * 1.2 + diversity * 0.6 + (1.5 if major else 0)
    return {"score": round(_clamp(raw), 1), "total_ways": total,
            "road_counts": dict(rc), "density": round(density, 2),
            "diversity": diversity, "has_major": major}


def _score_intersections(data):
    usage = Counter()
    for e in _elems(data):
        if e.get("type") == "way":
            for nid in e.get("nodes", []):
                usage[nid] += 1
    ix = sum(1 for c in usage.values() if c >= 2)
    de = sum(1 for c in usage.values() if c == 1)
    total = len(usage)
    area = max(_area(3000), 0.01)
    dens = ix / area
    raw = min(10, dens * 0.15 + (ix / max(total, 1)) * 12)
    return {"score": round(_clamp(raw), 1), "intersection_count": ix,
            "dead_end_count": de, "total_nodes": total,
            "density": round(dens, 2)}


def _score_bt(data):
    bridges, tunnels = [], []
    for e in _elems(data):
        tags = e.get("tags", {})
        c = e.get("center", {})
        info = {"name": tags.get("name", "Unnamed"),
                "lat": c.get("lat"), "lon": c.get("lon"),
                "highway": tags.get("highway", "")}
        if tags.get("bridge") == "yes":
            bridges.append(info)
        if tags.get("tunnel") == "yes":
            tunnels.append(info)
    bc, tc = len(bridges), len(tunnels)
    raw = min(10, (bc + tc) * 0.4 + min(bc, 10) * 0.3 + min(tc, 5) * 0.5)
    return {"score": round(_clamp(raw), 1), "bridge_count": bc,
            "tunnel_count": tc, "total": bc + tc,
            "bridges": bridges[:30], "tunnels": tunnels[:20]}


def _score_rail(data):
    lines, stations, rtypes = 0, [], Counter()
    for e in _elems(data):
        tags = e.get("tags", {})
        if e.get("type") == "way" and tags.get("railway"):
            lines += 1
            rtypes[tags["railway"]] += 1
        elif e.get("type") == "node" and tags.get("railway") == "station":
            stations.append({"name": tags.get("name", "Unnamed"),
                             "lat": e.get("lat"), "lon": e.get("lon"),
                             "operator": tags.get("operator", "")})
    raw = min(lines, 20) * 0.25 + len(stations) * 1.2 + len(rtypes) * 0.8
    return {"score": round(_clamp(raw), 1), "rail_lines": lines,
            "station_count": len(stations), "rail_types": dict(rtypes),
            "stations": stations[:25]}


def _score_water(data):
    riv, can, details = 0, 0, []
    for e in _elems(data):
        tags = e.get("tags", {})
        ww = tags.get("waterway", "")
        c = e.get("center", {})
        if ww == "river":
            riv += 1
        elif ww == "canal":
            can += 1
        if c:
            details.append({"name": tags.get("name", "Unnamed"), "type": ww,
                            "lat": c.get("lat"), "lon": c.get("lon")})
    total = riv + can
    if total == 0:
        raw = 8.0
    elif total <= 3:
        raw = 7.0
    elif total <= 8:
        raw = 5.0
    elif total <= 15:
        raw = 3.0
    else:
        raw = 1.5
    raw = min(10, raw + can * 0.3)
    return {"score": round(_clamp(raw), 1), "rivers": riv, "canals": can,
            "total": total, "details": details[:30]}


def _score_settle(data, lat, lon):
    items, pt = [], Counter()
    for e in _elems(data):
        tags = e.get("tags", {})
        sl, sn = e.get("lat"), e.get("lon")
        if sl and sn:
            d = _hav(lat, lon, sl, sn)
            items.append({"name": tags.get("name", "Unnamed"),
                          "type": tags.get("place", ""), "lat": sl, "lon": sn,
                          "dist_km": round(d, 1), "pop": tags.get("population", "")})
            pt[tags.get("place", "")] += 1
    items.sort(key=lambda s: s["dist_km"])
    raw = min(10, pt.get("city", 0) * 3 + pt.get("town", 0) * 1.5
              + pt.get("village", 0) * 0.5 + pt.get("hamlet", 0) * 0.2)
    return {"score": round(_clamp(raw), 1), "total": len(items),
            "types": dict(pt), "items": items[:40],
            "nearest": items[0] if items else None}


# ── Aggregator ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=900)
def _analyse(lat: float, lon: float) -> dict:
    d1 = _score_roads(_fetch_roads(lat, lon))
    d2 = _score_intersections(_fetch_road_ways_3km(lat, lon))
    d3 = _score_bt(_fetch_bridges_tunnels(lat, lon))
    d4 = _score_rail(_fetch_railway(lat, lon))
    d5 = _score_water(_fetch_waterways(lat, lon))
    d6 = _score_settle(_fetch_settlements(lat, lon), lat, lon)

    scores = [d1["score"], d2["score"], d3["score"],
              d4["score"], d5["score"], d6["score"]]
    weights = [0.25, 0.15, 0.15, 0.20, 0.10, 0.15]
    overall = round(sum(s * w for s, w in zip(scores, weights)), 1)

    cls, ccol, cdesc = "ISOLATED", CLR_DANGER, ""
    for thr, lb, co, ds in CONN_CLASSES:
        if overall >= thr:
            cls, ccol, cdesc = lb, co, ds
            break

    return {"road_network": d1, "intersections": d2, "bridges_tunnels": d3,
            "railway": d4, "water_crossings": d5, "settlements": d6,
            "scores": scores, "overall": overall,
            "cls": cls, "ccol": ccol, "cdesc": cdesc}


# ── Charts ───────────────────────────────────────────────────────────────────

def _radar(scores):
    vals = scores + [scores[0]]
    labs = DIM_NAMES + [DIM_NAMES[0]]
    cols = DIM_COLORS + [DIM_COLORS[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=labs, fill="toself",
        fillcolor="rgba(6,182,212,0.15)",
        line=dict(color=CLR_ACCENT, width=2),
        marker=dict(size=7, color=cols), name="Score",
        hovertemplate="%{theta}: %{r}/10<extra></extra>"))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10],
                            gridcolor="rgba(51,51,85,0.33)",
                            tickfont=dict(size=10, color=CLR_SEC)),
            angularaxis=dict(gridcolor="rgba(51,51,85,0.33)",
                             tickfont=dict(size=11, color=CLR_TEXT)),
            bgcolor=CLR_BG),
        showlegend=False, margin=dict(t=30, b=30, l=60, r=60),
        height=380, paper_bgcolor=CLR_BG, font=dict(color=CLR_TEXT))
    return fig


def _bar(labels, values, colors, height=240, key=None, ytitle=""):
    fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors,
                                 text=values, textposition="auto")])
    fig.update_layout(height=height, margin=dict(t=10, b=40, l=40, r=20),
                      paper_bgcolor=CLR_BG, plot_bgcolor=CLR_BG,
                      font=dict(color=CLR_TEXT, size=11),
                      xaxis=dict(gridcolor="rgba(51,51,85,0.2)"),
                      yaxis=dict(gridcolor="rgba(51,51,85,0.2)", title=ytitle))
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── Map ──────────────────────────────────────────────────────────────────────

def _build_map(lat, lon, res):
    if folium is None:
        return None
    m = MapFactory.create_base_map(center=(lat, lon), zoom=12)
    folium.Marker([lat, lon], popup="<b>Analysis Center</b>",
                  icon=folium.Icon(color="red", icon="crosshairs",
                                   prefix="fa")).add_to(m)

    # Bridges
    bg = folium.FeatureGroup(name="Bridges", show=True)
    for b in res["bridges_tunnels"].get("bridges", [])[:25]:
        if b.get("lat") and b.get("lon"):
            folium.CircleMarker([b["lat"], b["lon"]], radius=5, color="#f97316",
                                fill=True, fill_color="#f97316", fill_opacity=0.8,
                                popup=f"<b>Bridge</b><br/>{b['name']}").add_to(bg)
    bg.add_to(m)

    # Tunnels
    tg = folium.FeatureGroup(name="Tunnels", show=True)
    for t in res["bridges_tunnels"].get("tunnels", [])[:15]:
        if t.get("lat") and t.get("lon"):
            folium.CircleMarker([t["lat"], t["lon"]], radius=5, color="#6366f1",
                                fill=True, fill_color="#6366f1", fill_opacity=0.8,
                                popup=f"<b>Tunnel</b><br/>{t['name']}").add_to(tg)
    tg.add_to(m)

    # Stations
    sg = folium.FeatureGroup(name="Railway Stations", show=True)
    for s in res["railway"].get("stations", [])[:20]:
        if s.get("lat") and s.get("lon"):
            folium.Marker([s["lat"], s["lon"]],
                          popup=f"<b>{s['name']}</b><br/>{s.get('operator','')}",
                          icon=folium.Icon(color="darkred", icon="train",
                                           prefix="fa")).add_to(sg)
    sg.add_to(m)

    # Waterways
    wg = folium.FeatureGroup(name="Waterways", show=True)
    for w in res["water_crossings"].get("details", [])[:20]:
        if w.get("lat") and w.get("lon"):
            folium.CircleMarker([w["lat"], w["lon"]], radius=4, color="#06b6d4",
                                fill=True, fill_color="#06b6d4", fill_opacity=0.7,
                                popup=f"<b>{w['type'].title()}</b><br/>{w['name']}"
                                ).add_to(wg)
    wg.add_to(m)

    # Settlements
    stg = folium.FeatureGroup(name="Settlements", show=True)
    r_map = {"city": 10, "town": 7, "village": 5, "hamlet": 3}
    c_map = {"city": "#10b981", "town": "#22c55e",
             "village": "#86efac", "hamlet": "#bbf7d0"}
    for s in res["settlements"].get("items", [])[:30]:
        if s.get("lat") and s.get("lon"):
            pt = s.get("type", "village")
            folium.CircleMarker(
                [s["lat"], s["lon"]], radius=r_map.get(pt, 4),
                color=c_map.get(pt, "#86efac"), fill=True,
                fill_color=c_map.get(pt, "#86efac"), fill_opacity=0.8,
                popup=f"<b>{s['name']}</b><br/>{pt.title()} - {s['dist_km']} km"
            ).add_to(stg)
    stg.add_to(m)

    # Radius circles
    for rad, lbl, clr in [(5000, "5 km (Roads)", "#3b82f6"),
                           (10000, "10 km (Rail/Bridges)", "#f97316"),
                           (20000, "20 km (Settlements)", "#10b981")]:
        folium.Circle([lat, lon], radius=rad, color=clr, fill=False,
                      weight=1, dash_array="6", popup=lbl).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ── Detail Panels ────────────────────────────────────────────────────────────

def _detail_roads(d):
    st.markdown(_panel("Road Network Details", DIM_COLORS[0],
        _stat("Total Road Ways", d["total_ways"])
        + _stat("Road Density", f"{d['density']} ways/km\u00b2")
        + _stat("Type Diversity", f"{d['diversity']} types")
        + _stat("Has Major Road", "Yes" if d["has_major"] else "No",
                CLR_SAFE if d["has_major"] else CLR_WARN)),
        unsafe_allow_html=True)
    rc = d.get("road_counts", {})
    if rc:
        _bar([k.replace("_", " ").title() for k in rc],
             list(rc.values()),
             [ROAD_COLORS.get(k, "#888") for k in rc],
             height=240, key="netana_road_chart")


def _detail_ix(d):
    st.markdown(_panel("Intersection Analysis", DIM_COLORS[1],
        _stat("Intersections (2+ ways)", d["intersection_count"])
        + _stat("Dead-end Nodes", d["dead_end_count"])
        + _stat("Total Network Nodes", d["total_nodes"])
        + _stat("Intersection Density", f"{d['density']}/km\u00b2")),
        unsafe_allow_html=True)


def _detail_bt(d):
    st.markdown(_panel("Bridge & Tunnel Crossings", DIM_COLORS[2],
        _stat("Bridges", d["bridge_count"], "#f97316")
        + _stat("Tunnels", d["tunnel_count"], "#6366f1")
        + _stat("Total Crossings", d["total"])),
        unsafe_allow_html=True)
    named = [b["name"] for b in d.get("bridges", []) if b["name"] != "Unnamed"]
    if named:
        st.markdown(f"<div style='color:{CLR_SEC};font-size:12px;margin-top:4px;'>"
                    f"<b>Named bridges:</b> {', '.join(named[:8])}</div>",
                    unsafe_allow_html=True)


def _detail_rail(d):
    st.markdown(_panel("Railway Connectivity", DIM_COLORS[3],
        _stat("Rail Line Segments", d["rail_lines"])
        + _stat("Stations", d["station_count"], "#ef4444")
        + _stat("Rail Types", ", ".join(d.get("rail_types", {}).keys()) or "None")),
        unsafe_allow_html=True)
    snames = [s["name"] for s in d.get("stations", [])[:10]]
    if snames:
        st.markdown(f"<div style='color:{CLR_SEC};font-size:12px;margin-top:4px;'>"
                    f"<b>Stations:</b> {', '.join(snames)}</div>",
                    unsafe_allow_html=True)


def _detail_water(d):
    st.markdown(_panel("Water Crossing Obstacles", DIM_COLORS[4],
        _stat("Rivers", d["rivers"], "#06b6d4")
        + _stat("Canals", d["canals"], "#0891b2")
        + _stat("Total Waterways", d["total"])),
        unsafe_allow_html=True)


def _detail_settle(d):
    pt = d.get("types", {})
    n = d.get("nearest")
    ntxt = f"{n['name']} ({n['dist_km']} km)" if n else "None"
    st.markdown(_panel("Settlement Connectivity (20 km)", DIM_COLORS[5],
        _stat("Total Settlements", d["total"])
        + _stat("Cities", pt.get("city", 0))
        + _stat("Towns", pt.get("town", 0))
        + _stat("Villages", pt.get("village", 0))
        + _stat("Hamlets", pt.get("hamlet", 0))
        + _stat("Nearest", ntxt, CLR_SAFE)),
        unsafe_allow_html=True)
    items = d.get("items", [])[:8]
    if items:
        _bar([s["name"][:16] for s in items],
             [s["dist_km"] for s in items],
             [CLR_SAFE if s["type"] in ("city", "town") else "#86efac"
              for s in items],
             height=220, key="netana_settle_chart", ytitle="Distance (km)")


# ── Main Entry Point ────────────────────────────────────────────────────────

def render_network_analysis_tab():
    """Render the Network & Connectivity Analysis tab."""
    st.markdown("## Network & Connectivity Analysis")
    st.caption("Road network, transport links & reachability assessment")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, min_value=-90.0,
                          max_value=90.0, format="%.4f", key="netana_lat")
    lon = c2.number_input("Longitude", value=12.4964, min_value=-180.0,
                          max_value=180.0, format="%.4f", key="netana_lon")

    if not st.button("Analyze Network", type="primary",
                     use_container_width=True, key="netana_btn"):
        st.info("Enter coordinates and click **Analyze Network** to begin.")
        return

    with st.spinner("Mapping network connectivity... (querying 6 dimensions)"):
        res = _analyse(lat, lon)
    if not res:
        st.error("Analysis failed. Please try again or adjust coordinates.")
        return

    # ── Overall banner ──
    ov, cls, ccol, cdesc = res["overall"], res["cls"], res["ccol"], res["cdesc"]
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});'
        f'border-radius:14px;padding:22px;margin:10px 0 18px;'
        f'border:2px solid {ccol}66;text-align:center;">'
        f'<div style="font-size:13px;color:{CLR_SEC};text-transform:uppercase;'
        f'letter-spacing:2px;margin-bottom:4px;">Network Connectivity Index</div>'
        f'<div style="font-size:52px;font-weight:bold;color:{ccol};">'
        f'{ov}<span style="font-size:18px;color:{CLR_SEC};">/10</span></div>'
        f'<div style="display:inline-block;background:{ccol}22;border:1px solid {ccol};'
        f'border-radius:20px;padding:3px 16px;margin-top:6px;">'
        f'<span style="color:{ccol};font-weight:bold;font-size:15px;'
        f'letter-spacing:1px;">{cls}</span></div>'
        f'<div style="color:{CLR_SEC};font-size:12px;margin-top:6px;">{cdesc}</div>'
        f'</div>', unsafe_allow_html=True)

    # ── Score cards row ──
    cols = st.columns(6)
    for i, col in enumerate(cols):
        with col:
            st.markdown(_card(res[DIM_KEYS[i]]["score"], DIM_NAMES[i],
                              DIM_COLORS[i]), unsafe_allow_html=True)

    # ── Metrics summary ──
    mc = st.columns(6)
    mc[0].metric("Road Ways", res["road_network"]["total_ways"])
    mc[1].metric("Intersections", res["intersections"]["intersection_count"])
    mc[2].metric("Bridges", res["bridges_tunnels"]["bridge_count"])
    mc[3].metric("Rail Stations", res["railway"]["station_count"])
    mc[4].metric("Waterways", res["water_crossings"]["total"])
    mc[5].metric("Settlements", res["settlements"]["total"])

    # ── Radar chart ──
    st.markdown("### Connectivity Profile")
    st.plotly_chart(_radar(res["scores"], key="netana_pchart1"), use_container_width=True,
                    key="netana_radar")

    # ── Dimension details ──
    st.markdown("### Dimension Details")
    lc, rc = st.columns(2)
    with lc:
        with st.expander("Road Network Graph", expanded=True):
            _detail_roads(res["road_network"])
        with st.expander("Bridge & Tunnel Crossings"):
            _detail_bt(res["bridges_tunnels"])
        with st.expander("Water Crossings"):
            _detail_water(res["water_crossings"])
    with rc:
        with st.expander("Intersection Density", expanded=True):
            _detail_ix(res["intersections"])
        with st.expander("Railway Connectivity"):
            _detail_rail(res["railway"])
        with st.expander("Settlement Connectivity"):
            _detail_settle(res["settlements"])

    # ── Map ──
    st.markdown("### Connectivity Map")
    st.caption("Bridges (orange) | Tunnels (purple) | Stations (red) "
               "| Waterways (cyan) | Settlements (green)")
    _net_map = _build_map(lat, lon, res)
    if _net_map is not None and st_html is not None:
        st_html(_net_map._repr_html_(), height=500)
    else:
        st.warning("Install `folium` for interactive map: `pip install folium`")

    # ── Raw data ──
    with st.expander("Raw Analysis Data"):
        st.json({
            "coordinates": {"lat": lat, "lon": lon},
            "overall_index": ov, "classification": cls,
            "scores": {DIM_NAMES[i]: res[DIM_KEYS[i]]["score"] for i in range(6)},
            "road_network": {"ways": res["road_network"]["total_ways"],
                             "density": res["road_network"]["density"],
                             "diversity": res["road_network"]["diversity"],
                             "has_major": res["road_network"]["has_major"]},
            "intersections": {"count": res["intersections"]["intersection_count"],
                              "dead_ends": res["intersections"]["dead_end_count"],
                              "per_sqkm": res["intersections"]["density"]},
            "bridges_tunnels": {"bridges": res["bridges_tunnels"]["bridge_count"],
                                "tunnels": res["bridges_tunnels"]["tunnel_count"]},
            "railway": {"lines": res["railway"]["rail_lines"],
                        "stations": res["railway"]["station_count"],
                        "types": res["railway"]["rail_types"]},
            "water": {"rivers": res["water_crossings"]["rivers"],
                      "canals": res["water_crossings"]["canals"]},
            "settlements": {"total": res["settlements"]["total"],
                            "types": res["settlements"]["types"],
                            "nearest": (res["settlements"]["nearest"]["name"]
                                        if res["settlements"]["nearest"] else "None")},
        })
