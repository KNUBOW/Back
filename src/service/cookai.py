import requests
import json
from core.config import Settings
from database.repository import UserRepository
from service.user import UserService
from typing import List

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

    def generate_recipe_prompt(self, user_ingredients, prompt_type="suggestion", food_name=None):
        """요청 타입에 따라 프롬프트를 생성하는 메서드"""

        if prompt_type == "suggestion":
            prompt_detail = f"""
            당신은 숙련된 요리 레시피 전문가입니다.  
            사용자의 보유 식재료를 활용하여 만들 수 있는 요리를 **6가지** 추천해주세요.  
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **추가 설명 없이 JSON 데이터만 반환하세요.**  
            🔹 **각 요리는 `food`와 `use_ingredients` 필드를 포함해야 합니다.**  

            ---
            ### 🥦 사용자가 보유한 식재료 목록
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
                }}
              ]
            }}
            ```
            """

        elif prompt_type == "recipe" and food_name:
            prompt_detail = f"""
            당신은 요리 전문가이며, 사용자가 선택한 요리의 **초보자도 보고 따라할 수 있을 정도로 자세한 레시피**를 제공합니다.  
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **사용자가 선택한 요리의 `food`, `use_ingredients`, `steps` 필드를 포함해야 합니다.**  
            🔹 **입력된 식재료만 활용하여 요리를 구성하세요.**  
            🔹 **추가 설명 없이 JSON 데이터만 반환하세요.**  

            ---
            ### 🍽️ 사용자가 선택한 요리
            **요리명:** {food_name}  
            **사용할 재료:** {json.dumps(user_ingredients, ensure_ascii=False)}

            ---
            ### 📌 JSON 응답 예시
            ```json
            {{
              "recipe": {{
                "food": "{food_name}",
                "use_ingredients": {json.dumps(user_ingredients, ensure_ascii=False)},
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

        elif prompt_type == "quick":
            prompt_detail = f"""
            당신은 사용자의 냉장고 속 재료를 기반으로 맞춤형 레시피를 추천하는 AI입니다.  
            이 서비스는 사용자가 직접 데이터베이스에 재료를 입력하는 번거로움을 없애기 위해 만들어졌습니다.  
            따라서 사용자가 입력하는 재료 목록만을 참고하여, 가능한 레시피를 제안해야 합니다.  
            
            ### 🔹 역할과 목표  
            - 사용자가 입력한 **재료 목록**만을 기반으로 요리를 추천합니다.  
            - **간단하고 빠르게** 만들 수 있는 레시피를 제공합니다.  
            - 추가적인 질문 없이 한 번의 응답으로 **완성된 레시피**를 제공합니다.  
            
            ### 🔹 프롬프트 예시  
            사용자가 다음과 같이 입력합니다:  
            계란, 김치, 라면 스프, 파 있어. 뭐 만들어 먹으면 좋을까?
            
            당신은 이에 대해 다음과 같이 답변해야 합니다:  
            [김치 계란 볶음밥] 🍳🔥
            추가 필요 재료: 밥 한 공기, 간장 (선택)
            조리 방법:
            팬에 기름을 두르고 계란을 스크램블합니다.
            김치를 잘게 썰어 넣고 함께 볶습니다.
            라면 스프를 살짝 넣어 감칠맛을 더합니다.
            밥을 넣고 잘 섞은 후 파를 넣고 마무리합니다.
            
            ### 🔹 추가 조건  
            - 만약 사용자가 매우 적은 재료만 입력한다면, 최소한의 추가 재료로 만들 수 있는 요리를 추천해야 합니다.  
            - 너무 복잡한 레시피는 제공하지 말고, 가능한 **간단한 요리** 위주로 추천하세요.
            - 그 외의 요리와 관련된 질문이 아니라면, 재료 목록을 입력해달라고 하세요.
            """


        else:
            raise ValueError("Invalid prompt_type. Use 'suggestion' or 'recipe'.")

        return prompt_detail.strip()

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

    def get_food_recipe(self, food:str, use_ingredients:list):
        """선택한 요리의 레시피 설명 제공"""
        user_ingredients = self.get_user_ingredients()
        prompt = self.generate_recipe_prompt(user_ingredients, "recipe")
        return self.call_ollama(prompt)

    def get_quick_recipe(self, chat):
        """선택한 요리의 레시피 설명 제공"""
        prompt = self.generate_recipe_prompt("quick")
        return self.call_ollama(prompt)