"""
Geospatial Pattern Recognizer AI — Detects spatial patterns across multiple
data dimensions: elevation, water, urban, geological, soil.
Generates AI insight narratives with confidence scores.
Uses: Open Topo Data, Overpass, ISRIC SoilGrids, Open-Meteo, USGS, Macrostrat.
"""

import math
import logging
from collections import Counter

import numpy as np
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_earthquakes,
    fetch_geology,
)
from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ── Pattern definitions ─────────────────────────────────────────────────────

PATTERN_TYPES = {
    "terrain": {"name": "Terrain Morphology", "color": "#8b5cf6", "icon": "terrain"},
    "hydro": {"name": "Hydrological Network", "color": "#3b82f6", "icon": "water_drop"},
    "urban": {"name": "Urban Development", "color": "#f59e0b", "icon": "location_city"},
    "geological": {"name": "Geological Structure", "color": "#ef4444", "icon": "layers"},
    "ecological": {"name": "Ecological Zone", "color": "#10b981", "icon": "forest"},
    "soil": {"name": "Soil Composition", "color": "#f97316", "icon": "grass"},
}


@st.cache_data(ttl=1800)
def _detect_terrain_patterns(lat: float, lon: float) -> list:
    """Analyze elevation grid for terrain patterns."""
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=7)
    if not elev or not isinstance(elev, dict):
        return []

    elevations = [e for e in elev.get("grid_elevations", []) if e is not None]
    if len(elevations) < 4:
        return []

    patterns = []
    elev_min = min(elevations)
    elev_max = max(elevations)
    elev_range = elev_max - elev_min
    elev_mean = sum(elevations) / len(elevations)
    elev_std = (sum((e - elev_mean) ** 2 for e in elevations) / len(elevations)) ** 0.5

    # Flat terrain
    if elev_range < 20:
        patterns.append({
            "type": "terrain",
            "pattern": "Flat Plain",
            "confidence": min(95, 95 - elev_range * 2),
            "detail": f"Elevation range only {elev_range:.0f}m across analysis grid. "
                      f"Mean elevation {elev_mean:.0f}m. Indicates plain, plateau, or valley floor.",
            "significance": "high",
        })
    # Mountainous
    elif elev_range > 500:
        patterns.append({
            "type": "terrain",
            "pattern": "Mountainous Terrain",
            "confidence": min(95, 50 + elev_range / 20),
            "detail": f"Dramatic elevation change of {elev_range:.0f}m detected. "
                      f"Range: {elev_min:.0f}m to {elev_max:.0f}m. Complex mountain morphology.",
            "significance": "high",
        })
    # Hilly
    elif elev_range > 100:
        patterns.append({
            "type": "terrain",
            "pattern": "Rolling Hills",
            "confidence": 80,
            "detail": f"Moderate elevation variation of {elev_range:.0f}m. "
                      f"Typical of hilly terrain or dissected plateau.",
            "significance": "medium",
        })

    # Slope analysis
    if elev_std > 50:
        patterns.append({
            "type": "terrain",
            "pattern": "High Slope Variability",
            "confidence": min(90, 50 + elev_std / 2),
            "detail": f"Standard deviation of {elev_std:.1f}m indicates significant "
                      f"slope variation. Watch for erosion and instability.",
            "significance": "medium",
        })

    # Depression detection (center lower than edges)
    center_idx = len(elevations) // 2
    if center_idx < len(elevations):
        center_elev = elevations[center_idx]
        edge_avg = (sum(elevations[:3]) + sum(elevations[-3:])) / min(6, len(elevations))
        if center_elev < edge_avg - 30:
            patterns.append({
                "type": "terrain",
                "pattern": "Topographic Depression",
                "confidence": 75,
                "detail": f"Center elevation ({center_elev:.0f}m) is {edge_avg - center_elev:.0f}m below "
                          f"surrounding terrain. Possible valley, basin, or crater.",
                "significance": "high",
            })

    return patterns


