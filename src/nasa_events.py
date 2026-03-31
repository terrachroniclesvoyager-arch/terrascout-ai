"""
NASA Earth Events module for TerraScout AI.
Real-time natural events from NASA EONET with satellite imagery layers.
"""
import logging
import json
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from html import escape

logger = logging.getLogger(__name__)

# EONET category mapping: display name -> API id
CATEGORY_MAP = {
    "Wildfires": "wildfires",
    "Volcanoes": "volcanoes",
    "Severe Storms": "severeStorms",
    "Sea and Lake Ice": "seaLakeIce",
    "Icebergs": "icebergs",
    "Floods": "floods",
    "Earthquakes": "earthquakes",
    "Drought": "drought",
    "Dust and Haze": "dustHaze",
    "Snow": "snow",
    "Temperature Extremes": "tempExtremes",
    "Water Color": "waterColor",
}

# Color per category for map markers
CATEGORY_COLORS = {
    "Wildfires": "#ef4444",
    "Volcanoes": "#f97316",
    "Severe Storms": "#8b5cf6",
    "Sea and Lake Ice": "#38bdf8",
    "Icebergs": "#06b6d4",
    "Floods": "#3b82f6",
    "Earthquakes": "#f59e0b",
    "Drought": "#a3e635",
    "Dust and Haze": "#d4a06b",
    "Snow": "#e2e8f0",
    "Temperature Extremes": "#fb923c",
    "Water Color": "#22d3ee",
}

DEFAULT_COLOR = "#10b981"

EONET_BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"


