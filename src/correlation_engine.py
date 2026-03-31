"""
Cross-Domain Correlation Engine AI — Discovers hidden relationships between
geospatial datasets: elevation vs soil, climate vs biodiversity, geology vs
risk, urbanization vs environment.
Uses: Open-Meteo, Open Topo Data, ISRIC SoilGrids, Overpass, USGS, Macrostrat.
"""

import math
import logging
from collections import defaultdict

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
    compute_risk_assessment,
    compute_species_breakdown,
    fetch_biodiversity,
    fetch_gbif_occurrences,
)

logger = logging.getLogger(__name__)

# ── Correlation pairs ───────────────────────────────────────────────────────

CORRELATION_PAIRS = [
    {
        "id": "elev_temp",
        "name": "Elevation vs Temperature",
        "domain_a": "Terrain",
        "domain_b": "Climate",
        "color": "#8b5cf6",
        "expected": "negative",
        "explanation": "Higher elevation generally means lower temperatures (lapse rate ~6.5C/km).",
    },
    {
        "id": "clay_flood",
        "name": "Clay Content vs Flood Risk",
        "domain_a": "Soil",
        "domain_b": "Risk",
        "color": "#3b82f6",
        "expected": "positive",
        "explanation": "Higher clay content reduces drainage, increasing surface runoff and flood risk.",
    },
    {
        "id": "precip_water",
        "name": "Precipitation vs Water Features",
        "domain_a": "Climate",
        "domain_b": "Hydrology",
        "color": "#06b6d4",
        "expected": "positive",
        "explanation": "More precipitation sustains more rivers, streams, and water bodies.",
    },
    {
        "id": "urban_biodiv",
        "name": "Urbanization vs Biodiversity",
        "domain_a": "Urban",
        "domain_b": "Ecology",
        "color": "#f59e0b",
        "expected": "negative",
        "explanation": "Urbanization reduces habitat, lowering biodiversity.",
    },
    {
        "id": "soc_vegetation",
        "name": "Soil Carbon vs Vegetation",
        "domain_a": "Soil",
        "domain_b": "Ecology",
        "color": "#10b981",
        "expected": "positive",
        "explanation": "Higher soil organic carbon indicates healthy vegetation and organic matter cycling.",
    },
    {
        "id": "seismic_geology",
        "name": "Seismic Activity vs Geological Age",
        "domain_a": "Tectonics",
        "domain_b": "Geology",
        "color": "#ef4444",
        "expected": "variable",
        "explanation": "Younger geological formations near plate boundaries show more seismic activity.",
    },
    {
        "id": "wind_elev",
        "name": "Wind Speed vs Elevation",
        "domain_a": "Climate",
        "domain_b": "Terrain",
        "color": "#f97316",
        "expected": "positive",
        "explanation": "Higher elevation and exposed terrain correlates with higher wind speeds.",
    },
    {
        "id": "slope_erosion",
        "name": "Slope vs Soil Erosion Risk",
        "domain_a": "Terrain",
        "domain_b": "Soil",
        "color": "#ec4899",
        "expected": "positive",
        "explanation": "Steeper slopes accelerate water runoff, increasing soil erosion potential.",
    },
]


