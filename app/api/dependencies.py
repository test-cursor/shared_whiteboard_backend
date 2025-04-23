from fastapi import Depends
from app.services.redis_service import RedisServiceInterface, redis_service

async def get_redis_service() -> RedisServiceInterface:
    return redis_service 