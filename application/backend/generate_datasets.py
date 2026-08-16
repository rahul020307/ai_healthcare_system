import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Medicines Dataset (medicines.json)
medicines_data = [
    {
        "medicine_id": "MED-001",
        "brand_name": "Dolo 650",
        "generic_name": "Paracetamol",
        "composition": "Paracetamol (650 mg)",
        "category": "Analgesics & Antipyretics",
        "dosage_form": "Tablet",
        "strength": "650 mg",
        "manufacturer": "Micro Labs Ltd",
        "uses": ["Fever reduction", "Mild to moderate pain", "Headache relief"],
        "dosage": "1 tablet every 4 to 6 hours as needed post meal. Max 4 tablets/day.",
        "age_restriction": "Above 12 years",
        "side_effects": ["Nausea", "Allergic skin rash", "Gastric irritation (rare)"],
        "warnings": ["Do not consume alcohol while taking paracetamol", "Avoid liver failure risk by avoiding overdose"],
        "contraindications": ["Severe hepatic impairment", "Known hypersensitivity to paracetamol"],
        "storage": "Store below 30°C in a dry place away from direct sunlight.",
        "prescription_required": False,
        "barcode": "8901234567890",
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=400",
        "price": 30.50
    },
    {
        "medicine_id": "MED-002",
        "brand_name": "Limcee 500",
        "generic_name": "Ascorbic Acid",
        "composition": "Vitamin C (500 mg) + Sodium Ascorbate",
        "category": "Vitamins & Minerals",
        "dosage_form": "Chewable Tablet",
        "strength": "500 mg",
        "manufacturer": "Abbott Healthcare",
        "uses": ["Immunity booster", "Scurvy prevention", "Antioxidant support"],
        "dosage": "1 chewable tablet daily after breakfast.",
        "age_restriction": "Above 6 years",
        "side_effects": ["Mild stomach ache", "Diarrhea (if overconsumed)"],
        "warnings": ["High dosage may cause kidney stone risks in predisposed individuals"],
        "contraindications": ["Hyperoxaluria", "Severe kidney impairment"],
        "storage": "Store in a cool dry place. Keep container tightly closed.",
        "prescription_required": False,
        "barcode": "8902345678901",
        "image_url": "https://images.unsplash.com/photo-1577401239170-897942555fb3?auto=format&fit=crop&q=80&w=400",
        "price": 24.00
    },
    {
        "medicine_id": "MED-003",
        "brand_name": "Augmentin 625 Duo",
        "generic_name": "Amoxicillin and Clavulanate Potassium",
        "composition": "Amoxicillin (500 mg) + Clavulanic Acid (125 mg)",
        "category": "Antibiotics",
        "dosage_form": "Tablet",
        "strength": "625 mg",
        "manufacturer": "GlaxoSmithKline",
        "uses": ["Bacterial sinus infection", "Pneumonia", "Urinary tract infections", "Skin infections"],
        "dosage": "1 tablet twice daily for 5-7 days strictly as prescribed.",
        "age_restriction": "Above 12 years",
        "side_effects": ["Diarrhea", "Vomiting", "Oral thrush"],
        "warnings": ["Complete full antibiotic course even if feeling better"],
        "contraindications": ["Penicillin allergy", "History of amoxicillin-associated jaundice"],
        "storage": "Store in original foil package away from moisture below 25°C.",
        "prescription_required": True,
        "barcode": "8903456789012",
        "image_url": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&q=80&w=400",
        "price": 201.75
    },
    {
        "medicine_id": "MED-004",
        "brand_name": "Lipivas 10",
        "generic_name": "Atorvastatin",
        "composition": "Atorvastatin Calcium (10 mg)",
        "category": "Cardiovascular / Lipid Lowering",
        "dosage_form": "Tablet",
        "strength": "10 mg",
        "manufacturer": "Cipla Ltd",
        "uses": ["High cholesterol treatment", "Prevention of heart attack and stroke"],
        "dosage": "1 tablet daily at bedtime.",
        "age_restriction": "Above 18 years",
        "side_effects": ["Muscle soreness", "Elevated liver enzymes", "Headache"],
        "warnings": ["Report unusual muscle pain or weakness immediately"],
        "contraindications": ["Active liver disease", "Pregnancy & breastfeeding"],
        "storage": "Store at room temperature below 30°C.",
        "prescription_required": True,
        "barcode": "8904567890123",
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=400",
        "price": 72.80
    },
    {
        "medicine_id": "MED-005",
        "brand_name": "Pantocid 40",
        "generic_name": "Pantoprazole",
        "composition": "Pantoprazole Sodium (40 mg)",
        "category": "Gastrointestinal",
        "dosage_form": "Enteric-Coated Tablet",
        "strength": "40 mg",
        "manufacturer": "Sun Pharma",
        "uses": ["Acid reflux / GERD", "Peptic ulcer disease", "Zollinger-Ellison syndrome"],
        "dosage": "1 tablet daily 30 minutes before morning breakfast.",
        "age_restriction": "Above 12 years",
        "side_effects": ["Flatulence", "Headache", "Abdominal pain"],
        "warnings": ["Long term use may decrease Vitamin B12 and magnesium absorption"],
        "contraindications": ["Hypersensitivity to substituted benzimidazoles"],
        "storage": "Protect from moisture and light.",
        "prescription_required": True,
        "barcode": "8905678901234",
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=400",
        "price": 145.00
    }
]

# 2. Medicine Categories Dataset (medicine_categories.json)
categories_data = [
    {
        "category_id": "CAT-001",
        "category_name": "Pain Relief & Antipyretics",
        "icon": "pill",
        "description": "Medicines for treating headaches, body pain, joint pain, and fever reduction."
    },
    {
        "category_id": "CAT-002",
        "category_name": "Vitamins & Supplements",
        "icon": "apple",
        "description": "Nutritional supplements, immunity boosters, minerals, and daily multivitamin care."
    },
    {
        "category_id": "CAT-003",
        "category_name": "Antibiotics",
        "icon": "shield",
        "description": "Prescription antibiotics for bacterial infections across respiratory, urinary, and dermatological care."
    },
    {
        "category_id": "CAT-004",
        "category_name": "Cardiovascular Care",
        "icon": "heart",
        "description": "Blood pressure management, statins, blood thinners, and cardiac health medicines."
    },
    {
        "category_id": "CAT-005",
        "category_name": "Gastrointestinal Care",
        "icon": "activity",
        "description": "Antacids, proton pump inhibitors, laxatives, and digestion support."
    }
]

