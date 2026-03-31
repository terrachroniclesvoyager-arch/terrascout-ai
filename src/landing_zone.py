"""
Landing Zone & Drop Zone Assessment module for TerraScout AI.
Evaluates helicopter LZ and parachute DZ suitability across 7 dimensions:
surface flatness, obstacle clearance, surface type, wind conditions,
approach path, visibility, and accessibility.
Uses free APIs: Open Topo Data, Overpass, Open-Meteo (no API keys required).
"""

import logging, math
from html import escape
import streamlit as st
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# ── Theme ────────────────────────────────────────────────────────────────────
CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_DIM = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_ACCENT, CLR_GO, CLR_COND, CLR_NOGO = "#f59e0b", "#22c55e", "#f59e0b", "#ef4444"

DIMS = {
    "Surface Flatness":   {"c": "#3b82f6", "w": 0.18},
    "Obstacle Clearance": {"c": "#ef4444", "w": 0.16},
    "Surface Type":       {"c": "#a0785a", "w": 0.14},
    "Wind Conditions":    {"c": "#06b6d4", "w": 0.14},
    "Approach Path":      {"c": "#8b5cf6", "w": 0.14},
    "Visibility":         {"c": "#f59e0b", "w": 0.12},
    "Accessibility":      {"c": "#22c55e", "w": 0.12},
}
DIM_ORDER = list(DIMS.keys())

# ── Helpers ──────────────────────────────────────────────────────────────────
def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, float(v)))

def _vc(s):
    return CLR_GO if s >= 8 else CLR_COND if s >= 5 else CLR_NOGO

def _vl(s):
    return "GO" if s >= 8 else "CONDITIONAL" if s >= 5 else "NO-GO"

def _hav(la1, lo1, la2, lo2):
    R = 6371000.0; dl, dn = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dn/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def _mean(v):
    c = [x for x in (v or []) if x is not None]
    return sum(c)/len(c) if c else 0.0

