"""
Intelligence Map — Interactive Folium map for Fusion Console & Executive Brief.
Shows domain-score heatmap, threat markers, infrastructure density,
earthquake epicenters, biodiversity clusters, air quality zones,
volcano proximity circles, and fire hotspots — all from real hub data.
"""

import html as html_module
import logging
import math

import streamlit as st

try:
    import folium
    from folium import plugins as folium_plugins
    from streamlit.components.v1 import html as st_html
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

logger = logging.getLogger(__name__)

# ── Palette ───────────────────────────────────────────────────────────────
_CYAN = "#00f0ff"
_GREEN = "#00ff88"
_RED = "#ff3344"
_AMBER = "#ffaa00"
_BLUE = "#4488ff"
_PURPLE = "#aa44ff"
_DIM = "#6a7a8a"


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _score_color(score):
    """Return hex color for a domain score (0-100)."""
    if score >= 70:
        return _GREEN
    if score >= 40:
        return _AMBER
    return _RED


def _make_dark_tile_layer():
    """Return a dark map tile layer for ops-center aesthetic."""
    return folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="Dark Ops",
        max_zoom=19,
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN: BUILD INTELLIGENCE MAP
# ═══════════════════════════════════════════════════════════════════════════

def build_intelligence_map(lat, lon, hub, height=550):
    """Build and render a comprehensive intelligence map from hub data.

    Layers:
      1. Domain Score Heatmap (8 surrounding points colored by composite)
      2. Earthquake Epicenters (real USGS data)
      3. Infrastructure Density (Overpass amenities)
      4. Air Quality Zone (colored circle)
      5. Volcano Proximity (if any within 200km)
      6. Fire Hotspots (FIRMS/EONET data)
      7. Biodiversity Clusters (iNaturalist observations)
      8. Soil Moisture Gradient
    """
    if not HAS_FOLIUM:
        st.info("Folium not available — install folium for interactive maps.")
        return

    raw = hub.get("raw_data", {})
    scores = hub.get("scores", {})

    # Create dark-themed map centered on location
    m = folium.Map(
        location=[lat, lon],
        zoom_start=11,
        tiles=None,
        prefer_canvas=True,
    )
    _make_dark_tile_layer().add_to(m)

    # ── Center Marker ────────────────────────────────────────────────────
    overall = hub.get("overall_score", 50)
    label = hub.get("overall_label", "UNKNOWN")
    oc = _score_color(overall)

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(
            f"<b style='color:{oc}'>{html_module.escape(label)}</b><br>"
            f"Score: {overall:.0f}/100<br>"
            f"Lat: {lat:.4f}, Lon: {lon:.4f}",
            max_width=250,
        ),
        icon=folium.DivIcon(html=(
            f'<div style="background:{oc};width:16px;height:16px;border-radius:50%;'
            f'border:3px solid white;box-shadow:0 0 10px {oc}"></div>'
        )),
        tooltip=f"Target: {overall:.0f}/100",
    ).add_to(m)

    # ── Layer 1: Domain Score Heatmap ────────────────────────────────────
    _add_domain_heatmap(m, lat, lon, scores)

    # ── Layer 2: Earthquake Epicenters ───────────────────────────────────
    _add_earthquakes(m, raw)

    # ── Layer 3: Infrastructure ──────────────────────────────────────────
    _add_infrastructure(m, lat, lon, raw)

    # ── Layer 4: Air Quality Zone ────────────────────────────────────────
    _add_air_quality_zone(m, lat, lon, raw)

    # ── Layer 5: Volcanoes ───────────────────────────────────────────────
    _add_volcanoes(m, lat, lon, raw)

    # ── Layer 6: Fire Hotspots ───────────────────────────────────────────
    _add_fire_hotspots(m, lat, lon, raw)

    # ── Layer 7: Biodiversity ────────────────────────────────────────────
    _add_biodiversity(m, raw)

    # ── Layer 8: Flood Risk ──────────────────────────────────────────────
    _add_flood_indicator(m, lat, lon, raw)

    # Layer control + fullscreen
    folium.LayerControl(collapsed=True).add_to(m)
    try:
        folium_plugins.Fullscreen(
            position="topright",
            title="Expand",
            title_cancel="Exit fullscreen",
        ).add_to(m)
    except Exception:
        pass

    # Render
    try:
        st_html(m._repr_html_(), height=height)
    except Exception as exc:
        logger.warning("Map render failed: %s", exc)
        st.warning("Interactive map could not be rendered.")


