"""Coordinate conversion utilities."""

import logging

import pyproj
from pyproj import Geod

logger = logging.getLogger(__name__)


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two points in kilometers using WGS84 ellipsoid."""
    geod = Geod(ellps="WGS84")
    _, _, distance_m = geod.inv(lon1, lat1, lon2, lat2)
    return distance_m / 1000  # Convert meters to kilometers


def lamber93_to_gps(x: float, y: float) -> tuple[float, float]:
    """Convert Lambert 93 coordinates to GPS coordinates (WGS84)."""
    try:
        transformer = pyproj.Transformer.from_crs(
            "+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 "
            "+x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 "
            "+units=m +no_defs",
            "EPSG:4326",  # WGS84
            always_xy=True,
        )

        long, lat = transformer.transform(x, y)
        return long, lat
    except Exception as e:
        logger.error(
            f"Error converting Lambert 93 coordinates ({x}, {y}) to GPS: {str(e)}",
            exc_info=True,
        )
        raise
