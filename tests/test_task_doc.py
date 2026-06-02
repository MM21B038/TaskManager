from taskmanager.documents.task_doc import TaskDocument


def test_create_and_roundtrip():
    doc = TaskDocument.create_new(
        "550e8400-e29b-41d4-a716-446655440000",
        "Auth",
        "JWT flow",
        initial_plan="Step 1",
        initial_todos=["Write tests", "Deploy"],
    )
    text = doc.serialize()
    loaded = TaskDocument.parse(text)
    assert loaded.metadata["name"] == "Auth"
    assert loaded.get_plan() == "Step 1"
    todos = loaded.parse_todos()
    assert len(todos) == 2
    assert todos[0].text == "Write tests"
    assert todos[1].text == "Deploy"


def test_toggle_todo():
    doc = TaskDocument.create_new("id-1", "T", "D", initial_todos=["A"])
    todo_id = doc.parse_todos()[0].id
    doc.toggle_todo(todo_id, completed=True)
    assert doc.parse_todos()[0].completed is True
    doc.toggle_todo(todo_id, completed=None)
    assert doc.parse_todos()[0].completed is False


def test_update_and_remove_todo():
    doc = TaskDocument.create_new("id-1", "T", "D", initial_todos=["A", "B"])
    tid = doc.parse_todos()[0].id
    doc.update_todo(tid, "Updated A")
    assert doc.parse_todos()[0].text == "Updated A"
    doc.remove_todo(tid)
    assert len(doc.parse_todos()) == 1


def test_report_section():
    doc = TaskDocument.create_new("id-1", "T", "D")
    doc.set_report("Done.")
    assert doc.get_report() == "Done."
    text = doc.serialize()
    assert "Done." in TaskDocument.parse(text).get_report()
