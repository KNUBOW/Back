#유저 관리
from fastapi import APIRouter, Depends, HTTPException

from core.security import get_access_token
from schema.request import SignUpRequest, LogInRequest
from database.orm import User
from service.user import UserService
from schema.response import UserSchema, JWTResponse
from database.repository import UserRepository
from sqlalchemy.exc import OperationalError

router = APIRouter(prefix="/users")

@router.post("/sign-up", status_code=201)
def user_sign_up_handler(
    request: SignUpRequest,
    user_service: UserService = Depends(),
    user_repo: UserRepository = Depends(),
):
    try:
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

    except OperationalError as e:
        # 데이터베이스 관련 에러 발생
        raise HTTPException(status_code=500, detail="데이터베이스 관련 오류 발생(docker, mysql 등 확인)")

@router.post("/log-in")
def user_log_in_handler(
        request: LogInRequest,
        user_service: UserService = Depends(),
        user_repo: UserRepository = Depends(),
):
    user: User | None = user_repo.get_user_by_email(email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당하는 이메일 존재X")

    verified: bool = user_service.verify_password(
        plain_password=request.password,
        hashed_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="인증 실패")

    access_token: str = user_service.create_jwt(email=user.email)

    return JWTResponse(access_token=access_token)
