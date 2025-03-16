import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from core.config import Settings
from fastapi import HTTPException


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