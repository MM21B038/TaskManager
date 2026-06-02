import pytest

from taskmanager.config import Settings
from taskmanager.exceptions import NoteNotFoundError, TodoNotFoundError
from taskmanager.services.task_service import TaskService


@pytest.fixture
def service(tmp_path):
    settings = Settings(data_dir=tmp_path)
    return TaskService(settings)


def test_full_workflow(service):
    created = service.create_task(
        "Auth",
        "JWT login",
        initial_plan="Plan A",
        initial_todos=["Step 1", "Step 2"],
    )
    task_id = created.task_id

    plan = service.get_plan(task_id)
    assert plan.plan == "Plan A"

    todos = service.get_todos(task_id)
    assert len(todos.todos) == 2
    todo_id = todos.todos[0].id
    service.toggle_todo(task_id, todo_id, completed=True)

    service.rough_add(task_id, "scratch idea")
    notes = service.rough_list(task_id)
    assert len(notes.notes) == 1

    service.set_report(task_id, "All done.")
    detail = service.get_task(task_id)
    assert detail.report == "All done."
    assert detail.todos[0].completed is True

    summaries = service.list_tasks()
    assert len(summaries) == 1
    assert summaries[0].todo_done == 1


def test_not_found_errors(service):
    service.create_task("T", "D")
    task_id = service.list_tasks()[0].id
    with pytest.raises(TodoNotFoundError):
        service.toggle_todo(task_id, "todo-deadbeef", completed=True)
    with pytest.raises(NoteNotFoundError):
        service.rough_get(task_id, "note-missing")
