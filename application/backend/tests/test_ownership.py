import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import profile, store
from app.database.sql_db import (
    Base,
    UserModel,
    HealthRecordModel,
    AppointmentModel,
    OrderModel,
    VitalRecordModel,
)


@pytest.fixture()
def db_session(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ownership.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    user_a = UserModel(id="user-a", name="User A", email="a@example.com", role="Patient")
    user_b = UserModel(id="user-b", name="User B", email="b@example.com", role="Patient")
    session.add_all([user_a, user_b])
    session.add_all([
        HealthRecordModel(
            id="rec-a",
            owner_user_id="user-a",
            user_email="a@example.com",
            title="A record",
        ),
        HealthRecordModel(
            id="rec-b",
            owner_user_id="user-b",
            user_email="b@example.com",
            title="B record",
        ),
        AppointmentModel(
            id="appt-a",
            owner_user_id="user-a",
            user_email="a@example.com",
            doctor_name="Doctor A",
            patient_name="User A",
            appointment_date="2026-08-25",
            appointment_time="10:00 AM",
        ),
        VitalRecordModel(
            id="vital-a",
            owner_user_id="user-a",
            user_email="a@example.com",
        ),
        OrderModel(
            id="order-a",
            owner_user_id="user-a",
            user_email="a@example.com",
            patient_name="User A",
            items_json=json.dumps([]),
            total_amount=100.0,
            delivery_address="A address",
            payment_method="UPI",
        ),
    ])
    session.commit()

    monkeypatch.setattr(profile, "get_db_session", Session)
    monkeypatch.setattr(store, "get_db_session", Session)
    try:
        yield session, user_a, user_b
    finally:
        session.close()
        Session.close_all()


def test_health_records_are_isolated_by_owner(db_session):
    _, user_a, user_b = db_session

    a_records = profile.get_health_records(user_a)["records"]
    b_records = profile.get_health_records(user_b)["records"]

    assert [record["id"] for record in a_records] == ["rec-a"]
    assert [record["id"] for record in b_records] == ["rec-b"]


def test_cross_user_appointment_cannot_be_cancelled(db_session):
    _, user_a, user_b = db_session

    result = profile.cancel_appointment("appt-a", user_b)

    assert result["message"] == "Appointment not found or already cancelled"

    session = profile.get_db_session()
    try:
        appointment = session.query(AppointmentModel).filter_by(id="appt-a").first()
        assert appointment is not None
        assert appointment.owner_user_id == user_a.id
    finally:
        session.close()


def test_new_health_record_uses_authenticated_owner_not_payload_email(db_session):
    session, user_a, _ = db_session

    result = profile.upload_health_record(
        {
            "title": "New record",
            "userEmail": "b@example.com",
            "memberId": "fam2",
        },
        user_a,
    )

    created = session.query(HealthRecordModel).filter_by(id=result["record"]["id"]).first()
    assert created is not None
    assert created.owner_user_id == user_a.id
    assert created.user_email == user_a.email


def test_new_vital_uses_authenticated_owner(db_session):
    session, user_a, _ = db_session

    profile.log_vital_reading({"systolic": 130}, user_a)

    created = (
        session.query(VitalRecordModel)
        .filter(
            VitalRecordModel.owner_user_id == user_a.id,
            VitalRecordModel.systolic == 130,
        )
        .order_by(VitalRecordModel.recorded_at.desc())
        .first()
    )
    assert created is not None
    assert created.owner_user_id == user_a.id
    assert created.user_email == user_a.email


def test_orders_are_isolated_and_new_order_uses_authenticated_owner(db_session):
    session, user_a, user_b = db_session

    a_orders = store.get_user_orders(user_a)["orders"]
    b_orders = store.get_user_orders(user_b)["orders"]
    assert [order["orderId"] for order in a_orders] == ["order-a"]
    assert b_orders == []

    request = store.OrderRequest(
        userId="user-b",
        items=[{"id": "med-1", "name": "Medicine", "price": 25.0, "quantity": 1}],
        totalAmount=25.0,
        address="A address",
        paymentMethod="UPI",
    )
    result = store.place_order(request, user_a)

    created = session.query(OrderModel).filter_by(id=result["orderId"]).first()
    assert created is not None
    assert created.owner_user_id == user_a.id
    assert created.user_email == user_a.email
    assert created.patient_name == user_a.name
