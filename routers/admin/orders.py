from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from routers.auth import get_current_admin
from config import templates
from database import get_db
from models import Order, Dish, OrderStatus

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

@router.get("/orders", response_class=HTMLResponse)
async def admin_panel_page(
    request: Request,
    db: Session = Depends(get_db),
    user: None = Depends(get_current_admin),  # админ должен быть авторизован
):
    active_statuses = [
        OrderStatus.PENDING.value,
        OrderStatus.CONFIRMED.value,
        OrderStatus.DELIVERING.value,
    ]
    archived_statuses = [
        OrderStatus.COMPLETED.value,
        OrderStatus.CANCELLED.value,
    ]

    # Получаем активные заказы
    stmt_active = (
        select(Order)
        .options(joinedload(Order.user))
        .where(Order.status.in_(active_statuses))
        .order_by(Order.created_at.desc())
    )
    result_active = db.execute(stmt_active)
    orders = result_active.scalars().all()

    # Получаем архивные заказы (ограничим, чтобы не грузить слишком много)
    stmt_archived = (
        select(Order)
        .options(joinedload(Order.user))
        .where(Order.status.in_(archived_statuses))
        .order_by(Order.created_at.desc())
        .limit(50)
    )
    result_archived = db.execute(stmt_archived)
    archived_orders = result_archived.scalars().all()

    # Считаем итоговую сумму для каждого заказа (чтобы не делать это в шаблоне)
    for order in orders + archived_orders:
        total = sum(item.price * item.quantity for item in order.items)
        order.total = total

    dishes = db.query(Dish).all()

    return templates.TemplateResponse(
        "admin_panel.html",
        {
            "request": request,
            "orders": orders,              # активные
            "archived_orders": archived_orders,  # архив
            "dishes": dishes,
        },
    )

@router.post("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str = Form(...),
    db: Session = Depends(get_db),
    user: None = Depends(get_current_admin),
):
    try:
        status_enum = OrderStatus(new_status)  # конвертируем строку в Enum
    except ValueError:
        raise HTTPException(status_code=400, detail="Недопустимый статус заказа")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.status = status_enum
    db.commit()

    return RedirectResponse(url="/admin/orders", status_code=303)
