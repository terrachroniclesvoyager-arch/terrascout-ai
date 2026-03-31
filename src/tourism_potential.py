"""
Tourism Potential AI module for TerraScout AI.
Evaluates tourism attractiveness and visitor potential for any geographic
location using multi-source data: terrain, climate, biodiversity,
infrastructure, water features, and protected areas.
All data from free APIs -- no keys required.
"""

import logging
import math

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
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# TOURISM CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

TOURISM_CATEGORIES = {
    "nature": {
        "name": "Nature Tourism",
        "icon": "🌳",
        "color": "#22c55e",
    },
    "adventure": {
        "name": "Adventure Tourism",
        "icon": "🧗",
        "color": "#f97316",
    },
    "cultural": {
        "name": "Cultural / Heritage",
        "icon": "🏛️",
        "color": "#a855f7",
    },
    "wellness": {
        "name": "Wellness / Spa",
        "icon": "🧘",
        "color": "#06b6d4",
    },
    "eco": {
        "name": "Eco-Tourism",
        "icon": "🌿",
        "color": "#10b981",
    },
    "beach": {
        "name": "Beach / Coastal",
        "icon": "🏖️",
        "color": "#38bdf8",
    },
    "mountain": {
        "name": "Mountain / Alpine",
        "icon": "🏔️",
        "color": "#64748b",
    },
    "rural": {
        "name": "Rural / Agri-Tourism",
        "icon": "🌾",
        "color": "#eab308",
    },
}


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, val))


