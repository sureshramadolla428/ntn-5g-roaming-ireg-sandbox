"""LAB-IREG-025: netem B4 profile offline; live DEFERRED."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-025"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_025_netem_profile_present():
    assert (ROOT / "ran" / "oai" / "netem" / "profiles-b4.yaml").is_file()


@pytest.mark.live
@pytest.mark.deferred
def test_lab_ireg_025_ntn_live():
    pytest.skip("DEFERRED-TO-UBUNTU: live netem B4 + attach under delay")
