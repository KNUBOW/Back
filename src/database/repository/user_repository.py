from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
    InvalidRequestError
)

from exception.database_exception import (
    DatabaseException,
    TransactionException
)

from exception.external_exception import UnexpectedException
from database.orm import User

# 유저 관련 리프지토리

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).filter(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_user_by_nickname(self, nickname: str) -> Optional[User]:
        stmt = select(User).filter(User.nickname == nickname)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def save_user(self, user: User) -> User:
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user

        except InvalidRequestError: #트랜젝션 관련 에러
            await self.session.rollback()
            raise TransactionException()

        except IntegrityError:  # 중복 관련 오류
            await self.session.rollback()
            raise DatabaseException(detail=f"제약 조건 위반: 이메일, 닉네임 중복 등")

        except SQLAlchemyError as e:    # DB 오류
            await self.session.rollback()
            raise DatabaseException(detail=f"DB 처리 중 오류: {str(e)}")

        except Exception as e:  # 알 수 없는 에러
            await self.session.rollback()
            raise UnexpectedException(detail=f"예기치 못한 에러 발생: {str(e)}")