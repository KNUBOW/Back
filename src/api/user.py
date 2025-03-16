#유저 관리
import aioredis
import httpx
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from schema.request import SignUpRequest, LogInRequest
from database.orm import User
from service.user import UserService
from schema.response import UserSchema, JWTResponse
from database.repository import UserRepository
from sqlalchemy.exc import OperationalError
from core.config import Settings

NAVER_CLIENT_ID = Settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = Settings.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = Settings.NAVER_REDIRECT_URI


router = APIRouter(prefix="/users")

async def get_redis():
    return await aioredis.from_url(f"redis://{Settings.REDIS_HOST}:{Settings.REDIS_PORT}")

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

#-------------------------- 네이버 회원가입 / 로그인 --------------------------

async def get_naver_auth_url(request: Request):
    state = secrets.token_urlsafe(16)

    # Redis에 state 저장
    redis = await get_redis()
    await redis.setex(f"naver_state:{state}", 600, "valid")  # 10분 동안 유지

    print(f"🟢 생성된 state: {state}")

    return (
        "https://nid.naver.com/oauth2.0/authorize"
        "?response_type=code"
        f"&client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        f"&state={state}"
    )

# 네이버 토큰 요청
async def get_naver_token(code: str, state: str):
    token_url = "https://nid.naver.com/oauth2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "code": code,
        "state": state,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=params)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="네이버 토큰 요청 실패")

        token_data = response.json()
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="네이버에서 access_token을 받지 못했습니다.")

        return token_data

# 네이버 사용자 정보 요청
async def get_naver_user_info(access_token: str):
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="네이버 사용자 정보 요청 실패")

        user_data = response.json()
        if "response" not in user_data:
            raise HTTPException(status_code=400, detail="네이버 사용자 정보가 없습니다.")

        return user_data["response"]

@router.get("/naver")
async def naver_login(request: Request):
    auth_url = await get_naver_auth_url(request)
    return JSONResponse(content={"auth_url": auth_url})  # ✅ JSON으로 반환

@router.get("/naver/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    redis = await get_redis()
    saved_state = await redis.get(f"naver_state:{state}")

    if not saved_state:
        raise HTTPException(status_code=400, detail="state 불일치")

    # ✅ 사용한 state 값 Redis에서 삭제
    await redis.delete(f"naver_state:{state}")

    # 네이버에서 액세스 토큰 요청
    token_response = await get_naver_token(code, state)
    access_token = token_response.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="토큰 발급 실패")

    # 액세스 토큰으로 사용자 정보 요청
    user_info = await get_naver_user_info(access_token)

    return user_info

#------------------------------------------------------------------------