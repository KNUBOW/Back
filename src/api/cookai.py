#사용자에게 레시피 제공해달라는 요청 받으면, 사용자가 현재 들고있는 재료를 보고, 레시피를 줌

import json
import re

from core.security import get_access_token
from database.repository import UserRepository
from service.cookai import CookAIService
from fastapi import APIRouter, Depends, HTTPException
from schema.request import CookingRequest

from service.user import UserService

router = APIRouter(prefix="/recipe")

@router.get("/suggest")  # 레시피 제안
def suggest_recipe(
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    cook_ai = CookAIService(user_service=user_service, user_repo=user_repo, access_token=access_token)
    response = cook_ai.get_suggest_recipes()  # AI에서 받은 응답

    if not response:
        raise HTTPException(status_code=500, detail="AI 응답이 비어 있습니다.")

    # 마크다운 코드 블록 제거 (예: ```json ... ```)
    response_text = re.sub(r"^```json\n|\n```$", "", response.strip())

    try:
        response_json = json.loads(response_text)  # JSON 변환

        if "recipes" not in response_json:
            raise HTTPException(status_code=500, detail="AI 응답에 'recipes' 키가 없습니다.")

        filtered_recipes = []
        for r in response_json["recipes"]:
            recipe = {"food": r["food"], "use_ingredients": r["use_ingredients"]}
            filtered_recipes.append(recipe)

        return {"recipes": filtered_recipes}

    except json.JSONDecodeError:
        return {"error": "JSON 파싱 오류", "raw_response": response_text}
    except KeyError as e:
        return {"error": f"응답 처리 중 필요한 데이터 누락: {str(e)}", "raw_response": response_text}

@router.post("/cooking")  # POST 방식으로 요리 레시피 불러오기
def cooking_recipe(
    request: CookingRequest,
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    cook_ai = CookAIService(user_service=user_service, user_repo=user_repo, access_token=access_token)

    # AI에게 요리 레시피 요청
    response = cook_ai.get_food_recipe(food=request.food)

    if not response:
        raise HTTPException(status_code=500, detail="AI로부터 레시피 응답이 비어 있습니다.")

    # 마크다운 코드 블록 제거 (예: ```json ... ```)
    response_text = re.sub(r"^```json\n|\n```$", "", response.strip())

    try:
        response_json = json.loads(response_text)  # JSON 변환

        if "recipe" not in response_json:
            raise HTTPException(status_code=500, detail="AI 응답에 'recipe' 키가 없습니다.")

        return response_json  # 레시피 JSON 반환

    except json.JSONDecodeError:
        return {"error": "JSON 파싱 오류", "raw_response": response_text}
    except KeyError as e:
        return {"error": f"응답 처리 중 필요한 데이터 누락: {str(e)}", "raw_response": response_text}