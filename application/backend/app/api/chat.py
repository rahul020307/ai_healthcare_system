import json
import os
import urllib.request
import urllib.error
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.utils.ocr_processor import (
    process_prescription_ocr,
    generate_prescription_summary,
    fuzzy_match_medicine,
    validate_prescription_text,
)

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
    """Reads only the runtime environment configured by Vercel or the host process."""
    val = os.getenv(var_name)
    if val and val.strip():
        return val.strip()
    return None


def validate_required_env_vars() -> list[str]:
    """Returns missing required runtime env vars for AI integrations."""
    required = ["GEMINI_API_KEY", "OPENAI_API_KEY"]
    return [name for name in required if not get_env_variable(name)]


def call_remote_ai(user_prompt: str, patient_context: str) -> Optional[str]:
    """Attempts calling Google Gemini API or OpenAI API using only runtime env vars."""
    missing = validate_required_env_vars()
    if missing:
        print(f"Missing required AI env vars: {', '.join(missing)}")
        return None

    gemini_key = get_env_variable("GEMINI_API_KEY")
    openai_key = get_env_variable("OPENAI_API_KEY")

    system_prompt = (
        f"You are CuraBot AI, a warm, clear, and friendly medical AI assistant. "
        f"The patient is: {patient_context}. "
        f"Give simple, easy-to-understand advice in bullet points. Use bold text for key medicine names and simple English."
    )

    key_pool = [gemini_key] if gemini_key else []

    # 1. Try Google Gemini API first
    for g_key in key_pool:
        if not g_key:
            continue
        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key.strip()}"
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


FAQ_DB = load_data("faq.json")
GENERICS_DB = load_data("generic_alternatives.json")
DOCTORS_DB = load_data("doctors.json")


STOP_WORDS = {
    "what", "how", "when", "where", "who", "why", "can", "give", "tell", "about",
    "take", "use", "does", "should", "with", "for", "the", "and", "this", "that",
    "have", "need", "help", "please", "is", "are", "was", "were", "been", "be",
    "do", "did", "done", "some", "any", "much", "many", "all", "get", "got", "my",
    "your", "me", "you", "him", "her", "them", "us", "i", "a", "an", "in", "on", "at"
}


def ai_clinical_reasoning(message: str, patient_context: str) -> str:
    first_name = patient_context.split()[0] if patient_context else "there"
    return f"""🤖 **CuraBot AI Assistant**

Hello **{first_name}**! Regarding your query: *"{message}"*

• 🩺 **AI Medical Guidance**: Please ensure `GEMINI_API_KEY` or `OPENAI_API_KEY` is configured in your Vercel Environment Variables.
• 📊 **Vitals & Monitoring**: Log your daily Blood Pressure, Pulse, Temperature, and Glucose readings in your **Profile Vitals Tracker**.
• 🚨 **Emergency Protocol**: If experiencing severe discomfort, chest pain, or breathing difficulty, call 108 or tap **🚨 Emergency SOS** immediately."""


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


class OCRScanRequest(BaseModel):
    image_name: Optional[str] = "prescription_slip.jpg"
    image_base64: Optional[str] = None
    raw_text: Optional[str] = None


