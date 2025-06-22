"""API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas import (
    NearbyAddressRequestItem,
    NearbyAddressResponseItem,
)
from app.application.use_cases import FindNearbySitesByAddressUseCase
from app.infrastructure.database import get_db
from app.infrastructure.geocode_service import GeocodingService
from app.infrastructure.repositories import SQLAlchemyMobileSiteRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Dependency injection


def get_repository(
    session: AsyncSession = Depends(get_db),
) -> SQLAlchemyMobileSiteRepository:
    """Get repository instance."""
    return SQLAlchemyMobileSiteRepository(session)


def get_geocoding_service() -> GeocodingService:
    """Get geocoding service instance."""
    return GeocodingService()


def get_find_nearby_by_address_use_case(
    geocoding_service: GeocodingService = Depends(get_geocoding_service),
    repository: SQLAlchemyMobileSiteRepository = Depends(get_repository),
) -> FindNearbySitesByAddressUseCase:
    """Get find nearby by address use case instance."""
    return FindNearbySitesByAddressUseCase(geocoding_service, repository)


# Nearby search endpoint
@router.post("/api/v1/nearby", response_model=list[NearbyAddressResponseItem])
async def find_nearby_sites_by_address(
    addresses: list[NearbyAddressRequestItem],
    use_case: FindNearbySitesByAddressUseCase = Depends(
        get_find_nearby_by_address_use_case
    ),
) -> list[NearbyAddressResponseItem]:
    """Find mobile sites near a given list of addresses."""
    logger.info(f"Processing request for {len(addresses)} addresses")

    # Validate input
    if not addresses:
        logger.warning("Empty address list received")
        return []

    if len(addresses) > 100:  # Reasonable limit
        logger.warning(f"Too many addresses requested: {len(addresses)}")
        raise HTTPException(
            status_code=400,
            detail="Too many addresses requested. Maximum 100 addresses allowed.",
        )

    # Execute use case
    results = await use_case.execute(addresses)

    logger.info(f"Successfully processed request for {len(addresses)} addresses")
    return results


# Root endpoint
@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    from app.config import settings

    return {
        "message": "Mobile Coverage API",
        "version": settings.api_version,
        "docs": "/docs",
    }
