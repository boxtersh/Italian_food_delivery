from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from models import DishCategory, OrderStatus


# ---------- Dish ----------

class DishBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    is_available: bool = True
    image_url: Optional[str] = None


class DishCreate(DishBase):
    # category задаём роутером принудительно
    pass


class DishUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    is_available: Optional[bool] = None
    image_url: Optional[str] = None


class DishOut(DishBase):
    id: int
    category: DishCategory

    model_config = ConfigDict(from_attributes=True)