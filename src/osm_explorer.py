"""
OSM Explorer - Streamlit tab module for querying OpenStreetMap via Overpass API.

Provides interactive map-based bounding box selection and category-based
feature querying from OpenStreetMap data.
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import io
import csv
import logging

logger = logging.getLogger(__name__)

# ─── OVERPASS API ───
from src.overpass_client import query_overpass as _overpass_query

# ─── CATEGORIES: display name -> Overpass tag ───
CATEGORIES = {
    "Buildings": '"building"',
    "Roads": '"highway"',
    "Restaurants": '"amenity"="restaurant"',
    "Parks": '"leisure"="park"',
    "Hospitals": '"amenity"="hospital"',
    "Schools": '"amenity"="school"',
    "Water": '"natural"="water"',
    "Shops": '"shop"',
    "Public Transport": '"public_transport"="station"',
    "Parking": '"amenity"="parking"',
}


def build_overpass_query(bbox, category):
    """
    Builds an Overpass QL query for nodes, ways, and relations within a bounding box.

    Args:
        bbox: tuple/list of (south, west, north, east) in WGS84
        category: display name string from CATEGORIES dict

    Returns:
        Overpass QL query string
    """
    tag = CATEGORIES.get(category, '"building"')
    south, west, north, east = bbox

    query = f"""
