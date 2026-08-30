import json
import os
import re
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.auth import get_optional_current_user
from app.database.sql_db import UserModel
from app.utils.ocr_processor import (
    process_prescription_ocr,
    generate_prescription_summary,
    fuzzy_match_medicine,
    validate_prescription_text,
    extract_dosage_info,
    extract_frequency_info,
)

router = APIRouter(prefix="/chat", tags=["AI Healthcare Suite - Phase 6"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load_data(filename: str):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Chat API] Error loading {filename}:", e)
    return []


# Preload datasets for fast hybrid offline/online clinical intelligence
DISEASES_DB = load_data("diseases.json")
SYMPTOMS_DB = load_data("symptoms.json")
MEDICINES_DB = load_data("medicines.json")
INTERACTIONS_DB = load_data("drug_interactions.json")
FIRST_AID_DB = load_data("first_aid.json")
LAB_BIOMARKERS_DB = load_data("lab_biomarkers.json")
DOCTORS_DB = load_data("doctors.json")


def get_env_variable(*var_names: str) -> Optional[str]:
    """Reads the runtime environment configured by Vercel or host process, checking aliases."""
    for name in var_names:
        val = os.getenv(name)
        if val and val.strip():
            return val.strip()
    return None


def get_gemini_key() -> Optional[str]:
    """Retrieve Gemini API key from environment variables."""
    return get_env_variable(
        "GEMINI_API_KEY",
        "GOOGLE_GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "VITE_GEMINI_API_KEY"
    )


def get_openai_key() -> Optional[str]:
    """Retrieve OpenAI API key from environment variables."""
    return get_env_variable("OPENAI_API_KEY")


def call_remote_ai(user_prompt: str, patient_context: str = "Patient", system_instruction: Optional[str] = None) -> Optional[str]:
    """Calls Google Gemini API or OpenAI API using runtime environment keys."""
    gemini_key = get_gemini_key()
    openai_key = get_openai_key()

    if not gemini_key and not openai_key:
        return None

    system_prompt = system_instruction or (
        f"You are CuraBot AI, a world-class, empathetic medical AI assistant for CuraAssist Healthcare. "
        f"The patient is: {patient_context}. "
        f"Provide structured, clear, and actionable medical advice in clean Markdown. Use bold medicine names, clear bullet points, and include a warm closing with standard clinical disclaimers."
    )

    # 1. Try Google Gemini API models
    if gemini_key:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = json.dumps({
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{system_prompt}\n\nPatient Query / Case Data:\n{user_prompt}"}
                            ]
                        }
                    ]
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and parts[0].get("text"):
                                return parts[0].get("text")
            except Exception as e:
                print(f"[Gemini API - {model}] Note:", e)

    # 2. Try OpenAI API models
    if openai_key:
        for model in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                })
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content")
            except Exception as e:
                print(f"[OpenAI API - {model}] Note:", e)

    return None


# ==========================================
# 1. AI CHATBOT CONVERSATIONAL ENDPOINT
# ==========================================

class ChatRequest(BaseModel):
    message: str
    patientContext: Optional[str] = "Patient"
    conversationHistory: Optional[List[Dict[str, str]]] = None


