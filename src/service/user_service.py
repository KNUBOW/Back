import bcrypt

from fastapi import Request
from jose import jwt, JWTError
from datetime import datetime, timedelta

from exception.external_exception import UnexpectedException

from exception.auth_exception import (
    TokenExpiredException,
    InvalidCredentialsException,
    UserNotFoundException
)

from exception.user_exception import (
    DuplicateEmailException,
    DuplicateNicknameException
)

from core.logging import security_log
from core.config import settings
from database.repository.user_repository import UserRepository
from database.orm import User
from schema.request import SignUpRequest, LogInRequest
from schema.response import UserSchema, JWTResponse


class UserService:

    encoding = "UTF-8"
    secret_key = settings.SECRET_KEY.get_secret_value()
    jwt_algorithm = "HS256"

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    # 비밀번호 해쉬 처리
    def hash_password(self, plain_password: str) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt=bcrypt.gensalt(),
        )
        return hashed_password.decode(self.encoding)

    # 해쉬 검증
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.encoding),
            hashed_password.encode(self.encoding)
        )

    # jwt 생성
    def create_jwt(self, email: str) -> str:
        return jwt.encode(
            {
                "sub": email,
                "exp": datetime.now() + timedelta(days=1),
            },
            self.secret_key,
            algorithm=self.jwt_algorithm,
        )

    #jwt 복호화
    def decode_jwt(self, access_token: str, req: Request) -> str:
        try:
            payload: dict = jwt.decode(
                access_token, self.secret_key, algorithms=[self.jwt_algorithm]
            )
            email = payload.get("sub")

            if email is None:
                security_log(
                    event="Token Expired",
                    detail="JWT payload에서 email(sub) 누락됨",
                    ip=req.client.host
                )
                raise TokenExpiredException()

            return email

        except JWTError as e:
            security_log(
                event="Invalid Token",
                detail=f"JWT 디코드 실패 또는 조작된 토큰 사용: {str(e)}",
                ip=req.client.host
            )
            raise TokenExpiredException()

    # 회원가입 관련
    async def sign_up(self, request: SignUpRequest):
        # 중복 확인
        try:
            if await self.user_repo.get_user_by_email(request.email):   # 이메일 중복
                raise DuplicateEmailException()

            if await self.user_repo.get_user_by_nickname(request.nickname): # 닉네임 중복
                raise DuplicateNicknameException()

            hashed_password = self.hash_password(request.password)

            user = User.create(
                email=request.email,
                hashed_password=hashed_password,
                name=request.name,
                nickname=request.nickname,
                birth=request.birth,
                gender=request.gender,
            )

            user = await self.user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except (DuplicateEmailException, DuplicateNicknameException):
            raise

        except Exception as e:
            raise UnexpectedException(detail=f"회원가입 중 예기치 못한 오류 발생: {str(e)}")

    # 로그인 관련
    async def log_in(self, request: LogInRequest, req: Request):
        user = await self.user_repo.get_user_by_email(email=request.email)
        if not user:
            security_log(
                event="Login Failed",
                detail=f"존재하지 않는 이메일로 로그인 시도: {request.email}",
                ip=req.client.host
            )
            raise InvalidCredentialsException()

        verified = self.verify_password(request.password, user.password)
        if not verified:
            if not verified:
                security_log(
                    event="Login Failed",
                    detail=f"비밀번호 틀림 - 이메일: {request.email}",
                    ip=req.client.host
                )
            raise InvalidCredentialsException()

        access_token = self.create_jwt(email=user.email)
        return JWTResponse(access_token=access_token)

    # 유저의 토큰 조회
    async def get_user_by_token(self, access_token: str, req: Request) -> User:
        email: str = self.decode_jwt(access_token=access_token, req=req)
        user: User | None = await self.user_repo.get_user_by_email(email=email)
        if not user:
            security_log(
                event="User Not Found",
                detail=f"JWT 이메일 {email}에 해당하는 유저가 없음",
                ip=req.client.host
            )
            raise UserNotFoundException()
        return user