"""
Natural Resource Scanner for TerraScout AI.
Scans a location for natural resources: water sources, mineral indicators,
fertile land, energy potential (solar, wind, geothermal), timber, and more.
Combines elevation, soil, geology, weather, and water data.
"""

import logging
import math
import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_geology,
    fetch_landuse_infrastructure,
    compute_landuse_breakdown,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False


# ═══════════════════════════════════════════════════════════════
# RESOURCE ASSESSMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _scan_resources(lat, lon):
    """Comprehensive resource scan for a location."""
    resources = {
        "lat": lat, "lon": lon,
        "categories": {},
    }

    # ── Water Resources ──
    water_score = 0
    water_details = []
    try:
        water = fetch_water_features(lat, lon, radius=5000)
        elements = water.get("elements", [])
        springs = sum(1 for e in elements if e.get("tags", {}).get("natural") == "spring")
        wells = sum(1 for e in elements if e.get("tags", {}).get("man_made") == "water_well")
        waterways = sum(1 for e in elements if e.get("tags", {}).get("waterway"))
        water_bodies = sum(1 for e in elements if e.get("tags", {}).get("natural") == "water")
        total = len(elements)

        water_score = min(100, total * 8 + springs * 15 + wells * 12)
        water_details = [
            f"{springs} springs detected" if springs else None,
            f"{wells} water wells" if wells else None,
            f"{waterways} waterways/rivers" if waterways else None,
            f"{water_bodies} lakes/ponds" if water_bodies else None,
            f"{total} total water features within 5km",
        ]
        water_details = [d for d in water_details if d]
        resources["water_raw"] = {"springs": springs, "wells": wells,
                                  "waterways": waterways, "water_bodies": water_bodies,
                                  "total": total}
    except Exception as e:
        logger.warning(f"Water scan error: {e}")
        water_details = ["Water scan unavailable"]

    resources["categories"]["Water Resources"] = {
        "score": water_score, "color": "#3b82f6", "details": water_details,
    }

    # ── Soil & Agriculture ──
    soil_score = 0
    soil_details = []
    try:
        soil = fetch_soil_data(lat, lon)
        layers = soil.get("properties", {}).get("layers", [])
        soil_props = {}
        for layer in layers:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    if name == "phh2o":
                        soil_props["ph"] = round(val / 10, 1)
                    elif name == "soc":
                        soil_props["organic_c"] = round(val / 10, 1)
                    elif name == "clay":
                        soil_props["clay"] = round(val / 10, 1)
                    elif name == "sand":
                        soil_props["sand"] = round(val / 10, 1)
                    elif name == "nitrogen":
                        soil_props["nitrogen"] = round(val / 100, 2)

        ph = soil_props.get("ph", 0)
        oc = soil_props.get("organic_c", 0)
        n = soil_props.get("nitrogen", 0)

        # Score based on fertility indicators
        if 5.5 <= ph <= 7.5:
            soil_score += 30
        elif 4.5 <= ph <= 8.5:
            soil_score += 15
        if oc > 30:
            soil_score += 35
        elif oc > 15:
            soil_score += 25
        elif oc > 5:
            soil_score += 10
        if n > 0.3:
            soil_score += 20
        elif n > 0.1:
            soil_score += 10
        soil_score += 15  # baseline

        soil_details = [
            f"pH: {ph} ({'Ideal' if 5.5 <= ph <= 7.5 else 'Acceptable' if 4.5 <= ph <= 8.5 else 'Poor'})" if ph else None,
            f"Organic Carbon: {oc} g/kg ({'Rich' if oc > 30 else 'Good' if oc > 15 else 'Low'})" if oc else None,
            f"Nitrogen: {n} g/kg" if n else None,
            f"Clay: {soil_props.get('clay', 'N/A')}%, Sand: {soil_props.get('sand', 'N/A')}%",
        ]
        soil_details = [d for d in soil_details if d]
        resources["soil_props"] = soil_props
    except Exception as e:
        logger.warning(f"Soil scan error: {e}")
        soil_details = ["Soil data unavailable"]

    resources["categories"]["Soil & Agriculture"] = {
        "score": min(100, soil_score), "color": "#10b981", "details": soil_details,
    }

    # ── Solar Energy ──
    solar_score = 0
    solar_details = []
    try:
        wx = fetch_weather_data(lat, lon)
        daily = wx.get("daily", {})
        temps = daily.get("temperature_2m_max", [])
        precip = daily.get("precipitation_sum", [])

        abs_lat = abs(lat)
        # Solar irradiance estimate based on latitude
        if abs_lat < 25:
            solar_score += 40
            solar_details.append("Tropical zone: excellent solar irradiance")
        elif abs_lat < 35:
            solar_score += 30
            solar_details.append("Subtropical zone: very good solar potential")
        elif abs_lat < 50:
            solar_score += 20
            solar_details.append("Temperate zone: moderate solar potential")
        else:
            solar_score += 10
            solar_details.append("High latitude: limited solar hours in winter")

        # Cloud cover estimate from precipitation
        if precip:
            rainy_ratio = sum(1 for p in precip if p and p > 0.5) / max(1, len(precip))
            clear_days = round((1 - rainy_ratio) * 365)
            if rainy_ratio < 0.2:
                solar_score += 35
                solar_details.append(f"~{clear_days} clear days/year: ideal for solar")
            elif rainy_ratio < 0.4:
                solar_score += 25
                solar_details.append(f"~{clear_days} clear days/year: good for solar")
            elif rainy_ratio < 0.6:
                solar_score += 15
                solar_details.append(f"~{clear_days} clear days/year: moderate cloud cover")
            else:
                solar_score += 5
                solar_details.append(f"~{clear_days} clear days/year: high cloud cover")

        # Daylight hours estimate
        summer_daylight = round(12 + 2.5 * math.sin(math.radians(abs_lat)), 1)
        winter_daylight = round(12 - 2.5 * math.sin(math.radians(abs_lat)), 1)
        solar_details.append(f"Daylight range: {winter_daylight}h (winter) to {summer_daylight}h (summer)")
        solar_score += min(25, round(summer_daylight * 2))

    except Exception as e:
        logger.warning(f"Solar scan error: {e}")
        solar_details = ["Solar data unavailable"]

    resources["categories"]["Solar Energy"] = {
        "score": min(100, solar_score), "color": "#f59e0b", "details": solar_details,
    }

    # ── Wind Energy ──
    wind_score = 0
    wind_details = []
    try:
        wx = fetch_weather_data(lat, lon)
        current = wx.get("current", {})
        wind_now = current.get("wind_speed_10m", 0) or 0
        daily = wx.get("daily", {})
        wind_max_list = daily.get("wind_speed_10m_max", [])
        non_none_winds = [w for w in wind_max_list if w is not None]
        avg_wind = round(sum(non_none_winds) / max(1, len(non_none_winds)), 1) if non_none_winds else 0

        if avg_wind > 25:
            wind_score += 50
            wind_details.append(f"Avg peak wind {avg_wind} km/h: excellent wind resource")
        elif avg_wind > 15:
            wind_score += 35
            wind_details.append(f"Avg peak wind {avg_wind} km/h: good wind resource")
        elif avg_wind > 8:
            wind_score += 20
            wind_details.append(f"Avg peak wind {avg_wind} km/h: moderate wind")
        else:
            wind_score += 5
            wind_details.append(f"Avg peak wind {avg_wind} km/h: low wind area")

        # Terrain effect on wind
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)
        center_elev = elev.get("center_elevation", 0)
        elev_range = (elev.get("max_elevation", 0) or 0) - (elev.get("min_elevation", 0) or 0)
        if isinstance(center_elev, (int, float)) and center_elev > 500:
            wind_score += 15
            wind_details.append(f"Elevated site ({center_elev}m): improved wind exposure")
        if isinstance(elev_range, (int, float)) and elev_range < 50:
            wind_score += 15
            wind_details.append("Flat terrain: good for turbine installation")
        elif isinstance(elev_range, (int, float)) and elev_range > 300:
            wind_score += 10
            wind_details.append("Ridge/valley terrain: possible wind channeling")

        wind_details.append(f"Current wind: {wind_now} km/h")

    except Exception as e:
        logger.warning(f"Wind scan error: {e}")
        wind_details = ["Wind data unavailable"]

    resources["categories"]["Wind Energy"] = {
        "score": min(100, wind_score), "color": "#06b6d4", "details": wind_details,
    }

    # ── Geological Resources ──
    geo_score = 0
    geo_details = []
    try:
        geo = fetch_geology(lat, lon)
        if geo and geo.get("success"):
            records = geo.get("success", {}).get("data", [])
            for rec in records[:3]:
                rock = rec.get("lith", "Unknown")
                age = rec.get("t_int_name", "Unknown")
                geo_details.append(f"{rock} ({age})")

                # Score based on rock type (mineral potential)
                rock_lower = rock.lower() if rock else ""
                if any(m in rock_lower for m in ("granite", "basalt", "gabbro")):
                    geo_score += 25
                elif any(m in rock_lower for m in ("sandstone", "limestone", "marble")):
                    geo_score += 20
                elif any(m in rock_lower for m in ("shale", "slate", "quartzite")):
                    geo_score += 15
                else:
                    geo_score += 10

            if not records:
                geo_details.append("No geological records found")
        else:
            geo_details.append("Geology data unavailable for this location")
    except Exception as e:
        logger.warning(f"Geology scan error: {e}")
        geo_details = ["Geology scan unavailable"]

    resources["categories"]["Geological Resources"] = {
        "score": min(100, max(geo_score, 10)), "color": "#a855f7", "details": geo_details,
    }

    # ── Timber / Vegetation ──
    timber_score = 0
    timber_details = []
    try:
        landuse = fetch_landuse_infrastructure(lat, lon, radius=3000)
        lu = compute_landuse_breakdown(landuse)
        cats = lu.get("categories", {})
        forest = cats.get("forest", 0)
        meadow = cats.get("meadow", 0)
        farmland = cats.get("farmland", 0)

        if forest > 10:
            timber_score += 50
            timber_details.append(f"{forest} forest areas: significant timber potential")
        elif forest > 3:
            timber_score += 30
            timber_details.append(f"{forest} forest areas: moderate timber")
        elif forest > 0:
            timber_score += 15
            timber_details.append(f"{forest} forest areas: limited timber")
        else:
            timber_details.append("No forest areas detected within 3km")

        if meadow > 5:
            timber_score += 15
            timber_details.append(f"{meadow} meadow/grassland areas")
        if farmland > 5:
            timber_score += 10
            timber_details.append(f"{farmland} farmland areas")

        timber_score += 10  # baseline
    except Exception as e:
        logger.warning(f"Vegetation scan error: {e}")
        timber_details = ["Vegetation scan unavailable"]

    resources["categories"]["Timber & Vegetation"] = {
        "score": min(100, timber_score), "color": "#22c55e", "details": timber_details,
    }

    return resources


