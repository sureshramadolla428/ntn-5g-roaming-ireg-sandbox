"""LAB-IREG-017: Live SMS delivery DEFERRED-TO-UBUNTU."""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-017"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
    pytest.mark.live,
    pytest.mark.deferred,
]


def test_lab_ireg_017_sms_live():
    pytest.skip(
        "DEFERRED-TO-UBUNTU: live SGd/MAP SMS delivery requires Osmocom + Diameter peers"
    )
