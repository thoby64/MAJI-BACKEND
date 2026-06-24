"""
Health Check Tests
Tests for health check and status endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_api_health_check(self, client: TestClient):
        """Test API health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_database_health_check(self, client: TestClient):
        """Test database health check endpoint"""
        response = client.get("/api/health/database")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint"""
        response = client.get("/api/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data


class TestAPIRoot:
    """API root endpoint tests"""
    
    def test_api_root(self, client: TestClient):
        """Test API root endpoint"""
        response = client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test application root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
