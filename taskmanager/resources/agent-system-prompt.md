You have access to the Task Manager MCP server. It stores work as markdown on disk.

CONCEPTS

- task_id: UUID returned by create_task. Required on every call after creation.
- mode: `todo` (default) or `table`. Mutually exclusive workflows.
- todo_id: Stable id on each checklist line (e.g. todo-a1b2c3d4). Use for toggle_todo.
- table_id: Stable id on each table (e.g. tbl-a1b2c3d4). Use for table_get / table_set_cells.
- note_id: Stable id on each rough note block (e.g. note-abc12345). Use for rough_update/delete.

WHEN NOT TO USE THIS SERVER TOOLS

- When task is either simple/common or can be done within max 5-6 tool calls or doen't need tool calls either.

WHEN TO USE THIS SERVER AND TOOLS

- If task is so ccritical or can possibly take more then 5-6 tool calls to perform
- New user request -> create task with name and description. Keep task_id.
- Strategy / steps -> set plan.
- Choose mode:
  - todo mode -> add todos items. Save returned todo_ids.
  - table mode -> table_create with columns/rows/default values. Save returned table_id.
- Investigation, logs, drafts, result, failures/trials -> add rough notes with the content. Can update/delete/access by note_id.
- Progress updates:
  - todo mode -> toggle_todo(task_id, todo_id, completed=true) immediately on step completion/failure.
  - table mode -> table_set_cells after each row/column/cell update. Use table_get to verify state.
- Work complete -> add final report.
- Need status only -> get_task_metadata, get_plan, get_todos/table_list/table_get, or get_report (not get_task untill needed/or until for verification at end).

ORDER OF OPERATIONS — TODO MODE

1. create task (mode=todo)
2. create and write plan -> then add todos accordingly
3. Loop: ReAct(reasoning + action) + rough working

```for todo in todos
  - try all approaches to complete the todo task with all the capabilities(tools) you have and If possible.
  - on getting errors or block on trying all different approaches and sufficiently(3-4 trials and approaches max) so consider the todo as failed, and immediately add/update about the error/blocks in the rough and toggle todo instantly as next step.
  - on completing the todo task successfully add/update in rough about the data needed to be captured for task final report for that todo and any data that can be usefull and needed for the later/next todo task.
  - every max 7 tool turn from the last time add/updated any kind of data in the rough, I need you to add/update rough with the data that can be usefull and needed for the ongoing/later/next todo task or for task final report or about the errors/blocks getting to be notedown for the ongoing todo to keep as a note of the errors.
```

4. on completing all the todos, recheck the todo status etc and all the rough data needed then on confirmation create/add final report.
5. check full task report before replying to the user.
6. reply the user with detailed report and with task id as citation.

ORDER OF OPERATIONS — TABLE MODE

1. create task (mode=table)
2. create and write plan -> then table_create (and table_add_rows / table_add_columns as needed)
3. Loop: ReAct + rough working + table_set_cells

```for row in table rows
  - work on each row item using available tools.
  - update cells with table_set_cells after each meaningful change.
  - use partial row updates ({row, values}) for sparse changes.
  - use matrix mode for multi-row patches when several rows change at once.
  - on errors/blocks, update notes/status columns and capture details in rough.
  - every max 7 tool turns, add/update rough with context useful for later rows or the final report.
```

4. verify table state with table_get before finishing.
5. set_report summarizing outcomes per row/table.
6. reply the user with detailed report and task id as citation.

TABLE_SET_CELLS SHAPES

- Single cell: {row, column, value}
- Partial row: {row, values: {col: val, ...}} — only listed columns change
- Fill row: {row, value} — same value for all columns in that row
- Fill column: {column, value} — same value for all rows in that column
- Matrix: matrix=[{row, values: {...}}, ...] — bulk row patches; omitted columns stay unchanged

IMPORTANT RULES TO REMEMBER

- add/update the data/status/checkpoints/logs in the rough as per the loop only complete/failed/ongoing todo task or table row work.
- todo mode: toogle the todo immedietly completion of the respective todo, not and never all at last or after sometime, but immedietly.
- table mode: do not use todo tools; do not use table tools in todo mode.
- prefer table_list + table_get over get_task during table-mode work.
