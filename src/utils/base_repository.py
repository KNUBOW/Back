from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.exc import (
    InvalidRequestError,
    IntegrityError,
    SQLAlchemyError,
)
from exception.database_exception import TransactionException, DatabaseException
from exception.external_exception import UnexpectedException


async def commit_with_error_handling(session: AsyncSession, context: str = ""):
    try:
        await session.commit()
    except InvalidRequestError as e:
        await session.rollback()
        raise TransactionException(detail=f"{context}: {str(e)}")
    except IntegrityError as e:
        await session.rollback()
        raise DatabaseException(detail=f"{context}: 제약 조건 위반")
    except SQLAlchemyError as e:
        await session.rollback()
        raise DatabaseException(detail=f"{context}: DB 오류: {str(e)}")
    except Exception as e:
        await session.rollback()
        raise UnexpectedException(detail=f"{context}: 알 수 없는 에러: {str(e)}")