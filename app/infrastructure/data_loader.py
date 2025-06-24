"""Data loader for importing CSV data into the database."""

import csv
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Coverage, Location, MobileSite, Operator
from app.domain.services import MobileCoverageService
from app.infrastructure.coordinate_utils import lamber93_to_gps
from app.infrastructure.repositories import SQLAlchemyMobileSiteRepository

logger = logging.getLogger(__name__)


class CSVDataLoader:
    """Loader for CSV mobile coverage data."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self.repository = SQLAlchemyMobileSiteRepository(session)
        self.service = MobileCoverageService(self.repository)

    async def load_from_csv(self, csv_file_path: str) -> int:
        """Load mobile sites from CSV file."""
        try:
            logger.info(f"Starting CSV data loading from {csv_file_path}")
            sites = []
            row_count = 0
            processed_count = 0

            logger.info("Reading CSV file...")
            with open(csv_file_path, encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    row_count += 1

                    # Skip empty rows (all values are empty strings, whitespace, or None)
                    if not row or all(
                        not value or not str(value).strip() for value in row.values()
                    ):
                        continue

                    try:
                        site = self._parse_row(row, row_count)
                        sites.append(site)
                        processed_count += 1

                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing row {row_count}: {e}")
                        continue
                    except Exception as e:
                        logger.error(
                            f"Unexpected error parsing row {row_count}: {str(e)}",
                            exc_info=True,
                        )
                        continue

            logger.info(
                f"CSV parsing complete. Found {processed_count} valid rows out of {row_count} total rows."
            )

            if sites:
                logger.info("Saving to database...")
                try:
                    await self.repository.save_many(sites)
                    logger.info(f"Successfully loaded {len(sites)} mobile sites")
                except Exception as e:
                    logger.error(
                        f"Error saving sites to database: {str(e)}", exc_info=True
                    )
                    raise

            return len(sites)

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during CSV loading: {str(e)}", exc_info=True
            )
            raise

    def _parse_row(self, row: dict, row_number: int) -> MobileSite:
        """Parse a CSV row into a MobileSite entity."""
        try:
            operator_str = row["Operateur"].strip()

            # Map operator names to enum values
            operator_map = {
                "Orange": Operator.ORANGE,
                "SFR": Operator.SFR,
                "Bouygues": Operator.BOUYGUES,
                "Free": Operator.FREE,
            }

            if operator_str not in operator_map:
                raise ValueError(f"Unknown operator: {operator_str}")

            operator = operator_map[operator_str]

            # Check if coordinates are already converted (preprocessed CSV)
            if "longitude" in row and "latitude" in row:
                # Preprocessed CSV with GPS coordinates
                try:
                    longitude = float(row["longitude"])
                    latitude = float(row["latitude"])
                except ValueError as e:
                    raise ValueError(f"Invalid GPS coordinates: {e}") from e
            else:
                # Original CSV with Lambert 93 coordinates
                try:
                    x_lambert = float(row["x"])
                    y_lambert = float(row["y"])
                except ValueError as e:
                    raise ValueError(f"Invalid coordinates: {e}") from e

                # Convert Lambert 93 to GPS coordinates
                longitude, latitude = lamber93_to_gps(x_lambert, y_lambert)

            # Parse coverage flags
            try:
                has_2g = bool(int(row["2G"]))
                has_3g = bool(int(row["3G"]))
                has_4g = bool(int(row["4G"]))
            except (ValueError, KeyError) as e:
                raise ValueError(f"Invalid coverage flags: {e}") from e

            location = Location(longitude=longitude, latitude=latitude)
            coverage = Coverage(has_2g=has_2g, has_3g=has_3g, has_4g=has_4g)

            return MobileSite(
                operator=operator,
                location=location,
                coverage=coverage,
            )

        except Exception as e:
            logger.error(f"Error parsing row {row_number}: {str(e)}", exc_info=True)
            raise


async def load_data(csv_file_path: str, session: AsyncSession) -> int:
    """Convenience function to load data from CSV."""
    try:
        logger.info(f"Loading data from {csv_file_path}")
        loader = CSVDataLoader(session)
        result = await loader.load_from_csv(csv_file_path)
        logger.info("Data loading completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in load_data function: {str(e)}", exc_info=True)
        raise
