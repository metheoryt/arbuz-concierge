from pathlib import Path

from pydantic import HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).parent.parent  # app/

    # configurable
    database_url: PostgresDsn = PostgresDsn("postgresql+psycopg://postgres:postgres@localhost/postgres")
    arbuz_api_base: HttpUrl = HttpUrl("https://arbuz.kz/api/v1/")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def api(self, path: str):
        return str(self.arbuz_api_base) + path


settings = Settings()  # noqa
