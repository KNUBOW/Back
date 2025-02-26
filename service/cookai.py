import requests
import json

from core.config import Settings


class CookAIService:
    ollama_url = Settings.ollama_url
    model_name = Settings.model_name
    num_predict: int = 1500  #최대 토큰 수 지정

    prompt = (f"당신은 AI 셰프입니다. 나는 현재 다음과 같은 식재료를 가지고 있습니다: {user_ingredients}."
              f"저의 성별과 나이는 ~~하며, 좋아할 만한 음식을 추천해줘"
              f"내가 가진 재료만으로 만들 수 있는 요리 목록을 제공해 주세요. "
              f"각 요리에 대해 아래 정보를 포함하여 JSON 형식으로 응답해주세요:\n"
              f"- 요리 이름\n"
              f"- 요약 설명\n"
              f"- 필요 재료 리스트\n"
              f"- 조리법\n"
              f"- 예상 칼로리 정보\n\n"
              f"응답 예시:\n"
              f"{{'recipes': [\n"
              f"    {{'name': '토마토 파스타', 'description': '상큼한 토마토 베이스의 파스타', "
              f"'ingredients': ['토마토', '파스타', '마늘'], 'instructions': '1. ... 2. ...', 'calories': 450}},\n"
              f"    {{'name': '비건 샐러드', 'description': '신선한 채소로 만든 건강한 샐러드', "
              f"'ingredients': ['양상추', '토마토', '오이'], 'instructions': '1. ... 2. ...', 'calories': 200}}\n"
              f"]}}")
    '''
    1) 현재 내가 가지고 있는 재료들을(또는 추가할 건지) 
    2) 사용자의 음식 선호도에 취합하여(비건인지 아닌지, 매운 맛을 좋아하는지 안좋아하는지, 특정 나라의 식문화를 좋아한다던지 ex)양식,한식,중식)
    3) 식단을 하는 중이라면 칼로리에 대한 제한과, 탄단지 비율 설정
    4) 이걸로 만들 수 있는 요리들을 리스트로 알려주고
    5) 요리에 대한 레시피를 종류별로 받음
    '''

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": num_predict}
    }

    response = requests.post(ollama_url, json=payload)

    if response.status_code == 200:
        result = response.json()
        print("🔥 Ollama 응답:")
        print(result["response"])  # 모델이 생성한 텍스트 출력
    else:
        print(f"❌ 오류 발생: {response.status_code}")
        print(response.text)