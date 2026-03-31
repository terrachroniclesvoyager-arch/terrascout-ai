"""
Energy & Infrastructure Explorer module for TerraScout AI.
Uses the Overpass API (free) for power infrastructure from OpenStreetMap
and Open-Meteo API (free) for solar radiation and wind speed data.
"""

import io
import math
import json
import html
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ── Constants ────────────────────────────────────────────────────────────────

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

ENERGY_PRESETS = {
    "Custom": None,
    "Texas Wind Belt": {"lat": 32.0, "lon": -100.0, "radius": 25},
    "Sahara Solar": {"lat": 25.0, "lon": 10.0, "radius": 25},
    "North Sea Wind": {"lat": 56.0, "lon": 3.0, "radius": 25},
    "California Solar": {"lat": 35.0, "lon": -118.0, "radius": 20},
    "German Grid": {"lat": 51.0, "lon": 10.0, "radius": 20},
    "China Three Gorges": {"lat": 30.8, "lon": 111.0, "radius": 20},
    "India Solar Belt": {"lat": 26.0, "lon": 73.0, "radius": 25},
    "Brazil Itaipu": {"lat": -25.4, "lon": -54.6, "radius": 15},
}

INFRA_TYPES = {
    "Power Plants": {"color": "#ef4444", "icon": "bolt"},
    "Wind Turbines": {"color": "#06b6d4", "icon": "cloud"},
    "Solar Farms": {"color": "#f59e0b", "icon": "sun-o"},
    "Substations": {"color": "#8b5cf6", "icon": "cogs"},
}

GRID_TYPES = {
    "Transmission Lines": {"color": "#f59e0b", "icon": "minus"},
    "Pipelines": {"color": "#10b981", "icon": "minus"},
    "Power Towers": {"color": "#ef4444", "icon": "bolt"},
}


# ── Cached API helpers ───────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def _search_power_infra(south: float, west: float, north: float, east: float) -> dict:
    """Search power infrastructure via Overpass API."""
    bbox = f"{south},{west},{north},{east}"
    query = f"""
[out:json][timeout:90];
(
  node["power"="plant"]({bbox});
  way["power"="plant"]({bbox});
  relation["power"="plant"]({bbox});
  node["power"="generator"]["generator:source"="wind"]({bbox});
  way["power"="generator"]["generator:source"="wind"]({bbox});
  node["power"="generator"]["generator:source"="solar"]({bbox});
  way["power"="generator"]["generator:source"="solar"]({bbox});
  node["power"="substation"]({bbox});
  way["power"="substation"]({bbox});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"elements": [], "_error": err}
    return result


@st.cache_data(ttl=1800)
def _search_energy_grid(south: float, west: float, north: float, east: float) -> dict:
    """Search energy grid features via Overpass API."""
    bbox = f"{south},{west},{north},{east}"
    query = f"""
