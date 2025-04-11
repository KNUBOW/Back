from pydantic import BaseModel, EmailStr, constr, field_validator, Field
from datetime import date
from typing import Literal, Optional, List

# 테이블에 컬럼별 Request 양식
# pydantic에서 이메일 형식을 사용하려면 pip install email-validator 설치해야함.

class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소(아이디), 이메일 형식이어야댐")
    password: constr(min_length=8, max_length=20) = Field(..., description="비밀번호 (8~20자)")
    name: constr(min_length=2, max_length=20) = Field(..., description="이름 (2~20자)")
    nickname: constr(min_length=2, max_length=20) = Field(..., description="닉네임 (2~20자) 소셜만 70자까지임")
    birth: date = Field(..., description="생년월일 (YYYY-MM-DD)")
    gender: Literal["M", "F"] = Field(..., description="성별 (M(남자) 또는 F(여자))")


class LogInRequest(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str


class IngredientRequest(BaseModel): # 단일 추가용
    name: str = Field(..., description="재료명")
    expiration_date: Optional[date] = Field(None, description="유통기한 (선택)")

    @field_validator("expiration_date", mode="before")  #유통기한 관련 ""도 허용하는 코드
    @classmethod
    def validate_expiration_date(cls, v):
        if v == "":  # 빈 문자열이면 None으로 변환
            return None
        return v


class CookingRequest(BaseModel):
    food: str = Field(..., description="요리 이름")
    use_ingredients: List[str] = Field(..., description="사용할 재료 리스트")


class IngredientCategoriesRequest(BaseModel):
    name: str = Field(..., description="식재료 이름", max_length=50)
    parent_category: Optional[str] = Field(None, description="부모 카테고리", max_length=50)
    child_category: Optional[str] = Field(None, description="자식 카테고리", max_length=50)
    default_expiration_days: int = Field(..., ge=1, description="기본 유통기한 (일 단위)")