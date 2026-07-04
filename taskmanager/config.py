"""Application settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TASK_MANAGER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=_PROJECT_ROOT)
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def task_dir(self) -> Path:
        return self.data_dir / "task"

    @property
    def rough_dir(self) -> Path:
        return self.data_dir / "rough"

    @property
    def table_dir(self) -> Path:
        return self.data_dir / "table"

    def ensure_data_dirs(self) -> None:
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.rough_dir.mkdir(parents=True, exist_ok=True)
        self.table_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