# 3. Pharmacy Dataset (pharmacies.json)
pharmacies_data = [
    {
        "pharmacy_id": "PHARM-001",
        "pharmacy_name": "MedPlus 24x7 Express Pharmacy",
        "address": "Plot 14, Hitech City Main Road, Opposite Cyber Towers",
        "city": "Hyderabad",
        "state": "Telangana",
        "latitude": 17.4504,
        "longitude": 78.3808,
        "phone": "+91 40 4455 6677",
        "opening_hours": "Open 24 Hours",
        "home_delivery": True,
        "rating": 4.8
    },
    {
        "pharmacy_id": "PHARM-002",
        "pharmacy_name": "Apollo Pharmacy Jubilee Hills",
        "address": "Road No. 36, Near Metro Station, Jubilee Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "latitude": 17.4325,
        "longitude": 78.4071,
        "phone": "+91 40 2360 7777",
        "opening_hours": "07:00 AM - 11:00 PM",
        "home_delivery": True,
        "rating": 4.9
    },
    {
        "pharmacy_id": "PHARM-003",
        "pharmacy_name": "Wellness Forever Chemist",
        "address": "100 Feet Road, Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "phone": "+91 80 2525 8899",
        "opening_hours": "Open 24 Hours",
        "home_delivery": True,
        "rating": 4.7
    }
]

# 4. Hospital Dataset (hospitals.json)
hospitals_data = [
    {
        "hospital_id": "HOSP-001",
        "hospital_name": "Apollo Hospitals Jubilee Hills",
        "address": "Road No. 72, Opposite Bharatiya Vidya Bhavan, Film Nagar",
        "city": "Hyderabad",
        "latitude": 17.4184,
        "longitude": 78.4116,
        "departments": ["Cardiology", "Neurology", "Orthopedics", "Emergency Trauma", "Oncology"],
        "emergency_available": True,
        "phone": "+91 40 2360 7777",
        "rating": 4.9
    },
    {
        "hospital_id": "HOSP-002",
        "hospital_name": "Yashoda Hospitals Somajiguda",
        "address": "Raj Bhavan Road, Somajiguda",
        "city": "Hyderabad",
        "latitude": 17.4262,
        "longitude": 78.4578,
        "departments": ["Pulmonology", "Gastroenterology", "Pediatrics", "Critical Care"],
        "emergency_available": True,
        "phone": "+91 40 4567 4567",
        "rating": 4.8
    },
    {
        "hospital_id": "HOSP-003",
        "hospital_name": "Manipal Hospital HAL Airport Road",
        "address": "98 HAL Old Airport Rd, Kodihalli",
        "city": "Bengaluru",
        "latitude": 12.9585,
        "longitude": 77.6486,
        "departments": ["Cardiothoracic Surgery", "Nephrology", "Organ Transplant", "Emergency"],
        "emergency_available": True,
        "phone": "+91 80 2502 4444",
        "rating": 4.8
    }
]

# 5. Diagnostic Laboratory Dataset (laboratories.json)
laboratories_data = [
    {
        "lab_id": "LAB-001",
        "lab_name": "Vijaya Diagnostic Centre",
        "address": "Hitech City Metro Pillar 24, Madhapur",
        "latitude": 17.4475,
        "longitude": 78.3912,
        "available_tests": ["Complete Blood Count (CBC)", "Lipid Profile", "HbA1c Glucose Test", "Thyroid Profile (T3 T4 TSH)", "RT-PCR Test"],
        "phone": "+91 40 2345 6789",
        "rating": 4.8
    },
    {
        "lab_id": "LAB-002",
        "lab_name": "Dr Lal PathLabs",
        "address": "Banjara Hills Road No 1, Near GVK One Mall",
        "latitude": 17.4190,
        "longitude": 78.4485,
        "available_tests": ["Liver Function Test (LFT)", "Kidney Function Test (KFT)", "Vitamin D3 & B12 Panel", "D-Dimer Test"],
        "phone": "+91 40 3988 8888",
        "rating": 4.7
    }
]

# 6. Blood Bank Dataset (bloodbanks.json)
bloodbanks_data = [
    {
        "bloodbank_id": "BB-001",
        "bloodbank_name": "NTR Memorial Trust Blood Bank",
        "address": "Road No. 2, Banjara Hills",
        "latitude": 17.4215,
        "longitude": 78.4350,
        "contact_number": "+91 40 3079 9999",
        "available_blood_groups": ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
    },
    {
        "bloodbank_id": "BB-002",
        "bloodbank_name": "Chiranjeevi Charitable Blood Bank",
        "address": "Jubilee Hills Road No. 1",
        "latitude": 17.4285,
        "longitude": 78.4150,
        "contact_number": "+91 40 2355 5555",
        "available_blood_groups": ["O+", "A+", "B+", "AB+", "O-"]
    }
]

# 7. Doctors Dataset (doctors.json)
doctors_data = [
    {
        "doctor_id": "DOC-001",
        "doctor_name": "Dr. K. S. Somasekhar",
        "specialization": "Cardiologist",
        "hospital": "Apollo Hospitals Jubilee Hills",
        "experience": 22,
        "phone": "+91 98490 12345"
    },
    {
        "doctor_id": "DOC-002",
        "doctor_name": "Dr. Sunita Reddy",
        "specialization": "Dermatologist & Cosmetologist",
        "hospital": "Yashoda Hospitals Somajiguda",
        "experience": 15,
        "phone": "+91 98490 67890"
    },
    {
        "doctor_id": "DOC-003",
        "doctor_name": "Dr. Rajesh Varma",
        "specialization": "General Physician & Internal Medicine",
        "hospital": "Manipal Hospital Bengaluru",
        "experience": 18,
        "phone": "+91 98800 11223"
    }
]