def _near_m(lat, lon, els):
    best = None
    for e in (els if isinstance(els, list) else []):
        la = e.get("lat") or (e.get("center") or {}).get("lat")
        lo = e.get("lon") or (e.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            d = _hav(lat, lon, la, lo)
            if best is None or d < best: best = d
    return best

def _lz_class(r):
    d = r * 2
    if d < 30:  return "CONFINED", "<30 m"
    if d < 80:  return "LIMITED", "30-80 m"
    if d < 150: return "STANDARD", "80-150 m"
    return "LARGE", ">150 m"

def _wc(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[int((deg+11.25)/22.5) % 16]

def _card(name, sc, det, color):
    c = _vc(sc)
    return (f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px 12px;'
            f'border:1px solid {color}44;margin-bottom:8px;min-height:130px;">'
            f'<div style="font-size:12px;color:{color};font-weight:600;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">{escape(name)}</div>'
            f'<div style="font-size:28px;font-weight:800;color:{c};">{sc}</div>'
            f'<div style="font-size:11px;color:{CLR_DIM};margin-top:4px;'
            f'line-height:1.35;">{escape(det[:110])}</div></div>')

# ── Data Fetching (all cached, timeout=10, try/except) ───────────────────────
@st.cache_data(ttl=900)
def _fetch_elev(lat, lon, steps=7, sp=0.0008):
    try:
        pts = [f"{lat+(i-steps//2)*sp:.6f},{lon+(j-steps//2)*sp:.6f}"
               for i in range(steps) for j in range(steps)]
        r = requests.get("https://api.opentopodata.org/v1/srtm30m",
                         params={"locations": "|".join(pts)}, timeout=10)
        r.raise_for_status()
        return {"elevs": [float(x.get("elevation") or 0) for x in r.json().get("results",[])],
                "steps": steps, "sp": sp}
    except Exception as e:
        logger.warning("Elevation error: %s", e)
        return {"elevs": [], "steps": steps, "sp": sp}

@st.cache_data(ttl=900)
def _fetch_obs(lat, lon, radius=500):
    q = f"""[out:json][timeout:25];(
      way["building"](around:{radius},{lat},{lon});
      node["natural"="tree"](around:{radius},{lat},{lon});
      way["natural"="tree_row"](around:{radius},{lat},{lon});
      way["power"="line"](around:{radius},{lat},{lon});
      node["power"~"tower|pole"](around:{radius},{lat},{lon});
      node["man_made"~"mast|tower|chimney"](around:{radius},{lat},{lon});
      node["highway"="street_lamp"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Obstacles error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_srf(lat, lon, radius=300):
    q = f"""[out:json][timeout:25];(
      way["landuse"](around:{radius},{lat},{lon});
      way["natural"](around:{radius},{lat},{lon});
      way["surface"](around:{radius},{lat},{lon});
      way["aeroway"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Surface error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_wind(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "wind_speed_10m,wind_gusts_10m,wind_direction_10m",
            "timezone": "auto"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Wind error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_vis(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "cloud_cover,precipitation,visibility",
            "timezone": "auto"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Visibility error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_appr(lat, lon, radius=1500):
    q = f"""[out:json][timeout:25];(
      node["man_made"~"tower|mast|chimney"](around:{radius},{lat},{lon});
      node["power"="tower"](around:{radius},{lat},{lon});
      way["power"="line"](around:{radius},{lat},{lon});
      way["natural"~"cliff|ridge"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Approach error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_acc(lat, lon, radius=3000):
    q = f"""[out:json][timeout:25];(
      way["highway"~"primary|secondary|tertiary|trunk|motorway"](around:{radius},{lat},{lon});
      node["amenity"="fuel"](around:{radius},{lat},{lon});
      node["amenity"~"hospital|clinic"](around:{radius},{lat},{lon});
      node["amenity"~"fire_station|police"](around:{radius},{lat},{lon});
      way["highway"~"track|unclassified|service"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Access error: %s", e); return {"elements": []}

# ── Scoring Engine ───────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def _score(lat, lon):
    ed = _fetch_elev(lat, lon); obs = _fetch_obs(lat, lon)
    srf = _fetch_srf(lat, lon); wnd = _fetch_wind(lat, lon)
    vsd = _fetch_vis(lat, lon); apr = _fetch_appr(lat, lon)
    acc = _fetch_acc(lat, lon)
    S, D = {}, {}

    # 1 ─ Surface Flatness
    elevs, steps = ed.get("elevs",[]), ed.get("steps",7)
    sp_m = ed.get("sp",0.0008)*111320.0
    slps = []
    if len(elevs) == steps*steps:
        for i in range(steps):
            for j in range(steps):
                ix = i*steps+j
                if j < steps-1:
                    slps.append(math.degrees(math.atan2(abs(elevs[ix]-elevs[ix+1]), sp_m)))
                if i < steps-1:
                    slps.append(math.degrees(math.atan2(abs(elevs[ix]-elevs[(i+1)*steps+j]), sp_m)))
    avg_s, max_s = _mean(slps), (max(slps) if slps else 0)
    ce = elevs[len(elevs)//2] if elevs else 0.0
    if not slps:                  fs, fd = 5.0, "Elevation data unavailable"
    elif avg_s < 1.5:             fs, fd = 9.5, f"Very flat (avg {avg_s:.1f}, max {max_s:.1f} deg)"
    elif avg_s < 3:               fs, fd = 8.0, f"Flat (avg {avg_s:.1f} deg)"
    elif avg_s < 5:               fs, fd = 6.0, f"Moderate slope ({avg_s:.1f} deg), marginal"
    elif avg_s < 8:               fs, fd = 4.0, f"Steep ({avg_s:.1f} deg), risky"
    elif avg_s < 12:              fs, fd = 2.5, f"Very steep ({avg_s:.1f} deg), heli-only"
    else:                         fs, fd = 1.0, f"Extreme slope ({avg_s:.1f} deg), unsuitable"
    S["Surface Flatness"], D["Surface Flatness"] = round(_clamp(fs),1), fd

    # 2 ─ Obstacle Clearance
    ol = [e for e in (obs.get("elements") or []) if isinstance(e, dict)]
    bld = [e for e in ol if e.get("tags",{}).get("building")]
    tre = [e for e in ol if e.get("tags",{}).get("natural")=="tree"]
    pwr = [e for e in ol if e.get("tags",{}).get("power")=="line"]
    twr = [e for e in ol if e.get("tags",{}).get("man_made") in ("tower","mast","chimney")
           or e.get("tags",{}).get("power") in ("tower","pole")]
    no = _near_m(lat, lon, ol)
    if not ol:
        oc, od, cr = 9.5, "No obstacles within 500 m", 500.0
    else:
        cr = max(no or 10, 10); oc = 9.0 - min(7.0, len(ol)*0.12)
        if no and no < 50:    oc -= 3.0
        elif no and no < 100: oc -= 1.5
        elif no and no < 200: oc -= 0.5
        if pwr: oc -= 2.0
        if twr: oc -= 1.0
        pp = []
        for lb, ls in [("buildings",bld),("trees",tre),("power lines",pwr),("towers",twr)]:
            if ls: pp.append(f"{len(ls)} {lb}")
        od = "; ".join(filter(None, [", ".join(pp), f"nearest {no:.0f}m" if no else ""]))
    S["Obstacle Clearance"], D["Obstacle Clearance"] = round(_clamp(oc),1), od

    # 3 ─ Surface Type
    sl = [e for e in (srf.get("elements") or []) if isinstance(e, dict)]
    good = {"grass","gravel","paved","asphalt","concrete","compacted","ground"}
    bad = {"mud","sand","swamp","marsh","wetland"}
    fg, fb = [], []
    aero = [e for e in sl if e.get("tags",{}).get("aeroway")]
    for e in sl:
        t = e.get("tags",{})
        sv, lu, na = t.get("surface",""), t.get("landuse",""), t.get("natural","")
        if sv in good or lu in ("grass","meadow","farmland"): fg.append(t)
        if sv in bad or lu in ("forest","wood","wetland","reservoir") or na in ("wetland","water"): fb.append(t)
    if aero:             ss, sd = 9.5, "Aeroway/helipad found; ideal"
    elif fg and not fb:  ss, sd = 8.5, "Good surface: grass/paved/compacted"
    elif fg and fb:      ss, sd = 5.5, "Mixed surface; hazards present"
    elif fb:             ss, sd = 2.5, "Poor surface: water/swamp/forest"
    elif not sl:         ss, sd = 6.0, "No surface data; verify on-site"
    else:                ss, sd = 6.5, f"Acceptable; {len(sl)} features"
    S["Surface Type"], D["Surface Type"] = round(_clamp(ss),1), sd

    # 4 ─ Wind Conditions
    wc = (wnd if isinstance(wnd,dict) else {}).get("current",{})
    ws_v = wc.get("wind_speed_10m",0) or 0; wg = wc.get("wind_gusts_10m",0) or 0
    wd_v = wc.get("wind_direction_10m",0) or 0; wcomp = _wc(wd_v)
    ew = max(ws_v, wg*0.7)
    if ew < 10:   wsc, wdt = 9.5, f"Calm ({ws_v:.0f} km/h {wcomp})"
    elif ew < 20: wsc, wdt = 8.0, f"Light ({ws_v:.0f}, gusts {wg:.0f} km/h {wcomp})"
    elif ew < 25: wsc, wdt = 6.5, f"Moderate ({ws_v:.0f}, gusts {wg:.0f} km/h); caution"
    elif ew < 35: wsc, wdt = 4.5, f"Strong ({ws_v:.0f}, gusts {wg:.0f} km/h); marginal"
    elif ew < 50: wsc, wdt = 2.5, f"High ({ws_v:.0f}, gusts {wg:.0f} km/h); unsafe"
    else:         wsc, wdt = 1.0, f"Extreme ({ws_v:.0f}, gusts {wg:.0f} km/h); NO-GO"
    if wg > ws_v*2: wsc = _clamp(wsc-1.0); wdt += "; gusty"
    S["Wind Conditions"], D["Wind Conditions"] = round(_clamp(wsc),1), wdt

    # 5 ─ Approach Path
    al = [e for e in (apr.get("elements") or []) if isinstance(e, dict)]
    quads = {"N":0,"E":0,"S":0,"W":0}
    for e in al:
        la = e.get("lat") or (e.get("center") or {}).get("lat")
        lo = e.get("lon") or (e.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            dy, dx = la-lat, lo-lon
            if abs(dy)>abs(dx): quads["N" if dy>0 else "S"] += 1
            else: quads["E" if dx>0 else "W"] += 1
    clr = [d for d,c in quads.items() if c==0]
    blk = [d for d,c in quads.items() if c>3]
    er = (max(elevs)-min(elevs)) if elevs else 0.0
    if len(clr)>=3 and er<30: ap, ad = 9.0, f"{len(clr)} clear dirs ({','.join(clr)}); flat"
    elif len(clr)>=2:         ap, ad = 7.5, f"{len(clr)} clear dirs ({','.join(clr)})"
    elif len(clr)==1:         ap, ad = 5.0, f"1 clear approach ({clr[0]})"
    else:                     ap, ad = 3.0, "All directions obstructed"
    if blk: ap = _clamp(ap-len(blk)*0.5); ad += f"; blocked {','.join(blk)}"
    if er>100: ap = _clamp(ap-2); ad += f"; relief {er:.0f}m"
    elif er>50: ap = _clamp(ap-1); ad += f"; relief {er:.0f}m"
    if len(al)>20: ap = _clamp(ap-1)
    S["Approach Path"], D["Approach Path"] = round(_clamp(ap),1), ad

    # 6 ─ Visibility
    vc = (vsd if isinstance(vsd,dict) else {}).get("current",{})
    cc = vc.get("cloud_cover",50) or 0; prec = vc.get("precipitation",0) or 0
    vis = vc.get("visibility",10000) or 10000
    if vis>=8000 and cc<30 and prec==0: vs_, vd_ = 9.5, f"Excellent: {vis/1000:.0f}km, {cc:.0f}%cloud"
    elif vis>=5000 and cc<60:           vs_, vd_ = 7.5, f"Good: {vis/1000:.0f}km, {cc:.0f}%cloud"
    elif vis>=3000:                     vs_, vd_ = 5.5, f"Marginal: {vis/1000:.1f}km"
    elif vis>=1500:                     vs_, vd_ = 3.5, f"Poor: {vis/1000:.1f}km"
    else:                               vs_, vd_ = 1.5, f"Very poor ({vis:.0f}m)"
    if prec>0: vs_ = _clamp(vs_-min(3,prec*0.5)); vd_ += f"; precip {prec:.1f}mm"
    if cc>80:  vs_ = _clamp(vs_-1); vd_ += "; overcast"
    S["Visibility"], D["Visibility"] = round(_clamp(vs_),1), vd_

    # 7 ─ Accessibility
    al2 = [e for e in (acc.get("elements") or []) if isinstance(e, dict)]
    rmaj = [e for e in al2 if e.get("tags",{}).get("highway") in
            ("primary","secondary","tertiary","trunk","motorway")]
    rmin = [e for e in al2 if e.get("tags",{}).get("highway") in ("track","unclassified","service")]
    fuel = [e for e in al2 if e.get("tags",{}).get("amenity")=="fuel"]
    med  = [e for e in al2 if e.get("tags",{}).get("amenity") in ("hospital","clinic")]
    emrg = [e for e in al2 if e.get("tags",{}).get("amenity") in ("fire_station","police")]
    nr = _near_m(lat, lon, rmaj+rmin)
    if not al2:
        acs, acd = 1.5, "No roads/services within 3 km"
    else:
        acs = 3.0
        if rmaj: acs += min(2.5, len(rmaj)*0.3)
        if rmin: acs += min(1.5, len(rmin)*0.15)
        if fuel: acs += 1.0
        if med:  acs += 1.5
        if emrg: acs += 0.5
        if nr and nr<200: acs += 1.0
        elif nr and nr<500: acs += 0.5
        pp = []
        if rmaj: pp.append(f"{len(rmaj)} major roads")
        if fuel: pp.append(f"{len(fuel)} fuel")
        if med:  pp.append(f"{len(med)} medical")
        acd = "; ".join(filter(None,[", ".join(pp), f"road {nr:.0f}m" if nr else ""])) or f"{len(al2)} features"
    S["Accessibility"], D["Accessibility"] = round(_clamp(acs),1), acd

    # Overall
    wsum = sum(S[d]*DIMS[d]["w"] for d in DIM_ORDER)
    wtot = sum(DIMS[d]["w"] for d in DIM_ORDER)
    ov = round(wsum/wtot if wtot else 5.0, 1)
    lzc, lzd = _lz_class(cr)
    recs = []
    for dim, msg in [("Surface Flatness","Terrain too steep; seek alternate site."),
                     ("Obstacle Clearance","Clear obstacles or widen LZ perimeter."),
                     ("Surface Type","Surface unsuitable; consider matting."),
                     ("Wind Conditions","Wind unsafe; delay ops or find shelter."),
                     ("Approach Path","Limited approaches; brief pilots."),
                     ("Visibility","Low vis; use markers/smoke/IR strobes."),
                     ("Accessibility","Limited ground access; pre-stage vehicles.")]:
        if S[dim] < 5: recs.append(msg)
    if not recs: recs.append("LZ meets requirements; standard procedures apply.")
    return {"scores": S, "details": D, "overall": ov, "verdict": _vl(ov),
            "lz_class": lzc, "lz_class_desc": lzd,
            "advantages": [f"{d}: {D[d]}" for d in DIM_ORDER if S[d]>=7.5],
            "challenges": [f"{d}: {D[d]}" for d in DIM_ORDER if S[d]<4],
            "recommendations": recs,
            "raw": {"wind_speed": ws_v, "wind_gusts": wg, "wind_dir": wd_v,
                    "wind_compass": wcomp, "cloud_cover": cc, "precipitation": prec,
                    "visibility_m": vis, "center_elevation": ce,
                    "avg_slope_deg": avg_s, "max_slope_deg": max_s,
                    "obstacle_elements": ol, "approach_elements": al,
                    "access_elements": al2, "elevations": elevs,
                    "grid_steps": steps, "clear_radius_est": cr,
                    "quadrants": quads, "nearest_obstacle_m": no, "nearest_road_m": nr}}

# ── Plotly Radar ─────────────────────────────────────────────────────────────
def _radar(scores):
    cats = DIM_ORDER + [DIM_ORDER[0]]
    vals = [scores[d] for d in DIM_ORDER] + [scores[DIM_ORDER[0]]]
    cols = [DIMS[d]["c"] for d in DIM_ORDER]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself", fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(size=7, color=cols+[cols[0]]),
        hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>"))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0,10], tickvals=[2,4,6,8,10],
                                   gridcolor="rgba(255,255,255,0.1)",
                                   tickfont=dict(size=10, color=CLR_DIM)),
                   angularaxis=dict(gridcolor="rgba(255,255,255,0.1)",
                                    tickfont=dict(size=11, color=CLR_TEXT))),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60,r=60,t=30,b=30), height=400)
    return fig

# ── Plotly Wind Compass ──────────────────────────────────────────────────────
def _wind_plot(spd, gst, d):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[0,spd], theta=[d,d], mode="lines+markers",
        line=dict(color="#06b6d4", width=4),
        marker=dict(size=[8,14], color=["#06b6d4","#06b6d4"], symbol=["circle","arrow-up"]),
        name=f"Wind {spd:.0f} km/h"))
    if gst > spd:
        fig.add_trace(go.Scatterpolar(
            r=[0,gst], theta=[d,d], mode="lines",
            line=dict(color="#ef4444", width=2, dash="dash"), name=f"Gusts {gst:.0f}"))
    mx = max(gst, spd, 20)*1.3
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0,mx],
                                   gridcolor="rgba(255,255,255,0.1)",
                                   tickfont=dict(size=9, color=CLR_DIM), ticksuffix=" km/h"),
                   angularaxis=dict(direction="clockwise", rotation=90,
                                    gridcolor="rgba(255,255,255,0.15)",
                                    tickfont=dict(size=10, color=CLR_TEXT))),
        showlegend=True, legend=dict(font=dict(color=CLR_TEXT, size=10), bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50,r=50,t=30,b=30), height=350)
    return fig

