"""
Camp Site Selection AI module for TerraScout AI.
Finds and evaluates the best camping / base camp locations near a point
across 8 dimensions: ground flatness, drainage, water proximity, tree cover,
wind shelter, wildlife safety, access, and amenities.
Uses free APIs: Open Topo Data, ISRIC SoilGrids v2.0, Overpass, Open-Meteo,
iNaturalist (no API keys required).
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
CLR_ACCENT, CLR_GOOD, CLR_MED, CLR_BAD = "#f59e0b", "#22c55e", "#f59e0b", "#ef4444"

DIMS = {
    "Ground Flatness":  {"c": "#3b82f6", "w": 0.15},
    "Drainage":         {"c": "#a0785a", "w": 0.12},
    "Water Proximity":  {"c": "#06b6d4", "w": 0.14},
    "Tree Cover":       {"c": "#22c55e", "w": 0.12},
    "Wind Shelter":     {"c": "#8b5cf6", "w": 0.13},
    "Wildlife Safety":  {"c": "#ef4444", "w": 0.10},
    "Access":           {"c": "#f59e0b", "w": 0.12},
    "Amenities":        {"c": "#ec4899", "w": 0.12},
}
DIM_ORDER = list(DIMS.keys())

# ── Helpers ──────────────────────────────────────────────────────────────────
def _clamp(v, lo=0.0, hi=10.0): return max(lo, min(hi, float(v)))
def _vc(s): return CLR_GOOD if s >= 7 else CLR_MED if s >= 4 else CLR_BAD
def _stars(s10):
    n = max(0, min(5, round(s10 / 2)))
    return n, "\u2605" * n + "\u2606" * (5 - n)
def _hav(la1, lo1, la2, lo2):
    R = 6371.0; dl, dn = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dl/2)**2 + math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dn/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
def _mean(v):
    c = [x for x in (v or []) if x is not None]
    return sum(c)/len(c) if c else 0.0
def _near(lat, lon, els):
    best = None
    for e in (els if isinstance(els, list) else []):
        la = e.get("lat") or (e.get("center") or {}).get("lat")
        lo = e.get("lon") or (e.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            d = _hav(lat, lon, la, lo)
            if best is None or d < best: best = d
    return best
def _compass(deg):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[int((deg + 11.25) / 22.5) % 16]
def _tent_dir(wind_deg):
    opp = (wind_deg + 180) % 360
    return _compass(opp), opp
def _card(name, score, det, color):
    c = _vc(score)
    return (f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px 12px;'
            f'border:1px solid {color}44;margin-bottom:8px;min-height:130px;">'
            f'<div style="font-size:12px;color:{color};font-weight:600;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">{escape(name)}</div>'
            f'<div style="font-size:28px;font-weight:800;color:{c};">{score}</div>'
            f'<div style="font-size:11px;color:{CLR_DIM};margin-top:4px;'
            f'line-height:1.35;">{escape(det[:100])}</div></div>')

# ── Data Fetching (all cached ttl=900, timeout=10, try/except) ───────────────
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
def _fetch_soil(lat, lon):
    try:
        r = requests.get("https://rest.isric.org/soilgrids/v2.0/properties/query",
                         params={"lon": lon, "lat": lat, "property": ["clay","sand","soc"],
                                 "depth": "0-5cm", "value": "mean"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("SoilGrids error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_water(lat, lon, radius=2000):
    q = f"""[out:json][timeout:25];(
      node["natural"="spring"](around:{radius},{lat},{lon});
      way["waterway"="stream"](around:{radius},{lat},{lon});
      way["waterway"="river"](around:{radius},{lat},{lon});
      node["natural"="water"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
      node["man_made"="water_well"](around:{radius},{lat},{lon});
      node["amenity"="drinking_water"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Water error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_trees(lat, lon, radius=1500):
    q = f"""[out:json][timeout:25];(
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      node["natural"="tree"](around:{radius},{lat},{lon});
      way["natural"="scrub"](around:{radius},{lat},{lon});
      way["natural"="tree_row"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Trees error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,wind_gusts_10m,wind_direction_10m,precipitation,relative_humidity_2m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Weather error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_wildlife(lat, lon):
    try:
        r = requests.get("https://api.inaturalist.org/v1/observations",
                         params={"lat": lat, "lng": lon, "radius": 10,
                                 "per_page": 0, "iconic_taxa": "Mammalia"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("iNaturalist error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_wildlife_detail(lat, lon):
    try:
        r = requests.get("https://api.inaturalist.org/v1/observations",
                         params={"lat": lat, "lng": lon, "radius": 10,
                                 "per_page": 30, "iconic_taxa": "Mammalia",
                                 "order_by": "observed_on"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("iNaturalist detail error: %s", e); return {"results": []}

@st.cache_data(ttl=900)
def _fetch_access(lat, lon, radius=3000):
    q = f"""[out:json][timeout:25];(
      way["highway"~"path|footway|track|cycleway|bridleway"](around:{radius},{lat},{lon});
      way["highway"~"residential|unclassified|tertiary|secondary|primary"](around:{radius},{lat},{lon});
      node["amenity"="parking"](around:{radius},{lat},{lon});
      node["highway"="trailhead"](around:{radius},{lat},{lon});
      node["information"="guidepost"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Access error: %s", e); return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_amenities(lat, lon, radius=3000):
    q = f"""[out:json][timeout:25];(
      node["tourism"="camp_site"](around:{radius},{lat},{lon});
      way["tourism"="camp_site"](around:{radius},{lat},{lon});
      node["amenity"="toilets"](around:{radius},{lat},{lon});
      node["amenity"="shelter"](around:{radius},{lat},{lon});
      way["amenity"="shelter"](around:{radius},{lat},{lon});
      node["leisure"="picnic_table"](around:{radius},{lat},{lon});
      node["tourism"="picnic_site"](around:{radius},{lat},{lon});
      node["amenity"="bbq"](around:{radius},{lat},{lon});
      node["tourism"="wilderness_hut"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Amenities error: %s", e); return {"elements": []}

# ── Scoring Engine ───────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def _score(lat, lon):
    ed = _fetch_elev(lat, lon); soil = _fetch_soil(lat, lon)
    water = _fetch_water(lat, lon); trees = _fetch_trees(lat, lon)
    wx = _fetch_weather(lat, lon); wl = _fetch_wildlife(lat, lon)
    wl_det = _fetch_wildlife_detail(lat, lon)
    acc = _fetch_access(lat, lon); amen = _fetch_amenities(lat, lon)
    S, D = {}, {}

    # 1 ─ Ground Flatness
    elevs, steps = ed.get("elevs",[]), ed.get("steps",7)
    sp_m = ed.get("sp",0.0008)*111320.0; slopes = []
    if len(elevs) == steps*steps:
        for i in range(steps):
            for j in range(steps):
                ix = i*steps+j
                if j < steps-1: slopes.append(math.degrees(math.atan2(abs(elevs[ix]-elevs[ix+1]), sp_m)))
                if i < steps-1: slopes.append(math.degrees(math.atan2(abs(elevs[ix]-elevs[(i+1)*steps+j]), sp_m)))
    avg_s, max_s = _mean(slopes), max(slopes) if slopes else 0
    ce = elevs[len(elevs)//2] if elevs else 0.0
    if not slopes:          fs, fd = 5.0, "Elevation data unavailable"
    elif avg_s < 1.0:       fs, fd = 9.8, f"Perfectly flat ({avg_s:.1f} deg), ideal tent ground"
    elif avg_s < 2.5:       fs, fd = 8.5, f"Very flat ({avg_s:.1f} deg), excellent for tents"
    elif avg_s < 5.0:       fs, fd = 7.0, f"Gentle slope ({avg_s:.1f} deg), good with leveling"
    elif avg_s < 8.0:       fs, fd = 5.0, f"Moderate slope ({avg_s:.1f} deg), needs careful setup"
    elif avg_s < 12.0:      fs, fd = 3.0, f"Steep ({avg_s:.1f} deg), poor for camping"
    else:                   fs, fd = 1.5, f"Very steep ({avg_s:.1f} deg), unsuitable"
    if ce > 3500: fs = _clamp(fs - 1.5); fd += "; high altitude risk"
    S["Ground Flatness"], D["Ground Flatness"] = round(_clamp(fs),1), fd

    # 2 ─ Drainage (SoilGrids v2.0)
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln: _layer_map[_ln] = _l
    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths: return (depths[0].get("values", {}).get("mean") or 0) / div
        return None
    clay, sand, soc = _sv("clay",10), _sv("sand",10), _sv("soc",10)
    if sand is not None and clay is not None:
        if sand > 50 and clay < 20:    ds, dd = 9.0, f"Sandy ({sand:.0f}%), excellent drainage"
        elif sand > 35 and clay < 30:  ds, dd = 7.5, f"Good drainage ({sand:.0f}% sand, {clay:.0f}% clay)"
        elif clay < 30:                ds, dd = 6.5, f"Moderate drainage ({clay:.0f}% clay)"
        elif clay < 45:                ds, dd = 4.5, f"Poor drainage, high clay ({clay:.0f}%); puddling"
        else:                          ds, dd = 2.5, f"Very high clay ({clay:.0f}%); waterlogging"
        if soc is not None and soc > 40: ds = _clamp(ds - 1.0); dd += "; organic-rich"
    elif clay is not None:
        ds = 7.0 if clay < 25 else 4.5 if clay < 40 else 2.5; dd = f"Clay {clay:.0f}%"
    else: ds, dd = 5.0, "Soil data unavailable; check on-site"
    S["Drainage"], D["Drainage"] = round(_clamp(ds),1), dd

    # 3 ─ Water Proximity
    wl_el = [e for e in ((water or {}).get("elements",[]) or []) if isinstance(e, dict)]
    springs = [e for e in wl_el if e.get("tags",{}).get("natural")=="spring"]
    streams = [e for e in wl_el if e.get("tags",{}).get("waterway") in ("stream","river")]
    wells   = [e for e in wl_el if e.get("tags",{}).get("man_made")=="water_well"]
    drink   = [e for e in wl_el if e.get("tags",{}).get("amenity")=="drinking_water"]
    wbod    = [e for e in wl_el if e.get("tags",{}).get("natural")=="water"]
    nw = _near(lat, lon, wl_el)
    if not wl_el: ws, wd = 1.5, "No water sources within 2 km"
    elif nw is not None:
        if   nw < 0.05: ws, wd = 5.5, f"Water very close ({nw*1000:.0f}m); flood risk"
        elif nw < 0.2:  ws, wd = 9.0, f"Ideal water distance ({nw*1000:.0f}m)"
        elif nw < 0.5:  ws, wd = 8.0, f"Good water access ({nw*1000:.0f}m)"
        elif nw < 1.0:  ws, wd = 6.5, f"Moderate walk to water ({nw:.2f} km)"
        else:           ws, wd = 4.0, f"Water distant ({nw:.1f} km)"
        tv = sum(1 for g in [springs,streams,wells,drink,wbod] if g)
        ws = _clamp(ws + tv*0.3)
        pp = [f"{len(l)} {n}" for n,l in [("springs",springs),("streams",streams),
              ("wells",wells),("drinking",drink),("bodies",wbod)] if l]
        if pp: wd += " | " + ", ".join(pp)
    else: ws, wd = 4.0, f"{len(wl_el)} water features"
    S["Water Proximity"], D["Water Proximity"] = round(_clamp(ws),1), wd

    # 4 ─ Tree Cover
    tl = [e for e in ((trees or {}).get("elements",[]) or []) if isinstance(e, dict)]
    forests = [e for e in tl if e.get("tags",{}).get("landuse")=="forest" or e.get("tags",{}).get("natural")=="wood"]
    itrees  = [e for e in tl if e.get("tags",{}).get("natural")=="tree"]
    scrub   = [e for e in tl if e.get("tags",{}).get("natural")=="scrub"]
    trows   = [e for e in tl if e.get("tags",{}).get("natural")=="tree_row"]
    nt = _near(lat, lon, tl)
    if not tl: ts, td = 2.0, "No tree cover within 1.5 km; exposed"
    else:
        if forests:
            fc = len(forests)
            if fc <= 3:    ts, tdp = 8.5, "Good forest for shade/wind protection"
            elif fc <= 8:  ts, tdp = 7.5, "Moderate forest; some clearing needed"
            else:          ts, tdp = 5.5, "Dense forest; limited tent ground"
        else: ts, tdp = 6.0 + min(2.0, len(itrees)*0.2), "Scattered trees"
        if trows: ts = _clamp(ts + 0.5)
        if nt and nt < 0.1: ts = _clamp(ts + 0.5)
        pp = [f"{len(l)} {n}" for n,l in [("forests",forests),("trees",itrees),
              ("scrub",scrub),("rows",trows)] if l]
        td = tdp + " | " + ", ".join(pp)
    S["Tree Cover"], D["Tree Cover"] = round(_clamp(ts),1), td

    # 5 ─ Wind Shelter (Open-Meteo + elevation)
    cur = (wx if isinstance(wx, dict) else {}).get("current",{})
    daily = (wx if isinstance(wx, dict) else {}).get("daily",{})
    wspd = cur.get("wind_speed_10m",0) or 0; wgst = cur.get("wind_gusts_10m",0) or 0
    wdir = cur.get("wind_direction_10m",0) or 0; wcomp = _compass(wdir)
    temp = cur.get("temperature_2m",15) or 15; hum = cur.get("relative_humidity_2m",50) or 50
    prec = cur.get("precipitation",0) or 0
    dw_max = daily.get("wind_speed_10m_max",[]); dp = daily.get("precipitation_sum",[])
    dtmax = daily.get("temperature_2m_max",[]); dtmin = daily.get("temperature_2m_min",[])
    mw7 = max((v for v in dw_max if v is not None), default=wspd)
    tp7 = sum(v for v in dp if v is not None)
    eff = max(wspd, wgst*0.7)
    eb = 1.0 if ce < 200 else 0.5 if ce < 500 else -1.0 if ce > 2000 else 0.0
    tb = min(1.5, len(forests)*0.3) if forests else min(0.8, len(itrees)*0.1) if itrees else 0.0
    if   eff < 8:  wsh, wsd = 9.0, f"Calm ({wspd:.0f} km/h {wcomp})"
    elif eff < 15: wsh, wsd = 7.5, f"Light ({wspd:.0f}, gusts {wgst:.0f} km/h)"
    elif eff < 25: wsh, wsd = 5.5, f"Moderate ({wspd:.0f}, gusts {wgst:.0f} km/h)"
    elif eff < 40: wsh, wsd = 3.5, f"Strong ({wspd:.0f}, gusts {wgst:.0f} km/h)"
    else:          wsh, wsd = 1.5, f"Dangerous ({wspd:.0f}, gusts {wgst:.0f} km/h)"
    wsh = _clamp(wsh + eb + tb)
    if tb > 0: wsd += "; windbreak nearby"
    if mw7 > 50: wsh = _clamp(wsh - 1.5); wsd += f"; 7d max {mw7:.0f}!"
    S["Wind Shelter"], D["Wind Shelter"] = round(_clamp(wsh),1), wsd

    # 6 ─ Wildlife Safety (iNaturalist)
    try: tot_obs = int((wl if isinstance(wl, dict) else {}).get("total_results", 0))
    except (ValueError, TypeError): tot_obs = 0
    wr = (wl_det if isinstance(wl_det, dict) else {}).get("results",[])
    wr = wr if isinstance(wr, list) else []
    species = set()
    for ob in wr:
        tx = (ob.get("taxon") or {}) if isinstance(ob, dict) else {}
        nm = tx.get("preferred_common_name") or tx.get("name","")
        if nm: species.add(nm)
    danger_kw = {"bear","wolf","cougar","mountain lion","puma","jaguar","leopard","lion",
                 "tiger","hyena","wild boar","boar","moose","bison","hippopotamus",
                 "crocodile","alligator","rattlesnake","cobra","wolverine","elephant"}
    danger = [sp for sp in species if any(k in sp.lower() for k in danger_kw)]
    if tot_obs == 0:       wls, wld = 7.0, "No mammal observations; low data"
    elif danger:           wls, wld = max(2.0, 6.0-len(danger)*1.5), f"Danger: {', '.join(danger[:3])}"
    elif tot_obs > 200:    wls, wld = 5.5, f"High activity ({tot_obs} obs, {len(species)} spp)"
    elif tot_obs > 50:     wls, wld = 7.0, f"Moderate ({tot_obs} obs, {len(species)} spp)"
    else:                  wls, wld = 8.5, f"Low activity ({tot_obs} obs); safe"
    S["Wildlife Safety"], D["Wildlife Safety"] = round(_clamp(wls),1), wld

    # 7 ─ Access
    al = [e for e in ((acc or {}).get("elements",[]) or []) if isinstance(e, dict)]
    trails = [e for e in al if e.get("tags",{}).get("highway") in ("path","footway","cycleway","bridleway")]
    tracks = [e for e in al if e.get("tags",{}).get("highway")=="track"]
    roads  = [e for e in al if e.get("tags",{}).get("highway") in ("residential","unclassified","tertiary","secondary","primary")]
    park   = [e for e in al if e.get("tags",{}).get("amenity")=="parking"]
    thd    = [e for e in al if e.get("tags",{}).get("highway")=="trailhead" or e.get("tags",{}).get("information")=="guidepost"]
    ntr = _near(lat, lon, trails+tracks); nrd = _near(lat, lon, roads)
    if not al: acs, acd = 2.0, "No trails/roads within 3 km; remote"
    else:
        acs = 3.0
        if trails: acs += min(2.5, len(trails)*0.15)
        if tracks: acs += min(1.5, len(tracks)*0.2)
        if roads:  acs += min(1.5, len(roads)*0.1)
        if park:   acs += 1.0
        if thd:    acs += 0.8
        if ntr and ntr < 0.2: acs += 1.0
        elif ntr and ntr < 0.5: acs += 0.5
        pp = [f"{len(l)} {n}" for n,l in [("trails",trails),("tracks",tracks),
              ("roads",roads),("parking",park),("trailheads",thd)] if l]
        acd = ", ".join(pp)
        if ntr: acd += f"; trail {ntr*1000:.0f}m"
        if nrd: acd += f"; road {nrd:.1f}km"
    S["Access"], D["Access"] = round(_clamp(acs),1), acd

    # 8 ─ Amenities
    ae = [e for e in ((amen or {}).get("elements",[]) or []) if isinstance(e, dict)]
    camps = [e for e in ae if e.get("tags",{}).get("tourism")=="camp_site"]
    toil  = [e for e in ae if e.get("tags",{}).get("amenity")=="toilets"]
    shelt = [e for e in ae if e.get("tags",{}).get("amenity")=="shelter" or e.get("tags",{}).get("tourism")=="wilderness_hut"]
    pic   = [e for e in ae if e.get("tags",{}).get("leisure")=="picnic_table" or e.get("tags",{}).get("tourism")=="picnic_site" or e.get("tags",{}).get("amenity")=="bbq"]
    nc = _near(lat, lon, camps)
    if not ae: ams, amd = 2.0, "No amenities within 3 km; wild camping"
    else:
        ams = 3.0
        if camps: ams += min(3.0, len(camps)*1.0)
        if toil:  ams += min(1.5, len(toil)*0.5)
        if shelt: ams += min(1.5, len(shelt)*0.5)
        if pic:   ams += min(1.0, len(pic)*0.3)
        if nc and nc < 0.5: ams += 1.0
        pp = [f"{len(l)} {n}" for n,l in [("campsites",camps),("toilets",toil),
              ("shelters",shelt),("picnic",pic)] if l]
        amd = ", ".join(pp)
        if nc: amd += f"; camp {nc:.1f}km"
    S["Amenities"], D["Amenities"] = round(_clamp(ams),1), amd

    # Overall
    wsum = sum(S[d]*DIMS[d]["w"] for d in DIM_ORDER)
    wtot = sum(DIMS[d]["w"] for d in DIM_ORDER)
    ov = round(wsum/wtot if wtot else 5.0, 1)
    sn, ss = _stars(ov); td_dir, td_deg = _tent_dir(wdir)
    recs = []
    for dim, msg in [("Ground Flatness","Terrain steep; find flatter ground."),
                     ("Drainage","Poor drainage; use raised groundsheet."),
                     ("Water Proximity","Bring extra water; none nearby."),
                     ("Tree Cover","Exposed; bring tarps for shade/wind."),
                     ("Wind Shelter","High winds; stake tent securely."),
                     ("Wildlife Safety","Wildlife risk; use bear canisters."),
                     ("Access","Remote; carry GPS, inform contacts."),
                     ("Amenities","No facilities; pack-out all waste.")]:
        if S[dim] < 5: recs.append(msg)
    if nw and nw < 0.05: recs.append("Too close to water; move uphill for flood safety.")
    if not recs: recs.append("Good campsite; follow Leave No Trace principles.")

    return {"scores": S, "details": D, "overall": ov, "stars": sn, "star_str": ss,
            "recommendations": recs,
            "advantages": [f"{d}: {D[d]}" for d in DIM_ORDER if S[d] >= 7.5],
            "challenges": [f"{d}: {D[d]}" for d in DIM_ORDER if S[d] < 4],
            "raw": {"center_elevation": ce, "avg_slope": avg_s, "max_slope": max_s,
                    "elevations": elevs, "grid_steps": steps,
                    "clay": clay, "sand": sand, "soc": soc, "nearest_water_km": nw,
                    "water_elements": wl_el, "tree_elements": tl, "nearest_tree_km": nt,
                    "wind_speed": wspd, "wind_gusts": wgst, "wind_dir": wdir,
                    "wind_compass": wcomp, "temp_c": temp, "humidity": hum,
                    "precip_now": prec, "max_wind_7d": mw7, "total_precip_7d": tp7,
                    "d_tmax": dtmax, "d_tmin": dtmin,
                    "wildlife_total": tot_obs, "wildlife_species": list(species),
                    "wildlife_danger": danger, "access_elements": al,
                    "nearest_trail_km": ntr, "nearest_road_km": nrd,
                    "amenity_elements": ae, "nearest_camp_km": nc,
                    "tent_dir": td_dir, "tent_deg": td_deg}}

# ── Radar Chart ──────────────────────────────────────────────────────────────
def _radar(scores):
    cats = DIM_ORDER + [DIM_ORDER[0]]
    vals = [scores[d] for d in DIM_ORDER] + [scores[DIM_ORDER[0]]]
    cols = [DIMS[d]["c"] for d in DIM_ORDER]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself", fillcolor="rgba(34,197,94,0.12)",
        line=dict(color="#22c55e", width=2.5),
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
        margin=dict(l=60,r=60,t=30,b=30), height=420)
    return fig

# ── Wind Rose ────────────────────────────────────────────────────────────────
def _wind_rose(wspd, wgst, wdeg, tdeg):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[0,wspd], theta=[wdeg,wdeg], mode="lines+markers",
        line=dict(color="#06b6d4", width=4),
        marker=dict(size=[6,14], color="#06b6d4", symbol=["circle","arrow-up"]),
        name=f"Wind {wspd:.0f} km/h"))
    if wgst > wspd:
        fig.add_trace(go.Scatterpolar(r=[0,wgst], theta=[wdeg,wdeg], mode="lines",
            line=dict(color="#ef4444", width=2, dash="dash"), name=f"Gusts {wgst:.0f}"))
    fig.add_trace(go.Scatterpolar(r=[0, max(wspd,wgst,15)*0.6], theta=[tdeg,tdeg],
        mode="lines+markers", line=dict(color="#22c55e", width=3, dash="dot"),
        marker=dict(size=[4,12], color="#22c55e", symbol=["circle","triangle-up"]),
        name="Tent Door"))
    mx = max(wgst, wspd, 20)*1.3
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
        margin=dict(l=50,r=50,t=30,b=30), height=370)
    return fig

# ── Folium Map ───────────────────────────────────────────────────────────────
def _build_map(lat, lon, raw):
    try: import folium
    except ImportError: return None
    m = folium.Map(location=[lat,lon], zoom_start=15, tiles="CartoDB dark_matter")
    folium.Marker([lat,lon],
        popup=folium.Popup(f"<b>Camp Site</b><br>{lat:.5f}, {lon:.5f}<br>"
              f"Elev: {raw.get('center_elevation',0):.0f}m<br>"
              f"Slope: {raw.get('avg_slope',0):.1f} deg<br>"
              f"Tent door: {raw.get('tent_dir','N')}", max_width=240),
        icon=folium.Icon(color="green", icon="campground", prefix="fa")).add_to(m)
    folium.Circle([lat,lon], radius=2000, color=CLR_ACCENT, fill=False,
                  weight=1.5, dash_array="6 4", popup="2 km radius").add_to(m)
    # Water (blue)
    for el in raw.get("water_elements",[]):
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            tg = el.get("tags",{}); nm = tg.get("name", tg.get("waterway") or tg.get("natural") or "water")
            folium.CircleMarker([la,lo], radius=5, color="#06b6d4", fill=True,
                fill_color="#06b6d4", fill_opacity=0.7, popup=f"Water: {escape(str(nm))}").add_to(m)
    # Trees (green)
    for el in raw.get("tree_elements",[])[:30]:
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            folium.CircleMarker([la,lo], radius=4, color="#22c55e", fill=True,
                fill_color="#22c55e", fill_opacity=0.5,
                popup=f"Veg: {escape(el.get('tags',{}).get('natural','') or el.get('tags',{}).get('landuse','tree'))}").add_to(m)
    # Access
    for el in raw.get("access_elements",[])[:40]:
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            tg = el.get("tags",{}); hw = tg.get("highway",""); am = tg.get("amenity","")
            if am == "parking":
                folium.Marker([la,lo], popup="Parking", icon=folium.Icon(color="orange", icon="parking", prefix="fa")).add_to(m)
            elif hw == "trailhead" or tg.get("information")=="guidepost":
                folium.Marker([la,lo], popup="Trailhead", icon=folium.Icon(color="cadetblue", icon="hiking", prefix="fa")).add_to(m)
            else:
                folium.CircleMarker([la,lo], radius=3, color="#f59e0b", fill=True,
                    fill_color="#f59e0b", fill_opacity=0.4, popup=f"Path: {escape(hw or 'trail')}").add_to(m)
    # Amenities
    for el in raw.get("amenity_elements",[]):
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is not None and lo is not None:
            tg = el.get("tags",{}); tour = tg.get("tourism",""); am = tg.get("amenity","")
            if tour == "camp_site":
                folium.Marker([la,lo], popup=f"Campsite: {escape(tg.get('name','unnamed'))}",
                    icon=folium.Icon(color="green", icon="tent", prefix="fa")).add_to(m)
            elif am == "toilets":
                folium.Marker([la,lo], popup="Toilets", icon=folium.Icon(color="blue", icon="restroom", prefix="fa")).add_to(m)
            elif am == "shelter" or tour == "wilderness_hut":
                folium.Marker([la,lo], popup=f"Shelter: {escape(tg.get('name','shelter'))}",
                    icon=folium.Icon(color="darkred", icon="house", prefix="fa")).add_to(m)
            elif tg.get("leisure")=="picnic_table" or tour=="picnic_site" or am=="bbq":
                folium.CircleMarker([la,lo], radius=5, color="#ec4899", fill=True,
                    fill_color="#ec4899", fill_opacity=0.6, popup="Picnic/BBQ").add_to(m)
    # Wind label
    wd = raw.get("wind_dir",0); olat = 0.003*math.cos(math.radians(wd)); olon = 0.003*math.sin(math.radians(wd))
    folium.Marker([lat+olat, lon+olon], popup=f"Wind: {raw.get('wind_speed',0):.0f} km/h {raw.get('wind_compass','N')}",
        icon=folium.DivIcon(html=f'<div style="font-size:11px;color:#06b6d4;font-weight:bold;'
             f'text-shadow:1px 1px 2px black;white-space:nowrap;">Wind {raw.get("wind_speed",0):.0f} km/h {raw.get("wind_compass","N")}</div>')).add_to(m)
    return m

# ── Main Render ──────────────────────────────────────────────────────────────
def render_camp_site_tab():
    """Single entry point for Camp Site Selection AI."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});'
        f'padding:24px 28px;border-radius:12px;border:1px solid {CLR_BORDER};margin-bottom:20px;">'
        f'<h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">Camp Site Selection AI</h2>'
        f'<p style="margin:6px 0 0;color:{CLR_DIM};font-size:14px;">'
        f'Find and evaluate the best camping / base camp locations across 8 dimensions.</p></div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=45.8326, format="%.4f", min_value=-90.0, max_value=90.0, key="camp_lat")
    lon = c2.number_input("Longitude", value=6.8652, format="%.4f", min_value=-180.0, max_value=180.0, key="camp_lon")

    if not st.button("Evaluate Camp Site", type="primary", key="camp_btn", use_container_width=True):
        st.info("Enter coordinates and click **Evaluate Camp Site** to analyse the area.")
        return

    with st.spinner("Analysing camp site across 8 dimensions..."):
        res = _score(lat, lon)
    sc, det, ov, raw = res["scores"], res["details"], res["overall"], res["raw"]
    stars, star_s, vc = res["stars"], res["star_str"], _vc(ov)
    vl = "EXCELLENT" if ov >= 8 else "GOOD" if ov >= 6 else "FAIR" if ov >= 4 else "POOR"

    # Verdict banner with stars
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{vc}22,{CLR_BG});padding:24px 28px;'
        f'border-radius:12px;border:2px solid {vc}88;margin:10px 0 18px;text-align:center;">'
        f'<span style="font-size:13px;color:{CLR_DIM};text-transform:uppercase;letter-spacing:2px;">'
        f'Camp Site Assessment</span>'
        f'<h1 style="margin:8px 0 4px;color:{vc};font-size:52px;font-weight:800;">{ov}/10</h1>'
        f'<div style="font-size:32px;color:{CLR_ACCENT};letter-spacing:4px;margin-bottom:6px;">{star_s}</div>'
        f'<div style="display:inline-block;padding:6px 28px;border-radius:20px;'
        f'background:{vc}33;border:1px solid {vc}66;">'
        f'<span style="font-size:22px;font-weight:700;color:{vc};letter-spacing:3px;">{vl}</span></div>'
        f'<p style="margin:10px 0 0;color:{CLR_DIM};font-size:13px;">'
        f'Location: {lat:.4f}, {lon:.4f} &middot; Elev: {raw.get("center_elevation",0):.0f}m '
        f'&middot; {stars}/5 Stars</p></div>', unsafe_allow_html=True)

    # Key metrics
    m1, m2, m3, m4 = st.columns(4)
    nw = raw.get("nearest_water_km")
    m1.metric("Nearest Water",
              f"{nw*1000:.0f} m" if nw and nw < 1 else f"{nw:.1f} km" if nw else "N/A",
              delta="OK" if nw and 0.05 < nw < 1 else "Far" if nw and nw >= 1 else "Close!" if nw else None,
              delta_color="normal" if nw and 0.05 < nw < 1 else "inverse")
    m2.metric("Wind", f"{raw.get('wind_speed',0):.0f} km/h",
              delta=f"Gusts {raw.get('wind_gusts',0):.0f}",
              delta_color="normal" if raw.get("wind_gusts",99) < 25 else "inverse")
    m3.metric("Temperature", f"{raw.get('temp_c',0):.1f} C",
              delta=f"Humidity {raw.get('humidity',0):.0f}%", delta_color="off")
    m4.metric("Tent Door", raw.get("tent_dir","N"),
              delta=f"Face {raw.get('tent_dir','N')}, away from wind", delta_color="off")

    # Dimension cards
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin-bottom:12px;'>Dimension Scores</h3>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    for i, d in enumerate(DIM_ORDER):
        (ca if i%2==0 else cb).markdown(_card(d, sc[d], det[d], DIMS[d]["c"]), unsafe_allow_html=True)

    # Radar
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Camp Suitability Radar</h3>", unsafe_allow_html=True)
    st.plotly_chart(_radar(sc, key="camsit_pchart1"), use_container_width=True, key="camp_radar")

    # Wind + Water side-by-side
    w1, w2 = st.columns(2)
    with w1:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Wind &amp; Tent Orientation</h4>", unsafe_allow_html=True)
        st.plotly_chart(_wind_rose(raw.get("wind_speed",0, key="camsit_pchart2"), raw.get("wind_gusts",0),
                        raw.get("wind_dir",0), raw.get("tent_deg",0)),
                        use_container_width=True, key="camp_wind_fig")
        st.caption(f"Green = tent door (**{raw.get('tent_dir','N')}**), away from wind.")
    with w2:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Water Distance</h4>", unsafe_allow_html=True)
        nwk = raw.get("nearest_water_km")
        if nwk is not None:
            dm = nwk*1000; bp = max(5, min(100, 100-dm/20))
            bc = CLR_MED if dm < 50 else CLR_GOOD if dm < 500 else CLR_MED if dm < 1000 else CLR_BAD
            zn = "FLOOD RISK" if dm < 50 else "IDEAL" if dm < 500 else "MODERATE" if dm < 1000 else "FAR"
            st.markdown(
                f'<div style="background:{CLR_CARD};border-radius:10px;padding:16px;border:1px solid {bc}44;">'
                f'<div style="font-size:36px;font-weight:800;color:{bc};text-align:center;">{dm:.0f} m</div>'
                f'<div style="text-align:center;margin:6px 0;"><span style="padding:3px 14px;border-radius:10px;'
                f'background:{bc}33;color:{bc};font-weight:700;font-size:13px;">{zn}</span></div>'
                f'<div style="background:{CLR_SURFACE};border-radius:6px;height:12px;margin-top:10px;overflow:hidden;">'
                f'<div style="width:{bp:.0f}%;height:100%;background:{bc};border-radius:6px;"></div></div>'
                f'<div style="font-size:11px;color:{CLR_DIM};margin-top:8px;text-align:center;">'
                f'Ideal distance: 50-500m</div></div>', unsafe_allow_html=True)
        else: st.info("No water sources detected within search radius.")
        # Wildlife summary
        st.markdown(f"<h4 style='color:{CLR_TEXT};margin-top:16px;'>Wildlife Report</h4>", unsafe_allow_html=True)
        wl_d = raw.get("wildlife_danger",[]); dc = CLR_BAD if wl_d else CLR_GOOD
        st.markdown(
            f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px;border:1px solid {dc}44;">'
            f'<div style="font-size:13px;color:{CLR_TEXT};font-weight:600;">'
            f'Mammal Observations (10 km): {raw.get("wildlife_total",0)}</div>'
            f'<div style="font-size:12px;color:{CLR_DIM};margin-top:4px;">'
            f'Species: {len(raw.get("wildlife_species",[]))}</div>'
            + (f'<div style="margin-top:6px;padding:6px 10px;background:{CLR_BAD}22;border-radius:6px;'
               f'border:1px solid {CLR_BAD}44;color:{CLR_BAD};font-size:12px;font-weight:600;">'
               f'Dangerous: {", ".join(wl_d[:5])}</div>' if wl_d else
               f'<div style="margin-top:6px;color:{CLR_GOOD};font-size:12px;">No dangerous species detected</div>')
            + '</div>', unsafe_allow_html=True)

    # Folium map
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Camp Site Map</h3>", unsafe_allow_html=True)
    fm = _build_map(lat, lon, raw)
    if fm:
        try:
            from streamlit_folium import st_folium
            st_folium(fm, width=None, height=500, key="camp_folium_map")
        except ImportError:
            import streamlit.components.v1 as components
            components.html(fm._repr_html_(), height=520)
    else: st.warning("Folium not installed; map unavailable.")

    # Advantages & Challenges
    ac, cc = st.columns(2)
    with ac:
        st.markdown(f"<h4 style='color:{CLR_GOOD};'>Advantages</h4>", unsafe_allow_html=True)
        for a in (res["advantages"] or []): st.markdown(f"- {a}")
        if not res["advantages"]: st.caption("No strong advantages identified.")
    with cc:
        st.markdown(f"<h4 style='color:{CLR_BAD};'>Challenges</h4>", unsafe_allow_html=True)
        for c in (res["challenges"] or []): st.markdown(f"- {c}")
        if not res["challenges"]: st.caption("No critical challenges identified.")

    # Recommendations
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin:20px 0 8px;'>Recommendations</h3>", unsafe_allow_html=True)
    for rec in res["recommendations"]:
        st.markdown(f'<div style="background:{CLR_CARD};border-radius:8px;padding:10px 14px;'
                    f'border-left:3px solid {CLR_ACCENT};margin-bottom:6px;'
                    f'font-size:13px;color:{CLR_TEXT};">{escape(rec)}</div>', unsafe_allow_html=True)

    # Gear checklist
    st.markdown(f"<h4 style='color:{CLR_TEXT};margin:16px 0 8px;'>Suggested Gear</h4>", unsafe_allow_html=True)
    gear = ["Tent + rain fly", "Sleeping bag", "Ground pad", "Water purification"]
    if raw.get("wind_gusts",0) > 20: gear.append("Extra stakes & guy ropes")
    if raw.get("total_precip_7d",0) > 20: gear.append("Rain gear & tarp")
    if raw.get("wildlife_danger"): gear.append("Bear canister / food hang")
    if sc.get("Access",10) < 5: gear.append("GPS / sat communicator")
    if sc.get("Amenities",10) < 4: gear.append("Portable toilet / WAG bags")
    if raw.get("temp_c",15) < 5: gear.append("Insulated pad & layers")
    elif raw.get("temp_c",15) > 30: gear.append("Sun shade & extra water")
    gh = "".join(f'<div style="display:inline-block;padding:4px 12px;border-radius:6px;'
                 f'background:{CLR_CARD};border:1px solid {CLR_BORDER};margin:3px 4px;'
                 f'font-size:12px;color:{CLR_TEXT};">{escape(g)}</div>' for g in gear)
    st.markdown(f'<div style="margin-bottom:12px;">{gh}</div>', unsafe_allow_html=True)

    # 7-day forecast
    with st.expander("7-Day Weather Forecast", expanded=False):
        dtx, dtn = raw.get("d_tmax",[]), raw.get("d_tmin",[])
        if dtx and dtn:
            st.markdown(f"**Temp range:** {min((v for v in dtn if v is not None), default=0):.0f} "
                        f"to {max((v for v in dtx if v is not None), default=0):.0f} C")
        st.markdown(f"**7d precipitation:** {raw.get('total_precip_7d',0):.1f} mm")
        st.markdown(f"**Max wind (7d):** {raw.get('max_wind_7d',0):.0f} km/h")
        if raw.get("total_precip_7d",0) > 50: st.warning("Heavy rain expected; waterproof gear.")
        if raw.get("max_wind_7d",0) > 40: st.warning("Strong winds; reinforce anchoring.")

    # Raw data
    with st.expander("Raw API Data", expanded=False):
        st.json({"scores": sc, "details": det, "overall": ov, "stars": stars, "verdict": vl,
                 "wind": {"speed": raw.get("wind_speed"), "gusts": raw.get("wind_gusts"),
                          "dir": raw.get("wind_dir"), "compass": raw.get("wind_compass")},
                 "terrain": {"elev_m": raw.get("center_elevation"),
                             "avg_slope": raw.get("avg_slope"), "max_slope": raw.get("max_slope")},
                 "soil": {"clay": raw.get("clay"), "sand": raw.get("sand"), "soc": raw.get("soc")},
                 "water": {"nearest_km": raw.get("nearest_water_km"),
                           "count": len(raw.get("water_elements",[]))},
                 "trees": {"nearest_km": raw.get("nearest_tree_km"),
                           "count": len(raw.get("tree_elements",[]))},
                 "wildlife": {"total": raw.get("wildlife_total"),
                              "species": raw.get("wildlife_species"),
                              "dangerous": raw.get("wildlife_danger")},
                 "access": {"nearest_trail_km": raw.get("nearest_trail_km"),
                            "nearest_road_km": raw.get("nearest_road_km"),
                            "count": len(raw.get("access_elements",[]))},
                 "amenities": {"nearest_camp_km": raw.get("nearest_camp_km"),
                               "count": len(raw.get("amenity_elements",[]))},
                 "tent_orientation": raw.get("tent_dir")})
