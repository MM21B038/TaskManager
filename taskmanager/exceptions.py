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


class InvalidTaskModeError(TaskManagerError):
    """Raised when an operation is incompatible with the task mode."""

    def __init__(self, task_id: str, expected: str, actual: str) -> None:
        self.task_id = task_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Task {task_id} is in mode '{actual}', expected '{expected}'"
        )


class TableNotFoundError(TaskManagerError):
    """Raised when a table id is not found in a task."""

    def __init__(self, task_id: str, table_id: str) -> None:
        self.task_id = task_id
        self.table_id = table_id
        super().__init__(f"Table '{table_id}' not found in task {task_id}")


class RowNotFoundError(TaskManagerError):
    """Raised when a row key is not found in a table."""

    def __init__(self, task_id: str, table_id: str, row: str) -> None:
        self.task_id = task_id
        self.table_id = table_id
        self.row = row
        super().__init__(
            f"Row '{row}' not found in table '{table_id}' for task {task_id}"
        )


class ColumnNotFoundError(TaskManagerError):
    """Raised when a column name is not found in a table."""

    def __init__(self, task_id: str, table_id: str, column: str) -> None:
        self.task_id = task_id
        self.table_id = table_id
        self.column = column
        super().__init__(
            f"Column '{column}' not found in table '{table_id}' for task {task_id}"
        )


class DuplicateTableNameError(TaskManagerError):
    """Raised when creating a table with a name that already exists."""

    def __init__(self, task_id: str, name: str) -> None:
        self.task_id = task_id
        self.name = name
        super().__init__(f"Table '{name}' already exists for task {task_id}")


class InvalidTableUpdateError(TaskManagerError):
    """Raised when a table update payload is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
