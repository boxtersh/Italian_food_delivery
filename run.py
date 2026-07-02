from config import settings
import uvicorn
from app import app
from database import engine, Base

if __name__ == "__main__":
    try:
        print("1. Инициализация базы данных...")
        Base.metadata.create_all(bind=engine)
        print("2. База данных успешно инициализирована")
    except Exception as err:
        print(f"Ошибка при создании таблиц: {err}")
        raise
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)