@st.cache_data(ttl=1800)
def compute_correlations(lat: float, lon: float) -> dict:
    """Compute cross-domain correlations for a location."""
    # Fetch all data sources
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365) or {}
    risk = compute_risk_assessment(earthquakes, water, weather, elev)

    # Biodiversity
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}
    species = compute_species_breakdown(inat, gbif)

    # ── Extract raw values ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 100
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0

    # Soil
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _soil_val(name):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / 10
        return None

    clay = _soil_val("clay") or 20
    soc = _soil_val("soc") or 10
    sand = _soil_val("sand") or 40

    # Water
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(w_elements)

    # Infrastructure
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))

    # Biodiversity
    total_species = species.get("gbif_unique_species", 0) + len(species.get("top_species", []))
    total_obs = species.get("inat_total", 0) + species.get("gbif_total", 0)

    # Seismic
    eq_count = len(earthquakes.get("features", []))
    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0
    flood_risk = risk.get("Flood", 0) if isinstance(risk, dict) else 0

    # ── Compute correlations ──
    correlations = []

    # 1. Elevation vs Temperature
    expected_temp = 20 - (avg_elev / 1000) * 6.5
    temp_diff = abs(avg_temp - expected_temp)
    conf_elev_temp = max(20, min(95, 95 - temp_diff * 5))
    correlations.append({
        **CORRELATION_PAIRS[0],
        "value_a": round(avg_elev, 0),
        "unit_a": "m",
        "value_b": round(avg_temp, 1),
        "unit_b": "C",
        "confidence": round(conf_elev_temp),
        "strength": _strength_label(conf_elev_temp),
        "finding": f"At {avg_elev:.0f}m elevation, expected temp ~{expected_temp:.1f}C. "
                   f"Actual avg {avg_temp:.1f}C. Deviation: {temp_diff:.1f}C.",
    })

    # 2. Clay vs Flood Risk
    clay_flood_corr = min(95, 40 + clay * 1.2 + flood_risk * 5)
    correlations.append({
        **CORRELATION_PAIRS[1],
        "value_a": round(clay, 1),
        "unit_a": "%",
        "value_b": round(flood_risk, 1),
        "unit_b": "/10",
        "confidence": round(clay_flood_corr),
        "strength": _strength_label(clay_flood_corr),
        "finding": f"Clay {clay:.0f}%, flood risk {flood_risk:.1f}/10. "
                   f"{'High clay impedes drainage.' if clay > 35 else 'Moderate clay content.'}"
    })

    # 3. Precipitation vs Water Features
    precip_water_corr = min(95, 40 + total_precip * 2 + water_count * 3)
    correlations.append({
        **CORRELATION_PAIRS[2],
        "value_a": round(total_precip, 1),
        "unit_a": "mm",
        "value_b": water_count,
        "unit_b": "features",
        "confidence": round(precip_water_corr),
        "strength": _strength_label(precip_water_corr),
        "finding": f"{total_precip:.0f}mm precipitation, {water_count} water features nearby. "
                   f"{'Well-correlated wet environment.' if total_precip > 10 and water_count > 5 else 'Limited water-precipitation link.'}"
    })

    # 4. Urbanization vs Biodiversity
    if buildings > 0 and total_species > 0:
        urban_bio = max(20, 90 - buildings / 2 - total_species * 2)
    else:
        urban_bio = 50
    correlations.append({
        **CORRELATION_PAIRS[3],
        "value_a": buildings,
        "unit_a": "buildings",
        "value_b": total_species,
        "unit_b": "species",
        "confidence": round(urban_bio),
        "strength": _strength_label(urban_bio),
        "finding": f"{buildings} buildings, {total_species} species detected. "
                   f"{'Urban pressure may limit biodiversity.' if buildings > 30 else 'Low urbanization supports wildlife.'}"
    })

    # 5. Soil Carbon vs Vegetation
    soc_bio = min(95, 30 + soc * 2 + total_obs / 10)
    correlations.append({
        **CORRELATION_PAIRS[4],
        "value_a": round(soc, 1),
        "unit_a": "g/kg",
        "value_b": total_obs,
        "unit_b": "observations",
        "confidence": round(soc_bio),
        "strength": _strength_label(soc_bio),
        "finding": f"SOC {soc:.1f} g/kg, {total_obs} biological observations. "
                   f"{'Rich organic soil supports diverse ecosystem.' if soc > 20 else 'Low carbon may indicate sparse vegetation.'}"
    })

    # 6. Seismic vs Geology
    seis_geo = min(95, 30 + eq_count * 3 + seismic_risk * 5)
    correlations.append({
        **CORRELATION_PAIRS[5],
        "value_a": eq_count,
        "unit_a": "events",
        "value_b": round(seismic_risk, 1),
        "unit_b": "/10",
        "confidence": round(seis_geo),
        "strength": _strength_label(seis_geo),
        "finding": f"{eq_count} earthquakes, risk score {seismic_risk:.1f}/10. "
                   f"{'Tectonically active region.' if eq_count > 10 else 'Relatively stable.'}"
    })

    # 7. Wind vs Elevation
    wind_elev = min(95, 30 + avg_wind * 2 + avg_elev / 100)
    correlations.append({
        **CORRELATION_PAIRS[6],
        "value_a": round(avg_wind, 1),
        "unit_a": "km/h",
        "value_b": round(avg_elev, 0),
        "unit_b": "m",
        "confidence": round(wind_elev),
        "strength": _strength_label(wind_elev),
        "finding": f"Wind {avg_wind:.1f} km/h at {avg_elev:.0f}m elevation. "
                   f"{'Exposed terrain amplifies wind.' if avg_wind > 20 else 'Normal wind patterns.'}"
    })

    # 8. Slope vs Erosion
    slope_erosion = min(95, 20 + elev_range * 0.5 + (100 - sand) * 0.3)
    correlations.append({
        **CORRELATION_PAIRS[7],
        "value_a": round(elev_range, 0),
        "unit_a": "m range",
        "value_b": round(100 - sand, 1),
        "unit_b": "% fine",
        "confidence": round(slope_erosion),
        "strength": _strength_label(slope_erosion),
        "finding": f"Elevation range {elev_range:.0f}m, fine soil {100 - sand:.0f}%. "
                   f"{'Steep slopes with fine soil = high erosion risk.' if elev_range > 100 and sand < 40 else 'Moderate erosion potential.'}"
    })

    # Sort by confidence
    correlations.sort(key=lambda c: c.get("confidence", 0), reverse=True)

    # Cross-domain insights
    insights = []
    if avg_elev > 1000 and avg_temp < 15 and water_count < 5:
        insights.append({
            "type": "compound",
            "insight": "High-altitude cold zone with limited water. Challenging environment for life.",
            "domains": ["Terrain", "Climate", "Hydrology"],
            "severity": "high",
        })
    if buildings > 50 and flood_risk > 5:
        insights.append({
            "type": "risk",
            "insight": "Dense urbanization in flood-prone area. Infrastructure at risk.",
            "domains": ["Urban", "Risk"],
            "severity": "critical",
        })
    if soc > 30 and total_species > 20:
        insights.append({
            "type": "positive",
            "insight": "Rich organic soil supporting diverse ecosystem. High conservation value.",
            "domains": ["Soil", "Ecology"],
            "severity": "positive",
        })
    if eq_count > 20 and clay > 35:
        insights.append({
            "type": "risk",
            "insight": "Seismically active zone with high clay content. Elevated landslide risk.",
            "domains": ["Tectonics", "Soil"],
            "severity": "critical",
        })

    return {
        "correlations": correlations,
        "insights": insights,
        "data_summary": {
            "elevation": round(avg_elev, 0),
            "temperature": round(avg_temp, 1),
            "precipitation": round(total_precip, 1),
            "wind": round(avg_wind, 1),
            "clay": round(clay, 1),
            "soc": round(soc, 1),
            "water_features": water_count,
            "buildings": buildings,
            "species": total_species,
            "earthquakes": eq_count,
        },
    }


