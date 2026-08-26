"""LAB-IREG-015: SGd SMSC mock framing present (not live SMS)."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-015"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_015_sgd_mock_labelled():
    src = (ROOT / "mocks" / "sgd-smsc" / "server.py").read_text(encoding="utf-8")
    assert "MOCK:" in src
    assert "TS 29.338" in src
    assert "MOCK-SGD-ACK" in src
    assert "alert_sc" in src.lower() or "Alert-SC" in src
