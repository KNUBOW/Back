from .base_exception import CustomException

class AIServiceException(CustomException):
    log_level = "ERROR"
    def __init__(self, detail="AI 호출 중 문제가 발생했습니다"):
        super().__init__(status_code=500, detail=detail, code="AI_SERVICE_ERROR")

class AINullResponseException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="AI 응답 도중 문제가 발생했습니다"):
        super().__init__(status_code=500, detail=detail, code="AI_EMPTY_RESPONSE")

class AIJsonDecodeException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="AI 응답을 JSON으로 파싱하는 중 오류가 발생했습니다"):
        super().__init__(status_code=500, detail=detail, code="AI_JSON_ERROR")

class InvalidAIRequestException(CustomException):
    log_level = "WARNING"
    def __init__(self, detail="요청 데이터가 유효하지 않습니다"):
        super().__init__(status_code=400, detail=detail, code="INVALID_AI_REQUEST")