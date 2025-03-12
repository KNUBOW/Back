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
        """요청 타입에 따라 프롬프트를 생성하는 메서드(아직 난이도 기능 없음)"""
        if prompt_type == "suggestion":
            prompt_detail = f"""
            당신은 요리 레시피 전문가입니다.  
            사용자의 식재료를 최대한 활용하여 만들 수 있는 요리를 **6가지** 추천하세요.  

            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **추가 설명 없이 JSON 데이터만 반환하세요.**  

            ---
            ### 🥦 사용자가 보유한 식재료
            {json.dumps(user_ingredients, ensure_ascii=False)}

            ---
            ### 📌 JSON 응답 예시
            ```json
            {{
              "recipes": [
                {{
                  "food": "김치볶음밥",
                  "use_ingredients": ["김치", "밥"]
                }},
                {{
                  "food": "토마토파스타",
                  "use_ingredients": ["토마토", "파스타", "양파"]              
                }},
                ...
              ]
            }}
            ```
            """

        elif prompt_type == "recipe":
            prompt_detail = f"""
            당신은 요리 전문가이며, 사용자가 선택한 요리의 **상세한 레시피**를 제공합니다.  
            아래의 JSON 형식에 맞는 데이터를 제공합니다:
            {{
              "food": "김치볶음밥",
              "use_ingredients": ["김치", "밥", "대파", "달걀", "간장"]
            }}
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **입력된 식재료(use_ingredients)를 최대한 활용한 요리를 생성하세요.**  
            🔹 **조리 시간, 난이도, 필요 도구까지 포함하세요.**  
            🔹 **추가 설명 없이 JSON 데이터만 반환하세요.**  
            ---
            ### 🍽️ 사용자가 선택한 요리
            **사용할 재료:** {json.dumps(user_ingredients, ensure_ascii=False)}
            ---
            ### 📌 JSON 응답 예시
            ```json
            {{
              "recipe": {{
                "food": "김치볶음밥",
                "use_ingredients": ["김치", "밥", "대파", "달걀", "간장"],
                "steps": [
                  "대파를 송송 썰고, 김치는 한 입 크기로 자릅니다.",
                  "프라이팬에 기름을 두르고 중불에서 대파를 볶아 파기름을 냅니다.",
                  "김치를 넣고 2~3분간 볶아 감칠맛을 더합니다.",
                  "밥을 넣고 골고루 섞으며 볶아줍니다.",
                  "간장 1큰술을 팬의 한쪽에 넣고 살짝 태운 후 밥과 섞습니다.",
                  "밥을 한쪽으로 밀어두고 달걀을 풀어 스크램블을 만든 후 밥과 섞습니다.",
                  "기호에 따라 깨를 뿌리고 접시에 담아 완성합니다."
                ]
              }}
            }}
            ```
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