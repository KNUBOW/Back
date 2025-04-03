from database.orm import Ingredient
from schema.request import IngredientRequest
from schema.response import IngredientListSchema, IngredientSchema
from core.logging import service_log
from fastapi import Request

from exception.ingredient_exception import (
    IngredientConflictException,
    IngredientNotFoundException
)


class IngredientService:
    def __init__(self, user_repo, ingredient_repo, user_service, access_token: str, req: Request):
        self.user_repo = user_repo
        self.ingredient_repo = ingredient_repo
        self.user_service = user_service
        self.access_token = access_token
        self.req = req

    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token, self.req)

    async def create_ingredient(self, request: IngredientRequest):
        user = await self.get_current_user()

        # 중복 확인
        existing = await self.ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
        if existing:
            raise IngredientConflictException()

        ingredient = Ingredient.create(request, user.id)
        await self.ingredient_repo.create_ingredient(ingredient)

        service_log("IngredientService", f"식재료 '{ingredient.name}' 추가", user_id=user.id)

        return IngredientSchema.model_validate(ingredient)


    async def get_ingredients(self):
        user = await self.get_current_user()
        ingredients = await self.ingredient_repo.get_ingredients(user.id)

        service_log("IngredientService", f"식재료 목록 조회", user_id=user.id)

        return IngredientListSchema(ingredients=ingredients)

    async def delete_ingredient(self, ingredient_name: str):
        user = await self.get_current_user()
        success = await self.ingredient_repo.delete_ingredient(user.id, ingredient_name)

        if not success:
            raise IngredientNotFoundException()

        service_log("IngredientService", f"식재료 '{ingredient_name}' 삭제", user_id=user.id)
        return True