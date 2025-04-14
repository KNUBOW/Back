from fastapi import Request

from core.logging import security_log
from database.repository.admin_repository import AdminRepository
from database.repository.user_repository import UserRepository
from exception.admin_exception import AdminPermissionException, DuplicateCategoryException, \
    InvalidCategoryNestingException, CategoryNotFoundException
from exception.external_exception import UnexpectedException
from schema.request import IngredientCategoriesRequest, IngredientCategoryUpdateRequest
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
            "ingredient_name": new_category.ingredient_name,
            "set_expiration": new_category.default_expiration_days,
            "message": "카테고리가 성공적으로 등록되었습니다."
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

    async def update_category(self, request: IngredientCategoryUpdateRequest):
        user = await self.get_admin_user()

        target = await self.admin_repo.get_category_by_name(request.ingredient_name)
        if not target:
            raise CategoryNotFoundException()

        success = await self.admin_repo.update_category_expiration(
            ingredient_name=request.ingredient_name,
            new_expiration=request.default_expiration_days
        )
        if not success:
            raise UnexpectedException(detail="카테고리 수정 중 DB에서 해당 항목을 찾을 수 없습니다.")

        return {"message": f"'{request.ingredient_name}' 유통기한이 {request.default_expiration_days}일로 수정되었습니다."}
