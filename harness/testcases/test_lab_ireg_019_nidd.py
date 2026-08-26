"""LAB-IREG-019: SCEF health + UNVERIFIED path labelling (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mocks" / "scef"))
from app import app
from fastapi.testclient import TestClient

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-019"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_019_scef_health_unverified():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["paths_verified"] is False
