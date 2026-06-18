from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Dish, DishCategory
from schemas import DishOut


def make_client_router(category: DishCategory, prefix: str, tag: str) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=List[DishOut])
    def list_items(db: Session = Depends(get_db)):
        return (
            db.query(Dish)
            .filter(Dish.category == category, Dish.is_available == True)  # noqa: E712
            .all()
        )

    @router.get("/{dish_id}", response_model=DishOut)
    def get_item(dish_id: int, db: Session = Depends(get_db)):
        dish = (
            db.query(Dish)
            .filter(Dish.id == dish_id, Dish.category == category)
            .first()
        )
        if not dish:
            raise HTTPException(status_code=404, detail="Блюдо не найдено")
        return dish

    return router