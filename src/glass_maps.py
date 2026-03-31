# -*- coding: utf-8 -*-
"""
World Glass & Crystal Heritage module for TerraScout AI.
Explores glassmaking traditions, crystal workshops, stained glass heritage,
and glass art studios worldwide using curated data and the Overpass API.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

from src.overpass_client import query_overpass

MAP_MODES = [
    "Murano Glass Heritage",
    "Bohemian Crystal",
    "Stained Glass Windows",
    "Ancient Glass Making",
    "Japanese Glass Art",
    "Scandinavian Glass Design",
    "Art Nouveau Glass",
    "Glass Museums Worldwide",
    "Crystal & Chandelier Heritage",
    "World Glassblowing Studios",
]

MODE_COLORS = {
    "Murano Glass Heritage": "#06b6d4",
    "Bohemian Crystal": "#a855f7",
    "Stained Glass Windows": "#f59e0b",
    "Ancient Glass Making": "#ef4444",
    "Japanese Glass Art": "#ec4899",
    "Scandinavian Glass Design": "#3b82f6",
    "Art Nouveau Glass": "#10b981",
    "Glass Museums Worldwide": "#8b5cf6",
    "Crystal & Chandelier Heritage": "#14b8a6",
    "World Glassblowing Studios": "#f97316",
}

MODE_PRESETS = {
    "Murano Glass Heritage": {"lat": 45.4581, "lon": 12.3531, "zoom": 13, "radius": 5},
    "Bohemian Crystal": {"lat": 50.7671, "lon": 15.0543, "zoom": 8, "radius": 60},
    "Stained Glass Windows": {"lat": 48.4472, "lon": 1.4879, "zoom": 7, "radius": 80},
    "Ancient Glass Making": {"lat": 33.8547, "lon": 35.8623, "zoom": 6, "radius": 200},
    "Japanese Glass Art": {"lat": 35.1815, "lon": 136.9066, "zoom": 7, "radius": 100},
    "Scandinavian Glass Design": {"lat": 56.8777, "lon": 15.8008, "zoom": 8, "radius": 80},
    "Art Nouveau Glass": {"lat": 48.6921, "lon": 6.1844, "zoom": 7, "radius": 100},
    "Glass Museums Worldwide": {"lat": 36.8691, "lon": -76.3003, "zoom": 3, "radius": 50},
    "Crystal & Chandelier Heritage": {"lat": 48.2082, "lon": 16.3738, "zoom": 6, "radius": 100},
    "World Glassblowing Studios": {"lat": 47.3769, "lon": 8.5417, "zoom": 3, "radius": 50},
}

CURATED = {
    "Murano Glass Heritage": [
        {"name": "Museo del Vetro", "lat": 45.4590, "lon": 12.3525, "country": "Italy", "notes": "Murano glass museum, centuries of Venetian glassmaking history"},
        {"name": "Fornace Orsoni", "lat": 45.4449, "lon": 12.3227, "country": "Italy", "notes": "Last gold-leaf mosaic furnace in Venice, founded 1888"},
        {"name": "Venini Glassworks", "lat": 45.4586, "lon": 12.3534, "country": "Italy", "notes": "Iconic 20th-century art glass, designer collaborations"},
        {"name": "Barovier & Toso", "lat": 45.4582, "lon": 12.3539, "country": "Italy", "notes": "Oldest glass company in the world, founded 1295"},
        {"name": "Punta Conterie", "lat": 45.4596, "lon": 12.3510, "country": "Italy", "notes": "Historic bead-making district of Murano island"},
    ],
    "Bohemian Crystal": [
        {"name": "Moser Glassworks", "lat": 50.2215, "lon": 12.8727, "country": "Czechia", "notes": "Luxury crystal since 1857, Karlovy Vary"},
        {"name": "Novosad & Son Harrachov", "lat": 50.7671, "lon": 15.4290, "country": "Czechia", "notes": "Oldest continuously operating glassworks in Czechia, since 1712"},
        {"name": "Glass Museum Novy Bor", "lat": 50.7573, "lon": 14.5547, "country": "Czechia", "notes": "Center of north Bohemian glass industry since 17th century"},
        {"name": "Preciosa Jablonec", "lat": 50.7275, "lon": 15.1700, "country": "Czechia", "notes": "World-famous crystal chandeliers and jewelry components"},
        {"name": "Lasvit HQ", "lat": 50.7572, "lon": 15.0079, "country": "Czechia", "notes": "Contemporary Bohemian glass design for architecture"},
    ],
    "Stained Glass Windows": [
        {"name": "Chartres Cathedral", "lat": 48.4472, "lon": 1.4879, "country": "France", "notes": "176 stained glass windows, 13th-century masterpiece, UNESCO"},
        {"name": "Sainte-Chapelle", "lat": 48.8554, "lon": 2.3451, "country": "France", "notes": "1,113 stained glass panels, Gothic jewel of Paris"},
        {"name": "York Minster Great East Window", "lat": 53.9620, "lon": -1.0820, "country": "UK", "notes": "Largest medieval stained glass window in the world"},
        {"name": "Cologne Cathedral", "lat": 50.9413, "lon": 6.9580, "country": "Germany", "notes": "Richter pixel window (2007) and medieval Bavarian windows"},
        {"name": "National Cathedral Washington", "lat": 38.9306, "lon": -77.0709, "country": "USA", "notes": "Space Window contains a moon rock, 215 windows"},
    ],
    "Ancient Glass Making": [
        {"name": "Sidon (Saida)", "lat": 33.5577, "lon": 35.3714, "country": "Lebanon", "notes": "Phoenician glassblowing birthplace, 1st century BC"},
        {"name": "Alexandria Glass Quarter", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "notes": "Ptolemaic glass workshops, mosaic glass and cameo technique"},
        {"name": "Jalame Glass Factory", "lat": 32.7967, "lon": 35.0667, "country": "Israel", "notes": "4th-century Roman glass factory, excavated site"},
        {"name": "Corning Museum (Ancient Gallery)", "lat": 42.1430, "lon": -77.0547, "country": "USA", "notes": "World's largest ancient glass collection, 3500 years"},
        {"name": "Aquileia Roman Glassworks", "lat": 45.7693, "lon": 13.3694, "country": "Italy", "notes": "Major Roman glass production center, UNESCO area"},
    ],
    "Japanese Glass Art": [
        {"name": "Kiriko Glass Museum Sumida", "lat": 35.7104, "lon": 139.8009, "country": "Japan", "notes": "Edo Kiriko faceted glass cutting tradition since 1834"},
        {"name": "Otaru Glass Town", "lat": 43.1907, "lon": 140.9944, "country": "Japan", "notes": "Historic glass district, Kitaichi Glass and workshops"},
        {"name": "Satsuma Kiriko Museum", "lat": 31.5969, "lon": 130.5571, "country": "Japan", "notes": "Revived Satsuma cut glass, Kagoshima prefecture"},
        {"name": "Hakone Glass Forest Museum", "lat": 35.2478, "lon": 139.0231, "country": "Japan", "notes": "Venetian glass museum and Japanese glass art garden"},
        {"name": "Notojima Glass Art Museum", "lat": 37.1167, "lon": 136.8833, "country": "Japan", "notes": "Chinese and Japanese glass art traditions"},
    ],
    "Scandinavian Glass Design": [
        {"name": "Glasriket (Kingdom of Crystal)", "lat": 56.8777, "lon": 15.8008, "country": "Sweden", "notes": "Region with 13 glassworks, center of Swedish glass since 1742"},
        {"name": "Kosta Boda Glassworks", "lat": 56.8456, "lon": 15.7525, "country": "Sweden", "notes": "Founded 1742, Sweden's oldest glassworks, art glass icons"},
        {"name": "Orrefors Glassworks", "lat": 56.8058, "lon": 15.6953, "country": "Sweden", "notes": "World-renowned crystal design, Graal and Ariel techniques"},
        {"name": "Iittala Glass Museum", "lat": 61.1169, "lon": 24.1844, "country": "Finland", "notes": "Finnish design icon, Aalto vase birthplace, since 1881"},
        {"name": "Hadeland Glassverk", "lat": 60.2306, "lon": 10.3847, "country": "Norway", "notes": "Norway's oldest glass factory, founded 1762, still operating"},
        {"name": "Holmegaard Glasvaerk", "lat": 55.3878, "lon": 11.7956, "country": "Denmark", "notes": "Denmark's foremost glass producer since 1825"},
    ],
    "Art Nouveau Glass": [
        {"name": "Musee de l'Ecole de Nancy", "lat": 48.6844, "lon": 6.1657, "country": "France", "notes": "Emile Galle and Daum glass masterpieces, Art Nouveau capital"},
        {"name": "Daum Crystal Factory Nancy", "lat": 48.6921, "lon": 6.1844, "country": "France", "notes": "Pate de verre and cameo glass since 1878"},
        {"name": "Tiffany Studios (Met Museum)", "lat": 40.7794, "lon": -73.9632, "country": "USA", "notes": "Louis Comfort Tiffany collection, iconic Art Nouveau lamps"},
        {"name": "Lalique Museum Wingen", "lat": 48.9186, "lon": 7.3764, "country": "France", "notes": "Rene Lalique's art glass and jewelry legacy, Alsace"},
        {"name": "Loetz Glass (MAK Vienna)", "lat": 48.2082, "lon": 16.3815, "country": "Austria", "notes": "Bohemian iridescent Art Nouveau glass, MAK collection"},
        {"name": "Horta Museum Brussels", "lat": 50.8257, "lon": 4.3528, "country": "Belgium", "notes": "Victor Horta's Art Nouveau interiors with stained glass"},
    ],
    "Glass Museums Worldwide": [
        {"name": "Corning Museum of Glass", "lat": 42.1430, "lon": -77.0547, "country": "USA", "notes": "World's most comprehensive glass collection, 50,000+ objects"},
        {"name": "Murano Glass Museum", "lat": 45.4590, "lon": 12.3525, "country": "Italy", "notes": "Venetian glassmaking from Roman era to present"},
        {"name": "Museum of Glass Tacoma", "lat": 47.2451, "lon": -122.4334, "country": "USA", "notes": "Chihuly Bridge of Glass, hot shop theater"},
        {"name": "Glasmuseet Ebeltoft", "lat": 56.1944, "lon": 10.6828, "country": "Denmark", "notes": "International studio glass collection, artist residencies"},
        {"name": "Shanghai Museum of Glass", "lat": 31.3200, "lon": 121.4667, "country": "China", "notes": "Converted glass factory, contemporary and historical glass"},
    ],
    "Crystal & Chandelier Heritage": [
        {"name": "Lobmeyr Vienna", "lat": 48.2067, "lon": 16.3713, "country": "Austria", "notes": "Chandelier maker since 1823, Metropolitan Opera and Kremlin"},
        {"name": "Baccarat Crystal Museum", "lat": 48.4468, "lon": 6.7448, "country": "France", "notes": "Luxury crystal since 1764, Lorraine factory town"},
        {"name": "Waterford Crystal Centre", "lat": 52.2593, "lon": -7.1101, "country": "Ireland", "notes": "Famous Irish crystal, Times Square ball, factory tours"},
        {"name": "Swarovski Kristallwelten", "lat": 47.2942, "lon": 11.6000, "country": "Austria", "notes": "Crystal Worlds experience, Wattens, Tyrol"},
        {"name": "Preciosa Lighting", "lat": 50.7750, "lon": 14.4742, "country": "Czechia", "notes": "Bohemian chandelier capital, illuminated the world's palaces"},
    ],
    "World Glassblowing Studios": [
        {"name": "Pilchuck Glass School", "lat": 48.2153, "lon": -122.2200, "country": "USA", "notes": "Founded by Dale Chihuly 1971, premier glass art school"},
        {"name": "Biot Village Glassworks", "lat": 43.6275, "lon": 7.0953, "country": "France", "notes": "Provencal bubble glass tradition, artisan village"},
        {"name": "Canberra Glassworks", "lat": -35.3075, "lon": 149.1450, "country": "Australia", "notes": "Contemporary glass center in heritage power station"},
        {"name": "Berlin Glas e.V.", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "notes": "Berlin's glass art center, artist residencies and workshops"},
        {"name": "Jam Factory Adelaide", "lat": -34.9285, "lon": 138.6007, "country": "Australia", "notes": "Contemporary craft hub with glass, ceramics and design"},
    ],
}

OVERPASS_TAGS = {
    "Murano Glass Heritage": ('craft', 'glass'),
    "Bohemian Crystal": ('craft', 'glass'),
    "Stained Glass Windows": ('amenity', 'place_of_worship'),
    "Ancient Glass Making": ('historic', 'archaeological_site'),
    "Japanese Glass Art": ('craft', 'glass'),
    "Scandinavian Glass Design": ('craft', 'glass'),
    "Art Nouveau Glass": ('tourism', 'museum'),
    "Glass Museums Worldwide": ('tourism', 'museum'),
    "Crystal & Chandelier Heritage": ('shop', 'gift'),
    "World Glassblowing Studios": ('craft', 'glass'),
}


@st.cache_data(ttl=3600)
def _query_glass_overpass(lat: float, lon: float, radius_km: float,
                          tag_key: str, tag_value: str) -> list:
    """Search glass-related features via Overpass API."""
    r = int(radius_km * 1000)
    query = f"""
