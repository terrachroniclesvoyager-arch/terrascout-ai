"""
Ecosystem Health Index AI — Comprehensive ecosystem health assessment
combining biodiversity, soil health, water quality, vegetation, and
human impact into a unified Ecosystem Health Index (EHI).
Uses: iNaturalist, GBIF, SoilGrids, Open-Meteo, Overpass.
"""

import logging

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

EHI_COMPONENTS = {
    "biodiversity": {"name": "Biodiversity Index", "color": "#22c55e", "weight": 0.25},
    "soil_health": {"name": "Soil Health", "color": "#f59e0b", "weight": 0.20},
    "water_health": {"name": "Water System", "color": "#3b82f6", "weight": 0.20},
    "climate_fit": {"name": "Climate Fitness", "color": "#8b5cf6", "weight": 0.15},
    "human_impact": {"name": "Human Impact", "color": "#ef4444", "weight": 0.10},
    "protection": {"name": "Conservation Status", "color": "#10b981", "weight": 0.10},
}


@st.cache_data(ttl=1800)
def compute_ecosystem_health(lat: float, lon: float) -> dict:
    """Compute Ecosystem Health Index."""
    soil = fetch_soil_data(lat, lon) or {}
    weather = fetch_weather_data(lat, lon) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    protected = fetch_protected_areas(lat, lon) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}

    species = compute_species_breakdown(inat, gbif)
    scores = {}
    details = {}

    # 1. Biodiversity Index
    total_species = (species.get("gbif_unique_species") or 0) + len(species.get("top_species", []))
    total_obs = (species.get("inat_total") or 0) + (species.get("gbif_total") or 0)
    kingdoms = species.get("kingdom_counts", {})
    kingdom_diversity = len([k for k, v in kingdoms.items() if v > 0])

    bio_score = min(100, total_species * 3 + total_obs / 10 + kingdom_diversity * 10)
    scores["biodiversity"] = round(bio_score)
    details["biodiversity"] = {
        "species": total_species,
        "observations": total_obs,
        "kingdom_diversity": kingdom_diversity,
        "kingdoms": kingdoms,
    }

    # 2. Soil Health
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0
    nitrogen = _sv("nitrogen", 100) or 1.0
    clay = _sv("clay") or 20

    ph_score = max(0, 100 - abs(ph - 6.5) * 20)
    soc_score = min(100, soc * 3)
    n_score = min(100, nitrogen * 30)
    soil_score = (ph_score * 0.3 + soc_score * 0.4 + n_score * 0.3)
    scores["soil_health"] = round(soil_score)
    details["soil_health"] = {
        "soc": round(soc, 1),
        "ph": round(ph, 1),
        "nitrogen": round(nitrogen, 2),
        "clay": round(clay, 1),
    }

    # 3. Water System Health
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    springs = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "spring")
    wetlands = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "wetland")
    rivers = sum(1 for e in w_elements if e.get("tags", {}).get("waterway") in ("river", "stream"))
    water_total = len(w_elements)

    water_score = min(100, water_total * 5 + springs * 15 + wetlands * 20 + rivers * 8)
    scores["water_health"] = round(water_score)
    details["water_health"] = {
        "total_features": water_total,
        "springs": springs,
        "wetlands": wetlands,
        "rivers_streams": rivers,
    }

    # 4. Climate Fitness
    daily = weather.get("daily", {})
    current = weather.get("current", {})
    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20
    humidity = current.get("relative_humidity_2m", 50) or 50

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0

    temp_score = max(0, 100 - abs(avg_temp - 20) * 4)
    humid_score = max(0, 100 - abs(humidity - 55) * 2)
    precip_score = min(100, total_precip * 5)
    climate_score = (temp_score * 0.4 + humid_score * 0.3 + precip_score * 0.3)
    scores["climate_fit"] = round(climate_score)
    details["climate_fit"] = {
        "avg_temp": round(avg_temp, 1),
        "humidity": round(humidity),
        "precipitation": round(total_precip, 1),
    }

    # 5. Human Impact (inverted — less is better)
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))
    industrial = sum(1 for e in i_elements
                     if e.get("tags", {}).get("landuse") in ("industrial", "commercial", "landfill"))

    impact_raw = min(100, buildings * 2 + roads + industrial * 10)
    human_score = max(0, 100 - impact_raw)
    scores["human_impact"] = round(human_score)
    details["human_impact"] = {
        "buildings": buildings,
        "roads": roads,
        "industrial": industrial,
        "impact_level": "High" if impact_raw > 60 else "Moderate" if impact_raw > 30 else "Low",
    }

    # 6. Conservation Status
    p_elements = protected.get("elements", []) if isinstance(protected, dict) else []
    protection_score = min(100, len(p_elements) * 25)
    scores["protection"] = round(protection_score)
    details["protection"] = {
        "protected_areas": len(p_elements),
    }

    # ── Compute EHI (weighted) ──
    ehi = sum(scores[k] * EHI_COMPONENTS[k]["weight"] for k in scores)
    ehi = round(ehi)

    # Classification
    if ehi >= 80:
        ehi_class = "Excellent"
        ehi_color = "#10b981"
    elif ehi >= 60:
        ehi_class = "Good"
        ehi_color = "#22c55e"
    elif ehi >= 40:
        ehi_class = "Fair"
        ehi_color = "#f59e0b"
    elif ehi >= 20:
        ehi_class = "Poor"
        ehi_color = "#f97316"
    else:
        ehi_class = "Critical"
        ehi_color = "#ef4444"

    return {
        "ehi": ehi,
        "ehi_class": ehi_class,
        "ehi_color": ehi_color,
        "scores": scores,
        "details": details,
    }


