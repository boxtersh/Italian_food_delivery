from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Dish, DishCategory, User
from schemas import DishCreate, DishUpdate, DishOut
from routers.auth import get_current_admin

