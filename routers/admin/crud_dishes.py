from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Dish
from config import settings

UPLOAD_DIR = Path(settings.static_upload_path)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


router = APIRouter(prefix="/admin/dishes", tags=["Admin: Dishes CRUD"])

@router.post("/create")
async def create_dish(
    name: str = Form(...),
    description: str | None = Form(None),
    price: float = Form(...),
    category: str = Form(...),
    image_url: str | None = Form(None),
    db: Session = Depends(get_db),
):

    final_image_url = image_url if image_url else "/static/images/placeholders/no_photo.webp"

    new_dish = Dish(
        name=name,
        description=description,
        price=price,
        category=category,
        image_url=final_image_url,
        is_available=True,
    )
    db.add(new_dish)
    db.commit()
    db.refresh(new_dish)

    return RedirectResponse(url="/admin/?msg=create", status_code=303)

@router.post("/update")
async def update_dish(
    dish_id: int = Form(...),
    name: str | None = Form(None),
    price_raw: str | None = Form(None),
    description: str | None = Form(None),
    image_url: str | None = Form(None),
    is_available_raw: str | None = Form(None),  # <-- именно это имя, как в HTML
    db: Session = Depends(get_db)
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    if name is not None:
        dish.name = name

    if price_raw is not None and price_raw.strip() != "":
        try:
            dish.price = float(price_raw)
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректная цена")

    if description is not None:
        dish.description = description

    if image_url is not None and image_url.strip() != "":
        dish.image_url = image_url

    if is_available_raw is not None:
        dish.is_available = (is_available_raw.lower() == "true")
    else:
        dish.is_available = False

    db.commit()
    return RedirectResponse(url="/admin/?msg=update", status_code=303)


@router.post("/upload")
async def upload_dish_image(
    dish_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Проверяем, что блюдо существует
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    # Проверка расширения
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат. Разрешены: {', '.join(allowed_extensions)}"
        )

    # Уникальное имя, чтобы не было дублей
    new_filename = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / new_filename

    # Сохраняем файл на диск
    try:
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {e}")

    # ВАЖНО: пишем в базу именно тот путь, который у тебя сейчас работает:
    dish.image_url = f"/static/images/uploads/{new_filename}"
    db.commit()

    return RedirectResponse(url="/admin/?msg=upload", status_code=303)


@router.post("/delete")
async def delete_dish(
    dish_id: int = Form(...),
    db: Session = Depends(get_db),
):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    dish.is_available = False  # мягкое удаление
    db.commit()
    return RedirectResponse(url="/admin/?msg=deleted", status_code=303)