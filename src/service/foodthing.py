import requests
import json
import re

from fastapi import HTTPException
from core.config import Settings
from database.repository import UserRepository
from service.user import UserService


class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str):
        self.ollama_url = Settings.ollama_url
        self.model_name = Settings.model_name
        self.num_predict = 2000
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token

    def get_user_ingredients(self):
        """현재 로그인한 사용자의 식재료 목록을 조회"""
        email = self.user_service.decode_jwt(access_token=self.access_token)
        user = self.user_repo.get_user_by_email(email=email)
        if not user:
            raise HTTPException(status_code=404, detail="유저가 존재하지 않습니다.")

        # 유저의 식재료 리스트를 가져옴
        return [ingredient.name for ingredient in (user.ingredients or [])]

    def get_prompt(self, prompt_type: str, user_ingredients: list = None, food: str = None, chat: str = None):
        """프롬프트 생성 (추천, 레시피, 빠른 답변)"""
        base_prompt = """
        당신은 전문 요리 연구가이며, 레시피 추천 전문가입니다.
        🔹 **반드시 JSON 형식으로만 응답하세요.**
        🔹 **추가 설명 없이 JSON 데이터만 반환하세요.** 
        🔹 **응답이 올바른 JSON 형식인지 유효성을 항상 검증하세요.**
        """

        if prompt_type == "suggestion":
            return f"""
            {base_prompt}
            사용자가 현재 보유한 식재료를 최대한 활용하여 만들 수 있는 요리 **6가지**를 추천하세요.
            사용 가능한 재료 목록: {json.dumps(user_ingredients, ensure_ascii=False)}

            🔹 **반드시 사용자가 가진 재료 내에서 만들 수 있는 요리만 추천하세요.**
            🔹 **추천 요리는 현실적으로 조리 가능한 것만 포함하세요.**
            🔹 **응답 예시는 다음 JSON 형식과 동일해야 합니다.**
            🔹 **모든 값(value)은 한국어로만 대답하세요.**

            예시 응답:
            {{
              "recipes": [
                {{"food": "김치볶음밥", "use_ingredients": ["김치", "밥"]}},
                {{"food": "된장찌개", "use_ingredients": ["된장", "두부", "대파"]}}
              ]
            }}
            """

        elif prompt_type == "recipe":
            user_ingredients = user_ingredients or []  # None 방지
            ingredients_json = json.dumps(user_ingredients, ensure_ascii=False)

            return f"""
            {base_prompt}
            사용자가 요청한 음식의 **상세 조리법**을 제공합니다.

            요청된 음식: "{food}"  
            사용 가능한 재료: {ingredients_json}

            🔹 **반드시 요청된 음식과 제공된 재료를 사용하여 레시피를 작성하세요.**
            🔹 **레시피는 최소 450자 이상, 상세한 조리 방법을 포함해야 합니다.**
            🔹 **응답 예시는 아래 JSON 형식을 따라야 합니다.**

            예시 응답:
            {{
              "food": "{food}",
              "use_ingredients": {ingredients_json},
              "steps": [
                "양파를 잘게 썬다.",
                "계란을 풀고 치즈를 섞는다.",
                "팬에 기름을 두르고 오믈렛을 만든다."
              ]
            }}
            """


        elif prompt_type == "quick":

            return f"""
            {base_prompt}
            사용자가 입력한 재료 목록을 활용하여 **15분 이내**에 만들 수 있는 **간단한 요리 1가지**를 추천하세요.

            사용자 입력: "{chat}"

            🔹 **입력된 재료만 사용하고, 추가 재료는 절대 포함하지 마세요.**  
            🔹 **모든 재료를 반드시 사용할 필요는 없으며, 핵심 재료를 선택하세요.**  
            🔹 **조리 과정은 최소 300자 이상, 단계별로 상세히 설명하세요.**  
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **사용자가 식재료와 무관한 내용을 입력하면, '식재료를 입력해 주세요.'라고 응답하세요.**  
            
            **예시 응답 (요리 추천)**:
            ```json
            {{
              "food": "치즈 오믈렛",
              "use_ingredients": ["계란", "치즈", "우유"],
              "steps": [
                "계란을 풀고 치즈와 우유를 넣어 섞는다.",
                "팬에 기름을 두르고 계란 혼합물을 부어 중약불에서 익힌다.",
                "반으로 접어 완성한다."
              ]
            }}
            ```

            **예시 응답 (잘못된 입력 처리)**:
            ```json
            {{
              "error": "식재료를 입력해 주세요."
            }}
            ```
            """

        else:
            raise ValueError("Invalid prompt_type. Use 'suggestion', 'recipe', or 'quick'.")

    def call_ollama(self, prompt):
        """Ollama API 호출 및 JSON 변환"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }
        response = requests.post(self.ollama_url, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama 오류: {response.status_code} - {response.text}")

        response_text = response.json().get("response", "").strip()

        if not response_text:
            raise HTTPException(status_code=500, detail="AI 응답이 비어 있습니다.")

        # JSON 코드 블록 제거 (```json ... ```)
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            response_text = match.group(1).strip()

        try:
            return json.loads(response_text)  # JSON 변환
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"AI 응답을 JSON으로 변환하는 중 오류 발생: {response_text}")

    def get_suggest_recipes(self):
        """사용자가 만들 수 있는 요리 추천"""
        user_ingredients = self.get_user_ingredients()
        prompt = self.get_prompt("suggestion", user_ingredients)
        return self.call_ollama(prompt)

    def get_food_recipe(self, request_data: dict):
        """선택한 요리의 레시피 제공"""

        # dict에서 필요한 값 추출
        food = request_data.get("food")  # 기본값 처리
        use_ingredients = request_data.get("use_ingredients", [])

        if not food or not isinstance(use_ingredients, list):
            raise HTTPException(status_code=400, detail="올바른 'food' 및 'use_ingredients' 값을 제공해야 합니다.")

        prompt = self.get_prompt("recipe", user_ingredients=use_ingredients, food=food)
        return self.call_ollama(prompt)

    def get_quick_recipe(self, chat: str):
        """빠른 요리 추천 - 사용자가 입력한 재료만 활용"""
        prompt = self.get_prompt("quick", chat=chat)
        return self.call_ollama(prompt)