# ── Plotly Slope Heatmap ─────────────────────────────────────────────────────
def _slope_hm(elevs, steps):
    if len(elevs) != steps*steps: return None
    grid = []
    for i in range(steps):
        row = []
        for j in range(steps):
            ix = i*steps+j; nb = []
            if j < steps-1: nb.append(abs(elevs[ix]-elevs[ix+1]))
            if i < steps-1: nb.append(abs(elevs[ix]-elevs[(i+1)*steps+j]))
            row.append(_mean(nb) if nb else 0)
        grid.append(row)
    fig = go.Figure(data=go.Heatmap(
        z=grid, colorscale="YlOrRd",
        colorbar=dict(title=dict(text="Elev diff (m)", font=dict(color=CLR_TEXT)),
                      tickfont=dict(color=CLR_DIM)),
        hovertemplate="Row %{y}, Col %{x}<br>Diff: %{z:.1f}m<extra></extra>"))
    fig.update_layout(
        title=dict(text="Slope Heatmap", font=dict(color=CLR_TEXT, size=14)),
        xaxis=dict(title="Col", color=CLR_DIM), yaxis=dict(title="Row", color=CLR_DIM, autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50,r=30,t=50,b=50), height=350)
    return fig

# ── Folium Map ───────────────────────────────────────────────────────────────
def _fmap(lat, lon, raw):
    try:
        import folium
    except ImportError:
        return None
    m = folium.Map(location=[lat,lon], zoom_start=15, tiles="CartoDB dark_matter")
    cr = raw.get("clear_radius_est", 100)
    folium.Circle([lat,lon], radius=cr, color=CLR_GO, fill=True,
                  fill_color=CLR_GO, fill_opacity=0.12, weight=2,
                  popup=f"Clear zone: {cr:.0f}m radius").add_to(m)
    folium.Circle([lat,lon], radius=500, color=CLR_ACCENT, fill=False,
                  weight=1.5, dash_array="6 4", popup="500m check radius").add_to(m)
    folium.Marker([lat,lon],
        popup=folium.Popup(f"<b>LZ Center</b><br>{lat:.5f}, {lon:.5f}<br>"
              f"Elev: {raw.get('center_elevation',0):.0f}m<br>"
              f"Slope: {raw.get('avg_slope_deg',0):.1f} deg", max_width=230),
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)
    oc = {"building":("#ef4444","building"), "tree":("#22c55e","tree"),
          "line":("#f59e0b","bolt"), "tower":("#8b5cf6","broadcast-tower"),
          "pole":("#8b5cf6","broadcast-tower"), "mast":("#8b5cf6","broadcast-tower"),
          "chimney":("#6b7280","industry")}
    for el in raw.get("obstacle_elements",[]):
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            tg = el.get("tags",{})
            ot = tg.get("building") or tg.get("natural") or tg.get("power") or tg.get("man_made") or "obs"
            ci = oc.get(ot, ("#6b7280","exclamation-triangle"))
            folium.CircleMarker([la,lo], radius=4, color=ci[0], fill=True,
                fill_color=ci[0], fill_opacity=0.7,
                popup=f"Obstacle: {escape(str(tg.get('name',ot)))}").add_to(m)
    for el in raw.get("access_elements",[]):
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            am = el.get("tags",{}).get("amenity","")
            if am in ("hospital","clinic"):
                folium.Marker([la,lo], popup=f"Medical: {escape(el.get('tags',{}).get('name',am))}",
                    icon=folium.Icon(color="white", icon="plus-square", prefix="fa", icon_color="red")).add_to(m)
            elif am == "fuel":
                folium.Marker([la,lo], popup=f"Fuel: {escape(el.get('tags',{}).get('name','station'))}",
                    icon=folium.Icon(color="orange", icon="gas-pump", prefix="fa")).add_to(m)
    wdir = raw.get("wind_dir",0); wspd = raw.get("wind_speed",0); wcmp = raw.get("wind_compass","N")
    olat = 0.003*math.cos(math.radians(wdir)); olon = 0.003*math.sin(math.radians(wdir))
    folium.Marker([lat+olat, lon+olon], popup=f"Wind: {wspd:.0f} km/h {wcmp}",
        icon=folium.DivIcon(html=f'<div style="font-size:11px;color:#06b6d4;font-weight:bold;'
             f'text-shadow:1px 1px 2px black;white-space:nowrap;">Wind {wspd:.0f} km/h {wcmp}</div>')).add_to(m)
    return m

