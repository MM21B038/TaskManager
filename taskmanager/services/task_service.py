"""Task management business logic."""

from __future__ import annotations

import uuid
from typing import Literal

from taskmanager.config import Settings
from taskmanager.documents.rough_doc import NoteBlock
from taskmanager.documents.table_doc import TableData, TableDocument
from taskmanager.documents.task_doc import TaskDocument, TodoLine
from taskmanager.exceptions import (
    ColumnNotFoundError,
    DuplicateNoteError,
    DuplicateTableNameError,
    InvalidTableUpdateError,
    InvalidTaskModeError,
    NoteNotFoundError,
    RowNotFoundError,
    TableNotFoundError,
    TaskNotFoundError,
    TodoNotFoundError,
)
from taskmanager.models import (
    AddTodosResult,
    AddedTodo,
    CellUpdate,
    NoteItem,
    NotePreview,
    NoteResult,
    NotesListResult,
    PlanResult,
    ReportResult,
    RoughClearResult,
    RowMatrix,
    TableCellsUpdated,
    TableColumnsAdded,
    TableCreated,
    TableDetail,
    TableListResult,
    TableRowsAdded,
    TableSummary,
    TaskCreated,
    TaskDetail,
    TaskMetadata,
    TaskMode,
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
        mode: TaskMode = "todo",
        initial_plan: str = "",
        initial_todos: list[str] | None = None,
    ) -> TaskCreated:
        if mode == "table" and initial_todos:
            raise InvalidTableUpdateError(
                "initial_todos cannot be used when mode is 'table'"
            )
        task_id = str(uuid.uuid4())
        task_file, rough_file = self._repo.create_task_files(
            task_id,
            name,
            description,
            mode=mode,
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
        mode = _task_mode(doc)
        tables: list[TableSummary] = []
        todos: list[TodoItem] = []
        if mode == "table":
            table_doc = self._repo.read_table_doc(task_id)
            tables = [_table_summary(table_id, table) for table_id, table in table_doc.tables.items()]
        else:
            todos = _todos_from_doc(doc)
        return TaskDetail(
            metadata=_metadata_from_doc(doc),
            plan=doc.get_plan(),
            todos=todos,
            tables=tables,
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
            mode = _task_mode(doc)
            todo_done = 0
            todo_total = 0
            table_count = 0
            if mode == "table":
                try:
                    table_doc = self._repo.read_table_doc(task_id)
                    table_count = len(table_doc.tables)
                except TaskNotFoundError:
                    table_count = 0
            else:
                todos = doc.parse_todos()
                todo_done = sum(1 for t in todos if t.completed)
                todo_total = len(todos)
            summaries.append(
                TaskSummary(
                    id=doc.metadata.get("id", task_id),
                    name=doc.metadata.get("name", ""),
                    mode=mode,
                    status=doc.metadata.get("status", "active"),
                    updated_at=doc.metadata.get("updated_at", ""),
                    todo_done=todo_done,
                    todo_total=todo_total,
                    table_count=table_count,
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
        _require_mode(doc, task_id, expected="todo")
        created = doc.add_todos(items)
        self._repo.write_task_doc(task_id, doc)
        return AddTodosResult(
            todos=[AddedTodo(id=t.id, text=t.text) for t in created],
        )

    def toggle_todo(
        self, task_id: str, todo_id: str, completed: bool | None = None
    ) -> TodoItem:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="todo")
        try:
            todo = doc.toggle_todo(todo_id, completed=completed)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)
        return _todo_item(todo)

    def update_todo(self, task_id: str, todo_id: str, text: str) -> TodoItem:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="todo")
        try:
            todo = doc.update_todo(todo_id, text)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)
        return _todo_item(todo)

    def remove_todo(self, task_id: str, todo_id: str) -> None:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="todo")
        try:
            doc.remove_todo(todo_id)
        except KeyError as exc:
            raise TodoNotFoundError(task_id, todo_id) from exc
        self._repo.write_task_doc(task_id, doc)

    def get_todos(self, task_id: str) -> TodosResult:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="todo")
        return TodosResult(task_id=task_id, todos=_todos_from_doc(doc))

    def set_report(self, task_id: str, report: str) -> ReportResult:
        doc = self._repo.read_task_doc(task_id)
        doc.set_report(report)
        self._repo.write_task_doc(task_id, doc)
        return ReportResult(task_id=task_id, report=doc.get_report())

    def get_report(self, task_id: str) -> ReportResult:
        doc = self._repo.read_task_doc(task_id)
        return ReportResult(task_id=task_id, report=doc.get_report())

    def table_create(
        self,
        task_id: str,
        name: str,
        columns: list[str],
        *,
        rows: list[str] | None = None,
        default_value: str = "",
        initial_rows: list[dict[str, str]] | None = None,
    ) -> TableCreated:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        try:
            table_id, table = table_doc.create_table(
                name,
                columns,
                rows=rows,
                default_value=default_value,
                initial_rows=initial_rows,
            )
        except ValueError as exc:
            message = str(exc)
            if message == name.strip():
                raise DuplicateTableNameError(task_id, name.strip()) from exc
            raise _translate_table_value_error(task_id, table_id="", message=message) from exc
        self._repo.write_table_doc(task_id, table_doc)
        return TableCreated(
            task_id=task_id,
            table_id=table_id,
            name=table.name,
            columns=table.columns,
            rows=table.rows,
            default=table.default,
            cell_count=len(table.rows) * len(table.columns),
        )

    def table_list(self, task_id: str) -> TableListResult:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        return TableListResult(
            task_id=task_id,
            tables=[
                _table_summary(table_id, table)
                for table_id, table in table_doc.tables.items()
            ],
        )

    def table_get(
        self,
        task_id: str,
        table_id: str,
        *,
        rows: list[str] | None = None,
        columns: list[str] | None = None,
        resolved: bool = True,
    ) -> TableDetail:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        try:
            table = table_doc.get_table(table_id)
            cells = table_doc.resolve_cells(
                table,
                rows=rows,
                columns=columns,
                resolved=resolved,
            )
        except ValueError as exc:
            raise _translate_table_value_error(
                task_id, table_id=table_id, message=str(exc)
            ) from exc
        return TableDetail(
            task_id=task_id,
            table_id=table_id,
            name=table.name,
            columns=table.columns,
            rows=table.rows,
            default=table.default,
            cells=cells,
        )

    def table_add_rows(
        self,
        task_id: str,
        table_id: str,
        rows: list[str],
        *,
        default_value: str | None = None,
        values: list[dict[str, str]] | None = None,
    ) -> TableRowsAdded:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        try:
            table = table_doc.add_rows(
                table_id,
                rows,
                default_value=default_value,
                values=values,
            )
        except ValueError as exc:
            raise _translate_table_value_error(
                task_id, table_id=table_id, message=str(exc)
            ) from exc
        self._repo.write_table_doc(task_id, table_doc)
        return TableRowsAdded(
            task_id=task_id,
            table_id=table_id,
            rows=table.rows,
            row_count=len(table.rows),
        )

    def table_add_columns(
        self,
        task_id: str,
        table_id: str,
        columns: list[str],
        *,
        default_value: str | None = None,
    ) -> TableColumnsAdded:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        try:
            table = table_doc.add_columns(
                table_id,
                columns,
                default_value=default_value,
            )
        except ValueError as exc:
            raise _translate_table_value_error(
                task_id, table_id=table_id, message=str(exc)
            ) from exc
        self._repo.write_table_doc(task_id, table_doc)
        return TableColumnsAdded(
            task_id=task_id,
            table_id=table_id,
            columns=table.columns,
            column_count=len(table.columns),
        )

    def table_set_cells(
        self,
        task_id: str,
        table_id: str,
        *,
        updates: list[CellUpdate] | None = None,
        matrix: list[RowMatrix] | None = None,
    ) -> TableCellsUpdated:
        doc = self._repo.read_task_doc(task_id)
        _require_mode(doc, task_id, expected="table")
        table_doc = self._repo.read_table_doc(task_id)
        try:
            table_doc.apply_updates(
                table_id,
                updates=[update.model_dump(exclude_none=True) for update in (updates or [])],
                matrix=[row.model_dump() for row in (matrix or [])] if matrix is not None else None,
            )
        except ValueError as exc:
            raise _translate_table_value_error(
                task_id, table_id=table_id, message=str(exc)
            ) from exc
        self._repo.write_table_doc(task_id, table_doc)
        updated_count = len(updates or []) if matrix is None else len(matrix or [])
        return TableCellsUpdated(
            task_id=task_id,
            table_id=table_id,
            updated_count=updated_count,
        )

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


