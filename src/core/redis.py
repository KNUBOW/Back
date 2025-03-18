import aioredis
from core.config import Settings

class RedisClient:
    _redis = None

    @classmethod
    async def get_redis(cls):
        """Redis 싱글톤 인스턴스 생성 및 반환"""
        if cls._redis is None:
            cls._redis = await aioredis.from_url(f"redis://{Settings.REDIS_HOST}", decode_responses=True)
        return cls._redis

    @classmethod
    async def close_redis(cls):
        """애플리케이션 종료 시 Redis 연결 닫기"""
        if cls._redis:
            await cls._redis.close()
            cls._redis = None