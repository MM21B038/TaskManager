"""Task management business logic."""

from __future__ import annotations

import uuid

from taskmanager.config import Settings
from taskmanager.documents.rough_doc import NoteBlock
from taskmanager.documents.task_doc import TaskDocument, TodoLine
from taskmanager.exceptions import (
    DuplicateNoteError,
    NoteNotFoundError,
    TaskNotFoundError,
    TodoNotFoundError,
)
from taskmanager.models import (
    AddTodosResult,
    AddedTodo,
    NoteItem,
    NotePreview,
    NoteResult,
    NotesListResult,
    PlanResult,
    ReportResult,
    RoughClearResult,
    TaskCreated,
    TaskDetail,
    TaskMetadata,
    TaskSummary,
    TodoItem,
    TodosResult,
)
from taskmanager.storage.repository import TaskRepository


class TaskService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._repo = TaskRepository(self._settings)

    def create_task(
        self,
        name: str,
        description: str,
        *,
        initial_plan: str = "",
        initial_todos: list[str] | None = None,
    ) -> TaskCreated:
        task_id = str(uuid.uuid4())
        task_file, rough_file = self._repo.create_task_files(
            task_id,
            name,
            description,
            initial_plan=initial_plan,
            initial_todos=initial_todos,
        )
        return TaskCreated(
            task_id=task_id,
            task_path=str(task_file),
            rough_path=str(rough_file),
        )

    def get_task(self, task_id: str) -> TaskDetail:
        doc = self._repo.read_task_doc(task_id)
        return TaskDetail(
            metadata=_metadata_from_doc(doc),
            plan=doc.get_plan(),
            todos=_todos_from_doc(doc),
            report=doc.get_report(),
        )

    def get_task_metadata(self, task_id: str) -> TaskMetadata:
        doc = self._repo.read_task_doc(task_id)
        return _metadata_from_doc(doc)

    def list_tasks(self) -> list[TaskSummary]:
        summaries: list[TaskSummary] = []
        for task_id in self._repo.list_task_ids():
            try:
                doc = self._repo.read_task_doc(task_id)
            except TaskNotFoundError:
                continue
            todos = doc.parse_todos()
            summaries.append(
                TaskSummary(
                    id=doc.metadata.get("id", task_id),
                    name=doc.metadata.get("name", ""),
                    status=doc.metadata.get("status", "active"),
                    updated_at=doc.metadata.get("updated_at", ""),
                    todo_done=sum(1 for t in todos if t.completed),
                    todo_total=len(todos),
                )
            )
        return summaries

    def set_plan(self, task_id: str, plan: str) -> PlanResult:
        doc = self._repo.read_task_doc(task_id)
        doc.set_plan(plan)
        self._repo.write_task_doc(task_id, doc)
        return PlanResult(task_id=task_id, plan=doc.get_plan())

    def get_plan(self, task_id: str) -> PlanResult:
        doc = self._repo.read_task_doc(task_id)
        return PlanResult(task_id=task_id, plan=doc.get_plan())

    def add_todos(self, task_id: str, items: list[str]) -> AddTodosResult:
        doc = self._repo.read_task_doc(task_id)
        created = doc.add_todos(items)
        self._repo.write_task_doc(task_id, doc)
        return AddTodosResult(
            todos=[AddedTodo(id=t.id, text=t.text) for t in created],
        )

    def toggle_todo(
        self, task_id: str, todo_id: str, completed: bool | None = None
    ) -> TodoItem:
        doc = self._repo.read_task_doc(task_id)
        try:
            todo = doc.toggle_todo(todo_id, completed=completed)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)
        return _todo_item(todo)

    def update_todo(self, task_id: str, todo_id: str, text: str) -> TodoItem:
        doc = self._repo.read_task_doc(task_id)
        try:
            todo = doc.update_todo(todo_id, text)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)
        return _todo_item(todo)

    def remove_todo(self, task_id: str, todo_id: str) -> None:
        doc = self._repo.read_task_doc(task_id)
        try:
            doc.remove_todo(todo_id)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)

    def get_todos(self, task_id: str) -> TodosResult:
        doc = self._repo.read_task_doc(task_id)
        return TodosResult(task_id=task_id, todos=_todos_from_doc(doc))

    def set_report(self, task_id: str, report: str) -> ReportResult:
        doc = self._repo.read_task_doc(task_id)
        doc.set_report(report)
        self._repo.write_task_doc(task_id, doc)
        return ReportResult(task_id=task_id, report=doc.get_report())

    def get_report(self, task_id: str) -> ReportResult:
        doc = self._repo.read_task_doc(task_id)
        return ReportResult(task_id=task_id, report=doc.get_report())

    def rough_add(
        self, task_id: str, content: str, note_id: str | None = None
    ) -> NoteResult:
        doc = self._repo.read_rough_doc(task_id)
        try:
            block = doc.add_note(content, note_id=note_id)
        except ValueError as exc:
            raise DuplicateNoteError(task_id, note_id or "") from exc
        self._repo.write_rough_doc(task_id, doc)
        return NoteResult(task_id=task_id, note=_note_item(block))

    def rough_update(self, task_id: str, note_id: str, content: str) -> NoteResult:
        doc = self._repo.read_rough_doc(task_id)
        try:
            block = doc.update_note(note_id, content)
        except KeyError as exc:
            raise NoteNotFoundError(task_id, note_id) from exc
        self._repo.write_rough_doc(task_id, doc)
        return NoteResult(task_id=task_id, note=_note_item(block))

    def rough_delete(self, task_id: str, note_id: str) -> None:
        doc = self._repo.read_rough_doc(task_id)
        try:
            doc.delete_note(note_id)
        except KeyError as exc:
            raise NoteNotFoundError(task_id, note_id) from exc
        self._repo.write_rough_doc(task_id, doc)

    def rough_get(self, task_id: str, note_id: str) -> NoteResult:
        doc = self._repo.read_rough_doc(task_id)
        try:
            block = doc.get_note(note_id)
        except KeyError as exc:
            raise NoteNotFoundError(task_id, note_id) from exc
        return NoteResult(task_id=task_id, note=_note_item(block))

    def rough_list(self, task_id: str) -> NotesListResult:
        doc = self._repo.read_rough_doc(task_id)
        notes = [
            NotePreview(
                note_id=n.note_id,
                created=n.created,
                updated=n.updated,
                preview=n.preview(),
            )
            for n in doc.notes or []
        ]
        return NotesListResult(task_id=task_id, notes=notes)

    def rough_clear(self, task_id: str) -> RoughClearResult:
        doc = self._repo.read_rough_doc(task_id)
        removed = doc.clear_notes()
        self._repo.write_rough_doc(task_id, doc)
        return RoughClearResult(task_id=task_id, removed_count=removed)


def _metadata_from_doc(doc: TaskDocument) -> TaskMetadata:
    return TaskMetadata(
        id=str(doc.metadata.get("id", "")),
        name=str(doc.metadata.get("name", "")),
        description=str(doc.metadata.get("description", "")),
        status=str(doc.metadata.get("status", "active")),
        created_at=str(doc.metadata.get("created_at", "")),
        updated_at=str(doc.metadata.get("updated_at", "")),
    )


def _todo_item(todo: TodoLine) -> TodoItem:
    return TodoItem(id=todo.id, text=todo.text, completed=todo.completed)


def _todos_from_doc(doc: TaskDocument) -> list[TodoItem]:
    return [_todo_item(t) for t in doc.parse_todos()]


def _note_item(block: NoteBlock) -> NoteItem:
    return NoteItem(
        note_id=block.note_id,
        created=block.created,
        updated=block.updated,
        content=block.content,
    )
