<!-- Generated by SpecStory -->

# Command to Run All Tests (2025-04-22 21:27:29)

_**User**_

what ocmmand runs all tests?

---

_**Assistant**_

Let me check the test configuration and requirements files to find the correct test command.

---

Read file: /home/db/code/shared_whiteboard_backend/app/tests/README.md

---

Based on the README.md file, there are a few ways to run the tests:

1. Basic test command:
```bash
pytest
```

2. With coverage report:
```bash
pytest --cov=app
```

3. With verbose output:
```bash
pytest -v
```

Before running the tests, make sure you have the test dependencies installed:
```bash
pip install -r requirements-test.txt
```

You can also run specific test files individually if needed:
```bash
pytest test_auth.py
pytest test_rooms.py
pytest test_websocket.py
```

The simplest command to run all tests is just `pytest` in the project directory. The tests will use an in-memory SQLite database and mocked Redis service for testing.

---



---

