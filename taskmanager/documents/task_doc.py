"""Parse and serialize task markdown documents."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import frontmatter

SECTION_NAMES = ("Plan", "Todos", "Report")
TODO_LINE_RE = re.compile(
    r"^- \[(?P<check>[ xX])\] \*\*(?P<todo_id>todo-[a-f0-9]+)\*\* (?P<text>.*)$",
    re.MULTILINE,
)
@dataclass
class TodoLine:
    id: str
    text: str
    completed: bool
    raw_line: str


@dataclass
class TaskDocument:
    metadata: dict[str, Any]
    title: str
    sections: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create_new(
        cls,
        task_id: str,
        name: str,
        description: str,
        *,
        initial_plan: str = "",
        initial_todos: list[str] | None = None,
    ) -> TaskDocument:
        now = _utc_now()
        doc = cls(
            metadata={
                "id": task_id,
                "name": name,
                "description": description,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            title=name,
            sections={"Plan": initial_plan.strip(), "Todos": "", "Report": ""},
        )
        if initial_todos:
            lines = []
            for text in initial_todos:
                todo_id = _new_todo_id()
                lines.append(_format_todo_line(todo_id, text, completed=False))
            doc.sections["Todos"] = "\n".join(lines)
        return doc

    @classmethod
    def parse(cls, text: str) -> TaskDocument:
        post = frontmatter.loads(text)
        body = post.content.strip()
        title = name = post.metadata.get("name", "Task")
        sections: dict[str, str] = {"Plan": "", "Todos": "", "Report": ""}

        if body:
            if body.startswith("# "):
                first_nl = body.find("\n")
                if first_nl == -1:
                    title = body[2:].strip()
                    body = ""
                else:
                    title = body[2:first_nl].strip()
                    body = body[first_nl + 1 :].strip()

            if body:
                header_re = re.compile(r"^## (.+)$", re.MULTILINE)
                matches = list(header_re.finditer(body))
                for i, match in enumerate(matches):
                    name_part = match.group(1).strip()
                    if name_part not in sections:
                        continue
                    start = match.end()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                    sections[name_part] = body[start:end].strip()

        return cls(metadata=dict(post.metadata), title=title, sections=sections)

    def serialize(self) -> str:
        meta = dict(self.metadata)
        meta["updated_at"] = _utc_now()
        self.metadata = meta

        body_parts = [f"# {self.title}", ""]
        for section_name in SECTION_NAMES:
            body_parts.append(f"## {section_name}")
            content = self.sections.get(section_name, "").strip()
            if content:
                body_parts.append(content)
            body_parts.append("")

        post = frontmatter.Post("\n".join(body_parts).rstrip() + "\n", **meta)
        return frontmatter.dumps(post)

    def parse_todos(self) -> list[TodoLine]:
        todos: list[TodoLine] = []
        for line in self.sections.get("Todos", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = TODO_LINE_RE.match(stripped)
            if match:
                todos.append(
                    TodoLine(
                        id=match.group("todo_id"),
                        text=match.group("text"),
                        completed=match.group("check").lower() == "x",
                        raw_line=stripped,
                    )
                )
        return todos

    def set_plan(self, content: str) -> None:
        self.sections["Plan"] = content.strip()

    def get_plan(self) -> str:
        return self.sections.get("Plan", "")

    def set_report(self, content: str) -> str:
        self.sections["Report"] = content.strip()
        return self.sections["Report"]

    def get_report(self) -> str:
        return self.sections.get("Report", "")

    def add_todos(self, items: list[str]) -> list[TodoLine]:
        existing = self.sections.get("Todos", "").strip()
        new_lines: list[str] = []
        created: list[TodoLine] = []
        for text in items:
            todo_id = _new_todo_id()
            line = _format_todo_line(todo_id, text, completed=False)
            new_lines.append(line)
            created.append(
                TodoLine(id=todo_id, text=text.strip(), completed=False, raw_line=line)
            )
        combined = "\n".join(filter(None, [existing, "\n".join(new_lines)]))
        self.sections["Todos"] = combined.strip()
        return created

    def toggle_todo(self, todo_id: str, completed: bool | None = None) -> TodoLine:
        todos = self.parse_todos()
        for todo in todos:
            if todo.id == todo_id:
                new_completed = not todo.completed if completed is None else completed
                new_line = _format_todo_line(todo_id, todo.text, completed=new_completed)
                self.sections["Todos"] = self.sections["Todos"].replace(
                    todo.raw_line, new_line, 1
                )
                return TodoLine(
                    id=todo_id,
                    text=todo.text,
                    completed=new_completed,
                    raw_line=new_line,
                )
        raise KeyError(todo_id)

    def update_todo(self, todo_id: str, text: str) -> TodoLine:
        todos = self.parse_todos()
        for todo in todos:
            if todo.id == todo_id:
                new_line = _format_todo_line(todo_id, text, completed=todo.completed)
                self.sections["Todos"] = self.sections["Todos"].replace(
                    todo.raw_line, new_line, 1
                )
                return TodoLine(
                    id=todo_id, text=text.strip(), completed=todo.completed, raw_line=new_line
                )
        raise KeyError(todo_id)

    def remove_todo(self, todo_id: str) -> None:
        todos = self.parse_todos()
        for todo in todos:
            if todo.id == todo_id:
                lines = [
                    ln
                    for ln in self.sections.get("Todos", "").splitlines()
                    if ln.strip() != todo.raw_line
                ]
                self.sections["Todos"] = "\n".join(lines).strip()
                return
        raise KeyError(todo_id)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_todo_id() -> str:
    return f"todo-{secrets.token_hex(4)}"


def _format_todo_line(todo_id: str, text: str, *, completed: bool) -> str:
    check = "x" if completed else " "
    return f"- [{check}] **{todo_id}** {text.strip()}"
