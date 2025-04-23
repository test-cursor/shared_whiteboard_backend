import pytest
import json
from fastapi.testclient import TestClient
from app.models.models import Room, UserSession
from app.core.security import create_access_token
from fastapi import WebSocketDisconnect
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC
from app.services.redis_service import RedisServiceInterface

@pytest.fixture
def auth_token(session):
    """Create a test user and return their auth token"""
    token_data = {"sub": "testuser"}
    token = create_access_token(token_data)
    
    # Create user session
    user_session = UserSession(
        token=token,
        username="testuser",
        room_id=None
    )
    session.add(user_session)
    session.commit()
    
    return token

@pytest.fixture
def test_room(client: TestClient, session):
    """Create a test room and return its ID"""
    response = client.post("/api/v1/rooms")
    return response.json()["id"]

@pytest.mark.asyncio
async def test_websocket_connection_success(
    client: TestClient,
    websocket_client,
    auth_token,
    test_room,
    mock_redis_service
):
    """Test successful WebSocket connection"""
    with websocket_client(
        f"/api/v1/ws/{test_room}?token={auth_token}"
    ) as websocket:
        # Verify connection is established
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

def test_websocket_invalid_token(
    client: TestClient,
    websocket_client,
    test_room
):
    """Test WebSocket connection with invalid token"""
    with pytest.raises(WebSocketDisconnect):
        with websocket_client(
            f"/api/v1/ws/{test_room}?token=invalid_token"
        ) as websocket:
            websocket.receive_json()

@pytest.mark.asyncio
async def test_websocket_cursor_position(
    client: TestClient,
    websocket_client,
    auth_token,
    test_room,
    mock_redis_service
):
    """Test sending and receiving cursor position updates"""
    with websocket_client(
        f"/api/v1/ws/{test_room}?token={auth_token}"
    ) as websocket:
        # Wait for connection message
        websocket.receive_json()
        
        # Send cursor position
        cursor_data = {
            "type": "cursor_position",
            "data": {
                "x": 100.0,
                "y": 200.0
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        websocket.send_json(cursor_data)
        
        # Wait for response
        response = websocket.receive_json()
        
        # Verify cursor position was updated
        assert mock_redis_service.update_cursor_position.called
        assert mock_redis_service.update_cursor_position.call_args[0] == (test_room, auth_token, 100.0, 200.0)

@pytest.mark.asyncio
async def test_websocket_drawing_action(
    client: TestClient,
    websocket_client,
    auth_token,
    test_room,
    mock_redis_service
):
    """Test sending and receiving drawing actions"""
    with websocket_client(
        f"/api/v1/ws/{test_room}?token={auth_token}"
    ) as websocket:
        # Wait for connection message
        websocket.receive_json()
        
        # Send drawing action
        drawing_data = {
            "type": "drawing_action",
            "data": {
                "action": "draw",
                "points": [[100, 100], [200, 200]]
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        websocket.send_json(drawing_data)
        
        # Wait for response
        response = websocket.receive_json()
        
        # Verify drawing action was added
        assert mock_redis_service.add_drawing_action.called
        assert mock_redis_service.add_drawing_action.call_args[0] == (test_room, drawing_data["data"])

@pytest.mark.asyncio
async def test_websocket_disconnect_cleanup(
    client: TestClient,
    websocket_client,
    auth_token,
    test_room,
    session,
    mock_redis_service
):
    """Test cleanup after WebSocket disconnection"""
    with websocket_client(
        f"/api/v1/ws/{test_room}?token={auth_token}"
    ) as websocket:
        # Wait for connection message
        websocket.receive_json()
    
    # After disconnection, verify cleanup
    assert mock_redis_service.remove_user_from_room.called

def test_websocket_invalid_message_format(
    client: TestClient,
    websocket_client,
    auth_token,
    test_room
):
    """Test sending invalid message format"""
    with websocket_client(
        f"/api/v1/ws/{test_room}?token={auth_token}"
    ) as websocket:
        # Wait for connection message
        websocket.receive_json()
        
        # Send invalid message
        websocket.send_json({
            "type": "invalid_type",
            "data": {},
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Should receive error message
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "message" in response["data"]
        assert "details" in response["data"] 