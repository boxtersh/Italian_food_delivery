from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from routers.auth import router as auth_router
from routers.main import router as main_router

from routers.client import cart as client_cart
from routers.client import orders as client_orders
from routers.client import profile as client_profile

from routers.admin import orders as admin_orders
from routers.admin import crud_dishes as admin_dishes

from config import settings

app = FastAPI(
    title="Italian Food Delivery",
    description="Веб-приложение для онлайн-заказа блюд итальянской кухни",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    max_age=3600 * 24 * 7,
    https_only=False,
)


app.include_router(auth_router)
app.include_router(main_router)

app.include_router(client_cart.router)
app.include_router(client_orders.router)
app.include_router(client_profile.router)

app.include_router(admin_dishes.router)
app.include_router(admin_orders.router)