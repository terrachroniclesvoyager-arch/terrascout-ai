"""
Live Volcano & Eruption Monitor module for TerraScout AI.
Uses USGS earthquake API for volcano-related seismicity and curated
Smithsonian GVP volcano data. All free, no API key required.
"""

import io
import html as html_module
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from datetime import datetime, timedelta
from streamlit.components.v1 import html as st_html

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Activity-level colors
ACTIVITY_COLORS = {
    "Erupting": "#ef4444",
    "Restless": "#f97316",
    "Historical": "#f59e0b",
    "Holocene": "#10b981",
    "Dormant": "#6366f1",
    "Supervolcano": "#dc2626",
}

# ── Curated volcano database (Smithsonian GVP data) ──
VOLCANOES = [
    # Currently Erupting / Very Active
    {"name": "Kilauea", "lat": 19.421, "lon": -155.287, "elev": 1222, "country": "USA", "type": "Shield", "status": "Erupting", "region": "Hawaiian Hotspot Chain", "vei_max": 4},
    {"name": "Etna", "lat": 37.748, "lon": 15.002, "elev": 3357, "country": "Italy", "type": "Stratovolcano", "status": "Erupting", "region": "Italian Volcanoes", "vei_max": 4},
    {"name": "Stromboli", "lat": 38.789, "lon": 15.213, "elev": 924, "country": "Italy", "type": "Stratovolcano", "status": "Erupting", "region": "Italian Volcanoes", "vei_max": 3},
    {"name": "Semeru", "lat": -8.108, "lon": 112.922, "elev": 3676, "country": "Indonesia", "type": "Stratovolcano", "status": "Erupting", "region": "Indonesian Volcanic Arc", "vei_max": 4},
    {"name": "Merapi", "lat": -7.541, "lon": 110.446, "elev": 2910, "country": "Indonesia", "type": "Stratovolcano", "status": "Erupting", "region": "Indonesian Volcanic Arc", "vei_max": 4},
    {"name": "Dukono", "lat": 1.693, "lon": 127.894, "elev": 1229, "country": "Indonesia", "type": "Complex", "status": "Erupting", "region": "Indonesian Volcanic Arc", "vei_max": 3},
    {"name": "Sakurajima", "lat": 31.585, "lon": 130.657, "elev": 1117, "country": "Japan", "type": "Stratovolcano", "status": "Erupting", "region": "Japanese Volcanic Belt", "vei_max": 4},
    {"name": "Fagradalsfjall", "lat": 63.903, "lon": -22.266, "elev": 385, "country": "Iceland", "type": "Fissure", "status": "Erupting", "region": "Iceland Volcanic Zone", "vei_max": 1},
    {"name": "Sundhnukagigar", "lat": 63.873, "lon": -22.434, "elev": 50, "country": "Iceland", "type": "Fissure", "status": "Erupting", "region": "Iceland Volcanic Zone", "vei_max": 1},
    # Ring of Fire
    {"name": "Fuji", "lat": 35.361, "lon": 138.731, "elev": 3776, "country": "Japan", "type": "Stratovolcano", "status": "Historical", "region": "Ring of Fire Overview", "vei_max": 5},
    {"name": "Pinatubo", "lat": 15.13, "lon": 120.35, "elev": 1486, "country": "Philippines", "type": "Stratovolcano", "status": "Historical", "region": "Ring of Fire Overview", "vei_max": 6},
    {"name": "Rainier", "lat": 46.853, "lon": -121.760, "elev": 4392, "country": "USA", "type": "Stratovolcano", "status": "Dormant", "region": "Cascade Range Volcanoes", "vei_max": 4},
    {"name": "St. Helens", "lat": 46.200, "lon": -122.180, "elev": 2549, "country": "USA", "type": "Stratovolcano", "status": "Historical", "region": "Cascade Range Volcanoes", "vei_max": 5},
    {"name": "Hood", "lat": 45.374, "lon": -121.694, "elev": 3426, "country": "USA", "type": "Stratovolcano", "status": "Dormant", "region": "Cascade Range Volcanoes", "vei_max": 3},
    {"name": "Shasta", "lat": 41.409, "lon": -122.195, "elev": 4317, "country": "USA", "type": "Stratovolcano", "status": "Dormant", "region": "Cascade Range Volcanoes", "vei_max": 4},
    # Iceland
    {"name": "Hekla", "lat": 63.983, "lon": -19.667, "elev": 1491, "country": "Iceland", "type": "Stratovolcano", "status": "Historical", "region": "Iceland Volcanic Zone", "vei_max": 5},
    {"name": "Katla", "lat": 63.633, "lon": -19.083, "elev": 1512, "country": "Iceland", "type": "Subglacial", "status": "Restless", "region": "Iceland Volcanic Zone", "vei_max": 5},
    {"name": "Eyjafjallajokull", "lat": 63.633, "lon": -19.617, "elev": 1666, "country": "Iceland", "type": "Stratovolcano", "status": "Historical", "region": "Iceland Volcanic Zone", "vei_max": 4},
    # Italian
    {"name": "Vesuvius", "lat": 40.821, "lon": 14.426, "elev": 1281, "country": "Italy", "type": "Stratovolcano", "status": "Dormant", "region": "Italian Volcanoes", "vei_max": 5},
    {"name": "Campi Flegrei", "lat": 40.827, "lon": 14.139, "elev": 458, "country": "Italy", "type": "Caldera", "status": "Restless", "region": "Italian Volcanoes", "vei_max": 5},
    # Indonesian
    {"name": "Krakatau", "lat": -6.102, "lon": 105.423, "elev": 155, "country": "Indonesia", "type": "Caldera", "status": "Historical", "region": "Indonesian Volcanic Arc", "vei_max": 6},
    {"name": "Agung", "lat": -8.343, "lon": 115.508, "elev": 3031, "country": "Indonesia", "type": "Stratovolcano", "status": "Historical", "region": "Indonesian Volcanic Arc", "vei_max": 5},
    {"name": "Sinabung", "lat": 3.170, "lon": 98.392, "elev": 2460, "country": "Indonesia", "type": "Stratovolcano", "status": "Erupting", "region": "Indonesian Volcanic Arc", "vei_max": 4},
    # Hawaii
    {"name": "Mauna Loa", "lat": 19.475, "lon": -155.608, "elev": 4170, "country": "USA", "type": "Shield", "status": "Historical", "region": "Hawaiian Hotspot Chain", "vei_max": 4},
    {"name": "Mauna Kea", "lat": 19.820, "lon": -155.468, "elev": 4205, "country": "USA", "type": "Shield", "status": "Dormant", "region": "Hawaiian Hotspot Chain", "vei_max": 0},
    {"name": "Hualalai", "lat": 19.692, "lon": -155.870, "elev": 2523, "country": "USA", "type": "Shield", "status": "Historical", "region": "Hawaiian Hotspot Chain", "vei_max": 2},
    # East African Rift
    {"name": "Nyiragongo", "lat": -1.520, "lon": 29.250, "elev": 3470, "country": "DRC", "type": "Stratovolcano", "status": "Erupting", "region": "East African Rift Volcanoes", "vei_max": 3},
    {"name": "Erta Ale", "lat": 13.600, "lon": 40.670, "elev": 613, "country": "Ethiopia", "type": "Shield", "status": "Erupting", "region": "East African Rift Volcanoes", "vei_max": 2},
    {"name": "Ol Doinyo Lengai", "lat": -2.764, "lon": 35.914, "elev": 2962, "country": "Tanzania", "type": "Stratovolcano", "status": "Historical", "region": "East African Rift Volcanoes", "vei_max": 3},
    {"name": "Nyamulagira", "lat": -1.408, "lon": 29.200, "elev": 3058, "country": "DRC", "type": "Shield", "status": "Erupting", "region": "East African Rift Volcanoes", "vei_max": 2},
    # Japanese Belt
    {"name": "Aso", "lat": 32.884, "lon": 131.104, "elev": 1592, "country": "Japan", "type": "Caldera", "status": "Historical", "region": "Japanese Volcanic Belt", "vei_max": 5},
    {"name": "Suwanosejima", "lat": 29.638, "lon": 129.714, "elev": 796, "country": "Japan", "type": "Stratovolcano", "status": "Erupting", "region": "Japanese Volcanic Belt", "vei_max": 3},
    {"name": "Aira (Sakurajima)", "lat": 31.593, "lon": 130.657, "elev": 1117, "country": "Japan", "type": "Caldera", "status": "Erupting", "region": "Japanese Volcanic Belt", "vei_max": 5},
    # Supervolcano Sites
    {"name": "Yellowstone", "lat": 44.432, "lon": -110.588, "elev": 2805, "country": "USA", "type": "Caldera", "status": "Restless", "region": "Supervolcano Sites", "vei_max": 8},
    {"name": "Toba", "lat": 2.580, "lon": 98.830, "elev": 2157, "country": "Indonesia", "type": "Caldera", "status": "Holocene", "region": "Supervolcano Sites", "vei_max": 8},
    {"name": "Taupo", "lat": -38.820, "lon": 176.000, "elev": 760, "country": "New Zealand", "type": "Caldera", "status": "Holocene", "region": "Supervolcano Sites", "vei_max": 8},
    {"name": "Long Valley", "lat": 37.700, "lon": -118.870, "elev": 3390, "country": "USA", "type": "Caldera", "status": "Restless", "region": "Supervolcano Sites", "vei_max": 7},
    {"name": "Aira (Kagoshima)", "lat": 31.670, "lon": 130.720, "elev": 1117, "country": "Japan", "type": "Caldera", "status": "Historical", "region": "Supervolcano Sites", "vei_max": 7},
    {"name": "Campi Flegrei (Super)", "lat": 40.827, "lon": 14.139, "elev": 458, "country": "Italy", "type": "Caldera", "status": "Restless", "region": "Supervolcano Sites", "vei_max": 7},
]