@st.cache_data(ttl=600)
def fetch_eonet_events(categories: list, days: int, status: str, limit: int) -> dict:
    """Fetch natural events from NASA EONET v3 API."""
    try:
        params = {"limit": limit, "days": days}

        if status.lower() in ("open", "closed"):
            params["status"] = status.lower()

        if categories:
            cat_ids = [CATEGORY_MAP[c] for c in categories if c in CATEGORY_MAP]
            if cat_ids:
                params["category"] = ",".join(cat_ids)

        logger.info(f"Fetching EONET events: {params}")
        response = requests.get(EONET_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {"success": True, "events": data.get("events", []), "title": data.get("title", "")}
    except requests.exceptions.Timeout:
        logger.error("EONET API request timed out")
        return {"success": False, "error": "Request timed out. NASA EONET may be slow — try again."}
    except requests.exceptions.ConnectionError:
        logger.error("EONET API connection error")
        return {"success": False, "error": "Could not connect to NASA EONET API."}
    except requests.exceptions.HTTPError as e:
        logger.error(f"EONET API HTTP error: {e}")
        return {"success": False, "error": f"HTTP error: {e}"}
    except Exception as e:
        logger.error(f"EONET API error: {e}")
        return {"success": False, "error": str(e)}


def _parse_events(events: list) -> list:
    """Parse raw EONET events into flat records with coordinates."""
    records = []
    for ev in events:
        title = ev.get("title", "Unknown")
        event_id = ev.get("id", "")
        categories = ev.get("categories", [])
        cat_name = categories[0].get("title", "Unknown") if categories else "Unknown"

        sources = ev.get("sources", [])
        source_links = []
        for src in sources:
            sid = src.get("id", "")
            url = src.get("url", "")
            if url:
                source_links.append({"id": sid, "url": url})

        geometries = ev.get("geometry", [])
        if not geometries:
            continue

        # Use the most recent geometry entry
        latest_geom = geometries[-1]
        date_str = latest_geom.get("date", "")
        coords = latest_geom.get("coordinates", [])
        geom_type = latest_geom.get("type", "Point")

        if geom_type == "Point" and len(coords) >= 2:
            lon, lat = coords[0], coords[1]
        elif geom_type == "Polygon" and coords:
            # Use centroid of first ring
            ring = coords[0] if isinstance(coords[0], list) else coords
            if ring and isinstance(ring[0], list):
                lons = [p[0] for p in ring]
                lats = [p[1] for p in ring]
                lon = sum(lons) / len(lons)
                lat = sum(lats) / len(lats)
            else:
                continue
        else:
            continue

        # Parse date
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_display = dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            date_display = date_str

        records.append({
            "id": event_id,
            "title": title,
            "category": cat_name,
            "date": date_display,
            "date_raw": date_str,
            "lat": lat,
            "lon": lon,
            "sources": source_links,
            "sources_str": ", ".join(s["id"] for s in source_links),
            "geometry_type": geom_type,
        })

    return records


def _get_category_color(category_name: str) -> str:
    """Return marker color for a given category name."""
    for display_name, color in CATEGORY_COLORS.items():
        if display_name.lower() == category_name.lower():
            return color
    return DEFAULT_COLOR


def _build_popup_html(record: dict) -> str:
    """Build HTML popup content for a map marker."""
    title = escape(record["title"])
    category = escape(record["category"])
    date = escape(record["date"])
    lat = record["lat"]
    lon = record["lon"]

    sources_html = ""
    for src in record["sources"]:
        sid = escape(src["id"])
        url = escape(src["url"])
        sources_html += f'<a href="{url}" target="_blank" style="color:#06b6d4;">{sid}</a> '

    if not sources_html:
        sources_html = '<span style="color:#5a6580;">None</span>'

    color = _get_category_color(record["category"])

    html = f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;min-width:220px;max-width:300px;
                background:#1a2235;color:#e8ecf4;padding:12px;border-radius:8px;
                border:1px solid #2a3550;">
        <div style="font-size:13px;font-weight:600;margin-bottom:6px;">{title}</div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                         background:{color};"></span>
            <span style="font-size:11px;color:#8b97b0;">{category}</span>
        </div>
        <div style="font-size:11px;color:#8b97b0;margin-bottom:4px;">
            Date: {date}
        </div>
        <div style="font-size:11px;color:#8b97b0;margin-bottom:4px;">
            Coords: {lat:.4f}, {lon:.4f}
        </div>
        <div style="font-size:11px;color:#8b97b0;">
            Sources: {sources_html}
        </div>
    </div>
    """
    return html


def _build_geojson(records: list) -> dict:
    """Build a GeoJSON FeatureCollection from parsed event records."""
    features = []
    for rec in records:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [rec["lon"], rec["lat"]],
            },
            "properties": {
                "id": rec["id"],
                "title": rec["title"],
                "category": rec["category"],
                "date": rec["date"],
                "sources": rec["sources_str"],
            },
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def render_nasa_events_tab():
    """Main render function for the NASA Earth Events tab."""
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium

    # --- Tab Header ---
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>NASA Earth Events</h4>"
        "<p>Real-time natural events from NASA EONET — wildfires, volcanoes, storms, "
        "floods, icebergs, and more with satellite imagery layers.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # --- Controls ---
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        selected_categories = st.multiselect(
            "Category Filter",
            options=list(CATEGORY_MAP.keys()),
            default=[],
            placeholder="All categories",
            key="nasa_events_categories",
        )

    with col2:
        days_back = st.slider(
            "Days Back",
            min_value=1,
            max_value=365,
            value=30,
            key="nasa_events_days",
        )

    with col3:
        status_option = st.radio(
            "Status",
            options=["Open", "Closed", "All"],
            index=0,
            key="nasa_events_status",
        )

    with col4:
        event_limit = st.slider(
            "Limit",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="nasa_events_limit",
        )

    # GIBS overlay toggle
    show_gibs = st.checkbox(
        "Show NASA GIBS MODIS True Color overlay",
        value=False,
        key="nasa_events_gibs",
    )

    # --- Fetch ---
    fetch_clicked = st.button(
        "Fetch NASA Events",
        type="primary",
        key="nasa_events_fetch",
    )

    if fetch_clicked:
        with st.spinner("Fetching events from NASA EONET..."):
            result = fetch_eonet_events(
                categories=selected_categories,
                days=days_back,
                status=status_option,
                limit=event_limit,
            )
            st.session_state["nasa_events_result"] = result

    result = st.session_state.get("nasa_events_result")
    if not result:
        st.info("Configure filters above and click **Fetch NASA Events** to load data.")
        return

    if not result.get("success"):
        st.error(f"Failed to fetch events: {result.get('error', 'Unknown error')}")
        return

    raw_events = result.get("events", [])
    if not raw_events:
        st.warning("No events found for the selected filters. Try broadening your search.")
        return

    records = _parse_events(raw_events)

    if not records:
        st.warning("No events with valid coordinates found.")
        return

    # --- Stats Row ---
    unique_categories = set(r["category"] for r in records)
    all_sources = set()
    for r in records:
        for s in r["sources"]:
            all_sources.add(s["id"])

    # Most recent date
    dates_raw = [r["date_raw"] for r in records if r["date_raw"]]
    most_recent = ""
    if dates_raw:
        try:
            sorted_dates = sorted(dates_raw, reverse=True)
            dt = datetime.fromisoformat(sorted_dates[0].replace("Z", "+00:00"))
            most_recent = dt.strftime("%Y-%m-%d")
        except Exception:
            most_recent = "N/A"

    st1, st2, st3, st4 = st.columns(4)
    st1.metric("Total Events", len(records))
    st2.metric("Categories Active", len(unique_categories))
    st3.metric("Most Recent", most_recent)
    st4.metric("Sources", len(all_sources))

    # --- Category Legend ---
    legend_items = []
    for cat in sorted(unique_categories):
        color = _get_category_color(cat)
        count = sum(1 for r in records if r["category"] == cat)
        legend_items.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;">'
            f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
            f'background:{color};"></span>'
            f'<span style="font-size:12px;color:#8b97b0;">{escape(cat)} ({count})</span></span>'
        )
    if legend_items:
        st.markdown(
            '<div style="padding:8px 0;">' + "".join(legend_items) + "</div>",
            unsafe_allow_html=True,
        )

    # --- Folium Map ---
    # Compute center and bounds
    lats = [r["lat"] for r in records]
    lons = [r["lon"] for r in records]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Optional NASA GIBS MODIS True Color overlay
    if show_gibs:
        today = datetime.utcnow()
        gibs_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        gibs_url = (
            "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            "MODIS_Terra_CorrectedReflectance_TrueColor/default/"
            f"{gibs_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
        )
        folium.TileLayer(
            tiles=gibs_url,
            attr="NASA GIBS MODIS True Color",
            name="MODIS True Color",
            overlay=True,
            control=True,
            opacity=0.6,
        ).add_to(m)

    # MarkerCluster for dense areas
    marker_cluster = MarkerCluster(
        name="Events",
        options={
            "maxClusterRadius": 40,
            "spiderfyOnMaxZoom": True,
            "showCoverageOnHover": False,
        },
    ).add_to(m)

    # Add markers
    for rec in records:
        color = _get_category_color(rec["category"])
        popup_html = _build_popup_html(rec)

        folium.CircleMarker(
            location=[rec["lat"], rec["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(rec["title"]),
        ).add_to(marker_cluster)

    # Fit bounds
    if len(records) > 1:
        sw = [min(lats), min(lons)]
        ne = [max(lats), max(lons)]
        m.fit_bounds([sw, ne], padding=[30, 30])

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    st_folium(m, height=500, width=None, returned_objects=[], key="nasae_folium_map")

    # --- Data Table ---
    st.markdown("#### Event Data")
    df = pd.DataFrame(
        [
            {
                "Title": r["title"],
                "Category": r["category"],
                "Date": r["date"],
                "Lat": round(r["lat"], 4),
                "Lon": round(r["lon"], 4),
                "Sources": r["sources_str"],
            }
            for r in records
        ]
    )

    st.dataframe(df, width="stretch", hide_index=True)

    # --- Downloads ---
    st.markdown("#### Download")
    dl1, dl2, _ = st.columns([1, 1, 3])

    with dl1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="nasa_eonet_events.csv",
            mime="text/csv",
            key="nasa_events_csv_dl",
        )

    with dl2:
        geojson_data = json.dumps(_build_geojson(records), indent=2).encode("utf-8")
        st.download_button(
            label="Download GeoJSON",
            data=geojson_data,
            file_name="nasa_eonet_events.geojson",
            mime="application/geo+json",
            key="nasa_events_geojson_dl",
        )