[out:json][timeout:90];
(
  way["power"="line"]({bbox});
  way["man_made"="pipeline"]({bbox});
  node["power"="tower"]({bbox});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        err = result.get("_error", "Unknown error") if result else "No response"
        return {"elements": [], "_error": err}
    return result


@st.cache_data(ttl=1800)
def _fetch_renewable_potential(lat: float, lon: float) -> dict:
    """Fetch solar radiation and wind speed from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "direct_radiation,diffuse_radiation,windspeed_10m,windspeed_100m",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"_error": str(e)}


# ── Feature extraction helpers ───────────────────────────────────────────────

def _build_node_lookup(elements: list) -> dict:
    """Build a lookup of node id -> (lat, lon)."""
    lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lookup[el["id"]] = (el["lat"], el["lon"])
    return lookup


def _classify_infra(tags: dict) -> tuple:
    """Classify a power infrastructure element. Returns (category, color)."""
    power = tags.get("power", "")
    source = tags.get("generator:source", "")

    if power == "plant":
        return "Power Plants", INFRA_TYPES["Power Plants"]["color"]
    if power == "generator" and source == "wind":
        return "Wind Turbines", INFRA_TYPES["Wind Turbines"]["color"]
    if power == "generator" and source == "solar":
        return "Solar Farms", INFRA_TYPES["Solar Farms"]["color"]
    if power == "substation":
        return "Substations", INFRA_TYPES["Substations"]["color"]
    return None, None


def _extract_infra_features(data: dict) -> list:
    """Extract power infrastructure features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    seen = set()

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        el_id = el.get("id")
        if el_id in seen:
            continue
        seen.add(el_id)

        category, color = _classify_infra(tags)
        if category is None:
            continue

        lat, lon = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") in ("way", "relation"):
            nodes = el.get("nodes", el.get("members", []))
            if el.get("type") == "way":
                coords = [node_lookup[n] for n in nodes if n in node_lookup]
            else:
                coords = [
                    node_lookup[m.get("ref")]
                    for m in nodes
                    if m.get("type") == "node" and m.get("ref") in node_lookup
                ]
            if coords:
                lat = sum(c[0] for c in coords) / len(coords)
                lon = sum(c[1] for c in coords) / len(coords)

        if lat is None or lon is None:
            continue

        name = tags.get("name", tags.get("name:en", "Unnamed"))
        output_mw = tags.get("plant:output:electricity",
                             tags.get("generator:output:electricity", ""))

        features.append({
            "name": name,
            "category": category,
            "color": color,
            "lat": lat,
            "lon": lon,
            "output": output_mw,
            "tags": tags,
            "osm_id": el_id,
        })

    return features


def _extract_grid_features(data: dict) -> list:
    """Extract grid/pipeline features from Overpass response."""
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    seen = set()

    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        el_id = el.get("id")
        if el_id in seen:
            continue
        seen.add(el_id)

        power = tags.get("power", "")
        man_made = tags.get("man_made", "")

        category, color = None, None
        if power == "line":
            category = "Transmission Lines"
            color = GRID_TYPES["Transmission Lines"]["color"]
        elif man_made == "pipeline":
            category = "Pipelines"
            color = GRID_TYPES["Pipelines"]["color"]
        elif power == "tower":
            category = "Power Towers"
            color = GRID_TYPES["Power Towers"]["color"]

        if category is None:
            continue

        lat, lon = None, None
        coords_list = []

        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat, lon = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords_list = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords_list:
                lat = sum(c[0] for c in coords_list) / len(coords_list)
                lon = sum(c[1] for c in coords_list) / len(coords_list)

        if lat is None or lon is None:
            continue

        name = tags.get("name", tags.get("name:en", "Unnamed"))
        voltage = tags.get("voltage", "")

        features.append({
            "name": name,
            "category": category,
            "color": color,
            "lat": lat,
            "lon": lon,
            "coords": coords_list,
            "voltage": voltage,
            "tags": tags,
            "osm_id": el_id,
        })

    return features


# ── Chart helpers ────────────────────────────────────────────────────────────

def _dark_fig(rows=1, cols=1, figsize=(10, 4)):
    """Create a matplotlib figure with the dark TerraScout theme."""
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    if rows == 1 and cols == 1:
        axes = [axes]
    elif rows > 1 or cols > 1:
        axes = axes.flat if hasattr(axes, "flat") else [axes]
    for ax in axes:
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#8b97b0", labelsize=8)
        ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")
    return fig, axes


# ── Bbox helper ──────────────────────────────────────────────────────────────

def _bbox_from_center(lat: float, lon: float, radius_km: float):
    """Return (south, west, north, east) bounding box."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def render_energy_explorer_tab():
    """Main render function for the Energy & Infrastructure Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Energy &amp; Infrastructure Explorer</h4>
        <p>Discover power plants, wind turbines, solar farms, transmission grids, and assess renewable energy potential using OpenStreetMap and Open-Meteo data.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.radio(
        "Exploration Mode",
        ["Power Infrastructure", "Renewable Potential", "Energy Grid"],
        horizontal=True,
        key="energy_mode",
    )

    # ── Location controls ──
    st.markdown("#### Location")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        en_lat = st.number_input("Latitude", value=32.0, format="%.4f",
                                  min_value=-90.0, max_value=90.0, key="energy_lat")
    with col2:
        en_lon = st.number_input("Longitude", value=-100.0, format="%.4f",
                                  min_value=-180.0, max_value=180.0, key="energy_lon")
    with col3:
        en_radius = st.slider("Search Radius (km)", 5, 50, 20, key="energy_radius")

    preset_name = st.selectbox("Location Presets", list(ENERGY_PRESETS.keys()),
                                key="energy_preset")
    if preset_name != "Custom" and ENERGY_PRESETS.get(preset_name):
        p = ENERGY_PRESETS[preset_name]
        en_lat = p["lat"]
        en_lon = p["lon"]
        en_radius = p["radius"]

    # ── Dispatch to mode ──
    if mode == "Power Infrastructure":
        _render_power_infrastructure(en_lat, en_lon, en_radius)
    elif mode == "Renewable Potential":
        _render_renewable_potential(en_lat, en_lon)
    else:
        _render_energy_grid(en_lat, en_lon, en_radius)


# ══════════════════════════════════════════════════════════════════════════════
# MODE 1: Power Infrastructure
# ══════════════════════════════════════════════════════════════════════════════

def _render_power_infrastructure(lat: float, lon: float, radius_km: int):
    """Search and display power plants, wind turbines, solar farms, substations."""

    if st.button("Search Power Infrastructure", key="energy_infra_btn", width="stretch"):
        south, west, north, east = _bbox_from_center(lat, lon, radius_km)
        st.session_state.energy_infra_params = {
            "lat": lat, "lon": lon, "radius": radius_km,
            "south": south, "west": west, "north": north, "east": east,
        }

    if "energy_infra_params" not in st.session_state:
        st.info("Select a location and click Search to discover power infrastructure.")
        return

    ep = st.session_state.energy_infra_params

    with st.spinner("Searching power infrastructure via OpenStreetMap..."):
        data = _search_power_infra(ep["south"], ep["west"], ep["north"], ep["east"])

    if data.get("_error"):
        st.error(f"Overpass API error: {data['_error']}")
        return

    features = _extract_infra_features(data)

    if not features:
        st.warning("No power infrastructure found. Try a larger radius or different location.")
        return

    # ── Stats ──
    st.markdown("---")
    cat_counts = {}
    for f in features:
        cat_counts[f["category"]] = cat_counts.get(f["category"], 0) + 1

    stat_cols = st.columns(min(len(cat_counts) + 1, 5))
    stat_cols[0].metric("Total Features", len(features))
    for i, (cat, count) in enumerate(sorted(cat_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(stat_cols):
            stat_cols[i + 1].metric(cat, count)

    # ── Legend ──
    legend_items = " ".join([
        f'<span style="color:{INFRA_TYPES[c]["color"]}; font-size:0.8rem;">'
        f'&#9679; {html.escape(c)}</span>'
        for c in cat_counts.keys() if c in INFRA_TYPES
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # ── Map ──
    m = folium.Map(location=[ep["lat"], ep["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.Circle(
        location=[ep["lat"], ep["lon"]],
        radius=ep["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.04, weight=1,
    ).add_to(m)

    cluster = MarkerCluster(name="Infrastructure").add_to(m)

    for f in features:
        safe_name = html.escape(f["name"])
        safe_cat = html.escape(f["category"])
        safe_output = html.escape(str(f["output"])) if f["output"] else ""
        output_line = f"<br/>Output: {safe_output}" if safe_output else ""
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="font-size:0.85rem;">{safe_cat}</span>'
            f'{output_line}</div>'
        )

        folium.CircleMarker(
            location=[f["lat"], f["lon"]],
            radius=7,
            color=f["color"],
            fill=True,
            fill_color=f["color"],
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(cluster)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # ── Chart + list ──
    st.markdown("---")
    col_chart, col_list = st.columns([1, 1])

    with col_chart:
        st.markdown("#### Distribution")
        if cat_counts:
            fig, axes = _dark_fig(figsize=(6, 3.5))
            ax = axes[0]
            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            colors = [INFRA_TYPES.get(c, {}).get("color", "#8b97b0") for c in cats]
            ax.barh(range(len(cats)), counts, color=colors, alpha=0.85)
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels([c[:20] for c in cats], color="#8b97b0", fontsize=9)
            ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    with col_list:
        st.markdown("#### Named Facilities")
        named = [f for f in features if f["name"] != "Unnamed"][:20]
        if named:
            for f in named:
                safe = html.escape(f["name"])
                safe_out = html.escape(str(f["output"])) if f["output"] else ""
                st.markdown(
                    f'<div style="display:flex; align-items:center; margin-bottom:0.4rem;">'
                    f'<div style="width:10px; height:36px; border-radius:5px; '
                    f'background:{f["color"]}; margin-right:0.7rem; flex-shrink:0;"></div>'
                    f'<div>'
                    f'<div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{safe}</div>'
                    f'<div style="color:#8b97b0; font-size:0.75rem;">'
                    f'{html.escape(f["category"])}'
                    f'{" | " + safe_out if safe_out else ""}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No named facilities found in this area.")

    # ── Data table + download ──
    st.markdown("---")
    rows = []
    for f in features:
        rows.append({
            "name": f["name"],
            "category": f["category"],
            "latitude": round(f["lat"], 5),
            "longitude": round(f["lon"], 5),
            "output": f["output"],
            "osm_id": f["osm_id"],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    col_csv, col_geo = st.columns(2)
    with col_csv:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download CSV ({len(rows)} features)",
            data=csv_buf.getvalue(),
            file_name="energy_infrastructure.csv",
            mime="text/csv",
            key="energy_infra_csv",
        )
    with col_geo:
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point",
                                 "coordinates": [f["lon"], f["lat"]]},
                    "properties": {
                        "name": f["name"],
                        "category": f["category"],
                        "output": f["output"],
                    },
                }
                for f in features
            ],
        }
        st.download_button(
            "Download GeoJSON",
            data=json.dumps(geojson, indent=2),
            file_name="energy_infrastructure.geojson",
            mime="application/geo+json",
            key="energy_infra_geojson",
        )


# ══════════════════════════════════════════════════════════════════════════════
# MODE 2: Renewable Potential
# ══════════════════════════════════════════════════════════════════════════════

def _render_renewable_potential(lat: float, lon: float):
    """Fetch and display solar radiation and wind speed data."""

    if st.button("Assess Renewable Potential", key="energy_renew_btn", width="stretch"):
        st.session_state.energy_renew_params = {"lat": lat, "lon": lon}

    if "energy_renew_params" not in st.session_state:
        st.info("Select a location and click Assess to view solar and wind energy potential.")
        return

    rp = st.session_state.energy_renew_params

    with st.spinner("Fetching solar and wind data from Open-Meteo..."):
        weather = _fetch_renewable_potential(rp["lat"], rp["lon"])

    if weather.get("_error"):
        st.error(f"Open-Meteo API error: {weather['_error']}")
        return

    hourly = weather.get("hourly", {})
    times = hourly.get("time", [])
    direct_rad = hourly.get("direct_radiation", [])
    diffuse_rad = hourly.get("diffuse_radiation", [])
    wind_10m = hourly.get("windspeed_10m", [])
    wind_100m = hourly.get("windspeed_100m", [])

    if not times:
        st.warning("No data returned from Open-Meteo. Try a different location.")
        return

    # ── Calculate summary stats ──
    total_rad = [d + f for d, f in zip(direct_rad, diffuse_rad)]
    avg_solar = sum(total_rad) / len(total_rad) if total_rad else 0
    peak_solar = max(total_rad) if total_rad else 0
    avg_wind_10 = sum(wind_10m) / len(wind_10m) if wind_10m else 0
    avg_wind_100 = sum(wind_100m) / len(wind_100m) if wind_100m else 0
    peak_wind = max(wind_100m) if wind_100m else 0

    # Simple potential estimates
    # Solar: assume 20% panel efficiency, 1 m^2 panel
    solar_kwh_day = (avg_solar * 24 / 1000) * 0.20
    # Wind: P = 0.5 * rho * A * v^3, assume 1.225 kg/m^3, 35% capacity factor
    wind_power_w = (0.5 * 1.225 * 1.0 * (avg_wind_100 ** 3) * 0.35
                    if avg_wind_100 > 0 else 0)

    # ── Stats row ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Avg Solar Irradiance", f"{avg_solar:.0f} W/m\u00b2")
    with c2:
        st.metric("Peak Solar", f"{peak_solar:.0f} W/m\u00b2")
    with c3:
        st.metric("Avg Wind (100m)", f"{avg_wind_100:.1f} m/s")
    with c4:
        st.metric("Peak Wind (100m)", f"{peak_wind:.1f} m/s")

    st.markdown("---")
    c5, c6 = st.columns(2)
    with c5:
        st.metric("Est. Solar Yield", f"{solar_kwh_day:.2f} kWh/m\u00b2/day",
                   help="Assumes 20% panel efficiency")
    with c6:
        st.metric("Est. Wind Power Density", f"{wind_power_w:.1f} W/m\u00b2",
                   help="At 100m hub height, 35% capacity factor")

    # ── Charts ──
    st.markdown("---")
    st.markdown("#### Solar Irradiance & Wind Speed (7-Day Forecast)")

    short_times = [t[5:13] for t in times]

    fig, axes = _dark_fig(rows=1, cols=2, figsize=(12, 4))
    ax_sol, ax_wind = axes[0], axes[1]

    # Solar chart
    ax_sol.fill_between(range(len(total_rad)), total_rad,
                        color="#f59e0b", alpha=0.3)
    ax_sol.plot(range(len(direct_rad)), direct_rad, color="#f59e0b",
                linewidth=1.2, label="Direct", alpha=0.9)
    ax_sol.plot(range(len(diffuse_rad)), diffuse_rad, color="#fbbf24",
                linewidth=1.0, label="Diffuse", alpha=0.7)
    ax_sol.set_ylabel("W/m\u00b2", color="#8b97b0", fontsize=9)
    ax_sol.set_title("Solar Radiation", color="#e8ecf4", fontsize=11,
                     fontweight="bold")
    ax_sol.legend(fontsize=7, facecolor="#111827", edgecolor="#2a3550",
                  labelcolor="#8b97b0")

    step = max(1, len(short_times) // 8)
    tick_pos = list(range(0, len(short_times), step))
    ax_sol.set_xticks(tick_pos)
    ax_sol.set_xticklabels([short_times[i] for i in tick_pos], rotation=45,
                            ha="right", fontsize=7, color="#5a6580")

    # Wind chart
    ax_wind.plot(range(len(wind_10m)), wind_10m, color="#06b6d4",
                 linewidth=1.2, label="10m", alpha=0.8)
    ax_wind.plot(range(len(wind_100m)), wind_100m, color="#3b82f6",
                 linewidth=1.2, label="100m", alpha=0.9)
    ax_wind.fill_between(range(len(wind_100m)), wind_100m,
                         color="#3b82f6", alpha=0.2)
    ax_wind.set_ylabel("m/s", color="#8b97b0", fontsize=9)
    ax_wind.set_title("Wind Speed", color="#e8ecf4", fontsize=11,
                      fontweight="bold")
    ax_wind.legend(fontsize=7, facecolor="#111827", edgecolor="#2a3550",
                   labelcolor="#8b97b0")
    ax_wind.set_xticks(tick_pos)
    ax_wind.set_xticklabels([short_times[i] for i in tick_pos], rotation=45,
                             ha="right", fontsize=7, color="#5a6580")

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Daily aggregation chart ──
    st.markdown("#### Daily Averages")
    n_days = min(7, len(times) // 24)
    if n_days > 0:
        day_labels, daily_solar, daily_wind10, daily_wind100 = [], [], [], []

        for d in range(n_days):
            s, e = d * 24, d * 24 + 24
            day_labels.append(times[s][:10])
            daily_solar.append(sum(total_rad[s:e]) / 24)
            daily_wind10.append(sum(wind_10m[s:e]) / 24)
            daily_wind100.append(sum(wind_100m[s:e]) / 24)

        fig2, axes2 = _dark_fig(rows=1, cols=2, figsize=(10, 3.5))
        ax_ds, ax_dw = axes2[0], axes2[1]

        ax_ds.bar(range(n_days), daily_solar, color="#f59e0b", alpha=0.85)
        ax_ds.set_xticks(range(n_days))
        ax_ds.set_xticklabels([dl[5:] for dl in day_labels],
                               color="#8b97b0", fontsize=8)
        ax_ds.set_ylabel("Avg W/m\u00b2", color="#8b97b0", fontsize=9)
        ax_ds.set_title("Daily Solar Avg", color="#e8ecf4", fontsize=10,
                        fontweight="bold")

        width = 0.35
        ax_dw.bar([p - width / 2 for p in range(n_days)], daily_wind10, width,
                   color="#06b6d4", alpha=0.85, label="10m")
        ax_dw.bar([p + width / 2 for p in range(n_days)], daily_wind100, width,
                   color="#3b82f6", alpha=0.85, label="100m")
        ax_dw.set_xticks(range(n_days))
        ax_dw.set_xticklabels([dl[5:] for dl in day_labels],
                               color="#8b97b0", fontsize=8)
        ax_dw.set_ylabel("Avg m/s", color="#8b97b0", fontsize=9)
        ax_dw.set_title("Daily Wind Avg", color="#e8ecf4", fontsize=10,
                        fontweight="bold")
        ax_dw.legend(fontsize=7, facecolor="#111827", edgecolor="#2a3550",
                     labelcolor="#8b97b0")

        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Download data ──
    st.markdown("---")
    df_renew = pd.DataFrame({
        "time": times,
        "direct_radiation_wm2": direct_rad,
        "diffuse_radiation_wm2": diffuse_rad,
        "total_radiation_wm2": total_rad,
        "windspeed_10m_ms": wind_10m,
        "windspeed_100m_ms": wind_100m,
    })

    with st.expander(f"Raw Data ({len(df_renew)} hourly records)", expanded=False):
        st.dataframe(df_renew, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df_renew.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download Renewable Data CSV ({len(df_renew)} rows)",
        data=csv_buf.getvalue(),
        file_name="renewable_potential.csv",
        mime="text/csv",
        key="energy_renew_csv",
    )


# ══════════════════════════════════════════════════════════════════════════════
# MODE 3: Energy Grid
# ══════════════════════════════════════════════════════════════════════════════

def _render_energy_grid(lat: float, lon: float, radius_km: int):
    """Search and display transmission lines, pipelines, and power towers."""

    if st.button("Search Energy Grid", key="energy_grid_btn", width="stretch"):
        south, west, north, east = _bbox_from_center(lat, lon, radius_km)
        st.session_state.energy_grid_params = {
            "lat": lat, "lon": lon, "radius": radius_km,
            "south": south, "west": west, "north": north, "east": east,
        }

    if "energy_grid_params" not in st.session_state:
        st.info("Select a location and click Search to explore the energy grid.")
        return

    gp = st.session_state.energy_grid_params

    with st.spinner("Searching energy grid via OpenStreetMap..."):
        data = _search_energy_grid(gp["south"], gp["west"], gp["north"], gp["east"])

    if data.get("_error"):
        st.error(f"Overpass API error: {data['_error']}")
        return

    features = _extract_grid_features(data)

    if not features:
        st.warning("No energy grid features found. Try a larger radius or different location.")
        return

    # ── Stats ──
    st.markdown("---")
    cat_counts = {}
    for f in features:
        cat_counts[f["category"]] = cat_counts.get(f["category"], 0) + 1

    stat_cols = st.columns(min(len(cat_counts) + 1, 4))
    stat_cols[0].metric("Total Features", len(features))
    for i, (cat, count) in enumerate(sorted(cat_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(stat_cols):
            stat_cols[i + 1].metric(cat, count)

    # ── Legend ──
    legend_items = " ".join([
        f'<span style="color:{GRID_TYPES[c]["color"]}; font-size:0.8rem;">'
        f'&#9679; {html.escape(c)}</span>'
        for c in cat_counts.keys() if c in GRID_TYPES
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin:0.5rem 0;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # ── Map ──
    m = folium.Map(location=[gp["lat"], gp["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.Circle(
        location=[gp["lat"], gp["lon"]],
        radius=gp["radius"] * 1000,
        color="#06b6d4", fill=True, fill_opacity=0.04, weight=1,
    ).add_to(m)

    tower_cluster = MarkerCluster(name="Power Towers").add_to(m)

    for f in features:
        safe_name = html.escape(f["name"])
        safe_cat = html.escape(f["category"])
        safe_voltage = html.escape(str(f["voltage"])) if f["voltage"] else ""
        voltage_line = f"<br/>Voltage: {safe_voltage}" if safe_voltage else ""
        popup_html = (
            f'<div style="max-width:220px;">'
            f'<strong>{safe_name}</strong><br/>'
            f'<span style="font-size:0.85rem;">{safe_cat}</span>'
            f'{voltage_line}</div>'
        )

        if f["coords"] and f["category"] in ("Transmission Lines", "Pipelines"):
            folium.PolyLine(
                locations=[(c[0], c[1]) for c in f["coords"]],
                color=f["color"],
                weight=2 if f["category"] == "Pipelines" else 3,
                opacity=0.75,
                popup=folium.Popup(popup_html, max_width=240),
            ).add_to(m)
        elif f["category"] == "Power Towers":
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=3,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(popup_html, max_width=200),
            ).add_to(tower_cluster)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=5,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)

    # ── Chart ──
    st.markdown("---")
    col_chart, col_details = st.columns([1, 1])

    with col_chart:
        st.markdown("#### Grid Composition")
        if cat_counts:
            fig, axes = _dark_fig(figsize=(6, 3.5))
            ax = axes[0]
            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            colors = [GRID_TYPES.get(c, {}).get("color", "#8b97b0") for c in cats]
            ax.barh(range(len(cats)), counts, color=colors, alpha=0.85)
            ax.set_yticks(range(len(cats)))
            ax.set_yticklabels([c[:22] for c in cats], color="#8b97b0", fontsize=9)
            ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
            ax.invert_yaxis()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    with col_details:
        st.markdown("#### Voltage Summary")
        voltage_feats = [f for f in features if f["voltage"]]
        if voltage_feats:
            voltages = {}
            for f in voltage_feats:
                v = f["voltage"]
                voltages[v] = voltages.get(v, 0) + 1
            for v, cnt in sorted(voltages.items(), key=lambda x: -x[1])[:15]:
                safe_v = html.escape(str(v))
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; '
                    f'padding:0.25rem 0; border-bottom:1px solid #2a3550;">'
                    f'<span style="color:#e8ecf4; font-size:0.85rem;">'
                    f'{safe_v} V</span>'
                    f'<span style="color:#f59e0b; font-weight:600;">{cnt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No voltage data available for features in this area.")

    # ── Data table + download ──
    st.markdown("---")
    rows = []
    for f in features:
        rows.append({
            "name": f["name"],
            "category": f["category"],
            "latitude": round(f["lat"], 5),
            "longitude": round(f["lon"], 5),
            "voltage": f["voltage"],
            "osm_id": f["osm_id"],
        })
    df = pd.DataFrame(rows)

    with st.expander(f"Full Data Table ({len(df)} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    col_csv, col_geo = st.columns(2)
    with col_csv:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download CSV ({len(rows)} features)",
            data=csv_buf.getvalue(),
            file_name="energy_grid.csv",
            mime="text/csv",
            key="energy_grid_csv",
        )
    with col_geo:
        geo_features = []
        for f in features:
            if f["coords"] and len(f["coords"]) >= 2:
                geom = {
                    "type": "LineString",
                    "coordinates": [[c[1], c[0]] for c in f["coords"]],
                }
            else:
                geom = {
                    "type": "Point",
                    "coordinates": [f["lon"], f["lat"]],
                }
            geo_features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "name": f["name"],
                    "category": f["category"],
                    "voltage": f["voltage"],
                },
            })
        geojson = {"type": "FeatureCollection", "features": geo_features}
        st.download_button(
            "Download GeoJSON",
            data=json.dumps(geojson, indent=2),
            file_name="energy_grid.geojson",
            mime="application/geo+json",
            key="energy_grid_geojson",
        )
