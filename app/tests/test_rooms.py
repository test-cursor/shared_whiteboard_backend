import pytest
from fastapi.testclient import TestClient
from app.models.models import Room
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch

def test_create_room(client: TestClient, session):
    """Test creating a new room"""
    response = client.post("/api/v1/rooms")
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "id" in data
    assert "created_at" in data
    assert "last_activity" in data
    assert "active_user_count" in data
    
    # Verify room was created in database
    room = session.get(Room, data["id"])
    assert room is not None
    assert room.active_user_count == 0

def test_get_room(client: TestClient, session):
    """Test getting an existing room"""
    # Create a room first
    create_response = client.post("/api/v1/rooms")
    room_id = create_response.json()["id"]
    
    # Get the room
    response = client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == room_id

def test_get_nonexistent_room(client: TestClient):
    """Test getting a room that doesn't exist"""
    response = client.get("/api/v1/rooms/nonexistent-id")
    assert response.status_code == 404

def test_room_limit_per_ip(client: TestClient, session):
    """Test the room creation limit per IP"""
    # Create maximum allowed rooms
    for _ in range(10):
        response = client.post("/api/v1/rooms")
        assert response.status_code == 200
    
    # Try to create one more room
    response = client.post("/api/v1/rooms")
    assert response.status_code == 400
    assert "Room limit reached" in response.json()["detail"]

@pytest.mark.asyncio
async def test_room_cleanup(client: TestClient, session):
    """Test room cleanup for inactive rooms"""
    # Create a mock Redis service
    mock_redis = AsyncMock()
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.delete = AsyncMock()
    
    # Create a room
    response = client.post("/api/v1/rooms")
    room_id = response.json()["id"]
    
    # Get the room and modify its last_activity to be old
    room = session.get(Room, room_id)
    room.last_activity = datetime.now(UTC) - timedelta(minutes=10)
    session.add(room)
    session.commit()
    
    # Import and run cleanup
    from app.core.tasks import cleanup_inactive_rooms
    from app.services.redis_service import redis_service
    
    # Mock the Redis instance
    redis_service.redis = mock_redis
    
    await cleanup_inactive_rooms(session=session)
    
    # Verify room was deleted
    room = session.get(Room, room_id)
    assert room is None
    
    # Verify Redis cleanup was called
    mock_redis.keys.assert_called_once_with(f"room:{room_id}:*") 