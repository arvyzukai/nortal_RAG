import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /health ...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_chat(question):
    print(f"\nTesting /chat with question: '{question}' ...")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"question": question},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result['answer']}")
            print(f"Source Documents: {len(result['source_documents'])}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_health()
    test_chat("What is Nortal AI Hack?")
