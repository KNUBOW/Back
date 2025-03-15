from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import user, ingredient, cookai
from core.config import Settings
from middlewares.session import RedisSessionMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (보안 필요 시 특정 도메인만 허용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


app.add_middleware(
    RedisSessionMiddleware,
    secret_key=Settings.SESSION_MIDDLEWARE_SECRET_KEY
)


app.include_router(user.router)
app.include_router(ingredient.router)
app.include_router(cookai.router)

@app.get("/")
def hello_world():
    return {"Hello":"World!"}