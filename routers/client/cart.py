from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import CartItem, Dish, User
from schemas import CartItemCreate, CartItemUpdate, CartItemOut
from routers.auth import get_current_user

router = APIRouter(prefix="/cart", tags=["client: cart"])


@router.get("", response_model=List[CartItemOut])
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(CartItem).filter(CartItem.user_id == user.id).all()


@router.post("", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    data: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть больше 0")

    dish = (
        db.query(Dish)
        .filter(Dish.id == data.dish_id, Dish.is_available == True)  # noqa: E712
        .first()
    )
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено или недоступно")

    # если блюдо уже в корзине — увеличиваем количество
    item = (
        db.query(CartItem)
        .filter(CartItem.user_id == user.id, CartItem.dish_id == data.dish_id)
        .first()
    )
    if item:
        item.quantity += data.quantity
    else:
        item = CartItem(user_id=user.id, dish_id=data.dish_id, quantity=data.quantity)
        db.add(item)

    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=CartItemOut)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть больше 0")

    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Позиция корзины не найдена")

    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Позиция корзины не найдена")
    db.delete(item)
    db.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()