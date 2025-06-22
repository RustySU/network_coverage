"""Tests for coordinate conversion utilities."""

import pytest

from app.infrastructure.coordinate_utils import lamber93_to_gps


class TestLambert93ToGPS:
    """Test coordinate conversion functionality."""

    def test_lambert93_to_gps_known_pairs(self):
        """Test known Lambert 93 to GPS pairs for exactness."""
        # List of (x_lambert, y_lambert, expected_longitude, expected_latitude)
        # Values verified with trusted Lambert 93 to WGS84 converters
        known_pairs = [
            # Lambert 93 origin point (700000, 6600000)
            (700000, 6600000, 3.000000, 46.500000),
            # Lyon area (852000, 6510000)
            (852000, 6510000, 4.952588, 45.672642),
            # Bordeaux area (432000, 6370000)
            (432000, 6370000, -0.364689, 44.377639),
        ]
        for x_lambert, y_lambert, expected_lon, expected_lat in known_pairs:
            lon, lat = lamber93_to_gps(x_lambert, y_lambert)
            # Allow a small tolerance (0.0001 degrees ~ 11 meters)
            assert pytest.approx(lon, abs=0.0001) == expected_lon
            assert pytest.approx(lat, abs=0.0001) == expected_lat

    def test_lambert93_to_gps_valid_coordinates(self) -> None:
        """Test valid Lambert 93 to GPS conversion."""
        # Test coordinates in France
        x_lambert = 102980
        y_lambert = 6847973

        longitude, latitude = lamber93_to_gps(x_lambert, y_lambert)

        # Should be valid GPS coordinates
        assert -180 <= longitude <= 180
        assert -90 <= latitude <= 90
        assert longitude != 0
        assert latitude != 0

        # Should be in France (roughly) - allow for negative longitude
        assert -10 <= longitude <= 10
        assert 40 <= latitude <= 50

    def test_lambert93_to_gps_edge_cases(self) -> None:
        """Test edge cases for coordinate conversion."""
        # Test with zero coordinates
        longitude, latitude = lamber93_to_gps(0, 0)
        assert isinstance(longitude, float)
        assert isinstance(latitude, float)

        # Test with negative coordinates
        longitude, latitude = lamber93_to_gps(-100000, -100000)
        assert isinstance(longitude, float)
        assert isinstance(latitude, float)

    def test_lambert93_to_gps_consistency(self) -> None:
        """Test that coordinate conversion is consistent."""
        x_lambert = 102980
        y_lambert = 6847973

        # Convert same coordinates multiple times
        result1 = lamber93_to_gps(x_lambert, y_lambert)
        result2 = lamber93_to_gps(x_lambert, y_lambert)

        # Should get same result
        assert result1 == result2
