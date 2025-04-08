#ORM은 객체(Object)와 데이터베이스(Table)을 연결(Mapping)하는 기술
#SQL을 직접 쓰지 않고 파이썬 언어로 데이터베이스 조작하게 하는 도구
from typing import Optional
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, ForeignKey, Date, Enum, TIMESTAMP, text, Integer
from sqlalchemy.orm import declarative_base, relationship

from schema.request import IngredientRequest, IngredientCategoriesRequest

Base = declarative_base()

class User(Base):   #유저 관련 테이블 생성
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    name = Column(String(20), nullable=False)
    nickname = Column(String(70), nullable=False, unique=True)
    birth = Column(Date, nullable=False)
    gender = Column(Enum("M", "F", name="gender_enum"), nullable=False)
    social_auth = Column(Enum("G", "N", "K", name="social_auth_enum"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

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
    #릴레이션 정의 cascade설정, 계정 삭제 시 관련 데이터 삭제
    ingredients = relationship("Ingredient", back_populates="user", cascade="all, delete-orphan")
    manual_expiration_logs = relationship("ManualExpirationLog", back_populates="user", cascade="all, delete-orphan")
    unrecognized_ingredient_logs = relationship("UnrecognizedIngredientLog", back_populates="user", cascade="all, delete-orphan")

class Ingredient(Base): #식재료 관련 테이블 생성
    __tablename__ = "ingredients"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)   #외래키 참조
    name = Column(String(40), nullable=False)
    expiration_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    @classmethod
    def create(cls, request: IngredientRequest, user_id: int, expiration_date: Optional[datetime] = None):
        expiration_date = expiration_date or request.expiration_date  # 자동 기입 또는 수동 기입 이기에

        return cls(
            user_id=user_id,
            name=request.name,
            expiration_date=expiration_date
        )

    #릴레이션 정의
    user = relationship("User", back_populates="ingredients")

class IngredientCategories(Base): #식재료 관련 테이블 생성
    __tablename__ = "ingredient_categories"

    id = Column(BigInteger, primary_key=True, index=True)
    ingredient_name = Column(String(40), nullable=False, unique=True)
    parent_category = Column(String(20))
    child_category = Column(String(20))
    default_expiration_days = Column(Integer, nullable=False)

    @classmethod
    def create(cls, request: IngredientCategoriesRequest) -> "IngredientCategories":
        return cls(
            name=request.name,
            parent_category=request.parent_category,
            child_category=request.child_category,
            default_expiration_days=request.default_expiration_days
        )

class ManualExpirationLog(Base):    # 유저들이 직접 유통기한을 넣은 기록
    __tablename__ = "manual_expiration_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(40), nullable=False)
    expiration_date = Column(Integer, nullable=False)  # 유통기한 INT로 저장
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="manual_expiration_logs")

class UnrecognizedIngredientLog(Base):  # 유저들이 유통기한을 직접 기입하지 않았으나, DB에 해당 식재료가 없어서 자동으로 기입 못해준 로그
    __tablename__ = "unrecognized_ingredient_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user = relationship("User", back_populates="unrecognized_ingredient_logs")
