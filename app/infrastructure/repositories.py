"""SQLAlchemy implementation of repositories."""

import logging

from sqlalchemy import func, select, text
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import (
    Coverage,
    Location,
    MobileSite,
    Operator,
)
from app.domain.exceptions import RepositoryError
from app.domain.repositories import MobileSiteRepository
from app.infrastructure.models import MobileSiteModel

logger = logging.getLogger(__name__)


class SQLAlchemyMobileSiteRepository(MobileSiteRepository):
    """SQLAlchemy implementation of MobileSiteRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self.session = session

    async def save_many(self, sites: list[MobileSite]) -> list[MobileSite]:
        """Save multiple mobile sites."""
        try:
            logger.info(f"Saving {len(sites)} mobile sites to database")
            models = []
            for site in sites:
                model = MobileSiteModel(
                    operator=site.operator.value,
                    x=site.location.x,
                    y=site.location.y,
                    geom=func.ST_SetSRID(
                        func.ST_MakePoint(site.location.x, site.location.y), 4326
                    ),
                    has_2g=site.coverage.has_2g,
                    has_3g=site.coverage.has_3g,
                    has_4g=site.coverage.has_4g,
                )
                models.append(model)

            self.session.add_all(models)
            await self.session.commit()

            logger.info(f"Successfully saved {len(models)} mobile sites")
            return [self._to_entity(model) for model in models]

        except OperationalError as e:
            logger.error(
                f"Database operational error while saving sites: {str(e)}",
                exc_info=True,
            )
            await self.session.rollback()
            raise RepositoryError(f"Database operational error: {str(e)}") from e
        except ProgrammingError as e:
            logger.error(
                f"Database programming error while saving sites: {str(e)}",
                exc_info=True,
            )
            await self.session.rollback()
            raise RepositoryError(f"Database programming error: {str(e)}") from e
        except SQLAlchemyError as e:
            logger.error(
                f"SQLAlchemy error while saving sites: {str(e)}", exc_info=True
            )
            await self.session.rollback()
            raise RepositoryError(f"Database error: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error while saving sites: {str(e)}", exc_info=True
            )
            await self.session.rollback()
            raise RepositoryError(f"Unexpected database error: {str(e)}") from e

    async def find_nearby(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[MobileSite]:
        """Find mobile sites near a given location."""
        try:
            logger.debug(
                f"Searching for sites near ({latitude}, {longitude}) within {radius_km}km"
            )

            # Use a hybrid approach: SQLAlchemy functions with minimal raw text for geography casting
            # This ensures accurate spherical distance calculations while maintaining type safety
            query = select(MobileSiteModel).where(
                text("""
                    ST_DWithin(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                        :radius_meters
                    )
                """).bindparams(
                    longitude=longitude,
                    latitude=latitude,
                    radius_meters=radius_km * 1000
                )
            )

            # Execute query
            result = await self.session.execute(query)
            models = result.scalars().all()

            # Convert to domain entities
            results = []
            for model in models:
                try:
                    site = self._to_entity(model)
                    results.append(site)
                except Exception as e:
                    logger.error(
                        f"Error converting model to entity: {str(e)}", exc_info=True
                    )
                    # Skip this model and continue with others
                    continue

            logger.debug(f"Found {len(results)} sites near ({latitude}, {longitude})")
            return results

        except OperationalError as e:
            logger.error(
                f"Database operational error in find_nearby: {str(e)}", exc_info=True
            )
            raise RepositoryError(f"Database operational error: {str(e)}") from e
        except ProgrammingError as e:
            logger.error(
                f"Database programming error in find_nearby: {str(e)}", exc_info=True
            )
            raise RepositoryError(f"Database programming error: {str(e)}") from e
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error in find_nearby: {str(e)}", exc_info=True)
            raise RepositoryError(f"Database error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in find_nearby: {str(e)}", exc_info=True)
            raise RepositoryError(f"Unexpected database error: {str(e)}") from e

    def _to_entity(self, model: MobileSiteModel) -> MobileSite:
        """Convert database model to domain entity."""
        try:
            location = Location(x=model.x_value, y=model.y_value)
            coverage = Coverage(
                has_2g=model.has_2g_value,
                has_3g=model.has_3g_value,
                has_4g=model.has_4g_value,
            )

            # Convert operator string to enum
            operator_map = {
                "Orange": Operator.ORANGE,
                "SFR": Operator.SFR,
                "Bouygues": Operator.BOUYGUES,
                "Free": Operator.FREE,
            }
            operator = operator_map.get(model.operator_value)
            if not operator:
                raise ValueError(f"Unknown operator: {model.operator_value}")

            return MobileSite(
                operator=operator,
                location=location,
                coverage=coverage,
            )
        except Exception as e:
            logger.error(f"Error converting model to entity: {str(e)}", exc_info=True)
            raise
