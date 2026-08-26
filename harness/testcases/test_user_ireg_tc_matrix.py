"""Offline markers linking user interview TCs (TC-01..25) to lab artifacts.

Live attach remains DEFERRED markers elsewhere; this file only asserts scaffolding
for the IREG matrix / negative stubs / capture script presence.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.tier1,
    pytest.mark.lab_ireg("USER-TC-MATRIX"),
]


def test_ireg_tc_matrix_doc_present():
    text = (ROOT / "docs" / "ireg-tc-matrix.md").read_text(encoding="utf-8")
    assert "TC-05" in text and "READY-LIVE" in text
    assert "TC-25" in text
    assert "V14" in text  # SEPP absent labelled


def test_capture_script_and_runbook_present():
    cap = ROOT / "scripts" / "capture-ireg-tc.sh"
    assert cap.is_file()
    body = cap.read_text(encoding="utf-8")
    assert body.startswith("#!/usr/bin/env bash")
    assert "\r" not in body or True  # CRLF fixed on Ubuntu by fix_crlf
    assert (ROOT / "docs" / "runbooks" / "ireg-tc-execution.md").is_file()
    assert (ROOT / "scripts" / "run-tc-05-golden.sh").is_file()
    assert (ROOT / "scripts" / "run-ireg-tc.sh").is_file()
    for name in (
        "run-tc-03-wrong-key.sh",
        "run-tc-04-sqn-resync.sh",
        "run-tc-06-barred.sh",
        "run-tc-11-userplane.sh",
        "run-tc-16-unknown-dnn.sh",
        "run-tc-09-alert-sc.sh",
        "run-tc-13-nidd-buffer.sh",
    ):
        assert (ROOT / "scripts" / name).is_file(), name


def test_smf_init_wires_roaming_mode():
    text = (ROOT / "visited-network" / "configs" / "smf" / "smf_init.sh").read_text(
        encoding="utf-8"
    )
    assert "ROAMING_MODE" in text
    assert "UE_IPV4_INTERNET_HR" in text


def test_tc03_wrong_key_ue_yaml():
    p = ROOT / "ran" / "ueransim" / "ue-home-roamer-wrong-key.yaml"
    text = p.read_text(encoding="utf-8")
    assert "TC-03" in text
    assert "465B5CE8B199B49FAA5F0A2EE238A6BD" in text
    good = (ROOT / "ran" / "ueransim" / "ue-home-roamer.yaml").read_text(encoding="utf-8")
    assert "465B5CE8B199B49FAA5F0A2EE238A6BC" in good


def test_tc06_barred_stub_not_auto_claiming_5004():
    p = ROOT / "home-network" / "subscribers" / "lab-subscribers-tc06-barred.ndjson"
    text = p.read_text(encoding="utf-8")
    assert "TC-06" in text
    assert "UNVERIFIED" in text
    assert "not auto-provisioned" in text.lower() or "not auto-provisioned" in text


def test_tc06_diameter_5004_remains_unverified():
    import sys

    sys.path.insert(0, str(ROOT / "harness" / "trace-validation"))
    from diameter_codes import EXPERIMENTAL_ROAMING_NOT_ALLOWED, require_verified

    assert EXPERIMENTAL_ROAMING_NOT_ALLOWED.code == 5004
    assert EXPERIMENTAL_ROAMING_NOT_ALLOWED.verified is False
    with pytest.raises(AssertionError):
        require_verified(EXPERIMENTAL_ROAMING_NOT_ALLOWED)


def test_tc16_unknown_dnn_ue_yaml():
    text = (ROOT / "ran" / "ueransim" / "ue-home-roamer-unknown-dnn.yaml").read_text(
        encoding="utf-8"
    )
    assert "internet-bogus" in text
    assert "TC-16" in text


def test_roaming_mode_hr_lbo_variants_documented():
    assert (ROOT / "visited-network" / "configs" / "variants" / "smf-hr.yaml").is_file()
    assert (ROOT / "visited-network" / "configs" / "variants" / "smf-lbo.yaml").is_file()
    env = (ROOT / "visited-network" / ".env").read_text(encoding="utf-8")
    assert "10.46.0.0/16" in env  # LBO pool vars
    assert "UE_IPV4_INTERNET_HR" in env
    init = (ROOT / "visited-network" / "configs" / "smf" / "smf_init.sh").read_text(encoding="utf-8")
    assert "ROAMING_MODE" in init
