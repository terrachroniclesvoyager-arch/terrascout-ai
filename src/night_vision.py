"""
Night Sky & Light Pollution module for TerraScout AI.
Visualizes light pollution using NASA VIIRS tiles, estimates Bortle scale,
and shows nearest dark sky sites for stargazing.
"""

import logging
import math
import requests
import pandas as pd
import streamlit as st
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

from src.map_factory import MapFactory


# IDA International Dark Sky Places (curated selection)
DARK_SKY_SITES = [
    {"name": "NamibRand Nature Reserve", "country": "Namibia", "lat": -24.75, "lon": 15.95, "type": "Reserve", "bortle": 1},
    {"name": "Aoraki Mackenzie", "country": "New Zealand", "lat": -44.00, "lon": 170.47, "type": "Reserve", "bortle": 1},
    {"name": "Pic du Midi", "country": "France", "lat": 42.94, "lon": 0.14, "type": "Reserve", "bortle": 2},
    {"name": "Kerry Dark Sky Reserve", "country": "Ireland", "lat": 51.77, "lon": -9.85, "type": "Reserve", "bortle": 2},
    {"name": "Galloway Forest Park", "country": "UK", "lat": 55.05, "lon": -4.43, "type": "Park", "bortle": 2},
    {"name": "Zselic Starry Sky Park", "country": "Hungary", "lat": 46.25, "lon": 17.78, "type": "Park", "bortle": 2},
    {"name": "Westhavelland", "country": "Germany", "lat": 52.72, "lon": 12.25, "type": "Park", "bortle": 3},
    {"name": "Brecon Beacons", "country": "UK", "lat": 51.88, "lon": -3.44, "type": "Reserve", "bortle": 3},
    {"name": "Mont-Megantic", "country": "Canada", "lat": 45.45, "lon": -71.15, "type": "Reserve", "bortle": 2},
    {"name": "Natural Bridges NM", "country": "USA", "lat": 37.60, "lon": -110.01, "type": "Park", "bortle": 1},
    {"name": "Cherry Springs SP", "country": "USA", "lat": 41.66, "lon": -77.82, "type": "Park", "bortle": 2},
    {"name": "Big Bend NP", "country": "USA", "lat": 29.25, "lon": -103.25, "type": "Park", "bortle": 2},
    {"name": "Death Valley NP", "country": "USA", "lat": 36.46, "lon": -116.87, "type": "Park", "bortle": 2},
    {"name": "Mauna Kea", "country": "USA", "lat": 19.82, "lon": -155.47, "type": "Sanctuary", "bortle": 1},
    {"name": "Atacama Desert", "country": "Chile", "lat": -24.59, "lon": -69.33, "type": "Reserve", "bortle": 1},
    {"name": "Tekapo", "country": "New Zealand", "lat": -44.00, "lon": 170.48, "type": "Reserve", "bortle": 1},
    {"name": "Elqui Valley", "country": "Chile", "lat": -30.17, "lon": -70.83, "type": "Reserve", "bortle": 1},
    {"name": "Tenerife", "country": "Spain", "lat": 28.30, "lon": -16.51, "type": "Reserve", "bortle": 2},
    {"name": "La Palma", "country": "Spain", "lat": 28.76, "lon": -17.89, "type": "Reserve", "bortle": 1},
    {"name": "Sagarmatha NP", "country": "Nepal", "lat": 27.99, "lon": 86.93, "type": "Park", "bortle": 1},
    {"name": "Jasper NP", "country": "Canada", "lat": 52.87, "lon": -117.85, "type": "Park", "bortle": 2},
    {"name": "Exmoor NP", "country": "UK", "lat": 51.15, "lon": -3.63, "type": "Park", "bortle": 3},
    {"name": "Hortobagy NP", "country": "Hungary", "lat": 47.58, "lon": 21.15, "type": "Park", "bortle": 2},
    {"name": "Cevennes NP", "country": "France", "lat": 44.35, "lon": 3.58, "type": "Reserve", "bortle": 2},
    {"name": "Eifel NP", "country": "Germany", "lat": 50.52, "lon": 6.40, "type": "Park", "bortle": 3},
    {"name": "Central Idaho", "country": "USA", "lat": 44.27, "lon": -114.93, "type": "Reserve", "bortle": 1},
    {"name": "Headlands", "country": "USA", "lat": 45.78, "lon": -84.76, "type": "Park", "bortle": 3},
    {"name": "Cosmic Campground", "country": "USA", "lat": 33.41, "lon": -108.95, "type": "Sanctuary", "bortle": 1},
    {"name": "Aarhus", "country": "Denmark", "lat": 56.15, "lon": 10.22, "type": "Community", "bortle": 4},
    {"name": "Moffat", "country": "UK", "lat": 55.33, "lon": -3.44, "type": "Community", "bortle": 3},
    {"name": "Warrumbungle NP", "country": "Australia", "lat": -31.28, "lon": 149.00, "type": "Park", "bortle": 2},
    {"name": "River Murray", "country": "Australia", "lat": -34.35, "lon": 140.77, "type": "Reserve", "bortle": 2},
    {"name": "Alqueva", "country": "Portugal", "lat": 38.20, "lon": -7.50, "type": "Reserve", "bortle": 2},
    {"name": "Ramon Crater", "country": "Israel", "lat": 30.60, "lon": 34.80, "type": "Park", "bortle": 2},
    {"name": "Yeongyang", "country": "South Korea", "lat": 36.66, "lon": 129.18, "type": "Park", "bortle": 3},
    {"name": "Man & Biosphere Rhon", "country": "Germany", "lat": 50.45, "lon": 10.00, "type": "Reserve", "bortle": 3},
]
# Major cities for Bortle estimation
MAJOR_CITIES = [
    {"name": "Tokyo", "lat": 35.68, "lon": 139.69, "pop_M": 37.4},
    {"name": "Delhi", "lat": 28.61, "lon": 77.23, "pop_M": 32.9},
    {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "pop_M": 28.5},
    {"name": "Sao Paulo", "lat": -23.55, "lon": -46.63, "pop_M": 22.4},
    {"name": "Mexico City", "lat": 19.43, "lon": -99.13, "pop_M": 21.8},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "pop_M": 21.3},
    {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "pop_M": 21.0},
    {"name": "Beijing", "lat": 39.90, "lon": 116.40, "pop_M": 20.9},
    {"name": "Dhaka", "lat": 23.81, "lon": 90.41, "pop_M": 17.1},
    {"name": "Osaka", "lat": 34.69, "lon": 135.50, "pop_M": 19.1},
    {"name": "New York", "lat": 40.71, "lon": -74.01, "pop_M": 18.8},
    {"name": "Karachi", "lat": 24.86, "lon": 67.01, "pop_M": 16.5},
    {"name": "Buenos Aires", "lat": -34.60, "lon": -58.38, "pop_M": 15.4},
    {"name": "Istanbul", "lat": 41.01, "lon": 28.98, "pop_M": 15.6},
    {"name": "Lagos", "lat": 6.52, "lon": 3.38, "pop_M": 15.4},
    {"name": "London", "lat": 51.51, "lon": -0.13, "pop_M": 9.5},
    {"name": "Paris", "lat": 48.86, "lon": 2.35, "pop_M": 11.1},
    {"name": "Moscow", "lat": 55.76, "lon": 37.62, "pop_M": 12.6},
    {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "pop_M": 12.5},
    {"name": "Rome", "lat": 41.90, "lon": 12.50, "pop_M": 4.3},
    {"name": "Berlin", "lat": 52.52, "lon": 13.41, "pop_M": 3.7},
    {"name": "Madrid", "lat": 40.42, "lon": -3.70, "pop_M": 6.7},
    {"name": "Sydney", "lat": -33.87, "lon": 151.21, "pop_M": 5.4},
    {"name": "Chicago", "lat": 41.88, "lon": -87.63, "pop_M": 8.9},
    {"name": "Johannesburg", "lat": -26.20, "lon": 28.05, "pop_M": 6.1},
]


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_bortle(lat, lon):
    """Estimate Bortle scale (1-9) based on distance to major cities."""
    max_weighted = 0
    for city in MAJOR_CITIES:
        dist = _haversine(lat, lon, city["lat"], city["lon"])
        # Weight by population: larger cities have wider light domes
        dome_radius = city["pop_M"] * 8  # km of light dome influence
        if dist < dome_radius:
            weight = (1 - dist / dome_radius) * city["pop_M"]
            if weight > max_weighted:
                max_weighted = weight
    
    # Find closest city distance
    closest_dist = min((_haversine(lat, lon, c["lat"], c["lon"]) for c in MAJOR_CITIES), default=500)
    
    # Simple Bortle estimation based on distance to nearest large city
    if closest_dist > 300:
        return 1  # Excellent dark-sky site
    elif closest_dist > 200:
        return 2
    elif closest_dist > 100:
        return 3
    elif closest_dist > 60:
        return 4
    elif closest_dist > 40:
        return 5
    elif closest_dist > 20:
        return 6
    elif closest_dist > 10:
        return 7
    elif closest_dist > 5:
        return 8
    else:
        return 9  # Inner-city sky


