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
)
import app.database.sql_db as sql_db
import app.api.profile as profile_api
import app.api.store as store_api


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
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


def test_order_creation_uses_authenticated_owner(monkeypatch, db_session):
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


def test_appointment_and_vital_writes_set_authenticated_owner(monkeypatch, db_session):
    owner = UserModel(id="owner-a", name="A", email="a@example.com")
    db_session.add(owner)
    db_session.commit()
    monkeypatch.setattr(profile_api, "get_db_session", lambda: db_session)

    appointment = profile_api.book_appointment({"patientName": "Attacker"}, owner)
    vital = profile_api.log_vital_reading({"userEmail": "attacker@example.com"}, owner)

    stored_appointment = db_session.query(AppointmentModel).filter_by(id=appointment["appointment"]["id"]).one()
    stored_vital = db_session.query(VitalRecordModel).filter_by(id=vital["vital"]["id"]).one()

    assert stored_appointment.owner_user_id == "owner-a"
    assert stored_vital.owner_user_id == "owner-a"
    assert stored_appointment.user_email == "a@example.com"
    assert stored_vital.user_email == "a@example.com"
