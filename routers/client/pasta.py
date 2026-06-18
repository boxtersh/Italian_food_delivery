from models import DishCategory
from routers.client._factory import make_client_router

router = make_client_router(DishCategory.PASTA, "/pasta", "client: pasta")