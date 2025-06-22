"""Tests for application use cases."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases import FindNearbySitesByAddressUseCase
from app.application.schemas import NearbyAddressRequestItem, CoverageInfo
from app.domain.entities import MobileSite, Location, Coverage, Operator


class TestFindNearbySitesByAddressUseCase:
    """Test the FindNearbySitesByAddressUseCase."""

    @pytest.fixture
    def mock_geocoding_service(self):
        """Mock geocoding service."""
        service = AsyncMock()
        service.geocode_addresses.return_value = {
            "id1": {"latitude": 48.8566, "longitude": 2.3522},
            "id2": {"latitude": 45.7489, "longitude": 4.8260},
        }
        return service

    @pytest.fixture
    def mock_repository(self):
        """Mock repository."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def use_case(self, mock_geocoding_service, mock_repository):
        """Create use case with mocked dependencies."""
        return FindNearbySitesByAddressUseCase(
            geocoding_service=mock_geocoding_service,
            repository=mock_repository,
        )

    @pytest.mark.asyncio
    async def test_single_address_with_coverage(self, use_case, mock_repository):
        """Test single address with mobile coverage."""
        # Mock sites returned by repository
        mock_sites = [
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(x=2.3522, y=48.8566),
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=True),
            ),
            MobileSite(
                operator=Operator.SFR,
                location=Location(x=2.3523, y=48.8567),
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=False),
            ),
            MobileSite(
                operator=Operator.BOUYGUES,
                location=Location(x=2.3524, y=48.8568),
                coverage=Coverage(has_2g=False, has_3g=True, has_4g=True),
            ),
            MobileSite(
                operator=Operator.FREE,
                location=Location(x=2.3525, y=48.8569),
                coverage=Coverage(has_2g=False, has_3g=False, has_4g=True),
            ),
        ]
        mock_repository.find_nearby.return_value = mock_sites

        # Test data
        addresses = [NearbyAddressRequestItem(id="id1", address="Paris, France")]

        # Execute use case
        result = await use_case.execute(addresses)

        # Verify results
        assert len(result) == 1
        response = result[0]

        assert response.id == "id1"
        assert response.orange.has_2g is True
        assert response.orange.has_3g is True
        assert response.orange.has_4g is True

        assert response.SFR.has_2g is True
        assert response.SFR.has_3g is True
        assert response.SFR.has_4g is False

        assert response.bouygues.has_2g is False
        assert response.bouygues.has_3g is True
        assert response.bouygues.has_4g is True

        assert response.free.has_2g is False
        assert response.free.has_3g is False
        assert response.free.has_4g is True

    @pytest.mark.asyncio
    async def test_multiple_addresses(self, use_case, mock_repository):
        """Test multiple addresses."""
        # Mock sites for both addresses
        mock_sites = [
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(x=2.3522, y=48.8566),
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=True),
            ),
        ]
        mock_repository.find_nearby.return_value = mock_sites

        # Test data
        addresses = [
            NearbyAddressRequestItem(id="id1", address="Paris, France"),
            NearbyAddressRequestItem(id="id2", address="Lyon, France"),
        ]

        # Execute use case
        result = await use_case.execute(addresses)

        # Verify results
        assert len(result) == 2
        assert result[0].id == "id1"
        assert result[1].id == "id2"

    @pytest.mark.asyncio
    async def test_geocoding_failure(
        self, use_case, mock_geocoding_service, mock_repository
    ):
        """Test handling of geocoding failures."""
        # Mock geocoding failure
        mock_geocoding_service.geocode_addresses.return_value = {}

        # Test data
        addresses = [
            NearbyAddressRequestItem(id="id1", address="Invalid Address"),
        ]

        # Execute use case
        result = await use_case.execute(addresses)

        # Verify results
        assert len(result) == 1
        response = result[0]

        assert response.id == "id1"
        # All operators should have no coverage due to geocoding failure
        assert response.orange.has_2g is False
        assert response.orange.has_3g is False
        assert response.orange.has_4g is False
        assert response.SFR.has_2g is False
        assert response.SFR.has_3g is False
        assert response.SFR.has_4g is False
        assert response.bouygues.has_2g is False
        assert response.bouygues.has_3g is False
        assert response.bouygues.has_4g is False
        assert response.free.has_2g is False
        assert response.free.has_3g is False
        assert response.free.has_4g is False

    @pytest.mark.asyncio
    async def test_no_mobile_sites_found(self, use_case, mock_repository):
        """Test when no mobile sites are found."""
        # Mock empty sites list
        mock_repository.find_nearby.return_value = []

        # Test data
        addresses = [
            NearbyAddressRequestItem(id="id1", address="Remote Location"),
        ]

        # Execute use case
        result = await use_case.execute(addresses)

        # Verify results
        assert len(result) == 1
        response = result[0]

        assert response.id == "id1"
        # All operators should have no coverage
        assert response.orange.has_2g is False
        assert response.orange.has_3g is False
        assert response.orange.has_4g is False
        assert response.SFR.has_2g is False
        assert response.SFR.has_3g is False
        assert response.SFR.has_4g is False
        assert response.bouygues.has_2g is False
        assert response.bouygues.has_3g is False
        assert response.bouygues.has_4g is False
        assert response.free.has_2g is False
        assert response.free.has_3g is False
        assert response.free.has_4g is False

    @pytest.mark.asyncio
    async def test_coverage_aggregation_logic(self, use_case, mock_repository):
        """Test that coverage is correctly aggregated from multiple sites."""
        # Mock multiple sites for the same operator with different coverage
        mock_sites = [
            # Orange site with 2G and 3G
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(x=2.3522, y=48.8566),
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=False),
            ),
            # Another Orange site with 4G
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(x=2.3523, y=48.8567),
                coverage=Coverage(has_2g=False, has_3g=False, has_4g=True),
            ),
        ]
        mock_repository.find_nearby.return_value = mock_sites

        # Test data
        addresses = [
            NearbyAddressRequestItem(id="id1", address="Paris, France"),
        ]

        # Execute use case
        result = await use_case.execute(addresses)

        # Verify that Orange has all technologies (aggregated from both sites)
        assert len(result) == 1
        response = result[0]

        assert response.id == "id1"
        # Orange should have all technologies aggregated from both sites
        assert response.orange.has_2g is True  # From first site
        assert response.orange.has_3g is True  # From first site
        assert response.orange.has_4g is True  # From second site

        # Other operators should have no coverage
        assert response.SFR.has_2g is False
        assert response.SFR.has_3g is False
        assert response.SFR.has_4g is False
        assert response.bouygues.has_2g is False
        assert response.bouygues.has_3g is False
        assert response.bouygues.has_4g is False
        assert response.free.has_2g is False
        assert response.free.has_3g is False
        assert response.free.has_4g is False
