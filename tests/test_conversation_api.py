from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_chat_endpoint_returns_reply():
    payload = {"sessionId": "s1", "message": "Hello"}
    response = client.post("/api/chat", json=payload, headers={"X-Language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"]
    assert data["language"] == "en"
    assert "metadata" in data
    meta = data["metadata"]
    assert meta["model"]
    assert isinstance(meta["latencyMs"], int)
    assert "sourceDocs" in meta


def test_chat_empty_message_returns_400():
    payload = {"sessionId": "s1", "message": "  "}
    response = client.post("/api/chat", json=payload, headers={"X-Language": "en"})
    assert response.status_code == 400


def test_chat_invalid_language_header_returns_400():
    payload = {"sessionId": "s1", "message": "Hello"}
    response = client.post("/api/chat", json=payload, headers={"X-Language": "fr"})
    assert response.status_code == 400


def test_chat_defaults_to_en_when_no_language_provided():
    payload = {"sessionId": "s1", "message": "Hello"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
