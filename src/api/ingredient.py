#사용자의 식재료 관리(추가 및 삭제)
from typing import List
from fastapi import APIRouter, Depends,HTTPException

from core.security import get_access_token
from database.orm import Ingredient, User
from database.repository import IngredientRepository, UserRepository
from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientListSchema
from service.user import UserService

router = APIRouter(prefix="/ingredients")


@router.post("", status_code=201) #식재료 추가
def create_ingredient_handler(
        request: IngredientRequest,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo : UserRepository = Depends(),
        ingredient_repo : IngredientRepository = Depends(),
    ) -> IngredientSchema:
    email: str = user_service.decode_jwt(access_token=access_token)
    user: User | None = user_repo.get_user_by_email(email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    existing_ingredient = ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
    if existing_ingredient: #해당 아이디에서 같은 식재료를 또 추가하려 할 때,
        raise HTTPException(status_code=400, detail="이미 존재하는 식재료")

    ingredient: Ingredient = Ingredient.create(request=request, user_id=user.id)    #user_id는 로그인 된 유저의 id(int)
    ingredient: Ingredient = ingredient_repo.create_ingredient(ingredient=ingredient)

    return IngredientSchema.model_validate(ingredient)


@router.get("", status_code=200) # 식재료 조회(All)
def get_ingredients_handler(
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
    ) -> IngredientListSchema:
    email: str = user_service.decode_jwt(access_token=access_token)
    user: User | None = user_repo.get_user_by_email(email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    ingredients: List[Ingredient] = user.ingredients
    return IngredientListSchema(
        ingredients=[IngredientSchema.model_validate(ingredient) for ingredient in ingredients]
    )


@router.delete("/{ingredient_name}", status_code=204) #식재료 삭제
def delete_ingredient_handler(
        ingredient_name: str,
        ingredient_repo: IngredientRepository = Depends(),
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
):
    email: str = user_service.decode_jwt(access_token=access_token)
    user: User | None = user_repo.get_user_by_email(email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    success = ingredient_repo.delete_ingredient(user_id=user.id, ingredient_name=ingredient_name)
    if not success:
        raise HTTPException(status_code=404, detail="해당 식재료 존재하지 않음")