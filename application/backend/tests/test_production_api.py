import os
import requests

BASE_URL = os.getenv(
    "PRODUCTION_API_URL",
    "https://curaassist-carehub-backend-2.fastapicloud.dev",
).rstrip("/")


def test_api_status():
    r = requests.get(f"{BASE_URL}/api/status", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "online"


def test_home():
    r = requests.get(f"{BASE_URL}/home/", timeout=20)
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_home_health_tips():
    r = requests.get(f"{BASE_URL}/home/health-tips", timeout=20)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_medicine_all():
    r = requests.get(f"{BASE_URL}/medicine/all", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["count"] > 0


def test_medicine_info():
    r = requests.get(f"{BASE_URL}/medicine/info/MED-002", timeout=20)
    assert r.status_code == 200
    medicine = r.json()["medicine"]
    assert medicine["medicine_id"] == "MED-002"
    assert medicine["brand_name"] == "Augmentin 625 Duo Tablet"


def test_medicine_search():
    r = requests.get(f"{BASE_URL}/medicine/search", params={"query": "paracetamol"}, timeout=20)
    assert r.status_code == 200
    assert r.json()["count"] > 0


def test_medicine_generics():
    r = requests.get(f"{BASE_URL}/medicine/generics/MED-002", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["medicineId"] == "MED-002"
    assert "Moxikind-CV 625" in data["alternativeBrands"]


def test_medicine_interactions():
    r = requests.post(
        f"{BASE_URL}/medicine/check-interactions",
        json={"medicines": ["Warfarin", "Aspirin"]},
        timeout=20,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["hasInteractions"] is True
    assert data["count"] >= 1


def test_store_medicines():
    r = requests.get(
        f"{BASE_URL}/store/medicines",
        params={"search": "amoxicillin"},
        timeout=20,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["count"] > 0


def test_store_orders_read_path():
    r = requests.get(f"{BASE_URL}/store/orders", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "orders" in data


# Intentionally no production POST /store/orders test here because that would create
# a real order in the production database on every CI run.
