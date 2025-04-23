# Failing Tests Analysis

## 1. test_multiple_logins_same_user (test_auth.py)

**Purpose**: Tests the behavior when the same user attempts to log in multiple times.

**Error**: 
```
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: usersession.token
```

**Analysis**: 
- The test is failing because the token generation is deterministic based on username
- Each login attempt for the same user generates an identical token due to the same token data being used
- The current implementation doesn't include a unique identifier in the token data

**Solution**:
1. Modify token generation in `auth.py` to include both username and UUID in token data:
```python
token_data = {
    "sub": user.username,
    "uuid": str(uuid.uuid4())  # Add unique identifier
}
```
2. This ensures each login attempt generates a unique token while maintaining user identification

## 2. test_room_cleanup (test_rooms.py)

**Purpose**: Tests the cleanup of inactive rooms.

**Error**:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: room
```

**Analysis**:
- The test is failing because we're not properly initializing the test database
- The in-memory SQLite database is not being set up correctly for testing
- We need proper database fixtures for test isolation

**Solution**:
1. Create a database fixture in conftest.py:
```python
@pytest.fixture
def test_db():
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
```
2. Ensure each test uses the test database fixture
3. Add cleanup after each test to maintain test isolation

## 3. WebSocket Tests (test_websocket.py)

All WebSocket tests are failing with the same error:
```
redis.exceptions.ConnectionError: Error Multiple exceptions: [Errno 111] Connect call failed
```

**Affected Tests**:
- test_websocket_connection_success
- test_websocket_cursor_position
- test_websocket_drawing_action
- test_websocket_disconnect_cleanup
- test_websocket_invalid_message_format

**Analysis**:
- The tests are failing because we're directly using `redis_service` in room.py
- We need proper dependency injection and mocking for both Redis and database operations
- Tests should not affect actual application data

**Solution**:
1. Create a Redis service interface/abstract class:
```python
class RedisServiceInterface:
    async def add_user_to_room(self, room_id: str, token: str, username: str):
        raise NotImplementedError
    # ... other methods
```

2. Modify room.py to use dependency injection:
```python
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    session: Session = Depends(get_session),
    redis_service: RedisServiceInterface = Depends(get_redis_service)
):
    # ... implementation
```

3. Create test fixtures for both Redis and database:
```python
@pytest.fixture
def mock_redis_service():
    class MockRedisService(RedisServiceInterface):
        # Implement mock methods
        pass
    return MockRedisService()

@pytest.fixture
def test_db():
    # Create in-memory test database
    pass
```

4. Ensure proper cleanup between tests:
```python
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Clean up test data
```

## Implementation Steps

1. **Auth Token Fix**:
   - Add UUID to token generation
   - Update token verification to handle new format
   - Update tests to verify token uniqueness

2. **Database Testing**:
   - Create proper database fixtures
   - Implement test database initialization
   - Add cleanup procedures
   - Update tests to use fixtures

3. **WebSocket Testing**:
   - Create Redis service interface
   - Implement dependency injection
   - Create mock implementations
   - Update tests to use mocks
   - Ensure test isolation

## Additional Warnings

There are several deprecation warnings that should be addressed:

1. `datetime.utcnow()` is deprecated - should be replaced with `datetime.now(datetime.UTC)`
2. `session.query()` is deprecated - should use `session.exec()` instead
3. Event loop fixture warnings in pytest-asyncio
4. Multipart import warning in Starlette

These warnings don't cause test failures but should be addressed for future compatibility.