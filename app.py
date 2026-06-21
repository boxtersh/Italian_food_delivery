from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

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
from models import Dish, DishCategory

app = FastAPI(
    title="Italian Food Delivery",
    description="Веб-приложение для онлайн-заказа блюд итальянской кухни",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Авторизация
app.include_router(auth_router)

# Клиентская часть
app.include_router(client_pizzas.router)
app.include_router(client_pasta.router)
app.include_router(client_salads.router)
app.include_router(client_desserts.router)
app.include_router(client_drinks.router)
app.include_router(client_cart.router)
app.include_router(client_orders.router)

# Администраторская часть
app.include_router(admin_pizzas.router)
app.include_router(admin_pasta.router)
app.include_router(admin_salads.router)
app.include_router(admin_desserts.router)
app.include_router(admin_drinks.router)
app.include_router(admin_orders.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    stmt = select(Dish).where(Dish.is_available == True)
    results = db.execute(stmt).scalars().all()
    dishes_by_category = {cat.value: [] for cat in DishCategory}

    for dish in results:
        cat_name = dish.category.value
        if cat_name in dishes_by_category:
            dishes_by_category[cat_name].append(dish)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dishes": dishes_by_category
    })


@app.get("/policy_confidence", response_class=HTMLResponse)
def policy_confidence(request: Request):
    return templates.TemplateResponse("policy_confidence.html", {"request": request})