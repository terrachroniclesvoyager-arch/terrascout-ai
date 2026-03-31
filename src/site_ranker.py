"""
Site Ranker AI — Compares and ranks multiple locations across configurable
criteria with weighted scoring. Perfect for site selection decisions.
Users pick 2-5 locations and the AI ranks them across all dimensions.
Uses: All deep_zone_analysis data sources.
"""

import logging

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_earthquakes,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_risk_assessment,
    compute_species_breakdown,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ── Ranking criteria ────────────────────────────────────────────────────────

CRITERIA = {
    "climate_comfort": {
        "name": "Climate Comfort",
        "desc": "Temperature, humidity, wind comfort",
        "color": "#ef4444",
        "weight": 1.0,
    },
    "water_access": {
        "name": "Water Access",
        "desc": "Proximity to water sources",
        "color": "#3b82f6",
        "weight": 1.0,
    },
    "soil_quality": {
        "name": "Soil Quality",
        "desc": "Fertility, pH, organic content",
        "color": "#10b981",
        "weight": 1.0,
    },
    "safety": {
        "name": "Safety",
        "desc": "Low seismic, flood, fire risk",
        "color": "#f59e0b",
        "weight": 1.5,
    },
    "biodiversity": {
        "name": "Biodiversity",
        "desc": "Species diversity and ecological richness",
        "color": "#22c55e",
        "weight": 0.8,
    },
    "accessibility": {
        "name": "Accessibility",
        "desc": "Roads, buildings, infrastructure",
        "color": "#8b5cf6",
        "weight": 0.8,
    },
    "terrain_ease": {
        "name": "Terrain Ease",
        "desc": "Flat, navigable terrain",
        "color": "#06b6d4",
        "weight": 0.8,
    },
}


