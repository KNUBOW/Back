from fastapi import APIRouter, Depends, HTTPException
from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientListSchema
from service.ingredient import IngredientService
from service.user import UserService
from database.repository import IngredientRepository, UserRepository
from core.security import get_access_token

router = APIRouter(prefix="/ingredients")


def get_ingredient_service(
    user_repo: UserRepository = Depends(),
    ingredient_repo: IngredientRepository = Depends(),
    user_service: UserService = Depends()
) -> IngredientService:
    """FastAPI의 `Depends`를 사용하여 `IngredientService` 인스턴스를 생성"""
    return IngredientService(user_repo, ingredient_repo, user_service)


@router.post("", status_code=201)
async def create_ingredient_handler(
    request: IngredientRequest,
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
) -> IngredientSchema:
    try:
        # 비동기식으로 식재료 추가
        return await ingredient_service.create_ingredient(request, access_token)
    except HTTPException as e:
        # HTTPException 발생 시 에러 처리
        raise e
    except Exception as e:
        # 예기치 않은 에러 발생 시
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", status_code=200)
async def get_ingredients_handler(
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
) -> IngredientListSchema:
    try:
        # 비동기식으로 식재료 목록 조회
        return await ingredient_service.get_ingredients(access_token)
    except HTTPException as e:
        # HTTPException 발생 시 에러 처리
        raise e
    except Exception as e:
        # 예기치 않은 에러 발생 시
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{ingredient_name}", status_code=204)
async def delete_ingredient_handler(
    ingredient_name: str,
    access_token: str = Depends(get_access_token),
    ingredient_service: IngredientService = Depends(get_ingredient_service),
):
    try:
        # 비동기식으로 식재료 삭제
        await ingredient_service.delete_ingredient(ingredient_name, access_token)
    except HTTPException as e:
        # HTTPException 발생 시 에러 처리
        raise e
    except Exception as e:
        # 예기치 않은 에러 발생 시
        raise HTTPException(status_code=500, detail=str(e))
