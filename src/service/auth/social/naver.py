import secrets
import httpx

from datetime import datetime
from fastapi import Request

from core.connection import RedisClient
from core.config import settings
from core.logging import security_log
from database.repository.user_repository import UserRepository
from database.orm import User
from service.user_service import UserService

from exception.social_exception import (
    InvalidStateException,
    SocialTokenException,
    SocialUserInfoException,
    MissingSocialDataException,
    SocialSignupException,
)

# 네이버 소셜 로그인 관련 서비스

class NaverAuthService:
    CLIENT_ID = settings.NAVER_CLIENT_ID
    CLIENT_SECRET = settings.NAVER_CLIENT_SECRET.get_secret_value()
    REDIRECT_URI = settings.NAVER_REDIRECT_URI

    def __init__(self, user_service: UserService, user_repo: UserRepository):
        self.user_service = user_service
        self.user_repo = user_repo

    # url 제공
    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        redis = await RedisClient.get_redis()
        await redis.setex(f"naver_state:{state}", 300, "valid")

        return (
            "https://nid.naver.com/oauth2.0/authorize"
            "?response_type=code"
            f"&client_id={self.CLIENT_ID}"
            f"&redirect_uri={self.REDIRECT_URI}"
            f"&state={state}"
        )

    # state 확인
    async def validate_state(self, state: str, req: Request):
        redis = await RedisClient.get_redis()
        saved_state = await redis.get(f"naver_state:{state}")
        if not saved_state:
            security_log(
                event="Invalid State",
                detail=f"소셜 로그인 state 불일치 (state={state})",
                ip=req.client.host
            )
            raise InvalidStateException()
        await redis.delete(f"naver_state:{state}")

    # 사용자 코드 -> 토큰으로 받음
    async def get_token(self, code: str, state: str):
        token_url = "https://nid.naver.com/oauth2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": "authorization_code",
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "code": code,
            "state": state,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, data=params)
            if response.status_code != 200:
                raise SocialTokenException(detail=f"토큰 요청 실패: {response.status_code}")

            token_data = response.json()
            if "access_token" not in token_data:
                raise SocialTokenException(detail="access_token 누락됨")

            return token_data

    # 유저 정보 요청
    async def get_user_info(self, access_token: str):
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException(detail=f"사용자 정보 요청 실패: {response.status_code}")

            data = response.json()
            if "response" not in data:
                raise SocialUserInfoException(detail="사용자 정보 누락")

            return data["response"]

    # code와 state 기반으로 유저 토큰 받고 사용자 정보를 가져옴
    async def handle_naver_callback(self, code: str, state: str, req: Request):
        if not code or not state:
            raise SocialTokenException(detail="code 또는 state 파라미터 누락됨")

        await self.validate_state(state, req)
        token_data = await self.get_token(code, state)

        access_token = token_data.get("access_token")
        if not access_token:
            raise SocialTokenException(detail="access_token 누락됨")

        user_info = await self.get_user_info(access_token)
        return await self.handle_login_or_signup(user_info)

    # 사용자 정보 받은것을 기반으로 로그인 또는 회원가입함
    async def handle_login_or_signup(self, user_info: dict):
        email = user_info.get("email")
        name = user_info.get("name")
        nickname = user_info.get("id")
        gender = user_info.get("gender")
        birthday = user_info.get("birthday")
        birthyear = user_info.get("birthyear")

        if not all([email, name, nickname, gender, birthday, birthyear]):
            raise MissingSocialDataException()

        # 생년월일 양식에 맞게 포매팅
        try:
            birthday = "-".join(part.zfill(2) for part in birthday.split("-"))
            birth = f"{birthyear}-{birthday}"
            birth_date = datetime.strptime(birth, "%Y-%m-%d").date()
        except Exception as e:
            raise SocialUserInfoException(detail=f"생년월일 처리 실패: {str(e)}")

        user = await self.user_repo.get_user_by_email(email=email)

        if user:
            token = self.user_service.create_jwt(email=user.email)
            return f"http://프론트엔드서버/auth/success?token={token}"

        # 유저정보가 없으면 회원가입 진행
        try:
            password = secrets.token_urlsafe(12)
            hashed_password = self.user_service.hash_password(password)
            new_user = User(
                email=email,
                password=hashed_password,
                name=name,
                nickname=f"naver_{nickname}",
                birth=birth_date,
                gender=gender,
                social_auth="N",
            )
            await self.user_repo.save_user(new_user)

            token = self.user_service.create_jwt(email=email)
            return f"http://프론트엔드서버/auth/success?token={token}"
        except Exception as e:
            raise SocialSignupException(detail=f"회원가입 오류: {str(e)}")
