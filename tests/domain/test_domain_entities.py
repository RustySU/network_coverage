"""Tests for domain entities."""

import pytest

from app.domain.entities import (
    Coverage,
    Location,
    MobileSite,
    Operator,
)


class TestOperator:
    """Test Operator enum."""

    def test_operator_values(self) -> None:
        """Test operator enum values."""
        assert Operator.ORANGE == "Orange"
        assert Operator.SFR == "SFR"
        assert Operator.BOUYGUES == "Bouygues"


class TestLocation:
    """Test Location entity."""

    def test_location_creation(self) -> None:
        """Test location creation."""
        location = Location(x=100.0, y=200.0)
        assert location.x == 100.0
        assert location.y == 200.0


class TestCoverage:
    """Test Coverage entity."""

    def test_coverage_creation(self) -> None:
        """Test coverage creation."""
        coverage = Coverage(has_2g=True, has_3g=False, has_4g=True)
        assert coverage.has_2g is True
        assert coverage.has_3g is False
        assert coverage.has_4g is True


class TestMobileSite:
    """Test MobileSite entity."""

    def test_mobile_site_creation(self) -> None:
        """Test mobile site creation."""
        location = Location(x=100.0, y=200.0)
        coverage = Coverage(has_2g=True, has_3g=True, has_4g=False)
        site = MobileSite(
            operator=Operator.ORANGE,
            location=location,
            coverage=coverage,
        )

        assert site.operator == Operator.ORANGE
        assert site.location == location
        assert site.coverage == coverage

    def test_mobile_site_validation_invalid_operator(self) -> None:
        """Test mobile site validation with invalid operator."""
        location = Location(x=100.0, y=200.0)
        coverage = Coverage(has_2g=True, has_3g=True, has_4g=False)

        with pytest.raises(ValueError, match="Invalid operator"):
            MobileSite(
                operator="Invalid",  # type: ignore
                location=location,
                coverage=coverage,
            )

    def test_mobile_site_validation_invalid_location(self) -> None:
        """Test mobile site validation with invalid location."""
        coverage = Coverage(has_2g=True, has_3g=True, has_4g=False)

        with pytest.raises(ValueError, match="Invalid location"):
            MobileSite(
                operator=Operator.ORANGE,
                location="invalid",  # type: ignore
                coverage=coverage,
            )

    def test_mobile_site_validation_invalid_coverage(self) -> None:
        """Test mobile site validation with invalid coverage."""
        location = Location(x=100.0, y=200.0)

        with pytest.raises(ValueError, match="Invalid coverage"):
            MobileSite(
                operator=Operator.ORANGE,
                location=location,
                coverage="invalid",  # type: ignore
            )
