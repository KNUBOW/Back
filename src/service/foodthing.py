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
            당신은 전문 요리사 AI입니다.  
            사용자가 보유한 재료를 최대한 활용하여 만들 수 있는 **요리 6가지**를 추천해주세요.  
            아래 조건을 반드시 지켜주세요.  

            📌 **사용 가능한 재료 목록:** {json.dumps(user_ingredients, ensure_ascii=False)}  

            ---

            🔹 **반드시 사용자가 가진 재료만 사용해주세요.**  
            🔹 **추가 재료는 절대 포함하지 마세요.**  
            🔹 **모든 요리는 현실적으로 만들 수 있는 것만 포함해주세요.**  
            🔹 **응답 예시는 아래 JSON 형식과 동일해야 합니다.**  
            🔹 **모든 값(value)은 한국어로만 답해주세요.**  

            ---

            ### ✅ **출력 예시**
            ```json
            {{
              "recipes": [
                {{
                  "food": "계란 볶음밥",
                  "use_ingredients": [
                    "밥",
                    "계란",
                    "대파",
                    "소금",
                    "후춧가루"
                  ]
                }},
                {{
                  "food": "김치찌개",
                  "use_ingredients": [
                    "김치",
                    "두부",
                    "대파",
                    "소금",
                    "후춧가루"
                  ]
                }},
                {{
                  "food": "치즈 계란",
                  "use_ingredients": [
                    "치즈",
                    "계란",
                    "대파",
                    "소금"
                  ]
                }}
              ]
            }}
            ```
            """

        elif prompt_type == "recipe":
            user_ingredients = user_ingredients or []  # None 방지
            ingredients_json = json.dumps(user_ingredients, ensure_ascii=False)

            return f"""
            {base_prompt}
            당신은 전문 요리사 AI입니다.  
            사용자가 요청한 음식의 **상세 조리법**을 제공합니다.  
            반드시 아래 조건을 따르세요.  
            
            📌 **요청된 음식:** "{food}"  
            📌 **사용 가능한 재료:** {ingredients_json}  
            
            ---
            
            🔹 **반드시 요청된 음식과 제공된 재료를 사용하여 레시피를 작성하세요.**  
            🔹 **추가 재료는 절대 포함하지 마세요.**  
            🔹 **사용된 재료의 양을 상세히 명시하세요. (예: 100g, 1컵, 2스푼 등 / 1~2인분 기준)**  
            🔹 **레시피는 최소 450자 이상, 단계별로 상세한 조리 방법을 포함해야 합니다.**  
            🔹 **조리 과정은 이해하기 쉽도록 순서대로 작성하세요.**  
            🔹 **추가로 도움이 될 만한 팁이 있다면 포함하세요.**  
            🔹 **반드시 아래 JSON 형식으로만 응답하세요.**  
            
            ---
            
            ### ✅ **출력 예시 (정상적인 응답)**
            ```json
            {{
              "food": "{food}",
              "use_ingredients": [
                {{"name": "계란", "amount": "2개"}},
                {{"name": "양파", "amount": "50g"}},
                {{"name": "치즈", "amount": "30g"}},
                {{"name": "우유", "amount": "50ml"}}
              ],
              "steps": [
                "양파를 잘게 썰어 준비합니다.",
                "볼에 계란 2개를 깨서 넣고, 우유 50ml와 치즈 30g을 함께 섞어줍니다.",
                "팬을 중불로 달군 후, 약간의 기름을 두르고 양파를 볶습니다.",
                "양파가 투명해지면 계란 혼합물을 팬에 부어 중약불에서 천천히 익힙니다.",
                "계란이 반쯤 익으면 오믈렛을 반으로 접고, 치즈가 녹을 때까지 약불에서 1~2분 더 익힙니다.",
                "완성된 오믈렛을 접시에 담아 맛있게 즐깁니다."
              ],
              "tip": "계란을 부드럽게 만들려면 약한 불에서 천천히 익히고, 우유를 추가하면 더욱 촉촉한 식감을 얻을 수 있습니다."
            }}

            """


        elif prompt_type == "quick":

            return f"""
            {base_prompt}  
            당신은 요리 전문가 AI입니다.  
            사용자가 제공한 **재료만** 활용하여 만들 수 있는 **요리 1가지**를 추천하세요.  
            **아래 조건을 철저히 준수하세요.**  
            
            📌 **사용자 입력:**  
            "{chat}"  
            
            ---
            
            🔹 **입력된 재료만 사용하고, 추가 재료는 절대 포함하지 마세요.**  
            🔹 **모든 재료를 반드시 사용할 필요는 없으며, 핵심 재료만 선택하세요.**  
            🔹 **각 재료의 사용량을 정확히 명시하세요. (예: 100g, 1컵, 2스푼 등 / 1~2인분 기준)**  
            🔹 **조리 과정은 최소 300자 이상, 단계별로 상세히 설명하세요.**  
            🔹 **가능하면 추가적인 요리 팁을 포함하세요.**  
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **사용자가 식재료와 무관한 내용을 입력하면, 아래 형식으로 응답하세요.**  
            
            ```json
            {{
              "error": "정확한 음식명을 입력해 주세요."
            }}
            
            ---
            
            ### ✅ **출력 예시 (정상적인 응답)**
            ```json
            {{
              "food": "치즈 오믈렛",
              "use_ingredients": [
                {{"name": "계란", "amount": "2개"}},
                {{"name": "치즈", "amount": "30g"}},
                {{"name": "우유", "amount": "50ml"}}
              ],
              "steps": [
                "볼에 계란 2개를 깨서 넣고 잘 풀어줍니다.",
                "우유 50ml와 치즈 30g을 추가한 후 잘 섞습니다.",
                "팬에 약간의 기름을 두르고 중약불에서 계란 혼합물을 천천히 익힙니다.",
                "계란이 반쯤 익으면 반으로 접어 완성합니다."
              ],
              "tip": "계란을 부드럽게 만들려면 약한 불에서 천천히 익히세요."
            }}
            
            """

        elif prompt_type == "search":

            return f"""
            {base_prompt}  
            당신은 요리 전문가 AI입니다.  
            사용자가 입력한 **음식명**에 대한 **정확한 레시피**를 제공합니다.  
            아래 조건을 철저히 준수하세요.  
            
            📌 **사용자 입력 (요리명):**  
            "{chat}"  
            
            ---
            
            🔹 **반드시 요청된 음식의 레시피만 제공하세요.**  
            🔹 **추가적인 음식 추천이나 불필요한 설명을 포함하지 마세요.**  
            🔹 **각 재료의 사용량을 명확히 표기하세요. (예: 100g, 1컵, 2스푼 등 / 1~2인분 기준)**  
            🔹 **조리 과정은 최소 300자 이상, 단계별로 상세히 설명하세요.**  
            🔹 **가능하면 추가적인 요리 팁을 포함하세요.**  
            🔹 **반드시 JSON 형식으로만 응답하세요.**  
            🔹 **사용자가 식재료와 무관한 내용을 입력하면, 아래 형식으로 응답하세요.**  
            
            ```json
            {{
              "error": "정확한 음식명을 입력해 주세요."
            }}
            
            ---
            
            ### ✅ **출력 예시 (정상적인 응답)**
            ```json
            {{
              "food": "된장찌개",
              "use_ingredients": [
                {{"name": "된장", "amount": "2스푼"}},
                {{"name": "두부", "amount": "1/2모"}},
                {{"name": "대파", "amount": "반개"}},
                {{"name": "멸치 육수", "amount": "500ml"}}
              ],
              "steps": [
                "냄비에 멸치 육수 500ml를 넣고 끓입니다.",
                "된장 2스푼을 풀어 넣고 잘 저어줍니다.",
                "두부 1/2모를 깍둑 썰어 넣고 5분간 끓입니다.",
                "마지막으로 대파 10g을 썰어 넣고 2분 더 끓여 완성합니다."
              ],
              "tip": "감칠맛을 높이려면 육수에 마늘을 다져 넣어보세요."
            }}

                
            """

        else:
            raise ValueError("프롬프트 타입 Error.")

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

    def get_search_recipe(self, chat: str):
        """빠른 요리 추천 - 사용자가 입력한 재료만 활용"""
        prompt = self.get_prompt("search", chat=chat)
        return self.call_ollama(prompt)