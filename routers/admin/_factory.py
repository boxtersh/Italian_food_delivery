from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Dish, DishCategory, User
from schemas import DishCreate, DishUpdate, DishOut
from routers.auth import get_current_admin


def make_admin_router(category: DishCategory, prefix: str, tag: str) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=List[DishOut])
    def list_items(
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin),
    ):
        return db.query(Dish).filter(Dish.category == category).all()

    @router.post("", response_model=DishOut, status_code=status.HTTP_201_CREATED)
    def create_item(
        data: DishCreate,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin),
    ):
        payload = data.model_dump()
        payload["category"] = category  # фиксируем категорию принудительно
        dish = Dish(**payload)
        db.add(dish)
        db.commit()
        db.refresh(dish)
        return dish

    @router.put("/{dish_id}", response_model=DishOut)
    def update_item(
        dish_id: int,
        data: DishUpdate,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin),
    ):
        dish = (
            db.query(Dish)
            .filter(Dish.id == dish_id, Dish.category == category)
            .first()
        )
        if not dish:
            raise HTTPException(status_code=404, detail="Блюдо не найдено")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(dish, field, value)
        db.commit()
        db.refresh(dish)
        return dish

    @router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(
        dish_id: int,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_admin),
    ):
        dish = (
            db.query(Dish)
            .filter(Dish.id == dish_id, Dish.category == category)
            .first()
        )
        if not dish:
            raise HTTPException(status_code=404, detail="Блюдо не найдено")
        db.delete(dish)
        db.commit()

    return router