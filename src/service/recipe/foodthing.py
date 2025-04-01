import json
import re
import httpx

from fastapi import HTTPException, Depends
from sqlalchemy import select

from service.auth.jwt_handler import get_access_token
from database.orm import Ingredient
from core.config import Settings
from database.repository.user_repository import UserRepository
from service.user_service import UserService
from service.recipe.prompt_builder import PromptBuilder


def get_cook_ai(
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    return CookAIService(user_service, user_repo, access_token)


class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str):
        self.ollama_url = Settings.ollama_url
        self.model_name = Settings.model_name
        self.num_predict = 2000
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token

    async def get_user_ingredients(self):
        """현재 로그인한 사용자의 식재료 목록을 조회"""
        user = await self.user_service.get_user_by_token(self.access_token)
        ingredients = await self.user_repo.session.execute(
            select(Ingredient.name).filter(Ingredient.user_id == user.id)
        )
        return [name for (name,) in ingredients.all()]

    async def call_ollama(self, prompt):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }

        timeout = httpx.Timeout(50.0)  # 50초로 설정

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(self.ollama_url, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama 오류: {response.status_code} - {response.text}")

        response_text = response.json().get("response", "").strip()

        if not response_text:
            raise HTTPException(status_code=500, detail="AI 응답이 비어 있습니다.")

        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            response_text = match.group(1).strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"AI 응답을 JSON으로 변환하는 중 오류 발생: {response_text}")

    async def get_suggest_recipes(self):
        """사용자가 만들 수 있는 요리 추천"""
        user_ingredients = await self.get_user_ingredients()
        prompt = PromptBuilder.build_suggestion_prompt(user_ingredients)
        return await self.call_ollama(prompt)

    async def get_food_recipe(self, request_data: dict):
        """선택한 요리의 레시피 제공"""
        food = request_data.get("food")
        use_ingredients = request_data.get("use_ingredients", [])

        if not food or not isinstance(use_ingredients, list):
            raise HTTPException(status_code=400, detail="올바른 'food' 및 'use_ingredients' 값을 제공해야 합니다.")

        prompt = PromptBuilder.build_recipe_prompt(food, use_ingredients)
        return await self.call_ollama(prompt)

    async def get_quick_recipe(self, chat: str):
        """빠른 요리 추천 - 사용자가 입력한 재료만 활용"""
        prompt = PromptBuilder.build_quick_prompt(chat)
        return await self.call_ollama(prompt)

    async def get_search_recipe(self, chat: str):
        """요리 검색 - 음식명을 기반으로 레시피 반환"""
        prompt = PromptBuilder.build_search_prompt(chat)
        return await self.call_ollama(prompt)
