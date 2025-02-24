#기능 성공 후 뜰 메세지
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    nickname: str
    birth: date


    model_config = {"from_attributes": True}

class JWTResponse(BaseModel):
    access_token:str

class IngredientSchema(BaseModel):
    id: int
    name: str
    expiration_date: Optional[date] = Field(None)

    model_config = {"from_attributes": True}