from fastapi import APIRouter, Depends
from typing import List

from schema.request import IngredientRequest
from schema.response import (
    IngredientSchema,
    IngredientListSchema,
    BulkCreateResponseSchema
)

from service.ingredient_service import IngredientService
from dependencies.di import get_ingredient_service

#식재료 관련 라우터

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post("", status_code=201, response_model=IngredientSchema)
async def create_ingredient(
    request: IngredientRequest,
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.create_ingredient(request)

@router.post("/list", response_model=BulkCreateResponseSchema)
async def create_ingredients(
    requests: List[IngredientRequest],
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.create_ingredients(requests)

@router.get("", status_code=200, response_model=IngredientListSchema)
async def get_ingredients(
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.get_ingredients()

@router.delete("/{ingredient_name}", status_code=204)
async def delete_ingredient(
    ingredient_name: str,
    service: IngredientService = Depends(get_ingredient_service)
):
    await service.delete_ingredient(ingredient_name)