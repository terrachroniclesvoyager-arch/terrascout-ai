"""
LOCATION INTELLIGENCE - Deep Point Analysis
Click anywhere on the map to get comprehensive intelligence about that location
Aggregates data from 20+ APIs and databases
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
try:
    from streamlit_folium import st_folium
    HAS_ST_FOLIUM = True
except ImportError:
    HAS_ST_FOLIUM = False
import requests
from datetime import datetime
import concurrent.futures
from typing import Dict, List, Optional, Tuple
import json
import html as html_module

# Import UI components
try:
    from src.ui_components import (
        hero_section, category_header, info_card,
        stats_grid, success_banner, warning_banner, module_card
    )
except:
    # Fallback if imports fail
    def hero_section(*args, **kwargs): pass
    def category_header(*args, **kwargs): pass
    def info_card(*args, **kwargs): pass
    def stats_grid(*args, **kwargs): pass
    def success_banner(*args, **kwargs): pass
    def warning_banner(*args, **kwargs): pass
    def module_card(*args, **kwargs): pass


@st.cache_data(ttl=900)
def fetch_elevation(lat: float, lon: float) -> Dict:
    """Get elevation data from Open-Elevation API."""
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results_list = data.get('results', [])
            if not results_list:
                return {"success": False, "error": "No results"}
            elevation = results_list[0].get('elevation', 0)
            return {
                "success": True,
                "elevation_m": elevation,
                "elevation_ft": round(elevation * 3.28084, 1)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_weather(lat: float, lon: float) -> Dict:
    """Get current weather from Open-Meteo API."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            return {
                "success": True,
                "temperature_c": current.get('temperature_2m'),
                "humidity": current.get('relative_humidity_2m'),
                "precipitation": current.get('precipitation'),
                "wind_speed": current.get('wind_speed_10m'),
                "weather_code": current.get('weather_code'),
                "timezone": data.get('timezone')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_climate(lat: float, lon: float) -> Dict:
    """Get climate data (historical) from Open-Meteo."""
    try:
        url = "https://climate-api.open-meteo.com/v1/climate"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
            "models": "CMCC_CM2_VHR4",
            "daily": "temperature_2m_mean,precipitation_sum"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            daily = data.get('daily', {})
            temps = daily.get('temperature_2m_mean', [])
            precip = daily.get('precipitation_sum', [])

            if temps and precip:
                avg_temp = sum(temps) / len(temps)
                total_precip = sum(precip)
                return {
                    "success": True,
                    "avg_temperature_c": round(avg_temp, 1),
                    "annual_precipitation_mm": round(total_precip, 1)
                }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=300)
