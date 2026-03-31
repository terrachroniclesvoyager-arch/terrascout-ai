"""
Route Analysis module for TerraScout AI.
Analyze elevation profile, weather & hazards along any route.
Supports manual waypoint entry and preset routes.
"""

import logging
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

from src.map_factory import MapFactory
from src.deep_zone_analysis import (
    haversine_distance,
    fetch_weather_data,
    fetch_earthquakes,
    ANALYSIS_PRESETS,
)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False


PRESET_ROUTES = {
    "Custom": [],
    "Rome to Naples": [
        {"lat": 41.90, "lon": 12.50},
        {"lat": 41.46, "lon": 13.82},
        {"lat": 40.85, "lon": 14.27},
    ],
    "Grand Canyon Rim to Rim": [
        {"lat": 36.21, "lon": -112.06},
        {"lat": 36.11, "lon": -112.11},
        {"lat": 36.05, "lon": -112.14},
    ],
    "Swiss Alps Traverse": [
        {"lat": 46.56, "lon": 7.97},
        {"lat": 46.53, "lon": 8.04},
        {"lat": 46.48, "lon": 8.12},
        {"lat": 46.44, "lon": 8.18},
    ],
    "Iceland Ring Road Segment": [
        {"lat": 64.13, "lon": -21.90},
        {"lat": 64.26, "lon": -21.13},
        {"lat": 64.33, "lon": -20.29},
        {"lat": 64.25, "lon": -19.50},
    ],
}

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"


