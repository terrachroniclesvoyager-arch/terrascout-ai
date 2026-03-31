"""
Advanced Elevation Profiler module for TerraScout AI.
Deep terrain elevation analysis: cross-section profiles, slope maps,
aspect analysis, drainage pattern estimation, and terrain statistics.
Uses the free Open Topo Data SRTM30m API (no key required).
"""

import math
import logging
from typing import List, Optional, Tuple, Dict, Any

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
API_BASE = "https://api.opentopodata.org/v1/srtm30m"
MAX_BATCH = 100

_ELEV_CLASSES = [
    ("Coastal / Sea-level", 0, 50, "#3b82f6"),
    ("Lowland", 50, 200, "#22c55e"),
    ("Hills", 200, 500, "#84cc16"),
    ("Montane", 500, 1500, "#f59e0b"),
    ("Alpine", 1500, 3000, "#f97316"),
    ("Extreme / Nival", 3000, 99999, "#ef4444"),
]

_SLOPE_CLASSES = [
    ("Flat", 0, 2, "#22c55e"),
    ("Gentle", 2, 5, "#84cc16"),
    ("Moderate", 5, 10, "#f59e0b"),
    ("Steep", 10, 20, "#f97316"),
    ("Very Steep", 20, 35, "#ef4444"),
    ("Cliff", 35, 90, "#dc2626"),
]

_ASPECT_DIRS = [
    ("N", 337.5, 360.0), ("N", 0.0, 22.5),
    ("NE", 22.5, 67.5), ("E", 67.5, 112.5),
    ("SE", 112.5, 157.5), ("S", 157.5, 202.5),
    ("SW", 202.5, 247.5), ("W", 247.5, 292.5),
    ("NW", 292.5, 337.5),
]

_CLR = {
    "bg": "#1a1a2e", "card": "rgba(26,26,46,0.85)", "border": "#2d5a3d",
    "text": "#e8ecf4", "muted": "#8b97b0", "accent": "#22c55e",
}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _deg_per_km_lat() -> float:
    return 1.0 / 111.0


def _deg_per_km_lon(lat: float) -> float:
    return 1.0 / (111.0 * math.cos(math.radians(lat)))


def _classify_elevation(elev: float) -> Tuple[str, str]:
    for label, lo, hi, color in _ELEV_CLASSES:
        if lo <= elev < hi:
            return label, color
    return "Unknown", "#6b7280"


def _classify_slope(slope_deg: float) -> Tuple[str, str]:
    for label, lo, hi, color in _SLOPE_CLASSES:
        if lo <= slope_deg < hi:
            return label, color
    return "Cliff", "#dc2626"


def _aspect_label(aspect_deg: float) -> str:
    """Convert math-convention aspect to compass label."""
    geo = (90.0 - aspect_deg) % 360.0
    for label, lo, hi in _ASPECT_DIRS:
        if lo <= geo < hi:
            return label
    return "N"


