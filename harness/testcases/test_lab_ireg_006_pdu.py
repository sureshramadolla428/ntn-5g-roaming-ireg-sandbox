"""LAB-IREG-006: HR PDU config offline; live session DEFERRED via separate marker file note."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-006"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_006_pdu_hr_config_present():
    """Offline: HR SMF variant + home SMF present. Live PDU = DEFERRED-TO-UBUNTU."""
    assert (ROOT / "visited-network" / "configs" / "variants" / "smf-hr.yaml").is_file()
    assert (ROOT / "home-network" / "configs" / "smf" / "smf.yaml").is_file()


@pytest.mark.live
@pytest.mark.deferred
def test_lab_ireg_006_pdu_hr_live():
    pytest.skip("DEFERRED-TO-UBUNTU: live HR PDU session requires UE attach + N4/N3")
