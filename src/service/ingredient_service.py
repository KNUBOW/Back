from database.orm import Ingredient
from schema.request import IngredientRequest
from schema.response import IngredientListSchema, IngredientSchema
from core.logging import service_log
from fastapi import Request
from datetime import date
from typing import List, Dict

from exception.ingredient_exception import (
    IngredientConflictException,
    IngredientNotFoundException
)

# 식재료 관련 서비스

class IngredientService:
    def __init__(self, user_repo, ingredient_repo, user_service, access_token: str, req: Request):
        self.user_repo = user_repo
        self.ingredient_repo = ingredient_repo
        self.user_service = user_service
        self.access_token = access_token
        self.req = req

    # 토큰을 통해 유저 파악
    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token, self.req)

    # 유저의 식재료에 단일 추가
    async def create_ingredient(self, request: IngredientRequest) -> IngredientSchema:
        result = await self.create_ingredients([request])

        if not result["created"]:
            # 중복이라 등록 안 된 경우 예외 발생
            raise IngredientConflictException()

        return result["created"][0]

    # 유저의 식재료에 다중 추가
    async def create_ingredients(self, requests: List[IngredientRequest]) -> Dict:

        user = await self.get_current_user()

        # 다중 추가에서 식재료 중복 발생 시 걸러내기 위함
        created_ingredients = []
        duplicated_names = []

        for request in requests:
            # 중복 확인
            existing = await self.ingredient_repo.get_ingredient_by_name(user_id=user.id, name=request.name)
            if existing:
                duplicated_names.append(request.name)
                continue

            expiration_date = request.expiration_date

            # 유저가 유통기한 입력할 경우 (유통기한에 대한 정보 없던거 로그남기거나 또는 유통기한이 DB와 다를시 로그 남김)
            if expiration_date and isinstance(expiration_date, date):
                # DB에서 지정된 유통기한 조회
                default_expiration = await self.ingredient_repo.get_default_expiration(request.name)

                # DB에 유통기한이 존재하지 않을 때
                if not default_expiration:
                    # 기본값이 없으면 → unknown    (유통기한에 대한 정보 없던 거 유저가 직접 입력시 -> 업데이트용)
                    days_left = (expiration_date - date.today()).days
                    await self.ingredient_repo.save_manual_expiration_log(
                        user_id=user.id,
                        ingredient_name=request.name,
                        expiration_date=days_left,
                        event_type="unknown"
                    )
                elif expiration_date != default_expiration:
                    # 기본값과 다르면 → different  (유통기한 정보는 있었으나 유저가 입력한 것과 우리 DB의 유통기한이 다를 시 -> 유통기한 편차 조정용)
                    days_left = (expiration_date - date.today()).days
                    await self.ingredient_repo.save_manual_expiration_log(
                        user_id=user.id,
                        ingredient_name=request.name,
                        expiration_date=days_left,
                        event_type="different",
                    )

                # DB의 유통기한과 유저가 입력한 유통기한이 같으면 아무 로그도 남기지 않음 (불필요한 로그 제거)

            # 유통기한을 입력하지 않았을 경우 (유통기한을 자동 기입하거나 또는 DB에도 유통기한이 없을 때 로그 남김) -> 업데이트 용
            else:
                default_expiration = await self.ingredient_repo.get_default_expiration(request.name)

                # 유통기한 DB에 존재하지 않을 시 로그 남김
                if not default_expiration:
                    await self.ingredient_repo.save_unrecognized_ingredient_log(
                        user_id=user.id,
                        ingredient_name=request.name
                    )

                # DB에 존재할 시 유통기한 자동 기입
                expiration_date = default_expiration

            ingredient = Ingredient.create(request, user.id, expiration_date=expiration_date)
            await self.ingredient_repo.create_ingredient(ingredient)

            service_log("IngredientService", f"식재료 '{ingredient.name}' 추가", user_id=user.id)
            created_ingredients.append(IngredientSchema.model_validate(ingredient))

        # 결과 메시지 생성
        message = f"{len(created_ingredients)}개 식재료가 추가되었습니다."
        if duplicated_names:
            message += f" 중복으로 인해 {len(duplicated_names)}개는 제외되었습니다: {', '.join(duplicated_names)}"

        return {
            "message": message,
            "created": created_ingredients,
            "skipped_duplicates": duplicated_names
        }

    # 식재료 조회
    async def get_ingredients(self):
        user = await self.get_current_user()
        ingredients = await self.ingredient_repo.get_ingredients(user.id)

        service_log("IngredientService", f"식재료 목록 조회", user_id=user.id)

        return IngredientListSchema(ingredients=ingredients)

    # 식재료 삭제
    async def delete_ingredient(self, ingredient_name: str):
        user = await self.get_current_user()
        success = await self.ingredient_repo.delete_ingredient(user.id, ingredient_name)

        if not success:
            raise IngredientNotFoundException()

        service_log("IngredientService", f"식재료 '{ingredient_name}' 삭제", user_id=user.id)
        return True