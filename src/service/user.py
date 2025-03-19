import secrets
import httpx
from core.redis import RedisClient

import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from core.config import Settings
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from database.repository import UserRepository
from database.orm import User
from schema.request import SignUpRequest, LogInRequest
from schema.response import UserSchema, JWTResponse



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

    async def sign_up(self, request: SignUpRequest, user_repo: UserRepository):
        """회원가입 처리"""
        try:
            hashed_password = self.hash_password(request.password)

            user = User.create(
                email=request.email,
                hashed_password=hashed_password,
                name=request.name,
                nickname=request.nickname,
                birth=request.birth,
                gender=request.gender,
            )

            user = user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except OperationalError:
            raise HTTPException(status_code=500, detail="컨테이너 또는 데이터베이스 관련 오류 발생(docker, mysql 등 확인)")

    async def log_in(self, request: LogInRequest, user_repo: UserRepository):
        """로그인 처리"""
        user = user_repo.get_user_by_email(email=request.email)
        if not user:
            raise HTTPException(status_code=404, detail="해당하는 이메일 존재X")

        verified = self.verify_password(request.password, user.password)
        if not verified:
            raise HTTPException(status_code=401, detail="인증 실패")

        access_token = self.create_jwt(email=user.email)
        return JWTResponse(access_token=access_token)


class NaverAuthService:
    CLIENT_ID = Settings.NAVER_CLIENT_ID
    CLIENT_SECRET = Settings.NAVER_CLIENT_SECRET
    REDIRECT_URI = Settings.NAVER_REDIRECT_URI

    @staticmethod
    async def get_auth_url():
        """네이버 로그인 URL 생성 및 state 저장"""
        state = secrets.token_urlsafe(16)
        redis = await RedisClient.get_redis()
        await redis.setex(f"naver_state:{state}", 300, "valid")  # 5분 유지

        return (
            "https://nid.naver.com/oauth2.0/authorize"
            "?response_type=code"
            f"&client_id={NaverAuthService.CLIENT_ID}"
            f"&redirect_uri={NaverAuthService.REDIRECT_URI}"
            f"&state={state}"
        )

    @staticmethod
    async def validate_state(state: str):
        """Redis에서 state 값 검증"""
        redis = await RedisClient.get_redis()
        saved_state = await redis.get(f"naver_state:{state}")
        if not saved_state:
            raise HTTPException(status_code=400, detail="state 불일치")
        await redis.delete(f"naver_state:{state}")

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

    @staticmethod
    async def handle_naver_callback(code: str, state: str, user_service: UserService, user_repo: UserRepository):
        """네이버 OAuth 콜백 처리"""
        # 1. state 검증
        await NaverAuthService.validate_state(state)

        # 2. 네이버 OAuth 토큰 요청
        token_data = await NaverAuthService.get_token(code, state)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="네이버에서 access_token을 받지 못함.")

        # 3. 네이버 사용자 정보 가져오기
        user_info = await NaverAuthService.get_user_info(access_token)

        # 4. 로그인 또는 회원가입 처리
        result = await NaverAuthService.handle_login_or_signup(user_info, user_repo, user_service)

        return result["redirect_url"]

    @staticmethod
    async def handle_login_or_signup(user_info: dict, user_repo: UserRepository, user_service: UserService):
        """네이버 로그인 또는 회원가입 처리"""
        email = user_info.get("email")
        name = user_info.get("name")
        nickname = user_info.get("id")
        gender = user_info.get("gender")
        birthday = user_info.get("birthday")
        birthyear = user_info.get("birthyear")

        if not all([email, name, nickname, gender, birthday, birthyear]):
            raise HTTPException(status_code=400, detail="사용자 정보 가져오기 실패")

        # 생년월일 포맷 정리
        birthday = "-".join(part.zfill(2) for part in birthday.split("-"))
        birth = f"{birthyear}-{birthday}"

        # 기존 유저 확인
        user = user_repo.get_user_by_email(email=email)
        if user:
            # 로그인 처리
            token = user_service.create_jwt(email=user.email)
            return {"redirect_url": f"http://프론트엔드서버/auth/success?token={token}"}

        # 회원가입 처리
        try:
            password = secrets.token_urlsafe(12)
            hashed_password = user_service.hash_password(password)
            user = User(
                email=email,
                password=hashed_password,
                name=name,
                nickname=f"naver_{nickname}",
                birth=birth,
                gender=gender,
                social_auth="N",
            )
            user_repo.save_user(user)
            token = user_service.create_jwt(email=user.email)
            return {"redirect_url": f"http://프론트엔드서버/auth/signup?token={token}"}

        except Exception as e:
            raise HTTPException(status_code=500, detail="회원가입 중 오류 발생")
