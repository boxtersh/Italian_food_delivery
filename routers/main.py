import json
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Dish, DishCategory, CartItem, User
from config import templates
from routers.auth import get_optional_user

router = APIRouter()


@router.get("/")
def index(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = select(Dish).where(Dish.is_available == True)
    results = db.execute(stmt).scalars().all()

    dishes_by_category = {cat.value: [] for cat in DishCategory}
    for dish in results:
        cat_name = dish.category.value
        if cat_name in dishes_by_category:
            dishes_by_category[cat_name].append(dish)

    cart_count = 0
    if current_user:
        cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
        cart_count = sum(item.quantity for item in cart_items)
    else:
        cart_json = request.cookies.get("guest_cart", "[]")
        try:
            guest_cart_ids = json.loads(cart_json)
            if isinstance(guest_cart_ids, list):
                cart_count = len(guest_cart_ids)
        except Exception:
            cart_count = 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dishes": dishes_by_category,
            "cart_count": cart_count,
            "current_user": current_user,
        },
    )


@router.post("/add-to-cart")
def add_to_cart(
    request: Request,
    dish_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    dish = db.scalar(
        select(Dish)
        .where(Dish.id == dish_id, Dish.is_available == True)
    )
    if not dish:
        return JSONResponse(
            status_code=404,
            content={"error": "Блюдо не найдено или недоступно"},
        )

    if current_user is not None:
        cart_item = db.scalar(
            select(CartItem).where(
                CartItem.user_id == current_user.id,
                CartItem.dish_id == dish.id,
            )
        )

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                dish_id=dish.id,
                quantity=1,
            )
            db.add(cart_item)

        db.commit()

        total_count = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
        cart_size = sum(item.quantity for item in total_count)

        return JSONResponse(
            content={
                "status": "added",
                "cart_size": cart_size,
                "method": "database",
            }
        )

    cart_json = request.cookies.get("guest_cart", "[]")
    try:
        guest_cart = json.loads(cart_json)
        if not isinstance(guest_cart, list):
            guest_cart = []
    except Exception:
        guest_cart = []

    guest_cart.append(dish_id)
    new_cart_json = json.dumps(guest_cart)

    resp = JSONResponse(
        content={
            "status": "added",
            "cart_size": len(guest_cart),
            "method": "cookie",
        }
    )
    resp.set_cookie(
        key="guest_cart",
        value=new_cart_json,
        max_age=604800,
        httponly=False,
        samesite="lax",
    )
    return resp


@router.get("/policy_confidence", response_class=HTMLResponse)
def policy_confidence(request: Request):
    return templates.TemplateResponse("policy_confidence.html", {"request": request})
