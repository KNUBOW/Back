from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from schema.request import IngredientCategoriesRequest
from database.orm import IngredientCategories
from core.connection import get_postgres_db

#관리자 권한 라우터

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/categories", status_code=201)
async def add_categories(
    request: IngredientCategoriesRequest,
    db: Session = Depends(get_postgres_db)
):
    existing = db.query(IngredientCategories).filter_by(name=request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리입니다.")

    new_category = IngredientCategories.create(request)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {
        "id": new_category.id,
        "message": "카테고리가 성공적으로 등록되었습니다."
    }
