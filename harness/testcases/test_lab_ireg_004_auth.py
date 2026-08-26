"""LAB-IREG-004: Visited-PLMN-Id BCD offline (C1); live AVP assert DEFERRED."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "trace-validation"))
from plmn_bcd import encode_plmn_bcd, plmn_bcd_hex

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-004"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_004_visited_plmn_bcd():
    """Visited 999-70 → 99 F9 07 per Appendix C1 (pcap byte check = Ubuntu)."""
    assert encode_plmn_bcd("999", "70") == bytes.fromhex("99F907")
    assert plmn_bcd_hex("999", "70") == "99 F9 07"
