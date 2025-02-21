from fastapi import FastAPI

from api import user, cookai


app = FastAPI()
app.include_router(user.router)

@app.get("/")
def hello_world():
    return {"Hello":"World!"}