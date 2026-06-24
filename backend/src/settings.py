import os

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

CONTAINER_APP_HOSTNAME = os.getenv("CONTAINER_APP_HOSTNAME", "")


class Settings(BaseSettings):
    # App Identity - Keep in sync with docs/project.md
    client_name: str = "Workshop"
    project_name: str = "Invoice Intake"
    app_version: str = "v2"

    @property
    def display_name(self) -> str:
        """Combined display name: 'Project Name - Client Name'."""
        return f"{self.project_name} - {self.client_name}"

    @property
    def app_slug(self) -> str:
        """URL-safe slug for cache names and storage keys."""
        return (
            f"{self.client_name.lower()}-{self.project_name.lower().replace(' ', '-')}"
        )

    # Authentication
    api_key: SecretStr = SecretStr("apikey")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("postgres")
    postgres_sslmode: str = "disable"

    # Blob (local Azurite emulator; no real Azure account needed)
    azure_storage_account_key: str
    azure_storage_account_name: str
    azure_storage_connection_string: str

    # Cosmos (local Mongo-API container; no real Azure account needed)
    azure_cosmosdb_connection_string: str = ""
    # Database prefix for test isolation (automatically prefixed to all db names)
    cosmosdb_db_prefix: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore
