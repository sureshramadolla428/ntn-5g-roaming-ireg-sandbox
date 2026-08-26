"""LAB-IREG-002: Roaming registration LBO — live attach DEFERRED-TO-UBUNTU."""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-002"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
    pytest.mark.live,
    pytest.mark.deferred,
]


def test_lab_ireg_002_reg():
    pytest.skip(
        "DEFERRED-TO-UBUNTU: live roaming registration (LBO) needs Open5GS+RAN attach"
    )
