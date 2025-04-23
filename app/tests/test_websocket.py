import pytest
import json
from fastapi.testclient import TestClient
from app.models.models import Room, UserSession
from app.core.security import create_access_token
from fastapi import WebSocketDisconnect

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

def test_websocket_connection_success(
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

def test_websocket_cursor_position(
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
                "x": 100,
                "y": 200,
                "timestamp": "2024-03-14T12:00:00"
            }
        }
        websocket.send_json(cursor_data)
        
        # Verify cursor position was updated
        assert mock_redis_service.update_cursor_position.called

def test_websocket_drawing_action(
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
            }
        }
        websocket.send_json(drawing_data)
        
        # Verify drawing action was added
        assert mock_redis_service.add_drawing_action.called

def test_websocket_disconnect_cleanup(
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
        websocket.send_json({"invalid": "message"})
        
        # Should receive error message
        response = websocket.receive_json()
        assert response["type"] == "error" 