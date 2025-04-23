from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

class RoomCreate(BaseModel):
    pass  # No input needed, just creator's IP from request

class RoomResponse(BaseModel):
    id: str
    created_at: datetime
    last_activity: datetime
    active_user_count: int

class RoomState(BaseModel):
    users: Dict[str, str]  # user_id -> username
    cursors: Dict[str, dict]  # user_id -> position
    last_action: Optional[dict] = None

class Position(BaseModel):
    x: float
    y: float
    timestamp: datetime

class DrawingAction(BaseModel):
    type: str = "drawing_action"
    action: dict
    timestamp: datetime

class CursorPosition(BaseModel):
    type: str = "cursor_position"
    position: Position
    user_id: str
    timestamp: datetime

class WebSocketMessage(BaseModel):
    type: str  # "cursor_position" or "drawing_action"
    data: dict
    timestamp: datetime = None

class WebSocketResponse(BaseModel):
    users: Dict[str, str]
    cursors: Dict[str, Position]
    last_action: Optional[dict] = None 