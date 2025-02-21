# 테이블에 컬럼별 Request 양식
# pydantic에서 이메일 형식을 사용하려면 pip install email-validator 설치해야함.
from pydantic import BaseModel, EmailStr, constr
from datetime import date
from typing import Literal


class SignUpRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=255)  # 최소 8자, 최대 255자
    name: constr(min_length=2, max_length=20)  # 최소 2자, 최대 20자
    nickname: constr(min_length=2, max_length=20)  # 최소 2자, 최대 20자
    birth: date
    gender: Literal["M", "F"]



class LogInRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=255)