"""
Utilities API Tests
Tests for utility CRUD operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Utility


class TestUtilityCRUD:
    """Utility CRUD operation tests"""
    
    def test_list_utilities(self, client: TestClient, auth_headers: dict):
        """Test getting list of utilities"""
        response = client.get(
            "/api/utilities",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
    
    def test_create_utility(self, client: TestClient, auth_headers: dict):
        """Test creating new utility"""
        response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={
                "name": "Water Company A",
                "description": "Test water utility",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Water Company A"
        assert data["id"]
        self.utility_id = data["id"]
    
    def test_get_utility_by_id(self, client: TestClient, auth_headers: dict):
        """Test getting single utility by ID"""
        # First create a utility
        create_response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={"name": "Test Utility", "description": "Test"},
        )
        utility_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(
            f"/api/utilities/{utility_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Utility"
    
    def test_update_utility(self, client: TestClient, auth_headers: dict):
        """Test updating utility"""
        # Create utility
        create_response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={"name": "Original Name", "description": "Test"},
        )
        utility_id = create_response.json()["id"]
        
        # Update it
        response = client.put(
            f"/api/utilities/{utility_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    def test_delete_utility(self, client: TestClient, auth_headers: dict):
        """Test deleting utility"""
        # Create utility
        create_response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={"name": "To Delete", "description": "Test"},
        )
        utility_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(
            f"/api/utilities/{utility_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(
            f"/api/utilities/{utility_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
    
    def test_get_nonexistent_utility(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent utility"""
        response = client.get(
            "/api/utilities/nonexistent-id",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestUtilityValidation:
    """Utility input validation tests"""
    
    def test_create_utility_missing_name(self, client: TestClient, auth_headers: dict):
        """Test creating utility without name"""
        response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={"description": "No name"},
        )
        
        assert response.status_code == 422
    
    def test_create_utility_empty_name(self, client: TestClient, auth_headers: dict):
        """Test creating utility with empty name"""
        response = client.post(
            "/api/utilities",
            headers=auth_headers,
            json={"name": "", "description": "Empty name"},
        )
        
        assert response.status_code == 422
