import requests
import json
from core.config import Settings
from database.repository import UserRepository
from service.user import UserService

class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str):
        self.ollama_url = Settings.ollama_url
        self.model_name = Settings.model_name
        self.num_predict = 1500
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token

    def get_user_ingredients(self):
        """현재 로그인한 사용자의 식재료 목록을 조회"""
        email = self.user_service.decode_jwt(access_token=self.access_token)
        user = self.user_repo.get_user_by_email(email=email)
        if not user:
            raise Exception("유저 존재하지 않음")
        return [ingredient.name for ingredient in user.ingredients]

    def generate_recipe_prompt(self, user_ingredients, prompt_type="suggestion"):
        """요청 타입에 따라 프롬프트를 생성하는 메서드"""
        if prompt_type == "suggestion":
            prompt_detail = f"""
        당신은 요리 레시피 전문가입니다.
        최대한 사용자의 식재료를 활용하여 만들 수 있는 요리를 우선 추천하며,
        도저히 만들기 어려운 경우, 최소한의 추가 재료를 추천해주세요.

        응답은 **반드시 JSON 형식**으로 작성해야 하며,
        불필요한 설명 없이 JSON 데이터만 출력하세요.

        ## 요구사항
        - '현재 가지고 있는 재료만으로 만들 수 있는 요리'와 '추가 재료가 필요한 요리'를 **구분**해서 제공하세요.
        - **추가 재료가 필요한 경우, 부족한 재료 목록을 포함하세요.**
        - **JSON 형식의 순수 데이터만 반환하세요. (불필요한 설명 금지)**

        ### 입력된 사용자의 식재료
        {json.dumps(user_ingredients, ensure_ascii=False)}

        ## 응답 JSON 예시
        ```json
        {{
          "recipes": [
            {{
              "food": "김치볶음밥",
              "status": true
              "use_ingredients": ["김치", "밥"]
            }},
            {{
              "food": "토마토파스타",
              "status": false,
              "use_ingredients": 파스타면
              "missing_ingredients": ["토마토"]
            }}
          ]
        }}
        ```
        """

        elif prompt_type == "recipe":
            prompt_detail = f"""
사용자가 선택한 요리에 대한 레시피를 알려주세요. 아래의 JSON 형식에 맞는 데이터를 제공합니다:
[
    {{
        "food": "김치볶음밥",
        "status": true,
        "use_ingredients": ["김치", "밥"]
    }}
    또는
    {{
        "food": "토마토파스타",
        "status": false,
        "use_ingredients": ["파스타면"],
        "missing_ingredients": ["토마토"]
    }}
]

조건:
- "status": true인 경우는 "use_ingredients" 목록에 있는 재료로 바로 레시피를 제공합니다.
- "status": false인 경우는 "use_ingredients" 목록에 있는 재료와 "missing_ingredients" 목록에 포함된 재료가 모두 사용자의 식재료 목록에 있는 경우에만 레시피를 제공합니다.

입력한 음식에 맞는 레시피를 제공할 수 있도록 위 조건을 고려하여 응답해 주세요.
"""
        else:
            raise ValueError("Invalid prompt_type. Use 'suggestion' or 'recipe'.")

        return prompt_detail

    def call_ollama(self, prompt):
        """Ollama API 호출하는 메서드"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }

        response = requests.post(self.ollama_url, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result["response"]
        else:
            raise Exception(f"❌ Ollama 오류: {response.status_code} - {response.text}")

    def get_suggest_recipes(self):
        """사용자가 만들 수 있는 요리 리스트 추천"""
        user_ingredients = self.get_user_ingredients()
        prompt = self.generate_recipe_prompt(user_ingredients, "suggestion")
        return self.call_ollama(prompt)

    def get_food_recipe(self, food:str):
        """선택한 요리의 레시피 설명 제공"""
        user_ingredients = self.get_user_ingredients()
        prompt = self.generate_recipe_prompt(user_ingredients, "recipe")
        return self.call_ollama(prompt)