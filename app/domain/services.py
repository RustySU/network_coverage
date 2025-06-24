"""Domain services for business logic."""

from app.domain.entities import (
    Coverage,
    Location,
    MobileSite,
    Operator,
)
from app.domain.repositories import MobileSiteRepository


class MobileCoverageService:
    """Service for mobile coverage operations."""

    def __init__(self, repository: MobileSiteRepository) -> None:
        """Initialize the service with a repository."""
        self.repository = repository

    async def find_nearby_sites(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[MobileSite]:
        """Find mobile sites near a given location."""
        return await self.repository.find_nearby(latitude, longitude, radius_km)
