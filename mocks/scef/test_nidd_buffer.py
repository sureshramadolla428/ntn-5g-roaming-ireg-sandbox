"""TC-13 MT NIDD buffering tests for SCEF mock."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient

from app import BUFFER_PATH, app

client = TestClient(app)
UE = "imsi-001010000000001"


def test_buffer_while_psm_then_deliver() -> None:
    r = client.post(
        BUFFER_PATH,
        json={"ue_id": UE, "payload_hex": "deadbeef", "psm_active": True},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "buffered"
    r2 = client.post(f"{BUFFER_PATH}/{UE}/psm", json={"psm_active": False})
    assert r2.status_code == 200
    assert r2.json()["status"] == "delivered-on-wake"
    stats = client.get(BUFFER_PATH)
    assert stats.json()["count"] >= 1


def test_health_reports_buffer() -> None:
    assert client.get("/health").json()["mt_buffer"] is True


if __name__ == "__main__":
    test_buffer_while_psm_then_deliver()
    test_health_reports_buffer()
    print("TC-13 buffer tests OK")
