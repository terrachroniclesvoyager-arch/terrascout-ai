"""
Climate Intelligence Dashboard for TerraScout AI.
Advanced climate analysis combining current conditions, 7-day forecast,
30-day trends, and climate classification with rich interactive charts.
Uses Open-Meteo forecast + archive APIs.
"""

import logging
import math
import pandas as pd
import numpy as np
import streamlit as st
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests

from src.deep_zone_analysis import (
    fetch_weather_data,
    classify_koppen,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False


@st.cache_data(ttl=600)
def _fetch_forecast_extended(lat, lon):
    """Fetch 14-day hourly forecast from Open-Meteo."""
    try:
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,"
                      "precipitation,cloud_cover,pressure_msl,uv_index,"
                      "soil_temperature_0cm,soil_moisture_0_to_1cm",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "wind_speed_10m_max,uv_index_max,sunrise,sunset,"
                     "precipitation_hours,precipitation_probability_max",
            "forecast_days": 14,
            "timezone": "auto",
        }
        resp = requests.get("https://api.open-meteo.com/v1/forecast",
                            params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Extended forecast error: {e}")
    return {}


@st.cache_data(ttl=3600)
def _fetch_climate_history(lat, lon, years=5):
    """Fetch historical climate data from Open-Meteo archive for last N years."""
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=365 * years)
    try:
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "wind_speed_10m_max",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "timezone": "auto",
        }
        resp = requests.get("https://archive-api.open-meteo.com/v1/archive",
                            params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Climate history error: {e}")
    return {}


def _compute_climate_stats(history_data):
    """Compute comprehensive climate statistics from historical data."""
    daily = history_data.get("daily", {})
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("wind_speed_10m_max", [])
    dates = daily.get("time", [])

    if not temps_max or not temps_min:
        return {}

    valid_max = [t for t in temps_max if t is not None]
    valid_min = [t for t in temps_min if t is not None]
    valid_precip = [p for p in precip if p is not None]
    valid_wind = [w for w in wind if w is not None]

    avg_temps = [(mx + mn) / 2 for mx, mn in zip(temps_max, temps_min)
                 if mx is not None and mn is not None]

    stats = {
        "record_high": max(valid_max) if valid_max else 0,
        "record_low": min(valid_min) if valid_min else 0,
        "avg_high": round(sum(valid_max) / len(valid_max), 1) if valid_max else 0,
        "avg_low": round(sum(valid_min) / len(valid_min), 1) if valid_min else 0,
        "avg_temp": round(sum(avg_temps) / len(avg_temps), 1) if avg_temps else 0,
        "total_precip_annual": round(sum(valid_precip) / max(1, len(dates) / 365), 1) if valid_precip else 0,
        "max_daily_precip": max(valid_precip) if valid_precip else 0,
        "rainy_days_per_year": round(sum(1 for p in valid_precip if p > 1) / max(1, len(dates) / 365)),
        "avg_wind": round(sum(valid_wind) / len(valid_wind), 1) if valid_wind else 0,
        "max_wind": max(valid_wind) if valid_wind else 0,
        "frost_days_per_year": round(sum(1 for t in valid_min if t < 0) / max(1, len(dates) / 365)),
        "hot_days_per_year": round(sum(1 for t in valid_max if t > 30) / max(1, len(dates) / 365)),
        "data_points": len(dates),
    }

    # Monthly averages
    monthly_data = {}
    for i, date_str in enumerate(dates):
        if not date_str:
            continue
        month = date_str[5:7]
        if month not in monthly_data:
            monthly_data[month] = {"max": [], "min": [], "precip": []}
        if i < len(temps_max) and temps_max[i] is not None:
            monthly_data[month]["max"].append(temps_max[i])
        if i < len(temps_min) and temps_min[i] is not None:
            monthly_data[month]["min"].append(temps_min[i])
        if i < len(precip) and precip[i] is not None:
            monthly_data[month]["precip"].append(precip[i])

    months_order = ["01", "02", "03", "04", "05", "06",
                    "07", "08", "09", "10", "11", "12"]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    monthly_stats = []
    for m, name in zip(months_order, month_names):
        md = monthly_data.get(m, {})
        mx = md.get("max", [])
        mn = md.get("min", [])
        pr = md.get("precip", [])
        monthly_stats.append({
            "month": name,
            "avg_high": round(sum(mx) / len(mx), 1) if mx else 0,
            "avg_low": round(sum(mn) / len(mn), 1) if mn else 0,
            "precip": round(sum(pr) / max(1, len(dates) / 365 / 12), 1) if pr else 0,
        })
    stats["monthly"] = monthly_stats

    # Climate classification
    if avg_temps:
        t_avg = stats["avg_temp"]
        t_max = stats["record_high"]
        t_min = stats["record_low"]
        annual_p = stats["total_precip_annual"]
        driest_month = min((m["precip"] for m in monthly_stats), default=0)
        stats["koppen"] = classify_koppen(t_avg, annual_p, t_max, t_min, driest_month)
    else:
        stats["koppen"] = "Unknown"

    return stats


def render_climate_dashboard_tab():
    """Main render function for Climate Intelligence Dashboard."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Climate Intelligence Dashboard</h4>
        <p>14-day forecast, 5-year trends, monthly climate profiles & classification</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Preset",
                              ["Custom"] + [k for k in ANALYSIS_PRESETS.keys() if k != "Custom"],
                              key="clim_preset")
        p = ANALYSIS_PRESETS.get(preset)
    with col2:
        lat = st.number_input("Latitude", -90.0, 90.0,
                              p.get("lat", 41.9028) if p else 41.9028, step=0.01,
                              key="clim_lat", format="%.4f")
    with col3:
        lon = st.number_input("Longitude", -180.0, 180.0,
                              p.get("lon", 12.4964) if p else 12.4964, step=0.01,
                              key="clim_lon", format="%.4f")

    if st.button("Analyze Climate", type="primary", use_container_width=True):
        with st.spinner("Fetching 14-day forecast..."):
            forecast = _fetch_forecast_extended(lat, lon)
        with st.spinner("Fetching 5-year climate history..."):
            history = _fetch_climate_history(lat, lon, years=5)
        with st.spinner("Computing climate statistics..."):
            stats = _compute_climate_stats(history)

        st.session_state["clim_results"] = {
            "forecast": forecast,
            "history": history,
            "stats": stats,
            "lat": lat, "lon": lon,
        }

    if "clim_results" not in st.session_state:
        return

    r = st.session_state["clim_results"]
    forecast = r["forecast"]
    stats = r["stats"]

    st.markdown("---")

    # Climate Classification header
    koppen = stats.get("koppen", "Unknown")
    st.markdown(f"""
    <div style="text-align:center; padding:15px; background:rgba(6,182,212,0.1);
                border-radius:10px; border:1px solid rgba(6,182,212,0.3); margin-bottom:15px;">
        <div style="font-size:2em; font-weight:bold; color:#06b6d4;">{koppen}</div>
        <div style="color:#9ca3af;">Climate Classification</div>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Avg Temperature", f"{stats.get('avg_temp', 0)} C")
    with m2:
        st.metric("Record High", f"{stats.get('record_high', 0)} C")
    with m3:
        st.metric("Record Low", f"{stats.get('record_low', 0)} C")
    with m4:
        st.metric("Annual Rainfall", f"{stats.get('total_precip_annual', 0)} mm")
    with m5:
        st.metric("Frost Days/yr", stats.get("frost_days_per_year", 0))
    with m6:
        st.metric("Hot Days/yr", stats.get("hot_days_per_year", 0))

    # 14-day forecast chart
    daily = forecast.get("daily", {})
    if daily:
        st.markdown("### 14-Day Forecast")
        dates = daily.get("time", [])
        t_max = daily.get("temperature_2m_max", [])
        t_min = daily.get("temperature_2m_min", [])
        p_sum = daily.get("precipitation_sum", [])
        p_prob = daily.get("precipitation_probability_max", [])

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.08,
                            row_heights=[0.6, 0.4])

        fig.add_trace(go.Scatter(x=dates, y=t_max, name="Max Temp",
                                 line=dict(color="#ef4444", width=2),
                                 fill=None), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=t_min, name="Min Temp",
                                 line=dict(color="#3b82f6", width=2),
                                 fill="tonexty",
                                 fillcolor="rgba(59,130,246,0.1)"), row=1, col=1)

        fig.add_trace(go.Bar(x=dates, y=p_sum, name="Precipitation (mm)",
                             marker_color="#06b6d4", opacity=0.7), row=2, col=1)
        if p_prob:
            fig.add_trace(go.Scatter(x=dates, y=p_prob, name="Rain Prob %",
                                     line=dict(color="#f59e0b", dash="dot"),
                                     yaxis="y4"), row=2, col=1)

        fig.update_layout(height=450, margin=dict(t=30, b=30),
                          yaxis_title="Temperature (C)",
                          yaxis3_title="Precipitation (mm)")
        st.plotly_chart(fig, use_container_width=True, key="clidas_pchart1")

    # Monthly climate profile
    monthly = stats.get("monthly", [])
    if monthly:
        st.markdown("### Monthly Climate Profile")
        months = [m["month"] for m in monthly]
        avg_highs = [m["avg_high"] for m in monthly]
        avg_lows = [m["avg_low"] for m in monthly]
        precips = [m["precip"] for m in monthly]

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(x=months, y=precips, name="Precipitation (mm)",
                              marker_color="rgba(6,182,212,0.5)",
                              yaxis="y2"), secondary_y=True)
        fig2.add_trace(go.Scatter(x=months, y=avg_highs, name="Avg High",
                                  line=dict(color="#ef4444", width=3),
                                  mode="lines+markers"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=months, y=avg_lows, name="Avg Low",
                                  line=dict(color="#3b82f6", width=3),
                                  mode="lines+markers"), secondary_y=False)

        fig2.update_layout(height=400, margin=dict(t=30, b=30))
        fig2.update_yaxes(title_text="Temperature (C)", secondary_y=False)
        fig2.update_yaxes(title_text="Precipitation (mm)", secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True, key="clidas_pchart2")

    # Hourly detail for today/tomorrow
    hourly = forecast.get("hourly", {})
    if hourly:
        st.markdown("### Hourly Detail (Next 48h)")
        h_time = hourly.get("time", [])[:48]
        h_temp = hourly.get("temperature_2m", [])[:48]
        h_humidity = hourly.get("relative_humidity_2m", [])[:48]
        h_wind = hourly.get("wind_speed_10m", [])[:48]
        h_cloud = hourly.get("cloud_cover", [])[:48]
        h_uv = hourly.get("uv_index", [])[:48]

        fig3 = make_subplots(rows=3, cols=1, shared_xaxes=True,
                             vertical_spacing=0.05,
                             subplot_titles=["Temperature & Humidity",
                                             "Wind Speed", "UV Index & Cloud Cover"])

        fig3.add_trace(go.Scatter(x=h_time, y=h_temp, name="Temp (C)",
                                  line_color="#ef4444"), row=1, col=1)
        fig3.add_trace(go.Scatter(x=h_time, y=h_humidity, name="Humidity %",
                                  line_color="#3b82f6", line_dash="dot"), row=1, col=1)
        fig3.add_trace(go.Scatter(x=h_time, y=h_wind, name="Wind (km/h)",
                                  line_color="#10b981", fill="tozeroy",
                                  fillcolor="rgba(16,185,129,0.1)"), row=2, col=1)
        fig3.add_trace(go.Bar(x=h_time, y=h_uv, name="UV Index",
                              marker_color="#f59e0b", opacity=0.7), row=3, col=1)
        fig3.add_trace(go.Scatter(x=h_time, y=h_cloud, name="Cloud %",
                                  line_color="#64748b", line_dash="dash"), row=3, col=1)

        fig3.update_layout(height=600, margin=dict(t=40, b=30))
        st.plotly_chart(fig3, use_container_width=True, key="clidas_pchart3")

    # Additional stats
    st.markdown("### Climate Statistics")
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("Avg Wind", f"{stats.get('avg_wind', 0)} km/h")
        st.metric("Max Wind", f"{stats.get('max_wind', 0)} km/h")
    with stat_cols[1]:
        st.metric("Rainy Days/yr", stats.get("rainy_days_per_year", 0))
        st.metric("Max Daily Rain", f"{stats.get('max_daily_precip', 0)} mm")
    with stat_cols[2]:
        st.metric("Avg High", f"{stats.get('avg_high', 0)} C")
        st.metric("Avg Low", f"{stats.get('avg_low', 0)} C")
    with stat_cols[3]:
        st.metric("Data Points", f"{stats.get('data_points', 0):,}")
        st.metric("Analysis Period", "5 years")

    # Export
    st.markdown("---")
    if monthly:
        df_export = pd.DataFrame(monthly)
        df_export["latitude"] = r["lat"]
        df_export["longitude"] = r["lon"]
        df_export["climate_zone"] = koppen
        if HAS_EXPORT:
            render_export_buttons(df_export, prefix="climate", lat_col="latitude", lon_col="longitude")
        else:
            csv = df_export.to_csv(index=False)
            st.download_button("Download Climate Data (CSV)", data=csv,
                               file_name="climate_profile.csv", mime="text/csv")
