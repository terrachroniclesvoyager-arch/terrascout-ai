"""
Seismic Intelligence AI module for TerraScout AI.
Provides deep seismic/earthquake analysis with historical patterns,
magnitude distribution, depth classification, ground stability assessment,
and trend analysis using USGS earthquake data and SoilGrids soil data.
"""

import math
import logging
from datetime import datetime, timedelta

import html as html_module
import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

_SEISMIC_COLORS = {
    "high": "#ef4444",
    "moderate": "#f59e0b",
    "low": "#22c55e",
    "bg": "#1a1a2e",
    "card": "rgba(26,26,46,0.85)",
    "border": "#3d1a1a",
    "text": "#e8ecf4",
    "muted": "#8b97b0",
    "accent": "#ef4444",
    "accent2": "#f59e0b",
}

_INDEX_META = {
    "Seismic Activity": {"color": "#ef4444"},
    "Maximum Event Risk": {"color": "#f97316"},
    "Proximity Risk": {"color": "#f59e0b"},
    "Ground Stability": {"color": "#22c55e"},
    "Trend": {"color": "#8b5cf6"},
}

_MAG_RANGES = [
    ("< 2.0", 0, 2),
    ("2.0 - 3.0", 2, 3),
    ("3.0 - 4.0", 3, 4),
    ("4.0 - 5.0", 4, 5),
    ("5.0 - 6.0", 5, 6),
    ("6.0+", 6, 99),
]

_MAG_COLORS = ["#22c55e", "#84cc16", "#f59e0b", "#f97316", "#ef4444", "#dc2626"]


# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Cached USGS fetchers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_detailed_earthquakes(lat, lon, radius_km=300, days=365):
    """
    Fetch recent earthquakes from USGS within *radius_km* of (lat, lon)
    for the last *days* days.  Returns a GeoJSON dict or {}.
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        params = {
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "orderby": "magnitude",
            "limit": 500,
        }
        resp = requests.get(USGS_API, params=params, timeout=25)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("USGS recent earthquakes fetch failed: %s", exc)
        return {}


@st.cache_data(ttl=1800)
def fetch_historical_earthquakes(lat, lon, radius_km=500, years=10):
    """
    Fetch longer-term earthquake history from USGS for trend analysis.
    Returns a GeoJSON dict or {}.
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=years * 365)
        params = {
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "orderby": "magnitude",
            "limit": 1000,
        }
        resp = requests.get(USGS_API, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("USGS historical earthquakes fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Soil helpers
# ---------------------------------------------------------------------------

def _soil_value(props, name, div=10.0):
    """Return the top-layer mean for a soil property, or None."""
    layers = props.get("layers", [])
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            depths = layer.get("depths", [])
            if depths:
                raw = depths[0].get("values", {}).get("mean")
                if raw is not None:
                    return raw / div
    return None


def _classify_ground(clay, sand, silt, water_table_hint):
    """
    Classify ground type for seismic amplification purposes.
    Returns (label, amplification_factor).
    """
    if clay is None and sand is None:
        return "Unknown", 1.0

    c = clay if clay is not None else 20
    sa = sand if sand is not None else 30
    si = silt if silt is not None else 30

    # Liquefiable: saturated loose sand
    if sa > 60 and water_table_hint:
        return "Liquefiable", 2.0

    # Rock-like: very low clay, low silt, could be rocky
    if c < 5 and si < 15 and sa > 70:
        return "Rock", 0.8

    # Stiff soil: high clay content
    if c > 35:
        return "Stiff Soil", 1.2

    # Soft soil: high silt, moderate clay
    if si > 50 or (c > 15 and c <= 35 and sa < 40):
        return "Soft Soil", 1.5

    return "Stiff Soil", 1.1


# ---------------------------------------------------------------------------
# Main compute function
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_seismic_profile(lat, lon):
    """
    Compute a comprehensive seismic risk profile for a location.
    Returns a dict with risk scores, distributions, trends, and
    recommendations.
    """
    # --- data fetching ---
    recent_data = fetch_detailed_earthquakes(lat, lon, radius_km=300, days=365)
    historical_data = fetch_historical_earthquakes(lat, lon, radius_km=500, years=10)
    elevation = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)
    soil = fetch_soil_data(lat, lon)

    props = soil.get("properties", {}) if isinstance(soil, dict) else {}
    clay = _soil_value(props, "clay", 10)
    sand = _soil_value(props, "sand", 10)
    silt = _soil_value(props, "silt", 10)
    phh2o = _soil_value(props, "phh2o", 10)

    center_elev = 0
    if isinstance(elevation, dict):
        center_elev = elevation.get("center_elevation", 0) or 0

    # --- parse features ---
    recent_features = recent_data.get("features", []) if isinstance(recent_data, dict) else []
    hist_features = historical_data.get("features", []) if isinstance(historical_data, dict) else []

    # --- magnitude distribution ---
    mag_dist = {}
    for label, lo, hi in _MAG_RANGES:
        mag_dist[label] = 0

    all_magnitudes = []
    for f in recent_features:
        p = f.get("properties", {})
        mag = p.get("mag")
        if mag is not None:
            all_magnitudes.append(float(mag))
            for label, lo, hi in _MAG_RANGES:
                if lo <= float(mag) < hi:
                    mag_dist[label] += 1
                    break

    # --- depth distribution ---
    shallow = 0  # < 70 km
    intermediate = 0  # 70 - 300 km
    deep = 0  # > 300 km
    for f in recent_features:
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        if len(coords) >= 3:
            depth_km = coords[2]
            if depth_km is not None:
                if depth_km < 70:
                    shallow += 1
                elif depth_km <= 300:
                    intermediate += 1
                else:
                    deep += 1

    depth_dist = {
        "Shallow (< 70 km)": shallow,
        "Intermediate (70-300 km)": intermediate,
        "Deep (> 300 km)": deep,
    }

    # --- monthly trend (from historical data) ---
    monthly_counts = {}
    for f in hist_features:
        p = f.get("properties", {})
        ts = p.get("time")
        if ts is not None:
            try:
                dt = datetime.utcfromtimestamp(ts / 1000.0)
                key = dt.strftime("%Y-%m")
                monthly_counts[key] = monthly_counts.get(key, 0) + 1
            except Exception:
                pass

    sorted_months = sorted(monthly_counts.keys())
    monthly_trend = [{"month": m, "count": monthly_counts[m]} for m in sorted_months]

    # --- max magnitude ---
    valid_mags = [x for x in all_magnitudes if x is not None]
    max_mag = max(valid_mags) if valid_mags else 0.0

    hist_mags = []
    for f in hist_features:
        p = f.get("properties", {})
        m = p.get("mag")
        if m is not None:
            hist_mags.append(float(m))
    valid_hist_mags = [x for x in hist_mags if x is not None]
    max_hist_mag = max(valid_hist_mags) if valid_hist_mags else 0.0
    overall_max_mag = max(max_mag, max_hist_mag)

    # --- nearest significant event (mag >= 4) ---
    nearest_sig_dist = None
    nearest_sig_event = None
    for f in recent_features + hist_features:
        p = f.get("properties", {})
        mag = p.get("mag")
        if mag is not None and float(mag) >= 4.0:
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                eq_lon = coords[0]
                eq_lat = coords[1]
                dist = _haversine(lat, lon, eq_lat, eq_lon)
                if nearest_sig_dist is None or dist < nearest_sig_dist:
                    nearest_sig_dist = dist
                    nearest_sig_event = {
                        "magnitude": float(mag),
                        "distance_km": round(dist, 1),
                        "place": p.get("place", "Unknown"),
                        "time": p.get("time"),
                    }

    # --- ground classification ---
    water_hint = False
    if phh2o is not None and phh2o > 7.5:
        water_hint = True
    if center_elev < 10:
        water_hint = True

    ground_class, amplification = _classify_ground(clay, sand, silt, water_hint)

    # --- compute 5 seismic indices (0-10 scale) ---

    # 1. Seismic Activity: based on event count and average magnitude
    n_events = len(valid_mags)
    avg_mag = sum(valid_mags) / len(valid_mags) if valid_mags else 0
    activity_score = min(10, (n_events / 50.0) * 4 + avg_mag * 1.2)
    activity_score = round(max(0, min(10, activity_score)), 1)

    # 2. Maximum Event Risk: based on largest recorded magnitude
    if overall_max_mag >= 7.0:
        max_risk = 10.0
    elif overall_max_mag >= 6.0:
        max_risk = 8.5
    elif overall_max_mag >= 5.0:
        max_risk = 6.5
    elif overall_max_mag >= 4.0:
        max_risk = 4.5
    elif overall_max_mag >= 3.0:
        max_risk = 3.0
    elif overall_max_mag >= 2.0:
        max_risk = 1.5
    else:
        max_risk = 0.5
    max_risk = round(max_risk, 1)

    # 3. Proximity Risk: distance to nearest significant event
    if nearest_sig_dist is not None:
        if nearest_sig_dist < 10:
            prox_risk = 10.0
        elif nearest_sig_dist < 50:
            prox_risk = 8.0
        elif nearest_sig_dist < 100:
            prox_risk = 6.0
        elif nearest_sig_dist < 200:
            prox_risk = 4.0
        elif nearest_sig_dist < 400:
            prox_risk = 2.0
        else:
            prox_risk = 1.0
    else:
        prox_risk = 1.0
    prox_risk = round(prox_risk, 1)

    # 4. Ground Stability: soil type + liquefaction potential
    ground_scores = {
        "Rock": 2.0,
        "Stiff Soil": 4.0,
        "Soft Soil": 6.5,
        "Liquefiable": 9.0,
        "Unknown": 5.0,
    }
    ground_stability = ground_scores.get(ground_class, 5.0)
    # adjust for clay + water = worse
    if clay is not None and clay > 40 and water_hint:
        ground_stability = min(10, ground_stability + 1.5)
    ground_stability = round(ground_stability, 1)

    # 5. Trend: whether seismic activity is increasing, stable, or decreasing
    trend_score = 5.0
    trend_label = "Stable"
    if len(monthly_trend) >= 6:
        half = len(monthly_trend) // 2
        first_half = [e["count"] for e in monthly_trend[:half]]
        second_half = [e["count"] for e in monthly_trend[half:]]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        if avg_second > avg_first * 1.3:
            trend_score = 7.5
            trend_label = "Increasing"
        elif avg_second > avg_first * 1.1:
            trend_score = 6.0
            trend_label = "Slightly Increasing"
        elif avg_second < avg_first * 0.7:
            trend_score = 2.5
            trend_label = "Decreasing"
        elif avg_second < avg_first * 0.9:
            trend_score = 4.0
            trend_label = "Slightly Decreasing"
        else:
            trend_score = 5.0
            trend_label = "Stable"
    trend_score = round(trend_score, 1)

    indices = {
        "Seismic Activity": activity_score,
        "Maximum Event Risk": max_risk,
        "Proximity Risk": prox_risk,
        "Ground Stability": ground_stability,
        "Trend": trend_score,
    }

    # --- overall risk ---
    idx_values = [v for v in indices.values() if v is not None]
    overall_risk = round(sum(idx_values) / len(idx_values), 1) if idx_values else 0.0

    if overall_risk >= 7:
        risk_class = "High"
    elif overall_risk >= 4:
        risk_class = "Moderate"
    else:
        risk_class = "Low"

    # --- top 10 recent events ---
    recent_events = []
    for f in recent_features[:10]:
        p = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        mag = p.get("mag")
        ts = p.get("time")
        depth = coords[2] if len(coords) >= 3 else None
        eq_lat = coords[1] if len(coords) >= 2 else None
        eq_lon = coords[0] if len(coords) >= 1 else None
        dist = _haversine(lat, lon, eq_lat, eq_lon) if eq_lat is not None and eq_lon is not None else None
        time_str = ""
        if ts is not None:
            try:
                time_str = datetime.utcfromtimestamp(ts / 1000.0).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        recent_events.append({
            "magnitude": float(mag) if mag is not None else 0,
            "place": p.get("place", "Unknown"),
            "time": time_str,
            "depth_km": round(float(depth), 1) if depth is not None else None,
            "distance_km": round(dist, 1) if dist is not None else None,
        })

    # --- recommendations ---
    recommendations = _build_recommendations(
        overall_risk, risk_class, indices, ground_class,
        amplification, n_events, overall_max_mag, nearest_sig_dist,
        trend_label,
    )

    return {
        "overall_risk": overall_risk,
        "risk_class": risk_class,
        "indices": indices,
        "magnitude_distribution": mag_dist,
        "depth_distribution": depth_dist,
        "monthly_trend": monthly_trend,
        "nearest_significant": nearest_sig_event,
        "ground_classification": ground_class,
        "amplification_factor": amplification,
        "recent_events": recent_events,
        "recommendations": recommendations,
        "max_magnitude": overall_max_mag,
        "total_events_recent": n_events,
        "total_events_historical": len(hist_mags),
        "trend_label": trend_label,
        "elevation": center_elev,
    }


# ---------------------------------------------------------------------------
# Recommendations engine
# ---------------------------------------------------------------------------

def _build_recommendations(overall, risk_class, indices, ground_class,
                           amplification, n_events, max_mag, nearest_dist,
                           trend_label):
    recs = []

    if risk_class == "High":
        recs.append({
            "title": "High Seismic Risk Zone",
            "text": (
                "This area shows significant seismic activity. All structures "
                "should comply with seismic building codes. Conduct detailed "
                "site-specific geotechnical surveys before any construction."
            ),
            "priority": "high",
        })

    if max_mag >= 5.0:
        recs.append({
            "title": f"Historical M{max_mag:.1f} Event Recorded",
            "text": (
                "A magnitude 5+ event has been recorded in this region. "
                "Consider seismic retrofitting for older structures and "
                "ensure emergency preparedness plans are in place."
            ),
            "priority": "high",
        })
    elif max_mag >= 4.0:
        recs.append({
            "title": f"Moderate Events Recorded (M{max_mag:.1f})",
            "text": (
                "Moderate seismic events have occurred in this region. "
                "Standard seismic design provisions should be followed."
            ),
            "priority": "medium",
        })

    if ground_class == "Liquefiable":
        recs.append({
            "title": "Liquefaction Risk Detected",
            "text": (
                "Sandy soil with potential water saturation indicates "
                "liquefaction risk during seismic events. Deep foundations, "
                "soil densification, or ground improvement may be needed."
            ),
            "priority": "high",
        })
    elif ground_class == "Soft Soil":
        recs.append({
            "title": "Soft Soil Amplification",
            "text": (
                f"Soft soil conditions (amplification factor {amplification:.1f}x) "
                "can amplify ground shaking. Consider stiffer foundation systems "
                "and account for site effects in structural design."
            ),
            "priority": "medium",
        })

    if nearest_dist is not None and nearest_dist < 50:
        recs.append({
            "title": "Close Proximity to Significant Events",
            "text": (
                f"A significant earthquake (M4+) occurred within {nearest_dist:.0f} km. "
                "This proximity warrants heightened awareness and seismic-resistant design."
            ),
            "priority": "high",
        })

    if trend_label in ("Increasing", "Slightly Increasing"):
        recs.append({
            "title": "Increasing Seismic Trend",
            "text": (
                "The frequency of seismic events appears to be increasing over "
                "time. This may indicate tectonic stress accumulation. Monitor "
                "USGS alerts and maintain emergency preparedness."
            ),
            "priority": "medium",
        })

    if amplification > 1.3:
        recs.append({
            "title": f"Site Amplification Factor: {amplification:.1f}x",
            "text": (
                "Ground conditions may amplify seismic waves. Engineering design "
                "should account for site amplification effects beyond standard "
                "seismic hazard maps."
            ),
            "priority": "medium",
        })

    if risk_class == "Low" and not recs:
        recs.append({
            "title": "Low Seismic Risk",
            "text": (
                "This location shows minimal seismic activity. Standard "
                "building practices are generally adequate, though basic "
                "seismic provisions are always recommended."
            ),
            "priority": "info",
        })

    if not recs:
        recs.append({
            "title": "Moderate Seismic Environment",
            "text": (
                "This area has moderate seismic characteristics. Follow local "
                "building codes and maintain standard earthquake preparedness."
            ),
            "priority": "info",
        })

    return recs


# ---------------------------------------------------------------------------
# Render function
# ---------------------------------------------------------------------------

def render_seismic_profiler_tab():
    """Render the Seismic Intelligence AI tab in Streamlit."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#7f1d1d 0%,#1a1a2e 100%);'
        'border-radius:14px;padding:18px 24px;margin-bottom:18px;'
        'border:1px solid #ef4444;">'
        '<h4 style="color:#ef4444;margin:0;">Seismic Intelligence AI</h4>'
        '<p style="color:#d4a9a9;margin:4px 0 0 0;font-size:14px;">'
        'Deep seismic risk profiling with USGS earthquake data, historical trend '
        'analysis, magnitude distributions, ground stability, and site amplification.</p></div>',
        unsafe_allow_html=True,
    )

    # --- Location selector ---
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="sp_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    with c2:
        lat = st.number_input(
            "Latitude", min_value=-90.0, max_value=90.0,
            value=p.get("lat", 41.90) if p else 41.90,
            format="%.5f", key="sp_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0,
            value=p.get("lon", 12.50) if p else 12.50,
            format="%.5f", key="sp_lon",
        )

    run = st.button(
        "Profile Seismic Risk", type="primary",
        key="sp_run", use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Profile Seismic Risk** to begin "
            "comprehensive seismic intelligence analysis."
        )
        return

    # --- Compute ---
    with st.spinner("Fetching earthquake data, soil, and elevation..."):
        data = compute_seismic_profile(lat, lon)

    overall = data["overall_risk"]
    risk_class = data["risk_class"]
    indices = data["indices"]
    mag_dist = data["magnitude_distribution"]
    depth_dist = data["depth_distribution"]
    monthly_trend = data["monthly_trend"]
    nearest_sig = data["nearest_significant"]
    ground_class = data["ground_classification"]
    recent_events = data["recent_events"]
    recs = data["recommendations"]
    amp = data["amplification_factor"]

    # --- risk color ---
    if risk_class == "High":
        risk_color = _SEISMIC_COLORS["high"]
    elif risk_class == "Moderate":
        risk_color = _SEISMIC_COLORS["moderate"]
    else:
        risk_color = _SEISMIC_COLORS["low"]

    # ================================================================
    # Overall risk header
    # ================================================================
    st.markdown(
        f'<div style="background:{_SEISMIC_COLORS["card"]};border:1px solid '
        f'{_SEISMIC_COLORS["border"]};border-radius:12px;padding:18px 24px;'
        f'margin:12px 0;text-align:center;">'
        f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:14px;">'
        f'Overall Seismic Risk Score</span><br/>'
        f'<span style="color:{risk_color};font-size:44px;font-weight:bold;">'
        f'{overall}</span>'
        f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:18px;"> / 10</span><br/>'
        f'<span style="background:{risk_color};color:#fff;padding:3px 14px;'
        f'border-radius:8px;font-size:13px;font-weight:600;">{risk_class} Risk</span>'
        f'<br/><span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;margin-top:6px;'
        f'display:inline-block;">'
        f'Max recorded M{data["max_magnitude"]:.1f} &bull; '
        f'{data["total_events_recent"]} events (1 yr) &bull; '
        f'{data["total_events_historical"]} events (10 yr) &bull; '
        f'Trend: {data["trend_label"]}</span></div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # 5 Index cards
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SEISMIC_COLORS["accent"]};margin-top:18px;">'
        f'Seismic Risk Indices</h5>',
        unsafe_allow_html=True,
    )
    idx_keys = list(indices.keys())
    cols = st.columns(5)
    for i, col in enumerate(cols):
        if i >= len(idx_keys):
            break
        key = idx_keys[i]
        val = indices[key]
        meta = _INDEX_META.get(key, {"color": "#06b6d4"})
        color = meta["color"]
        if val >= 7:
            level = "High"
            level_color = _SEISMIC_COLORS["high"]
        elif val >= 4:
            level = "Moderate"
            level_color = _SEISMIC_COLORS["moderate"]
        else:
            level = "Low"
            level_color = _SEISMIC_COLORS["low"]
        bar_pct = min(val * 10, 100)
        col.markdown(
            f'<div style="background:{_SEISMIC_COLORS["card"]};border:1px solid '
            f'{_SEISMIC_COLORS["border"]};border-radius:10px;padding:12px;'
            f'text-align:center;min-height:130px;">'
            f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:11px;">'
            f'{key}</span><br/>'
            f'<span style="color:{color};font-size:28px;font-weight:bold;">'
            f'{val}</span>'
            f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;">/10</span><br/>'
            f'<div style="background:#2a2a3e;border-radius:4px;height:8px;'
            f'margin-top:6px;overflow:hidden;">'
            f'<div style="width:{bar_pct}%;background:{color};height:100%;'
            f'border-radius:4px;"></div></div>'
            f'<span style="color:{level_color};font-size:10px;">{level}</span></div>',
            unsafe_allow_html=True,
        )

    # ================================================================
    # Magnitude distribution bar chart
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:18px;">'
        f'Magnitude Distribution (1 Year)</h5>',
        unsafe_allow_html=True,
    )
    mag_labels = list(mag_dist.keys())
    mag_values = [mag_dist[k] for k in mag_labels]

    fig_mag = go.Figure()
    fig_mag.add_trace(go.Bar(
        x=mag_labels,
        y=mag_values,
        marker_color=_MAG_COLORS[:len(mag_labels)],
        text=mag_values,
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig_mag.update_layout(
        paper_bgcolor=_SEISMIC_COLORS["bg"],
        plot_bgcolor=_SEISMIC_COLORS["bg"],
        font=dict(color="#e8ecf4"),
        xaxis=dict(title="Magnitude Range", gridcolor="#3d1a1a",
                   tickfont=dict(color="#8b97b0")),
        yaxis=dict(title="Number of Events", gridcolor="#3d1a1a",
                   tickfont=dict(color="#8b97b0")),
        height=340,
        margin=dict(t=20, b=50, l=50, r=20),
        showlegend=False,
    )
    st.plotly_chart(fig_mag, use_container_width=True, key="seipro_pchart1")

    # ================================================================
    # Depth distribution pie chart
    # ================================================================
    col_depth, col_trend = st.columns(2)

    with col_depth:
        st.markdown(
            f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:12px;">'
            f'Depth Distribution</h5>',
            unsafe_allow_html=True,
        )
        depth_labels = list(depth_dist.keys())
        depth_values = [depth_dist[k] for k in depth_labels]
        depth_colors = ["#22c55e", "#f59e0b", "#ef4444"]

        fig_depth = go.Figure()
        fig_depth.add_trace(go.Pie(
            labels=depth_labels,
            values=depth_values,
            marker=dict(colors=depth_colors,
                        line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent+value",
            textfont=dict(color="#e8ecf4", size=11),
            hole=0.4,
        ))
        fig_depth.update_layout(
            paper_bgcolor=_SEISMIC_COLORS["bg"],
            plot_bgcolor=_SEISMIC_COLORS["bg"],
            font=dict(color="#e8ecf4"),
            showlegend=True,
            legend=dict(font=dict(color="#e8ecf4", size=11)),
            height=340,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_depth, use_container_width=True, key="seipro_pchart2")

    # ================================================================
    # Monthly trend line chart
    # ================================================================
    with col_trend:
        st.markdown(
            f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:12px;">'
            f'Monthly Event Trend (10 Years)</h5>',
            unsafe_allow_html=True,
        )
        if monthly_trend:
            trend_months = [e["month"] for e in monthly_trend]
            trend_counts = [e["count"] for e in monthly_trend]

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_months,
                y=trend_counts,
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=4, color="#f59e0b"),
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.15)",
                name="Events",
            ))
            fig_trend.update_layout(
                paper_bgcolor=_SEISMIC_COLORS["bg"],
                plot_bgcolor=_SEISMIC_COLORS["bg"],
                font=dict(color="#e8ecf4"),
                xaxis=dict(title="Month", gridcolor="#3d1a1a",
                           tickfont=dict(color="#8b97b0", size=9),
                           tickangle=-45),
                yaxis=dict(title="Events", gridcolor="#3d1a1a",
                           tickfont=dict(color="#8b97b0")),
                height=340,
                margin=dict(t=10, b=60, l=50, r=20),
                showlegend=False,
            )
            st.plotly_chart(fig_trend, use_container_width=True, key="seipro_pchart3")
        else:
            st.info("No historical trend data available.")

    # ================================================================
    # Recent significant events table
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:18px;">'
        f'Recent Significant Events (Top 10)</h5>',
        unsafe_allow_html=True,
    )
    if recent_events:
        header = (
            '<div style="display:grid;grid-template-columns:0.8fr 2fr 1.2fr 0.8fr 0.8fr;'
            'gap:4px;padding:8px 12px;background:#2a1a1a;border-radius:8px 8px 0 0;'
            'font-size:11px;color:#8b97b0;font-weight:600;">'
            '<span>Mag</span><span>Place</span><span>Time (UTC)</span>'
            '<span>Depth</span><span>Dist.</span></div>'
        )
        rows = ""
        for ev in recent_events:
            mag = ev["magnitude"]
            if mag >= 5:
                mc = _SEISMIC_COLORS["high"]
            elif mag >= 3:
                mc = _SEISMIC_COLORS["moderate"]
            else:
                mc = _SEISMIC_COLORS["low"]
            depth_str = f'{ev["depth_km"]} km' if ev["depth_km"] is not None else "N/A"
            dist_str = f'{ev["distance_km"]} km' if ev["distance_km"] is not None else "N/A"
            rows += (
                f'<div style="display:grid;grid-template-columns:0.8fr 2fr 1.2fr 0.8fr 0.8fr;'
                f'gap:4px;padding:6px 12px;border-bottom:1px solid #2a1a1a;font-size:12px;">'
                f'<span style="color:{mc};font-weight:bold;">M{mag:.1f}</span>'
                f'<span style="color:{_SEISMIC_COLORS["text"]};white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;">{html_module.escape(str(ev["place"]))}</span>'
                f'<span style="color:{_SEISMIC_COLORS["muted"]};">{ev["time"]}</span>'
                f'<span style="color:{_SEISMIC_COLORS["muted"]};">{depth_str}</span>'
                f'<span style="color:{_SEISMIC_COLORS["muted"]};">{dist_str}</span></div>'
            )
        st.markdown(
            f'<div style="background:{_SEISMIC_COLORS["card"]};border:1px solid '
            f'{_SEISMIC_COLORS["border"]};border-radius:10px;overflow:hidden;">'
            f'{header}{rows}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No recent earthquakes found in this area.")

    # ================================================================
    # Ground stability section
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:18px;">'
        f'Ground Stability Assessment</h5>',
        unsafe_allow_html=True,
    )

    ground_colors = {
        "Rock": _SEISMIC_COLORS["low"],
        "Stiff Soil": "#84cc16",
        "Soft Soil": _SEISMIC_COLORS["moderate"],
        "Liquefiable": _SEISMIC_COLORS["high"],
        "Unknown": _SEISMIC_COLORS["muted"],
    }
    gc_color = ground_colors.get(ground_class, _SEISMIC_COLORS["muted"])

    nearest_html = ""
    if nearest_sig is not None:
        nearest_html = (
            f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;">'
            f'Nearest significant event: M{nearest_sig["magnitude"]:.1f} at '
            f'{nearest_sig["distance_km"]} km ({html_module.escape(str(nearest_sig["place"]))})</span>'
        )

    st.markdown(
        f'<div style="background:{_SEISMIC_COLORS["card"]};border:1px solid '
        f'{_SEISMIC_COLORS["border"]};border-radius:12px;padding:16px 22px;'
        f'margin:8px 0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'flex-wrap:wrap;gap:12px;">'
        f'<div>'
        f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;">'
        f'Ground Classification</span><br/>'
        f'<span style="color:{gc_color};font-size:24px;font-weight:bold;">'
        f'{ground_class}</span></div>'
        f'<div>'
        f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;">'
        f'Site Amplification Factor</span><br/>'
        f'<span style="color:{_SEISMIC_COLORS["text"]};font-size:24px;font-weight:bold;">'
        f'{amp:.1f}x</span></div>'
        f'<div>'
        f'<span style="color:{_SEISMIC_COLORS["muted"]};font-size:12px;">'
        f'Elevation</span><br/>'
        f'<span style="color:{_SEISMIC_COLORS["text"]};font-size:24px;font-weight:bold;">'
        f'{data["elevation"]:.0f} m</span></div>'
        f'</div>'
        f'<div style="margin-top:10px;">{nearest_html}</div></div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # Recommendations
    # ================================================================
    st.markdown(
        f'<h5 style="color:{_SEISMIC_COLORS["accent2"]};margin-top:18px;">'
        f'Recommendations</h5>',
        unsafe_allow_html=True,
    )
    priority_colors = {
        "high": "#dc2626",
        "medium": "#f59e0b",
        "info": "#22c55e",
    }
    for rec in recs:
        pc = priority_colors.get(rec.get("priority", "info"), "#22c55e")
        st.markdown(
            f'<div style="background:{_SEISMIC_COLORS["card"]};border-left:4px solid {pc};'
            f'border-radius:8px;padding:12px 16px;margin-bottom:8px;">'
            f'<span style="color:{pc};font-weight:bold;font-size:13px;">'
            f'{rec["title"]}</span><br/>'
            f'<span style="color:{_SEISMIC_COLORS["text"]};font-size:12px;">'
            f'{rec["text"]}</span></div>',
            unsafe_allow_html=True,
        )
