"""
global_events_api.py — 7 free global event APIs + unified aggregator.

Returns standardized event dicts for the Global Intelligence Globe.
"""

import html as html_module
import logging
import math
import csv
import io
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

EVENT_CATEGORIES = (
    "DISASTER", "EARTHQUAKE", "FIRE", "CONFLICT",
    "HEALTH", "WEATHER", "HUMANITARIAN", "NEWS",
)

# Country approximate centroids for geocoding fallback (~140 countries)
_COUNTRY_COORDS = {
    # Africa (50)
    "Algeria": (28.0, 3.0), "Angola": (-12.5, 18.5), "Benin": (9.3, 2.3), "Botswana": (-22.3, 24.7),
    "Burkina Faso": (12.3, -1.5), "Burundi": (-3.4, 29.9), "Cameroon": (6.0, 12.0), "Cape Verde": (15.1, -23.6),
    "Central African Republic": (6.6, 20.9), "Chad": (15.0, 19.0), "Comoros": (-12.2, 44.3),
    "Congo": (-1.0, 15.0), "DR Congo": (-3.0, 23.0), "Djibouti": (11.6, 43.1), "Egypt": (27.0, 30.0),
    "Equatorial Guinea": (1.6, 10.3), "Eritrea": (15.2, 39.8), "Eswatini": (-26.5, 31.5),
    "Ethiopia": (9.0, 38.7), "Gabon": (-0.8, 11.6), "Gambia": (13.4, -15.4), "Ghana": (7.9, -1.0),
    "Guinea": (9.9, -11.0), "Guinea-Bissau": (12.0, -15.0), "Ivory Coast": (7.5, -5.5),
    "Kenya": (1.0, 38.0), "Lesotho": (-29.6, 28.2), "Liberia": (6.4, -9.4), "Libya": (27.0, 17.0),
    "Madagascar": (-19.0, 47.0), "Malawi": (-13.3, 33.8), "Mali": (17.0, -4.0),
    "Mauritania": (20.3, -10.9), "Mauritius": (-20.3, 57.6), "Morocco": (32.0, -5.0),
    "Mozambique": (-18.0, 35.0), "Namibia": (-22.6, 17.1), "Niger": (16.0, 8.0), "Nigeria": (10.0, 8.0),
    "Rwanda": (-2.0, 29.9), "Senegal": (14.5, -14.5), "Sierra Leone": (8.5, -11.8),
    "Somalia": (6.0, 46.0), "South Africa": (-29.0, 24.0), "South Sudan": (7.0, 30.0),
    "Sudan": (15.0, 30.0), "Tanzania": (-6.4, 34.9), "Togo": (8.6, 1.2), "Tunisia": (34.0, 9.0),
    "Uganda": (1.4, 32.3), "Zambia": (-13.1, 27.8), "Zimbabwe": (-20.0, 30.0),
    # Americas (26)
    "Argentina": (-34.0, -64.0), "Belize": (17.2, -88.5), "Bolivia": (-17.0, -65.0),
    "Brazil": (-10.0, -55.0), "Canada": (56.0, -106.0), "Chile": (-30.0, -71.0),
    "Colombia": (4.0, -72.0), "Costa Rica": (10.0, -84.0), "Cuba": (22.0, -80.0),
    "Dominican Republic": (18.7, -70.2), "Ecuador": (-2.0, -77.5), "El Salvador": (13.8, -88.9),
    "Guatemala": (15.5, -90.3), "Haiti": (19.0, -72.3), "Honduras": (15.0, -86.5),
    "Jamaica": (18.1, -77.3), "Mexico": (23.0, -102.0), "Nicaragua": (12.9, -85.2),
    "Panama": (9.0, -79.5), "Paraguay": (-23.4, -58.4), "Peru": (-10.0, -76.0),
    "Puerto Rico": (18.2, -66.6), "Trinidad": (10.4, -61.3), "Trinidad and Tobago": (10.4, -61.3),
    "United States": (38.0, -97.0), "Uruguay": (-32.5, -55.8), "Venezuela": (8.0, -66.0),
    # Asia (40)
    "Afghanistan": (33.0, 65.0), "Armenia": (40.1, 44.5), "Azerbaijan": (40.4, 49.9),
    "Bahrain": (26.0, 50.5), "Bangladesh": (24.0, 90.0), "Bhutan": (27.5, 90.4),
    "Brunei": (4.9, 114.9), "Cambodia": (13.0, 105.0), "China": (35.0, 105.0),
    "Georgia": (42.3, 43.4), "India": (22.0, 78.0), "Indonesia": (-2.0, 118.0),
    "Iran": (32.0, 53.0), "Iraq": (33.0, 44.0), "Israel": (31.5, 34.8), "Japan": (36.0, 138.0),
    "Jordan": (31.0, 36.0), "Kazakhstan": (48.0, 68.0), "Kuwait": (29.5, 47.8),
    "Kyrgyzstan": (41.2, 74.8), "Laos": (18.0, 105.0), "Lebanon": (33.9, 35.9),
    "Malaysia": (4.2, 101.7), "Maldives": (3.2, 73.2), "Mongolia": (46.9, 103.8),
    "Myanmar": (22.0, 98.0), "Nepal": (28.0, 84.0), "North Korea": (40.3, 127.5),
    "Oman": (21.5, 55.9), "Pakistan": (30.0, 70.0), "Palestine": (31.9, 35.2),
    "Philippines": (13.0, 122.0), "Qatar": (25.3, 51.2), "Saudi Arabia": (24.0, 45.0),
    "Singapore": (1.3, 103.8), "South Korea": (36.5, 127.8), "Sri Lanka": (7.9, 80.8),
    "Syria": (35.0, 38.0), "Taiwan": (23.7, 121.0), "Tajikistan": (38.9, 71.3),
    "Thailand": (15.0, 100.0), "Timor-Leste": (-8.6, 125.7), "Turkmenistan": (38.9, 59.6),
    "United Arab Emirates": (24.0, 54.0), "Uzbekistan": (41.4, 64.6),
    "Vietnam": (16.0, 108.0), "Yemen": (15.0, 48.0),
    # Europe (34)
    "Albania": (41.2, 20.2), "Austria": (47.5, 14.6), "Belarus": (53.7, 27.9),
    "Belgium": (50.8, 4.5), "Bosnia and Herzegovina": (44.0, 17.8), "Bulgaria": (42.7, 25.5),
    "Croatia": (45.2, 15.5), "Cyprus": (35.1, 33.4), "Czech Republic": (49.8, 15.5),
    "Czechia": (49.8, 15.5), "Denmark": (56.3, 9.5), "Estonia": (58.6, 25.0),
    "Finland": (64.0, 26.0), "France": (46.0, 2.0), "Germany": (51.0, 10.0),
    "Greece": (39.0, 22.0), "Hungary": (47.2, 19.5), "Iceland": (65.0, -18.0),
    "Ireland": (53.4, -8.2), "Italy": (42.5, 12.5), "Kosovo": (42.6, 21.0),
    "Latvia": (56.9, 24.1), "Lithuania": (55.2, 23.9), "Luxembourg": (49.8, 6.1),
    "Malta": (35.9, 14.4), "Moldova": (47.4, 28.4), "Montenegro": (42.7, 19.4),
    "Netherlands": (52.1, 5.3), "North Macedonia": (41.5, 21.7), "Norway": (62.0, 10.0),
    "Poland": (52.0, 20.0), "Portugal": (39.4, -8.2), "Romania": (45.9, 25.0),
    "Russia": (60.0, 100.0), "Serbia": (44.0, 21.0), "Slovakia": (48.7, 19.7),
    "Slovenia": (46.1, 14.8), "Spain": (40.0, -4.0), "Sweden": (62.0, 15.0),
    "Switzerland": (46.8, 8.2), "Turkey": (39.0, 35.0), "Ukraine": (49.0, 32.0),
    "United Kingdom": (54.0, -2.0),
    # Oceania (8)
    "Australia": (-25.0, 134.0), "Fiji": (-18.0, 178.0), "New Zealand": (-41.3, 174.9),
    "Papua New Guinea": (-6.3, 147.0), "Samoa": (-13.8, -172.0), "Solomon Islands": (-9.4, 160.0),
    "Tonga": (-21.2, -175.2), "Vanuatu": (-15.4, 166.9),
}

