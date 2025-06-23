"""Application layer use cases."""

import logging
import math

from app.application.schemas import (
    CoverageInfo,
    NearbyAddressRequestItem,
    NearbyAddressResponseItem,
)
from app.domain.exceptions import GeocodingError, RepositoryError
from app.domain.repositories import MobileSiteRepository
from app.domain.services import MobileCoverageService
from app.infrastructure.coordinate_utils import calculate_distance_km

# Technology-specific search radii
TECHNOLOGY_RADII = {
    "2G": 30.0,  # 2G coverage radius in km
    "3G": 5.0,   # 3G coverage radius in km
    "4G": 10.0,  # 4G coverage radius in km
}

# Use the longest search radius (2G: 30km) to cover all technologies
SEARCH_RADIUS_KM = 30.0

logger = logging.getLogger(__name__)


class FindNearbySitesByAddressUseCase:
    """Use case for finding nearby mobile sites for a list of addresses."""

    def __init__(
        self,
        geocoding_service,
        repository: MobileSiteRepository,  # Abstract repository interface
    ):
        self.geocoding_service = geocoding_service
        self.repository = repository

    async def execute(
        self, addresses: list[NearbyAddressRequestItem]
    ) -> list[NearbyAddressResponseItem]:
        """
        Executes the use case.

        Args:
            addresses: List of address items to find nearby mobile sites for.

        Returns:
            A list of NearbyAddressResponseItem with coverage information for each address.
        """
        try:
            # Convert list to dictionary for geocoding service
            addresses_dict = {item.id: item.address for item in addresses}

            # Step 1: Geocode all addresses concurrently
            logger.info(f"Starting geocoding for {len(addresses)} addresses")
            coordinates = await self._geocode_addresses_safe(addresses_dict)

            # Step 2: Process addresses sequentially to avoid session concurrency issues
            logger.info(f"Processing {len(addresses)} addresses for coverage data")
            results = []
            for i, address_item in enumerate(addresses, 1):
                try:
                    address_id = address_item.id
                    coords = coordinates.get(address_id)

                    if coords:
                        # Process address with coordinates
                        logger.debug(
                            f"Processing address {i}/{len(addresses)}: {address_id}"
                        )
                        result = await self._process_address_with_coords(
                            address_id, coords
                        )
                        results.append(result)
                    else:
                        # Create empty coverage for failed geocoding
                        logger.warning(
                            f"Address {address_id} failed geocoding, returning empty coverage"
                        )
                        empty_coverage = CoverageInfo(
                            **{"2G": False, "3G": False, "4G": False}
                        )
                        results.append(
                            NearbyAddressResponseItem(
                                id=address_id,
                                orange=empty_coverage,
                                SFR=empty_coverage,
                                bouygues=empty_coverage,
                                free=empty_coverage,
                            )
                        )
                except Exception as e:
                    logger.error(
                        f"Error processing address {address_item.id}: {str(e)}",
                        exc_info=True,
                    )
                    # Return empty coverage for failed processing
                    empty_coverage = CoverageInfo(
                        **{"2G": False, "3G": False, "4G": False}
                    )
                    results.append(
                        NearbyAddressResponseItem(
                            id=address_item.id,
                            orange=empty_coverage,
                            SFR=empty_coverage,
                            bouygues=empty_coverage,
                            free=empty_coverage,
                        )
                    )

            logger.info(f"Successfully processed {len(results)} addresses")
            return results

        except Exception as e:
            logger.error(
                f"Critical error in use case execution: {str(e)}", exc_info=True
            )
            # Return empty results for all addresses in case of critical failure
            return [
                NearbyAddressResponseItem(
                    id=address_item.id,
                    orange=CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                    SFR=CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                    bouygues=CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                    free=CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                )
                for address_item in addresses
            ]

    async def _geocode_addresses_safe(
        self, addresses_dict: dict[str, str]
    ) -> dict[str, dict[str, float]]:
        """Safely geocode addresses with proper error handling."""
        try:
            return await self.geocoding_service.geocode_addresses(addresses_dict)
        except GeocodingError as e:
            logger.error(f"Geocoding error: {str(e)}", exc_info=True)
            return {}  # Return empty dict to trigger empty coverage for all addresses
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {str(e)}", exc_info=True)
            return {}  # Return empty dict to trigger empty coverage for all addresses

    async def _process_address_with_coords(
        self, address_id: str, coords: dict[str, float]
    ) -> NearbyAddressResponseItem:
        """Process an address that was successfully geocoded."""
        try:
            # Use the injected repository (abstract interface)
            coverage_service = MobileCoverageService(self.repository)

            coverage_info = await self._find_coverage_for_location(
                coverage_service,
                coords["latitude"],
                coords["longitude"],
            )
            return NearbyAddressResponseItem(
                id=address_id,
                orange=coverage_info["orange"],
                SFR=coverage_info["sfr"],
                bouygues=coverage_info["bouygues"],
                free=coverage_info["free"],
            )
        except RepositoryError as e:
            logger.error(
                f"Database error for address {address_id}: {str(e)}", exc_info=True
            )
            # Return empty coverage for database errors
            empty_coverage = CoverageInfo(**{"2G": False, "3G": False, "4G": False})
            return NearbyAddressResponseItem(
                id=address_id,
                orange=empty_coverage,
                SFR=empty_coverage,
                bouygues=empty_coverage,
                free=empty_coverage,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error processing address {address_id}: {str(e)}",
                exc_info=True,
            )
            # Return empty coverage for unexpected errors
            empty_coverage = CoverageInfo(**{"2G": False, "3G": False, "4G": False})
            return NearbyAddressResponseItem(
                id=address_id,
                orange=empty_coverage,
                SFR=empty_coverage,
                bouygues=empty_coverage,
                free=empty_coverage,
            )

    async def _find_coverage_for_location(
        self,
        coverage_service: MobileCoverageService,
        latitude: float,
        longitude: float,
    ) -> dict[str, CoverageInfo]:
        """
        Finds mobile coverage for a single location.
        Searches for all sites within 30km and checks their technology capabilities.
        """
        try:
            # Initialize coverage for all operators
            coverage_by_operator = {
                "orange": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "sfr": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "bouygues": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "free": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
            }

            # Search for all sites within the longest radius (30km)
            sites = await coverage_service.find_nearby_sites(
                latitude, longitude, SEARCH_RADIUS_KM
            )

            # Check each site's capabilities and update coverage accordingly
            for site in sites:
                operator_name = site.operator.value.lower()
                if operator_name in coverage_by_operator:
                    # Calculate distance from search point to site
                    distance_km = calculate_distance_km(
                        latitude, longitude, site.location.latitude, site.location.longitude
                    )
                    
                    # Update coverage based on what this site supports and distance
                    if site.coverage.has_2g and distance_km <= TECHNOLOGY_RADII["2G"]:
                        coverage_by_operator[operator_name].has_2g = True
                    if site.coverage.has_3g and distance_km <= TECHNOLOGY_RADII["3G"]:
                        coverage_by_operator[operator_name].has_3g = True
                    if site.coverage.has_4g and distance_km <= TECHNOLOGY_RADII["4G"]:
                        coverage_by_operator[operator_name].has_4g = True

            return coverage_by_operator

        except RepositoryError as e:
            logger.error(
                f"Database error in coverage lookup for coordinates ({latitude}, {longitude}): {str(e)}",
                exc_info=True,
            )
            # Return empty coverage for database errors
            return {
                "orange": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "sfr": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "bouygues": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "free": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
            }
        except Exception as e:
            logger.error(
                f"Unexpected error in coverage lookup for coordinates ({latitude}, {longitude}): {str(e)}",
                exc_info=True,
            )
            # Return empty coverage for unexpected errors
            return {
                "orange": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "sfr": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "bouygues": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
                "free": CoverageInfo(**{"2G": False, "3G": False, "4G": False}),
            }
