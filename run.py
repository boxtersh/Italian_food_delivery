from config import settings
import uvicorn
from app import app
from database import engine, Base

if __name__ == "__main__":
    try:
        print("🔧 Инициализация базы данных...")
        Base.metadata.create_all(bind=engine)
        print("✅ База данных успешно инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)