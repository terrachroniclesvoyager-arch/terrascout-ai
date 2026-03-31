"""
Wind Pattern & Energy Analysis module for TerraScout AI.
Comprehensive wind analysis with wind rose, energy potential,
terrain wind effects, and multi-domain impact assessment.
Uses Open-Meteo and Open Topo Data APIs (free, no API key).
"""

import math
import logging
import streamlit as st
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# -- Theme constants ---------------------------------------------------------
CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_SEC = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_PRI, CLR_SAFE, CLR_WARN = "#06b6d4", "#22c55e", "#f59e0b"
CLR_DANGER, CLR_CRIT = "#ef4444", "#991b1b"

# -- Beaufort scale (min m/s, max m/s, label, force) -------------------------
BEAUFORT = [
    (0, 0.3, "Calm", 0), (0.3, 1.6, "Light Air", 1),
    (1.6, 3.4, "Light Breeze", 2), (3.4, 5.5, "Gentle Breeze", 3),
    (5.5, 8.0, "Moderate Breeze", 4), (8.0, 10.8, "Fresh Breeze", 5),
    (10.8, 13.9, "Strong Breeze", 6), (13.9, 17.2, "Near Gale", 7),
    (17.2, 20.8, "Gale", 8), (20.8, 24.5, "Strong Gale", 9),
    (24.5, 28.5, "Storm", 10), (28.5, 32.7, "Violent Storm", 11),
    (32.7, 999, "Hurricane Force", 12),
]

COMPASS_PTS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
               "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

# Wind power classes: (class, lo, hi, label, color)
WPC = [
    (1, 0, 100, "Poor", "#94a3b8"), (2, 100, 150, "Marginal", "#60a5fa"),
    (3, 150, 200, "Fair", "#34d399"), (4, 200, 250, "Good", "#a3e635"),
    (5, 250, 300, "Excellent", "#facc15"), (6, 300, 400, "Outstanding", "#fb923c"),
    (7, 400, 9999, "Superb", "#f87171"),
]

AIR_DENSITY = 1.225  # kg/m^3


# -- Helpers -----------------------------------------------------------------

def _beaufort(spd_ms):
    for lo, hi, desc, f in BEAUFORT:
        if lo <= spd_ms < hi:
            return lo, hi, desc, f
    return BEAUFORT[-1]


def _deg2compass(deg):
    return COMPASS_PTS[int((deg + 11.25) / 22.5) % 16]


def _wind_arrow(deg):
    return ["\u2193", "\u2199", "\u2190", "\u2196",
            "\u2191", "\u2197", "\u2192", "\u2198"][int((deg + 22.5) / 45) % 8]


def _pd(v): return 0.5 * AIR_DENSITY * v ** 3


def _wclass(pd_val):
    for c, lo, hi, lbl, col in WPC:
        if lo <= pd_val < hi:
            return c, lbl, col
    return 7, "Superb", "#f87171"


def _wchill(t, v_kmh):
    if t > 10 or v_kmh < 4.8:
        return t
    return round(13.12 + 0.6215 * t - 11.37 * v_kmh ** 0.16
                 + 0.3965 * t * v_kmh ** 0.16, 1)


def _card(label, value, sub="", color=CLR_PRI):
    s = f'<div style="font-size:.78rem;color:{CLR_SEC};margin-top:2px">{sub}</div>' if sub else ""
    return (f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
            f'border-radius:10px;padding:14px;text-align:center;border-left:4px solid {color}">'
            f'<div style="font-size:.82rem;color:{CLR_SEC};margin-bottom:3px">{label}</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:{color}">{value}</div>{s}</div>')


def _header(title, icon=""):
    st.markdown(f'<div style="background:{CLR_SURFACE};border:1px solid {CLR_BORDER};'
                f'border-radius:10px;padding:12px 18px;margin:22px 0 10px 0;'
                f'font-size:1.12rem;font-weight:600;color:{CLR_TEXT}">{icon} {title}</div>',
                unsafe_allow_html=True)


