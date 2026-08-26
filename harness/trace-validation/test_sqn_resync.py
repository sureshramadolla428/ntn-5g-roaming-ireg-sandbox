"""Offline tests for TC-04 SQN resync observer."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sqn_resync import ScanResult, scan_text


def test_sqn_resync_detects_auts_marker():
    result = ScanResult()
    scan_text("fake", "AUSF: received AUTS from UE", result)
    assert result.found


def test_sqn_resync_silent_on_unrelated():
    result = ScanResult()
    scan_text("fake", "Registration accept", result)
    assert not result.found
