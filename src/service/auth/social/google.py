import os
import secrets
import httpx

from fastapi import HTTPException, Request
from urllib.parse import urlencode

from core.connection import RedisClient
from database.orm import User
from core.logging import security_log
from database.repository.user_repository import UserRepository
from exception.social_exception import InvalidStateException, SocialTokenException, SocialSignupException, \
    MissingSocialDataException, SocialUserInfoException
from service.user_service import UserService


class GoogleAuthService:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, user_service: UserService, user_repo: UserRepository):
        self.user_service = user_service
        self.user_repo = user_repo

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

    async def exchange_code_for_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(self.GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            })
            if response.status_code != 200:
                raise SocialTokenException(detail="access_token 요청 실패")
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(self.GOOGLE_USERINFO_URL, headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException(detail=f"사용자 정보 요청 실패: {response.status_code}")
            return response.json()

    async def handle_google_callback(self, code: str, state: str, req: Request) -> str:
        await self.validate_state(state, req)
        token_data = await self.exchange_code_for_token(code)

        access_token = token_data.get("access_token")
        if not access_token:
            raise SocialTokenException(detail="access_token 누락됨")

        user_info = await self.get_user_info(access_token)
        return await self.handle_login_or_signup(user_info)

    async def handle_login_or_signup(self, user_info: dict) -> str:
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("id")
        picture = user_info.get("picture")

        if not all([email, name, google_id]):
            raise MissingSocialDataException()

        user = await self.user_repo.get_user_by_email(email=email)

        if user:
            token = self.user_service.create_jwt(email=user.email)
            return f"http://프론트엔드서버/auth/success?token={token}"

        try:
            password = secrets.token_urlsafe(12)
            hashed_password = self.user_service.hash_password(password)
            new_user = User(
                email=email,
                password=hashed_password,
                name=name,
                nickname=f"google_{google_id}",
                social_auth="G",
            )
            await self.user_repo.save_user(new_user)

            token = self.user_service.create_jwt(email=email)
            return f"http://프론트엔드서버/auth/success?token={token}"
        except Exception as e:
            raise SocialSignupException(detail=f"회원가입 오류: {str(e)}")