"""
Data Fusion Dashboard AI — Unified multi-source data aggregation dashboard.
Combines ALL available data sources into a single comprehensive overview
with real-time quality scoring, data completeness tracking, and integrated
visualizations.
Uses: All available free APIs (10+ data sources).
"""

import logging
from datetime import datetime

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
    fetch_protected_areas,
    fetch_earthquakes,
    fetch_geology,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_risk_assessment,
    compute_species_breakdown,
    compute_landuse_breakdown,
)

logger = logging.getLogger(__name__)


DATA_SOURCES = [
    {"id": "weather", "name": "Open-Meteo Weather", "icon": "cloud", "color": "#3b82f6"},
    {"id": "elevation", "name": "Open Topo Data", "icon": "terrain", "color": "#8b5cf6"},
    {"id": "soil", "name": "ISRIC SoilGrids", "icon": "grass", "color": "#10b981"},
    {"id": "water", "name": "Overpass (Water)", "icon": "water_drop", "color": "#06b6d4"},
    {"id": "infra", "name": "Overpass (Infra)", "icon": "road", "color": "#f59e0b"},
    {"id": "protected", "name": "Overpass (Protected)", "icon": "park", "color": "#22c55e"},
    {"id": "earthquakes", "name": "USGS Earthquakes", "icon": "warning", "color": "#ef4444"},
    {"id": "geology", "name": "Macrostrat Geology", "icon": "layers", "color": "#f97316"},
    {"id": "inat", "name": "iNaturalist", "icon": "pets", "color": "#a855f7"},
    {"id": "gbif", "name": "GBIF Biodiversity", "icon": "eco", "color": "#059669"},
]