# ═══════════════════════════════════════════════════════════════════════════
# LAYER BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def _add_domain_heatmap(m, lat, lon, scores):
    """Add a heatmap layer from domain scores projected onto surrounding grid."""
    try:
        fg = folium.FeatureGroup(name="Domain Score Heatmap", show=True)

        # Generate a grid of points around the location
        heat_data = []
        offsets = [
            (-0.03, -0.03), (-0.03, 0), (-0.03, 0.03),
            (0, -0.03), (0, 0), (0, 0.03),
            (0.03, -0.03), (0.03, 0), (0.03, 0.03),
            (-0.06, -0.06), (-0.06, 0.06), (0.06, -0.06), (0.06, 0.06),
            (0, -0.06), (0, 0.06), (-0.06, 0), (0.06, 0),
        ]

        domain_list = list(scores.keys())
        avg_score = sum(v for v in scores.values() if isinstance(v, (int, float))) / max(len(scores), 1)

        for i, (dlat, dlon) in enumerate(offsets):
            # Each point gets a weight based on a domain score (cycling through domains)
            # Plus some spatial variation to make the heatmap interesting
            domain_idx = i % len(domain_list) if domain_list else 0
            d = domain_list[domain_idx] if domain_list else ""
            s = scores.get(d, 50)
            if not isinstance(s, (int, float)):
                s = 50
            weight = max(0.1, s / 100)

            heat_data.append([lat + dlat, lon + dlon, weight])

        if heat_data:
            folium_plugins.HeatMap(
                data=heat_data,
                radius=30,
                blur=25,
                max_zoom=14,
                gradient={
                    0.0: "#ff3344",
                    0.3: "#ffaa00",
                    0.5: "#ffff00",
                    0.7: "#00f0ff",
                    1.0: "#00ff88",
                },
                name="Score Heat",
            ).add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("Domain heatmap layer failed: %s", exc)


def _add_earthquakes(m, raw):
    """Add earthquake epicenters from USGS data."""
    try:
        quakes = raw.get("quakes") or {}
        features = quakes.get("features", [])
        if not features:
            return

        fg = folium.FeatureGroup(name="Earthquakes", show=True)
        for feat in features[:20]:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            eq_lon, eq_lat = coords[0], coords[1]
            mag = props.get("mag", 0) or 0
            place = props.get("place", "Unknown")

            # Size and color by magnitude
            radius = max(4, min(20, mag * 3))
            if mag >= 5:
                color = _RED
            elif mag >= 3:
                color = _AMBER
            else:
                color = _CYAN

            folium.CircleMarker(
                location=[eq_lat, eq_lon],
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                weight=1,
                popup=folium.Popup(
                    f"<b>M{mag:.1f}</b><br>{html_module.escape(str(place))}",
                    max_width=200,
                ),
                tooltip=f"M{mag:.1f}",
            ).add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("Earthquake layer failed: %s", exc)


def _add_infrastructure(m, lat, lon, raw):
    """Add infrastructure density circle."""
    try:
        infra = raw.get("infra") or {}
        elements = infra.get("elements", [])
        if not elements:
            return

        count = len(elements)
        fg = folium.FeatureGroup(name="Infrastructure", show=False)

        # Add individual markers for first 50 items
        for el in elements[:50]:
            tags = el.get("tags", {})
            el_lat = el.get("lat")
            el_lon = el.get("lon")
            if el_lat is None or el_lon is None:
                continue
            name = tags.get("name", tags.get("amenity", "Infrastructure"))
            amenity = tags.get("amenity", "")

            folium.CircleMarker(
                location=[el_lat, el_lon],
                radius=3,
                color=_AMBER,
                fill=True,
                fill_color=_AMBER,
                fill_opacity=0.5,
                weight=1,
                tooltip=html_module.escape(str(name)),
            ).add_to(fg)

        fg.add_to(m)
    except Exception as exc:
        logger.debug("Infrastructure layer failed: %s", exc)


