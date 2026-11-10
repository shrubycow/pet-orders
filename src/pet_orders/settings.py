from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import EmailStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / '.env'


class Environment(StrEnum):
    local = 'local'
    development = 'development'
    production = 'production'
    test = 'test'


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str | None = None
    redis_url: str

    mail_username: str = ''
    mail_password: str = ''
    mail_from: EmailStr = 'noreply@example.com'
    mail_from_name: str = 'Pet Orders'
    mail_server: str = 'mailpit'
    mail_port: int = 1025
    mail_starttls: bool = False
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = False
    mail_validate_certs: bool = False

    environment: Environment = Environment.local

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        extra='ignore',
    )

    @model_validator(mode='after')
    def require_rabbitmq_url(self) -> Self:
        if self.environment is not Environment.test and not self.rabbitmq_url:
            raise ValueError('RABBITMQ_URL is required')
        return self


settings = Settings()
