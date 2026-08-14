"""
Enhanced OCR Processing Module - CuraAssist CareHub
Handles accurate prescription & medicine detection with fuzzy matching & AI validation
"""

import re
import json
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Medical abbreviations & common misspellings database
MEDICAL_ABBREVIATIONS = {
    "asp": "aspirin",
    "paracet": "paracetamol",
    "cap": "capsule",
    "tab": "tablet",
    "mg": "milligram",
    "ml": "milliliter",
    "bd": "twice daily",
    "tid": "thrice daily",
    "qid": "four times daily",
    "od": "once daily",
    "hs": "at bedtime",
    "ac": "before food",
    "pc": "after food",
    "stat": "immediately",
    "prn": "as needed",
    "iv": "intravenous",
    "im": "intramuscular",
    "sc": "subcutaneous",
    "po": "oral",
}

COMMON_MISSPELLINGS = {
    "asprin": "aspirin",
    "paracetomol": "paracetamol",
    "ibuprofen": "ibuprofen",
    "amoxicilin": "amoxicillin",
    "azithromycin": "azithromycin",
    "metformin": "metformin",
    "atorvastatin": "atorvastatin",
    "omeprazole": "omeprazole",
    "loratadine": "loratadine",
    "cetirizine": "cetirizine",
    "diphenhydramine": "diphenhydramine",
    "dexamethasone": "dexamethasone",
    "prednisolone": "prednisolone",
}

DOSAGE_PATTERN = r"(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|units?|tablet?|capsule?|drop?|spray?)"
STRENGTH_PATTERN = r"(\d+(?:\.\d+)?)\s*(?:mg|g|mcg|%)"


def normalize_medicine_text(text: str) -> str:
    """Normalize medicine text for better matching."""
    # Convert to lowercase
    text = text.lower().strip()
    
    # Remove common non-alphanumeric characters
    text = re.sub(r"[^\w\s-]", " ", text)
    
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    
    # Expand common abbreviations
    for abbr, full in MEDICAL_ABBREVIATIONS.items():
        text = re.sub(r"\b" + abbr + r"\b", full, text)
    
    # Fix common misspellings
    for misspell, correct in COMMON_MISSPELLINGS.items():
        text = re.sub(r"\b" + misspell + r"\b", correct, text)
    
    return text.strip()


