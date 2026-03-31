"""
Geological Explorer module for TerraScout AI.
Aggregates data from multiple free geological databases:
  - Macrostrat (geological units, formations, lithology, fossils)
  - Paleobiology Database (PBDB) — fossil occurrences worldwide
  - Smithsonian GVP — Holocene volcanoes
  - OneGeology WMS — global geological map tiles
All free, no API key required.
"""

import io
import logging
import streamlit as st
import requests
import pandas as pd
from html import escape
from datetime import datetime

import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════
MACROSTRAT_API = "https://macrostrat.org/api/v2"
PBDB_API = "https://paleobiodb.org/data1.2"
GVP_VOLCANOES_URL = "https://volcano.si.edu/database/list_volcano_holocene.cfm"

# ═══════════════════════════════════════════
# COLOR MAPS
# ═══════════════════════════════════════════
LITH_COLORS = {
    "sandstone": "#f59e0b", "limestone": "#38bdf8", "shale": "#8b97b0",
    "granite": "#ef4444", "basalt": "#5a6580", "gneiss": "#ec4899",
    "schist": "#8b5cf6", "marble": "#06b6d4", "clay": "#a0522d",
    "silt": "#d2b48c", "gravel": "#b8860b", "conglomerate": "#cd853f",
    "dolomite": "#4682b4", "quartzite": "#dda0dd", "slate": "#708090",
    "volcanic": "#dc143c", "metamorphic": "#9370db", "chalk": "#f0f0f0",
    "coal": "#333333", "andesite": "#c44e52", "rhyolite": "#e8a0bf",
    "tuff": "#b5651d", "obsidian": "#1a1a2e", "pumice": "#d4d4d4",
    "gabbro": "#4a4a4a", "peridotite": "#2e8b57", "serpentinite": "#3cb371",
    "migmatite": "#da70d6", "amphibolite": "#556b2f", "eclogite": "#006400",
}

GEO_PERIODS = {
    "Quaternary": "#f9f97f", "Neogene": "#ffe619", "Paleogene": "#fd9a52",
    "Cretaceous": "#7fc64e", "Jurassic": "#34b2c9", "Triassic": "#812b92",
    "Permian": "#f04028", "Carboniferous": "#67a599", "Devonian": "#cb8c37",
    "Silurian": "#b3e1b6", "Ordovician": "#009270", "Cambrian": "#7fa056",
    "Precambrian": "#f04370", "Ediacaran": "#fec07f", "Proterozoic": "#f573a0",
    "Archean": "#f0047f", "Hadean": "#b8006b",
}

# ═══════════════════════════════════════════
# 30+ PRESET LOCATIONS (worldwide geological landmarks)
# ═══════════════════════════════════════════
PRESETS = {
    "Custom": None,
    # Europe
    "Dolomites, Italy": (46.41, 11.84),
    "Mount Vesuvius, Italy": (40.82, 14.43),
    "Mount Etna, Sicily": (37.75, 14.99),
    "Campi Flegrei, Italy": (40.83, 14.14),
    "Santorini, Greece": (36.39, 25.46),
    "White Cliffs of Dover, UK": (51.13, 1.33),
    "Giant's Causeway, N. Ireland": (55.24, -6.51),
    "Swiss Alps — Jungfrau": (46.56, 7.97),
    "Iceland — Thingvellir Rift": (64.26, -21.13),
    "Eyjafjallajökull, Iceland": (63.63, -19.61),
    "Black Forest, Germany": (47.87, 8.07),
    "Ural Mountains, Russia": (56.50, 59.50),
    # Americas
    "Grand Canyon, Arizona": (36.11, -112.11),
    "Yellowstone Caldera, Wyoming": (44.43, -110.59),
    "Mount St. Helens, Washington": (46.20, -122.18),
    "Hawaiian Kilauea": (19.41, -155.28),
    "Yosemite Granite, California": (37.75, -119.57),
    "Appalachian Mountains, Virginia": (37.75, -79.45),
    "Chicxulub Crater Edge, Mexico": (21.30, -89.50),
    "Atacama Desert, Chile": (-23.86, -69.13),
    "Patagonia, Argentina": (-50.34, -72.27),
    "Canadian Shield, Ontario": (49.00, -85.00),
    # Africa & Middle East
    "East African Rift, Kenya": (-1.29, 36.82),
    "Karoo Basin, South Africa": (-32.35, 22.58),
    "Atlas Mountains, Morocco": (31.07, -7.92),
    "Dead Sea Rift, Jordan": (31.50, 35.47),
    # Asia & Oceania
    "Himalayas — Everest region": (27.99, 86.93),
    "Mount Fuji, Japan": (35.36, 138.73),
    "Deccan Traps, India": (18.52, 73.86),
    "Uluru, Australia": (-25.35, 131.04),
    "Milford Sound, New Zealand": (-44.67, 167.93),
    "Krakatoa, Indonesia": (-6.10, 105.42),
    "Pinatubo, Philippines": (15.14, 120.35),
}