# 8. Clinics Dataset (clinics.json)
clinics_data = [
    {
        "clinic_id": "CLN-001",
        "clinic_name": "CuraCare Family Health Clinic",
        "address": "Kondapur Main Road, Near Botanical Garden",
        "latitude": 17.4622,
        "longitude": 78.3655,
        "doctor_name": "Dr. Ananya Rao",
        "phone": "+91 40 6677 8899"
    },
    {
        "clinic_id": "CLN-002",
        "clinic_name": "Skin & Child Wellness Clinic",
        "address": "Gachibowli DLF Road, Opposite Cyber Life",
        "latitude": 17.4435,
        "longitude": 78.3582,
        "doctor_name": "Dr. Vikram Joshi",
        "phone": "+91 40 5544 3322"
    }
]

# 9. Symptoms Dataset (symptoms.json)
# 9. Symptoms Dataset (symptoms.json)
symptoms_data = [
    {
        "symptom_id": "SYM-001",
        "symptom_name": "High Fever & Chills",
        "keywords": ["fever", "pyrexia", "high temp", "chills", "shivering", "burning forehead"],
        "possible_causes": ["Viral upper respiratory infection", "Malaria", "Dengue fever", "Urinary tract infection", "Typhoid", "Pneumonia"],
        "severity": "Moderate to Severe",
        "severity_level": "moderate",
        "suggested_specialist": "General Physician / Infectious Disease Specialist",
        "home_care": ["Drink plenty of warm ORS & fluids (2-3L/day)", "Tepid sponge bath to lower temp", "Take prescribed antipyretic (e.g. Paracetamol 650mg)", "Rest adequately in well-ventilated room", "Monitor temperature every 4 hours"],
        "red_flags": ["Fever above 103°F not responding to antipyretics", "Severe stiff neck with confusion", "Extreme breathlessness or blue lips", "Convulsions or seizures"]
    },
    {
        "symptom_id": "SYM-002",
        "symptom_name": "Persistent Dry / Productive Cough",
        "keywords": ["cough", "dry cough", "wet cough", "phlegm", "mucus", "throat irritation", "wheezing"],
        "possible_causes": ["Upper respiratory viral infection", "Allergic bronchitis", "Bronchial asthma", "GERD acid reflux", "Bacterial pneumonia"],
        "severity": "Mild to Moderate",
        "severity_level": "mild",
        "suggested_specialist": "Pulmonologist / ENT Specialist",
        "home_care": ["Warm saline water gargling twice daily", "Steam inhalation with eucalyptus oil", "Honey and warm ginger tea", "Keep head elevated while sleeping"],
        "red_flags": ["Coughing up blood (hemoptysis)", "Severe chest pain while breathing", "Shortness of breath at rest", "Stridor / high-pitched wheezing"]
    },
    {
        "symptom_id": "SYM-003",
        "symptom_name": "Chest Pain & Pressure",
        "keywords": ["chest pain", "chest tightness", "angina", "left arm pain", "heart palpitations", "pressure in chest"],
        "possible_causes": ["Acute Coronary Syndrome / Angina", "Severe GERD / Acid Reflux", "Costochondritis (rib inflammation)", "Panic attack / Anxiety", "Musculoskeletal strain"],
        "severity": "Severe / Critical Emergency",
        "severity_level": "critical",
        "suggested_specialist": "Cardiologist / Emergency Medicine",
        "home_care": ["Sit upright and remain calm", "Loosen tight clothing", "Do NOT exert physically", "If known cardiac patient, take prescribed Sublingual Nitroglycerin", "Call Emergency SOS (108) immediately"],
        "red_flags": ["Crushing chest pain radiating to left arm/jaw", "Cold sweating, dizziness, nausea", "Difficulty breathing", "Unconsciousness"]
    },
    {
        "symptom_id": "SYM-004",
        "symptom_name": "Throbbing Headache & Migraine",
        "keywords": ["headache", "migraine", "throbbing head", "temple pain", "forehead pain", "light sensitivity"],
        "possible_causes": ["Tension headache", "Migraine with/without aura", "Sinusitis", "Dehydration", "High blood pressure", "Eye strain"],
        "severity": "Mild to Moderate",
        "severity_level": "mild",
        "suggested_specialist": "Neurologist / General Physician",
        "home_care": ["Rest in a quiet, dark room", "Apply cold or warm compress to forehead/neck", "Hydrate with electrolyte water", "Avoid loud sounds and bright screens"],
        "red_flags": ["Sudden explosive 'thunderclap' headache", "Headache accompanied by slurred speech or facial drooping", "High fever with neck rigidity", "Post-head trauma headache"]
    },
    {
        "symptom_id": "SYM-005",
        "symptom_name": "Acid Reflux, Heartburn & Indigestion",
        "keywords": ["acidity", "heartburn", "acid reflux", "gerd", "stomach burning", "bloating", "burping", "indigestion"],
        "possible_causes": ["Gastroesophageal Reflux Disease (GERD)", "Gastritis", "Peptic ulcer", "Spicy/oily food intolerance", "Hiatal hernia"],
        "severity": "Mild to Moderate",
        "severity_level": "mild",
        "suggested_specialist": "Gastroenterologist",
        "home_care": ["Avoid spicy, oily, acidic, and caffeinated foods", "Take antacid / PPI (e.g. Pantoprazole 40mg before meals)", "Do not lie down for 2 hours after meals", "Drink cold milk or coconut water"],
        "red_flags": ["Vomiting blood or coffee-ground material", "Black, tarry stools (melena)", "Severe difficulty swallowing (dysphagia)", "Unexplained rapid weight loss"]
    },
    {
        "symptom_id": "SYM-006",
        "symptom_name": "Skin Rash, Itching & Hives",
        "keywords": ["rash", "itching", "hives", "urticaria", "red spots", "eczema", "skin allergy", "swelling"],
        "possible_causes": ["Allergic contact dermatitis", "Urticaria / Drug reaction", "Viral exanthem", "Eczema / Atopic dermatitis", "Fungal infection"],
        "severity": "Mild to Moderate",
        "severity_level": "mild",
        "suggested_specialist": "Dermatologist / Allergist",
        "home_care": ["Apply soothing calamine lotion or aloe vera gel", "Take OTC antihistamine (e.g. Cetirizine 10mg)", "Use mild fragrance-free soaps and wear loose cotton clothing", "Avoid scratching to prevent secondary bacterial infection"],
        "red_flags": ["Swelling of lips, tongue, or throat (Angioedema)", "Difficulty breathing or wheezing (Anaphylaxis)", "Blistering peeling skin over large body area (Stevens-Johnson syndrome)", "High fever with rapidly spreading purple spots (Purpura)"]
    },
    {
        "symptom_id": "SYM-007",
        "symptom_name": "Joint Pain, Stiffness & Swelling",
        "keywords": ["joint pain", "knee pain", "arthritis", "stiff joints", "swollen knees", "gout", "backache"],
        "possible_causes": ["Osteoarthritis", "Rheumatoid arthritis", "Gout / Hyperuricemia", "Post-viral reactive arthritis (Chikungunya/Dengue)", "Ligament sprain"],
        "severity": "Moderate",
        "severity_level": "moderate",
        "suggested_specialist": "Rheumatologist / Orthopedic Surgeon",
        "home_care": ["Apply warm compress for stiffness, ice packs for acute swelling", "Gentle low-impact range-of-motion stretching", "Elevate swollen joints and rest", "Topical pain-relief gel (Diclofenac)"],
        "red_flags": ["Single hot, red, extremely swollen joint with fever (Septic arthritis)", "Inability to bear any weight on the leg", "Numbness or loss of sensation in limbs"]
    },
    {
        "symptom_id": "SYM-008",
        "symptom_name": "Dizziness, Vertigo & Lightheadedness",
        "keywords": ["dizziness", "vertigo", "spinning room", "lightheaded", "feeling faint", "low bp", "unsteady balance"],
        "possible_causes": ["Benign Paroxysmal Positional Vertigo (BPPV)", "Orthostatic hypotension (low BP)", "Dehydration / Low blood sugar", "Inner ear labyrinthitis", "Anemia"],
        "severity": "Mild to Moderate",
        "severity_level": "moderate",
        "suggested_specialist": "ENT Specialist / Neurologist",
        "home_care": ["Sit down or lie flat immediately to avoid falls", "Hydrate with electrolyte / glucose water", "Move head and change postures slowly", "Avoid driving or operating heavy machinery"],
        "red_flags": ["Dizziness accompanied by double vision, facial weakness, or limb paralysis", "Loss of consciousness / syncope", "Sudden severe hearing loss"]
    },
    {
        "symptom_id": "SYM-009",
        "symptom_name": "Excessive Thirst, Frequent Urination & Fatigue",
        "keywords": ["frequent urination", "excessive thirst", "high sugar", "diabetes symptoms", "fatigue", "dry mouth", "unexplained weight loss"],
        "possible_causes": ["Type 1 / Type 2 Diabetes Mellitus", "Urinary tract infection", "Diabetic ketoacidosis", "Electrolyte imbalance"],
        "severity": "Moderate to High",
        "severity_level": "moderate",
        "suggested_specialist": "Endocrinologist / Diabetologist",
        "home_care": ["Check fasting and postprandial blood sugar levels immediately", "Drink adequate clean water to avoid dehydration", "Avoid sugary beverages, sweets, and refined carbohydrates", "Schedule HbA1c lab test"],
        "red_flags": ["Fruity-smelling breath with deep rapid breathing", "Confusion, lethargy, vomiting (Diabetic Ketoacidosis)", "Blood glucose > 300 mg/dL with ketones"]
    },
    {
        "symptom_id": "SYM-010",
        "symptom_name": "Severe Diarrhea, Vomiting & Dehydration",
        "keywords": ["diarrhea", "loose motion", "vomiting", "food poisoning", "gastroenteritis", "stomach cramps", "dehydration"],
        "possible_causes": ["Acute bacterial or viral gastroenteritis", "Food poisoning", "Amoebiasis", "Side effect of antibiotics"],
        "severity": "Moderate to Severe",
        "severity_level": "moderate",
        "suggested_specialist": "General Physician / Gastroenterologist",
        "home_care": ["Sip Oral Rehydration Salt (ORS) solution continuously after every loose stool", "Eat bland BRAT diet (Bananas, Rice, Applesauce, Toast)", "Take probiotics to restore gut flora", "Avoid dairy, caffeine, and fatty foods"],
        "red_flags": ["Inability to retain any liquids for over 12 hours", "Extreme dry mouth, sunken eyes, zero urine output for >8 hours", "High fever with bloody stools (Dysentery)"]
    }
]

