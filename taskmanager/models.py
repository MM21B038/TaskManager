"""Pydantic models for API responses."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema, model_validator


TaskMode = Literal["todo", "table"]


class TaskCreated(BaseModel):
    task_id: str
    task_path: str
    rough_path: str


class TaskMetadata(BaseModel):
    id: str
    name: str
    description: str
    mode: TaskMode = "todo"
    status: str
    created_at: str
    updated_at: str


class TodoItem(BaseModel):
    id: str
    text: str
    completed: bool


class NoteItem(BaseModel):
    note_id: str
    created: str
    updated: str
    content: str


class NotePreview(BaseModel):
    note_id: str
    created: str
    updated: str
    preview: str


class TaskSummary(BaseModel):
    id: str
    name: str
    mode: TaskMode = "todo"
    status: str
    updated_at: str
    todo_done: int
    todo_total: int
    table_count: int = 0


class TaskDetail(BaseModel):
    metadata: TaskMetadata
    plan: str
    todos: list[TodoItem] = Field(default_factory=list)
    tables: list[TableSummary] = Field(default_factory=list)
    report: str


class AddedTodo(BaseModel):
    id: str
    text: str


class AddTodosResult(BaseModel):
    todos: list[AddedTodo]


class PlanResult(BaseModel):
    task_id: str
    plan: str


class ReportResult(BaseModel):
    task_id: str
    report: str


class TodosResult(BaseModel):
    task_id: str
    todos: list[TodoItem]


class NoteResult(BaseModel):
    task_id: str
    note: NoteItem


class NotesListResult(BaseModel):
    task_id: str
    notes: list[NotePreview] = Field(default_factory=list)


class RoughClearResult(BaseModel):
    task_id: str
    removed_count: int


class ToolErrorResult(BaseModel):
    error: str
    error_type: str


_NULL_VALUE_ERROR = "value must be a string; pass an empty string to store a blank cell"

_CELL_VALUE_SCHEMA = {
    "type": "string",
    "description": (
        "Cell value as a string. Null is rejected; pass an empty string to store a blank cell."
    ),
}


class SeedRow(BaseModel):
    """One seeded row. `row` is required; every other key is a column name mapped to a string cell value.

    Example: {"row": "users", "status": "done"}.
    """

    model_config = ConfigDict(extra="allow")

    row: str = Field(
        description=(
            "Row key. Additional properties are column names mapped to string cell values, "
            'for example {"row": "users", "status": "done"}.'
        )
    )

    @model_validator(mode="before")
    @classmethod
    def _require_row_and_string_cells(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("entries must include a non-empty 'row' key")
        row = data.get("row")
        if not isinstance(row, str) or not row.strip():
            raise ValueError("entries must include a non-empty 'row' key")
        for key, raw in data.items():
            if key == "row":
                continue
            if not isinstance(key, str):
                raise ValueError("column names must be non-empty strings")
            if not isinstance(raw, str):
                raise ValueError(_NULL_VALUE_ERROR)
        return data

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):  # type: ignore[no-untyped-def]
        schema = handler(core_schema)
        schema["additionalProperties"] = {"type": "string"}
        return schema


class CellUpdate(BaseModel):
    """One cell update. Use exactly one shape.

    - Single cell: row, column, and value
    - Partial row: row and values (column name to string; omitted columns stay unchanged)
    - Fill row: row and value (same string for every column in that row)
    - Fill column: column and value (same string for every row in that column)

    value is a string. Null is rejected; pass an empty string to store a blank cell.
    """

    row: str | None = Field(default=None, description="Row key, when the update targets a row.")
    column: str | None = Field(
        default=None, description="Column name, when the update targets one column."
    )
    value: Annotated[str | None, WithJsonSchema(_CELL_VALUE_SCHEMA)] = None
    values: dict[str, str] | None = Field(
        default=None,
        description="Column name to string cell value. Used for a partial-row update.",
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_null_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "value" in data and data["value"] is None:
            raise ValueError(_NULL_VALUE_ERROR)
        raw_values = data.get("values")
        if isinstance(raw_values, dict):
            for raw in raw_values.values():
                if not isinstance(raw, str):
                    raise ValueError(_NULL_VALUE_ERROR)
        return data

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):  # type: ignore[no-untyped-def]
        schema = handler(core_schema)
        value_schema = schema.get("properties", {}).get("value")
        if isinstance(value_schema, dict):
            value_schema.pop("default", None)
        return schema


class RowMatrix(BaseModel):
    """One matrix row. `row` is required. Omitted columns stay unchanged."""

    row: str = Field(description="Row key.")
    values: dict[str, str] = Field(
        description="Column name to string cell value. Every value must be a string."
    )


class TableSummary(BaseModel):
    table_id: str
    name: str
    row_count: int
    column_count: int


class TableCreated(BaseModel):
    task_id: str
    table_id: str
    name: str
    columns: list[str]
    rows: list[str]
    default: str
    cell_count: int


class TableDetail(BaseModel):
    task_id: str
    table_id: str
    name: str
    columns: list[str]
    rows: list[str]
    default: str
    cells: dict[str, dict[str, str]]


class TableListResult(BaseModel):
    task_id: str
    tables: list[TableSummary]


class TableRowsAdded(BaseModel):
    task_id: str
    table_id: str
    rows: list[str]
    row_count: int


class TableColumnsAdded(BaseModel):
    task_id: str
    table_id: str
    columns: list[str]
    column_count: int


class TableCellsUpdated(BaseModel):
    task_id: str
    table_id: str
    updated_count: int
    op_count: int


class TableDeleted(BaseModel):
    task_id: str
    table_id: str


class TableRowsRemoved(BaseModel):
    task_id: str
    table_id: str
    rows: list[str]
    row_count: int


class TableColumnsRemoved(BaseModel):
    task_id: str
    table_id: str
    columns: list[str]
    column_count: int


class TableRenamed(BaseModel):
    task_id: str
    table_id: str
    name: str


class TableRowRenamed(BaseModel):
    task_id: str
    table_id: str
    row: str
    rows: list[str]


class TableColumnRenamed(BaseModel):
    task_id: str
    table_id: str
    column: str
    columns: list[str]
