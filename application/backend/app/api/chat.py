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
        f"You are CuraBot AI, a warm, clear, and friendly medical AI assistant. "
        f"The patient is: {patient_context}. "
        f"Give simple, easy-to-understand advice in bullet points. Use bold text for key medicine names and simple English."
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

    matched_symptoms = [s for s in SYMPTOMS_DB if any(kw in msg for kw in [s.get("symptom_name", "").lower()] + [c.lower() for c in s.get("possible_causes", [])])]
    matched_diseases = [d for d in DISEASES_DB if any(kw in msg for kw in [d.get("disease_name", "").lower()] + [s.lower() for s in d.get("symptoms", [])])]
    matched_meds = [m for m in MEDICINES_DB if m.get("brand_name", "").lower() in msg or m.get("generic_name", "").lower() in msg or any(u.lower() in msg for u in m.get("uses", []))]

    lines = []
    patient_first_name = patient_context.split()[0] if patient_context else "there"
    lines.append(f"👋 **Hi {patient_first_name}! Here is your quick medical guide:**\n")

    if matched_meds:
        med = matched_meds[0]
        lines.append(f"💊 **Medicine Info: {med.get('brand_name')}** ({med.get('strength')})")
        lines.append(f"• **Active Salt**: {med.get('composition', med.get('generic_name'))}")
        lines.append(f"• **How to take**: {med.get('dosage')}")
        lines.append(f"• **Used for**: {', '.join(med.get('uses', []))}")
        if med.get('warnings'):
            lines.append(f"• ⚠️ **Precaution**: {med.get('warnings')[0]}")
        lines.append("")

    elif "fever" in msg or "headache" in msg or "pain" in msg:
        lines.append("🤒 **What to do for Fever & Pain:**")
        lines.append("• **Medicine**: Take **Dolo 650mg** (Paracetamol) after food.")
        lines.append("• **Rest & Fluid**: Sleep well and drink warm water or ORS.")
        lines.append("• **Doctor Alert**: Consult a doctor if fever stays > 2 days.")
        lines.append("")

    elif "stomach" in msg or "acid" in msg or "ulcer" in msg or "gas" in msg or "heartburn" in msg:
        lines.append("🫃 **What to do for Acid & Stomach care:**")
        lines.append("• **Medicine**: Take **Pan 40** (Pantoprazole 40mg) 30 mins before breakfast.")
        lines.append("• **Diet**: Avoid spicy foods, coffee, and carbonated drinks.")
        lines.append("")

    elif "cold" in msg or "cough" in msg or "throat" in msg:
        lines.append("🤧 **What to do for Cold & Cough:**")
        lines.append("• **Medicine**: Take **Cetzine 10** for sneezing or **Limcee 500mg** (Vitamin C).")
        lines.append("• **Home Care**: Gargle with warm salt water 2 times daily.")
        lines.append("")

    elif matched_symptoms:
        sym = matched_symptoms[0]
        lines.append(f"📋 **Symptom Guide: {sym.get('symptom_name')}**")
        lines.append(f"• **Home Care**: {sym.get('home_care')}")
        lines.append(f"• **Specialist**: Consult a **{sym.get('suggested_specialist')}** if needed.")
        lines.append("")

    else:
        lines.append("💡 **General Health Care Advice:**")
        lines.append("• Drink 8+ glasses of water daily and rest well.")
        lines.append("• You can search any tablet or scan your prescription slip in CuraAssist.")
        lines.append("")

    lines.append("🚨 *If you experience chest pain or severe difficulty breathing, please call 108 immediately.*")

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
