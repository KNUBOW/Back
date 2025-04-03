from .base_exception import CustomException

class TransactionException(CustomException):
    log_level = "ERROR"

    def __init__(self, detail="트랜잭션 처리 중 오류가 발생했습니다"):
        super().__init__(status_code=400, detail=detail, code="TX_ERROR")

class DatabaseException(CustomException):
    log_level = "ERROR"

    def __init__(self, detail: str = "데이터베이스 오류가 발생했습니다"):
        super().__init__(status_code=500, detail=detail, code="DB_ERROR")