# ═══════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════

def render_resource_scanner_tab():
    """Main render function for Resource Scanner."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Natural Resource Scanner</h4>
        <p>Scan any location for water, soil, solar, wind, minerals & timber potential</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Preset",
                              ["Custom"] + [k for k in ANALYSIS_PRESETS.keys() if k != "Custom"],
                              key="rscan_preset")
        p = ANALYSIS_PRESETS.get(preset)
    with col2:
        lat = st.number_input("Latitude", -90.0, 90.0,
                              p.get("lat", 41.9028) if p else 41.9028, step=0.01,
                              key="rscan_lat", format="%.4f")
    with col3:
        lon = st.number_input("Longitude", -180.0, 180.0,
                              p.get("lon", 12.4964) if p else 12.4964, step=0.01,
                              key="rscan_lon", format="%.4f")

    if st.button("Scan Resources", type="primary", use_container_width=True):
        with st.spinner("Scanning natural resources (6 categories)..."):
            results = _scan_resources(lat, lon)
        st.session_state["rscan_results"] = results

    if "rscan_results" not in st.session_state:
        return

    results = st.session_state["rscan_results"]
    categories = results["categories"]

    st.markdown("---")

    # Overall resource score
    scores = [c["score"] for c in categories.values()]
    overall = round(sum(scores) / len(scores)) if scores else 0
    overall_color = "#10b981" if overall >= 60 else "#f59e0b" if overall >= 35 else "#ef4444"

    st.markdown(f"""
    <div style="text-align:center; padding:15px; background:rgba(0,0,0,0.2);
                border-radius:10px; border-left:4px solid {overall_color}; margin-bottom:15px;">
        <div style="font-size:2.5em; font-weight:bold; color:{overall_color};">{overall}/100</div>
        <div style="color:#9ca3af;">Overall Resource Potential</div>
    </div>
    """, unsafe_allow_html=True)

    # Resource gauges
    gauge_cols = st.columns(len(categories))
    for i, (name, data) in enumerate(categories.items()):
        with gauge_cols[i]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data["score"],
                title={"text": name.split(" ")[0], "font": {"size": 12}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": data["color"]},
                    "steps": [
                        {"range": [0, 30], "color": "rgba(239,68,68,0.1)"},
                        {"range": [30, 60], "color": "rgba(245,158,11,0.1)"},
                        {"range": [60, 100], "color": "rgba(16,185,129,0.1)"},
                    ],
                },
            ))
            fig.update_layout(height=180, margin=dict(t=35, b=5, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True, key="ressca_pchart1")

    # Radar chart
    st.markdown("### Resource Profile")
    cat_names = list(categories.keys())
    cat_scores = [categories[n]["score"] for n in cat_names]
    cat_scores_closed = cat_scores + [cat_scores[0]]
    short_names = [n.split(" ")[0] for n in cat_names]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=cat_scores_closed,
        theta=short_names + [short_names[0]],
        fill="toself",
        line_color="#06b6d4",
        fillcolor="rgba(6,182,212,0.2)",
        name="Resources",
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="ressca_pchart2")

    # Detailed findings
    st.markdown("### Detailed Findings")
    for name, data in categories.items():
        score = data["score"]
        color = data["color"]
        level = "Excellent" if score >= 70 else "Good" if score >= 50 else "Moderate" if score >= 30 else "Low"
        details_html = "".join(f"<li>{d}</li>" for d in data["details"])

        st.markdown(f"""
        <div style="padding:12px; background:rgba(0,0,0,0.15); border-radius:10px;
                    border-left:4px solid {color}; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:{color};">{name}</strong>
                <span style="color:{color}; font-weight:bold;">{score}/100 ({level})</span>
            </div>
            <ul style="color:#d1d5db; margin:8px 0 0 0; font-size:0.9em;">
                {details_html}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Export
    st.markdown("---")
    export_rows = []
    for name, data in categories.items():
        export_rows.append({
            "Resource": name,
            "Score": data["score"],
            "Details": " | ".join(data["details"]),
            "Latitude": results["lat"],
            "Longitude": results["lon"],
        })
    df_export = pd.DataFrame(export_rows)
    if HAS_EXPORT:
        render_export_buttons(df_export, prefix="resources", lat_col="Latitude", lon_col="Longitude")
    else:
        csv = df_export.to_csv(index=False)
        st.download_button("Download Resource Report (CSV)", data=csv,
                           file_name="resource_scan.csv", mime="text/csv")
