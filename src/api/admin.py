from fastapi import APIRouter, Depends

from dependencies.di import get_admin_service
from schema.request import IngredientCategoriesRequest, IngredientCategoryUpdateRequest
from schema.response import CategoryListSchema
from service.admin_service import AdminService

#관리자 권한 라우터

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/categories", status_code=201)
async def add_category(
    request: IngredientCategoriesRequest,
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.create_category(request)

@router.get("/categories", status_code=200, response_model=CategoryListSchema)
async def get_categories(
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.get_categories()

@router.delete("/categories/{ingredient_name}", status_code=204)
async def delete_category(
    ingredient_name: str,
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.delete_category(ingredient_name)

@router.patch("/categories", status_code=200)
async def update_category(
    request: IngredientCategoryUpdateRequest,
    admin_service: AdminService = Depends(get_admin_service)
):
    return await admin_service.update_category(request)
#@router.get("/logs/unrecognized_ingredient_log", status_code=200)
#@router.get("/logs/manual_expiration_logs", status_code=200)