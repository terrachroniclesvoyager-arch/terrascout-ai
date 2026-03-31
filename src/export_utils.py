"""
TerraScout AI -- Multi-format export utilities.

Provides functions to convert pandas DataFrames into several geospatial and
tabular formats:

* CSV   -- plain comma-separated values
* GeoJSON -- RFC 7946 FeatureCollection (built manually, no geopandas needed)
* KML   -- Keyhole Markup Language XML (pure-Python, no external library)
* GeoPackage -- OGC GeoPackage via geopandas + shapely (lazy-imported)

A convenience function ``render_export_buttons`` creates a horizontal row of
Streamlit download buttons, one per format.
"""

from __future__ import annotations

import io
import json
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def export_csv(df: pd.DataFrame) -> str:
    """Return the contents of *df* as a CSV string.

    An empty DataFrame produces a string that contains only the header row
    (or an empty string when there are no columns at all).
    """
    if df is None or df.empty:
        if df is not None and len(df.columns) > 0:
            return df.head(0).to_csv(index=False)
        return ""
    return df.to_csv(index=False)


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def export_geojson(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> str:
    """Return a GeoJSON FeatureCollection string built from *df*.

    Each row becomes a Feature whose geometry is a Point constructed from
    *lat_col* and *lon_col*.  All remaining columns are placed in the
    ``properties`` object.  Rows where either coordinate is missing are
    skipped.

    An empty DataFrame returns a valid but empty FeatureCollection.
    """
    features: list[dict] = []

    if df is not None and not df.empty and lat_col in df.columns and lon_col in df.columns:
        property_cols = [c for c in df.columns if c not in (lat_col, lon_col)]

        for _, row in df.iterrows():
            lat = row.get(lat_col)
            lon = row.get(lon_col)

            # Skip rows with missing coordinates
            if pd.isna(lat) or pd.isna(lon):
                continue

            properties: dict = {}
            for col in property_cols:
                value = row[col]
                # Convert numpy/pandas types to native Python so json.dumps
                # does not choke.
                if pd.isna(value):
                    properties[col] = None
                elif hasattr(value, "item"):
                    properties[col] = value.item()
                else:
                    properties[col] = value

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "properties": properties,
            }
            features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }
    return json.dumps(feature_collection, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# KML
# ---------------------------------------------------------------------------

def export_kml(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    name_col: Optional[str] = None,
) -> str:
    """Return a KML XML string with one Placemark per row.

    *name_col*, when provided and present in *df*, is used as the
    ``<name>`` element of each Placemark.  All other columns are emitted
    inside an ``<ExtendedData>`` block as ``<Data>`` elements.

    The function uses only the standard-library ``xml.etree.ElementTree``
    module -- no external KML library is required.

    An empty DataFrame returns a valid KML document with no Placemarks.
    """
    kml_ns = "http://www.opengis.net/kml/2.2"

    kml = Element("kml", xmlns=kml_ns)
    document = SubElement(kml, "Document")
    doc_name = SubElement(document, "name")
    doc_name.text = "TerraScout AI Export"

    if df is not None and not df.empty and lat_col in df.columns and lon_col in df.columns:
        extra_cols = [
            c for c in df.columns
            if c not in (lat_col, lon_col) and c != name_col
        ]

        for _, row in df.iterrows():
            lat = row.get(lat_col)
            lon = row.get(lon_col)

            if pd.isna(lat) or pd.isna(lon):
                continue

            placemark = SubElement(document, "Placemark")

            # <name>
            pm_name = SubElement(placemark, "name")
            if name_col and name_col in df.columns and not pd.isna(row.get(name_col)):
                pm_name.text = str(row[name_col])
            else:
                pm_name.text = ""

            # <Point><coordinates>lon,lat,0</coordinates></Point>
            point = SubElement(placemark, "Point")
            coords = SubElement(point, "coordinates")
            coords.text = f"{float(lon)},{float(lat)},0"

            # <ExtendedData>
            if extra_cols:
                ext_data = SubElement(placemark, "ExtendedData")
                for col in extra_cols:
                    value = row[col]
                    data_el = SubElement(ext_data, "Data", name=col)
                    value_el = SubElement(data_el, "value")
                    value_el.text = "" if pd.isna(value) else str(value)

    xml_str: str = tostring(kml, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


# ---------------------------------------------------------------------------
# GeoPackage
# ---------------------------------------------------------------------------

def export_geopackage(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    filename: str = "export.gpkg",
) -> Optional[bytes]:
    """Return a GeoPackage file as *bytes*, or ``None`` on failure.

    ``geopandas`` and ``shapely`` are imported lazily so the rest of the
    module keeps working even when they are not installed.  If the import
    fails, a ``st.warning`` is displayed and ``None`` is returned.

    An empty DataFrame produces a GeoPackage that contains the schema but
    no rows.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        st.warning(
            "**geopandas** and/or **shapely** are not installed.  "
            "GeoPackage export is unavailable.  Install them with:\n\n"
            "```\npip install geopandas shapely\n```"
        )
        return None

    if df is None or df.empty:
        # Create an empty GeoDataFrame with the right schema
        gdf = gpd.GeoDataFrame(df, geometry=[], crs="EPSG:4326")
    else:
        if lat_col not in df.columns or lon_col not in df.columns:
            st.warning(
                f"Columns **{lat_col}** and/or **{lon_col}** not found in "
                "the DataFrame.  Cannot build geometry for GeoPackage export."
            )
            return None

        geometry = [
            Point(float(lon), float(lat))
            if not (pd.isna(lat) or pd.isna(lon))
            else None
            for lat, lon in zip(df[lat_col], df[lon_col])
        ]
        drop_cols = [c for c in (lat_col, lon_col) if c in df.columns]
        gdf = gpd.GeoDataFrame(
            df.drop(columns=drop_cols),
            geometry=geometry,
            crs="EPSG:4326",
        )

    buf = io.BytesIO()
    gdf.to_file(buf, driver="GPKG", layer="export")
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Streamlit download buttons
# ---------------------------------------------------------------------------

def render_export_buttons(
    df: pd.DataFrame,
    prefix: str = "export",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> None:
    """Render a row of four ``st.download_button`` widgets (CSV, GeoJSON, KML, GPKG).

    Parameters
    ----------
    df : pd.DataFrame
        The data to export.
    prefix : str
        A short string prepended to each download file name so that
        multiple export rows on the same page do not collide.
    lat_col, lon_col : str
        Column names used for spatial formats.
    """
    col_csv, col_geojson, col_kml, col_gpkg = st.columns(4)

    with col_csv:
        csv_data = export_csv(df)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{prefix}.csv",
            mime="text/csv",
            key=f"{prefix}_csv_btn",
        )

    with col_geojson:
        geojson_data = export_geojson(df, lat_col=lat_col, lon_col=lon_col)
        st.download_button(
            label="Download GeoJSON",
            data=geojson_data,
            file_name=f"{prefix}.geojson",
            mime="application/geo+json",
            key=f"{prefix}_geojson_btn",
        )

    with col_kml:
        kml_data = export_kml(df, lat_col=lat_col, lon_col=lon_col)
        st.download_button(
            label="Download KML",
            data=kml_data,
            file_name=f"{prefix}.kml",
            mime="application/vnd.google-earth.kml+xml",
            key=f"{prefix}_kml_btn",
        )

    with col_gpkg:
        gpkg_data = export_geopackage(
            df, lat_col=lat_col, lon_col=lon_col, filename=f"{prefix}.gpkg"
        )
        if gpkg_data is not None:
            st.download_button(
                label="Download GPKG",
                data=gpkg_data,
                file_name=f"{prefix}.gpkg",
                mime="application/geopackage+sqlite3",
                key=f"{prefix}_gpkg_btn",
            )
