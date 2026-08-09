import requests
import json

BASE_URL = "https://ai-healthcare-system-eta.vercel.app"

def test_api():
    print(f"Testing API connection at {BASE_URL}...")
    
    # 1. Test GET /store/medicines
    try:
        r = requests.get(f"{BASE_URL}/store/medicines", timeout=10)
        print(f"GET /store/medicines: Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Received {len(data) if isinstance(data, list) else 'non-list'} medicines.")
        else:
            print(f"  Response: {r.text[:150]}")
    except Exception as e:
        print(f"  Error testing /store/medicines: {e}")

    # 2. Test POST /chat/ask
    try:
        payload = {"question": "What is Paracetamol used for?", "user_id": "test_user"}
        r = requests.post(f"{BASE_URL}/chat/ask", json=payload, timeout=15)
        print(f"POST /chat/ask: Status {r.status_code}")
        if r.status_code == 200:
            res = r.json()
            print(f"  Chat Answer snippet: {str(res)[:150]}...")
        else:
            print(f"  Response: {r.text[:150]}")
    except Exception as e:
        print(f"  Error testing /chat/ask: {e}")

if __name__ == "__main__":
    test_api()
