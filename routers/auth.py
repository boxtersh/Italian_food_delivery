from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import templates
from database import get_db
from models import CartItem, User
from schemas import UserCreate, UserResponse

import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _sanitize_next(next_value: str | None) -> str:
    if not next_value:
        return "/"
    if ".." in next_value or next_value.startswith("http://") or next_value.startswith("https://"):
        return "/"
    if not next_value.startswith("/"):
        return "/"
    return next_value


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не авторизован",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    return user


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user = get_current_user(request=request, db=db)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль администратора",
        )

    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        request.session.clear()
        return None

    return user


def _migrate_guest_cart_to_user(request: Request, db: Session, user_id: int) -> bool:
    guest_cart_cookie = request.cookies.get("guest_cart")
    if not guest_cart_cookie:
        return False

    try:
        guest_ids = json.loads(guest_cart_cookie)
    except Exception as e:
        print(f"Ошибка чтения guest_cart: {e}")
        return True

    if not isinstance(guest_ids, list) or not guest_ids:
        return True

    try:
        for raw_dish_id in guest_ids:
            try:
                dish_id = int(raw_dish_id)
            except (TypeError, ValueError):
                continue

            existing_item = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.dish_id == dish_id,
            ).first()

            if existing_item:
                existing_item.quantity += 1
            else:
                db.add(CartItem(user_id=user_id, dish_id=dish_id, quantity=1))

        db.commit()
    except Exception as e:
        print(f"Ошибка миграции корзины: {e}")
        db.rollback()

    return True


@router.get("/register")
async def show_register_page(request: Request, next: str = "/"):
    if request.session.get("user_id"):
        safe_next = _sanitize_next(next)
        return RedirectResponse(url=safe_next, status_code=302)

    safe_next = _sanitize_next(next)
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "next": safe_next,
            "errors": {},
            "values": {}
        },
    )


@router.post("/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    next_value = _sanitize_next(form.get("next"))

    try:
        user_data = UserCreate(
            email=form.get("email"),
            phone=form.get("phone"),
            password=form.get("password"),
            name=form.get("name"),
            password_confirm=form.get("password_confirm"),
        )
    except Exception as e:
        errors = {}
        if hasattr(e, "errors"):
            for err in e.errors():
                loc = err["loc"]
                msg = err["msg"]
                if loc:
                    field_name = loc[-1]
                    if field_name in ("__root__", "body", "form"):
                        if "general" not in errors:
                            errors["general"] = []
                        errors["general"].append(msg)
                    else:
                        errors[field_name] = msg


        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "next": next_value,
                "errors": errors,
                "values": form,
            },
            status_code=422,
        )

    existing_by_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_by_email:
        errors = {"email": "Пользователь с таким email уже существует"}
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "next": next_value,
                "errors": errors,
                "values": form,
            },
            status_code=400,
        )

    existing_by_phone = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_by_phone:
        errors = {"phone": "Пользователь с таким телефоном уже существует"}
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "next": next_value,
                "errors": errors,
                "values": form,
            },
            status_code=400,
        )

    final_name = user_data.name or "Маэстро"
    user = User(
        email=user_data.email,
        name=final_name,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id

    had_guest_cart = _migrate_guest_cart_to_user(request, db, user.id)

    response = RedirectResponse(url=next_value, status_code=status.HTTP_303_SEE_OTHER)

    if had_guest_cart:
        response.delete_cookie(key="guest_cart", path="/")

    return response


@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")

    email = None
    password = None
    next_value = "/"

    if "application/json" in content_type:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        next_value = _sanitize_next(data.get("next"))
    else:
        form = await request.form()
        email = form.get("email")
        password = form.get("password")
        next_value = _sanitize_next(form.get("next"))

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email и пароль обязательны",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    request.session["user_id"] = user.id
    had_guest_cart = _migrate_guest_cart_to_user(request, db, user.id)

    if "application/json" in content_type:
        response = JSONResponse(
            content={
                "message": "Вход выполнен успешно",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "is_admin": user.is_admin,
                },
                "redirect_to": next_value,
            }
        )
    else:
        response = RedirectResponse(url=next_value, status_code=status.HTTP_302_FOUND)

    if had_guest_cart:
        response.delete_cookie(key="guest_cart", path="/")

    return response


@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    response = JSONResponse(content={"detail": "Вы вышли из аккаунта"})
    response.delete_cookie(key="guest_cart", path="/")
    return response


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user