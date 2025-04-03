from .base_exception import CustomException

class DuplicateEmailException(CustomException):
    def __init__(self, detail: str = "이미 사용 중인 이메일입니다"):
        super().__init__(status_code=409, detail=detail, code="EMAIL_CONFLICT")

class DuplicateNicknameException(CustomException):
    def __init__(self, detail: str = "이미 사용 중인 닉네임입니다"):
        super().__init__(status_code=409, detail=detail, code="NICKNAME_CONFLICT")