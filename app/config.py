from pathlib import Path

from pydantic import HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    base_dir: Path = Path(__file__).parent  # app/

    postgres_url: PostgresDsn
    openai_api_key: str | None

    # optionals
    arbuz_api_base: HttpUrl = HttpUrl("https://arbuz.kz/api/v1/")

    def api(self, path: str):
        return str(self.arbuz_api_base) + path


settings = Settings()  # noqa