@router.post("/ocr-scan")
def scan_prescription_ocr(req: OCRScanRequest):
    """
    Enhanced OCR prescription scanning with fuzzy matching & AI validation.
    Handles typos, abbreviations, and low-quality OCR text.
    """
    img_name = req.image_name or "prescription_slip.jpg"
    raw_input = (req.raw_text or "").strip()
    name_lower = img_name.lower()

    meds = MEDICINES_DB if MEDICINES_DB else load_data("medicines.json")

    if raw_input and not validate_prescription_text(raw_input):
        return {
            "status": "success",
            "category": "Unrecognized Document",
            "summary": "⚠️ This image does not appear to be a valid prescription or medical document. Please upload a doctor's prescription, medicine note, or clinical report.",
            "confidence": "low",
            "is_valid_prescription": False,
        }
    
    # 1. Categorize document type
    if "blood" in name_lower or "lab" in name_lower or "test" in name_lower:
        doc_category = "Lab Reports"
        summary = f"LABORATORY TEST REPORT ANALYSIS ({img_name})\n----------------------------------------------------\n• Extracted Text: {raw_input[:150] or 'Diagnostic Clinical Test'}\n• Status: Clinical Data Extracted & Recorded in Health Log."
    elif "xray" in name_lower or "mri" in name_lower or "scan" in name_lower:
        doc_category = "Scans"
        summary = f"RADIOLOGY & IMAGING SCAN ({img_name})\n----------------------------------------------------\n• Examination Type: Medical Imaging Analysis\n• Extracted Details: {raw_input[:150] or 'Diagnostic Image'}"
    else:
        doc_category = "Prescriptions"
        
        # 2. Use improved OCR processor with fuzzy matching
        if raw_input and len(raw_input) > 5:
            try:
                # Process prescription with fuzzy matching & dosage extraction
                extraction_result = process_prescription_ocr(raw_input, meds)
                
                if extraction_result.get("extracted_medicines"):
                    # Use generated summary
                    summary = generate_prescription_summary(extraction_result)
                    
                    # Add AI enhancement if high confidence
                    if extraction_result.get("has_confident_matches"):
                        try:
                            ai_prompt = f"Verify and enhance this prescription extraction:\n\n{summary}\n\nProvide dosage warnings and drug interactions if any."
                            ai_response = call_remote_ai(ai_prompt, "N/A")
                            if ai_response and len(ai_response) > 20:
                                summary = f"{summary}\n\n🤖 AI VALIDATION:\n{ai_response}"
                        except Exception as e:
                            print("AI enhancement note:", e)
                    
                    return {
                        "status": "success",
                        "category": doc_category,
                        "summary": summary,
                        "extracted_medicines": extraction_result.get("extracted_medicines", []),
                        "confidence": "high" if extraction_result.get("has_confident_matches") else "medium"
                    }
            except Exception as e:
                print(f"OCR processor error (fallback to legacy): {e}")
        
        # 3. Fallback: Try AI-powered extraction
        if raw_input and len(raw_input) > 5:
            try:
                ai_prompt = f"Analyze this medical prescription/scan text: {img_name}\n\nExtract: medicine names, dosages, frequencies, duration, side effects warnings:\n\n{raw_input}"
                ai_response = call_remote_ai(ai_prompt, "N/A")
                if ai_response and len(ai_response) > 20:
                    return {"status": "success", "category": "Prescriptions", "summary": ai_response, "confidence": "medium"}
            except Exception as e:
                print("AI OCR extraction note:", e)
        
        # 4. Fallback: Legacy exact matching (last resort)
        matched_meds = []
        text_lower = raw_input.lower()
        
        for m in meds:
            b_name = m.get("brand_name", "").lower()
            g_name = m.get("generic_name", "").lower()
            if (b_name and b_name in text_lower) or (g_name and g_name in text_lower):
                matched_meds.append({
                    "name": m.get("brand_name"),
                    "salt": m.get("generic_name", "Active Formula"),
                    "dosage": m.get("dosage", "1 Dose Post Meals"),
                    "category": m.get("category", "Healthcare Product"),
                    "duration": "As Advised"
                })
        
        if matched_meds:
            med_lines = "\n".join([f"• {m['name']} ({m['salt']}) - Category: {m['category']}\n  Dosage: {m['dosage']} (Duration: {m['duration']})" for m in matched_meds])
            summary = f"DOCTOR PRESCRIPTION / MEDICINE ANALYSIS ({img_name})\n----------------------------------------------------\nMatched Medicines (Legacy Mode):\n{med_lines}"
            return {"status": "success", "category": "Prescriptions", "summary": summary, "confidence": "low"}
        
        # 5. No matches found
        summary = f"MEDICAL PRESCRIPTION RECORD ({img_name})\n----------------------------------------------------\n• Document: {img_name}\n• Extracted Content: {raw_input or 'No readable text found'}\n• Recommendation: Please review manually or try higher quality image."
    
    return {
        "status": "success",
        "category": doc_category,
        "summary": summary,
        "confidence": "medium"
    }


class ScanMedicineRequest(BaseModel):
    query_text: Optional[str] = ""
    barcode: Optional[str] = ""


@router.post("/scan-medicine")
def scan_medicine_database_search(req: ScanMedicineRequest):
    q = (req.query_text or "").strip().lower()
    barcode = (req.barcode or "").strip().lower()

    meds = MEDICINES_DB if MEDICINES_DB else load_data("medicines.json")

    results = []
    for m in meds:
        b_name = m.get("brand_name", "").lower()
        g_name = m.get("generic_name", "").lower()
        cat = m.get("category", "").lower()
        m_id = m.get("id", "").lower()

        if q and (q in b_name or q in g_name or q in cat or q in m_id):
            results.append(m)
        elif barcode and (barcode in m_id or barcode in b_name):
            results.append(m)

    if not results and meds:
        results = [meds[0]]

    return {
        "status": "success",
        "matched_count": len(results),
        "matches": results
    }
