#사용자의 식재료 관리(추가 및 삭제)

from fastapi import APIRouter, Depends,HTTPException

from core.security import get_access_token
from database.orm import Ingredient, User
from database.repository import IngredientRepository, UserRepository
from schema.request import IngredientRequest
from schema.response import IngredientSchema
from service.user import UserService

router = APIRouter(prefix="/ingredients")


@router.post("/add", status_code=201) #식재료 추가
def create_ingredients_handler(
        request: IngredientRequest,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo : UserRepository = Depends(),
        ingredient_repo : IngredientRepository = Depends(),
    ) -> IngredientSchema:
    email: str = user_service.decode_jwt(access_token=access_token) #jwt 토큰 확인
    user: User | None = user_repo.get_user_by_email(email=email)
    if not user:
        raise HTTPException(status_code=404, detail="로그인 해야 사용가능")

    existing_ingredient = ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
    if existing_ingredient: #해당 아이디에서 같은 식재료를 또 추가하려 할 때,
        raise HTTPException(status_code=400, detail="이미 존재하는 식재료")

    ingredient: Ingredient = Ingredient.create(request=request, user_id=user.id)    #user_id는 로그인 된 유저의 id
    ingredient: Ingredient = ingredient_repo.create_ingredient(ingredient=ingredient)

    return IngredientSchema.model_validate(ingredient)


@router.get("/", status_code=200) # 식재료 조회
def get_ingredients_handler():
    pass


@router.delete("/", status_code=204) #식재료 삭제
def delete_todo_handler():
    pass