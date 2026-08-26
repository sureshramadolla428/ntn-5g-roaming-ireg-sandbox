import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient
from app import app, NIDD_MAX_PAYLOAD_UNVERIFIED

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.json()["paths_verified"] is False


def test_size_boundary():
    over = "aa" * (NIDD_MAX_PAYLOAD_UNVERIFIED + 1)
    r = client.post("/t8-nidd/v1/unverified/scs-as-sessions", json={"ue_id": "imsi-1", "payload_hex": over})
    assert r.status_code == 413
