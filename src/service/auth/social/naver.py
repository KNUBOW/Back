import secrets
import httpx

from datetime import datetime
from fastapi import HTTPException

from core.connection import RedisClient
from core.config import Settings
from database.repository.user_repository import UserRepository
from database.orm import User
from service.user_service import UserService

class NaverAuthService:
    CLIENT_ID = Settings.NAVER_CLIENT_ID
    CLIENT_SECRET = Settings.NAVER_CLIENT_SECRET
    REDIRECT_URI = Settings.NAVER_REDIRECT_URI

    def __init__(self, user_service: UserService, user_repo: UserRepository):
        self.user_service = user_service
        self.user_repo = user_repo

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

    async def validate_state(self, state: str):
        redis = await RedisClient.get_redis()
        saved_state = await redis.get(f"naver_state:{state}")
        if not saved_state:
            raise HTTPException(status_code=400, detail="state 불일치")
        await redis.delete(f"naver_state:{state}")

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
                raise HTTPException(status_code=response.status_code, detail="네이버 토큰 요청 실패")

            token_data = response.json()
            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="access_token 누락")

            return token_data

    async def get_user_info(self, access_token: str):
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="사용자 정보 요청 실패")

            data = response.json()
            if "response" not in data:
                raise HTTPException(status_code=400, detail="사용자 정보 누락")

            return data["response"]

    async def handle_naver_callback(self, code: str, state: str):
        await self.validate_state(state)
        token_data = await self.get_token(code, state)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="토큰 누락")

        user_info = await self.get_user_info(access_token)
        return await self.handle_login_or_signup(user_info)

    async def handle_login_or_signup(self, user_info: dict):
        email = user_info.get("email")
        name = user_info.get("name")
        nickname = user_info.get("id")
        gender = user_info.get("gender")
        birthday = user_info.get("birthday")
        birthyear = user_info.get("birthyear")

        if not all([email, name, nickname, gender, birthday, birthyear]):
            raise HTTPException(status_code=400, detail="필수 정보 누락")

        try:
            birthday = "-".join(part.zfill(2) for part in birthday.split("-"))
            birth = f"{birthyear}-{birthday}"
            birth_date = datetime.strptime(birth, "%Y-%m-%d").date()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"생년월일 오류: {str(e)}")

        user = await self.user_repo.get_user_by_email(email=email)

        if user:
            token = self.user_service.create_jwt(email=user.email)
            return f"http://프론트엔드서버/auth/success?token={token}"

        # 유저가 없으면 회원가입 진행
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
            raise HTTPException(status_code=500, detail=f"회원가입 오류: {str(e)}")
