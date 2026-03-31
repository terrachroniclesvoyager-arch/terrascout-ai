"""
Solar Energy & Sunlight Analysis module for TerraScout AI.
Comprehensive solar potential assessment including irradiance measurement,
sunshine duration tracking, cloud cover impact, daylight calculations,
solar panel sizing estimates, and terrain shading risk analysis.
Uses Open-Meteo and Open Topo Data APIs (free, no API key required).
"""

import logging
import math
import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
MONTH_15TH_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_SOLAR, CLR_ORANGE, CLR_RED = "#facc15", "#f59e0b", "#ef4444"
CLR_BLUE, CLR_CYAN, CLR_GREEN = "#3b82f6", "#06b6d4", "#22c55e"

SOLAR_CLASSES = [
    (1800, "EXCELLENT", CLR_GREEN,  "Outstanding solar resource - ideal for solar farms"),
    (1400, "GOOD",      CLR_SOLAR,  "Strong solar resource - excellent for rooftop PV"),
    (1000, "MODERATE",  CLR_ORANGE, "Adequate solar resource - viable with good design"),
    (600,  "POOR",      CLR_RED,    "Limited solar resource - supplementary use only"),
    (0,    "MINIMAL",   CLR_TEXT_SEC, "Very low solar resource - not recommended"),
]

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
OPEN_TOPO = "https://api.opentopodata.org/v1/srtm30m"
PANEL_EFF, PERF_RATIO, SYS_KW = 0.20, 0.75, 1.0
_LAYOUT = dict(template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _classify(val: float) -> tuple:
    for thresh, label, color, desc in SOLAR_CLASSES:
        if val >= thresh:
            return label, color, desc
    return "MINIMAL", CLR_TEXT_SEC, "Very low solar resource"


def _avg(vals: list) -> float:
    c = [v for v in vals if v is not None]
    return round(sum(c) / len(c), 2) if c else 0.0


def _total(vals: list) -> float:
    return round(sum(v for v in vals if v is not None), 2)


# ---------------------------------------------------------------------------
# Data fetching (cached, timeout, try/except)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_sunshine(lat: float, lon: float) -> dict:
    """Fetch 30-day sunshine duration and shortwave radiation."""
    try:
        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon,
            "daily": "sunshine_duration,shortwave_radiation_sum",
            "past_days": 30, "timezone": "auto",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Sunshine fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_cloud(lat: float, lon: float) -> dict:
    """Fetch 7-day hourly cloud cover and direct radiation."""
    try:
        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon,
            "hourly": "cloud_cover,direct_radiation",
            "past_days": 7, "timezone": "auto",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Cloud fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_terrain(lat: float, lon: float) -> dict:
    """Fetch 7x7 elevation grid for shading analysis."""
    pts = []
    step = 0.005
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            pts.append(f"{lat + dy * step:.6f},{lon + dx * step:.6f}")
    try:
        r = requests.get(OPEN_TOPO, params={"locations": "|".join(pts)}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Terrain fetch failed: %s", e)
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Solar calculations
# ---------------------------------------------------------------------------
def _daylight_hours(lat: float) -> list:
    """Monthly daylight hours via solar declination formula."""
    lr = math.radians(lat)
    out = []
    for doy in MONTH_15TH_DOY:
        decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + doy) / 365)))
        ch = -math.tan(lr) * math.tan(decl)
        if ch <= -1:
            out.append(24.0)
        elif ch >= 1:
            out.append(0.0)
        else:
            out.append(round(2 * math.acos(ch) * 12 / math.pi, 2))
    return out


def _sunrise_sunset(lat: float, doy: int) -> tuple:
    """Sunrise/sunset decimal hours for a given day-of-year."""
    lr = math.radians(lat)
    decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + doy) / 365)))
    ch = -math.tan(lr) * math.tan(decl)
    if ch <= -1:
        return 0.0, 24.0
    if ch >= 1:
        return 12.0, 12.0
    ha = math.acos(ch) * 12 / math.pi
    return round(12 - ha, 2), round(12 + ha, 2)


def _monthly_irradiance(avg_daily: float, lat: float) -> list:
    """Weight average irradiance by monthly daylight proportion."""
    dl = _daylight_hours(lat)
    avg_dl = sum(dl) / 12
    return [round(avg_daily * (d / avg_dl if avg_dl > 0 else 1), 2) for d in dl]


