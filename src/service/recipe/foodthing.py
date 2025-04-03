import json
import re
import httpx

from fastapi import Depends
from sqlalchemy import select

from exception.foodthing_exception import (
    AIServiceException,
    AINullResponseException,
    AIJsonDecodeException,
    InvalidAIRequestException
)

from exception.auth_exception import (
    TokenExpiredException,
    UserNotFoundException
)

from service.auth.jwt_handler import get_access_token
from database.orm import Ingredient
from core.config import settings
from database.repository.user_repository import UserRepository
from service.user_service import UserService
from service.recipe.prompt_builder import PromptBuilder
from core.logging import service_log

def get_cook_ai(
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    return CookAIService(user_service, user_repo, access_token)


class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.MODEL_NAME
        self.num_predict = 2000
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token

    async def _get_authenticated_user(self):
        try:
            user = await self.user_service.get_user_by_token(self.access_token)
        except TokenExpiredException:
            raise
        except Exception as e:
            raise TokenExpiredException(detail=f"토큰 처리 중 오류: {str(e)}")

        if not user:
            raise UserNotFoundException()

        return user

    async def get_user_ingredients(self):
        user = await self._get_authenticated_user()

        try:
            ingredients = await self.user_repo.session.execute(
                select(Ingredient.name).filter(Ingredient.user_id == user.id)
            )
        except Exception as e:
            raise AIServiceException(detail=f"DB에서 재료 조회 실패: {str(e)}")

        return [name for (name,) in ingredients.all()]

    async def call_ollama(self, prompt):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }

        timeout = httpx.Timeout(50.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(self.ollama_url, json=payload)
        except httpx.RequestError as e:
            raise AIServiceException(detail=f"Ollama 네트워크 오류: {str(e)}")

        if response.status_code != 200:
            raise AIServiceException(detail=f"Ollama 호출 실패: {response.status_code} - {response.text}")

        response_text = response.json().get("response", "").strip()

        if not response_text:
            raise AINullResponseException()

        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            response_text = match.group(1).strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise AIJsonDecodeException(detail=f"응답 파싱 실패: {response_text}")

    async def get_suggest_recipes(self):
        user = await self._get_authenticated_user()
        user_ingredients = await self.get_user_ingredients()

        service_log("RecipeService", f"AI 추천 레시피 요청", user_id=user.id)

        prompt = PromptBuilder.build_suggestion_prompt(user_ingredients)
        return await self.call_ollama(prompt)

    async def get_food_recipe(self, request_data: dict):
        user = await self._get_authenticated_user()

        food = request_data.get("food")
        use_ingredients = request_data.get("use_ingredients", [])

        service_log("RecipeService", f"AI 레시피 요청: '{food}'", user_id=user.id)

        if not food or not isinstance(use_ingredients, list):
            raise InvalidAIRequestException(detail="올바른 'food' 및 'use_ingredients' 값을 제공해야 합니다.")

        prompt = PromptBuilder.build_recipe_prompt(food, use_ingredients)
        return await self.call_ollama(prompt)

    async def get_quick_recipe(self, chat: str):
        user = await self._get_authenticated_user()
        prompt = PromptBuilder.build_quick_prompt(chat)
        service_log("RecipeService", f"빠른 AI 레시피 요청: '{chat}'", user_id=user.id)
        return await self.call_ollama(prompt)

    async def get_search_recipe(self, chat: str):
        user = await self._get_authenticated_user()
        prompt = PromptBuilder.build_search_prompt(chat)
        service_log("RecipeService", f"레시피 검색 요청: '{chat}'", user_id=user.id)
        return await self.call_ollama(prompt)