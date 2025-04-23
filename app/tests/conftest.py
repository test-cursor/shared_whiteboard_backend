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
from app.services.redis_service import redis_service, RedisService
from app.core.config import settings

# Create in-memory SQLite database for testing
@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # Drop all tables first to ensure clean state
    SQLModel.metadata.drop_all(engine)
    # Create all tables
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Mock Redis Service
@pytest.fixture(name="mock_redis_service")
async def mock_redis_service_fixture():
    # Create a mock Redis service
    mock_service = AsyncMock(spec=RedisService)
    mock_service.redis = AsyncMock()  # Add mock redis instance
    
    # Setup default behaviors for commonly used methods
    mock_service.get_room_users.return_value = {}
    mock_service.get_cursor_positions.return_value = {}
    mock_service.get_room_state.return_value = None
    mock_service.add_user_to_room = AsyncMock()
    mock_service.remove_user_from_room = AsyncMock()
    mock_service.update_cursor_position = AsyncMock()
    mock_service.add_drawing_action = AsyncMock()
    mock_service.get_drawing_actions.return_value = []
    mock_service.delete_room_data = AsyncMock()
    
    # Mock Redis instance methods
    mock_service.redis.hset = AsyncMock()
    mock_service.redis.hdel = AsyncMock()
    mock_service.redis.hgetall = AsyncMock(return_value={})
    mock_service.redis.rpush = AsyncMock()
    mock_service.redis.lrange = AsyncMock(return_value=[])
    mock_service.redis.keys = AsyncMock(return_value=[])
    mock_service.redis.delete = AsyncMock()
    
    # Store the original service
    original_service = redis_service
    
    # Replace the global redis_service with our mock
    import app.services.redis_service
    app.services.redis_service.redis_service = mock_service
    
    # Initialize the mock service
    await mock_service.init()
    
    yield mock_service
    
    # Restore the original service after the test
    app.services.redis_service.redis_service = original_service

# WebSocket test client
@pytest.fixture(name="websocket_client")
def websocket_client_fixture(client: TestClient):
    return client.websocket_connect

# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    nest_asyncio.apply(loop)  # Allow nested event loops
    yield loop
    loop.close() 