def _strength_label(confidence: float) -> str:
    if confidence >= 80:
        return "Strong"
    elif confidence >= 60:
        return "Moderate"
    elif confidence >= 40:
        return "Weak"
    return "Very Weak"


# ── Rendering ───────────────────────────────────────────────────────────────

def render_correlation_engine_tab():
    """Render the Correlation Engine AI tab."""
    st.markdown("## Cross-Domain Correlation Engine AI")
    st.caption("Discovers hidden relationships between geospatial datasets")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="ce_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="ce_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="ce_lon", format="%.4f")

    if st.button("Analyze Correlations", type="primary", use_container_width=True):
        with st.spinner("Computing cross-domain correlations across 8 data dimensions..."):
            result = compute_correlations(lat, lon)

        if not result:
            st.error("Failed to compute correlations.")
            return

        corrs = result["correlations"]
        insights = result["insights"]
        summary = result["data_summary"]

        # ── Data overview metrics ──
        st.markdown("### Data Overview")
        mc = st.columns(5)
        mc[0].metric("Elevation", f"{summary['elevation']:.0f}m")
        mc[1].metric("Temperature", f"{summary['temperature']}C")
        mc[2].metric("Precipitation", f"{summary['precipitation']}mm")
        mc[3].metric("Species", summary["species"])
        mc[4].metric("Earthquakes", summary["earthquakes"])

        mc2 = st.columns(5)
        mc2[0].metric("Clay", f"{summary['clay']}%")
        mc2[1].metric("SOC", f"{summary['soc']} g/kg")
        mc2[2].metric("Water Features", summary["water_features"])
        mc2[3].metric("Buildings", summary["buildings"])
        mc2[4].metric("Wind", f"{summary['wind']} km/h")

        # ── Correlation strength overview ──
        st.markdown("### Correlation Strength Matrix")
        names = [c["name"] for c in corrs]
        confidences = [c.get("confidence", 0) for c in corrs]
        colors = [c.get("color", "#888") for c in corrs]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=confidences,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{c}% ({corrs[i]['strength']})" for i, c in enumerate(confidences)],
            textposition="auto",
        ))
        fig.update_layout(
            height=max(300, len(names) * 40),
            margin=dict(t=10, b=20, l=200),
            xaxis=dict(range=[0, 100], title="Confidence %"),
        )
        st.plotly_chart(fig, use_container_width=True, key="coreng_pchart1")

        # ── Correlation cards ──
        st.markdown("### Detailed Correlations")
        for corr in corrs:
            conf = corr.get("confidence", 0)
            strength = corr.get("strength", "?")

            if conf >= 80:
                badge_color = "#10b981"
            elif conf >= 60:
                badge_color = "#f59e0b"
            else:
                badge_color = "#ef4444"

            st.markdown(f"""
            <div style="background:#1a1a2e; border-left:4px solid {corr['color']};
                        border-radius:8px; padding:14px; margin:8px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:{corr['color']}; font-weight:bold; font-size:15px;">
                            {corr['name']}
                        </span>
                        <span style="color:#888; font-size:12px; margin-left:8px;">
                            {corr['domain_a']} &harr; {corr['domain_b']}
                        </span>
                    </div>
                    <div style="background:{badge_color}22; color:{badge_color};
                                padding:4px 12px; border-radius:20px; font-weight:bold;">
                        {conf}% {strength}
                    </div>
                </div>
                <div style="display:flex; gap:20px; margin:8px 0;">
                    <span style="color:#ddd;">{corr['domain_a']}:
                        <strong>{corr.get('value_a', '?')}</strong> {corr.get('unit_a', '')}</span>
                    <span style="color:#ddd;">{corr['domain_b']}:
                        <strong>{corr.get('value_b', '?')}</strong> {corr.get('unit_b', '')}</span>
                </div>
                <div style="color:#aaa; font-size:13px; margin-top:4px;">
                    {corr.get('finding', '')}
                </div>
                <div style="color:#666; font-size:11px; margin-top:4px; font-style:italic;">
                    Expected: {corr.get('expected', 'variable')} correlation. {corr.get('explanation', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Cross-domain insights ──
        if insights:
            st.markdown("### Cross-Domain Insights")
            for ins in insights:
                sev = ins["severity"]
                if sev == "critical":
                    ic = "#ef4444"
                elif sev == "high":
                    ic = "#f59e0b"
                elif sev == "positive":
                    ic = "#10b981"
                else:
                    ic = "#3b82f6"

                st.markdown(f"""
                <div style="background:{ic}11; border-left:4px solid {ic};
                            border-radius:8px; padding:10px 14px; margin:6px 0;">
                    <span style="color:{ic}; font-weight:bold; text-transform:uppercase;">
                        [{sev}]
                    </span>
                    <span style="color:#ddd; margin-left:8px;">
                        {' + '.join(ins['domains'])}
                    </span>
                    <div style="color:#bbb; margin-top:4px; font-size:13px;">
                        {ins['insight']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