# 10. Diseases Dataset (diseases.json)
diseases_data = [
    {
        "disease_id": "DIS-001",
        "disease_name": "Dengue Fever",
        "category": "Vector-Borne Viral Infection",
        "symptoms": ["High fever", "Severe headache", "Retro-orbital pain", "Joint & muscle pain", "Low platelet count", "Skin petechiae"],
        "causes": ["Bite of infected Aedes aegypti mosquito carrying Dengue virus"],
        "prevention": ["Prevent mosquito breeding in stagnant water", "Use mosquito repellent creams & nets", "Wear long-sleeved clothing"],
        "specialist": "Internal Medicine / Infectious Disease Specialist",
        "recommended_tests": ["Dengue NS1 Antigen", "Dengue IgM/IgG Antibody", "Complete Blood Count (Platelets & Hematocrit)"],
        "home_care": "Adequate hydration with ORS, coconut water, kiwi fruit, papaya leaf extract, paracetamol for fever. Avoid Aspirin and NSAIDs."
    },
    {
        "disease_id": "DIS-002",
        "disease_name": "Type 2 Diabetes Mellitus",
        "category": "Endocrine & Metabolic Disorder",
        "symptoms": ["Increased thirst (polydipsia)", "Frequent urination (polyuria)", "Unexplained weight loss", "Fatigue", "Blurred vision", "Slow wound healing"],
        "causes": ["Insulin resistance", "Genetic predisposition", "Sedentary lifestyle and obesity"],
        "prevention": ["Maintain healthy BMI (<23 for South Asians)", "Low glycemic index, fiber-rich diet", "30-45 minutes daily aerobic exercise"],
        "specialist": "Endocrinologist / Diabetologist",
        "recommended_tests": ["Fasting Blood Sugar (FBS)", "Postprandial Blood Sugar (PPBS)", "HbA1c Glycated Hemoglobin", "Lipid Profile", "Serum Creatinine"],
        "home_care": "Regular daily blood glucose tracking, portion-controlled meals, foot care inspection, regular medication compliance."
    },
    {
        "disease_id": "DIS-003",
        "disease_name": "Essential Hypertension",
        "category": "Cardiovascular Disease",
        "symptoms": ["Occipital morning headache", "Dizziness", "Shortness of breath on exertion", "Nosebleeds (epistaxis)", "Palpitations", "Often asymptomatic ('Silent Killer')"],
        "causes": ["Arterial stiffness", "High dietary sodium intake", "Chronic stress", "Renal artery vasoconstriction", "Family history"],
        "prevention": ["DASH diet (low sodium <2g/day, high potassium)", "Weight management", "Stress reduction and yoga", "Smoking cessation"],
        "specialist": "Cardiologist / General Physician",
        "recommended_tests": ["24-Hour Ambulatory BP Monitoring", "Electrocardiogram (ECG)", "Echocardiogram", "Lipid Profile", "Kidney Function Test"],
        "home_care": "Log morning and evening BP in app Vitals Tracker, restrict table salt, avoid NSAID pain relievers."
    },
    {
        "disease_id": "DIS-004",
        "disease_name": "Gastroesophageal Reflux Disease (GERD)",
        "category": "Gastrointestinal Disorder",
        "symptoms": ["Retrosternal heartburn", "Acid regurgitation into throat", "Sour taste in mouth", "Chronic dry cough", "Dysphagia", "Bloating"],
        "causes": ["Lower esophageal sphincter (LES) relaxation", "Hiatal hernia", "Obesity", "Late-night heavy meals", "Smoking & alcohol"],
        "prevention": ["Eat smaller, frequent meals", "Do not lie down within 2-3 hours of dinner", "Elevate head of bed by 6 inches"],
        "specialist": "Gastroenterologist",
        "recommended_tests": ["Upper GI Endoscopy", "24-hour Esophageal pH Impedance Study"],
        "home_care": "Take PPIs 30 mins before breakfast, drink cold skim milk, avoid citrus, mint, chocolate, and carbonated beverages."
    },
    {
        "disease_id": "DIS-005",
        "disease_name": "Bronchial Asthma",
        "category": "Respiratory Disease",
        "symptoms": ["Expiratory wheezing", "Shortness of breath", "Chest tightness", "Nocturnal dry cough", "Difficulty speaking full sentences"],
        "causes": ["Chronic airway inflammation and bronchial hyperresponsiveness triggered by allergens, cold air, dust, pollen, viral infections"],
        "prevention": ["Identify and avoid allergen triggers", "Use HEPA air purifiers at home", "Cover mouth and nose in cold dry weather"],
        "specialist": "Pulmonologist / Allergist",
        "recommended_tests": ["Spirometry / Pulmonary Function Test (PFT)", "Peak Expiratory Flow Rate (PEFR)", "Serum Total IgE", "Chest X-Ray"],
        "home_care": "Keep rescue inhaler (Salbutamol) always accessible, rinse mouth after steroid inhalers, monitor daily peak flow."
    }
]

