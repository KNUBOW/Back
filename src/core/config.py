#민감한 정보 보호
import secrets
import os
from dotenv import load_dotenv


load_dotenv(verbose=True)

class Settings:

    #service user.py
    encoding: str = os.getenv("ENCODING")
    secret_key: str = os.getenv("SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM")

    #service cookai.py
    ollama_url: str = os.getenv("OLLAMA_URL")
    model_name: str = os.getenv("MODEL_NAME")
    num_predict: int = os.getenv("NUM_PREDICT")

    #core connection.py
    DATABASE_URL = os.getenv("DATABASE_URL")

    #api user.py
    KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
    KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")

    #main.py
    SESSION_MIDDLEWARE_SECRET_KEY = os.getenv("SESSION_MIDDLEWARE_SECRET_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_DB = int(os.getenv("REDIS_DB", 0))