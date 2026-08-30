"""
Universal SQL Database Engine - CuraAssist CareHub
Supports SQLite for local/test use and PostgreSQL / Supabase / Neon for deployed environments.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import sqlalchemy
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    select
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SQLITE_DB_PATH = DATA_DIR / "curaassist.db"

EXPLICIT_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
DATABASE_URL = EXPLICIT_DATABASE_URL or f"sqlite:///{SQLITE_DB_PATH}"

# Fix postgres:// -> postgresql:// for SQLAlchemy 2.0+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()

# --- SQLALCHEMY ORM MODELS ---

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, default="+91 98765 43210")
    location = Column(String, default="Hyderabad, Telangana")
    age = Column(Integer, default=34)
    gender = Column(String, default="Male")
    blood_group = Column(String, default="O+")
    role = Column(String, default="Patient")
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class HealthRecordModel(Base):
    __tablename__ = "health_records"
    id = Column(String, primary_key=True, index=True)
    owner_user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    member_id = Column(String, index=True, default="fam1")
    user_email = Column(String, index=True, default="rahul.sharma@email.com")
    title = Column(String, nullable=False)
    category = Column(String, index=True, default="Medical Reports")
    date = Column(String, default=lambda: datetime.date.today().isoformat())
    doctor = Column(String, default="Self Upload / Clinic")
    facility = Column(String, default="CuraAssist Digital Hub")
    summary = Column(Text, default="")
    tags = Column(String, default="Uploaded, Health Record")
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AppointmentModel(Base):
    __tablename__ = "appointments"
    id = Column(String, primary_key=True, index=True)
    owner_user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    user_email = Column(String, index=True, default="rahul.sharma@email.com")
    doctor_id = Column(String, index=True)
    doctor_name = Column(String, nullable=False)
    specialty = Column(String, default="General Physician")
    patient_name = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    status = Column(String, default="Confirmed")
    consultation_type = Column(String, default="In-Person")
    hospital_name = Column(String, default="Apollo Hospitals")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    owner_user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    user_email = Column(String, index=True, default="rahul.sharma@email.com")
    patient_name = Column(String, default="Rahul Sharma")
    items_json = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    delivery_address = Column(Text, nullable=False)
    payment_method = Column(String, default="UPI / Card")
    status = Column(String, default="Processing")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VitalRecordModel(Base):
    __tablename__ = "vitals"
    id = Column(String, primary_key=True, index=True)
    owner_user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    user_email = Column(String, index=True, default="rahul.sharma@email.com")
    systolic = Column(Integer, default=120)
    diastolic = Column(Integer, default=80)
    pulse = Column(Integer, default=72)
    temperature = Column(Float, default=98.6)
    glucose = Column(Float, default=95.0)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)


class MedicineScheduleModel(Base):
    __tablename__ = "schedules"
    id = Column(String, primary_key=True, index=True)
    owner_user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    user_email = Column(String, index=True, default="user@curaassist.health")
    name = Column(String, nullable=False)
    dosage = Column(String, default="1 Tablet")
    frequency = Column(String, default="Daily")
    time = Column(String, default="08:00 AM")
    meal_instruction = Column(String, default="After Meals")
    category = Column(String, default="General")
    next_dose = Column(String, default="Today, 08:00 AM")
    refills_left = Column(Integer, default=30)
    total_pills = Column(Integer, default=30)
    taken = Column(Boolean, default=False)
    last_taken_at = Column(DateTime, nullable=True)
    snooze_until = Column(String, nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)



class MedicineModel(Base):
    __tablename__ = "medicines"
    medicine_id = Column(String, primary_key=True, index=True)
    brand_name = Column(String, index=True)
    generic_name = Column(String, index=True)
    composition = Column(String)
    category = Column(String, index=True)
    price = Column(Float)
    original_price = Column(Float)
    dosage = Column(String)
    prescription_required = Column(Boolean, default=False)
    rating = Column(Float, default=4.8)
    image_url = Column(String, default="")


class FacilityModel(Base):
    __tablename__ = "facilities"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, index=True)
    address = Column(String)
    phone = Column(String)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    rating = Column(Float, default=4.8)
    open_hours = Column(String, default="Open 24 Hours")
    emergency_available = Column(Boolean, default=True)


# --- DATABASE ENGINE & SESSION FACTORY ---

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        try:
            _engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
        except Exception as e:
            if EXPLICIT_DATABASE_URL:
                raise RuntimeError(
                    "Configured database could not be initialized; refusing SQLite fallback"
                ) from e

            print("[SQL DB] Local database initialization failed; using SQLite:", e)
            _engine = create_engine(
                f"sqlite:///{SQLITE_DB_PATH}",
                connect_args={"check_same_thread": False},
            )
    return _engine


def get_db_session() -> Session:
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionFactory()


def init_db():
    """Initializes tables and seeds reference/demo dataset only in explicit demo mode."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # Ensure missing columns in existing SQLite tables are safely added
    if str(engine.url).startswith("sqlite"):
        try:
            with engine.connect() as conn:
                for table_name, col_name, col_type in [
                    ("users", "avatar_url", "VARCHAR"),
                    ("health_records", "owner_user_id", "VARCHAR"),
                    ("appointments", "owner_user_id", "VARCHAR"),
                    ("orders", "owner_user_id", "VARCHAR"),
                    ("vitals", "owner_user_id", "VARCHAR"),
                    ("schedules", "owner_user_id", "VARCHAR"),
                    ("schedules", "meal_instruction", "VARCHAR DEFAULT 'After Meals'"),
                    ("schedules", "refills_left", "INTEGER DEFAULT 30"),
                    ("schedules", "total_pills", "INTEGER DEFAULT 30"),
                    ("schedules", "taken", "BOOLEAN DEFAULT 0"),
                    ("schedules", "last_taken_at", "DATETIME"),
                    ("schedules", "snooze_until", "VARCHAR"),
                ]:
                    try:
                        res = conn.execute(sqlalchemy.text(f"PRAGMA table_info({table_name})")).fetchall()
                        existing_cols = [r[1] for r in res]
                        if existing_cols and col_name not in existing_cols:
                            conn.execute(sqlalchemy.text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                    except Exception:
                        pass
        except Exception:
            pass

    seed_initial_sql_data()


def seed_initial_sql_data():
    """Seeds reference/demo dataset entries into SQL only when demo mode is explicit."""
    session = get_db_session()
    try:
        allow_demo_seed = os.getenv("CURAASSIST_DEMO_MODE", "false").strip().lower() == "true"

        # 1. Seed Default User and synthetic patient data only in explicit demo mode.
        if allow_demo_seed:
            existing_user = session.query(UserModel).filter_by(email="rahul.sharma@email.com").first()
            if not existing_user:
                user = UserModel(
                    id="usr-default-01",
                    name="Rahul Sharma",
                    email="rahul.sharma@email.com",
                    phone="+91 98765 43210",
                    location="Hyderabad, Telangana",
                    age=34,
                    gender="Male",
                    blood_group="O+",
                    role="Patient"
                )
                session.add(user)

        # 2. Seed Medicines (reference data remains safe; no ownership required).
        med_count = session.query(MedicineModel).count()
        if med_count == 0:
            med_json_path = DATA_DIR / "medicines.json"
            if med_json_path.exists():
                with open(med_json_path, "r", encoding="utf-8") as f:
                    meds = json.load(f)
                    for m in meds:
                        med_obj = MedicineModel(
                            medicine_id=m.get("medicine_id", f"MED-{len(meds)}"),
                            brand_name=m.get("brand_name", m.get("name", "")),
                            generic_name=m.get("generic_name", ""),
                            composition=m.get("composition", ""),
                            category=m.get("category", "General"),
                            price=float(m.get("price", 50.0)),
                            original_price=float(m.get("original_price", 60.0)),
                            dosage=m.get("dosage", "1 tablet post meals"),
                            prescription_required=bool(m.get("prescription_required", False)),
                            rating=float(m.get("rating", 4.8)),
                            image_url=m.get("image_url", "")
                        )
                        session.merge(med_obj)

        # 3. Seed Health Records only in explicit demo mode with ownership set.
        if allow_demo_seed:
            rec_count = session.query(HealthRecordModel).count()
            if rec_count == 0:
                rec_json_path = DATA_DIR / "health_records.json"
                if rec_json_path.exists():
                    with open(rec_json_path, "r", encoding="utf-8") as f:
                        recs = json.load(f)
                        for r in recs:
                            rec_obj = HealthRecordModel(
                                id=r.get("id", f"rec-{r.get('title', '001')}"),
                                owner_user_id="usr-default-01",
                                member_id=r.get("memberId", "fam1"),
                                user_email="rahul.sharma@email.com",
                                title=r.get("title", "Medical Report"),
                                category=r.get("category", "Reports"),
                                date=r.get("date", "2026-08-01"),
                                doctor=r.get("doctor", "Clinic Specialist"),
                                facility=r.get("facility", "CareHub Center"),
                                summary=r.get("summary", ""),
                                tags=",".join(r.get("tags", ["Health", "Record"])) if isinstance(r.get("tags"), list) else str(r.get("tags", ""))
                            )
                            session.merge(rec_obj)

        # 4. Seed Facilities from hospitals, pharmacies, clinics, laboratories.
        fac_count = session.query(FacilityModel).count()
        if fac_count == 0:
            facility_files = [
                ("hospitals.json", "Hospitals", "hospital_id", "hospital_name"),
                ("pharmacies.json", "Pharmacies", "pharmacy_id", "pharmacy_name"),
                ("clinics.json", "Clinics", "clinic_id", "clinic_name"),
                ("laboratories.json", "Labs", "lab_id", "lab_name"),
                ("bloodbanks.json", "Emergency", "bloodbank_id", "bloodbank_name"),
            ]
            for fname, ftype, id_key, name_key in facility_files:
                fpath = DATA_DIR / fname
                if fpath.exists():
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            items = json.load(f)
                            for it in items:
                                fac_obj = FacilityModel(
                                    id=str(it.get(id_key, f"fac-{ftype}-{it.get(name_key, '01')}")),
                                    name=str(it.get(name_key, it.get("name", "Healthcare Center"))),
                                    type=ftype,
                                    address=str(it.get("address", it.get("city", "Local Medical Center"))),
                                    phone=str(it.get("phone", "+91 40 2360 7777")),
                                    lat=float(it.get("latitude", it.get("lat", 17.4184))),
                                    lng=float(it.get("longitude", it.get("lng", 78.4116))),
                                    rating=float(it.get("rating", 4.8)),
                                    open_hours=str(it.get("opening_hours", "Open 24 Hours")),
                                    emergency_available=bool(it.get("emergency_available", True))
                                )
                                session.merge(fac_obj)
                    except Exception as fe:
                        print(f"[SQL DB] Note loading {fname}:", fe)

        session.commit()
        print("[SQL DB] Initialization and seed complete successfully.")
    except Exception as e:
        session.rollback()
        print("[SQL DB] Seed error:", e)
    finally:
        session.close()
