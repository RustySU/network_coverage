"""Tests for repository functionality."""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities import Coverage, Location, MobileSite, Operator
from app.infrastructure.models import Base
from app.infrastructure.repositories import SQLAlchemyMobileSiteRepository


class TestSQLAlchemyMobileSiteRepository:
    """Combined unit and integration tests for SQLAlchemyMobileSiteRepository."""

    # Unit test fixtures
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def unit_repository(
        self, mock_session: AsyncMock
    ) -> SQLAlchemyMobileSiteRepository:
        """Create a repository with mock session for unit tests."""
        return SQLAlchemyMobileSiteRepository(mock_session)

    # Integration test fixtures
    @pytest.fixture
    async def test_engine(self):
        """Create a test database engine with a temporary test database."""
        # Generate a unique database name for this test run
        db_name = f"test_coverage_{uuid.uuid4().hex[:8]}"

        # First, connect to the default postgres database to create our test database
        admin_db_url = "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
        admin_engine = create_async_engine(admin_db_url, echo=False)

        # Create the test database
        async with admin_engine.connect() as conn:
            # Set autocommit mode for DDL operations
            await conn.execute(text("COMMIT"))
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            await conn.execute(text(f"CREATE DATABASE {db_name}"))

        await admin_engine.dispose()

        # Now connect to our test database
        test_db_url = f"postgresql+asyncpg://postgres:postgres@postgres:5432/{db_name}"
        test_engine = create_async_engine(
            test_db_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
        )

        # Set up the test database with PostGIS and tables
        async with test_engine.begin() as conn:
            # Enable PostGIS extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        yield test_engine

        # Cleanup: dispose of the test engine first
        await test_engine.dispose()

        # Then drop the test database
        cleanup_engine = create_async_engine(admin_db_url, echo=False)
        async with cleanup_engine.connect() as conn:
            # Set autocommit mode for DDL operations
            await conn.execute(text("COMMIT"))
            # Terminate any remaining connections to the test database
            await conn.execute(
                text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            )
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))

        await cleanup_engine.dispose()

    @pytest.fixture
    async def test_session(self, test_engine) -> AsyncGenerator[AsyncSession, None]:
        """Create a test session."""
        async_session = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        session = async_session()
        yield session
        await session.close()

    @pytest.fixture
    async def repository(
        self, test_session: AsyncSession
    ) -> SQLAlchemyMobileSiteRepository:
        """Create a repository instance with the test session for integration tests."""
        return SQLAlchemyMobileSiteRepository(test_session)

    @pytest.fixture
    async def sample_sites(self, test_session: AsyncSession) -> list[MobileSite]:
        """Create sample mobile sites for testing."""
        sites = [
            # Paris center - Eiffel Tower area
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(
                    longitude=2.2945, latitude=48.8584
                ),  # Eiffel Tower coordinates
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=True),
            ),
            # Paris - Notre Dame area
            MobileSite(
                operator=Operator.SFR,
                location=Location(
                    longitude=2.3499, latitude=48.8530
                ),  # Notre Dame coordinates
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=False),
            ),
            # Paris - Arc de Triomphe area
            MobileSite(
                operator=Operator.BOUYGUES,
                location=Location(
                    longitude=2.2950, latitude=48.8738
                ),  # Arc de Triomphe coordinates
                coverage=Coverage(has_2g=True, has_3g=False, has_4g=True),
            ),
            # Paris - Montmartre area
            MobileSite(
                operator=Operator.FREE,
                location=Location(
                    longitude=2.3424, latitude=48.8867
                ),  # Sacré-Cœur coordinates
                coverage=Coverage(has_2g=False, has_3g=True, has_4g=True),
            ),
            # Lyon - far from Paris (should not be found in Paris searches)
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(
                    longitude=4.8357, latitude=45.7640
                ),  # Lyon coordinates
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=True),
            ),
        ]

        # Save sites to database
        repository = SQLAlchemyMobileSiteRepository(test_session)
        try:
            await repository.save_many(sites)
            await test_session.commit()  # Ensure data is committed
        except Exception as e:
            await test_session.rollback()
            raise e

        return sites

    # Unit tests
    def test_to_entity_with_string_operator(
        self, unit_repository: SQLAlchemyMobileSiteRepository
    ) -> None:
        """Test _to_entity method with string operator from database."""
        # Create a mock model with string operator
        mock_model = MagicMock()
        mock_model.configure_mock(
            operator_value="Orange",
            longitude_value=100.0,
            latitude_value=200.0,
            has_2g_value=True,
            has_3g_value=True,
            has_4g_value=False,
        )

        entity = unit_repository._to_entity(mock_model)

        assert entity.operator == Operator.ORANGE
        assert entity.location.longitude == 100.0
        assert entity.location.latitude == 200.0
        assert entity.coverage.has_2g is True
        assert entity.coverage.has_3g is True
        assert entity.coverage.has_4g is False

    def test_to_entity_with_invalid_operator(
        self, unit_repository: SQLAlchemyMobileSiteRepository
    ) -> None:
        """Test _to_entity method with invalid operator string."""
        # Create a mock model with invalid operator
        mock_model = MagicMock()
        mock_model.configure_mock(
            operator_value="InvalidOperator",
            longitude_value=100.0,
            latitude_value=200.0,
            has_2g_value=True,
            has_3g_value=True,
            has_4g_value=False,
        )

        with pytest.raises(ValueError, match="Unknown operator"):
            unit_repository._to_entity(mock_model)

    def test_to_entity_all_operators(
        self, unit_repository: SQLAlchemyMobileSiteRepository
    ) -> None:
        """Test _to_entity method with all valid operators."""
        operators = ["Orange", "SFR", "Bouygues", "Free"]
        expected_enums = [
            Operator.ORANGE,
            Operator.SFR,
            Operator.BOUYGUES,
            Operator.FREE,
        ]

        for operator_str, expected_enum in zip(operators, expected_enums, strict=False):
            mock_model = MagicMock()
            mock_model.configure_mock(
                operator_value=operator_str,
                longitude_value=100.0,
                latitude_value=200.0,
                has_2g_value=True,
                has_3g_value=True,
                has_4g_value=False,
            )

            entity = unit_repository._to_entity(mock_model)
            assert entity.operator == expected_enum

    # Integration tests
    @pytest.mark.asyncio
    async def test_find_nearby_paris_larger_radius(
        self, repository: SQLAlchemyMobileSiteRepository, sample_sites: list[MobileSite]
    ) -> None:
        """Test finding sites near Paris center with a larger radius."""
        # Search from Eiffel Tower coordinates with larger radius
        search_lat, search_lon = 48.8584, 2.2945
        radius_km = 50.0  # Larger radius should include more Paris sites

        result = await repository.find_nearby(
            latitude=search_lat, longitude=search_lon, radius_km=radius_km
        )

        # Should find exactly 4 sites (all Paris sites, no Lyon)
        assert len(result) == 4, f"Expected 4 sites, but found {len(result)}"

        # Verify that Lyon is not included (it should be ~400km away)
        lyon_sites_in_result = [
            site
            for site in result
            if site.location.longitude == 4.8357 and site.location.latitude == 45.7640
        ]
        assert len(lyon_sites_in_result) == 0, (
            "Lyon site should not be within 50km of Paris"
        )

    @pytest.mark.asyncio
    async def test_find_nearby_notre_dame(
        self, repository: SQLAlchemyMobileSiteRepository, sample_sites: list[MobileSite]
    ) -> None:
        """Test finding sites near Notre Dame."""
        # Search from Notre Dame coordinates
        search_lat, search_lon = 48.8530, 2.3499
        radius_km = 2.0

        result = await repository.find_nearby(
            latitude=search_lat, longitude=search_lon, radius_km=radius_km
        )

        assert len(result) == 1, f"Expected 1 site, but found {len(result)}"
        # Should find the Notre Dame site
        notre_dame_site = next(
            (
                site
                for site in result
                if site.location.longitude == 2.3499
                and site.location.latitude == 48.8530
            ),
            None,
        )
        assert notre_dame_site is not None
        assert notre_dame_site.operator == Operator.SFR
        assert notre_dame_site.location.longitude == 2.3499
        assert notre_dame_site.location.latitude == 48.8530

    @pytest.mark.asyncio
    async def test_find_nearby_no_results(
        self, repository: SQLAlchemyMobileSiteRepository, sample_sites: list[MobileSite]
    ) -> None:
        """Test finding sites in a location with no coverage."""
        # Search from a location far from any sites
        search_lat, search_lon = 0.0, 0.0  # Middle of the ocean
        radius_km = 5.0

        result = await repository.find_nearby(
            latitude=search_lat, longitude=search_lon, radius_km=radius_km
        )

        # Should return empty list
        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_save_many_integration(
        self, repository: SQLAlchemyMobileSiteRepository, test_session: AsyncSession
    ) -> None:
        """Test saving multiple mobile sites to the database."""
        # Create test sites
        sites = [
            MobileSite(
                operator=Operator.ORANGE,
                location=Location(longitude=2.3522, latitude=48.8566),  # Paris center
                coverage=Coverage(has_2g=True, has_3g=True, has_4g=True),
            ),
            MobileSite(
                operator=Operator.SFR,
                location=Location(
                    longitude=2.3523, latitude=48.8567
                ),  # Slightly offset
                coverage=Coverage(has_2g=True, has_3g=False, has_4g=True),
            ),
            MobileSite(
                operator=Operator.BOUYGUES,
                location=Location(longitude=2.3524, latitude=48.8568),  # Another offset
                coverage=Coverage(has_2g=False, has_3g=True, has_4g=True),
            ),
        ]

        # Save the sites
        saved_sites = await repository.save_many(sites)

        # Verify the return value
        assert len(saved_sites) == 3, f"Expected 3 saved sites, got {len(saved_sites)}"

        # Verify each saved site has the correct data
        for i, saved_site in enumerate(saved_sites):
            original_site = sites[i]
            assert saved_site.operator == original_site.operator
            assert saved_site.location.longitude == original_site.location.longitude
            assert saved_site.location.latitude == original_site.location.latitude
            assert saved_site.coverage.has_2g == original_site.coverage.has_2g
            assert saved_site.coverage.has_3g == original_site.coverage.has_3g
            assert saved_site.coverage.has_4g == original_site.coverage.has_4g

        # Verify the sites were actually saved to the database
        count_result = await test_session.execute(
            text("SELECT COUNT(*) FROM mobile_sites")
        )
        count = count_result.scalar()
        assert count == 3, f"Expected 3 sites in database, found {count}"