[out:json][timeout:60];
(
  node[{tag}]({south},{west},{north},{east});
  way[{tag}]({south},{west},{north},{east});
  relation[{tag}]({south},{west},{north},{east});
);
out body;
>;
out skel qt;
"""
    return query.strip()


@st.cache_data(ttl=300)
def query_overpass(query):
    """
    POSTs an Overpass QL query with automatic server failover.

    Args:
        query: Overpass QL query string

    Returns:
        dict with Overpass JSON response, or None on error
    """
    result = _overpass_query(query)
    if result is None:
        st.error("All Overpass servers unreachable. Check your internet connection.")
        return None
    if "_error" in result:
        st.error(f"All Overpass servers failed: {result['_error']}. Try a smaller area or retry later.")
        return None
    return result


def overpass_to_geojson(data):
    """
    Converts Overpass API JSON elements to a GeoJSON FeatureCollection.

    Handles:
    - Nodes as Point geometries
    - Ways with geometry as LineString or Polygon (closed ways become Polygons)

    Args:
        data: Overpass JSON response dict

    Returns:
        GeoJSON FeatureCollection dict
    """
    if not data or "elements" not in data:
        return {"type": "FeatureCollection", "features": []}

    elements = data["elements"]

    # Build a lookup of node id -> (lat, lon) for resolving way references
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []

    for el in elements:
        el_type = el.get("type")
        tags = el.get("tags", {})
        properties = {
            "id": el.get("id"),
            "type": el_type,
        }
        properties.update(tags)

        geometry = None

        if el_type == "node" and "lat" in el and "lon" in el:
            # Only include nodes that have tags (actual features, not just reference nodes)
            if tags:
                geometry = {
                    "type": "Point",
                    "coordinates": [el["lon"], el["lat"]]
                }

        elif el_type == "way":
            # Resolve node references to coordinates
            node_refs = el.get("nodes", [])
            coords = []
            for nid in node_refs:
                if nid in node_lookup:
                    lat, lon = node_lookup[nid]
                    coords.append([lon, lat])

            if len(coords) >= 2:
                # Check if way is closed (polygon) or open (linestring)
                if len(coords) >= 4 and coords[0] == coords[-1]:
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [coords]
                    }
                else:
                    geometry = {
                        "type": "LineString",
                        "coordinates": coords
                    }

        elif el_type == "relation" and tags:
            # Relations are complex; include as a tagged point at centroid if members have coords
            # This is a simplified approach - full relation geometry requires more logic
            member_coords = []
            for member in el.get("members", []):
                if member.get("type") == "node" and member.get("ref") in node_lookup:
                    lat, lon = node_lookup[member["ref"]]
                    member_coords.append([lon, lat])

            if member_coords:
                avg_lon = sum(c[0] for c in member_coords) / len(member_coords)
                avg_lat = sum(c[1] for c in member_coords) / len(member_coords)
                geometry = {
                    "type": "Point",
                    "coordinates": [avg_lon, avg_lat]
                }

        if geometry:
            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            })

    return {"type": "FeatureCollection", "features": features}


def compute_stats(geojson):
    """
    Computes summary statistics from a GeoJSON FeatureCollection.

    Args:
        geojson: GeoJSON FeatureCollection dict

    Returns:
        dict with keys: total, points, lines, polygons
    """
    features = geojson.get("features", [])
    points = 0
    lines = 0
    polygons = 0

    for f in features:
        geom_type = f.get("geometry", {}).get("type", "")
        if geom_type == "Point":
            points += 1
        elif geom_type == "LineString" or geom_type == "MultiLineString":
            lines += 1
        elif geom_type in ("Polygon", "MultiPolygon"):
            polygons += 1

    return {
        "total": len(features),
        "points": points,
        "lines": lines,
        "polygons": polygons,
    }


def _geojson_to_csv(geojson):
    """
    Converts GeoJSON features to CSV format for download.

    Args:
        geojson: GeoJSON FeatureCollection dict

    Returns:
        CSV string
    """
    features = geojson.get("features", [])
    if not features:
        return ""

    # Collect all property keys across features
    all_keys = set()
    for f in features:
        all_keys.update(f.get("properties", {}).keys())
    all_keys = sorted(all_keys)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header: geometry_type, longitude, latitude, then all property keys
    header = ["geometry_type", "longitude", "latitude"] + list(all_keys)
    writer.writerow(header)

    for f in features:
        geom = f.get("geometry", {})
        props = f.get("properties", {})
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])

        # Extract a representative point
        if geom_type == "Point":
            lon, lat = coords[0], coords[1]
        elif geom_type == "LineString" and coords:
            # Midpoint of line
            mid = coords[len(coords) // 2]
            lon, lat = mid[0], mid[1]
        elif geom_type == "Polygon" and coords and coords[0]:
            # Centroid approximation from ring
            ring = coords[0]
            lon = sum(c[0] for c in ring) / len(ring)
            lat = sum(c[1] for c in ring) / len(ring)
        else:
            lon, lat = "", ""

        row = [geom_type, lon, lat]
        for key in all_keys:
            row.append(props.get(key, ""))
        writer.writerow(row)

    return output.getvalue()


def _create_bbox_map(center_lat=41.8902, center_lon=12.4922, zoom=12):
    """
    Creates a folium map with the Draw plugin for bounding box selection.

    Args:
        center_lat: initial map center latitude
        center_lon: initial map center longitude
        zoom: initial zoom level

    Returns:
        folium.Map object
    """
    import folium
    from folium.plugins import Draw

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    Draw(
        draw_options={
            "polyline": False,
            "polygon": False,
            "circle": False,
            "marker": False,
            "circlemarker": False,
            "rectangle": {
                "shapeOptions": {
                    "color": "#06b6d4",
                    "weight": 2,
                    "fillColor": "#06b6d4",
                    "fillOpacity": 0.1,
                }
            },
        },
        edit_options={"edit": False},
    ).add_to(m)

    return m


def _create_results_map(geojson, bbox):
    """
    Creates a folium map displaying GeoJSON results.

    Args:
        geojson: GeoJSON FeatureCollection dict
        bbox: tuple (south, west, north, east)

    Returns:
        folium.Map object
    """
    import folium

    center_lat = (bbox[0] + bbox[2]) / 2
    center_lon = (bbox[1] + bbox[3]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    # Fit map to bounding box
    m.fit_bounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]])

    # Draw bbox rectangle
    folium.Rectangle(
        bounds=[[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
        color="#06b6d4",
        weight=2,
        fill=True,
        fill_color="#06b6d4",
        fill_opacity=0.05,
        dash_array="5",
    ).add_to(m)

    # Add GeoJSON layer
    if geojson and geojson.get("features"):
        folium.GeoJson(
            geojson,
            name="OSM Features",
            style_function=lambda feature: {
                "fillColor": "rgba(6,182,212,0.2)",
                "color": "#06b6d4",
                "weight": 2,
                "fillOpacity": 0.3,
            },
            point_to_layer=lambda feature, latlng: folium.CircleMarker(
                latlng,
                radius=5,
                color="#06b6d4",
                fill=True,
                fill_color="#06b6d4",
                fill_opacity=0.6,
                weight=1,
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=["name"] if any(
                    "name" in f.get("properties", {})
                    for f in geojson["features"][:20]
                ) else ["type"],
                aliases=["Name"] if any(
                    "name" in f.get("properties", {})
                    for f in geojson["features"][:20]
                ) else ["Type"],
                sticky=True,
            ),
        ).add_to(m)

    return m


def render_osm_explorer():
    """
    Main render function for the OSM Explorer tab.

    Displays:
    - Left column: folium map with Draw plugin for bbox selection
    - Right column: category selector, search button
    - After search: stats metrics, results map, download buttons
    """
    try:
        import folium
    except ImportError:
        st.error("folium is required for OSM Explorer. Install it with: pip install folium")
        return

    # Check for streamlit_folium
    try:
        from streamlit_folium import st_folium
        has_st_folium = True
    except ImportError:
        has_st_folium = False

    # Initialize session state
    if "osm_bbox" not in st.session_state:
        st.session_state.osm_bbox = None
    if "osm_geojson" not in st.session_state:
        st.session_state.osm_geojson = None
    if "osm_stats" not in st.session_state:
        st.session_state.osm_stats = None
    if "osm_category" not in st.session_state:
        st.session_state.osm_category = "Buildings"
    if "osm_searching" not in st.session_state:
        st.session_state.osm_searching = False

    st.markdown("""
    <div class="tab-header cyan">
        <h4>OpenStreetMap Explorer</h4>
        <p>Query buildings, roads, parks, and more from OpenStreetMap via the Overpass API. Draw a rectangle to define your search area.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Map & Search Controls
    # ══════════════════════════════════════════
    st.markdown("#### Search Area")
    col_map, col_controls = st.columns([2, 1])

    with col_map:

        m = _create_bbox_map()
        map_output = None

        if has_st_folium:
            try:
                map_output = st_folium(
                    m,
                    height=480,
                    width=None,
                    returned_objects=["all_drawings"],
                    key="osm_map",
                )
            except Exception as e:
                logger.warning(f"st_folium error: {e}")
                has_st_folium = False

        if not has_st_folium:
            components.html(m._repr_html_(), height=480)
            st.warning(
                "Interactive drawing unavailable. "
                "Install streamlit-folium: `pip install -U streamlit-folium`"
            )

        # Extract bbox from drawn rectangle
        if map_output:
            drawings = map_output.get("all_drawings") or []
            if drawings:
                last_drawing = drawings[-1]
                geometry = last_drawing.get("geometry", {})
                coords = geometry.get("coordinates", [[]])[0]
                if coords and len(coords) >= 4:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    st.session_state.osm_bbox = (
                        min(lats), min(lons), max(lats), max(lons)
                    )

    with col_controls:
        st.markdown(
            '<p style="color:#e8ecf4; font-weight:600; font-size:1.05rem;">'
            "Search Parameters</p>",
            unsafe_allow_html=True,
        )

        selected_category = st.selectbox(
            "Feature Category",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(st.session_state.osm_category),
            key="osm_category_select",
        )
        st.session_state.osm_category = selected_category

        # Show current bbox info
        if st.session_state.osm_bbox:
            bbox = st.session_state.osm_bbox
            st.markdown(
                f'<div class="glass-card" style="margin:0.5rem 0;">'
                f'<span style="color:#06b6d4; font-weight:600; font-size:0.85rem;">Bounding Box</span><br/>'
                f'<span style="color:#8b97b0; font-size:0.82rem;">'
                f"S: {bbox[0]:.5f}, W: {bbox[1]:.5f}<br/>"
                f"N: {bbox[2]:.5f}, E: {bbox[3]:.5f}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Draw a rectangle on the map to set the search area.")

        # Manual bbox input as fallback
        with st.expander("Manual Bbox Entry"):
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                man_south = st.number_input("South", value=41.885, format="%.5f", key="osm_man_south")
                man_west = st.number_input("West", value=12.485, format="%.5f", key="osm_man_west")
            with mcol2:
                man_north = st.number_input("North", value=41.895, format="%.5f", key="osm_man_north")
                man_east = st.number_input("East", value=12.500, format="%.5f", key="osm_man_east")
            if st.button("Set Manual Bbox", width="stretch", key="osm_set_manual"):
                st.session_state.osm_bbox = (man_south, man_west, man_north, man_east)
                st.rerun()

        # Search button
        can_search = st.session_state.osm_bbox is not None
        if st.button(
            "Search OSM",
            type="primary",
            width="stretch",
            disabled=not can_search,
            key="osm_search_btn",
        ):
            bbox = st.session_state.osm_bbox
            with st.spinner(f"Querying Overpass API for {selected_category}..."):
                query = build_overpass_query(bbox, selected_category)
                data = query_overpass(query)
                if data:
                    geojson = overpass_to_geojson(data)
                    stats = compute_stats(geojson)
                    st.session_state.osm_geojson = geojson
                    st.session_state.osm_stats = stats
                else:
                    st.session_state.osm_geojson = None
                    st.session_state.osm_stats = None

    # ══════════════════════════════════════════
    # SECTION 2: Results Overview
    # ══════════════════════════════════════════
    if st.session_state.osm_stats and st.session_state.osm_geojson:
        st.divider()
        stats = st.session_state.osm_stats
        geojson = st.session_state.osm_geojson

        st.markdown("#### Results Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Features", stats["total"])
        with col2:
            st.metric("Points", stats["points"])
        with col3:
            st.metric("Lines", stats["lines"])
        with col4:
            st.metric("Polygons", stats["polygons"])

        # ── SECTION 3: Results Map ──
        if stats["total"] > 0:
            st.markdown("---")
            st.markdown("#### Interactive Results Map")

            results_map = _create_results_map(geojson, st.session_state.osm_bbox)

            if has_st_folium:
                try:
                    st_folium(
                        results_map,
                        height=500,
                        width=None,
                        returned_objects=[],
                        key="osm_results_map",
                    )
                except Exception:
                    components.html(results_map._repr_html_(), height=500)
            else:
                components.html(results_map._repr_html_(), height=500)

            # ── SECTION 4: Download ──
            st.markdown("---")
            st.markdown("#### Export Data")
            dl_col1, dl_col2 = st.columns(2)

            with dl_col1:
                geojson_str = json.dumps(geojson, indent=2, ensure_ascii=False)
                st.download_button(
                    "Download GeoJSON",
                    data=geojson_str,
                    file_name=f"osm_{st.session_state.osm_category.lower().replace(' ', '_')}.geojson",
                    mime="application/json",
                    width="stretch",
                    key="osm_dl_geojson",
                )

            with dl_col2:
                csv_str = _geojson_to_csv(geojson)
                st.download_button(
                    "Download CSV",
                    data=csv_str,
                    file_name=f"osm_{st.session_state.osm_category.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    width="stretch",
                    key="osm_dl_csv",
                )

            # Feature table preview
            with st.expander(f"Feature Table ({stats['total']} features)"):
                try:
                    import pandas as pd

                    rows = []
                    for f in geojson["features"][:500]:
                        props = f.get("properties", {})
                        geom_type = f.get("geometry", {}).get("type", "")
                        row = {
                            "Name": props.get("name", ""),
                            "Type": geom_type,
                            "OSM ID": props.get("id", ""),
                        }
                        # Include a few common tags
                        for tag_key in ("amenity", "building", "highway", "leisure",
                                        "natural", "shop", "public_transport",
                                        "addr:street", "addr:housenumber"):
                            if tag_key in props:
                                row[tag_key] = props[tag_key]
                        rows.append(row)

                    if rows:
                        df = pd.DataFrame(rows)
                        st.dataframe(df, width="stretch", hide_index=True)
                    else:
                        st.info("No features to display.")
                except ImportError:
                    st.info("Install pandas for feature table display.")
        else:
            st.warning(
                f"No {st.session_state.osm_category} features found in the selected area. "
                "Try a larger area or different category."
            )
