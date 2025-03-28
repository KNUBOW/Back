#기능 성공 후 출력 메세지
from datetime import date
from typing import Optional, List

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
    user_id: int
    name: str
    expiration_date: Optional[date] = None

    model_config = {"from_attributes": True}

class IngredientListSchema(BaseModel):
    ingredients: List[IngredientSchema]
