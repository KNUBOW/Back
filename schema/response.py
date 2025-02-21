#기능 성공 후 뜰 메세지
from datetime import date

from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    nickname: str
    birth: date


    model_config = {"from_attributes": True}

class JWTResponse(BaseModel):
    access_token:str