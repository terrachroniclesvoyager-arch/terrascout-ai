"""
Biodiversity Hotspot AI module for TerraScout AI.
Provides deep biodiversity analysis with conservation priority assessment
using multi-source ecological data from free APIs (iNaturalist, GBIF,
Open-Meteo, Overpass/OSM, SoilGrids, Open-Elevation).
"""

import html as html_module
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
    fetch_protected_areas,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# THEME COLOURS
# ═══════════════════════════════════════════════════════════════════════════════
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
BG_CARD_ALT = "#0f3460"
GREEN_PRIMARY = "#059669"
GREEN_MEDIUM = "#10b981"
GREEN_LIGHT = "#34d399"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
ACCENT_BLUE = "#3b82f6"
TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"

WATER_TYPES = {"spring", "river", "stream", "wetland", "lake", "reservoir",
               "pond", "canal", "ditch", "waterfall", "water_well"}

INDEX_COLORS = {
    "Species Richness": GREEN_PRIMARY,
    "Habitat Quality": GREEN_MEDIUM,
    "Ecosystem Integrity": GREEN_LIGHT,
    "Conservation Priority": ACCENT_AMBER,
    "Genetic Diversity": "#8b5cf6",
    "Connectivity": ACCENT_BLUE,
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def _shannon_index(counts: dict) -> float:
    """Compute Shannon Diversity Index from a frequency dict."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            h -= p * math.log(p)
    return h


def _classify_water_element(el: dict) -> str:
    """Return a water-type label for an Overpass element."""
    tags = el.get("tags", {})
    nat = tags.get("natural", "")
    ww = tags.get("waterway", "")
    mm = tags.get("man_made", "")
    if nat == "spring" or mm == "water_well":
        return "spring"
    if ww in ("river", "stream", "canal", "ditch", "drain"):
        return ww
    if nat == "water":
        water_type = tags.get("water", "lake")
        return water_type
    if nat == "wetland":
        return "wetland"
    return ww or nat or "other"


# ═══════════════════════════════════════════════════════════════════════════════
# CORE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_biodiversity_hotspot(lat: float, lon: float) -> dict:
    """
    Perform a comprehensive biodiversity hotspot assessment for a location.
    Returns indices, species summary, habitat profile, threat level,
    conservation priority class, kingdom breakdown, top species, and
    recommendations.
    """
    # ── Fetch all data sources ──────────────────────────────────────────────
    inat = fetch_biodiversity(lat, lon, radius_km=10)
    gbif = fetch_gbif_occurrences(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    soil = fetch_soil_data(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    infrastructure = fetch_landuse_infrastructure(lat, lon)

    # ── Species analysis ────────────────────────────────────────────────────
    species_data = compute_species_breakdown(inat, gbif)
    kingdom_counts = species_data.get("kingdom_counts") or {}
    top_species = species_data.get("top_species") or []
    inat_total = species_data.get("inat_total") or 0
    gbif_total = species_data.get("gbif_total") or 0
    gbif_unique = species_data.get("gbif_unique_species") or 0

    total_observations = (inat_total or 0) + (gbif_total or 0)
    total_species = (gbif_unique or 0) + len(top_species)
    kingdom_diversity = len(kingdom_counts) if kingdom_counts else 0
    shannon = _shannon_index(kingdom_counts)
    area_km2 = math.pi * 10 * 10  # radius 10 km circle
    species_density = total_observations / area_km2 if area_km2 > 0 else 0

    species_summary = {
        "total_species": total_species,
        "total_observations": total_observations,
        "kingdom_diversity": kingdom_diversity,
        "shannon_index": round(shannon, 3),
        "species_density": round(species_density, 2),
        "inat_total": inat_total,
        "gbif_total": gbif_total,
        "gbif_unique_species": gbif_unique,
    }

    # ── Habitat quality assessment ──────────────────────────────────────────
    elements = (water if isinstance(water, dict) else {}).get("elements", [])
    water_type_set = set()
    for el in elements:
        wt = _classify_water_element(el)
        water_type_set.add(wt)
    water_diversity = len(water_type_set)

    elev_min = elevation.get("min_elevation", 0) or 0
    elev_max = elevation.get("max_elevation", 0) or 0
    elev_range = max(0, elev_max - elev_min)
    terrain_variety = min(elev_range / 500.0, 1.0)  # 0-1 scale

    # Soil quality: organic carbon + nitrogen indicate fertile soil
    soil_quality = 0.0
    try:
        props = soil.get("properties", {}).get("layers", [])
        for layer in props:
            depths = layer.get("depths", [])
            prop_name = layer.get("name", "")
            if depths and prop_name in ("soc", "nitrogen"):
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    soil_quality += min(float(val) / 500.0, 0.5)
    except Exception:
        soil_quality = 0.3

    # Climate suitability: moderate temp + adequate precipitation
    current = weather.get("current", {})
    temp = current.get("temperature_2m", 15)
    daily = weather.get("daily", {})
    precip_list = daily.get("precipitation_sum", [])
    precip_total = sum(p for p in precip_list if p is not None) if precip_list else 0
    temp_suitability = max(0, 1.0 - abs(temp - 18) / 30.0)
    precip_suitability = min(precip_total / 50.0, 1.0)
    climate_suitability = (temp_suitability + precip_suitability) / 2.0

    habitat_profile = {
        "water_diversity": water_diversity,
        "water_types": sorted(water_type_set),
        "terrain_variety": round(terrain_variety, 2),
        "elevation_range_m": round(elev_range, 1),
        "soil_quality": round(min(soil_quality, 1.0), 2),
        "climate_suitability": round(climate_suitability, 2),
        "temperature_c": round(temp, 1),
        "precipitation_7d_mm": round(precip_total, 1),
    }

    # ── Threat assessment ───────────────────────────────────────────────────
    infra_elements = (infrastructure if isinstance(infrastructure, dict)
                      else {}).get("elements", [])
    building_count = 0
    road_count = 0
    industrial_count = 0
    park_count = 0
    natural_landuse = 0
    for el in infra_elements:
        tags = el.get("tags", {})
        if tags.get("building"):
            building_count += 1
        if tags.get("highway"):
            road_count += 1
        lu = tags.get("landuse", "")
        if lu in ("industrial", "commercial", "construction"):
            industrial_count += 1
        if lu in ("forest", "meadow", "farmland", "grass", "orchard",
                  "vineyard"):
            natural_landuse += 1
        if tags.get("leisure") == "park":
            park_count += 1

    total_features = max(len(infra_elements), 1)
    built_count = building_count + road_count + industrial_count
    natural_count = natural_landuse + park_count + len(elements)
    natural_ratio = natural_count / max(natural_count + built_count, 1)

    development_pressure = _clamp(
        (building_count / 50.0) * 30 + (road_count / 30.0) * 30 +
        (industrial_count / 10.0) * 40, 0, 100
    )
    fragmentation = _clamp((1.0 - natural_ratio) * 100, 0, 100)
    climate_stress = _clamp(
        abs(temp - 18) * 2 + max(0, 20 - precip_total) * 2, 0, 100
    )

    threat_score = (development_pressure * 0.4 + fragmentation * 0.3 +
                    climate_stress * 0.3)

    if threat_score >= 70:
        threat_level = "Critical"
    elif threat_score >= 50:
        threat_level = "High"
    elif threat_score >= 30:
        threat_level = "Moderate"
    else:
        threat_level = "Low"

    # ── Conservation priority ───────────────────────────────────────────────
    protected_elements = (protected if isinstance(protected, dict)
                          else {}).get("elements", [])
    protection_score = min(len(protected_elements) * 15, 100)

    richness_score = _clamp(
        min(total_species / 50.0, 1.0) * 50 +
        min(total_observations / 500.0, 1.0) * 30 +
        min(kingdom_diversity / 6.0, 1.0) * 20,
        0, 100
    )

    # Higher threat + high biodiversity = more urgent
    urgency = _clamp(
        (threat_score * 0.5 + richness_score * 0.3 +
         (100 - protection_score) * 0.2),
        0, 100
    )

    if urgency >= 75:
        conservation_priority_class = "CRITICAL - Immediate Action Required"
    elif urgency >= 55:
        conservation_priority_class = "HIGH - Priority Conservation Area"
    elif urgency >= 35:
        conservation_priority_class = "MODERATE - Monitoring Recommended"
    else:
        conservation_priority_class = "LOW - Stable Ecosystem"

    # ── Six biodiversity indices (0-100) ────────────────────────────────────
    idx_species_richness = _clamp(
        min(total_species / 80.0, 1.0) * 60 +
        min(total_observations / 800.0, 1.0) * 40,
        0, 100
    )

    idx_habitat_quality = _clamp(
        min(water_diversity / 4.0, 1.0) * 25 +
        terrain_variety * 25 +
        min(soil_quality, 1.0) * 25 +
        climate_suitability * 25,
        0, 100
    )

    idx_ecosystem_integrity = _clamp(natural_ratio * 100, 0, 100)

    idx_conservation_priority = _clamp(
        richness_score * 0.4 + threat_score * 0.35 +
        (100 - protection_score) * 0.25,
        0, 100
    )

    idx_genetic_diversity = _clamp(
        min(kingdom_diversity / 6.0, 1.0) * 50 +
        min(len(top_species) / 15.0, 1.0) * 30 +
        min(shannon / 2.0, 1.0) * 20,
        0, 100
    )

    water_corridors = min(water_diversity / 3.0, 1.0)
    green_corridors = min((natural_landuse + park_count) / 10.0, 1.0)
    idx_connectivity = _clamp(
        water_corridors * 50 + green_corridors * 50,
        0, 100
    )

    indices = {
        "Species Richness": round(idx_species_richness, 1),
        "Habitat Quality": round(idx_habitat_quality, 1),
        "Ecosystem Integrity": round(idx_ecosystem_integrity, 1),
        "Conservation Priority": round(idx_conservation_priority, 1),
        "Genetic Diversity": round(idx_genetic_diversity, 1),
        "Connectivity": round(idx_connectivity, 1),
    }

    # ── Recommendations ─────────────────────────────────────────────────────
    recommendations = []
    if protection_score < 30:
        recommendations.append(
            "Establish formal protected area designation to safeguard "
            "biodiversity assets."
        )
    if development_pressure > 50:
        recommendations.append(
            "Implement development buffer zones to reduce habitat "
            "encroachment pressure."
        )
    if fragmentation > 60:
        recommendations.append(
            "Create wildlife corridors to reconnect fragmented habitats "
            "and improve gene flow."
        )
    if water_diversity < 2:
        recommendations.append(
            "Restore riparian zones and wetland areas to increase "
            "aquatic habitat diversity."
        )
    if kingdom_diversity < 3:
        recommendations.append(
            "Investigate barriers to taxonomic diversity; consider "
            "habitat enrichment programs."
        )
    if climate_stress > 50:
        recommendations.append(
            "Develop climate adaptation strategies including shade "
            "corridors and water retention features."
        )
    if idx_connectivity < 40:
        recommendations.append(
            "Improve ecological connectivity through green bridges, "
            "underpasses, and riparian buffers."
        )
    if not recommendations:
        recommendations.append(
            "Continue current conservation management and monitoring "
            "programs. Ecosystem appears healthy."
        )

    return {
        "indices": indices,
        "species_summary": species_summary,
        "habitat_profile": habitat_profile,
        "threat_level": threat_level,
        "conservation_priority_class": conservation_priority_class,
        "kingdom_breakdown": kingdom_counts,
        "top_species": top_species,
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# UI RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def _render_index_card(label: str, value: float, color: str) -> None:
    """Render a single biodiversity index card."""
    if value >= 70:
        status = "High"
        status_color = GREEN_PRIMARY
    elif value >= 40:
        status = "Moderate"
        status_color = ACCENT_AMBER
    else:
        status = "Low"
        status_color = ACCENT_RED

    st.markdown(f"""
    <div style="background:{BG_CARD};border-left:4px solid {color};
                border-radius:8px;padding:16px;margin-bottom:8px;">
        <div style="color:{TEXT_SECONDARY};font-size:0.85rem;">
            {label}
        </div>
        <div style="font-size:2rem;font-weight:700;color:{color};
                    margin:4px 0;">
            {value:.1f}
        </div>
        <div style="color:{status_color};font-size:0.8rem;font-weight:600;">
            {status}
        </div>
        <div style="background:#2d2d4e;border-radius:4px;height:6px;
                    margin-top:8px;">
            <div style="background:{color};width:{value}%;height:6px;
                        border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_biodiversity_hotspot_tab() -> None:
    """Render the Biodiversity Hotspot AI tab in the Streamlit app."""
    st.markdown(f"""
    <style>
        .bio-header {{
            background: linear-gradient(135deg, {BG_DARK}, {BG_CARD});
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border-left: 4px solid {GREEN_PRIMARY};
        }}
        .bio-section {{
            background: {BG_CARD};
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
        }}
        .threat-badge {{
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="bio-header">
        <h2 style="color:{GREEN_LIGHT};margin:0;">
            Biodiversity Hotspot AI
        </h2>
        <p style="color:{TEXT_SECONDARY};margin:4px 0 0 0;">
            Deep ecological analysis with conservation priority assessment
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Location selector ───────────────────────────────────────────────────
    preset_names = list(ANALYSIS_PRESETS.keys())
    preset = st.selectbox(
        "Select Location Preset",
        preset_names,
        index=0,
        key="bio_hotspot_preset",
    )

    p = ANALYSIS_PRESETS.get(preset)
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input(
            "Latitude", value=p.get("lat", 41.90) if p else 41.90,
            format="%.4f", key="bio_hotspot_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=p.get("lon", 12.50) if p else 12.50,
            format="%.4f", key="bio_hotspot_lon",
        )

    if not st.button("Assess Biodiversity", type="primary",
                      key="bio_hotspot_run"):
        return

    with st.spinner("Analysing biodiversity hotspot..."):
        data = compute_biodiversity_hotspot(lat, lon)

    indices = data["indices"]
    summary = data["species_summary"]
    habitat = data["habitat_profile"]
    threat = data["threat_level"]
    priority_class = data["conservation_priority_class"]
    kingdoms = data["kingdom_breakdown"]
    top_sp = data["top_species"]
    recs = data["recommendations"]

    # ── Conservation priority header ────────────────────────────────────────
    if "CRITICAL" in priority_class:
        badge_bg, badge_fg = ACCENT_RED, "#fff"
    elif "HIGH" in priority_class:
        badge_bg, badge_fg = ACCENT_AMBER, "#000"
    elif "MODERATE" in priority_class:
        badge_bg, badge_fg = ACCENT_BLUE, "#fff"
    else:
        badge_bg, badge_fg = GREEN_PRIMARY, "#fff"

    st.markdown(f"""
    <div class="bio-section" style="text-align:center;">
        <h3 style="color:{TEXT_PRIMARY};margin:0 0 8px 0;">
            Conservation Priority Assessment
        </h3>
        <span class="threat-badge"
              style="background:{badge_bg};color:{badge_fg};">
            {priority_class}
        </span>
        <p style="color:{TEXT_SECONDARY};margin:10px 0 0 0;font-size:0.9rem;">
            Threat Level: <strong style="color:{ACCENT_AMBER};">{threat}
            </strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 6 index cards in 3x2 grid ──────────────────────────────────────────
    st.markdown(f"### Biodiversity Indices")
    index_names = list(indices.keys())
    row1 = st.columns(3)
    for i, col in enumerate(row1):
        if i < len(index_names):
            name = index_names[i]
            with col:
                _render_index_card(name, indices[name],
                                   INDEX_COLORS.get(name, GREEN_MEDIUM))
    row2 = st.columns(3)
    for i, col in enumerate(row2):
        idx = i + 3
        if idx < len(index_names):
            name = index_names[idx]
            with col:
                _render_index_card(name, indices[name],
                                   INDEX_COLORS.get(name, GREEN_MEDIUM))

    # ── Radar chart ─────────────────────────────────────────────────────────
    st.markdown(f"### Ecological Profile Radar")
    radar_labels = list(indices.keys())
    radar_values = [indices[k] for k in radar_labels]
    # Close the polygon
    radar_labels_closed = radar_labels + [radar_labels[0]]
    radar_values_closed = radar_values + [radar_values[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        fillcolor=f"rgba(5,150,105,0.25)",
        line=dict(color=GREEN_PRIMARY, width=2),
        marker=dict(color=GREEN_LIGHT, size=6),
        name="Biodiversity Profile",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2d2d4e", linecolor="#2d2d4e",
                tickfont=dict(color=TEXT_SECONDARY, size=10),
            ),
            angularaxis=dict(
                gridcolor="#2d2d4e", linecolor="#2d2d4e",
                tickfont=dict(color=TEXT_PRIMARY, size=11),
            ),
        ),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_CARD,
        font=dict(color=TEXT_PRIMARY),
        showlegend=False,
        height=420,
        margin=dict(l=60, r=60, t=30, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="biohot_pchart1")

    # ── Kingdom breakdown pie chart (donut) ─────────────────────────────────
    if kingdoms:
        st.markdown(f"### Kingdom Breakdown")
        k_labels = list(kingdoms.keys())
        k_values = [kingdoms[k] for k in k_labels]
        kingdom_colors = [
            GREEN_PRIMARY, GREEN_MEDIUM, GREEN_LIGHT,
            ACCENT_AMBER, ACCENT_BLUE, "#8b5cf6",
            "#ec4899", "#f97316", "#64748b", "#14b8a6",
        ]
        fig_kingdom = go.Figure()
        fig_kingdom.add_trace(go.Pie(
            labels=k_labels,
            values=k_values,
            hole=0.45,
            marker=dict(colors=kingdom_colors[:len(k_labels)]),
            textinfo="label+percent",
            textfont=dict(color="#fff", size=12),
            hovertemplate="%{label}: %{value} observations<extra></extra>",
        ))
        fig_kingdom.update_layout(
            paper_bgcolor=BG_DARK,
            plot_bgcolor=BG_CARD,
            font=dict(color=TEXT_PRIMARY),
            showlegend=True,
            legend=dict(font=dict(color=TEXT_PRIMARY, size=11)),
            height=380,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_kingdom, use_container_width=True, key="biohot_pchart2")
    else:
        st.info("No kingdom breakdown data available for this location.")

    # ── Top species list ────────────────────────────────────────────────────
    st.markdown(f"### Top Observed Species")
    if top_sp:
        for rank, (sci_name, count, common_name) in enumerate(top_sp[:15], 1):
            bar_width = min((count or 0) / max(
                (top_sp[0][1] if top_sp else 1), 1) * 100, 100)
            safe_sci = html_module.escape(str(sci_name))
            safe_common = html_module.escape(str(common_name))
            st.markdown(f"""
            <div style="background:{BG_CARD};border-radius:8px;padding:10px 14px;
                        margin-bottom:6px;display:flex;align-items:center;">
                <div style="min-width:28px;color:{GREEN_LIGHT};
                            font-weight:700;font-size:0.9rem;">
                    {rank}
                </div>
                <div style="flex:1;">
                    <div style="color:{TEXT_PRIMARY};font-size:0.9rem;">
                        <em>{safe_sci}</em>
                    </div>
                    <div style="color:{TEXT_SECONDARY};font-size:0.8rem;">
                        {safe_common}
                    </div>
                </div>
                <div style="min-width:50px;text-align:right;
                            color:{GREEN_MEDIUM};font-weight:600;">
                    {count}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No species observation data available for this location.")

    # ── Habitat quality metrics ─────────────────────────────────────────────
    st.markdown(f"### Habitat Quality Profile")
    hcol1, hcol2 = st.columns(2)

    with hcol1:
        st.markdown(f"""
        <div class="bio-section">
            <h4 style="color:{GREEN_LIGHT};margin:0 0 12px 0;">
                Aquatic Habitat
            </h4>
            <div style="color:{TEXT_SECONDARY};font-size:0.85rem;
                        margin-bottom:4px;">
                Water Feature Diversity
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:1.4rem;
                        font-weight:700;">
                {habitat['water_diversity']} types
            </div>
            <div style="color:{TEXT_SECONDARY};font-size:0.8rem;
                        margin-top:4px;">
                {', '.join(html_module.escape(str(wt)) for wt in habitat['water_types']) if habitat['water_types']
                 else 'None detected'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="bio-section">
            <h4 style="color:{GREEN_LIGHT};margin:0 0 12px 0;">
                Soil Ecosystem
            </h4>
            <div style="color:{TEXT_SECONDARY};font-size:0.85rem;
                        margin-bottom:4px;">
                Soil Quality Index
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:1.4rem;
                        font-weight:700;">
                {habitat['soil_quality']:.0%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with hcol2:
        st.markdown(f"""
        <div class="bio-section">
            <h4 style="color:{GREEN_LIGHT};margin:0 0 12px 0;">
                Terrain Diversity
            </h4>
            <div style="color:{TEXT_SECONDARY};font-size:0.85rem;
                        margin-bottom:4px;">
                Elevation Range
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:1.4rem;
                        font-weight:700;">
                {habitat['elevation_range_m']:.0f} m
            </div>
            <div style="color:{TEXT_SECONDARY};font-size:0.8rem;
                        margin-top:4px;">
                Terrain variety: {habitat['terrain_variety']:.0%}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="bio-section">
            <h4 style="color:{GREEN_LIGHT};margin:0 0 12px 0;">
                Climate Suitability
            </h4>
            <div style="color:{TEXT_SECONDARY};font-size:0.85rem;
                        margin-bottom:4px;">
                Temperature / Precipitation
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:1.4rem;
                        font-weight:700;">
                {habitat['temperature_c']:.1f} C &nbsp;|&nbsp;
                {habitat['precipitation_7d_mm']:.1f} mm/7d
            </div>
            <div style="color:{TEXT_SECONDARY};font-size:0.8rem;
                        margin-top:4px;">
                Suitability: {habitat['climate_suitability']:.0%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Threat assessment section ───────────────────────────────────────────
    st.markdown(f"### Threat Assessment")

    if threat == "Critical":
        threat_color = ACCENT_RED
    elif threat == "High":
        threat_color = ACCENT_AMBER
    elif threat == "Moderate":
        threat_color = ACCENT_BLUE
    else:
        threat_color = GREEN_PRIMARY

    st.markdown(f"""
    <div class="bio-section" style="border-left:4px solid {threat_color};">
        <div style="display:flex;justify-content:space-between;
                    align-items:center;margin-bottom:12px;">
            <h4 style="color:{TEXT_PRIMARY};margin:0;">
                Overall Threat Level
            </h4>
            <span class="threat-badge"
                  style="background:{threat_color};
                         color:{'#000' if threat == 'High' else '#fff'};">
                {threat}
            </span>
        </div>
        <div style="color:{TEXT_SECONDARY};font-size:0.85rem;">
            Species observed: <strong style="color:{TEXT_PRIMARY};">
            {summary['total_observations']}</strong> &nbsp;|&nbsp;
            Kingdoms represented: <strong style="color:{TEXT_PRIMARY};">
            {summary['kingdom_diversity']}</strong> &nbsp;|&nbsp;
            Shannon Index: <strong style="color:{TEXT_PRIMARY};">
            {summary['shannon_index']}</strong> &nbsp;|&nbsp;
            Density: <strong style="color:{TEXT_PRIMARY};">
            {summary['species_density']} obs/km2</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Recommendations ─────────────────────────────────────────────────────
    st.markdown(f"### Conservation Recommendations")
    for i, rec in enumerate(recs, 1):
        st.markdown(f"""
        <div style="background:{BG_CARD};border-radius:8px;padding:12px 16px;
                    margin-bottom:8px;border-left:3px solid {GREEN_MEDIUM};">
            <span style="color:{GREEN_LIGHT};font-weight:700;
                         margin-right:8px;">{i}.</span>
            <span style="color:{TEXT_PRIMARY};font-size:0.9rem;">
                {rec}
            </span>
        </div>
        """, unsafe_allow_html=True)
