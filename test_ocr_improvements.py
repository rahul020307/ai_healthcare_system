#!/usr/bin/env python3
"""
Test script for enhanced OCR processor
Tests fuzzy matching, abbreviation handling, and dosage extraction
"""

import sys
sys.path.insert(0, '/workspaces/ai_healthcare_system/application/backend')

from app.utils.ocr_processor import (
    process_prescription_ocr,
    fuzzy_match_medicine,
    extract_dosage_info,
    extract_frequency_info,
    similarity_score,
    normalize_medicine_text,
    validate_prescription_text,
)

# Sample medicine database (minimal for testing)
TEST_MEDICINES = [
    {
        "medicine_id": "med_001",
        "name": "Aspirin",
        "brand_name": "Aspirin",
        "generic_name": "Acetylsalicylic Acid",
        "category": "Analgesic",
        "dosage": "325mg/500mg",
        "side_effects": ["Gastrointestinal upset", "Bleeding risk"]
    },
    {
        "medicine_id": "med_002",
        "name": "Paracetamol",
        "brand_name": "Paracetamol",
        "generic_name": "Acetaminophen",
        "category": "Analgesic",
        "dosage": "500mg/650mg",
        "side_effects": ["Liver damage in overdose"]
    },
    {
        "medicine_id": "med_003",
        "name": "Ibuprofen",
        "brand_name": "Ibuprofen",
        "generic_name": "2-(4-isobutylphenyl)propionic acid",
        "category": "NSAID",
        "dosage": "200mg/400mg",
        "side_effects": ["GI ulcers", "Kidney damage"]
    },
    {
        "medicine_id": "med_004",
        "name": "Amoxicillin",
        "brand_name": "Amoxicillin",
        "generic_name": "Amoxicillin trihydrate",
        "category": "Antibiotic",
        "dosage": "250mg/500mg",
        "side_effects": ["Allergic reactions", "Diarrhea"]
    },
]

def test_case_1():
    """Test fuzzy matching with typos"""
    print("\n" + "="*60)
    print("TEST 1: Fuzzy Matching - Typo Handling")
    print("="*60)
    
    test_inputs = [
        ("Paracetomol", "Paracetamol (typo)"),
        ("Asperin", "Aspirin (typo)"),
        ("Ibuprofen", "Ibuprofen (correct)"),
        ("Amoxicilin", "Amoxicillin (typo)"),
    ]
    
    for input_text, description in test_inputs:
        match = fuzzy_match_medicine(input_text, TEST_MEDICINES, threshold=0.65)
        score = similarity_score(input_text.lower(), 
                                 (match.get("brand_name") if match else "").lower())
        
        if match:
            print(f"✓ '{input_text}' ({description})")
            print(f"  → Matched: {match['brand_name']} (Generic: {match['generic_name']})")
            print(f"  → Similarity: {score:.0%}")
        else:
            print(f"✗ '{input_text}' - No match found")
        print()

def test_case_2():
    """Test abbreviation handling"""
    print("\n" + "="*60)
    print("TEST 2: Medical Abbreviation Expansion")
    print("="*60)
    
    test_texts = [
        "Aspirin 500mg BD x7 days",
        "Paracetamol 650mg AC TID",
        "Amoxicillin 250mg OD x10 days",
    ]
    
    for text in test_texts:
        normalized = normalize_medicine_text(text)
        print(f"Original:   {text}")
        print(f"Normalized: {normalized}")
        print()

def test_case_3():
    """Test dosage extraction"""
    print("\n" + "="*60)
    print("TEST 3: Dosage & Frequency Extraction")
    print("="*60)
    
    test_texts = [
        "Aspirin 500mg twice daily after food",
        "Paracetamol 650mg tablet 3 times daily",
        "Ibuprofen 200mg capsule once daily at night",
    ]
    
    for text in test_texts:
        dosages = extract_dosage_info(text)
        frequencies = extract_frequency_info(text)
        
        print(f"Text: {text}")
        print(f"  Dosages: {[d['full'] for d in dosages]}")
        print(f"  Frequencies: {frequencies}")
        print()

def test_case_4():
    """Test full prescription processing"""
    print("\n" + "="*60)
    print("TEST 4: Full Prescription Processing (Multi-medicine)")
    print("="*60)
    
    prescription_text = """
    DR. SHARMA'S CLINIC
    
    Patient: Rahul Kumar
    Date: 2024-01-15
    
    Rx:
    1. Paracetomol 500mg tablet BD x3 days
    2. Asperin 325mg caplet OD AC
    3. Ibuprofen 200mg tablet PRN
    4. Amoxicilin 500mg capsule TID x7 days
    """
    
    print("Input Prescription:")
    print(prescription_text)
    print("\n" + "-"*60)
    
    result = process_prescription_ocr(prescription_text, TEST_MEDICINES)
    
    print(f"\nExtraction Results:")
    print(f"Status: {result.get('status')}")
    print(f"Medicines Found: {result.get('medicine_count')}")
    print(f"Confident Matches: {result.get('has_confident_matches')}")
    
    for med in result.get('extracted_medicines', []):
        print(f"\n  💊 {med['brand_name']} ({med['generic_name']})")
        print(f"     Dosage: {med['dosage']}")
        print(f"     Frequency: {', '.join(med['frequency'])}")
        print(f"     Duration: {med['duration']}")
        print(f"     Confidence: {med['confidence']:.0%}")

def test_case_5():
    """Test low-quality OCR output"""
    print("\n" + "="*60)
    print("TEST 5: Handling Low-Quality OCR Output (Garbled)")
    print("="*60)
    
    poor_ocr = """
    Rx:
    Paraceutamol 50omg 2x daily
    Asppirin 325 tablet once
    lbuprofen 200mg 3x per day AC
    Amoxicilin 5oomg capsule
    """
    
    print("Poor OCR Output (with OCR errors):")
    print(poor_ocr)
    print("\n" + "-"*60)
    
    result = process_prescription_ocr(poor_ocr, TEST_MEDICINES)
    
    print(f"\nRecovery Results:")
    print(f"Medicines Recovered: {result.get('medicine_count')}")
    
    for med in result.get('extracted_medicines', []):
        print(f"  ✓ {med['brand_name']} - Confidence: {med['confidence']:.0%}")


def test_case_6():
    """Ensure random images are not accepted as prescriptions."""
    print("\n" + "="*60)
    print("TEST 6: Random Image / Non-Prescription Rejection")
    print("="*60)

    random_photo_text = """
    a colorful photo of a dog outdoor with blue sky and trees
    family vacation picture at the beach smiling and waving
    """

    valid_prescription = """
    Dr. Sharma Clinic
    Rx:
    Paracetamol 500mg twice daily for 5 days
    Amoxicillin 250mg once daily for 7 days
    """

    assert validate_prescription_text(random_photo_text) is False
    assert validate_prescription_text(valid_prescription) is True

    print("Random image-like text correctly rejected.")
    print("Valid prescription text correctly accepted.")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("OCR PROCESSOR - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    try:
        test_case_1()
        test_case_2()
        test_case_3()
        test_case_4()
        test_case_5()
        test_case_6()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
