"""
Historical Timeline Analysis for TerraScout AI.
Temperature anomalies, precipitation trends, earthquake history & deforestation.
Uses Open-Meteo Archive API and USGS historical earthquake data.
"""

import logging
import requests
import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

from src.deep_zone_analysis import ANALYSIS_PRESETS, fetch_earthquakes


@st.cache_data(ttl=7200)
def _fetch_climate_history(lat, lon, start_year=1950, end_year=2024):
    """Fetch historical temperature and precipitation from Open-Meteo Climate API."""
    try:
        # Use climate API for long-term data
        resp = requests.get("https://climate-api.open-meteo.com/v1/climate", params={
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{start_year}-01-01",
            "end_date": f"{end_year}-12-31",
            "models": "EC_Earth3P_HR",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "auto",
        }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            return {
                "dates": daily.get("time", []),
                "temp": daily.get("temperature_2m_mean", []),
                "precip": daily.get("precipitation_sum", []),
            }
    except Exception:
        pass
    return {"dates": [], "temp": [], "precip": []}


@st.cache_data(ttl=7200)
def _fetch_historical_earthquakes(lat, lon, radius_km=200, start_year=1900):
    """Fetch historical earthquake data from USGS."""
    try:
        resp = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params={
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "starttime": f"{start_year}-01-01",
            "minmagnitude": 4,
            "orderby": "time",
            "limit": 500,
        }, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"features": []}


def _aggregate_yearly(dates, values, agg="mean"):
    """Aggregate daily data to yearly."""
    if not dates or not values:
        return [], []
    df = pd.DataFrame({"date": dates, "value": values})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    df["year"] = df["date"].dt.year
    if agg == "mean":
        yearly = df.groupby("year")["value"].mean()
    else:
        yearly = df.groupby("year")["value"].sum()
    return yearly.index.tolist(), yearly.values.tolist()


