"""
Multi-Location Comparison for TerraScout AI.
Compare 2-4 locations side by side: elevation, weather, soil, biodiversity & risk.
Reuses data-fetching functions from deep_zone_analysis.
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

logger = logging.getLogger(__name__)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_biodiversity,
    fetch_earthquakes,
    fetch_water_features,
    compute_risk_assessment,
    compute_species_breakdown,
    fetch_gbif_occurrences,
    haversine_distance,
    ANALYSIS_PRESETS,
)


def _safe_get(d, *keys, default="N/A"):
    """Safely traverse nested dicts."""
    val = d
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val


def _fetch_location_data(name, lat, lon):
    """Fetch all data for a single location. Returns a summary dict."""
    summary = {"name": name, "lat": lat, "lon": lon}

    # Elevation
    try:
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)
        summary["elevation"] = elev.get("center_elevation", "N/A")
        summary["elev_min"] = elev.get("min_elevation", "N/A")
        summary["elev_max"] = elev.get("max_elevation", "N/A")
        summary["elev_avg"] = elev.get("avg_elevation", "N/A")
    except Exception:
        summary["elevation"] = "N/A"
        summary["elev_min"] = summary["elev_max"] = summary["elev_avg"] = "N/A"

    # Weather
    try:
        wx = fetch_weather_data(lat, lon)
        current = wx.get("current", {})
        summary["temp"] = current.get("temperature_2m", "N/A")
        summary["humidity"] = current.get("relative_humidity_2m", "N/A")
        summary["wind"] = current.get("wind_speed_10m", "N/A")
        summary["precip"] = current.get("precipitation", "N/A")
        # 7-day forecast averages
        daily = wx.get("daily", {})
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        if temps_max and temps_min:
            summary["forecast_avg"] = round(sum(
                (mx + mn) / 2 for mx, mn in zip(temps_max, temps_min)
            ) / len(temps_max), 1)
        else:
            summary["forecast_avg"] = "N/A"
    except Exception:
        summary["temp"] = summary["humidity"] = summary["wind"] = "N/A"
        summary["precip"] = summary["forecast_avg"] = "N/A"
    # Soil
    try:
        soil = fetch_soil_data(lat, lon)
        props = soil.get("properties", {}).get("layers", [])
        for layer in props:
            prop_name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    if prop_name in ("clay", "sand", "silt"):
                        summary[f"soil_{prop_name}"] = round(val / 10, 1)
                    elif prop_name == "phh2o":
                        summary["soil_ph"] = round(val / 10, 1)
                    elif prop_name == "soc":
                        summary["soil_organic_c"] = round(val / 10, 1)
    except Exception:
        pass

    # Biodiversity
    try:
        inat = fetch_biodiversity(lat, lon, radius_km=10)
        gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
        breakdown = compute_species_breakdown(inat, gbif)
        summary["species_total"] = breakdown.get("gbif_unique_species", 0) + len(breakdown.get("top_species", []))
        summary["observations"] = breakdown.get("inat_total", 0) + breakdown.get("gbif_total", 0)
    except Exception:
        summary["species_total"] = 0
        summary["observations"] = 0

    # Risk
    try:
        eq = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        water = fetch_water_features(lat, lon, radius=5000)
        # Build elevation dict with safe numeric defaults
        _elev_val = summary.get("elevation", 0)
        _elev_min = summary.get("elev_min", 0)
        _elev_max = summary.get("elev_max", 0)
        elev_data = {"center_elevation": _elev_val if isinstance(_elev_val, (int, float)) else 0,
                     "min_elevation": _elev_min if isinstance(_elev_min, (int, float)) else 0,
                     "max_elevation": _elev_max if isinstance(_elev_max, (int, float)) else 0}
        risk = compute_risk_assessment(eq, water, {}, elev_data, lat, lon)
        summary["risk_seismic"] = risk.get("Seismic", 0)
        summary["risk_flood"] = risk.get("Flood", 0)
        summary["risk_fire"] = risk.get("Fire", 0)
        summary["risk_landslide"] = risk.get("Landslide", 0)
    except Exception:
        summary["risk_seismic"] = summary["risk_flood"] = 0
        summary["risk_fire"] = summary["risk_landslide"] = 0

    return summary


def _make_radar_chart(locations_data):
    """Create a radar chart comparing risk profiles."""
    categories = ["Seismic", "Flood", "Fire", "Landslide"]
    fig = go.Figure()
    colors = ["#06b6d4", "#f59e0b", "#10b981", "#ef4444"]

    for i, loc in enumerate(locations_data):
        values = [
            loc.get("risk_seismic", 0),
            loc.get("risk_flood", 0),
            loc.get("risk_fire", 0),
            loc.get("risk_landslide", 0),
        ]
        values.append(values[0])  # close the polygon
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            name=loc["name"],
            line_color=colors[i % len(colors)],
            opacity=0.6,
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=True,
        title="Risk Comparison (0-10)",
        height=400,
        margin=dict(t=60, b=30),
    )
    return fig


def _make_bar_chart(locations_data, metric_key, title, unit=""):
    """Create grouped bar chart for a single metric."""
    names = [loc["name"] for loc in locations_data]
    values = []
    for loc in locations_data:
        v = loc.get(metric_key, 0)
        values.append(v if isinstance(v, (int, float)) else 0)

    colors = ["#06b6d4", "#f59e0b", "#10b981", "#ef4444"]
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=values,
            marker_color=[colors[i % len(colors)] for i in range(len(names))],
            text=[f"{v}{unit}" for v in values],
            textposition="auto",
        )
    ])
    fig.update_layout(title=title, height=350, margin=dict(t=50, b=30))
    return fig


def render_compare_locations_tab():
    """Main render function for Location Comparison tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>📊 Location Comparison</h4>
        <p>Compare 2-4 locations side by side — elevation, weather, soil, biodiversity &amp; risk assessment</p>
    </div>
    """, unsafe_allow_html=True)

    # Number of locations
    num_locs = st.slider("Number of locations to compare", 2, 4, 2, key="cmp_num")

    # Preset list for convenience
    preset_names = [k for k in ANALYSIS_PRESETS.keys() if k != "Custom"]

    locations = []
    cols = st.columns(num_locs)
    for i in range(num_locs):
        with cols[i]:
            st.markdown(f"**Location {i+1}**")
            preset = st.selectbox("Preset", ["Custom"] + preset_names,
                                  key=f"cmp_preset_{i}")
            p = ANALYSIS_PRESETS.get(preset)
            d_lat = p["lat"] if p else 41.90 + i * 5
            d_lon = p["lon"] if p else 12.50 + i * 5
            name = st.text_input("Name", value=preset if preset != "Custom" else f"Location {i+1}",
                                 key=f"cmp_name_{i}")
            la = st.number_input("Lat", -90.0, 90.0, d_lat, step=0.01,
                                 key=f"cmp_lat_{i}", format="%.4f")
            lo = st.number_input("Lon", -180.0, 180.0, d_lon, step=0.01,
                                 key=f"cmp_lon_{i}", format="%.4f")
            locations.append({"name": name, "lat": la, "lon": lo})

    if st.button("🔍 Compare Locations", type="primary", use_container_width=True):
        all_data = []
        progress = st.progress(0)
        for idx, loc in enumerate(locations):
            with st.spinner(f"Analyzing {loc['name']}..."):
                data = _fetch_location_data(loc["name"], loc["lat"], loc["lon"])
                all_data.append(data)
            progress.progress((idx + 1) / len(locations))

        st.session_state["cmp_results"] = all_data

    # Display results
    if "cmp_results" in st.session_state:
        all_data = st.session_state["cmp_results"]

        st.markdown("---")
        st.markdown("### 📊 Comparison Results")

        # Side-by-side metrics
        metric_cols = st.columns(len(all_data))
        for i, loc in enumerate(all_data):
            with metric_cols[i]:
                st.markdown(f"#### {loc['name']}")
                st.caption(f"({loc['lat']:.4f}, {loc['lon']:.4f})")
                st.metric("Elevation", f"{loc.get('elevation', 'N/A')} m")
                st.metric("Temperature", f"{loc.get('temp', 'N/A')} °C")
                st.metric("Humidity", f"{loc.get('humidity', 'N/A')} %")
                st.metric("Wind", f"{loc.get('wind', 'N/A')} km/h")
                st.metric("Species", f"{loc.get('species_total', 0)}")
                st.metric("Observations", f"{loc.get('observations', 0)}")

        # Charts
        st.markdown("---")
        chart_cols = st.columns(2)
        with chart_cols[0]:
            fig_radar = _make_radar_chart(all_data)
            st.plotly_chart(fig_radar, use_container_width=True, key="cml_radar")
        with chart_cols[1]:
            fig_elev = _make_bar_chart(all_data, "elevation", "Elevation (m)", " m")
            st.plotly_chart(fig_elev, use_container_width=True, key="cml_elev")

        c1, c2 = st.columns(2)
        with c1:
            fig_temp = _make_bar_chart(all_data, "temp", "Temperature (°C)", " °C")
            st.plotly_chart(fig_temp, use_container_width=True, key="cml_temp")
        with c2:
            fig_bio = _make_bar_chart(all_data, "species_total", "Species Count")
            st.plotly_chart(fig_bio, use_container_width=True, key="cml_bio")

        # Soil comparison
        soil_keys = ["soil_clay", "soil_sand", "soil_silt", "soil_ph", "soil_organic_c"]
        soil_labels = ["Clay %", "Sand %", "Silt %", "pH", "Organic C (g/kg)"]
        has_soil = any(loc.get(k) for loc in all_data for k in soil_keys)
        if has_soil:
            st.markdown("#### 🌱 Soil Comparison")
            soil_rows = []
            for loc in all_data:
                row = {"Location": loc["name"]}
                for k, label in zip(soil_keys, soil_labels):
                    row[label] = loc.get(k, "N/A")
                soil_rows.append(row)
            st.dataframe(pd.DataFrame(soil_rows), use_container_width=True)

        # Distance matrix
        if len(all_data) > 1:
            st.markdown("#### 📏 Distance Matrix (km)")
            dist_data = []
            for a in all_data:
                row = {"Location": a["name"]}
                for b in all_data:
                    if a["name"] == b["name"]:
                        row[b["name"]] = 0
                    else:
                        row[b["name"]] = round(haversine_distance(
                            a["lat"], a["lon"], b["lat"], b["lon"]
                        ), 1)
                dist_data.append(row)
            st.dataframe(pd.DataFrame(dist_data).set_index("Location"),
                         use_container_width=True)

        # Export
        st.markdown("---")
        st.markdown("### Export Data")
        df_export = pd.DataFrame(all_data)
        if HAS_EXPORT:
            render_export_buttons(df_export, prefix="comparison", lat_col="lat", lon_col="lon")
        else:
            csv = df_export.to_csv(index=False)
            st.download_button("📥 Download Comparison (CSV)", data=csv,
                               file_name="location_comparison.csv", mime="text/csv")
