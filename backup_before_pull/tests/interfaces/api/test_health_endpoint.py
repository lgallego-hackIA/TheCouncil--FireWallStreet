"""
Tests for the central health endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the app from the main API file
from src.vercel_api import app

# Create test client for the API
client = TestClient(app)

def test_health_check():
    """Test the central health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Check that all expected fields are present
    health_data = response.json()
    assert "timestamp" in health_data
    assert "version" in health_data
    assert "environment" in health_data
    assert "registered_automations" in health_data
    assert "automations" in health_data
    
    # Verify that automations is a list (could be empty)
    assert isinstance(health_data["automations"], list)