# ═══════════════════════════════════════════
# SAFE EXTRACTION HELPERS
# ═══════════════════════════════════════════
def _safe_name(item) -> str:
    """Extract name from item that could be dict or string."""
    if isinstance(item, dict):
        return item.get("name", item.get("lith", str(item)))
    return str(item)


def _safe_names(items: list) -> list[str]:
    """Extract names from a list of dicts or strings."""
    if not items:
        return []
    return [_safe_name(i) for i in items]


# ═══════════════════════════════════════════
# MACROSTRAT API FUNCTIONS
# ═══════════════════════════════════════════
@st.cache_data(ttl=1800)
def get_geology_at_point(lat: float, lon: float) -> list:
    """Query geological units at a specific point."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/geologic_units/map",
            params={"lat": lat, "lng": lon},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception as e:
        logger.warning(f"Macrostrat point query error: {e}")
        return []


@st.cache_data(ttl=1800)
def get_columns_near(lat: float, lon: float) -> list:
    """Get stratigraphic columns near a point."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/columns",
            params={"lat": lat, "lng": lon, "adjacents": "true", "response": "long"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception as e:
        logger.warning(f"Macrostrat columns error: {e}")
        return []


@st.cache_data(ttl=1800)
def search_formations(query: str) -> list:
    """Search geological formations by name."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/defs/strat_names",
            params={"strat_name_like": query},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception as e:
        logger.warning(f"Macrostrat formation search error: {e}")
        return []


@st.cache_data(ttl=3600)
def get_time_intervals() -> list:
    """Get geological time intervals from Macrostrat."""
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/defs/intervals",
            params={"timescale": "international ages"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception:
        return []


@st.cache_data(ttl=3600)
def get_lithology_definitions() -> list:
    """Get all lithology types from Macrostrat."""
    try:
        resp = requests.get(f"{MACROSTRAT_API}/defs/lithologies", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception:
        return []


# ═══════════════════════════════════════════
# PALEOBIOLOGY DATABASE (PBDB) FUNCTIONS
# ═══════════════════════════════════════════
@st.cache_data(ttl=1800)
def get_fossils_near(lat: float, lon: float, radius_km: float = 50) -> list:
    """Query PBDB for fossil occurrences near a point."""
    try:
        resp = requests.get(
            f"{PBDB_API}/occs/list.json",
            params={
                "lngmin": lon - radius_km / 111,
                "lngmax": lon + radius_km / 111,
                "latmin": lat - radius_km / 111,
                "latmax": lat + radius_km / 111,
                "show": "coords,class,phylo",
                "limit": 500,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("records", [])
    except Exception as e:
        logger.warning(f"PBDB fossils error: {e}")
        return []


@st.cache_data(ttl=1800)
def search_pbdb_taxa(taxon: str) -> list:
    """Search PBDB for taxonomic occurrences."""
    try:
        resp = requests.get(
            f"{PBDB_API}/occs/list.json",
            params={
                "base_name": taxon,
                "show": "coords,class",
                "limit": 1000,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("records", [])
    except Exception as e:
        logger.warning(f"PBDB taxa search error: {e}")
        return []


# ═══════════════════════════════════════════
# SMITHSONIAN GVP — HOLOCENE VOLCANOES
# ═══════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_holocene_volcanoes() -> list:
    """Fetch Holocene volcanoes from Smithsonian GVP via Macrostrat/external."""
    # Use a public GeoJSON source of Holocene volcanoes
    try:
        resp = requests.get(
            "https://raw.githubusercontent.com/datasets/geo-boundaries/main/data/volcanoes.geojson",
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("features", [])
    except Exception:
        pass

    # Fallback: use Macrostrat burwell volcanic units as proxy
    try:
        resp = requests.get(
            f"{MACROSTRAT_API}/defs/lithologies",
            params={"lith_type": "volcanic"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", {}).get("data", [])
    except Exception as e:
        logger.warning(f"Volcano data error: {e}")
        return []


@st.cache_data(ttl=1800)
def get_volcanoes_near(lat: float, lon: float, radius_km: float = 200) -> list:
    """Search for volcanic features using Overpass API."""
    try:
        from src.overpass_client import query_overpass
        dlat = radius_km / 111.0
        dlon = radius_km / (111.0 * max(abs(__import__('math').cos(__import__('math').radians(lat))), 0.05))
        south = lat - dlat
        north = lat + dlat
        west = lon - dlon
        east = lon + dlon

        query = f"""
        [out:json][timeout:30];
        (
          node["natural"="volcano"]({south},{west},{north},{east});
          node["geological"="volcanic_vent"]({south},{west},{north},{east});
          node["geological"="volcanic_caldera_rim"]({south},{west},{north},{east});
          way["natural"="volcano"]({south},{west},{north},{east});
          relation["natural"="volcano"]({south},{west},{north},{east});
        );
        out center body;
        """
        data = query_overpass(query, timeout=30)
        if data and "_error" not in data:
            return data.get("elements", [])
        return []
    except Exception as e:
        logger.warning(f"Overpass volcano query error: {e}")
        return []


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════
def _lith_color(name: str) -> str:
    name_lower = name.lower()
    for key, color in LITH_COLORS.items():
        if key in name_lower:
            return color
    return "#8b97b0"


def _period_color(period: str) -> str:
    if not period:
        return "#8b97b0"
    for key, color in GEO_PERIODS.items():
        if key.lower() in period.lower():
            return color
    return "#8b97b0"


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_geology_tab():
    """Main render function for the Geological Explorer tab."""

    st.markdown("""
    <div class="tab-header violet">
        <h4>Geological Explorer</h4>
        <p>Multi-source geological intelligence: Macrostrat formations, PBDB fossils, volcanoes, and global geological maps &mdash; all free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Exploration Mode",
        ["Point Query", "Formation Search", "Fossil Explorer", "Volcano Finder", "Area Overview"],
        horizontal=True,
        key="geology_mode",
    )

    st.markdown("---")

    # ══════════════════════════════════════════
    # POINT QUERY
    # ══════════════════════════════════════════
    if mode == "Point Query":
        _render_point_query()
    elif mode == "Formation Search":
        _render_formation_search()
    elif mode == "Fossil Explorer":
        _render_fossil_explorer()
    elif mode == "Volcano Finder":
        _render_volcano_finder()
    else:
        _render_area_overview()