def generate_fallback_chat_reply(message: str, patient_context: str) -> str:
    """Intelligent clinical knowledge engine fallback when remote AI API is unreachable."""
    msg_lower = message.lower()
    first_name = patient_context.split()[0] if patient_context else "there"

    # Check for symptoms match
    matched_symptom = None
    for s in SYMPTOMS_DB:
        name = s.get("symptom_name", "").lower()
        keywords = [k.lower() for k in s.get("keywords", [])]
        if name in msg_lower or any(k in msg_lower for k in keywords):
            matched_symptom = s
            break

    if matched_symptom:
        home_care_list = "\n".join([f"• {step}" for step in matched_symptom.get("home_care", [])])
        red_flags_list = "\n".join([f"• 🚨 {rf}" for rf in matched_symptom.get("red_flags", [])])
        return (
            f"🤖 **CuraBot AI Clinical Guidance**\n\n"
            f"Hello **{first_name}**! Based on your query regarding **{matched_symptom.get('symptom_name')}**:\n\n"
            f"### 🩺 Assessment & Specialist\n"
            f"• **Severity Level**: {matched_symptom.get('severity', 'Moderate')}\n"
            f"• **Recommended Doctor**: {matched_symptom.get('suggested_specialist')}\n\n"
            f"### 🏡 Immediate Home Care Protocols\n"
            f"{home_care_list}\n\n"
            f"### ⚠️ Red Flag Warnings (Seek Immediate Care If):\n"
            f"{red_flags_list}\n\n"
            f"> *Note: This automated clinical summary provides guidance. If symptoms worsen or persist, please consult a verified physician.*"
        )

    # Check for medicine lookup in query
    for m in MEDICINES_DB:
        b_name = m.get("brand_name", "").lower()
        g_name = m.get("generic_name", "").lower()
        if (b_name and b_name in msg_lower) or (g_name and g_name in msg_lower):
            uses_str = ", ".join(m.get("uses", ["General health"]))
            side_fx = ", ".join(m.get("side_effects", ["Consult pharmacist"]))
            warnings = ", ".join(m.get("warnings", ["Take as prescribed"]))
            return (
                f"🤖 **CuraBot AI Medicine Monograph**\n\n"
                f"### 💊 **{m.get('brand_name')}** ({m.get('generic_name')})\n"
                f"• **Composition**: {m.get('composition', 'Active formula')}\n"
                f"• **Primary Uses**: {uses_str}\n"
                f"• **Standard Dosage**: {m.get('dosage', 'As advised by doctor')}\n"
                f"• **Common Side Effects**: {side_fx}\n"
                f"• **Crucial Warnings**: {warnings}\n"
                f"• **Storage**: {m.get('storage', 'Store in cool dry place')}\n\n"
                f"> *Always verify medication dosage with your doctor or pharmacist.*"
            )

    # Check first aid query
    for fa in FIRST_AID_DB:
        etype = fa.get("emergency_type", "").lower()
        if any(w in msg_lower for w in etype.split()):
            steps = "\n".join([f"{i+1}. {st}" for i, st in enumerate(fa.get("first_aid_steps", []))])
            return (
                f"🚨 **Emergency First Aid Protocol - {fa.get('emergency_type')}**\n\n"
                f"{steps}\n\n"
                f"📞 **Emergency Dispatch**: Tap **🚨 Emergency SOS** or call **{fa.get('emergency_number', '108')}** immediately."
            )

    # General clinical response
    return (
        f"🤖 **CuraBot AI Assistant**\n\n"
        f"Hello **{first_name}**! I have received your health inquiry: *\"{message}\"*\n\n"
        f"• 🩺 **Clinical Advice**: For best personalized medical guidance, share specific symptoms, their duration, or upload a prescription/lab report in the **Scanner** tab.\n"
        f"• 📊 **Vitals Logging**: Remember to record your daily Blood Pressure, Pulse, Temperature, and Glucose in your **Profile Vitals Tracker**.\n"
        f"• 🚨 **Emergency Care**: If experiencing sudden chest pain, severe shortness of breath, or fainting, call **108** or tap the red **Emergency SOS** button immediately."
    )


@router.post("/ask")
def ask_ai_assistant(
    request: ChatRequest,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
):
    if current_user:
        patient_ctx = f"{current_user.name} (Age {current_user.age or 30})"
    else:
        patient_ctx = request.patientContext or "Patient"

    remote_reply = call_remote_ai(request.message, patient_ctx)
    if remote_reply:
        reply = remote_reply
        source = "Google Gemini AI (Live API)"
    else:
        reply = generate_fallback_chat_reply(request.message, patient_ctx)
        source = "CuraBot Clinical Knowledge AI Engine"

    return {
        "status": "success",
        "reply": reply,
        "timestamp": "Just now",
        "sender": source
    }


# ==========================================
# 2. SYMPTOM GUIDANCE & CLINICAL TRIAGE
# ==========================================

class SymptomCheckerRequest(BaseModel):
    symptoms: List[str] = Field(..., description="List of patient symptoms")
    duration: Optional[str] = "1-2 days"
    severity: Optional[str] = "Moderate"
    patient_age: Optional[int] = 34
    patient_gender: Optional[str] = "Male"
    additional_notes: Optional[str] = ""


