from fastapi import APIRouter, Depends

from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientListSchema
from service.ingredient_service import IngredientService
from service.di import ServiceProvider

router = APIRouter(prefix="/ingredients")

@router.post("", status_code=201, response_model=IngredientSchema)
async def create_ingredient(
    request: IngredientRequest,
    service: IngredientService = Depends(ServiceProvider.ingredient_service),
):
    return await service.create_ingredient(request)


@router.get("", status_code=200, response_model=IngredientListSchema)
async def get_ingredients(
    service: IngredientService = Depends(ServiceProvider.ingredient_service),
):
    return await service.get_ingredients()


@router.delete("/{ingredient_name}", status_code=204)
async def delete_ingredient(
    ingredient_name: str,
    service: IngredientService = Depends(ServiceProvider.ingredient_service),
):
    await service.delete_ingredient(ingredient_name)