# 11. Drug Interaction Dataset (drug_interactions.json)
drug_interactions_data = [
    {
        "interaction_id": "INT-001",
        "medicine_1": "Warfarin",
        "medicine_2": "Aspirin",
        "severity": "High / Severe",
        "description": "Concurrent use significantly increases risk of severe internal gastrointestinal bleeding and hemorrhaging due to combined anticoagulant and antiplatelet actions.",
        "recommendation": "Avoid combination unless closely monitored with regular INR tests and gastric mucosal protection."
    },
    {
        "interaction_id": "INT-002",
        "medicine_1": "Amoxicillin",
        "medicine_2": "Methotrexate",
        "severity": "Moderate to High",
        "description": "Amoxicillin decreases renal clearance of methotrexate, potentially increasing methotrexate serum levels and systemic bone marrow toxicity.",
        "recommendation": "Monitor complete blood counts and liver enzymes closely."
    },
    {
        "interaction_id": "INT-003",
        "medicine_1": "Ibuprofen",
        "medicine_2": "Aspirin",
        "severity": "Moderate to High",
        "description": "Ibuprofen interferes with the antiplatelet cardio-protective effect of low-dose aspirin and increases risk of stomach ulceration.",
        "recommendation": "Take aspirin at least 30 minutes before or 8 hours after ibuprofen."
    },
    {
        "interaction_id": "INT-004",
        "medicine_1": "Omeprazole",
        "medicine_2": "Clopidogrel",
        "severity": "Moderate",
        "description": "Omeprazole inhibits CYP2C19 enzyme, reducing conversion of clopidogrel to its active antiplatelet metabolite, potentially lowering cardioprotective efficacy.",
        "recommendation": "Consider pantoprazole or H2 blockers as alternatives if gastroprotection is needed."
    },
    {
        "interaction_id": "INT-005",
        "medicine_1": "Metformin",
        "medicine_2": "Ciprofloxacin",
        "severity": "Moderate",
        "description": "Fluoroquinolones may alter blood glucose regulation when taken with metformin, causing severe hypoglycemia or hyperglycemia.",
        "recommendation": "Perform frequent blood glucose monitoring during antibiotic therapy."
    },
    {
        "interaction_id": "INT-006",
        "medicine_1": "Paracetamol",
        "medicine_2": "Isoniazid",
        "severity": "Moderate",
        "description": "Concurrent use may increase the risk of hepatotoxicity (liver damage).",
        "recommendation": "Limit paracetamol dosage to maximum 2g/day and monitor liver function tests."
    },
    {
        "interaction_id": "INT-007",
        "medicine_1": "Atorvastatin",
        "medicine_2": "Clarithromycin",
        "severity": "High / Severe",
        "description": "Clarithromycin strongly inhibits CYP3A4 metabolism of atorvastatin, dramatically increasing statin levels and risking rhabdomyolysis / muscle breakdown.",
        "recommendation": "Temporarily suspend atorvastatin during the course of clarithromycin or use azithromycin."
    },
    {
        "interaction_id": "INT-008",
        "medicine_1": "Telmisartan",
        "medicine_2": "Spironolactone",
        "severity": "Moderate to High",
        "description": "Combining ARBs with potassium-sparing diuretics increases risk of hyperkalemia (dangerously high blood potassium).",
        "recommendation": "Monitor serum potassium and renal function within 1-2 weeks of initiation."
    },
    {
        "interaction_id": "INT-009",
        "medicine_1": "Sildenafil",
        "medicine_2": "Nitroglycerin",
        "severity": "High / Severe",
        "description": "Combining PDE5 inhibitors with nitrates produces profound, potentially life-threatening systemic vasodilation and severe hypotension.",
        "recommendation": "Absolute contraindication. Never take sildenafil or tadalafil within 24-48 hours of nitrate medications."
    },
    {
        "interaction_id": "INT-010",
        "medicine_1": "Levothyroxine",
        "medicine_2": "Calcium Carbonate",
        "severity": "Moderate",
        "description": "Calcium supplements chelate with levothyroxine in the gastrointestinal tract, significantly reducing thyroid hormone absorption.",
        "recommendation": "Separate administration by at least 4 hours."
    },
    {
        "interaction_id": "INT-011",
        "medicine_1": "Fluoxetine",
        "medicine_2": "Tramadol",
        "severity": "High / Severe",
        "description": "Combining SSRIs with tramadol markedly increases risk of Serotonin Syndrome (hyperthermia, agitation, muscle rigidity) and lowers seizure threshold.",
        "recommendation": "Avoid concurrent use or use non-serotonergic analgesics."
    },
    {
        "interaction_id": "INT-012",
        "medicine_1": "Enalapril",
        "medicine_2": "Potassium Chloride",
        "severity": "Moderate to High",
        "description": "ACE inhibitors reduce aldosterone secretion, causing potassium retention. Adding potassium supplements can trigger dangerous hyperkalemia and arrhythmias.",
        "recommendation": "Avoid routine potassium supplementation unless prescribed and monitored by a cardiologist."
    }
]

