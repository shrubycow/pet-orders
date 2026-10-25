from enum import Enum
from pathlib import Path

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Environment(str, Enum):
    local = "local"
    development = "development"
    production = "production"

class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    redis_url: str

    mail_username: str = ""
    mail_password: str = ""
    mail_from: EmailStr = "noreply@example.com"
    mail_from_name: str = "Pet Orders"
    mail_server: str = "mailpit"
    mail_port: int = 1025
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = False
    mail_validate_certs: bool = False

    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )


settings = Settings()
