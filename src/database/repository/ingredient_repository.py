from typing import Optional, List
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm import Ingredient

from exception.external_exception import UnexpectedException

from sqlalchemy.exc import (
    InvalidRequestError,
    IntegrityError,
    SQLAlchemyError,
)

from exception.database_exception import (
    TransactionException,
    DatabaseException)

class IngredientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ingredient(self, ingredient):
        try:
            async with self.session.begin_nested() if self.session.in_transaction() else self.session.begin():
                self.session.add(ingredient)

            await self.session.commit()

        except InvalidRequestError as e:    #Transaction 에러
            await self.session.rollback()
            raise TransactionException(detail=str(e))

        except IntegrityError:  # 식재료 중복 시
            await self.session.rollback()
            raise DatabaseException(detail="제약 조건 위반: 식재료 중복 등")

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(detail=f"DB 처리 중 오류: {str(e)}")

        except Exception as e:  # 예상치 못한 에러
            await self.session.rollback()
            raise UnexpectedException(detail=f"예기치 못한 에러 발생: {str(e)}")

    async def get_ingredient_by_name(self, user_id: int, name: str) -> Optional[Ingredient]:
        stmt = select(Ingredient).filter(
            Ingredient.user_id == user_id,
            Ingredient.name == name)
        result = await self.session.execute(stmt)
        return result.scalar()  # 첫 번째 결과 반환

    async def get_ingredients(self, user_id: int) -> List[Ingredient]:
        try:
            stmt = select(Ingredient).filter(Ingredient.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()

        except SQLAlchemyError as e:
            raise DatabaseException(detail=f"재료 조회 중 DB 오류: {str(e)}")

        except Exception as e:
            raise UnexpectedException(detail=f"예기치 못한 에러 발생: {str(e)}")

    async def delete_ingredient(self, user_id: int, ingredient_name: str) -> bool:
        try:
            stmt = delete(Ingredient).where(
                and_(Ingredient.user_id == user_id, Ingredient.name == ingredient_name)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0


        except InvalidRequestError as e:
            await self.session.rollback()
            raise TransactionException(detail=str(e))

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(detail=f"DB 삭제 중 오류: {str(e)}")

        except Exception as e:
            await self.session.rollback()
            raise UnexpectedException(detail=f"예기치 못한 에러 발생: {str(e)}")