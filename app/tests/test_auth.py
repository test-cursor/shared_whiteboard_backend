import pytest
from fastapi.testclient import TestClient
from app.core.security import verify_token
from app.models.models import UserSession

def test_login_success(client: TestClient, session):
    """Test successful login with valid username"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
    # Verify token is valid
    token = data["access_token"]
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    
    # Check user session was created
    user_session = session.query(UserSession).filter(UserSession.token == token).first()
    assert user_session is not None
    assert user_session.username == "testuser"

def test_login_empty_username(client: TestClient):
    """Test login with empty username"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": ""}
    )
    assert response.status_code == 422  # Validation error

def test_login_missing_username(client: TestClient):
    """Test login with missing username field"""
    response = client.post(
        "/api/v1/auth/login",
        json={}
    )
    assert response.status_code == 422  # Validation error

def test_multiple_logins_same_user(client: TestClient, session):
    """Test multiple logins from the same username"""
    # First login
    response1 = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser"}
    )
    token1 = response1.json()["access_token"]
    
    # Second login
    response2 = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser"}
    )
    token2 = response2.json()["access_token"]
    
    # Both logins should succeed with different tokens
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert token1 != token2
    
    # Both sessions should exist
    sessions = session.query(UserSession).filter(
        UserSession.username == "testuser"
    ).all()
    assert len(sessions) == 2 