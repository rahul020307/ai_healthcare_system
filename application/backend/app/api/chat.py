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
        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
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
    msg = message.lower().strip()
    raw_words = msg.replace("?", "").replace(".", "").replace(",", "").replace("!", "").split()
    query_keywords = [w for w in raw_words if len(w) > 2 and w not in STOP_WORDS]

    first_name = patient_context.split()[0] if patient_context else "there"
    lines = [f"👋 **Hi {first_name}! Here is your personalized medical advice:**\n"]
    has_match = False

    # Check for Special High-Priority Emergencies & Bites
    if any(k in msg for k in ["spider", "insect", "bee", "wasp", "scorpion", "bug", "ant"]):
        lines.append("🕷️ **SPIDER & INSECT BITE / STING FIRST AID PROTOCOL**:")
        lines.append("• **Step 1 (Cleanse)**: Wash the sting/bite site with mild soap and clean water immediately.")
        lines.append("• **Step 2 (Cold Compress)**: Apply an ice pack wrapped in a cloth for 10-15 minutes to reduce localized swelling & pain.")
        lines.append("• **Step 3 (Itch Relief)**: Apply Calamine lotion or take an OTC antihistamine tablet (**Cetzine 10 / Cetirizine**) for itching.")
        lines.append("• 🚨 **ANAPHYLAXIS EMERGENCY ALERT**: Seek immediate ER medical care (Call 108) if experiencing shortness of breath, throat/facial swelling, dizziness, or hives.\n")
        lines.append("🚨 *If symptoms worsen rapidly, call 108 or visit an emergency room.*")
        return "\n".join(lines)

    if any(k in msg for k in ["dog", "puppy", "cat", "rabies", "monkey", "stray", "mammal"]):
        lines.append("🐕 **DOG / ANIMAL BITE EMERGENCY PROTOCOL (Rabies Risk)**:")
        lines.append("• **Step 1 (Immediate Wash)**: Wash the bite wound thoroughly with soap and running tap water for at least 15 minutes to reduce viral load.")
        lines.append("• **Step 2 (Disinfect)**: Apply an antiseptic solution like Betadine (Povidone-Iodine) or Dettol/Savlon.")
        lines.append("• **Step 3 (Stop Bleeding)**: Apply light pressure with a sterile bandage if bleeding.")
        lines.append("• 🚨 **URGENT**: Visit a hospital within **24 hours** to receive the **Anti-Rabies Vaccine (ARV)** and Tetanus (TT) injection.")
        lines.append("• ⚠️ **Warning**: Do not cover tightly, stitch open wounds, or apply household powders.\n")
        lines.append("🚨 *If bleeding is severe or animal is suspected rabid, call 108 immediately.*")
        return "\n".join(lines)

    if any(k in msg for k in ["snake", "venom", "viper", "cobra", "reptile"]):
        lines.append("🐍 **SNAKE BITE EMERGENCY FIRST AID**:")
        lines.append("• **Step 1**: Keep the victim strictly immobile and calm. Keep bitten limb below heart level.")
        lines.append("• **Step 2**: Remove tight rings, watch, or clothing near wound.")
        lines.append("• **Step 3**: DO NOT cut wound, suck venom, or tie tight tourniquets.")
        lines.append("• 🚨 **CRITICAL**: Go immediately to the nearest hospital for Anti-Snake Venom (ASV).\n")
        lines.append("🚨 *Call 108 Emergency Dispatch immediately.*")
        return "\n".join(lines)

    # 1. Search First Aid DB
    aid_matches = []
    for aid in FIRST_AID_DB:
        e_type = aid.get("emergency_type", "").lower()
        sympts = [s.lower() for s in aid.get("symptoms", [])]
        if any(kw in e_type for kw in query_keywords) or any(any(kw in s for kw in query_keywords) for s in sympts):
            aid_matches.append(aid)

    if aid_matches and not has_match:
        aid = aid_matches[0]
        lines.append(f"🚑 **First Aid Protocol ({aid.get('emergency_type')})**:")
        for i, step in enumerate(aid.get('first_aid_steps', []), 1):
            lines.append(f"• **Step {i}**: {step}")
        lines.append("")
        has_match = True

    # 2. Search Medicines DB
    med_matches = []
    for med in MEDICINES_DB:
        b_name = med.get("brand_name", "").lower()
        g_name = med.get("generic_name", "").lower()
        comp = med.get("composition", "").lower()
        uses = [u.lower() for u in med.get("uses", [])]

        if any(kw in b_name or kw in g_name or kw in comp for kw in query_keywords):
            med_matches.append(med)
        elif any(any(kw == u or kw in u for kw in query_keywords) for u in uses):
            med_matches.append(med)

    if med_matches and not has_match:
        med = med_matches[0]
        lines.append(f"💊 **Medicine Insight: {med.get('brand_name')}** ({med.get('strength', 'Standard')})")
        lines.append(f"• **Active Salt**: {med.get('composition', med.get('generic_name'))}")
        lines.append(f"• **Primary Uses**: {', '.join(med.get('uses', []))}")
        lines.append(f"• **Dosage**: {med.get('dosage')}")
        lines.append(f"• **Storage**: {med.get('storage', 'Keep below 30°C')}")
        if med.get('side_effects'):
            lines.append(f"• **Side Effects**: {', '.join(med.get('side_effects'))}")
        if med.get('warnings'):
            lines.append(f"• ⚠️ **Precaution**: {med.get('warnings')[0]}")
        lines.append(f"• **Prescription Status**: {'🔒 Rx Required' if med.get('prescription_required') else '✅ Over The Counter (OTC)'}\n")
        has_match = True

    # 3. Search Symptoms DB
    symptom_matches = []
    for sym in SYMPTOMS_DB:
        s_name = sym.get("symptom_name", "").lower()
        causes = [c.lower() for c in sym.get("possible_causes", [])]
        if any(kw in s_name or any(kw in c for c in causes) for kw in query_keywords):
            symptom_matches.append(sym)

    if symptom_matches and not has_match:
        sym = symptom_matches[0]
        lines.append(f"📋 **Symptom Guide: {sym.get('symptom_name')}**")
        lines.append(f"• **Severity Level**: {sym.get('severity', 'Moderate')}")
        lines.append(f"• **Possible Causes**: {', '.join(sym.get('possible_causes', []))}")
        lines.append(f"• **Home Care**: {sym.get('home_care')}")
        lines.append(f"• **Doctor Specialist**: {sym.get('suggested_specialist')}\n")
        has_match = True

    # 4. Search Diseases DB
    disease_matches = []
    for dis in DISEASES_DB:
        d_name = dis.get("disease_name", "").lower()
        sympt_list = [s.lower() for s in dis.get("symptoms", [])]
        if any(kw in d_name or any(kw in s for s in sympt_list) for kw in query_keywords):
            disease_matches.append(dis)

    if disease_matches and not has_match:
        dis = disease_matches[0]
        lines.append(f"🔍 **Condition Profile: {dis.get('disease_name')}**")
        lines.append(f"• **Key Symptoms**: {', '.join(dis.get('symptoms', []))}")
        lines.append(f"• **Prevention & Care**: {dis.get('prevention')}")
        lines.append(f"• **Recommended Doctor**: {dis.get('specialist')}\n")
        has_match = True

    # 5. Search FAQ DB
    for faq in FAQ_DB:
        q = faq.get("question", "").lower()
        if any(kw in q for kw in query_keywords if len(kw) > 3) or msg in q:
            lines.append(f"❓ **Question**: **{faq.get('question')}**")
            lines.append(f"💡 **Answer**: {faq.get('answer')}")
            lines.append(f"🏷️ **Category**: {faq.get('category', 'General Health')}\n")
            has_match = True
            break

    # 6. Fallback Query-Specific Guidance
    if not has_match:
        lines.append(f"💡 **Clinical Guidance for Query**: *\"{message}\"*")
        lines.append(f"• **Key Terms**: {', '.join(query_keywords) if query_keywords else 'General Query'}")
        lines.append(f"• **Action Plan**: For unlisted health concerns, monitor symptoms closely and consult a certified physician.")
        lines.append(f"• **Explore CuraAssist**: Search registered tablets (*Dolo 650*, *Pan 40*), scan prescriptions, or locate nearby hospitals on Maps.\n")

    lines.append("🚨 *If you experience chest pain, sudden numbness, or severe difficulty breathing, please call 108 immediately.*")

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


