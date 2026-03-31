"""
Global Real-Time Intelligence Dashboard for TerraScout AI.
Aggregates live data from multiple free APIs to display real-time worldwide
events: earthquakes, wildfires, aircraft, disasters, ISS position, and solar activity.
"""

import io
import json
import html as html_module
import xml.etree.ElementTree as ET
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
from datetime import datetime, timedelta, timezone

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

USGS_FEED_BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
FIRMS_CSV_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"
FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/FIRMS_OPEN/VIIRS_SNPP_NRT/-180,-90,180,90/1"
OPENSKY_API = "https://opensky-network.org/api/states/all"
GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"
ISS_API = "http://api.open-notify.org/iss-now.json"
SWPC_KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
SWPC_ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"

# Earthquake time-frame mapping for USGS summary feeds
EARTHQUAKE_FEEDS = {
    "1h": "all_hour",
    "24h": "all_day",
    "7d": "all_week",
    "30d": "all_month",
}

# Earthquake magnitude color scale
MAG_COLORS = {
    "micro": "#6b7280",    # < 2.0  gray
    "minor": "#eab308",    # 2.0-4.0  yellow
    "moderate": "#f97316",  # 4.0-6.0  orange
    "major": "#ef4444",    # 6.0+  red
}

# Fire brightness color scale
FIRE_COLORS = {
    "low": "#f97316",      # orange
    "high": "#ef4444",     # red
}

# Analysis mode definitions
ANALYSIS_MODES = {
    "All Feeds Active": "Display all active data layers simultaneously on the global map",
    "Seismic Activity": "Earthquakes only, color-coded by magnitude",
    "Wildfire Monitor": "Active fire hotspots with brightness coloring",
    "Air Traffic": "Live aircraft positions (sampled to avoid overload)",
    "Disaster Alerts": "GDACS global disaster alerts only",
    "Space Weather": "ISS position and solar activity indicators",
    "Crisis Dashboard": "Earthquakes + fires + disasters combined for crisis overview",
}


# ══════════════════════════════════════════════════════════════════════════════
# COLOR / SIZE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _earthquake_color(mag: float) -> str:
    """Return color based on earthquake magnitude."""
    if mag < 2.0:
        return MAG_COLORS["micro"]
    elif mag < 4.0:
        return MAG_COLORS["minor"]
    elif mag < 6.0:
        return MAG_COLORS["moderate"]
    return MAG_COLORS["major"]


def _earthquake_radius(mag: float) -> float:
    """Return circle radius based on earthquake magnitude."""
    if mag < 2.0:
        return 3
    elif mag < 4.0:
        return 5
    elif mag < 6.0:
        return 8
    return 12


def _fire_color(brightness: float) -> str:
    """Return color based on fire brightness/FRP."""
    if brightness < 350:
        return FIRE_COLORS["low"]
    return FIRE_COLORS["high"]


def _fire_radius(brightness: float) -> float:
    """Return circle radius based on fire brightness."""
    if brightness < 300:
        return 3
    elif brightness < 400:
        return 5
    return 7


def _kp_color(kp: float) -> str:
    """Return color for Kp index (space weather)."""
    if kp < 4:
        return "#10b981"   # green - quiet
    elif kp < 6:
        return "#f59e0b"   # amber - unsettled/active
    elif kp < 8:
        return "#f97316"   # orange - storm
    return "#ef4444"       # red - severe storm


def _kp_label(kp: float) -> str:
    """Human-readable Kp index label."""
    if kp < 2:
        return "Quiet"
    elif kp < 4:
        return "Unsettled"
    elif kp < 6:
        return "Active/Minor Storm"
    elif kp < 8:
        return "Geomagnetic Storm"
    return "Severe Storm"


# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING FUNCTIONS (cached)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120)
def fetch_earthquakes(timeframe: str = "24h") -> dict:
    """
    Fetch earthquake data from USGS GeoJSON summary feed.
    timeframe: '1h', '24h', '7d', '30d'
    Returns GeoJSON FeatureCollection dict.
    """
    feed_name = EARTHQUAKE_FEEDS.get(timeframe, "all_day")
    url = f"{USGS_FEED_BASE}/{feed_name}.geojson"
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.Timeout:
        return {"type": "FeatureCollection", "features": [], "error": "USGS request timed out"}
    except requests.exceptions.ConnectionError:
        return {"type": "FeatureCollection", "features": [], "error": "Cannot reach USGS server"}
    except Exception as e:
        return {"type": "FeatureCollection", "features": [], "error": str(e)}


@st.cache_data(ttl=300)
def fetch_active_fires() -> pd.DataFrame:
    """
    Fetch active fire detections from NASA FIRMS.
    Returns DataFrame with latitude, longitude, brightness columns.
    """
    # Try VIIRS NRT first (higher resolution)
    for url in [FIRMS_AREA_URL, FIRMS_CSV_URL]:
        try:
            resp = requests.get(
                url, timeout=30,
                headers={"User-Agent": "TerraScoutAI/1.0"}
            )
            if resp.status_code == 200 and len(resp.text) > 200:
                df = pd.read_csv(io.StringIO(resp.text))
                if len(df) > 0:
                    # Normalize column names to lowercase
                    df.columns = [c.lower().strip() for c in df.columns]
                    return df
        except Exception:
            continue

    return pd.DataFrame()