def render_timeline_analysis_tab():
    """Main render function for Historical Timeline tab."""
    st.markdown("""
    <div class="tab-header violet">
        <h4>📅 Historical Timeline</h4>
        <p>Temperature anomalies, precipitation trends &amp; earthquake history over decades</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="tl_preset")
    preset_data = ANALYSIS_PRESETS.get(preset)
    d_lat = preset_data.get("lat", 41.90) if preset_data else 41.90
    d_lon = preset_data.get("lon", 12.50) if preset_data else 12.50

    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01, key="tl_lat", format="%.4f")
        with c2:
            lon = st.number_input("Longitude", -180.0, 180.0, d_lon, step=0.01, key="tl_lon", format="%.4f")

    # Time range
    tc1, tc2 = st.columns(2)
    with tc1:
        start_year = st.slider("Start Year", 1950, 2020, 1950, key="tl_start")
    with tc2:
        end_year = st.slider("End Year", 1960, 2024, 2024, key="tl_end")

    if st.button("Analyze Historical Trends", type="primary", use_container_width=True):
        with st.spinner("Fetching climate history..."):
            climate = _fetch_climate_history(lat, lon, start_year, end_year)

        with st.spinner("Fetching earthquake history..."):
            eq_data = _fetch_historical_earthquakes(lat, lon, radius_km=200, start_year=start_year)

        st.session_state["tl_results"] = {
            "climate": climate, "earthquakes": eq_data, "lat": lat, "lon": lon,
            "start_year": start_year, "end_year": end_year,
        }

    if "tl_results" in st.session_state:
        r = st.session_state["tl_results"]
        climate = r["climate"]
        eq_data = r["earthquakes"]

        st.markdown("---")

        # Temperature trend
        st.markdown("### Temperature Trend")
        years_t, temps = _aggregate_yearly(climate["dates"], climate["temp"], "mean")
        if years_t:
            # Compute anomaly relative to first decade average
            baseline_temps = [t for y, t in zip(years_t, temps) if y < years_t[0] + 10]
            baseline = sum(baseline_temps) / len(baseline_temps) if baseline_temps else 0
            anomalies = [t - baseline for t in temps]

            fig_temp = go.Figure()
            colors = ["#ef4444" if a >= 0 else "#3b82f6" for a in anomalies]
            fig_temp.add_trace(go.Bar(
                x=years_t, y=anomalies,
                marker_color=colors,
                name="Temp Anomaly",
            ))
            fig_temp.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
            fig_temp.update_layout(
                title=f"Temperature Anomaly vs {years_t[0]}-{years_t[0]+9} Baseline ({baseline:.1f} C)",
                xaxis_title="Year",
                yaxis_title="Anomaly (C)",
                height=400,
                margin=dict(t=50, b=40),
            )
            st.plotly_chart(fig_temp, use_container_width=True, key="tla_temp")

            # Summary metrics
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric("Baseline Avg", f"{baseline:.1f} C")
            with mc2:
                recent = temps[-5:] if len(temps) >= 5 else temps
                recent_avg = sum(recent) / len(recent) if recent else baseline
                st.metric("Recent Avg (last 5yr)", f"{recent_avg:.1f} C",
                          delta=f"{recent_avg - baseline:+.1f} C")
            with mc3:
                st.metric("Warming Trend", f"{anomalies[-1]:+.1f} C" if anomalies else "N/A")
        else:
            st.warning("No temperature data available for this location/period.")

        # Precipitation trend
        st.markdown("### Precipitation Trend")
        years_p, precips = _aggregate_yearly(climate["dates"], climate["precip"], "sum")
        if years_p:
            fig_precip = go.Figure()
            fig_precip.add_trace(go.Scatter(
                x=years_p, y=precips,
                fill="tozeroy",
                line_color="#3b82f6",
                fillcolor="rgba(59, 130, 246, 0.2)",
                name="Annual Precipitation",
            ))
            fig_precip.update_layout(
                title="Annual Precipitation",
                xaxis_title="Year",
                yaxis_title="Precipitation (mm/year)",
                height=350,
                margin=dict(t=50, b=40),
            )
            st.plotly_chart(fig_precip, use_container_width=True, key="tla_precip")

            pm1, pm2 = st.columns(2)
            with pm1:
                overall_avg = sum(precips) / len(precips) if precips else 0
                st.metric("Avg Annual Precip", f"{overall_avg:.0f} mm")
            with pm2:
                recent_p = precips[-5:] if len(precips) >= 5 else precips
                recent_avg = sum(recent_p) / len(recent_p) if recent_p else 0
                st.metric("Recent Avg (5yr)", f"{recent_avg:.0f} mm",
                          delta=f"{recent_avg - overall_avg:+.0f} mm")
        else:
            st.warning("No precipitation data available for this location/period.")

        # Earthquake timeline
        st.markdown("### Earthquake History")
        quakes = eq_data.get("features", [])
        if quakes:
            eq_rows = []
            for feat in quakes:
                props = feat.get("properties", {})
                coords = feat.get("geometry", {}).get("coordinates", [])
                time_ms = props.get("time")
                if time_ms:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(time_ms / 1000)
                    eq_rows.append({
                        "Date": dt.strftime("%Y-%m-%d"),
                        "Year": dt.year,
                        "Magnitude": props.get("mag", 0),
                        "Depth (km)": coords[2] if len(coords) > 2 else 0,
                        "Place": props.get("place", "Unknown"),
                    })

            df_eq = pd.DataFrame(eq_rows)

            # Scatter plot
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=df_eq["Date"],
                y=df_eq["Magnitude"],
                mode="markers",
                marker=dict(
                    size=df_eq["Magnitude"] * 3,
                    color=df_eq["Magnitude"],
                    colorscale="YlOrRd",
                    showscale=True,
                    colorbar=dict(title="Mag"),
                ),
                text=df_eq["Place"],
                name="Earthquakes",
            ))
            fig_eq.update_layout(
                title=f"Earthquakes M4+ within 200km ({len(df_eq)} events)",
                xaxis_title="Date",
                yaxis_title="Magnitude",
                height=400,
                margin=dict(t=50, b=40),
            )
            st.plotly_chart(fig_eq, use_container_width=True, key="tla_eq")

            # Decade summary
            df_eq["Decade"] = (df_eq["Year"] // 10) * 10
            decade_counts = df_eq.groupby("Decade").size().reset_index(name="Count")
            fig_dec = go.Figure(data=go.Bar(
                x=decade_counts["Decade"].astype(str) + "s",
                y=decade_counts["Count"],
                marker_color="#f59e0b",
            ))
            fig_dec.update_layout(
                title="Earthquakes per Decade",
                height=300,
                margin=dict(t=50, b=30),
            )
            st.plotly_chart(fig_dec, use_container_width=True, key="tla_dec")

            # Summary stats
            eq1, eq2, eq3 = st.columns(3)
            with eq1:
                st.metric("Total Earthquakes", len(df_eq))
            with eq2:
                st.metric("Strongest", f"M{df_eq['Magnitude'].max():.1f}")
            with eq3:
                st.metric("Avg Magnitude", f"M{df_eq['Magnitude'].mean():.1f}")

            # Table
            with st.expander("Earthquake Details"):
                st.dataframe(df_eq.sort_values("Date", ascending=False),
                             use_container_width=True, hide_index=True)
        else:
            st.success("No significant earthquakes (M4+) recorded in this area.")
