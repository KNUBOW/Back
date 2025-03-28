from typing import List, Optional
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.future import select
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm import User, Ingredient
from core.connection import get_postgres_db


from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_postgres_db)):
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



class IngredientRepository:
    def __init__(self, session: AsyncSession = Depends(get_postgres_db)):
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
            # 트랜잭션이 열려 있는지 확인
            if not self.session.in_transaction():
                async with self.session.begin():  # 트랜잭션 시작
                    stmt = select(Ingredient).where(
                        Ingredient.name == ingredient_name, Ingredient.user_id == user_id
                    )
                    result = await self.session.execute(stmt)
                    ingredient = result.scalar()

                    if not ingredient:
                        raise HTTPException(status_code=404, detail="Ingredient not found")

                    # 삭제 작업
                    await self.session.delete(ingredient)
                    await self.session.commit()  # 삭제 후 커밋을 비동기적으로 처리
            else:
                stmt = select(Ingredient).where(
                    Ingredient.name == ingredient_name, Ingredient.user_id == user_id
                )
                result = await self.session.execute(stmt)
                ingredient = result.scalar()

                if not ingredient:
                    raise HTTPException(status_code=404, detail="Ingredient not found")

                # 삭제 작업
                await self.session.delete(ingredient)
                await self.session.commit()  # 커밋을 비동기적으로 처리

            return True
        except IntegrityError as e:
            await self.session.rollback()  # 롤백 처리
            print(f"IntegrityError: {str(e)}")
            raise HTTPException(status_code=400, detail="데이터베이스 제약 조건 위반")
        except Exception as e:
            await self.session.rollback()  # 롤백 처리
            print(f"Unexpected Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected Error")