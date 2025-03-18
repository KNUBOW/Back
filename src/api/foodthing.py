# foodthing API (요리 리스트 추천, 요리 레시피 제공, 빠른 레시피(챗봇) 제공)

from fastapi import APIRouter, Depends, Body
from core.security import get_access_token
from database.repository import UserRepository
from service.foodthing import CookAIService
from schema.request import CookingRequest
from service.user import UserService

router = APIRouter(prefix="/recipe")

@router.get("/suggest", status_code=200)    #요리 레시피 리스트 추천 API
def suggest_recipe(
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    cook_ai = CookAIService(user_service, user_repo, access_token)
    return cook_ai.get_suggest_recipes()  # JSON 응답


@router.post("/cooking", status_code=200)   #요리 레시피 API
def cooking_recipe(
        request: CookingRequest,
        access_token: str = Depends(get_access_token),
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
):
    cook_ai = CookAIService(user_service, user_repo, access_token)

    # request 객체를 dict로 변환 후 service로 전달
    request_data = request.model_dump()
    return cook_ai.get_food_recipe(request_data)  # JSON 응답

@router.post("/quick", status_code=200)
def quick_recipe(
    chat: str = Body(..., media_type="text/plain"),
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    cook_ai = CookAIService(user_service, user_repo, access_token)
    return cook_ai.get_quick_recipe(chat)  # JSON 응답