#MySQL 데이터베이스와 연결 설정, 세션 관리

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = ""

engine = create_engine(DATABASE_URL)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():   #제너레이터에 대해 알아볼 것
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
