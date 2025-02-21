#유저 관리
from fastapi import APIRouter, Depends, HTTPException

from schema.request import SignUpRequest
from database.orm import User
from service.user import UserService
from schema.response import UserSchema
from database.repository import UserRepository
from sqlalchemy.exc import OperationalError

router = APIRouter(prefix="/users")

@router.post("/sign-up", status_code=201)
def user_sign_up_handler(
    request: SignUpRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):

    hashed_password: str = user_service.hash_password(
        plain_password=request.password
    )

    user: User = User.create(
        email=request.email,
        hashed_password=hashed_password,
        name=request.name,
        nickname = request.nickname,
        birth=request.birth,
        gender=request.gender,
    )

    user: User = user_repo.save_user(user=user)

    return UserSchema.model_validate(user)