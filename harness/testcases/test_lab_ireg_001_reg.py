"""LAB-IREG-001: Roaming registration success HR — live attach DEFERRED-TO-UBUNTU."""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-001"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
    pytest.mark.live,
    pytest.mark.deferred,
]


def test_lab_ireg_001_reg():
    pytest.skip(
        "DEFERRED-TO-UBUNTU: live roaming registration (HR) needs Open5GS+UERANSIM/OAI attach"
    )
