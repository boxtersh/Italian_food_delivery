from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware
from collections import Counter
import json



from routers.auth import router as auth_router
from routers.client import pizzas as client_pizzas
from routers.client import pasta as client_pasta
from routers.client import salads as client_salads
from routers.client import desserts as client_desserts
from routers.client import drinks as client_drinks
from routers.client import cart as client_cart
from routers.client import orders as client_orders
from routers.admin import pizzas as admin_pizzas
from routers.admin import pasta as admin_pasta
from routers.admin import salads as admin_salads
from routers.admin import desserts as admin_desserts
from routers.admin import drinks as admin_drinks
from routers.admin import orders as admin_orders

from database import get_db
from models import Dish, DishCategory, CartItem, User
from config import settings

app = FastAPI(
    title="Italian Food Delivery",
    description="Веб-приложение для онлайн-заказа блюд итальянской кухни",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates", auto_reload=True)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    max_age=3600 * 24 * 7,
)

app.include_router(auth_router)
app.include_router(client_pizzas.router)
app.include_router(client_pasta.router)
app.include_router(client_salads.router)
app.include_router(client_desserts.router)
app.include_router(client_drinks.router)
app.include_router(client_cart.router)
app.include_router(client_orders.router)
app.include_router(admin_pizzas.router)
app.include_router(admin_pasta.router)
app.include_router(admin_salads.router)
app.include_router(admin_desserts.router)
app.include_router(admin_drinks.router)
app.include_router(admin_orders.router)


def get_guest_cart_summary(dish_ids: list, db: Session):
    if not dish_ids:
        return [], 0.0

    counts = Counter(dish_ids)
    unique_ids = list(counts.keys())
    dishes_map = {d.id: d for d in db.query(Dish).filter(Dish.id.in_(unique_ids)).all()}
    cart_items = []
    total_amount = 0.0

    for dish_id, qty in counts.items():
        dish = dishes_map.get(dish_id)
        if dish:
            subtotal = float(dish.price) * qty
            total_amount += subtotal
            cart_items.append({
                "dish": dish,
                "quantity": qty,
                "subtotal": subtotal
            })

    return cart_items, round(total_amount, 2)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    stmt = select(Dish).where(Dish.is_available == True)
    results = db.execute(stmt).scalars().all()

    dishes_by_category = {cat.value: [] for cat in DishCategory}
    for dish in results:
        cat_name = dish.category.value
        if cat_name in dishes_by_category:
            dishes_by_category[cat_name].append(dish)

    current_user = None
    user_id = request.session.get("user_id")
    if user_id:
        current_user = db.query(User).filter(User.id == user_id).first()

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

    return templates.TemplateResponse("index.html", {
        "request": request,
        "dishes": dishes_by_category,
        "cart_count": cart_count,
        "current_user": current_user
    })


@app.post("/add-to-cart")
async def add_to_cart(
        request: Request,
        response: Response,
        dish_id: int = Form(...),
        db: Session = Depends(get_db)
):
    dish = db.query(Dish).filter(
        Dish.id == dish_id,
        Dish.is_available == True
    ).first()

    if not dish:
        return JSONResponse(status_code=404, content={"error": "Блюдо не найдено или недоступно"})

    user_id = request.session.get("user_id")

    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            request.session.pop("user_id", None)
            return JSONResponse(status_code=401, content={"error": "Сессия истекла"})

        cart_item = db.query(CartItem).filter(
            CartItem.user_id == user.id,
            CartItem.dish_id == dish.id
        ).first()

        if cart_item:
            cart_item.quantity += 1
        else:
            new_item = CartItem(user_id=user.id, dish_id=dish.id, quantity=1)
            db.add(new_item)

        db.commit()

        total_count = db.query(CartItem).filter(CartItem.user_id == user.id).count()

        return JSONResponse(content={
            "status": "added",
            "cart_size": total_count,
            "method": "database"
        })

    else:
        cart_json = request.cookies.get("guest_cart", "[]")
        try:
            cart_ids = json.loads(cart_json)
            if not isinstance(cart_ids, list):
                cart_ids = []
        except Exception:
            cart_ids = []

        cart_ids.append(dish_id)
        new_cart_json = json.dumps(cart_ids)

        resp = JSONResponse(content={"status": "added", "cart_size": len(cart_ids), "method": "cookie"})

        resp.set_cookie(
            key="guest_cart",
            value=new_cart_json,
            max_age=604800,
            httponly=False,
            samesite="lax"
        )
        return resp


@app.get("/cart", response_class=HTMLResponse)
async def view_cart_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    items = []
    total = 0.0
    count = 0

    if user_id:
        user_cart = db.query(CartItem).filter(CartItem.user_id == user_id).all()

        if user_cart:
            dish_ids = [item.dish_id for item in user_cart]
            dishes_map = {d.id: d for d in db.query(Dish).filter(Dish.id.in_(dish_ids)).all()}

            for item in user_cart:
                dish = dishes_map.get(item.dish_id)
                if dish:
                    subtotal = float(dish.price) * item.quantity
                    total += subtotal
                    items.append({
                        "dish": dish,
                        "quantity": item.quantity,
                        "subtotal": round(subtotal, 2),
                        "cart_item_id": item.id
                    })
                    count += item.quantity
    else:
        cart_json = request.cookies.get("guest_cart", "[]")
        try:
            guest_ids = json.loads(cart_json)
            if isinstance(guest_ids, list):
                items, total = get_guest_cart_summary(guest_ids, db)
                count = sum(i["quantity"] for i in items)
        except Exception as e:
            print(f"Ошибка чтения корзины гостя: {e}")

    return templates.TemplateResponse("cart.html", {
        "request": request,
        "items": items,
        "total": total,
        "count": count,
        "is_authenticated": user_id is not None
    })


@app.get("/policy_confidence", response_class=HTMLResponse)
def policy_confidence(request: Request):
    return templates.TemplateResponse("policy_confidence.html", {"request": request})