# 12. Generic Alternatives Dataset (generic_alternatives.json)
generic_alternatives_data = [
    {
        "medicine_id": "MED-001",
        "brand_name": "Dolo 650",
        "generic_name": "Paracetamol 650mg",
        "alternative_brands": ["Calpol 650", "Crocin 650", "Pacimol 650", "Febrinil 650"]
    },
    {
        "medicine_id": "MED-003",
        "brand_name": "Augmentin 625 Duo",
        "generic_name": "Amoxicillin 500mg + Clavulanic Acid 125mg",
        "alternative_brands": ["Moxikind-CV 625", "Clavam 625", "Megaclav 625", "Advent 625"]
    }
]

# 13. Barcode Dataset (medicine_barcodes.json)
medicine_barcodes_data = [
    {
        "barcode": "8901234567890",
        "medicine_id": "MED-001",
        "brand_name": "Dolo 650"
    },
    {
        "barcode": "8902345678901",
        "medicine_id": "MED-002",
        "brand_name": "Limcee 500"
    },
    {
        "barcode": "8903456789012",
        "medicine_id": "MED-003",
        "brand_name": "Augmentin 625 Duo"
    }
]

# 14. Medicine Images Dataset (medicine_images.json)
medicine_images_data = [
    {
        "image_id": "IMG-001",
        "medicine_id": "MED-001",
        "front_image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=600",
        "back_image": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&q=80&w=600"
    },
    {
        "image_id": "IMG-002",
        "medicine_id": "MED-002",
        "front_image": "https://images.unsplash.com/photo-1577401239170-897942555fb3?auto=format&fit=crop&q=80&w=600",
        "back_image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=600"
    }
]

# 15. First Aid Dataset (first_aid.json)
first_aid_data = [
    {
        "emergency_id": "EMG-001",
        "emergency_type": "Severe Bleeding & Cuts",
        "symptoms": ["Continuous dark or bright red blood flow", "Dizziness", "Pale skin"],
        "first_aid_steps": [
            "Apply direct, constant pressure over the wound using a clean cloth or sterile bandage.",
            "Elevate the injured limb above heart level if no bone fracture is suspected.",
            "Do not remove embedded sharp objects; apply padding around them.",
            "Call emergency services (108) if bleeding persists after 10 minutes of direct pressure."
        ],
        "emergency_number": "108"
    },
    {
        "emergency_id": "EMG-002",
        "emergency_type": "Thermal Burns & Scalds",
        "symptoms": ["Red skin", "Blisters", "Severe localized pain"],
        "first_aid_steps": [
            "Hold the burned area under cool running tap water for at least 15-20 minutes.",
            "Do not apply ice, butter, toothpastes, or oil ointment on fresh burns.",
            "Cover loosely with a clean, non-stick sterile gauze bandage.",
            "Seek immediate emergency medical care for electrical, chemical, or face/joint burns."
        ],
        "emergency_number": "108"
    }
]

# 16. Health Tips Dataset (health_tips.json)
health_tips_data = [
    {
        "tip_id": "TIP-001",
        "category": "Hydration",
        "title": "Daily Hydration Goals",
        "description": "Drink at least 2.5 to 3 liters of water daily to support kidney function, skin health, and cognitive concentration."
    },
    {
        "tip_id": "TIP-002",
        "category": "Sleep Hygiene",
        "title": "Optimize Circadian Sleep",
        "description": "Maintain a consistent sleep schedule and turn off blue-light screens 45 minutes before bedtime for restorative REM sleep."
    }
]

