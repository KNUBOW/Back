from fastapi import FastAPI

from api import user, ingredient


app = FastAPI()
app.include_router(user.router)
app.include_router(ingredient.router)

@app.get("/")
def hello_world():
    return {"Hello":"World!"}

