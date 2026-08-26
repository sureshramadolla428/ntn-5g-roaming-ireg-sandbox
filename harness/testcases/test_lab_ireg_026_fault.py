"""LAB-IREG-026: AMF-down pattern → VISITED via fault_domain (offline unit)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from fault_domain import FaultDomain, Observation, fault_domain

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-026"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_026_amf_down_fault_unit():
    """Live AMF-down inject is Ubuntu; offline asserts AIA-ok/attach-fail → VISITED."""
    assert (
        fault_domain(Observation(aia_success=True, attach_success=False))
        == FaultDomain.VISITED
    )
    variant = ROOT / "visited-network" / "configs" / "variants" / "failure-amf-down.yaml"
    assert variant.is_file()
