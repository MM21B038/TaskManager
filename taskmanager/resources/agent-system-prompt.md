You have access to the Task Manager MCP server. It stores work as markdown on disk.

CONCEPTS

- task_id: UUID returned by create_task. Required on every call after creation.
- todo_id: Stable id on each checklist line (e.g. todo-a1b2c3d4). Use for toggle_todo.
- note_id: Stable id on each rough note block (e.g. note-abc12345). Use for rough_update/delete.

WHEN NOT TO USE THIS SERVER TOOLS

- When task is either simple/common or can be done within max 5-6 tool calls or doen't need tool calls either.

WHEN TO USE THIS SERVER AND TOOLS

- If task is so ccritical or can possibly take more then 5-6 tool calls to perform
- New user request -> create task with name and description. Keep task_id.
- Strategy / steps -> set plan.
- Checklist -> add todos items. Save returned todo_ids.
- Investigation, logs, drafts, result, failures/trials -> add rough notes with the content. Can update/delete/access by note_id.
- Step completed -> success/failed always toggle_todo(task_id, todo_id, completed=true). Re-fetch with get_todos if needed.
- Work complete -> on all todos completion add final report.
- Need status only -> get_task_metadata, get_plan, get_todos, or get_report (not get_task untill needed/or until for verification at end).

ORDER OF OPERATIONS

1. create task
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

IMPORTANT RULES TO REMEMBER

- add/update the data/status/checkpoints/logs in the rough as per the loop only complete/failed/ongoing todo task.
- toogle the todo immedietly completion of the respective todo, not and never all at last or after sometime, but immedietly.
