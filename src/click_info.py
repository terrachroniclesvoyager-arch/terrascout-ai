import os
import numpy as np
import logging

logger = logging.getLogger(__name__)


def get_pixel_data(lat, lng, raster_path):
    """Extracts pixel values from all bands at a given lat/lng coordinate."""
    try:
        import rasterio
        from pyproj import Transformer

        with rasterio.open(raster_path) as src:
            # Transform lat/lng to the raster's CRS
            if src.crs and str(src.crs) != "EPSG:4326":
                transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
                x, y = transformer.transform(lng, lat)
            else:
                x, y = lng, lat

            # Get pixel row/col
            row, col = src.index(x, y)

            # Check bounds
            if 0 <= row < src.height and 0 <= col < src.width:
                values = {}
                for band_idx in range(1, src.count + 1):
                    band_data = src.read(band_idx)
                    values[f"Band {band_idx}"] = float(band_data[row, col])
                return values
            else:
                return None
    except Exception as e:
        logger.warning(f"Could not read pixel data: {e}")
        return None


def classify_terrain(pixel_values):
    """Heuristic terrain classification from RGB band values."""
    if not pixel_values:
        return "Unknown"

    bands = list(pixel_values.values())
    if len(bands) < 3:
        return "Single-band data"

    r, g, b = bands[0], bands[1], bands[2]

    # Normalize to 0-255 range if needed
    max_val = max(r, g, b, 1)
    if max_val > 255:
        r, g, b = r / max_val * 255, g / max_val * 255, b / max_val * 255

    # Simple heuristic classification
    if r < 50 and g < 50 and b < 50:
        return "Shadow / Dark area"
    elif r > 200 and g > 200 and b > 200:
        return "Bright surface / Cloud"
    elif g > r and g > b and g > 80:
        return "Vegetation"
    elif b > r and b > g and b > 80:
        return "Water"
    elif r > 150 and g > 120 and b > 100 and abs(r - g) < 40:
        return "Bare soil / Sand"
    elif r > 140 and g < 100 and b < 100:
        return "Built-up / Rooftop"
    elif r > g and r > b:
        return "Urban / Dry terrain"
    else:
        return "Mixed / Unclassified"


def build_click_info(lat, lng, active_rasters=None):
    """Builds a complete info dictionary for a map click point."""
    info = {
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "terrain": None,
        "pixel_data": None,
    }

    if active_rasters:
        for raster_path in active_rasters:
            if raster_path and os.path.exists(raster_path):
                pixel_data = get_pixel_data(lat, lng, raster_path)
                if pixel_data:
                    info["pixel_data"] = pixel_data
                    info["terrain"] = classify_terrain(pixel_data)
                    break

    return info
