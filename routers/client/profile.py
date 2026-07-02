from fastapi import APIRouter, Request, Depends, status, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from routers.auth import get_optional_user
from config import templates
from database import get_db
from models import Order, User


router = APIRouter(prefix="/client", tags=["Client Profile"])


@router.get("/profile", response_class=HTMLResponse)
async def client_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: None | object = Depends(get_optional_user),
):
    # Если гость — редирект на /login с подсказкой, куда вернуть после входа
    if not current_user:
        return RedirectResponse(
            url="/login?next=/client/profile",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # Получаем заказы текущего пользователя
    # selectinload(Order.items) нужен, чтобы items гарантированно были доступны в шаблоне
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = db.execute(stmt).scalars().all()

    # Считаем сумму заказа на бэкенде
    for order in orders:
        total = sum(item.price * item.quantity for item in order.items)
        order.total = total  # динамическое поле для шаблона

    # Статусы можно подстроить под твою модель
    active_statuses = {"pending", "confirmed", "delivering"}
    archive_statuses = {"completed", "cancelled"}

    active_orders = []
    archive_orders = []

    for order in orders:
        status_value = getattr(order.status, "value", order.status)
        status_value = str(status_value).lower() if status_value is not None else ""

        if status_value in archive_statuses:
            archive_orders.append(order)
        else:
            # Всё остальное считаем активным, чтобы ничего не потерять
            active_orders.append(order)

    return templates.TemplateResponse(
        "client_profile.html",
        {
            "request": request,
            "current_user": current_user,
            "orders": orders,  # оставил для совместимости
            "active_orders": active_orders,
            "archive_orders": archive_orders,
        },
    )

@router.post("/profile/update")
async def update_profile(
    user_id: int = Form(...),
    name: str | None = Form(None),
    phone: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: None | object = Depends(get_optional_user),
):
    # Защита: можно менять только свой профиль
    if not current_user or current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if name is not None:
        user.name = name.strip()

    if phone is not None:
        normalized_phone = phone.strip()

        existing_user = (
            db.query(User)
            .filter(User.phone == normalized_phone, User.id != user_id)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким номером телефона уже существует",
            )

        user.phone = normalized_phone

    db.commit()

    # После сохранения всегда возвращаем на профиль, чтобы увидеть изменения
    return RedirectResponse(url="/client/profile", status_code=303)
