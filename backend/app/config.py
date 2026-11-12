from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "demo", "prod"] = "local"
    database_url: str
    cors_origins: list[str] = []
    auth_mode: Literal["cognito", "dev"] = "cognito"
    cognito_issuer: str = ""
    cognito_client_id: str = ""
    bills_bucket: str
    s3_endpoint_url: str | None = None
    business_name: str
    business_address: str
    log_level: str = "INFO"