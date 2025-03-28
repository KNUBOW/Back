# service/ingredient.py
from typing import List
from fastapi import HTTPException
from database.orm import Ingredient, User
from database.repository import IngredientRepository, UserRepository
from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientListSchema
from service.user import UserService


class IngredientService:
    def __init__(self, user_repo: UserRepository, ingredient_repo: IngredientRepository, user_service: UserService):
        self.user_repo = user_repo
        self.ingredient_repo = ingredient_repo
        self.user_service = user_service

    async def get_user_by_token(self, access_token: str) -> User:
        """JWT 토큰에서 사용자 정보 가져오기"""
        email: str = self.user_service.decode_jwt(access_token=access_token)
        user: User | None = await self.user_repo.get_user_by_email(email=email)  # 비동기 호출
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        return user

    async def create_ingredient(self, request: IngredientRequest, access_token: str) -> IngredientSchema:
        """사용자의 식재료 추가"""
        user = await self.get_user_by_token(access_token)

        existing_ingredient = await self.ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
        if existing_ingredient:
            raise HTTPException(status_code=400, detail="이미 존재하는 식재료")

        ingredient = Ingredient.create(request=request, user_id=user.id)
        await self.ingredient_repo.create_ingredient(ingredient=ingredient)  # 비동기 호출

        return IngredientSchema.model_validate(ingredient)

    async def get_ingredients(self, access_token: str) -> IngredientListSchema:
        """사용자의 식재료 목록 조회"""
        user = await self.get_user_by_token(access_token)
        ingredients: List[Ingredient] = await self.ingredient_repo.get_ingredients(user_id=user.id)  # 비동기 호출
        return IngredientListSchema(
            ingredients=[IngredientSchema.model_validate(ingredient) for ingredient in ingredients]
        )

    async def delete_ingredient(self, ingredient_name: str, access_token: str) -> None:
        """사용자의 식재료 삭제"""
        user = await self.get_user_by_token(access_token)
        success = await self.ingredient_repo.delete_ingredient(user_id=user.id, ingredient_name=ingredient_name)  # 비동기 호출
        if not success:
            raise HTTPException(status_code=404, detail="해당 식재료 존재하지 않음")