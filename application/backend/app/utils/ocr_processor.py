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


def fuzzy_match_medicine(medicine_name: str, medicines_db: List[Dict], threshold: float = 0.70) -> Optional[Dict]:
    """
    Find best matching medicine using fuzzy matching against brand names,
    generic names, and individual salt / composition ingredients.
    """
    normalized_input = normalize_medicine_text(medicine_name)
    if not normalized_input or len(normalized_input) < 3:
        return None

    best_match = None
    best_score = 0

    for med in medicines_db:
        brand_name = med.get("brand_name", "") or med.get("name", "")
        generic_name = med.get("generic_name", "")
        composition = med.get("composition", "")

        normalized_brand = normalize_medicine_text(brand_name)
        normalized_generic = normalize_medicine_text(generic_name)

        brand_score = similarity_score(normalized_input, normalized_brand)
        generic_score = similarity_score(normalized_input, normalized_generic)

        # Check sub-components/salts in generic_name and composition (split by +, &, ,, /)
        salt_scores = []
        for raw_field in [generic_name, composition]:
            if not raw_field:
                continue
            parts = re.split(r"[\+\&\,/]|(?:\band\b)", raw_field)
            for part in parts:
                clean_part = normalize_medicine_text(re.sub(r"\d+.*", "", part))
                if len(clean_part) >= 3:
                    salt_scores.append(similarity_score(normalized_input, clean_part))
                    # If input is a prefix or word in the salt name
                    if normalized_input in clean_part or clean_part in normalized_input:
                        salt_scores.append(0.88)

        max_salt_score = max(salt_scores) if salt_scores else 0
        current_score = max(brand_score, generic_score, max_salt_score)

        if current_score > best_score:
            best_score = current_score
            best_match = med

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


