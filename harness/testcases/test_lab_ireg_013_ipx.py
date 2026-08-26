"""LAB-IREG-013: HOME fault when answer origin HOME with 5xxx experimental class."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from diameter_codes import EXPERIMENTAL_USER_UNKNOWN
from fault_domain import FaultDomain, Observation, fault_domain

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-013"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_013_home_answer_fault():
    # Use string class prefix only — experimental numeric code remains UNVERIFIED for oracles
    assert EXPERIMENTAL_USER_UNKNOWN.verified is False
    assert (
        fault_domain(Observation(answer_origin="HOME", answer_code="5xxx-class"))
        == FaultDomain.HOME
    )
