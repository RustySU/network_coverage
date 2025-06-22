"""Repository interfaces for domain entities."""

from abc import ABC, abstractmethod

from app.domain.entities import MobileSite


class MobileSiteRepository(ABC):
    """Repository interface for mobile sites."""

    @abstractmethod
    async def save_many(self, sites: list[MobileSite]) -> list[MobileSite]:
        """Save multiple mobile sites."""
        pass

    @abstractmethod
    async def find_nearby(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[MobileSite]:
        """Find mobile sites near a given location."""
        pass