def _shading_risk(topo: dict, lat: float) -> dict:
    """Assess terrain shading from 7x7 elevation grid."""
    results = topo.get("results", [])
    if not results or len(results) < 49:
        return {"risk": "UNKNOWN", "color": CLR_TEXT_SEC, "score": 50,
                "detail": "Insufficient data", "centre_elev": 0, "max_rise_m": 0,
                "shading_pct": 0, "direction": "south"}
    elevs = [(r.get("elevation") or 0) for r in results]
    centre = elevs[24]
    # NH: sun is south, check southern terrain (rows 0-2); SH: check north (rows 4-6)
    if lat >= 0:
        idx, direction = list(range(0, 21)), "south"
    else:
        idx, direction = list(range(28, 49)), "north"
    higher = sum(1 for i in idx if elevs[i] - centre > 5)
    max_rise = max((elevs[i] - centre for i in idx), default=0)
    max_rise = max(max_rise, 0)
    pct = higher / len(idx) * 100
    if pct > 60 or max_rise > 200:
        risk, color, score = "HIGH", CLR_RED, 25
    elif pct > 30 or max_rise > 100:
        risk, color, score = "MODERATE", CLR_ORANGE, 55
    elif pct > 10 or max_rise > 30:
        risk, color, score = "LOW", CLR_SOLAR, 80
    else:
        risk, color, score = "MINIMAL", CLR_GREEN, 95
    return {"risk": risk, "color": color, "score": score, "shading_pct": round(pct, 1),
            "max_rise_m": round(max_rise, 1), "direction": direction,
            "centre_elev": round(centre, 1),
            "detail": f"{higher}/{len(idx)} grid points to {direction} are higher (max +{max_rise:.0f}m)"}


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------
def _chart_sunshine(dates, hrs):
    colors = [CLR_SOLAR if h >= 8 else CLR_ORANGE if h >= 4 else CLR_RED for h in hrs]
    fig = go.Figure(go.Bar(x=dates, y=hrs, marker_color=colors, opacity=0.85,
                           text=[f"{h:.1f}" for h in hrs], textposition="outside",
                           textfont=dict(size=7)))
    fig.update_layout(title="Daily Sunshine Hours (Past 30 Days)",
                      xaxis_title="Date", yaxis_title="Hours", height=370,
                      margin=dict(l=50, r=30, t=55, b=50), **_LAYOUT)
    return fig


def _chart_irradiance(dates, kwh):
    fig = go.Figure(go.Scatter(x=dates, y=kwh, mode="lines+markers",
                               line=dict(color=CLR_ORANGE, width=2),
                               marker=dict(size=4, color=CLR_SOLAR),
                               fill="tozeroy", fillcolor="rgba(250,204,21,0.15)"))
    a = _avg(kwh)
    fig.add_hline(y=a, line_dash="dash", line_color=CLR_CYAN,
                  annotation_text=f"Avg: {a:.2f}")
    fig.update_layout(title="Daily Solar Irradiance (kWh/m\u00b2/day)",
                      xaxis_title="Date", yaxis_title="kWh/m\u00b2/day", height=370,
                      margin=dict(l=50, r=30, t=55, b=50), **_LAYOUT)
    return fig


def _chart_cloud(times, cloud, rad):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=cloud, mode="lines", name="Cloud %",
                             line=dict(color=CLR_BLUE, width=1),
                             fill="tozeroy", fillcolor="rgba(59,130,246,0.2)"))
    fig.add_trace(go.Scatter(x=times, y=rad, mode="lines", name="Direct Rad (W/m\u00b2)",
                             line=dict(color=CLR_SOLAR, width=1),
                             fill="tozeroy", fillcolor="rgba(250,204,21,0.1)", yaxis="y2"))
    fig.update_layout(title="Cloud Cover vs Direct Radiation (7 Days)", xaxis_title="Time",
                      yaxis=dict(title="Cloud %", range=[0, 100]),
                      yaxis2=dict(title="W/m\u00b2", overlaying="y", side="right"),
                      height=390, margin=dict(l=50, r=60, t=55, b=50),
                      legend=dict(orientation="h", y=1.02, xanchor="center", x=0.5),
                      **_LAYOUT)
    return fig


