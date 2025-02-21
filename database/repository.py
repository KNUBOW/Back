# SQLAlchemy ORM을 사용하여 cookai와 User 데이터를 데이터베이스에서 조회, 저장, 수정, 삭제 하는 기능을 제공하는 Repository 패턴
from sqlite3 import IntegrityError

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.orm import User
from core.connection import get_db



class UserRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_user_by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User).where(User.email == email)
        )

    def save_user(self, user: User) -> User:
        existing_user_email = self.session.query(User).filter(User.email == user.email).first()
        existing_user_nickname = self.session.query(User).filter(User.nickname == user.nickname).first()
        if existing_user_email:
            raise HTTPException(status_code=400, detail="이메일 중복 발생")
        if existing_user_nickname:
            raise HTTPException(status_code=400, detail="닉네임 중복 발생")

        try:
            self.session.add(instance=user)
            self.session.commit()
            self.session.refresh(instance=user)
            return user
        except IntegrityError:
            self.session.rollback()
            raise HTTPException(status_code=400, detail="데이터베이스 제약 조건 위반")