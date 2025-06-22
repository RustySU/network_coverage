"""Coordinate conversion utilities."""

import logging

import pyproj

logger = logging.getLogger(__name__)


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