@st.cache_data(ttl=3600)
def _fetch_route_elevations(waypoints, num_samples=50):
    """Interpolate waypoints and fetch elevation along the route."""
    if len(waypoints) < 2:
        return []

    # Generate evenly spaced points along the route
    total_dist = 0
    segments = []
    for i in range(len(waypoints) - 1):
        d = haversine_distance(
            waypoints[i]["lat"], waypoints[i]["lon"],
            waypoints[i + 1]["lat"], waypoints[i + 1]["lon"]
        )
        segments.append(d)
        total_dist += d

    if total_dist == 0:
        return []

    # Interpolate points
    points = []
    cum_dist = 0
    for i in range(len(waypoints) - 1):
        seg_len = segments[i]
        n_pts = max(2, int(num_samples * seg_len / total_dist))
        for j in range(n_pts):
            t = j / n_pts
            lat = waypoints[i]["lat"] + t * (waypoints[i + 1]["lat"] - waypoints[i]["lat"])
            lon = waypoints[i]["lon"] + t * (waypoints[i + 1]["lon"] - waypoints[i]["lon"])
            dist_km = cum_dist + t * seg_len
            points.append({"lat": round(lat, 6), "lon": round(lon, 6), "dist_km": round(dist_km, 2)})
        cum_dist += seg_len

    # Add last point
    points.append({
        "lat": waypoints[-1]["lat"],
        "lon": waypoints[-1]["lon"],
        "dist_km": round(total_dist, 2),
    })

    # Fetch elevations in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        locations = "|".join(f"{p['lat']},{p['lon']}" for p in batch)
        try:
            resp = requests.get(OPEN_TOPO_API, params={"locations": locations}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for j, r in enumerate(data.get("results", [])):
                    elev = r.get("elevation")
                    if elev is not None and i + j < len(points):
                        points[i + j]["elevation"] = elev
        except Exception:
            continue

    # Fill missing elevations
    for p in points:
        if "elevation" not in p:
            p["elevation"] = 0

    return points


def _compute_route_stats(points):
    """Compute route statistics from elevation profile."""
    if not points:
        return {}

    elevations = [p["elevation"] for p in points]
    total_dist = points[-1]["dist_km"] if points else 0

    ascent = 0
    descent = 0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            ascent += diff
        else:
            descent += abs(diff)

    return {
        "total_distance_km": round(total_dist, 2),
        "min_elevation": round(min(elevations), 1),
        "max_elevation": round(max(elevations), 1),
        "total_ascent": round(ascent, 1),
        "total_descent": round(descent, 1),
        "elevation_range": round(max(elevations) - min(elevations), 1),
        "avg_elevation": round(sum(elevations) / len(elevations), 1),
        "num_points": len(points),
    }


def render_route_analysis_tab():
    """Main render function for Route Analysis tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>🛤️ Route Analyzer</h4>
        <p>Analyze elevation, weather &amp; hazards along any route with detailed elevation profile</p>
    </div>
    """, unsafe_allow_html=True)

    # Route selection
    col1, col2 = st.columns([1, 2])
    with col1:
        route_preset = st.selectbox("Route Preset", list(PRESET_ROUTES.keys()), key="ra_preset")
        num_waypoints = st.slider("Number of waypoints", 2, 8, 3, key="ra_nwp")
        num_samples = st.slider("Profile resolution", 20, 100, 50, key="ra_samples")

    preset_wps = PRESET_ROUTES.get(route_preset, [])

    with col2:
        st.markdown("**Waypoints**")
        waypoints = []
        wp_cols = st.columns(min(num_waypoints, 4))
        for i in range(num_waypoints):
            col_idx = i % len(wp_cols)
            with wp_cols[col_idx]:
                d_lat = preset_wps[i]["lat"] if i < len(preset_wps) else 41.90 + i * 0.5
                d_lon = preset_wps[i]["lon"] if i < len(preset_wps) else 12.50 + i * 0.5
                la = st.number_input(f"WP{i+1} Lat", -90.0, 90.0, d_lat, step=0.01,
                                     key=f"ra_lat_{i}", format="%.4f")
                lo = st.number_input(f"WP{i+1} Lon", -180.0, 180.0, d_lon, step=0.01,
                                     key=f"ra_lon_{i}", format="%.4f")
                waypoints.append({"lat": la, "lon": lo})

    if st.button("Analyze Route", type="primary", use_container_width=True):
        with st.spinner("Fetching elevation profile..."):
            points = _fetch_route_elevations(waypoints, num_samples=num_samples)

        if not points:
            st.error("Could not fetch route data. Check waypoints.")
            return

        stats = _compute_route_stats(points)
        st.session_state["ra_results"] = {
            "points": points, "stats": stats, "waypoints": waypoints,
        }

    if "ra_results" in st.session_state:
        r = st.session_state["ra_results"]
        points = r["points"]
        stats = r["stats"]
        waypoints = r["waypoints"]

        st.markdown("---")

        # Route metrics
        st.markdown("### Route Summary")
        if not stats:
            st.warning("No route statistics available.")
        else:
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Total Distance", f"{stats.get('total_distance_km', 0)} km")
            with m2:
                st.metric("Total Ascent", f"{stats.get('total_ascent', 0)} m")
            with m3:
                st.metric("Total Descent", f"{stats.get('total_descent', 0)} m")
            with m4:
                st.metric("Min Elevation", f"{stats.get('min_elevation', 0)} m")
            with m5:
                st.metric("Max Elevation", f"{stats.get('max_elevation', 0)} m")

        # Elevation profile chart
        st.markdown("### Elevation Profile")
        df_profile = pd.DataFrame(points)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_profile["dist_km"],
            y=df_profile["elevation"],
            fill="tozeroy",
            line_color="#06b6d4",
            fillcolor="rgba(6, 182, 212, 0.2)",
            name="Elevation",
        ))
        # Mark waypoints
        for i, wp in enumerate(waypoints):
            closest = min(points, key=lambda p: abs(p["lat"] - wp["lat"]) + abs(p["lon"] - wp["lon"]))
            fig.add_trace(go.Scatter(
                x=[closest["dist_km"]],
                y=[closest["elevation"]],
                mode="markers+text",
                marker=dict(size=10, color="#f59e0b"),
                text=[f"WP{i+1}"],
                textposition="top center",
                showlegend=False,
            ))
        fig.update_layout(
            xaxis_title="Distance (km)",
            yaxis_title="Elevation (m)",
            height=400,
            margin=dict(t=30, b=40),
        )
        st.plotly_chart(fig, use_container_width=True, key="rta_elev")

        # Route map
        st.markdown("### Route Map")
        if not points:
            st.warning("No route points to display.")
            return
        center_lat = sum(p["lat"] for p in points) / len(points)
        center_lon = sum(p["lon"] for p in points) / len(points)
        m = MapFactory.create_base_map(center=(center_lat, center_lon), zoom=10)

        # Route polyline
        route_coords = [(p["lat"], p["lon"]) for p in points]
        folium.PolyLine(
            route_coords,
            color="#06b6d4",
            weight=4,
            opacity=0.8,
            tooltip="Route",
        ).add_to(m)

        # Waypoint markers
        for i, wp in enumerate(waypoints):
            MapFactory.add_marker(
                m, (wp["lat"], wp["lon"]),
                popup=f"Waypoint {i+1}<br>({wp['lat']:.4f}, {wp['lon']:.4f})",
                tooltip=f"WP{i+1}",
                icon="flag" if i == 0 else "flag-checkered" if i == len(waypoints) - 1 else "map-pin",
                icon_color="green" if i == 0 else "red" if i == len(waypoints) - 1 else "blue",
            )

        folium.LayerControl().add_to(m)
        st_html(m._repr_html_(), height=450)

        # Weather along route (start, mid, end)
        st.markdown("### Weather Along Route")
        weather_points = [waypoints[0], waypoints[len(waypoints) // 2], waypoints[-1]]
        weather_labels = ["Start", "Midpoint", "End"]
        wx_cols = st.columns(3)
        for i, (wp, label) in enumerate(zip(weather_points, weather_labels)):
            with wx_cols[i]:
                try:
                    wx = fetch_weather_data(wp["lat"], wp["lon"])
                    current = wx.get("current", {})
                    st.markdown(f"**{label}** ({wp['lat']:.2f}, {wp['lon']:.2f})")
                    st.metric("Temp", f"{current.get('temperature_2m', 'N/A')} C")
                    st.metric("Wind", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                    st.metric("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%")
                except Exception:
                    st.warning(f"Weather data unavailable for {label}")

        # Seismic hazards along route
        st.markdown("### Seismic Activity Along Route")
        all_quakes = []
        for wp in waypoints:
            try:
                eq = fetch_earthquakes(wp["lat"], wp["lon"], radius_km=50, days=365)
                for feat in eq.get("features", []):
                    props = feat.get("properties", {})
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        all_quakes.append({
                            "Magnitude": props.get("mag", 0),
                            "Place": props.get("place", "Unknown"),
                            "Lat": coords[1],
                            "Lon": coords[0],
                            "Depth (km)": coords[2] if len(coords) > 2 else 0,
                        })
            except Exception:
                continue

        if all_quakes:
            df_eq = pd.DataFrame(all_quakes).drop_duplicates(subset=["Lat", "Lon"])
            st.dataframe(df_eq.sort_values("Magnitude", ascending=False).head(10),
                         use_container_width=True, hide_index=True)
            st.caption(f"{len(df_eq)} earthquakes within 50km of route (past year)")
        else:
            st.success("No significant seismic activity detected along this route.")

        # Export elevation profile
        st.markdown("---")
        st.markdown("### Export Data")
        df_export = pd.DataFrame(points)
        if HAS_EXPORT:
            render_export_buttons(df_export, prefix="route", lat_col="lat", lon_col="lon")
        else:
            csv = df_export.to_csv(index=False)
            st.download_button("📥 Download Elevation Profile (CSV)", data=csv,
                               file_name="route_elevation_profile.csv", mime="text/csv")
