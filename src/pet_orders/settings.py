from enum import StrEnum
from pathlib import Path

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / '.env'


class Environment(StrEnum):
    local = 'local'
    development = 'development'
    production = 'production'
    test = 'test'


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
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


settings = Settings()
