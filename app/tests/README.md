# Test Suite for FastAPI WebSocket Whiteboard

This directory contains the test suite for the FastAPI WebSocket Whiteboard application. The tests cover authentication, room management, and real-time WebSocket communication.

## Test Structure

- `conftest.py`: Common test fixtures and configurations
- `test_auth.py`: Authentication and token management tests
- `test_rooms.py`: Room creation, retrieval, and cleanup tests
- `test_websocket.py`: WebSocket connection and real-time communication tests

## Running Tests

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Run all tests:
```bash
pytest
```

3. Run tests with coverage:
```bash
pytest --cov=app
```

4. Run specific test file:
```bash
pytest test_auth.py
pytest test_rooms.py
pytest test_websocket.py
```

5. Run tests with detailed output:
```bash
pytest -v
```

## Test Environment

The test suite uses:
- In-memory SQLite database for testing
- Mocked Redis service
- FastAPI TestClient for HTTP endpoints
- WebSocket test client for real-time communication

## Adding New Tests

When adding new tests:
1. Use appropriate fixtures from `conftest.py`
2. Follow the existing test structure and naming conventions
3. Include both success and error cases
4. Add docstrings explaining test purpose
5. Mock external services when appropriate

## Coverage

The test suite aims to cover:
- All HTTP endpoints
- WebSocket communication
- Authentication flows
- Database operations
- Redis operations
- Error handling
- Edge cases 