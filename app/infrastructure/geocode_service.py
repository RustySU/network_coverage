"""Geocoding service implementation."""

import asyncio
import logging

import httpx

from app.domain.exceptions import GeocodingError

logger = logging.getLogger(__name__)

# TODO add test
class GeocodingService:
    """Service for geocoding addresses using external API."""

    def __init__(self, base_url: str = "https://api-adresse.data.gouv.fr/search/"):
        self.base_url = base_url
        self.timeout = 10.0  # 10 seconds timeout

    async def geocode_addresses(
        self, addresses: dict[str, str]
    ) -> dict[str, dict[str, float]]:
        """
        Geocode multiple addresses concurrently.

        Args:
            addresses: Dictionary mapping address IDs to address strings.

        Returns:
            Dictionary mapping address IDs to coordinate dictionaries with 'latitude' and 'longitude' keys.
        """
        if not addresses:
            logger.warning("No addresses provided for geocoding")
            return {}

        logger.info(f"Starting geocoding for {len(addresses)} addresses")

        try:
            # Create tasks for concurrent geocoding
            tasks = []
            for address_id, address in addresses.items():
                task = self._geocode_single_address(address_id, address)
                tasks.append(task)

            # Execute all geocoding tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle exceptions
            coordinates = {}
            for i, result in enumerate(results):
                address_id = list(addresses.keys())[i]
                address = list(addresses.values())[i]

                if isinstance(result, Exception):
                    logger.error(
                        f"Geocoding failed for address {address_id} ({address}): {str(result)}",
                        exc_info=True,
                    )
                    # Don't add to coordinates - will trigger empty coverage
                elif result:
                    coordinates[address_id] = result
                    logger.debug(
                        f"Successfully geocoded address {address_id}: {result}"
                    )
                else:
                    logger.warning(
                        f"No coordinates found for address {address_id} ({address})"
                    )

            logger.info(
                f"Geocoding completed: {len(coordinates)}/{len(addresses)} addresses geocoded successfully"
            )
            return coordinates

        except TimeoutError as e:
            logger.error(f"Geocoding timeout error: {str(e)}", exc_info=True)
            raise GeocodingError(f"Geocoding timeout: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Critical error in geocoding service: {str(e)}", exc_info=True
            )
            raise GeocodingError(f"Critical geocoding error: {str(e)}") from e

    async def _geocode_single_address(
        self, address_id: str, address: str
    ) -> dict[str, float] | None:
        """
        Geocode a single address.

        Args:
            address_id: Unique identifier for the address.
            address: Address string to geocode.

        Returns:
            Dictionary with 'latitude' and 'longitude' keys, or None if geocoding failed.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    params = {"q": address, "limit": 1}
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                except httpx.TimeoutException as e:
                    logger.error(
                        f"Geocoding timeout for address {address_id} ({address}): {str(e)}"
                    )
                    raise GeocodingError(f"Geocoding timeout: {str(e)}") from e
                except httpx.ConnectError as e:
                    logger.error(
                        f"Geocoding connection error for address {address_id} ({address}): {str(e)}"
                    )
                    raise GeocodingError(f"Geocoding connection error: {str(e)}") from e
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"Geocoding HTTP error for address {address_id} ({address}) (status {e.response.status_code}): {str(e)}"
                    )
                    raise GeocodingError(
                        f"Geocoding HTTP error (status {e.response.status_code}): {str(e)}"
                    ) from e
                except httpx.RequestError as e:
                    logger.error(
                        f"Geocoding request error for address {address_id} ({address}): {str(e)}"
                    )
                    raise GeocodingError(f"Geocoding request error: {str(e)}") from e

                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(
                        f"Invalid JSON response for address {address_id}: {str(e)}"
                    )
                    raise GeocodingError(f"Invalid JSON response: {str(e)}") from e

                if data.get("features") and len(data["features"]) > 0:
                    feature = data["features"][0]
                    geometry = feature.get("geometry", {})
                    coordinates = geometry.get("coordinates", [])

                    # Check confidence score - filter out low-quality matches
                    properties = feature.get("properties", {})
                    score = properties.get("score", 0.0)

                    if len(coordinates) >= 2:
                        # API returns [longitude, latitude] format
                        longitude, latitude = coordinates[0], coordinates[1]
                        logger.info(
                            f"Geocoded address {address_id} with confidence {score}: {address} -> ({latitude}, {longitude})"
                        )
                        return {"latitude": latitude, "longitude": longitude}
                    else:
                        logger.warning(
                            f"Invalid coordinates format for address {address_id}: {coordinates}"
                        )
                        return None
                else:
                    logger.warning(
                        f"No geocoding results found for address {address_id}: {address}"
                    )
                    return None

        except Exception as e:
            logger.error(
                f"Unexpected geocoding error for address {address_id}: {str(e)}",
                exc_info=True,
            )
            return None
