from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import CartItem, Dish, User, Order, OrderItem
from routers.auth import get_optional_user
from config import templates

router = APIRouter(prefix="/orders", tags=["client: orders"])


@router.get("/checkout", response_class=HTMLResponse)
async def show_checkout_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Логика получения корзины (одинаково для гостя и авторизованного)
    if user:
        cart_items = (
            db.query(CartItem)
            .options(joinedload(CartItem.dish))
            .filter(CartItem.user_id == user.id)
            .all()
        )
        total = sum(
            item.dish.price * item.quantity
            for item in cart_items
            if item.dish
        )
    else:
        import json
        from collections import Counter

        raw = request.cookies.get("guest_cart")
        if not raw:
            raise HTTPException(status_code=400, detail="Корзина пуста")

        try:
            dish_ids = json.loads(raw)
        except Exception:
            raise HTTPException(status_code=400, detail="Некорректная корзина гостя")

        if not isinstance(dish_ids, list):
            raise HTTPException(status_code=400, detail="Некорректная корзина гостя")

        counter = Counter(dish_ids)
        dishes = db.query(Dish).filter(Dish.id.in_(counter.keys())).all()
        dishes_map = {d.id: d for d in dishes}

        cart_items = []
        total = 0
        for did, qty in counter.items():
            dish = dishes_map.get(did)
            if not dish:
                continue
            sub = dish.price * qty
            total += sub
            cart_items.append({
                "dish": dish,
                "quantity": qty,
                "subtotal": sub,
            })

    if not cart_items:
        return RedirectResponse(url="/cart", status_code=302)

    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "cart_items": cart_items,
            "total": total,
            "is_authenticated": user is not None,
        },
    )


@router.post("/create")
async def create_order(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    address: str = Form(...),
    comment: str | None = Form(None),
):
    # Если нет пользователя — кидаем на регистрацию (твоя текущая логика)
    if not user:
        next_url = "/orders/checkout"
        return RedirectResponse(
            url=f"/auth/register?next={next_url}",
            status_code=status.HTTP_302_FOUND,
        )

    # Получаем товары из корзины пользователя
    cart_items_db = (
        db.query(CartItem)
        .options(joinedload(CartItem.dish))
        .filter(CartItem.user_id == user.id)
        .all()
    )

    if not cart_items_db:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    # Создаём заказ: теперь передаём address и comment
    order = Order(
        user_id=user.id,
        status="pending",
        address=address,          # <-- сохраняем адрес
        comment=comment,         # <-- сохраняем комментарий
        total_amount=0,           # посчитаем ниже
    )
    db.add(order)
    db.flush()  # чтобы получить order.id до commit

    total = 0
    for item in cart_items_db:
        if not item.dish:
            continue
        price_at_moment = item.dish.price
        subtotal = price_at_moment * item.quantity
        total += subtotal

        order_item = OrderItem(
            order_id=order.id,
            dish_id=item.dish.id,
            quantity=item.quantity,
            price=price_at_moment,
        )
        db.add(order_item)

    order.total_amount = total
    # Очищаем корзину пользователя
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()

    db.commit()

    return RedirectResponse(url=f"/orders/{order.id}", status_code=302)



@router.get("/{order_id}")
async def view_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.dish),
            joinedload(Order.user),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if not user or (order.user_id != user.id and not user.is_admin):
        raise HTTPException(status_code=403, detail="Нет доступа к этому заказу")

    total = sum(item.price * item.quantity for item in order.items)

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "total": total,
        },
    )
