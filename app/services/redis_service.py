import json
from typing import Optional, Dict, List
from redis.asyncio import Redis
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.redis: Optional[Redis] = None

    async def init(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def close(self):
        if self.redis:
            await self.redis.close()

    # Room management
    async def set_room_state(self, room_id: str, state: dict):
        await self.redis.set(f"room:{room_id}:state", json.dumps(state))

    async def get_room_state(self, room_id: str) -> Optional[dict]:
        state = await self.redis.get(f"room:{room_id}:state")
        return json.loads(state) if state else None

    # User presence
    async def add_user_to_room(self, room_id: str, user_id: str, username: str):
        await self.redis.hset(f"room:{room_id}:users", user_id, username)

    async def remove_user_from_room(self, room_id: str, user_id: str):
        await self.redis.hdel(f"room:{room_id}:users", user_id)

    async def get_room_users(self, room_id: str) -> Dict[str, str]:
        return await self.redis.hgetall(f"room:{room_id}:users")

    # Cursor positions
    async def update_cursor_position(self, room_id: str, user_id: str, position: dict):
        await self.redis.hset(
            f"room:{room_id}:cursors",
            user_id,
            json.dumps(position)
        )

    async def get_cursor_positions(self, room_id: str) -> Dict[str, dict]:
        cursors = await self.redis.hgetall(f"room:{room_id}:cursors")
        return {k: json.loads(v) for k, v in cursors.items()}

    # Drawing actions
    async def add_drawing_action(self, room_id: str, action: dict):
        await self.redis.rpush(
            f"room:{room_id}:drawing_actions",
            json.dumps(action)
        )

    async def get_drawing_actions(self, room_id: str) -> List[dict]:
        actions = await self.redis.lrange(f"room:{room_id}:drawing_actions", 0, -1)
        return [json.loads(action) for action in actions]

    # Room cleanup
    async def delete_room_data(self, room_id: str):
        keys = await self.redis.keys(f"room:{room_id}:*")
        if keys:
            await self.redis.delete(*keys)

# Create a global Redis service instance
redis_service = RedisService() 