import pytest

from fastapi.testclient import TestClient

from src.main import app





def test_get_test():
    """Test the GET /test endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/test")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_stock-price():
    """Test the GET /stock-price endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/stock-price")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_brent-price():
    """Test the GET /brent-price endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/brent-price")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_trading-volume():
    """Test the GET /trading-volume endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/trading-volume")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_msrket-cap():
    """Test the GET /msrket-cap endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/msrket-cap")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_all-data():
    """Test the GET /all-data endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/all-data")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_collect():
    """Test the GET /collect endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/collect")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()



def test_get_health():
    """Test the GET /health endpoint"""
    with TestClient(app) as client:
        response = client.get("/financial-data-collector/health")
    assert response.status_code == 200
    # Add more specific assertions here based on expected response
    assert "message" in response.json()