@st.cache_data(ttl=1800)
def _detect_hydro_patterns(lat: float, lon: float) -> list:
    """Analyze water features for hydrological patterns."""
    water = fetch_water_features(lat, lon, radius=5000) or {}
    elements = water.get("elements", []) if isinstance(water, dict) else []
    if not elements:
        return [{
            "type": "hydro",
            "pattern": "Arid / Low Water",
            "confidence": 70,
            "detail": "No significant water features detected within 5km radius. "
                      "Indicates arid conditions or deep water table.",
            "significance": "medium",
        }]

    patterns = []
    rivers = sum(1 for e in elements if e.get("tags", {}).get("waterway") in ("river", "canal"))
    streams = sum(1 for e in elements if e.get("tags", {}).get("waterway") in ("stream", "ditch", "drain"))
    lakes = sum(1 for e in elements if e.get("tags", {}).get("natural") == "water")
    springs = sum(1 for e in elements if e.get("tags", {}).get("natural") == "spring")
    wetlands = sum(1 for e in elements if e.get("tags", {}).get("natural") == "wetland")

    total_water = rivers + streams + lakes + springs + wetlands

    if total_water > 15:
        patterns.append({
            "type": "hydro",
            "pattern": "Dense Hydrological Network",
            "confidence": 90,
            "detail": f"Highly water-rich area: {rivers} rivers, {streams} streams, "
                      f"{lakes} lakes, {springs} springs. Dense drainage network.",
            "significance": "high",
        })
    elif total_water > 5:
        patterns.append({
            "type": "hydro",
            "pattern": "Moderate Water Network",
            "confidence": 80,
            "detail": f"Well-watered area: {rivers} rivers, {streams} streams, {lakes} water bodies.",
            "significance": "medium",
        })

    if wetlands > 0:
        patterns.append({
            "type": "hydro",
            "pattern": "Wetland Ecosystem",
            "confidence": 85,
            "detail": f"{wetlands} wetland areas detected. Indicates high water table, "
                      f"flood plain, or marshy terrain.",
            "significance": "high",
        })

    if springs > 2:
        patterns.append({
            "type": "hydro",
            "pattern": "Spring-Fed System",
            "confidence": 80,
            "detail": f"{springs} natural springs detected. Indicates active groundwater "
                      f"discharge zone with reliable water supply.",
            "significance": "high",
        })

    return patterns


@st.cache_data(ttl=1800)
def _detect_urban_patterns(lat: float, lon: float) -> list:
    """Analyze infrastructure for urban patterns."""
    infra = fetch_landuse_infrastructure(lat, lon, radius=3000) or {}
    elements = infra.get("elements", []) if isinstance(infra, dict) else []
    if not elements:
        return [{
            "type": "urban",
            "pattern": "Undeveloped / Rural",
            "confidence": 75,
            "detail": "Minimal infrastructure detected. Area appears rural or uninhabited.",
            "significance": "medium",
        }]

    patterns = []
    tags_counter = Counter()
    for e in elements:
        tags = e.get("tags", {})
        for key in ("landuse", "building", "amenity", "highway"):
            val = tags.get(key)
            if val:
                tags_counter[f"{key}={val}"] += 1

    buildings = sum(v for k, v in tags_counter.items() if k.startswith("building="))
    roads = sum(v for k, v in tags_counter.items() if k.startswith("highway="))
    amenities = sum(v for k, v in tags_counter.items() if k.startswith("amenity="))

    if buildings > 50:
        patterns.append({
            "type": "urban",
            "pattern": "Dense Urban Area",
            "confidence": 90,
            "detail": f"{buildings} buildings, {roads} road segments, {amenities} amenities. "
                      f"Indicates developed urban or suburban zone.",
            "significance": "high",
        })
    elif buildings > 10:
        patterns.append({
            "type": "urban",
            "pattern": "Suburban / Village",
            "confidence": 80,
            "detail": f"{buildings} buildings detected. Small settlement or suburban area.",
            "significance": "medium",
        })

    industrial = sum(v for k, v in tags_counter.items() if "industrial" in k)
    if industrial > 3:
        patterns.append({
            "type": "urban",
            "pattern": "Industrial Zone",
            "confidence": 85,
            "detail": f"{industrial} industrial features detected. Area has significant "
                      f"industrial activity.",
            "significance": "high",
        })

    farmland = sum(v for k, v in tags_counter.items() if "farm" in k or "orchard" in k or "vineyard" in k)
    if farmland > 3:
        patterns.append({
            "type": "urban",
            "pattern": "Agricultural Zone",
            "confidence": 85,
            "detail": f"{farmland} agricultural features (farms, orchards, vineyards).",
            "significance": "medium",
        })

    return patterns


