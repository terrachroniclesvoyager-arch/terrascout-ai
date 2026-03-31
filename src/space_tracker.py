"""
Space & ISS Tracker for TerraScout AI.
Real-time ISS tracking, astronauts in space, near-Earth objects, and NASA APOD.
Uses Open Notify, NASA NEO, NASA APOD, and TLE APIs (all free, no key required
except NASA DEMO_KEY for NEO/APOD which is rate-limited but keyless).
"""

import html as html_module
import io
import math
import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import streamlit.components.v1 as components

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


# ── API Endpoints ──
ISS_POSITION_API = "http://api.open-notify.org/iss-now.json"
ASTROS_API = "http://api.open-notify.org/astros.json"
NASA_NEO_API = "https://api.nasa.gov/neo/rest/v1/feed"
NASA_APOD_API = "https://api.nasa.gov/planetary/apod"
TLE_API = "https://tle.ivanstanojevic.me/api/tle/"

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

# ── ISS constants ──
ISS_ALTITUDE_KM = 408
ISS_VELOCITY_KMH = 27_600
ISS_ORBITAL_PERIOD_MIN = 92.68


# ──────────────────────────────────────────────
# Data Fetchers
# ──────────────────────────────────────────────

@st.cache_data(ttl=15)
def fetch_iss_position() -> dict:
    """Fetch current ISS lat/lon from Open Notify."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("nasa_neo")
    try:
        resp = requests.get(ISS_POSITION_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") == "success":
            pos = data["iss_position"]
            return {
                "latitude": float(pos["latitude"]),
                "longitude": float(pos["longitude"]),
                "timestamp": data.get("timestamp", 0),
            }
        return {"error": "Unexpected response format"}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=120)
def fetch_astronauts() -> dict:
    """Fetch current astronauts in space from Open Notify."""
    try:
        resp = requests.get(ASTROS_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") == "success":
            return {"number": data["number"], "people": data["people"]}
        return {"error": "Unexpected response format", "number": 0, "people": []}
    except Exception as e:
        return {"error": str(e), "number": 0, "people": []}


@st.cache_data(ttl=600)
def fetch_neo_feed(start_date: str, end_date: str) -> dict:
    """Fetch Near-Earth Objects from NASA NEO API."""
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": NASA_API_KEY,
    }
    try:
        resp = requests.get(NASA_NEO_API, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=3600)
def fetch_apod() -> dict:
    """Fetch NASA Astronomy Picture of the Day."""
    params = {"api_key": NASA_API_KEY}
    try:
        resp = requests.get(NASA_APOD_API, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=3600)
def fetch_iss_tle() -> dict:
    """Fetch ISS TLE (Two-Line Element) orbital data."""
    try:
        resp = requests.get(f"{TLE_API}", params={"search": "ISS"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        members = data.get("member", [])
        if members:
            return members[0]
        return {"error": "No TLE data found for ISS"}
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _approximate_ground_track(lat: float, lon: float, points: int = 80) -> list:
    """
    Generate an approximate ISS ground track (sinusoidal projection).
    The ISS orbit is inclined ~51.6 degrees. This produces a rough sine-wave
    track shifted so the current position is in the middle.
    """
    inclination = 51.6
    track = []
    for i in range(points + 1):
        frac = i / points
        offset_lon = (frac - 0.5) * 360  # span full orbit
        current_lon = lon + offset_lon
        # Latitude follows a sinusoidal pattern
        phase = 2 * math.pi * frac
        current_lat = inclination * math.sin(phase + math.asin(max(-1, min(1, lat / inclination))) if inclination != 0 else 0)
        # Clamp latitude
        current_lat = max(-90, min(90, current_lat))
        # Normalize longitude
        current_lon = ((current_lon + 180) % 360) - 180
        track.append((current_lat, current_lon))
    return track


def _split_track_at_antimeridian(track: list) -> list:
    """Split a ground track into segments at the antimeridian to avoid wrap-around lines."""
    segments = []
    current_segment = [track[0]]
    for i in range(1, len(track)):
        prev_lon = track[i - 1][1]
        curr_lon = track[i][1]
        if abs(curr_lon - prev_lon) > 180:
            segments.append(current_segment)
            current_segment = []
        current_segment.append(track[i])
    if current_segment:
        segments.append(current_segment)
    return segments


def _hazard_color(is_hazardous: bool) -> str:
    return "#ef4444" if is_hazardous else "#10b981"


def _format_km(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M km"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K km"
    return f"{value:.1f} km"


# ──────────────────────────────────────────────
# Render Functions for Each Mode
# ──────────────────────────────────────────────

def _render_iss_tracker():
    """Mode 1: ISS Live Tracker."""
    import folium

    st.markdown("#### ISS Live Position")

    with st.spinner("Fetching ISS position..."):
        pos = fetch_iss_position()

    if pos.get("error"):
        st.error(f"Failed to fetch ISS position: {pos['error']}")
        return

    lat = pos["latitude"]
    lon = pos["longitude"]
    ts = pos.get("timestamp", 0)
    utc_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC") if ts else "Unknown"

    # ── Metrics ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Latitude", f"{lat:.4f}")
    with c2:
        st.metric("Longitude", f"{lon:.4f}")
    with c3:
        st.metric("Altitude", f"{ISS_ALTITUDE_KM} km")
    with c4:
        st.metric("Velocity", f"{ISS_VELOCITY_KMH:,} km/h")

    c5, c6 = st.columns(2)
    with c5:
        st.metric("Orbital Period", f"{ISS_ORBITAL_PERIOD_MIN:.1f} min")
    with c6:
        st.metric("Timestamp (UTC)", utc_str)

    # ── Folium Map ──
    st.markdown("---")
    st.markdown("#### ISS Ground Track Map")

    m = folium.Map(
        location=[lat, lon],
        zoom_start=3,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # ISS marker
    folium.CircleMarker(
        location=[lat, lon],
        radius=12,
        color="#06b6d4",
        fill=True,
        fill_color="#06b6d4",
        fill_opacity=0.9,
        weight=2,
        popup=folium.Popup(
            f"""<div style="max-width:200px;">
                <strong>ISS</strong><br/>
                Lat: {lat:.4f}, Lon: {lon:.4f}<br/>
                Alt: {ISS_ALTITUDE_KM} km<br/>
                Speed: {ISS_VELOCITY_KMH:,} km/h<br/>
                <span style="font-size:0.8rem;">{utc_str}</span>
            </div>""",
            max_width=220,
        ),
    ).add_to(m)

    # Outer glow ring
    folium.CircleMarker(
        location=[lat, lon],
        radius=20,
        color="#06b6d4",
        fill=False,
        weight=1,
        opacity=0.4,
    ).add_to(m)

    # Approximate ground track
    track = _approximate_ground_track(lat, lon, points=100)
    segments = _split_track_at_antimeridian(track)
    for seg in segments:
        if len(seg) >= 2:
            folium.PolyLine(
                locations=seg,
                color="#06b6d4",
                weight=1.5,
                opacity=0.4,
                dash_array="6 4",
            ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── TLE Info ──
    with st.expander("ISS Orbital Elements (TLE)", expanded=False):
        tle_data = fetch_iss_tle()
        if tle_data.get("error"):
            st.warning(f"Could not fetch TLE data: {tle_data['error']}")
        else:
            st.code(
                f"Name: {tle_data.get('name', 'ISS')}\n"
                f"Line 1: {tle_data.get('line1', 'N/A')}\n"
                f"Line 2: {tle_data.get('line2', 'N/A')}",
                language=None,
            )
            st.caption("Two-Line Element set describing ISS orbital parameters.")

    st.info("ISS position updates every ~15 seconds. Refresh the page or re-run for the latest position.")


def _render_astronauts():
    """Mode 2: Astronauts Currently in Space."""
    st.markdown("#### People in Space Right Now")

    with st.spinner("Fetching astronaut data..."):
        data = fetch_astronauts()

    if data.get("error"):
        st.error(f"Failed to fetch astronaut data: {data['error']}")
        return

    total = data.get("number", 0)
    people = data.get("people", [])

    # ── Summary Metrics ──
    crafts = {}
    for person in people:
        craft = person.get("craft", "Unknown")
        crafts[craft] = crafts.get(craft, 0) + 1

    cols = st.columns(min(len(crafts) + 1, 5))
    with cols[0]:
        st.metric("Total in Space", str(total))
    for i, (craft, count) in enumerate(crafts.items()):
        if i + 1 < len(cols):
            with cols[i + 1]:
                st.metric(craft, str(count))

    st.markdown("---")

    # ── Astronaut Cards ──
    craft_colors = {
        "ISS": "#06b6d4",
        "Tiangong": "#f59e0b",
    }

    # Group by craft
    grouped = {}
    for person in people:
        craft = person.get("craft", "Unknown")
        grouped.setdefault(craft, []).append(person.get("name", "Unknown"))

    for craft, names in grouped.items():
        color = craft_colors.get(craft, "#8b5cf6")
        safe_craft = html_module.escape(str(craft))
        st.markdown(f"""
        <div style="margin-bottom:0.5rem; padding:0.3rem 0;">
            <span style="color:{color}; font-weight:700; font-size:1rem;">{safe_craft}</span>
            <span style="color:#5a6580; font-size:0.85rem;"> ({len(names)} crew)</span>
        </div>
        """, unsafe_allow_html=True)

        # Render cards in rows of 3
        row_size = 3
        for row_start in range(0, len(names), row_size):
            row_names = names[row_start:row_start + row_size]
            card_cols = st.columns(row_size)
            for j, name in enumerate(row_names):
                with card_cols[j]:
                    safe_name = html_module.escape(str(name))
                    initials = "".join(w[0].upper() for w in name.split() if w)[:2]
                    safe_initials = html_module.escape(str(initials))
                    st.markdown(f"""
                    <div class="bio-card" style="text-align:center; padding:1rem 0.75rem;">
                        <div style="width:48px; height:48px; border-radius:50%; background:{color}20;
                                    display:flex; align-items:center; justify-content:center;
                                    margin:0 auto 0.5rem auto;">
                            <span style="color:{color}; font-weight:700; font-size:1.1rem;">{safe_initials}</span>
                        </div>
                        <div style="color:#e8ecf4; font-weight:600; font-size:0.9rem;">{safe_name}</div>
                        <div style="color:#5a6580; font-size:0.75rem; margin-top:0.2rem;">{safe_craft}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.caption(f"Data from Open Notify API. Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


def _render_neo():
    """Mode 3: Near-Earth Objects."""
    st.markdown("#### Near-Earth Objects (Asteroids)")

    today = datetime.utcnow().date()
    end_date = today + timedelta(days=7)

    st.markdown(f"Showing NEOs from **{today}** to **{end_date}** (NASA DEMO_KEY, rate-limited).")

    with st.spinner("Fetching NEO data from NASA..."):
        data = fetch_neo_feed(str(today), str(end_date))

    if data.get("error"):
        st.error(f"NASA NEO API error: {data['error']}")
        return

    element_count = data.get("element_count", 0)
    neo_objects = data.get("near_earth_objects", {})

    if element_count == 0:
        st.warning("No NEO data available for the selected period.")
        return

    # Flatten all NEOs into a list
    all_neos = []
    for date_str, neos in neo_objects.items():
        for neo in neos:
            est_diam = neo.get("estimated_diameter", {}).get("kilometers", {})
            close_approaches = neo.get("close_approach_data", [])
            if close_approaches:
                approach = close_approaches[0]
                miss_km = float(approach.get("miss_distance", {}).get("kilometers", 0))
                velocity_kmh = float(approach.get("relative_velocity", {}).get("kilometers_per_hour", 0))
                approach_date = approach.get("close_approach_date", date_str)
            else:
                miss_km = 0
                velocity_kmh = 0
                approach_date = date_str

            all_neos.append({
                "name": neo.get("name", "Unknown"),
                "id": neo.get("id", ""),
                "diameter_min_km": est_diam.get("estimated_diameter_min", 0),
                "diameter_max_km": est_diam.get("estimated_diameter_max", 0),
                "is_hazardous": neo.get("is_potentially_hazardous_asteroid", False),
                "miss_distance_km": miss_km,
                "velocity_kmh": velocity_kmh,
                "approach_date": approach_date,
                "absolute_magnitude": neo.get("absolute_magnitude_h", 0),
            })

    # Sort by closest approach
    all_neos.sort(key=lambda x: x["miss_distance_km"])

    hazardous_count = sum(1 for n in all_neos if n["is_hazardous"])
    closest = all_neos[0] if all_neos else None

    # ── Stats ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total NEOs (7 days)", f"{element_count:,}")
    with c2:
        st.metric("Potentially Hazardous", str(hazardous_count),
                   delta="Caution" if hazardous_count > 0 else "None",
                   delta_color="inverse" if hazardous_count > 0 else "off")
    with c3:
        if closest:
            st.metric("Closest Approach", _format_km(closest["miss_distance_km"]))
        else:
            st.metric("Closest Approach", "--")
    with c4:
        if closest:
            st.metric("Closest Object", closest["name"])
        else:
            st.metric("Closest Object", "--")

    # ── Data Table ──
    st.markdown("---")
    st.markdown("#### NEO Data Table")

    df = pd.DataFrame(all_neos)
    df_display = df[[
        "name", "approach_date", "diameter_min_km", "diameter_max_km",
        "velocity_kmh", "miss_distance_km", "is_hazardous",
    ]].copy()
    df_display.columns = [
        "Name", "Approach Date", "Diameter Min (km)", "Diameter Max (km)",
        "Velocity (km/h)", "Miss Distance (km)", "Hazardous",
    ]
    df_display["Diameter Min (km)"] = df_display["Diameter Min (km)"].map(lambda x: f"{x:.4f}")
    df_display["Diameter Max (km)"] = df_display["Diameter Max (km)"].map(lambda x: f"{x:.4f}")
    df_display["Velocity (km/h)"] = df_display["Velocity (km/h)"].map(lambda x: f"{x:,.0f}")
    df_display["Miss Distance (km)"] = df_display["Miss Distance (km)"].map(lambda x: f"{x:,.0f}")

    st.dataframe(df_display, width="stretch", hide_index=True)

    # ── Scatter Plot: Diameter vs Miss Distance ──
    st.markdown("---")
    st.markdown("#### Diameter vs Miss Distance")

    diameters = [(n["diameter_min_km"] + n["diameter_max_km"]) / 2 for n in all_neos]
    miss_distances = [n["miss_distance_km"] for n in all_neos]
    hazardous_flags = [n["is_hazardous"] for n in all_neos]

    if diameters and miss_distances:
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#0a0e1a")

        # Split into hazardous and safe
        safe_d = [d for d, h in zip(diameters, hazardous_flags) if not h]
        safe_m = [m for m, h in zip(miss_distances, hazardous_flags) if not h]
        haz_d = [d for d, h in zip(diameters, hazardous_flags) if h]
        haz_m = [m for m, h in zip(miss_distances, hazardous_flags) if h]

        if safe_d:
            ax.scatter(safe_m, safe_d, c="#06b6d4", alpha=0.7, s=40, label="Safe", edgecolors="#0a0e1a", linewidth=0.5)
        if haz_d:
            ax.scatter(haz_m, haz_d, c="#ef4444", alpha=0.9, s=60, label="Hazardous", edgecolors="#0a0e1a", linewidth=0.5, marker="D")

        ax.set_xlabel("Miss Distance (km)", color="#8b97b0", fontsize=10)
        ax.set_ylabel("Avg Diameter (km)", color="#8b97b0", fontsize=10)
        ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
        ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

        # Use log scale if range is large
        if miss_distances and max(miss_distances) > 10 * min(d for d in miss_distances if d > 0):
            ax.set_xscale("log")
        if diameters and max(diameters) > 10 * min(d for d in diameters if d > 0):
            ax.set_yscale("log")

        legend = ax.legend(facecolor="#111827", edgecolor="#2a3550", labelcolor="#e8ecf4", fontsize=9)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── Download ──
    st.markdown("---")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(all_neos)} NEOs (CSV)",
        data=csv_buf.getvalue(),
        file_name="near_earth_objects.csv",
        mime="text/csv",
        key="neo_download",
    )


