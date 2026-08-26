"""LAB-IREG-024: NTN config offline; live attach DEFERRED."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-024"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_024_ntn_config_present():
    assert (ROOT / "ran" / "oai" / "configs" / "gnb.sa.band254.u0.25prb.rfsim.ntn-leo.conf").is_file()


@pytest.mark.live
@pytest.mark.deferred
def test_lab_ireg_024_ntn_live():
    pytest.skip("DEFERRED-TO-UBUNTU: live OAI NTN LEO attach + MEASURED RTT")
