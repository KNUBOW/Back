from pydantic_settings import BaseSettings
from pydantic import SecretStr
from typing import Literal


class Settings(BaseSettings):
    # user_service.py
    SECRET_KEY: SecretStr
    JWT_ALGORITHM: str

    KAKAO_CLIENT_ID: str
    KAKAO_REDIRECT_URI: str

    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: SecretStr
    NAVER_REDIRECT_URI: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: SecretStr
    GOOGLE_REDIRECT_URI: str

    # recipe.py
    OLLAMA_URL: str
    MODEL_NAME: str

    # connection.py
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    POSTGRES_DATABASE_URL: str

    # main.py
    SESSION_MIDDLEWARE_SECRET_KEY: SecretStr

    # 공통
    ENV: Literal["dev", "prod", "test"] = "dev"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # ✅ 유효성 체크 여기서 자동 수행됨