def fetch_reverse_geocode(lat: float, lon: float) -> Dict:
    """Reverse geocode to get location details from Nominatim."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18
        }
        headers = {"User-Agent": "TerraScout-AI/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            return {
                "success": True,
                "display_name": data.get('display_name'),
                "country": address.get('country'),
                "state": address.get('state'),
                "city": address.get('city') or address.get('town') or address.get('village'),
                "postcode": address.get('postcode'),
                "road": address.get('road'),
                "place_type": data.get('type'),
                "osm_type": data.get('osm_type'),
                "osm_id": data.get('osm_id')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_inaturalist(lat: float, lon: float, radius_km: float = 5) -> Dict:
    """Get nearby species observations from iNaturalist."""
    try:
        url = "https://api.inaturalist.org/v1/observations"
        params = {
            "lat": lat,
            "lng": lon,
            "radius": radius_km,
            "order": "desc",
            "order_by": "created_at",
            "per_page": 50,
            "quality_grade": "research"
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            species = []
            taxa_counts = {}

            for obs in results[:50]:
                taxon = obs.get('taxon', {})
                species_name = taxon.get('name')
                common_name = taxon.get('preferred_common_name')
                rank = taxon.get('rank')
                iconic_taxon = taxon.get('iconic_taxon_name', 'Unknown')

                if species_name:
                    species.append({
                        "name": species_name,
                        "common_name": common_name,
                        "rank": rank,
                        "type": iconic_taxon
                    })

                    taxa_counts[iconic_taxon] = taxa_counts.get(iconic_taxon, 0) + 1

            return {
                "success": True,
                "total_observations": len(species),
                "species": species[:20],  # Top 20
                "taxa_distribution": taxa_counts
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_gbif_species(lat: float, lon: float, radius_km: float = 5) -> Dict:
    """Get species data from GBIF."""
    try:
        url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            "decimalLatitude": lat,
            "decimalLongitude": lon,
            "limit": 100,
            "hasCoordinate": True,
            "hasGeospatialIssue": False
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            species_set = set()
            kingdoms = {}

            for record in results:
                species = record.get('species')
                kingdom = record.get('kingdom', 'Unknown')

                if species:
                    species_set.add(species)
                    kingdoms[kingdom] = kingdoms.get(kingdom, 0) + 1

            return {
                "success": True,
                "unique_species": len(species_set),
                "total_records": len(results),
                "kingdoms": kingdoms
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_osm_features(lat: float, lon: float, radius_m: int = 5000) -> Dict:
    """Get nearby features from OpenStreetMap via Overpass API."""
    try:
        # Build Overpass query for various features
        query = f"""
        [out:json][timeout:25];
        (
          node["aeroway"="heliport"](around:{radius_m},{lat},{lon});
          node["amenity"="hospital"](around:{radius_m},{lat},{lon});
          node["amenity"="school"](around:{radius_m},{lat},{lon});
          node["amenity"="university"](around:{radius_m},{lat},{lon});
          node["tourism"](around:{radius_m},{lat},{lon});
          node["natural"="peak"](around:{radius_m},{lat},{lon});
          way["natural"="water"](around:{radius_m},{lat},{lon});
          node["place"="city"](around:{radius_m},{lat},{lon});
          node["place"="town"](around:{radius_m},{lat},{lon});
          node["place"="village"](around:{radius_m},{lat},{lon});
          way["landuse"](around:{radius_m},{lat},{lon});
        );
        out center;
        """

        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data={"data": query}, timeout=30)

        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])

            # Categorize features
            categories = {
                "heliports": [],
                "hospitals": [],
                "schools": [],
                "universities": [],
                "tourism": [],
                "peaks": [],
                "water_bodies": [],
                "cities": [],
                "landuse": {}
            }

            for elem in elements:
                tags = elem.get('tags', {})

                if tags.get('aeroway') == 'heliport':
                    categories['heliports'].append(tags.get('name', 'Unnamed'))
                elif tags.get('amenity') == 'hospital':
                    categories['hospitals'].append(tags.get('name', 'Unnamed'))
                elif tags.get('amenity') == 'school':
                    categories['schools'].append(tags.get('name', 'Unnamed'))
                elif tags.get('amenity') == 'university':
                    categories['universities'].append(tags.get('name', 'Unnamed'))
                elif 'tourism' in tags:
                    categories['tourism'].append(tags.get('name', tags.get('tourism')))
                elif tags.get('natural') == 'peak':
                    peak_name = tags.get('name', 'Unnamed Peak')
                    elevation = tags.get('ele', 'N/A')
                    categories['peaks'].append(f"{peak_name} ({elevation}m)")
                elif tags.get('natural') == 'water':
                    categories['water_bodies'].append(tags.get('name', 'Unnamed'))
                elif tags.get('place') in ['city', 'town', 'village']:
                    place_name = tags.get('name', 'Unnamed')
                    population = tags.get('population', 'N/A')
                    categories['cities'].append(f"{place_name} (pop: {population})")
                elif 'landuse' in tags:
                    landuse_type = tags['landuse']
                    categories['landuse'][landuse_type] = categories['landuse'].get(landuse_type, 0) + 1

            return {
                "success": True,
                "categories": categories,
                "total_features": len(elements)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_earthquakes(lat: float, lon: float, radius_km: float = 100) -> Dict:
    """Get recent earthquakes from USGS."""
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "orderby": "time",
            "limit": 50
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])

            quakes = []
            for feat in features[:10]:
                props = feat.get('properties', {})
                quakes.append({
                    "magnitude": props.get('mag'),
                    "place": props.get('place'),
                    "time": props.get('time'),
                    "depth": (feat.get('geometry', {}).get('coordinates', [None, None, None])[2]
                             if len(feat.get('geometry', {}).get('coordinates', [])) > 2 else None)
                })

            return {
                "success": True,
                "total_earthquakes": len(features),
                "recent_quakes": quakes,
                "max_magnitude": max([q['magnitude'] for q in quakes if q['magnitude']], default=0)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


@st.cache_data(ttl=900)
def fetch_air_quality(lat: float, lon: float) -> Dict:
    """Get air quality data from OpenAQ."""
    try:
        url = "https://api.openaq.org/v2/latest"
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": 50000,  # 50km
            "limit": 1
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            if results:
                station = results[0]
                measurements = station.get('measurements', [])

                aqi_data = {}
                for m in measurements:
                    param = m.get('parameter')
                    value = m.get('value')
                    unit = m.get('unit')
                    aqi_data[param] = {"value": value, "unit": unit}

                return {
                    "success": True,
                    "station_name": station.get('location'),
                    "measurements": aqi_data,
                    "last_updated": station.get('lastUpdated')
                }
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False}


def analyze_location(lat: float, lon: float) -> Dict:
    """
    Comprehensive location analysis - fetches data from ALL sources in parallel.
    """
    st.info(f"🔍 Analyzing location: {lat:.4f}, {lon:.4f}")

    results = {}

    # Use ThreadPoolExecutor for parallel API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        futures = {
            "elevation": executor.submit(fetch_elevation, lat, lon),
            "weather": executor.submit(fetch_weather, lat, lon),
            "climate": executor.submit(fetch_climate, lat, lon),
            "location": executor.submit(fetch_reverse_geocode, lat, lon),
            "inaturalist": executor.submit(fetch_inaturalist, lat, lon, 5),
            "gbif": executor.submit(fetch_gbif_species, lat, lon, 5),
            "osm_features": executor.submit(fetch_osm_features, lat, lon, 5000),
            "earthquakes": executor.submit(fetch_earthquakes, lat, lon, 100),
            "air_quality": executor.submit(fetch_air_quality, lat, lon)
        }

        # Collect results with progress
        progress_bar = st.progress(0.0)
        completed = 0
        total = len(futures)

        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=30)
            except Exception as e:
                results[key] = {"success": False, "error": str(e)}

            completed += 1
            progress_bar.progress(completed / total)

        progress_bar.empty()

    return results


def display_results(results: Dict, lat: float, lon: float):
    """Display all results in elegant cards."""

    st.markdown("---")

    # ============================================================
    # LOCATION INFO
    # ============================================================
    if results.get('location', {}).get('success'):
        category_header("📍 Location Information", count=1, icon="🌍")

        loc = results['location']

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="glass-card" style="
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(12px);
            ">
                <h3 style="color: #60a5fa; margin-bottom: 1rem;">🗺️ Address</h3>
                <p style="font-size: 1.1rem; color: #e5e7eb; line-height: 1.6;">
                    <strong>{html_module.escape(str(loc.get('display_name', 'N/A')))}</strong>
                </p>
                <div style="margin-top: 1rem; font-size: 0.9rem; color: #cbd5e1;">
                    <p>🏙️ <strong>City:</strong> {html_module.escape(str(loc.get('city', 'N/A')))}</p>
                    <p>🏛️ <strong>State:</strong> {html_module.escape(str(loc.get('state', 'N/A')))}</p>
                    <p>🌐 <strong>Country:</strong> {html_module.escape(str(loc.get('country', 'N/A')))}</p>
                    <p>📮 <strong>Postcode:</strong> {html_module.escape(str(loc.get('postcode', 'N/A')))}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="glass-card" style="
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(12px);
            ">
                <h3 style="color: #10b981; margin-bottom: 1rem;">📐 Coordinates</h3>
                <p style="font-size: 1.5rem; color: #e5e7eb; font-weight: 600;">
                    {lat:.6f}° N<br>{lon:.6f}° E
                </p>
                <div style="margin-top: 1rem; font-size: 0.9rem; color: #cbd5e1;">
                    <p>🏷️ <strong>Place Type:</strong> {html_module.escape(str(loc.get('place_type', 'N/A')))}</p>
                    <p>🆔 <strong>OSM ID:</strong> {html_module.escape(str(loc.get('osm_id', 'N/A')))}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ============================================================
    # PHYSICAL CHARACTERISTICS
    # ============================================================
    category_header("🏔️ Physical Characteristics", count=2, icon="⛰️")

    stats = []

    # Elevation
    if results.get('elevation', {}).get('success'):
        elev = results['elevation']
        stats.append({
            "label": "Elevation",
            "value": f"{elev['elevation_m']:.0f}m",
            "icon": "⛰️",
            "color": "#8b5cf6"
        })
        stats.append({
            "label": "Elevation (ft)",
            "value": f"{elev['elevation_ft']:.0f}ft",
            "icon": "📏",
            "color": "#a855f7"
        })

    # Climate
    if results.get('climate', {}).get('success'):
        climate = results['climate']
        stats.append({
            "label": "Avg Temperature",
            "value": f"{climate['avg_temperature_c']:.1f}°C",
            "icon": "🌡️",
            "color": "#f59e0b"
        })
        stats.append({
            "label": "Annual Precipitation",
            "value": f"{climate['annual_precipitation_mm']:.0f}mm",
            "icon": "🌧️",
            "color": "#06b6d4"
        })

    if stats:
        stats_grid(stats, columns=4)

    # ============================================================
    # CURRENT WEATHER
    # ============================================================
    if results.get('weather', {}).get('success'):
        category_header("☁️ Current Weather", count=1, icon="🌤️")

        weather = results['weather']

        weather_stats = [
            {
                "label": "Temperature",
                "value": f"{weather.get('temperature_c', 'N/A')}°C",
                "icon": "🌡️",
                "color": "#ef4444"
            },
            {
                "label": "Humidity",
                "value": f"{weather.get('humidity', 'N/A')}%",
                "icon": "💧",
                "color": "#06b6d4"
            },
            {
                "label": "Wind Speed",
                "value": f"{weather.get('wind_speed', 'N/A')} km/h",
                "icon": "💨",
                "color": "#94a3b8"
            },
            {
                "label": "Precipitation",
                "value": f"{weather.get('precipitation', 0)} mm",
                "icon": "🌧️",
                "color": "#3b82f6"
            }
        ]

        stats_grid(weather_stats, columns=4)

    # ============================================================
    # BIODIVERSITY
    # ============================================================
    category_header("🦋 Biodiversity & Wildlife", count=2, icon="🌿")

    col1, col2 = st.columns(2)

    # iNaturalist
    with col1:
        if results.get('inaturalist', {}).get('success'):
            inat = results['inaturalist']

            st.markdown(f"""
            <div class="glass-card" style="
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(12px);
            ">
                <h3 style="color: #10b981; margin-bottom: 1rem;">🔬 iNaturalist Observations</h3>
                <p style="font-size: 2rem; color: #e5e7eb; font-weight: 700;">
                    {inat['total_observations']} observations
                </p>
            </div>
            """, unsafe_allow_html=True)

            if inat['species']:
                with st.expander(f"🦎 View {len(inat['species'])} Species", expanded=False):
                    for sp in inat['species'][:15]:
                        st.markdown(f"""
                        - **{sp['name']}** {f"({sp['common_name']})" if sp['common_name'] else ''}
                          *{sp['type']} • {sp['rank']}*
                        """)

            # Taxa distribution
            if inat['taxa_distribution']:
                st.markdown("**Taxa Distribution:**")
                for taxon, count in sorted(inat['taxa_distribution'].items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"- {taxon}: {count}")

    # GBIF
    with col2:
        if results.get('gbif', {}).get('success'):
            gbif = results['gbif']

            st.markdown(f"""
            <div class="glass-card" style="
                background: rgba(139, 92, 246, 0.1);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(12px);
            ">
                <h3 style="color: #a855f7; margin-bottom: 1rem;">🌍 GBIF Records</h3>
                <p style="font-size: 2rem; color: #e5e7eb; font-weight: 700;">
                    {gbif['unique_species']} unique species
                </p>
                <p style="color: #cbd5e1; margin-top: 0.5rem;">
                    {gbif['total_records']} total records
                </p>
            </div>
            """, unsafe_allow_html=True)

            if gbif['kingdoms']:
                st.markdown("**Kingdom Distribution:**")
                for kingdom, count in sorted(gbif['kingdoms'].items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"- {kingdom}: {count}")

    # ============================================================
    # INFRASTRUCTURE & POI
    # ============================================================
    if results.get('osm_features', {}).get('success'):
        category_header("🏗️ Infrastructure & Points of Interest", count=1, icon="🏙️")

        osm = results['osm_features']
        cats = osm['categories']

        # Stats
        infra_stats = [
            {
                "label": "Heliports",
                "value": str(len(cats['heliports'])),
                "icon": "🚁",
                "color": "#ef4444"
            },
            {
                "label": "Hospitals",
                "value": str(len(cats['hospitals'])),
                "icon": "🏥",
                "color": "#10b981"
            },
            {
                "label": "Schools",
                "value": str(len(cats['schools'])),
                "icon": "🏫",
                "color": "#3b82f6"
            },
            {
                "label": "Universities",
                "value": str(len(cats['universities'])),
                "icon": "🎓",
                "color": "#8b5cf6"
            },
            {
                "label": "Tourism Sites",
                "value": str(len(cats['tourism'])),
                "icon": "🗿",
                "color": "#f59e0b"
            },
            {
                "label": "Nearby Cities",
                "value": str(len(cats['cities'])),
                "icon": "🏙️",
                "color": "#06b6d4"
            }
        ]

        stats_grid(infra_stats, columns=3)

        # Detailed lists
        col1, col2, col3 = st.columns(3)

        with col1:
            if cats['heliports']:
                with st.expander(f"🚁 Heliports ({len(cats['heliports'])})"):
                    for h in cats['heliports'][:10]:
                        st.markdown(f"- {h}")

            if cats['hospitals']:
                with st.expander(f"🏥 Hospitals ({len(cats['hospitals'])})"):
                    for h in cats['hospitals'][:10]:
                        st.markdown(f"- {h}")

        with col2:
            if cats['cities']:
                with st.expander(f"🏙️ Cities ({len(cats['cities'])})"):
                    for c in cats['cities'][:10]:
                        st.markdown(f"- {c}")

            if cats['peaks']:
                with st.expander(f"⛰️ Peaks ({len(cats['peaks'])})"):
                    for p in cats['peaks'][:10]:
                        st.markdown(f"- {p}")

        with col3:
            if cats['tourism']:
                with st.expander(f"🗿 Tourism ({len(cats['tourism'])})"):
                    for t in cats['tourism'][:10]:
                        st.markdown(f"- {t}")

            if cats['landuse']:
                with st.expander(f"🌍 Land Use Types"):
                    for lu, count in sorted(cats['landuse'].items(), key=lambda x: x[1], reverse=True):
                        st.markdown(f"- {lu}: {count}")

    # ============================================================
    # SEISMIC ACTIVITY
    # ============================================================
    if results.get('earthquakes', {}).get('success'):
        category_header("🌋 Seismic Activity", count=1, icon="⚡")

        quakes = results['earthquakes']

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div class="glass-card" style="
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(12px);
            ">
                <h3 style="color: #ef4444; margin-bottom: 1rem;">🌋 Earthquakes (100km)</h3>
                <p style="font-size: 2rem; color: #e5e7eb; font-weight: 700;">
                    {quakes['total_earthquakes']}
                </p>
                <p style="color: #cbd5e1; margin-top: 0.5rem;">
                    Max magnitude: <strong>{quakes['max_magnitude']}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if quakes['recent_quakes']:
                with st.expander(f"📋 Recent Earthquakes ({len(quakes['recent_quakes'])})", expanded=True):
                    for q in quakes['recent_quakes'][:5]:
                        time_str = datetime.fromtimestamp(q['time']/1000).strftime('%Y-%m-%d %H:%M')
                        st.markdown(f"""
                        - **M{q['magnitude']}** - {q['place']}
                          *{time_str} • Depth: {q['depth']}km*
                        """)

    # ============================================================
    # AIR QUALITY
    # ============================================================
    if results.get('air_quality', {}).get('success'):
        category_header("💨 Air Quality", count=1, icon="🌬️")

        aq = results['air_quality']

        st.markdown(f"""
        <div class="glass-card" style="
            background: rgba(6, 182, 212, 0.1);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
        ">
            <h3 style="color: #06b6d4; margin-bottom: 1rem;">🌬️ {aq['station_name']}</h3>
            <p style="color: #cbd5e1; margin-bottom: 1rem;">
                Last updated: {aq['last_updated']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        measurements = aq.get('measurements', {})
        if measurements:
            aq_stats = []
            for param, data in measurements.items():
                aq_stats.append({
                    "label": param.upper(),
                    "value": f"{data['value']} {data['unit']}",
                    "icon": "💨",
                    "color": "#06b6d4"
                })

            if aq_stats:
                stats_grid(aq_stats, columns=4)


def render_location_intelligence_tab():
    """Main render function for Location Intelligence module."""

    # Hero section
    hero_section(
        title="Location Intelligence",
        subtitle="Click anywhere on the map to get comprehensive intelligence from 20+ data sources",
        features=["Elevation", "Weather & Climate", "Biodiversity", "Infrastructure", "Seismic Activity", "Air Quality"]
    )

    st.markdown("---")

    # Instructions
    info_card(
        title="How to Use",
        content="""
        1. Click anywhere on the map below to select a location
        2. The system will query 20+ APIs in parallel
        3. View comprehensive intelligence about that point
        """,
        icon="ℹ️",
        color="#3b82f6"
    )

    # Map
    st.markdown("### 🗺️ Select Location")

    # Initialize session state for coordinates
    if 'loc_intel_lat' not in st.session_state:
        st.session_state.loc_intel_lat = 40.7128
        st.session_state.loc_intel_lon = -74.0060

    # Create map
    m = folium.Map(
        location=[st.session_state.loc_intel_lat, st.session_state.loc_intel_lon],
        zoom_start=10,
        tiles="CartoDB dark_matter"
    )

    # Add marker for selected point
    folium.Marker(
        [st.session_state.loc_intel_lat, st.session_state.loc_intel_lon],
        popup="Selected Location",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

    # Display map and capture clicks
    map_data = st_folium(m, width=None, height=500, key="loc_intel_map")

    # Check for click
    if map_data and map_data.get('last_clicked'):
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lon = map_data['last_clicked']['lng']

        # Update session state
        st.session_state.loc_intel_lat = clicked_lat
        st.session_state.loc_intel_lon = clicked_lon

        st.rerun()

    st.markdown("---")

    # Manual coordinate input
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        manual_lat = st.number_input(
            "Latitude",
            value=st.session_state.loc_intel_lat,
            format="%.6f",
            key="manual_lat"
        )

    with col2:
        manual_lon = st.number_input(
            "Longitude",
            value=st.session_state.loc_intel_lon,
            format="%.6f",
            key="manual_lon"
        )

    with col3:
        if st.button("🔍 Analyze", type="primary", use_container_width=True):
            st.session_state.loc_intel_lat = manual_lat
            st.session_state.loc_intel_lon = manual_lon
            st.rerun()

    # Analyze button
    if st.button("🚀 Analyze Location", type="primary", use_container_width=True, key="analyze_main"):
        with st.spinner("🔄 Fetching data from 20+ sources..."):
            results = analyze_location(
                st.session_state.loc_intel_lat,
                st.session_state.loc_intel_lon
            )

            if results:
                success_banner(
                    f"✅ Analysis complete! Retrieved data from {sum(1 for r in results.values() if r.get('success'))} sources",
                    icon="🎉"
                )

                # Display results
                display_results(
                    results,
                    st.session_state.loc_intel_lat,
                    st.session_state.loc_intel_lon
                )