_EONET_CATEGORY_MAP = {
    "Wildfires": "FIRE", "Volcanoes": "DISASTER", "Severe Storms": "WEATHER",
    "Floods": "DISASTER", "Earthquakes": "EARTHQUAKE", "Drought": "WEATHER",
    "Dust and Haze": "WEATHER", "Landslides": "DISASTER", "Snow": "WEATHER",
    "Sea and Lake Ice": "WEATHER", "Temperature Extremes": "WEATHER",
    "Water Color": "WEATHER", "Manmade": "HUMANITARIAN",
}

_GDACS_TYPE_MAP = {
    "EQ": "EARTHQUAKE", "FL": "DISASTER", "TC": "WEATHER",
    "VO": "DISASTER", "DR": "WEATHER", "WF": "FIRE",
    "TS": "EARTHQUAKE",
}

_GDACS_SEVERITY_MAP = {"Green": 0.3, "Orange": 0.6, "Red": 0.9}

# WHO severity keywords — high-lethality / pandemic-potential diseases
_WHO_SEVERITY_KEYWORDS = {
    0.9: ("ebola", "marburg", "cholera outbreak"),
    0.8: ("avian influenza", "mers", "plague"),
    0.7: ("dengue", "yellow fever", "mpox"),
}

# ReliefWeb disaster-type keywords for severity
_RELIEFWEB_SEVERITY_KEYWORDS = {
    0.85: ("earthquake", "tsunami"),
    0.75: ("flood", "cyclone", "hurricane", "typhoon"),
    0.70: ("drought", "famine"),
    0.65: ("conflict", "displacement"),
}

# Source confidence levels (Phase 1D)
_SOURCE_CONFIDENCE = {
    "USGS": 0.95,
    "GDACS": 0.90,
    "NASA EONET": 0.85,
    "NASA FIRMS": 0.80,
    "WHO": 0.85,
    "ReliefWeb": 0.75,
    "GDELT": 0.60,
}

