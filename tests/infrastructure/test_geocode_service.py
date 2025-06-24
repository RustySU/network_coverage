"""Tests for geocoding service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import asyncio

from app.domain.exceptions import GeocodingError
from app.infrastructure.geocode_service import GeocodingService


class TestGeocodingService:
    """Test GeocodingService with deduplicated and parameterized tests."""

    @pytest.fixture
    def geocoding_service(self):
        """Create a GeocodingService instance for testing."""
        return GeocodingService()

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Create a mock client instance
            mock_client_instance = MagicMock()

            # Set up the context manager behavior
            mock_client_class.return_value = mock_client_instance
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)

            # Make the get method async
            mock_client_instance.get = AsyncMock()

            yield mock_client_instance

    @pytest.mark.asyncio
    async def test_geocode_single_address_success(
        self, geocoding_service, mock_httpx_client
    ):
        """Test successful geocoding of a single address."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [2.3522, 48.8566]  # [longitude, latitude]
                    },
                    "properties": {"score": 0.95},
                }
            ]
        }
        mock_httpx_client.get.return_value = mock_response

        result = await geocoding_service._geocode_single_address(
            "test_id", "Paris, France"
        )

        assert result == {"latitude": 48.8566, "longitude": 2.3522}
        mock_httpx_client.get.assert_called_once_with(
            "https://api-adresse.data.gouv.fr/search/",
            params={"q": "Paris, France", "limit": 1},
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mock_json,expected",
        [
            ({"features": []}, None),
            (
                {
                    "features": [
                        {
                            "geometry": {"coordinates": [2.3522]},
                            "properties": {"score": 0.95},
                        }
                    ]
                },
                None,
            ),
            ({"features": [{"properties": {"score": 0.95}}]}, None),
            ({"features": [{"geometry": {}, "properties": {"score": 0.95}}]}, None),
        ],
    )
    async def test_geocode_single_address_various_no_results(
        self, geocoding_service, mock_httpx_client, mock_json, expected
    ):
        """Test geocoding with no features, invalid/missing coordinates, or missing geometry."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_json
        mock_httpx_client.get.return_value = mock_response
        result = await geocoding_service._geocode_single_address(
            "test_id", "Any Address"
        )
        assert result is expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "side_effect",
        [
            httpx.TimeoutException("Request timeout"),
            httpx.ConnectError("Connection failed"),
            httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=MagicMock()
            ),
            httpx.RequestError("Request failed"),
            ValueError("Invalid JSON"),
            Exception("Unexpected error"),
        ],
    )
    async def test_geocode_single_address_errors_return_none(
        self, geocoding_service, mock_httpx_client, side_effect
    ):
        """Test geocoding with various exceptions returns None."""
        if isinstance(side_effect, ValueError):
            mock_response = MagicMock()
            mock_response.json.side_effect = side_effect
            mock_httpx_client.get.return_value = mock_response
        else:
            mock_httpx_client.get.side_effect = side_effect
        result = await geocoding_service._geocode_single_address(
            "test_id", "Paris, France"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_geocode_single_address_custom_base_url(self):
        """Test geocoding service with custom base URL."""
        custom_service = GeocodingService("https://custom-api.example.com/")
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "features": [
                    {
                        "geometry": {"coordinates": [2.3522, 48.8566]},
                        "properties": {"score": 0.95},
                    }
                ]
            }
            mock_client_instance.get.return_value = mock_response
            result = await custom_service._geocode_single_address(
                "test_id", "Paris, France"
            )
            assert result == {"latitude": 48.8566, "longitude": 2.3522}
            mock_client_instance.get.assert_called_once_with(
                "https://custom-api.example.com/",
                params={"q": "Paris, France", "limit": 1},
            )

    @pytest.mark.asyncio
    async def test_geocode_addresses_empty_dict(self, geocoding_service):
        """Test geocoding with empty addresses dictionary."""
        result = await geocoding_service.geocode_addresses({})

        assert result == {}

    @pytest.mark.asyncio
    async def test_geocode_addresses_single_address_success(self, geocoding_service):
        """Test geocoding a single address successfully."""
        addresses = {"addr1": "Paris, France"}

        with patch.object(geocoding_service, "_geocode_single_address") as mock_geocode:
            mock_geocode.return_value = {"latitude": 48.8566, "longitude": 2.3522}

            result = await geocoding_service.geocode_addresses(addresses)

            assert result == {"addr1": {"latitude": 48.8566, "longitude": 2.3522}}
            mock_geocode.assert_called_once_with("addr1", "Paris, France")

    @pytest.mark.asyncio
    async def test_geocode_addresses_multiple_addresses_success(
        self, geocoding_service
    ):
        """Test geocoding multiple addresses successfully."""
        addresses = {
            "addr1": "Paris, France",
            "addr2": "Lyon, France",
            "addr3": "Marseille, France",
        }

        with patch.object(geocoding_service, "_geocode_single_address") as mock_geocode:
            mock_geocode.side_effect = [
                {"latitude": 48.8566, "longitude": 2.3522},  # Paris
                {"latitude": 45.7640, "longitude": 4.8357},  # Lyon
                {"latitude": 43.2965, "longitude": 5.3698},  # Marseille
            ]

            result = await geocoding_service.geocode_addresses(addresses)

            expected = {
                "addr1": {"latitude": 48.8566, "longitude": 2.3522},
                "addr2": {"latitude": 45.7640, "longitude": 4.8357},
                "addr3": {"latitude": 43.2965, "longitude": 5.3698},
            }
            assert result == expected
            assert mock_geocode.call_count == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "side_effect,expected",
        [
            (
                [
                    {"latitude": 48.8566, "longitude": 2.3522},
                    None,
                    {"latitude": 45.7640, "longitude": 4.8357},
                ],
                2,
            ),
            (
                [
                    {"latitude": 48.8566, "longitude": 2.3522},
                    GeocodingError("Connection failed"),
                    {"latitude": 45.7640, "longitude": 4.8357},
                ],
                2,
            ),
            ([None, None], 0),
            ([GeocodingError("Connection failed"), GeocodingError("Timeout")], 0),
            ([TimeoutError("Global timeout")], 0),
            ([Exception("Critical error")], 0),
        ],
    )
    async def test_geocode_addresses_various_results(
        self, geocoding_service, side_effect, expected
    ):
        """Test geocoding_addresses with mixed, all-failure, and exception scenarios."""
        addresses = {f"addr{i}": f"Address {i}" for i in range(len(side_effect))}
        with patch.object(geocoding_service, "_geocode_single_address") as mock_geocode:
            mock_geocode.side_effect = side_effect
            result = await geocoding_service.geocode_addresses(addresses)
            assert len(result) == expected

    @pytest.mark.asyncio
    async def test_geocode_addresses_concurrent_execution(self, geocoding_service):
        """Test that geocoding happens concurrently."""
        addresses = {
            "addr1": "Paris, France",
            "addr2": "Lyon, France",
            "addr3": "Marseille, France",
        }

        # Track call order to verify concurrent execution
        call_order = []

        async def mock_geocode_with_delay(address_id, address):
            call_order.append(address_id)
            # Simulate different processing times
            if address_id == "addr1":
                await asyncio.sleep(0.1)
            elif address_id == "addr2":
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.15)
            return {"latitude": 0.0, "longitude": 0.0}

        with patch.object(
            geocoding_service,
            "_geocode_single_address",
            side_effect=mock_geocode_with_delay,
        ):
            result = await geocoding_service.geocode_addresses(addresses)

            # All addresses should be processed
            assert len(result) == 3
            # The call order should be the order they were added (concurrent start)
            assert call_order == ["addr1", "addr2", "addr3"]

    @pytest.mark.asyncio
    async def test_geocode_addresses_large_batch(self, geocoding_service):
        """Test geocoding with a large batch of addresses."""
        addresses = {f"addr{i}": f"Address {i}" for i in range(100)}

        with patch.object(geocoding_service, "_geocode_single_address") as mock_geocode:
            # Return coordinates for even addresses, None for odd addresses
            mock_geocode.side_effect = [
                {"latitude": float(i), "longitude": float(i)} if i % 2 == 0 else None
                for i in range(100)
            ]

            result = await geocoding_service.geocode_addresses(addresses)

            # Should have 50 successful geocodings (even numbers)
            assert len(result) == 50
            assert mock_geocode.call_count == 100

    @pytest.mark.asyncio
    async def test_geocode_addresses_none_input(self, geocoding_service):
        """Test geocoding with None input."""
        result = await geocoding_service.geocode_addresses(None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_geocode_addresses_empty_strings(self, geocoding_service):
        """Test geocoding with empty string addresses."""
        addresses = {"addr1": "", "addr2": "   ", "addr3": "Valid Address"}

        with patch.object(geocoding_service, "_geocode_single_address") as mock_geocode:
            mock_geocode.side_effect = [
                None,
                None,
                {"latitude": 48.8566, "longitude": 2.3522},
            ]

            result = await geocoding_service.geocode_addresses(addresses)

            expected = {"addr3": {"latitude": 48.8566, "longitude": 2.3522}}
            assert result == expected
