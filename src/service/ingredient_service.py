from fastapi import HTTPException

from database.orm import Ingredient
from schema.request import IngredientRequest
from schema.response import IngredientListSchema, IngredientSchema


class IngredientService:
    def __init__(self, user_repo, ingredient_repo, user_service, access_token: str):
        self.user_repo = user_repo
        self.ingredient_repo = ingredient_repo
        self.user_service = user_service
        self.access_token = access_token

    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token)

    async def create_ingredient(self, request: IngredientRequest):
        user = await self.get_current_user()

        # ✅ 중복 확인
        existing = await self.ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 식재료입니다.")

        ingredient = Ingredient.create(request, user.id)
        await self.ingredient_repo.create_ingredient(ingredient)
        return IngredientSchema.model_validate(ingredient)

    async def get_ingredients(self):
        user = await self.get_current_user()
        ingredients = await self.ingredient_repo.get_ingredients(user.id)
        return IngredientListSchema(ingredients=ingredients)

    async def delete_ingredient(self, ingredient_name: str):
        user = await self.get_current_user()
        success = await self.ingredient_repo.delete_ingredient(user.id, ingredient_name)
        if not success:
            raise HTTPException(status_code=404, detail="삭제할 식재료가 없습니다.")