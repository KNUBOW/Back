from datetime import date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

#기능 성공 후 출력 메세지

class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    nickname: str


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


class BulkCreateResponseSchema(BaseModel):
    message: str
    created: List[IngredientSchema]
    skipped_duplicates: List[str]