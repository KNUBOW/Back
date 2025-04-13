from fastapi import Request

from core.logging import security_log
from database.repository.admin_repository import AdminRepository
from database.repository.user_repository import UserRepository
from exception.admin_exception import AdminPermissionException, DuplicateCategoryException, \
    InvalidCategoryNestingException, CategoryNotFoundException
from exception.external_exception import UnexpectedException
from schema.request import IngredientCategoriesRequest
from schema.response import CategorySchema, CategoryListSchema
from service.user_service import UserService
from database.orm import User


#관리자 권한 서비스

class AdminService:
    def __init__(self, user_repo: UserRepository, admin_repo: AdminRepository, user_service: UserService, access_token: str, req: Request):
        self.user_repo = user_repo
        self.admin_repo = admin_repo
        self.user_service = user_service
        self.access_token = access_token
        self.req = req

    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token, self.req)

    async def get_admin_user(self) -> User:
        user = await self.get_current_user()
        if not user.is_admin:
            security_log(
                event="관리자 권한 없음",
                detail=f"비관리자 접근 시도: user_id={user.id}",
                ip=self.req.client.host
            )
            raise AdminPermissionException()
        return user

    async def create_category(self, request: IngredientCategoriesRequest):
        user = await self.get_admin_user()

        if request.child_category and not request.parent_category:
            raise InvalidCategoryNestingException()

        existing = await self.admin_repo.get_category_by_name(request.ingredient_name)
        if existing:
            raise DuplicateCategoryException()

        try:
            new_category = await self.admin_repo.create_category(request, user_id=user.id)

        except Exception as e:
            raise UnexpectedException(detail=f"카테고리 생성 중 알 수 없는 오류: {str(e)}")

        return {
            "식재료명": new_category.ingredient_name,
            "설정한 유통기한": new_category.default_expiration_days,
            "메세지": "카테고리가 성공적으로 등록되었습니다."
        }

    async def get_categories(self) -> CategoryListSchema:
        user = await self.get_admin_user()
        categories = await self.admin_repo.get_all_categories()

        return CategoryListSchema(
            categories=[CategorySchema.model_validate(cat) for cat in categories]
        )

    async def delete_category(self, ingredient_name: str) -> dict:
        user = await self.get_admin_user()

        success = await self.admin_repo.delete_category_by_name(ingredient_name)
        if not success:
            raise CategoryNotFoundException()

        security_log(
            event="카테고리 삭제",
            detail=f"관리자 user_id={user.id}, 삭제된 카테고리: {ingredient_name}",
            ip=self.req.client.host
        )

        return {
            "message": f"카테고리 '{ingredient_name}'가 성공적으로 삭제되었습니다."
        }