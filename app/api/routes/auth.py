from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.security import create_access_token
from app.db.database import get_session
from app.models.models import UserSession
from app.schemas.auth import UserLogin, Token
import uuid

router = APIRouter()

@router.post("/auth/login", response_model=Token)
async def login(user: UserLogin, session: Session = Depends(get_session)):
    # Create token with both username and unique UUID
    token_data = {
        "sub": user.username,
        "uuid": str(uuid.uuid4())  # Add unique identifier
    }
    
    access_token = create_access_token(token_data)
    
    # Create user session
    user_session = UserSession(
        token=access_token,
        username=user.username,
        room_id=None  # Will be set when user joins a room
    )
    
    session.add(user_session)
    session.commit()
    
    return Token(
        access_token=access_token,
        token_type="bearer"
    ) 