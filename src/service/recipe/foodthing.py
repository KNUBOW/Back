import json
import re
import httpx

from fastapi import Depends, Request
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

# LLM 서비스 관련

class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str, req: Request):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = settings.MODEL_NAME
        self.num_predict = 2000
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token
        self.req = req

    # 유저 정보 확인
    async def _get_authenticated_user(self):
        try:
            user = await self.user_service.get_user_by_token(self.access_token, self.req)
        except TokenExpiredException:
            raise
        except Exception as e:
            raise TokenExpiredException(detail=f"토큰 처리 중 오류: {str(e)}")

        if not user:
            raise UserNotFoundException()

        return user

    # 식재료 조회
    async def get_user_ingredients(self):
        user = await self._get_authenticated_user()

        try:
            ingredients = await self.user_repo.session.execute(
                select(Ingredient.name).filter(Ingredient.user_id == user.id)
            )
        except Exception as e:
            raise AIServiceException(detail=f"DB에서 재료 조회 실패: {str(e)}")

        return [name for (name,) in ingredients.all()]

    # ollama 호출
    async def call_ollama(self, prompt):
        health_url = self.ollama_url.replace("/api/generate", "/")
        timeout = httpx.Timeout(50.0)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 서버 확인 먼저 (필요없는 로딩 없애기 위해)
                await client.get(health_url)
        except httpx.RequestError as e:
            raise AIServiceException(detail=f"Ollama 서버에 연결할 수 없습니다: {str(e)}")

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }


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

    # 만들 수 있는 요리 리스트 출력
    async def get_suggest_recipes(self):
        user = await self._get_authenticated_user()
        user_ingredients = await self.get_user_ingredients()

        service_log("RecipeService", f"AI 추천 레시피 요청", user_id=user.id)

        prompt = PromptBuilder.build_suggestion_prompt(user_ingredients)
        return await self.call_ollama(prompt)

    # 요리 레시피 출력
    async def get_food_recipe(self, request_data: dict):
        user = await self._get_authenticated_user()

        food = request_data.get("food")
        use_ingredients = request_data.get("use_ingredients", [])

        service_log("RecipeService", f"AI 레시피 요청: '{food}'", user_id=user.id)

        if not food or not isinstance(use_ingredients, list):
            raise InvalidAIRequestException(detail="올바른 'food' 및 'use_ingredients' 값을 제공해야 합니다.")

        prompt = PromptBuilder.build_recipe_prompt(food, use_ingredients)
        return await self.call_ollama(prompt)

    # 간단한 입력식 레시피 출력 (식재료만 입력)
    async def get_quick_recipe(self, chat: str):
        user = await self._get_authenticated_user()
        prompt = PromptBuilder.build_quick_prompt(chat)
        service_log("RecipeService", f"입력식 AI 레시피 요청: '{chat}'", user_id=user.id)
        return await self.call_ollama(prompt)

    # 레시피 검색(식재료 없이 요리이름만 입력)
    async def get_search_recipe(self, chat: str):
        user = await self._get_authenticated_user()
        prompt = PromptBuilder.build_search_prompt(chat)
        service_log("RecipeService", f"레시피 검색 요청: '{chat}'", user_id=user.id)
        return await self.call_ollama(prompt)