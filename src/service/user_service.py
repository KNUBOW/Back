import bcrypt

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
                raise TokenExpiredException()
            return email

        except JWTError:
            raise TokenExpiredException()

    async def sign_up(self, request: SignUpRequest):
        # 중복 확인
        try:
            if await self.user_repo.get_user_by_email(request.email):
                raise DuplicateEmailException()

            if await self.user_repo.get_user_by_nickname(request.nickname):
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

    async def log_in(self, request: LogInRequest):
        user = await self.user_repo.get_user_by_email(email=request.email)
        if not user:
            raise InvalidCredentialsException()

        verified = self.verify_password(request.password, user.password)
        if not verified:
            raise InvalidCredentialsException()

        access_token = self.create_jwt(email=user.email)
        return JWTResponse(access_token=access_token)

    async def get_user_by_token(self, access_token: str) -> User:
        email: str = self.decode_jwt(access_token=access_token)
        user: User | None = await self.user_repo.get_user_by_email(email=email)
        if not user:
            raise UserNotFoundException()
        return user