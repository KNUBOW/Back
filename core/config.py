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