from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid

class Room(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    creator_ip: str
    active_user_count: int = Field(default=0)

class DrawingData(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    room_id: str = Field(foreign_key="room.id")
    path_data: str  # JSON string containing vector path data
    stroke_width: float
    color: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserSession(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    username: str = Field(index=True)
    room_id: Optional[str] = Field(default=None, foreign_key="room.id", nullable=True)
    last_active: datetime = Field(default_factory=datetime.utcnow) 