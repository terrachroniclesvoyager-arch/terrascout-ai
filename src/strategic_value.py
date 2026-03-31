"""
Strategic Value Assessment AI module for TerraScout AI.
Computes overall strategic value of a geographic location for different
stakeholder categories: government, defense (military), commercial,
environmental, and humanitarian.  Uses all available data sources to produce
a multi-dimensional score, conflict matrix, key-asset inventory, and
actionable recommendations.
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# STAKEHOLDER PROFILES
# ---------------------------------------------------------------------------
STAKEHOLDER_PROFILES = {
    "government": {
        "label": "Government",
        "color": "#3b82f6",
        "icon": "building-columns",
        "priorities": ["infrastructure", "population", "services"],
        "description": "Public administration, zoning, civic planning",
    },
    "defense": {
        "label": "Defense",
        "color": "#64748b",
        "icon": "shield-halved",
        "priorities": ["terrain control", "elevation", "access"],
        "description": "Military positioning, terrain dominance, logistics",
    },
    "commercial": {
        "label": "Commercial",
        "color": "#f59e0b",
        "icon": "industry",
        "priorities": ["transport", "infrastructure", "market"],
        "description": "Market access, supply-chain viability, ROI potential",
    },
    "environmental": {
        "label": "Environmental",
        "color": "#22c55e",
        "icon": "leaf",
        "priorities": ["biodiversity", "conservation", "sustainability"],
        "description": "Ecosystem health, protected status, sustainability",
    },
    "humanitarian": {
        "label": "Humanitarian",
        "color": "#ef4444",
        "icon": "hand-holding-heart",
        "priorities": ["access", "safety", "water", "shelter"],
        "description": "Aid delivery, shelter feasibility, water/safety",
    },
}

# ---------------------------------------------------------------------------
# SCORING HELPERS
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _safe_avg(values: list) -> float:
    clean = [v for v in values if v is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def _count_elements(data, tag_key: str | None = None,
                    tag_value: str | None = None) -> int:
    """Count Overpass elements, optionally filtering by a tag."""
    elems = (data if isinstance(data, dict) else {}).get("elements", [])
    if tag_key is None:
        return len(elems)
    count = 0
    for e in elems:
        tags = e.get("tags", {}) if isinstance(e, dict) else {}
        if tags.get(tag_key) == tag_value or (tag_value is None and tag_key in tags):
            count += 1
    return count


def _has_protected(protected) -> bool:
    elems = (protected if isinstance(protected, dict) else {}).get("elements", [])
    return len(elems) > 0


# ---------------------------------------------------------------------------
# SUB-DIMENSION SCORES  (each returns 0-100)
# ---------------------------------------------------------------------------

def _score_infrastructure_density(landuse) -> float:
    buildings = _count_elements(landuse, "building")
    return _clamp(buildings * 0.5, 0, 100)


def _score_services(landuse) -> float:
    highways = _count_elements(landuse, "highway")
    parks = _count_elements(landuse, "leisure", "park")
    return _clamp((highways * 0.8 + parks * 3.0), 0, 100)


def _score_transport(landuse) -> float:
    highways = _count_elements(landuse, "highway")
    return _clamp(highways * 1.2, 0, 100)


def _score_development_potential(soil, weather) -> float:
    score = 50.0
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    temp = current.get("temperature_2m", 15) if isinstance(current, dict) else 15
    if 5 < temp < 35:
        score += 20.0
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    if isinstance(props, dict):
        layers = props.get("layers", [])
        if isinstance(layers, list) and len(layers) > 0:
            score += 15.0
    return _clamp(score, 0, 100)


def _score_elevation_advantage(elev) -> float:
    d = elev if isinstance(elev, dict) else {}
    center = d.get("center_elevation", 0)
    avg = d.get("avg_elevation", 0)
    diff = center - avg
    score = 50.0 + diff * 0.5
    return _clamp(score, 0, 100)


def _score_terrain_difficulty(elev) -> float:
    d = elev if isinstance(elev, dict) else {}
    mn = d.get("min_elevation", 0)
    mx = d.get("max_elevation", 0)
    relief = mx - mn
    return _clamp(relief * 0.3, 0, 100)


def _score_access_control(landuse) -> float:
    highways = _count_elements(landuse, "highway")
    score = 70.0 if highways < 10 else max(10, 70.0 - highways * 1.5)
    return _clamp(score, 0, 100)


def _score_observation_potential(elev) -> float:
    d = elev if isinstance(elev, dict) else {}
    center = d.get("center_elevation", 0)
    mx = d.get("max_elevation", 0)
    if mx <= 0:
        return 30.0
    ratio = center / mx if mx > 0 else 0
    return _clamp(ratio * 100, 0, 100)


def _score_market_access(landuse) -> float:
    commercial = _count_elements(landuse, "landuse", "commercial")
    retail = _count_elements(landuse, "landuse", "retail")
    return _clamp((commercial + retail) * 8.0, 0, 100)


def _score_resource_availability(water, soil) -> float:
    water_elems = _count_elements(water)
    score = water_elems * 5.0
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    if isinstance(props, dict) and props.get("layers"):
        score += 20.0
    return _clamp(score, 0, 100)


def _score_biodiversity_proxy(protected, water) -> float:
    prot_count = _count_elements(protected)
    water_count = _count_elements(water)
    return _clamp(prot_count * 12.0 + water_count * 4.0, 0, 100)


def _score_protected_status(protected) -> float:
    return _clamp(_count_elements(protected) * 15.0, 0, 100)


def _score_ecosystem_health(water, weather) -> float:
    w_count = _count_elements(water)
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    humidity = (current if isinstance(current, dict) else {}).get(
        "relative_humidity_2m", 50)
    return _clamp(w_count * 5.0 + humidity * 0.4, 0, 100)


def _score_sustainability(protected, quakes) -> float:
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    seismic_penalty = min(len(features) * 2.0, 40.0)
    prot_bonus = _count_elements(protected) * 10.0
    return _clamp(60.0 + prot_bonus - seismic_penalty, 0, 100)


def _score_water_access(water) -> float:
    return _clamp(_count_elements(water) * 6.0, 0, 100)


def _score_shelter_potential(landuse) -> float:
    buildings = _count_elements(landuse, "building")
    return _clamp(buildings * 0.6, 0, 100)


def _score_safety(quakes, weather) -> float:
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    mags = [
        f.get("properties", {}).get("mag", 0)
        for f in features
        if isinstance(f, dict) and f.get("properties", {}).get("mag") is not None
    ]
    max_mag = max(mags) if mags else 0
    seismic_penalty = max_mag * 8.0
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    wind = (current if isinstance(current, dict) else {}).get("wind_speed_10m", 0)
    wind_penalty = max(0, (wind - 40) * 0.8) if wind else 0
    return _clamp(90.0 - seismic_penalty - wind_penalty, 0, 100)


def _score_aid_access(landuse) -> float:
    highways = _count_elements(landuse, "highway")
    return _clamp(highways * 1.5, 0, 100)


# ---------------------------------------------------------------------------
# CONFLICT MATRIX
# ---------------------------------------------------------------------------

_CONFLICT_PAIRS = [
    ("defense", "environmental", 0.7,
     "Military activity often disrupts protected ecosystems"),
    ("commercial", "environmental", 0.6,
     "Commercial development can threaten conservation areas"),
    ("government", "defense", 0.2,
     "Potential zoning conflicts with military land use"),
    ("commercial", "humanitarian", 0.3,
     "Market-driven development may displace vulnerable populations"),
    ("defense", "humanitarian", 0.5,
     "Security operations can impede humanitarian access"),
    ("government", "commercial", 0.15,
     "Regulatory burden versus commercial freedom"),
    ("government", "environmental", 0.1,
     "Infrastructure projects may affect environmental areas"),
    ("government", "humanitarian", 0.1,
     "Bureaucratic delays in aid distribution"),
    ("commercial", "defense", 0.35,
     "Commercial logistics vs military restricted zones"),
    ("environmental", "humanitarian", 0.2,
     "Conservation restrictions may limit shelter construction"),
]


def _build_conflict_matrix(scores: dict) -> list:
    """Return list of conflict dicts with intensity scaled by score gap."""
    conflicts = []
    for a, b, base_intensity, reason in _CONFLICT_PAIRS:
        sa = scores.get(a, {}).get("overall", 0)
        sb = scores.get(b, {}).get("overall", 0)
        gap_factor = abs(sa - sb) / 100.0
        intensity = _clamp(base_intensity * 100 * (0.5 + gap_factor), 0, 100)
        conflicts.append({
            "stakeholder_a": a,
            "stakeholder_b": b,
            "intensity": round(intensity, 1),
            "reason": reason,
        })
    return sorted(conflicts, key=lambda c: c["intensity"], reverse=True)


# ---------------------------------------------------------------------------
# KEY ASSETS & RECOMMENDATIONS
# ---------------------------------------------------------------------------

def _identify_key_assets(elev, water, landuse, protected, quakes) -> list:
    assets = []
    d = elev if isinstance(elev, dict) else {}
    center_elev = d.get("center_elevation", 0)
    if center_elev > 500:
        assets.append({
            "type": "High Ground",
            "detail": f"Elevation {center_elev:.0f} m -- strategic vantage point",
        })
    water_count = _count_elements(water)
    if water_count > 0:
        assets.append({
            "type": "Water Resources",
            "detail": f"{water_count} water feature(s) in area",
        })
    building_count = _count_elements(landuse, "building")
    if building_count > 20:
        assets.append({
            "type": "Built Infrastructure",
            "detail": f"{building_count} structures detected",
        })
    highway_count = _count_elements(landuse, "highway")
    if highway_count > 5:
        assets.append({
            "type": "Transport Network",
            "detail": f"{highway_count} road segment(s)",
        })
    if _has_protected(protected):
        prot_count = _count_elements(protected)
        assets.append({
            "type": "Protected Areas",
            "detail": f"{prot_count} protected zone(s) nearby",
        })
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    if len(features) > 10:
        assets.append({
            "type": "Seismic Activity (Risk)",
            "detail": f"{len(features)} earthquake(s) recorded in past year",
        })
    if not assets:
        assets.append({
            "type": "Baseline Terrain",
            "detail": "No exceptional assets identified; standard terrain",
        })
    return assets


def _generate_recommendations(scores: dict, conflicts: list,
                               assets: list) -> list:
    recs = []
    top_stakeholder = max(scores, key=lambda k: scores[k].get("overall", 0))
    top_score = scores[top_stakeholder]["overall"]
    recs.append(
        f"Primary stakeholder interest: "
        f"{STAKEHOLDER_PROFILES[top_stakeholder]['label']} "
        f"(score {top_score:.0f}/100)."
    )
    if conflicts and conflicts[0]["intensity"] > 40:
        c = conflicts[0]
        la = STAKEHOLDER_PROFILES[c["stakeholder_a"]]["label"]
        lb = STAKEHOLDER_PROFILES[c["stakeholder_b"]]["label"]
        recs.append(
            f"Highest conflict: {la} vs {lb} "
            f"(intensity {c['intensity']:.0f}%). {c['reason']}."
        )
    asset_types = [a["type"] for a in assets]
    if "Water Resources" in asset_types:
        recs.append(
            "Water resources present -- critical for humanitarian and "
            "agricultural planning."
        )
    if "High Ground" in asset_types:
        recs.append(
            "Elevated terrain provides observation advantage; "
            "consider for defense or communications infrastructure."
        )
    if "Protected Areas" in asset_types:
        recs.append(
            "Protected zones restrict development; environmental impact "
            "assessment required before any construction."
        )
    if "Seismic Activity (Risk)" in asset_types:
        recs.append(
            "Significant seismic activity recorded; structural resilience "
            "measures recommended for all construction."
        )
    low_stakeholder = min(scores, key=lambda k: scores[k].get("overall", 0))
    low_score = scores[low_stakeholder]["overall"]
    if low_score < 30:
        recs.append(
            f"Low viability for "
            f"{STAKEHOLDER_PROFILES[low_stakeholder]['label']} "
            f"operations (score {low_score:.0f}/100); additional investment "
            f"or alternative site recommended."
        )
    return recs


# ---------------------------------------------------------------------------
# MAIN COMPUTATION  (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_strategic_value(lat: float, lon: float) -> dict:
    """
    Fetch all data sources and compute multi-stakeholder strategic value
    for the given coordinates.

    Returns
    -------
    dict with keys:
        stakeholder_scores  - per-profile breakdown
        overall_significance - single 0-100 number
        conflict_matrix     - list of conflict dicts
        key_assets          - list of asset dicts
        strategic_recommendations - list of strings
    """
    # -- fetch data --------------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elev = fetch_elevation_grid(lat, lon)
    landuse = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    quakes = fetch_earthquakes(lat, lon)

    # -- per-stakeholder scores -------------------------------------------
    gov_dims = {
        "infrastructure": _score_infrastructure_density(landuse),
        "services": _score_services(landuse),
        "transport": _score_transport(landuse),
        "development_potential": _score_development_potential(soil, weather),
    }
    gov_overall = _safe_avg(list(gov_dims.values()))

    def_dims = {
        "elevation_advantage": _score_elevation_advantage(elev),
        "terrain_difficulty": _score_terrain_difficulty(elev),
        "access_control": _score_access_control(landuse),
        "observation_potential": _score_observation_potential(elev),
    }
    def_overall = _safe_avg(list(def_dims.values()))

    com_dims = {
        "market_access": _score_market_access(landuse),
        "infrastructure": _score_infrastructure_density(landuse),
        "transport": _score_transport(landuse),
        "resource_availability": _score_resource_availability(water, soil),
    }
    com_overall = _safe_avg(list(com_dims.values()))

    env_dims = {
        "biodiversity": _score_biodiversity_proxy(protected, water),
        "protected_status": _score_protected_status(protected),
        "ecosystem_health": _score_ecosystem_health(water, weather),
        "sustainability": _score_sustainability(protected, quakes),
    }
    env_overall = _safe_avg(list(env_dims.values()))

    hum_dims = {
        "water_access": _score_water_access(water),
        "shelter_potential": _score_shelter_potential(landuse),
        "safety": _score_safety(quakes, weather),
        "aid_access": _score_aid_access(landuse),
    }
    hum_overall = _safe_avg(list(hum_dims.values()))

    stakeholder_scores = {
        "government": {"dimensions": gov_dims, "overall": round(gov_overall, 1)},
        "defense": {"dimensions": def_dims, "overall": round(def_overall, 1)},
        "commercial": {"dimensions": com_dims, "overall": round(com_overall, 1)},
        "environmental": {"dimensions": env_dims, "overall": round(env_overall, 1)},
        "humanitarian": {"dimensions": hum_dims, "overall": round(hum_overall, 1)},
    }

    overall_significance = round(
        _safe_avg([v["overall"] for v in stakeholder_scores.values()]), 1
    )

    conflict_matrix = _build_conflict_matrix(stakeholder_scores)
    key_assets = _identify_key_assets(elev, water, landuse, protected, quakes)
    strategic_recommendations = _generate_recommendations(
        stakeholder_scores, conflict_matrix, key_assets
    )

    return {
        "stakeholder_scores": stakeholder_scores,
        "overall_significance": overall_significance,
        "conflict_matrix": conflict_matrix,
        "key_assets": key_assets,
        "strategic_recommendations": strategic_recommendations,
    }


# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------

def _render_stakeholder_card(key: str, profile: dict, score_data: dict):
    """Render a single stakeholder score card."""
    color = profile["color"]
    overall = score_data.get("overall", 0)
    dims = score_data.get("dimensions", {})
    bar_width = max(1, int(overall))

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                    border-left:4px solid {color};border-radius:8px;
                    padding:14px 18px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:6px;">
                <span style="color:{color};font-weight:700;font-size:1.05rem;">
                    {profile['label']}</span>
                <span style="color:#e2e8f0;font-weight:700;font-size:1.15rem;">
                    {overall:.0f}<small style="color:#94a3b8;">/100</small></span>
            </div>
            <div style="background:#0f172a;border-radius:4px;height:8px;
                        margin-bottom:8px;">
                <div style="background:{color};width:{bar_width}%;
                            height:100%;border-radius:4px;"></div>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
        """ + "".join(
            f'<span style="background:#0f172a;color:#cbd5e1;'
            f'padding:2px 8px;border-radius:10px;font-size:0.78rem;">'
            f'{dim.replace("_", " ").title()}: {val:.0f}</span>'
            for dim, val in dims.items()
        ) + """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_radar_chart(stakeholder_scores: dict) -> go.Figure:
    """Build a Plotly radar chart overlaying all stakeholder profiles."""
    all_dims = sorted({
        dim
        for sd in stakeholder_scores.values()
        for dim in sd.get("dimensions", {})
    })
    if not all_dims:
        all_dims = ["n/a"]

    fig = go.Figure()
    for key, sd in stakeholder_scores.items():
        profile = STAKEHOLDER_PROFILES.get(key, {})
        dims = sd.get("dimensions", {})
        values = [dims.get(d, 0) for d in all_dims]
        values.append(values[0])  # close the polygon
        labels = [d.replace("_", " ").title() for d in all_dims]
        labels.append(labels[0])

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill="toself",
            name=profile.get("label", key),
            line=dict(color=profile.get("color", "#888")),
            fillcolor=profile.get("color", "#888"),
            opacity=0.25,
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#1e293b", linecolor="#334155",
                tickfont=dict(color="#94a3b8", size=9),
            ),
            angularaxis=dict(
                gridcolor="#1e293b", linecolor="#334155",
                tickfont=dict(color="#cbd5e1", size=10),
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e2e8f0"),
        legend=dict(
            font=dict(color="#e2e8f0", size=11),
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="#334155",
            borderwidth=1,
        ),
        margin=dict(t=40, b=40, l=60, r=60),
        height=460,
        title=dict(
            text="Multi-Stakeholder Radar Overlay",
            font=dict(color="#e2e8f0", size=14),
        ),
    )
    return fig


def _render_conflict_matrix(conflicts: list):
    """Render the conflict matrix as styled cards."""
    if not conflicts:
        st.info("No conflict data available.")
        return

    for c in conflicts:
        a_label = STAKEHOLDER_PROFILES.get(
            c["stakeholder_a"], {}
        ).get("label", c["stakeholder_a"])
        b_label = STAKEHOLDER_PROFILES.get(
            c["stakeholder_b"], {}
        ).get("label", c["stakeholder_b"])
        intensity = c.get("intensity", 0)
        reason = c.get("reason", "")

        if intensity >= 50:
            badge_color = "#ef4444"
            badge_text = "HIGH"
        elif intensity >= 25:
            badge_color = "#f59e0b"
            badge_text = "MEDIUM"
        else:
            badge_color = "#22c55e"
            badge_text = "LOW"

        bar_w = max(1, int(intensity))

        st.markdown(
            f"""
            <div style="background:#0f172a;border-radius:6px;padding:10px 14px;
                        margin-bottom:6px;border:1px solid #1e293b;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;">
                    <span style="color:#cbd5e1;font-size:0.9rem;">
                        {a_label} &harr; {b_label}</span>
                    <span style="background:{badge_color};color:#fff;
                           padding:2px 8px;border-radius:10px;
                           font-size:0.72rem;font-weight:600;">
                        {badge_text} {intensity:.0f}%</span>
                </div>
                <div style="background:#1e293b;border-radius:3px;height:5px;
                            margin:6px 0;">
                    <div style="background:{badge_color};width:{bar_w}%;
                                height:100%;border-radius:3px;"></div>
                </div>
                <div style="color:#64748b;font-size:0.78rem;">{reason}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# PUBLIC TAB RENDERER
