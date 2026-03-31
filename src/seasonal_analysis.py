"""
Seasonal Pattern Analysis module for TerraScout AI.
Analyzes how a location changes across seasons using temperature, precipitation,
daylight, and wind data. Computes growing season, Koppen classification, and
recommends best visit months using multi-factor scoring.
Uses Open-Meteo Archive API (free, no key required).
"""

import logging
import math
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
MONTH_15TH_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]

CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_WARM, CLR_COOL, CLR_RAIN = "#ef4444", "#3b82f6", "#06b6d4"
CLR_SUN, CLR_WIND, CLR_GREEN = "#facc15", "#a78bfa", "#22c55e"
CLR_GOLD, CLR_ACCENT = "#f59e0b", "#e879f9"

ARCHIVE_BASE = "https://archive-api.open-meteo.com/v1/archive"


# ---------------------------------------------------------------------------
# Data fetching (cached, timeout, try/except)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_all_seasonal_data(lat: float, lon: float) -> dict:
    """Fetch 2023 full-year daily temp, precip, wind from Open-Meteo Archive."""
    try:
        resp = requests.get(ARCHIVE_BASE, params={
            "latitude": lat, "longitude": lon,
            "start_date": "2023-01-01", "end_date": "2023-12-31",
            "daily": ("temperature_2m_max,temperature_2m_min,"
                      "precipitation_sum,wind_speed_10m_max"),
            "timezone": "auto",
        }, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        logger.warning("Seasonal data fetch failed: %s", exc)
    return {}


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------
def _aggregate_monthly(daily: dict) -> dict:
    """Aggregate daily data into monthly statistics (0-11 keyed dict)."""
    dates = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("wind_speed_10m_max", [])
    buckets = {m: {"max": [], "min": [], "precip": [], "wind": []} for m in range(12)}

    for i, d in enumerate(dates):
        if not d:
            continue
        mi = int(d[5:7]) - 1
        if i < len(t_max) and t_max[i] is not None:
            buckets[mi]["max"].append(t_max[i])
        if i < len(t_min) and t_min[i] is not None:
            buckets[mi]["min"].append(t_min[i])
        if i < len(precip) and precip[i] is not None:
            buckets[mi]["precip"].append(precip[i])
        if i < len(wind) and wind[i] is not None:
            buckets[mi]["wind"].append(wind[i])

    monthly = {}
    for m in range(12):
        b = buckets[m]
        mx, mn, pr, wd = b["max"], b["min"], b["precip"], b["wind"]
        avg_max = round(sum(mx) / len(mx), 1) if mx else 0.0
        avg_min = round(sum(mn) / len(mn), 1) if mn else 0.0
        monthly[m] = {
            "avg_max": avg_max, "avg_min": avg_min,
            "avg_temp": round((avg_max + avg_min) / 2, 1),
            "total_precip": round(sum(pr), 1),
            "avg_wind": round(sum(wd) / len(wd), 1) if wd else 0.0,
            "days": len(mx),
        }
    return monthly


def _calc_daylight_hours(lat: float) -> list:
    """Approximate daylight hours for the 15th of each month via solar declination."""
    lat_rad = math.radians(lat)
    results = []
    for doy in MONTH_15TH_DOY:
        decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + doy) / 365)))
        cos_ha = -math.tan(lat_rad) * math.tan(decl)
        if cos_ha <= -1.0:
            results.append(24.0)
        elif cos_ha >= 1.0:
            results.append(0.0)
        else:
            results.append(round(2.0 * math.acos(cos_ha) * 24.0 / (2.0 * math.pi), 2))
    return results


def _identify_growing_season(monthly: dict) -> dict:
    """Months where avg_temp > 5 C AND monthly precip > 30 mm."""
    growing = [m for m in range(12)
               if monthly[m]["avg_temp"] > 5.0 and monthly[m]["total_precip"] > 30.0]
    if not growing:
        return {"months": [], "length": 0, "start": None, "end": None}
    return {"months": growing, "length": len(growing),
            "start": MONTH_FULL[growing[0]], "end": MONTH_FULL[growing[-1]]}


