import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import get_current_user
from app.database.sql_db import (
    AppointmentModel,
    Base,
    HealthRecordModel,
    OrderModel,
    UserModel,
    VitalRecordModel,
    MedicineScheduleModel,
)
import app.database.sql_db as sql_db
import app.api.profile as profile_api
import app.api.store as store_api


def test_medicine_schedule_reads_and_writes_are_scoped_to_authenticated_owner(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add_all([
        MedicineScheduleModel(id="sch-a", owner_user_id="owner-a", user_email="a@example.com", name="Amoxicillin"),
        MedicineScheduleModel(id="sch-b", owner_user_id="owner-b", user_email="b@example.com", name="Metformin"),
    ])
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    res_a = profile_api.get_medicine_schedules(owner_a)
    assert res_a["count"] == 1
    assert res_a["schedules"][0]["id"] == "sch-a"

    res_write = profile_api.add_medicine_schedule({"name": "Paracetamol", "dosage": "500mg"}, owner_a)
    stored = db_session.query(MedicineScheduleModel).filter_by(id=res_write["schedule"]["id"]).one()
    assert stored.owner_user_id == "owner-a"

    # User B cannot delete User A's schedule
    with pytest.raises(Exception):
        profile_api.delete_medicine_schedule("sch-a", owner_b)


def test_health_record_deletion_enforces_ownership(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add(HealthRecordModel(id="rec-a", owner_user_id="owner-a", title="A Report"))
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    # User B deletion attempt must fail
    with pytest.raises(Exception):
        profile_api.delete_health_record("rec-a", owner_b)

    # User A deletion succeeds
    del_res = profile_api.delete_health_record("rec-a", owner_a)
    assert del_res["status"] == "success"
    assert db_session.query(HealthRecordModel).filter_by(id="rec-a").first() is None



@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)()
    real_close = session.close
    session.close = lambda: None
    try:
        yield session
    finally:
        session.close = real_close
        session.close()
        engine.dispose()


def test_verified_supabase_identity_resolves_existing_user(monkeypatch, db_session):
    existing = UserModel(id="usr-internal", name="Existing User", email="user@example.com")
    db_session.add(existing)
    db_session.commit()

    monkeypatch.setattr(sql_db, "get_db_session", lambda: db_session)

    user = get_current_user({"sub": "supabase-user-id", "email": "user@example.com"})

    assert user.id == "usr-internal"
    assert user.email == "user@example.com"


def test_verified_supabase_identity_creates_missing_user(monkeypatch, db_session):
    monkeypatch.setattr(sql_db, "get_db_session", lambda: db_session)

    user = get_current_user({"sub": "supabase-new-user", "email": "new@example.com"})

    assert user.id == "supabase-new-user"
    assert user.email == "new@example.com"
    assert db_session.query(UserModel).filter_by(id="supabase-new-user").one()


def test_health_records_are_scoped_to_authenticated_owner(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add_all([
        HealthRecordModel(id="rec-a", owner_user_id="owner-a", title="A record"),
        HealthRecordModel(id="rec-b", owner_user_id="owner-b", title="B record"),
    ])
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    response = profile_api.get_health_records(owner_a)

    assert response["count"] == 1
    assert response["records"][0]["id"] == "rec-a"


def test_order_creation_uses_authenticated_owner_and_ignores_client_user_id(monkeypatch, db_session):
    owner = UserModel(id="owner-a", name="A", email="a@example.com")
    db_session.add(owner)
    db_session.commit()
    monkeypatch.setattr(store_api, "get_db_session", lambda: db_session)

    request = store_api.OrderRequest(
        userId="attacker@example.com",
        items=[store_api.OrderItem(id="med-1", name="Medicine", price=10.0, quantity=1)],
        totalAmount=10.0,
        address="Test address",
        paymentMethod="UPI",
    )

    response = store_api.place_order(request, owner)
    stored = db_session.query(OrderModel).filter_by(id=response["orderId"]).one()

    assert stored.owner_user_id == "owner-a"
    assert stored.user_email == "a@example.com"


def test_order_reads_are_scoped_to_authenticated_owner(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add_all([
        OrderModel(id="order-a", owner_user_id="owner-a", user_email="a@example.com", items_json="[]", total_amount=10.0, delivery_address="A", payment_method="Test", status="Confirmed"),
        OrderModel(id="order-b", owner_user_id="owner-b", user_email="b@example.com", items_json="[]", total_amount=20.0, delivery_address="B", payment_method="Test", status="Confirmed"),
    ])
    db_session.commit()
    monkeypatch.setattr(store_api, "get_db_session", lambda: db_session)

    response = store_api.get_user_orders(owner_a)

    assert response["count"] == 1
    assert response["orders"][0]["orderId"] == "order-a"


def test_appointment_and_vital_writes_set_authenticated_owner_and_ignore_client_identity(monkeypatch, db_session):
    owner = UserModel(id="owner-a", name="A", email="a@example.com")
    db_session.add(owner)
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    appointment = profile_api.book_appointment({"patientName": "Attacker", "userEmail": "attacker@example.com"}, owner)
    vital = profile_api.log_vital_reading({"userEmail": "attacker@example.com"}, owner)

    stored_appointment = db_session.query(AppointmentModel).filter_by(id=appointment["appointment"]["id"]).one()
    stored_vital = db_session.query(VitalRecordModel).filter_by(id=vital["vital"]["id"]).one()

    assert stored_appointment.owner_user_id == "owner-a"
    assert stored_vital.owner_user_id == "owner-a"
    assert stored_appointment.user_email == "a@example.com"
    assert stored_vital.user_email == "a@example.com"


def test_appointment_reads_are_scoped_to_authenticated_owner(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add_all([
        AppointmentModel(id="appt-a", owner_user_id="owner-a", user_email="a@example.com", doctor_name="Dr. Smith", patient_name="Patient A", appointment_date="2026-08-28", appointment_time="10:00 AM"),
        AppointmentModel(id="appt-b", owner_user_id="owner-b", user_email="b@example.com", doctor_name="Dr. Jones", patient_name="Patient B", appointment_date="2026-08-28", appointment_time="11:00 AM"),
    ])
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    response = profile_api.get_appointments(owner_a)

    assert response["count"] == 1
    assert response["appointments"][0]["id"] == "appt-a"


def test_vital_reads_are_scoped_to_authenticated_owner(monkeypatch, db_session):
    owner_a = UserModel(id="owner-a", name="A", email="a@example.com")
    owner_b = UserModel(id="owner-b", name="B", email="b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.add_all([
        VitalRecordModel(id="vital-a", owner_user_id="owner-a", user_email="a@example.com"),
        VitalRecordModel(id="vital-b", owner_user_id="owner-b", user_email="b@example.com"),
    ])
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    response = profile_api.get_user_vitals(owner_a)

    assert response["count"] == 1
    assert response["vitals"][0]["id"] == "vital-a"
