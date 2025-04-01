import logging

from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import InvalidRequestError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm import Ingredient

logger = logging.getLogger(__name__)

class IngredientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ingredient(self, ingredient):
        try:
            # 트랜잭션이 이미 시작된 상태인지 확인
            if not self.session.in_transaction():
                async with self.session.begin():  # 트랜잭션 시작
                    # 트랜잭션 내에서 ingredient 추가 작업
                    self.session.add(ingredient)
            else:
                # 이미 트랜잭션이 열린 상태면 그냥 추가 작업
                self.session.add(ingredient)

            # 커밋을 비동기적으로 처리
            await self.session.commit()

        except InvalidRequestError as e:
            # 예외 처리
            await self.session.rollback()  # 롤백 처리
            print(f"Transaction Error: {str(e)}")
            raise HTTPException(status_code=400, detail="Transaction Error")
        except IntegrityError as e:
            # 예외 처리
            await self.session.rollback()  # 롤백 처리
            print(f"IntegrityError: {str(e)}")
            raise HTTPException(status_code=400, detail="데이터베이스 제약 조건 위반")
        except Exception as e:
            # 기타 예외 처리
            await self.session.rollback()  # 롤백 처리
            print(f"Unexpected Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected Error")

    async def get_ingredient_by_name(self, user_id: int, name: str) -> Optional[Ingredient]:
        stmt = select(Ingredient).filter(Ingredient.user_id == user_id, Ingredient.name == name)
        result = await self.session.execute(stmt)
        return result.scalar()  # 첫 번째 결과 반환

    async def get_ingredients(self, user_id: int) -> List[Ingredient]:
        stmt = select(Ingredient).filter(Ingredient.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()  # 리스트로 반환

    async def delete_ingredient(self, user_id: int, ingredient_name: str) -> bool:
        try:
            stmt = delete(Ingredient).where(
                and_(Ingredient.user_id == user_id, Ingredient.name == ingredient_name)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0  # 삭제된 행이 있으면 True 반환
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"IntegrityError: {str(e)}")
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected Error: {str(e)}")
            return False
