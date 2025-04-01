#민감한 정보 보호
import os

from dotenv import load_dotenv


load_dotenv(verbose=True)

class Settings:

    #service user_service.py
    encoding: str = os.getenv("ENCODING")
    secret_key: str = os.getenv("SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM")
    KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
    KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    #service recipe.py
    ollama_url: str = os.getenv("OLLAMA_URL")
    model_name: str = os.getenv("MODEL_NAME")

    #core connection.py
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

    #main.py
    SESSION_MIDDLEWARE_SECRET_KEY = os.getenv("SESSION_MIDDLEWARE_SECRET_KEY")
