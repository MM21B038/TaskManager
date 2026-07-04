"""Path helpers for task storage."""

from pathlib import Path

from taskmanager.config import Settings


def task_path(settings: Settings, task_id: str) -> Path:
    return settings.task_dir / f"{task_id}.md"


def rough_path(settings: Settings, task_id: str) -> Path:
    return settings.rough_dir / f"{task_id}.md"


def table_path(settings: Settings, task_id: str) -> Path:
    return settings.table_dir / f"{task_id}.json"


def lock_path(file_path: Path) -> Path:
    return file_path.with_suffix(file_path.suffix + ".lock")
