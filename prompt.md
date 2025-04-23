# Shared Whiteboard App Backend Specifications

## Technology Stack
- FastAPI for REST API and WebSocket handling
- SQLModel for ORM with SQLite database
- Async Redis for real-time state management
- Built-in FastAPI WebSocket support
- JWT for authentication

## Core Features

### Authentication & Users
- Simple JWT-based authentication
- Users only need to enter a name to join/create rooms
- No permanent user accounts required

### Room Management
- Rooms identified by UUIDs
- Access only via invite links
- No listing of active rooms
- Auto-cleanup of empty rooms after 5 minutes
- Limit of 10 rooms per IP address
- No user limit per room
- No moderation features
- No private rooms

### Drawing Features
- Vector-based drawing paths
  - Support for different stroke widths and colors
  - No additional metadata stored with paths
- Real-time synchronization
- Batched drawing actions (100ms intervals, no max batch size)
- No chat functionality
- Real-time cursor positions and user presence

### Data Storage & Persistence
- SQLite (via SQLModel) for persistent storage
  - Room data
  - Drawing data (vector paths)
  - User session data
- Redis for real-time state
  - Active cursors
  - User presence
  - Current room state
  - Temporary drawing data

### Backup & Data Management
- Automatic backups every minute
- Import/Export functionality
  - SVG format for drawing data
  - Import only available during room creation
  - Export available anytime
- Indefinite whiteboard preservation
- No rate limiting on drawing actions

## Technical Specifications

### Real-time Communication
- WebSocket-based real-time updates
- Presence tracking for active users
- Cursor position broadcasting
- Batched drawing action updates (100ms intervals)
- Full state sync on reconnection
- Last-Write-Wins (LWW) conflict resolution

### Data Models
1. Room
   - UUID identifier
   - Creation timestamp
   - Last activity timestamp
   - Creator IP
   - Active user count

2. Drawing Data
   - Vector paths with:
     - Stroke width
     - Color
   - Associated room ID
   - Timestamp for LWW conflict resolution

3. User Session
   - JWT token
   - Username
   - Associated room
   - Last active timestamp

### Redis Schema
1. Real-time Room State
   - Active users
   - Cursor positions
   - Recent drawing actions
   - Room metadata

2. Rate Limiting
   - IP-based room creation tracking

### Cleanup & Maintenance
- Automatic room cleanup after 5 minutes of inactivity
- Regular data backups (1-minute intervals)
- IP-based room limit enforcement

### Security
- JWT-based authentication
- No explicit rate limiting on drawing actions
- Room access controlled via invite links only

## Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── websockets/
│   │   └── dependencies/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── events.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
├── alembic/
└── docker/
``` 