"""
Unit tests for FastAPI endpoints.

This module contains comprehensive tests for all API endpoints including
success cases, error handling, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.main import app, number_set


class TestFastAPIEndpoints:
    """Test class for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture(autouse=True)
    def reset_number_set(self):
        """Reset the number set before each test."""
        number_set.reset()
        yield
        number_set.reset()
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Missing Number API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "extract" in data["endpoints"]
        assert "missing" in data["endpoints"]
        assert "reset" in data["endpoints"]
    
    def test_health_check_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Missing Number API"
    
    def test_status_endpoint_initial_state(self, client):
        """Test the status endpoint returns correct initial state."""
        response = client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_numbers"] == 100
        assert data["remaining_count"] == 100
        assert data["extracted_count"] == 0
        assert data["extracted_numbers"] == []
        assert data["is_complete"] is True
    
    def test_extract_valid_number(self, client):
        """Test extracting a valid number."""
        response = client.post("/extract/42")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["extracted_number"] == 42
        assert data["remaining_count"] == 99
        assert "Successfully extracted number 42" in data["message"]
    
    def test_extract_number_at_boundaries(self, client):
        """Test extracting numbers at valid boundaries."""
        # Test minimum boundary
        response = client.post("/extract/1")
        assert response.status_code == 200
        assert response.json()["extracted_number"] == 1
        
        # Reset and test maximum boundary
        client.post("/reset")
        response = client.post("/extract/100")
        assert response.status_code == 200
        assert response.json()["extracted_number"] == 100
    
    def test_extract_invalid_number_below_range(self, client):
        """Test extracting a number below valid range."""
        response = client.post("/extract/0")
        assert response.status_code == 400
        
        data = response.json()
        assert "Number must be between 1 and 100" in data["detail"]
    
    def test_extract_invalid_number_above_range(self, client):
        """Test extracting a number above valid range."""
        response = client.post("/extract/101")
        assert response.status_code == 400
        
        data = response.json()
        assert "Number must be between 1 and 100" in data["detail"]
    
    def test_extract_already_extracted_number(self, client):
        """Test extracting a number that has already been extracted."""
        # First extraction should succeed
        response = client.post("/extract/50")
        assert response.status_code == 200
        
        # Second extraction of same number should fail
        response = client.post("/extract/50")
        assert response.status_code == 409
        
        data = response.json()
        assert "already been extracted" in data["detail"]
    
    def test_get_missing_number_success(self, client):
        """Test getting missing number after extraction."""
        # Extract a number first
        client.post("/extract/75")
        
        response = client.get("/missing")
        assert response.status_code == 200
        
        data = response.json()
        assert data["missing_number"] == 75
        assert data["calculation_method"] == "mathematical_sum"
        assert data["execution_time_ms"] >= 0
        assert data["extracted_numbers"] == [75]
    
    def test_get_missing_number_no_extractions(self, client):
        """Test getting missing number when no numbers have been extracted."""
        response = client.get("/missing")
        assert response.status_code == 400
        
        data = response.json()
        assert "No numbers have been extracted yet" in data["detail"]
    
    def test_get_missing_number_multiple_extractions(self, client):
        """Test getting missing number when multiple numbers are extracted."""
        # Extract multiple numbers
        client.post("/extract/10")
        client.post("/extract/20")
        
        response = client.get("/missing")
        assert response.status_code == 400
        
        data = response.json()
        assert "multiple numbers are extracted" in data["detail"]
    
    def test_reset_endpoint(self, client):
        """Test the reset endpoint."""
        # Extract some numbers first
        client.post("/extract/25")
        client.post("/extract/50")
        
        # Verify numbers were extracted
        status_response = client.get("/status")
        assert status_response.json()["extracted_count"] == 2
        
        # Reset the set
        response = client.post("/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["total_numbers"] == 100
        assert "reset to contain all numbers" in data["message"]
        
        # Verify reset worked
        status_response = client.get("/status")
        status_data = status_response.json()
        assert status_data["extracted_count"] == 0
        assert status_data["remaining_count"] == 100
        assert status_data["is_complete"] is True
    
    def test_complete_workflow(self, client):
        """Test a complete workflow: extract, get missing, reset."""
        # Initial status check
        response = client.get("/status")
        assert response.json()["is_complete"] is True
        
        # Extract a number
        extract_response = client.post("/extract/33")
        assert extract_response.status_code == 200
        assert extract_response.json()["extracted_number"] == 33
        
        # Check status after extraction
        status_response = client.get("/status")
        status_data = status_response.json()
        assert status_data["extracted_count"] == 1
        assert status_data["remaining_count"] == 99
        assert 33 in status_data["extracted_numbers"]
        
        # Get missing number
        missing_response = client.get("/missing")
        assert missing_response.status_code == 200
        assert missing_response.json()["missing_number"] == 33
        
        # Reset
        reset_response = client.post("/reset")
        assert reset_response.status_code == 200
        
        # Verify reset
        final_status = client.get("/status")
        assert final_status.json()["is_complete"] is True
        assert final_status.json()["extracted_count"] == 0
    
    def test_status_endpoint_after_extractions(self, client):
        """Test status endpoint after multiple extractions."""
        # Extract multiple numbers
        numbers_to_extract = [15, 30, 45, 60]
        for num in numbers_to_extract:
            response = client.post(f"/extract/{num}")
            assert response.status_code == 200
        
        # Check status
        response = client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_numbers"] == 100
        assert data["remaining_count"] == 96  # 100 - 4
        assert data["extracted_count"] == 4
        assert data["extracted_numbers"] == sorted(numbers_to_extract)
        assert data["is_complete"] is False