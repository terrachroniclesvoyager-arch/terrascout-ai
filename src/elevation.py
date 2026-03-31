"""
Elevation tab module for Pocket GIS AI.
Uses Open Topo Data API for elevation queries and profile generation.
"""

import math
import logging
import requests
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# ─── CONSTANTS ───
DATASETS = {
    "SRTM 30m": "srtm30m",
    "ASTER 30m": "aster30m",
    "ETOPO1": "etopo1",
}

API_BASE = "https://api.opentopodata.org/v1"


# ─── CORE FUNCTIONS ───

@st.cache_data(ttl=600)
def get_elevation(lat: float, lng: float, dataset: str = "srtm30m") -> float | None:
    """Query elevation for a single point from Open Topo Data API.

    Args:
        lat: Latitude in decimal degrees.
        lng: Longitude in decimal degrees.
        dataset: One of 'srtm30m', 'aster30m', 'etopo1'.

    Returns:
        Elevation in meters, or None on failure.
    """
    try:
        url = f"{API_BASE}/{dataset}"
        params = {"locations": f"{lat},{lng}"}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "OK" and len(data.get("results", [])) > 0:
            elev = data["results"][0].get("elevation")
            if elev is None:
                return None
            try:
                return float(elev)
            except (TypeError, ValueError):
                return None
        return None
    except Exception as e:
        logger.warning(f"Elevation API error for ({lat}, {lng}): {e}")
        return None


def interpolate_points(
    lat1: float, lng1: float, lat2: float, lng2: float, num_points: int = 100
) -> list[tuple[float, float]]:
    """Interpolate points along a great circle between two coordinates.

    Args:
        lat1, lng1: Start coordinate in decimal degrees.
        lat2, lng2: End coordinate in decimal degrees.
        num_points: Number of points to generate (inclusive of endpoints).

    Returns:
        List of (lat, lng) tuples.
    """
    phi1 = math.radians(lat1)
    lam1 = math.radians(lng1)
    phi2 = math.radians(lat2)
    lam2 = math.radians(lng2)

    # Angular distance (central angle) via haversine
    d_phi = phi2 - phi1
    d_lam = lam2 - lam1
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    angular_dist = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Edge case: start and end are the same point
    if angular_dist < 1e-12:
        return [(lat1, lng1)] * num_points

    points = []
    for i in range(num_points):
        f = i / max(num_points - 1, 1)

        # Spherical linear interpolation (slerp)
        A = math.sin((1 - f) * angular_dist) / math.sin(angular_dist)
        B = math.sin(f * angular_dist) / math.sin(angular_dist)

        x = A * math.cos(phi1) * math.cos(lam1) + B * math.cos(phi2) * math.cos(lam2)
        y = A * math.cos(phi1) * math.sin(lam1) + B * math.cos(phi2) * math.sin(lam2)
        z = A * math.sin(phi1) + B * math.sin(phi2)

        lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
        lng = math.degrees(math.atan2(y, x))
        points.append((round(lat, 6), round(lng, 6)))

    return points


@st.cache_data(ttl=600)
def get_elevation_profile(
    points: list[tuple[float, float]], dataset: str = "srtm30m"
) -> list[float | None]:
    """Batch-query elevations for a list of points.

    The API supports up to 100 pipe-separated locations per request.
    If more than 100 points are provided, they are split into chunks.

    Args:
        points: List of (lat, lng) tuples.
        dataset: One of 'srtm30m', 'aster30m', 'etopo1'.

    Returns:
        List of elevation floats (None for failed points).
    """
    elevations = []
    chunk_size = 100

    for start in range(0, len(points), chunk_size):
        chunk = points[start : start + chunk_size]
        locations_str = "|".join(f"{lat},{lng}" for lat, lng in chunk)

        try:
            url = f"{API_BASE}/{dataset}"
            params = {"locations": locations_str}
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == "OK" and data.get("results"):
                for result in data["results"]:
                    elev = result.get("elevation")
                    elevations.append(float(elev) if elev is not None else None)
            else:
                elevations.extend([None] * len(chunk))
        except Exception as e:
            logger.warning(f"Elevation profile API error: {e}")
            elevations.extend([None] * len(chunk))

    return elevations


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute the haversine distance between two points in kilometers.

    Args:
        lat1, lng1: First coordinate in decimal degrees.
        lat2, lng2: Second coordinate in decimal degrees.

    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _cumulative_distances(points: list[tuple[float, float]]) -> list[float]:
    """Compute cumulative distances along a list of (lat, lng) points.

    Returns:
        List of cumulative distances in km, starting at 0.0.
    """
    distances = [0.0]
    for i in range(1, len(points)):
        seg = _haversine_distance(
            points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]
        )
        distances.append(distances[-1] + seg)
    return distances


