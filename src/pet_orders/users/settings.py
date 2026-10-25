from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class UsersSettings(BaseSettings):
    user_created_code_ttl: int = 600

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
    )


users_settings = UsersSettings()
