"""LAB-IREG-005: Home PLMN BCD + realm naming offline; live AIR DEFERRED."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from plmn_bcd import encode_plmn_bcd, plmn_bcd_hex

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-005"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_005_home_plmn_and_realm():
    plan = yaml.safe_load((ROOT / "network-plan.yaml").read_text(encoding="utf-8"))
    assert encode_plmn_bcd("001", "01") == bytes.fromhex("00F110")
    assert plmn_bcd_hex("001", "01") == "00 F1 10"
    assert plan["lab"]["realms"]["home"] == "epc.mnc001.mcc001.3gppnetwork.org"
    assert plan["lab"]["realms"]["visited"] == "epc.mnc070.mcc999.3gppnetwork.org"
