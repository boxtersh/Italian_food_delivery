from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator
import re

from models import DishCategory, OrderStatus


# ---------- Dish ----------

class DishBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    is_available: bool = True
    image_url: Optional[str] = '/static/images/placeholders/no_photo.webp'


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


# ---------- Cart ----------

class CartItemCreate(BaseModel):
    dish_id: int
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemOut(BaseModel):
    id: int
    dish: DishOut
    quantity: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Order ----------

class OrderItemOut(BaseModel):
    id: int
    dish: DishOut
    quantity: int
    price: Decimal  # цена за единицу на момент заказа

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemOut]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def total(self) -> Decimal:
        return sum((item.price * item.quantity for item in self.items), Decimal("0"))


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ---------- Auth / User ----------

class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None
    phone: str | None = None
    password: str = Field(..., min_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = re.sub(r"[^\d+]", "", v)
        match_plus7 = re.fullmatch(r"\+7\d{10}", cleaned)
        match_8 = re.fullmatch(r"8\d{10}", cleaned)

        if match_plus7:
            return cleaned
        elif match_8:
            return "+7" + cleaned[1:]
        else:
            raise ValueError("Номер телефона должен состоять из 11 цифр и начинаться на +7 или 8")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
