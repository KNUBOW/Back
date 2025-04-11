from typing import Optional, List
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from exception.external_exception import UnexpectedException

from sqlalchemy.exc import (
    SQLAlchemyError,
)

from database.orm import (
    Ingredient,
    ManualExpirationLog,
    UnrecognizedIngredientLog,
    IngredientCategories
)

from exception.database_exception import (
    DatabaseException)

from utils.base_repository import commit_with_error_handling
# 식재료 관련 리포지토리

class IngredientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ingredient(self, ingredient):
        self.session.add(ingredient)
        await commit_with_error_handling(self.session, context="식재료 생성")

    # 유통기한 카테고리 에서 유통기한 부여
    async def get_default_expiration(self, ingredient_name: str) -> Optional[int]:
        stmt = select(IngredientCategories.default_expiration_days).where(
            IngredientCategories.ingredient_name == ingredient_name
        )
        result = await self.session.execute(stmt)
        days = result.scalar()
        if days is not None:
            return (datetime.utcnow() + timedelta(days=days)).date()
        return None

    # 유저가 수동적으로 입력한 유통기한 로그 관련 (유통기한 편차 확인용)
    async def save_manual_expiration_log(self, user_id: int, ingredient_name: str, expiration_date: int, event_type: str):
        log = ManualExpirationLog(
            user_id=user_id,
            ingredient_name=ingredient_name,
            expiration_date=expiration_date,
            event_type=event_type
        )
        self.session.add(log)
        await commit_with_error_handling(self.session, context="수동 유통기한 로그 저장")

    # 유저가 유통기한 부여하지 않고, 우리 DB에도 해당 식재료에 대한 유통기한 없을 때 확인하는 로그 (업데이트용)
    async def save_unrecognized_ingredient_log(self, user_id: int, ingredient_name: str):
        log = UnrecognizedIngredientLog(
            user_id=user_id,
            ingredient_name=ingredient_name
        )
        self.session.add(log)
        await commit_with_error_handling(self.session, context="유통기한 미인식 로그 저장")

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
        stmt = delete(Ingredient).where(
            and_(Ingredient.user_id == user_id, Ingredient.name == ingredient_name)
        )
        result = await self.session.execute(stmt)
        await commit_with_error_handling(self.session, context="식재료 삭제")
        return result.rowcount > 0