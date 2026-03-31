"""
Report Generator for TerraScout AI.
Generate downloadable HTML reports for any location with comprehensive environmental data.
"""

import json
import logging
from datetime import datetime
import streamlit as st
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_biodiversity,
    fetch_earthquakes,
    fetch_water_features,
    fetch_geology,
    compute_risk_assessment,
    compute_species_breakdown,
    fetch_gbif_occurrences,
    ANALYSIS_PRESETS,
)


REPORT_SECTIONS = {
    "elevation": "Elevation & Terrain",
    "weather": "Current Weather & Forecast",
    "soil": "Soil Composition",
    "biodiversity": "Biodiversity",
    "geology": "Geology",
    "risk": "Risk Assessment",
    "water": "Water Features",
}


def _html_header(title, lat, lon):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
  .header {{ background: linear-gradient(135deg, #06b6d4, #8b5cf6); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
  .header p {{ opacity: 0.9; }}
  .section {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border-left: 4px solid #06b6d4; }}
  .section h2 {{ color: #06b6d4; margin-bottom: 1rem; font-size: 1.3rem; }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .metric {{ background: #334155; padding: 1rem; border-radius: 8px; text-align: center; }}
  .metric .value {{ font-size: 1.5rem; font-weight: bold; color: #06b6d4; }}
  .metric .label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 0.3rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
  th {{ color: #06b6d4; font-weight: 600; }}
  .risk-bar {{ height: 20px; border-radius: 4px; margin: 4px 0; }}
  .footer {{ text-align: center; color: #64748b; margin-top: 2rem; padding: 1rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>TerraScout AI - Location Report</h1>
  <p>{title} | Coordinates: {lat:.6f}, {lon:.6f} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
"""


def _html_metric(label, value):
    return f'<div class="metric"><div class="value">{value}</div><div class="label">{label}</div></div>'


def _section_elevation(data):
    if not data:
        return ""
    html = '<div class="section"><h2>Elevation &amp; Terrain</h2><div class="metric-grid">'
    html += _html_metric("Center Elevation", f"{data.get('center_elevation', 'N/A')} m")
    html += _html_metric("Min Elevation", f"{data.get('min_elevation', 'N/A')} m")
    html += _html_metric("Max Elevation", f"{data.get('max_elevation', 'N/A')} m")
    html += _html_metric("Avg Elevation", f"{data.get('avg_elevation', 'N/A')} m")
    relief = "N/A"
    if isinstance(data.get('max_elevation'), (int, float)) and isinstance(data.get('min_elevation'), (int, float)):
        relief = f"{data['max_elevation'] - data['min_elevation']:.0f} m"
    html += _html_metric("Total Relief", relief)
    html += '</div></div>'
    return html


def _section_weather(data):
    if not data:
        return ""
    current = data.get("current", {})
    html = '<div class="section"><h2>Current Weather</h2><div class="metric-grid">'
    html += _html_metric("Temperature", f"{current.get('temperature_2m', 'N/A')} C")
    html += _html_metric("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%")
    html += _html_metric("Wind Speed", f"{current.get('wind_speed_10m', 'N/A')} km/h")
    html += _html_metric("Precipitation", f"{current.get('precipitation', 'N/A')} mm")
    html += '</div>'

    # 7-day forecast table
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    if dates:
        html += '<h3 style="color:#94a3b8; margin:1rem 0 0.5rem;">7-Day Forecast</h3>'
        html += '<table><tr><th>Date</th><th>Max C</th><th>Min C</th><th>Precip mm</th></tr>'
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        p_sum = daily.get("precipitation_sum", [])
        for i, d in enumerate(dates[:7]):
            mx = t_max[i] if i < len(t_max) else "N/A"
            mn = t_min[i] if i < len(t_min) else "N/A"
            pr = p_sum[i] if i < len(p_sum) else "N/A"
            html += f'<tr><td>{d}</td><td>{mx}</td><td>{mn}</td><td>{pr}</td></tr>'
        html += '</table>'

    html += '</div>'
    return html


def _section_soil(data):
    if not data:
        return ""
    html = '<div class="section"><h2>Soil Composition</h2>'
    try:
        layers = data.get("properties", {}).get("layers", [])
        if layers:
            html += '<table><tr><th>Property</th><th>Value (0-5cm)</th></tr>'
            name_map = {"clay": "Clay", "sand": "Sand", "silt": "Silt", "soc": "Organic Carbon",
                        "phh2o": "pH (H2O)", "nitrogen": "Nitrogen", "cec": "CEC"}
            unit_map = {"clay": "%", "sand": "%", "silt": "%", "soc": "g/kg",
                        "phh2o": "pH", "nitrogen": "g/kg", "cec": "cmol/kg"}
            div_map = {"clay": 10, "sand": 10, "silt": 10, "soc": 10,
                       "phh2o": 10, "nitrogen": 100, "cec": 10}
            for layer in layers:
                name = layer.get("name", "")
                depths = layer.get("depths", [])
                if depths and name in name_map:
                    val = depths[0].get("values", {}).get("mean")
                    if val is not None:
                        val = val / div_map.get(name, 10)
                        html += f'<tr><td>{name_map[name]}</td><td>{val:.1f} {unit_map.get(name, "")}</td></tr>'
            html += '</table>'
    except Exception:
        html += '<p>Soil data parsing error.</p>'
    html += '</div>'
    return html


def _section_biodiversity(inat_data, gbif_data):
    breakdown = compute_species_breakdown(inat_data, gbif_data)
    html = '<div class="section"><h2>Biodiversity</h2><div class="metric-grid">'
    species_count = breakdown.get("gbif_unique_species", 0) + len(breakdown.get("top_species", []))
    obs_count = breakdown.get("inat_total", 0) + breakdown.get("gbif_total", 0)
    html += _html_metric("Total Species", str(species_count))
    html += _html_metric("Total Observations", str(obs_count))
    html += '</div>'

    # Kingdom breakdown
    kingdoms = breakdown.get("kingdom_counts", {})
    if kingdoms:
        html += '<table><tr><th>Kingdom</th><th>Count</th></tr>'
        for k, v in kingdoms.items():
            html += f'<tr><td>{k}</td><td>{v}</td></tr>'
        html += '</table>'

    html += '</div>'
    return html


def _section_geology(data):
    if not data:
        return ""
    html = '<div class="section"><h2>Geology</h2>'
    try:
        records = data.get("success", {}).get("data", [])
        if records:
            html += '<table><tr><th>Unit</th><th>Lithology</th><th>Age</th></tr>'
            for rec in records[:10]:
                name = rec.get("unit_name", rec.get("strat_name", "Unknown"))
                lith = rec.get("lith", "Unknown")
                age = f"{rec.get('b_age', '?')} - {rec.get('t_age', '?')} Ma"
                html += f'<tr><td>{name}</td><td>{lith}</td><td>{age}</td></tr>'
            html += '</table>'
        else:
            html += '<p>No geological data available.</p>'
    except Exception:
        html += '<p>Error parsing geology data.</p>'
    html += '</div>'
    return html


def _section_risk(risk_data):
    if not risk_data:
        return ""
    html = '<div class="section"><h2>Risk Assessment</h2><div class="metric-grid">'
    colors = {"Seismic": "#ef4444", "Flood": "#3b82f6", "Fire": "#f97316", "Landslide": "#a855f7", "Pollution": "#64748b"}
    for risk_name, risk_info in risk_data.items():
        score = risk_info if isinstance(risk_info, (int, float)) else 0
        color = colors.get(risk_name, "#64748b")
        level = "LOW" if score < 3 else "MODERATE" if score < 6 else "HIGH" if score < 8 else "CRITICAL"
        html += f'''<div class="metric">
            <div class="value" style="color:{color};">{score}/10</div>
            <div class="label">{risk_name} Risk - {level}</div>
            <div class="risk-bar" style="background:linear-gradient(90deg, {color} {score*10}%, #334155 {score*10}%);"></div>
        </div>'''
    html += '</div></div>'
    return html


def _section_water(data):
    if not data:
        return ""
    html = '<div class="section"><h2>Water Features</h2><div class="metric-grid">'
    html += _html_metric("Springs", str(len(data.get("springs", []))))
    html += _html_metric("Wells", str(len(data.get("wells", []))))
    html += _html_metric("Waterways", str(len(data.get("waterways", []))))
    html += _html_metric("Water Bodies", str(len(data.get("water_bodies", []))))
    html += '</div></div>'
    return html


def render_report_generator_tab():
    """Main render function for Report Generator tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>📋 Report Generator</h4>
        <p>Generate comprehensive downloadable HTML reports for any location</p>
    </div>
    """, unsafe_allow_html=True)

    # Location selection
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="repgen_preset")
    preset_data = ANALYSIS_PRESETS.get(preset)
    d_lat = preset_data.get("lat", 41.90) if preset_data else 41.90
    d_lon = preset_data.get("lon", 12.50) if preset_data else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01, key="repgen_lat", format="%.4f")
        with c2:
            lon = st.number_input("Longitude", -180.0, 180.0, d_lon, step=0.01, key="repgen_lon", format="%.4f")

    report_title = st.text_input("Report Title", value=f"Location Analysis ({lat:.2f}, {lon:.2f})", key="rg_title")

    # Section selection
    st.markdown("**Select Report Sections:**")
    selected = {}
    sec_cols = st.columns(4)
    for i, (key, label) in enumerate(REPORT_SECTIONS.items()):
        with sec_cols[i % 4]:
            selected[key] = st.checkbox(label, value=True, key=f"rg_sec_{key}")

    if st.button("Generate Report", type="primary", use_container_width=True):
        html_parts = [_html_header(report_title, lat, lon)]
        progress = st.progress(0)
        total = sum(1 for v in selected.values() if v)
        done = 0

        if selected.get("elevation"):
            with st.spinner("Fetching elevation..."):
                elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5)
                html_parts.append(_section_elevation(elev))
            done += 1
            progress.progress(done / total)

        if selected.get("weather"):
            with st.spinner("Fetching weather..."):
                wx = fetch_weather_data(lat, lon)
                html_parts.append(_section_weather(wx))
            done += 1
            progress.progress(done / total)

        if selected.get("soil"):
            with st.spinner("Fetching soil data..."):
                soil = fetch_soil_data(lat, lon)
                html_parts.append(_section_soil(soil))
            done += 1
            progress.progress(done / total)

        bio_inat, bio_gbif = None, None
        if selected.get("biodiversity"):
            with st.spinner("Fetching biodiversity..."):
                bio_inat = fetch_biodiversity(lat, lon, radius_km=10)
                bio_gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
                html_parts.append(_section_biodiversity(bio_inat, bio_gbif))
            done += 1
            progress.progress(done / total)

        if selected.get("geology"):
            with st.spinner("Fetching geology..."):
                geo = fetch_geology(lat, lon)
                html_parts.append(_section_geology(geo))
            done += 1
            progress.progress(done / total)

        if selected.get("risk"):
            with st.spinner("Computing risk..."):
                eq = fetch_earthquakes(lat, lon, radius_km=100, days=365)
                water = fetch_water_features(lat, lon, radius=5000)
                elev_r = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=5)
                risk = compute_risk_assessment(eq, water, {}, elev_r, lat, lon)
                html_parts.append(_section_risk(risk))
            done += 1
            progress.progress(done / total)

        if selected.get("water"):
            with st.spinner("Fetching water features..."):
                water_data = fetch_water_features(lat, lon, radius=5000)
                html_parts.append(_section_water(water_data))
            done += 1
            progress.progress(done / total)

        # Footer
        html_parts.append(f"""
        <div class="footer">
            <p>Generated by TerraScout AI | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>All data from free, open APIs: Open Topo Data, Open-Meteo, ISRIC SoilGrids, iNaturalist, GBIF, Macrostrat, USGS</p>
        </div>
        </body></html>
        """)

        full_html = "\n".join(html_parts)
        st.session_state["rg_html"] = full_html
        st.success("Report generated successfully!")

    if "rg_html" in st.session_state:
        html = st.session_state["rg_html"]

        # Preview
        st.markdown("### Report Preview")
        st_html(html, height=600, scrolling=True)

        # Download
        st.download_button(
            "Download HTML Report",
            data=html,
            file_name=f"terrascout_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
            key="rg_download",
        )
