"""
Authentication Tests
Tests for login, token refresh, and authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_refresh_token(self, client: TestClient, test_user: User):
        """Test token refresh"""
        # First login to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
    
    def test_verify_token_valid(self, client: TestClient, auth_headers: dict):
        """Test token verification with valid token"""
        # Extract token from headers
        token = auth_headers["Authorization"].split(" ")[1]
        
        response = client.post(
            "/api/auth/verify",
            json={"token": token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"]
        assert data["email"]
    
    def test_verify_token_invalid(self, client: TestClient):
        """Test token verification with invalid token"""
        response = client.post(
            "/api/auth/verify",
            json={"token": "invalid.token.here"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test logout endpoint"""
        response = client.post(
            "/api/auth/logout",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestTokenManagement:
    """Token management and expiration tests"""
    
    def test_invalid_refresh_token(self, client: TestClient):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"},
        )
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields"""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com"},
        )
        
        assert response.status_code == 422  # Validation error
