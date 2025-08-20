"""
Integration tests for the FastAPI application.

This module contains integration tests that test the API as a whole,
including error handling, response formats, and real HTTP interactions.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.main import app, number_set


class TestAPIIntegration:
    """Integration tests for the FastAPI application."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        with TestClient(app) as client:
            # Reset the number set before each test
            number_set.reset()
            yield client
    
    def test_api_documentation_endpoints(self, client):
        """Test that API documentation endpoints are accessible."""
        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI JSON schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "Missing Number API"
        assert schema["info"]["version"] == "1.0.0"
    
    def test_sequential_extractions(self, client):
        """Test sequential extraction requests."""
        numbers = [1, 2, 3, 4, 5]
        
        for num in numbers:
            response = client.post(f"/extract/{num}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["extracted_number"] == num
    
    def test_error_response_format(self, client):
        """Test that error responses have consistent format."""
        # Test invalid number extraction
        response = client.post("/extract/150")
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
        
        # Test missing number without extractions
        client.post("/reset")
        response = client.get("/missing")
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)
    
    def test_response_time_performance(self, client):
        """Test that API responses are reasonably fast."""
        import time
        
        # Test extract endpoint performance
        start_time = time.time()
        response = client.post("/extract/50")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete in less than 1 second
        
        # Test missing number calculation performance
        start_time = time.time()
        response = client.get("/missing")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete in less than 1 second
        
        # Verify the execution time is reported in the response
        data = response.json()
        assert "execution_time_ms" in data
        assert isinstance(data["execution_time_ms"], (int, float))
        assert data["execution_time_ms"] >= 0
    
    def test_api_state_persistence(self, client):
        """Test that API state persists across requests."""
        # Extract a number
        response = client.post("/extract/77")
        assert response.status_code == 200
        
        # Check status in separate request
        response = client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["extracted_count"] == 1
        assert 77 in data["extracted_numbers"]
        
        # Get missing number in separate request
        response = client.get("/missing")
        assert response.status_code == 200
        assert response.json()["missing_number"] == 77
        
        # Reset in separate request
        response = client.post("/reset")
        assert response.status_code == 200
        
        # Verify reset persisted
        response = client.get("/status")
        assert response.status_code == 200
        assert response.json()["extracted_count"] == 0