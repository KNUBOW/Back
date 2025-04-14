from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm import IngredientCategories
from exception.admin_exception import CategoryNotFoundException
from schema.request import IngredientCategoriesRequest
from utils.base_repository import commit_with_error_handling

#관리자 권한 리포지토리

class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_category_by_name(self, ingredient_name: str):
        result = await self.session.execute(
            select(IngredientCategories).filter_by(ingredient_name=ingredient_name)
        )
        return result.scalars().first()

    async def create_category(self, request: IngredientCategoriesRequest, user_id: int):
        new_category = IngredientCategories(
            user_id=user_id,
            ingredient_name=request.ingredient_name,
            parent_category=request.parent_category,
            child_category=request.child_category,
            default_expiration_days=request.default_expiration_days
        )
        self.session.add(new_category)
        await commit_with_error_handling(self.session, context="카테고리 생성")
        await self.session.refresh(new_category)
        return new_category

    async def get_all_categories(self):
        result = await self.session.execute(
            select(IngredientCategories).order_by(IngredientCategories.id)
        )
        return result.scalars().all()

    async def delete_category_by_name(self, ingredient_name: str) -> bool:
        category = await self.get_category_by_name(ingredient_name)
        if not category:
            return False

        await self.session.delete(category)
        await commit_with_error_handling(self.session, context=f"{ingredient_name} 카테고리 삭제")
        return True

    async def update_category_expiration(self, ingredient_name: str, new_expiration: int) -> bool:
        category = await self.get_category_by_name(ingredient_name)
        if not category:
            return False

        category.default_expiration_days = new_expiration
        await commit_with_error_handling(self.session, context=f"[{ingredient_name}] 카테고리 유통기한 수정")
        await self.session.refresh(category)
        return True