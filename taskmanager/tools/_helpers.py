"""Shared helpers for MCP tools."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from taskmanager.exceptions import TaskManagerError
from taskmanager.models import ToolErrorResult
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
        except TaskManagerError as exc:
            return ToolErrorResult(
                error=str(exc),
                error_type=type(exc).__name__,
            )

    return wrapper  # type: ignore[return-value]
