"""Tests for CSV data loader functionality."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Operator
from app.infrastructure.data_loader import CSVDataLoader


class TestCSVDataLoader:
    """Unit tests for CSV data loader without database dependencies."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def data_loader(self, mock_session: AsyncMock) -> CSVDataLoader:
        """Create a CSV data loader with mock session."""
        return CSVDataLoader(mock_session)

    def test_parse_row_original_csv(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row from original CSV format."""
        row = {
            "Operateur": "Orange",
            "x": "102980",
            "y": "6847973",
            "2G": "1",
            "3G": "1",
            "4G": "0",
        }

        site = data_loader._parse_row(row, 0)

        assert site.operator == Operator.ORANGE
        assert isinstance(site.location.x, float)
        assert isinstance(site.location.y, float)
        assert site.coverage.has_2g is True
        assert site.coverage.has_3g is True
        assert site.coverage.has_4g is False

    def test_parse_row_preprocessed_csv(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row from preprocessed CSV format."""
        row = {
            "Operateur": "SFR",
            "longitude": "2.3522",
            "latitude": "48.8566",
            "2G": "1",
            "3G": "0",
            "4G": "1",
        }

        site = data_loader._parse_row(row, 0)

        assert site.operator == Operator.SFR
        assert site.location.x == 2.3522  # longitude
        assert site.location.y == 48.8566  # latitude
        assert site.coverage.has_2g is True
        assert site.coverage.has_3g is False
        assert site.coverage.has_4g is True

    def test_parse_row_invalid_operator(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row with invalid operator."""
        row = {
            "Operateur": "InvalidOperator",
            "x": "102980",
            "y": "6847973",
            "2G": "1",
            "3G": "1",
            "4G": "0",
        }

        with pytest.raises(ValueError, match="Unknown operator"):
            data_loader._parse_row(row, 0)

    def test_parse_row_invalid_coordinates(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row with invalid coordinates."""
        row = {
            "Operateur": "Orange",
            "x": "invalid",
            "y": "6847973",
            "2G": "1",
            "3G": "1",
            "4G": "0",
        }

        with pytest.raises(ValueError, match="Invalid coordinates"):
            data_loader._parse_row(row, 0)

    def test_parse_row_invalid_coverage_flags(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row with invalid coverage flags."""
        row = {
            "Operateur": "Orange",
            "x": "102980",
            "y": "6847973",
            "2G": "invalid",
            "3G": "1",
            "4G": "0",
        }

        with pytest.raises(ValueError, match="Invalid coverage flags"):
            data_loader._parse_row(row, 0)

    def test_parse_row_empty_values(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row with empty values."""
        row = {
            "Operateur": "",
            "x": "102980",
            "y": "6847973",
            "2G": "1",
            "3G": "1",
            "4G": "0",
        }

        with pytest.raises(ValueError, match="Unknown operator"):
            data_loader._parse_row(row, 0)

    def test_parse_row_missing_fields(self, data_loader: CSVDataLoader) -> None:
        """Test parsing a row with missing fields."""
        row = {
            "Operateur": "Orange",
            "x": "102980",
            # Missing 'y' field
            "2G": "1",
            "3G": "1",
            "4G": "0",
        }

        with pytest.raises(KeyError):
            data_loader._parse_row(row, 0)
