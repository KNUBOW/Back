#MySQL 데이터베이스와 연결 설정, 세션 관리

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import Settings
import redis
from motor.motor_asyncio import AsyncIOMotorClient

# MySQL 연결 설정
DATABASE_URL = Settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis 연결 설정
redis_client = redis.Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, decode_responses=True)

# MongoDB 연결 설정
MONGO_URI = Settings.MONGO_URI  # 예: "mongodb://localhost:27017"
MONGO_DB_NAME = Settings.MONGO_DB_NAME  # 예: "mydatabase"

mongo_client = AsyncIOMotorClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]

def get_db():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