# 17. Reviews Dataset (reviews.json)
reviews_data = [
    {
        "review_id": "REV-001",
        "medicine_id": "MED-001",
        "user_name": "Rahul Sharma",
        "rating": 5.0,
        "review": "Very effective for fever reduction. Delivered within 20 mins from MedPlus Express!",
        "review_date": "2026-08-01"
    },
    {
        "review_id": "REV-002",
        "medicine_id": "MED-002",
        "user_name": "Priya Patel",
        "rating": 4.8,
        "review": "Great chewable Vitamin C taste. Helps keep immunity strong during seasonal changes.",
        "review_date": "2026-08-03"
    }
]

# 18. FAQ Dataset (faq.json)
faq_data = [
    {
        "faq_id": "FAQ-001",
        "question": "How does the AI Medicine & Prescription Scanner work?",
        "answer": "Our scanner utilizes OCR text extraction and computer vision algorithms to instantly analyze medicine names, dosage forms, side effects, and active compositions from any uploaded picture or scan."
    },
    {
        "faq_id": "FAQ-002",
        "question": "Are emergency blood requests sent to nearby donors automatically?",
        "answer": "Yes! Tapping 'Submit Blood Request' matches your requested blood group with registered local donors and emergency blood bank inventories within a 10 km radius."
    }
]

# 19. Ambulance Services Dataset (ambulance_services.json)
ambulance_services_data = [
    {
        "ambulance_id": "AMB-001",
        "service_name": "108 National Emergency Ambulance Response",
        "phone": "108",
        "address": "Government Emergency Dispatch Center",
        "latitude": 17.4300,
        "longitude": 78.4000
    },
    {
        "ambulance_id": "AMB-002",
        "service_name": "Apollo 1066 Critical Care ALS Ambulance",
        "phone": "1066",
        "address": "Apollo Hospitals Jubilee Hills Dispatch Unit",
        "latitude": 17.4184,
        "longitude": 78.4116
    }
]

# 20. Offers Dataset (offers.json)
offers_data = [
    {
        "offer_id": "OFFER-001",
        "title": "Flat 20% OFF Everything",
        "description": "Get flat 20% discount on all prescription medicines and healthcare products across partner pharmacies.",
        "discount": 20.0,
        "valid_until": "2026-08-31",
        "applicable_products": ["MED-001", "MED-002", "MED-003", "MED-004", "MED-005"]
    },
    {
        "offer_id": "OFFER-002",
        "title": "First-Order 25% Savings",
        "description": "Use promo code CURA25 on your first medicine order above ₹200.",
        "discount": 25.0,
        "valid_until": "2026-09-15",
        "applicable_products": ["MED-001", "MED-002"]
    }
]

