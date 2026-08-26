"""LAB-IREG-003: Auth / Diameter code registry offline (no live AIA)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from diameter_codes import DIAMETER_SUCCESS, EXPERIMENTAL_USER_UNKNOWN, require_verified

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-003"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_003_auth_success_code_verified():
    """Success path uses RFC 6733 DIAMETER_SUCCESS only — experimental codes stay gated."""
    require_verified(DIAMETER_SUCCESS)
    assert DIAMETER_SUCCESS.code == 2001
    with pytest.raises(AssertionError):
        require_verified(EXPERIMENTAL_USER_UNKNOWN)
