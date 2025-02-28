#사용자에게 레시피 제공해달라는 요청 받으면, 사용자가 현재 들고있는 재료를 보고, 레시피를 줌

import json
import re

from core.security import get_access_token
from database.repository import UserRepository
from service.cookai import CookAIService
from fastapi import APIRouter, Depends, HTTPException

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
            recipe = {"food": r["food"], "status": r["status"]}
            if "missing_ingredients" in r and r["missing_ingredients"]:  # 값이 있을 때만 추가
                recipe["missing_ingredients"] = r["missing_ingredients"]
            filtered_recipes.append(recipe)

        return {"recipes": filtered_recipes}

    except json.JSONDecodeError:
        return {"error": "JSON 파싱 오류", "raw_response": response_text}
    except KeyError as e:
        return {"error": f"응답 처리 중 필요한 데이터 누락: {str(e)}", "raw_response": response_text}
