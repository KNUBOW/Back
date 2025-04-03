from .base_exception import CustomException

class UnauthorizedException(CustomException):
    def __init__(self, detail: str = "로그인이 필요합니다"):
        super().__init__(status_code=401, detail=detail, code="UNAUTHORIZED")

class TokenExpiredException(CustomException):
    def __init__(self, detail: str = "토큰이 유효하지 않거나 만료되었습니다"):
        super().__init__(status_code=401, detail=detail, code="TOKEN_EXPIRED")

class InvalidCredentialsException(CustomException):
    def __init__(self, detail: str = "이메일 또는 비밀번호가 잘못되었습니다"):
        super().__init__(status_code=401, detail=detail, code="INVALID_CREDENTIALS")

class UserNotFoundException(CustomException):
    def __init__(self, detail="해당 유저를 찾을 수 없습니다"):
        super().__init__(status_code=404, detail=detail, code="USER_NOT_FOUND")