def _chart_daylight(dl):
    fig = go.Figure(go.Scatter(x=MONTH_NAMES, y=dl, mode="lines+markers",
                               line=dict(color=CLR_SOLAR, width=3),
                               marker=dict(size=7, color=CLR_ORANGE),
                               fill="tozeroy", fillcolor="rgba(250,204,21,0.15)",
                               text=[f"{h:.1f}h" for h in dl], textposition="top center"))
    a = sum(dl) / 12
    fig.add_hline(y=a, line_dash="dash", line_color=CLR_CYAN,
                  annotation_text=f"Avg: {a:.1f}h")
    fig.update_layout(title="Monthly Daylight Hours", xaxis_title="Month",
                      yaxis_title="Hours", yaxis_range=[0, 26], height=370,
                      margin=dict(l=50, r=30, t=55, b=40), **_LAYOUT)
    return fig


def _chart_output(mo):
    colors = [CLR_GREEN if v >= 120 else CLR_SOLAR if v >= 80
              else CLR_ORANGE if v >= 40 else CLR_RED for v in mo]
    fig = go.Figure(go.Bar(x=MONTH_NAMES, y=mo, marker_color=colors, opacity=0.85,
                           text=[f"{v:.0f}" for v in mo], textposition="outside"))
    fig.update_layout(title="Monthly Panel Output (1 kW System)",
                      xaxis_title="Month", yaxis_title="kWh", height=370,
                      margin=dict(l=50, r=30, t=55, b=40), **_LAYOUT)
    return fig


