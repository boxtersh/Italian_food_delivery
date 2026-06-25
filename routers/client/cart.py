from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from jose import jwt
import json

from database import get_db
from models import CartItem, Dish, User
from schemas import CartItemCreate
from config import settings


router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/add")
async def add_to_cart(
        request: Request,
        response: Response,
        payload: CartItemCreate,
        db: Session = Depends(get_db),
):

    dish = db.query(Dish).filter(Dish.id == payload.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    current_user = None
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if token:
        try:
            payload_jwt = jwt.decode(token, settings.secret_key, algorithms=settings.algorithm)
            sub = payload_jwt.get("sub")
            if sub:
                current_user = db.query(User).filter(User.id == int(sub)).first()
        except Exception:
            pass


    if current_user:
        existing_item = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.dish_id == payload.dish_id
        ).first()

        if existing_item:
            existing_item.quantity += payload.quantity
        else:
            new_item = CartItem(user_id=current_user.id, dish_id=payload.dish_id, quantity=payload.quantity)
            db.add(new_item)

        db.commit()

        cart_size = db.query(CartItem).filter(CartItem.user_id == current_user.id).count()

        return {
            "status": "added",
            "cart_size": cart_size,
            "message": f"{dish.name} добавлено в вашу корзину",
            "is_guest": False
        }

    else:
        guest_cart_cookie = request.cookies.get("guest_cart")
        guest_ids = []

        if guest_cart_cookie:
            try:
                guest_ids = json.loads(guest_cart_cookie)
            except:
                guest_ids = []

        for _ in range(payload.quantity):
            guest_ids.append(payload.dish_id)

        response.set_cookie(
            key="guest_cart",
            value=json.dumps(guest_ids),
            max_age=60 * 60 * 24 * 7,
            httponly=False
        )

        return {
            "status": "added",
            "cart_size": len(guest_ids),
            "message": f"{dish.name} добавлено в корзину (как гость)",
            "is_guest": True
        }
