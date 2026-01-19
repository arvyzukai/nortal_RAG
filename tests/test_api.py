import requests
import pytest

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print(f"\nHealth check passed: {data}")

def test_chat_nortal_services():
    """Test the chat endpoint with a general services question."""
    payload = {"question": "What services does Nortal provide?"}
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "source_documents" in data
    assert len(data["source_documents"]) > 0
    print(f"\nChat test (services) passed! Answer snippet: {data['answer'][:100]}...")

def test_chat_ai_hack():
    """Test the chat endpoint with a specific AI Hack question (from verify_api.py)."""
    payload = {"question": "What is Nortal AI Hack?"}
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["source_documents"]) > 0
    print(f"\nChat test (AI Hack) passed! Answer snippet: {data['answer'][:100]}...")

if __name__ == "__main__":
    # This allows running the file directly if needed, 
    # but preferred way is `pytest tests/test_api.py`
    print("Running API tests manually...")
    try:
        test_health()
        test_chat_nortal_services()
        test_chat_ai_hack()
        print("All API tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
