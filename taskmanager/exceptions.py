"""Domain exceptions for task management."""


class TaskManagerError(Exception):
    """Base error for task manager operations."""


class TaskNotFoundError(TaskManagerError):
    """Raised when a task file does not exist."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class TodoNotFoundError(TaskManagerError):
    """Raised when a todo id is not found in a task."""

    def __init__(self, task_id: str, todo_id: str) -> None:
        self.task_id = task_id
        self.todo_id = todo_id
        super().__init__(f"Todo '{todo_id}' not found in task {task_id}")


class NoteNotFoundError(TaskManagerError):
    """Raised when a rough note id is not found."""

    def __init__(self, task_id: str, note_id: str) -> None:
        self.task_id = task_id
        self.note_id = note_id
        super().__init__(f"Note '{note_id}' not found in rough notes for task {task_id}")


class DuplicateNoteError(TaskManagerError):
    """Raised when adding a note with an id that already exists."""

    def __init__(self, task_id: str, note_id: str) -> None:
        self.task_id = task_id
        self.note_id = note_id
        super().__init__(f"Note '{note_id}' already exists for task {task_id}")
