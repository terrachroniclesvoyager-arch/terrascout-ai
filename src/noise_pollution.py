# -*- coding: utf-8 -*-
"""
Noise & Environmental Pollution AI module for TerraScout AI.
Estimates noise pollution levels and environmental disturbance from
infrastructure, land-use, and geographic context using Overpass / Open-Meteo
data plus logarithmic acoustic modelling.
"""

import math
import logging

import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_elevation_grid,
    fetch_water_features,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# NOISE SOURCE CATALOGUE
# ═══════════════════════════════════════════════════════════════════════════════

NOISE_SOURCES = {
    "traffic": {
        "label": "Road Traffic",
        "typical_dB": 75,
        "color": "#ef4444",
        "icon": "car",
        "description": "Highways, primary, secondary and residential roads",
    },
    "industrial": {
        "label": "Industrial",
        "typical_dB": 80,
        "color": "#f97316",
        "icon": "factory",
        "description": "Factories, plants, industrial land-use zones",
    },
    "airports": {
        "label": "Airports / Aeroways",
        "typical_dB": 90,
        "color": "#dc2626",
        "icon": "plane",
        "description": "Airport runways, terminals and aeroways",
    },
    "railways": {
        "label": "Railways",
        "typical_dB": 85,
        "color": "#8b5cf6",
        "icon": "train",
        "description": "Rail tracks, stations and freight lines",
    },
    "construction": {
        "label": "Construction Sites",
        "typical_dB": 88,
        "color": "#f59e0b",
        "icon": "hammer",
        "description": "Active construction and demolition zones",
    },
    "nightlife": {
        "label": "Nightlife / Social",
        "typical_dB": 70,
        "color": "#ec4899",
        "icon": "music",
        "description": "Bars, pubs, nightclubs and entertainment venues",
    },
    "natural": {
        "label": "Natural Quiet",
        "typical_dB": 30,
        "color": "#10b981",
        "icon": "leaf",
        "description": "Forests, water bodies, parks -- natural sound buffers",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(hi, value))


def _log_add_dB(*levels: float) -> float:
    """Logarithmic addition of decibel values (energy summation)."""
    valid = [lv for lv in levels if lv is not None and lv > 0]
    if not valid:
        return 0.0
    total_energy = sum(10 ** (lv / 10.0) for lv in valid)
    return 10.0 * math.log10(total_energy)


def _noise_class(dB: float) -> str:
    if dB < 30:
        return "Silent"
    if dB < 45:
        return "Quiet"
    if dB < 60:
        return "Moderate"
    if dB < 75:
        return "Loud"
    return "Very Loud"


def _class_color(cls: str) -> str:
    return {
        "Silent": "#10b981",
        "Quiet": "#22c55e",
        "Moderate": "#f59e0b",
        "Loud": "#ef4444",
        "Very Loud": "#dc2626",
    }.get(cls, "#64748b")


# ═══════════════════════════════════════════════════════════════════════════════
# CORE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_noise_profile(lat: float, lon: float) -> dict:
    """
    Build a comprehensive noise-pollution profile for the given coordinates.
    Returns estimated dB, noise class, five sub-indices, source breakdown,
    buffer factors and actionable recommendations.
    """
    # ------------------------------------------------------------------
    # 1. Fetch raw data
    # ------------------------------------------------------------------
    infra = fetch_landuse_infrastructure(lat, lon, radius=5000)
    water = fetch_water_features(lat, lon, radius=5000)
    elev = fetch_elevation_grid(lat, lon)
    weather = fetch_weather_data(lat, lon)

    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])

    # ------------------------------------------------------------------
    # 2. Count noise sources
    # ------------------------------------------------------------------
    highway_counts = {"motorway": 0, "trunk": 0, "primary": 0,
                      "secondary": 0, "tertiary": 0, "residential": 0}
    railway_count = 0
    airport_count = 0
    industrial_count = 0
    nightlife_count = 0
    construction_count = 0

    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        hw = tags.get("highway", "")
        if hw in ("motorway", "motorway_link", "trunk", "trunk_link"):
            highway_counts["motorway"] += 1
        elif hw in ("primary", "primary_link"):
            highway_counts["primary"] += 1
        elif hw in ("secondary", "secondary_link"):
            highway_counts["secondary"] += 1
        elif hw in ("tertiary", "tertiary_link"):
            highway_counts["tertiary"] += 1
        elif hw in ("residential", "living_street", "unclassified"):
            highway_counts["residential"] += 1

        if tags.get("railway") in ("rail", "light_rail", "subway", "tram"):
            railway_count += 1

        if tags.get("aeroway") in ("runway", "taxiway", "terminal", "aerodrome"):
            airport_count += 1

        landuse = tags.get("landuse", "")
        if landuse == "industrial":
            industrial_count += 1
        if landuse == "construction":
            construction_count += 1

        amenity = tags.get("amenity", "")
        if amenity in ("bar", "pub", "nightclub", "biergarten", "casino"):
            nightlife_count += 1

    # ------------------------------------------------------------------
    # 3. Count noise buffers
    # ------------------------------------------------------------------
    forest_count = 0
    park_count = 0
    water_count = len(water_elements)

    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        lu = tags.get("landuse", "")
        leisure = tags.get("leisure", "")
        natural = tags.get("natural", "")
        if lu == "forest" or natural == "wood":
            forest_count += 1
        if leisure == "park" or leisure == "garden":
            park_count += 1

    # Elevation variance as potential barrier
    elev_data = (elev if isinstance(elev, dict) else {}).get("results", [])
    elevations = [r.get("elevation") for r in elev_data
                  if isinstance(r, dict) and r.get("elevation") is not None]
    elev_range = (max(elevations) - min(elevations)) if elevations else 0.0

    # Wind speed can disperse or carry sound
    current_weather = (weather if isinstance(weather, dict) else {}).get("current", {})
    wind_speed = current_weather.get("wind_speed_10m", 0) if isinstance(current_weather, dict) else 0

    # ------------------------------------------------------------------
    # 4. Compute dB contributions per category
    # ------------------------------------------------------------------
    traffic_dB = (highway_counts["motorway"] * 8.0
                  + highway_counts["primary"] * 5.0
                  + highway_counts["secondary"] * 3.0
                  + highway_counts["tertiary"] * 2.0
                  + highway_counts["residential"] * 1.0)
    industrial_dB = industrial_count * 6.0
    transport_dB = airport_count * 15.0 + railway_count * 7.0
    social_dB = nightlife_count * 3.0
    construction_dB = construction_count * 8.0

    # Cap individual categories at a reasonable ceiling
    traffic_dB = min(traffic_dB, 90.0)
    industrial_dB = min(industrial_dB, 85.0)
    transport_dB = min(transport_dB, 95.0)
    social_dB = min(social_dB, 75.0)
    construction_dB = min(construction_dB, 90.0)

    # Baseline ambient (rural ~ 30 dB)
    baseline_dB = 30.0

    # Logarithmic summation of all sources
    composite_dB = _log_add_dB(baseline_dB, traffic_dB, industrial_dB,
                               transport_dB, social_dB, construction_dB)

    # ------------------------------------------------------------------
    # 5. Apply buffer attenuation
    # ------------------------------------------------------------------
    buffer_reduction = 0.0
    buffer_reduction += min(forest_count * 1.5, 8.0)   # forests absorb ~3-8 dB
    buffer_reduction += min(park_count * 0.8, 4.0)      # parks provide mild buffer
    buffer_reduction += min(water_count * 0.5, 3.0)     # water masks noise
    buffer_reduction += min(elev_range * 0.02, 3.0)     # terrain shielding

    estimated_dB = max(composite_dB - buffer_reduction, 20.0)
    noise_cls = _noise_class(estimated_dB)

    # ------------------------------------------------------------------
    # 6. Five pollution indices (0-100)
    # ------------------------------------------------------------------
    traffic_index = _clamp(traffic_dB * 1.1)
    industrial_index = _clamp(industrial_dB * 1.2)
    transport_index = _clamp(transport_dB * 1.05)
    social_index = _clamp(social_dB * 1.3)
    # Natural quiet: higher = quieter = better
    raw_quiet = (forest_count * 5 + water_count * 4 + park_count * 3
                 + max(0, 50 - estimated_dB))
    natural_quiet_index = _clamp(raw_quiet, 0.0, 100.0)

    indices = {
        "Traffic Noise": round(traffic_index, 1),
        "Industrial Noise": round(industrial_index, 1),
        "Transport Noise": round(transport_index, 1),
        "Social Noise": round(social_index, 1),
        "Natural Quiet": round(natural_quiet_index, 1),
    }

    # ------------------------------------------------------------------
    # 7. Source breakdown (for pie chart)
    # ------------------------------------------------------------------
    source_breakdown = {}
    if traffic_dB > 0:
        source_breakdown["Road Traffic"] = round(traffic_dB, 1)
    if industrial_dB > 0:
        source_breakdown["Industrial"] = round(industrial_dB, 1)
    if transport_dB > 0:
        source_breakdown["Airports & Railways"] = round(transport_dB, 1)
    if social_dB > 0:
        source_breakdown["Nightlife / Social"] = round(social_dB, 1)
    if construction_dB > 0:
        source_breakdown["Construction"] = round(construction_dB, 1)
    if not source_breakdown:
        source_breakdown["Ambient"] = baseline_dB

    # ------------------------------------------------------------------
    # 8. Buffer factors summary
    # ------------------------------------------------------------------
    buffer_factors = {
        "Forests": {"count": forest_count, "reduction_dB": round(min(forest_count * 1.5, 8.0), 1)},
        "Parks": {"count": park_count, "reduction_dB": round(min(park_count * 0.8, 4.0), 1)},
        "Water Bodies": {"count": water_count, "reduction_dB": round(min(water_count * 0.5, 3.0), 1)},
        "Elevation Barrier": {"range_m": round(elev_range, 1), "reduction_dB": round(min(elev_range * 0.02, 3.0), 1)},
    }

    # ------------------------------------------------------------------
    # 9. Recommendations
    # ------------------------------------------------------------------
    recommendations = []
    if estimated_dB >= 70:
        recommendations.append("Hearing protection is advisable for prolonged exposure in this area.")
    if traffic_index > 60:
        recommendations.append("Significant road-traffic noise -- consider noise barriers or sound-insulated buildings.")
    if industrial_index > 50:
        recommendations.append("Industrial activity is a major noise contributor; enforce zoning buffer distances.")
    if transport_index > 50:
        recommendations.append("Airport or railway proximity drives high transport noise; sound-proofing recommended.")
    if social_index > 40:
        recommendations.append("Nightlife venues contribute notable noise; regulate operating hours if residential nearby.")
    if natural_quiet_index < 20:
        recommendations.append("Very low natural quiet -- increase green spaces and tree cover as acoustic buffers.")
    if not recommendations:
        recommendations.append("Noise levels appear acceptable. Maintain existing green buffers and land-use balance.")
    if wind_speed and wind_speed > 20:
        recommendations.append(f"High wind speed ({wind_speed} km/h) may carry noise further than usual.")

    return {
        "estimated_dB": round(estimated_dB, 1),
        "noise_class": noise_cls,
        "indices": indices,
        "source_breakdown": source_breakdown,
        "buffer_factors": buffer_factors,
        "recommendations": recommendations,
        "raw_counts": {
            "highways": dict(highway_counts),
            "railways": railway_count,
            "airports": airport_count,
            "industrial": industrial_count,
            "nightlife": nightlife_count,
            "construction": construction_count,
            "forests": forest_count,
            "parks": park_count,
            "water_bodies": water_count,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════════════════════════════════════

def render_noise_pollution_tab() -> None:
    """Render the full Noise & Environmental Pollution analysis tab."""

    st.markdown(
        "<h2 style='text-align:center;color:#e0e0e0;'>"
        "Noise &amp; Environmental Pollution AI</h2>"
        "<p style='text-align:center;color:#aaa;'>"
        "Estimate noise pollution from infrastructure, land-use and natural buffers"
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Location selector ────────────────────────────────────────────────
    preset_names = list(ANALYSIS_PRESETS.keys())
    preset = st.selectbox("Location Preset", preset_names,
                          index=0, key="noise_preset")

    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude", value=default_lat,
                              format="%.4f", key="noise_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=default_lon,
                              format="%.4f", key="noise_lon")

    if not st.button("Analyze Noise Profile", type="primary",
                     key="noise_analyze_btn"):
        st.info("Select a location and press **Analyze Noise Profile** to begin.")
        return

    with st.spinner("Fetching infrastructure & computing noise profile..."):
        profile = compute_noise_profile(lat, lon)

    estimated_dB = profile["estimated_dB"]
    noise_cls = profile["noise_class"]
    indices = profile["indices"]
    source_breakdown = profile["source_breakdown"]
    buffer_factors = profile["buffer_factors"]
    recommendations = profile["recommendations"]

    cls_color = _class_color(noise_cls)

    # ── Estimated dB header ──────────────────────────────────────────────
    st.markdown(
        f"<div style='text-align:center;padding:18px;background:#1a1a2e;"
        f"border-radius:12px;margin-bottom:16px;'>"
        f"<span style='font-size:3rem;font-weight:700;color:{cls_color};'>"
        f"{estimated_dB} dB</span><br>"
        f"<span style='font-size:1.3rem;color:{cls_color};'>{noise_cls}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── dB gauge chart ───────────────────────────────────────────────────
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=estimated_dB,
        number={"suffix": " dB", "font": {"size": 36, "color": "#e0e0e0"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#555",
                     "dtick": 10},
            "bar": {"color": cls_color},
            "bgcolor": "#1a1a2e",
            "steps": [
                {"range": [0, 30], "color": "#064e3b"},
                {"range": [30, 45], "color": "#065f46"},
                {"range": [45, 60], "color": "#78350f"},
                {"range": [60, 75], "color": "#7c2d12"},
                {"range": [75, 100], "color": "#7f1d1d"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 3},
                "thickness": 0.8,
                "value": estimated_dB,
            },
        },
        title={"text": "Estimated Noise Level", "font": {"size": 16, "color": "#aaa"}},
    ))
    gauge.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font={"color": "#e0e0e0"}, height=280, margin=dict(t=50, b=10, l=30, r=30),
    )
    st.plotly_chart(gauge, use_container_width=True, key="noipol_pchart1")

    # ── Five index cards ─────────────────────────────────────────────────
    st.subheader("Pollution Indices")
    idx_cols = st.columns(5)
    idx_colors = ["#ef4444", "#f97316", "#8b5cf6", "#ec4899", "#10b981"]
    for i, (idx_name, idx_val) in enumerate(indices.items()):
        with idx_cols[i]:
            col_c = idx_colors[i % len(idx_colors)]
            label_extra = "(higher = quieter)" if idx_name == "Natural Quiet" else "(lower = quieter)"
            st.markdown(
                f"<div style='background:#1a1a2e;border-left:4px solid {col_c};"
                f"padding:12px;border-radius:8px;text-align:center;'>"
                f"<div style='color:#aaa;font-size:0.8rem;'>{idx_name}</div>"
                f"<div style='font-size:1.6rem;font-weight:700;color:{col_c};'>"
                f"{idx_val}</div>"
                f"<div style='color:#666;font-size:0.65rem;'>{label_extra}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Source breakdown pie chart ────────────────────────────────────────
    st.subheader("Noise Source Breakdown")
    src_labels = list(source_breakdown.keys())
    src_values = list(source_breakdown.values())
    src_colors = ["#ef4444", "#f97316", "#8b5cf6", "#ec4899", "#f59e0b", "#64748b"]
    pie = go.Figure(go.Pie(
        labels=src_labels,
        values=src_values,
        hole=0.45,
        marker=dict(colors=src_colors[:len(src_labels)]),
        textinfo="label+percent",
        textfont=dict(color="#e0e0e0"),
    ))
    pie.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"), height=350,
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(font=dict(color="#ccc")),
    )
    st.plotly_chart(pie, use_container_width=True, key="noipol_pchart2")

    # ── Horizontal bar: noise sources (dB contribution) ──────────────────
    st.subheader("Source dB Contributions")
    bar_labels = list(source_breakdown.keys())
    bar_vals = list(source_breakdown.values())
    bar_colors_map = {
        "Road Traffic": "#ef4444",
        "Industrial": "#f97316",
        "Airports & Railways": "#8b5cf6",
        "Nightlife / Social": "#ec4899",
        "Construction": "#f59e0b",
        "Ambient": "#10b981",
    }
    bar_c = [bar_colors_map.get(lb, "#64748b") for lb in bar_labels]
    hbar = go.Figure(go.Bar(
        x=bar_vals,
        y=bar_labels,
        orientation="h",
        marker=dict(color=bar_c),
        text=[f"{v} dB" for v in bar_vals],
        textposition="auto",
        textfont=dict(color="#e0e0e0"),
    ))
    hbar.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        xaxis=dict(title="Estimated dB Contribution",
                   gridcolor="#333", color="#aaa"),
        yaxis=dict(color="#aaa"),
        font=dict(color="#e0e0e0"), height=300,
        margin=dict(t=20, b=40, l=140, r=20),
    )
    st.plotly_chart(hbar, use_container_width=True, key="noipol_pchart3")

    # ── Buffer factors section ───────────────────────────────────────────
    st.subheader("Noise Buffers (what reduces noise)")
    buf_cols = st.columns(len(buffer_factors))
    buf_icons = {"Forests": "trees", "Parks": "park", "Water Bodies": "water",
                 "Elevation Barrier": "mountain"}
    for i, (buf_name, buf_info) in enumerate(buffer_factors.items()):
        with buf_cols[i]:
            count_str = ""
            if "count" in buf_info:
                count_str = f"<div style='color:#aaa;font-size:0.8rem;'>Count: {buf_info['count']}</div>"
            elif "range_m" in buf_info:
                count_str = f"<div style='color:#aaa;font-size:0.8rem;'>Range: {buf_info['range_m']} m</div>"
            reduction = buf_info.get("reduction_dB", 0)
            r_color = "#10b981" if reduction > 0 else "#64748b"
            st.markdown(
                f"<div style='background:#1a1a2e;border:1px solid #333;"
                f"padding:12px;border-radius:8px;text-align:center;'>"
                f"<div style='font-weight:600;color:#e0e0e0;'>{buf_name}</div>"
                f"{count_str}"
                f"<div style='font-size:1.3rem;font-weight:700;color:{r_color};'>"
                f"-{reduction} dB</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Recommendations ──────────────────────────────────────────────────
    st.subheader("Recommendations")
    for rec in recommendations:
        st.markdown(
            f"<div style='background:#1a1a2e;border-left:4px solid #3b82f6;"
            f"padding:10px 14px;border-radius:6px;margin-bottom:8px;"
            f"color:#e0e0e0;'>{rec}</div>",
            unsafe_allow_html=True,
        )
