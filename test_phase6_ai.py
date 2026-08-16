#!/usr/bin/env python3
"""
Test Suite for Phase 6: AI Healthcare Module (CuraBot AI, Symptom Triage, Lab Report Explainer, Prescription Analyzer, Drug Safety Matrix)
"""

import sys
sys.path.insert(0, '/workspaces/ai_healthcare_system/application/backend')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ai_chatbot():
    print("\n" + "="*60)
    print("TEST 1: AI Chatbot Conversational Response")
    print("="*60)
    r = client.post("/chat/ask", json={
        "message": "What is Dolo 650 used for and what are its side effects?",
        "patientContext": "Rahul Sharma (Age 34)"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("status") == "success"
    assert len(data.get("reply", "")) > 20
    print(f"✓ Chatbot response received from: {data.get('sender')}")
    print(f"  Snippet: {data.get('reply')[:120]}...\n")


def test_symptom_triage():
    print("="*60)
    print("TEST 2: AI Clinical Symptom Guidance & Triage")
    print("="*60)
    # Test high-fever & chills triage
    r = client.post("/chat/symptom-checker", json={
        "symptoms": ["High Fever & Chills", "Throbbing Headache & Migraine"],
        "duration": "2 days",
        "severity": "Moderate",
        "patient_age": 34,
        "patient_gender": "Male"
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "success"
    assert "primary_condition" in data
    assert len(data.get("probable_conditions", [])) > 0
    assert "recommended_specialist" in data
    assert len(data.get("home_care_steps", [])) > 0
    print(f"✓ Triage Level: {data.get('triage_level')} ({data.get('severity_badge')})")
    print(f"✓ Primary Diagnosis: {data.get('primary_condition')}")
    print(f"✓ Recommended Specialist: {data.get('recommended_specialist')}")
    print(f"✓ Probable Conditions: {[c['condition'] for c in data.get('probable_conditions', [])]}")
    print(f"✓ Home Care Steps: {len(data.get('home_care_steps', []))} steps provided\n")


def test_lab_report_explainer():
    print("="*60)
    print("TEST 3: Medical Diagnostic Lab Report Explainer")
    print("="*60)
    # Test CBC report with low hemoglobin and high WBC
    r = client.post("/chat/explain-lab-report", json={
        "report_type": "Complete Blood Count (CBC)",
        "biomarkers": [
            {"name": "Hemoglobin (Hb)", "value": 10.8, "unit": "g/dL"},
            {"name": "Total White Blood Cells (WBC / TLC)", "value": 13500.0, "unit": "/µL"},
            {"name": "Platelet Count", "value": 240.0, "unit": "x10^3/µL"}
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "success"
    assert data.get("abnormal_count") == 2
    assert len(data.get("biomarkers_analyzed", [])) == 3

    statuses = {b["name"]: b["status"] for b in data.get("biomarkers_analyzed", [])}
    assert statuses.get("Hemoglobin (Hb)") == "Low"
    assert statuses.get("Total White Blood Cells (WBC / TLC)") == "High"
    assert statuses.get("Platelet Count") == "Normal"

    print(f"✓ Total Biomarkers Analyzed: {data.get('total_biomarkers')}")
    print(f"✓ Abnormal Findings: {data.get('abnormal_count')} flagged")
    for b in data.get("biomarkers_analyzed", []):
        print(f"  • {b['name']}: {b['patient_value']} {b['unit']} -> {b['status_badge']} (Ref: {b['normal_range']})")
    print(f"✓ Diet & Lifestyle Tips: {len(data.get('diet_and_lifestyle_recommendations', []))} items\n")


def test_prescription_analysis():
    print("="*60)
    print("TEST 4: AI Prescription Analyzer & Daily Medication Timeline")
    print("="*60)
    # Multi-drug prescription with potential interaction
    rx_text = """
    DR. R. VARMA CLINIC
    Rx:
    1. Ecosprin 75 75mg tablet OD PC x30 days
    2. Warf 5 5mg tablet OD x30 days
    3. Pan 40 40mg tablet OD AC x30 days
    """
    r = client.post("/chat/analyze-prescription", json={"prescription_text": rx_text})
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "success"
    assert data.get("medicine_count") >= 2
    assert data.get("has_interactions") is True
    assert len(data.get("interactions", [])) >= 1

    tl = data.get("daily_schedule_timeline", {})
    assert "morning" in tl
    assert "evening" in tl

    print(f"✓ Medicines Extracted: {[m['brand_name'] for m in data.get('extracted_medicines', [])]}")
    print(f"✓ Interactions Shield Active: {data.get('has_interactions')}")
    for inter in data.get("interactions", []):
        print(f"  ⚠️ Hazard: {inter['drug1']} + {inter['drug2']} -> Severity: {inter['severity']}")
    print(f"✓ Morning Schedule Clock: {len(tl.get('morning', []))} meds scheduled at 08:00 AM\n")


def test_drug_interactions_checker():
    print("="*60)
    print("TEST 5: Multi-Drug Interaction Safety Matrix")
    print("="*60)
    # 1. High risk pair
    r1 = client.post("/medicine/check-interactions", json={"medicines": ["Warfarin", "Aspirin"]})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1.get("hasInteractions") is True
    assert len(d1.get("interactions")) >= 1
    print(f"✓ Warfarin + Aspirin: {d1.get('interactions')[0]['severity']} hazard correctly detected")

    # 2. Atorvastatin + Clarithromycin
    r2 = client.post("/medicine/check-interactions", json={"medicines": ["Atorvastatin", "Clarithromycin"]})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("hasInteractions") is True
    print(f"✓ Atorvastatin + Clarithromycin: {d2.get('interactions')[0]['severity']} hazard correctly detected")

    # 3. Safe pair
    r3 = client.post("/medicine/check-interactions", json={"medicines": ["Paracetamol", "Amoxicillin"]})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3.get("hasInteractions") is False
    print("✓ Paracetamol + Amoxicillin: Correctly evaluated as Safe / No Interaction\n")


def test_medicine_info_monograph():
    print("="*60)
    print("TEST 6: Clinical Medicine Monograph Lookup")
    print("="*60)
    r = client.post("/chat/medicine-info", json={"medicine_name": "Augmentin 625 Duo"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "success"
    assert "Amoxicillin" in data.get("composition")
    print(f"✓ Brand: {data.get('brand_name')}")
    print(f"✓ Generic / Active Salt: {data.get('generic_name')}")
    print(f"✓ Uses: {data.get('uses')}")
    print(f"✓ Dosage Guidelines: {data.get('dosage_guidelines')}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PHASE 6: AI HEALTHCARE SYSTEM - VERIFICATION SUITE")
    print("="*60)
    try:
        test_ai_chatbot()
        test_symptom_triage()
        test_lab_report_explainer()
        test_prescription_analysis()
        test_drug_interactions_checker()
        test_medicine_info_monograph()
        print("="*60)
        print("✅ ALL PHASE 6 AI TESTS COMPLETED & VERIFIED SUCCESSFULLY")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