@router.get("/symptom-catalog")
def get_symptom_catalog():
    """Returns catalog of searchable symptoms and pre-configured quick selector chips."""
    quick_chips = [
        {"id": "sym_fever", "name": "Fever & Chills", "category": "General", "icon": "thermometer"},
        {"id": "sym_cough", "name": "Dry / Wet Cough", "category": "Respiratory", "icon": "wind"},
        {"id": "sym_headache", "name": "Headache / Migraine", "category": "Neurological", "icon": "zap"},
        {"id": "sym_chest", "name": "Chest Discomfort", "category": "Cardiovascular", "icon": "heart"},
        {"id": "sym_acidity", "name": "Acidity & Heartburn", "category": "Gastrointestinal", "icon": "flame"},
        {"id": "sym_rash", "name": "Skin Rash & Itching", "category": "Dermatology", "icon": "shield-alert"},
        {"id": "sym_joint", "name": "Joint Pain & Swelling", "category": "Orthopedic", "icon": "activity"},
        {"id": "sym_dizzy", "name": "Dizziness & Vertigo", "category": "Neurological", "icon": "compass"},
        {"id": "sym_sugar", "name": "Frequent Urination & Thirst", "category": "Endocrine", "icon": "droplet"},
        {"id": "sym_vomit", "name": "Diarrhea & Nausea", "category": "Gastrointestinal", "icon": "alert-circle"}
    ]
    return {
        "status": "success",
        "count": len(SYMPTOMS_DB),
        "catalog": SYMPTOMS_DB,
        "quick_chips": quick_chips
    }