def _score_best_month(monthly: dict, daylight: list) -> list:
    """Score months for visit suitability (temp comfort, low rain, daylight, low wind)."""
    scores = []
    max_dl = max(daylight) if daylight else 12.0
    for m in range(12):
        md = monthly.get(m, {})
        avg_t = md.get("avg_temp", 15.0)
        pr = md.get("total_precip", 0.0)
        w = md.get("avg_wind", 0.0)
        dl = daylight[m] if m < len(daylight) else 12.0
        ts = max(0.0, 100.0 - abs(avg_t - 20.0) * 8.0)      # ideal 15-25 C
        rs = max(0.0, 100.0 - pr * 0.833)                     # lower rain better
        ds = (dl / max_dl) * 100.0 if max_dl > 0 else 50.0    # more daylight better
        ws = max(0.0, 100.0 - w * 2.5)                        # lower wind better
        total = ts * 0.35 + rs * 0.25 + ds * 0.20 + ws * 0.20
        scores.append({
            "month": MONTH_NAMES[m], "month_full": MONTH_FULL[m],
            "temp_score": round(ts, 1), "rain_score": round(rs, 1),
            "day_score": round(ds, 1), "wind_score": round(ws, 1),
            "total": round(total, 1),
            "avg_temp": avg_t, "precip": pr, "daylight": dl, "wind": w,
        })
    scores.sort(key=lambda x: x["total"], reverse=True)
    return scores


def _estimate_koppen(monthly: dict) -> str:
    """Estimate Koppen climate classification from monthly patterns."""
    temps = [monthly[m]["avg_temp"] for m in range(12)]
    precips = [monthly[m]["total_precip"] for m in range(12)]
    t_avg, t_max_m, t_min_m = sum(temps) / 12, max(temps), min(temps)
    p_total, p_driest = sum(precips), min(precips)
    # E: Polar
    if t_max_m < 10:
        return ("EF - Ice Cap (all months below 0 C)" if t_max_m < 0
                else "ET - Tundra (warmest month below 10 C)")
    # B: Arid
    threshold = 20 * t_avg + 280
    if p_total < threshold:
        if p_total < threshold / 2:
            return "BWh - Hot Desert" if t_avg >= 18 else "BWk - Cold Desert"
        return ("BSh - Hot Semi-Arid (Steppe)" if t_avg >= 18
                else "BSk - Cold Semi-Arid (Steppe)")
    # A: Tropical
    if t_min_m >= 18:
        if p_driest >= 60:
            return "Af - Tropical Rainforest"
        if p_driest >= 100 - (p_total / 25):
            return "Am - Tropical Monsoon"
        return "Aw - Tropical Savanna"
    # D: Continental
    if t_min_m < -3:
        if p_driest < 30:
            return ("Dwa - Hot-Summer Continental (dry winter)" if t_max_m >= 22
                    else "Dwb - Warm-Summer Continental (dry winter)")
        if t_max_m >= 22:
            return "Dfa - Hot-Summer Continental"
        return ("Dfb - Warm-Summer Continental"
                if sum(1 for t in temps if t >= 10) >= 4 else "Dfc - Subarctic")
    # C: Temperate
    if p_driest < 30:
        return ("Cwa - Humid Subtropical (dry winter)" if t_max_m >= 22
                else "Cwb - Subtropical Highland (dry winter)")
    if min(precips[3:9]) < 30:
        return ("Csa - Hot-Summer Mediterranean" if t_max_m >= 22
                else "Csb - Warm-Summer Mediterranean")
    return "Cfa - Humid Subtropical" if t_max_m >= 22 else "Cfb - Oceanic"


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------
def _chart_temperature_profile(monthly: dict) -> go.Figure:
    """Dual bar chart of monthly avg max/min temperatures."""
    months = MONTH_NAMES
    avg_max = [monthly[m]["avg_max"] for m in range(12)]
    avg_min = [monthly[m]["avg_min"] for m in range(12)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=avg_max, name="Avg Max", marker_color=CLR_WARM,
                         opacity=0.85, text=[f"{v:.1f}" for v in avg_max],
                         textposition="outside"))
    fig.add_trace(go.Bar(x=months, y=avg_min, name="Avg Min", marker_color=CLR_COOL,
                         opacity=0.85, text=[f"{v:.1f}" for v in avg_min],
                         textposition="outside"))
    fig.update_layout(
        title="Monthly Temperature Profile (2023)", barmode="group",
        xaxis_title="Month", yaxis_title="Temperature (C)",
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
        height=420, margin=dict(l=50, r=30, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    return fig


def _chart_precipitation(monthly: dict) -> go.Figure:
    """Bar chart with wet/dry colouring and average line."""
    precips = [monthly[m]["total_precip"] for m in range(12)]
    avg_p = sum(precips) / 12
    colors = [CLR_RAIN if p > avg_p else CLR_GOLD for p in precips]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=MONTH_NAMES, y=precips, marker_color=colors, opacity=0.85,
                         text=[f"{v:.0f}" for v in precips], textposition="outside"))
    fig.add_hline(y=avg_p, line_dash="dash", line_color=CLR_TEXT_SEC,
                  annotation_text=f"Avg: {avg_p:.0f} mm", annotation_position="top right")
    fig.update_layout(
        title="Monthly Precipitation Calendar (2023)",
        xaxis_title="Month", yaxis_title="Precipitation (mm)",
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
        height=400, margin=dict(l=50, r=30, t=60, b=40))
    return fig


