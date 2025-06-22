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

    def create_mobile_site(
        self,
        operator: Operator,
        x: float,
        y: float,
        has_2g: bool,
        has_3g: bool,
        has_4g: bool,
    ) -> MobileSite:
        """Create a new mobile site."""
        location = Location(x=x, y=y)
        coverage = Coverage(has_2g=has_2g, has_3g=has_3g, has_4g=has_4g)
        return MobileSite(operator=operator, location=location, coverage=coverage)