# ── Main Render ──────────────────────────────────────────────────────────────
def render_landing_zone_tab():
    """Single entry point for Landing Zone & Drop Zone Assessment."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});'
        f'padding:24px 28px;border-radius:12px;border:1px solid {CLR_BORDER};margin-bottom:20px;">'
        f'<h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">Landing Zone &amp; Drop Zone Assessment</h2>'
        f'<p style="margin:6px 0 0;color:{CLR_DIM};font-size:14px;">'
        f'Helicopter LZ &amp; parachute DZ suitability analysis across 7 operational dimensions.</p></div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", min_value=-90.0, max_value=90.0, key="lz_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", min_value=-180.0, max_value=180.0, key="lz_lon")

    if not st.button("Assess Landing Zone", type="primary", key="lz_btn", use_container_width=True):
        st.info("Enter coordinates and click **Assess Landing Zone** to evaluate the area.")
        return

    with st.spinner("Assessing landing zone across 7 dimensions..."):
        res = _score(lat, lon)

    sc, det, ov = res["scores"], res["details"], res["overall"]
    verdict, lzc, lzd, raw = res["verdict"], res["lz_class"], res["lz_class_desc"], res["raw"]
    vc = _vc(ov)

    # Verdict banner
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{vc}22,{CLR_BG});padding:24px 28px;'
        f'border-radius:12px;border:2px solid {vc}88;margin:10px 0 18px;text-align:center;">'
        f'<span style="font-size:13px;color:{CLR_DIM};text-transform:uppercase;letter-spacing:2px;">'
        f'Landing Zone Assessment</span>'
        f'<h1 style="margin:8px 0 4px;color:{vc};font-size:52px;font-weight:800;">{ov}/10</h1>'
        f'<div style="display:inline-block;padding:6px 28px;border-radius:20px;'
        f'background:{vc}33;border:1px solid {vc}66;">'
        f'<span style="font-size:22px;font-weight:700;color:{vc};letter-spacing:3px;">'
        f'{escape(verdict)}</span></div>'
        f'<div style="margin-top:10px;"><span style="display:inline-block;padding:4px 16px;'
        f'border-radius:12px;background:{CLR_CARD};border:1px solid {CLR_BORDER};'
        f'font-size:13px;color:{CLR_ACCENT};font-weight:600;">'
        f'LZ Class: {escape(lzc)} ({escape(lzd)})</span></div>'
        f'<p style="margin:8px 0 0;color:{CLR_DIM};font-size:13px;">'
        f'Location: {lat:.4f}, {lon:.4f} &middot; Elev: {raw.get("center_elevation",0):.0f}m</p></div>',
        unsafe_allow_html=True)

    # Dimension cards
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin-bottom:12px;'>Dimension Scores</h3>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    for i, d in enumerate(DIM_ORDER):
        (ca if i%2==0 else cb).markdown(_card(d, sc[d], det[d], DIMS[d]["c"]), unsafe_allow_html=True)

    # Radar
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Performance Radar</h3>", unsafe_allow_html=True)
    st.plotly_chart(_radar(sc, key="lanzon_pchart1"), use_container_width=True, key="lz_radar")

    # Wind & Slope side-by-side
    w1, w2 = st.columns(2)
    with w1:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Wind Indicator</h4>", unsafe_allow_html=True)
        st.plotly_chart(_wind_plot(raw.get("wind_speed",0, key="lanzon_pchart2"), raw.get("wind_gusts",0),
                                   raw.get("wind_dir",0)), use_container_width=True, key="lz_wind_fig")
    with w2:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Slope Heatmap</h4>", unsafe_allow_html=True)
        sf = _slope_hm(raw.get("elevations",[]), raw.get("grid_steps",7))
        if sf: st.plotly_chart(sf, use_container_width=True, key="lz_slope_fig")
        else:  st.caption("Elevation data insufficient for slope heatmap.")

    # Folium map
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>LZ Obstacle Map</h3>", unsafe_allow_html=True)
    fm = _fmap(lat, lon, raw)
    if fm:
        try:
            from streamlit_folium import st_folium
            st_folium(fm, width=None, height=500, key="lz_folium_map")
        except ImportError:
            import streamlit.components.v1 as components
            components.html(fm._repr_html_(), height=520)
    else:
        st.warning("Folium not installed; map unavailable.")

    # Key metrics
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Key Metrics</h3>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Slope", f"{raw.get('avg_slope_deg',0):.1f} deg",
              delta="FLAT" if raw.get('avg_slope_deg',99)<3 else "STEEP",
              delta_color="normal" if raw.get('avg_slope_deg',99)<3 else "inverse")
    m2.metric("Wind Speed", f"{raw.get('wind_speed',0):.0f} km/h",
              delta=f"Gusts {raw.get('wind_gusts',0):.0f}",
              delta_color="normal" if raw.get('wind_gusts',99)<25 else "inverse")
    m3.metric("Visibility", f"{raw.get('visibility_m',0)/1000:.1f} km",
              delta=f"Clouds {raw.get('cloud_cover',0):.0f}%",
              delta_color="normal" if raw.get('cloud_cover',99)<50 else "inverse")
    m4.metric("Clear Zone", f"{raw.get('clear_radius_est',0):.0f} m", delta=lzc, delta_color="normal")

    # Approach quadrants
    st.markdown(f"<h4 style='color:{CLR_TEXT};margin:16px 0 8px;'>Approach Quadrant Analysis</h4>",
                unsafe_allow_html=True)
    quads = raw.get("quadrants",{})
    qa, qb, qc, qd = st.columns(4)
    for col, dr in zip([qa,qb,qc,qd], ["N","E","S","W"]):
        oc = quads.get(dr,0)
        st_ = "CLEAR" if oc==0 else "PARTIAL" if oc<=3 else "BLOCKED"
        co = CLR_GO if oc==0 else CLR_COND if oc<=3 else CLR_NOGO
        col.markdown(
            f'<div style="background:{CLR_CARD};border-radius:8px;padding:10px;text-align:center;'
            f'border:1px solid {co}55;">'
            f'<div style="font-size:18px;font-weight:700;color:{CLR_TEXT};">{dr}</div>'
            f'<div style="font-size:12px;color:{co};font-weight:600;">{st_}</div>'
            f'<div style="font-size:10px;color:{CLR_DIM};">{oc} obstacles</div></div>',
            unsafe_allow_html=True)

    # Advantages & Challenges
    ac, cc_ = st.columns(2)
    with ac:
        st.markdown(f"<h4 style='color:{CLR_GO};'>Advantages</h4>", unsafe_allow_html=True)
        for a in (res["advantages"] or [st.caption("No strong advantages.") or ""][:0]):
            st.markdown(f"- {a}")
        if not res["advantages"]: st.caption("No strong advantages identified.")
    with cc_:
        st.markdown(f"<h4 style='color:{CLR_NOGO};'>Challenges</h4>", unsafe_allow_html=True)
        for c in (res["challenges"] or []):
            st.markdown(f"- {c}")
        if not res["challenges"]: st.caption("No critical challenges identified.")

    # Recommendations
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Recommendations</h3>", unsafe_allow_html=True)
    for rec in res["recommendations"]:
        st.markdown(f'<div style="background:{CLR_CARD};border-radius:8px;padding:10px 14px;'
                    f'border-left:3px solid {CLR_ACCENT};margin-bottom:6px;'
                    f'font-size:13px;color:{CLR_TEXT};">{escape(rec)}</div>', unsafe_allow_html=True)

    # DZ notes
    st.markdown(f"<h4 style='color:{CLR_TEXT};margin:16px 0 8px;'>Drop Zone (Parachute) Notes</h4>",
                unsafe_allow_html=True)
    dw = raw.get("wind_speed",99)<18; df = raw.get("avg_slope_deg",99)<3
    dv = raw.get("visibility_m",0)>=5000; do = sc.get("Obstacle Clearance",0)>=6
    ds = sum([dw,df,dv,do])
    dzv = "SUITABLE" if ds>=3 else "MARGINAL" if ds>=2 else "UNSUITABLE"
    dzc = CLR_GO if ds>=3 else CLR_COND if ds>=2 else CLR_NOGO
    dn = [f"Wind: {'OK (<18 km/h)' if dw else 'TOO HIGH'}",
          f"Flatness: {'OK (<3 deg)' if df else 'TOO STEEP'}",
          f"Visibility: {'OK (>5 km)' if dv else 'INSUFFICIENT'}",
          f"Obstacles: {'CLEAR' if do else 'HAZARDS present'}"]
    st.markdown(
        f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px 16px;'
        f'border:1px solid {dzc}55;margin-bottom:10px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:14px;color:{CLR_TEXT};font-weight:600;">DZ Assessment</span>'
        f'<span style="padding:3px 14px;border-radius:10px;background:{dzc}33;'
        f'color:{dzc};font-weight:700;font-size:13px;">{dzv}</span></div>'
        f'<div style="margin-top:8px;font-size:12px;color:{CLR_DIM};'
        f'line-height:1.6;">{"<br>".join(dn)}</div></div>', unsafe_allow_html=True)

    # Raw data
    with st.expander("Raw API Data", expanded=False):
        st.json({"scores": sc, "details": det, "overall": ov, "verdict": verdict,
                 "lz_class": lzc,
                 "wind": {"speed": raw.get("wind_speed"), "gusts": raw.get("wind_gusts"),
                          "dir": raw.get("wind_dir"), "compass": raw.get("wind_compass")},
                 "terrain": {"elev_m": raw.get("center_elevation"),
                             "avg_slope": raw.get("avg_slope_deg"), "max_slope": raw.get("max_slope_deg")},
                 "visibility": {"m": raw.get("visibility_m"), "cloud_pct": raw.get("cloud_cover"),
                                "precip_mm": raw.get("precipitation")},
                 "obstacles_n": len(raw.get("obstacle_elements",[])),
                 "approach_obs_n": len(raw.get("approach_elements",[])),
                 "access_n": len(raw.get("access_elements",[])),
                 "quadrants": raw.get("quadrants")})
