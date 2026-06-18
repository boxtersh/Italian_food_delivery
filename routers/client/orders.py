from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import CartItem, Order, OrderItem, OrderStatus, User
from schemas import OrderOut
from routers.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["client: orders"])


@router.get("", response_model=List[OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Оформляет заказ из текущей корзины пользователя."""
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    order = Order(user_id=user.id, status=OrderStatus.PENDING)
    db.add(order)
    db.flush()  # получаем order.id до коммита

    for ci in cart_items:
        # фиксируем цену на момент заказа
        order_item = OrderItem(
            order_id=order.id,
            dish_id=ci.dish_id,
            quantity=ci.quantity,
            price=ci.dish.price,
        )
        db.add(order_item)

    # очищаем корзину
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()

    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Отменить можно только заказ в статусе 'pending'",
        )
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order