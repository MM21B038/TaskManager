"""File-backed storage with locking."""

from pathlib import Path

from filelock import FileLock

from taskmanager.config import Settings
from taskmanager.documents.rough_doc import RoughDocument
from taskmanager.documents.task_doc import TaskDocument
from taskmanager.exceptions import TaskNotFoundError
from taskmanager.storage.paths import lock_path, rough_path, task_path


class TaskRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        settings.ensure_data_dirs()

    def exists(self, task_id: str) -> bool:
        return task_path(self._settings, task_id).is_file()

    def assert_exists(self, task_id: str) -> None:
        if not self.exists(task_id):
            raise TaskNotFoundError(task_id)

    def read_text(self, path: Path) -> str:
        with FileLock(lock_path(path), timeout=10):
            return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(lock_path(path), timeout=10):
            path.write_text(content, encoding="utf-8")

    def read_task_doc(self, task_id: str) -> TaskDocument:
        self.assert_exists(task_id)
        path = task_path(self._settings, task_id)
        return TaskDocument.parse(self.read_text(path))

    def write_task_doc(self, task_id: str, doc: TaskDocument) -> Path:
        path = task_path(self._settings, task_id)
        self.write_text(path, doc.serialize())
        return path

    def read_rough_doc(self, task_id: str) -> RoughDocument:
        self.assert_exists(task_id)
        path = rough_path(self._settings, task_id)
        if not path.is_file():
            raise TaskNotFoundError(task_id)
        return RoughDocument.parse(self.read_text(path))

    def write_rough_doc(self, task_id: str, doc: RoughDocument) -> Path:
        path = rough_path(self._settings, task_id)
        self.write_text(path, doc.serialize())
        return path

    def create_task_files(
        self,
        task_id: str,
        name: str,
        description: str,
        *,
        initial_plan: str = "",
        initial_todos: list[str] | None = None,
    ) -> tuple[Path, Path]:
        task_file = task_path(self._settings, task_id)
        rough_file = rough_path(self._settings, task_id)
        task_doc = TaskDocument.create_new(
            task_id,
            name,
            description,
            initial_plan=initial_plan,
            initial_todos=initial_todos,
        )
        rough_doc = RoughDocument.create_new(task_id)
        self.write_text(task_file, task_doc.serialize())
        try:
            self.write_text(rough_file, rough_doc.serialize())
        except OSError:
            if task_file.is_file():
                task_file.unlink(missing_ok=True)
            raise
        return task_file, rough_file

    def list_task_ids(self) -> list[str]:
        return sorted(p.stem for p in self._settings.task_dir.glob("*.md"))