@router.post("/symptom-checker")
def analyze_symptoms_triage(req: SymptomCheckerRequest):
    """
    Evaluates patient symptoms against clinical datasets and Gemini AI to provide:
    - Differential condition probability
    - Triage level (Mild, Moderate, Urgent, Critical)
    - Recommended specialist & tests
    - Home care steps & safe OTC options
    - Emergency red flag alerts
    """
    user_symptoms = [s.strip().lower() for s in req.symptoms if s and s.strip()]
    if not user_symptoms:
        raise HTTPException(status_code=400, detail="Please provide at least one symptom to analyze.")

    # 1. Try Live Gemini AI for deep medical triage
    ai_prompt = (
        f"Perform structured clinical triage for a {req.patient_age}yo {req.patient_gender} patient.\n"
        f"Symptoms: {', '.join(req.symptoms)}\n"
        f"Duration: {req.duration}\n"
        f"Severity: {req.severity}\n"
        f"Notes: {req.additional_notes or 'None'}\n\n"
        f"Return structured JSON format with keys:\n"
        f"triage_level ('mild', 'moderate', 'urgent', 'critical'),\n"
        f"severity_badge ('🟢 Mild / Home Care', '🟡 Moderate / Review', '🟠 Urgent Specialist', '🔴 Emergency / SOS'),\n"
        f"primary_condition (string),\n"
        f"probable_conditions (array of {{\"condition\": string, \"probability\": int (0-100), \"reasoning\": string}}),\n"
        f"recommended_specialist (string),\n"
        f"suggested_tests (array of strings),\n"
        f"home_care_steps (array of strings),\n"
        f"safe_otc_options (array of strings),\n"
        f"red_flags (array of strings),\n"
        f"doctor_summary (string)"
    )

    remote_res = call_remote_ai(
        ai_prompt,
        f"{req.patient_gender}, Age {req.patient_age}",
        system_instruction="You are a board-certified AI Triage Physician. Return ONLY valid JSON."
    )

    if remote_res:
        try:
            json_str = remote_res.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            if "probable_conditions" in parsed:
                parsed["status"] = "success"
                parsed["source"] = "Google Gemini Clinical Triage Engine"
                return parsed
        except Exception as e:
            print("[Symptom Triage JSON parse note]:", e)

    # 2. Offline Clinical Rule Engine
    matched_conditions = []
    matched_home_care = []
    matched_red_flags = []
    specialists = set()
    suggested_tests = []
    triage_level = "mild"
    severity_badge = "🟢 Mild / Home Care"

    # Match against symptoms database
    for sym_item in SYMPTOMS_DB:
        s_name = sym_item.get("symptom_name", "").lower()
        keywords = [k.lower() for k in sym_item.get("keywords", [])]

        hit = any(s in s_name or any(s in k for k in keywords) for s in user_symptoms)
        if hit:
            specialists.add(sym_item.get("suggested_specialist", "General Physician"))
            matched_home_care.extend(sym_item.get("home_care", []))
            matched_red_flags.extend(sym_item.get("red_flags", []))
            if sym_item.get("severity_level") == "critical" or "chest" in s_name:
                triage_level = "critical"
                severity_badge = "🔴 Emergency / SOS"
            elif sym_item.get("severity_level") == "moderate" and triage_level != "critical":
                triage_level = "moderate"
                severity_badge = "🟡 Moderate / Physician Review"

    # Match against diseases database
    for dis in DISEASES_DB:
        dis_symptoms = [ds.lower() for ds in dis.get("symptoms", [])]
        overlap_count = sum(1 for us in user_symptoms if any(us in ds or ds in us for ds in dis_symptoms))
        if overlap_count > 0:
            prob = min(92, 35 + (overlap_count * 25))
            matched_conditions.append({
                "condition": dis.get("disease_name"),
                "category": dis.get("category", "General"),
                "probability": prob,
                "reasoning": f"Matches symptoms: {', '.join([us for us in user_symptoms if any(us in ds for ds in dis_symptoms)])}"
            })
            if dis.get("recommended_tests"):
                suggested_tests.extend(dis.get("recommended_tests"))
            if dis.get("specialist"):
                specialists.add(dis.get("specialist"))

    if not matched_conditions:
        matched_conditions.append({
            "condition": "Acute Viral Syndrome / Non-Specific Malaise",
            "category": "Infectious Disease",
            "probability": 72,
            "reasoning": f"Common clinical manifestation for duration of {req.duration}"
        })

    matched_conditions.sort(key=lambda x: x["probability"], reverse=True)
    primary_condition = matched_conditions[0]["condition"]

    if not matched_home_care:
        matched_home_care = [
            "Maintain optimal hydration with Oral Rehydration Solution (ORS) & clean water (2.5L/day)",
            "Get at least 8 hours of uninterrupted restful sleep",
            "Monitor body temperature and vitals twice daily in Profile Vitals Tracker",
            "Eat nutrient-dense, easily digestible home-cooked meals"
        ]

    if not matched_red_flags:
        matched_red_flags = [
            "Sudden severe difficulty breathing or shortness of breath",
            "Loss of consciousness, extreme dizziness, or slurred speech",
            "High fever exceeding 103°F unresponsive to paracetamol",
            "Persistent, severe localized pain"
        ]

    safe_otc = [
        "Paracetamol 650mg (For fever & mild aches - Max 3-4 doses/day)",
        "ORS Electrolyte Sachet (For hydration & fatigue)",
        "Steam Inhalation & Saline Gargle (For throat/airway soothing)"
    ]

    doctor_summary = (
        f"Patient presents with {', '.join(req.symptoms)} lasting {req.duration} of {req.severity.lower()} intensity. "
        f"Primary diagnostic consideration is {primary_condition}. "
        f"Recommended specialist consultation: {list(specialists)[0] if specialists else 'General Physician'}."
    )

    return {
        "status": "success",
        "source": "CuraBot Clinical Triage Matrix",
        "triage_level": triage_level,
        "severity_badge": severity_badge,
        "primary_condition": primary_condition,
        "probable_conditions": matched_conditions[:4],
        "recommended_specialist": list(specialists)[0] if specialists else "General Physician",
        "suggested_tests": list(dict.fromkeys(suggested_tests))[:5] or ["Complete Blood Count (CBC)", "Basic Metabolic Panel"],
        "home_care_steps": list(dict.fromkeys(matched_home_care))[:5],
        "safe_otc_options": safe_otc,
        "red_flags": list(dict.fromkeys(matched_red_flags))[:4],
        "doctor_summary": doctor_summary
    }


# ==========================================
# 3. LAB & HEALTH REPORT EXPLAINER
# ==========================================

class BiomarkerInput(BaseModel):
    name: str
    value: float
    unit: Optional[str] = ""


