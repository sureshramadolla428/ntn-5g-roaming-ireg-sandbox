"""Unit tests for Appendix C1 PLMN BCD encoding."""
from __future__ import annotations

from plmn_bcd import decode_plmn_bcd, encode_plmn_bcd, plmn_bcd_hex


def test_home_001_01():
    raw = encode_plmn_bcd("001", "01")
    assert raw == bytes.fromhex("00F110")
    assert plmn_bcd_hex("001", "01") == "00 F1 10"
    assert decode_plmn_bcd(raw) == ("001", "01")


def test_visited_999_70():
    raw = encode_plmn_bcd("999", "70")
    assert raw == bytes.fromhex("99F907")
    assert plmn_bcd_hex("999", "70") == "99 F9 07"
    assert decode_plmn_bcd(raw) == ("999", "70")


def test_three_digit_mnc_roundtrip():
    raw = encode_plmn_bcd("310", "260")
    assert decode_plmn_bcd(raw) == ("310", "260")