def _add_air_quality_zone(m, lat, lon, raw):
    """Add an air quality colored circle zone."""
    try:
        aq = raw.get("air_quality") or {}
        current_aq = aq.get("current", {}) if isinstance(aq, dict) else {}
        aqi = current_aq.get("european_aqi", 0) or 0
        pm25 = current_aq.get("pm2_5", 0) or 0
        pm10 = current_aq.get("pm10", 0) or 0

        if not (aqi or pm25 or pm10):
            return

        if aqi < 50:
            color = _GREEN
            label = "Good"
        elif aqi <= 100:
            color = _AMBER
            label = "Moderate"
        else:
            color = _RED
            label = "Poor"

        fg = folium.FeatureGroup(name="Air Quality Zone", show=True)
        folium.Circle(
            location=[lat, lon],
            radius=3000,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.1,
            popup=folium.Popup(
                f"<b>Air Quality: {label}</b><br>"
                f"EU AQI: {aqi}<br>PM2.5: {pm25}<br>PM10: {pm10}",
                max_width=200,
            ),
            tooltip=f"AQI: {aqi} ({label})",
        ).add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("AQ zone layer failed: %s", exc)


def _add_volcanoes(m, lat, lon, raw):
    """Add volcano markers from Smithsonian GVP data."""
    try:
        volcanoes = raw.get("volcanoes") or {}
        volcano_list = volcanoes.get("volcanoes", [])
        if not volcano_list:
            return

        fg = folium.FeatureGroup(name="Volcanoes", show=True)
        for v in volcano_list[:10]:
            v_lat = v.get("lat")
            v_lon = v.get("lon")
            if v_lat is None or v_lon is None:
                continue
            name = v.get("name", "Unknown Volcano")
            dist = v.get("distance_km", 0)
            elev = v.get("elevation_m", 0)
            last_eruption = v.get("last_eruption_year", "Unknown")
            v_type = v.get("type", "")

            # Danger circle
            if dist < 50:
                circle_color = _RED
            elif dist < 100:
                circle_color = _AMBER
            else:
                circle_color = _DIM

            folium.CircleMarker(
                location=[float(v_lat), float(v_lon)],
                radius=10,
                color=circle_color,
                fill=True,
                fill_color=circle_color,
                fill_opacity=0.5,
                weight=2,
                popup=folium.Popup(
                    f"<b>{html_module.escape(str(name))}</b><br>"
                    f"Type: {html_module.escape(str(v_type))}<br>"
                    f"Elevation: {elev}m<br>"
                    f"Last eruption: {last_eruption}<br>"
                    f"Distance: {dist:.0f}km",
                    max_width=250,
                ),
                tooltip=f"{html_module.escape(str(name))} ({dist:.0f}km)",
            ).add_to(fg)

            # Add triangle icon for volcano
            folium.Marker(
                location=[float(v_lat), float(v_lon)],
                icon=folium.DivIcon(html=(
                    f'<div style="color:{circle_color};font-size:18px;text-shadow:0 0 4px {circle_color}">'
                    f'&#9650;</div>'
                )),
            ).add_to(fg)

        fg.add_to(m)
    except Exception as exc:
        logger.debug("Volcano layer failed: %s", exc)


def _add_fire_hotspots(m, lat, lon, raw):
    """Add fire hotspots from FIRMS/EONET data."""
    try:
        firms = raw.get("firms_fires") or {}
        events = firms.get("events", [])
        if not events:
            return

        fg = folium.FeatureGroup(name="Fire Hotspots", show=True)
        for ev in events[:20]:
            f_lat = ev.get("lat")
            f_lon = ev.get("lon") or ev.get("lng")
            if f_lat is None or f_lon is None:
                continue
            title = ev.get("title", "Fire Event")
            dist = ev.get("distance_km", 0)

            folium.CircleMarker(
                location=[float(f_lat), float(f_lon)],
                radius=8,
                color="#ff4400",
                fill=True,
                fill_color="#ff4400",
                fill_opacity=0.7,
                weight=1,
                popup=folium.Popup(
                    f"<b>{html_module.escape(str(title))}</b><br>"
                    f"Distance: {dist:.0f}km",
                    max_width=200,
                ),
                tooltip=html_module.escape(str(title)),
            ).add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("Fire hotspot layer failed: %s", exc)


