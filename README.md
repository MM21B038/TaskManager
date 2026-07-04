# Task Manager MCP Server

HTTP-based [FastMCP](https://github.com/jlowin/fastmcp) server that persists agent work as markdown: one **task file** per job (`task/{uuid}.md`), one **rough-notes file** (`rough/{uuid}.md`), and for table-mode tasks one **table file** (`table/{uuid}.json`).

## Features

- **Task file** — YAML metadata plus `Plan`, `Todos`, and `Report` sections in a single document
- **Table mode** — matrix-style tracking with multiple named tables per task (v0.2.0)
- **Rough notes** — append/update/delete delimited note blocks by stable `note_id`
- **24 MCP tools** — full lifecycle from task creation through todos or tables to final report
- **Server info resource** — `taskmanager://server-info` (overview, tools, storage)
- **Agent system prompt** — MCP **prompt** `agent_system_prompt`
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
| `TASK_MANAGER_DATA_DIR` | project root | Base directory; contains `task/`, `rough/`, and `table/` |
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
| Tables | `table_create`, `table_list`, `table_get`, `table_add_rows`, `table_add_columns`, `table_set_cells` |
| Report | `set_report`, `get_report` |
| Rough | `rough_add`, `rough_update`, `rough_delete`, `rough_get`, `rough_list`, `rough_clear` |

### Task modes

`create_task` accepts `mode="todo"` (default) or `mode="table"`. Modes are mutually exclusive:

- **todo** — checklist workflow via `add_todos` / `toggle_todo`
- **table** — matrix workflow via `table_create` / `table_set_cells`

## MCP server info & agent prompt

| Kind | Name / URI | Source | How to use |
|------|------------|--------|------------|
| **Resource** | `taskmanager://server-info` | [`server-info.md`](taskmanager/resources/server-info.md) | MCP **Resources** — server overview, tools, storage, env |
| **Prompt** | `agent_system_prompt` | [`agent-system-prompt.md`](taskmanager/resources/agent-system-prompt.md) | MCP **Prompts** — agent workflow instructions |

## How and when to use the MCP tools

Use this section as an **operator guide**. For agent instructions, use MCP prompt **`agent_system_prompt`** (see above).

### Mental model

| Store | Path | Purpose |
|-------|------|---------|
| Task document | `task/{task_id}.md` | Durable **plan**, trackable **todos** or **table summaries**, final **report** |
| Table document | `table/{task_id}.json` | Matrix data for `mode=table` tasks |
| Rough document | `rough/{task_id}.md` | Disposable **scratch** (ideas, logs, snippets) |

Always keep `task_id` from `create_task` for every later call. Todos use `todo_id`. Tables use `table_id` (e.g. `tbl-a1b2c3d4`). Rough entries use `note_id`.

### Lifecycle phases

```text
1. ORIENT     list_tasks / get_task_metadata
2. START      create_task (mode=todo or mode=table)
3. PLAN       set_plan, add_todos OR table_create
4. WORK       rough_add, rough_update, toggle_todo OR table_set_cells
5. FINISH     set_report
6. HANDOFF    get_task
```

### Table tools

| Tool | When to use |
|------|-------------|
| `table_create` | Define a named table with columns, optional rows, and default cell value |
| `table_list` | See all tables in a task without loading full matrices |
| `table_get` | Read a table; slice by `rows` / `columns` to save tokens |
| `table_add_rows` | Add row keys and fill with defaults or per-row seed values |
| `table_add_columns` | Add columns and fill existing rows with defaults |
| `table_set_cells` | Update values via sparse `updates` or bulk `matrix` patches |

**`table_set_cells` update shapes:**

| Shape | Fields | Effect |
|-------|--------|--------|
| Single cell | `row`, `column`, `value` | Set one cell |
| Partial row | `row`, `values` | Update only listed columns |
| Fill row | `row`, `value` | Same value for all columns in the row |
| Fill column | `column`, `value` | Same value for all rows in the column |

`matrix` accepts a list of `{row, values}` objects; omitted columns in each row stay unchanged.

### Recommended workflow (todo mode)

1. **`create_task`** — `name` = short title, `description` = user goal and constraints.
2. **`set_plan`** — numbered or bulleted steps the agent will follow.
3. **`add_todos`** — concrete checklist aligned with the plan (3–10 items is typical).
4. **While working**
   - **`rough_add`** for exploration, errors, and interim facts.
   - **`toggle_todo`** as each checklist item completes.
   - **`get_todos`** if you lost track of ids or status.
5. **`set_report`** — final summary for the user (what changed, how to verify, open questions).
6. **`get_task`** — optional final read-back before responding to the user.

### Recommended workflow (table mode)

1. **`create_task(mode="table")`**
2. **`set_plan`**
3. **`table_create`** — define tracking grid (e.g. services × status × notes)
4. **While working** — **`table_set_cells`** after each unit of progress; **`rough_add`** for investigation
5. **`table_get`** to verify row states before finishing
6. **`set_report`**

## File formats

**Task** (`task/{uuid}.md`):

```markdown
---
id: "550e8400-e29b-41d4-a716-446655440000"
name: "Implement auth"
description: "Add JWT login flow"
mode: todo
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

**Table** (`table/{uuid}.json`):

```json
{
  "schema_version": 1,
  "tables": {
    "tbl-a1b2c3d4": {
      "name": "API migration",
      "columns": ["status", "owner", "notes"],
      "rows": ["users", "orders"],
      "default": "pending",
      "cells": {
        "users": {"status": "done", "owner": "agent"}
      }
    }
  }
}
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

Project layout: `taskmanager/` (server, parsers, services, tools, resources), `task/`, `rough/`, `table/`, `tests/`.
