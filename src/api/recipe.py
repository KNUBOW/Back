from fastapi import APIRouter, Depends, Body

from service.recipe.foodthing import CookAIService
from schema.request import CookingRequest
from service.di import get_cook_ai_service

router = APIRouter(prefix="/recipe", tags=["Recipe"])

@router.get("/suggest", status_code=200)
async def suggest_recipe(
    cook_ai: CookAIService = Depends(get_cook_ai_service),
):
    return await cook_ai.get_suggest_recipes()

@router.post("/cooking", status_code=200)
async def cooking_recipe(
    request: CookingRequest,
    cook_ai: CookAIService = Depends(get_cook_ai_service)
):
    return await cook_ai.get_food_recipe(request.model_dump())

@router.post("/quick", status_code=200)
async def quick_recipe(
    chat: str = Body(..., media_type="text/plain"),
    cook_ai: CookAIService = Depends(get_cook_ai_service)
):
    return await cook_ai.get_quick_recipe(chat)

@router.post("/search", status_code=200)
async def search_recipe(
    chat: str = Body(..., media_type="text/plain"),
    cook_ai: CookAIService = Depends(get_cook_ai_service)
):
    return await cook_ai.get_search_recipe(chat)
