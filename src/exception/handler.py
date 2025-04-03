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
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from exception.base_exception import CustomException
from core.logging import loggers
from exception.external_exception import GlobalException

error_logger = loggers["error"]

async def custom_exception_handler(request: Request, exc: CustomException):
    exc.log(error_logger, request.url.path)  # 각 예외 클래스의 log_level로 자동 기록
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        error_logger.warning(f"[NotFound] {request.url}")
    else:
        error_logger.warning(f"[HTTPException] {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_logger.warning(f"[ValidationError] {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, GlobalException):
        exc.log(error_logger, request.url.path)
        status_code = exc.status_code
        code = exc.code
        detail = exc.detail

    else:
        error_logger.error(f"[Unhandled Exception] {type(exc).__name__}: {str(exc)}")
        status_code = 500
        code = "UNHANDLED_ERROR"
        detail = "예기치 못한 오류가 발생", str(exc)

    return JSONResponse(
        status_code=status_code,
        content={"code": code, "detail": detail}
    )