def _add_biodiversity(m, raw):
    """Add biodiversity observation clusters from iNaturalist."""
    try:
        inat = raw.get("inat") or {}
        results = inat.get("results", [])
        if not results:
            return

        fg = folium.FeatureGroup(name="Biodiversity", show=False)
        cluster = folium_plugins.MarkerCluster(name="Species")

        kingdom_colors = {
            "Animalia": _AMBER, "Plantae": _GREEN, "Fungi": _PURPLE,
            "Aves": _BLUE, "Insecta": "#ff66aa",
        }

        for obs in results[:80]:
            geom = obs.get("geojson") or {}
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue
            o_lon, o_lat = coords[0], coords[1]

            taxon = obs.get("taxon") or {}
            name = taxon.get("preferred_common_name") or taxon.get("name", "Unknown")
            kingdom = taxon.get("iconic_taxon_name", "")
            color = kingdom_colors.get(kingdom, _CYAN)

            folium.CircleMarker(
                location=[o_lat, o_lon],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=1,
                tooltip=html_module.escape(str(name)),
            ).add_to(cluster)

        cluster.add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("Biodiversity layer failed: %s", exc)


def _add_flood_indicator(m, lat, lon, raw):
    """Add flood risk indicator from Open-Meteo flood data."""
    try:
        flood = raw.get("flood") or {}
        discharge = flood.get("daily", {}).get("river_discharge", []) if isinstance(flood, dict) else []
        if not discharge:
            return

        # Filter out None values
        valid = [d for d in discharge if d is not None]
        if not valid:
            return

        max_discharge = max(valid)
        avg_discharge = sum(valid) / len(valid)

        # Only show if there's meaningful discharge
        if max_discharge < 1:
            return

        # Color by relative flood risk
        if max_discharge > avg_discharge * 3:
            color = _RED
            risk = "HIGH"
        elif max_discharge > avg_discharge * 1.5:
            color = _AMBER
            risk = "MODERATE"
        else:
            color = _CYAN
            risk = "LOW"

        fg = folium.FeatureGroup(name="Flood Risk", show=True)
        folium.Circle(
            location=[lat, lon],
            radius=5000,
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.06,
            dash_array="5,10",
            popup=folium.Popup(
                f"<b>Flood Risk: {risk}</b><br>"
                f"Max discharge: {max_discharge:.1f} m³/s<br>"
                f"Avg discharge: {avg_discharge:.1f} m³/s",
                max_width=200,
            ),
            tooltip=f"Flood risk: {risk}",
        ).add_to(fg)
        fg.add_to(m)
    except Exception as exc:
        logger.debug("Flood indicator layer failed: %s", exc)


# ═══════════════════════════════════════════════════════════════════════════
# COMPACT MAP for smaller sections
# ═══════════════════════════════════════════════════════════════════════════

def render_compact_threat_map(lat, lon, raw, height=350):
    """Render a small threat-focused map (earthquakes + volcanoes + fires)."""
    if not HAS_FOLIUM:
        return

    try:
        m = folium.Map(location=[lat, lon], zoom_start=8, tiles=None, prefer_canvas=True)
        _make_dark_tile_layer().add_to(m)

        # Center marker
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=(
                '<div style="background:#00f0ff;width:12px;height:12px;border-radius:50%;'
                'border:2px solid white;box-shadow:0 0 8px #00f0ff"></div>'
            )),
            tooltip="Target Location",
        ).add_to(m)

        _add_earthquakes(m, raw)
        _add_volcanoes(m, lat, lon, raw)
        _add_fire_hotspots(m, lat, lon, raw)
        _add_flood_indicator(m, lat, lon, raw)

        folium.LayerControl(collapsed=True).add_to(m)
        st_html(m._repr_html_(), height=height)
    except Exception as exc:
        logger.warning("Compact threat map failed: %s", exc)
