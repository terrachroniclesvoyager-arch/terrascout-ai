"""
Map Catalog module for Pocket GIS AI.
Browse, search, and overlay 200+ tile layers from multiple providers.
"""

import json
import os
import streamlit as st
try:
    import folium
    from folium.plugins import DualMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "tile_catalog.json")
LAYERS_PER_PAGE = 21


@st.cache_data(ttl=3600)
def load_catalog() -> dict:
    """Load the tile catalog JSON file."""
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def count_total_layers(catalog: dict) -> int:
    """Count total layers across all categories."""
    total = 0
    for layers in catalog.get("categories", {}).values():
        total += len(layers)
    return total


def search_catalog(catalog: dict, query: str = "", category: str = "All") -> list:
    """Search layers by name/attr, optionally filter by category."""
    results = []
    categories = catalog.get("categories", {})

    for cat_name, layers in categories.items():
        if category != "All" and cat_name != category:
            continue
        for layer in layers:
            if query:
                q = query.lower()
                if (q in layer["name"].lower() or
                    q in layer.get("attr", "").lower() or
                    q in cat_name.lower()):
                    results.append({**layer, "_category": cat_name})
            else:
                results.append({**layer, "_category": cat_name})

    return results


def _build_preview_map(layers: list, center=None, zoom=3, height=500) -> str:
    """Build a folium map with selected layers and return HTML."""
    if center is None:
        center = [41.9, 12.5]

    m = folium.Map(location=center, zoom_start=zoom, tiles=None)

    # Dark base
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
        overlay=False,
    ).add_to(m)

    for layer in layers:
        url = layer.get("url", "")
        name = layer.get("name", "Unnamed")
        attr = layer.get("attr", "")
        is_overlay = layer.get("overlay", False)

        # Skip layers needing API keys with placeholder
        if "placeholder" in url:
            continue

        # Handle date-enabled layers (use a recent date)
        if layer.get("date_enabled"):
            url = url.replace("{date}", "2024-06-01")

        folium.TileLayer(
            tiles=url,
            attr=attr,
            name=name,
            overlay=is_overlay,
            control=True,
            opacity=0.8 if is_overlay else 1.0,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m._repr_html_()


def render_catalog_tab():
    """Main render function for the Map Catalog tab."""

    catalog = load_catalog()
    total = count_total_layers(catalog)
    categories = ["All"] + list(catalog.get("categories", {}).keys())

    # Header
    st.markdown(f"""
    <div class="tab-header cyan">
        <h4>Map Layer Catalog &mdash; <span class="counter-badge">{total} layers</span></h4>
        <p>Browse, search, and overlay tile layers from NASA GIBS, Esri, OpenStreetMap, national mapping agencies, and more. Add layers to the viewer for overlay or side-by-side comparison.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search & Filter
    # ══════════════════════════════════════════
    st.markdown("#### Search & Filter")
    col_search, col_cat = st.columns([2, 1])
    with col_search:
        query = st.text_input(
            "Search layers",
            placeholder="e.g. MODIS, satellite, terrain, France...",
            key="catalog_search",
        )
    with col_cat:
        selected_cat = st.selectbox("Category", categories, key="catalog_category")

    # Search results
    results = search_catalog(catalog, query, selected_cat)

    # Pagination
    total_results = len(results)
    if "catalog_page" not in st.session_state:
        st.session_state.catalog_page = 0

    max_page = max(0, (total_results - 1) // LAYERS_PER_PAGE)
    # Reset page on new search
    if st.session_state.catalog_page > max_page:
        st.session_state.catalog_page = 0

    page = st.session_state.catalog_page
    start_idx = page * LAYERS_PER_PAGE
    end_idx = min(start_idx + LAYERS_PER_PAGE, total_results)
    page_results = results[start_idx:end_idx]

    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">Showing {start_idx+1}-{end_idx} of {total_results} layers</p>',
        unsafe_allow_html=True,
    )

    # Selected layers state
    if "catalog_selected" not in st.session_state:
        st.session_state.catalog_selected = []

    # Layer grid (3 columns)
    cols = st.columns(3)
    for i, layer in enumerate(page_results):
        col = cols[i % 3]
        with col:
            needs_key = "placeholder" in layer.get("url", "")
            key_badge = ' <span style="color:#ec4899; font-size:0.7rem;">API KEY</span>' if needs_key else ""
            overlay_badge = ' <span style="color:#10b981; font-size:0.7rem;">OVERLAY</span>' if layer.get("overlay") else ""
            date_badge = ' <span style="color:#8b5cf6; font-size:0.7rem;">DATE</span>' if layer.get("date_enabled") else ""

            st.markdown(f"""
            <div class="catalog-card">
                <div class="layer-name">{layer['name']}{key_badge}{overlay_badge}{date_badge}</div>
                <div class="layer-source">{layer.get('attr', 'Unknown')}</div>
                <div class="layer-category">{layer.get('_category', '')}</div>
                <div style="color:#5a6580; font-size:0.7rem; margin-top:0.3rem;">Max zoom: {layer.get('max_zoom', '?')}</div>
            </div>
            """, unsafe_allow_html=True)

            # Add to selected
            layer_id = f"{layer['name']}_{layer.get('_category', '')}"
            if st.button("Add to Map", key=f"add_{start_idx}_{i}", width="stretch"):
                if layer_id not in [l.get("_id") for l in st.session_state.catalog_selected]:
                    st.session_state.catalog_selected.append({**layer, "_id": layer_id})
                    st.rerun()

    # Pagination controls
    if total_results > LAYERS_PER_PAGE:
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("Previous", disabled=(page == 0), key="cat_prev"):
                st.session_state.catalog_page = max(0, page - 1)
                st.rerun()
        with pcol2:
            st.markdown(
                f'<p style="text-align:center; color:#8b97b0;">Page {page+1} of {max_page+1}</p>',
                unsafe_allow_html=True,
            )
        with pcol3:
            if st.button("Next", disabled=(page >= max_page), key="cat_next"):
                st.session_state.catalog_page = min(max_page, page + 1)
                st.rerun()

    st.markdown("---")

    # ══════════════════════════════════════════
    # SECTION 2: Selected Layers & Map Viewer
    # ══════════════════════════════════════════
    selected = st.session_state.catalog_selected

    if selected:
        st.subheader(f"Selected Layers ({len(selected)})")

        # List selected with remove buttons
        for idx, sl in enumerate(selected):
            scol1, scol2 = st.columns([4, 1])
            with scol1:
                st.markdown(
                    f'<span style="color:#e8ecf4; font-size:0.9rem;">{sl["name"]}</span> '
                    f'<span style="color:#8b97b0; font-size:0.75rem;">({sl.get("attr", "")})</span>',
                    unsafe_allow_html=True,
                )
            with scol2:
                if st.button("Remove", key=f"rm_{idx}"):
                    st.session_state.catalog_selected.pop(idx)
                    st.rerun()

        # Clear all button
        if st.button("Clear All Selected", key="cat_clear"):
            st.session_state.catalog_selected = []
            st.rerun()

        st.markdown("---")

        # View mode
        view_mode = st.radio(
            "View Mode",
            ["Overlay Viewer", "Side-by-Side Compare"],
            horizontal=True,
            key="catalog_view_mode",
        )

        if view_mode == "Overlay Viewer":
            # Single map with all selected layers
            st.markdown("**Multi-Layer Overlay Map**")
            map_html = _build_preview_map(selected, height=550)
            components.html(map_html, height=550)

        else:
            # Side-by-side with DualMap
            if len(selected) >= 2:
                st.markdown("**Side-by-Side Comparison**")

                left_choice = st.selectbox(
                    "Left Map",
                    [s["name"] for s in selected],
                    key="dual_left",
                )
                right_choice = st.selectbox(
                    "Right Map",
                    [s["name"] for s in selected],
                    index=min(1, len(selected) - 1),
                    key="dual_right",
                )

                left_layer = next((s for s in selected if s["name"] == left_choice), selected[0])
                right_layer = next((s for s in selected if s["name"] == right_choice), selected[-1])

                dm = DualMap(location=[41.9, 12.5], zoom_start=5)

                for side, layer in [("m1", left_layer), ("m2", right_layer)]:
                    url = layer.get("url", "")
                    if "placeholder" in url:
                        continue
                    if layer.get("date_enabled"):
                        url = url.replace("{date}", "2024-06-01")

                    target = dm.m1 if side == "m1" else dm.m2
                    folium.TileLayer(
                        tiles=url,
                        attr=layer.get("attr", ""),
                        name=layer["name"],
                    ).add_to(target)

                components.html(dm._repr_html_(), height=550)
            else:
                st.info("Select at least 2 layers for side-by-side comparison.")
    else:
        st.info("Click 'Add to Map' on any layer above to start building your map.")
