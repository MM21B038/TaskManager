import pytest

from taskmanager.documents.table_doc import TableDocument


def test_create_and_roundtrip():
    doc = TableDocument.create_new()
    table_id, table = doc.create_table(
        "Services",
        ["status", "owner"],
        rows=["users", "orders"],
        default_value="pending",
    )
    text = doc.serialize()
    loaded = TableDocument.parse(text)
    loaded_table = loaded.get_table(table_id)
    assert loaded_table.name == "Services"
    assert loaded_table.rows == ["users", "orders"]
    assert loaded_table.columns == ["status", "owner"]
    cells = loaded.resolve_cells(loaded_table)
    assert cells["users"]["status"] == "pending"


def test_initial_rows_seed():
    doc = TableDocument.create_new()
    table_id, table = doc.create_table(
        "Services",
        ["status", "notes"],
        rows=["users"],
        default_value="pending",
        initial_rows=[{"row": "users", "status": "done", "notes": "ok"}],
    )
    cells = doc.resolve_cells(table)
    assert cells["users"]["status"] == "done"
    assert cells["users"]["notes"] == "ok"


def test_add_rows_and_columns():
    doc = TableDocument.create_new()
    table_id, _ = doc.create_table("T", ["a"], rows=["r1"], default_value="")
    doc.add_rows(table_id, ["r2"], default_value="x")
    doc.add_columns(table_id, ["b"], default_value="y")
    table = doc.get_table(table_id)
    cells = doc.resolve_cells(table)
    assert table.rows == ["r1", "r2"]
    assert table.columns == ["a", "b"]
    assert cells["r2"]["a"] == "x"
    assert cells["r1"]["b"] == "y"


def test_set_single_cell_and_row_fill_and_column_fill():
    doc = TableDocument.create_new()
    table_id, table = doc.create_table(
        "T",
        ["status", "notes"],
        rows=["a", "b"],
        default_value="pending",
    )
    doc.apply_updates(
        table_id,
        updates=[
            {"row": "a", "column": "status", "value": "done"},
            {"row": "b", "value": "blocked"},
            {"column": "notes", "value": "n/a"},
        ],
    )
    cells = doc.resolve_cells(table)
    assert cells["a"]["status"] == "done"
    assert cells["b"]["status"] == "blocked"
    assert cells["b"]["notes"] == "n/a"
    assert cells["a"]["notes"] == "n/a"


def test_partial_row_and_matrix_updates():
    doc = TableDocument.create_new()
    table_id, table = doc.create_table(
        "T",
        ["status", "test", "notes"],
        rows=["users", "orders", "billing"],
        default_value="pending",
    )
    doc.apply_updates(
        table_id,
        updates=[{"row": "users", "values": {"status": "done", "test": "pass"}}],
    )
    doc.apply_updates(
        table_id,
        matrix=[
            {"row": "orders", "values": {"status": "done", "test": "pass", "notes": "migrated"}},
            {"row": "billing", "values": {"status": "blocked", "notes": "waiting"}},
        ],
    )
    cells = doc.resolve_cells(table)
    assert cells["users"]["status"] == "done"
    assert cells["users"]["notes"] == "pending"
    assert cells["orders"]["notes"] == "migrated"
    assert cells["billing"]["test"] == "pending"


def test_sparse_get():
    doc = TableDocument.create_new()
    table_id, table = doc.create_table("T", ["a"], rows=["r1"], default_value="")
    doc.apply_updates(table_id, updates=[{"row": "r1", "column": "a", "value": "set"}])
    sparse = doc.resolve_cells(table, resolved=False)
    assert sparse["r1"] == {"a": "set"}


def test_invalid_update_and_duplicate_names():
    doc = TableDocument.create_new()
    table_id, _ = doc.create_table("T", ["a"], rows=["r1"], default_value="")
    with pytest.raises(ValueError, match="either updates or matrix"):
        doc.apply_updates(table_id, updates=[{"row": "r1"}], matrix=[{"row": "r1", "values": {}}])
    with pytest.raises(ValueError):
        doc.create_table("T", ["b"], rows=["r1"])
    with pytest.raises(ValueError, match="unknown-table"):
        doc.get_table("tbl-missing")