[out:json][timeout:30];
(
  node["{tag_key}"="{tag_value}"](around:{r},{lat},{lon});
  way["{tag_key}"="{tag_value}"](around:{r},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    node_lookup = {}
    for el in result.get("elements", []):
        if el.get("type") == "node" and "lat" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in result.get("elements", []):
        tags = el.get("tags", {})
        if not tags:
            continue
        lat_v, lon_v = None, None
        if el.get("type") == "node" and "lat" in el:
            lat_v, lon_v = el["lat"], el["lon"]
        elif el.get("type") == "way":
            coords = [node_lookup[n] for n in el.get("nodes", []) if n in node_lookup]
            if coords:
                lat_v = sum(c[0] for c in coords) / len(coords)
                lon_v = sum(c[1] for c in coords) / len(coords)
        if lat_v is None:
            continue
        features.append({
            "name": tags.get("name", tags.get("name:en", "Unnamed")),
            "lat": lat_v, "lon": lon_v,
            "description": tags.get("description", ""),
            "wikipedia": tags.get("wikipedia", ""),
            "osm_id": el.get("id"),
        })
    return features


def _show_stats(metrics: list):
    cols = st.columns(min(len(metrics), 4))
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)


def _build_map(data: list, color: str, center: tuple = None,
               zoom: int = 3) -> folium.Map:
    esc = html_module.escape
    if center is None and data:
        center = (
            sum(d["lat"] for d in data) / len(data),
            sum(d["lon"] for d in data) / len(data),
        )
    center = center or (20, 0)
    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)
    for item in data:
        popup_html = (
            f'<div style="max-width:240px;font-size:0.85rem;">'
            f'<strong>{esc(str(item.get("name", "")))}</strong><br/>'
        )
        if item.get("country"):
            popup_html += f'<b>Country:</b> {esc(str(item["country"]))}<br/>'
        if item.get("notes"):
            popup_html += f'<span style="font-size:0.75rem;">{esc(str(item["notes"])[:200])}</span>'
        popup_html += '</div>'
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7, color=color, fill=True, fill_color=color,
            fill_opacity=0.7, weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=esc(str(item.get("name", ""))),
        ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def _download_section(df: pd.DataFrame, filename: str, label: str, key: str):
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(label, data=csv_buf.getvalue(),
                       file_name=filename, mime="text/csv", key=key)


