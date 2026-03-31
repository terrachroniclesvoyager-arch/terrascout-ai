"""
Administrative Boundary Intelligence module for TerraScout AI.

Shows what administrative boundaries a point falls within, nearby jurisdictions,
border proximity, timezone context, and elevation data.

Uses only free APIs (no API keys):
  - Nominatim / OpenStreetMap (reverse geocoding)
  - Overpass API (admin boundaries, nearby settlements, border proximity)
  - Open-Meteo (timezone & local info)
  - Open Topo Data (elevation)
"""

import json
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import streamlit as st
import requests
import pandas as pd

try:
    import folium
except ImportError:
    folium = None

try:
    from streamlit_folium import st_folium
except ImportError:
    st_folium = None

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
_HEADERS = {"User-Agent": "TerraScoutAI/1.0"}
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
EARTH_RADIUS_KM = 6371.0

ADMIN_LEVEL_LABELS = {
    "1": "Supranational", "2": "Country", "3": "Region / Territory",
    "4": "State / Province", "5": "District / Department",
    "6": "County / Municipality", "7": "Sub-county", "8": "City / Town",
    "9": "Ward / Borough", "10": "Neighbourhood / Suburb", "11": "Sub-neighbourhood",
}

_HIERARCHY_KEYS = [
    ("country", "Country"), ("state", "State / Region"),
    ("state_district", "State District"), ("province", "Province"),
    ("county", "County"), ("municipality", "Municipality"),
    ("city", "City"), ("town", "Town"), ("village", "Village"),
    ("city_district", "City District"), ("suburb", "Suburb"),
    ("neighbourhood", "Neighbourhood"), ("quarter", "Quarter"),
    ("road", "Road"), ("house_number", "House Number"), ("postcode", "Postcode"),
]