@st.cache_data(ttl=1800)
def _detect_geological_patterns(lat: float, lon: float) -> list:
    """Analyze geological structure."""
    geo = fetch_geology(lat, lon) or {}
    eq = fetch_earthquakes(lat, lon, radius_km=100, days=365) or {}
    patterns = []

    # Geological units
    units = geo.get("success", {}).get("data", []) if isinstance(geo, dict) else []
    if units:
        liths = [u.get("lith", "unknown") for u in units[:5]]
        ages = [u.get("t_age", "") for u in units[:5] if u.get("t_age")]
        types = set(u.get("lith_type", "") for u in units[:5])

        patterns.append({
            "type": "geological",
            "pattern": f"Geological Formation: {liths[0] if liths else 'Unknown'}",
            "confidence": 85,
            "detail": f"Lithologies: {', '.join(set(liths))}. "
                      f"Ages: {', '.join(set(ages[:3]))}. "
                      f"Types: {', '.join(t for t in types if t)}.",
            "significance": "high",
        })

        volcanic = any("volcan" in l.lower() for l in liths)
        if volcanic:
            patterns.append({
                "type": "geological",
                "pattern": "Volcanic Province",
                "confidence": 90,
                "detail": "Volcanic lithology detected. Area is in or near volcanic formation.",
                "significance": "high",
            })

        sedimentary = any(t.lower() in ("sedimentary", "clastic") for t in types)
        if sedimentary:
            patterns.append({
                "type": "geological",
                "pattern": "Sedimentary Basin",
                "confidence": 80,
                "detail": "Sedimentary rock formations. Possible fossil deposits, "
                          "aquifer, or resource deposits.",
                "significance": "medium",
            })

    # Seismic patterns
    features = eq.get("features", [])
    if len(features) > 20:
        mags = [f["properties"].get("mag", 0) or 0 for f in features]
        patterns.append({
            "type": "geological",
            "pattern": "Seismically Active Zone",
            "confidence": 90,
            "detail": f"{len(features)} earthquakes in 1 year, max magnitude {max(mags):.1f}. "
                      f"Active tectonic region.",
            "significance": "high",
        })
    elif len(features) > 5:
        patterns.append({
            "type": "geological",
            "pattern": "Moderate Seismic Activity",
            "confidence": 75,
            "detail": f"{len(features)} earthquakes recorded in past year.",
            "significance": "medium",
        })

    return patterns


@st.cache_data(ttl=1800)
def _detect_soil_patterns(lat: float, lon: float) -> list:
    """Analyze soil composition patterns."""
    soil = fetch_soil_data(lat, lon) or {}
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}
    patterns = []

    def _get_surface(prop_name):
        prop = props.get(prop_name, {})
        if isinstance(prop, dict):
            depths = prop.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / 10
        return None

    clay = _get_surface("clay")
    sand = _get_surface("sand")
    soc = _get_surface("soc")
    ph = _get_surface("phh2o")

    if clay is not None and sand is not None:
        if clay > 40:
            patterns.append({
                "type": "soil",
                "pattern": "Clay-Dominant Soil",
                "confidence": 85,
                "detail": f"Clay content {clay:.0f}%. Heavy, water-retentive soil. "
                          f"Risk of waterlogging and slow drainage.",
                "significance": "medium",
            })
        elif sand > 60:
            patterns.append({
                "type": "soil",
                "pattern": "Sandy Soil",
                "confidence": 85,
                "detail": f"Sand content {sand:.0f}%. Well-drained but low water retention. "
                          f"Poor nutrient holding capacity.",
                "significance": "medium",
            })
        elif 20 <= clay <= 35 and 30 <= sand <= 50:
            patterns.append({
                "type": "soil",
                "pattern": "Loamy Soil (Ideal)",
                "confidence": 80,
                "detail": f"Balanced composition: {clay:.0f}% clay, {sand:.0f}% sand. "
                          f"Excellent for agriculture.",
                "significance": "high",
            })

    if soc is not None:
        if soc > 30:
            patterns.append({
                "type": "soil",
                "pattern": "High Organic Carbon",
                "confidence": 85,
                "detail": f"SOC {soc:.1f} g/kg. Rich organic matter indicating fertile soil "
                          f"or peat/wetland environment.",
                "significance": "high",
            })
        elif soc < 5:
            patterns.append({
                "type": "soil",
                "pattern": "Low Organic Carbon",
                "confidence": 80,
                "detail": f"SOC only {soc:.1f} g/kg. Nutrient-poor soil. "
                          f"Possible desert, eroded, or degraded land.",
                "significance": "high",
            })

    if ph is not None:
        if ph > 8.5:
            patterns.append({
                "type": "soil",
                "pattern": "Alkaline Soil",
                "confidence": 85,
                "detail": f"pH {ph:.1f} — strongly alkaline. Possible salinity issues.",
                "significance": "medium",
            })
        elif ph < 5.0:
            patterns.append({
                "type": "soil",
                "pattern": "Acidic Soil",
                "confidence": 85,
                "detail": f"pH {ph:.1f} — acidic conditions. Nutrient availability may be limited.",
                "significance": "medium",
            })

    return patterns


@st.cache_data(ttl=1800)
def detect_all_patterns(lat: float, lon: float) -> list:
    """Run all pattern detectors and combine results."""
    all_patterns = []
    all_patterns.extend(_detect_terrain_patterns(lat, lon))
    all_patterns.extend(_detect_hydro_patterns(lat, lon))
    all_patterns.extend(_detect_urban_patterns(lat, lon))
    all_patterns.extend(_detect_geological_patterns(lat, lon))
    all_patterns.extend(_detect_soil_patterns(lat, lon))

    # Sort by confidence descending
    all_patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
    return all_patterns


