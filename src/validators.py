"""
Input validation utilities for TerraScout AI.
Prevents crashes from invalid coordinates, types, and resource limits.
"""

import math

# Mercator projection safe latitude limit
MERCATOR_LAT_LIMIT = 85.051129


def safe_float(val, default: float = 0.0) -> float:
    """Convert any value to float safely, returning default on failure."""
    if val is None:
        return default
    try:
        result = float(val)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def clamp_lat(lat: float) -> float:
    """Clamp latitude to valid Mercator range."""
    return max(-MERCATOR_LAT_LIMIT, min(MERCATOR_LAT_LIMIT, lat))


def validate_bbox(south: float, west: float, north: float, east: float) -> tuple:
    """
    Validate and normalize a bounding box.
    Returns (south, west, north, east) with guaranteed south <= north.
    Raises ValueError for clearly invalid input.
    """
    south = max(-90.0, min(90.0, south))
    north = max(-90.0, min(90.0, north))
    west = max(-180.0, min(180.0, west))
    east = max(-180.0, min(180.0, east))

    # Swap if inverted
    if south > north:
        south, north = north, south
    if west > east:
        west, east = east, west

    # Reject zero-area
    if abs(north - south) < 1e-6 and abs(east - west) < 1e-6:
        raise ValueError("Bounding box has zero area")

    return (south, west, north, east)


def bbox_from_center(lat: float, lon: float, radius_km: float) -> tuple:
    """
    Compute a bounding box from center point + radius.
    Handles poles correctly by capping dlon.
    Returns (south, west, north, east).
    """
    dlat = radius_km / 111.0
    cos_lat = abs(math.cos(math.radians(lat)))
    # At poles cos → 0; cap to prevent huge dlon
    if cos_lat < 0.05:
        dlon = 180.0  # Near pole: span full hemisphere
    else:
        dlon = radius_km / (111.0 * cos_lat)

    south = max(-90.0, lat - dlat)
    north = min(90.0, lat + dlat)
    west = max(-180.0, lon - dlon)
    east = min(180.0, lon + dlon)
    return (south, west, north, east)


def estimate_download_mb(tile_count: int) -> float:
    """Estimate download size in MB from tile count."""
    return tile_count * 0.05  # ~50KB per satellite tile at typical zoom


MAX_TILE_COUNT = 2000
MAX_AREA_KM2 = 50000


def check_tile_limit(tile_count: int) -> str | None:
    """Return error message if tile count exceeds safe limit, else None."""
    if tile_count > MAX_TILE_COUNT:
        return (
            f"Area too large: {tile_count:,} tiles estimated "
            f"(max {MAX_TILE_COUNT:,}). Select a smaller area or lower zoom."
        )
    return None
