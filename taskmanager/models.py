"""Pydantic models for API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskCreated(BaseModel):
    task_id: str
    task_path: str
    rough_path: str


class TaskMetadata(BaseModel):
    id: str
    name: str
    description: str
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
    status: str
    updated_at: str
    todo_done: int
    todo_total: int


class TaskDetail(BaseModel):
    metadata: TaskMetadata
    plan: str
    todos: list[TodoItem]
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
