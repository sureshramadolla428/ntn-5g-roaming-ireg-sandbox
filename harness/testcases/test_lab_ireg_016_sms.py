"""LAB-IREG-016: SMS concat/emergency call-flow docs present (offline)."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-016"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_016_sms_docs():
    assert (ROOT / "docs" / "call-flows" / "sms-concat-emergency.md").is_file()
