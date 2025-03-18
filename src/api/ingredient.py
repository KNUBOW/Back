# 식재료 추가/조회/삭제 하는 식재료 관련 API

from fastapi import APIRouter, Depends
from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientListSchema
from service.ingredient import IngredientService
from service.user import UserService
from database.repository import IngredientRepository, UserRepository
from core.security import get_access_token

router = APIRouter(prefix="/ingredients")


def get_ingredient_service(
    user_repo: UserRepository = Depends(),
    ingredient_repo: IngredientRepository = Depends(),
    user_service: UserService = Depends()
) -> IngredientService:
    """FastAPI의 `Depends`를 사용하여 `IngredientService` 인스턴스를 생성"""
    return IngredientService(user_repo, ingredient_repo, user_service)


@router.post("", status_code=201)
def create_ingredient_handler(
    request: IngredientRequest,
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
) -> IngredientSchema:
    return ingredient_service.create_ingredient(request, access_token)


@router.get("", status_code=200)
def get_ingredients_handler(
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
) -> IngredientListSchema:
    return ingredient_service.get_ingredients(access_token)


@router.delete("/{ingredient_name}", status_code=204)
def delete_ingredient_handler(
    ingredient_name: str,
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
):
    ingredient_service.delete_ingredient(ingredient_name, access_token)