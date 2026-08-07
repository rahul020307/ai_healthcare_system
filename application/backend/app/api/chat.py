import json
import os
import urllib.request
import urllib.error
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


def get_env_variable(var_name: str) -> Optional[str]:
    """Reads environment variable from os.getenv or parses .env file directly."""
    val = os.getenv(var_name)
    if val and val.strip():
        return val.strip()

    env_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == var_name:
                                return v.strip().strip("'\"")
            except Exception as e:
                print(f"Error reading .env at {env_path}:", e)
    return None


def call_remote_ai(user_prompt: str, patient_context: str) -> Optional[str]:
    """Attempts calling Google Gemini API or OpenAI API using keys loaded from .env."""
    gemini_key = get_env_variable("GEMINI_API_KEY")
    openai_key = get_env_variable("OPENAI_API_KEY")

    system_prompt = (
        f"You are CuraBot AI, a helpful, empathetic, and scientifically accurate medical AI health assistant. "
        f"The patient context is: {patient_context}. "
        f"Provide clear, structured, clinical guidance with bullet points. Include OTC suggestions when relevant, "
        f"and always mention safety precautions or when to consult a doctor."
    )

    # 1. Try Google Gemini API first
    if gemini_key:
        for model in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = json.dumps({
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{system_prompt}\n\nPatient Query: {user_prompt}"}
                            ]
                        }
                    ]
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts:
                                return parts[0].get("text")
            except Exception as e:
                print(f"Gemini API ({model}) call note:", e)

    # 2. Try OpenAI API
    if openai_key:
        for model in ["gpt-3.5-turbo", "gpt-4o-mini"]:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.4
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                })
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content")
            except Exception as e:
                print(f"OpenAI API ({model}) call note:", e)

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
