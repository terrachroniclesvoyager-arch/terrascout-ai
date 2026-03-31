"""
Terrain Classifier AI — Advanced landform classification using elevation grid
analysis, slope computation, roughness index, and geomorphological categorization.
Generates terrain intelligence reports with 3D-style visualizations.
Uses: Open Topo Data, Open-Meteo, ISRIC SoilGrids.
"""

import math
import logging

import numpy as np
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
)

logger = logging.getLogger(__name__)

# ── Landform classifications ────────────────────────────────────────────────

LANDFORMS = {
    "flat_plain": {"name": "Flat Plain", "color": "#10b981", "min_slope": 0, "max_slope": 2},
    "gentle_slope": {"name": "Gentle Slope", "color": "#22c55e", "min_slope": 2, "max_slope": 5},
    "moderate_slope": {"name": "Moderate Slope", "color": "#f59e0b", "min_slope": 5, "max_slope": 15},
    "steep_slope": {"name": "Steep Slope", "color": "#f97316", "min_slope": 15, "max_slope": 30},
    "very_steep": {"name": "Very Steep", "color": "#ef4444", "min_slope": 30, "max_slope": 45},
    "cliff": {"name": "Cliff / Escarpment", "color": "#dc2626", "min_slope": 45, "max_slope": 90},
}


