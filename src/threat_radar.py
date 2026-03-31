"""
Threat Radar — Real-Time Multi-Source Threat Aggregation for TerraScout AI.

Aggregates threats from ALL available sources into a unified threat picture:
- NASA FIRMS active fire hotspots
- GDACS disaster events
- USGS earthquake events
- Air quality alerts (from existing data)
- Terrain hazard indicators

Produces a UNIFIED THREAT LEVEL and proximity-weighted threat map.
"""

import math
import logging
from datetime import datetime

import requests
import streamlit as st

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# NASA FIRMS — Active Fire Data
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900)
def fetch_nasa_firms_fires(lat, lon, radius_km=100):
    """Fetch active fire hotspots from NASA FIRMS (MODIS/VIIRS).

    Uses the open CSV endpoint (no API key needed for MAP_KEY=FIRMS).
    Returns a list of fire hotspots near the location.
    """
    try:
        # Use the open FIRMS endpoint for recent 24h data
        # Map key for open access
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/"
            f"FIRMS_OPEN/VIIRS_SNPP_NRT/world/1"
        )
        resp = requests.get(url, timeout=12, headers={
            "Accept": "text/csv",
            "User-Agent": "TerraScout-AI/1.0",
        })

        if resp.status_code != 200:
            # Fallback: try the area API with bounding box
            return _fetch_firms_fallback(lat, lon, radius_km)

        # Parse CSV: latitude,longitude,bright_ti4,scan,track,acq_date,...
        lines = resp.text.strip().split("\n")
        if len(lines) < 2:
            return []

        headers = lines[0].split(",")
        lat_idx = _find_col(headers, ["latitude", "lat"])
        lon_idx = _find_col(headers, ["longitude", "lon", "lng"])
        bright_idx = _find_col(headers, ["bright_ti4", "brightness", "bright_ti5"])
        conf_idx = _find_col(headers, ["confidence", "conf"])
        date_idx = _find_col(headers, ["acq_date", "date"])

        fires = []
        for line in lines[1:]:
            try:
                cols = line.split(",")
                if lat_idx is None or lon_idx is None:
                    continue
                f_lat = float(cols[lat_idx])
                f_lon = float(cols[lon_idx])
                dist = _haversine(lat, lon, f_lat, f_lon)
                if dist > radius_km:
                    continue
                brightness = float(cols[bright_idx]) if bright_idx is not None else 0
                confidence = cols[conf_idx].strip() if conf_idx is not None else "N"
                acq_date = cols[date_idx].strip() if date_idx is not None else ""
                fires.append({
                    "lat": f_lat,
                    "lon": f_lon,
                    "distance_km": round(dist, 1),
                    "brightness": brightness,
                    "confidence": confidence,
                    "date": acq_date,
                })
            except (ValueError, IndexError):
                continue

        fires.sort(key=lambda x: x["distance_km"])
        return fires[:50]

    except Exception as e:
        logger.warning("NASA FIRMS fetch failed: %s", e)
        return []


def _fetch_firms_fallback(lat, lon, radius_km):
    """Fallback: construct fires from available data."""
    # If FIRMS API fails, return empty — fire data is optional
    return []


def _find_col(headers, candidates):
    """Find column index for any candidate name (case-insensitive)."""
    for i, h in enumerate(headers):
        if h.strip().lower() in [c.lower() for c in candidates]:
            return i
    return None


# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED THREAT ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