def _render_mode(mode: str):
    """Unified renderer for all 10 modes."""
    esc = html_module.escape
    color = MODE_COLORS.get(mode, "#06b6d4")
    preset = MODE_PRESETS[mode]
    curated = CURATED.get(mode, [])

    # Stats
    countries = len(set(d.get("country", "") for d in curated))
    _show_stats([
        ("Sites Listed", len(curated)),
        ("Countries", countries),
        ("Map Mode", mode.split()[0]),
    ])

    st.markdown("---")

    # Overpass live search toggle
    use_live = st.checkbox("Add live OSM results", value=False,
                           key=f"glass_live_{mode}")
    live_features = []
    if use_live:
        tag_key, tag_value = OVERPASS_TAGS.get(mode, ("craft", "glass"))
        with st.spinner("Querying Overpass API..."):
            live_features = _query_glass_overpass(
                preset["lat"], preset["lon"], preset["radius"],
                tag_key, tag_value,
            )
        if live_features:
            st.success(f"Found {len(live_features)} additional OSM features.")
        else:
            st.info("No additional OSM features found in this area.")

    # Combine data
    all_data = list(curated)
    for lf in live_features:
        all_data.append({
            "name": lf["name"], "lat": lf["lat"], "lon": lf["lon"],
            "country": "OSM", "notes": lf.get("description", ""),
        })

    if not all_data:
        st.warning("No data available for this mode.")
        return

    # Map
    st.markdown(f"#### {esc(mode)} Map")
    m = _build_map(all_data, color,
                   center=(preset["lat"], preset["lon"]),
                   zoom=preset["zoom"])
    st_html(m._repr_html_(), height=500)

    # Data table & download
    df = pd.DataFrame(all_data)
    cols = [c for c in ["name", "country", "lat", "lon", "notes"] if c in df.columns]
    df = df[cols]
    safe_name = mode.lower().replace(" ", "_").replace("&", "and")
    _download_section(df, f"{safe_name}.csv",
                      f"Download {len(df)} {mode} sites (CSV)",
                      f"dl_glass_{safe_name}")


def render_glass_maps_tab():
    """Main render function for the World Glass & Crystal Heritage Explorer tab."""

    # Header
    header_html = (
        '<div class="tab-header violet">'
        '<h4>\U0001f52e World Glass & Crystal Heritage Explorer</h4>'
        '<p>Discover glassmaking traditions, crystal workshops & stained glass heritage</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Mode selector
    st.markdown("#### Explore Glass Heritage")
    mode = st.selectbox(
        "Select Map Mode", MAP_MODES, key="glass_mode",
        help="Choose a glass/crystal heritage theme to explore.",
    )

    # Mode description bar
    color = MODE_COLORS.get(mode, "#06b6d4")
    st.markdown(
        f'<div style="border-left:3px solid {color};padding:0.5rem 0.75rem;'
        f'margin:0.5rem 0 1rem;background:rgba(15,23,42,0.4);border-radius:0 6px 6px 0;">'
        f'<span style="color:{color};font-weight:600;">{html_module.escape(mode)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    _render_mode(mode)
