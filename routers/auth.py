from datetime import datetime, timedelta, timezone
from typing import Optional

import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import CartItem, User
from schemas import Token, UserCreate, UserResponse


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _extract_token_from_request(request: Request, bearer_token: Optional[str]) -> Optional[str]:
    if bearer_token:
        return bearer_token

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    actual_token = _extract_token_from_request(request, token)
    if not actual_token:
        raise credentials_exception

    try:
        payload = jwt.decode(actual_token, settings.secret_key, algorithms=settings.algorithm)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_admin(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = get_current_user(request=request, token=token, db=db)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль администратора",
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user_by_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    existing_user_by_phone = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user_by_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким телефоном уже существует"
        )

    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    guest_cart_cookie = request.cookies.get("guest_cart")
    if guest_cart_cookie:
        try:
            guest_ids = json.loads(guest_cart_cookie)
            if isinstance(guest_ids, list) and guest_ids:
                for gid in guest_ids:
                    existing_item = db.query(CartItem).filter(
                        CartItem.user_id == user.id,
                        CartItem.dish_id == gid,
                    ).first()

                    if existing_item:
                        existing_item.quantity += 1
                    else:
                        db.add(CartItem(user_id=user.id, dish_id=gid, quantity=1))

                db.commit()
                response.delete_cookie(key="guest_cart", path="/")
        except Exception as e:
            print(f"Ошибка миграции корзины: {e}")
            db.rollback()

    token = create_access_token({"sub": str(user.id)})
    request.session["user_id"] = user.id

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )

    return Token(access_token=token)


@router.post("/logout")
def logout(request: Request, response: Response):
    request.session.pop("user_id", None)
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "Вы вышли из аккаунта"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user