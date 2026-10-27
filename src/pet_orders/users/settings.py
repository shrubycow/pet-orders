from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from pet_orders.settings import ENV_FILE_PATH


class UsersSettings(BaseSettings):
    user_created_code_ttl: int = 600

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        extra="ignore",
    )


users_settings = UsersSettings()
