import secrets
import httpx

from fastapi import Request
from urllib.parse import urlencode

from core.config import settings
from core.connection import RedisClient
from database.orm import User
from core.logging import security_log
from database.repository.user_repository import UserRepository
from service.user_service import UserService
from exception.social_exception import (
    InvalidStateException,
    SocialTokenException,
    SocialSignupException,
    MissingSocialDataException,
    SocialUserInfoException
)

# 구글 소셜 로그인 관련 서비스

class GoogleAuthService:
    GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET.get_secret_value()
    GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, user_service: UserService, user_repo: UserRepository):
        self.user_service = user_service
        self.user_repo = user_repo

    # url 제공
    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        redis = await RedisClient.get_redis()
        await redis.setex(f"google_state:{state}", 300, "valid")

        query = urlencode({
            "client_id": self.GOOGLE_CLIENT_ID,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "redirect_uri": self.GOOGLE_REDIRECT_URI,
            "access_type": "offline",
            "state": state,
            "prompt": "consent"
        })

        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    # state 확인
    async def validate_state(self, state: str, req: Request):
        redis = await RedisClient.get_redis()
        saved_state = await redis.get(f"google_state:{state}")
        if not saved_state:
            security_log(
                event="Invalid State",
                detail=f"소셜 로그인 state 불일치 (state={state})",
                ip=req.client.host
            )
            raise InvalidStateException()
        await redis.delete(f"google_state:{state}")

    # 사용자 코드 -> 토큰으로 받음
    async def get_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            })
            if response.status_code != 200:
                raise SocialTokenException(detail="access_token 요청 실패")
            return response.json()

    # 유저 정보 요청
    async def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException(detail=f"사용자 정보 요청 실패: {response.status_code}")
            return response.json()

    # code와 state 기반으로 유저 토큰 받고 사용자 정보를 가져옴
    async def handle_google_callback(self, code: str, state: str, req: Request) -> str:
        await self.validate_state(state, req)
        token_data = await self.get_token(code)

        access_token = token_data.get("access_token")
        if not access_token:
            raise SocialTokenException(detail="access_token 누락됨")

        user_info = await self.get_user_info(access_token)
        return await self.handle_login_or_signup(user_info)

    # 사용자 정보 받은것을 기반으로 로그인 또는 회원가입함
    async def handle_login_or_signup(self, user_info: dict) -> str:
        nickname = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")

        if not all([email, name, nickname]):
            raise MissingSocialDataException()

        user = await self.user_repo.get_user_by_email(email=email)

        if user:
            token = self.user_service.create_jwt(email=user.email)
            return f"http://프론트엔드서버/auth/success?token={token}"

        #유저정보가 없으면 회원가입 진행
        try:
            password = secrets.token_urlsafe(12)
            hashed_password = self.user_service.hash_password(password)
            new_user = User(
                email=email,
                password=hashed_password,
                name=name,
                nickname=f"google_{nickname}",
                social_auth="G",
            )
            await self.user_repo.save_user(new_user)

            token = self.user_service.create_jwt(email=email)
            return f"http://프론트엔드서버/auth/success?token={token}"
        except Exception as e:
            raise SocialSignupException(detail=f"회원가입 오류: {str(e)}")