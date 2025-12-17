from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_chat_endpoint_returns_reply():
    payload = {"sessionId": "s1", "message": "Hello", "language": "en"}
    response = client.post("/api/chat/chat", json=payload)
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
    payload = {"sessionId": "s1", "message": "  ", "language": "en"}
    response = client.post("/api/chat/chat", json=payload)
    assert response.status_code == 400


def test_chat_unsupported_language_returns_422():
    payload = {"sessionId": "s1", "message": "Hello", "language": "fr"}
    response = client.post("/api/chat/chat", json=payload)
    # Pydantic validation error from FastAPI
    assert response.status_code == 422