@st.cache_data(ttl=1800)
def fuse_all_data(lat: float, lon: float) -> dict:
    """Fetch and fuse all available data sources."""
    results = {}
    quality = {}

    # 1. Weather
    try:
        weather = fetch_weather_data(lat, lon) or {}
        daily = weather.get("daily", {})
        temp_max = daily.get("temperature_2m_max", [])
        valid_tmax = [t for t in temp_max if t is not None]
        results["weather"] = {
            "available": bool(valid_tmax),
            "fields": len(daily),
            "summary": {
                "avg_temp": round(sum(valid_tmax) / len(valid_tmax), 1) if valid_tmax else None,
                "humidity": weather.get("current", {}).get("relative_humidity_2m"),
                "wind": round(sum(w for w in daily.get("wind_speed_10m_max", []) if w is not None) /
                              max(1, len([w for w in daily.get("wind_speed_10m_max", []) if w is not None])), 1)
                        if daily.get("wind_speed_10m_max") else None,
                "precip": round(sum(p for p in daily.get("precipitation_sum", []) if p is not None), 1)
                        if daily.get("precipitation_sum") else None,
            },
        }
        quality["weather"] = 100 if valid_tmax else 0
    except Exception:
        results["weather"] = {"available": False, "fields": 0, "summary": {}}
        quality["weather"] = 0

    # 2. Elevation
    try:
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5) or {}
        elevations = [e for e in elev.get("grid_elevations", []) if e is not None]
        results["elevation"] = {
            "available": bool(elevations),
            "points": len(elevations),
            "summary": {
                "min": round(min(elevations), 1) if elevations else None,
                "max": round(max(elevations), 1) if elevations else None,
                "mean": round(sum(elevations) / len(elevations), 1) if elevations else None,
                "range": round(max(elevations) - min(elevations), 1) if len(elevations) >= 2 else None,
            },
        }
        quality["elevation"] = 100 if len(elevations) >= 10 else len(elevations) * 10
    except Exception:
        results["elevation"] = {"available": False, "points": 0, "summary": {}}
        quality["elevation"] = 0

    # 3. Soil
    try:
        soil = fetch_soil_data(lat, lon) or {}
        props = soil.get("properties", {}) if isinstance(soil, dict) else {}

        def _sv(name, div=10):
            layers = props.get("layers", [])
            for layer in (layers if isinstance(layers, list) else []):
                if isinstance(layer, dict) and layer.get("name") == name:
                    depths = layer.get("depths", [])
                    if depths:
                        return round((depths[0].get("values", {}).get("mean") or 0) / div, 1)
            return None

        results["soil"] = {
            "available": bool(props),
            "properties": len(props),
            "summary": {
                "clay": _sv("clay"),
                "sand": _sv("sand"),
                "soc": _sv("soc"),
                "ph": _sv("phh2o"),
            },
        }
        quality["soil"] = 100 if props else 0
    except Exception:
        results["soil"] = {"available": False, "properties": 0, "summary": {}}
        quality["soil"] = 0

    # 4. Water
    try:
        water = fetch_water_features(lat, lon) or {}
        w_elements = water.get("elements", []) if isinstance(water, dict) else []
        results["water"] = {
            "available": bool(w_elements),
            "features": len(w_elements),
            "summary": {"count": len(w_elements)},
        }
        quality["water"] = 100 if w_elements else 30  # Absence is valid data
    except Exception:
        results["water"] = {"available": False, "features": 0, "summary": {}}
        quality["water"] = 0

    # 5. Infrastructure
    try:
        infra = fetch_landuse_infrastructure(lat, lon) or {}
        i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
        buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
        roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))
        results["infra"] = {
            "available": bool(i_elements),
            "elements": len(i_elements),
            "summary": {"buildings": buildings, "roads": roads},
        }
        quality["infra"] = 100 if i_elements else 30
    except Exception:
        results["infra"] = {"available": False, "elements": 0, "summary": {}}
        quality["infra"] = 0

    # 6. Protected areas
    try:
        protected = fetch_protected_areas(lat, lon) or {}
        p_elements = protected.get("elements", []) if isinstance(protected, dict) else []
        results["protected"] = {
            "available": True,
            "areas": len(p_elements),
            "summary": {"count": len(p_elements)},
        }
        quality["protected"] = 100
    except Exception:
        results["protected"] = {"available": False, "areas": 0, "summary": {}}
        quality["protected"] = 0

    # 7. Earthquakes
    try:
        eq = fetch_earthquakes(lat, lon, radius_km=150, days=365) or {}
        features = eq.get("features", [])
        mags = [f["properties"].get("mag", 0) or 0 for f in features]
        results["earthquakes"] = {
            "available": True,
            "events": len(features),
            "summary": {
                "count": len(features),
                "max_mag": round(max(mags), 1) if mags else 0,
            },
        }
        quality["earthquakes"] = 100
    except Exception:
        results["earthquakes"] = {"available": False, "events": 0, "summary": {}}
        quality["earthquakes"] = 0

    # 8. Geology
    try:
        geo = fetch_geology(lat, lon) or {}
        units = geo.get("success", {}).get("data", []) if isinstance(geo, dict) else []
        results["geology"] = {
            "available": bool(units),
            "units": len(units),
            "summary": {
                "primary": units[0].get("unit_name", "Unknown") if units else None,
                "lith": units[0].get("lith", "") if units else None,
            },
        }
        quality["geology"] = 100 if units else 0
    except Exception:
        results["geology"] = {"available": False, "units": 0, "summary": {}}
        quality["geology"] = 0

    # 9. iNaturalist
    try:
        inat = fetch_biodiversity(lat, lon) or {}
        inat_total = inat.get("total_results", 0)
        results["inat"] = {
            "available": True,
            "observations": inat_total,
            "summary": {"total": inat_total},
        }
        quality["inat"] = 100
    except Exception:
        results["inat"] = {"available": False, "observations": 0, "summary": {}}
        quality["inat"] = 0

    # 10. GBIF
    try:
        gbif = fetch_gbif_occurrences(lat, lon) or {}
        gbif_count = gbif.get("count", 0)
        results["gbif"] = {
            "available": True,
            "records": gbif_count,
            "summary": {"total": gbif_count},
        }
        quality["gbif"] = 100
    except Exception:
        results["gbif"] = {"available": False, "records": 0, "summary": {}}
        quality["gbif"] = 0

    # Compute risk assessment
    try:
        _eq = earthquakes.get("features", []) if 'earthquakes' in results and results.get("earthquakes", {}).get("available") else {}
        risk = compute_risk_assessment(
            {"features": eq.get("features", [])} if 'eq' in locals() else {},
            water if 'water' in locals() else {},
            weather if 'weather' in locals() else {},
            elev if 'elev' in locals() else {},
        )
    except Exception:
        risk = {}

    # Overall quality
    total_quality = sum(quality.values()) / max(len(quality), 1)

    return {
        "sources": results,
        "quality": quality,
        "overall_quality": round(total_quality, 1),
        "risk": risk if isinstance(risk, dict) else {},
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_data_fusion_tab():
    """Render the Data Fusion Dashboard AI tab."""
    st.markdown("## Data Fusion Dashboard AI")
    st.caption("Unified multi-source data aggregation with quality scoring")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="df_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="df_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="df_lon", format="%.4f")

    if st.button("Fuse All Data Sources", type="primary", use_container_width=True):
        with st.spinner("Fetching from 10 data sources simultaneously..."):
            result = fuse_all_data(lat, lon)

        if not result:
            st.error("Failed to fuse data.")
            return

        sources = result["sources"]
        quality = result["quality"]
        overall_q = result["overall_quality"]

        # ── Quality overview ──
        q_color = "#10b981" if overall_q >= 80 else "#f59e0b" if overall_q >= 50 else "#ef4444"
        available_count = sum(1 for s in sources.values() if s.get("available"))

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {q_color}22, {q_color}44);
                    border-left:5px solid {q_color}; border-radius:10px;
                    padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">DATA QUALITY SCORE</div>
                    <div style="color:{q_color}; font-size:36px; font-weight:bold;">
                        {overall_q}%
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:12px;">SOURCES AVAILABLE</div>
                    <div style="color:#eee; font-size:36px; font-weight:bold;">
                        {available_count}<span style="font-size:16px; color:#888;">/10</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Data source quality bars ──
        st.markdown("### Data Source Quality")
        ds_names = [ds["name"] for ds in DATA_SOURCES]
        ds_quality = [quality.get(ds["id"], 0) for ds in DATA_SOURCES]
        ds_colors = [ds["color"] if quality.get(ds["id"], 0) >= 50 else "#ef4444" for ds in DATA_SOURCES]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=ds_quality,
            y=ds_names,
            orientation="h",
            marker_color=ds_colors,
            text=[f"{q}%" for q in ds_quality],
            textposition="auto",
        ))
        fig.update_layout(
            height=max(350, len(ds_names) * 35),
            margin=dict(t=10, b=20, l=180),
            xaxis=dict(range=[0, 100], title="Quality %"),
        )
        st.plotly_chart(fig, use_container_width=True, key="datfus_pchart1")

        # ── Data source cards ──
        st.markdown("### Fused Data Summary")
        cols = st.columns(2)

        for idx, ds in enumerate(DATA_SOURCES):
            src = sources.get(ds["id"], {})
            q = quality.get(ds["id"], 0)
            available = src.get("available", False)

            status_icon = "OK" if available and q >= 50 else "WARN" if available else "FAIL"
            status_color = "#10b981" if status_icon == "OK" else "#f59e0b" if status_icon == "WARN" else "#ef4444"

            summary_items = []
            for k, v in src.get("summary", {}).items():
                if v is not None:
                    summary_items.append(f"{k.replace('_', ' ').title()}: **{v}**")

            summary_text = " | ".join(summary_items) if summary_items else "No data"

            with cols[idx % 2]:
                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:3px solid {ds['color']};
                            border-radius:8px; padding:12px; margin:4px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:{ds['color']}; font-weight:bold; font-size:13px;">
                            {ds['name']}
                        </span>
                        <span style="background:{status_color}22; color:{status_color};
                                    padding:2px 8px; border-radius:4px; font-size:11px;">
                            {status_icon} {q}%
                        </span>
                    </div>
                    <div style="color:#aaa; font-size:12px; margin-top:4px;">
                        {summary_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Risk summary from fused data ──
        risk = result.get("risk", {})
        if risk and isinstance(risk, dict):
            st.markdown("### Computed Risk (from fused data)")
            risk_items = {k: v for k, v in risk.items() if isinstance(v, (int, float))}
            if risk_items:
                r_names = list(risk_items.keys())
                r_values = [round(v, 1) for v in risk_items.values()]
                r_colors = ["#10b981" if v < 3 else "#f59e0b" if v < 6 else "#ef4444" for v in r_values]

                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=r_values,
                    y=r_names,
                    orientation="h",
                    marker_color=r_colors,
                    text=[f"{v}/10" for v in r_values],
                    textposition="auto",
                ))
                fig2.update_layout(
                    height=max(200, len(r_names) * 40),
                    margin=dict(t=10, b=20, l=120),
                    xaxis=dict(range=[0, 10], title="Risk Score"),
                )
                st.plotly_chart(fig2, use_container_width=True, key="datfus_pchart2")

        st.caption(f"Report generated: {result['timestamp']}")
