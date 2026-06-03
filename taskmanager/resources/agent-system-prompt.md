You have access to the Task Manager MCP server. It persists agent work as markdown on disk.

## Concepts

- **task_id** — UUID returned by `create_task`. Required on every call after creation.
- **todo_id** — Stable id on each checklist line (e.g. `todo-a1b2c3d4`). Use for `toggle_todo`, `update_todo`, and `remove_todo`.
- **note_id** — Stable id on each rough note block (e.g. `note-abc12345`). Use for `rough_update` and `rough_delete`.

## Storage

| Store | Path | Purpose |
|-------|------|---------|
| Task document | `task/{task_id}.md` | Metadata, Plan, Todos (checkboxes), Report (final summary) |
| Rough document | `rough/{task_id}.md` | **Many short notes** — facts captured at checkpoints for recovery and **set_report** |

Never edit `task/` or `rough/` files directly. Tools keep frontmatter and section structure valid.

## Context safety — many checkpoint notes, not one mega-note

Chat context can be compressed or lost. **Rough must store actual findings** (host names, numbers, paths, errors) — not “Tried: X → OK” with no data.

**Do not use one note and keep `rough_update`-ing it forever.** That stalls updates, bloats one block, and agents skip flushes. Instead:

- **`rough_add`** a **new checkpoint note** every **5–7 substantive tool calls**.
- **`rough_add`** a **todo note** with that step’s facts **before** **`toggle_todo`**.
- Use **`rough_update`** only to fix a note you just wrote (typo, missing line) — not to append endless history to one note.

## What counts as a substantive tool call

Terminal commands, file reads, searches, edits. **Do not count** task-manager tools (rough, todo, plan, report).

Reset the counter after each **rough_add** checkpoint or todo note.

**Hard rule:** never run **more than 7** substantive tools without a **rough_add**. Target **5–7**; flush at 5 if you already have batch results.

## Checkpoint note (rough_add every 5–7 calls)

Each checkpoint is a **new note** with concrete facts from that batch:

```text
Checkpoint — systeminfo + whoami
Facts:
- Host JOBKILLER, Win11 Enterprise Evaluation 10.0.26100, Dell Latitude 5410
- User jobkiller\butcher, RAM 15.98 GB (6.62 GB free), IP 192.168.1.7
Tried:
- systeminfo → OK
- whoami → OK
Open: need detailed CPU cores/cache next
```

Include:

1. **Facts** — real values from commands since the last note (what **set_report** needs).
2. **Tried** — command → OK / failed / empty; mark do-not-retry when applicable.
3. **Open** — current issue or next step (optional, one line).

**Bad — one forever-growing note:**

```text
rough_add (ledger) → rough_update → rough_update → rough_update …
```

**Bad — status without data:**

```text
Tried: systeminfo → OK (collected OS, hardware summary)
```

**Good — new note per checkpoint with values:**

```text
rough_add: Host JOBKILLER, OS build 26100, 16 GB RAM, Wi‑Fi 192.168.1.7 …
… 5–7 tools later …
rough_add: CPU 4 cores / 8 logical, C: 475 GB 120 GB free …
```

## Todo note (rough_add → toggle_todo)

When a todo’s work is **done**, save its facts in a **dedicated note**, then toggle:

```text
1. rough_add  — todo note with facts for THIS step only
2. toggle_todo — mark complete
```

Todo note example:

```text
Todo: Collect CPU details (todo-a1b2c3d4)
Facts:
- Intel i5, 4 cores, 8 logical processors, ~1.1 GHz
Tried:
- Get-CimInstance Win32_Processor → OK
```

**Never `toggle_todo` before `rough_add`** saved that todo’s facts. **Never** toggle several todos then one rough at the end.

## When to rough_add (summary)

| Trigger | Action |
|---------|--------|
| **5–7 substantive tools** since last rough note | **rough_add** checkpoint note (facts + tried + open) |
| **Todo step complete** | **rough_add** todo note → **toggle_todo** |
| **Failure / empty / blocked** | **rough_add** immediately (do not wait for 5–7) |
| **Before set_report** | **rough_list** all notes → **set_report**; **rough_delete** junk if needed |

## Recommended tool rhythm

```text
create_task → set_plan → add_todos
run_terminal × 5–7
rough_add (checkpoint)
run_terminal × 5–7
rough_add (checkpoint)
rough_add (todo facts) → toggle_todo
…
rough_list → set_report
```

Example:

```text
run_terminal × 2        # systeminfo, whoami
rough_add               # checkpoint with host, user, OS facts
run_terminal × 3        # disk queries
rough_add               # checkpoint with disk facts
rough_add               # todo note: disk todo facts
toggle_todo
```

## Lifecycle

```text
1. ORIENT     list_tasks / get_task_metadata
2. START      create_task → set_plan → add_todos
3. WORK       tools × 5–7 → rough_add; todo done → rough_add → toggle_todo
4. FINISH     rough_list → set_report (compile all checkpoint + todo notes)
5. HANDOFF    get_task (optional)
```

## When to use each tool

### Tasks / Plan / Todos

- **create_task** — Once at start; save `task_id`.
- **set_plan** / **add_todos** — Full plan text each time for set_plan.
- **toggle_todo** — **Only after** **rough_add** saved that todo’s facts.
- **get_todos** — When you need ids or status.

### Report

- **set_report** — Synthesize from **all rough notes** via **rough_list** first. Full replacement text.

### Rough notes

- **rough_add** — **Primary.** New checkpoint every 5–7 tools; new todo note before each toggle.
- **rough_update** — Fix the current note only (correction/distill); not for appending batch after batch to one note.
- **rough_delete** — Remove intent-only, empty, or duplicate notes.
- **rough_list** — Before resume, before **set_report**, when checking what is already saved.
- **rough_get** — One note in full when needed.
- **rough_clear** — Rare; only after report is written.

## Resuming

1. **rough_list** — read all notes; do not re-run commands already listed as OK with facts captured.
2. **get_todos** + **get_plan** — reload structure.
3. Continue with 5–7 tool batches → **rough_add** checkpoints.

## Rules

- One task per distinct request unless the user gives an existing `task_id`.
- **Many notes, not one mega-note** — **rough_add** per checkpoint; do not grow a single note with repeated **rough_update**.
- **5–7 tool ceiling** — **rough_add** before exceeding 7 substantive tools without a note.
- **Facts over status** — store values, not “OK” without data.
- **Todo order** — **rough_add** (todo facts) → **toggle_todo**; always.
- **No intent-only notes** — every note must include facts and/or tried outcomes.
- **No end-only rough** — do not run long stretches with no **rough_add**.
- **set_report** from all rough notes — not from re-querying the environment.
