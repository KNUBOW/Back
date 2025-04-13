from exception.base_exception import CustomException


class AdminPermissionException(CustomException):
    def __init__(self):
        super().__init__(status_code=403, detail="관리자 권한이 필요합니다.", code="NO_ADMIN_PERMISSION")


class DuplicateCategoryException(CustomException):
    def __init__(self):
        super().__init__(status_code=400, detail="이미 유통기한이 등록된 식재료입니다.", code="DUPLICATE_CATEGORY")


class InvalidCategoryNestingException(CustomException):
    def __init__(self):
        super().__init__(status_code=400, detail="하위 카테고리는 상위 카테고리 없이 등록할 수 없습니다.", code="INVALID_CATEGORY_NESTING")

class CategoryNotFoundException(CustomException):
    def __init__(self):
        super().__init__(status_code=404, detail="해당 식재료를 찾을 수 없습니다.", code="CATEGORY_NOT_FOUND")