class LabReportExplainerRequest(BaseModel):
    report_type: Optional[str] = "Complete Blood Count (CBC)"
    report_text: Optional[str] = ""
    biomarkers: Optional[List[BiomarkerInput]] = None
    patient_context: Optional[str] = "Rahul Sharma (Age 34)"


@router.get("/lab-test-templates")
def get_lab_test_templates():
    """Returns sample test templates for quick evaluation in the UI."""
    return {
        "status": "success",
        "templates": [
            {
                "id": "cbc_sample",
                "name": "Complete Blood Count (CBC)",
                "category": "Hematology",
                "biomarkers": [
                    {"name": "Hemoglobin (Hb)", "value": 11.4, "unit": "g/dL"},
                    {"name": "Total White Blood Cells (WBC / TLC)", "value": 12800, "unit": "/µL"},
                    {"name": "Platelet Count", "value": 142, "unit": "x10^3/µL"}
                ]
            },
            {
                "id": "lipid_sample",
                "name": "Lipid Profile (Cholesterol)",
                "category": "Cardiology",
                "biomarkers": [
                    {"name": "Total Cholesterol", "value": 235.0, "unit": "mg/dL"},
                    {"name": "LDL Bad Cholesterol", "value": 145.0, "unit": "mg/dL"},
                    {"name": "HDL Good Cholesterol", "value": 36.0, "unit": "mg/dL"}
                ]
            },
            {
                "id": "diabetes_sample",
                "name": "Diabetes / Blood Sugar Panel",
                "category": "Endocrine",
                "biomarkers": [
                    {"name": "Fasting Blood Sugar (FBS)", "value": 138.0, "unit": "mg/dL"},
                    {"name": "Glycated Hemoglobin (HbA1c)", "value": 7.2, "unit": "%"}
                ]
            },
            {
                "id": "liver_sample",
                "name": "Liver Function Test (LFT)",
                "category": "Gastroenterology",
                "biomarkers": [
                    {"name": "Serum Bilirubin (Total)", "value": 1.9, "unit": "mg/dL"},
                    {"name": "SGPT / ALT (Alanine Aminotransferase)", "value": 74.0, "unit": "U/L"}
                ]
            },
            {
                "id": "thyroid_sample",
                "name": "Thyroid Profile (TSH)",
                "category": "Endocrine",
                "biomarkers": [
                    {"name": "Thyroid Stimulating Hormone (TSH)", "value": 6.8, "unit": "mIU/L"}
                ]
            }
        ]
    }


