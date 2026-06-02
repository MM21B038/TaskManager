"""Parse and serialize rough-note markdown documents."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import frontmatter

NOTE_OPEN_RE = re.compile(
    r'^<!-- NOTE id="(?P<id>[^"]+)" created="(?P<created>[^"]+)" updated="(?P<updated>[^"]+)" -->\s*$',
    re.MULTILINE,
)
NOTE_CLOSE = "<!-- /NOTE -->"
PREVIEW_LEN = 120


@dataclass(frozen=True)
class NoteBlock:
    note_id: str
    created: str
    updated: str
    content: str

    def preview(self) -> str:
        flat = " ".join(self.content.split())
        if len(flat) <= PREVIEW_LEN:
            return flat
        return flat[: PREVIEW_LEN - 3] + "..."


@dataclass
class RoughDocument:
    metadata: dict[str, Any]
    preamble: str = "# Rough notes\n"
    notes: list[NoteBlock] | None = None

    def __post_init__(self) -> None:
        if self.notes is None:
            self.notes = []

    @classmethod
    def create_new(cls, task_id: str) -> RoughDocument:
        now = _utc_now()
        return cls(
            metadata={"task_id": task_id, "created_at": now, "updated_at": now},
            preamble="# Rough notes\n",
            notes=[],
        )

    @classmethod
    def parse(cls, text: str) -> RoughDocument:
        post = frontmatter.loads(text)
        body = post.content
        notes = _parse_note_blocks(body)
        preamble = "# Rough notes\n"
        if body.strip().startswith("# Rough notes"):
            end = body.find("<!-- NOTE")
            if end == -1:
                preamble = body.strip() + ("\n" if not body.endswith("\n") else "")
            else:
                preamble = body[:end].rstrip() + "\n"
        return cls(metadata=dict(post.metadata), preamble=preamble, notes=notes)

    def serialize(self) -> str:
        meta = dict(self.metadata)
        meta["updated_at"] = _utc_now()
        self.metadata = meta

        parts = [self.preamble.rstrip(), ""]
        for note in self.notes or []:
            parts.append(_render_note_block(note))
            parts.append("")

        body = "\n".join(parts).rstrip() + "\n"
        post = frontmatter.Post(body, **meta)
        return frontmatter.dumps(post)

    def add_note(self, content: str, note_id: str | None = None) -> NoteBlock:
        nid = note_id or _new_note_id()
        if any(n.note_id == nid for n in self.notes or []):
            raise ValueError(f"duplicate note id: {nid}")
        now = _utc_now()
        block = NoteBlock(note_id=nid, created=now, updated=now, content=content.strip())
        self.notes = list(self.notes or []) + [block]
        return block

    def update_note(self, note_id: str, content: str) -> NoteBlock:
        updated_notes: list[NoteBlock] = []
        found: NoteBlock | None = None
        for note in self.notes or []:
            if note.note_id == note_id:
                found = NoteBlock(
                    note_id=note.note_id,
                    created=note.created,
                    updated=_utc_now(),
                    content=content.strip(),
                )
                updated_notes.append(found)
            else:
                updated_notes.append(note)
        if found is None:
            raise KeyError(note_id)
        self.notes = updated_notes
        return found

    def delete_note(self, note_id: str) -> None:
        notes = self.notes or []
        if not any(n.note_id == note_id for n in notes):
            raise KeyError(note_id)
        self.notes = [n for n in notes if n.note_id != note_id]

    def get_note(self, note_id: str) -> NoteBlock:
        for note in self.notes or []:
            if note.note_id == note_id:
                return note
        raise KeyError(note_id)

    def clear_notes(self) -> int:
        count = len(self.notes or [])
        self.notes = []
        return count


def _parse_note_blocks(body: str) -> list[NoteBlock]:
    notes: list[NoteBlock] = []
    pos = 0
    while pos < len(body):
        match = NOTE_OPEN_RE.search(body, pos)
        if not match:
            break
        start = match.end()
        close_idx = body.find(NOTE_CLOSE, start)
        if close_idx == -1:
            break
        content = body[start:close_idx].strip("\n")
        notes.append(
            NoteBlock(
                note_id=match.group("id"),
                created=match.group("created"),
                updated=match.group("updated"),
                content=content,
            )
        )
        pos = close_idx + len(NOTE_CLOSE)
    return notes


def _render_note_block(note: NoteBlock) -> str:
    lines = [
        f'<!-- NOTE id="{note.note_id}" created="{note.created}" updated="{note.updated}" -->',
        note.content,
        NOTE_CLOSE,
    ]
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_note_id() -> str:
    return f"note-{secrets.token_hex(4)}"
