import pytest

from taskmanager.config import Settings
from taskmanager.exceptions import (
    ColumnNotFoundError,
    InvalidTableUpdateError,
    InvalidTaskModeError,
    TableNotFoundError,
)
from taskmanager.models import CellUpdate, RowMatrix
from taskmanager.services.task_service import TaskService


@pytest.fixture
def service(tmp_path):
    settings = Settings(data_dir=tmp_path)
    return TaskService(settings)


def test_table_mode_workflow(service):
    created = service.create_task("Migrate", "Move services", mode="table", initial_plan="Plan")
    task_id = created.task_id

    table = service.table_create(
        task_id,
        "services",
        columns=["status", "test", "notes"],
        rows=["users", "orders", "billing"],
        default_value="pending",
    )
    table_id = table.table_id

    service.table_set_cells(
        task_id,
        table_id,
        updates=[
            CellUpdate(row="users", values={"status": "done", "test": "pass"}),
        ],
    )
    service.table_set_cells(
        task_id,
        table_id,
        matrix=[
            RowMatrix(row="orders", values={"status": "done", "test": "pass", "notes": "ok"}),
        ],
    )

    detail = service.table_get(task_id, table_id)
    assert detail.cells["users"]["status"] == "done"
    assert detail.cells["orders"]["notes"] == "ok"
    assert detail.cells["billing"]["status"] == "pending"

    listed = service.table_list(task_id)
    assert len(listed.tables) == 1
    assert listed.tables[0].row_count == 3

    task_detail = service.get_task(task_id)
    assert task_detail.metadata.mode == "table"
    assert len(task_detail.tables) == 1
    assert task_detail.todos == []

    summaries = service.list_tasks()
    assert summaries[0].mode == "table"
    assert summaries[0].table_count == 1
    assert summaries[0].todo_total == 0


def test_mode_guards(service):
    todo_task = service.create_task("Todo task", "D", mode="todo")
    table_task = service.create_task("Table task", "D", mode="table")

    with pytest.raises(InvalidTaskModeError):
        service.add_todos(table_task.task_id, ["Step 1"])

    service.table_create(table_task.task_id, "tracker", columns=["a"])

    with pytest.raises(InvalidTaskModeError):
        service.table_create(todo_task.task_id, "t", columns=["a"])

    with pytest.raises(InvalidTableUpdateError):
        service.create_task("Bad", "D", mode="table", initial_todos=["nope"])


def test_table_errors(service):
    created = service.create_task("T", "D", mode="table")
    task_id = created.task_id
    table = service.table_create(task_id, "main", columns=["status"], rows=["a"])
    table_id = table.table_id

    with pytest.raises(TableNotFoundError):
        service.table_get(task_id, "tbl-deadbeef")

    with pytest.raises(ColumnNotFoundError):
        service.table_set_cells(
            task_id,
            table_id,
            updates=[CellUpdate(row="a", column="missing", value="x")],
        )
