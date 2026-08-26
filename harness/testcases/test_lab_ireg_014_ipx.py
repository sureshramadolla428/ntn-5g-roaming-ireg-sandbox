"""LAB-IREG-014: INDETERMINATE when multi-point evidence incomplete."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from fault_domain import FaultDomain, Observation, fault_domain

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-014"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_014_indeterminate():
    assert (
        fault_domain(
            Observation(
                request_at_visited_edge=True,
                request_at_ipx_ingress=True,
                request_at_home_edge=True,
                answer_origin=None,
            )
        )
        == FaultDomain.INDETERMINATE
    )
