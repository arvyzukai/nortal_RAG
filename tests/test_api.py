from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_health():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_chat_nortal_services():
    """Test the chat endpoint with a general services question."""
    payload = {"question": "What services does Nortal provide?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "source_documents" in data
    # Note: Depending on mock state/database content, we might not always get sources,
    # but the structure should be correct.
    assert isinstance(data["answer"], str)

def test_chat_ai_hack():
    """Test the chat endpoint with a specific AI Hack question."""
    payload = {"question": "What is Nortal AI Hack?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

