import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import datetime, timedelta, timezone



# 한국 시간대 설정 (UTC+9)
KST = timezone(timedelta(hours=9))
def kst_converter(*args):
    return datetime.now(tz=KST).timetuple()

# 로그 디렉토리 생성
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 포매터 설정
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    "%Y-%m-%d %H:%M:%S"
)
formatter.converter = kst_converter

# 로그 파일 이름 매핑
LOG_FILES = {
    "system": "system.log",
    "error": "error.log",
    "business": "business.log",
    "access": "access.log",
    "security": "security.log",
    "background": "background.log"
}

def create_file_handler(name: str, level=logging.INFO):
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILES[name]),
        maxBytes=1_000_000,
        backupCount=10
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler

def setup_logging():
    # 각 카테고리별 전용 로거 설정
    loggers = {}

    for name in LOG_FILES:
        logger = logging.getLogger(f"capstone.{name}")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(create_file_handler(name))

        # 콘솔 출력
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)

        loggers[name] = logger

    return loggers

# 비즈니스 로그 추적
def service_log(service: str, message: str, user_id: int | None = None, level: str = "INFO"):
    tag = f"[{service}]"
    user_info = f"유저({user_id})" if user_id else "익명 사용자"
    log_msg = f"{tag} {user_info} - {message}"

    logger = loggers["business"]
    match level.upper():
        case "DEBUG": logger.debug(log_msg)
        case "WARNING": logger.warning(log_msg)
        case "ERROR": logger.error(log_msg)
        case _: logger.info(log_msg)

# 보안 로그 설정
def security_log(event: str, detail: str, user_id: int = None, ip: str = None, level: str = "WARNING"):
    logger = loggers["security"]
    message = f"[Security] {event} | {detail}"

    if user_id:
        message += f" | user_id={user_id}"
    if ip:
        message += f" | ip={ip}"

    match level.upper():
        case "INFO":logger.info(message)
        case "ERROR":logger.error(message)
        case "CRITICAL":logger.critical(message)
        case _:logger.warning(message)

# 전역에서 쓸 로거들
loggers = setup_logging()
__all__ = ["loggers", "service_log"]

# 로그 활성 시 출력 메세지
loggers["system"].info("시스템 로그 활성")
loggers["error"].error("에러 로그 활성")
loggers["business"].info("비즈니스 로그 활성")
loggers["access"].info("접근 로그 활성")
loggers["security"].warning("보안 관련 로그 활성")
loggers["background"].info("스케줄러 로그 활성")