# ── Rendering ───────────────────────────────────────────────────────────────

def render_pattern_recognizer_tab():
    """Render the Pattern Recognizer AI tab."""
    st.markdown("## Geospatial Pattern Recognizer AI")
    st.caption("Multi-dimensional pattern detection with confidence scoring")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="pr2_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="pr2_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="pr2_lon", format="%.4f")

    if st.button("Detect Patterns", type="primary", use_container_width=True):
        with st.spinner("Scanning 6 pattern dimensions..."):
            patterns = detect_all_patterns(lat, lon)

        if not patterns:
            st.info("No significant patterns detected.")
            return

        # ── Summary metrics ──
        type_counts = Counter(p["type"] for p in patterns)
        high_conf = sum(1 for p in patterns if p.get("confidence", 0) >= 80)
        high_sig = sum(1 for p in patterns if p.get("significance") == "high")
        avg_conf = sum(p.get("confidence", 0) for p in patterns) / len(patterns)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Patterns Found", len(patterns))
        mc2.metric("High Confidence", high_conf)
        mc3.metric("High Significance", high_sig)
        mc4.metric("Avg Confidence", f"{avg_conf:.0f}%")

        # ── Pattern distribution chart ──
        st.markdown("### Pattern Distribution")
        dist_types = []
        dist_counts = []
        dist_colors = []
        for pt_id, pt_info in PATTERN_TYPES.items():
            count = type_counts.get(pt_id, 0)
            if count > 0:
                dist_types.append(pt_info["name"])
                dist_counts.append(count)
                dist_colors.append(pt_info["color"])

        if dist_types:
            fig = go.Figure(data=[go.Bar(
                x=dist_types,
                y=dist_counts,
                marker_color=dist_colors,
                text=dist_counts,
                textposition="auto",
            )])
            fig.update_layout(
                height=300,
                margin=dict(t=20, b=40),
                xaxis_title="",
                yaxis_title="Patterns Detected",
            )
            st.plotly_chart(fig, use_container_width=True, key="patrec_pchart1")

        # ── Confidence radar ──
        st.markdown("### Confidence by Domain")
        domain_avg = {}
        for p in patterns:
            t = p["type"]
            if t not in domain_avg:
                domain_avg[t] = []
            domain_avg[t].append(p.get("confidence", 0))

        radar_names = []
        radar_vals = []
        for pt_id in PATTERN_TYPES:
            if pt_id in domain_avg:
                radar_names.append(PATTERN_TYPES[pt_id]["name"])
                radar_vals.append(sum(domain_avg[pt_id]) / len(domain_avg[pt_id]))

        if len(radar_names) >= 3:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatterpolar(
                r=radar_vals + [radar_vals[0]],
                theta=radar_names + [radar_names[0]],
                fill="toself",
                fillcolor="rgba(139,92,246,0.15)",
                line=dict(color="#8b5cf6", width=2),
            ))
            fig2.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                height=350,
                margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig2, use_container_width=True, key="patrec_pchart2")

        # ── Pattern cards ──
        st.markdown("### Detected Patterns")
        for p in patterns:
            info = PATTERN_TYPES.get(p["type"], {})
            conf = p.get("confidence", 0)
            sig = p.get("significance", "medium")

            if sig == "high":
                sig_color = "#ef4444"
                sig_label = "HIGH"
            elif sig == "medium":
                sig_color = "#f59e0b"
                sig_label = "MED"
            else:
                sig_color = "#10b981"
                sig_label = "LOW"

            conf_color = "#10b981" if conf >= 80 else "#f59e0b" if conf >= 60 else "#ef4444"

            st.markdown(f"""
            <div style="background:#1a1a2e; border-left:4px solid {info.get('color', '#888')};
                        border-radius:8px; padding:12px; margin:6px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:{info.get('color', '#888')}; font-size:12px;">
                            {info.get('name', p['type']).upper()}
                        </span><br/>
                        <span style="color:#eee; font-weight:bold; font-size:16px;">
                            {p['pattern']}
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:{conf_color}; font-weight:bold;">{conf}%</span>
                        <span style="color:#888; font-size:11px;"> conf</span><br/>
                        <span style="background:{sig_color}22; color:{sig_color};
                                    padding:2px 8px; border-radius:4px; font-size:11px;">
                            {sig_label}
                        </span>
                    </div>
                </div>
                <div style="color:#aaa; font-size:13px; margin-top:8px;">
                    {p['detail']}
                </div>
            </div>
            """, unsafe_allow_html=True)
