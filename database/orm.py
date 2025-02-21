#ORM은 객체(Object)와 데이터베이스(Table)을 연결(Mapping)하는 기술
#SQL을 직접 쓰지 않고 파이썬 언어로 데이터베이스 조작하게 하는 도구
#ORM create table 하는 코드로 추정됨.

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, func, Date, Enum, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, relationship
import pytz
from datetime import datetime


Base = declarative_base()

def get_kst_now():
    kst = pytz.timezone("Asia/Seoul")
    return datetime.now(kst)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    name = Column(String(20), nullable=False)
    nickname = Column(String(20), nullable=False, unique=True)
    birth = Column(Date, nullable=False)
    gender = Column(Enum("M", "F", name="gender_enum"), nullable=False)
    created_at = Column(TIMESTAMP, default=get_kst_now, nullable=False)

    @classmethod
    def create(cls, email: str, hashed_password: str, name: str, nickname: str, birth: Date, gender: str) -> "User":
        return cls(
            email=email,
            password=hashed_password,
            name=name,
            nickname=nickname,
            birth=birth,
            gender=gender
        )

