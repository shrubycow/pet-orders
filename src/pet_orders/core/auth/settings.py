from pydantic_settings import BaseSettings, SettingsConfigDict

from pet_orders.settings import ENV_FILE_PATH


class AuthSettings(BaseSettings):
    secret_key: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        extra='ignore',
    )

auth_settings = AuthSettings()
