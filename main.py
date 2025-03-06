from fastapi import FastAPI
from api import user, ingredient, cookai
from core.config import Settings
from middlewares.session import RedisSessionMiddleware

app = FastAPI()

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

