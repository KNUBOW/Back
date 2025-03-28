#MySQL 데이터베이스와 연결 설정, 세션 관리
from sqlalchemy.orm import sessionmaker
from core.config import Settings
import redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine



# PostgreSQL 연결 설정 (비동기식)
POSTGRES_DATABASE_URL = Settings.POSTGRES_DATABASE_URL
postgres_engine = create_async_engine(POSTGRES_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=postgres_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Redis 연결 설정
redis_client = redis.Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, decode_responses=True)


# PostgreSQL 비동기식 DB 세션 관리
async def get_postgres_db():
    async with AsyncSessionLocal() as session:
        yield session