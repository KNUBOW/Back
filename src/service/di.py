# DI(Dependency Injection)를 이용하여 라우터와 서비스에서 코드를 줄여 가독성 올림.

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository.ingredient_repository import IngredientRepository
from database.repository.user_repository import UserRepository
from core.connection import get_postgres_db
from service.user_service import UserService
from service.ingredient_service import IngredientService
from service.recipe.foodthing import CookAIService
from service.auth.social.naver import NaverAuthService
from service.auth.jwt_handler import get_access_token

# ----------------------
# Repository DI
# ----------------------

def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

def get_ingredient_repo(session: AsyncSession = Depends(get_postgres_db)) -> IngredientRepository:
    return IngredientRepository(session)

# ----------------------
# Service DI
# ----------------------

def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)

def get_ingredient_service(
    req: Request,
    access_token: str = Depends(get_access_token),
    ingredient_repo: IngredientRepository = Depends(get_ingredient_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
) -> IngredientService:
    return IngredientService(user_repo, ingredient_repo, user_service, access_token, req)

def get_cook_ai_service(
    req: Request,
    access_token: str = Depends(get_access_token),
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> CookAIService:
    return CookAIService(user_service, user_repo, access_token, req)

def get_naver_auth_service(
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> NaverAuthService:
    return NaverAuthService(user_service, user_repo)