# -- API functions -----------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_current(lat, lon):
    try:
        r = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
            f"temperature_2m,apparent_temperature&timezone=auto", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Current wind fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_hourly(lat, lon):
    try:
        r = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&hourly=wind_speed_10m,wind_direction_10m"
            f"&timezone=auto&forecast_hours=168", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Hourly wind fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_daily(lat, lon):
    try:
        r = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=wind_speed_10m_max,wind_gusts_10m_max,"
            f"wind_direction_10m_dominant&past_days=30&timezone=auto", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Daily wind fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_elev_grid(lat, lon, radius_km=2.0):
    pts = []
    half = 3
    step = radius_km / (half - 1)
    for r in range(half):
        for c in range(half):
            dl = (r - 1) * step / 111.0
            dn = (c - 1) * step / (111.0 * max(math.cos(math.radians(lat)), 0.01))
            pts.append((lat + dl, lon + dn))
    pts.append((lat, lon))
    loc_str = "|".join(f"{p[0]:.6f},{p[1]:.6f}" for p in pts)
    try:
        r = requests.get(f"https://api.opentopodata.org/v1/srtm90m?locations={loc_str}",
                         timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Elevation fetch failed: %s", e)
        return {"error": str(e)}


# -- Section 1: Current Wind ------------------------------------------------

def _render_current(lat, lon):
    _header("Current Wind Conditions", "\U0001F4A8")
    data = _fetch_current(lat, lon)
    if "error" in data:
        st.warning(f"Could not fetch current wind data: {data['error']}")
        return {}
    cur = data.get("current", {})
    spd, dirn, gust = cur.get("wind_speed_10m", 0), cur.get("wind_direction_10m", 0), cur.get("wind_gusts_10m", 0)
    temp = cur.get("temperature_2m")
    comp, arrow = _deg2compass(dirn), _wind_arrow(dirn)
    spd_ms, gust_ms = spd / 3.6, gust / 3.6
    _, _, bf_desc, bf_f = _beaufort(spd_ms)
    unit = st.selectbox("Display units", ["km/h", "m/s", "knots", "mph"], key="wind_unit_select")
    conv = {"km/h": (spd, gust), "m/s": (round(spd_ms, 1), round(gust_ms, 1)),
            "knots": (round(spd_ms * 1.944, 1), round(gust_ms * 1.944, 1)),
            "mph": (round(spd_ms * 2.237, 1), round(gust_ms * 2.237, 1))}
    ds, dg = conv[unit]
    # Direction arrow
    st.markdown(f'<div style="text-align:center;margin:10px 0">'
                f'<span style="font-size:4rem;color:{CLR_PRI}">{arrow}</span>'
                f'<div style="font-size:1rem;color:{CLR_SEC}">From {comp} ({dirn}\u00b0)</div></div>',
                unsafe_allow_html=True)
    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_card("Wind Speed", f"{ds} {unit}"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card("Gusts", f"{dg} {unit}", color=CLR_WARN), unsafe_allow_html=True)
    with c3:
        st.markdown(_card("Beaufort", f"F{bf_f}", bf_desc, "#a78bfa"), unsafe_allow_html=True)
    with c4:
        wc = _wchill(temp, spd) if temp is not None else None
        v = f"{wc}\u00b0C" if wc is not None else "N/A"
        s = f"Actual: {temp}\u00b0C" if temp is not None else ""
        st.markdown(_card("Wind Chill", v, s, "#38bdf8"), unsafe_allow_html=True)
    # Beaufort gauge
    bf_colors = ["#e0f2fe", "#bae6fd", "#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7",
                 "#0369a1", "#075985", "#0c4a6e", "#fbbf24", "#f97316", "#ef4444", "#991b1b"]
    segs = "".join(
        f'<div style="flex:1;background:{bf_colors[i]};height:28px;'
        f'opacity:{"1" if i == bf_f else "0.5"};'
        f'border:{"3px solid white" if i == bf_f else "1px solid rgba(255,255,255,.2)"};'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:.7rem;font-weight:700;color:#1a1a2e">{i}</div>' for i in range(13))
    st.markdown(f'<div style="display:flex;border-radius:8px;overflow:hidden;margin:8px 0">{segs}</div>'
                f'<div style="text-align:center;font-size:.75rem;color:{CLR_SEC}">Beaufort Scale</div>',
                unsafe_allow_html=True)
    return {"speed_ms": spd_ms, "direction": dirn, "gusts_ms": gust_ms, "temp": temp, "compass": comp}


# -- Section 2: Wind Rose ---------------------------------------------------

def _render_rose(lat, lon):
    _header("Wind Rose (7-Day Hourly Data)", "\U0001F9ED")
    data = _fetch_hourly(lat, lon)
    if "error" in data:
        st.warning(f"Could not fetch hourly wind data: {data['error']}")
        return
    h = data.get("hourly", {})
    speeds, dirs = h.get("wind_speed_10m", []), h.get("wind_direction_10m", [])
    if not speeds or not dirs:
        st.info("No hourly wind data available.")
        return
    sbins = [(0, 5, "0-5 km/h", "#a5b4fc"), (5, 15, "5-15 km/h", "#60a5fa"),
             (15, 25, "15-25 km/h", "#3b82f6"), (25, 40, "25-40 km/h", "#f59e0b"),
             (40, 999, "40+ km/h", "#ef4444")]
    dc = {cp: {s[2]: 0 for s in sbins} for cp in COMPASS_PTS}
    total = 0
    for s, d in zip(speeds, dirs):
        if s is None or d is None:
            continue
        total += 1
        cp = _deg2compass(d)
        for lo, hi, lbl, _ in sbins:
            if lo <= s < hi:
                dc[cp][lbl] += 1
                break
    if total == 0:
        st.info("No valid wind observations.")
        return
    fig = go.Figure()
    for lo, hi, lbl, col in sbins:
        fig.add_trace(go.Barpolar(
            r=[round(dc[cp][lbl] / total * 100, 1) for cp in COMPASS_PTS],
            theta=COMPASS_PTS, name=lbl, marker_color=col,
            marker_line_color="#1a1a2e", marker_line_width=1, opacity=0.88))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, ticksuffix="%",
                                   gridcolor="rgba(255,255,255,.1)"),
                   angularaxis=dict(direction="clockwise",
                                    gridcolor="rgba(255,255,255,.15)"),
                   bgcolor=CLR_SURFACE),
        paper_bgcolor=CLR_BG, font=dict(color=CLR_TEXT, size=12),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center",
                    bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=40, b=60), height=480)
    st.plotly_chart(fig, use_container_width=True, key="wind_rose_chart")
    tbd = {cp: sum(dc[cp].values()) for cp in COMPASS_PTS}
    dom = max(tbd, key=tbd.get)
    st.markdown(f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
                f'border-radius:8px;padding:12px;text-align:center">'
                f'Prevailing wind: <b style="color:{CLR_PRI}">{dom}</b> '
                f'({round(tbd[dom] / total * 100, 1)}% of {total} hours)</div>',
                unsafe_allow_html=True)


