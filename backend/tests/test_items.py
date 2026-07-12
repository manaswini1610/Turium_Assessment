def test_get_items_empty_state(client):
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


def test_get_items_after_ingestion_ordered_newest_first(client):
    client.post(
        "/ingest",
        json={"source_type": "note", "title": "First Note", "content": "First note content."},
    )
    client.post(
        "/ingest",
        json={"source_type": "note", "title": "Second Note", "content": "Second note content."},
    )

    response = client.get("/items")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "Second Note"
    assert data[1]["title"] == "First Note"
    assert "embedding" not in data[0]
    assert "raw_content" not in data[0]
    assert "content_preview" in data[0]