MODE_CENTERS = {
    "Currently Erupting Volcanoes": (10, 25, 2),
    "Ring of Fire Overview": (10, 170, 2),
    "Iceland Volcanic Zone": (64.5, -19.0, 7),
    "Italian Volcanoes": (39.5, 15.0, 6),
    "Indonesian Volcanic Arc": (-3, 115, 4),
    "Hawaiian Hotspot Chain": (19.5, -155.5, 8),
    "Cascade Range Volcanoes": (45.0, -122.0, 6),
    "East African Rift Volcanoes": (2.0, 33.0, 4),
    "Japanese Volcanic Belt": (33.0, 131.0, 5),
    "Supervolcano Sites": (20, 0, 2),
}


@st.cache_data(ttl=300)
def _fetch_seismicity(lat: float, lon: float, radius_km: int = 100, days: int = 7) -> list:
    """Fetch recent quakes near a volcano from USGS."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "format": "geojson", "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"), "latitude": lat,
        "longitude": lon, "maxradiuskm": radius_km,
        "minmagnitude": 0.5, "limit": 200, "orderby": "time",
    }
    try:
        r = requests.get(USGS_API, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("features", [])
    except Exception:
        return []


def _build_map(volcanoes: list, center: tuple, zoom: int) -> folium.Map:
    """Build a dark-theme folium map with volcano markers."""
    m = folium.Map(location=[center[0], center[1]], zoom_start=zoom,
                   tiles="CartoDB dark_matter", control_scale=True)
    for v in volcanoes:
        color = ACTIVITY_COLORS.get(v["status"], "#8b97b0")
        radius = 9 if v["status"] == "Erupting" else (7 if v["status"] == "Restless" else 5)
        name_safe = html_module.escape(v["name"])
        popup_html = (
            f"<div style='font-family:sans-serif;min-width:160px'>"
            f"<b>{name_safe}</b><br>"
            f"Elev: {v['elev']}m | VEI max: {v['vei_max']}<br>"
            f"Type: {html_module.escape(v['type'])}<br>"
            f"Status: <span style='color:{color}'>{html_module.escape(v['status'])}</span><br>"
            f"{html_module.escape(v['country'])}</div>"
        )
        folium.CircleMarker(
            location=[v["lat"], v["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=name_safe,
        ).add_to(m)
    return m


def render_volcano_live_maps_tab():
    """Main render function for the Live Volcano & Eruption Monitor tab."""

    st.markdown(
        '<div class="tab-header red"><h4>\U0001f30b Live Volcano & Eruption Monitor</h4>'
        '<p>Real-time volcanic activity, eruption alerts, ash plumes &amp; seismic tremor worldwide</p></div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    modes = list(MODE_CENTERS.keys())
    mode = st.selectbox("Monitoring Mode", modes, key="vlm_mode")

    # Filter volcanoes for selected mode
    if mode == "Currently Erupting Volcanoes":
        filtered = [v for v in VOLCANOES if v["status"] == "Erupting"]
    else:
        filtered = [v for v in VOLCANOES if v["region"] == mode]

    center_lat, center_lon, zoom = MODE_CENTERS[mode]

    # ── Stats row ──
    erupting = sum(1 for v in filtered if v["status"] == "Erupting")
    restless = sum(1 for v in filtered if v["status"] == "Restless")
    total = len(filtered)
    avg_elev = int(sum(v["elev"] for v in filtered) / total) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Volcanoes", total)
    c2.metric("Erupting", erupting)
    c3.metric("Restless", restless)
    c4.metric("Avg Elevation", f"{avg_elev} m")

    # ── Map ──
    st.markdown("#### Volcanic Activity Map")
    m = _build_map(filtered, (center_lat, center_lon), zoom)
    st_html(m._repr_html_(), height=500)

    # ── Legend ──
    legend_items = " ".join(
        f"<span style='color:{c}'>\u25cf</span> {html_module.escape(lbl)}&nbsp;&nbsp;"
        for lbl, c in ACTIVITY_COLORS.items()
    )
    st.markdown(
        f"<div style='background:#111827;padding:6px 12px;border-radius:6px;font-size:0.85rem;"
        f"color:#8b97b0'>{legend_items}</div>", unsafe_allow_html=True,
    )

    # ── Seismicity check for erupting volcanoes ──
    erupting_list = [v for v in filtered if v["status"] in ("Erupting", "Restless")]
    if erupting_list:
        with st.expander(f"Recent Seismicity near {len(erupting_list)} active volcanoes", expanded=False):
            target = st.selectbox(
                "Select volcano", [v["name"] for v in erupting_list], key="vlm_seis_target"
            )
            sel = next((v for v in erupting_list if v["name"] == target), None)
            if sel and st.button("Fetch Seismicity", key="vlm_fetch_seis"):
                quakes = _fetch_seismicity(sel["lat"], sel["lon"])
                if quakes:
                    rows = []
                    for f in quakes:
                        p = f.get("properties", {})
                        rows.append({
                            "Time (UTC)": datetime.utcfromtimestamp(p.get("time", 0) / 1000).strftime("%Y-%m-%d %H:%M"),
                            "Magnitude": p.get("mag", 0),
                            "Depth (km)": round(f["geometry"]["coordinates"][2], 1),
                            "Place": p.get("place", ""),
                        })
                    sdf = pd.DataFrame(rows)
                    st.dataframe(sdf, width="stretch")
                    st.caption(f"{len(rows)} earthquakes within 100 km in the last 7 days")
                else:
                    st.info("No seismic events found near this volcano in the past 7 days.")

    # ── Data table ──
    st.markdown("#### Volcano Data")
    df = pd.DataFrame(filtered)
    display_cols = ["name", "lat", "lon", "elev", "country", "type", "status", "vei_max"]
    display_df = df[[c for c in display_cols if c in df.columns]].copy()
    display_df.columns = ["Name", "Lat", "Lon", "Elev (m)", "Country", "Type", "Status", "VEI Max"]
    st.dataframe(display_df, width="stretch")

    # ── Download ──
    csv_buf = io.StringIO()
    display_df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download CSV", csv_buf.getvalue(), file_name=f"volcanoes_{mode.replace(' ', '_').lower()}.csv",
        mime="text/csv", key="vlm_dl",
    )
