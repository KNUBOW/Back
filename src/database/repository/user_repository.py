from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).filter(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar()  # 첫 번째 결과 반환

    async def save_user(self, user: User) -> User:
        # 이메일과 닉네임 중복 체크
        stmt_email = select(User).filter(User.email == user.email)
        stmt_nickname = select(User).filter(User.nickname == user.nickname)

        email_check = await self.session.execute(stmt_email)
        nickname_check = await self.session.execute(stmt_nickname)

        if email_check.scalar():
            raise HTTPException(status_code=400, detail="이메일 중복 발생")
        if nickname_check.scalar():
            raise HTTPException(status_code=400, detail="닉네임 중복 발생")

        try:
            self.session.add(user)
            await self.session.commit()  # 비동기적으로 커밋
            await self.session.refresh(user)  # 비동기적으로 리프레시
            return user
        except IntegrityError:
            await self.session.rollback()  # 롤백 처리
            raise HTTPException(status_code=400, detail="데이터베이스 제약 조건 위반")
