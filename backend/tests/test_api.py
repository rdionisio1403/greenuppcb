import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="https://testserver")


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "GreenUpPCB LIS API is operational"}


def test_full_pcb_and_child_resources_flow():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must target the isolated test database.")

    url = make_url(database_url)
    if url.database != "greenupcb_test":
        raise RuntimeError("Refusing to run write tests outside greenupcb_test.")

    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()
            if actual_database != "greenupcb_test":
                raise RuntimeError("Test database safety check failed.")
    finally:
        engine.dispose()

    unique = str(time.time_ns())
    username = f"api_test_{unique}"
    email = f"{username}@example.com"
    password = f"TestPass-{unique}-Safe"

    register_res = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_res.status_code == 200, register_res.text

    login_res = client.post(
        "/auth/login",
        json={"username": username, "password": password, "role": "user"},
    )
    assert login_res.status_code == 200, login_res.text
    csrf_token = login_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    customer_res = client.post(
        "/customers",
        json={"name": f"ABB Drives Test {unique}"},
        headers=headers,
    )
    assert customer_res.status_code == 201, customer_res.text
    customer_id = customer_res.json()["id"]

    test_ref = f"PCB-LAB-{unique}"
    pcb_payload = {
        "internal_reference": test_ref,
        "customer_id": customer_id,
        "equipment": "Frequency Converter",
        "manufacturer": "ABB",
        "pcb_model": "ACS880",
        "serial_number": f"SN-{unique}",
        "date_received": "2026-08-31",
        "failure_description": "IGBT driver circuit failure",
    }

    create_res = client.post("/pcbs", json=pcb_payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    pcb_id = create_res.json()["id"]

    list_res = client.get("/pcbs")
    assert list_res.status_code == 200, list_res.text

    get_res = client.get(f"/pcbs/{pcb_id}")
    assert get_res.status_code == 200, get_res.text
    assert get_res.json()["internal_reference"] == test_ref

    patch_payload = {
        "internal_reference": test_ref,
        "customer_name": "ABB Drives Portugal",
        "equipment": "Frequency Converter",
        "date_received": "2026-08-31",
        "failure_description": "Updated failure details",
    }
    patch_res = client.patch(
        f"/pcbs/{pcb_id}", json=patch_payload, headers=headers
    )
    assert patch_res.status_code == 200, patch_res.text

    diag_payload = {
        "diagnosis_date": "2026-08-31",
        "technician": "Test Technician",
        "fault_found": "Optocoupler isolation fault in gate drive",
        "recommended_action": "Replace HCPL-3120 optocoupler",
    }
    diag_res = client.post(
        f"/pcbs/{pcb_id}/diagnoses", json=diag_payload, headers=headers
    )
    assert diag_res.status_code == 201, diag_res.text
    assert client.get(f"/pcbs/{pcb_id}/diagnoses").status_code == 200

    repair_payload = {
        "repair_date": "2026-08-31",
        "technician": "Test Technician",
        "actions_taken": "Replaced HCPL-3120 optocoupler and cleaned flux residue",
        "components_replaced": "HCPL-3120 Optocoupler",
    }
    repair_res = client.post(
        f"/pcbs/{pcb_id}/repairs", json=repair_payload, headers=headers
    )
    assert repair_res.status_code == 201, repair_res.text
    assert client.get(f"/pcbs/{pcb_id}/repairs").status_code == 200

    test_payload = {
        "test_date": "2026-08-31",
        "tester": "Test Technician",
        "test_type": "Signal generation and isolation test",
        "result": "PASSED",
        "notes": "PWM pulses clear at 20kHz, no jitter",
    }
    test_res = client.post(
        f"/pcbs/{pcb_id}/tests", json=test_payload, headers=headers
    )
    assert test_res.status_code == 201, test_res.text
    assert client.get(f"/pcbs/{pcb_id}/tests").status_code == 200
