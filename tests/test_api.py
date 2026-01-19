import requests
import time

def test_health():
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    print("Health check passed:", response.json())

def test_chat():
    payload = {"question": "What services does Nortal provide?"}
    response = requests.post("http://localhost:8000/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "source_documents" in data
    print("Chat test passed!")
    print("Answer summary:", data["answer"][:100], "...")

if __name__ == "__main__":
    print("Starting API tests...")
    try:
        test_health()
        test_chat()
        print("All tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
