import requests
import json
from core.config import Settings
from database.repository import UserRepository
from service.user import UserService

class CookAIService:
    def __init__(self, user_service: UserService, user_repo: UserRepository, access_token: str):
        self.ollama_url = Settings.ollama_url
        self.model_name = Settings.model_name
        self.num_predict = 1500  # 최대 토큰 수 지정
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token

    def get_user_ingredients(self): #현재 로그인한 사용자의 식재료 목록을 조회
        email = self.user_service.decode_jwt(access_token=self.access_token)
        user = self.user_repo.get_user_by_email(email=email)
        if not user:
            raise Exception("User Not Found")
        return [ingredient.name for ingredient in user.ingredients]

    def get_suggest_recipes(self):    #사용자가 만들 수 있는 요리 리스트들을 추천하고 저장함.
        user_ingredients = self.get_user_ingredients()  # 사용자의 식재료 가져오기

        prompt = (
            "당신은 요리 레시피 전문가입니다. "
            "사용자가 제공한 식재료 목록을 기반으로 만들 수 있는 요리와, "
            "일부 재료를 추가하면 만들 수 있는 요리를 총 10개 추천해주세요."
            "최대한 식재료 목록을 기반으로 만들 수 있는게 많을수록 좋으며 도저히 만들기 힘들다고 가정할 떄, 일부 재료 추가를 추천해주세요. "
            "응답은 반드시 JSON 형식으로 작성해야 합니다.\n\n"

            "## 요구사항\n"
            "- '현재 가지고 있는 재료만으로 만들 수 있는 요리'와 "
            "'추가 재료가 필요한 요리'를 구분해서 제공하세요.\n"
            "- 추가 재료가 필요한 경우, 부족한 재료 목록도 함께 포함하세요.\n"
            "- JSON 형식으로 응답해야 하며, 아래의 예제 형식을 따르세요.\n\n"

            f"### 입력된 사용자의 식재료: {json.dumps(user_ingredients, ensure_ascii=False)}\n\n"

            "## 응답 JSON 예시"
            "{"
            '  "recipes": ['
            '    {'
            '      "food": "김치볶음밥"'
            '      "status": "true",'
            '    },'
            '    {'
            '      "food": "토마토파스타",'
            '      "status": "false",'
            '      "missing_ingredients": ["토마토"]'
            '    }'
            '  ]'
            "}"
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": self.num_predict},
        }

        response = requests.post(self.ollama_url, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result["response"]  # 모델이 생성한 텍스트 반환
        else:
            raise Exception(f"❌ Ollama 오류: {response.status_code} - {response.text}")


    def food_recipe(self):    #저장된 요리 리스트들의 레시피를 설명해주고 저장함.
        pass