"""
User API Tests
Tests for user CRUD operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User


class TestUserCRUD:
    """User CRUD operation tests"""
    
    def test_list_users(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting list of users"""
        response = client.get(
            "/api/users",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
    
    def test_get_user_by_id(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting single user by ID"""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
    
    def test_get_user_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent user"""
        response = client.get(
            "/api/users/nonexistent-id",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    def test_create_user(self, client: TestClient):
        """Test creating new user"""
        response = client.post(
            "/api/users",
            json={
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "phone_number": "+1111111111",
                "password": "newpassword123",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["id"]
    
    def test_create_user_duplicate_email(self, client: TestClient, test_user: User):
        """Test creating user with duplicate email"""
        response = client.post(
            "/api/users",
            json={
                "email": "test@example.com",
                "first_name": "Another",
                "last_name": "User",
                "password": "password123",
            },
        )
        
        assert response.status_code == 400
    
    def test_update_user(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test updating user"""
        response = client.put(
            f"/api/users/{test_user.id}",
            headers=auth_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    def test_patch_user(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test partial update of user"""
        response = client.patch(
            f"/api/users/{test_user.id}",
            headers=auth_headers,
            json={"phone_number": "+9999999999"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+9999999999"
    
    def test_delete_user(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test deleting user"""
        response = client.delete(
            f"/api/users/{test_user.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify user is deleted
        get_response = client.get(
            f"/api/users/{test_user.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404
    
    def test_get_current_user_profile(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting current user profile"""
        response = client.get(
            "/api/users/me/profile",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"


class TestUserValidation:
    """User input validation tests"""
    
    def test_create_user_invalid_email(self, client: TestClient):
        """Test creating user with invalid email"""
        response = client.post(
            "/api/users",
            json={
                "email": "not-an-email",
                "first_name": "Test",
                "last_name": "User",
                "password": "password123",
            },
        )
        
        assert response.status_code == 422
    
    def test_create_user_short_password(self, client: TestClient):
        """Test creating user with short password"""
        response = client.post(
            "/api/users",
            json={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "short",
            },
        )
        
        assert response.status_code == 422
    
    def test_create_user_missing_fields(self, client: TestClient):
        """Test creating user with missing required fields"""
        response = client.post(
            "/api/users",
            json={
                "email": "test@example.com",
                "first_name": "Test",
            },
        )
        
        assert response.status_code == 422
