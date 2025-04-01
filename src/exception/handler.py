#전역 예외 처리
'''
예외처리 할 리스트
1) 로그인 안했을 때
2) AI관련 JSON 에러 발생
3) AI가 값을 제대로 반환 안할때
4) 데이터베이스 관련 에러 발생 (데이터베이스 제약 조건 위반, 데이터베이스 연결 실패 등)
5) Docker 관련 에러 발생
6) 404 Not Found
7) 소셜 로그인 측 에러 발생(네이버, 카카오, 구글) -> state 불일치 또는 원하는 정보 출력X, 등
8) 이메일, 닉네임 중복
9) 이메일이 틀렸거나 비밀번호가 틀렸을 때
10) 유효하지 않은 토큰 또는 만료될 때
'''
from fastapi import Request
from starlette.responses import JSONResponse

class CustomException(Exception):
    def __init__(self, name: str, status_code: int = 400, detail: str = "커스텀 오류 발생"):
        self.name = name
        self.status_code = status_code
        self.detail = detail

async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.name, "detail": exc.detail}
    )