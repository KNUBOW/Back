class CustomException(Exception):
    log_level: str = "WARNING"  # 기본 로그 레벨

    def __init__(self, status_code: int = 400, detail: str = "에러가 발생했습니다", code: str = "ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.code = code

    def log(self, logger, request_url: str = ""):
        message = f"[{self.__class__.__name__}] {self.code} - {self.detail}"
        if self.log_level == "INFO":
            logger.info(message)
        elif self.log_level == "DEBUG":
            logger.debug(message)
        elif self.log_level == "ERROR":
            logger.error(message)
        else:
            logger.warning(message)