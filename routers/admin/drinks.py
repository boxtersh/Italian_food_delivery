from models import DishCategory
from routers.admin._factory import make_admin_router

router = make_admin_router(DishCategory.DRINK, "/admin/drinks", "admin: drinks")