# ── Utilities ─────────────────────────────────────────────────────────────────
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two points (Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt_pop(pop: Any) -> str:
    try:
        return f"{int(pop):,}"
    except (TypeError, ValueError):
        return "N/A"


# ── API Functions (all cached, all with timeout=10 & try/except) ──────────────
@st.cache_data(ttl=900)
def _fetch_reverse_geocode(lat: float, lon: float) -> dict | None:
    """Reverse-geocode via Nominatim / OSM."""
    try:
        r = requests.get(NOMINATIM_REVERSE, params={
            "lat": lat, "lon": lon, "format": "json",
            "zoom": 18, "addressdetails": 1,
        }, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("Nominatim failed: %s", exc)
        return None


@st.cache_data(ttl=900)
def _fetch_admin_boundaries(lat: float, lon: float) -> list[dict]:
    """All admin boundary relations containing the point (Overpass is_in)."""
    q = (f'[out:json][timeout:25];is_in({lat},{lon})->.a;'
         f'relation(pivot.a)["admin_level"];out tags;')
    try:
        data = query_overpass(q, timeout=30)
        return data.get("elements", []) if data else []
    except Exception as exc:
        logger.warning("Overpass admin query failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_nearby_settlements(lat: float, lon: float, radius: int = 50000) -> list[dict]:
    """Cities, towns and villages within *radius* metres (Overpass)."""
    q = (f'[out:json][timeout:25];'
         f'node["place"~"city|town|village"](around:{radius},{lat},{lon});out body;')
    try:
        data = query_overpass(q, timeout=30)
        return data.get("elements", []) if data else []
    except Exception as exc:
        logger.warning("Overpass settlements failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_border_ways(lat: float, lon: float, radius: int = 100000) -> list[dict]:
    """International border ways (admin_level=2) near the point (Overpass)."""
    q = (f'[out:json][timeout:25];'
         f'way["admin_level"="2"]["boundary"="administrative"]'
         f'(around:{radius},{lat},{lon});out geom;')
    try:
        data = query_overpass(q, timeout=30)
        return data.get("elements", []) if data else []
    except Exception as exc:
        logger.warning("Overpass border query failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_timezone_info(lat: float, lon: float) -> dict | None:
    """Timezone + current temperature from Open-Meteo."""
    try:
        r = requests.get(OPEN_METEO_FORECAST, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m", "timezone": "auto",
        }, headers=_HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("Open-Meteo failed: %s", exc)
        return None


@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> float | None:
    """Elevation in metres from Open Topo Data (SRTM 30 m)."""
    try:
        r = requests.get(OPEN_TOPO_API,
                         params={"locations": f"{lat},{lon}"},
                         headers=_HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "OK" and data.get("results"):
            elev = data["results"][0].get("elevation")
            return _safe_float(elev) if elev is not None else None
        return None
    except Exception as exc:
        logger.warning("OpenTopoData failed: %s", exc)
        return None


# ── Processing helpers ────────────────────────────────────────────────────────
def _build_address_hierarchy(address: dict) -> list[tuple[str, str]]:
    return [(lbl, address[key]) for key, lbl in _HIERARCHY_KEYS if address.get(key)]


def _parse_admin_levels(elements: list[dict]) -> list[dict]:
    rows = []
    for el in elements:
        t = el.get("tags", {})
        lvl = t.get("admin_level", "?")
        name, name_en = t.get("name", "Unknown"), t.get("name:en", "")
        disp = f"{name} ({name_en})" if name_en and name_en != name else name
        rows.append({"Level": lvl,
                      "Type": ADMIN_LEVEL_LABELS.get(str(lvl), f"Level {lvl}"),
                      "Name": disp,
                      "Boundary": t.get("boundary", "administrative")})
    rows.sort(key=lambda r: _safe_float(r["Level"], 99))
    return rows


def _process_settlements(elements: list[dict], lat: float, lon: float) -> list[dict]:
    out = []
    for el in elements:
        sl, sn = el.get("lat", 0), el.get("lon", 0)
        t = el.get("tags", {})
        name, name_en = t.get("name", "Unknown"), t.get("name:en", "")
        disp = f"{name} ({name_en})" if name_en and name_en != name else name
        out.append({
            "Name": disp, "Type": t.get("place", "unknown").capitalize(),
            "Distance (km)": round(_haversine(lat, lon, sl, sn), 1),
            "Population": _fmt_pop(t.get("population")),
            "lat": sl, "lon": sn,
        })
    out.sort(key=lambda s: s["Distance (km)"])
    return out


def _nearest_border(ways: list[dict], lat: float, lon: float):
    """Return (min_dist_km | None, border_polylines)."""
    min_d, lines = None, []
    for w in ways:
        geom = w.get("geometry", [])
        if not geom:
            continue
        coords = [(p["lat"], p["lon"]) for p in geom]
        lines.append(coords)
        for pl, pn in coords:
            d = _haversine(lat, lon, pl, pn)
            if min_d is None or d < min_d:
                min_d = d
    return (round(min_d, 2) if min_d is not None else None, lines)


# ── Map builder ───────────────────────────────────────────────────────────────
def _build_map(lat, lon, settlements, border_lines):
    if folium is None:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=9, tiles="CartoDB positron")
    folium.Marker(
        [lat, lon], popup=f"Query Point<br>{lat:.4f}, {lon:.4f}",
        tooltip="Query Point",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)
    pcol = {"City": "blue", "Town": "green", "Village": "orange"}
    for s in settlements[:30]:
        pop_s = f"Pop: {s['Population']}" if s["Population"] != "N/A" else ""
        folium.CircleMarker(
            [s["lat"], s["lon"]],
            radius=6 if s["Type"] == "City" else 4,
            color=pcol.get(s["Type"], "gray"), fill=True, fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{s['Name']}</b><br>Type: {s['Type']}<br>"
                f"Distance: {s['Distance (km)']} km<br>{pop_s}", max_width=250),
            tooltip=f"{s['Name']} ({s['Distance (km)']} km)",
        ).add_to(m)
    for lc in border_lines:
        if len(lc) >= 2:
            folium.PolyLine(lc, color="#dc2626", weight=3, opacity=0.8,
                            dash_array="8 4", tooltip="International Border").add_to(m)
    folium.Circle([lat, lon], radius=50000, color="#6366f1",
                  fill=False, weight=1, dash_array="4 4",
                  tooltip="50 km radius").add_to(m)
    return m


# ── Section renderers ─────────────────────────────────────────────────────────
def _render_geocoding(geo: dict | None):
    st.markdown("### 1. Reverse Geocoding (Nominatim / OSM)")
    if geo is None:
        st.warning("Reverse geocoding request failed or returned no data.")
        return
    address = geo.get("address", {})
    if not address:
        st.info("No address details available for this location.")
        return
    hierarchy = _build_address_hierarchy(address)
    st.markdown(f"**Full Address:** {geo.get('display_name', 'N/A')}")
    crumbs = [v for l, v in hierarchy
              if l not in ("Postcode", "House Number", "Road")]
    if crumbs:
        st.markdown(f"**Hierarchy:** {' > '.join(reversed(crumbs))}")
    for i in range(0, len(hierarchy), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(hierarchy):
                col.metric(hierarchy[i + j][0], hierarchy[i + j][1])
    cc = address.get("country_code", "").upper()
    with st.expander("Raw Nominatim Details", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Country Code:** `{cc}`")
        c2.markdown(f"**OSM Type:** `{geo.get('osm_type', 'N/A')}`")
        c3.markdown(f"**OSM ID:** `{geo.get('osm_id', 'N/A')}`")
        st.json(address)


def _render_admin(elements: list[dict]):
    st.markdown("### 2. Administrative Levels (Overpass)")
    if not elements:
        st.info("No administrative boundary data returned. The Overpass API may be busy.")
        return
    rows = _parse_admin_levels(elements)
    if not rows:
        st.info("No admin levels found for this point.")
        return
    st.markdown(f"**{len(rows)} administrative boundaries** contain this point:")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={
                     "Level": st.column_config.TextColumn("Level", width="small"),
                     "Type": st.column_config.TextColumn("Classification", width="medium"),
                     "Name": st.column_config.TextColumn("Name", width="large"),
                     "Boundary": st.column_config.TextColumn("Boundary Type", width="medium"),
                 })


def _render_settlements(settlements: list[dict]):
    st.markdown("### 3. Nearby Cities, Towns & Villages")
    if not settlements:
        st.info("No settlements found within 50 km. The area may be very remote.")
        return
    cats = {t: [s for s in settlements if s["Type"] == t]
            for t in ("City", "Town", "Village")}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Settlements", len(settlements))
    m2.metric("Cities", len(cats["City"]))
    m3.metric("Towns", len(cats["Town"]))
    m4.metric("Villages", len(cats["Village"]))
    n = settlements[0]
    st.success(f"Nearest settlement: **{n['Name']}** ({n['Type']}) "
               f"at **{n['Distance (km)']} km**")
    tbl = [{k: s[k] for k in ("Name", "Type", "Distance (km)", "Population")}
           for s in settlements[:40]]
    if tbl:
        st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)


def _render_border(min_dist, border_lines):
    st.markdown("### 4. International Border Proximity")
    if min_dist is None:
        st.info("No international borders found within 100 km. "
                "This point may be deep in the interior of a large country.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Nearest Border", f"{min_dist} km")
    c2.metric("Border Segments Found", len(border_lines))
    if min_dist < 5:
        st.error("Very close to an international border (< 5 km).")
    elif min_dist < 20:
        st.warning("Near an international border (< 20 km).")
    elif min_dist < 50:
        st.info("Moderately close to an international border (< 50 km).")
    else:
        st.success("More than 50 km from the nearest international border.")


def _render_timezone(tz: dict | None):
    st.markdown("### 5. Time Zone & Local Info (Open-Meteo)")
    if tz is None:
        st.warning("Timezone data could not be retrieved.")
        return
    tz_name = tz.get("timezone", "Unknown")
    tz_abbr = tz.get("timezone_abbreviation", "?")
    off_s = tz.get("utc_offset_seconds", 0)
    off_h = off_s / 3600
    local_now = datetime.now(timezone.utc) + timedelta(seconds=off_s)
    cur = tz.get("current", {})
    temp = cur.get("temperature_2m")
    t_unit = tz.get("current_units", {}).get("temperature_2m", "C")
    c1, c2, c3 = st.columns(3)
    c1.metric("Timezone", tz_name)
    c2.metric("Abbreviation", tz_abbr)
    sign = "+" if off_h >= 0 else ""
    c3.metric("UTC Offset", f"UTC{sign}{off_h:.1f}")
    c4, c5 = st.columns(2)
    c4.metric("Local Time", local_now.strftime("%Y-%m-%d %H:%M:%S"))
    c5.metric("Current Temperature", f"{temp} {t_unit}" if temp is not None else "N/A")
    with st.expander("Open-Meteo Location Details", expanded=False):
        em = tz.get("elevation")
        if em is not None:
            st.markdown(f"**Model Elevation:** {em} m (Open-Meteo grid)")
        lm, nm = tz.get("latitude"), tz.get("longitude")
        if lm is not None and nm is not None:
            st.markdown(f"**Grid Coordinates:** {lm:.4f}, {nm:.4f} "
                        "(snapped to nearest model grid cell)")
        st.json({"timezone": tz_name, "abbreviation": tz_abbr,
                 "utc_offset_seconds": off_s, "model_elevation": em})


def _render_elevation(elevation: float | None):
    st.markdown("### 6. Elevation Context (Open Topo Data)")
    if elevation is None:
        st.warning("Elevation data unavailable. The point may be over ocean "
                   "or the API may be temporarily down.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Elevation", f"{elevation:.0f} m")
    c2.metric("Elevation (ft)", f"{elevation * 3.28084:.0f} ft")
    if elevation < 0:
        cls = "Below Sea Level"
    elif elevation < 200:
        cls = "Lowland"
    elif elevation < 500:
        cls = "Upland"
    elif elevation < 1500:
        cls = "Highland"
    elif elevation < 3500:
        cls = "Mountain"
    elif elevation < 5500:
        cls = "High Mountain"
    else:
        cls = "Extreme Altitude"
    c3.metric("Classification", cls)
    if elevation < 0:
        st.info(f"This location is **{abs(elevation):.0f} m below sea level**. "
                "It may be in a depression or rift valley.")
    elif elevation < 50:
        st.info("Low-elevation coastal or floodplain area. "
                "May be vulnerable to sea-level rise.")
    elif elevation > 4000:
        st.info("Extreme altitude. Challenges with thin air, cold temperatures "
                "and limited accessibility.")


def _render_map(lat, lon, settlements, border_lines):
    st.markdown("### Interactive Map")
    m = _build_map(lat, lon, settlements, border_lines)
    st.caption("**Legend:** Red marker = Query Point | Blue = City | "
               "Green = Town | Orange = Village | Red dashed = International "
               "Border | Purple dashed = 50 km radius")
    if m is not None and st_folium is not None:
        st_folium(m, width=None, height=520, key="bndint_map")
    else:
        st.warning("Install `folium` and `streamlit-folium` for interactive map: "
                   "`pip install folium streamlit-folium`")


def _render_summary(geo, admin_rows, settlements, min_bd, tz, elev, lat, lon):
    st.markdown("---")
    st.markdown("### Quick Summary")
    cols = st.columns(4)
    if geo and geo.get("address"):
        a = geo["address"]
        loc = ", ".join(filter(None, [
            a.get("city", a.get("town", a.get("village", ""))),
            a.get("state", a.get("province", "")),
            a.get("country", "Unknown"),
        ]))
        cols[0].metric("Location", loc[:40])
    else:
        cols[0].metric("Location", "Unknown")
    cols[1].metric("Admin Levels", f"{len(admin_rows)} boundaries")
    if settlements:
        cols[2].metric("Nearest Place", settlements[0]["Name"][:25])
    else:
        cols[2].metric("Nearest Place", "None within 50 km")
    cols[3].metric("Nearest Border",
                   f"{min_bd} km" if min_bd is not None else "> 100 km")
    # Timezone & elevation in second row
    cols2 = st.columns(3)
    if tz:
        cols2[0].metric("Timezone", tz.get("timezone", "?"))
        off = tz.get("utc_offset_seconds", 0) / 3600
        sign = "+" if off >= 0 else ""
        cols2[1].metric("UTC Offset", f"UTC{sign}{off:.1f}")
    else:
        cols2[0].metric("Timezone", "N/A")
        cols2[1].metric("UTC Offset", "N/A")
    cols2[2].metric("Elevation",
                    f"{elev:.0f} m" if elev is not None else "N/A")


# ── Main entry point ─────────────────────────────────────────────────────────
def render_boundary_intel_tab():
    """Single entry point for Administrative Boundary Intelligence."""
    st.markdown("## Administrative Boundary Intelligence")
    st.caption("Jurisdictions, borders, nearby settlements & "
               "administrative context for any coordinate.")

    # --- Input controls ---
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, min_value=-90.0,
                          max_value=90.0, format="%.4f", key="bndint_lat",
                          help="Decimal degrees (-90 to 90).")
    lon = c2.number_input("Longitude", value=12.4964, min_value=-180.0,
                          max_value=180.0, format="%.4f", key="bndint_lon",
                          help="Decimal degrees (-180 to 180).")

    presets = {
        "Custom": None,
        "Rome, Italy": (41.9028, 12.4964),
        "New York, USA": (40.7128, -74.0060),
        "Tokyo, Japan": (35.6762, 139.6503),
        "Sydney, Australia": (-33.8688, 151.2093),
        "Nairobi, Kenya": (-1.2921, 36.8219),
        "Sao Paulo, Brazil": (-23.5505, -46.6333),
        "Tromso, Norway": (69.6496, 18.9560),
    }
    preset = st.selectbox("Quick Presets", list(presets.keys()), index=0,
                          key="bndint_preset",
                          help="Pick a preset or use custom coordinates.")
    if preset != "Custom" and presets[preset] is not None:
        lat, lon = presets[preset]

    st.markdown(f"**Coordinates:** `{lat:.4f}, {lon:.4f}`")

    if st.button("Analyze Boundaries", type="primary", key="bndint_btn"):
        prog = st.progress(0, text="Initializing boundary analysis...")

        prog.progress(5, text="Reverse geocoding location...")
        geocode = _fetch_reverse_geocode(lat, lon)

        prog.progress(20, text="Querying administrative boundaries...")
        admin_els = _fetch_admin_boundaries(lat, lon)

        prog.progress(40, text="Searching nearby settlements...")
        sett_raw = _fetch_nearby_settlements(lat, lon, radius=50000)
        settlements = _process_settlements(sett_raw, lat, lon)

        prog.progress(55, text="Checking border proximity...")
        bways = _fetch_border_ways(lat, lon, radius=100000)
        min_bd, blines = _nearest_border(bways, lat, lon)

        prog.progress(70, text="Retrieving timezone data...")
        tz_data = _fetch_timezone_info(lat, lon)

        prog.progress(85, text="Fetching elevation data...")
        elevation = _fetch_elevation(lat, lon)

        prog.progress(100, text="Analysis complete.")

        admin_rows = _parse_admin_levels(admin_els)

        # --- Render all sections ---
        _render_summary(geocode, admin_rows, settlements,
                        min_bd, tz_data, elevation, lat, lon)

        st.markdown("---")
        _render_geocoding(geocode)
        st.markdown("---")
        _render_admin(admin_els)
        st.markdown("---")
        _render_settlements(settlements)
        st.markdown("---")
        _render_border(min_bd, blines)
        st.markdown("---")
        _render_timezone(tz_data)
        st.markdown("---")
        _render_elevation(elevation)
        st.markdown("---")
        _render_map(lat, lon, settlements, blines)

        # --- Export ---
        st.markdown("---")
        st.markdown("### Export")
        export = {
            "query": {"latitude": lat, "longitude": lon},
            "reverse_geocode": geocode,
            "admin_levels": admin_rows,
            "nearby_settlements_count": len(settlements),
            "nearest_settlement": settlements[0] if settlements else None,
            "nearest_border_km": min_bd,
            "border_segments_found": len(blines),
            "timezone": tz_data.get("timezone") if tz_data else None,
            "utc_offset_seconds": (tz_data.get("utc_offset_seconds")
                                   if tz_data else None),
            "elevation_m": elevation,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        st.download_button(
            label="Download Boundary Report (JSON)",
            data=json.dumps(export, indent=2, default=str),
            file_name=f"boundary_intel_{lat:.4f}_{lon:.4f}.json",
            mime="application/json", key="bndint_download",
        )