def render_ecosystem_health_tab():
    """Render the Ecosystem Health Index AI tab."""
    st.markdown("## Ecosystem Health Index AI")
    st.caption("Unified ecosystem health assessment across 6 dimensions")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="eh_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="eh_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="eh_lon", format="%.4f")

    if st.button("Assess Ecosystem Health", type="primary", use_container_width=True):
        with st.spinner("Assessing ecosystem health across 6 dimensions..."):
            result = compute_ecosystem_health(lat, lon)

        if not result:
            st.error("Assessment failed.")
            return

        ehi = result["ehi"]
        ehi_class = result["ehi_class"]
        ehi_color = result["ehi_color"]
        scores = result["scores"]
        details = result["details"]

        # ── EHI Header ──
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {ehi_color}22, {ehi_color}44);
                    border-left:5px solid {ehi_color}; border-radius:12px;
                    padding:25px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">ECOSYSTEM HEALTH INDEX</div>
                    <div style="color:{ehi_color}; font-size:36px; font-weight:bold; margin:4px 0;">
                        {ehi_class}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:56px; font-weight:bold; color:{ehi_color};">
                        {ehi}
                    </div>
                    <div style="color:#888; font-size:14px;">/100</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Radar chart ──
        comp_names = [EHI_COMPONENTS[k]["name"] for k in scores]
        comp_values = [scores[k] for k in scores]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=comp_values + [comp_values[0]],
            theta=comp_names + [comp_names[0]],
            fill="toself",
            fillcolor=_hex_rgba(ehi_color, 0.13),
            line=dict(color=ehi_color, width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=400,
            margin=dict(t=30, b=30, l=70, r=70),
        )
        st.plotly_chart(fig, use_container_width=True, key="ecohea_pchart1")

        # ── Component cards ──
        cols = st.columns(3)
        for idx, (comp_id, comp_info) in enumerate(EHI_COMPONENTS.items()):
            score = scores[comp_id]
            detail = details[comp_id]

            if score >= 70:
                sc = "#10b981"
            elif score >= 40:
                sc = "#f59e0b"
            else:
                sc = "#ef4444"

            detail_text = " | ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in detail.items()
                                     if not isinstance(v, dict))

            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid {comp_info['color']}44;
                            border-radius:10px; padding:15px; margin:5px 0; min-height:130px;">
                    <div style="color:{comp_info['color']}; font-weight:bold; font-size:13px;">
                        {comp_info['name']}
                    </div>
                    <div style="font-size:32px; font-weight:bold; color:{sc}; margin:4px 0;">
                        {score}<span style="font-size:12px; color:#888;">%</span>
                    </div>
                    <div style="color:#aaa; font-size:11px;">{detail_text}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Biodiversity breakdown ──
        kingdoms = details["biodiversity"].get("kingdoms", {})
        if kingdoms:
            st.markdown("### Biodiversity Kingdoms")
            fig2 = go.Figure(data=[go.Pie(
                labels=list(kingdoms.keys()),
                values=list(kingdoms.values()),
                hole=0.4,
            )])
            fig2.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True, key="ecohea_pchart2")
