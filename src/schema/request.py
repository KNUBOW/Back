# 테이블에 컬럼별 Request 양식
# pydantic에서 이메일 형식을 사용하려면 pip install email-validator 설치해야함.
from pydantic import BaseModel, EmailStr, constr, field_validator
from datetime import date
from typing import Literal, Optional, List


class SignUpRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=255)  # 최소 8자, 최대 255자
    name: constr(min_length=2, max_length=20)  # 최소 2자, 최대 20자
    nickname: constr(min_length=2, max_length=20)  # 최소 2자, 최대 20자
    birth: date
    gender: Literal["M", "F"]



class LogInRequest(BaseModel):
    email: EmailStr
    password: str

class IngredientRequest(BaseModel):
    name: str
    expiration_date: Optional[date] = None  #유통기한 관련 expiration_date의 속성이 사라져도 허용하는 코드

    @field_validator("expiration_date", mode="before")  #유통기한 관련 ""도 허용하는 코드
    @classmethod
    def validate_expiration_date(cls, v):
        if v == "":  # 빈 문자열이면 None으로 변환
            return None
        return v

class CookingRequest(BaseModel):
    food: str
    use_ingredients: List[str]