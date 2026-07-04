import pytest

from taskmanager.config import Settings
from taskmanager.exceptions import InvalidTaskModeError, TodoNotFoundError
from taskmanager.models import ToolErrorResult
from taskmanager.services.task_service import TaskService
from taskmanager.tools._helpers import get_service, map_errors


@pytest.fixture(autouse=True)
def reset_service():
    import taskmanager.tools._helpers as helpers

    helpers._service = None
    yield
    helpers._service = None


@pytest.fixture
def service(tmp_path):
    settings = Settings(data_dir=tmp_path)
    svc = TaskService(settings)
    import taskmanager.tools._helpers as helpers

    helpers._service = svc
    return svc


def test_map_errors_returns_response_instead_of_raising(service):
    created = service.create_task("T", "D")
    task_id = created.task_id

    @map_errors
    def toggle_missing(task_id: str, todo_id: str):
        return get_service().toggle_todo(task_id, todo_id, completed=True)

    result = toggle_missing(task_id, "todo-missing")

    assert isinstance(result, ToolErrorResult)
    assert result.error_type == "TodoNotFoundError"
    assert "todo-missing" in result.error


def test_map_errors_passes_through_success(service):
    created = service.create_task("T", "D", initial_todos=["Step 1"])
    task_id = created.task_id
    todo_id = service.get_todos(task_id).todos[0].id

    @map_errors
    def toggle(task_id: str, todo_id: str):
        return get_service().toggle_todo(task_id, todo_id, completed=True)

    result = toggle(task_id, todo_id)

    assert result.completed is True


def test_map_errors_invalid_task_mode(service):
    created = service.create_task("T", "D", mode="table")

    @map_errors
    def add_todo(task_id: str):
        return get_service().add_todos(task_id, ["Step"])

    result = add_todo(created.task_id)

    assert isinstance(result, ToolErrorResult)
    assert result.error_type == "InvalidTaskModeError"
