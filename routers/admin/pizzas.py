from models import DishCategory
from routers.admin._factory import make_admin_router

router = make_admin_router(DishCategory.PIZZA, "/admin/pizzas", "admin: pizzas")