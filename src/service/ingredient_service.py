from database.orm import Ingredient
from schema.request import IngredientRequest
from schema.response import IngredientListSchema, IngredientSchema
from core.logging import service_log
from fastapi import Request
from datetime import date
from typing import List, Dict

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

    async def create_ingredient(self, request: IngredientRequest) -> IngredientSchema:
        result = await self.create_ingredients([request])

        if not result["created"]:
            # 중복이라 등록 안 된 경우 예외 발생
            raise IngredientConflictException()

        return result["created"][0]

    async def create_ingredients(self, requests: List[IngredientRequest]) -> Dict:
        user = await self.get_current_user()
        created_ingredients = []
        duplicated_names = []

        for request in requests:
            # 중복 확인
            existing = await self.ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
            if existing:
                duplicated_names.append(request.name)
                continue

            expiration_date = request.expiration_date

            if expiration_date:
                days_left = (expiration_date - date.today()).days
                await self.ingredient_repo.save_manual_expiration_log(
                    user_id=user.id,
                    ingredient_name=request.name,
                    expiration_date=days_left
                )
            else:
                default_expiration = await self.ingredient_repo.get_default_expiration(request.name)
                if default_expiration:
                    expiration_date = default_expiration
                else:
                    await self.ingredient_repo.save_unrecognized_ingredient_log(
                        user_id=user.id,
                        ingredient_name=request.name
                    )

            ingredient = Ingredient.create(request, user.id, expiration_date=expiration_date)
            await self.ingredient_repo.create_ingredient(ingredient)

            service_log("IngredientService", f"식재료 '{ingredient.name}' 추가", user_id=user.id)
            created_ingredients.append(IngredientSchema.model_validate(ingredient))

        # 결과 메시지 생성
        message = f"{len(created_ingredients)}개 식재료가 추가되었습니다."
        if duplicated_names:
            message += f" 중복으로 인해 {len(duplicated_names)}개는 제외되었습니다: {', '.join(duplicated_names)}"

        return {
            "message": message,
            "created": created_ingredients,
            "skipped_duplicates": duplicated_names
        }


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