# 21. Lab Biomarkers Reference Dataset (lab_biomarkers.json)
lab_biomarkers_data = [
    {
        "biomarker_id": "BIO-001",
        "name": "Hemoglobin (Hb)",
        "category": "Complete Blood Count (CBC)",
        "unit": "g/dL",
        "normal_range_min": 13.0,
        "normal_range_max": 17.5,
        "description": "Oxygen-carrying protein in red blood cells.",
        "low_implication": "Microcytic / normocytic anemia, fatigue, weakness, iron deficiency, or blood loss.",
        "high_implication": "Polycythemia, severe dehydration, COPD, or high altitude adaptation.",
        "diet_advice": "For low Hb: Consume iron-rich foods like spinach, lentils, beetroot, pomegranate, eggs, and Vitamin C for absorption."
    },
    {
        "biomarker_id": "BIO-002",
        "name": "Total White Blood Cells (WBC / TLC)",
        "category": "Complete Blood Count (CBC)",
        "unit": "/µL",
        "normal_range_min": 4000,
        "normal_range_max": 11000,
        "description": "Immune defense cells fighting infections and inflammation.",
        "low_implication": "Leukopenia, viral infections (Dengue), bone marrow suppression, or autoimmune conditions.",
        "high_implication": "Leukocytosis, acute bacterial infection, systemic inflammation, severe tissue damage, or leukemia.",
        "diet_advice": "Eat zinc-rich foods, citrus fruits, yogurt with probiotics, and stay well hydrated."
    },
    {
        "biomarker_id": "BIO-003",
        "name": "Platelet Count",
        "category": "Complete Blood Count (CBC)",
        "unit": "x10^3/µL",
        "normal_range_min": 150,
        "normal_range_max": 450,
        "description": "Cell fragments essential for normal blood clotting.",
        "low_implication": "Thrombocytopenia, Dengue infection, ITP, risk of petechiae/bruising and spontaneous bleeding.",
        "high_implication": "Thrombocytosis, reactive inflammation, iron deficiency, or myeloproliferative disorder.",
        "diet_advice": "For low platelets: Papaya leaf extract, kiwi fruit, pomegranate, pumpkin seeds, and leafy greens."
    },
    {
        "biomarker_id": "BIO-004",
        "name": "Fasting Blood Sugar (FBS)",
        "category": "Diabetes / Glucose Profile",
        "unit": "mg/dL",
        "normal_range_min": 70,
        "normal_range_max": 100,
        "description": "Blood glucose level measured after minimum 8 hours of overnight fasting.",
        "low_implication": "Hypoglycemia (<70 mg/dL): dizziness, sweating, tremors, hunger, risk of fainting.",
        "high_implication": "Impaired Fasting Glucose / Pre-diabetes (100-125 mg/dL), Diabetes Mellitus (>=126 mg/dL).",
        "diet_advice": "High fiber diet, whole grains, avoid refined sugars, sweet beverages, and practice intermittent fasting or 30 min daily brisk walking."
    },
    {
        "biomarker_id": "BIO-005",
        "name": "Glycated Hemoglobin (HbA1c)",
        "category": "Diabetes / Glucose Profile",
        "unit": "%",
        "normal_range_min": 4.0,
        "normal_range_max": 5.6,
        "description": "Average blood sugar control over the past 90-120 days.",
        "low_implication": "Hemolytic anemia or frequent hypoglycemic episodes.",
        "high_implication": "Pre-diabetes (5.7 - 6.4%), Diabetes Mellitus (>= 6.5%). High risk of diabetic microvascular complications.",
        "diet_advice": "Low glycemic index foods (millets, oats, legumes), portion control, eliminate added sugars, monitor quarterly."
    },
    {
        "biomarker_id": "BIO-006",
        "name": "Total Cholesterol",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "normal_range_min": 125,
        "normal_range_max": 200,
        "description": "Total amount of cholesterol circulating in bloodstream.",
        "low_implication": "Severe malnutrition, malabsorption, or hyperthyroidism.",
        "high_implication": "Hypercholesterolemia (>200 mg/dL): Atherosclerosis, coronary artery disease, and stroke risk.",
        "diet_advice": "Reduce saturated and trans-fats, incorporate olive oil, walnuts, almonds, flaxseeds, and soluble fiber (psyllium husk, oats)."
    },
    {
        "biomarker_id": "BIO-007",
        "name": "LDL Bad Cholesterol",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "normal_range_min": 50,
        "normal_range_max": 100,
        "description": "Low-Density Lipoprotein that deposits plaque in arterial walls.",
        "low_implication": "Hypobetalipoproteinemia or extreme statin response.",
        "high_implication": "Atherogenic plaque buildup in arteries. Optimal: <100 mg/dL (or <70 mg/dL for cardiac patients).",
        "diet_advice": "Strictly eliminate fried fast foods, butter, palm oil; consume garlic, green tea, and plant sterols."
    },
    {
        "biomarker_id": "BIO-008",
        "name": "HDL Good Cholesterol",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "normal_range_min": 40,
        "normal_range_max": 80,
        "description": "High-Density Lipoprotein that scavenges excess cholesterol back to liver.",
        "low_implication": "Increased risk of coronary heart disease (<40 mg/dL in men, <50 mg/dL in women).",
        "high_implication": "Cardio-protective (>60 mg/dL).",
        "diet_advice": "Regular aerobic cardio exercise, omega-3 fatty acids (fatty fish, chia seeds, walnuts), quit smoking."
    },
    {
        "biomarker_id": "BIO-009",
        "name": "Serum Creatinine",
        "category": "Kidney Function Test (KFT)",
        "unit": "mg/dL",
        "normal_range_min": 0.6,
        "normal_range_max": 1.2,
        "description": "Waste byproduct of muscle metabolism filtered by kidneys.",
        "low_implication": "Low muscle mass, severe liver disease, or malnutrition.",
        "high_implication": "Impaired renal glomerular filtration, acute kidney injury (AKI), chronic kidney disease (CKD), or severe dehydration.",
        "diet_advice": "Adequate daily hydration (2.5-3L water), moderate protein intake, limit sodium, avoid NSAID painkillers."
    },
    {
        "biomarker_id": "BIO-010",
        "name": "Serum Bilirubin (Total)",
        "category": "Liver Function Test (LFT)",
        "unit": "mg/dL",
        "normal_range_min": 0.2,
        "normal_range_max": 1.2,
        "description": "Yellow pigment produced during breakdown of red blood cells.",
        "low_implication": "Generally no clinical significance.",
        "high_implication": "Jaundice, viral hepatitis, bile duct obstruction (gallstones), hemolytic anemia, or Gilbert's syndrome.",
        "diet_advice": "Bland, easily digestible diet (khichdi, boiled vegetables), cane sugar juice, avoid alcohol and oily foods."
    },
    {
        "biomarker_id": "BIO-011",
        "name": "SGPT / ALT (Alanine Aminotransferase)",
        "category": "Liver Function Test (LFT)",
        "unit": "U/L",
        "normal_range_min": 7,
        "normal_range_max": 56,
        "description": "Enzyme primarily found inside liver hepatocytes.",
        "low_implication": "Normal clinical finding.",
        "high_implication": "Hepatocellular injury, Non-Alcoholic Fatty Liver Disease (NAFLD), viral hepatitis, alcohol toxicity, or drug-induced liver injury.",
        "diet_advice": "Eliminate alcohol completely, reduce refined fructose and sugars, drink black coffee (liver-protective), lose excess visceral fat."
    },
    {
        "biomarker_id": "BIO-012",
        "name": "Thyroid Stimulating Hormone (TSH)",
        "category": "Thyroid Profile",
        "unit": "mIU/L",
        "normal_range_min": 0.4,
        "normal_range_max": 4.5,
        "description": "Pituitary hormone regulating thyroid gland secretion of T3 and T4.",
        "low_implication": "Hyperthyroidism: weight loss, rapid heartbeat, heat intolerance, anxiety, tremors.",
        "high_implication": "Hypothyroidism (>4.5 mIU/L): weight gain, fatigue, dry skin, cold intolerance, constipation, hair loss.",
        "diet_advice": "For high TSH: Take prescribed Levothyroxine on empty stomach with water, avoid soy and cruciferous raw vegetables in excess, ensure adequate iodine and selenium."
    }
]

# Save all datasets
datasets = {
    "medicines.json": medicines_data,
    "medicine_categories.json": categories_data,
    "pharmacies.json": pharmacies_data,
    "hospitals.json": hospitals_data,
    "laboratories.json": laboratories_data,
    "bloodbanks.json": bloodbanks_data,
    "doctors.json": doctors_data,
    "clinics.json": clinics_data,
    "symptoms.json": symptoms_data,
    "diseases.json": diseases_data,
    "drug_interactions.json": drug_interactions_data,
    "generic_alternatives.json": generic_alternatives_data,
    "medicine_barcodes.json": medicine_barcodes_data,
    "medicine_images.json": medicine_images_data,
    "first_aid.json": first_aid_data,
    "health_tips.json": health_tips_data,
    "reviews.json": reviews_data,
    "faq.json": faq_data,
    "ambulance_services.json": ambulance_services_data,
    "offers.json": offers_data,
    "lab_biomarkers.json": lab_biomarkers_data
}

# Preserve existing rich medicines data if present
med_file = os.path.join(DATA_DIR, "medicines.json")
if os.path.exists(med_file):
    try:
        with open(med_file, "r", encoding="utf-8") as f:
            existing_meds = json.load(f)
            if len(existing_meds) > len(medicines_data):
                datasets["medicines.json"] = existing_meds
    except Exception:
        pass

for filename, content in datasets.items():
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated dataset: {filename} ({len(content)} records)")

print("\nAll 21 Datasets generated successfully in data/ directory!")

