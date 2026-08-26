"""LAB-IREG-018: Live emergency SMS path DEFERRED-TO-UBUNTU."""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-018"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
    pytest.mark.live,
    pytest.mark.deferred,
]


def test_lab_ireg_018_sms_live():
    pytest.skip(
        "DEFERRED-TO-UBUNTU: live emergency/SOS SMS over SGd requires Ubuntu stack"
    )
