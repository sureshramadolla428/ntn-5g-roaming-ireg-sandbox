"""LAB-IREG-009: Realm-not-served uses verified RFC 6733 code 3003 (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from diameter_codes import DIAMETER_REALM_NOT_SERVED, require_verified

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-009"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_009_realm_not_served_code():
    require_verified(DIAMETER_REALM_NOT_SERVED)
    assert DIAMETER_REALM_NOT_SERVED.code == 3003
    rt = Path(__file__).resolve().parents[2] / "ipx" / "freediameter" / "rt.conf.template"
    assert "DIAMETER_REALM_NOT_SERVED" in rt.read_text(encoding="utf-8")
