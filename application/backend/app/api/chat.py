from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["Chat AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    patientContext: str = "Rahul Sharma (Age 34)"


@router.post("/ask")
def ask_ai_assistant(request: ChatRequest):
    msg = request.message.lower()

    if "fever" in msg or "headache" in msg or "temperature" in msg:
        reply = (
            "For mild to moderate fever and headache:\n"
            "• **Recommended OTC**: Paracetamol 650mg post meal.\n"
            "• **Hydration**: Drink plenty of fluids (water, warm soups, ORS).\n"
            "• **Rest**: Ensure 8 hours of restful sleep.\n\n"
            "⚠️ *Warning*: If fever exceeds 102°F or persists over 48 hours, consult a physician immediately."
        )
    elif "cold" in msg or "cough" in msg or "sore throat" in msg:
        reply = (
            "For cold and cough symptoms:\n"
            "• **Supplements**: Vitamin C 500mg chewable tablets daily.\n"
            "• **Home Remedies**: Warm saline water gargles 3x daily, steam inhalation.\n"
            "• **Precaution**: Avoid chilled beverages and dusty environments."
        )
    elif "blood" in msg or "emergency" in msg:
        reply = (
            "🚨 **Emergency Guidance**:\n"
            "If this is an immediate medical emergency, please call **108** or tap the **Emergency SOS** button in Home view."
        )
    else:
        reply = (
            f"Hello! I am your AI Medical Assistant analyzing queries for **{request.patientContext}**.\n\n"
            f"Regarding your query: *\"{request.message}\"*\n"
            "• Always follow doctor-prescribed dosages.\n"
            "• You can use the Medicine Scanner or Prescription Scanner to verify active ingredients."
        )

    return {
        "status": "success",
        "reply": reply,
        "timestamp": "Just now",
        "sender": "CuraBot AI"
    }