def _render_apod():
    """Mode 4: NASA Astronomy Picture of the Day."""
    st.markdown("#### NASA Astronomy Picture of the Day")

    with st.spinner("Fetching APOD from NASA..."):
        data = fetch_apod()

    if data.get("error"):
        st.error(f"NASA APOD API error: {data['error']}")
        return

    title = data.get("title", "Untitled")
    explanation = data.get("explanation", "")
    url = data.get("url", "")
    hdurl = data.get("hdurl", url)
    date = data.get("date", "")
    copyright_info = data.get("copyright", "")
    media_type = data.get("media_type", "image")

    # ── Title & Date ──
    safe_title = html_module.escape(str(title))
    safe_date = html_module.escape(str(date))
    safe_copyright = html_module.escape(str(copyright_info)) if copyright_info else ""
    st.markdown(f"""
    <div style="margin-bottom:0.75rem;">
        <span style="color:#e8ecf4; font-weight:700; font-size:1.2rem;">{safe_title}</span><br/>
        <span style="color:#5a6580; font-size:0.85rem;">{safe_date}</span>
        {f'<span style="color:#5a6580; font-size:0.8rem;"> | &copy; {safe_copyright}</span>' if copyright_info else ''}
    </div>
    """, unsafe_allow_html=True)

    # ── Image or Video ──
    if media_type == "image" and url:
        st.image(url, caption=title, use_container_width=True)
        if hdurl and hdurl != url:
            st.markdown(f"[View HD version]({hdurl})")
    elif media_type == "video" and url:
        st.video(url)
    else:
        st.warning("No image or video available for today's APOD.")

    # ── Explanation ──
    if explanation:
        st.markdown("---")
        st.markdown("**Explanation**")
        safe_explanation = html_module.escape(str(explanation))
        st.markdown(f"""
        <div style="color:#8b97b0; font-size:0.9rem; line-height:1.6;">
            {safe_explanation}
        </div>
        """, unsafe_allow_html=True)

    st.caption("Data from NASA Astronomy Picture of the Day API (DEMO_KEY).")


# ──────────────────────────────────────────────
# Main Render Entry Point
# ──────────────────────────────────────────────

def render_space_tracker_tab():
    """Main render function for the Space & ISS Tracker tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Space & ISS Tracker</h4>
        <p>Real-time ISS position, astronauts in space, near-Earth asteroids, and NASA imagery &mdash; free APIs.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode Selector ──
    mode = st.selectbox("Select Mode", [
        "ISS Live Tracker",
        "Astronauts in Space",
        "Near-Earth Objects",
        "NASA APOD",
    ], key="space_mode")

    st.markdown("---")

    # ── Dispatch ──
    if mode == "ISS Live Tracker":
        _render_iss_tracker()
    elif mode == "Astronauts in Space":
        _render_astronauts()
    elif mode == "Near-Earth Objects":
        _render_neo()
    elif mode == "NASA APOD":
        _render_apod()
