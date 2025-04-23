# Shared Whiteboard Backend

A real-time collaborative whiteboard backend built with FastAPI, SQLModel, and Redis.

## Features

- Real-time collaborative drawing
- Room-based collaboration
- Cursor position tracking
- User presence
- Automatic room cleanup
- JWT-based authentication

## Requirements

- Python 3.7+
- Redis server
- SQLite

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory (optional):
```env
SECRET_KEY=your-secret-key
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password  # if required
```

## Running the Application

1. Start Redis server

2. Run the FastAPI application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access:
- Interactive API documentation (Swagger UI): http://localhost:8000/docs
- Alternative API documentation (ReDoc): http://localhost:8000/redoc

## WebSocket Endpoints

Connect to the WebSocket endpoint with:
```
ws://localhost:8000/api/v1/ws/{room_id}?token={your_jwt_token}
```

## License

MIT 