def _chart_daylight(daylight: list) -> go.Figure:
    """Area chart of daylight hours by month."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES, y=daylight, mode="lines+markers", fill="tozeroy",
        marker=dict(color=CLR_SUN, size=8), line=dict(color=CLR_SUN, width=2),
        fillcolor="rgba(250,204,21,0.2)",
        text=[f"{h:.1f}h" for h in daylight],
        hovertemplate="%{x}: %{text}<extra></extra>"))
    fig.add_hline(y=12, line_dash="dot", line_color=CLR_TEXT_SEC,
                  annotation_text="12h Equinox", annotation_position="top right")
    fig.update_layout(
        title="Daylight Hours by Month",
        xaxis_title="Month", yaxis_title="Hours of Daylight",
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
        height=380, yaxis=dict(range=[0, 26]), margin=dict(l=50, r=30, t=60, b=40))
    return fig


def _chart_wind(monthly: dict) -> go.Figure:
    """Line chart of monthly avg max wind speed."""
    winds = [monthly[m]["avg_wind"] for m in range(12)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTH_NAMES, y=winds, mode="lines+markers+text",
        marker=dict(color=CLR_WIND, size=9, symbol="diamond"),
        line=dict(color=CLR_WIND, width=2.5),
        text=[f"{w:.1f}" for w in winds], textposition="top center",
        textfont=dict(size=10)))
    fig.update_layout(
        title="Monthly Wind Speed Patterns (2023)",
        xaxis_title="Month", yaxis_title="Avg Max Wind Speed (km/h)",
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
        height=380, margin=dict(l=50, r=30, t=60, b=40))
    return fig


def _chart_growing(growing: dict) -> go.Figure:
    """Horizontal stacked bar showing growing vs dormant months."""
    gm = growing.get("months", [])
    fig = go.Figure()
    for m in range(12):
        clr = CLR_GREEN if m in gm else "#4b5563"
        fig.add_trace(go.Bar(
            x=[1], y=["Growing Season"], orientation="h", marker_color=clr,
            showlegend=False, text=MONTH_NAMES[m], textposition="inside",
            textfont=dict(size=10, color="white"),
            hovertemplate=f"{MONTH_NAMES[m]}: {'Growing' if m in gm else 'Dormant'}<extra></extra>"))
    fig.update_layout(
        barmode="stack", template="plotly_dark",
        paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE, height=120,
        margin=dict(l=100, r=30, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showgrid=False))
    return fig


def _chart_radar(top: dict) -> go.Figure:
    """Radar chart for best-month score breakdown."""
    cats = ["Temperature", "Low Rain", "Daylight", "Low Wind", "Temperature"]
    vals = [top["temp_score"], top["rain_score"], top["day_score"],
            top["wind_score"], top["temp_score"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor="rgba(34,197,94,0.25)", line=dict(color=CLR_GREEN, width=2),
        marker=dict(size=6)))
    fig.update_layout(
        polar=dict(bgcolor=CLR_SURFACE,
                   radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9))),
        template="plotly_dark", paper_bgcolor=CLR_BG,
        height=350, margin=dict(l=60, r=60, t=30, b=30), showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def _card(label: str, value: str, sub: str = "", color: str = CLR_TEXT) -> str:
    """HTML metric card."""
    return (f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
            f'border-radius:8px;padding:14px 16px;text-align:center;">'
            f'<div style="color:{CLR_TEXT_SEC};font-size:0.78rem;">{label}</div>'
            f'<div style="color:{color};font-size:1.6rem;font-weight:700;'
            f'margin:4px 0;">{value}</div>'
            f'<div style="color:{CLR_TEXT_SEC};font-size:0.72rem;">{sub}</div></div>')


def _summary_table(monthly: dict, daylight: list) -> str:
    """Full 12-month HTML summary table."""
    rows = ""
    for m in range(12):
        md = monthly[m]
        dl = daylight[m] if m < len(daylight) else 0
        rows += (f'<tr style="border-bottom:1px solid {CLR_BORDER};">'
                 f'<td style="padding:6px 10px;font-weight:600;">{MONTH_NAMES[m]}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_WARM};">{md["avg_max"]:.1f}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_COOL};">{md["avg_min"]:.1f}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_RAIN};">{md["total_precip"]:.0f}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_SUN};">{dl:.1f}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_WIND};">{md["avg_wind"]:.1f}</td></tr>')
    hdr = (f'<tr style="background:{CLR_CARD};border-bottom:2px solid {CLR_BORDER};">'
           '<th style="padding:8px 10px;text-align:left;">Month</th>'
           '<th style="padding:8px 10px;">Max C</th>'
           '<th style="padding:8px 10px;">Min C</th>'
           '<th style="padding:8px 10px;">Precip mm</th>'
           '<th style="padding:8px 10px;">Daylight h</th>'
           '<th style="padding:8px 10px;">Wind km/h</th></tr>')
    return (f'<table style="width:100%;border-collapse:collapse;color:{CLR_TEXT};'
            f'font-size:0.85rem;background:{CLR_SURFACE};border-radius:8px;'
            f'overflow:hidden;"><thead>{hdr}</thead><tbody>{rows}</tbody></table>')


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_seasonal_analysis_tab():
    """Render the complete Seasonal Pattern Analysis tab."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f3460,#1a1a2e);'
        f'border:1px solid #1a4080;border-radius:10px;padding:18px 22px;margin-bottom:18px;">'
        f'<h3 style="margin:0;color:#e8ecf4;">&#127810; Seasonal Pattern Analysis</h3>'
        f'<p style="margin:6px 0 0;color:#8b97b0;font-size:0.92rem;">'
        f'How temperature, rain, daylight &amp; wind change across the year</p></div>',
        unsafe_allow_html=True)

    # -- Inputs --
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, min_value=-90.0, max_value=90.0,
                          format="%.4f", key="season_lat")
    lon = c2.number_input("Longitude", value=12.5, min_value=-180.0, max_value=180.0,
                          format="%.4f", key="season_lon")

    if st.button("Analyze Seasons", key="season_btn", type="primary",
                 use_container_width=True):
        with st.spinner("Fetching seasonal climate data for 2023..."):
            raw = _fetch_all_seasonal_data(lat, lon)
        if not raw or "daily" not in raw:
            st.error("Could not retrieve seasonal data. Check coordinates or try again.")
            return
        monthly = _aggregate_monthly(raw["daily"])
        daylight = _calc_daylight_hours(lat)
        st.session_state["season_results"] = {
            "monthly": monthly, "daylight": daylight,
            "growing": _identify_growing_season(monthly),
            "scores": _score_best_month(monthly, daylight),
            "koppen": _estimate_koppen(monthly),
            "lat": lat, "lon": lon,
        }

    # -- Guard --
    if "season_results" not in st.session_state:
        st.info("Enter coordinates and click **Analyze Seasons** to begin.")
        return

    res = st.session_state["season_results"]
    monthly, daylight = res["monthly"], res["daylight"]
    growing, scores, koppen = res["growing"], res["scores"], res["koppen"]

    # ======================================================================
    # Overview metrics
    # ======================================================================
    st.markdown("### Overview")
    temps_avg = [monthly[m]["avg_temp"] for m in range(12)]
    precips_total = sum(monthly[m]["total_precip"] for m in range(12))
    warmest_m = max(range(12), key=lambda m: monthly[m]["avg_max"])
    coldest_m = min(range(12), key=lambda m: monthly[m]["avg_min"])
    wettest_m = max(range(12), key=lambda m: monthly[m]["total_precip"])
    windiest_m = max(range(12), key=lambda m: monthly[m]["avg_wind"])

    ov1, ov2, ov3, ov4 = st.columns(4)
    ov1.markdown(_card("Warmest Month", MONTH_NAMES[warmest_m],
                       f"{monthly[warmest_m]['avg_max']:.1f} C avg max", CLR_WARM),
                 unsafe_allow_html=True)
    ov2.markdown(_card("Coldest Month", MONTH_NAMES[coldest_m],
                       f"{monthly[coldest_m]['avg_min']:.1f} C avg min", CLR_COOL),
                 unsafe_allow_html=True)
    ov3.markdown(_card("Annual Precip", f"{precips_total:.0f} mm",
                       f"Wettest: {MONTH_NAMES[wettest_m]}", CLR_RAIN),
                 unsafe_allow_html=True)
    k_code = koppen.split(" - ")[0] if " - " in koppen else koppen[:4]
    k_desc = koppen.split(" - ")[1] if " - " in koppen else koppen
    ov4.markdown(_card("Climate Type", k_code, k_desc, CLR_ACCENT),
                 unsafe_allow_html=True)
    st.markdown("---")

    # ======================================================================
    # 1. Monthly Temperature Profile
    # ======================================================================
    st.markdown("### 1. Monthly Temperature Profile")
    st.plotly_chart(_chart_temperature_profile(monthly, key="seaana_pchart1"), use_container_width=True,
                    key="season_temp_chart")
    temp_range = monthly[warmest_m]["avg_max"] - monthly[coldest_m]["avg_min"]
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Annual Temp Range", f"{temp_range:.1f} C")
    tc2.metric("Avg Annual Temp", f"{sum(temps_avg) / 12:.1f} C")
    tc3.metric("Continentality",
               "High" if temp_range > 30 else ("Moderate" if temp_range > 15 else "Low"))
    st.markdown("---")

    # ======================================================================
    # 2. Precipitation Calendar
    # ======================================================================
    st.markdown("### 2. Precipitation Calendar")
    st.plotly_chart(_chart_precipitation(monthly, key="seaana_pchart2"), use_container_width=True,
                    key="season_precip_chart")
    avg_p = precips_total / 12
    wet = [MONTH_NAMES[m] for m in range(12) if monthly[m]["total_precip"] > avg_p]
    dry = [MONTH_NAMES[m] for m in range(12) if monthly[m]["total_precip"] <= avg_p]
    pc1, pc2 = st.columns(2)
    pc1.markdown(_card("Wet Season", ", ".join(wet) if wet else "N/A",
                       f"Above {avg_p:.0f} mm/month", CLR_RAIN), unsafe_allow_html=True)
    pc2.markdown(_card("Dry Season", ", ".join(dry) if dry else "N/A",
                       f"Below {avg_p:.0f} mm/month", CLR_GOLD), unsafe_allow_html=True)
    st.markdown("---")

    # ======================================================================
    # 3. Growing Season
    # ======================================================================
    st.markdown("### 3. Growing Season Analysis")
    if growing["length"] > 0:
        st.plotly_chart(_chart_growing(growing, key="seaana_pchart3"), use_container_width=True,
                        key="season_grow_chart")
        gc1, gc2, gc3 = st.columns(3)
        gc1.markdown(_card("Growing Season Length", f"{growing['length']} months",
                           f"{growing['start']} to {growing['end']}", CLR_GREEN),
                     unsafe_allow_html=True)
        gc2.markdown(_card("First Growing Month", growing["start"] or "N/A",
                           "", CLR_GREEN), unsafe_allow_html=True)
        gc3.markdown(_card("Last Growing Month", growing["end"] or "N/A",
                           "", CLR_GREEN), unsafe_allow_html=True)
        gn = [MONTH_NAMES[m] for m in growing["months"]]
        st.caption(f"Growing months (avg temp > 5 C AND precip > 30 mm): {', '.join(gn)}")
    else:
        st.warning("No months meet the growing criteria "
                   "(avg temp > 5 C AND precipitation > 30 mm).")
    st.markdown("---")

    # ======================================================================
    # 4. Daylight Hours
    # ======================================================================
    st.markdown("### 4. Daylight Hours")
    st.plotly_chart(_chart_daylight(daylight, key="seaana_pchart4"), use_container_width=True,
                    key="season_daylight_chart")
    longest_m = max(range(12), key=lambda m: daylight[m])
    shortest_m = min(range(12), key=lambda m: daylight[m])
    dl_range = daylight[longest_m] - daylight[shortest_m]
    dc1, dc2, dc3 = st.columns(3)
    dc1.markdown(_card("Longest Day", f"{daylight[longest_m]:.1f}h",
                       MONTH_FULL[longest_m], CLR_SUN), unsafe_allow_html=True)
    dc2.markdown(_card("Shortest Day", f"{daylight[shortest_m]:.1f}h",
                       MONTH_FULL[shortest_m], CLR_TEXT_SEC), unsafe_allow_html=True)
    dc3.markdown(_card("Day Length Variation", f"{dl_range:.1f}h",
                       "High" if dl_range > 6 else ("Moderate" if dl_range > 3 else "Low"),
                       CLR_SUN), unsafe_allow_html=True)
    st.markdown("---")

    # ======================================================================
    # 5. Wind Patterns
    # ======================================================================
    st.markdown("### 5. Wind Patterns")
    st.plotly_chart(_chart_wind(monthly, key="seaana_pchart5"), use_container_width=True,
                    key="season_wind_chart")
    calmest_m = min(range(12), key=lambda m: monthly[m]["avg_wind"])
    avg_wind_yr = sum(monthly[m]["avg_wind"] for m in range(12)) / 12
    wc1, wc2, wc3 = st.columns(3)
    wc1.markdown(_card("Windiest Month", MONTH_NAMES[windiest_m],
                       f"{monthly[windiest_m]['avg_wind']:.1f} km/h avg max", CLR_WIND),
                 unsafe_allow_html=True)
    wc2.markdown(_card("Calmest Month", MONTH_NAMES[calmest_m],
                       f"{monthly[calmest_m]['avg_wind']:.1f} km/h avg max", CLR_GREEN),
                 unsafe_allow_html=True)
    wc3.markdown(_card("Annual Avg Wind", f"{avg_wind_yr:.1f} km/h",
                       "Strong" if avg_wind_yr > 25 else
                       ("Moderate" if avg_wind_yr > 15 else "Light"), CLR_WIND),
                 unsafe_allow_html=True)
    st.markdown("---")

    # ======================================================================
    # 6. Best Visit Month
    # ======================================================================
    st.markdown("### 6. Best Visit Month Recommendation")
    if scores:
        best = scores[0]
        b1, b2 = st.columns([1, 1])
        with b1:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#065f46,#0f3460);'
                f'border:2px solid {CLR_GREEN};border-radius:12px;'
                f'padding:22px;text-align:center;">'
                f'<div style="color:{CLR_TEXT_SEC};font-size:0.85rem;'
                f'margin-bottom:4px;">BEST MONTH TO VISIT</div>'
                f'<div style="color:{CLR_GREEN};font-size:2.4rem;'
                f'font-weight:800;">{best["month_full"]}</div>'
                f'<div style="color:{CLR_TEXT};font-size:1.1rem;margin-top:6px;">'
                f'Overall Score: <b>{best["total"]:.0f}</b>/100</div>'
                f'<div style="margin-top:10px;color:{CLR_TEXT_SEC};font-size:0.82rem;">'
                f'Avg Temp {best["avg_temp"]:.1f} C &bull; '
                f'Precip {best["precip"]:.0f} mm &bull; '
                f'Daylight {best["daylight"]:.1f}h &bull; '
                f'Wind {best["wind"]:.1f} km/h</div></div>',
                unsafe_allow_html=True)
        with b2:
            st.plotly_chart(_chart_radar(best, key="seaana_pchart6"), use_container_width=True,
                            key="season_radar_chart")

        # Top-3 + worst
        st.markdown("#### Monthly Visit Scores")
        sc_cols = st.columns(4)
        display = scores[:3] + [scores[-1]] if len(scores) > 3 else scores
        labels = ["Best", "2nd Best", "3rd Best", "Worst"]
        clrs = [CLR_GREEN, "#22d3ee", CLR_SUN, CLR_WARM]
        for idx, (sc, lbl, clr) in enumerate(zip(display, labels, clrs)):
            with sc_cols[idx]:
                st.markdown(_card(lbl, sc["month"], f"Score: {sc['total']:.0f}/100", clr),
                            unsafe_allow_html=True)

        with st.expander("Full Monthly Rankings", expanded=False):
            hdr = "| Rank | Month | Score | Temp | Rain | Daylight | Wind |\n"
            hdr += "|------|-------|-------|------|------|----------|------|\n"
            rows = ""
            for i, sc in enumerate(scores):
                rows += (f"| {i+1} | {sc['month_full']} | **{sc['total']:.0f}** | "
                         f"{sc['temp_score']:.0f} | {sc['rain_score']:.0f} | "
                         f"{sc['day_score']:.0f} | {sc['wind_score']:.0f} |\n")
            st.markdown(hdr + rows)
    st.markdown("---")

    # ======================================================================
    # Koppen Classification Detail
    # ======================================================================
    st.markdown("### Climate Classification")
    k_code = koppen.split(" - ")[0] if " - " in koppen else koppen
    k_desc = koppen.split(" - ")[1] if " - " in koppen else ""
    st.markdown(
        f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
        f'border-radius:10px;padding:16px 20px;">'
        f'<div style="color:{CLR_ACCENT};font-size:1.5rem;font-weight:700;">{k_code}</div>'
        f'<div style="color:{CLR_TEXT};font-size:1rem;margin-top:4px;">{k_desc}</div>'
        f'<div style="color:{CLR_TEXT_SEC};font-size:0.82rem;margin-top:8px;">'
        f'Estimated from 2023 monthly temperature and precipitation patterns '
        f'at ({res["lat"]:.4f}, {res["lon"]:.4f}).</div></div>',
        unsafe_allow_html=True)
    st.markdown("---")

    # ======================================================================
    # Full Summary Table
    # ======================================================================
    st.markdown("### Seasonal Summary Table")
    st.markdown(_summary_table(monthly, daylight), unsafe_allow_html=True)
    st.caption("Data source: Open-Meteo Archive API (2023). "
               "Daylight hours computed via solar declination formula. "
               "Koppen classification is an estimate based on single-year data.")