# ---------------------------------------------------------------------------
# Cached API functions
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_elevations_batch(locations_str: str) -> List[Optional[float]]:
    """Fetch elevations for a pipe-separated locations string (max 100)."""
    try:
        resp = requests.get(f"{API_BASE}?locations={locations_str}", timeout=10)
        resp.raise_for_status()
        return [r.get("elevation") for r in resp.json().get("results", [])]
    except Exception as exc:
        logger.warning("Open Topo Data batch fetch failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_single_elevation(lat: float, lon: float) -> Optional[float]:
    """Fetch the elevation of a single point."""
    try:
        resp = requests.get(f"{API_BASE}?locations={lat},{lon}", timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0].get("elevation") if results else None
    except Exception as exc:
        logger.warning("Elevation fetch failed for (%.4f, %.4f): %s", lat, lon, exc)
        return None


# ---------------------------------------------------------------------------
# Point generation & batched fetch
# ---------------------------------------------------------------------------

def _linspace_points(lat0: float, lon0: float, lat1: float, lon1: float,
                     n: int = 20) -> List[Tuple[float, float]]:
    """Generate *n* evenly spaced points along a line."""
    return [
        (round(lat0 + (lat1 - lat0) * i / max(n - 1, 1), 6),
         round(lon0 + (lon1 - lon0) * i / max(n - 1, 1), 6))
        for i in range(n)
    ]


def _grid_points(lat_c: float, lon_c: float, r_deg: float,
                 gs: int = 10) -> Tuple[List[Tuple[float, float]], List[float], List[float]]:
    """Generate a gs x gs square grid centred on (lat_c, lon_c)."""
    lat_ticks = [round(lat_c - r_deg + 2 * r_deg * i / max(gs - 1, 1), 6)
                 for i in range(gs)]
    lon_ticks = [round(lon_c - r_deg + 2 * r_deg * i / max(gs - 1, 1), 6)
                 for i in range(gs)]
    coords = [(la, lo) for la in lat_ticks for lo in lon_ticks]
    return coords, lat_ticks, lon_ticks


def _fetch_points(coords: List[Tuple[float, float]]) -> List[Optional[float]]:
    """Fetch elevations for arbitrary number of points (auto-batched)."""
    elevs: List[Optional[float]] = []
    for i in range(0, len(coords), MAX_BATCH):
        batch = coords[i:i + MAX_BATCH]
        loc_str = "|".join(f"{la},{lo}" for la, lo in batch)
        result = _fetch_elevations_batch(loc_str)
        elevs.extend(result if result else [None] * len(batch))
    return elevs


# ---------------------------------------------------------------------------
# Slope & Aspect computation
# ---------------------------------------------------------------------------

def _compute_slope_aspect(
    grid: List[List[float]], lat_ticks: List[float], lon_ticks: List[float],
) -> Tuple[List[List[float]], List[List[float]]]:
    """Finite-difference slope (deg) and aspect (deg) from an elevation grid."""
    rows, cols = len(grid), len(grid[0]) if grid else 0
    slope_g = [[0.0] * cols for _ in range(rows)]
    aspect_g = [[0.0] * cols for _ in range(rows)]

    dlat_m = _haversine_km(lat_ticks[0], lon_ticks[0],
                           lat_ticks[-1], lon_ticks[0]) * 1000.0 / max(rows - 1, 1)
    dlon_m = _haversine_km(lat_ticks[0], lon_ticks[0],
                           lat_ticks[0], lon_ticks[-1]) * 1000.0 / max(cols - 1, 1)

    for r in range(rows):
        for c in range(cols):
            z = grid[r][c]
            # dz/dx
            if c == 0:
                dz_dx = (grid[r][c + 1] - z) / dlon_m if dlon_m else 0.0
            elif c == cols - 1:
                dz_dx = (z - grid[r][c - 1]) / dlon_m if dlon_m else 0.0
            else:
                dz_dx = (grid[r][c + 1] - grid[r][c - 1]) / (2.0 * dlon_m) if dlon_m else 0.0
            # dz/dy
            if r == 0:
                dz_dy = (grid[r + 1][c] - z) / dlat_m if dlat_m else 0.0
            elif r == rows - 1:
                dz_dy = (z - grid[r - 1][c]) / dlat_m if dlat_m else 0.0
            else:
                dz_dy = (grid[r + 1][c] - grid[r - 1][c]) / (2.0 * dlat_m) if dlat_m else 0.0

            mag = math.sqrt(dz_dx ** 2 + dz_dy ** 2)
            slope_g[r][c] = round(math.degrees(math.atan2(mag, 1.0)), 2)
            asp = math.degrees(math.atan2(-dz_dy, dz_dx))
            aspect_g[r][c] = round(asp % 360.0, 2)

    return slope_g, aspect_g


# ---------------------------------------------------------------------------
# Terrain statistics
# ---------------------------------------------------------------------------

def _terrain_statistics(elevations: List[Optional[float]]) -> Dict[str, Any]:
    """Compute summary statistics from a flat elevation list."""
    valid = [e for e in elevations if e is not None]
    if not valid:
        return {}
    n, mn, mx = len(valid), min(valid), max(valid)
    mean = sum(valid) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in valid) / n)
    return {
        "count": n, "min": round(mn, 1), "max": round(mx, 1),
        "mean": round(mean, 1), "std_dev": round(std, 1),
        "relief": round(mx - mn, 1), "roughness_index": round(std, 2),
    }


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _profile_chart(distances: List[float], elevations: List[float],
                   title: str, color: str = "#22c55e") -> go.Figure:
    """Line chart for an elevation profile cross-section."""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=distances, y=elevations, mode="lines+markers",
        fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.18)",
        line=dict(color=color, width=2.5), marker=dict(size=5, color=color),
        hovertemplate="Distance: %{x:.2f} km<br>Elevation: %{y:.1f} m<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=_CLR["text"])),
        xaxis_title="Distance (km)", yaxis_title="Elevation (m)",
        template="plotly_dark", paper_bgcolor=_CLR["bg"],
        plot_bgcolor="rgba(0,0,0,0)", height=340,
        margin=dict(l=50, r=30, t=50, b=50),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    )
    return fig