# ---------------------------------------------------------------------------

def render_strategic_value_tab():
    """Render the Strategic Value Assessment tab in the Streamlit app."""

    # -- header ------------------------------------------------------------
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
        'border-radius:10px;padding:18px 22px;margin-bottom:14px;'
        'border-left:4px solid #64748b;">'
        '<h4 style="color:#e2e8f0;margin:0 0 4px 0;">'
        'Strategic Value Assessment AI</h4>'
        '<p style="color:#94a3b8;margin:0;font-size:0.92rem;">'
        'Multi-stakeholder location analysis: government, defense, '
        'commercial, environmental &amp; humanitarian value scoring'
        '</p></div>',
        unsafe_allow_html=True,
    )

    # -- location selector -------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox(
            "Location Preset", list(ANALYSIS_PRESETS.keys()),
            key="sv_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with c2:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="sv_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="sv_lon",
        )

    run_btn = st.button(
        "Assess Strategic Value", type="primary",
        key="sv_run", use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and click **Assess Strategic Value** "
            "to run the multi-stakeholder analysis."
        )
        return

    # -- progress ----------------------------------------------------------
    progress = st.progress(0, text="Initializing strategic assessment...")
    progress.progress(10, text="Collecting data sources...")
    result = compute_strategic_value(lat, lon)
    progress.progress(100, text="Assessment complete.")

    scores = result.get("stakeholder_scores", {})
    overall = result.get("overall_significance", 0)
    conflicts = result.get("conflict_matrix", [])
    assets = result.get("key_assets", [])
    recs = result.get("strategic_recommendations", [])

    # -- overall significance banner ---------------------------------------
    if overall >= 70:
        sig_color = "#22c55e"
        sig_label = "HIGH"
    elif overall >= 40:
        sig_color = "#f59e0b"
        sig_label = "MODERATE"
    else:
        sig_color = "#ef4444"
        sig_label = "LOW"

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);
                    border:1px solid {sig_color};border-radius:10px;
                    padding:20px 24px;text-align:center;margin:10px 0 18px 0;">
            <div style="color:#94a3b8;font-size:0.85rem;
                        text-transform:uppercase;letter-spacing:1.5px;">
                Overall Strategic Significance</div>
            <div style="color:{sig_color};font-size:2.4rem;
                        font-weight:800;margin:4px 0;">
                {overall:.0f}<span style="font-size:1.1rem;
                color:#64748b;">/100</span></div>
            <div style="display:inline-block;background:{sig_color};
                        color:#0f172a;padding:3px 14px;border-radius:12px;
                        font-size:0.82rem;font-weight:700;">
                {sig_label}</div>
            <div style="color:#64748b;font-size:0.8rem;margin-top:6px;">
                {lat:.4f}N, {lon:.4f}E</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- stakeholder cards -------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin-bottom:8px;">'
        'Stakeholder Scores</h5>',
        unsafe_allow_html=True,
    )
    left_col, right_col = st.columns(2)
    keys = list(STAKEHOLDER_PROFILES.keys())
    for idx, key in enumerate(keys):
        target_col = left_col if idx % 2 == 0 else right_col
        with target_col:
            _render_stakeholder_card(
                key, STAKEHOLDER_PROFILES[key], scores.get(key, {}),
            )

    # -- radar chart -------------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:16px 0 8px 0;">'
        'Multi-Stakeholder Radar</h5>',
        unsafe_allow_html=True,
    )
    fig = _render_radar_chart(scores)
    st.plotly_chart(fig, use_container_width=True, key="strval_pchart1")

    # -- conflict matrix ---------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:16px 0 8px 0;">'
        'Conflict Matrix</h5>',
        unsafe_allow_html=True,
    )
    _render_conflict_matrix(conflicts)

    # -- key assets --------------------------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:16px 0 8px 0;">'
        'Key Assets</h5>',
        unsafe_allow_html=True,
    )
    for asset in assets:
        atype = asset.get("type", "Unknown")
        detail = asset.get("detail", "")
        st.markdown(
            f"""
            <div style="background:#0f172a;border-radius:6px;padding:10px 14px;
                        margin-bottom:6px;border:1px solid #1e293b;
                        display:flex;align-items:center;gap:12px;">
                <span style="color:#22c55e;font-weight:600;
                             min-width:160px;">{atype}</span>
                <span style="color:#94a3b8;font-size:0.88rem;">{detail}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- strategic recommendations -----------------------------------------
    st.markdown(
        '<h5 style="color:#e2e8f0;margin:16px 0 8px 0;">'
        'Strategic Recommendations</h5>',
        unsafe_allow_html=True,
    )
    for i, rec in enumerate(recs, 1):
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);
                        border-radius:6px;padding:10px 14px;margin-bottom:6px;
                        border-left:3px solid #64748b;">
                <span style="color:#64748b;font-weight:600;
                             margin-right:8px;">{i}.</span>
                <span style="color:#cbd5e1;font-size:0.9rem;">{rec}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
