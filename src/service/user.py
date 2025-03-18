import secrets
import httpx
import aioredis

import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from core.config import Settings
from fastapi import HTTPException


async def get_redis():  #네이버에서 세션 관리하기 위해 설정
    return await aioredis.from_url(f"redis://{Settings.REDIS_HOST}:{Settings.REDIS_PORT}")



class UserService:

    encoding = Settings.encoding
    secret_key = Settings.secret_key
    jwt_algorithm = Settings.jwt_algorithm

    def hash_password(self, plain_password: str) -> str:    #암호 해싱
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt=bcrypt.gensalt(),
        )
        return hashed_password.decode(self.encoding)

    def verify_password(self, plain_password: str, hashed_password: str #암호 검증
    ) -> bool:
        # try / except
        return bcrypt.checkpw(
            plain_password.encode(self.encoding),
            hashed_password.encode(self.encoding)
        )

    def create_jwt(self, email: str) -> str:    #jwt 암호화 값
        return jwt.encode(
            {
                "sub": email,    # unique id
                "exp": datetime.now() + timedelta(days=1),  #토큰 유효기간 1일
            },
            self.secret_key,
            algorithm=self.jwt_algorithm,
        )

    def decode_jwt(self, access_token: str):    #jwt 복호화 값
        try:
            payload: dict = jwt.decode(
                access_token, self.secret_key, algorithms=[self.jwt_algorithm]
            )
            email = payload.get("sub")

            if email is None:
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
            return email

        except JWTError as e:
            raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰")


class NaverAuthService:
    CLIENT_ID = Settings.NAVER_CLIENT_ID
    CLIENT_SECRET = Settings.NAVER_CLIENT_SECRET
    REDIRECT_URI = Settings.NAVER_REDIRECT_URI

    @staticmethod
    async def get_auth_url():
        """네이버 로그인 URL 생성 (OAuth 2.0 state 포함)"""
        state = secrets.token_urlsafe(16)

        # Redis에 state 저장
        redis = await get_redis()
        await redis.setex(f"naver_state:{state}", 300, "valid")  # 5분 동안 유지

        return (
            "https://nid.naver.com/oauth2.0/authorize"
            "?response_type=code"
            f"&client_id={NaverAuthService.CLIENT_ID}"
            f"&redirect_uri={NaverAuthService.REDIRECT_URI}"
            f"&state={state}"
        )

    @staticmethod
    async def get_token(code: str, state: str):
        """네이버 OAuth 토큰 요청"""
        token_url = "https://nid.naver.com/oauth2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "grant_type": "authorization_code",
            "client_id": NaverAuthService.CLIENT_ID,
            "client_secret": NaverAuthService.CLIENT_SECRET,
            "code": code,
            "state": state,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, data=params)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="네이버 토큰 요청 실패")

            token_data = response.json()
            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="네이버에서 access_token을 받지 못함.")

            return token_data

    @staticmethod
    async def get_user_info(access_token: str):
        """네이버 사용자 정보 요청"""
        user_info_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="네이버 사용자 정보 요청 실패")

            user_data = response.json()
            if "response" not in user_data:
                raise HTTPException(status_code=400, detail="네이버에 사용자 정보 X.")

            return user_data["response"]