def _slope_heatmap(slope_grid: List[List[float]],
                   lat_ticks: List[float], lon_ticks: List[float]) -> go.Figure:
    """Heatmap for slope analysis."""
    fig = go.Figure(data=go.Heatmap(
        z=slope_grid,
        x=[round(lo, 4) for lo in lon_ticks],
        y=[round(la, 4) for la in lat_ticks],
        colorscale=[[0, "#22c55e"], [0.06, "#84cc16"], [0.15, "#f59e0b"],
                     [0.3, "#f97316"], [0.55, "#ef4444"], [1.0, "#dc2626"]],
        colorbar=dict(title="Slope (\u00b0)", ticksuffix="\u00b0"),
        hovertemplate="Lat: %{y:.4f}<br>Lon: %{x:.4f}<br>Slope: %{z:.1f}\u00b0<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Slope Analysis Heatmap", font=dict(size=15, color=_CLR["text"])),
        xaxis_title="Longitude", yaxis_title="Latitude",
        template="plotly_dark", paper_bgcolor=_CLR["bg"],
        plot_bgcolor="rgba(0,0,0,0)", height=420,
        margin=dict(l=60, r=30, t=50, b=50),
    )
    return fig


def _aspect_rose(aspect_counts: Dict[str, int]) -> go.Figure:
    """Compass-rose bar polar chart for aspect distribution."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    colors = ["#3b82f6", "#6366f1", "#8b5cf6", "#a855f7",
              "#ec4899", "#f43f5e", "#f97316", "#22d3ee"]
    fig = go.Figure(data=go.Barpolar(
        r=[aspect_counts.get(d, 0) for d in dirs], theta=dirs,
        marker_color=colors, marker_line_color="#1a1a2e",
        marker_line_width=1, opacity=0.85,
        hovertemplate="Direction: %{theta}<br>Count: %{r}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Aspect Compass Rose", font=dict(size=15, color=_CLR["text"])),
        template="plotly_dark", paper_bgcolor=_CLR["bg"],
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   angularaxis=dict(direction="clockwise", rotation=90,
                                    gridcolor="rgba(255,255,255,0.12)"),
                   radialaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                                   showticklabels=True)),
        height=400, margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def _contour_map(elev_grid: List[List[Optional[float]]],
                 lat_ticks: List[float], lon_ticks: List[float]) -> go.Figure:
    """Contour plot for elevation data."""
    z = [[c if c is not None else 0.0 for c in row] for row in elev_grid]
    fig = go.Figure(data=go.Contour(
        z=z, x=[round(lo, 4) for lo in lon_ticks],
        y=[round(la, 4) for la in lat_ticks], colorscale="Earth",
        contours=dict(showlabels=True, labelfont=dict(size=10, color="white")),
        colorbar=dict(title="Elevation (m)"),
        hovertemplate="Lat: %{y:.4f}<br>Lon: %{x:.4f}<br>Elev: %{z:.1f} m<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Elevation Contour Map", font=dict(size=15, color=_CLR["text"])),
        xaxis_title="Longitude", yaxis_title="Latitude",
        template="plotly_dark", paper_bgcolor=_CLR["bg"],
        plot_bgcolor="rgba(0,0,0,0)", height=420,
        margin=dict(l=60, r=30, t=50, b=50),
    )
    return fig


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _badge(label: str, color: str) -> str:
    return (f'<span style="background:{color};color:#fff;padding:4px 12px;'
            f'border-radius:12px;font-size:0.85rem;font-weight:600;">{label}</span>')


def _card(title: str, value: str, sub: str = "") -> str:
    s = f'<div style="font-size:0.75rem;color:{_CLR["muted"]};">{sub}</div>' if sub else ""
    return (f'<div style="background:{_CLR["card"]};border:1px solid {_CLR["border"]};'
            f'border-radius:10px;padding:14px 18px;text-align:center;">'
            f'<div style="font-size:0.8rem;color:{_CLR["muted"]};">{title}</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:{_CLR["text"]};">'
            f'{value}</div>{s}</div>')


def _header(num: str, title: str) -> None:
    st.markdown(
        f'<div style="margin:24px 0 10px;padding:8px 14px;'
        f'background:linear-gradient(90deg,{_CLR["card"]},{_CLR["bg"]});'
        f'border-left:4px solid {_CLR["accent"]};border-radius:6px;">'
        f'<span style="font-size:1.1rem;font-weight:600;color:{_CLR["text"]};">'
        f'{num}. {title}</span></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_elevation_profiler_tab():
    """Render the Advanced Elevation Profiler tab."""

    st.markdown("## Advanced Elevation Profiler")
    st.caption("Terrain profiles, slope analysis, aspect mapping & drainage patterns")

    # -- Coordinate inputs -------------------------------------------------
    col_a, col_b = st.columns(2)
    lat = col_a.number_input("Latitude", value=41.9028, format="%.4f",
                             key="elevp_lat", min_value=-90.0, max_value=90.0)
    lon = col_b.number_input("Longitude", value=12.4964, format="%.4f",
                             key="elevp_lon", min_value=-180.0, max_value=180.0)

    radius_km = st.slider("Analysis radius (km)", 1, 20, 5, key="elevp_radius",
                           help="Spatial extent of profile transects and grid analysis.")
    radius_deg = round(radius_km * _deg_per_km_lat(), 4)

    grid_size = st.select_slider("Grid resolution", options=[6, 8, 10], value=10,
                                  key="elevp_grid_res",
                                  help="Grid dimension for slope/aspect (10x10 = 100 pts).")

    if not st.button("Profile Elevation", key="elevp_btn"):
        st.info("Configure coordinates and radius, then press **Profile Elevation**.")
        return

    prog = st.progress(0, text="Starting elevation analysis...")

    # ====================================================================
    # 1 - Centre Point Elevation
    # ====================================================================
    prog.progress(5, text="Fetching centre elevation...")
    _header("1", "Centre Point Elevation")

    centre_elev = _fetch_single_elevation(lat, lon)
    if centre_elev is not None:
        cls_label, cls_color = _classify_elevation(centre_elev)
        c1, c2, c3 = st.columns(3)
        c1.markdown(_card("Elevation", f"{centre_elev:.1f} m"), unsafe_allow_html=True)
        c2.markdown(_card("Classification", cls_label), unsafe_allow_html=True)
        c3.markdown(_card("Coordinates", f"{lat:.4f}, {lon:.4f}"), unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;Zone: {_badge(cls_label, cls_color)}",
                    unsafe_allow_html=True)
    else:
        st.warning("Could not retrieve elevation for the centre point.")

    # ====================================================================
    # 2 - North-South Profile
    # ====================================================================
    prog.progress(20, text="Building North-South profile...")
    _header("2", "North-South Elevation Profile")

    ns_pts = _linspace_points(lat - radius_deg, lon, lat + radius_deg, lon, 20)
    ns_elevs = _fetch_points(ns_pts)
    ns_dists = [_haversine_km(ns_pts[0][0], ns_pts[0][1], p[0], p[1]) for p in ns_pts]

    ns_valid = [(d, e) for d, e in zip(ns_dists, ns_elevs) if e is not None]
    if ns_valid:
        ns_d, ns_e = [v[0] for v in ns_valid], [v[1] for v in ns_valid]
        st.plotly_chart(_profile_chart(ns_d, ns_e,
                        f"N-S Profile ({radius_km * 2} km transect)", "#3b82f6"),
                        use_container_width=True, key="elepro_pchart1")
        m1, m2, m3 = st.columns(3)
        m1.metric("Min Elevation", f"{min(ns_e):.1f} m")
        m2.metric("Max Elevation", f"{max(ns_e):.1f} m")
        m3.metric("Relief", f"{max(ns_e) - min(ns_e):.1f} m")
    else:
        st.warning("Insufficient data for North-South profile.")

    # ====================================================================
    # 3 - East-West Profile
    # ====================================================================
    prog.progress(40, text="Building East-West profile...")
    _header("3", "East-West Elevation Profile")

    lon_r = round(radius_km * _deg_per_km_lon(lat), 4)
    ew_pts = _linspace_points(lat, lon - lon_r, lat, lon + lon_r, 20)
    ew_elevs = _fetch_points(ew_pts)
    ew_dists = [_haversine_km(ew_pts[0][0], ew_pts[0][1], p[0], p[1]) for p in ew_pts]

    ew_valid = [(d, e) for d, e in zip(ew_dists, ew_elevs) if e is not None]
    if ew_valid:
        ew_d, ew_e = [v[0] for v in ew_valid], [v[1] for v in ew_valid]
        st.plotly_chart(_profile_chart(ew_d, ew_e,
                        f"E-W Profile ({radius_km * 2} km transect)", "#f59e0b"),
                        use_container_width=True, key="elepro_pchart2")
        e1, e2, e3 = st.columns(3)
        e1.metric("Min Elevation", f"{min(ew_e):.1f} m")
        e2.metric("Max Elevation", f"{max(ew_e):.1f} m")
        e3.metric("Relief", f"{max(ew_e) - min(ew_e):.1f} m")
    else:
        st.warning("Insufficient data for East-West profile.")

    # ====================================================================
    # Shared: fetch elevation grid for sections 4-6
    # ====================================================================
    prog.progress(55, text="Fetching elevation grid...")

    g_coords, lat_ticks, lon_ticks = _grid_points(lat, lon, radius_deg, grid_size)
    grid_elevs = _fetch_points(g_coords)

    # Reshape to 2-D
    elev_grid: List[List[Optional[float]]] = []
    for r in range(grid_size):
        row = []
        for c in range(grid_size):
            idx = r * grid_size + c
            row.append(grid_elevs[idx] if idx < len(grid_elevs) else None)
        elev_grid.append(row)

    all_valid = [e for e in grid_elevs if e is not None]
    g_mean = sum(all_valid) / len(all_valid) if all_valid else 0.0
    filled = [[c if c is not None else g_mean for c in row] for row in elev_grid]
    has_grid = len(all_valid) >= 9

    # ====================================================================
    # 4 - Slope Analysis
    # ====================================================================
    prog.progress(70, text="Computing slope analysis...")
    _header("4", "Slope Analysis")

    avg_slope = 0.0
    if has_grid:
        slope_grid, aspect_grid = _compute_slope_aspect(filled, lat_ticks, lon_ticks)
        st.plotly_chart(_slope_heatmap(slope_grid, lat_ticks, lon_ticks),
                        use_container_width=True, key="elepro_pchart3")

        slope_flat = [slope_grid[r][c] for r in range(grid_size) for c in range(grid_size)]
        slope_cc: Dict[str, int] = {}
        for s in slope_flat:
            lbl, _ = _classify_slope(s)
            slope_cc[lbl] = slope_cc.get(lbl, 0) + 1

        # Slope distribution bar chart
        s_labels = [sc[0] for sc in _SLOPE_CLASSES]
        s_vals = [slope_cc.get(l, 0) for l in s_labels]
        s_colors = [sc[3] for sc in _SLOPE_CLASSES]
        dist_fig = go.Figure(data=go.Bar(
            y=s_labels, x=s_vals, orientation="h", marker_color=s_colors,
            hovertemplate="%{y}: %{x} cells<extra></extra>"))
        dist_fig.update_layout(
            title=dict(text="Slope Class Distribution",
                       font=dict(size=14, color=_CLR["text"])),
            xaxis_title="Cells", template="plotly_dark",
            paper_bgcolor=_CLR["bg"], plot_bgcolor="rgba(0,0,0,0)",
            height=260, margin=dict(l=90, r=20, t=40, b=40))
        st.plotly_chart(dist_fig, use_container_width=True, key="elevp_slope_dist")

        avg_slope = sum(slope_flat) / len(slope_flat) if slope_flat else 0.0
        max_slope = max(slope_flat) if slope_flat else 0.0
        dom_cls, _ = _classify_slope(avg_slope)
        s1, s2, s3 = st.columns(3)
        s1.metric("Average Slope", f"{avg_slope:.1f}\u00b0")
        s2.metric("Maximum Slope", f"{max_slope:.1f}\u00b0")
        s3.metric("Dominant Class", dom_cls)
    else:
        st.warning("Insufficient grid data for slope analysis.")

    # ====================================================================
    # 5 - Aspect Analysis
    # ====================================================================
    prog.progress(85, text="Computing aspect analysis...")
    _header("5", "Aspect Analysis")

    if has_grid:
        aspect_flat = [aspect_grid[r][c] for r in range(grid_size) for c in range(grid_size)]
        a_counts: Dict[str, int] = {d: 0 for d in
                                     ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]}
        for a in aspect_flat:
            lbl = _aspect_label(a)
            if lbl in a_counts:
                a_counts[lbl] += 1

        st.plotly_chart(_aspect_rose(a_counts), use_container_width=True,
                        key="elepro_pchart4")

        dom_asp = max(a_counts, key=lambda k: a_counts[k])
        total = sum(a_counts.values())
        dom_pct = (a_counts[dom_asp] / total * 100) if total else 0
        a1, a2 = st.columns(2)
        a1.metric("Dominant Aspect", dom_asp)
        a2.metric("Dominance", f"{dom_pct:.0f}%")

        with st.expander("Aspect Distribution Table", expanded=False):
            rows_data = []
            for d in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
                cnt = a_counts.get(d, 0)
                pct = (cnt / total * 100) if total else 0
                rows_data.append({"Direction": d, "Cells": cnt,
                                  "Percentage": f"{pct:.1f}%"})
            st.table(rows_data)
    else:
        st.warning("Insufficient grid data for aspect analysis.")

    # ====================================================================
    # 6 - Terrain Statistics & Contour Map
    # ====================================================================
    prog.progress(93, text="Compiling terrain statistics...")
    _header("6", "Terrain Statistics & Contour Map")

    stats = _terrain_statistics(grid_elevs)
    if stats:
        t1, t2, t3, t4 = st.columns(4)
        t1.markdown(_card("Minimum", f"{stats['min']} m"), unsafe_allow_html=True)
        t2.markdown(_card("Maximum", f"{stats['max']} m"), unsafe_allow_html=True)
        t3.markdown(_card("Mean", f"{stats['mean']} m"), unsafe_allow_html=True)
        t4.markdown(_card("Std Dev", f"{stats['std_dev']} m"), unsafe_allow_html=True)

        t5, t6, t7 = st.columns(3)
        t5.markdown(_card("Total Relief", f"{stats['relief']} m",
                          "Max - Min elevation"), unsafe_allow_html=True)
        t6.markdown(_card("Roughness Index", f"{stats['roughness_index']}",
                          "Std deviation of elevation"), unsafe_allow_html=True)
        t7.markdown(_card("Sample Points", str(stats["count"]),
                          f"{grid_size} x {grid_size} grid"), unsafe_allow_html=True)

        # Elevation zone pie chart
        ez_counts: Dict[str, int] = {}
        for e in grid_elevs:
            if e is not None:
                lbl, _ = _classify_elevation(e)
                ez_counts[lbl] = ez_counts.get(lbl, 0) + 1
        if ez_counts:
            ez_labels = list(ez_counts.keys())
            ez_vals = list(ez_counts.values())
            ez_colors = [next((ec[3] for ec in _ELEV_CLASSES if ec[0] == l),
                              "#6b7280") for l in ez_labels]
            pie = go.Figure(data=go.Pie(
                labels=ez_labels, values=ez_vals,
                marker=dict(colors=ez_colors,
                            line=dict(color="#1a1a2e", width=2)),
                hole=0.4, textinfo="label+percent",
                hovertemplate="%{label}: %{value} cells (%{percent})<extra></extra>"))
            pie.update_layout(
                title=dict(text="Elevation Zone Distribution",
                           font=dict(size=14, color=_CLR["text"])),
                template="plotly_dark", paper_bgcolor=_CLR["bg"],
                height=340, margin=dict(l=20, r=20, t=50, b=20),
                showlegend=True, legend=dict(font=dict(color=_CLR["text"])))
            st.plotly_chart(pie, use_container_width=True, key="elevp_elev_pie")

        # Contour map
        if has_grid:
            st.plotly_chart(_contour_map(elev_grid, lat_ticks, lon_ticks),
                            use_container_width=True, key="elepro_pchart5")
    else:
        st.warning("No terrain statistics available.")

    # -- Drainage Pattern Estimation ---------------------------------------
    if has_grid and stats and stats.get("relief", 0) > 0:
        with st.expander("Drainage Pattern Estimation", expanded=False):
            st.markdown(f"**Estimated drainage characteristics** based on "
                        f"{grid_size}x{grid_size} elevation grid analysis.")
            relief = stats["relief"]
            if avg_slope < 2 and relief < 20:
                pattern, desc = "Distributary / Braided", (
                    "Very flat terrain with minimal relief suggests broad, slow-moving "
                    "drainage with possible braided or distributary channels.")
            elif avg_slope < 5 and relief < 100:
                pattern, desc = "Dendritic", (
                    "Gentle, uniform slopes favour a tree-like dendritic drainage "
                    "pattern typical of homogeneous substrates.")
            elif avg_slope < 10 and relief < 300:
                pattern, desc = "Sub-dendritic / Parallel", (
                    "Moderate slopes may produce semi-parallel streams that "
                    "converge into a dendritic trunk.")
            elif avg_slope < 20:
                pattern, desc = "Parallel / Trellis", (
                    "Steeper terrain suggests parallel channels flowing down-slope, "
                    "possibly controlled by structural geology.")
            else:
                pattern, desc = "Radial / Steep Gorge", (
                    "Very steep slopes indicate rapid runoff in narrow gorges; "
                    "radial patterns may form around peaks.")

            d1, d2 = st.columns(2)
            d1.markdown(_card("Pattern", pattern), unsafe_allow_html=True)
            d2.markdown(_card("Relief Driver", f"{relief:.0f} m"),
                        unsafe_allow_html=True)
            st.markdown(f"> {desc}")

            # Flow convergence proxy
            cr, cc = grid_size // 2, grid_size // 2
            c_elev = filled[cr][cc]
            higher = sum(1 for r in range(grid_size)
                         for c in range(grid_size) if filled[r][c] > c_elev)
            total_cells = grid_size * grid_size
            label = "significant" if higher > total_cells * 0.6 else "moderate"
            st.markdown(
                f"**Flow convergence indicator:** {higher} of {total_cells} grid "
                f"cells are higher than the centre point, suggesting {label} "
                f"potential for water accumulation at the analysis centre.")

    # -- Done --------------------------------------------------------------
    prog.progress(100, text="Elevation profiling complete.")
    st.success(f"Analysis complete for ({lat:.4f}, {lon:.4f}) with "
               f"{radius_km} km radius ({grid_size}x{grid_size} grid).")
