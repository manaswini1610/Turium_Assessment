def test_query_empty_question_rejected(client):
    response = client.post("/query", json={"question": "", "top_k": 3})
    assert response.status_code == 422


def test_query_top_k_below_minimum_rejected(client):
    response = client.post("/query", json={"question": "test question", "top_k": 0})
    assert response.status_code == 422


def test_query_top_k_above_maximum_rejected(client):
    response = client.post("/query", json={"question": "test question", "top_k": 20})
    assert response.status_code == 422


def test_query_with_no_saved_data_returns_404(client):
    response = client.post("/query", json={"question": "Any question?"})
    assert response.status_code == 404


def test_query_with_data_returns_answer_and_sources(client, monkeypatch):
    client.post(
        "/ingest",
        json={
            "source_type": "note",
            "title": "Leave Policy",
            "content": "Employees receive 20 paid leave days every year.",
        },
    )

    monkeypatch.setattr(
        "app.services.llm_service.generate_answer",
        lambda question, chunks: "Employees receive 20 paid leave days every year.",
    )

    response = client.post("/query", json={"question": "How many leave days?", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "leave" in data["answer"].lower()
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["title"] == "Leave Policy"
    assert data["sources"][0]["source_type"] == "note"