# ═══════════════════════════════════════════════════════════════════════════════
# CORE COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_tourism_potential(lat: float, lon: float) -> dict:
    """
    Compute a comprehensive tourism potential assessment for a location.
    Returns overall score, type-specific scores, general indices,
    attraction counts, and recommendations.
    """
    # ------------------------------------------------------------------
    # 1. Fetch all data sources
    # ------------------------------------------------------------------
    try:
        weather = fetch_weather_data(lat, lon)
    except Exception as exc:
        logger.warning("Weather fetch error: %s", exc)
        weather = {}

    try:
        elevation = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=7)
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        elevation = {}

    try:
        water = fetch_water_features(lat, lon, radius=5000)
    except Exception as exc:
        logger.warning("Water fetch error: %s", exc)
        water = {}

    try:
        infra = fetch_landuse_infrastructure(lat, lon, radius=3000)
    except Exception as exc:
        logger.warning("Infrastructure fetch error: %s", exc)
        infra = {}

    try:
        protected = fetch_protected_areas(lat, lon, radius=10000)
    except Exception as exc:
        logger.warning("Protected areas fetch error: %s", exc)
        protected = {}

    try:
        inat = fetch_biodiversity(lat, lon, radius_km=10)
        gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
        bio = compute_species_breakdown(inat, gbif)
    except Exception as exc:
        logger.warning("Biodiversity fetch error: %s", exc)
        bio = {}

    # ------------------------------------------------------------------
    # 2. Parse raw elements
    # ------------------------------------------------------------------
    water_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    infra_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    protected_elements = (protected if isinstance(protected, dict) else {}).get("elements", [])

    # ------------------------------------------------------------------
    # 3. Attraction analysis
    # ------------------------------------------------------------------
    # -- Natural attractions --
    water_count = len(water_elements)
    rivers = sum(1 for e in water_elements if e.get("tags", {}).get("waterway") in ("river", "stream"))
    lakes = sum(1 for e in water_elements if e.get("tags", {}).get("natural") == "water")
    springs = sum(1 for e in water_elements if e.get("tags", {}).get("natural") == "spring")

    center_elev = elevation.get("center_elevation", 0) or 0
    max_elev = elevation.get("max_elevation", 0) or 0
    min_elev = elevation.get("min_elevation", 0) or 0
    elev_range = max_elev - min_elev

    scenic_mountains = 1 if center_elev > 1000 or elev_range > 500 else 0

    inat_total = (bio.get("inat_total") or 0)
    gbif_total = (bio.get("gbif_total") or 0)
    gbif_unique = (bio.get("gbif_unique_species") or 0)
    total_species = inat_total + gbif_total
    wildlife_watching = 1 if total_species > 50 else 0

    parks_count = len(protected_elements)

    natural_attractions = water_count + scenic_mountains + wildlife_watching + parks_count

    # -- Cultural attractions --
    hotels = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") in ("hotel", "motel", "guest_house")
    )
    restaurants = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("amenity") == "restaurant"
           or e.get("tags", {}).get("amenity") == "cafe"
    )
    museums = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") == "museum"
           or e.get("tags", {}).get("amenity") == "museum"
    )
    monuments = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("historic") in ("monument", "memorial", "castle", "ruins")
    )
    cultural_attractions = hotels + restaurants + museums + monuments

    # -- Activity analysis --
    trails = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("highway") in ("path", "footway", "track", "cycleway")
    )
    slope_factor = min(elev_range / 500.0, 1.0) if elev_range > 0 else 0
    hiking_potential = min(trails * 5 + slope_factor * 30, 100)

    water_sports = min((rivers + lakes) * 15, 100)
    climbing = min(slope_factor * 60 + (1 if center_elev > 1500 else 0) * 40, 100)

    # -- Infrastructure analysis --
    hostels = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") == "hostel"
    )
    camp_sites = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") == "camp_site"
    )
    accommodation_count = hotels + hostels + camp_sites
    tourist_info = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("tourism") == "information"
    )
    parking = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("amenity") == "parking"
    )
    roads = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("highway") in (
            "primary", "secondary", "tertiary", "motorway",
            "trunk", "residential", "unclassified",
        )
    )

    # ------------------------------------------------------------------
    # 4. Climate attractiveness
    # ------------------------------------------------------------------
    current = weather.get("current", {}) if isinstance(weather, dict) else {}
    daily = weather.get("daily", {}) if isinstance(weather, dict) else {}
    temp_now = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    cloud_cover = current.get("cloud_cover")
    precip_now = current.get("precipitation")

    # Comfort index (ideal temp 18-28 C)
    comfort = 50.0
    if temp_now is not None:
        if 18 <= temp_now <= 28:
            comfort = 95.0
        elif 14 <= temp_now < 18 or 28 < temp_now <= 32:
            comfort = 75.0
        elif 8 <= temp_now < 14 or 32 < temp_now <= 36:
            comfort = 55.0
        elif temp_now < 0 or temp_now > 40:
            comfort = 15.0
        else:
            comfort = 35.0

    # Sunshine bonus
    sunshine = 50.0
    if cloud_cover is not None:
        sunshine = max(0.0, 100.0 - cloud_cover)

    # Rain penalty
    rain_score = 80.0
    if precip_now is not None:
        if precip_now < 0.5:
            rain_score = 95.0
        elif precip_now < 2.0:
            rain_score = 70.0
        elif precip_now < 5.0:
            rain_score = 45.0
        else:
            rain_score = 20.0

    # Humidity
    humidity_score = 60.0
    if humidity is not None:
        if 30 <= humidity <= 65:
            humidity_score = 90.0
        elif 20 <= humidity < 30 or 65 < humidity <= 80:
            humidity_score = 65.0
        else:
            humidity_score = 35.0

    climate_appeal = (comfort * 0.40 + sunshine * 0.25
                      + rain_score * 0.20 + humidity_score * 0.15)

    # Seasonal variability
    temps_max_list = daily.get("temperature_2m_max", [])
    temps_min_list = daily.get("temperature_2m_min", [])
    valid_maxes = [t for t in temps_max_list if t is not None]
    valid_mins = [t for t in temps_min_list if t is not None]
    seasonal_var = 0.0
    if valid_maxes and valid_mins:
        seasonal_var = max(valid_maxes) - min(valid_mins)

    # ------------------------------------------------------------------
    # 5. Tourism-type suitability scores (0-100)
    # ------------------------------------------------------------------
    type_scores = {}

    # Nature Tourism
    nature_s = _clamp(
        min(water_count * 6, 30)
        + min(parks_count * 10, 25)
        + min(total_species / 5, 25)
        + (15 if scenic_mountains else 0)
        + climate_appeal * 0.05
    )
    type_scores["nature"] = round(nature_s)

    # Adventure Tourism
    adventure_s = _clamp(
        hiking_potential * 0.30
        + climbing * 0.25
        + water_sports * 0.20
        + min(elev_range / 10, 25)
    )
    type_scores["adventure"] = round(adventure_s)

    # Cultural / Heritage
    cultural_s = _clamp(
        min(museums * 15, 30)
        + min(monuments * 10, 30)
        + min(restaurants * 3, 20)
        + min(accommodation_count * 4, 20)
    )
    type_scores["cultural"] = round(cultural_s)

    # Wellness / Spa
    wellness_s = _clamp(
        climate_appeal * 0.40
        + min(springs * 15, 25)
        + min(accommodation_count * 5, 20)
        + (15 if 18 <= (temp_now or 15) <= 30 else 5)
    )
    type_scores["wellness"] = round(wellness_s)

    # Eco-Tourism
    eco_s = _clamp(
        min(total_species / 3, 30)
        + min(parks_count * 12, 30)
        + min(water_count * 4, 20)
        + (20 if gbif_unique > 30 else gbif_unique * 0.6)
    )
    type_scores["eco"] = round(eco_s)

    # Beach / Coastal
    coastal_water = sum(
        1 for e in water_elements
        if e.get("tags", {}).get("natural") == "water"
        or e.get("tags", {}).get("natural") == "coastline"
        or e.get("tags", {}).get("natural") == "beach"
    )
    beach_s = _clamp(
        min(coastal_water * 15, 40)
        + climate_appeal * 0.30
        + (20 if center_elev < 50 else 5)
        + min(accommodation_count * 3, 10)
    )
    type_scores["beach"] = round(beach_s)

    # Mountain / Alpine
    mountain_s = _clamp(
        min(center_elev / 30, 30)
        + min(elev_range / 10, 30)
        + hiking_potential * 0.20
        + climbing * 0.10
        + (10 if trails > 3 else trails * 3)
    )
    type_scores["mountain"] = round(mountain_s)

    # Rural / Agri-Tourism
    farmland = sum(
        1 for e in infra_elements
        if e.get("tags", {}).get("landuse") in ("farmland", "vineyard", "orchard", "meadow")
    )
    rural_s = _clamp(
        min(farmland * 8, 35)
        + min(trails * 5, 20)
        + climate_appeal * 0.15
        + (15 if accommodation_count >= 1 else 0)
        + (15 if restaurants >= 1 else 0)
    )
    type_scores["rural"] = round(rural_s)

    # ------------------------------------------------------------------
    # 6. General indices (0-100)
    # ------------------------------------------------------------------
    idx_natural = _clamp(
        min(elev_range / 5, 25)
        + min(water_count * 5, 25)
        + min(total_species / 4, 25)
        + min(parks_count * 8, 25)
    )
    idx_infrastructure = _clamp(
        min(accommodation_count * 8, 35)
        + min(restaurants * 5, 30)
        + min(roads * 2, 35)
    )
    idx_climate = _clamp(climate_appeal)
    idx_activity = _clamp(
        min(elev_range / 8, 30)
        + water_sports * 0.30
        + hiking_potential * 0.25
        + climbing * 0.15
    )
    idx_accessibility = _clamp(
        min(roads * 3, 40)
        + min(parking * 8, 25)
        + min(tourist_info * 12, 20)
        + (15 if accommodation_count >= 2 else accommodation_count * 7)
    )

    indices = {
        "Natural Attractions": round(idx_natural),
        "Tourism Infrastructure": round(idx_infrastructure),
        "Climate Appeal": round(idx_climate),
        "Activity Potential": round(idx_activity),
        "Accessibility": round(idx_accessibility),
    }

    # ------------------------------------------------------------------
    # 7. Overall Tourism Score
    # ------------------------------------------------------------------
    overall = round(
        idx_natural * 0.25
        + idx_infrastructure * 0.20
        + idx_climate * 0.25
        + idx_activity * 0.15
        + idx_accessibility * 0.15
    )
    overall = int(_clamp(overall))

    # ------------------------------------------------------------------
    # 8. Best tourism type
    # ------------------------------------------------------------------
    if type_scores:
        best_key = max(type_scores, key=type_scores.get)
    else:
        best_key = "nature"
    best_tourism_type = TOURISM_CATEGORIES[best_key]["name"]

    # ------------------------------------------------------------------
    # 9. Recommendations
    # ------------------------------------------------------------------
    recommendations = []

    if idx_natural >= 60:
        recommendations.append(
            ("Leverage Natural Assets",
             "The area has strong natural features -- promote hiking trails, scenic viewpoints, and wildlife tours.",
             "#22c55e")
        )
    elif idx_natural < 30:
        recommendations.append(
            ("Enhance Natural Appeal",
             "Consider creating green spaces or nature trails to boost attractiveness.",
             "#eab308")
        )

    if idx_infrastructure < 40:
        recommendations.append(
            ("Improve Tourism Infrastructure",
             "Investment in accommodation, restaurants, and tourist information points would increase visitor capacity.",
             "#f97316")
        )

    if idx_climate >= 70:
        recommendations.append(
            ("Capitalize on Favorable Climate",
             "Year-round comfortable weather is a major draw -- market outdoor activities and open-air events.",
             "#06b6d4")
        )
    elif idx_climate < 40:
        recommendations.append(
            ("Address Climate Challenges",
             "Develop indoor attractions and seasonal events to compensate for less ideal weather conditions.",
             "#ef4444")
        )

    if type_scores.get("adventure", 0) >= 50:
        recommendations.append(
            ("Develop Adventure Offerings",
             "Terrain and water features support adventure tourism -- consider guided climbing, rafting, and trail networks.",
             "#f97316")
        )

    if type_scores.get("eco", 0) >= 50:
        recommendations.append(
            ("Promote Eco-Tourism",
             "Rich biodiversity and protected areas make this location ideal for sustainable eco-tourism programs.",
             "#10b981")
        )

    if idx_accessibility < 35:
        recommendations.append(
            ("Improve Access Routes",
             "Better road connections, signage, and parking would make the destination more visitor-friendly.",
             "#64748b")
        )

    if not recommendations:
        recommendations.append(
            ("Balanced Potential",
             "The location shows moderate tourism potential across multiple dimensions. A targeted strategy could amplify specific strengths.",
             "#a855f7")
        )

    # ------------------------------------------------------------------
    # 10. Assemble result
    # ------------------------------------------------------------------
    attractions_count = {
        "Water Features": water_count,
        "Rivers & Streams": rivers,
        "Lakes & Ponds": lakes,
        "Springs": springs,
        "Protected Areas": parks_count,
        "Hotels & Accommodation": accommodation_count,
        "Restaurants & Cafes": restaurants,
        "Museums": museums,
        "Monuments & Heritage": monuments,
        "Trails & Paths": trails,
        "Parking Areas": parking,
    }

    return {
        "overall": overall,
        "best_tourism_type": best_tourism_type,
        "type_scores": type_scores,
        "indices": indices,
        "attractions_count": attractions_count,
        "recommendations": recommendations,
        "climate": {
            "comfort": round(comfort),
            "sunshine": round(sunshine),
            "rain_score": round(rain_score),
            "humidity_score": round(humidity_score),
            "climate_appeal": round(climate_appeal),
            "seasonal_variability": round(seasonal_var, 1),
            "temp_now": temp_now,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _score_color(score: int) -> str:
    """Return a colour hex for a given 0-100 score."""
    if score >= 75:
        return "#22c55e"
    if score >= 55:
        return "#eab308"
    if score >= 35:
        return "#f97316"
    return "#ef4444"


def _score_label(score: int) -> str:
    """Return a human-readable label for a 0-100 score."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Limited"
    return "Very Low"


# ═══════════════════════════════════════════════════════════════════════════════
# STREAMLIT RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render_tourism_potential_tab() -> None:
    """Main render function for the Tourism Potential AI tab."""

    st.markdown("""
    <div class="tab-header" style="border-image:linear-gradient(90deg,#f97316,#eab308) 1;">
        <h4>🗺️ Tourism Potential AI</h4>
        <p>Evaluate tourism attractiveness and visitor potential using multi-source geospatial intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Location selector ──────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="tp_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    d_lat = p.get("lat", 41.90) if p else 41.90
    d_lon = p.get("lon", 12.50) if p else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Latitude", -90.0, 90.0, d_lat,
                step=0.01, key="tp_lat", format="%.4f",
            )
        with c2:
            lon = st.number_input(
                "Longitude", -180.0, 180.0, d_lon,
                step=0.01, key="tp_lon", format="%.4f",
            )

    # ── Run button ─────────────────────────────────────────────────────
    if st.button("🗺️ Assess Tourism Potential", type="primary", use_container_width=True):
        progress = st.progress(0, text="Initializing tourism analysis...")
        progress.progress(10, text="Gathering multi-source data...")
        result = compute_tourism_potential(lat, lon)
        progress.progress(100, text="Tourism assessment complete!")
        st.session_state["tp_result"] = {**result, "lat": lat, "lon": lon}

    # ── Guard: nothing to show yet ─────────────────────────────────────
    if "tp_result" not in st.session_state:
        return

    res = st.session_state["tp_result"]
    overall = res["overall"]
    best_type = res["best_tourism_type"]
    type_scores = res["type_scores"]
    indices = res["indices"]
    attractions = res["attractions_count"]
    climate = res["climate"]
    recommendations = res["recommendations"]
    r_lat = res["lat"]
    r_lon = res["lon"]

    st.markdown("---")

    # ── Overall Score ──────────────────────────────────────────────────
    oc = _score_color(overall)
    st.markdown(f"""
    <div style="text-align:center; padding:1.8rem; background:linear-gradient(135deg,#1a1a2e,#16213e);
                border-radius:16px; border:2px solid {oc}; margin-bottom:1.5rem;">
        <div style="font-size:3.8rem; font-weight:900; color:{oc};">{overall}</div>
        <div style="font-size:1.3rem; color:{oc}; font-weight:700;">{_score_label(overall)}</div>
        <div style="color:#94a3b8; margin-top:0.5rem;">Overall Tourism Potential Score</div>
        <div style="color:#64748b; font-size:0.85rem;">({r_lat:.4f}, {r_lon:.4f})</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Best Tourism Type Header ───────────────────────────────────────
    best_cat = None
    for k, v in TOURISM_CATEGORIES.items():
        if v["name"] == best_type:
            best_cat = v
            break
    if best_cat is None:
        best_cat = {"icon": "🗺️", "color": "#eab308", "name": best_type}

    st.markdown(f"""
    <div style="text-align:center; padding:1rem; background:#1a1a2e;
                border-radius:12px; border:1px solid {best_cat['color']}; margin-bottom:1.5rem;">
        <div style="font-size:1.6rem;">{best_cat['icon']}</div>
        <div style="font-size:1.1rem; font-weight:700; color:{best_cat['color']};">
            Best Match: {best_cat['name']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tourism Type Cards (4x2 grid) ─────────────────────────────────
    st.markdown("### Tourism Type Suitability")
    keys = list(TOURISM_CATEGORIES.keys())
    for row_start in range(0, 8, 4):
        cols = st.columns(4)
        for idx, col in enumerate(cols):
            cat_idx = row_start + idx
            if cat_idx >= len(keys):
                break
            cat_key = keys[cat_idx]
            cat = TOURISM_CATEGORIES[cat_key]
            sc = type_scores.get(cat_key, 0)
            sc_col = _score_color(sc)
            with col:
                st.markdown(f"""
                <div style="background:#1a1a2e; border-radius:12px; padding:1rem;
                            text-align:center; border-top:3px solid {cat['color']};
                            min-height:160px; margin-bottom:0.8rem;">
                    <div style="font-size:1.6rem;">{cat['icon']}</div>
                    <div style="font-size:1.8rem; font-weight:800; color:{sc_col};">{sc}</div>
                    <div style="font-weight:600; color:#e2e8f0; font-size:0.85rem;">
                        {cat['name']}
                    </div>
                    <div style="color:#64748b; font-size:0.72rem;">{_score_label(sc)}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Radar Chart of General Indices ─────────────────────────────────
    st.markdown("### Tourism Profile Radar")
    idx_labels = list(indices.keys())
    idx_values = list(indices.values())
    idx_values_closed = idx_values + [idx_values[0]]
    idx_labels_closed = idx_labels + [idx_labels[0]]

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=idx_values_closed,
        theta=idx_labels_closed,
        fill="toself",
        line_color="#f97316",
        fillcolor="rgba(249, 115, 22, 0.15)",
        name="Tourism Indices",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#64748b"),
            angularaxis=dict(color="#94a3b8"),
            bgcolor="#1a1a2e",
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        height=420,
        margin=dict(t=40, b=40, l=70, r=70),
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="toupot_pchart1")

    # ── Horizontal Bar: Type Scores ────────────────────────────────────
    st.markdown("### Tourism Type Scores")
    sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [TOURISM_CATEGORIES[k]["name"] for k, _ in sorted_types]
    bar_values = [v for _, v in sorted_types]
    bar_colors = [TOURISM_CATEGORIES[k]["color"] for k, _ in sorted_types]

    fig_bar = go.Figure(data=go.Bar(
        x=bar_values,
        y=bar_names,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v}" for v in bar_values],
        textposition="auto",
    ))
    fig_bar.update_layout(
        xaxis=dict(range=[0, 100], title="Suitability Score", color="#94a3b8"),
        yaxis=dict(autorange="reversed", color="#e2e8f0"),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        height=350,
        margin=dict(t=20, b=40, l=160, r=30),
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="toupot_pchart2")

    # ── Attractions Summary ────────────────────────────────────────────
    st.markdown("### Attractions & Amenities Summary")
    attr_items = list(attractions.items())
    rows = math.ceil(len(attr_items) / 4)
    for row in range(rows):
        cols = st.columns(4)
        for ci in range(4):
            ai = row * 4 + ci
            if ai >= len(attr_items):
                break
            a_name, a_count = attr_items[ai]
            with cols[ci]:
                st.markdown(f"""
                <div style="background:#1a1a2e; border-radius:10px; padding:0.9rem;
                            text-align:center; border:1px solid #2a2a4e; margin-bottom:0.5rem;">
                    <div style="font-size:1.6rem; font-weight:800; color:#eab308;">{a_count}</div>
                    <div style="color:#94a3b8; font-size:0.78rem;">{a_name}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Climate Appeal Metrics ─────────────────────────────────────────
    st.markdown("### Climate Appeal")
    cl_cols = st.columns(5)
    climate_metrics = [
        ("Comfort", climate.get("comfort", 0), "#22c55e"),
        ("Sunshine", climate.get("sunshine", 0), "#eab308"),
        ("Low Rain", climate.get("rain_score", 0), "#38bdf8"),
        ("Humidity", climate.get("humidity_score", 0), "#a855f7"),
        ("Overall", climate.get("climate_appeal", 0), "#f97316"),
    ]
    for i, (name, val, color) in enumerate(climate_metrics):
        with cl_cols[i]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border-radius:10px; padding:0.9rem;
                        text-align:center; border-top:3px solid {color}; margin-bottom:0.5rem;">
                <div style="font-size:1.8rem; font-weight:800; color:{color};">{val}</div>
                <div style="color:#94a3b8; font-size:0.78rem;">{name}</div>
            </div>
            """, unsafe_allow_html=True)

    temp_display = climate.get("temp_now")
    seasonal = climate.get("seasonal_variability", 0)
    temp_str = f"{temp_display:.1f} C" if temp_display is not None else "N/A"
    st.markdown(f"""
    <div style="background:#16213e; border-radius:10px; padding:0.8rem; margin-top:0.3rem;
                text-align:center; color:#94a3b8; font-size:0.88rem;">
        Current Temperature: <b style="color:#e2e8f0;">{temp_str}</b> &nbsp;|&nbsp;
        7-day Variability: <b style="color:#e2e8f0;">{seasonal} C</b>
    </div>
    """, unsafe_allow_html=True)

    # ── Recommendations ────────────────────────────────────────────────
    st.markdown("### Recommendations")
    for title, desc, color in recommendations:
        st.markdown(f"""
        <div style="background:#1a1a2e; border-left:4px solid {color}; padding:1rem;
                    margin:0.5rem 0; border-radius:0 10px 10px 0;">
            <div style="color:{color}; font-weight:700; font-size:1rem;">{title}</div>
            <div style="color:#94a3b8; font-size:0.88rem; margin-top:0.3rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
