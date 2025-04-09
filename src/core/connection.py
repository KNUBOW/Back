import aioredis

from sqlalchemy.orm import sessionmaker
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

#연결 설정, 세션 관리

# PostgreSQL 연결 설정 (비동기식)
POSTGRES_DATABASE_URL = settings.POSTGRES_DATABASE_URL
postgres_engine = create_async_engine(POSTGRES_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=postgres_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


# PostgreSQL 비동기식 DB 세션 관리
async def get_postgres_db():
    async with AsyncSessionLocal() as session:
        yield session

# Redis 연결
class RedisClient:
    _redis = None

    @classmethod
    async def get_redis(cls):
        if cls._redis is None:
            cls._redis = await aioredis.from_url(f"redis://{settings.REDIS_HOST}", decode_responses=True)
        return cls._redis

    @classmethod
    async def close_redis(cls):
        if cls._redis:
            await cls._redis.close()
            cls._redis = None