def _chart_gauge(val):
    label, color, _ = _classify(val)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        title=dict(text=f"Solar Potential ({label})", font=dict(size=16, color=CLR_TEXT)),
        number=dict(suffix=" kWh/kW/yr", font=dict(size=24, color=color)),
        gauge=dict(axis=dict(range=[0, 2400]), bar=dict(color=color),
                   bgcolor=CLR_SURFACE, borderwidth=2, bordercolor=CLR_BORDER,
                   steps=[{"range": [0, 600], "color": "rgba(139,151,176,0.2)"},
                          {"range": [600, 1000], "color": "rgba(239,68,68,0.2)"},
                          {"range": [1000, 1400], "color": "rgba(245,158,11,0.2)"},
                          {"range": [1400, 1800], "color": "rgba(250,204,21,0.2)"},
                          {"range": [1800, 2400], "color": "rgba(34,197,94,0.2)"}])))
    fig.update_layout(height=280, margin=dict(l=40, r=40, t=50, b=20), **_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------
def _sec_sunshine(data: dict) -> float:
    st.markdown("### 1. Sunshine Duration")
    daily = data.get("daily", {})
    dates, raw = daily.get("time", []), daily.get("sunshine_duration", [])
    if not dates or not raw:
        st.warning("No sunshine data available."); return 0.0
    hrs = [round((s or 0) / 3600, 2) for s in raw]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", f"{_total(hrs):.1f} hrs")
    c2.metric("Daily Avg", f"{_avg(hrs):.1f} hrs")
    c3.metric("Peak Day", f"{max(hrs):.1f} hrs")
    c4.metric("Sunny Days (6h+)", str(sum(1 for h in hrs if h >= 6)))
    st.plotly_chart(_chart_sunshine(dates, hrs, key="solana_pchart1"), use_container_width=True,
                    key="solar_sunshine_chart")
    return _avg(hrs)


def _sec_irradiance(data: dict) -> float:
    st.markdown("### 2. Solar Irradiance")
    daily = data.get("daily", {})
    dates, raw = daily.get("time", []), daily.get("shortwave_radiation_sum", [])
    if not dates or not raw:
        st.warning("No irradiance data available."); return 0.0
    kwh = [round((r or 0) * 0.2778, 2) for r in raw]  # MJ -> kWh
    pos = [v for v in kwh if v > 0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Irradiance", f"{_avg(kwh):.2f} kWh/m\u00b2/day")
    c2.metric("Peak", f"{max(kwh):.2f} kWh/m\u00b2")
    c3.metric("Min (non-zero)", f"{min(pos):.2f} kWh/m\u00b2" if pos else "0.00")
    st.plotly_chart(_chart_irradiance(dates, kwh, key="solana_pchart2"), use_container_width=True,
                    key="solar_irradiance_chart")
    return _avg(kwh)


def _sec_cloud(data: dict):
    st.markdown("### 3. Cloud Cover Impact")
    h = data.get("hourly", {})
    times, cloud, rad = h.get("time", []), h.get("cloud_cover", []), h.get("direct_radiation", [])
    if not times or not cloud:
        st.warning("No cloud data available."); return
    valid = [c for c in cloud if c is not None]
    total = len(valid)
    clear = sum(1 for c in valid if c < 20)
    overcast = sum(1 for c in valid if c > 80)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Cloud Cover", f"{_avg(cloud):.1f}%")
    c2.metric("Clear (<20%)", str(clear), delta=f"{clear/total*100:.0f}%" if total else "0%")
    c3.metric("Overcast (>80%)", str(overcast),
              delta=f"-{overcast/total*100:.0f}%" if total else "0%", delta_color="inverse")
    avg_rad = _avg([r for r in rad if r is not None and r > 0])
    c4.metric("Avg Direct Rad", f"{avg_rad:.0f} W/m\u00b2")
    ac = _avg(cloud)
    if ac < 30: st.success("Low cloud cover - excellent direct solar exposure.")
    elif ac < 55: st.info("Moderate cloud cover - good solar conditions with diffuse radiation.")
    elif ac < 75: st.warning("High cloud cover - reduced direct radiation.")
    else: st.error("Very high cloud cover - limited direct solar resource.")
    st.plotly_chart(_chart_cloud(times, cloud, rad, key="solana_pchart3"), use_container_width=True,
                    key="solar_cloud_chart")


def _sec_daylight(lat: float) -> list:
    st.markdown("### 4. Daylight Hours Calculation")
    dl = _daylight_hours(lat)
    doy = datetime.now().timetuple().tm_yday
    sr, ss = _sunrise_sunset(lat, doy)
    cur_dl = ss - sr
    sum_doy = 172 if lat >= 0 else 355
    win_doy = 355 if lat >= 0 else 172
    sr_s, ss_s = _sunrise_sunset(lat, sum_doy)
    sr_w, ss_w = _sunrise_sunset(lat, win_doy)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today's Daylight", f"{cur_dl:.1f} hrs")
    c2.metric("Sunrise / Sunset",
              f"{int(sr)}:{int((sr%1)*60):02d} / {int(ss)}:{int((ss%1)*60):02d}")
    c3.metric("Summer Solstice", f"{ss_s - sr_s:.1f} hrs")
    c4.metric("Seasonal Variation", f"{(ss_s - sr_s) - (ss_w - sr_w):.1f} hrs")
    st.plotly_chart(_chart_daylight(dl, key="solana_pchart4"), use_container_width=True, key="solar_daylight_chart")
    with st.expander("Monthly Sunrise & Sunset Times", expanded=False):
        rows = []
        for i, d in enumerate(MONTH_15TH_DOY):
            r, s = _sunrise_sunset(lat, d)
            rows.append({"Month": MONTH_FULL[i],
                         "Sunrise": f"{int(r):02d}:{int((r%1)*60):02d}",
                         "Sunset": f"{int(s):02d}:{int((s%1)*60):02d}",
                         "Daylight": f"{dl[i]:.1f}h"})
        st.dataframe(rows, use_container_width=True, hide_index=True)
    return dl


def _sec_panel(avg_irr: float, lat: float) -> float:
    st.markdown("### 5. Solar Panel Sizing Estimate")
    st.caption(f"{SYS_KW:.0f} kW system | Efficiency {PANEL_EFF*100:.0f}% | PR {PERF_RATIO*100:.0f}%")
    annual = avg_irr * 365 * PANEL_EFF * PERF_RATIO * SYS_KW
    mi = _monthly_irradiance(avg_irr, lat)
    mo = [round(mi[m] * DAYS_IN_MONTH[m] * PANEL_EFF * PERF_RATIO * SYS_KW, 1) for m in range(12)]
    label, color, desc = _classify(annual)
    st.plotly_chart(_chart_gauge(annual, key="solana_pchart5"), use_container_width=True, key="solar_gauge_chart")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Output", f"{annual:.0f} kWh")
    c2.metric("Classification", label)
    c3.metric("Best Month", MONTH_NAMES[mo.index(max(mo))])
    c4.metric("Worst Month", MONTH_NAMES[mo.index(min(mo))])
    st.markdown(f"**Assessment:** {desc}")
    with st.expander("Energy & Financial Estimates", expanded=True):
        price = st.slider("Electricity price (USD/kWh)", 0.05, 0.50, 0.12, 0.01,
                          key="solar_elec_price")
        cost_kw = st.slider("System cost (USD/kW)", 500, 3000, 1200, 100,
                            key="solar_system_cost")
        savings = annual * price
        cost = cost_kw * SYS_KW
        payback = cost / savings if savings > 0 else 999
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Annual Savings", f"${savings:.0f}")
        f2.metric("System Cost", f"${cost:,.0f}")
        f3.metric("Payback", f"{payback:.1f} yrs")
        f4.metric("25-Year Value", f"${savings * 25 - cost:,.0f}")
    st.plotly_chart(_chart_output(mo, key="solana_pchart6"), use_container_width=True, key="solar_panel_chart")
    with st.expander("Monthly Output Detail", expanded=False):
        detail = [{"Month": MONTH_FULL[m],
                   "Irradiance (kWh/m\u00b2/day)": f"{mi[m]:.2f}",
                   "Days": DAYS_IN_MONTH[m],
                   "Output (kWh)": f"{mo[m]:.1f}",
                   "Daily Avg": f"{mo[m]/DAYS_IN_MONTH[m]:.2f}"} for m in range(12)]
        st.dataframe(detail, use_container_width=True, hide_index=True)
    return annual


def _sec_shading(lat: float, lon: float):
    st.markdown("### 6. Terrain Shading Risk")
    topo = _fetch_terrain(lat, lon)
    if "error" in topo:
        st.warning(f"Could not fetch terrain: {topo['error']}"); return
    sh = _shading_risk(topo, lat)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Shading Risk", sh["risk"])
    c2.metric("Openness Score", f"{sh['score']}/100")
    c3.metric("Site Elevation", f"{sh['centre_elev']:.0f} m")
    c4.metric("Max Rise", f"{sh['max_rise_m']:.0f} m")
    r = sh["risk"]
    msg = f"{sh['detail']}"
    if r == "MINIMAL": st.success(msg)
    elif r == "LOW": st.info(msg)
    elif r == "MODERATE": st.warning(msg)
    else: st.error(msg)
    # Elevation heatmap
    res = topo.get("results", [])
    if res and len(res) >= 49:
        grid = [[(res[row * 7 + col].get("elevation") or 0)
                 for col in range(7)] for row in range(7)]
        fig = go.Figure(go.Heatmap(
            z=grid, x=[str(c - 3) for c in range(7)], y=[str(r - 3) for r in range(7)],
            colorscale="Earth",
            text=[[f"{v:.0f}m" for v in row] for row in grid], texttemplate="%{text}",
            hovertemplate="(%{x},%{y}): %{z:.0f}m<extra></extra>",
            colorbar=dict(title="m")))
        fig.add_trace(go.Scatter(
            x=["0"], y=["0"], mode="markers+text",
            marker=dict(size=14, color=CLR_SOLAR, symbol="star"),
            text=["Site"], textposition="top center",
            textfont=dict(color=CLR_TEXT, size=11), showlegend=False))
        fig.update_layout(title="Elevation Grid (~3.5 km radius)",
                          xaxis_title="E-W offset", yaxis_title="S-N offset",
                          height=400, margin=dict(l=50, r=30, t=55, b=50), **_LAYOUT)
        st.plotly_chart(fig, use_container_width=True, key="solar_terrain_heatmap")
    # Folium sun-path map
    _sun_path_map(lat, lon, sh)


def _sun_path_map(lat: float, lon: float, sh: dict):
    """Folium map with sun path overlay markers."""
    try:
        import folium
        import streamlit.components.v1 as components
    except ImportError:
        st.info("Folium not available."); return
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
    folium.Marker([lat, lon],
                  popup=f"Site: {lat:.4f}, {lon:.4f}<br>Elev: {sh.get('centre_elev','?')}m",
                  icon=folium.Icon(color="orange", icon="sun-o", prefix="fa")).add_to(m)
    # Key sun positions
    for label, bearing, dist in [
        ("Sunrise (Summer)", 60, 0.008), ("Sunrise (Winter)", 120, 0.008),
        ("Solar Noon", 180 if lat >= 0 else 0, 0.006),
        ("Sunset (Summer)", 300, 0.008), ("Sunset (Winter)", 240, 0.008),
    ]:
        br = math.radians(bearing)
        folium.CircleMarker(
            [lat + dist * math.cos(br),
             lon + dist * math.sin(br) / math.cos(math.radians(lat))],
            radius=7, color=CLR_SOLAR, fill=True, fill_color=CLR_ORANGE,
            fill_opacity=0.7, popup=label).add_to(m)
    # Sun arc polyline
    arc = []
    for a in range(60, 301, 10):
        br = math.radians(a)
        arc.append([lat + 0.007 * math.cos(br),
                    lon + 0.007 * math.sin(br) / math.cos(math.radians(lat))])
    folium.PolyLine(arc, color=CLR_SOLAR, weight=2, opacity=0.6,
                    dash_array="5,5", tooltip="Sun arc").add_to(m)
    # Shading direction indicator
    d = sh.get("direction", "south")
    ilat = lat - 0.012 if d == "south" else lat + 0.012
    folium.CircleMarker([ilat, lon], radius=10,
                        color=sh.get("color", CLR_TEXT_SEC), fill=True,
                        fill_color=sh.get("color", CLR_TEXT_SEC), fill_opacity=0.5,
                        popup=f"Check: {d} | Risk: {sh['risk']}").add_to(m)
    components.html(m._repr_html_(), height=440)


def _render_summary(sun_h, irr, annual, dl):
    st.markdown("---")
    st.markdown("### Solar Energy Summary")
    label, color, desc = _classify(annual)
    avg_dl = sum(dl) / 12 if dl else 12
    st.markdown(f"""
    <div style="background:{CLR_CARD};border:1px solid {color};border-radius:12px;padding:24px;margin:8px 0">
        <div style="text-align:center">
            <span style="font-size:48px">&#9728;&#65039;</span>
            <h2 style="color:{color};margin:8px 0">{label} Solar Potential</h2>
            <p style="color:{CLR_TEXT};font-size:24px;margin:4px 0">{annual:.0f} kWh/kW/year</p>
            <p style="color:{CLR_TEXT_SEC}">{desc}</p>
        </div>
        <div style="display:flex;justify-content:space-around;margin-top:20px">
            <div style="text-align:center">
                <p style="color:{CLR_SOLAR};font-size:22px;margin:0">{sun_h:.1f}h</p>
                <p style="color:{CLR_TEXT_SEC};font-size:13px">Avg Daily Sunshine</p>
            </div>
            <div style="text-align:center">
                <p style="color:{CLR_ORANGE};font-size:22px;margin:0">{irr:.2f}</p>
                <p style="color:{CLR_TEXT_SEC};font-size:13px">Avg Irradiance (kWh/m&sup2;/day)</p>
            </div>
            <div style="text-align:center">
                <p style="color:{CLR_CYAN};font-size:22px;margin:0">{avg_dl:.1f}h</p>
                <p style="color:{CLR_TEXT_SEC};font-size:13px">Avg Daylight Hours</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================
def render_solar_analysis_tab():
    """Render the Solar Energy & Sunlight Analysis tab."""
    st.markdown("## ☀️ Solar Energy & Sunlight Analysis")
    st.caption("Solar irradiance, panel sizing, shading & energy potential")

    col_a, col_b = st.columns(2)
    with col_a:
        lat = st.number_input("Latitude", value=45.0, min_value=-90.0,
                              max_value=90.0, step=0.01, key="solar_latitude")
    with col_b:
        lon = st.number_input("Longitude", value=9.0, min_value=-180.0,
                              max_value=180.0, step=0.01, key="solar_longitude")

    hemi = "Northern" if lat >= 0 else "Southern"
    st.caption(f"Location: {lat:.4f}, {lon:.4f} | {hemi} Hemisphere")

    if st.button("Analyze Solar Potential", key="solar_analyze_btn",
                 type="primary", use_container_width=True):
        with st.spinner("Fetching solar data..."):
            sun_data = _fetch_sunshine(lat, lon)
            cld_data = _fetch_cloud(lat, lon)
        if "error" in sun_data and "error" in cld_data:
            st.error("Failed to fetch solar data. Check coordinates and retry.")
            return
        st.markdown("---")
        avg_sun = _sec_sunshine(sun_data)
        st.markdown("---")
        avg_irr = _sec_irradiance(sun_data)
        st.markdown("---")
        _sec_cloud(cld_data)
        st.markdown("---")
        dl = _sec_daylight(lat)
        st.markdown("---")
        annual = _sec_panel(avg_irr, lat)
        st.markdown("---")
        with st.spinner("Analyzing terrain shading..."):
            _sec_shading(lat, lon)
        _render_summary(avg_sun, avg_irr, annual, dl)
