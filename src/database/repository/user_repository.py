from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import (
    SQLAlchemyError,
)

from exception.database_exception import (
    DatabaseException,
)

from utils.base_repository import commit_with_error_handling

from exception.external_exception import UnexpectedException
from database.orm import User

# 유저 관련 리프지토리

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            stmt = select(User).where(User.email == email)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(detail=f"DB 조회 오류: {str(e)}")
        except Exception as e:
            raise UnexpectedException(detail=f"예기치 못한 에러: {str(e)}")

    async def get_user_by_nickname(self, nickname: str) -> Optional[User]:
        try:
            stmt = select(User).where(User.nickname == nickname)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(detail=f"DB 조회 오류: {str(e)}")
        except Exception as e:
            raise UnexpectedException(detail=f"예기치 못한 에러: {str(e)}")

    async def save_user(self, user: User) -> User:
        self.session.add(user)
        await commit_with_error_handling(self.session, context="유저 저장")
        await self.session.refresh(user)
        return user

    async def update_password(self, user: User, hashed_password: str) -> None:
        user.password = hashed_password
        self.session.add(user)
        await commit_with_error_handling(self.session, context="비밀번호 변경")