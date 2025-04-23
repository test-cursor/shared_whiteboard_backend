import pytest
import asyncio
import nest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.db.database import get_session
from app.services.redis_service import redis_service, RedisServiceInterface
from app.api.dependencies import get_redis_service
from app.core.config import settings
from app.models.models import Room, DrawingData, UserSession  # Import all models
from datetime import datetime, UTC

# Create in-memory SQLite database for testing
@pytest.fixture(name="engine")
def engine_fixture():
    # Import models to ensure they are registered with SQLModel
    from app.models import models
    
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

# Mock Redis Service
@pytest.fixture(name="mock_redis_service")
def mock_redis_service_fixture():
    # Create a mock Redis service
    mock_service = AsyncMock(spec=RedisServiceInterface)
    
    # Create an in-memory state to simulate Redis storage
    state = {
        'rooms': {},  # Store room data
        'cursors': {},  # Store cursor positions
        'drawings': {},  # Store drawing actions
        'users': {},  # Store user sessions
    }
    
    # Create a mock Redis instance with state management
    mock_redis = AsyncMock()
    
    async def mock_keys(pattern):
        if pattern == "room:*":
            return [f"room:{room_id}" for room_id in state['rooms'].keys()]
        return []
    
    async def mock_delete(*keys):
        for key in keys:
            if key.startswith("room:"):
                room_id = key.split(":")[1]
                state['rooms'].pop(room_id, None)
                state['cursors'].pop(room_id, None)
                state['drawings'].pop(room_id, None)
                state['users'].pop(room_id, None)
    
    async def mock_hgetall(key):
        if key.startswith("room:"):
            room_id = key.split(":")[1]
            return state['rooms'].get(room_id, {})
        return {}
    
    async def mock_hset(key, mapping):
        if key.startswith("room:"):
            room_id = key.split(":")[1]
            if room_id not in state['rooms']:
                state['rooms'][room_id] = {}
            state['rooms'][room_id].update(mapping)
    
    async def mock_rpush(key, *values):
        if key.startswith("drawings:"):
            room_id = key.split(":")[1]
            if room_id not in state['drawings']:
                state['drawings'][room_id] = []
            state['drawings'][room_id].extend(values)
    
    async def mock_lrange(key, start, end):
        if key.startswith("drawings:"):
            room_id = key.split(":")[1]
            actions = state['drawings'].get(room_id, [])
            return actions[start:end if end != -1 else None]
        return []
    
    # Configure mock methods
    mock_redis.keys = AsyncMock(side_effect=mock_keys)
    mock_redis.delete = AsyncMock(side_effect=mock_delete)
    mock_redis.hgetall = AsyncMock(side_effect=mock_hgetall)
    mock_redis.hset = AsyncMock(side_effect=mock_hset)
    mock_redis.rpush = AsyncMock(side_effect=mock_rpush)
    mock_redis.lrange = AsyncMock(side_effect=mock_lrange)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    
    # Set the mock Redis instance
    mock_service.redis = mock_redis
    
    # Mock service methods with state management
    async def mock_add_user_to_room(room_id: str, user_id: str, username: str):
        if room_id not in state['users']:
            state['users'][room_id] = {}
        state['users'][room_id][user_id] = username  # Store just the username string
    
    async def mock_remove_user_from_room(room_id: str, user_id: str):
        if room_id in state['users']:
            state['users'][room_id].pop(user_id, None)
    
    async def mock_get_room_users(room_id: str):
        return state['users'].get(room_id, {})  # Returns Dict[str, str]
    
    async def mock_update_cursor_position(room_id: str, user_id: str, x: float, y: float):
        if room_id not in state['cursors']:
            state['cursors'][room_id] = {}
        state['cursors'][room_id][user_id] = {
            "x": x,
            "y": y,
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    async def mock_get_cursor_positions(room_id: str):
        return state['cursors'].get(room_id, {})  # Returns Dict[str, dict]
    
    async def mock_add_drawing_action(room_id: str, action: dict):
        if room_id not in state['drawings']:
            state['drawings'][room_id] = []
        state['drawings'][room_id].append(action)
    
    async def mock_get_drawing_actions(room_id: str):
        return state['drawings'].get(room_id, [])
    
    # Configure service methods
    mock_service.init = AsyncMock()
    mock_service.close = AsyncMock()
    mock_service.add_user_to_room = AsyncMock(side_effect=mock_add_user_to_room)
    mock_service.remove_user_from_room = AsyncMock(side_effect=mock_remove_user_from_room)
    mock_service.get_room_users = AsyncMock(side_effect=mock_get_room_users)
    mock_service.update_cursor_position = AsyncMock(side_effect=mock_update_cursor_position)
    mock_service.get_cursor_positions = AsyncMock(side_effect=mock_get_cursor_positions)
    mock_service.add_drawing_action = AsyncMock(side_effect=mock_add_drawing_action)
    mock_service.get_drawing_actions = AsyncMock(side_effect=mock_get_drawing_actions)
    mock_service.delete_room_data = AsyncMock(side_effect=lambda room_id: mock_delete(f"room:{room_id}"))
    mock_service.set_room_state = AsyncMock()
    mock_service.get_room_state = AsyncMock(return_value=None)
    
    return mock_service

@pytest.fixture(name="client")
def client_fixture(engine, mock_redis_service):
    def get_session_override():
        with Session(engine) as session:
            yield session

    async def get_redis_service_override():
        return mock_redis_service

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_redis_service] = get_redis_service_override
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()

# WebSocket test client
@pytest.fixture(name="websocket_client")
def websocket_client_fixture(client):
    def _websocket_client(url):
        return client.websocket_connect(url)
    return _websocket_client

# Auth token fixture
@pytest.fixture(name="auth_token")
def auth_token_fixture():
    from app.core.security import create_access_token
    return create_access_token({"sub": "test_user"})

# Test room fixture
@pytest.fixture(name="test_room")
def test_room_fixture(client):
    response = client.post("/api/v1/rooms")
    return response.json()["id"]

# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    nest_asyncio.apply(loop)  # Allow nested event loops
    yield loop
    loop.close() 