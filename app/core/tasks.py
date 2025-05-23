from datetime import datetime, timedelta, UTC
import asyncio
import logging
from sqlmodel import Session, select
from app.models.models import Room
from app.services.redis_service import redis_service
from app.db.database import engine
from app.core.config import settings

logger = logging.getLogger(__name__)

async def cleanup_inactive_rooms(session: Session = None):
    """Clean up rooms that have been inactive for more than 5 minutes"""
    try:
        # Use provided session or create a new one
        if session is None:
            with Session(engine) as session:
                await _cleanup_rooms(session)
        else:
            await _cleanup_rooms(session)
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_rooms: {str(e)}")
        # Re-raise the exception to ensure the test fails if cleanup fails
        raise

async def _cleanup_rooms(session: Session):
    """Internal function to perform the actual cleanup"""
    cutoff_time = datetime.now(UTC) - timedelta(minutes=settings.ROOM_CLEANUP_MINUTES)
    
    # Find inactive rooms
    inactive_rooms = session.exec(
        select(Room).where(
            (Room.last_activity < cutoff_time) & 
            (Room.active_user_count == 0)
        )
    ).all()
    
    # Clean up each inactive room
    for room in inactive_rooms:
        # Clean up Redis data
        await redis_service.delete_room_data(room.id)
        
        # Delete room from database
        session.delete(room)
        logger.info(f"Cleaned up inactive room: {room.id}")
    
    session.commit()

async def periodic_cleanup():
    """Run cleanup every minute"""
    while True:
        await cleanup_inactive_rooms()
        await asyncio.sleep(60)  # Wait for 1 minute

# Keep track of the background task
cleanup_task: asyncio.Task = None

async def start_cleanup_task():
    """Start the periodic cleanup task"""
    global cleanup_task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Started room cleanup background task")

async def stop_cleanup_task():
    """Stop the periodic cleanup task"""
    global cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped room cleanup background task") 