# -- Section 3: 30-Day History ----------------------------------------------

def _render_history(lat, lon):
    _header("30-Day Wind History", "\U0001F4C8")
    data = _fetch_daily(lat, lon)
    if "error" in data:
        st.warning(f"Could not fetch wind history: {data['error']}")
        return 0.0
    d = data.get("daily", {})
    dates, mx, gx = d.get("time", []), d.get("wind_speed_10m_max", []), d.get("wind_gusts_10m_max", [])
    dd = d.get("wind_direction_10m_dominant", [])
    if not dates or not mx:
        st.info("No daily wind data available.")
        return 0.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=mx, mode="lines+markers", name="Max Wind Speed",
                             line=dict(color=CLR_PRI, width=2), marker=dict(size=5)))
    if gx:
        fig.add_trace(go.Scatter(x=dates, y=gx, mode="lines+markers", name="Max Gusts",
                                 line=dict(color=CLR_WARN, width=2, dash="dot"), marker=dict(size=4)))
    fig.update_layout(xaxis_title="Date", yaxis_title="Speed (km/h)",
                      paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
                      font=dict(color=CLR_TEXT, size=12),
                      legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                      margin=dict(l=50, r=30, t=30, b=60), height=350,
                      xaxis=dict(gridcolor="rgba(255,255,255,.07)"),
                      yaxis=dict(gridcolor="rgba(255,255,255,.07)"))
    st.plotly_chart(fig, use_container_width=True, key="wind_history_chart")
    vs = [s for s in mx if s is not None]
    vg = [g for g in (gx or []) if g is not None]
    avg = sum(vs) / len(vs) if vs else 0
    pk, pg = (max(vs) if vs else 0), (max(vg) if vg else 0)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(_card("Avg Max Speed", f"{avg:.1f} km/h"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card("Peak Speed", f"{pk:.1f} km/h", color=CLR_WARN), unsafe_allow_html=True)
    with c3:
        st.markdown(_card("Peak Gust", f"{pg:.1f} km/h", color=CLR_DANGER), unsafe_allow_html=True)
    if dd and any(x is not None for x in dd):
        with st.expander("Daily dominant wind directions", expanded=False):
            rows = [{"Date": t, "Dir (\u00b0)": v, "Compass": _deg2compass(v)}
                    for t, v in zip(dates, dd) if v is not None]
            if rows:
                st.dataframe(rows, use_container_width=True, key="wind_dir_table")
    return avg


# -- Section 4: Energy Potential --------------------------------------------

def _render_energy(avg_kmh):
    _header("Wind Energy Potential", "\u26A1")
    avg_ms = avg_kmh / 3.6
    pdv = _pd(avg_ms)
    cn, cl, cc = _wclass(pdv)
    st.markdown(f'<div style="text-align:center;margin:10px 0">'
                f'<div style="font-size:1rem;color:{CLR_SEC}">Power Density</div>'
                f'<div style="font-size:2.5rem;font-weight:700;color:{cc}">{pdv:.0f} W/m\u00b2</div>'
                f'<div style="font-size:1.1rem;color:{cc}">Class {cn} \u2014 {cl}</div></div>',
                unsafe_allow_html=True)
    # Class gauge
    segs = "".join(
        f'<div style="flex:1;background:{c[4]};height:32px;'
        f'opacity:{"1" if c[0] == cn else ".45"};'
        f'border:{"3px solid white" if c[0] == cn else "1px solid rgba(255,255,255,.15)"};'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:.72rem;font-weight:700;color:#1a1a2e">{c[0]}</div>' for c in WPC)
    st.markdown(f'<div style="display:flex;border-radius:8px;overflow:hidden;margin:8px 0">{segs}</div>'
                f'<div style="display:flex;justify-content:space-between;font-size:.7rem;'
                f'color:{CLR_SEC};padding:0 4px"><span>Poor</span><span>Outstanding</span>'
                f'<span>Superb</span></div>', unsafe_allow_html=True)
    # Turbine estimates
    st.markdown("##### Reference Turbine Estimates")
    turbs = [("Small (10 kW)", 10, 7.0), ("Medium (100 kW)", 100, 12.0), ("Large (2 MW)", 2000, 25.0)]
    cols = st.columns(3)
    for i, (nm, kw, rd) in enumerate(turbs):
        cf = min(0.45, max(0.05, (avg_ms / 12.0) ** 2 * 0.35))
        mwh = kw * cf * 8760 / 1000
        with cols[i]:
            st.markdown(_card(nm, f"{mwh:.0f} MWh/yr", f"CF ~{cf * 100:.0f}%", cc),
                        unsafe_allow_html=True)
    if cn >= 4:
        st.success("This site shows **good to excellent** wind energy potential. "
                   "Utility-scale development may be viable.")
    elif cn >= 3:
        st.info("This site has **fair** wind energy potential. "
                "Small-scale or community wind may be feasible.")
    else:
        st.warning("This site has **marginal to poor** wind energy potential. "
                   "Solar or other renewables may be preferable.")


# -- Section 5: Terrain Effect ----------------------------------------------

def _render_terrain(lat, lon):
    _header("Terrain Wind Exposure", "\u26F0\uFE0F")
    data = _fetch_elev_grid(lat, lon)
    if "error" in data:
        st.warning(f"Could not fetch elevation data: {data['error']}")
        return
    results = data.get("results", [])
    elevs = [r.get("elevation") for r in results if r.get("elevation") is not None]
    if not elevs:
        st.info("Elevation values unavailable for this location.")
        return
    center = elevs[-1]
    surr = elevs[:-1] if len(elevs) > 1 else elevs
    avg_s = sum(surr) / len(surr) if surr else center
    mn_s, mx_s = (min(surr), max(surr)) if surr else (center, center)
    diff, relief = center - avg_s, mx_s - mn_s
    # Classify
    if diff > 50:
        exp, ec = "Ridge / Hilltop", CLR_DANGER
        we = "Highly exposed \u2014 wind speeds amplified (factor 1.5\u20132.0x)"
    elif diff > 20:
        exp, ec = "Elevated / Exposed", CLR_WARN
        we = "Moderately exposed \u2014 wind speeds amplified (factor 1.2\u20131.5x)"
    elif diff < -30:
        exp, ec = "Valley / Sheltered", CLR_SAFE
        we = "Sheltered \u2014 wind speeds reduced (factor 0.5\u20130.7x), possible channeling"
    elif diff < -10:
        exp, ec = "Low-lying / Partial Shelter", "#60a5fa"
        we = "Partially sheltered \u2014 wind speeds reduced (factor 0.7\u20130.9x)"
    else:
        exp, ec = "Open Plain / Flat", CLR_SEC
        we = "Neutral terrain \u2014 standard wind conditions (factor ~1.0x)"
    st.markdown(f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:10px;'
                f'padding:18px;text-align:center;border-top:4px solid {ec}">'
                f'<div style="font-size:1.4rem;font-weight:700;color:{ec}">{exp}</div>'
                f'<div style="font-size:.9rem;color:{CLR_TEXT};margin-top:6px">{we}</div></div>',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_card("Site Elevation", f"{center:.0f} m"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card("Avg Surrounding", f"{avg_s:.0f} m", color="#8b97b0"), unsafe_allow_html=True)
    with c3:
        sign = "+" if diff >= 0 else ""
        st.markdown(_card("Difference", f"{sign}{diff:.0f} m",
                          color=CLR_WARN if abs(diff) > 20 else CLR_SEC), unsafe_allow_html=True)
    with c4:
        st.markdown(_card("Local Relief", f"{relief:.0f} m", color="#a78bfa"), unsafe_allow_html=True)
    if len(surr) >= 4:
        with st.expander("Elevation grid profile", expanded=False):
            labels = [f"Pt {i + 1}" for i in range(len(surr))] + ["Center"]
            vals = surr + [center]
            fig = go.Figure(go.Bar(
                x=labels, y=vals,
                marker_color=[CLR_SEC] * len(surr) + [CLR_PRI],
                text=[f"{v:.0f}m" for v in vals], textposition="outside"))
            fig.update_layout(paper_bgcolor=CLR_BG, plot_bgcolor=CLR_SURFACE,
                              font=dict(color=CLR_TEXT, size=11), yaxis_title="Elevation (m)",
                              margin=dict(l=50, r=20, t=20, b=40), height=280,
                              yaxis=dict(gridcolor="rgba(255,255,255,.07)"))
            st.plotly_chart(fig, use_container_width=True, key="wind_terrain_profile")


# -- Section 6: Impact Assessment -------------------------------------------

def _render_impacts(cur, avg_kmh):
    _header("Wind Impact Assessment", "\U0001F6E1\uFE0F")
    spd_ms = cur.get("speed_ms", avg_kmh / 3.6)
    spd_kmh = spd_ms * 3.6
    gust_ms = cur.get("gusts_ms", spd_ms * 1.4)
    gust_kmh = gust_ms * 3.6
    temp = cur.get("temp", 15) or 15

    # Construction
    if gust_kmh > 90:
        con = ("Critical", CLR_CRIT, "All crane ops must cease. Scaffolding at extreme risk.")
    elif gust_kmh > 60:
        con = ("High", CLR_DANGER, "Suspend crane and roofing work. Secure materials.")
    elif gust_kmh > 40:
        con = ("Moderate", CLR_WARN, "Limit crane operations. Secure lightweight materials.")
    elif gust_kmh > 25:
        con = ("Low", CLR_SAFE, "Normal operations with standard precautions.")
    else:
        con = ("Minimal", CLR_SEC, "No wind-related construction constraints.")

    # Agriculture
    if spd_kmh > 60:
        agr = ("Severe", CLR_DANGER, "Crop damage likely. Livestock shelter essential.")
    elif spd_kmh > 40:
        agr = ("High", CLR_WARN, "Evapotranspiration increase. Lodging risk. Spray drift extreme.")
    elif spd_kmh > 20:
        agr = ("Moderate", "#60a5fa", "Spray drift likely. Good drying. Adequate pollination.")
    elif spd_kmh > 8:
        agr = ("Beneficial", CLR_SAFE, "Ideal for crop drying, pollination, pest dispersal.")
    else:
        agr = ("Low", CLR_SEC, "Calm. Possible frost risk in clear weather.")

    # Comfort
    wc = _wchill(temp, spd_kmh)
    if wc < -25:
        cmf = ("Dangerous", CLR_CRIT, f"Wind chill {wc}\u00b0C. Frostbite in minutes.")
    elif wc < -10:
        cmf = ("Very Cold", CLR_DANGER, f"Wind chill {wc}\u00b0C. Frostbite risk.")
    elif wc < 0:
        cmf = ("Cold", CLR_WARN, f"Wind chill {wc}\u00b0C. Dress warmly.")
    elif spd_kmh > 40:
        cmf = ("Uncomfortable", CLR_WARN, f"Wind chill {wc}\u00b0C. Strong wind.")
    elif spd_kmh > 20:
        cmf = ("Breezy", "#60a5fa", f"Wind chill {wc}\u00b0C. Wear a windbreaker.")
    else:
        cmf = ("Comfortable", CLR_SAFE, f"Wind chill {wc}\u00b0C. Pleasant conditions.")

    # Aviation
    xkt = round(spd_ms * 1.944, 1)
    gkt = round(gust_ms * 1.944, 1)
    if xkt > 35 or gkt > 45:
        avi = ("Severe", CLR_CRIT, f"Crosswind {xkt} kt (gusts {gkt} kt). Limits exceeded.")
    elif xkt > 25 or gkt > 35:
        avi = ("Significant", CLR_DANGER, f"Crosswind {xkt} kt. Light aircraft grounded.")
    elif xkt > 15:
        avi = ("Moderate", CLR_WARN, f"Crosswind {xkt} kt. Student pilots restricted.")
    elif xkt > 8:
        avi = ("Minor", "#60a5fa", f"Crosswind {xkt} kt. Standard technique required.")
    else:
        avi = ("Minimal", CLR_SAFE, f"Crosswind {xkt} kt. Favorable for all ops.")

    items = [("\U0001F3D7\uFE0F Construction", con), ("\U0001F33E Agriculture", agr),
             ("\U0001F321\uFE0F Comfort", cmf), ("\u2708\uFE0F Aviation", avi)]
    for i in range(0, 4, 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < 4:
                title, (lvl, clr, desc) = items[i + j]
                with col:
                    st.markdown(
                        f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
                        f'border-radius:10px;padding:16px;min-height:130px;border-left:4px solid {clr}">'
                        f'<div style="font-size:.95rem;font-weight:600;color:{CLR_TEXT}">{title}</div>'
                        f'<div style="font-size:1.2rem;font-weight:700;color:{clr};margin:6px 0">{lvl}</div>'
                        f'<div style="font-size:.82rem;color:{CLR_SEC}">{desc}</div></div>',
                        unsafe_allow_html=True)
    # Overall
    rsk = {"Minimal": 1, "Low": 2, "Minor": 2, "Beneficial": 1, "Comfortable": 1,
           "Breezy": 2, "Moderate": 3, "Uncomfortable": 3, "High": 4, "Significant": 4,
           "Severe": 5, "Very Cold": 4, "Cold": 3, "Critical": 5, "Dangerous": 5}
    ar = sum(rsk.get(it[1][0], 3) for it in items) / 4
    if ar <= 1.5:
        ov, oc = "Low", CLR_SAFE
    elif ar <= 2.5:
        ov, oc = "Moderate", "#60a5fa"
    elif ar <= 3.5:
        ov, oc = "Elevated", CLR_WARN
    elif ar <= 4.5:
        ov, oc = "High", CLR_DANGER
    else:
        ov, oc = "Critical", CLR_CRIT
    st.markdown(f'<div style="background:{CLR_SURFACE};border:1px solid {oc};'
                f'border-radius:10px;padding:14px;text-align:center;margin-top:12px">'
                f'<span style="font-size:.9rem;color:{CLR_SEC}">Overall Wind Impact: </span>'
                f'<span style="font-size:1.15rem;font-weight:700;color:{oc}">{ov}</span></div>',
                unsafe_allow_html=True)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def render_wind_analysis_tab():
    """Main entry point for Wind Pattern & Energy Analysis tab."""
    st.markdown("## \U0001F4A8 Wind Pattern & Energy Analysis")
    st.caption("Wind rose, energy potential, terrain effects & impact assessment")

    col_a, col_b = st.columns(2)
    with col_a:
        lat = st.number_input("Latitude", value=45.0, min_value=-90.0,
                              max_value=90.0, step=0.01, key="wind_lat_input")
    with col_b:
        lon = st.number_input("Longitude", value=9.0, min_value=-180.0,
                              max_value=180.0, step=0.01, key="wind_lon_input")

    if st.button("Analyze Wind Patterns", key="wind_analyze_btn",
                 type="primary", use_container_width=True):
        st.session_state["wind_run_analysis"] = True
        st.session_state["wind_lat"] = lat
        st.session_state["wind_lon"] = lon

    if not st.session_state.get("wind_run_analysis"):
        st.info("Enter coordinates and click **Analyze Wind Patterns** to begin.")
        return

    a_lat = st.session_state.get("wind_lat", lat)
    a_lon = st.session_state.get("wind_lon", lon)

    current_data = _render_current(a_lat, a_lon)
    st.divider()
    _render_rose(a_lat, a_lon)
    st.divider()
    avg_max = _render_history(a_lat, a_lon)
    st.divider()
    _render_energy(avg_max if avg_max > 0 else 15.0)
    st.divider()
    _render_terrain(a_lat, a_lon)
    st.divider()
    _render_impacts(current_data, avg_max if avg_max > 0 else 15.0)

    st.markdown(f'<div style="text-align:center;margin-top:24px;padding:12px;'
                f'color:{CLR_SEC};font-size:.75rem">'
                f'Data: Open-Meteo (weather) | Open Topo Data (elevation) | '
                f'All APIs free, no key required</div>', unsafe_allow_html=True)
