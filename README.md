# Task Manager MCP Server

HTTP-based [FastMCP](https://github.com/jlowin/fastmcp) server that persists agent work as markdown: one **task file** per job (`task/{uuid}.md`) and one **rough-notes file** (`rough/{uuid}.md`) for scratch thinking.

## Features

- **Task file** — YAML metadata plus `Plan`, `Todos`, and `Report` sections in a single document
- **Rough notes** — append/update/delete delimited note blocks by stable `note_id`
- **18 MCP tools** — full lifecycle from task creation through todos to final report
- **File locking** — safe concurrent read/write on Windows and Unix

## Quick start

```bash
uv sync
uv run taskmanager
```

Server listens at **`http://127.0.0.1:8000/mcp`** (streamable HTTP). Start it before connecting an MCP client.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_MANAGER_DATA_DIR` | project root | Base directory; contains `task/` and `rough/` |
| `TASK_MANAGER_HOST` | `127.0.0.1` | Bind host |
| `TASK_MANAGER_PORT` | `8000` | Bind port |

## Cursor MCP configuration

Add to `.cursor/mcp.json` or **Settings → MCP**:

```json
{
  "mcpServers": {
    "task-manager": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Windows console noise

`ConnectionResetError: [WinError 10054]` after MCP requests is usually harmless: the client closed an HTTP connection during streamable-HTTP setup while the server already returned `200` / `202`. The server patches asyncio on Windows to reduce this noise; restart after upgrades.

## Tool reference

| Category | Tools |
|----------|-------|
| Tasks | `create_task`, `get_task`, `get_task_metadata`, `list_tasks` |
| Plan | `set_plan`, `get_plan` |
| Todos | `add_todos`, `toggle_todo`, `update_todo`, `remove_todo`, `get_todos` |
| Report | `set_report`, `get_report` |
| Rough | `rough_add`, `rough_update`, `rough_delete`, `rough_get`, `rough_list`, `rough_clear` |

## How and when to use the MCP tools

Use this section as an **operator guide** or paste the [system prompt block](#system-prompt-for-agents) into agent instructions.

### Mental model

| Store | Path | Purpose |
|-------|------|---------|
| Task document | `task/{task_id}.md` | Durable **plan**, trackable **todos**, final **report** |
| Rough document | `rough/{task_id}.md` | Disposable **scratch** (ideas, logs, snippets) |

Always keep `task_id` from `create_task` for every later call. Todos are referenced by `todo_id` (e.g. `todo-a1b2c3d4`). Rough entries use `note_id` (e.g. `note-x7k2m9p1`).

### Lifecycle phases

```text
1. ORIENT     list_tasks / get_task_metadata
2. START      create_task
3. PLAN       set_plan, add_todos
4. WORK       rough_add, rough_update, get_todos, toggle_todo
5. FINISH     set_report
6. HANDOFF    get_task
```

### When to call each tool

#### Tasks

| Tool | When to use |
|------|-------------|
| `create_task` | **Once** at the beginning of a new piece of work. Pass a clear `name` and `description`. Optionally seed `initial_plan` or `initial_todos` if already known. Save the returned `task_id`. |
| `list_tasks` | Resume work, pick up an old job, or see what is in flight. Prefer this over reading files on disk. |
| `get_task_metadata` | You only need title, description, status, or timestamps — not full plan/todos/report. Saves tokens. |
| `get_task` | You need the **full picture** (plan + todos + report) or you are handing off to another agent/session. |

#### Plan

| Tool | When to use |
|------|-------------|
| `set_plan` | After `create_task`, when you have (or revise) the step-by-step approach. Replaces the whole plan section — include the full plan each time. |
| `get_plan` | Before executing, to re-read strategy without loading todos/report. |

#### Todos

| Tool | When to use |
|------|-------------|
| `add_todos` | Break work into checkable steps **after** the plan exists, or when new steps appear mid-task. Returns new `todo_id` values — store them if you will toggle soon. |
| `get_todos` | Check what is left; get `todo_id`s before toggling. |
| `toggle_todo` | **Immediately** when a step is done (or undone). Pass `completed: true` / `false`, or omit/`null` to flip. |
| `update_todo` | Wording changed but the step is the same item. |
| `remove_todo` | Step is invalid or duplicate; do not use for “done” — use `toggle_todo`. |

#### Report

| Tool | When to use |
|------|-------------|
| `set_report` | When work is **finished** (or stopped with a clear outcome). Summarize what was done, decisions, and follow-ups. Replaces the whole report section. |
| `get_report` | Review outcome without reloading plan/todos. |

#### Rough notes

| Tool | When to use |
|------|-------------|
| `rough_add` | Scratch during investigation: hypotheses, command output, partial findings. **Not** for the final deliverable. |
| `rough_update` | Correct or expand an existing note (`note_id` from `rough_list` / `rough_get`). |
| `rough_delete` | Remove a note that is wrong or merged elsewhere. |
| `rough_get` | Read one note in full. |
| `rough_list` | See all notes with short previews; use before update/delete. |
| `rough_clear` | Wipe all rough notes after folding important bits into plan/report (optional cleanup). |

### Recommended workflow (happy path)

1. **`create_task`** — `name` = short title, `description` = user goal and constraints.
2. **`set_plan`** — numbered or bulleted steps the agent will follow.
3. **`add_todos`** — concrete checklist aligned with the plan (3–10 items is typical).
4. **While working**
   - **`rough_add`** for exploration, errors, and interim facts.
   - **`toggle_todo`** as each checklist item completes.
   - **`get_todos`** if you lost track of ids or status.
5. **`set_report`** — final summary for the user (what changed, how to verify, open questions).
6. **`get_task`** — optional final read-back before responding to the user.

### Practices

- **Do** create exactly one task per distinct user request (or epic), unless the user explicitly continues an existing `task_id`.
- **Do** toggle todos as you go; do not batch all toggles at the end.
- **Do** put polished output in **`set_report`**; put messy debugging in **`rough_add`**.
- **Do** use `get_task_metadata` / `get_plan` / `get_todos` when you only need one slice.
- **Don't** edit markdown files on disk directly — tools keep frontmatter and section structure valid.
- **Don't** store long-term truth only in rough notes; promote important conclusions to plan or report.
- **Don't** call `set_plan` or `set_report` for tiny deltas — they replace the entire section; send the full updated text.

### Resuming a previous task

1. `list_tasks` or use a `task_id` the user provided.
2. `get_task` or `get_todos` + `get_plan` to reload context.
3. `rough_list` for scratch context.
4. Continue toggling todos and updating rough/report as needed.

---

## System prompt for agents

Copy everything inside the block below into system instructions, a Cursor rule, or an agent harness prompt.

```text
You have access to the Task Manager MCP server. It stores work as markdown on disk.

CONCEPTS
- task_id: UUID returned by create_task. Required on every call after creation.
- todo_id: Stable id on each checklist line (e.g. todo-a1b2c3d4). Use for toggle_todo.
- note_id: Stable id on each rough note block (e.g. note-abc12345). Use for rough_update/delete.

STORAGE
- task/{task_id}.md — metadata, Plan, Todos (checkboxes), Report (final summary).
- rough/{task_id}.md — scratch notes only; safe for messy or partial content.

WHEN TO USE TOOLS
- New user request → create_task(name, description). Keep task_id.
- Strategy / steps → set_plan(task_id, full plan markdown).
- Checklist → add_todos(task_id, items). Save returned todo_ids.
- Investigation, logs, drafts → rough_add(task_id, content). Use rough_update/delete by note_id.
- Step completed → toggle_todo(task_id, todo_id, completed=true). Re-fetch with get_todos if needed.
- Work complete → set_report(task_id, full report markdown).
- Need status only → get_task_metadata, get_plan, get_todos, or get_report (not get_task).
- Full handoff or final review → get_task(task_id).
- Continue old work → list_tasks, then get_task or partial getters.

ORDER OF OPERATIONS
1. create_task
2. set_plan → add_todos
3. Loop: rough_add / rough_update as needed; toggle_todo after each finished step
4. set_report when done
5. get_task optional before replying to user

RULES
- One task per distinct assignment unless the user gives an existing task_id.
- Never edit task/ or rough/ files directly; always use MCP tools.
- set_plan and set_report replace their entire section — send complete updated content.
- Keep making rough notes as you progress, specially before you toggle_todo.
- Put final user-facing conclusions in set_report, not only in rough notes.
- Toggle todos as work progresses, not all at once at the end.
- Check all todos were completed and toggled before writing final report or responding user.
```

---

## File formats

**Task** (`task/{uuid}.md`):

```markdown
---
id: "550e8400-e29b-41d4-a716-446655440000"
name: "Implement auth"
description: "Add JWT login flow"
status: active
created_at: "2026-06-01T12:00:00Z"
updated_at: "2026-06-01T12:05:00Z"
---

# Implement auth

## Plan
1. Add login endpoint
2. Wire middleware

## Todos
- [ ] **todo-a1b2c3d4** Add login endpoint
- [x] **todo-e5f6a7b8** Write tests

## Report
Shipped JWT auth; run `uv run pytest` to verify.
```

**Rough** (`rough/{uuid}.md`):

```markdown
---
task_id: "550e8400-e29b-41d4-a716-446655440000"
created_at: "2026-06-01T12:01:00Z"
updated_at: "2026-06-01T12:10:00Z"
---

# Rough notes

<!-- NOTE id="note-abc12345" created="2026-06-01T12:01:00Z" updated="2026-06-01T12:01:00Z" -->
Tried approach A — failed with 401 on refresh token.
<!-- /NOTE -->
```

## Development

```bash
uv sync --group dev
uv run pytest
```

Project layout: `taskmanager/` (server, parsers, services, tools), `task/`, `rough/`, `tests/`.