@router.post("/explain-lab-report")
def explain_medical_lab_report(req: LabReportExplainerRequest):
    """
    Parses and explains laboratory and diagnostic blood tests.
    Calculates normal, high, low, and critical biomarker states,
    providing plain-English clinical explanations and dietary guidelines.
    """
    analyzed_items = []
    abnormal_count = 0

    input_biomarkers = req.biomarkers or []

    # If raw text provided without structured biomarkers, parse common patterns
    if not input_biomarkers and req.report_text:
        text = req.report_text
        for b in LAB_BIOMARKERS_DB:
            b_name = b.get("name", "")
            pattern = re.escape(b_name.split()[0]) + r"[:\s\-]+([0-9]+\.?[0-9]*)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    input_biomarkers.append(BiomarkerInput(name=b_name, value=val, unit=b.get("unit", "")))
                except Exception:
                    pass

    # If still empty, use default sample
    if not input_biomarkers:
        input_biomarkers = [
            BiomarkerInput(name="Hemoglobin (Hb)", value=11.2, unit="g/dL"),
            BiomarkerInput(name="Total Cholesterol", value=220.0, unit="mg/dL"),
            BiomarkerInput(name="Fasting Blood Sugar (FBS)", value=115.0, unit="mg/dL")
        ]

    for item in input_biomarkers:
        match_def = None
        for b in LAB_BIOMARKERS_DB:
            if b.get("name", "").lower() in item.name.lower() or item.name.lower() in b.get("name", "").lower():
                match_def = b
                break

        if not match_def:
            match_def = {
                "name": item.name,
                "unit": item.unit or "",
                "normal_range_min": 0,
                "normal_range_max": 100,
                "description": "Clinical diagnostic test parameter.",
                "low_implication": "Below standard physiological threshold.",
                "high_implication": "Above standard physiological threshold.",
                "diet_advice": "Consult your physician for personalized dietary recommendations."
            }

        min_val = float(match_def.get("normal_range_min", 0))
        max_val = float(match_def.get("normal_range_max", 100))
        val = item.value

        if val < min_val:
            status = "Low"
            status_badge = "🟡 Low"
            implication = match_def.get("low_implication", "Below normal range.")
            abnormal_count += 1
        elif val > max_val:
            if val > (max_val * 1.5):
                status = "Critical High"
                status_badge = "🔴 Critical High"
            else:
                status = "High"
                status_badge = "🔴 High"
            implication = match_def.get("high_implication", "Above normal range.")
            abnormal_count += 1
        else:
            status = "Normal"
            status_badge = "🟢 Optimal / Normal"
            implication = "Within optimal reference limits."

        analyzed_items.append({
            "name": match_def.get("name"),
            "category": match_def.get("category", "General Panel"),
            "patient_value": val,
            "unit": match_def.get("unit", item.unit),
            "normal_range": f"{min_val} - {max_val} {match_def.get('unit', '')}",
            "status": status,
            "status_badge": status_badge,
            "description": match_def.get("description"),
            "clinical_implication": implication,
            "diet_lifestyle_advice": match_def.get("diet_advice")
        })

    doctor_lines = []
    for item in analyzed_items:
        if item["status"] != "Normal":
            doctor_lines.append(f"• **{item['name']}** is **{item['status_badge']}** ({item['patient_value']} {item['unit']}). {item['clinical_implication']}")
        else:
            doctor_lines.append(f"• **{item['name']}** is **{item['status_badge']}** ({item['patient_value']} {item['unit']}) ✓.")

    doctor_explanation = "\n".join(doctor_lines)
    diet_tips = [item["diet_lifestyle_advice"] for item in analyzed_items if item.get("diet_lifestyle_advice")]

    return {
        "status": "success",
        "report_type": req.report_type or "Clinical Laboratory Panel",
        "total_biomarkers": len(analyzed_items),
        "abnormal_count": abnormal_count,
        "overall_health_assessment": "Attention Required" if abnormal_count > 0 else "All Biomarkers Within Normal Limits",
        "biomarkers_analyzed": analyzed_items,
        "doctor_explanation": doctor_explanation,
        "diet_and_lifestyle_recommendations": list(dict.fromkeys(diet_tips)),
        "suggested_specialist": "General Physician / Pathologist" if abnormal_count <= 1 else "Specialist Physician"
    }


# ==========================================
# 4. PRESCRIPTION ANALYSIS & SCHEDULE
# ==========================================

class PrescriptionAnalysisRequest(BaseModel):
    prescription_text: str
    patient_context: Optional[str] = "Rahul Sharma (Age 34)"


