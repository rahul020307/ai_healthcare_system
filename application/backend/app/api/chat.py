import json
import os
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/chat", tags=["Chat AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    patientContext: Optional[str] = "Rahul Sharma (Age 34)"


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


# Preload dataset knowledge bases for AI contextual reasoning
DISEASES_DB = load_data("diseases.json")
SYMPTOMS_DB = load_data("symptoms.json")
MEDICINES_DB = load_data("medicines.json")
INTERACTIONS_DB = load_data("drug_interactions.json")
FIRST_AID_DB = load_data("first_aid.json")


def call_remote_ai(user_prompt: str, patient_context: str) -> Optional[str]:
    """Attempts calling Google Gemini API or OpenAI API if API keys are configured in environment."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    system_prompt = (
        f"You are CuraBot AI, a helpful, empathetic, and scientifically accurate medical AI health assistant. "
        f"The patient context is: {patient_context}. "
        f"Provide clear, structured, clinical guidance with bullet points. Include OTC suggestions when relevant, "
        f"and always mention safety precautions or when to consult a doctor."
    )

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt},
                            {"text": f"Patient Query: {user_prompt}"}
                        ]
                    }
                ]
            }
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("Gemini API call error:", e)

    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4
            }
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print("OpenAI API call error:", e)

    return None


def ai_clinical_reasoning(message: str, patient_context: str) -> str:
    msg = message.lower()

    # 1. Search Symptoms DB
    matched_symptoms = [s for s in SYMPTOMS_DB if any(kw in msg for kw in [s.get("symptom_name", "").lower()] + [c.lower() for c in s.get("possible_causes", [])])]

    # 2. Search Diseases DB
    matched_diseases = [d for d in DISEASES_DB if any(kw in msg for kw in [d.get("disease_name", "").lower()] + [s.lower() for s in d.get("symptoms", [])])]

    # 3. Search Medicines DB
    matched_meds = [m for m in MEDICINES_DB if m.get("brand_name", "").lower() in msg or m.get("generic_name", "").lower() in msg or any(u.lower() in msg for u in m.get("uses", []))]

    # Build AI clinical response
    lines = [f"🤖 **CuraBot AI Clinical Analysis for {patient_context}**:\n"]

    if matched_symptoms:
        sym = matched_symptoms[0]
        lines.append(f"• **Symptom Recognized**: {sym.get('symptom_name', 'General Discomfort')} (Severity: {sym.get('severity', 'Moderate')})")
        lines.append(f"• **Suggested Specialist**: {sym.get('suggested_specialist', 'General Physician')}")
        lines.append(f"• **Home Care**: {sym.get('home_care', 'Stay hydrated and rest')}\n")

    if matched_diseases:
        dis = matched_diseases[0]
        lines.append(f"• **Possible Condition Correlation**: {dis.get('disease_name')}")
        lines.append(f"• **Prevention/Care**: {dis.get('prevention', 'Consult healthcare provider')}\n")

    if matched_meds:
        med = matched_meds[0]
        lines.append(f"💊 **Medication Insights ({med.get('brand_name')})**:")
        lines.append(f"• Active Salt: {med.get('composition', med.get('generic_name'))}")
        lines.append(f"• Typical Dosage: {med.get('dosage')}")
        lines.append(f"• Primary Uses: {', '.join(med.get('uses', []))}")
        if med.get('warnings'):
            lines.append(f"• ⚠️ Precaution: {med.get('warnings')[0]}\n")
    elif "fever" in msg or "headache" in msg or "pain" in msg:
        lines.append("💊 **Recommended OTC Relief**:")
        lines.append("• **Paracetamol 650mg**: 1 tablet post meal for fever and pain reduction.")
        lines.append("• **Hydration**: Consume 2.5L+ fluids (water, ORS, warm broths).")
        lines.append("• **Rest**: Adequate bed rest is strongly advised.\n")
    elif "stomach" in msg or "acid" in msg or "ulcer" in msg or "gas" in msg:
        lines.append("💊 **Recommended Gastro Relief**:")
        lines.append("• **Pan 40 (Pantoprazole 40mg)**: 1 tablet 30 minutes before breakfast.")
        lines.append("• **Dietary Advice**: Avoid spicy, greasy, or caffeine-rich foods.\n")
    elif "cough" in msg or "throat" in msg or "cold" in msg:
        lines.append("💊 **Cold & Respiratory Care**:")
        lines.append("• **Vitamin C 500mg**: Daily chewable tablet for immune support.")
        lines.append("• **Steam Inhalation**: 2x daily with eucalyptus/saline.")
        lines.append("• **Gargle**: Warm salt water gargles every 6 hours.\n")
    else:
        lines.append(f"• **AI Observation**: Analysis of *\"{message}\"* indicates general wellness query.")
        lines.append("• **General Guidance**: Maintain balanced nutrition, hydration, and regular exercise.")
        lines.append("• **Medicine Insights**: You can use the Medicine Scanner or Search Bar to explore active ingredients and dosages.\n")

    lines.append("⚠️ *Medical Notice*: CuraBot AI provides clinical informational support based on registered healthcare datasets. For severe or persisting symptoms beyond 48h, please consult a certified doctor.")

    return "\n".join(lines)


@router.post("/ask")
def ask_ai_assistant(request: ChatRequest):
    patient_ctx = request.patientContext or "Rahul Sharma (Age 34)"

    # Try live Gemini / OpenAI remote AI API first
    remote_reply = call_remote_ai(request.message, patient_ctx)

    if remote_reply:
        reply = remote_reply
        source = "Google Gemini AI (Live API)"
    else:
        reply = ai_clinical_reasoning(request.message, patient_ctx)
        source = "CuraBot Clinical Knowledge AI Engine"

    return {
        "status": "success",
        "reply": reply,
        "timestamp": "Just now",
        "sender": source
    }