@st.cache_data(ttl=90)
def fetch_aircraft() -> list:
    """
    Fetch live aircraft positions from OpenSky Network.
    Returns list of state vectors. Anonymous access (no API key).
    Each state: [icao24, callsign, origin_country, time_position, last_contact,
                 longitude, latitude, baro_altitude, on_ground, velocity,
                 true_track, vertical_rate, sensors, geo_altitude,
                 squawk, spi, position_source]
    """
    try:
        resp = requests.get(OPENSKY_API, timeout=20, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        data = resp.json()
        states = data.get("states", [])
        return states if states else []
    except requests.exceptions.Timeout:
        return []
    except requests.exceptions.ConnectionError:
        return []
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_disaster_alerts() -> list:
    """
    Fetch global disaster alerts from GDACS RSS feed.
    Returns list of dicts with title, description, lat, lon, severity, etc.
    """
    alerts = []
    try:
        resp = requests.get(GDACS_RSS, timeout=15, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        # GDACS RSS uses namespaces
        ns = {
            "gdacs": "http://www.gdacs.org",
            "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        channel = root.find("channel")
        if channel is None:
            return alerts

        for item in channel.findall("item"):
            alert = {}
            title_el = item.find("title")
            alert["title"] = title_el.text if title_el is not None and title_el.text else "Unknown Event"
            desc_el = item.find("description")
            alert["description"] = desc_el.text if desc_el is not None and desc_el.text else ""
            link_el = item.find("link")
            alert["link"] = link_el.text if link_el is not None and link_el.text else ""
            pub_el = item.find("pubDate")
            alert["pubDate"] = pub_el.text if pub_el is not None and pub_el.text else ""

            # Try to extract coordinates
            lat_el = item.find("geo:lat", ns)
            lon_el = item.find("geo:long", ns)
            if lat_el is not None and lon_el is not None:
                try:
                    alert["lat"] = float(lat_el.text)
                    alert["lon"] = float(lon_el.text)
                except (ValueError, TypeError):
                    alert["lat"] = None
                    alert["lon"] = None
            else:
                # Fallback: try gdacs:geo namespace
                point = item.find(".//gdacs:geo", ns)
                if point is not None and point.text:
                    parts = point.text.strip().split()
                    if len(parts) >= 2:
                        try:
                            alert["lat"] = float(parts[0])
                            alert["lon"] = float(parts[1])
                        except ValueError:
                            alert["lat"] = None
                            alert["lon"] = None
                    else:
                        alert["lat"] = None
                        alert["lon"] = None
                else:
                    alert["lat"] = None
                    alert["lon"] = None

            # Severity
            severity_el = item.find("gdacs:severity", ns)
            alert["severity"] = severity_el.text if severity_el is not None and severity_el.text else "Unknown"

            # Event type
            event_el = item.find("gdacs:eventtype", ns)
            alert["eventtype"] = event_el.text if event_el is not None and event_el.text else "Unknown"

            # Alert level
            alert_el = item.find("gdacs:alertlevel", ns)
            alert["alertlevel"] = alert_el.text if alert_el is not None and alert_el.text else "Green"

            alerts.append(alert)

    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass
    except ET.ParseError:
        pass
    except Exception:
        pass

    return alerts


@st.cache_data(ttl=30)
def fetch_iss_position() -> dict:
    """
    Fetch current ISS position.
    Returns dict with lat, lon, timestamp.
    """
    try:
        resp = requests.get(ISS_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("message") == "success":
            pos = data.get("iss_position", {})
            return {
                "lat": float(pos.get("latitude", 0)),
                "lon": float(pos.get("longitude", 0)),
                "timestamp": data.get("timestamp", 0),
            }
    except Exception:
        pass
    return {"lat": None, "lon": None, "timestamp": None}


@st.cache_data(ttl=120)
def fetch_space_weather() -> dict:
    """
    Fetch space weather data from NOAA SWPC.
    Returns dict with latest Kp index, activity level, and recent history.
    """
    result = {"kp": None, "level": "Unknown", "history": [], "alerts": []}

    # Fetch Kp index
    try:
        resp = requests.get(SWPC_KP_URL, timeout=15, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        kp_data = resp.json()
        if kp_data and len(kp_data) > 0:
            # Get the most recent entry
            latest = kp_data[-1]
            kp_val = float(latest.get("kp_index", 0))
            result["kp"] = kp_val
            result["level"] = _kp_label(kp_val)
            # Last 24 entries for sparkline
            result["history"] = [
                {"time": entry.get("time_tag", ""), "kp": float(entry.get("kp_index", 0))}
                for entry in kp_data[-24:]
            ]
    except Exception:
        pass

    # Fetch SWPC alerts
    try:
        resp = requests.get(SWPC_ALERTS_URL, timeout=10, headers={"User-Agent": "TerraScoutAI/1.0"})
        resp.raise_for_status()
        alerts_data = resp.json()
        if alerts_data and isinstance(alerts_data, list):
            result["alerts"] = alerts_data[:10]  # Last 10 alerts
    except Exception:
        pass

    return result


# ══════════════════════════════════════════════════════════════════════════════
# MAP BUILDING HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _add_earthquakes_to_map(m: folium.Map, features: list, use_heatmap: bool = False):
    """Add earthquake markers or heatmap layer to folium map."""
    if not features:
        return

    if use_heatmap:
        heat_data = []
        for feat in features:
            coords = feat["geometry"]["coordinates"]
            mag = feat["properties"].get("mag", 1) or 1
            heat_data.append([coords[1], coords[0], mag])
        if heat_data:
            HeatMap(
                heat_data,
                name="Earthquakes Heatmap",
                radius=15,
                blur=10,
                max_zoom=8,
                gradient={0.2: "#eab308", 0.5: "#f97316", 0.8: "#ef4444", 1.0: "#991b1b"},
            ).add_to(m)
    else:
        eq_group = folium.FeatureGroup(name="Earthquakes")
        for feat in features[:2000]:
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            mag = props.get("mag", 0) or 0
            place = html_module.escape(str(props.get("place", "Unknown")))
            time_ms = props.get("time", 0)
            depth = coords[2] if len(coords) > 2 else 0

            eq_time = ""
            if time_ms:
                try:
                    eq_time = datetime.fromtimestamp(
                        time_ms / 1000, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M UTC")
                except (OSError, ValueError):
                    eq_time = "Unknown"

            popup_text = (
                f"<div style='min-width:160px;'>"
                f"<b>M{mag:.1f}</b> &mdash; {place}<br/>"
                f"<small>Depth: {depth:.1f} km</small><br/>"
                f"<small>{html_module.escape(eq_time)}</small>"
                f"</div>"
            )

            folium.CircleMarker(
                location=[coords[1], coords[0]],
                radius=_earthquake_radius(mag),
                color=_earthquake_color(mag),
                fill=True,
                fill_color=_earthquake_color(mag),
                fill_opacity=0.6,
                weight=1,
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"M{mag:.1f} - {place}",
            ).add_to(eq_group)
        eq_group.add_to(m)


def _add_fires_to_map(m: folium.Map, df: pd.DataFrame, use_heatmap: bool = False,
                       max_points: int = 3000):
    """Add fire markers or heatmap layer to folium map."""
    if df.empty:
        return

    # Identify coordinate columns
    lat_col = None
    lon_col = None
    bright_col = None
    for col in df.columns:
        cl = col.lower()
        if "lat" in cl and lat_col is None:
            lat_col = col
        if ("lon" in cl or "lng" in cl) and lon_col is None:
            lon_col = col
        if "bright" in cl and bright_col is None:
            bright_col = col
        if "frp" in cl and bright_col is None:
            bright_col = col

    if lat_col is None or lon_col is None:
        return

    df_valid = df.dropna(subset=[lat_col, lon_col]).head(max_points)

    if use_heatmap:
        heat_data = []
        for _, row in df_valid.iterrows():
            bright = float(row[bright_col]) if bright_col and pd.notna(row.get(bright_col)) else 300
            heat_data.append([float(row[lat_col]), float(row[lon_col]), bright / 500.0])
        if heat_data:
            HeatMap(
                heat_data,
                name="Fires Heatmap",
                radius=12,
                blur=8,
                max_zoom=8,
                gradient={0.3: "#f59e0b", 0.6: "#f97316", 0.9: "#ef4444", 1.0: "#991b1b"},
            ).add_to(m)
    else:
        fire_group = folium.FeatureGroup(name="Active Fires")
        for _, row in df_valid.iterrows():
            lat = float(row[lat_col])
            lon = float(row[lon_col])
            bright = float(row[bright_col]) if bright_col and pd.notna(row.get(bright_col)) else 300

            # Build popup with available info
            popup_parts = [f"<div style='min-width:140px;'><b>Fire Detection</b><br/>"]
            popup_parts.append(f"<small>Lat: {lat:.4f}, Lon: {lon:.4f}</small><br/>")
            if bright_col and pd.notna(row.get(bright_col)):
                popup_parts.append(f"<small>Brightness: {bright:.1f}</small><br/>")
            conf_col = None
            for c in df.columns:
                if "conf" in c.lower():
                    conf_col = c
                    break
            if conf_col and pd.notna(row.get(conf_col)):
                popup_parts.append(f"<small>Confidence: {html_module.escape(str(row[conf_col]))}</small><br/>")
            date_col = None
            for c in df.columns:
                if "acq_date" in c.lower() or "date" in c.lower():
                    date_col = c
                    break
            if date_col and pd.notna(row.get(date_col)):
                popup_parts.append(f"<small>Date: {html_module.escape(str(row[date_col]))}</small>")
            popup_parts.append("</div>")

            folium.CircleMarker(
                location=[lat, lon],
                radius=_fire_radius(bright),
                color=_fire_color(bright),
                fill=True,
                fill_color=_fire_color(bright),
                fill_opacity=0.5,
                weight=1,
                popup=folium.Popup("".join(popup_parts), max_width=220),
            ).add_to(fire_group)
        fire_group.add_to(m)


def _add_aircraft_to_map(m: folium.Map, states: list, max_points: int = 1500):
    """Add aircraft position markers to folium map."""
    if not states:
        return

    ac_group = folium.FeatureGroup(name="Aircraft")
    count = 0
    for state in states:
        if count >= max_points:
            break
        # state vector indices: 5=longitude, 6=latitude
        lon = state[5]
        lat = state[6]
        if lat is None or lon is None:
            continue

        callsign = html_module.escape(str(state[1]).strip()) if state[1] else "N/A"
        origin = html_module.escape(str(state[2])) if state[2] else "Unknown"
        altitude = state[7]  # baro_altitude in meters
        velocity = state[9]  # m/s
        on_ground = state[8]

        alt_str = f"{altitude:.0f}m" if altitude is not None else "N/A"
        vel_str = f"{velocity:.0f} m/s" if velocity is not None else "N/A"
        status = "On Ground" if on_ground else "Airborne"

        popup_text = (
            f"<div style='min-width:150px;'>"
            f"<b>{callsign}</b><br/>"
            f"<small>Origin: {origin}</small><br/>"
            f"<small>Alt: {alt_str}</small><br/>"
            f"<small>Speed: {vel_str}</small><br/>"
            f"<small>Status: {status}</small>"
            f"</div>"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=2,
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_text, max_width=200),
        ).add_to(ac_group)
        count += 1

    ac_group.add_to(m)


def _add_disasters_to_map(m: folium.Map, alerts: list):
    """Add GDACS disaster alert markers to folium map."""
    if not alerts:
        return

    disaster_group = folium.FeatureGroup(name="Disaster Alerts")
    for alert in alerts:
        lat = alert.get("lat")
        lon = alert.get("lon")
        if lat is None or lon is None:
            continue

        title = html_module.escape(alert.get("title", "Unknown"))
        desc = html_module.escape(alert.get("description", "")[:200])
        severity = html_module.escape(alert.get("severity", "Unknown"))
        event_type = html_module.escape(alert.get("eventtype", "Unknown"))
        alert_level = alert.get("alertlevel", "Green").lower()

        # Color based on alert level
        if "red" in alert_level:
            color = "#ef4444"
            icon_color = "red"
        elif "orange" in alert_level:
            color = "#f97316"
            icon_color = "orange"
        else:
            color = "#10b981"
            icon_color = "green"

        popup_text = (
            f"<div style='min-width:180px; max-width:280px;'>"
            f"<b>{title}</b><br/>"
            f"<small>Type: {event_type}</small><br/>"
            f"<small>Severity: {severity}</small><br/>"
            f"<small>Alert: {html_module.escape(alert.get('alertlevel', 'Green'))}</small><br/>"
            f"<small>{desc}</small>"
            f"</div>"
        )

        # Use pulsing marker effect via larger semi-transparent circle + inner circle
        folium.CircleMarker(
            location=[lat, lon],
            radius=18,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.15,
            weight=2,
        ).add_to(disaster_group)

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=title,
        ).add_to(disaster_group)

    disaster_group.add_to(m)


def _add_iss_to_map(m: folium.Map, iss_data: dict):
    """Add ISS position marker to folium map."""
    lat = iss_data.get("lat")
    lon = iss_data.get("lon")
    if lat is None or lon is None:
        return

    ts = iss_data.get("timestamp", 0)
    time_str = ""
    if ts:
        try:
            time_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except (OSError, ValueError):
            time_str = "Unknown"

    popup_text = (
        f"<div style='min-width:160px;'>"
        f"<b>International Space Station</b><br/>"
        f"<small>Lat: {lat:.4f}, Lon: {lon:.4f}</small><br/>"
        f"<small>Updated: {html_module.escape(time_str)}</small>"
        f"</div>"
    )

    # Outer glow
    folium.CircleMarker(
        location=[lat, lon],
        radius=20,
        color="#10b981",
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.15,
        weight=2,
    ).add_to(m)

    # Inner marker
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color="#10b981",
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.9,
        weight=2,
        popup=folium.Popup(popup_text, max_width=250),
        tooltip="ISS - International Space Station",
    ).add_to(m)


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _compute_earthquake_stats(features: list) -> dict:
    """Compute summary statistics from earthquake GeoJSON features."""
    if not features:
        return {"count": 0, "max_mag": 0, "avg_mag": 0, "avg_depth": 0}

    mags = [f["properties"].get("mag", 0) or 0 for f in features]
    depths = []
    for f in features:
        coords = f["geometry"]["coordinates"]
        if len(coords) > 2:
            depths.append(coords[2])

    return {
        "count": len(features),
        "max_mag": max(mags) if mags else 0,
        "avg_mag": sum(mags) / len(mags) if mags else 0,
        "avg_depth": sum(depths) / len(depths) if depths else 0,
    }


def _compute_fire_stats(df: pd.DataFrame) -> dict:
    """Compute summary statistics from fire DataFrame."""
    if df.empty:
        return {"count": 0, "avg_brightness": 0}

    bright_col = None
    for col in df.columns:
        if "bright" in col.lower() or "frp" in col.lower():
            bright_col = col
            break

    avg_b = 0
    if bright_col:
        try:
            avg_b = df[bright_col].mean()
        except Exception:
            avg_b = 0

    return {
        "count": len(df),
        "avg_brightness": avg_b,
    }


def _build_earthquake_dataframe(features: list) -> pd.DataFrame:
    """Convert earthquake GeoJSON features to a pandas DataFrame."""
    if not features:
        return pd.DataFrame()

    rows = []
    for feat in features[:2000]:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        time_ms = props.get("time", 0)
        time_str = ""
        if time_ms:
            try:
                time_str = datetime.fromtimestamp(
                    time_ms / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M UTC")
            except (OSError, ValueError):
                time_str = ""
        rows.append({
            "Time": time_str,
            "Magnitude": props.get("mag", 0),
            "Place": props.get("place", "Unknown"),
            "Depth (km)": coords[2] if len(coords) > 2 else 0,
            "Latitude": coords[1],
            "Longitude": coords[0],
            "Type": props.get("type", ""),
            "Status": props.get("status", ""),
        })
    return pd.DataFrame(rows)


def _build_fire_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize fire DataFrame columns for display."""
    if df.empty:
        return pd.DataFrame()

    display_cols = {}
    for col in df.columns:
        cl = col.lower()
        if "lat" in cl:
            display_cols[col] = "Latitude"
        elif "lon" in cl or "lng" in cl:
            display_cols[col] = "Longitude"
        elif "bright" in cl:
            display_cols[col] = "Brightness"
        elif "frp" in cl:
            display_cols[col] = "FRP"
        elif "conf" in cl:
            display_cols[col] = "Confidence"
        elif "acq_date" in cl or "date" in cl:
            display_cols[col] = "Date"
        elif "acq_time" in cl:
            display_cols[col] = "Time"

    if display_cols:
        subset = df[list(display_cols.keys())].copy()
        subset.rename(columns=display_cols, inplace=True)
        return subset.head(2000)
    return df.head(2000)


def _build_aircraft_dataframe(states: list) -> pd.DataFrame:
    """Convert OpenSky state vectors to a DataFrame."""
    if not states:
        return pd.DataFrame()

    rows = []
    for s in states[:3000]:
        if s[6] is None or s[5] is None:
            continue
        rows.append({
            "ICAO24": s[0],
            "Callsign": str(s[1]).strip() if s[1] else "N/A",
            "Origin": s[2] if s[2] else "Unknown",
            "Latitude": s[6],
            "Longitude": s[5],
            "Altitude (m)": s[7] if s[7] is not None else 0,
            "Velocity (m/s)": s[9] if s[9] is not None else 0,
            "On Ground": s[8],
        })
    return pd.DataFrame(rows)


def _build_disaster_dataframe(alerts: list) -> pd.DataFrame:
    """Convert GDACS alerts to a DataFrame."""
    if not alerts:
        return pd.DataFrame()

    rows = []
    for a in alerts:
        rows.append({
            "Title": a.get("title", ""),
            "Type": a.get("eventtype", ""),
            "Severity": a.get("severity", ""),
            "Alert Level": a.get("alertlevel", ""),
            "Latitude": a.get("lat"),
            "Longitude": a.get("lon"),
            "Date": a.get("pubDate", ""),
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def render_global_realtime_tab():
    """Main render function for the Global Real-Time Intelligence Dashboard."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Global Real-Time Intelligence</h4>
        <p>Live worldwide monitoring &mdash; earthquakes, fires, aircraft, disasters, ISS, weather &amp; solar activity</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Controls
    # ══════════════════════════════════════════
    st.markdown("#### Dashboard Controls")

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

    with ctrl_col1:
        analysis_mode = st.selectbox(
            "Analysis Mode",
            list(ANALYSIS_MODES.keys()),
            key="grt_mode",
            help="Choose which data layers to display",
        )
        st.caption(ANALYSIS_MODES[analysis_mode])

    with ctrl_col2:
        time_range = st.selectbox(
            "Time Range",
            ["1h", "6h", "24h", "7d", "30d"],
            index=2,
            key="grt_timerange",
            help="Time window for earthquake data (fire data is always last 24h)",
        )

    with ctrl_col3:
        use_heatmap = st.toggle("Heatmap Mode", value=False, key="grt_heatmap",
                                help="Toggle between individual markers and heatmap visualization")
        auto_refresh = st.toggle("Auto-Refresh (60s)", value=False, key="grt_autorefresh",
                                 help="Automatically refresh data every 60 seconds")

    # Layer toggles
    st.markdown("##### Data Layers")
    layer_cols = st.columns(7)
    default_layers = {
        "All Feeds Active": [True, True, True, True, True, True],
        "Seismic Activity": [True, False, False, False, False, False],
        "Wildfire Monitor": [False, True, False, False, False, False],
        "Air Traffic": [False, False, True, False, False, False],
        "Disaster Alerts": [False, False, False, True, False, False],
        "Space Weather": [False, False, False, False, True, True],
        "Crisis Dashboard": [True, True, False, True, False, False],
    }

    defaults = default_layers.get(analysis_mode, [True] * 6)

    with layer_cols[0]:
        show_earthquakes = st.checkbox("Earthquakes", value=defaults[0], key="grt_eq")
    with layer_cols[1]:
        show_fires = st.checkbox("Fires", value=defaults[1], key="grt_fire")
    with layer_cols[2]:
        show_aircraft = st.checkbox("Aircraft", value=defaults[2], key="grt_air")
    with layer_cols[3]:
        show_disasters = st.checkbox("Disasters", value=defaults[3], key="grt_dis")
    with layer_cols[4]:
        show_iss = st.checkbox("ISS", value=defaults[4], key="grt_iss")
    with layer_cols[5]:
        show_solar = st.checkbox("Solar", value=defaults[5], key="grt_solar")
    with layer_cols[6]:
        if st.button("Refresh Now", key="grt_refresh", width="stretch"):
            # Clear cached data to force refresh
            fetch_earthquakes.clear()
            fetch_active_fires.clear()
            fetch_aircraft.clear()
            fetch_disaster_alerts.clear()
            fetch_iss_position.clear()
            fetch_space_weather.clear()
            st.rerun()

    # ══════════════════════════════════════════
    # SECTION 2: Fetch Data
    # ══════════════════════════════════════════
    st.markdown("---")

    # Map earthquake time_range to USGS feed timeframe
    eq_timeframe = time_range
    if time_range == "6h":
        eq_timeframe = "24h"  # USGS doesn't have a 6h feed, filter client-side

    # Fetch data for enabled layers
    eq_data = None
    fire_df = pd.DataFrame()
    aircraft_states = []
    disaster_alerts = []
    iss_data = {"lat": None, "lon": None, "timestamp": None}
    space_data = {"kp": None, "level": "Unknown", "history": [], "alerts": []}

    with st.spinner("Fetching live global data..."):
        if show_earthquakes:
            eq_data = fetch_earthquakes(eq_timeframe)
            # Client-side filter for 6h
            if time_range == "6h" and eq_data and eq_data.get("features"):
                cutoff = (datetime.now(timezone.utc) - timedelta(hours=6)).timestamp() * 1000
                eq_data["features"] = [
                    f for f in eq_data["features"]
                    if f["properties"].get("time", 0) >= cutoff
                ]

        if show_fires:
            fire_df = fetch_active_fires()

        if show_aircraft:
            aircraft_states = fetch_aircraft()

        if show_disasters:
            disaster_alerts = fetch_disaster_alerts()

        if show_iss:
            iss_data = fetch_iss_position()

        if show_solar:
            space_data = fetch_space_weather()

    # ══════════════════════════════════════════
    # SECTION 3: Summary Statistics Dashboard
    # ══════════════════════════════════════════
    st.markdown("#### Live Intelligence Summary")

    eq_features = eq_data.get("features", []) if eq_data else []
    eq_stats = _compute_earthquake_stats(eq_features)
    fire_stats = _compute_fire_stats(fire_df)

    stat_cols = st.columns(6)
    with stat_cols[0]:
        st.metric(
            "Earthquakes",
            f"{eq_stats['count']:,}" if show_earthquakes else "Off",
            delta=f"M{eq_stats['max_mag']:.1f} max" if eq_stats["count"] > 0 else None,
        )
    with stat_cols[1]:
        st.metric(
            "Active Fires",
            f"{fire_stats['count']:,}" if show_fires else "Off",
            delta=f"Avg {fire_stats['avg_brightness']:.0f} bright" if fire_stats["count"] > 0 else None,
        )
    with stat_cols[2]:
        ac_count = len([s for s in aircraft_states if s[6] is not None]) if aircraft_states else 0
        st.metric(
            "Aircraft Tracked",
            f"{ac_count:,}" if show_aircraft else "Off",
        )
    with stat_cols[3]:
        st.metric(
            "Disaster Alerts",
            f"{len(disaster_alerts)}" if show_disasters else "Off",
        )
    with stat_cols[4]:
        iss_lat = iss_data.get("lat")
        iss_lon = iss_data.get("lon")
        if show_iss and iss_lat is not None:
            st.metric("ISS Position", f"{iss_lat:.2f}, {iss_lon:.2f}")
        else:
            st.metric("ISS Position", "Off" if not show_iss else "N/A")
    with stat_cols[5]:
        kp = space_data.get("kp")
        if show_solar and kp is not None:
            st.metric("Solar Kp Index", f"{kp:.1f}", delta=space_data.get("level", ""))
        else:
            st.metric("Solar Kp Index", "Off" if not show_solar else "N/A")

    # Show errors if any
    if eq_data and eq_data.get("error"):
        st.warning(f"Earthquake data: {eq_data['error']}")
    if show_fires and fire_df.empty:
        st.info("No active fire data retrieved. NASA FIRMS may be temporarily unavailable.")
    if show_aircraft and not aircraft_states:
        st.info("No aircraft data retrieved. OpenSky Network may be temporarily unavailable or rate-limited.")

    # ══════════════════════════════════════════
    # SECTION 4: Global Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Global Intelligence Map")

    # Color legend
    legend_parts = []
    if show_earthquakes:
        legend_parts.append(
            '<span style="color:#6b7280;font-size:0.8rem;">&#9679; M&lt;2</span>'
            '<span style="color:#eab308;font-size:0.8rem;">&#9679; M2-4</span>'
            '<span style="color:#f97316;font-size:0.8rem;">&#9679; M4-6</span>'
            '<span style="color:#ef4444;font-size:0.8rem;">&#9679; M6+</span>'
        )
    if show_fires:
        legend_parts.append(
            '<span style="color:#f97316;font-size:0.8rem;">&#9679; Fire (low)</span>'
            '<span style="color:#ef4444;font-size:0.8rem;">&#9679; Fire (high)</span>'
        )
    if show_aircraft:
        legend_parts.append(
            '<span style="color:#06b6d4;font-size:0.8rem;">&#9679; Aircraft</span>'
        )
    if show_disasters:
        legend_parts.append(
            '<span style="color:#ef4444;font-size:0.8rem;">&#11044; Disaster</span>'
        )
    if show_iss:
        legend_parts.append(
            '<span style="color:#10b981;font-size:0.8rem;">&#11044; ISS</span>'
        )

    if legend_parts:
        st.markdown(
            '<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem;">'
            + " ".join(legend_parts) + '</div>',
            unsafe_allow_html=True,
        )

    # Build folium map
    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles=None,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Base",
    ).add_to(m)

    # Add data layers
    if show_earthquakes and eq_features:
        _add_earthquakes_to_map(m, eq_features, use_heatmap=use_heatmap)

    if show_fires and not fire_df.empty:
        _add_fires_to_map(m, fire_df, use_heatmap=use_heatmap)

    if show_aircraft and aircraft_states:
        _add_aircraft_to_map(m, aircraft_states)

    if show_disasters and disaster_alerts:
        _add_disasters_to_map(m, disaster_alerts)

    if show_iss:
        _add_iss_to_map(m, iss_data)

    # Add layer control if multiple layers
    active_count = sum([show_earthquakes, show_fires, show_aircraft, show_disasters])
    if active_count > 1:
        folium.LayerControl(collapsed=False).add_to(m)

    # Render map
    map_html = m._repr_html_()
    st_html(map_html, height=600)

    # ══════════════════════════════════════════
    # SECTION 5: Detailed Data Tables & Downloads
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Detailed Data")

    # Create expandable sections for each data source
    if show_earthquakes and eq_features:
        with st.expander(f"Earthquake Data ({eq_stats['count']:,} events)", expanded=False):
            eq_df = _build_earthquake_dataframe(eq_features)
            if not eq_df.empty:
                # Top events
                st.markdown("##### Strongest Events")
                top_eq = eq_df.nlargest(10, "Magnitude")
                st.dataframe(top_eq, use_container_width=True)

                st.markdown("##### All Events")
                st.dataframe(eq_df, use_container_width=True)

                # Magnitude distribution
                st.markdown("##### Magnitude Distribution")
                mag_bins = {"M<2": 0, "M2-3": 0, "M3-4": 0, "M4-5": 0, "M5-6": 0, "M6+": 0}
                for mag in eq_df["Magnitude"]:
                    if mag < 2:
                        mag_bins["M<2"] += 1
                    elif mag < 3:
                        mag_bins["M2-3"] += 1
                    elif mag < 4:
                        mag_bins["M3-4"] += 1
                    elif mag < 5:
                        mag_bins["M4-5"] += 1
                    elif mag < 6:
                        mag_bins["M5-6"] += 1
                    else:
                        mag_bins["M6+"] += 1
                dist_df = pd.DataFrame(
                    {"Range": list(mag_bins.keys()), "Count": list(mag_bins.values())}
                )
                st.bar_chart(dist_df.set_index("Range"))

                # Download
                csv_buf = io.StringIO()
                eq_df.to_csv(csv_buf, index=False)
                st.download_button(
                    "Download Earthquake CSV",
                    csv_buf.getvalue(),
                    file_name=f"earthquakes_{time_range}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="grt_dl_eq",
                )

    if show_fires and not fire_df.empty:
        with st.expander(f"Active Fire Data ({fire_stats['count']:,} detections)", expanded=False):
            fire_display = _build_fire_dataframe(fire_df)
            if not fire_display.empty:
                st.dataframe(fire_display.head(500), use_container_width=True)

                # Download
                csv_buf = io.StringIO()
                fire_display.to_csv(csv_buf, index=False)
                st.download_button(
                    "Download Fire Data CSV",
                    csv_buf.getvalue(),
                    file_name=f"active_fires_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="grt_dl_fire",
                )

    if show_aircraft and aircraft_states:
        with st.expander(f"Aircraft Data ({ac_count:,} tracked)", expanded=False):
            ac_df = _build_aircraft_dataframe(aircraft_states)
            if not ac_df.empty:
                # Top countries by aircraft
                st.markdown("##### Aircraft by Origin Country")
                country_counts = ac_df["Origin"].value_counts().head(20)
                st.bar_chart(country_counts)

                st.markdown("##### Aircraft Details (sample)")
                st.dataframe(ac_df.head(500), use_container_width=True)

                # Download
                csv_buf = io.StringIO()
                ac_df.to_csv(csv_buf, index=False)
                st.download_button(
                    "Download Aircraft CSV",
                    csv_buf.getvalue(),
                    file_name=f"aircraft_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="grt_dl_ac",
                )

    if show_disasters and disaster_alerts:
        with st.expander(f"Disaster Alerts ({len(disaster_alerts)} alerts)", expanded=False):
            dis_df = _build_disaster_dataframe(disaster_alerts)
            if not dis_df.empty:
                st.dataframe(dis_df, use_container_width=True)

                # Individual alert details
                st.markdown("##### Alert Details")
                for i, alert in enumerate(disaster_alerts[:10]):
                    level = alert.get("alertlevel", "Green")
                    color = "#ef4444" if "red" in level.lower() else (
                        "#f97316" if "orange" in level.lower() else "#10b981"
                    )
                    st.markdown(
                        f'<div style="border-left:3px solid {color};padding-left:0.75rem;'
                        f'margin-bottom:0.5rem;">'
                        f'<b>{html_module.escape(alert.get("title", ""))}</b><br/>'
                        f'<small style="color:#8b97b0;">{html_module.escape(alert.get("eventtype", ""))} '
                        f'| {html_module.escape(alert.get("severity", ""))} '
                        f'| Alert: {html_module.escape(level)}</small><br/>'
                        f'<small>{html_module.escape(alert.get("description", "")[:300])}</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # Download
                csv_buf = io.StringIO()
                dis_df.to_csv(csv_buf, index=False)
                st.download_button(
                    "Download Disaster Alerts CSV",
                    csv_buf.getvalue(),
                    file_name=f"disaster_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="grt_dl_dis",
                )

    if show_solar and space_data.get("kp") is not None:
        with st.expander("Space Weather Details", expanded=False):
            st.markdown("##### Current Conditions")

            kp_val = space_data["kp"]
            kp_color = _kp_color(kp_val)
            st.markdown(
                f'<div style="border-left:3px solid {kp_color};padding-left:0.75rem;">'
                f'<b>Planetary Kp Index: {kp_val:.1f}</b><br/>'
                f'<small>Activity Level: {html_module.escape(space_data.get("level", "Unknown"))}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Kp history chart
            kp_history = space_data.get("history", [])
            if kp_history:
                st.markdown("##### Recent Kp Index History")
                hist_df = pd.DataFrame(kp_history)
                if "kp" in hist_df.columns:
                    st.line_chart(hist_df.set_index("time")["kp"])

            # SWPC alerts
            swpc_alerts = space_data.get("alerts", [])
            if swpc_alerts:
                st.markdown("##### Recent SWPC Alerts")
                for alert_item in swpc_alerts[:5]:
                    if isinstance(alert_item, dict):
                        msg = alert_item.get("message", "")
                        issue_time = alert_item.get("issue_datetime", "")
                        st.markdown(
                            f'<div style="background:rgba(30,41,59,0.5);padding:0.5rem;'
                            f'border-radius:6px;margin-bottom:0.4rem;">'
                            f'<small style="color:#8b97b0;">{html_module.escape(str(issue_time))}</small><br/>'
                            f'<small>{html_module.escape(str(msg)[:500])}</small>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    if show_iss and iss_data.get("lat") is not None:
        with st.expander("ISS Details", expanded=False):
            iss_ts = iss_data.get("timestamp", 0)
            iss_time_str = ""
            if iss_ts:
                try:
                    iss_time_str = datetime.fromtimestamp(
                        iss_ts, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
                except (OSError, ValueError):
                    iss_time_str = "Unknown"

            icol1, icol2, icol3 = st.columns(3)
            with icol1:
                st.metric("Latitude", f"{iss_data['lat']:.4f}")
            with icol2:
                st.metric("Longitude", f"{iss_data['lon']:.4f}")
            with icol3:
                st.metric("Last Update", iss_time_str if iss_time_str else "N/A")

            st.info(
                "The International Space Station orbits Earth approximately every 90 minutes "
                "at an altitude of about 408 km (253 miles) and a speed of 28,000 km/h (17,500 mph)."
            )

    # ══════════════════════════════════════════
    # SECTION 6: Combined Data Export
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Export All Data")

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        # JSON export of all fetched data
        export_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "time_range": time_range,
            "analysis_mode": analysis_mode,
        }

        if show_earthquakes and eq_features:
            export_data["earthquakes"] = {
                "count": eq_stats["count"],
                "max_magnitude": eq_stats["max_mag"],
                "avg_magnitude": round(eq_stats["avg_mag"], 2),
            }
        if show_fires and not fire_df.empty:
            export_data["fires"] = {
                "count": fire_stats["count"],
                "avg_brightness": round(fire_stats["avg_brightness"], 1),
            }
        if show_aircraft and aircraft_states:
            export_data["aircraft"] = {"tracked": ac_count}
        if show_disasters and disaster_alerts:
            export_data["disasters"] = {
                "count": len(disaster_alerts),
                "alerts": [
                    {"title": a.get("title", ""), "type": a.get("eventtype", ""),
                     "level": a.get("alertlevel", "")}
                    for a in disaster_alerts
                ],
            }
        if show_iss and iss_data.get("lat") is not None:
            export_data["iss"] = {
                "latitude": iss_data["lat"],
                "longitude": iss_data["lon"],
            }
        if show_solar and space_data.get("kp") is not None:
            export_data["space_weather"] = {
                "kp_index": space_data["kp"],
                "level": space_data.get("level", ""),
            }

        st.download_button(
            "Download Summary (JSON)",
            json.dumps(export_data, indent=2),
            file_name=f"global_intelligence_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            key="grt_dl_json",
        )

    with export_col2:
        # Generate a text report
        report_lines = [
            "GLOBAL REAL-TIME INTELLIGENCE REPORT",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Time Range: {time_range}",
            f"Analysis Mode: {analysis_mode}",
            "=" * 50,
            "",
        ]

        if show_earthquakes and eq_features:
            report_lines.extend([
                "SEISMIC ACTIVITY",
                f"  Total earthquakes: {eq_stats['count']:,}",
                f"  Strongest event: M{eq_stats['max_mag']:.1f}",
                f"  Average magnitude: M{eq_stats['avg_mag']:.1f}",
                f"  Average depth: {eq_stats['avg_depth']:.1f} km",
                "",
            ])

        if show_fires and not fire_df.empty:
            report_lines.extend([
                "WILDFIRE ACTIVITY",
                f"  Active fire detections: {fire_stats['count']:,}",
                f"  Average brightness: {fire_stats['avg_brightness']:.1f}",
                "",
            ])

        if show_aircraft and aircraft_states:
            report_lines.extend([
                "AIR TRAFFIC",
                f"  Aircraft currently tracked: {ac_count:,}",
                "",
            ])

        if show_disasters and disaster_alerts:
            report_lines.extend([
                "DISASTER ALERTS",
                f"  Active alerts: {len(disaster_alerts)}",
            ])
            for a in disaster_alerts[:5]:
                report_lines.append(
                    f"  - [{a.get('alertlevel', 'N/A')}] {a.get('title', 'Unknown')}"
                )
            report_lines.append("")

        if show_iss and iss_data.get("lat") is not None:
            report_lines.extend([
                "ISS POSITION",
                f"  Latitude: {iss_data['lat']:.4f}",
                f"  Longitude: {iss_data['lon']:.4f}",
                "",
            ])

        if show_solar and space_data.get("kp") is not None:
            report_lines.extend([
                "SPACE WEATHER",
                f"  Kp Index: {space_data['kp']:.1f}",
                f"  Activity Level: {space_data.get('level', 'Unknown')}",
                "",
            ])

        report_text = "\n".join(report_lines)
        st.download_button(
            "Download Report (TXT)",
            report_text,
            file_name=f"intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            key="grt_dl_txt",
        )

    # ══════════════════════════════════════════
    # SECTION 7: Auto-Refresh
    # ══════════════════════════════════════════
    if auto_refresh:
        # Initialize or check the last refresh timestamp
        now = datetime.now(timezone.utc).timestamp()
        last_refresh = st.session_state.get("grt_last_refresh", 0)

        if now - last_refresh >= 60:
            st.session_state["grt_last_refresh"] = now
            # Clear caches and rerun
            fetch_earthquakes.clear()
            fetch_active_fires.clear()
            fetch_aircraft.clear()
            fetch_disaster_alerts.clear()
            fetch_iss_position.clear()
            fetch_space_weather.clear()
            st.rerun()
        else:
            remaining = int(60 - (now - last_refresh))
            st.caption(f"Auto-refresh in {remaining}s")

    # Footer
    st.markdown(
        '<div style="text-align:center;margin-top:1rem;">'
        '<small style="color:#5a6580;">Data sources: USGS, NASA FIRMS, OpenSky Network, '
        'GDACS, Open-Notify (ISS), NOAA SWPC &mdash; all free APIs, no keys required</small>'
        '</div>',
        unsafe_allow_html=True,
    )
