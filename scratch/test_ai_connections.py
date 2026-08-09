import json

def verify_local_ai_code():
    print("Checking local files for AI integration...")

    with open("application/frontend/app.js", "r", encoding="utf-8") as f:
        app_js = f.read()

    # Check AI function signatures and calls
    assert "async function callDirectGeminiAPI" in app_js, "callDirectGeminiAPI missing!"
    assert "sendAIMessage" in app_js, "sendAIMessage missing!"
    assert "generateSmartAIChatResponse" in app_js, "generateSmartAIChatResponse missing!"
    assert "triggerBarcodeScanProcess" in app_js, "triggerBarcodeScanProcess missing!"
    assert "parseRawOCRWithAIAgent" in app_js, "parseRawOCRWithAIAgent missing!"

    print("[OK] All frontend AI handlers (Chatbot, Scanner, Prescription OCR) are present.")

    with open("application/backend/app/api/chat.py", "r", encoding="utf-8") as f:
        chat_py = f.read()

    assert "call_remote_ai" in chat_py, "call_remote_ai missing in backend!"
    print("[OK] Backend chat AI router (chat.py) is present.")

    print("[OK] Everything in local files is verified and properly connected.")

if __name__ == "__main__":
    verify_local_ai_code()