def similarity_score(str1: str, str2: str) -> float:
    """Calculate string similarity using SequenceMatcher (0-1 scale)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def fuzzy_match_medicine(medicine_name: str, medicines_db: List[Dict], threshold: float = 0.75) -> Optional[Dict]:
    """
    Find best matching medicine using fuzzy matching.
    
    Args:
        medicine_name: User-provided medicine name (potentially with typos)
        medicines_db: List of medicine records from database
        threshold: Minimum similarity score (0-1)
    
    Returns:
        Best matching medicine dict or None if no good match found
    """
    normalized_input = normalize_medicine_text(medicine_name)
    best_match = None
    best_score = 0
    
    for med in medicines_db:
        # Check against brand name
        brand_name = med.get("brand_name", "") or med.get("name", "")
        generic_name = med.get("generic_name", "")
        
        normalized_brand = normalize_medicine_text(brand_name)
        normalized_generic = normalize_medicine_text(generic_name)
        
        # Calculate similarity scores
        brand_score = similarity_score(normalized_input, normalized_brand)
        generic_score = similarity_score(normalized_input, normalized_generic)
        
        # Take the maximum score
        current_score = max(brand_score, generic_score)
        
        if current_score > best_score:
            best_score = current_score
            best_match = med
    
    # Return only if score exceeds threshold
    if best_score >= threshold:
        return best_match
    
    return None


def extract_dosage_info(text: str) -> List[Dict]:
    """Extract dosage information from OCR text."""
    dosages = []
    
    # Find all dosage patterns (e.g., "500mg", "2 tablets", "10 ml")
    matches = re.finditer(DOSAGE_PATTERN, text, re.IGNORECASE)
    
    for match in matches:
        amount = match.group(1)
        unit = match.group(2)
        dosages.append({
            "amount": amount,
            "unit": unit,
            "full": f"{amount} {unit}"
        })
    
    return dosages


def extract_frequency_info(text: str) -> List[str]:
    """Extract medication frequency/timing from OCR text."""
    text_lower = text.lower()
    frequencies = []
    
    frequency_patterns = {
        "once daily": [r"\bonce\s+daily\b", r"\bod\b", r"\b1x\b"],
        "twice daily": [r"\btwice\s+daily\b", r"\bbd\b", r"\b2x\b"],
        "thrice daily": [r"\bthrice\s+daily\b", r"\btid\b", r"\b3x\b"],
        "four times daily": [r"\bfour\s+times\s+daily\b", r"\bqid\b", r"\b4x\b"],
        "morning": [r"\bmorning\b", r"\bam\b"],
        "afternoon": [r"\bafternoon\b"],
        "evening": [r"\bevening\b", r"\bpm\b"],
        "night": [r"\bnight\b", r"\bhs\b"],
        "before food": [r"\bbefore\s+food\b", r"\bac\b"],
        "after food": [r"\bafter\s+food\b", r"\bpc\b"],
        "as needed": [r"\bas\s+needed\b", r"\bprn\b"],
    }
    
    for frequency, patterns in frequency_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                frequencies.append(frequency)
                break
    
    return list(set(frequencies))  # Remove duplicates


def extract_duration_info(text: str) -> Optional[str]:
    """Extract treatment duration from OCR text."""
    # Look for patterns like "5 days", "1 week", "2 weeks", "1 month"
    duration_patterns = [
        (r"(\d+)\s*days?", "{} days"),
        (r"(\d+)\s*weeks?", "{} weeks"),
        (r"(\d+)\s*months?", "{} months"),
    ]
    
    for pattern, template in duration_patterns:
        match = re.search(pattern, text.lower())
        if match:
            return template.format(match.group(1))
    
    return None


def score_medicine_match(medicine_name: str, ocr_text: str, medicines_db: List[Dict]) -> Tuple[Optional[Dict], float]:
    """
    Score and find best matching medicine with confidence level.
    
    Returns:
        Tuple of (matched_medicine_dict, confidence_score_0_to_1)
    """
    matched_med = fuzzy_match_medicine(medicine_name, medicines_db, threshold=0.65)
    
    if matched_med:
        # Additional scoring: check if generic name or related words appear in text
        full_text_lower = ocr_text.lower()
        generic = (matched_med.get("generic_name") or "").lower()
        brand = (matched_med.get("brand_name") or matched_med.get("name") or "").lower()
        
        confidence = 0.8  # Base confidence for fuzzy match
        
        # Boost confidence if we find exact keywords in text
        if brand and brand in full_text_lower:
            confidence = min(0.95, confidence + 0.15)
        if generic and generic in full_text_lower:
            confidence = min(0.95, confidence + 0.15)
        
        return matched_med, confidence
    
    return None, 0.0


def process_prescription_ocr(raw_ocr_text: str, medicines_db: List[Dict]) -> Dict:
    """
    Process raw OCR text to extract structured prescription data.
    
    Args:
        raw_ocr_text: Raw text output from Tesseract or other OCR engine
        medicines_db: Database of known medicines
    
    Returns:
        Structured prescription data with medicines, dosages, frequencies, etc.
    """
    # Normalize the input text
    normalized_text = normalize_medicine_text(raw_ocr_text)
    
    extracted_medicines = []
    
    # Split text into lines for better medicine detection
    lines = raw_ocr_text.split('\n')
    
    # Try to detect medicine mentions in each line
    for line in lines:
        line_clean = line.strip()
        
        # Skip very short lines (likely not medicine names)
        if len(line_clean) < 3:
            continue
        
        # Skip lines with low alphanumeric content
        if sum(c.isalnum() for c in line_clean) / len(line_clean) < 0.5:
            continue
        
        # Look for medicine names in this line
        for medicine in medicines_db:
            brand_name = medicine.get("brand_name") or medicine.get("name", "")
            generic_name = medicine.get("generic_name", "")
            
            if not brand_name:
                continue
            
            # Check if medicine appears in line (case-insensitive)
            if brand_name.lower() in line_clean.lower() or generic_name.lower() in line_clean.lower():
                # Extract dosage and frequency for this specific line
                dosages = extract_dosage_info(line_clean)
                frequencies = extract_frequency_info(line_clean)
                duration = extract_duration_info(line_clean)
                
                extracted_medicines.append({
                    "medicine_id": medicine.get("medicine_id"),
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "dosage": dosages[0].get("full") if dosages else medicine.get("dosage", "1 tablet"),
                    "frequency": frequencies if frequencies else ["as prescribed"],
                    "duration": duration or "as advised",
                    "line": line_clean,
                    "confidence": 0.85
                })
                break
    
    # If no exact matches found, try fuzzy matching
    if not extracted_medicines:
        medicine_name_candidates = []
        # Extract potential medicine names (words that appear before dosage patterns)
        for match in re.finditer(r"([A-Za-z\s]{3,30}?)\s+\d+\s*(?:mg|g|ml|tablet|capsule)", raw_ocr_text):
            candidate = match.group(1).strip()
            if len(candidate) > 2:
                medicine_name_candidates.append(candidate)
        
        for candidate in medicine_name_candidates:
            matched_med, confidence = score_medicine_match(candidate, raw_ocr_text, medicines_db)
            if matched_med and confidence > 0.7:
                dosages = extract_dosage_info(raw_ocr_text)
                frequencies = extract_frequency_info(raw_ocr_text)
                duration = extract_duration_info(raw_ocr_text)
                
                extracted_medicines.append({
                    "medicine_id": matched_med.get("medicine_id"),
                    "brand_name": matched_med.get("brand_name") or matched_med.get("name"),
                    "generic_name": matched_med.get("generic_name", ""),
                    "dosage": dosages[0].get("full") if dosages else matched_med.get("dosage", "1 tablet"),
                    "frequency": frequencies if frequencies else ["as prescribed"],
                    "duration": duration or "as advised",
                    "confidence": confidence
                })
    
    return {
        "status": "success",
        "extracted_medicines": extracted_medicines,
        "raw_text_length": len(raw_ocr_text),
        "medicine_count": len(extracted_medicines),
        "has_confident_matches": any(m.get("confidence", 0) > 0.8 for m in extracted_medicines)
    }


def generate_prescription_summary(extracted_data: Dict) -> str:
    """Generate human-readable prescription summary from extracted data."""
    medicines = extracted_data.get("extracted_medicines", [])
    
    if not medicines:
        return "No medicines detected in prescription. Please review the document manually."
    
    summary_lines = ["PRESCRIPTION EXTRACTION SUMMARY", "=" * 50, ""]
    
    for med in medicines:
        summary_lines.append(f"💊 {med.get('brand_name', 'Medicine')}")
        if med.get('generic_name'):
            summary_lines.append(f"   Generic: {med['generic_name']}")
        summary_lines.append(f"   Dosage: {med.get('dosage', 'As prescribed')}")
        if med.get('frequency'):
            summary_lines.append(f"   Frequency: {', '.join(med['frequency'])}")
        summary_lines.append(f"   Duration: {med.get('duration', 'As advised')}")
        confidence = med.get("confidence", 0)
        confidence_pct = int(confidence * 100)
        summary_lines.append(f"   Confidence: {confidence_pct}%" + (" ✓ High" if confidence > 0.8 else " ⚠ Review"))
        summary_lines.append("")
    
    return "\n".join(summary_lines)