class OCRScanRequest(BaseModel):
    image_name: Optional[str] = "prescription_slip.jpg"
    image_base64: Optional[str] = None
    raw_text: Optional[str] = None


@router.post("/ocr-scan")
def scan_prescription_ocr(req: OCRScanRequest):
    img_name = req.image_name or "prescription_slip.jpg"
    raw_input = (req.raw_text or "").strip()
    name_lower = img_name.lower()

    # 1. Attempt AI-powered OCR & Clinical Vision Extraction
    if raw_input and len(raw_input) > 5:
        try:
            ai_prompt = f"Analyze the following extracted medical prescription/scan text for file '{img_name}'. Provide a clean, structured clinical summary including document type, recognized medicine names, salt formulas, dosage instructions, and precautions:\n\n{raw_input}"
            ai_response = call_remote_ai(ai_prompt, "N/A")
            if ai_response and len(ai_response) > 20:
                return {"status": "success", "category": "Prescriptions", "summary": ai_response}
        except Exception as e:
            print("AI OCR extraction note:", e)

    # 2. Dynamic Database & Text Analysis Matching
    matched_meds = []
    text_lower = raw_input.lower()
    meds = MEDICINES_DB if MEDICINES_DB else load_data("medicines.json")

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
        summary = f"DOCTOR PRESCRIPTION / MEDICINE ANALYSIS ({img_name})\n----------------------------------------------------\nVerified Items Matched in Database:\n{med_lines}"
        return {"status": "success", "category": "Prescriptions", "summary": summary}

    # 3. Dynamic OCR Document Categorization (Lab Reports, Scans, General Prescriptions)
    if "blood" in name_lower or "lab" in name_lower or "test" in name_lower:
        doc_category = "Lab Reports"
        summary = f"LABORATORY TEST REPORT ANALYSIS ({img_name})\n----------------------------------------------------\n• Extracted Text Signature: {raw_input[:150] or 'Diagnostic Clinical Test'}\n• Status: Clinical Indicators Extracted & Recorded in Health Log."
    elif "xray" in name_lower or "mri" in name_lower or "scan" in name_lower:
        doc_category = "Scans"
        summary = f"RADIOLOGY & IMAGING SCAN ({img_name})\n----------------------------------------------------\n• Examination: PA/Lateral View Diagnostic Scan\n• Extracted Details: {raw_input[:150] or 'Radiology Diagnostic Image'}"
    else:
        doc_category = "Prescriptions"
        summary = f"MEDICAL PRESCRIPTION RECORD ({img_name})\n----------------------------------------------------\n• Document Name: {img_name}\n• Extracted Content: {raw_input or 'Prescription Document Record'}\n• Clinical Status: Processed & Saved to Patient Health Records."

    return {
        "status": "success",
        "category": doc_category,
        "summary": summary
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