def render_elevation_chart(
    elevations: list[float], distances: list[float]
) -> plt.Figure:
    """Create a styled matplotlib elevation profile chart.

    Args:
        elevations: Elevation values in meters.
        distances: Corresponding cumulative distances in km.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 4))

    # Dark theme styling
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    # Plot line and fill
    ax.plot(distances, elevations, color="#06b6d4", linewidth=2)
    ax.fill_between(distances, elevations, alpha=0.3, color="#06b6d4")

    # Grid
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    # Labels
    ax.set_xlabel("Distance (km)", color="#e8ecf4", fontsize=11)
    ax.set_ylabel("Elevation (m)", color="#e8ecf4", fontsize=11)
    ax.set_title("Elevation Profile", color="#e8ecf4", fontsize=13, fontweight="bold")

    # Tick colors
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.tick_params(axis="y", colors="#8b97b0", labelsize=9)

    # Spine colors
    for spine in ax.spines.values():
        spine.set_color("#2a3550")

    fig.tight_layout()
    return fig


# ─── STREAMLIT TAB RENDERER ───

def render_elevation_tab():
    """Main render function for the Elevation tab."""

    st.markdown("""
    <div class="tab-header emerald">
        <h4>Elevation Data</h4>
        <p>Query elevation from global DEMs (SRTM, ASTER, ETOPO1) via Open Topo Data &mdash; free, no API key required.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ──
    col_mode, col_ds = st.columns([1, 1])

    with col_mode:
        mode = st.radio(
            "Mode",
            ["Single Point", "Elevation Profile"],
            key="elev_mode",
            horizontal=True,
        )

    with col_ds:
        dataset_label = st.selectbox(
            "Dataset",
            list(DATASETS.keys()),
            key="elev_dataset",
        )
    dataset = DATASETS[dataset_label]

    st.markdown("---")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SINGLE POINT MODE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if mode == "Single Point":
        col_lat, col_lng = st.columns(2)
        with col_lat:
            sp_lat = st.number_input(
                "Latitude",
                value=41.8902,
                format="%.6f",
                min_value=-90.0,
                max_value=90.0,
                key="elev_sp_lat",
            )
        with col_lng:
            sp_lng = st.number_input(
                "Longitude",
                value=12.4922,
                format="%.6f",
                min_value=-180.0,
                max_value=180.0,
                key="elev_sp_lng",
            )

        if st.button("Get Elevation", key="elev_sp_btn", width="stretch"):
            with st.spinner("Querying elevation..."):
                elev = get_elevation(sp_lat, sp_lng, dataset)

            if elev is not None:
                st.markdown(
                    f"""
                    <div class="stat-card" style="margin-top:1rem; padding:2rem;">
                        <div class="stat-value" style="font-size:2.5rem;">{elev:.1f} m</div>
                        <div class="stat-label">Elevation ({dataset_label})</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.error(
                    "Could not retrieve elevation for this location. "
                    "The point may be outside the dataset coverage or the API may be rate-limited."
                )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ELEVATION PROFILE MODE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        st.markdown(
            '<p style="color:#8b97b0; font-size:0.9rem;">Define start and end coordinates for the elevation transect.</p>',
            unsafe_allow_html=True,
        )

        col_s1, col_s2, col_e1, col_e2 = st.columns(4)
        with col_s1:
            start_lat = st.number_input(
                "Start Lat",
                value=45.8326,
                format="%.6f",
                min_value=-90.0,
                max_value=90.0,
                key="elev_start_lat",
            )
        with col_s2:
            start_lng = st.number_input(
                "Start Lng",
                value=6.8652,
                format="%.6f",
                min_value=-180.0,
                max_value=180.0,
                key="elev_start_lng",
            )
        with col_e1:
            end_lat = st.number_input(
                "End Lat",
                value=45.9237,
                format="%.6f",
                min_value=-90.0,
                max_value=90.0,
                key="elev_end_lat",
            )
        with col_e2:
            end_lng = st.number_input(
                "End Lng",
                value=6.8694,
                format="%.6f",
                min_value=-180.0,
                max_value=180.0,
                key="elev_end_lng",
            )

        if st.button("Generate Profile", key="elev_prof_btn", width="stretch"):
            with st.spinner("Interpolating points and querying elevations..."):
                # Interpolate along the great circle
                points = interpolate_points(start_lat, start_lng, end_lat, end_lng, 100)

                # Batch query elevations
                elevations_raw = get_elevation_profile(tuple(points), dataset)

                # Compute distances
                distances = _cumulative_distances(points)

            # Filter out None values for display (replace with neighbours or 0)
            elevations_clean = []
            for e in elevations_raw:
                if e is not None:
                    elevations_clean.append(e)
                else:
                    # Use last known value or 0
                    elevations_clean.append(elevations_clean[-1] if elevations_clean else 0.0)

            valid_elevations = [e for e in elevations_raw if e is not None]

            if not valid_elevations:
                st.error(
                    "Could not retrieve any elevation data for this transect. "
                    "Try a different dataset or check that coordinates are valid."
                )
                return

            # ── Chart ──
            fig = render_elevation_chart(elevations_clean, distances)
            st.pyplot(fig)
            plt.close(fig)

            # ── Stats ──
            elev_min = min(valid_elevations)
            elev_max = max(valid_elevations)
            total_dist = distances[-1] if distances else 0.0

            # Elevation gain: sum of positive deltas
            elev_gain = 0.0
            for i in range(1, len(elevations_clean)):
                delta = elevations_clean[i] - elevations_clean[i - 1]
                if delta > 0:
                    elev_gain += delta

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Min Elevation", f"{elev_min:.1f} m")
            c2.metric("Max Elevation", f"{elev_max:.1f} m")
            c3.metric("Elevation Gain", f"{elev_gain:.1f} m")
            c4.metric("Total Distance", f"{total_dist:.2f} km")

            # ── Export elevation profile data ──
            try:
                import pandas as pd
                export_data = []
                for i, (point, elev, dist) in enumerate(zip(points, elevations_clean, distances)):
                    export_data.append({
                        "Point": i + 1,
                        "Latitude": point[0],
                        "Longitude": point[1],
                        "Elevation_m": elev,
                        "Distance_km": dist
                    })

                df_profile = pd.DataFrame(export_data)
                csv_profile = df_profile.to_csv(index=False)

                st.download_button(
                    "📥 Download Elevation Profile (CSV)",
                    csv_profile,
                    "elevation_profile.csv",
                    "text/csv",
                    use_container_width=True
                )
            except Exception as e:
                logger.warning(f"Export failed: {e}")

            # ── Folium map with profile line ──
            try:
                import folium
                from streamlit_folium import st_folium

                mid_lat = (start_lat + end_lat) / 2
                mid_lng = (start_lng + end_lng) / 2

                m = folium.Map(
                    location=[mid_lat, mid_lng],
                    zoom_start=11,
                    tiles="CartoDB dark_matter",
                )

                # Profile line
                line_coords = [(lat, lng) for lat, lng in points]
                folium.PolyLine(
                    locations=line_coords,
                    color="#06b6d4",
                    weight=3,
                    opacity=0.9,
                ).add_to(m)

                # Start / end markers
                folium.CircleMarker(
                    location=[start_lat, start_lng],
                    radius=6,
                    color="#06b6d4",
                    fill=True,
                    fill_color="#06b6d4",
                    fill_opacity=0.9,
                    popup="Start",
                ).add_to(m)

                folium.CircleMarker(
                    location=[end_lat, end_lng],
                    radius=6,
                    color="#38bdf8",
                    fill=True,
                    fill_color="#38bdf8",
                    fill_opacity=0.9,
                    popup="End",
                ).add_to(m)

                st.markdown(
                    '<p style="color:#8b97b0; font-size:0.85rem; margin-top:1rem;">Profile transect on map:</p>',
                    unsafe_allow_html=True,
                )
                st_folium(m, height=400, width=None, returned_objects=[], key="elev_folium_map")

            except ImportError:
                st.info("Install `folium` and `streamlit-folium` to display the profile map.")
            except Exception as e:
                logger.warning(f"Could not render folium map: {e}")
                st.warning(f"Map rendering failed: {e}")