def _task_mode(doc: TaskDocument) -> TaskMode:
    mode = str(doc.metadata.get("mode", "todo"))
    return "table" if mode == "table" else "todo"


def _require_mode(doc: TaskDocument, task_id: str, *, expected: Literal["todo", "table"]) -> None:
    actual = _task_mode(doc)
    if actual != expected:
        raise InvalidTaskModeError(task_id, expected, actual)


def _metadata_from_doc(doc: TaskDocument) -> TaskMetadata:
    return TaskMetadata(
        id=str(doc.metadata.get("id", "")),
        name=str(doc.metadata.get("name", "")),
        description=str(doc.metadata.get("description", "")),
        mode=_task_mode(doc),
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


def _table_summary(table_id: str, table: TableData) -> TableSummary:
    return TableSummary(
        table_id=table_id,
        name=table.name,
        row_count=len(table.rows),
        column_count=len(table.columns),
    )


def _translate_table_value_error(task_id: str, *, table_id: str, message: str) -> Exception:
    if message.startswith("unknown-table:"):
        return TableNotFoundError(task_id, message.removeprefix("unknown-table:"))
    if message.startswith("unknown-row:"):
        return RowNotFoundError(task_id, table_id, message.removeprefix("unknown-row:"))
    if message.startswith("unknown-column:"):
        return ColumnNotFoundError(task_id, table_id, message.removeprefix("unknown-column:"))
    return InvalidTableUpdateError(message)
