def test_ingest_note_success(client):
    response = client.post(
        "/ingest",
        json={
            "source_type": "note",
            "title": "Leave Policy",
            "content": "Employees receive 20 paid leave days every year. " * 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Leave Policy"
    assert data["source_type"] == "note"
    assert data["source_url"] is None
    assert data["chunk_count"] >= 1


def test_ingest_note_empty_content_rejected_by_schema(client):
    response = client.post(
        "/ingest",
        json={"source_type": "note", "title": "Empty Note", "content": ""},
    )
    assert response.status_code == 422


def test_ingest_note_missing_title_rejected_by_schema(client):
    response = client.post(
        "/ingest",
        json={"source_type": "note", "title": "", "content": "Some content"},
    )
    assert response.status_code == 422


def test_ingest_invalid_url_scheme_rejected(client):
    response = client.post(
        "/ingest",
        json={"source_type": "url", "url": "ftp://example.com/file"},
    )
    assert response.status_code == 400
    assert "http" in response.json()["detail"].lower()


def test_ingest_unsupported_source_type_rejected(client):
    response = client.post(
        "/ingest",
        json={"source_type": "pdf", "title": "x", "content": "y"},
    )
    assert response.status_code == 422
