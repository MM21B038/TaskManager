import re

import pytest
from pydantic import ValidationError

from taskmanager.config import Settings
from taskmanager.exceptions import (
    ColumnNotFoundError,
    DuplicateTableNameError,
    InvalidTableUpdateError,
    InvalidTaskModeError,
    RowNotFoundError,
    TableNotFoundError,
)
from taskmanager.models import CellUpdate, RowMatrix, SeedRow
from taskmanager.services.task_service import TaskService
from taskmanager.storage.paths import task_path


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


def test_seed_row_schema_and_duplicate_messages(service):
    schema = SeedRow.model_json_schema()
    assert "row" in schema["required"]
    assert schema["additionalProperties"] == {"type": "string"}
    assert "row" in (SeedRow.__doc__ or "")
    value_schema = CellUpdate.model_json_schema()["properties"]["value"]
    assert value_schema.get("type") == "string"
    assert "default" not in value_schema
    assert "anyOf" not in value_schema
    assert "string" in (CellUpdate.__doc__ or "")
    assert "row" in (RowMatrix.__doc__ or "")

    with pytest.raises(ValidationError, match="row"):
        SeedRow.model_validate({"status": "done"})
    seeded = SeedRow.model_validate({"row": "users", "status": "done"})
    assert seeded.model_dump()["status"] == "done"

    with pytest.raises(ValidationError, match="must be a string"):
        CellUpdate.model_validate({"row": "a", "column": "status", "value": None})
    blank = CellUpdate.model_validate({"row": "a", "column": "status", "value": ""})
    assert blank.value == ""

    created = service.create_task("T", "D", mode="table")
    task_id = created.task_id
    table = service.table_create(
        task_id,
        "services",
        columns=["status"],
        rows=["alpha"],
        initial_rows=[{"row": "alpha", "status": "done"}],
    )
    with pytest.raises(InvalidTableUpdateError, match="non-empty 'row' key"):
        service.table_create(
            task_id,
            "other",
            columns=["status"],
            initial_rows=[{"status": "done"}],
        )
    with pytest.raises(InvalidTableUpdateError, match="Row 'alpha' already exists in table 'services'"):
        service.table_add_rows(task_id, table.table_id, ["alpha"])
    with pytest.raises(InvalidTableUpdateError, match="Row 'beta' is duplicated"):
        service.table_add_rows(task_id, table.table_id, ["beta", "beta"])
    with pytest.raises(InvalidTableUpdateError, match="Column 'status' already exists in table 'services'"):
        service.table_add_columns(task_id, table.table_id, ["status"])
    with pytest.raises(InvalidTableUpdateError, match="Column 'notes' is duplicated"):
        service.table_add_columns(task_id, table.table_id, ["notes", "notes"])
    with pytest.raises(DuplicateTableNameError, match="services"):
        service.table_create(task_id, "services", columns=["status"])


def test_delete_remove_rename_and_slice(service):
    created = service.create_task("T", "D", mode="table")
    task_id = created.task_id
    first = service.table_create(
        task_id,
        "services",
        columns=["status", "notes"],
        rows=["alpha", "beta"],
        default_value="pending",
    )
    second = service.table_create(task_id, "other", columns=["status"], rows=["alpha"])
    table_id = first.table_id

    renamed = service.table_rename(task_id, table_id, "tracker")
    assert renamed.name == "tracker"
    row = service.table_rename_row(task_id, table_id, "alpha", "first")
    assert row.rows == ["first", "beta"]
    column = service.table_rename_column(task_id, table_id, "status", "state")
    assert column.columns == ["state", "notes"]

    service.table_set_cells(
        task_id,
        table_id,
        updates=[CellUpdate(row="first", column="state", value="done")],
    )
    detail = service.table_get(task_id, table_id, rows=["beta", "first"], columns=["state"])
    assert detail.rows == ["beta", "first"]
    assert detail.columns == ["state"]
    assert detail.cells["first"]["state"] == "done"
    assert "notes" not in detail.cells["first"]

    removed_rows = service.table_remove_rows(task_id, table_id, ["beta"])
    assert removed_rows.rows == ["first"]
    removed_columns = service.table_remove_columns(task_id, table_id, ["notes"])
    assert removed_columns.columns == ["state"]

    with pytest.raises(RowNotFoundError):
        service.table_remove_rows(task_id, table_id, ["missing"])
    with pytest.raises(DuplicateTableNameError):
        service.table_rename(task_id, table_id, "other")
    with pytest.raises(TableNotFoundError):
        service.table_delete(task_id, "tbl-missing")

    service.table_delete(task_id, second.table_id)
    listed = service.table_list(task_id)
    assert [item.table_id for item in listed.tables] == [table_id]


def test_updated_at_cell_counts_and_empty_writes(service):
    created = service.create_task("T", "D", mode="table", initial_plan="## Test plan\n\nSteps")
    task_id = created.task_id
    assert service.get_plan(task_id).plan == "## Test plan\n\nSteps"

    table = service.table_create(
        task_id,
        "services",
        columns=["status"],
        rows=["a", "b", "c", "d"],
    )
    path = task_path(service._settings, task_id)
    stale = "2000-01-01T00:00:00Z"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        re.sub(
            r"^updated_at:.*$",
            f'updated_at: "{stale}"',
            text,
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )

    with pytest.raises(InvalidTableUpdateError, match="non-empty"):
        service.table_set_cells(task_id, table.table_id, updates=[])
    assert service.get_task_metadata(task_id).updated_at == stale

    result = service.table_set_cells(
        task_id,
        table.table_id,
        updates=[CellUpdate(column="status", value="done")],
    )
    assert result.updated_count == 4
    assert result.op_count == 1
    assert service.get_task_metadata(task_id).updated_at != stale

    stored = service.table_set_cells(
        task_id,
        table.table_id,
        updates=[CellUpdate(row="a", column="status", value="")],
    )
    assert stored.updated_count == 1
    assert service.table_get(task_id, table.table_id).cells["a"]["status"] == ""
