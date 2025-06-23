"""Tests for coordinate conversion utilities."""

import pytest

from app.infrastructure.coordinate_utils import calculate_distance_km, lamber93_to_gps


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


class TestCoordinateUtils:
    """Test coordinate utility functions."""

    def test_calculate_distance_km(self) -> None:
        """Test distance calculation between two points."""
        # Test distance between Paris and Lyon (approximately 400km)
        paris_lat, paris_lon = 48.8566, 2.3522
        lyon_lat, lyon_lon = 45.7640, 4.8357
        
        distance = calculate_distance_km(paris_lat, paris_lon, lyon_lat, lyon_lon)
        
        # Should be approximately 400km (allowing some tolerance)
        assert 390 <= distance <= 410
        
    def test_calculate_distance_km_same_point(self) -> None:
        """Test distance calculation for the same point."""
        lat, lon = 48.8566, 2.3522
        
        distance = calculate_distance_km(lat, lon, lat, lon)
        
        # Should be 0km
        assert distance == 0.0
        
    def test_calculate_distance_km_close_points(self) -> None:
        """Test distance calculation for very close points."""
        # Two points in Paris (Eiffel Tower and Notre Dame)
        eiffel_lat, eiffel_lon = 48.8584, 2.2945
        notre_dame_lat, notre_dame_lon = 48.8530, 2.3499
        
        distance = calculate_distance_km(eiffel_lat, eiffel_lon, notre_dame_lat, notre_dame_lon)
        
        # Should be approximately 4-5km
        assert 4.0 <= distance <= 5.0