@st.cache_data(ttl=1800)
def classify_terrain(lat: float, lon: float) -> dict:
    """Perform advanced terrain classification using dense elevation grid."""
    # Fetch dense elevation grid
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=0.06, grid_size=10) or {}
    elevations = elev_data.get("grid_elevations", [])
    lats = elev_data.get("lats", [])
    lons = elev_data.get("lons", [])

    valid_elevs = [e for e in elevations if e is not None]
    if len(valid_elevs) < 9:
        return {"error": "Insufficient elevation data"}

    # Fill None values with mean
    mean_elev = sum(valid_elevs) / len(valid_elevs)
    filled = [e if e is not None else mean_elev for e in elevations]

    grid_size = int(math.sqrt(len(filled)))
    if grid_size < 3:
        return {"error": "Grid too small"}

    grid = np.array(filled[:grid_size * grid_size]).reshape(grid_size, grid_size)

    # ── Compute slope (degrees) ──
    # Approximate cell size in meters
    cell_size_lat = 111000 * (0.12 / max(grid_size - 1, 1))
    cell_size_lon = 111000 * math.cos(math.radians(lat)) * (0.12 / max(grid_size - 1, 1))
    cell_size = (cell_size_lat + cell_size_lon) / 2

    slopes = np.zeros_like(grid)
    for i in range(1, grid_size - 1):
        for j in range(1, grid_size - 1):
            dz_dx = (grid[i, j + 1] - grid[i, j - 1]) / (2 * cell_size)
            dz_dy = (grid[i + 1, j] - grid[i - 1, j]) / (2 * cell_size)
            slopes[i, j] = math.degrees(math.atan(math.sqrt(dz_dx ** 2 + dz_dy ** 2)))

    # ── Compute aspect (degrees from north) ──
    aspects = np.zeros_like(grid)
    for i in range(1, grid_size - 1):
        for j in range(1, grid_size - 1):
            dz_dx = (grid[i, j + 1] - grid[i, j - 1]) / (2 * cell_size)
            dz_dy = (grid[i + 1, j] - grid[i - 1, j]) / (2 * cell_size)
            aspect = math.degrees(math.atan2(-dz_dy, dz_dx))
            aspects[i, j] = (90 - aspect) % 360

    # ── Terrain Roughness Index (TRI) ──
    tri = np.zeros_like(grid)
    for i in range(1, grid_size - 1):
        for j in range(1, grid_size - 1):
            neighbors = [
                grid[i - 1, j - 1], grid[i - 1, j], grid[i - 1, j + 1],
                grid[i, j - 1], grid[i, j + 1],
                grid[i + 1, j - 1], grid[i + 1, j], grid[i + 1, j + 1],
            ]
            tri[i, j] = sum(abs(n - grid[i, j]) for n in neighbors) / 8

    # ── Landform classification ──
    inner_slopes = slopes[1:-1, 1:-1].flatten()
    landform_counts = {}
    for s in inner_slopes:
        for lf_id, lf in LANDFORMS.items():
            if lf["min_slope"] <= s < lf["max_slope"]:
                landform_counts[lf_id] = landform_counts.get(lf_id, 0) + 1
                break

    total_cells = len(inner_slopes)
    dominant = max(landform_counts, key=landform_counts.get) if landform_counts else "flat_plain"

    # ── Aspect distribution ──
    inner_aspects = aspects[1:-1, 1:-1].flatten()
    aspect_names = {
        "N": (337.5, 22.5), "NE": (22.5, 67.5), "E": (67.5, 112.5),
        "SE": (112.5, 157.5), "S": (157.5, 202.5), "SW": (202.5, 247.5),
        "W": (247.5, 292.5), "NW": (292.5, 337.5),
    }
    aspect_dist = {k: 0 for k in aspect_names}
    for a in inner_aspects:
        for name, (low, high) in aspect_names.items():
            if name == "N":
                if a >= 337.5 or a < 22.5:
                    aspect_dist[name] += 1
                    break
            elif low <= a < high:
                aspect_dist[name] += 1
                break

    # ── Statistics ──
    inner_tri = tri[1:-1, 1:-1].flatten()

    # Classification result
    elev_min = float(np.min(grid))
    elev_max = float(np.max(grid))
    elev_range = elev_max - elev_min

    # Geomorphological type
    avg_slope = float(np.mean(inner_slopes))
    avg_tri = float(np.mean(inner_tri))

    if avg_slope < 2 and elev_range < 20:
        geomorph = "Flat Terrain (Plain/Plateau)"
    elif avg_slope < 5 and elev_range < 100:
        geomorph = "Gently Undulating Terrain"
    elif avg_slope < 15 and elev_range < 300:
        geomorph = "Hilly Terrain"
    elif avg_slope < 25:
        geomorph = "Mountainous Terrain"
    else:
        geomorph = "Alpine / Rugged Terrain"

    if elev_min < 5:
        geomorph += " (Coastal)"
    elif mean_elev > 2000:
        geomorph += " (High Altitude)"

    # Traversability score (0-10, higher = easier to traverse)
    traversability = max(0, min(10, 10 - avg_slope / 4 - avg_tri / 10))

    return {
        "grid": grid.tolist(),
        "slopes": slopes.tolist(),
        "aspects": aspects.tolist(),
        "tri": tri.tolist(),
        "lats": lats,
        "lons": lons,
        "grid_size": grid_size,
        "stats": {
            "elev_min": round(elev_min, 1),
            "elev_max": round(elev_max, 1),
            "elev_mean": round(float(np.mean(grid)), 1),
            "elev_std": round(float(np.std(grid)), 1),
            "elev_range": round(elev_range, 1),
            "slope_min": round(float(np.min(inner_slopes)), 1),
            "slope_max": round(float(np.max(inner_slopes)), 1),
            "slope_mean": round(avg_slope, 1),
            "tri_mean": round(avg_tri, 1),
            "tri_max": round(float(np.max(inner_tri)), 1),
        },
        "dominant_landform": dominant,
        "landform_distribution": {
            LANDFORMS[k]["name"]: round(v / max(total_cells, 1) * 100, 1)
            for k, v in landform_counts.items()
        },
        "aspect_distribution": aspect_dist,
        "geomorphology": geomorph,
        "traversability": round(traversability, 1),
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_terrain_classifier_tab():
    """Render the Terrain Classifier AI tab."""
    st.markdown("## Terrain Classifier AI")
    st.caption("Advanced landform classification with slope, aspect & roughness analysis")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="tc_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="tc_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="tc_lon", format="%.4f")

    if st.button("Classify Terrain", type="primary", use_container_width=True):
        with st.spinner("Analyzing terrain morphology..."):
            result = classify_terrain(lat, lon)

        if "error" in result:
            st.error(result["error"])
            return

        stats = result["stats"]
        geomorph = result["geomorphology"]
        trav = result["traversability"]

        # ── Header ──
        trav_color = "#10b981" if trav >= 7 else "#f59e0b" if trav >= 4 else "#ef4444"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #1a1a2e, #16213e);
                    border:1px solid #333; border-radius:12px; padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">GEOMORPHOLOGY</div>
                    <div style="color:#eee; font-size:22px; font-weight:bold;">{geomorph}</div>
                    <div style="color:#888; font-size:13px;">
                        Dominant: {LANDFORMS[result['dominant_landform']]['name']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:12px;">TRAVERSABILITY</div>
                    <div style="color:{trav_color}; font-size:36px; font-weight:bold;">
                        {trav}<span style="font-size:14px; color:#888;">/10</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Statistics ──
        mc = st.columns(5)
        mc[0].metric("Elevation Range", f"{stats['elev_range']:.0f}m")
        mc[1].metric("Min / Max", f"{stats['elev_min']:.0f} / {stats['elev_max']:.0f}m")
        mc[2].metric("Avg Slope", f"{stats['slope_mean']:.1f}deg")
        mc[3].metric("Max Slope", f"{stats['slope_max']:.1f}deg")
        mc[4].metric("Roughness (TRI)", f"{stats['tri_mean']:.1f}")

        # ── 3D Surface ──
        st.markdown("### Elevation Surface")
        grid = np.array(result["grid"])
        fig = go.Figure(data=[go.Surface(
            z=grid,
            colorscale="earth",
            showscale=True,
            colorbar=dict(title="Elev (m)"),
        )])
        fig.update_layout(
            height=450,
            margin=dict(t=20, b=20, l=20, r=20),
            scene=dict(
                xaxis_title="",
                yaxis_title="",
                zaxis_title="Elevation (m)",
                aspectratio=dict(x=1, y=1, z=0.5),
            ),
        )
        st.plotly_chart(fig, use_container_width=True, key="tercla_pchart1")

        # ── Slope heatmap ──
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("### Slope Map")
            slopes = np.array(result["slopes"])
            fig2 = go.Figure(data=go.Heatmap(
                z=slopes,
                colorscale=[
                    [0, "#10b981"],
                    [0.1, "#22c55e"],
                    [0.3, "#f59e0b"],
                    [0.6, "#f97316"],
                    [1, "#ef4444"],
                ],
                colorbar=dict(title="Slope (deg)"),
            ))
            fig2.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig2, use_container_width=True, key="tercla_pchart2")

        with col_b:
            st.markdown("### Roughness Map")
            tri_arr = np.array(result["tri"])
            fig3 = go.Figure(data=go.Heatmap(
                z=tri_arr,
                colorscale="YlOrRd",
                colorbar=dict(title="TRI"),
            ))
            fig3.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig3, use_container_width=True, key="tercla_pchart3")

        # ── Landform distribution ──
        st.markdown("### Landform Distribution")
        lf_dist = result["landform_distribution"]
        if lf_dist:
            lf_names = list(lf_dist.keys())
            lf_pcts = list(lf_dist.values())
            lf_colors = [LANDFORMS[k]["color"] for k in result["landform_distribution"]
                         if k in LANDFORMS] or ["#888"] * len(lf_names)

            # Fix color lookup
            color_map = {v["name"]: v["color"] for v in LANDFORMS.values()}
            lf_colors = [color_map.get(n, "#888") for n in lf_names]

            fig4 = go.Figure(data=[go.Pie(
                labels=lf_names,
                values=lf_pcts,
                marker=dict(colors=lf_colors),
                hole=0.4,
                textinfo="label+percent",
            )])
            fig4.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig4, use_container_width=True, key="tercla_pchart4")

        # ── Aspect rose ──
        st.markdown("### Aspect Distribution (Compass)")
        aspect_dist = result["aspect_distribution"]
        directions = list(aspect_dist.keys())
        counts = list(aspect_dist.values())

        fig5 = go.Figure()
        fig5.add_trace(go.Barpolar(
            r=counts + [counts[0]],
            theta=directions + [directions[0]],
            marker_color="#8b5cf6",
            marker_line_color="#6d28d9",
            marker_line_width=1,
            opacity=0.8,
        ))
        fig5.update_layout(
            polar=dict(
                radialaxis=dict(visible=True),
                angularaxis=dict(direction="clockwise"),
            ),
            height=380,
            margin=dict(t=30, b=30),
        )
        st.plotly_chart(fig5, use_container_width=True, key="tercla_pchart5")
