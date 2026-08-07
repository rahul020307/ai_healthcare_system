import os
import json
from typing import Dict, Any, Optional

try:
    import sqlalchemy
    from sqlalchemy import create_engine, Column, String, Float, Integer, Text, Boolean, DateTime
    from sqlalchemy.orm import declarative_base, sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

POSTGRES_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/curaassist_db"))

_engine = None
_SessionLocal = None
Base = declarative_base() if HAS_SQLALCHEMY else object


# --- SQLALCHEMY ORM MODELS ---
if HAS_SQLALCHEMY:
    class HealthRecordModel(Base):
        __tablename__ = "health_records"
        id = Column(String, primary_key=True, index=True)
        memberId = Column(String, index=True)
        title = Column(String)
        date = Column(String)
        doctor = Column(String)
        facility = Column(String)
        category = Column(String, index=True)
        summary = Column(Text)
        tags = Column(String)

    class MedicineModel(Base):
        __tablename__ = "medicines"
        medicine_id = Column(String, primary_key=True, index=True)
        brand_name = Column(String, index=True)
        generic_name = Column(String, index=True)
        category = Column(String)
        price = Column(Float)
        composition = Column(String)
        dosage = Column(String)
        prescription_required = Column(Boolean, default=False)

    class ReminderModel(Base):
        __tablename__ = "reminders"
        id = Column(String, primary_key=True, index=True)
        memberId = Column(String, index=True)
        medName = Column(String)
        dosage = Column(String)
        timeSlot = Column(String)
        isTaken = Column(Boolean, default=False)


def get_postgres_engine():
    global _engine
    if not HAS_SQLALCHEMY:
        return None
    if _engine is None:
        try:
            # Short timeout to avoid blocking if local postgres server is offline
            _engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3} if "postgresql" in POSTGRES_URL else {})
        except Exception as e:
            print("[PostgreSQL] Engine init error:", e)
            _engine = None
    return _engine


def get_postgres_session():
    global _SessionLocal
    engine = get_postgres_engine()
    if engine is None:
        return None
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        return _SessionLocal()
    except Exception as e:
        print("[PostgreSQL] Session creation error:", e)
        return None


def check_postgresql_connection() -> Dict[str, Any]:
    if not HAS_SQLALCHEMY:
        return {
            "status": "offline",
            "driverInstalled": False,
            "message": "SQLAlchemy/psycopg2 library not installed. Falling back to disk JSON storage."
        }

    engine = get_postgres_engine()
    if not engine:
        return {
            "status": "offline",
            "driverInstalled": True,
            "message": "PostgreSQL engine creation failed."
        }

    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return {
            "status": "online",
            "driverInstalled": True,
            "postgresUri": POSTGRES_URL.split("@")[-1],
            "database": POSTGRES_URL.split("/")[-1]
        }
    except Exception as e:
        return {
            "status": "standalone_fallback",
            "driverInstalled": True,
            "message": f"PostgreSQL server offline at {POSTGRES_URL.split('@')[-1]}. Using disk JSON datasets.",
            "error": str(e)
        }


def init_postgres_tables():
    """Create PostgreSQL tables if server is connected"""
    engine = get_postgres_engine()
    if engine and HAS_SQLALCHEMY:
        try:
            Base.metadata.create_all(bind=engine)
            return True
        except Exception as e:
            print("[PostgreSQL] Table creation note:", e)
    return False
