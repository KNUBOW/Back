from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository.admin_repository import AdminRepository
from database.repository.ingredient_repository import IngredientRepository
from database.repository.user_repository import UserRepository
from core.connection import get_postgres_db
from service.admin_service import AdminService
from service.auth.social.google import GoogleAuthService
from service.user_service import UserService
from service.ingredient_service import IngredientService
from service.recipe.foodthing import CookAIService
from service.auth.social.naver import NaverAuthService
from service.auth.jwt_handler import get_access_token

# DI(Dependency Injection)를 이용하여 라우터와 서비스에서 코드를 줄여 가독성 올림.

# ------------------- 리포지토리 관련 DI -------------------
def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

def get_ingredient_repo(session: AsyncSession = Depends(get_postgres_db)) -> IngredientRepository:
    return IngredientRepository(session)

def get_admin_repo(session: AsyncSession = Depends(get_postgres_db)) -> AdminRepository:
    return AdminRepository(session)

# ------------------- 서비스 관련 DI -------------------
def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)

def get_admin_service(
    req: Request,
    access_token: str = Depends(get_access_token),
    user_repo: UserRepository = Depends(get_user_repo),
    admin_repo: AdminRepository = Depends(get_admin_repo),
    user_service: UserService = Depends(get_user_service),
) -> AdminService:
    return AdminService(user_repo, admin_repo, user_service, access_token, req)

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

def get_google_auth_service(
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> GoogleAuthService:
    return GoogleAuthService(user_service, user_repo)