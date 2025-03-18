#유저 관리
import aioredis

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from schema.request import SignUpRequest, LogInRequest
from database.orm import User
from service.user import UserService, NaverAuthService
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
        # 컨테이너 또는 데이터베이스 관련 에러 발생
        raise HTTPException(status_code=500, detail="컨테이너 또는 데이터베이스 관련 오류 발생(docker, mysql 등 확인)")


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

#-------------------------- 네이버 회원가입 / 로그인 --------------------------
@router.get("/naver")
async def naver_login():
    auth_url = await NaverAuthService.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})  # Redirect에서 JSON으로 해야함. Front에서 정상적으로 전달안됨.

@router.get("/naver/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    await NaverAuthService.validate_state(state)

    # 네이버에서 액세스 토큰 요청
    token_response = await NaverAuthService.get_token(code, state)
    access_token = token_response.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="토큰 발급 실패")

    # 액세스 토큰으로 사용자 정보 요청
    user_info = await NaverAuthService.get_user_info(access_token)

    return user_info

#------------------------------------------------------------------------