def _render_point_query():
    st.markdown("#### Query Geology at a Point")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.85rem;">Explore geological units, lithology, age, and nearby fossils at any location.</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        geo_lat = st.number_input("Latitude", value=41.8902, format="%.4f",
                                   min_value=-90.0, max_value=90.0, key="geol_lat")
    with col2:
        geo_lon = st.number_input("Longitude", value=12.4922, format="%.4f",
                                   min_value=-180.0, max_value=180.0, key="geol_lon")

    preset = st.selectbox("Quick Locations", list(PRESETS.keys()), key="geol_preset")
    if preset != "Custom" and PRESETS.get(preset):
        geo_lat, geo_lon = PRESETS[preset]

    if st.button("Query Geology", key="geol_query_btn", width="stretch"):
        st.session_state.geol_query_data = {"lat": geo_lat, "lon": geo_lon}

    if "geol_query_data" not in st.session_state:
        st.info("Enter coordinates or select a preset, then click Query Geology.")
        return

    q = st.session_state.geol_query_data

    with st.spinner("Querying Macrostrat + PBDB..."):
        units = get_geology_at_point(q["lat"], q["lon"])
        fossils = get_fossils_near(q["lat"], q["lon"], radius_km=30)

    if not units and not fossils:
        st.warning("No geological data found. Macrostrat has best coverage in N. America and Europe. Try a different point.")
        return

    # ── Stats ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Rock Units", len(units))
    with c2:
        liths = set()
        for u in units:
            for item in u.get("lith", []):
                liths.add(_safe_name(item))
        st.metric("Lithologies", len(liths))
    with c3:
        periods = set()
        for u in units:
            p = u.get("b_period", u.get("period", ""))
            if p:
                periods.add(p if isinstance(p, str) else str(p))
        st.metric("Periods", len(periods))
    with c4:
        st.metric("Nearby Fossils", len(fossils))

    # ── Map ──
    import folium
    m = folium.Map(location=[q["lat"], q["lon"]], zoom_start=10, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png",
        attr="Macrostrat", name="Geological Map", overlay=True, opacity=0.7,
    ).add_to(m)

    # Query point
    folium.CircleMarker(
        location=[q["lat"], q["lon"]], radius=8,
        color="#06b6d4", fill=True, fill_color="#06b6d4", fill_opacity=0.8,
        popup="Query Point",
    ).add_to(m)

    # Fossil markers
    for f in fossils[:200]:
        flat = f.get("lat")
        flng = f.get("lng")
        if flat and flng:
            fname = escape(str(f.get("tna", "Unknown")))
            fage = escape(str(f.get("oei", "?")))
            folium.CircleMarker(
                location=[flat, flng], radius=4,
                color="#f59e0b", fill=True, fill_color="#f59e0b", fill_opacity=0.7,
                popup=f'<div style="background:#1a2235;color:#e8ecf4;padding:6px;border-radius:4px;">'
                      f'<b>{fname}</b><br><span style="color:#8b97b0;">{fage}</span></div>',
            ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=450)

    # ── Unit details ──
    if units:
        st.markdown("---")
        st.markdown("#### Rock Unit Details")

        for unit in units:
            name = unit.get("strat_name", unit.get("unit_name", "Unknown Unit"))
            if isinstance(name, dict):
                name = name.get("name", str(name))
            age = f"{unit.get('b_age', '?')} – {unit.get('t_age', '?')} Ma"
            period = unit.get("b_period", unit.get("period", "Unknown"))
            if isinstance(period, dict):
                period = period.get("name", str(period))

            liths_list = _safe_names(unit.get("lith", []))
            lith_text = ", ".join(liths_list) if liths_list else "Unknown"

            envs_list = _safe_names(unit.get("environ", []))
            env_text = ", ".join(envs_list) if envs_list else "—"

            econs = _safe_names(unit.get("econ", []))
            econ_text = ", ".join(econs) if econs else ""

            color = _period_color(str(period))

            st.markdown(f"""
            <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.75rem;">
                <div style="width:8px; height:70px; border-radius:4px; background:{color};
                            margin-right:1rem; flex-shrink:0;"></div>
                <div style="flex:1;">
                    <div style="color:#e8ecf4; font-weight:700; font-size:0.95rem;">{escape(str(name))}</div>
                    <div style="color:#8b5cf6; font-size:0.8rem;">{escape(str(period))} &mdash; {escape(str(age))}</div>
                    <div style="color:#8b97b0; font-size:0.8rem;">Lithology: {escape(lith_text)}</div>
                    <div style="color:#7a8a9f; font-size:0.75rem;">Environment: {escape(env_text)}</div>
                    {"<div style='color:#f59e0b; font-size:0.72rem;'>Economic: " + escape(econ_text) + "</div>" if econ_text else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Raw JSON — {str(name)[:40]}"):
                st.json(unit)

    # ── Fossil table ──
    if fossils:
        st.markdown("---")
        st.markdown("#### Nearby Fossil Occurrences (PBDB)")
        fossil_rows = []
        for f in fossils[:200]:
            fossil_rows.append({
                "Taxon": f.get("tna", "Unknown"),
                "Rank": f.get("rnk", ""),
                "Early Interval": f.get("oei", ""),
                "Late Interval": f.get("oli", ""),
                "Lat": f.get("lat"),
                "Lon": f.get("lng"),
                "Collection": f.get("cid", ""),
            })
        df = pd.DataFrame(fossil_rows)
        st.dataframe(df, width="stretch", hide_index=True)


def _render_formation_search():
    st.markdown("#### Search Geological Formations")

    search_q = st.text_input("Formation Name", placeholder="e.g. Morrison, Navajo, Dolomia, Chalk...",
                              key="geol_search_input")

    if st.button("Search", key="geol_search_btn", width="stretch") and search_q:
        st.session_state.geol_search_results = search_formations(search_q)

    results = st.session_state.get("geol_search_results", [])
    if not results:
        if "geol_search_results" in st.session_state:
            st.warning("No formations found. Try a different name.")
        return

    st.metric("Formations Found", len(results))

    rows = []
    for r in results[:100]:
        ref = r.get("ref", {})
        ref_text = ref.get("author", "") if isinstance(ref, dict) else str(ref) if ref else ""
        rows.append({
            "Name": r.get("strat_name", ""),
            "Rank": r.get("rank", ""),
            "Concept ID": r.get("concept_id", ""),
            "Reference": ref_text,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)

        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button("Download CSV", data=csv_buf.getvalue(),
                           file_name=f"formations_{search_q}.csv", mime="text/csv",
                           key="geol_form_dl")


def _render_fossil_explorer():
    st.markdown("#### Fossil Explorer (PBDB)")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.85rem;">Search the Paleobiology Database — millions of fossil occurrences from over 70,000 publications.</p>',
        unsafe_allow_html=True,
    )

    search_mode = st.radio("Search by", ["Location", "Taxon Name"], horizontal=True, key="fossil_mode")

    if search_mode == "Location":
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            f_lat = st.number_input("Latitude", value=44.43, format="%.4f", key="fossil_lat")
        with col2:
            f_lon = st.number_input("Longitude", value=-110.59, format="%.4f", key="fossil_lon")
        with col3:
            f_radius = st.slider("Radius (km)", 10, 200, 50, key="fossil_radius")

        if st.button("Search Fossils", key="fossil_search_btn", width="stretch"):
            with st.spinner("Querying Paleobiology Database..."):
                fossils = get_fossils_near(f_lat, f_lon, f_radius)
            st.session_state.fossil_results = fossils
            st.session_state.fossil_center = (f_lat, f_lon)

    else:
        taxon = st.text_input("Taxon Name", placeholder="e.g. Tyrannosaurus, Ammonoidea, Trilobita...",
                               key="fossil_taxon_input")
        if st.button("Search Taxon", key="fossil_taxon_btn", width="stretch") and taxon:
            with st.spinner(f"Searching PBDB for {taxon}..."):
                fossils = search_pbdb_taxa(taxon)
            st.session_state.fossil_results = fossils
            st.session_state.fossil_center = None

    fossils = st.session_state.get("fossil_results", [])
    if not fossils:
        if "fossil_results" in st.session_state:
            st.warning("No fossil occurrences found.")
        return

    # Stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Occurrences", len(fossils))
    with c2:
        taxa = set(f.get("tna", "") for f in fossils if f.get("tna"))
        st.metric("Unique Taxa", len(taxa))
    with c3:
        intervals = set(f.get("oei", "") for f in fossils if f.get("oei"))
        st.metric("Time Intervals", len(intervals))

    # Map
    import folium
    from folium.plugins import MarkerCluster

    center = st.session_state.get("fossil_center")
    points_with_coords = [(f.get("lat"), f.get("lng"), f) for f in fossils if f.get("lat") and f.get("lng")]

    if points_with_coords:
        if center:
            clat, clon = center
        else:
            clat = sum(p[0] for p in points_with_coords) / len(points_with_coords)
            clon = sum(p[1] for p in points_with_coords) / len(points_with_coords)

        m = folium.Map(location=[clat, clon], zoom_start=6, tiles="CartoDB dark_matter")
        cluster = MarkerCluster(name="Fossil Occurrences").add_to(m)

        for flat, flng, f in points_with_coords[:500]:
            fname = escape(str(f.get("tna", "Unknown")))
            fage = escape(str(f.get("oei", "?")))
            folium.CircleMarker(
                location=[flat, flng], radius=5,
                color="#f59e0b", fill=True, fill_color="#f59e0b", fill_opacity=0.7,
                popup=f'<div style="background:#1a2235;color:#e8ecf4;padding:8px;border-radius:6px;min-width:120px;">'
                      f'<b style="color:#f59e0b;">{fname}</b><br>'
                      f'<span style="color:#8b97b0;">Age: {fage}</span></div>',
            ).add_to(cluster)

        folium.LayerControl().add_to(m)
        components.html(m._repr_html_(), height=450)

    # Table
    rows = []
    for f in fossils[:500]:
        rows.append({
            "Taxon": f.get("tna", ""),
            "Rank": f.get("rnk", ""),
            "Phylum": f.get("phl", ""),
            "Class": f.get("cll", ""),
            "Order": f.get("odl", ""),
            "Early Interval": f.get("oei", ""),
            "Late Interval": f.get("oli", ""),
            "Lat": f.get("lat"),
            "Lon": f.get("lng"),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button("Download Fossil CSV", data=csv_buf.getvalue(),
                       file_name="pbdb_fossils.csv", mime="text/csv", key="fossil_dl")


def _render_volcano_finder():
    st.markdown("#### Volcano Finder")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.85rem;">Find volcanoes worldwide using OpenStreetMap data (Overpass API) and geological maps.</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        v_lat = st.number_input("Center Latitude", value=40.82, format="%.4f", key="volc_lat")
    with col2:
        v_lon = st.number_input("Center Longitude", value=14.43, format="%.4f", key="volc_lon")
    with col3:
        v_radius = st.slider("Radius (km)", 50, 500, 200, key="volc_radius")

    preset = st.selectbox("Quick Volcanic Regions", [
        "Custom",
        "Campania, Italy (Vesuvius/Flegrei)",
        "Sicily, Italy (Etna)",
        "Iceland — Mid-Atlantic Ridge",
        "Hawaiian Islands",
        "Pacific Ring of Fire — Japan",
        "Pacific Ring of Fire — Indonesia",
        "Pacific Ring of Fire — Philippines",
        "Cascade Range, USA",
        "Andes — Ecuador/Colombia",
        "East African Rift",
        "Kamchatka, Russia",
        "Canary Islands, Spain",
        "Azores, Portugal",
    ], key="volc_preset")

    volc_presets = {
        "Campania, Italy (Vesuvius/Flegrei)": (40.82, 14.43),
        "Sicily, Italy (Etna)": (37.75, 14.99),
        "Iceland — Mid-Atlantic Ridge": (64.96, -19.02),
        "Hawaiian Islands": (19.82, -155.47),
        "Pacific Ring of Fire — Japan": (35.36, 138.73),
        "Pacific Ring of Fire — Indonesia": (-7.54, 110.44),
        "Pacific Ring of Fire — Philippines": (15.14, 120.35),
        "Cascade Range, USA": (46.20, -122.18),
        "Andes — Ecuador/Colombia": (0.82, -77.66),
        "East African Rift": (-1.29, 36.82),
        "Kamchatka, Russia": (56.06, 160.64),
        "Canary Islands, Spain": (28.27, -16.64),
        "Azores, Portugal": (38.72, -27.22),
    }
    if preset != "Custom" and preset in volc_presets:
        v_lat, v_lon = volc_presets[preset]

    if st.button("Find Volcanoes", key="volc_search_btn", width="stretch"):
        with st.spinner("Searching for volcanic features..."):
            volcanoes = get_volcanoes_near(v_lat, v_lon, v_radius)
        st.session_state.volc_results = volcanoes
        st.session_state.volc_center = (v_lat, v_lon)

    volcanoes = st.session_state.get("volc_results", [])
    if not volcanoes:
        if "volc_results" in st.session_state:
            st.warning("No volcanic features found in this area. Try a larger radius or known volcanic region.")
        return

    st.metric("Volcanic Features Found", len(volcanoes))

    # Map
    import folium
    center = st.session_state.get("volc_center", (v_lat, v_lon))
    m = folium.Map(location=center, zoom_start=8, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png",
        attr="Macrostrat", name="Geological Map", overlay=True, opacity=0.6,
    ).add_to(m)

    for v in volcanoes:
        vlat = v.get("lat", v.get("center", {}).get("lat") if isinstance(v.get("center"), dict) else None)
        vlon = v.get("lon", v.get("center", {}).get("lon") if isinstance(v.get("center"), dict) else None)
        if not vlat or not vlon:
            continue
        vname = escape(v.get("tags", {}).get("name", "Unknown Volcano"))
        vtype = escape(v.get("tags", {}).get("geological", v.get("tags", {}).get("natural", "volcano")))
        ele = v.get("tags", {}).get("ele", "?")

        folium.CircleMarker(
            location=[vlat, vlon], radius=8,
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.8,
            popup=f'<div style="background:#1a2235;color:#e8ecf4;padding:8px;border-radius:6px;min-width:140px;">'
                  f'<b style="color:#ef4444;">{vname}</b><br>'
                  f'<span style="color:#8b97b0;">Type: {vtype}</span><br>'
                  f'<span style="color:#8b97b0;">Elevation: {ele}m</span></div>',
        ).add_to(m)

    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=450)

    # Table
    rows = []
    for v in volcanoes:
        tags = v.get("tags", {})
        vlat = v.get("lat", v.get("center", {}).get("lat") if isinstance(v.get("center"), dict) else None)
        vlon = v.get("lon", v.get("center", {}).get("lon") if isinstance(v.get("center"), dict) else None)
        rows.append({
            "Name": tags.get("name", "Unknown"),
            "Type": tags.get("geological", tags.get("natural", "volcano")),
            "Elevation": tags.get("ele", "?"),
            "Lat": vlat,
            "Lon": vlon,
            "Wikipedia": tags.get("wikipedia", ""),
        })
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)


def _render_area_overview():
    st.markdown("#### Area Geological Overview")
    st.markdown(
        '<p style="color:#8b97b0; font-size:0.85rem;">View the geological map, stratigraphic columns, and regional data for an area.</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        area_lat = st.number_input("Center Latitude", value=44.4280, format="%.4f",
                                    min_value=-90.0, max_value=90.0, key="geol_area_lat")
    with col2:
        area_lon = st.number_input("Center Longitude", value=-110.5885, format="%.4f",
                                    min_value=-180.0, max_value=180.0, key="geol_area_lon")

    preset = st.selectbox("Quick Regions", list(PRESETS.keys()), key="geol_area_preset")
    if preset != "Custom" and PRESETS.get(preset):
        area_lat, area_lon = PRESETS[preset]

    if st.button("Load Area", key="geol_area_btn", width="stretch"):
        st.session_state.geol_area = {"lat": area_lat, "lon": area_lon}

    if "geol_area" not in st.session_state:
        st.info("Enter coordinates and click Load Area.")
        return

    a = st.session_state.geol_area

    # Map with multiple geological layers
    import folium
    m = folium.Map(location=[a["lat"], a["lon"]], zoom_start=8, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base", overlay=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png",
        attr="Macrostrat", name="Macrostrat Geological", overlay=True, opacity=0.7,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://tiles.macrostrat.org/carto-slim/{z}/{x}/{y}.png",
        attr="Macrostrat Slim", name="Macrostrat Slim", overlay=True, show=False, opacity=0.6,
    ).add_to(m)
    # Sentinel-2 Cloudless as optional comparison
    folium.TileLayer(
        tiles="https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
        attr="EOX Sentinel-2", name="Sentinel-2 Cloudless", overlay=False,
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    components.html(m._repr_html_(), height=500)

    # Stratigraphic columns
    st.markdown("##### Nearby Stratigraphic Columns")
    with st.spinner("Loading stratigraphic data..."):
        columns = get_columns_near(a["lat"], a["lon"])

    if columns:
        st.metric("Stratigraphic Columns", len(columns))
        for col_data in columns[:15]:
            col_name = col_data.get("col_name", "Unknown Column")
            if isinstance(col_name, dict):
                col_name = col_name.get("name", str(col_name))
            col_id = col_data.get("col_id", "")
            area = col_data.get("col_area", "—")
            units_count = col_data.get("t_units", 0)

            st.markdown(f"""
            <div class="bio-card" style="margin-bottom:0.5rem;">
                <div style="color:#e8ecf4; font-weight:600;">{escape(str(col_name))}</div>
                <div style="color:#8b97b0; font-size:0.8rem;">ID: {col_id} | Units: {units_count} | Area: {area} km²</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Column Details — {str(col_name)[:30]}"):
                st.json(col_data)
    else:
        st.info("No stratigraphic columns found near this location.")

    # Also show nearby fossils in area mode
    st.markdown("##### Nearby Fossils (PBDB)")
    with st.spinner("Querying PBDB..."):
        fossils = get_fossils_near(a["lat"], a["lon"], radius_km=50)

    if fossils:
        st.metric("Fossil Occurrences", len(fossils))
        rows = []
        for f in fossils[:100]:
            rows.append({
                "Taxon": f.get("tna", ""),
                "Interval": f.get("oei", ""),
                "Lat": f.get("lat"),
                "Lon": f.get("lng"),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No fossil data found in this area.")
