import bcrypt

from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from core.config import Settings
from database.repository.user_repository import UserRepository
from database.orm import User
from schema.request import SignUpRequest, LogInRequest
from schema.response import UserSchema, JWTResponse


class UserService:

    encoding = Settings.encoding
    secret_key = Settings.secret_key
    jwt_algorithm = Settings.jwt_algorithm

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def hash_password(self, plain_password: str) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt=bcrypt.gensalt(),
        )
        return hashed_password.decode(self.encoding)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.encoding),
            hashed_password.encode(self.encoding)
        )

    def create_jwt(self, email: str) -> str:
        return jwt.encode(
            {
                "sub": email,
                "exp": datetime.now() + timedelta(days=1),
            },
            self.secret_key,
            algorithm=self.jwt_algorithm,
        )

    def decode_jwt(self, access_token: str):
        try:
            payload: dict = jwt.decode(
                access_token, self.secret_key, algorithms=[self.jwt_algorithm]
            )
            email = payload.get("sub")

            if email is None:
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
            return email

        except JWTError:
            raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 토큰")

    async def sign_up(self, request: SignUpRequest):
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

            user = await self.user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except OperationalError:
            raise HTTPException(status_code=500, detail="컨테이너 또는 데이터베이스 관련 오류 발생(docker, mysql 등 확인)")

    async def log_in(self, request: LogInRequest):
        user = await self.user_repo.get_user_by_email(email=request.email)
        if not user:
            raise HTTPException(status_code=404, detail="해당하는 이메일 존재X")

        verified = self.verify_password(request.password, user.password)
        if not verified:
            raise HTTPException(status_code=401, detail="인증 실패")

        access_token = self.create_jwt(email=user.email)
        return JWTResponse(access_token=access_token)

    async def get_user_by_token(self, access_token: str) -> User:
        email: str = self.decode_jwt(access_token=access_token)
        user: User | None = await self.user_repo.get_user_by_email(email=email)
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        return user