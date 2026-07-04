"""Pydantic models for API responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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


class CellUpdate(BaseModel):
    row: str | None = None
    column: str | None = None
    value: str | None = None
    values: dict[str, str] | None = None


class RowMatrix(BaseModel):
    row: str
    values: dict[str, str]


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