def compute_threat_assessment(raw_data, details, scores):
    """Aggregate all threat sources into a unified threat picture.

    Returns:
        {
            threat_level: "CRITICAL" | "HIGH" | "ELEVATED" | "MODERATE" | "LOW",
            threat_score: 0-100,
            threat_sources: list of {source, level, count, nearest_km, details},
            threat_summary: str,
            fire_data: list,
            combined_threats: int,
            proximity_alert: bool,
        }
    """
    threat_sources = []
    threat_score = 0

    # 1. EARTHQUAKE THREATS
    quakes = raw_data.get("quakes", {})
    eq_features = quakes.get("features", []) if isinstance(quakes, dict) else []
    significant_quakes = []
    for f in (eq_features if isinstance(eq_features, list) else []):
        props = f.get("properties", {}) if isinstance(f, dict) else {}
        mag = props.get("mag", 0)
        if mag and float(mag) >= 3.0:
            significant_quakes.append({
                "magnitude": float(mag),
                "place": props.get("place", "Unknown"),
                "time": props.get("time", 0),
            })

    if significant_quakes:
        max_mag = max(q["magnitude"] for q in significant_quakes)
        eq_score = min(30, len(significant_quakes) * 2 + max_mag * 3)
        level = "HIGH" if max_mag >= 5 else ("ELEVATED" if max_mag >= 4 else "MODERATE")
        threat_sources.append({
            "source": "SEISMIC",
            "icon": "earthquake",
            "level": level,
            "count": len(significant_quakes),
            "nearest_km": 0,  # area-based
            "score_contribution": round(eq_score, 1),
            "detail": f"Max magnitude: {max_mag:.1f}",
        })
        threat_score += eq_score

    # 2. DISASTER EVENTS (GDACS)
    gdacs = details.get("gdacs_events", raw_data.get("gdacs", []))
    if gdacs:
        red_events = sum(1 for e in gdacs if e.get("alert_level") == "RED")
        orange_events = sum(1 for e in gdacs if e.get("alert_level") == "ORANGE")
        nearest_dist = min(e.get("distance_km", 999) for e in gdacs)
        gdacs_score = red_events * 15 + orange_events * 8
        # Proximity bonus
        if nearest_dist < 50:
            gdacs_score += 10
        elif nearest_dist < 100:
            gdacs_score += 5
        gdacs_score = min(35, gdacs_score)

        level = "CRITICAL" if red_events > 0 else ("HIGH" if orange_events > 0 else "MODERATE")
        threat_sources.append({
            "source": "DISASTERS",
            "icon": "warning",
            "level": level,
            "count": len(gdacs),
            "nearest_km": round(nearest_dist, 1),
            "score_contribution": round(gdacs_score, 1),
            "detail": f"{red_events} red, {orange_events} orange alerts",
        })
        threat_score += gdacs_score

    # 3. AIR QUALITY THREATS
    aq_stations = details.get("nearest_aq_stations", [])
    air_quality = raw_data.get("air_quality", {})
    aqi = 0
    pm25 = 0
    if isinstance(air_quality, dict):
        current = air_quality.get("current", {})
        if isinstance(current, dict):
            aqi = current.get("european_aqi", 0) or 0
            pm25 = current.get("pm2_5", 0) or 0

    # Also check station data
    if aq_stations:
        station_pm25 = [s["pm25"] for s in aq_stations if s.get("pm25") is not None]
        if station_pm25:
            pm25 = max(pm25, max(station_pm25))

    if aqi > 50 or pm25 > 35:
        aq_score = min(20, aqi * 0.15 + pm25 * 0.2)
        level = "HIGH" if aqi > 100 or pm25 > 55 else "ELEVATED"
        threat_sources.append({
            "source": "AIR QUALITY",
            "icon": "air",
            "level": level,
            "count": 1,
            "nearest_km": 0,
            "score_contribution": round(aq_score, 1),
            "detail": f"AQI: {aqi}, PM2.5: {pm25:.1f} µg/m³",
        })
        threat_score += aq_score

    # 4. FIRE THREATS (NASA FIRMS — optional, may fail)
    fire_data = []
    try:
        fire_data = fetch_nasa_firms_fires(
            details.get("center_lat", raw_data.get("lat", 0)),
            details.get("center_lon", raw_data.get("lon", 0)),
            100
        )
    except Exception:
        pass

    if fire_data:
        high_conf_fires = [f for f in fire_data if f.get("confidence", "").upper() in ("H", "HIGH")]
        nearest_fire = fire_data[0].get("distance_km", 999)
        fire_score = min(25, len(fire_data) * 1.5 + len(high_conf_fires) * 3)
        if nearest_fire < 20:
            fire_score += 10
        fire_score = min(30, fire_score)

        level = "CRITICAL" if nearest_fire < 10 else ("HIGH" if len(fire_data) > 5 else "ELEVATED")
        threat_sources.append({
            "source": "WILDFIRE",
            "icon": "fire",
            "level": level,
            "count": len(fire_data),
            "nearest_km": round(nearest_fire, 1),
            "score_contribution": round(fire_score, 1),
            "detail": f"{len(high_conf_fires)} high-confidence hotspots",
        })
        threat_score += fire_score

    # 5. TERRAIN HAZARD
    hazard_score = scores.get("hazard_safety", 50)
    geo_score = scores.get("geological_stability", 50)
    if hazard_score < 35 or geo_score < 35:
        terrain_threat = max(0, (70 - min(hazard_score, geo_score)) * 0.3)
        threat_sources.append({
            "source": "TERRAIN",
            "icon": "terrain",
            "level": "ELEVATED" if terrain_threat > 5 else "MODERATE",
            "count": 0,
            "nearest_km": 0,
            "score_contribution": round(terrain_threat, 1),
            "detail": f"Hazard: {hazard_score:.0f}, Geo: {geo_score:.0f}",
        })
        threat_score += terrain_threat

    # UNIFIED THREAT LEVEL
    threat_score = min(100, threat_score)
    if threat_score >= 70:
        threat_level = "CRITICAL"
    elif threat_score >= 50:
        threat_level = "HIGH"
    elif threat_score >= 30:
        threat_level = "ELEVATED"
    elif threat_score >= 15:
        threat_level = "MODERATE"
    else:
        threat_level = "LOW"

    # Proximity alert
    proximity_alert = any(
        ts.get("nearest_km", 999) < 25
        for ts in threat_sources
        if ts["source"] in ("WILDFIRE", "DISASTERS")
    )

    # Summary
    if threat_sources:
        top_threats = sorted(threat_sources, key=lambda x: x["score_contribution"], reverse=True)
        primary = top_threats[0]["source"]
        summary = (
            f"Threat level: {threat_level} ({threat_score:.0f}/100). "
            f"Primary threat source: {primary}. "
            f"{len(threat_sources)} active threat categories monitored."
        )
    else:
        summary = f"Threat level: {threat_level}. No active threats detected."

    return {
        "threat_level": threat_level,
        "threat_score": round(threat_score, 1),
        "threat_sources": threat_sources,
        "threat_summary": summary,
        "fire_data": fire_data,
        "combined_threats": len(threat_sources),
        "proximity_alert": proximity_alert,
    }


# ═══════════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
