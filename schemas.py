from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator
import re

from models import DishCategory, OrderStatus


class DishBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    is_available: bool = True
    image_url: Optional[str] = '/static/images/placeholders/no_photo.webp'


class DishCreate(DishBase):
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


class OrderItemOut(BaseModel):
    id: int
    dish: DishOut
    quantity: int
    price: Decimal

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


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        value = v.strip()

        if value.startswith("+7"):
            digits = re.sub(r"\D", "", value)
            if len(digits) != 11 or not digits.startswith("7"):
                raise ValueError("Телефон должен начинаться на 8 или +7 и содержать 11 цифр")
            return "+" + digits

        if value.startswith("8"):
            digits = re.sub(r"\D", "", value)
            if len(digits) != 11 or not digits.startswith("8"):
                raise ValueError("Телефон должен начинаться на 8 или +7 и содержать 11 цифр")
            return digits

        raise ValueError("Телефон должен начинаться на 8 или +7 и содержать 11 цифр")


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckoutForm(BaseModel):
    address: str = Field(..., min_length=5, max_length=255)
    comment: Optional[str] = Field(None, max_length=500)
