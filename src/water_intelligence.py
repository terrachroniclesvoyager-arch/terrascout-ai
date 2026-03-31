"""
Water Intelligence AI — Comprehensive water resource analysis: surface water
mapping, groundwater potential, water quality indicators, drought risk,
and watershed characterization.
Uses: Overpass, Open Topo Data, Open-Meteo, ISRIC SoilGrids.
"""

import math
import logging

import numpy as np
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
)
from src.map_factory import MapFactory
from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

WATER_TYPES = {
    "river": {"name": "River", "color": "#3b82f6", "icon": "water"},
    "stream": {"name": "Stream", "color": "#60a5fa", "icon": "water_drop"},
    "canal": {"name": "Canal", "color": "#2563eb", "icon": "waves"},
    "lake": {"name": "Lake", "color": "#1d4ed8", "icon": "pool"},
    "spring": {"name": "Spring", "color": "#06b6d4", "icon": "local_drink"},
    "well": {"name": "Well", "color": "#0891b2", "icon": "water_pump"},
    "wetland": {"name": "Wetland", "color": "#059669", "icon": "grass"},
    "reservoir": {"name": "Reservoir", "color": "#7c3aed", "icon": "water"},
}


@st.cache_data(ttl=1800)
def analyze_water(lat: float, lon: float) -> dict:
    """Comprehensive water resource analysis."""
    water = fetch_water_features(lat, lon, radius=8000) or {}
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6) or {}

    elements = water.get("elements", []) if isinstance(water, dict) else []

    # ── Classify water features ──
    features = {k: [] for k in WATER_TYPES}
    for e in elements:
        tags = e.get("tags", {})
        etype = e.get("type", "")
        elat = e.get("lat") or (e.get("center", {}) or {}).get("lat")
        elon = e.get("lon") or (e.get("center", {}) or {}).get("lon")

        if tags.get("natural") == "spring":
            features["spring"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Spring"), "tags": tags})
        elif tags.get("man_made") == "water_well":
            features["well"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Well"), "tags": tags})
        elif tags.get("natural") == "water":
            wtype = tags.get("water", "")
            if wtype == "reservoir":
                features["reservoir"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Reservoir"), "tags": tags})
            else:
                features["lake"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Water Body"), "tags": tags})
        elif tags.get("natural") == "wetland":
            features["wetland"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Wetland"), "tags": tags})
        elif tags.get("waterway") == "river":
            features["river"].append({"lat": elat, "lon": elon, "name": tags.get("name", "River"), "tags": tags})
        elif tags.get("waterway") in ("stream", "ditch", "drain"):
            features["stream"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Stream"), "tags": tags})
        elif tags.get("waterway") == "canal":
            features["canal"].append({"lat": elat, "lon": elon, "name": tags.get("name", "Canal"), "tags": tags})

    # ── Water abundance score ──
    total = sum(len(v) for v in features.values())
    abundance = min(10, total / 3)

    # ── Groundwater potential ──
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    sand = _sv("sand") or 40
    clay = _sv("clay") or 20
    soc = _sv("soc") or 10

    spring_count = len(features["spring"])
    well_count = len(features["well"])

    gw_score = 0
    gw_indicators = []

    if sand > 50:
        gw_score += 3
        gw_indicators.append(f"Sandy soil ({sand:.0f}%): good permeability")
    elif clay > 40:
        gw_indicators.append(f"Clay-rich soil ({clay:.0f}%): poor permeability")
    else:
        gw_score += 1.5
        gw_indicators.append(f"Mixed soil: moderate permeability")

    if spring_count > 0:
        gw_score += min(4, spring_count * 2)
        gw_indicators.append(f"{spring_count} natural springs: active groundwater discharge")

    if well_count > 0:
        gw_score += min(3, well_count * 1.5)
        gw_indicators.append(f"{well_count} wells: confirmed groundwater access")

    # Precipitation contribution
    daily = weather.get("daily", {})
    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0
    annual_est = total_precip * (365 / max(len(valid_precip), 1)) if valid_precip else 500

    if annual_est > 800:
        gw_score += 2
        gw_indicators.append(f"High precipitation (~{annual_est:.0f}mm/yr): good recharge")
    elif annual_est < 300:
        gw_indicators.append(f"Low precipitation (~{annual_est:.0f}mm/yr): limited recharge")
    else:
        gw_score += 1
        gw_indicators.append(f"Moderate precipitation (~{annual_est:.0f}mm/yr)")

    gw_score = min(10, gw_score)

    # ── Drought risk ──
    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_high = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 25
    humidity = weather.get("current", {}).get("relative_humidity_2m", 50) or 50

    drought_score = 0
    if annual_est < 400:
        drought_score += 4
    elif annual_est < 600:
        drought_score += 2
    if avg_high > 30:
        drought_score += 2
    if humidity < 30:
        drought_score += 2
    if total == 0:
        drought_score += 2
    drought_score = min(10, drought_score)

    # ── Water quality indicators ──
    quality_indicators = []
    if soc and soc > 20:
        quality_indicators.append({"factor": "Organic Content", "status": "high",
                                    "detail": f"SOC {soc:.1f} g/kg — may affect water taste/color"})
    if clay and clay > 40:
        quality_indicators.append({"factor": "Turbidity Risk", "status": "elevated",
                                    "detail": f"High clay ({clay:.0f}%) increases sediment in surface water"})
    if len(features["wetland"]) > 0:
        quality_indicators.append({"factor": "Natural Filtration", "status": "good",
                                    "detail": "Wetlands present — natural water purification system"})

    # ── Watershed characterization ──
    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 0

    watershed = {
        "elevation": round(avg_elev, 0),
        "relief": round(elev_range, 0),
        "drainage_density": min(10, (len(features["river"]) + len(features["stream"])) / 2),
        "water_body_count": len(features["lake"]) + len(features["reservoir"]),
    }

    return {
        "features": {k: len(v) for k, v in features.items()},
        "feature_details": features,
        "total_features": total,
        "abundance_score": round(abundance, 1),
        "groundwater": {
            "score": round(gw_score, 1),
            "indicators": gw_indicators,
        },
        "drought_risk": round(drought_score, 1),
        "quality": quality_indicators,
        "watershed": watershed,
        "precipitation_annual": round(annual_est, 0),
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_water_intelligence_tab():
    """Render the Water Intelligence AI tab."""
    st.markdown("## Water Intelligence AI")
    st.caption("Comprehensive water resource analysis with groundwater assessment")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="wi_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="wi_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="wi_lon", format="%.4f")

    if st.button("Analyze Water Resources", type="primary", use_container_width=True):
        with st.spinner("Scanning water resources..."):
            result = analyze_water(lat, lon)

        if not result:
            st.error("Failed to analyze water resources.")
            return

        # ── Header gauges ──
        abund = result["abundance_score"]
        gw = result["groundwater"]["score"]
        drought = result["drought_risk"]

        col_a, col_b, col_c = st.columns(3)

        def _gauge_html(value, label, color):
            return f"""
            <div style="text-align:center; background:#1a1a2e; border-radius:10px;
                        padding:15px; border:1px solid {color}44;">
                <div style="font-size:36px; font-weight:bold; color:{color};">
                    {value}<span style="font-size:14px; color:#888;">/10</span>
                </div>
                <div style="color:#aaa; font-size:13px; margin-top:4px;">{label}</div>
            </div>
            """

        with col_a:
            st.markdown(_gauge_html(abund, "Water Abundance",
                                      "#10b981" if abund >= 6 else "#f59e0b" if abund >= 3 else "#ef4444"),
                        unsafe_allow_html=True)
        with col_b:
            st.markdown(_gauge_html(gw, "Groundwater Potential",
                                      "#3b82f6" if gw >= 6 else "#f59e0b" if gw >= 3 else "#ef4444"),
                        unsafe_allow_html=True)
        with col_c:
            st.markdown(_gauge_html(drought, "Drought Risk",
                                      "#ef4444" if drought >= 6 else "#f59e0b" if drought >= 3 else "#10b981"),
                        unsafe_allow_html=True)

        # ── Feature breakdown ──
        st.markdown("### Water Feature Inventory")
        feats = result["features"]
        feat_names = []
        feat_counts = []
        feat_colors = []
        for wt_id, info in WATER_TYPES.items():
            count = feats.get(wt_id, 0)
            if count > 0:
                feat_names.append(info["name"])
                feat_counts.append(count)
                feat_colors.append(info["color"])

        if feat_names:
            fig = go.Figure(data=[go.Bar(
                x=feat_names,
                y=feat_counts,
                marker_color=feat_colors,
                text=feat_counts,
                textposition="auto",
            )])
            fig.update_layout(height=300, margin=dict(t=20, b=40))
            st.plotly_chart(fig, use_container_width=True, key="watint_pchart1")
        else:
            st.info("No water features detected in the analysis area.")

        mc = st.columns(4)
        mc[0].metric("Total Features", result["total_features"])
        mc[1].metric("Annual Precip (est)", f"{result['precipitation_annual']}mm")
        mc[2].metric("Watershed Relief", f"{result['watershed']['relief']:.0f}m")
        mc[3].metric("Drainage Density", f"{result['watershed']['drainage_density']:.1f}")

        # ── Groundwater indicators ──
        st.markdown("### Groundwater Assessment")
        for ind in result["groundwater"]["indicators"]:
            st.markdown(f"""
            <div style="background:#3b82f622; border-left:3px solid #3b82f6;
                        border-radius:6px; padding:8px 12px; margin:4px 0;
                        color:#60a5fa; font-size:13px;">
                {ind}
            </div>
            """, unsafe_allow_html=True)

        # ── Water quality ──
        if result["quality"]:
            st.markdown("### Water Quality Indicators")
            for qi in result["quality"]:
                s = qi["status"]
                if s == "good":
                    qc = "#10b981"
                elif s == "elevated":
                    qc = "#f59e0b"
                else:
                    qc = "#ef4444"

                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:3px solid {qc};
                            border-radius:6px; padding:10px 12px; margin:4px 0;">
                    <span style="color:{qc}; font-weight:bold;">{qi['factor']}</span>
                    <span style="color:#888; font-size:11px; margin-left:8px;">[{s.upper()}]</span>
                    <div style="color:#aaa; font-size:13px; margin-top:2px;">{qi['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Water features map ──
        st.markdown("### Water Features Map")
        details = result["feature_details"]
        m = MapFactory.create_base_map(center=(lat, lon), zoom=13)

        for wt_id, items in details.items():
            info = WATER_TYPES.get(wt_id, {})
            for item in items:
                if item.get("lat") and item.get("lon"):
                    folium.CircleMarker(
                        location=[item["lat"], item["lon"]],
                        radius=6,
                        color=info.get("color", "#3b82f6"),
                        fill=True,
                        fill_color=info.get("color", "#3b82f6"),
                        fill_opacity=0.7,
                        popup=f"<b>{item.get('name', wt_id)}</b><br/>{info.get('name', '')}",
                    ).add_to(m)

        st_html(m._repr_html_(), height=450)
