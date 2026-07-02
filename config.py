from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.templating import Jinja2Templates


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int
    base_url: str
    server_host: str = "127.0.0.1"
    server_port: int
    static_upload_path: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
templates = Jinja2Templates(directory="templates", auto_reload=True)