def validate_prescription_text(raw_ocr_text: str) -> bool:
    """Return True only when the text looks like a medical prescription."""
    if not raw_ocr_text or not str(raw_ocr_text).strip():
        return False

    normalized = normalize_medicine_text(raw_ocr_text)
    if len(normalized) < 20:
        return False

    prescription_signals = re.search(
        r"\b(?:rx|prescription|doctor|clinic|patient|medicine|medicines|tablet|capsule|syrup|dosage|frequency|dr|physician)\b",
        normalized,
        re.IGNORECASE,
    )
    medical_timing = re.search(
        r"\b(?:od|bd|tid|qid|once|twice|thrice|morning|afternoon|evening|night|before|after|daily|days?|weeks?|months?)\b",
        normalized,
        re.IGNORECASE,
    )
    dosage_pattern = re.search(
        r"\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|units?|tablet|capsule|drops?|spray)\b",
        normalized,
        re.IGNORECASE,
    )

    return bool(prescription_signals and (medical_timing or dosage_pattern))


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
    if not validate_prescription_text(raw_ocr_text):
        return {
            "status": "invalid",
            "extracted_medicines": [],
            "raw_text_length": len(raw_ocr_text or ""),
            "medicine_count": 0,
            "has_confident_matches": False,
            "message": "The uploaded image does not appear to contain a valid medical prescription."
        }

    extracted_medicines = []
    seen_medicine_ids = set()
    seen_medicine_names = set()

    def add_medicine_match(med_dict, dosage_list, freq_list, dur_val, line_text, conf):
        med_id = med_dict.get("medicine_id") or med_dict.get("id") or med_dict.get("brand_name")
        brand = med_dict.get("brand_name") or med_dict.get("name", "")
        generic = med_dict.get("generic_name", "")
        key = (brand or generic or "").lower().strip()

        if med_id and med_id in seen_medicine_ids:
            return
        if key and key in seen_medicine_names:
            return

        if med_id:
            seen_medicine_ids.add(med_id)
        if key:
            seen_medicine_names.add(key)

        extracted_medicines.append({
            "medicine_id": med_id,
            "brand_name": brand,
            "generic_name": generic,
            "dosage": dosage_list[0].get("full") if dosage_list else med_dict.get("dosage", "1 tablet"),
            "frequency": freq_list if freq_list else ["as prescribed"],
            "duration": dur_val or "as advised",
            "line": line_text,
            "confidence": round(conf, 2)
        })

    # Split text into lines for line-by-line analysis
    lines = [line.strip() for line in raw_ocr_text.split('\n') if line.strip()]

    for line_clean in lines:
        if len(line_clean) < 3:
            continue
        if sum(c.isalnum() for c in line_clean) / len(line_clean) < 0.4:
            continue

        normalized_line = normalize_medicine_text(line_clean)
        line_dosages = extract_dosage_info(line_clean)
        line_freqs = extract_frequency_info(normalized_line)
        line_duration = extract_duration_info(line_clean)

        line_matched = False

        # 1. Exact match check in line
        for medicine in medicines_db:
            brand_name = medicine.get("brand_name") or medicine.get("name", "")
            generic_name = medicine.get("generic_name", "")

            if brand_name and brand_name.lower() in line_clean.lower():
                add_medicine_match(medicine, line_dosages, line_freqs, line_duration, line_clean, 0.95)
                line_matched = True
                break
            elif generic_name and generic_name.lower() in line_clean.lower():
                add_medicine_match(medicine, line_dosages, line_freqs, line_duration, line_clean, 0.90)
                line_matched = True
                break

        # 2. If no exact match on this line, try fuzzy matching on candidate tokens/words
        if not line_matched:
            # Extract candidate medicine names from words before dosage or individual words
            line_tokens = []
            # Match word sequence before dosage pattern if present
            dosage_match = re.search(r"([A-Za-z\s]{3,30}?)\s+\d+\s*(?:mg|g|ml|mcg|tablet|capsule|cap|tab)", line_clean, re.IGNORECASE)
            if dosage_match:
                candidate = dosage_match.group(1).strip()
                # strip list numbering like "1. ", "2) "
                candidate = re.sub(r"^\d+[\.\)\-]?\s*", "", candidate).strip()
                if len(candidate) >= 3:
                    line_tokens.append(candidate)

            # Also consider individual words of sufficient length
            words = [re.sub(r"[^\w]", "", w) for w in line_clean.split()]
            for w in words:
                if len(w) >= 4 and not w.isdigit():
                    if w.lower() not in {"tablet", "tablets", "capsule", "capsules", "syrup", "daily", "twice", "thrice", "morning", "night", "food", "clinic", "patient", "doctor"}:
                        line_tokens.append(w)

            for token in line_tokens:
                matched_med = fuzzy_match_medicine(token, medicines_db, threshold=0.65)
                if matched_med:
                    brand = matched_med.get("brand_name") or matched_med.get("name", "")
                    sim = similarity_score(token.lower(), brand.lower())
                    conf = max(0.75, sim)
                    add_medicine_match(matched_med, line_dosages, line_freqs, line_duration, line_clean, conf)
                    line_matched = True
                    break

    # 3. Global Regex Fallback across entire document for any missed items
    for match in re.finditer(r"([A-Za-z\s]{3,30}?)\s+(\d+\s*(?:mg|g|ml|mcg|tablet|capsule))", raw_ocr_text, re.IGNORECASE):
        candidate = match.group(1).strip()
        candidate = re.sub(r"^\d+[\.\)\-]?\s*", "", candidate).strip()
        if len(candidate) >= 3:
            matched_med = fuzzy_match_medicine(candidate, medicines_db, threshold=0.65)
            if matched_med:
                med_id = matched_med.get("medicine_id") or matched_med.get("id") or matched_med.get("brand_name")
                if med_id not in seen_medicine_ids:
                    brand = matched_med.get("brand_name") or matched_med.get("name", "")
                    sim = similarity_score(candidate.lower(), brand.lower())
                    full_context = raw_ocr_text[max(0, match.start() - 20):min(len(raw_ocr_text), match.end() + 40)]
                    ctx_dosages = extract_dosage_info(match.group(2))
                    ctx_freqs = extract_frequency_info(full_context)
                    ctx_dur = extract_duration_info(full_context)
                    add_medicine_match(matched_med, ctx_dosages, ctx_freqs, ctx_dur, candidate, max(0.75, sim))

    return {
        "status": "success",
        "extracted_medicines": extracted_medicines,
        "raw_text_length": len(raw_ocr_text),
        "medicine_count": len(extracted_medicines),
        "has_confident_matches": any(m.get("confidence", 0) >= 0.8 for m in extracted_medicines)
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
