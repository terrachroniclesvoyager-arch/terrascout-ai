"""
Change Detector AI — Temporal change detection and trend forecasting.
Analyzes how environmental parameters have changed over time using
historical weather data, seismic records, and land use trends.
Uses: Open-Meteo Archive, USGS, Open Topo Data, Overpass.
"""

import math
import logging
from datetime import datetime, timedelta

import numpy as np
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_earthquakes,
    fetch_water_features,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"


@st.cache_data(ttl=3600)
def _fetch_historical_climate(lat: float, lon: float, years: int = 10) -> dict:
    """Fetch historical daily climate data from Open-Meteo Archive."""
    import requests

    end_date = datetime.now() - timedelta(days=7)
    start_date = end_date - timedelta(days=years * 365)

    try:
        resp = requests.get(ARCHIVE_API, params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "wind_speed_10m_max",
            "timezone": "auto",
        }, timeout=30)
        if resp.ok:
            return resp.json()
    except Exception as e:
        logger.warning(f"Historical climate fetch failed: {e}")
    return {}


@st.cache_data(ttl=1800)
def detect_changes(lat: float, lon: float) -> dict:
    """Detect temporal changes across multiple environmental parameters."""
    # Fetch historical climate data (10 years)
    hist = _fetch_historical_climate(lat, lon, years=10)
    daily = hist.get("daily", {})

    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("wind_speed_10m_max", [])

    changes = []
    trends = {}
    yearly_data = {}

    if dates and len(dates) > 365:
        # Group by year
        year_temps = {}
        year_precip = {}
        year_wind = {}

        for i, date_str in enumerate(dates):
            try:
                year = int(date_str[:4])
            except (ValueError, IndexError):
                continue

            if year not in year_temps:
                year_temps[year] = []
                year_precip[year] = []
                year_wind[year] = []

            if i < len(temp_max) and temp_max[i] is not None:
                year_temps[year].append(temp_max[i])
            if i < len(precip) and precip[i] is not None:
                year_precip[year].append(precip[i])
            if i < len(wind) and wind[i] is not None:
                year_wind[year].append(wind[i])

        sorted_years = sorted(year_temps.keys())
        if len(sorted_years) >= 3:
            # ── Temperature trend ──
            yearly_avg_temp = []
            for y in sorted_years:
                temps = year_temps.get(y, [])
                if temps:
                    yearly_avg_temp.append({"year": y, "avg": sum(temps) / len(temps)})

            if len(yearly_avg_temp) >= 3:
                first_3 = [d["avg"] for d in yearly_avg_temp[:3]]
                last_3 = [d["avg"] for d in yearly_avg_temp[-3:]]
                temp_change = sum(last_3) / len(last_3) - sum(first_3) / len(first_3)

                trends["temperature"] = {
                    "yearly": yearly_avg_temp,
                    "change": round(temp_change, 2),
                    "direction": "warming" if temp_change > 0.3 else "cooling" if temp_change < -0.3 else "stable",
                }

                if abs(temp_change) > 0.5:
                    changes.append({
                        "parameter": "Temperature",
                        "change": f"{'+' if temp_change > 0 else ''}{temp_change:.1f}C",
                        "direction": "up" if temp_change > 0 else "down",
                        "severity": "high" if abs(temp_change) > 1.5 else "medium",
                        "detail": f"Average max temperature has {'increased' if temp_change > 0 else 'decreased'} "
                                  f"by {abs(temp_change):.1f}C over the analysis period.",
                    })

            # ── Precipitation trend ──
            yearly_total_precip = []
            for y in sorted_years:
                precs = year_precip.get(y, [])
                if precs:
                    annual = sum(precs) * (365 / max(len(precs), 1))
                    yearly_total_precip.append({"year": y, "total": annual})

            if len(yearly_total_precip) >= 3:
                first_3p = [d["total"] for d in yearly_total_precip[:3]]
                last_3p = [d["total"] for d in yearly_total_precip[-3:]]
                precip_change = sum(last_3p) / len(last_3p) - sum(first_3p) / len(first_3p)
                pct_change = (precip_change / max(sum(first_3p) / len(first_3p), 1)) * 100

                trends["precipitation"] = {
                    "yearly": yearly_total_precip,
                    "change_mm": round(precip_change, 1),
                    "change_pct": round(pct_change, 1),
                    "direction": "wetter" if precip_change > 20 else "drier" if precip_change < -20 else "stable",
                }

                if abs(pct_change) > 10:
                    changes.append({
                        "parameter": "Precipitation",
                        "change": f"{'+' if pct_change > 0 else ''}{pct_change:.0f}%",
                        "direction": "up" if pct_change > 0 else "down",
                        "severity": "high" if abs(pct_change) > 25 else "medium",
                        "detail": f"Annual precipitation has {'increased' if pct_change > 0 else 'decreased'} "
                                  f"by {abs(pct_change):.0f}% ({abs(precip_change):.0f}mm).",
                    })

            # ── Wind trend ──
            yearly_avg_wind = []
            for y in sorted_years:
                winds = year_wind.get(y, [])
                if winds:
                    yearly_avg_wind.append({"year": y, "avg": sum(winds) / len(winds)})

            if len(yearly_avg_wind) >= 3:
                first_3w = [d["avg"] for d in yearly_avg_wind[:3]]
                last_3w = [d["avg"] for d in yearly_avg_wind[-3:]]
                wind_change = sum(last_3w) / len(last_3w) - sum(first_3w) / len(first_3w)

                trends["wind"] = {
                    "yearly": yearly_avg_wind,
                    "change": round(wind_change, 2),
                    "direction": "increasing" if wind_change > 1 else "decreasing" if wind_change < -1 else "stable",
                }

            # ── Extreme events ──
            extreme_heat_days = {}
            extreme_rain_days = {}
            for y in sorted_years:
                temps = year_temps.get(y, [])
                precs = year_precip.get(y, [])
                extreme_heat_days[y] = sum(1 for t in temps if t > 35)
                extreme_rain_days[y] = sum(1 for p in precs if p > 20)

            if sorted_years:
                first_extreme_heat = sum(extreme_heat_days.get(y, 0) for y in sorted_years[:3]) / 3
                last_extreme_heat = sum(extreme_heat_days.get(y, 0) for y in sorted_years[-3:]) / 3
                heat_change = last_extreme_heat - first_extreme_heat

                if abs(heat_change) > 2:
                    changes.append({
                        "parameter": "Extreme Heat Days (>35C)",
                        "change": f"{'+' if heat_change > 0 else ''}{heat_change:.0f} days/yr",
                        "direction": "up" if heat_change > 0 else "down",
                        "severity": "high" if heat_change > 5 else "medium",
                        "detail": f"Days above 35C changed from ~{first_extreme_heat:.0f} to ~{last_extreme_heat:.0f} per year.",
                    })

                trends["extreme_heat"] = {
                    "yearly": [{"year": y, "days": extreme_heat_days.get(y, 0)} for y in sorted_years],
                }
                trends["extreme_rain"] = {
                    "yearly": [{"year": y, "days": extreme_rain_days.get(y, 0)} for y in sorted_years],
                }

    # ── Seismic activity trend ──
    eq_recent = fetch_earthquakes(lat, lon, radius_km=150, days=365) or {}
    eq_older = fetch_earthquakes(lat, lon, radius_km=150, days=1825) or {}

    recent_count = len(eq_recent.get("features", []))
    older_count = len(eq_older.get("features", []))
    annual_rate = older_count / 5 if older_count > 0 else 0

    if recent_count > annual_rate * 1.5 and recent_count > 5:
        changes.append({
            "parameter": "Seismic Activity",
            "change": f"+{((recent_count / max(annual_rate, 1)) - 1) * 100:.0f}%",
            "direction": "up",
            "severity": "high",
            "detail": f"Recent year: {recent_count} events. 5-year avg: {annual_rate:.0f}/yr. Elevated activity.",
        })

    trends["seismic"] = {
        "recent_annual": recent_count,
        "five_year_avg": round(annual_rate, 1),
    }

    # Forecast projection
    forecasts = []
    if "temperature" in trends:
        t_trend = trends["temperature"]
        if t_trend["direction"] == "warming":
            forecasts.append({
                "parameter": "Temperature",
                "projection": f"+{t_trend['change'] * 2:.1f}C by next decade",
                "confidence": "medium",
                "impact": "Higher cooling costs, altered growing seasons, increased heat stress.",
            })
    if "precipitation" in trends:
        p_trend = trends["precipitation"]
        if p_trend["direction"] != "stable":
            forecasts.append({
                "parameter": "Precipitation",
                "projection": f"{'+' if p_trend['change_mm'] > 0 else ''}{p_trend['change_pct'] * 2:.0f}% change projected",
                "confidence": "low",
                "impact": "Water availability changes, flood/drought risk shifting.",
            })

    return {
        "changes": changes,
        "trends": trends,
        "forecasts": forecasts,
        "years_analyzed": len(sorted_years) if 'sorted_years' in dir() and sorted_years else len(dates) // 365 if dates else 0,
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_change_detector_tab():
    """Render the Change Detector AI tab."""
    st.markdown("## Change Detector AI")
    st.caption("Temporal change detection and environmental trend forecasting")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="cd_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="cd_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="cd_lon", format="%.4f")

    if st.button("Detect Changes", type="primary", use_container_width=True):
        with st.spinner("Analyzing 10 years of environmental data..."):
            result = detect_changes(lat, lon)

        if not result:
            st.error("Failed to detect changes.")
            return

        changes = result["changes"]
        trends = result["trends"]
        forecasts = result["forecasts"]

        # ── Summary ──
        total_changes = len(changes)
        high_severity = sum(1 for c in changes if c.get("severity") == "high")
        upward = sum(1 for c in changes if c.get("direction") == "up")
        downward = sum(1 for c in changes if c.get("direction") == "down")

        mc = st.columns(4)
        mc[0].metric("Changes Detected", total_changes)
        mc[1].metric("High Severity", high_severity)
        mc[2].metric("Increasing", upward)
        mc[3].metric("Decreasing", downward)

        # ── Change cards ──
        if changes:
            st.markdown("### Detected Changes")
            for ch in changes:
                sev = ch.get("severity", "medium")
                direction = ch.get("direction", "up")
                if sev == "high":
                    border = "#ef4444"
                else:
                    border = "#f59e0b"

                arrow = "trending_up" if direction == "up" else "trending_down"
                arrow_char = "+" if direction == "up" else ""

                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:4px solid {border};
                            border-radius:8px; padding:14px; margin:8px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#eee; font-weight:bold; font-size:16px;">
                            {ch['parameter']}
                        </span>
                        <span style="color:{border}; font-weight:bold; font-size:20px;">
                            {ch['change']}
                        </span>
                    </div>
                    <div style="color:#aaa; font-size:13px; margin-top:6px;">
                        {ch['detail']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Temperature trend chart ──
        if "temperature" in trends:
            st.markdown("### Temperature Trend")
            t_data = trends["temperature"]
            years = [d["year"] for d in t_data["yearly"]]
            temps = [d["avg"] for d in t_data["yearly"]]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=temps,
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=6),
                name="Avg Max Temp",
            ))
            # Trend line
            if len(years) >= 3:
                z = np.polyfit(range(len(temps)), temps, 1)
                trend_line = np.polyval(z, range(len(temps)))
                fig.add_trace(go.Scatter(
                    x=years, y=trend_line,
                    mode="lines",
                    line=dict(color="rgba(239,68,68,0.27)", width=1, dash="dash"),
                    name="Trend",
                ))
            fig.update_layout(
                height=350,
                margin=dict(t=20, b=40),
                xaxis_title="Year",
                yaxis_title="Avg Max Temp (C)",
            )
            st.plotly_chart(fig, use_container_width=True, key="chadet_pchart1")

            direction = t_data["direction"]
            change = t_data["change"]
            st.markdown(f"**Trend**: {direction.title()} ({'+' if change > 0 else ''}{change:.2f}C)")

        # ── Precipitation trend chart ──
        if "precipitation" in trends:
            st.markdown("### Precipitation Trend")
            p_data = trends["precipitation"]
            years = [d["year"] for d in p_data["yearly"]]
            totals = [d["total"] for d in p_data["yearly"]]

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=years, y=totals,
                marker_color="#3b82f6",
                name="Annual Precipitation",
            ))
            if len(years) >= 3:
                z = np.polyfit(range(len(totals)), totals, 1)
                trend_line = np.polyval(z, range(len(totals)))
                fig2.add_trace(go.Scatter(
                    x=years, y=trend_line,
                    mode="lines",
                    line=dict(color="#ef4444", width=2, dash="dash"),
                    name="Trend",
                ))
            fig2.update_layout(
                height=350,
                margin=dict(t=20, b=40),
                xaxis_title="Year",
                yaxis_title="Annual Precipitation (mm)",
            )
            st.plotly_chart(fig2, use_container_width=True, key="chadet_pchart2")

            st.markdown(f"**Trend**: {p_data['direction'].title()} "
                        f"({'+' if p_data['change_mm'] > 0 else ''}{p_data['change_mm']:.0f}mm, "
                        f"{'+' if p_data['change_pct'] > 0 else ''}{p_data['change_pct']:.0f}%)")

        # ── Extreme events chart ──
        if "extreme_heat" in trends and "extreme_rain" in trends:
            st.markdown("### Extreme Events Trend")
            heat_data = trends["extreme_heat"]["yearly"]
            rain_data = trends["extreme_rain"]["yearly"]

            years = [d["year"] for d in heat_data]
            heat_days = [d["days"] for d in heat_data]
            rain_days = [d["days"] for d in rain_data]

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=years, y=heat_days,
                name="Extreme Heat (>35C)",
                marker_color="#f97316",
            ))
            fig3.add_trace(go.Bar(
                x=years, y=rain_days,
                name="Heavy Rain (>20mm)",
                marker_color="#3b82f6",
            ))
            fig3.update_layout(
                barmode="group",
                height=350,
                margin=dict(t=20, b=40),
                xaxis_title="Year",
                yaxis_title="Days per Year",
            )
            st.plotly_chart(fig3, use_container_width=True, key="chadet_pchart3")

        # ── Seismic activity ──
        if "seismic" in trends:
            st.markdown("### Seismic Activity")
            s_data = trends["seismic"]
            sc1, sc2 = st.columns(2)
            sc1.metric("Recent Year Events", s_data["recent_annual"])
            sc2.metric("5-Year Average", f"{s_data['five_year_avg']}/yr")

        # ── Forecasts ──
        if forecasts:
            st.markdown("### AI Projections")
            for fc in forecasts:
                st.markdown(f"""
                <div style="background:#1a1a2e; border-left:4px solid #8b5cf6;
                            border-radius:8px; padding:12px; margin:6px 0;">
                    <div style="color:#8b5cf6; font-weight:bold;">{fc['parameter']}</div>
                    <div style="color:#eee; font-size:18px; margin:4px 0;">
                        {fc['projection']}
                    </div>
                    <div style="color:#aaa; font-size:13px;">
                        Impact: {fc['impact']}
                    </div>
                    <div style="color:#666; font-size:11px;">
                        Confidence: {fc['confidence'].title()}
                    </div>
                </div>
                """, unsafe_allow_html=True)
