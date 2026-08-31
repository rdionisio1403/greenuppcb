import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_full_pcb_and_child_resources_flow():
    # Benzersiz referans için standart zaman damgası
    test_ref = f"PCB-LAB-{int(time.time())}"

# 1. PCB Tablosu: Oluşturma (POST)
    pcb_payload = {
        "internal_reference": test_ref,
        "customer_name": "ABB Drives",
        "equipment": "Frequency Converter",
        "manufacturer": "ABB",
        "pcb_model": "ACS880",
        "serial_number": "SN-TEST-880",
        "date_received": "2026-08-31",
        "failure_description": "IGBT driver circuit failure",
    }
    create_res = client.post("/pcbs", json=pcb_payload)
    assert create_res.status_code == 201
    pcb_id = create_res.json()["id"]

# 2. PCB Tablosu: Listeleme ve Detay (GET)
    list_res = client.get("/pcbs")
    assert list_res.status_code == 200
    
    get_res = client.get(f"/pcbs/{pcb_id}")
    assert get_res.status_code == 200
    assert get_res.json()["internal_reference"] == test_ref

    # 3. PCB Tablosu: Güncelleme (PATCH)
    patch_payload = {
        "internal_reference": test_ref,
        "customer_name": "ABB Drives Portugal",
        "equipment": "Frequency Converter",
        "date_received": "2026-08-31",
        "failure_description": "Updated failure details",
    }
    patch_res = client.patch(f"/pcbs/{pcb_id}", json=patch_payload)
    assert patch_res.status_code == 200

# 4. Diagnoses Tablosu: Ekleme ve Listeleme
    diag_payload = {
        "diagnosis_date": "2026-08-31",
        "technician": "Sema",
        "fault_found": "Optocoupler isolation fault in gate drive",
        "recommended_action": "Replace HCPL-3120 optocoupler",
    }
    diag_res = client.post(f"/pcbs/{pcb_id}/diagnoses", json=diag_payload)
    assert diag_res.status_code == 201
    assert client.get(f"/pcbs/{pcb_id}/diagnoses").status_code == 200

# 5. Repairs Tablosu: Ekleme ve Listeleme
    repair_payload = {
        "repair_date": "2026-08-31",
        "technician": "Sema",
        "actions_taken": "Replaced HCPL-3120 optocoupler and cleaned flux residue",
        "components_replaced": "HCPL-3120 Optocoupler",
    }
    repair_res = client.post(f"/pcbs/{pcb_id}/repairs", json=repair_payload)
    assert repair_res.status_code == 201
    assert client.get(f"/pcbs/{pcb_id}/repairs").status_code == 200

# 6. Tests Tablosu: Ekleme ve Listeleme
    test_payload = {
        "test_date": "2026-08-31",
        "tester": "Sema",
        "test_type": "Signal generation and isolation test",
        "result": "PASSED",
        "notes": "PWM pulses clear at 20kHz, no jitter",
    }
    test_res = client.post(f"/pcbs/{pcb_id}/tests", json=test_payload)
    assert test_res.status_code == 201
    assert client.get(f"/pcbs/{pcb_id}/tests").status_code == 200