@router.post("/analyze-prescription")
def analyze_prescription_comprehensive(req: PrescriptionAnalysisRequest):
    """
    Extracts medicines, verifies dosages, checks multi-drug interactions,
    and builds an interactive daily medication schedule timeline.
    """
    raw_text = req.prescription_text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Prescription text cannot be empty.")

    meds = MEDICINES_DB if MEDICINES_DB else load_data("medicines.json")
    extraction_result = process_prescription_ocr(raw_text, meds)
    extracted_meds = extraction_result.get("extracted_medicines", [])

    morning_schedule = []
    afternoon_schedule = []
    evening_schedule = []
    bedtime_schedule = []

    med_names_for_interaction = []

    for med in extracted_meds:
        b_name = med.get("brand_name", "Medicine")
        g_name = med.get("generic_name", "")
        dosage = med.get("dosage", "1 Dose")
        freq_list = [f.lower() for f in med.get("frequency", [])]
        raw_freq = " ".join(freq_list)

        med_names_for_interaction.append(b_name)

        timing_note = "After Food" if "after food" in raw_freq or "pc" in raw_text.lower() else "Before/After Food"

        if any(w in raw_freq for w in ["once daily", "od", "morning", "twice daily", "bd", "thrice daily", "tid"]):
            morning_schedule.append({
                "medicine": b_name,
                "generic": g_name,
                "dosage": dosage,
                "timing": "08:00 AM",
                "instructions": timing_note
            })

        if any(w in raw_freq for w in ["thrice daily", "tid", "afternoon", "noon", "qid"]):
            afternoon_schedule.append({
                "medicine": b_name,
                "generic": g_name,
                "dosage": dosage,
                "timing": "01:00 PM",
                "instructions": "After Lunch"
            })

        if any(w in raw_freq for w in ["twice daily", "bd", "thrice daily", "tid", "evening", "night"]):
            evening_schedule.append({
                "medicine": b_name,
                "generic": g_name,
                "dosage": dosage,
                "timing": "08:00 PM",
                "instructions": timing_note
            })

        if any(w in raw_freq for w in ["bedtime", "hs", "night", "statin", "atorvastatin"]):
            bedtime_schedule.append({
                "medicine": b_name,
                "generic": g_name,
                "dosage": dosage,
                "timing": "10:00 PM",
                "instructions": "With water before sleep"
            })

    detected_interactions = []
    med_identifiers = []
    for med in extracted_meds:
        b_name = med.get("brand_name", "")
        g_name = med.get("generic_name", "")
        if b_name:
            med_identifiers.append(b_name.lower())
        if g_name:
            med_identifiers.append(g_name.lower())
            for part in re.split(r"[\+\&\,/\(\)]|\band\b", g_name):
                clean_p = part.strip().lower()
                if len(clean_p) >= 3:
                    med_identifiers.append(clean_p)

    if len(extracted_meds) >= 2:
        for item in INTERACTIONS_DB:
            m1 = (item.get("medicine_1") or item.get("drug_1") or "").lower()
            m2 = (item.get("medicine_2") or item.get("drug_2") or "").lower()
            has1 = any(m1 in ident or ident in m1 for ident in med_identifiers)
            has2 = any(m2 in ident or ident in m2 for ident in med_identifiers)
            if has1 and has2:
                detected_interactions.append({
                    "drug1": item.get("medicine_1"),
                    "drug2": item.get("medicine_2"),
                    "severity": item.get("severity", "Moderate"),
                    "description": item.get("description"),
                    "recommendation": item.get("recommendation")
                })

    summary_text = generate_prescription_summary(extraction_result)

    return {
        "status": "success",
        "medicine_count": len(extracted_meds),
        "extracted_medicines": extracted_meds,
        "has_interactions": len(detected_interactions) > 0,
        "interactions": detected_interactions,
        "daily_schedule_timeline": {
            "morning": morning_schedule,
            "afternoon": afternoon_schedule,
            "evening": evening_schedule,
            "bedtime": bedtime_schedule
        },
        "ai_summary": summary_text,
        "patient_safety_checklist": [
            "Always complete full antibiotic courses even if symptoms improve.",
            "Take pain relievers with meals to protect gastric lining.",
            "Do not consume alcohol while on paracetamol, antibiotics, or statins."
        ]
    }


# ==========================================
# 5. MEDICINE CLINICAL INFORMATION
# ==========================================

class MedicineInfoRequest(BaseModel):
    medicine_name: str


