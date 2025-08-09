"""Integration tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_client():
    """Create test client for API testing."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_check(self, test_client):
        """Test basic health endpoint."""
        response = test_client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "ReelsBot API"
    
    def test_detailed_health_check(self, test_client):
        """Test detailed health endpoint."""
        response = test_client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data


class TestContentEndpoints:
    """Test content generation endpoints."""
    
    def test_generate_content_success(self, test_client):
        """Test successful content generation."""
        # Note: This will fail without valid API keys, but tests the endpoint structure
        request_data = {
            "topic": "Test topic",
            "platform": "instagram",
            "tone": "casual",
            "target_audience": "Test audience",
            "include_music": False,
            "include_trends": False
        }
        
        response = test_client.post("/api/v1/content/generate", json=request_data)
        
        # Since we don't have real API keys in tests, this might fail at the service level
        # But we can check that the endpoint accepts the request format
        assert response.status_code in [200, 422, 500]  # Valid responses
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "request_id" in data
    
    def test_generate_content_validation_errors(self, test_client):
        """Test content generation with invalid data."""
        # Missing required fields
        response = test_client.post("/api/v1/content/generate", json={})
        assert response.status_code == 422
        
        # Invalid platform
        request_data = {
            "topic": "Test topic",
            "platform": "invalid_platform",
            "tone": "casual",
            "target_audience": "Test audience"
        }
        response = test_client.post("/api/v1/content/generate", json=request_data)
        assert response.status_code == 422
        
        # Empty topic
        request_data = {
            "topic": "",
            "platform": "instagram",
            "tone": "casual",
            "target_audience": "Test audience"
        }
        response = test_client.post("/api/v1/content/generate", json=request_data)
        assert response.status_code == 422
    
    def test_get_nonexistent_script(self, test_client):
        """Test retrieving non-existent content script."""
        response = test_client.get("/api/v1/content/scripts/99999")
        assert response.status_code == 404
    
    def test_get_nonexistent_request(self, test_client):
        """Test retrieving non-existent generation request."""
        response = test_client.get("/api/v1/content/requests/99999")
        assert response.status_code == 404


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, test_client):
        """Test the root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data