"""LAB-IREG-007: LBO PDU config offline; live session DEFERRED."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-007"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_007_pdu_lbo_config_present():
    assert (ROOT / "visited-network" / "configs" / "variants" / "smf-lbo.yaml").is_file()


@pytest.mark.live
@pytest.mark.deferred
def test_lab_ireg_007_pdu_lbo_live():
    pytest.skip("DEFERRED-TO-UBUNTU: live LBO PDU session requires UE attach")
