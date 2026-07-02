from collections import Counter
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from routers.auth import get_optional_user
from config import templates
from database import get_db
from models import CartItem, Dish, User

router = APIRouter(prefix="/cart", tags=["cart"])


def _read_guest_cart(request: Request) -> list[int]:
    raw = request.cookies.get("guest_cart")
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    result = []
    for item in data:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue

    return result


def _write_guest_cart(response: RedirectResponse, cart: list[int]) -> None:
    response.set_cookie(
        key="guest_cart",
        value=json.dumps(cart),
        path="/",
        httponly=True,
        samesite="lax",
    )


def _build_guest_cart_view(db: Session, dish_ids: list[int]):
    counter = Counter(dish_ids)
    if not counter:
        return [], 0

    dishes = db.query(Dish).filter(Dish.id.in_(counter.keys())).all()
    dishes_map = {dish.id: dish for dish in dishes}

    items = []
    total = 0

    for dish_id, quantity in counter.items():
        dish = dishes_map.get(dish_id)
        if not dish:
            continue

        subtotal = dish.price * quantity
        total += subtotal

        items.append({
            "id": dish.id,
            "dish_id": dish.id,
            "quantity": quantity,
            "dish": dish,
            "subtotal": subtotal,
        })

    return items, total


@router.get("")
def view_cart(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user:
        cart_items = (
            db.query(CartItem)
            .options(joinedload(CartItem.dish))
            .filter(CartItem.user_id == user.id)
            .all()
        )

        total = sum(item.dish.price * item.quantity for item in cart_items if item.dish)

        return templates.TemplateResponse(
            "cart.html",
            {
                "request": request,
                "cart_items": cart_items,
                "total": total,
                "is_guest_cart": False,
            },
        )

    guest_cart = _read_guest_cart(request)
    cart_items, total = _build_guest_cart_view(db, guest_cart)

    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total": total,
            "is_guest_cart": True,
        },
    )


@router.post("/add/{dish_id}")
def add_to_cart(
    dish_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        return RedirectResponse(url="/menu", status_code=302)

    if user:
        cart_item = db.query(CartItem).filter(
            CartItem.user_id == user.id,
            CartItem.dish_id == dish_id,
        ).first()

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=user.id, dish_id=dish_id, quantity=1)
            db.add(cart_item)

        db.commit()
        return RedirectResponse(url="/cart", status_code=302)

    guest_cart = _read_guest_cart(request)
    guest_cart.append(dish_id)

    response = RedirectResponse(url="/cart", status_code=302)
    _write_guest_cart(response, guest_cart)
    return response


@router.post("/increase/{item_id}")
def increase_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user:
        cart_item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.user_id == user.id,
        ).first()

        if cart_item:
            cart_item.quantity += 1
            db.commit()

        return RedirectResponse(url="/cart", status_code=302)

    guest_cart = _read_guest_cart(request)
    guest_cart.append(item_id)

    response = RedirectResponse(url="/cart", status_code=302)
    _write_guest_cart(response, guest_cart)
    return response


@router.post("/decrease/{item_id}")
def decrease_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user:
        cart_item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.user_id == user.id,
        ).first()

        if cart_item:
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                db.delete(cart_item)
            db.commit()

        return RedirectResponse(url="/cart", status_code=302)

    guest_cart = _read_guest_cart(request)

    try:
        guest_cart.remove(item_id)
    except ValueError:
        pass

    response = RedirectResponse(url="/cart", status_code=302)
    _write_guest_cart(response, guest_cart)
    return response


@router.post("/remove/{item_id}")
def remove_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user:
        cart_item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.user_id == user.id,
        ).first()

        if cart_item:
            db.delete(cart_item)
            db.commit()

        return RedirectResponse(url="/cart", status_code=302)

    guest_cart = _read_guest_cart(request)
    guest_cart = [dish_id for dish_id in guest_cart if dish_id != item_id]

    response = RedirectResponse(url="/cart", status_code=302)
    _write_guest_cart(response, guest_cart)
    return response


@router.post("/clear")
def clear_cart(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if user:
        db.query(CartItem).filter(CartItem.user_id == user.id).delete()
        db.commit()
        return RedirectResponse(url="/", status_code=302)

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="guest_cart", path="/")
    return response