# Adaptive dedup parameters per category (Phase 1C)
_DEDUP_RADIUS_KM = {
    "EARTHQUAKE": 30, "FIRE": 15, "WEATHER": 100,
    "CONFLICT": 50, "HEALTH": 75, "NEWS": 25,
    "DISASTER": 50, "HUMANITARIAN": 75,
}
_DEDUP_TIME_HOURS = {
    "EARTHQUAKE": 7 * 24, "FIRE": 3 * 24, "WEATHER": 5 * 24,
    "CONFLICT": 14 * 24, "HEALTH": 30 * 24, "NEWS": 2 * 24,
    "DISASTER": 7 * 24, "HUMANITARIAN": 14 * 24,
}
# Cross-category merge pairs (Phase 1C)
_CROSS_CATEGORY_MERGE = {
    "EARTHQUAKE": "DISASTER", "FIRE": "DISASTER", "WEATHER": "DISASTER",
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _normalize_severity(raw_value, min_val=0.0, max_val=10.0):
    """Map a raw value from [min_val, max_val] to [0.0, 1.0]."""
    if raw_value is None:
        return 0.5
    try:
        v = float(raw_value)
    except (TypeError, ValueError):
        return 0.5
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (v - min_val) / (max_val - min_val)))


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _parse_date_to_utc(date_str):
    """Best-effort parse of a date string to a datetime in UTC, or None."""
    if not date_str:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y%m%d%H%M%S",
        "%Y-%m-%dT%H%M",
    ):
        try:
            dt = datetime.strptime(str(date_str).strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    # Fallback: Python fromisoformat (handles many ISO 8601 variants)
    try:
        return datetime.fromisoformat(str(date_str).strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass
    return None


_last_geocode_time = 0.0


def _geocode_location(place_name):
    """Geocode a place name to (lat, lon) via Nominatim with fallback."""
    global _last_geocode_time
    if not place_name:
        return None, None
    # Check country coords first (longest names first to avoid Niger->Nigeria)
    for country, coords in sorted(_COUNTRY_COORDS.items(), key=lambda x: len(x[0]), reverse=True):
        if country.lower() in place_name.lower():
            return coords
    # Try Nominatim (rate-limited to 1 request per 1.1 seconds)
    try:
        now = time.time()
        if now - _last_geocode_time < 1.1:
            time.sleep(1.1 - (now - _last_geocode_time))
        _last_geocode_time = time.time()
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json", "limit": 1},
            headers={"User-Agent": "TerraScoutAI/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


def _safe_str(value):
    """Convert to string for safe storage. HTML escaping done at render time."""
    return str(value).strip() if value else ""


def _token_overlap(a, b):
    """Compute token overlap ratio between two strings (pure Python, no deps)."""
    tokens_a = set(re.findall(r'\w{3,}', (a or "").lower()))
    tokens_b = set(re.findall(r'\w{3,}', (b or "").lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / min(len(tokens_a), len(tokens_b))


def _make_event(
    eid, title, description, lat, lon, date_str,
    category, severity, source, url="", extra=None,
    confidence=None,
):
    """Build a standardized event dict. HTML escaping done at render time."""
    if confidence is None:
        confidence = _SOURCE_CONFIDENCE.get(str(source), 0.70)
    return {
        "id": str(eid),
        "title": _safe_str(title)[:200],
        "description": _safe_str(description)[:300],
        "lat": float(lat) if lat is not None else 0.0,
        "lon": float(lon) if lon is not None else 0.0,
        "date": str(date_str or ""),
        "category": category if category in EVENT_CATEGORIES else "NEWS",
        "severity": max(0.0, min(1.0, float(severity or 0.5))),
        "source": str(source),
        "url": str(url or ""),
        "extra": extra or {},
        "confidence": max(0.0, min(1.0, float(confidence))),
        "updated_at": datetime.now(timezone.utc).isoformat()[:19] + "Z",
    }


def compute_impact_score(event):
    """Compute a composite impact score 0-100 for an event."""
    base = event.get("severity", 0.5) * 60
    cred_boost = min(20, event.get("credibility", 1) * 5)
    cat_boost = {"EARTHQUAKE": 15, "DISASTER": 12, "CONFLICT": 10,
                 "FIRE": 8, "HEALTH": 8}.get(event.get("category", ""), 5)
    # Recency boost (Phase 1B)
    recency_boost = 0
    ev_dt = _parse_date_to_utc(event.get("date", ""))
    if ev_dt:
        hours_ago = (datetime.now(timezone.utc) - ev_dt).total_seconds() / 3600
        if hours_ago < 6:
            recency_boost = 10
        elif hours_ago < 24:
            recency_boost = 5
    return min(100, base + cred_boost + cat_boost + recency_boost)


# ═══════════════════════════════════════════════════════════════════════════
# API A: GDELT GEO — Global news events with locations
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900)
def fetch_gdelt_events(timespan="24h", max_events=200):
    """Fetch geolocated news events from GDELT GEO API."""
    events = []
    try:
        url = (
            "https://api.gdeltproject.org/api/v2/geo/geo"
            f"?query=&format=GeoJSON&timespan={timespan}"
        )
        resp = requests.get(url, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", []) if isinstance(data, dict) else []
        for i, feat in enumerate(features[:max_events]):
            if not isinstance(feat, dict):
                continue
            props = feat.get("properties", {}) or {}
            geom = feat.get("geometry", {}) or {}
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            if lat == 0 and lon == 0:
                continue
            name = props.get("name", "News Event")

            # ── Tone parsing (Phase 1A: clamp to [-15,+15], explicit missing) ──
            tone_raw = props.get("tone")
            if tone_raw is None or tone_raw == "":
                tone_val = 0.0
            else:
                try:
                    tone_val = max(-15.0, min(15.0, float(tone_raw)))
                except (TypeError, ValueError):
                    tone_val = 0.0

            # ── Article count ──
            numarts = 0
            try:
                numarts = int(props.get("numarts", 0))
            except (TypeError, ValueError):
                numarts = 0

            # ── Goldstein scale (Phase 1B) ──
            goldstein_raw = props.get("goldsteinscale")
            has_goldstein = False
            goldstein_val = 0.0
            if goldstein_raw is not None:
                try:
                    goldstein_val = float(goldstein_raw)
                    has_goldstein = True
                except (TypeError, ValueError):
                    pass

            # ── Severity: use 40/30/30 if goldstein available, else 60/40 ──
            tone_severity = _normalize_severity(-tone_val, -15, 15)
            coverage_severity = min(1.0, numarts / 50) if numarts > 0 else 0.0
            if has_goldstein:
                goldstein_severity = _normalize_severity(-goldstein_val, -10, 10)
                sev = 0.4 * tone_severity + 0.3 * coverage_severity + 0.3 * goldstein_severity
            else:
                sev = 0.6 * tone_severity + 0.4 * coverage_severity

            # ── Impact score for extra ──
            gdelt_impact = numarts * abs(tone_val)

            # ── Category detection for high-impact negative news ──
            category = "NEWS"
            if tone_val < -5 and numarts > 10:
                name_lower = name.lower()
                conflict_kw = ("attack", "war", "military", "bomb", "strike", "kill",
                               "soldier", "troops", "armed", "weapon", "terror")
                disaster_kw = ("flood", "earthquake", "hurricane", "typhoon", "cyclone",
                               "tsunami", "landslide", "eruption", "wildfire", "storm")
                if any(kw in name_lower for kw in conflict_kw):
                    category = "CONFLICT"
                elif any(kw in name_lower for kw in disaster_kw):
                    category = "DISASTER"

            domain = _safe_str(props.get("domain", ""))
            share_image = str(props.get("shareimage", ""))
            article_url = props.get("url", "")

            events.append(_make_event(
                eid=f"gdelt_{i}",
                title=name,
                description=f"GDELT news event. Tone: {tone_val:.1f}, Articles: {numarts}",
                lat=lat, lon=lon,
                date_str=props.get("date", datetime.now(timezone.utc).isoformat()[:10]),
                category=category,
                severity=sev,
                source="GDELT",
                url=article_url,
                extra={
                    "tone": tone_val,
                    "num_articles": numarts,
                    "domain": domain,
                    "share_image": share_image,
                    "impact_score": round(gdelt_impact, 1),
                },
            ))
    except Exception as exc:
        logger.warning("GDELT fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API B: GDACS — Active natural disasters
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def fetch_gdacs_global_events():
    """Fetch active disasters from GDACS API (GeoJSON)."""
    events = []
    try:
        resp = requests.get(
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", []) if isinstance(data, dict) else []
        for i, feat in enumerate(features[:100]):
            if not isinstance(feat, dict):
                continue
            props = feat.get("properties", {}) or {}
            geom = feat.get("geometry", {}) or {}
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            etype = str(props.get("eventtype", ""))
            category = _GDACS_TYPE_MAP.get(etype, "DISASTER")

            # ── Alert-level base severity ──
            alert_level = str(props.get("alertlevel", "Green"))
            alert_sev = _GDACS_SEVERITY_MAP.get(alert_level, 0.5)

            # ── Extract detailed severity data (Phase 1A: isinstance guard) ──
            severity_data = props.get("severitydata", {}) or {}
            if not isinstance(severity_data, dict):
                severity_data = {}
            sev_value = None
            sev_unit_raw = severity_data.get("severityUnit", "")
            sev_unit = str(sev_unit_raw) if isinstance(sev_unit_raw, (str, int, float)) else ""
            population = 0
            sev_raw = severity_data.get("severity", 0)
            if isinstance(sev_raw, (int, float)):
                sev_value = float(sev_raw)
            elif isinstance(sev_raw, str):
                try:
                    sev_value = float(sev_raw)
                except (TypeError, ValueError):
                    sev_value = None
            pop_raw = severity_data.get("population", 0)
            if isinstance(pop_raw, (int, float)):
                population = int(pop_raw)
            elif isinstance(pop_raw, str):
                try:
                    population = int(float(pop_raw))
                except (TypeError, ValueError):
                    population = 0

            # ── Compute severity: blend alert-level with numeric severity ──
            if sev_value is not None and sev_value > 0:
                # Normalize numeric severity (depends on event type)
                if etype == "EQ":
                    numeric_sev = _normalize_severity(sev_value, 0, 9)
                elif etype == "TC":
                    numeric_sev = _normalize_severity(sev_value, 0, 250)  # wind speed km/h
                elif etype == "FL":
                    numeric_sev = _normalize_severity(sev_value, 0, 5)
                else:
                    numeric_sev = _normalize_severity(sev_value, 0, 10)
                sev = 0.6 * numeric_sev + 0.4 * alert_sev
            else:
                sev = alert_sev

            # Population boost: multiplicative (Phase 1B)
            if population > 10_000_000:
                sev = min(1.0, sev * 1.25)
            elif population > 1_000_000:
                sev = min(1.0, sev * 1.15)
            elif population > 100_000:
                sev = min(1.0, sev * 1.08)

            to_date = str(props.get("todate", ""))

            events.append(_make_event(
                eid=f"gdacs_{props.get('eventid', i)}",
                title=props.get("eventname", props.get("htmldescription", "Disaster Event")),
                description=props.get("description", f"{etype} event, alert: {alert_level}"),
                lat=lat, lon=lon,
                date_str=props.get("fromdate", ""),
                category=category,
                severity=sev,
                source="GDACS",
                url=props.get("url", ""),
                extra={
                    "alert_level": alert_level,
                    "event_type": etype,
                    "severity_value": sev_value if sev_value is not None else 0,
                    "severity_unit": sev_unit,
                    "population": population,
                    "to_date": to_date,
                },
            ))
    except Exception as exc:
        logger.warning("GDACS fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API C: USGS Significant Earthquakes — Last 7 days
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_usgs_significant_quakes():
    """Fetch significant earthquakes from USGS (last 7 days)."""
    events = []
    try:
        resp = requests.get(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", []) if isinstance(data, dict) else []
        for feat in features:
            if not isinstance(feat, dict):
                continue
            props = feat.get("properties", {}) or {}
            geom = feat.get("geometry", {}) or {}
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            mag = props.get("mag", 0)
            try:
                mag_f = float(mag)
            except (TypeError, ValueError):
                mag_f = 0.0
            sev = _normalize_severity(mag_f, 0, 10)

            # ── Depth modifier (Phase 1B): shallow=amplify, deep=dampen ──
            depth_km = 0.0
            if len(coords) > 2:
                try:
                    depth_km = float(coords[2])
                except (TypeError, ValueError):
                    depth_km = 0.0
            if depth_km < 10:
                sev = min(1.0, sev * 1.15)
            elif depth_km > 300:
                sev = max(0.0, sev * 0.85)

            # ── Felt reports boost ──
            felt = 0
            try:
                felt = int(props.get("felt") or 0)
            except (TypeError, ValueError):
                felt = 0
            if felt > 1000:
                sev = min(1.0, sev + 0.1)
            elif felt > 500:
                sev = min(1.0, sev + 0.05)

            # ── Additional seismic metadata ──
            cdi = None
            try:
                cdi = float(props.get("cdi")) if props.get("cdi") is not None else None
            except (TypeError, ValueError):
                cdi = None
            mmi = None
            try:
                mmi = float(props.get("mmi")) if props.get("mmi") is not None else None
            except (TypeError, ValueError):
                mmi = None
            status = str(props.get("status", ""))

            ts = props.get("time")
            date_str = ""
            if ts:
                try:
                    date_str = datetime.fromtimestamp(
                        ts / 1000, tz=timezone.utc
                    ).isoformat()[:19]
                except Exception:
                    pass
            events.append(_make_event(
                eid=feat.get("id", f"usgs_{mag_f}"),
                title=props.get("place", f"M{mag_f:.1f} Earthquake"),
                description=f"Magnitude {mag_f:.1f} earthquake. {props.get('place', '')}",
                lat=lat, lon=lon,
                date_str=date_str,
                category="EARTHQUAKE",
                severity=sev,
                source="USGS",
                url=props.get("url", ""),
                extra={
                    "magnitude": mag_f,
                    "depth": float(coords[2]) if len(coords) > 2 else 0,
                    "tsunami": props.get("tsunami", 0),
                    "felt": felt,
                    "cdi": cdi,
                    "mmi": mmi,
                    "status": status,
                },
            ))
    except Exception as exc:
        logger.warning("USGS fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API D: NASA FIRMS — Global active fires (last 24h)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_global_fires(max_fires=500):
    """Fetch global active fires from NASA FIRMS (VIIRS SNPP, last 24h)."""
    events = []
    try:
        firms_key = os.environ.get("FIRMS_MAP_KEY", "DEMO_KEY")
        resp = requests.get(
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{firms_key}/VIIRS_SNPP_NRT/world/1",
            timeout=20,
        )
        # Fallback URL if primary fails
        if resp.status_code != 200:
            resp = requests.get(
                f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{firms_key}/VIIRS_SNPP_NRT/world/1",
                timeout=20,
            )
        resp.raise_for_status()
        # Verify response is CSV-like (not error HTML/JSON)
        content_type = resp.headers.get("Content-Type", "")
        if "text/csv" not in content_type and "text/plain" not in content_type:
            logger.warning("FIRMS returned unexpected content-type: %s", content_type)
            return []
        reader = csv.DictReader(io.StringIO(resp.text))
        # Phase 1A: validate required CSV columns
        if reader.fieldnames:
            required_cols = {"latitude", "longitude", "frp", "confidence"}
            available = set(c.lower().strip() for c in reader.fieldnames if c)
            if not required_cols.issubset(available):
                logger.warning("FIRMS CSV missing columns: %s",
                               required_cols - available)
                return []
        all_fires = []
        for row in reader:
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))
                frp = float(row.get("frp", 0))
                conf = row.get("confidence", "nominal")
                all_fires.append((lat, lon, frp, conf, row))
            except (TypeError, ValueError):
                continue
        # Sample down to max_fires evenly
        step = max(1, len(all_fires) // max_fires)
        sampled = all_fires[::step][:max_fires]
        for i, (lat, lon, frp, conf, row) in enumerate(sampled):
            # ── Brightness temperature ──
            bright_ti4 = 0.0
            try:
                bright_ti4 = float(row.get("bright_ti4", 0))
            except (TypeError, ValueError):
                bright_ti4 = 0.0

            # ── Day/night flag ──
            daynight = str(row.get("daynight", "")).upper()

            # ── Severity: 70% FRP, 30% brightness (Phase 1B: FRP range 500) ──
            frp_sev = _normalize_severity(frp, 0, 500)
            bright_sev = _normalize_severity(bright_ti4, 300, 500)
            sev = 0.7 * frp_sev + 0.3 * bright_sev

            # Confidence boost
            if conf in ("high", "h"):
                sev = min(1.0, sev + 0.15)

            # Night fire boost (more concerning / harder to fight)
            if daynight == "N":
                sev = min(1.0, sev + 0.05)

            # Cluster density boost (Phase 1B): grid 0.5°, ≥10 fires = +0.15
            grid_key = (round(lat * 2) / 2, round(lon * 2) / 2)
            nearby_count = sum(
                1 for f_lat, f_lon, _, _, _ in all_fires
                if (round(f_lat * 2) / 2, round(f_lon * 2) / 2) == grid_key
            )
            if nearby_count >= 10:
                sev = min(1.0, sev + 0.15)

            acq_date = row.get("acq_date", "")
            acq_time = row.get("acq_time", "")
            events.append(_make_event(
                eid=f"firms_{i}",
                title=f"Active Fire ({lat:.2f}, {lon:.2f})",
                description=f"Fire radiative power: {frp:.1f} MW. Confidence: {conf}",
                lat=lat, lon=lon,
                date_str=f"{acq_date}T{acq_time[:2]}:{acq_time[2:]}" if acq_date and len(acq_time) >= 4 else (f"{acq_date}" if acq_date else ""),
                category="FIRE",
                severity=sev,
                source="NASA FIRMS",
                extra={
                    "frp": frp,
                    "confidence": conf,
                    "satellite": row.get("satellite", ""),
                    "bright_ti4": bright_ti4,
                    "daynight": daynight,
                },
            ))
    except Exception as exc:
        logger.warning("NASA FIRMS fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API E: NASA EONET — Natural events (storms, icebergs, etc.)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_eonet_events():
    """Fetch open natural events from NASA EONET v3."""
    events = []
    try:
        resp = requests.get(
            "https://eonet.gsfc.nasa.gov/api/v3/events",
            params={"status": "open", "limit": 50},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        eonet_events = data.get("events", []) if isinstance(data, dict) else []
        for ev in eonet_events:
            if not isinstance(ev, dict):
                continue
            categories = ev.get("categories", [])
            cat_title = ""
            if categories and isinstance(categories[0], dict):
                cat_title = categories[0].get("title", "")
            category = _EONET_CATEGORY_MAP.get(cat_title, "WEATHER")
            geometry = ev.get("geometry", [])
            if not geometry or not isinstance(geometry, list):
                continue

            # ── Use latest geometry point for location ──
            last_geom = geometry[-1]
            if not isinstance(last_geom, dict):
                continue
            coords = last_geom.get("coordinates", [])
            date_str = last_geom.get("date", "")
            if not coords or len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])

            # ── Extract magnitude from geometry if available ──
            sev = 0.4  # default (Phase 1B: reduced from 0.6)
            magnitude_val = None
            magnitude_unit = ""
            for gpt in geometry:
                if isinstance(gpt, dict) and "magnitudeValue" in gpt:
                    try:
                        magnitude_val = float(gpt["magnitudeValue"])
                        # Phase 1A: only overwrite unit if non-empty
                        new_unit = str(gpt.get("magnitudeUnit", ""))
                        if new_unit:
                            magnitude_unit = new_unit
                    except (TypeError, ValueError):
                        pass

            if magnitude_val is not None:
                # Normalize based on unit type
                if "kts" in magnitude_unit.lower():
                    sev = _normalize_severity(magnitude_val, 0, 200)
                elif "km" in magnitude_unit.lower() and "sq" not in magnitude_unit.lower():
                    sev = _normalize_severity(magnitude_val, 0, 500)
                elif "acres" in magnitude_unit.lower() or "sq" in magnitude_unit.lower():
                    sev = _normalize_severity(magnitude_val, 0, 500000)
                else:
                    sev = _normalize_severity(magnitude_val, 0, 100)

            # ── Duration boost (Phase 1B): long-running events ──
            first_dt = _parse_date_to_utc(
                geometry[0].get("date", "") if isinstance(geometry[0], dict) else ""
            )
            last_dt_eonet = _parse_date_to_utc(
                geometry[-1].get("date", "") if isinstance(geometry[-1], dict) else ""
            )
            if first_dt and last_dt_eonet and last_dt_eonet > first_dt:
                duration_days = (last_dt_eonet - first_dt).total_seconds() / 86400
                if duration_days > 14:
                    sev = min(1.0, sev + 0.15)
                elif duration_days > 7:
                    sev = min(1.0, sev + 0.10)

            # ── Compute trajectory info from all geometry points ──
            trajectory_len_km = 0.0
            num_points = 0
            movement_speed_kmh = 0.0
            for gidx in range(1, len(geometry)):
                prev_g = geometry[gidx - 1]
                curr_g = geometry[gidx]
                if not isinstance(prev_g, dict) or not isinstance(curr_g, dict):
                    continue
                pc = prev_g.get("coordinates", [])
                cc = curr_g.get("coordinates", [])
                if len(pc) >= 2 and len(cc) >= 2:
                    try:
                        seg = _haversine(float(pc[1]), float(pc[0]),
                                         float(cc[1]), float(cc[0]))
                        trajectory_len_km += seg
                        num_points += 1
                    except (TypeError, ValueError):
                        pass
            # Estimate average speed from first to last point
            if num_points >= 1 and len(geometry) >= 2:
                first_dt = _parse_date_to_utc(
                    geometry[0].get("date", "") if isinstance(geometry[0], dict) else ""
                )
                last_dt = _parse_date_to_utc(
                    geometry[-1].get("date", "") if isinstance(geometry[-1], dict) else ""
                )
                if first_dt and last_dt and last_dt > first_dt:
                    hours = (last_dt - first_dt).total_seconds() / 3600.0
                    if hours > 0:
                        movement_speed_kmh = round(trajectory_len_km / hours, 1)

            title = ev.get("title", "Natural Event")
            events.append(_make_event(
                eid=ev.get("id", f"eonet_{title}"),
                title=title,
                description=f"EONET: {cat_title}. {title}",
                lat=lat, lon=lon,
                date_str=date_str,
                category=category,
                severity=sev,
                source="NASA EONET",
                url=ev.get("link", ""),
                extra={
                    "eonet_category": cat_title,
                    "magnitude_value": magnitude_val,
                    "magnitude_unit": magnitude_unit,
                    "trajectory_km": round(trajectory_len_km, 1),
                    "num_geometry_points": len(geometry),
                    "movement_speed_kmh": movement_speed_kmh,
                },
            ))
    except Exception as exc:
        logger.warning("EONET fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API F: WHO Disease Outbreaks — Global health emergencies
# ═══════════════════════════════════════════════════════════════════════════

def _who_severity_from_title(title):
    """Assign severity based on disease-type keywords in the title.
    Phase 1B: partial keyword matching (all words in keyword must appear)."""
    title_lower = (title or "").lower()
    for sev, keywords in _WHO_SEVERITY_KEYWORDS.items():
        for kw in keywords:
            # Exact match first
            if kw in title_lower:
                return sev, kw
            # Partial match: all words in the keyword must appear
            kw_words = kw.split()
            if len(kw_words) > 1 and all(w in title_lower for w in kw_words):
                return sev, kw
    return 0.6, ""


@st.cache_data(ttl=3600)
def fetch_who_outbreaks():
    """Fetch disease outbreak news from WHO Disease Outbreak News API (JSON)."""
    events = []
    try:
        resp = requests.get(
            "https://www.who.int/api/news/diseaseoutbreaknews",
            params={"$orderby": "PublicationDate desc", "$top": 30},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("value", []) if isinstance(data, dict) else []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            title = item.get("Title", "Health Event")
            summary = item.get("Summary", "")
            pub_date = item.get("PublicationDate", "")
            item_id = item.get("Id", i)
            link = f"https://www.who.int/emergencies/disease-outbreak-news/item/{item_id}"

            # Try country from CountryName field first, then parse from title
            country_name = item.get("CountryName", "") or ""
            lat, lon = None, None
            if country_name:
                lat, lon = _geocode_location(country_name)
            if lat is None or lon is None:
                lat, lon = _geocode_location(title)
            if lat is None or lon is None:
                # Phase 1A: log when geocoding fails
                logger.info("WHO: geocoding failed for '%s', skipping", title[:80])
                continue

            # Disease-keyword severity
            sev, disease_keyword = _who_severity_from_title(title)

            # Phase 1B: multi-country boost (+0.1 for ≥3 countries)
            country_count = 0
            for cname in _COUNTRY_COORDS:
                if cname.lower() in (title or "").lower() or cname.lower() in (summary or "").lower():
                    country_count += 1
            if country_count >= 3:
                sev = min(1.0, sev + 0.1)

            events.append(_make_event(
                eid=f"who_{i}",
                title=title,
                description=summary[:300] if summary else "WHO disease outbreak report",
                lat=lat, lon=lon,
                date_str=pub_date,
                category="HEALTH",
                severity=sev,
                source="WHO",
                url=link,
                extra={
                    "disease_keyword": disease_keyword,
                    "country": country_name,
                    "country_count": country_count,
                },
            ))
    except Exception as exc:
        logger.warning("WHO outbreaks fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# API G: ReliefWeb Crises — Humanitarian emergencies
# ═══════════════════════════════════════════════════════════════════════════

def _reliefweb_severity(title, fields):
    """Compute ReliefWeb severity from status, disaster-type keywords, or default.
    Phase 1B: null-check status, accumulate keyword matches."""
    base_sev = 0.5
    # Check status field (Phase 1B: null-check)
    status_info = fields.get("status") if isinstance(fields, dict) else None
    if status_info is not None:
        status = ""
        if isinstance(status_info, dict):
            status = str(status_info.get("name", "")).lower()
        elif isinstance(status_info, str):
            status = status_info.lower()
        if "alert" in status or "emergency" in status:
            base_sev = 0.8
        elif "ongoing" in status:
            base_sev = 0.65

    # Phase 1B: accumulate keyword matches (each adds a small boost)
    title_lower = (title or "").lower()
    keyword_boost = 0.0
    matched_count = 0
    for sev, keywords in _RELIEFWEB_SEVERITY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                if matched_count == 0:
                    base_sev = max(base_sev, sev)
                else:
                    keyword_boost += 0.05
                matched_count += 1
    return min(1.0, base_sev + keyword_boost)


@st.cache_data(ttl=1800)
def fetch_reliefweb_crises():
    """Fetch humanitarian reports from ReliefWeb RSS feed."""
    events = []
    try:
        resp = requests.get(
            "https://reliefweb.int/updates/rss.xml",
            timeout=10,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return events
        items = channel.findall("item")
        for i, item in enumerate(items[:50]):
            title = item.findtext("title", "Humanitarian Report")
            desc_raw = item.findtext("description", "")
            # Strip HTML tags from description + Phase 1A: unescape HTML entities
            desc = html_module.unescape(re.sub(r'<[^>]+>', '', desc_raw))[:300]
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            # Extract country from title (often "Country: Title" format)
            country_name = ""
            if ": " in title:
                country_name = title.split(": ")[0].strip()
            lat, lon = _geocode_location(country_name or title)
            if lat is None or lon is None:
                continue

            sev = _reliefweb_severity(title, {})

            # ── Extract disaster type keyword for extra ──
            disaster_type = ""
            title_lower = title.lower()
            for _, keywords in _RELIEFWEB_SEVERITY_KEYWORDS.items():
                for kw in keywords:
                    if kw in title_lower:
                        disaster_type = kw
                        break
                if disaster_type:
                    break

            events.append(_make_event(
                eid=f"reliefweb_{i}",
                title=title,
                description=desc if desc else "ReliefWeb humanitarian report",
                lat=float(lat), lon=float(lon),
                date_str=pub_date,
                category="HUMANITARIAN",
                severity=sev,
                source="ReliefWeb",
                url=link,
                extra={
                    "country": country_name,
                    "disaster_type": disaster_type,
                },
            ))
    except Exception as exc:
        logger.warning("ReliefWeb fetch failed: %s", exc)
    return events


# ═══════════════════════════════════════════════════════════════════════════
# AGGREGATOR — Fetch all sources, deduplicate, sort, score
# ═══════════════════════════════════════════════════════════════════════════

def fetch_all_global_events(timespan="24h"):
    """Fetch all 7 sources in parallel, deduplicate (spatial+temporal),
    compute credibility & impact scores, sort by severity descending."""
    fetchers = [
        ("GDELT", lambda: fetch_gdelt_events(timespan=timespan, max_events=200)),
        ("GDACS", fetch_gdacs_global_events),
        ("USGS", fetch_usgs_significant_quakes),
        ("FIRMS", lambda: fetch_global_fires(max_fires=500)),
        ("EONET", fetch_eonet_events),
        ("WHO", fetch_who_outbreaks),
        ("ReliefWeb", fetch_reliefweb_crises),
    ]

    all_events = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {}
        for name, fn in fetchers:
            future_map[executor.submit(fn)] = name
        for future in as_completed(future_map):
            source_name = future_map[future]
            try:
                result = future.result(timeout=30)
                if isinstance(result, list):
                    all_events.extend(result)
                    logger.info("Fetched %d events from %s", len(result), source_name)
            except Exception as exc:
                logger.warning("Source %s failed: %s", source_name, exc)

    # ── Filter null island (0, 0) coordinates ──
    all_events = [ev for ev in all_events if not (ev["lat"] == 0.0 and ev["lon"] == 0.0)]

    # ── Smart deduplication (Phase 1C): adaptive radius/time + title similarity ──
    deduped = []
    for ev in all_events:
        merged = False
        ev_dt = _parse_date_to_utc(ev.get("date", ""))
        ev_cat = ev["category"]
        # Adaptive radius and time window for this category
        radius_km = _DEDUP_RADIUS_KM.get(ev_cat, 50)
        time_window_h = _DEDUP_TIME_HOURS.get(ev_cat, 48)
        # Cross-category merge partner
        cross_cat = _CROSS_CATEGORY_MERGE.get(ev_cat)

        for existing in deduped:
            ex_cat = existing["category"]
            # Category match: same category OR cross-category pair
            cats_match = (ev_cat == ex_cat)
            if not cats_match and cross_cat:
                cats_match = (ex_cat == cross_cat or ex_cat == ev_cat)
            if not cats_match:
                # Check reverse cross-category
                ex_cross = _CROSS_CATEGORY_MERGE.get(ex_cat)
                if ex_cross and ex_cross == ev_cat:
                    cats_match = True
            if not cats_match:
                continue

            dist = _haversine(ev["lat"], ev["lon"], existing["lat"], existing["lon"])
            if dist >= radius_km:
                continue

            # Temporal check: within adaptive time window
            ex_dt = _parse_date_to_utc(existing.get("date", ""))
            if ev_dt and ex_dt:
                time_diff = abs((ev_dt - ex_dt).total_seconds())
                if time_diff > time_window_h * 3600:
                    continue

            # Title similarity check (token overlap)
            title_sim = _token_overlap(ev.get("title", ""), existing.get("title", ""))
            # Require either close proximity OR title similarity
            if dist > radius_km * 0.5 and title_sim < 0.3:
                continue

            # ── Merge: keep highest severity, earliest date, combine sources ──
            merged_sources = existing.get("merged_sources", [existing["source"]])
            if ev["source"] not in merged_sources:
                merged_sources.append(ev["source"])
            existing["merged_sources"] = merged_sources
            existing["credibility"] = len(merged_sources)

            # Track merged IDs
            merged_ids = existing.get("merged_ids", [existing["id"]])
            if ev["id"] not in merged_ids:
                merged_ids.append(ev["id"])
            existing["merged_ids"] = merged_ids

            if ev["severity"] > existing["severity"]:
                keep_sources = existing["merged_sources"]
                keep_cred = existing["credibility"]
                keep_date = existing["date"]
                keep_ids = existing["merged_ids"]
                existing.update(ev)
                existing["merged_sources"] = keep_sources
                existing["credibility"] = keep_cred
                existing["merged_ids"] = keep_ids
                if ev_dt and ex_dt and ex_dt < ev_dt:
                    existing["date"] = keep_date
            else:
                if ev_dt and ex_dt and ev_dt < ex_dt:
                    existing["date"] = ev["date"]

            merged = True
            break

        if not merged:
            ev["merged_sources"] = [ev["source"]]
            ev["credibility"] = 1
            ev["merged_ids"] = [ev["id"]]
            deduped.append(ev)

    # ── Enforce timespan cutoff: remove events older than requested window ──
    timespan_hours = {"1h": 1, "6h": 6, "12h": 12, "24h": 24,
                      "3d": 72, "7d": 168, "30d": 720}
    cutoff_h = timespan_hours.get(timespan, 168)  # default 7 days
    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=cutoff_h)
    time_filtered = []
    for ev in deduped:
        ev_dt = _parse_date_to_utc(ev.get("date", ""))
        if ev_dt is None or ev_dt >= cutoff_dt:
            time_filtered.append(ev)
    logger.info("Timespan filter (%s): %d -> %d events", timespan,
                len(deduped), len(time_filtered))
    deduped = time_filtered

    # ── Compute impact scores ──
    for ev in deduped:
        ev["impact_score"] = round(compute_impact_score(ev), 1)

    # Sort by severity descending
    deduped.sort(key=lambda e: e.get("severity", 0), reverse=True)

    logger.info("Aggregated %d events (from %d raw)", len(deduped), len(all_events))
    return deduped
