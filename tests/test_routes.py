import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.application.use_cases import FindNearbySitesByAddressUseCase
from app.routes import get_find_nearby_by_address_use_case


class TestRoutes:
    """Test class for API routes."""

    @pytest.fixture(autouse=True)
    def client(self):
        """Create a test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def mock_use_case(self):
        """Create a mock use case."""
        return AsyncMock(spec=FindNearbySitesByAddressUseCase)

    @pytest.fixture
    def sample_response_data(self):
        """Sample response data for testing."""
        return [
            {
                "id": "addr1",
                "orange": {"2G": True, "3G": True, "4G": True},
                "SFR": {"2G": True, "3G": True, "4G": False},
                "bouygues": {"2G": False, "3G": True, "4G": True},
                "free": {"2G": False, "3G": False, "4G": True},
            }
        ]

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Mobile Coverage API"
        assert "version" in data
        assert data["docs"] == "/docs"

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_nearby_endpoint_empty_list(self, client):
        """Test nearby endpoint with empty list."""
        response = client.post("/api/v1/nearby", json=[])
        assert response.status_code == 400
        assert response.json()["detail"] == "Empty address list received"

    def test_nearby_endpoint_invalid_json(self, client):
        """Test nearby endpoint with invalid JSON."""
        response = client.post("/api/v1/nearby", json="invalid json")
        assert response.status_code == 422  # Validation error

    def test_nearby_endpoint_missing_fields(self, client):
        """Test nearby endpoint with missing required fields."""
        invalid_data = [{"id": "addr1"}]  # Missing address field
        response = client.post("/api/v1/nearby", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_nearby_endpoint_valid_request(
        self, client, mock_use_case, sample_response_data
    ):
        """Test nearby endpoint with valid request using mock use case."""
        valid_data = [{"id": "addr1", "address": "Paris, France"}]
        mock_use_case.execute.return_value = sample_response_data

        # Override the dependency
        app.dependency_overrides = {}
        app.dependency_overrides[get_find_nearby_by_address_use_case] = (
            lambda: mock_use_case
        )

        try:
            response = client.post("/api/v1/nearby", json=valid_data)

            assert response.status_code == 200
            assert response.json() == sample_response_data
            mock_use_case.execute.assert_called_once()
        finally:
            app.dependency_overrides = {}
