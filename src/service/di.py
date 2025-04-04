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

class RepositoryProvider:
    @staticmethod
    def user_repo(session: AsyncSession = Depends(get_postgres_db)):
        return UserRepository(session)

    @staticmethod
    def ingredient_repo(session: AsyncSession = Depends(get_postgres_db)):
        return IngredientRepository(session)


class ServiceProvider:
    @staticmethod
    def user_service(user_repo=Depends(RepositoryProvider.user_repo)):
        return UserService(user_repo)

    @staticmethod
    def ingredient_service(
        req: Request,
        access_token: str = Depends(get_access_token),
        ingredient_repo: IngredientRepository = Depends(RepositoryProvider.ingredient_repo),
        user_repo: UserRepository = Depends(RepositoryProvider.user_repo),
        user_service: UserService = Depends(user_service),
    ):
        return IngredientService(user_repo, ingredient_repo, user_service, access_token, req)

    @staticmethod
    def cook_ai_service(
        req: Request,
        access_token: str = Depends(get_access_token),  # JWT Token
        user_service: UserService = Depends(user_service),
        user_repo: UserRepository = Depends(RepositoryProvider.user_repo),
    ):
        return CookAIService(user_service, user_repo, access_token, req)

    @staticmethod
    def naver_auth_service(
        user_service: UserService = Depends(user_service),
        user_repo: UserRepository = Depends(RepositoryProvider.user_repo),
    ):
        return NaverAuthService(user_service, user_repo)
