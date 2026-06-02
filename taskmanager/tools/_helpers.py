"""Shared helpers for MCP tools."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastmcp.exceptions import ToolError

from taskmanager.exceptions import (
    DuplicateNoteError,
    NoteNotFoundError,
    TaskManagerError,
    TaskNotFoundError,
    TodoNotFoundError,
)
from taskmanager.services.task_service import TaskService

F = TypeVar("F", bound=Callable[..., Any])

_service: TaskService | None = None


def get_service() -> TaskService:
    global _service
    if _service is None:
        _service = TaskService()
    return _service


def map_errors(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except TaskNotFoundError as exc:
            raise ToolError(str(exc)) from exc
        except TodoNotFoundError as exc:
            raise ToolError(str(exc)) from exc
        except NoteNotFoundError as exc:
            raise ToolError(str(exc)) from exc
        except DuplicateNoteError as exc:
            raise ToolError(str(exc)) from exc
        except TaskManagerError as exc:
            raise ToolError(str(exc)) from exc

    return wrapper  # type: ignore[return-value]
