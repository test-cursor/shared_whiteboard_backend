from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
from datetime import datetime, UTC
from app.core.security import verify_token
from app.db.database import get_session
from app.models.models import Room, UserSession
from app.services.redis_service import RedisServiceInterface
from app.api.dependencies import get_redis_service
from app.schemas.room import RoomCreate, RoomResponse, RoomState, WebSocketMessage, WebSocketResponse, Position
from app.core.utils import DateTimeEncoder
from pydantic import ValidationError
import json

router = APIRouter()

@router.post("/rooms", response_model=RoomResponse)
async def create_room(request: Request, session: Session = Depends(get_session)):
    # Check IP-based room limit
    creator_ip = request.client.host
    room_count = session.exec(
        select(Room).where(Room.creator_ip == creator_ip)
    ).all()
    
    if len(room_count) >= 10:
        raise HTTPException(status_code=400, detail="Room limit reached for this IP")
    
    # Create new room
    room = Room(creator_ip=creator_ip)
    session.add(room)
    session.commit()
    session.refresh(room)
    
    return room

@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, session: Session = Depends(get_session)):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str,
    session: Session = Depends(get_session),
    redis_service: RedisServiceInterface = Depends(get_redis_service)
):
    await websocket.accept()
    
    # Verify token and get user
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008)  # Policy violation
        return
    
    username = payload["sub"]
    
    try:
        # Update user session
        user_session = session.exec(
            select(UserSession).where(UserSession.token == token)
        ).first()
        
        if not user_session:
            await websocket.close(code=1008)
            return
        
        user_session.room_id = room_id
        user_session.last_active = datetime.now(UTC)
        session.add(user_session)
        session.commit()
        
        # Add user to Redis room
        await redis_service.add_user_to_room(room_id, token, username)
        
        # Send connection established message
        await websocket.send_json({"type": "connection_established"})
        
        try:
            while True:
                data = await websocket.receive_json()
                try:
                    message = WebSocketMessage(**data)
                except ValidationError as e:
                    error_response = {
                        "type": "error",
                        "data": {
                            "message": "Invalid message format",
                            "details": str(e)
                        }
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue
                
                try:
                    if message.type == "cursor_position":
                        # Extract x and y from the data
                        x = float(message.data["x"])
                        y = float(message.data["y"])
                        await redis_service.update_cursor_position(
                            room_id, token, x, y
                        )
                        
                    elif message.type == "drawing_action":
                        await redis_service.add_drawing_action(
                            room_id, message.data
                        )
                    else:
                        error_response = {
                            "type": "error",
                            "data": {
                                "message": "Invalid message type",
                                "details": f"Unsupported message type: {message.type}"
                            }
                        }
                        await websocket.send_text(json.dumps(error_response))
                        continue
                    
                    # Broadcast to all clients in the room
                    room_users = await redis_service.get_room_users(room_id)
                    cursor_positions = await redis_service.get_cursor_positions(room_id)
                    
                    # Convert cursor positions to Position objects
                    cursors = {
                        user_id: {
                            "x": pos["x"],
                            "y": pos["y"],
                            "timestamp": pos["timestamp"]
                        }
                        for user_id, pos in cursor_positions.items()
                    }
                    
                    response = WebSocketResponse(
                        users=room_users,
                        cursors=cursors,
                        last_action=message.data if message.type == "drawing_action" else None
                    )
                    
                    # Serialize response with datetime handling
                    json_response = json.dumps(response.dict(), cls=DateTimeEncoder)
                    await websocket.send_text(json_response)
                    
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "data": {
                            "message": "Error processing message",
                            "details": str(e)
                        }
                    }
                    await websocket.send_text(json.dumps(error_response))
                    continue
                
        except WebSocketDisconnect:
            # Clean up when user disconnects
            await redis_service.remove_user_from_room(room_id, token)
            
            # Update room activity
            room = session.get(Room, room_id)
            if room:
                room.active_user_count = max(0, room.active_user_count - 1)
                room.last_activity = datetime.now(UTC)
                session.add(room)
                session.commit()
    
    except Exception as e:
        await websocket.close(code=1011)  # Internal error
        raise e 