import json
import urllib.request

questions = [
    "hello, i got bitten by a dog what do i do",
    "i got bitten by a spider what should i do"
]

for q in questions:
    try:
        url = "http://localhost:8000/chat/ask"
        payload = json.dumps({"message": q, "patientContext": "Rahul Sharma"}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode('utf-8'))
            print("========================================")
            print("QUESTION:", q)
            print("SENDER:", data.get("sender"))
            print("REPLY:\n" + data.get("reply"))
            print("========================================\n")
    except Exception as e:
        print("ERROR for", q, ":", e)
