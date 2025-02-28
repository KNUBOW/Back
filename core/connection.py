#MySQL 데이터베이스와 연결 설정, 세션 관리

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import Settings
import redis

DATABASE_URL = Settings.DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
redis_client = redis.Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, decode_responses=True)


def get_db():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
