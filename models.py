import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from database import Base


class DishCategory(str, enum.Enum):
    PIZZA = "pizza"
    PASTA = "pasta"
    SALAD = "salad"
    DESSERT = "dessert"
    DRINK = "drink"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"