BORTLE_DESC = {
    1: ("Excellent dark-sky site", "#064e3b"),
    2: ("Truly dark site", "#065f46"),
    3: ("Rural sky", "#047857"),
    4: ("Rural/suburban transition", "#059669"),
    5: ("Suburban sky", "#f59e0b"),
    6: ("Bright suburban sky", "#d97706"),
    7: ("Suburban/urban transition", "#ea580c"),
    8: ("City sky", "#dc2626"),
    9: ("Inner-city sky", "#991b1b"),
}


@st.cache_data(ttl=3600)
def _fetch_cloud_cover(lat, lon):
    """Fetch current cloud cover from Open-Meteo."""
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "cloud_cover",
        }, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("current", {}).get("cloud_cover")
    except Exception:
        pass
    return None



def render_night_vision_tab():
    """Main render function for Night Sky & Light Pollution tab."""
    st.markdown("""
    <div class="tab-header indigo">
        <h4>🌙 Night Sky & Light Pollution</h4>
        <p>Light pollution map, Bortle scale estimation &amp; best stargazing spots worldwide</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        lat = st.number_input("Latitude", -90.0, 90.0, 41.90, step=0.01, key="nv_lat", format="%.4f")
    with col2:
        lon = st.number_input("Longitude", -180.0, 180.0, 12.50, step=0.01, key="nv_lon", format="%.4f")
    with col3:
        show_sites = st.checkbox("Show Dark Sky Sites", value=True, key="nv_sites")

    if st.button("🌙 Analyze Night Sky", type="primary", use_container_width=True):
        bortle = _estimate_bortle(lat, lon)
        desc, color = BORTLE_DESC[bortle]
        cloud = _fetch_cloud_cover(lat, lon)

        # Bortle gauge
        st.markdown("### Bortle Scale Assessment")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div style="background:{color}; color:white; padding:1.5rem; border-radius:12px; text-align:center;">
                <h1 style="margin:0; font-size:3rem;">{bortle}</h1>
                <p style="margin:0.5rem 0 0 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            if cloud is not None:
                sky_status = "Clear" if cloud < 20 else "Partly Cloudy" if cloud < 60 else "Cloudy"
                st.metric("Cloud Cover", f"{cloud}%")
                st.metric("Sky Status", sky_status)
                good = cloud < 30 and bortle <= 4
                st.markdown(f"**Stargazing:** {'Excellent' if good else 'Fair' if cloud < 50 else 'Poor'}")
            else:
                st.metric("Cloud Cover", "N/A")
        with m3:
            # Nearest dark sky site
            sites_dist = [(s, _haversine(lat, lon, s["lat"], s["lon"])) for s in DARK_SKY_SITES]
            sites_dist.sort(key=lambda x: x[1])
            nearest = sites_dist[0]
            st.metric("Nearest Dark Sky Site", nearest[0]["name"])
            st.metric("Distance", f"{nearest[1]:.0f} km")
            st.caption(f"{nearest[0]['country']} | Bortle {nearest[0]['bortle']}")
        # Map with VIIRS night lights
        st.markdown("### Light Pollution Map")
        m = MapFactory.create_base_map(center=(lat, lon), zoom=7, tile_layer="cartodb_dark")

        # NASA VIIRS Day/Night Band tile layer
        folium.TileLayer(
            tiles="https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg",
            attr="NASA VIIRS",
            name="VIIRS Night Lights",
            overlay=True,
            opacity=0.7,
        ).add_to(m)

        # User location marker
        MapFactory.add_marker(m, (lat, lon), popup=f"Your Location<br>Bortle: {bortle}",
                              tooltip=f"Bortle {bortle}: {desc}",
                              icon="star", icon_color="yellow")

        # Dark sky sites
        if show_sites:
            for site in DARK_SKY_SITES:
                dist = _haversine(lat, lon, site["lat"], site["lon"])
                if dist < 3000:  # Show within 3000 km
                    MapFactory.add_circle_marker(
                        m, (site["lat"], site["lon"]),
                        radius=8,
                        color="#10b981",
                        popup=f"<b>{site['name']}</b><br>{site['country']}<br>Bortle: {site['bortle']}<br>{site['type']}",
                        tooltip=site["name"],
                    )

        folium.LayerControl().add_to(m)
        st_html(m._repr_html_(), height=500)

        # Top 10 nearest dark sky sites
        st.markdown("### Nearest Dark Sky Sites")
        top10 = sites_dist[:10]
        df_sites = pd.DataFrame([{
            "Name": s["name"],
            "Country": s["country"],
            "Type": s["type"],
            "Bortle": s["bortle"],
            "Distance (km)": round(d, 1),
            "Lat": s["lat"],
            "Lon": s["lon"],
        } for s, d in top10])
        st.dataframe(df_sites, use_container_width=True, hide_index=True)

        # Bortle scale reference
        with st.expander("Bortle Scale Reference"):
            for b in range(1, 10):
                d, c = BORTLE_DESC[b]
                bar_width = b * 11
                st.markdown(f"""
                <div style="display:flex; align-items:center; margin:4px 0;">
                    <span style="width:30px; font-weight:bold;">{b}</span>
                    <div style="background:{c}; width:{bar_width}%; height:24px; border-radius:4px; margin:0 8px;"></div>
                    <span>{d}</span>
                </div>
                """, unsafe_allow_html=True)
