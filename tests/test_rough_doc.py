from taskmanager.documents.rough_doc import RoughDocument


def test_note_crud_roundtrip():
    doc = RoughDocument.create_new("task-1")
    doc.add_note("First note")
    doc.add_note("## heading inside\n\n```py\nx=1\n```", note_id="note-custom")
    text = doc.serialize()
    loaded = RoughDocument.parse(text)
    assert len(loaded.notes) == 2
    assert loaded.get_note("note-custom").content.startswith("## heading")

    loaded.update_note("note-custom", "Updated content")
    loaded.delete_note(loaded.notes[0].note_id)
    assert len(loaded.notes) == 1
    assert loaded.get_note("note-custom").content == "Updated content"


def test_clear_notes():
    doc = RoughDocument.create_new("task-1")
    doc.add_note("a")
    doc.add_note("b")
    removed = doc.clear_notes()
    assert removed == 2
    assert doc.serialize()
    assert len(RoughDocument.parse(doc.serialize()).notes) == 0
