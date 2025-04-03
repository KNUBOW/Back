from exception.base_exception import CustomException

class SocialLoginException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="소셜 로그인 중 오류가 발생했습니다"):
        super().__init__(status_code=400, detail=detail, code="SOCIAL_LOGIN_ERROR")

class InvalidStateException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="OAuth state 값이 유효하지 않습니다"):
        super().__init__(status_code=400, detail=detail, code="INVALID_STATE")

class SocialTokenException(CustomException):
    log_level = "ERROR"
    def __init__(self, detail="소셜 토큰 발급 실패"):
        super().__init__(status_code=500, detail=detail, code="TOKEN_FETCH_FAILED")

class SocialUserInfoException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="소셜 사용자 정보 조회 실패"):
        super().__init__(status_code=400, detail=detail, code="USER_INFO_ERROR")

class MissingSocialDataException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="소셜 사용자 정보가 누락되었습니다 (개인 정보 다 수락해야함)"):
        super().__init__(status_code=400, detail=detail, code="MISSING_SOCIAL_DATA")

class SocialSignupException(CustomException):
    log_level = "ERROR"
    def __init__(self, detail="소셜 사용자 회원가입 실패"):
        super().__init__(status_code=500, detail=detail, code="SOCIAL_SIGNUP_ERROR")
