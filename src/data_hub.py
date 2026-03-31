"""
Data Hub - Shared cached data layer for TerraScout AI.
Wraps collect_all_intelligence() and computes all derived analytics
(domain scores, cross-correlations, SWOT, recommendations) in one shot.
Results are cached in st.session_state["ts_data_hub"] with a 30-min TTL.
"""

import time
import logging

import streamlit as st

from src.unified_intelligence import (
    collect_all_intelligence,
    compute_domain_scores,
    compute_cross_correlations,
    generate_swot,
    generate_recommendations,
    _compute_overall_score,
    _classify_score,
    compute_data_confidence,
    INTELLIGENCE_DOMAINS,
)
from src.enhanced_data_sources import fetch_all_enhanced_sources
from src.geopolitical_engine import fetch_complete_geopolitical_profile
from src.satellite_intelligence import fetch_complete_satellite_profile
from src.next_gen_data_sources import fetch_all_next_gen_sources
from src.advanced_data_sources import fetch_all_advanced_sources
from src.apex_data_sources import fetch_all_apex_sources

logger = logging.getLogger(__name__)

_HUB_KEY = "ts_data_hub"
_HUB_TTL = 1800  # 30 minutes


def init_data_hub():
    """Initialize the data hub in session state (no-op if already exists)."""
    pass  # We lazy-init on first get_hub_data call


def _is_stale(hub):
    """Check if cached hub data is older than TTL."""
    if not hub:
        return True
    ts = hub.get("_timestamp", 0)
    return (time.time() - ts) > _HUB_TTL


def get_hub_data(lat, lon):
    """Return cached hub data for (lat, lon), or fetch fresh.

    Returns a dict with keys:
        raw_data, scores, details, insights, swot, recommendations,
        overall_score, overall_label, overall_color, lat, lon
    """
    hub = st.session_state.get(_HUB_KEY)

    # Check if cached data matches current coordinates and is fresh
    if hub and not _is_stale(hub):
        if abs(hub.get("lat", 0) - lat) < 1e-4 and abs(hub.get("lon", 0) - lon) < 1e-4:
            return hub

    # Fetch fresh data
    raw_data = collect_all_intelligence(lat, lon)

    # Enhanced data sources (GDACS, WorldPop, OpenAQ)
    try:
        enhanced = fetch_all_enhanced_sources(lat, lon)
        raw_data["gdacs"] = enhanced.get("gdacs", [])
        raw_data["population"] = enhanced.get("population", {})
        raw_data["openaq"] = enhanced.get("openaq", [])
    except Exception as exc:
        logger.warning("Enhanced data sources fetch failed: %s", exc)
        raw_data.setdefault("gdacs", [])
        raw_data.setdefault("population", {})
        raw_data.setdefault("openaq", [])

    # Geopolitical context
    try:
        geopolitical = fetch_complete_geopolitical_profile(lat, lon)
        raw_data["geopolitical"] = geopolitical
    except Exception as exc:
        logger.warning("Geopolitical profile fetch failed: %s", exc)
        raw_data.setdefault("geopolitical", {})

    # Satellite intelligence (NDVI, land cover, water)
    try:
        satellite = fetch_complete_satellite_profile(lat, lon)
        raw_data["satellite"] = satellite
    except Exception as exc:
        logger.warning("Satellite intelligence fetch failed: %s", exc)
        raw_data.setdefault("satellite", {})

    # Next-gen data sources (NASA POWER, NOAA, FIRMS, WHO, HDI)
    try:
        next_gen = fetch_all_next_gen_sources(lat, lon)
        raw_data["nasa_power"] = next_gen.get("nasa_power", {})
        raw_data["noaa_alerts"] = next_gen.get("noaa_alerts", [])
        raw_data["firms_fires"] = next_gen.get("firms_fires", {})
        raw_data["who_health"] = next_gen.get("who_health", {})
        raw_data["hdi"] = next_gen.get("hdi", {})
    except Exception as exc:
        logger.warning("Next-gen data sources failed: %s", exc)
        for k in ("nasa_power", "firms_fires", "who_health", "hdi"):
            raw_data.setdefault(k, {})
        raw_data.setdefault("noaa_alerts", [])

    # Advanced data sources Phase 3 (Marine, Flood, Streamflow, ReliefWeb, GeoNames)
    try:
        advanced = fetch_all_advanced_sources(lat, lon)
        raw_data["marine"] = advanced.get("marine", {})
        raw_data["flood"] = advanced.get("flood", {})
        raw_data["streamflow"] = advanced.get("streamflow", {})
        raw_data["reliefweb"] = advanced.get("reliefweb", {})
        raw_data["geonames"] = advanced.get("geonames", {})
    except Exception as exc:
        logger.warning("Advanced data sources (Phase 3) failed: %s", exc)
        for k in ("marine", "flood", "streamflow", "reliefweb", "geonames"):
            raw_data.setdefault(k, {})

    # Apex data sources Phase 4 (Climate projections, Volcanoes, Normals, Soil moisture, UV/Pollen)
    try:
        apex = fetch_all_apex_sources(lat, lon)
        raw_data["climate_projections"] = apex.get("climate_projections", {})
        raw_data["volcanoes"] = apex.get("volcanoes", {})
        raw_data["climate_normals"] = apex.get("climate_normals", {})
        raw_data["soil_moisture"] = apex.get("soil_moisture", {})
        raw_data["uv_pollen"] = apex.get("uv_pollen", {})
    except Exception as exc:
        logger.warning("Apex data sources (Phase 4) failed: %s", exc)
        for k in ("climate_projections", "volcanoes", "climate_normals", "soil_moisture", "uv_pollen"):
            raw_data.setdefault(k, {})

    scores, details = compute_domain_scores(lat, lon, raw_data)
    insights = compute_cross_correlations(scores, details)
    swot = generate_swot(scores, details, insights)
    recommendations = generate_recommendations(scores, swot, insights)
    overall_score = _compute_overall_score(scores)
    overall_label, overall_color = _classify_score(overall_score)
    confidence = compute_data_confidence(raw_data)

    hub = {
        "lat": lat,
        "lon": lon,
        "raw_data": raw_data,
        "scores": scores,
        "details": details,
        "insights": insights,
        "swot": swot,
        "recommendations": recommendations,
        "overall_score": overall_score,
        "overall_label": overall_label,
        "overall_color": overall_color,
        "confidence": confidence,
        "_timestamp": time.time(),
    }

    st.session_state[_HUB_KEY] = hub
    return hub


def get_raw_source(source_name):
    """Access a single raw data source (e.g. 'soil', 'weather') from cached hub.

    Returns the raw API response dict, or {} if no hub data is available.
    """
    hub = st.session_state.get(_HUB_KEY)
    if not hub:
        return {}
    raw = hub.get("raw_data", {})
    return raw.get(source_name, {})


def invalidate_data_hub():
    """Invalidate the data hub cache (called by set_location)."""
    st.session_state.pop(_HUB_KEY, None)
