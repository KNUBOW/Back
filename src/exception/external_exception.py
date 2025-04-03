class GlobalException(Exception):
    log_level: str = "WARNING"  # 기본 로그 레벨

    def __init__(self, status_code: int = 500, detail: str = "에러가 발생했습니다", code: str = "ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.code = code

    def log(self, logger, request_url=""):
        message = f"[{self.__class__.__name__}] {self.code} - {self.detail} (URL: {request_url})"
        getattr(logger, self.log_level.lower(), logger.warning)(message)

class UnexpectedException(GlobalException):
    log_level = "ERROR"

    def __init__(self, detail="예기치 못한 오류"):
        super().__init__(status_code=500, code="UNEXPECTED_ERROR", detail=detail)
