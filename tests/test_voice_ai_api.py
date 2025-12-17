from io import BytesIO

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_voice_query_endpoint():
    file_content = b"fake audio data"
    files = {"audio_file": ("test.wav", BytesIO(file_content), "audio/wav")}
    data = {"session_id": "s1", "language": "en"}
    response = client.post("/api/voice/query", data=data, files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"]
    assert body["reply"]


def test_templates_and_send_notification():
    response = client.get("/api/voice/templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 1
    template_id = templates[0]["id"]

    send_payload = {
        "templateId": template_id,
        "channel": "sms",
        "previewOnly": True,
        "language": "en",
    }
    send_response = client.post("/api/voice/send", json=send_payload)
    assert send_response.status_code == 200
    send_data = send_response.json()
    assert send_data["status"] in {"preview", "sent"}