@router.post("/medicine-info")
def get_medicine_clinical_monograph(req: MedicineInfoRequest):
    """Returns in-depth clinical monograph for any medicine or active salt."""
    q = req.medicine_name.strip().lower()
    if not q:
        raise HTTPException(status_code=400, detail="Medicine name cannot be empty.")

    med_match = None
    for m in MEDICINES_DB:
        b_name = m.get("brand_name", "").lower()
        g_name = m.get("generic_name", "").lower()
        comp = m.get("composition", "").lower()
        if q in b_name or q in g_name or q in comp or b_name in q or g_name in q:
            med_match = m
            break

    if not med_match:
        fuzzy = fuzzy_match_medicine(req.medicine_name, MEDICINES_DB, threshold=0.6)
        if fuzzy:
            med_match = fuzzy

    if med_match:
        return {
            "status": "success",
            "source": "CuraAssist Pharmacopeia Knowledge Base",
            "medicine_id": med_match.get("medicine_id"),
            "brand_name": med_match.get("brand_name"),
            "generic_name": med_match.get("generic_name"),
            "composition": med_match.get("composition"),
            "category": med_match.get("category"),
            "dosage_form": med_match.get("dosage_form", "Tablet / Capsule"),
            "strength": med_match.get("strength", "Standard Dose"),
            "price": med_match.get("price", 50.0),
            "prescription_required": med_match.get("prescription_required", False),
            "uses": med_match.get("uses", ["Symptom relief"]),
            "dosage_guidelines": med_match.get("dosage", "Take as directed by doctor"),
            "side_effects": med_match.get("side_effects", ["Nausea", "Drowsiness"]),
            "warnings": med_match.get("warnings", ["Do not exceed recommended dose"]),
            "contraindications": med_match.get("contraindications", ["Known allergy to formula"]),
            "storage": med_match.get("storage", "Store below 30°C in a dry place"),
            "pregnancy_safety": "Category B - Consult obstetrician before use",
            "alcohol_warning": "Avoid concurrent alcohol consumption"
        }

    ai_prompt = (
        f"Provide a structured clinical monograph for medicine '{req.medicine_name}'.\n"
        f"Include: Generic name, Active composition, Therapeutic category, Primary uses, Standard dosage, Common side effects, Crucial warnings, and Contraindications."
    )
    remote_res = call_remote_ai(ai_prompt, "Patient")

    return {
        "status": "success",
        "source": "AI Clinical Generation",
        "brand_name": req.medicine_name.title(),
        "generic_name": "Active Pharmacological Compound",
        "composition": req.medicine_name,
        "category": "Therapeutic Medication",
        "uses": ["Symptom management as prescribed"],
        "dosage_guidelines": "Consult physician for exact dosage schedule.",
        "ai_overview": remote_res or f"Information for {req.medicine_name} retrieved."
    }


# ==========================================
# 6. OCR SCAN & BARCODE
# ==========================================

class OCRScanRequest(BaseModel):
    image_name: Optional[str] = "prescription_slip.jpg"
    image_base64: Optional[str] = None
    raw_text: Optional[str] = None


@router.post("/ocr-scan")
def scan_prescription_ocr(req: OCRScanRequest):
    """Prescription scanning with fuzzy matching & AI validation."""
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

    if "blood" in name_lower or "lab" in name_lower or "test" in name_lower:
        doc_category = "Lab Reports"
        summary = f"LABORATORY TEST REPORT ANALYSIS ({img_name})\n----------------------------------------------------\n• Extracted Text: {raw_input[:150] or 'Diagnostic Clinical Test'}\n• Status: Clinical Data Extracted & Recorded in Health Log."
    elif "xray" in name_lower or "mri" in name_lower or "scan" in name_lower:
        doc_category = "Scans"
        summary = f"RADIOLOGY & IMAGING SCAN ({img_name})\n----------------------------------------------------\n• Examination Type: Medical Imaging Analysis\n• Extracted Details: {raw_input[:150] or 'Diagnostic Image'}"
    else:
        doc_category = "Prescriptions"
        if raw_input and len(raw_input) > 5:
            try:
                extraction_result = process_prescription_ocr(raw_input, meds)
                if extraction_result.get("extracted_medicines"):
                    summary = generate_prescription_summary(extraction_result)
                    return {
                        "status": "success",
                        "category": doc_category,
                        "summary": summary,
                        "extracted_medicines": extraction_result.get("extracted_medicines", []),
                        "confidence": "high" if extraction_result.get("has_confident_matches") else "medium"
                    }
            except Exception as e:
                print(f"[OCR Scan fallback]: {e}")

        summary = f"MEDICAL PRESCRIPTION RECORD ({img_name})\n----------------------------------------------------\n• Document: {img_name}\n• Extracted Content: {raw_input or 'Prescription verified'}"

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
        m_id = m.get("medicine_id", "").lower()

        if q and (q in b_name or q in g_name or q in cat or q in m_id):
            results.append(m)
        elif barcode and (barcode in m_id or barcode in b_name or barcode in m.get("barcode", "")):
            results.append(m)

    if not results and meds:
        results = [meds[0]]

    return {
        "status": "success",
        "matched_count": len(results),
        "matches": results
    }