@st.cache_data(ttl=1800)
def _score_site(lat: float, lon: float) -> dict:
    """Score a single site across all criteria."""
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}

    risk = compute_risk_assessment(earthquakes, water, weather, elev)
    species = compute_species_breakdown(inat, gbif)

    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20
    humidity = current.get("relative_humidity_2m", 50) or 50

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0

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

    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(w_elements)

    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))

    total_species = species.get("gbif_unique_species", 0) + len(species.get("top_species", []))

    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0
    flood_risk = risk.get("Flood", 0) if isinstance(risk, dict) else 0
    fire_risk = risk.get("Fire", 0) if isinstance(risk, dict) else 0

    # Score each criterion 0-10
    scores = {}

    # Climate comfort: best around 22C, 40-60% humidity, low wind
    temp_score = max(0, 10 - abs(avg_temp - 22) / 2)
    humid_score = max(0, 10 - abs(humidity - 50) / 5)
    wind_score = max(0, 10 - avg_wind / 8)
    scores["climate_comfort"] = round((temp_score + humid_score + wind_score) / 3, 1)

    # Water access
    scores["water_access"] = round(min(10, water_count / 3), 1)

    # Soil quality
    ph_score = max(0, 10 - abs(ph - 6.5) * 2)
    soc_score = min(10, soc / 3)
    scores["soil_quality"] = round((ph_score + soc_score) / 2, 1)

    # Safety (inverse of risk)
    avg_risk = (seismic_risk + flood_risk + fire_risk) / 3
    scores["safety"] = round(max(0, 10 - avg_risk), 1)

    # Biodiversity
    scores["biodiversity"] = round(min(10, total_species / 5), 1)

    # Accessibility
    scores["accessibility"] = round(min(10, (buildings + roads) / 8), 1)

    # Terrain ease
    scores["terrain_ease"] = round(max(0, min(10, 10 - elev_range / 30)), 1)

    # Weighted total
    weighted = sum(scores[k] * CRITERIA[k]["weight"] for k in scores)
    total_weight = sum(CRITERIA[k]["weight"] for k in scores)
    overall = round(weighted / total_weight, 1) if total_weight > 0 else 0

    return {
        "scores": scores,
        "overall": overall,
        "raw": {
            "temp": round(avg_temp, 1),
            "humidity": round(humidity),
            "wind": round(avg_wind, 1),
            "water_features": water_count,
            "soc": round(soc, 1),
            "ph": round(ph, 1),
            "species": total_species,
            "buildings": buildings,
            "roads": roads,
            "seismic_risk": round(seismic_risk, 1),
            "elev_range": round(elev_range, 0),
        },
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_site_ranker_tab():
    """Render the Site Ranker AI tab."""
    st.markdown("## Site Ranker AI")
    st.caption("Compare and rank multiple locations for site selection")

    # Initialize session state
    if "sr_sites" not in st.session_state:
        st.session_state["sr_sites"] = [
            {"name": "Rome, Italy", "lat": 41.90, "lon": 12.50},
            {"name": "Grand Canyon, USA", "lat": 36.11, "lon": -112.11},
        ]

    # ── Site input ──
    st.markdown("### Define Sites to Compare")

    sites = st.session_state["sr_sites"]
    updated_sites = []

    for i, site in enumerate(sites):
        cols = st.columns([2, 1, 1, 0.5])
        with cols[0]:
            name = st.text_input(f"Name", site["name"], key=f"sr_name_{i}")
        with cols[1]:
            slat = st.number_input("Lat", -90.0, 90.0, site["lat"],
                                   step=0.01, key=f"sr_lat_{i}", format="%.4f")
        with cols[2]:
            slon = st.number_input("Lon", -180.0, 180.0, site["lon"],
                                   step=0.01, key=f"sr_lon_{i}", format="%.4f")
        with cols[3]:
            if st.button("X", key=f"sr_del_{i}") and len(sites) > 2:
                continue
        updated_sites.append({"name": name, "lat": slat, "lon": slon})

    st.session_state["sr_sites"] = updated_sites

    if len(updated_sites) < 5:
        if st.button("+ Add Site", key="sr_add"):
            st.session_state["sr_sites"].append(
                {"name": f"Site {len(updated_sites) + 1}", "lat": 41.90, "lon": 12.50}
            )
            st.rerun()

    if st.button("Rank Sites", type="primary", use_container_width=True):
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, site in enumerate(updated_sites):
            status.text(f"Analyzing {site['name']}...")
            score_data = _score_site(site["lat"], site["lon"])
            results.append({
                "name": site["name"],
                "lat": site["lat"],
                "lon": site["lon"],
                **score_data,
            })
            progress.progress((i + 1) / len(updated_sites))

        progress.empty()
        status.empty()

        # Sort by overall score
        results.sort(key=lambda r: r["overall"], reverse=True)

        # ── Ranking display ──
        st.markdown("### Final Ranking")
        for rank, r in enumerate(results):
            if rank == 0:
                medal = "1st"
                border_color = "#f59e0b"
            elif rank == 1:
                medal = "2nd"
                border_color = "#94a3b8"
            elif rank == 2:
                medal = "3rd"
                border_color = "#b45309"
            else:
                medal = f"{rank + 1}th"
                border_color = "#555"

            overall_color = "#10b981" if r["overall"] >= 7 else "#f59e0b" if r["overall"] >= 5 else "#ef4444"

            st.markdown(f"""
            <div style="background:#1a1a2e; border:2px solid {border_color};
                        border-radius:12px; padding:16px; margin:8px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:{border_color}; font-size:24px; font-weight:bold;">
                            #{medal}
                        </span>
                        <span style="color:#eee; font-size:20px; font-weight:bold; margin-left:12px;">
                            {r['name']}
                        </span>
                        <span style="color:#888; font-size:12px; margin-left:8px;">
                            ({r['lat']:.2f}, {r['lon']:.2f})
                        </span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:36px; font-weight:bold; color:{overall_color};">
                            {r['overall']}
                        </span>
                        <span style="font-size:14px; color:#888;">/10</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Comparison radar ──
        st.markdown("### Multi-Site Radar Comparison")
        fig = go.Figure()
        colors = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444"]

        criteria_names = [CRITERIA[c]["name"] for c in CRITERIA]

        for i, r in enumerate(results):
            vals = [r["scores"][c] for c in CRITERIA]
            color = colors[i % len(colors)]
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=criteria_names + [criteria_names[0]],
                fill="toself",
                fillcolor=_hex_rgba(color, 0.13),
                line=dict(color=color, width=2),
                name=r["name"],
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            height=450,
            margin=dict(t=30, b=30, l=70, r=70),
        )
        st.plotly_chart(fig, use_container_width=True, key="sitran_pchart1")

        # ── Criteria comparison bars ──
        st.markdown("### Criteria Comparison")
        for crit_id, crit_info in CRITERIA.items():
            st.markdown(f"**{crit_info['name']}** — {crit_info['desc']}")

            fig2 = go.Figure()
            site_names = [r["name"] for r in results]
            site_scores = [r["scores"][crit_id] for r in results]
            bar_colors = [colors[i % len(colors)] for i in range(len(results))]

            fig2.add_trace(go.Bar(
                x=site_names,
                y=site_scores,
                marker_color=bar_colors,
                text=[f"{s}" for s in site_scores],
                textposition="auto",
            ))
            fig2.update_layout(
                height=200,
                margin=dict(t=10, b=30, l=40, r=20),
                yaxis=dict(range=[0, 10]),
            )
            st.plotly_chart(fig2, use_container_width=True, key="sitran_pchart2")

        # ── Winner summary ──
        winner = results[0]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #f59e0b22, #f59e0b44);
                    border:2px solid #f59e0b; border-radius:12px;
                    padding:20px; margin:15px 0; text-align:center;">
            <div style="color:#f59e0b; font-size:14px;">RECOMMENDED SITE</div>
            <div style="color:#eee; font-size:28px; font-weight:bold; margin:6px 0;">
                {winner['name']}
            </div>
            <div style="color:#888; font-size:14px;">
                Overall Score: {winner['overall']}/10 |
                Best in: {max(winner['scores'], key=winner['scores'].get).replace('_', ' ').title()}
                ({max(winner['scores'].values())}/10)
            </div>
        </div>
        """, unsafe_allow_html=True)
