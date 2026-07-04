# Task Manager MCP Server

HTTP-based FastMCP server that persists agent work as markdown on disk.

## Endpoints

- **MCP (streamable HTTP):** `http://127.0.0.1:8000/mcp` (default host/port; see environment variables)

## Storage

| Path | Contents |
|------|----------|
| `task/{task_id}.md` | Metadata, Plan, Todos, Report |
| `table/{task_id}.json` | Named tables with row/column cell data (`mode=table` tasks) |
| `rough/{task_id}.md` | Rough notes (facts, checkpoints) |

Base directory is `TASK_MANAGER_DATA_DIR` (defaults to project root). Do not edit these files directly — use MCP tools.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_MANAGER_DATA_DIR` | project root | Base directory for `task/`, `rough/`, and `table/` |
| `TASK_MANAGER_HOST` | `127.0.0.1` | Bind host |
| `TASK_MANAGER_PORT` | `8000` | Bind port |

## Tools (24)

| Category | Tools |
|----------|-------|
| Tasks | `create_task`, `get_task`, `get_task_metadata`, `list_tasks` |
| Plan | `set_plan`, `get_plan` |
| Todos | `add_todos`, `toggle_todo`, `update_todo`, `remove_todo`, `get_todos` |
| Tables | `table_create`, `table_list`, `table_get`, `table_add_rows`, `table_add_columns`, `table_set_cells` |
| Report | `set_report`, `get_report` |
| Rough | `rough_add`, `rough_update`, `rough_delete`, `rough_get`, `rough_list`, `rough_clear` |

## Task modes

- `mode=todo` (default) — checklist tracking via todos
- `mode=table` — matrix tracking via named tables in `table/{task_id}.json`

Modes are mutually exclusive. Existing tasks without `mode` in frontmatter are treated as `todo`.

## Workflow

```text
Todo mode        create_task(mode=todo) → set_plan → add_todos → work/rough/toggle → set_report
Table mode       create_task(mode=table) → set_plan → table_create → work/rough/table_set_cells → set_report
```

Full agent instructions: MCP **prompt** `agent_system_prompt` (see below).

## MCP prompt

Agent instructions are exposed as MCP **prompt** `agent_system_prompt` (not this resource). Use the Prompts panel in your client, or read `taskmanager/resources/agent-system-prompt.md` in the repo.

## Package

- **Name:** taskmanager  
- **Version:** 0.2.0  
