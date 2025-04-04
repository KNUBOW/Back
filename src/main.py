from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager

from api import user, ingredient, recipe
from core.config import settings
from core.connection import AsyncSessionLocal, RedisClient
from core.logging import loggers
from middlewares.access_logging import AccessLogMiddleware
from middlewares.session import RedisSessionMiddleware
from exception.handler import (
    custom_exception_handler,
    CustomException,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

system_logger = loggers["system"]
system_logger.info("서버 시작 전 초기화 중...")

# DB 및 .env 유효성 검사
@asynccontextmanager
async def lifespan(app: FastAPI):
    system_logger.info("FastAPI 애플리케이션 시작 준비 중...")

    try:
        secret_key_value = settings.SECRET_KEY.get_secret_value()
        if len(secret_key_value) != 64:
            raise ValueError("SECRET_KEY는 반드시 64자리여야 합니다.")

    except Exception as e:
        system_logger.error(f".env 설정 오류: {e}", exc_info=True)
        raise RuntimeError("앱 실행 중단 🔴")

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        system_logger.error(f"PostgreSQL 연결 실패: {e}", exc_info=True)
        raise RuntimeError("PostgreSQL 연결 실패 🔴")

    try:
        redis = await RedisClient.get_redis()
        await redis.ping()
    except Exception as e:
        system_logger.error(f"Redis 연결 실패: {e}")
        raise RuntimeError("Redis 연결 실패 🔴")

    system_logger.info("FastAPI 애플리케이션 정상 작동")
    yield


    await RedisClient.close_redis()
    system_logger.info("Redis 연결 종료")
    system_logger.info("FastAPI 애플리케이션 종료")
app = FastAPI(lifespan=lifespan)

# 예외 처리 핸들러 설정
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS 설정
origins = [
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# Redis Session 미들웨어
app.add_middleware(
    RedisSessionMiddleware,
    secret_key=settings.SESSION_MIDDLEWARE_SECRET_KEY.get_secret_value()
)

# 외부에서 접속시 로그 기록
app.add_middleware(AccessLogMiddleware)

# router 리스트
app.include_router(user.router)
app.include_router(ingredient.router)
app.include_router(recipe.router)

@app.get("/")
def hello_world():
    return {"Hello":"World!"}